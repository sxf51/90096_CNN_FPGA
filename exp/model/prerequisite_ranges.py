#!/usr/bin/env python3
"""Archive exact integer ranges needed by the authorized architecture phase."""
import csv
import json
import subprocess
import sys
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_exp import ROOT, FIELDS, check_protected, append_log, lock, utc, write_json, markdown_table


def main():
    check_protected()
    exp_id, name = "E071", "architecture_prerequisite_ranges"
    archive = ROOT / "experiments" / (exp_id + "_" + name)
    if archive.exists():
        raise RuntimeError("Existing ID")
    archive.mkdir()
    config = {"id": exp_id, "stage": 6, "time": utc(), "rounding": "AP_RND_CONV",
              "overflow": "AP_SAT", "scope": "parameter analysis, no HLS measurement",
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()}
    details = []
    g2 = np.array([[2, 0, 0], [1, 1, 1], [1, -1, 1], [0, 0, 2]], dtype=np.int64)
    for layer, shape in enumerate(((64, 1, 9, 9), (32, 64, 1, 1), (1, 32, 5, 5)), 1):
        values = np.fromfile(ROOT / f"src/weights/conv{layer}_weights_3x_flp.bin", dtype="<f4").reshape(shape)
        for bits in (8, 10, 16):
            raw = np.clip(np.rint(np.ldexp(values.astype(np.float64), bits - 1)),
                          -(1 << (bits - 1)), (1 << (bits - 1)) - 1).astype(np.int64)
            low = ((raw + 128) % 256) - 128
            residual = (raw - low) // 256
            row = {"kind": "weight", "layer": layer, "bits": bits,
                   "raw_min": int(raw.min()), "raw_max": int(raw.max()),
                   "raw_abs_max": int(np.abs(raw).max()),
                   "fits_signed8": bool(np.all((raw >= -128) & (raw <= 127))),
                   "residual_min": int(residual.min()), "residual_max": int(residual.max())}
            if layer == 1:
                transformed = []
                for kernel in raw[:, 0]:
                    for y in (0, 3, 6):
                        for x in (0, 3, 6):
                            transformed.append(g2 @ kernel[y:y+3, x:x+3] @ g2.T)
                transformed = np.array(transformed)
                bound = int(np.abs(transformed).max())
                row["G2_weight_abs_max"] = bound
                row["G2_weight_signed_bits"] = bound.bit_length() + 1
                row["conservative_transform_bits"] = bits + 4
            details.append(row)
    for activation_max, label in ((128, "signed INT8 worst-case"), (511, "nonnegative nine-bit raw activation")):
        worst_term = 128 * activation_max
        details.append({"kind": "packing_bound", "label": label, "field_bits": 18,
                        "worst_abs_term": worst_term, "max_safe_terms": ((1 << 17) - 1) // worst_term})
    for t, c1, c2, c3, label in ((8, 648, 256, 100, "direct 16-bit"),
                                (4, 648, 256, 100, "uniform INT8 packing: precision failed"),
                                (8, 288, 256, 100, "Conv1 Winograd"),
                                (4, 576, 512, 200, "Conv1 Winograd direct remainder"),
                                (4, 576, 256, 100, "Winograd plus mixed/exact packing")):
        details.append({"kind": "paper_budget", "label": label, "T": t, "C1_DSP": c1,
                        "C2_DSP": c2, "C3_DSP": c3, "DSP": c1+c2+c3,
                        "DSP_pct": 100*(c1+c2+c3)/1248,
                        "frame_compute_floor_cycles": 65025*t})
    columns = sorted(set().union(*(r.keys() for r in details)))
    with (archive / "data.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=columns)
        writer.writeheader()
        writer.writerows(details)
    write_json(archive / "config.json", config)
    md = f"# {exp_id}: integer prerequisites\n\n"
    md += "## 1. Purpose and hypothesis / 目的与假设\n\nResolve first-phase parameter prerequisites for packing and exact Winograd. This is software parameter analysis; DSP figures are paper budgets, not measured hardware.\n\n"
    md += f"## 2. Changes / 改动\n\nRead-only quantization and G2 transforms of protected parameters. Source commit `{config['source_commit']}`. No network design changes.\n\n"
    md += "## 3. Configuration / 配置\n\n" + markdown_table([{"parameter": k, "value": v} for k, v in config.items()], ["parameter", "value"])
    md += "\n## 4. Reproduction / 复现\n\n```sh\nworkspace/exp_runs/_tools/venv/bin/python exp/model/prerequisite_ranges.py\n```\n\n"
    md += "## 5. Results / 结果\n\n" + markdown_table(details, columns)
    md += "\nNo synthesis, loop II, latency or module resource measurement was performed.\n\n"
    md += "## 6. Interpretation / 解读\n\nConv3 ten-bit raw coefficients can fit signed8 while retaining fraction9; this is exact recoding, unlike the failed eight-bit fraction7 quantization. Conv2 accepts actual eight-bit weights (E065/E066), but its activations remain ten-bit with nonnegative nine-bit magnitudes. Such packing requires unpacking after at most two terms at gap18; the seven-term INT8 bound cannot be reused. G2 increases weight range without adding rounding; inverse transform must divide exactly by four. Paper budgets omit transforms, input loading, raster reorder, FIFO stalls and address/control overhead.\n\n"
    md += "## 7. Conclusion and next step / 结论与下一步\n\nTest DSP mapping, pre-adder use and exact unpacking in phase-two microbenchmarks before integrating. Raw weight residuals must be handled explicitly where needed. Full Set14 acceptance remains pending because comic is absent.\n\n"
    md += "## 8. Raw files / 原始文件位置\n\nThis parameter-only study reads src/weights; all derived data is in this archive. No HLS workspace was created.\n"
    (archive / (exp_id + ".md")).write_text(md)
    row = dict.fromkeys(FIELDS, "")
    row.update(id=exp_id, time=config["time"], stage=6, design="parameter_range_analysis",
               status="analysis_complete", git_commit=config["source_commit"],
               md_path=archive.name + "/" + exp_id + ".md", notes="paper budgets only, no hardware measurements")
    write_json(archive / "metrics.json", row)
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        with (ROOT / "experiments/results.csv").open("a", newline="") as out:
            csv.DictWriter(out, fieldnames=FIELDS).writerow(row)
        append_log("E071: archived exact coefficient ranges and phase-two paper budgets; no synthesis claim")
    check_protected()
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id, name], check=True)


if __name__ == "__main__":
    main()
