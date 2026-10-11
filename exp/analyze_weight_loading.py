#!/usr/bin/env python3
"""Derive loader gates and area attribution from archived reports and logs."""
import argparse
import csv
import json
from analyze_arch import area_breakdown, write_csv
from run_exp import ROOT, markdown_table, number


def loader_measurement(archive, baseline):
    row = json.loads((archive / "metrics.json").read_text())
    config = json.loads((archive / "config.json").read_text())
    result = {key: row.get(key) for key in ("id", "T_target", "clock_target_ns", "clock_est_ns",
              "latency_cycles", "interval_cycles", "latency_ms_est", "DSP", "BRAM18K", "URAM", "LUT", "FF",
              "csim_pass", "bit_exact", "border_mse", "delta_psnr", "status")}
    modules = [item for item in config.get("parsed_modules", []) if item["module"] == "dataflow_region"]
    result["dataflow_LUT"] = modules[0]["LUT"] if len(modules) == 1 else None
    result["outside_LUT"] = (number(row["LUT"]) - result["dataflow_LUT"]
                              if number(row["LUT"]) is not None and result["dataflow_LUT"] is not None else None)
    report = archive / "csynth.rpt"
    if report.is_file():
        area = area_breakdown(report)
        result["top_multiplexer_LUT"] = next(item["LUT"] for item in area if item["category"] == "Multiplexer")
    else:
        result["top_multiplexer_LUT"] = None
    log = archive / "csynth.log.txt"
    warnings = [line.strip() for line in log.read_text().splitlines() if "HLS 200-1449" in line] if log.is_file() else []
    result["weight_predecessor_warnings"] = len(warnings) if log.is_file() else None
    fold_aliases = (("c1_fold", "wino_fold"), ("c2_fold",), ("c3_fold",))
    folds = [item for item in config.get("parsed_loops", []) if any(
        key in item["loop"] for aliases in fold_aliases for key in aliases)]
    fold_names = {layer for layer, aliases in enumerate(fold_aliases)
                  if any(any(key in item["loop"] for key in aliases) for item in folds)}
    result["fold_II1"] = len(fold_names) == 3 and all(item["actual_ii"] == 1 for item in folds)
    actual_cycles, actual_clock = number(row["latency_cycles"]), number(row["clock_est_ns"])
    result["cycles_gate"] = actual_cycles <= number(baseline["latency_cycles"])*1.01 if actual_cycles is not None else None
    result["clock_gate"] = actual_clock <= number(baseline["clock_est_ns"]) if actual_clock is not None else None
    result["outside_gate"] = result["outside_LUT"] <= 12000 if result["outside_LUT"] is not None else None
    result["border_gate"] = number(row["border_mse"]) == number(baseline["border_mse"]) if number(row["border_mse"]) is not None else None
    result["ws2_all_gates"] = (row["status"] in {"pass", "provisional"} and row["bit_exact"] is True and
                               result["fold_II1"] and all(result[key] is True for key in
                                   ("cycles_gate", "clock_gate", "outside_gate", "border_gate")) and
                               (row["id"] != "F27" or result["weight_predecessor_warnings"] == 0))
    for key in ("DSP", "BRAM18K", "LUT", "FF", "latency_cycles", "outside_LUT"):
        estimate = number(config.get("estimates", {}).get(key))
        actual = number(result.get(key))
        result["estimated_"+key] = estimate
        result["deviation_"+key+"_pct"] = 100*(actual/estimate-1) if actual is not None and estimate else None
    return result, warnings


def update_block(path, block, heading):
    text = path.read_text()
    start, end = "<!-- AUTO: LOADER START -->", "<!-- AUTO: LOADER END -->"
    rendered = start + "\n\n" + block.rstrip() + "\n\n" + end + "\n\n"
    if start in text:
        before, after = text.split(start, 1)
        text = before + rendered + after.split(end, 1)[1].lstrip("\n")
    else:
        text = text.replace(heading, rendered + heading, 1)
    path.write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", default=["F25", "F26", "F27", "W17", "W19"])
    args = parser.parse_args()
    baseline_archive = next((ROOT / "experiments").glob("F25_*/metrics.json"))
    baseline = json.loads(baseline_archive.read_text())
    rows = []
    for exp_id in args.ids:
        matches = list((ROOT / "experiments").glob(exp_id+"_*/metrics.json"))
        if not matches:
            continue
        if len(matches) != 1:
            raise RuntimeError("Ambiguous archive: "+exp_id)
        archive = matches[0].parent
        row, warnings = loader_measurement(archive, baseline)
        rows.append(row)
        write_csv(archive / "loader_analysis.csv", [row], list(row))
        block = "Loader analysis parsed from csynth XML/report and console logs:\n\n"
        block += markdown_table([{"metric":key,"value":value} for key,value in row.items()], ["metric","value"])
        block += "\nOutside LUT = top total minus the dataflow_region child; moving loaders inside changes this boundary. Compare total LUT too.\n\n"
        block += "HLS200-1449 messages:\n\n" + ("\n".join("- " + item for item in warnings) if warnings else "None in the archived synthesis log." if (archive / "csynth.log.txt").is_file() else "Unknown; no synthesis log.") + "\n"
        if exp_id not in {"F25", "W17"}:
            update_block(archive / (exp_id+".md"), block, "## 6. Interpretation")
    if not rows:
        return
    write_csv(ROOT / "experiments/weight_loading_comparison.csv", rows, list(rows[0]))
    columns = ["id", "T_target", "clock_target_ns", "clock_est_ns", "latency_cycles", "latency_ms_est",
               "DSP", "BRAM18K", "LUT", "dataflow_LUT", "outside_LUT", "FF", "fold_II1", "ws2_all_gates", "status"]
    text = "# Weight loading and T8 measurements\n\nGenerated by `python3 exp/analyze_weight_loading.py`. All numbers come from archived reports.\n\n"
    text += markdown_table(rows, columns)
    text += "\nThe WS2 gates compare T16 loaders with F25; T8 rows use the same diagnostics but are not WS2 acceptance points. Missing comic leaves image-quality conclusions provisional.\n\n"
    text += "![Loader area attribution](figs/weight_loading_area.png)\n\n"
    (ROOT / "experiments/WEIGHT_LOADING.md").write_text(text)
    print("Parsed loader records:", ", ".join(row["id"] for row in rows))


if __name__ == "__main__":
    main()
