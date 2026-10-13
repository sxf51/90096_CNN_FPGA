#!/usr/bin/env python3
"""Report measured streaming bottlenecks and MAC-budget deviations."""
import csv
import json
from pathlib import Path
from run_exp import ROOT, FIELDS, lock, markdown_table, number, write_json

results = ROOT / "experiments/results.csv"
with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
    rows = list(csv.DictReader(results.open(newline="")))
analysis = []
for row in rows:
    if not row["design"].startswith(("designs/dataflow", "designs/scatter")):
        continue
    if not row["T_target"]:
        continue
    archive = ROOT / "experiments" / Path(row["md_path"]).parent
    config = json.loads((archive / "config.json").read_text())
    if config.get("operation") in {"impl", "cosim"}:
        continue
    modules = {p["module"]: p for p in config.get("parsed_modules", [])}
    defines = config.get("defines", {})
    splits = ["tap" if defines.get("EXP_C1_SPLIT") else "Cout",
              "Cin" if defines.get("EXP_C2_SPLIT") else "Cout",
              "tap" if defines.get("EXP_C3_SPLIT") else "Cin"]
    row["unroll_split"] = "/".join(splits)
    config["unroll"] = row["unroll_split"]
    metrics = json.loads((archive / "metrics.json").read_text())
    metrics["unroll_split"] = row["unroll_split"]
    if row["precision_w_a_acc"] == "w10a10acc23" and row["bit_exact"] == "True":
        quality = json.loads((ROOT / "experiments/E017_apfixed_boundary_w10a10/metrics.json").read_text())
        for key in ("delta_psnr", "set14_psnr"):
            row[key] = metrics[key] = quality[key]
        config["quality_provenance"] = {"path": "experiments/E017_apfixed_boundary_w10a10/metrics.json",
            "image_count": 13, "method": "Identical quantization points and full butterfly bit identity to E019/E017"}
    write_json(archive / "config.json", config)
    write_json(archive / "metrics.json", metrics)
    t = number(row["T_target"])
    measured = number(row["latency_cycles"])
    if t is None or measured is None:
        continue
    compute_floor = 65025 * t
    ideal_dsp = (64 * ((81 + int(t) - 1) // int(t)) if defines.get("EXP_C1_SPLIT") else 5184 / t)
    ideal_dsp += 2048 / t
    ideal_dsp += (32 * ((25 + int(t) - 1) // int(t)) if defines.get("EXP_C3_SPLIT") else 800 / t)
    point = {"id": row["id"], "T": t, "ideal_MAC_DSP": ideal_dsp,
             "actual_DSP": number(row["DSP"]), "compute_floor_cycles": compute_floor,
             "actual_cycles": measured, "cycle_overhead_pct": 100 * (measured / compute_floor - 1),
             "C1_DSP": modules.get("conv1_stream", {}).get("DSP"),
             "C2_DSP": modules.get("conv2_stream", {}).get("DSP"),
             "C3_DSP": modules.get("conv3_stream", {}).get("DSP"),
             "C1_cycles": modules.get("conv1_stream", {}).get("latency_cycles"),
             "C2_cycles": modules.get("conv2_stream", {}).get("latency_cycles"),
             "C3_cycles": modules.get("conv3_stream", {}).get("latency_cycles"),
             "clock_ns": number(row["clock_est_ns"]), "status": row["status"]}
    analysis.append(point)
    narrative = "Measured budget comparison:\n\n" + markdown_table([point], list(point))
    fold = modules.get("conv1_stream_Pipeline_c1_fold", {})
    if fold:
        narrative += f"\nConv1 fold module latency is {fold.get('latency_cycles')} cycles, with interval {fold.get('interval_cycles')}. "
        narrative += f"Its containing spatial engine takes {point['C1_cycles']} cycles; Conv2 takes {point['C2_cycles']} cycles. "
        narrative += "Inner-loop II=1 alone does not establish T cycles per pixel: pipeline fill/drain and unpipelined spatial control add frame overhead.\n"
    if row["design"] in {"designs/dataflow_v1", "designs/scatter_v1"}:
        narrative += "\nThe baseline report lists narrow `mul_10s_10s_20_1_1` fabric products at 62 LUT and zero DSP each, with a few fused DSP MACs. "
        narrative += "Complete register weight partitions also create large variable-index sparse muxes. Saturating every partial addition prevents associative reduction; Conv3's recurrence can satisfy II=1 by lengthening the combinational clock path. These effects explain the deviation from the one-DSP-per-MAC paper model.\n"
    else:
        narrative += "\nCompare to E033 to separate saturation semantics, product binding, banking and clock effects. Accumulator mode changes retain full fractions and rely on the trained-weight absolute-sum bounds; bit identity is required.\n"
    if row["id"] in {"E041", "E042", "E043"}:
        control = next(r for r in rows if r["id"] == "E058")
        narrative += (f"\nThe clock-only control E058 takes {control['latency_cycles']} cycles at target "
                      f"{control['clock_target_ns']} ns, or {control['latency_ms_est']} ms. This run takes "
                      f"{measured:g} cycles at target {row['clock_target_ns']} ns and estimated "
                      f"{row['clock_est_ns']} ns, or {row['latency_ms_est']} ms. More pipeline stages "
                      "increase cycles while the shorter clock improves the specified latency estimate. "
                      "This is a csynth clock sweep; E070's routed timing failure demonstrates why these "
                      "estimates must be checked by implementation before claiming timing closure.\n")
    if row["id"] == "E060":
        control = next(r for r in rows if r["id"] == "E057")
        scatter = modules.get("conv3_stream", {})
        pad = modules.get("replicate_pad_pixel2_2_s", {})
        narrative += (f"\nAgainst gather E057, scatter changes frame latency from "
                      f"{control['latency_ms_est']} to {row['latency_ms_est']} ms, BRAM18K from "
                      f"{control['BRAM18K']} to {row['BRAM18K']}, LUT from {control['LUT']} to "
                      f"{row['LUT']} and FF from {control['FF']} to {row['FF']}. Conv3 itself uses "
                      f"{scatter.get('BRAM18K')} BRAM18K for five 32-bit partial-sum rows, while the "
                      f"explicit 32-channel padding row still costs {pad.get('BRAM18K')} BRAM18K. "
                      "The register window removes same-column BRAM read/modify/write hazards, but "
                      "scatter visits every padded source pixel and adds register-update/control work. "
                      "Butterfly and border identity pass; boundary-kernel scatter in phase two can "
                      "test eliminating that remaining padding row.\n")
    log = (archive / "csynth.log.txt").read_text(errors="replace")
    warnings = [line for line in log.splitlines() if "[HLS 200-1449]" in line or "[HLS 200-880]" in line]
    if warnings:
        narrative += "\nDataflow/scheduling warnings:\n\n```text\n" + "\n".join(warnings[:12]) + "\n```\n"
    narrative += "\nSoftware stream occupancy is unbounded and is not evidence of finite FIFO deadlock freedom. RTL cosimulation remains required. Resource status uses the stated K26 limits without relaxation.\n"
    path = archive / (row["id"] + ".md")
    text = path.read_text()
    start, end = text.index("## 6."), text.index("## 7.")
    text = text[:start] + "## 6. Interpretation / 解读\n\n" + narrative + "\n" + text[end:]
    start, end = text.index("## 3."), text.index("## 4.")
    table = markdown_table([{"parameter": k, "value": v} for k, v in config.items()
                            if k not in {"parsed_loops", "parsed_modules", "validation"}], ["parameter", "value"])
    text = text[:start] + "## 3. Configuration / 配置\n\n<!-- AUTO -->\n\n" + table + "\n" + text[end:]
    start, end = text.index("## 5."), text.index("## 6.")
    table = markdown_table([{"metric": k, "value": metrics.get(k)} for k in FIELDS], ["metric", "value"])
    table += "\n### Pipeline loops\n\n" + markdown_table(config.get("parsed_loops", []), ["module", "loop", "target_ii", "actual_ii", "ii_ok"])
    table += "\n### Module resources\n\n" + markdown_table(config.get("parsed_modules", []), ["module", "DSP", "BRAM18K", "URAM", "LUT", "FF"])
    text = text[:start] + "## 5. Results / 结果\n\n<!-- AUTO -->\n\n" + table + "\n" + text[end:]
    path.write_text(text)
with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
    current = list(csv.DictReader(results.open(newline="")))
    updated = {row["id"]: row for row in rows}
    with results.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(updated.get(row["id"], row) for row in current)
if analysis:
    with (ROOT / "experiments/streaming_analysis.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(analysis[0]))
        writer.writeheader()
        writer.writerows(analysis)
    (ROOT / "experiments/STAGE3.md").write_text("# Streaming structure and measured overhead\n\n" +
        markdown_table(analysis, list(analysis[0])) +
        "\nE030 float and fixed architecture butterfly outputs match their respective references bit for bit. "
        "All 65,025 output pixels and the six-pixel border are checked. Padding emits 69,169 first-layer and 67,081 third-layer tokens; output remains 65,025. "
        "AXI input/output/weights retain float arrays, sequential bursts up to 256 words, and AXI-Lite pointer/control registers. "
        "No intermediate feature map goes to DDR. Weight and bias load happens before DATAFLOW. "
        "Inferred burst lengths and throughput are report values, not measured board bandwidth.\n")
