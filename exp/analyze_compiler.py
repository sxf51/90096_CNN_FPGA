#!/usr/bin/env python3
"""Write report-grounded compiler experiment interpretation and stage summary."""
import json
from run_exp import ROOT, markdown_table

interpretation = {
    "E020": "Loop labels reproduce the original schedule. Full-frame intermediate storage is the primary infeasibility; floating accumulation recurrence limits the auto-pipelined MAC loops.",
    "E021": "Tighter clock increases Conv1/Conv3 recurrence II to 11/10, compared with 5/4 at 10 ns. More cycles partially offset the shorter target period; full-frame storage is unchanged.",
    "E022": "Disabling automatic pipelining reduces DSP/LUT/FF but more than doubles frame latency. It cannot change intermediate-array capacity requirements.",
    "E026": "Unsafe floating-point reassociation changes generated arithmetic logic but scarcely changes frame latency. The dominant Conv1/Conv3 recurrence and full-frame storage remain; no RTL functional equivalence claim follows from C simulation alone.",
    "E027": "Changing types cuts feature-map storage roughly in half, still far above capacity. Runtime float-to-fixed weight loading is also costly: srcnn_Pipeline_VITIS_LOOP_55_4 alone reports 113,878 LUT and II 32. The 64-way Conv2 loop uses 64 DSP with II 1. Type replacement without architecture and memory organization is insufficient.",
    "E028": "Explicit innermost pipeline reaches II 1 for Conv1 and Conv3 by accepting a much slower estimated clock. The 26.707 ns estimate controls the required latency formula rather than the requested 10 ns. Conv2 remains II 32; target II achievement alone does not establish a fast feasible implementation.",
    "E029": "Pixel pipelining expands computation and memory access. Conv1 reports II 41 from input-port pressure; Conv2 reaches II 1 using a 310-DSP scheduled module; Conv3 pipeline is not achieved. Total DSP 320 and LUT 80,812 are much higher than default, while intermediate BRAM is still infeasible.",
    "E032": "Cyclic partition changes port organization and reduces some datapath mux logic, but the requested innermost II was already 1 in E028. It adds BRAM without improving the 26.707 ns critical path or frame latency. Ports are not the only bottleneck.",
}
summary = []
for exp_id, explanation in interpretation.items():
    archive = next((ROOT / "experiments").glob(exp_id + "_*"))
    row = json.loads((archive / "metrics.json").read_text())
    config = json.loads((archive / "config.json").read_text())
    md = archive / (exp_id + ".md")
    text = md.read_text()
    start, end = text.index("## 6."), text.index("## 7.")
    measured = "Reported top: " + "; ".join(f"{key}={row.get(key, 'unknown')}" for key in
                ("latency_cycles", "latency_ms_est", "clock_est_ns", "DSP", "BRAM18K", "LUT", "FF")) + "."
    replacement = "## 6. Interpretation / 解读\n\n" + explanation + "\n\n" + measured + " See archived csynth.rpt/XML and data.csv for exact module/loop attribution.\n\n"
    md.write_text(text[:start] + replacement + text[end:])
    summary.append({"id": exp_id, "latency_ms_est": row["latency_ms_est"], "DSP": row["DSP"],
                    "BRAM18K": row["BRAM18K"], "LUT": row["LUT"], "status": row["status"]})
stage = ROOT / "experiments/STAGE2.md"
stage.write_text("# Stage 2: compiler controls\n\nAll valid compiler-only variants are resource-infeasible. The fastest float control is E029; type-change E027 approaches its latency but has a very expensive parameter load and still stores full feature maps. No compiler flag removes the need to redesign storage and streaming.\n\n" +
                 markdown_table(summary, list(summary[0])) +
                 "\nE023/E024/E025 remain invalid_config because their original directive key was skipped. They are not evidence for the intended configurations.\n")
