#!/usr/bin/env python3
"""Generate phase-one numeric tables from archived CSV measurements."""
import csv
import json
from pathlib import Path
from run_exp import ROOT, markdown_table, number, utc


def is_network(row):
    return (row["design"] in {"src", "designs/golden_auto"} or
            row["design"].startswith(("designs/dataflow", "designs/scatter"))) and bool(row["T_target"] or row["latency_cycles"])


def table_row(row):
    result = {k: row.get(k, "") for k in ("design", "precision_w_a_acc", "T_target", "clock_target_ns", "clock_est_ns",
              "latency_cycles", "interval_cycles", "latency_ms_est", "DSP", "BRAM18K", "LUT", "FF", "delta_psnr", "ii_ok", "status")}
    result["id"] = f"[{row['id']}]({row['md_path']})"
    return result


rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
rows = [r for r in rows if r["id"].startswith("E")]
network = [r for r in rows if is_network(r) and number(r["latency_ms_est"]) is not None and r["status"] in {"pass", "provisional", "infeasible"}]
network.sort(key=lambda r: float(r["latency_ms_est"]))
accepted = [r for r in network if r["status"] in {"pass", "provisional"} and r["csim_pass"] == "True" and
            (r["precision_w_a_acc"] == "float32" or number(r["delta_psnr"]) is not None and float(r["delta_psnr"]) >= -.1)]
baseline = next(r for r in rows if r["id"] == "E000")
best = accepted[0] if accepted else None
text = "# SRCNN on K26: overnight experiments\n\n"
text += f"The unchanged float baseline is functionally correct but infeasible ({baseline['BRAM18K']} BRAM18K; {float(baseline['latency_ms_est']):.3f} ms). "
text += "Uniform w10a10 loses 0.069514 dB on all 13 supplied Set14 pairs; w8a8 loses 5.179955 dB. "
if best:
    text += f"The fastest resource-feasible supplied-image candidate is [{best['id']}]({best['md_path']}) at {float(best['latency_ms_est']):.6f} ms; missing comic prevents complete Set14 acceptance.\n\n"
else:
    text += "No resource-feasible accepted network candidate has been measured; missing comic also prevents complete Set14 acceptance.\n\n"
text += "## Current best\n\n"
if best:
    text += markdown_table([table_row(best)], list(table_row(best)))
    verifies = [r for r in rows if r["status"] == "impl_complete"]
    text += "\nImplementation results are separate from HLS estimates; see verification experiments below. " if verifies else "\nNo completed Vivado implementation result has been recorded. "
else:
    text += "No qualifying fastest design. The smallest estimated latency of an infeasible design does not count as a usable result. "
text += "All performance is tool-estimated or explicitly labeled RTL/implementation evidence. No board validation was run.\n\n"
text += "## Precision\n\n[E010](E010_precision_scan/E010.md) profiles every supplied image and establishes nearest-even AP_RND_CONV, AP_SAT, full product fractions and bounded accumulators. "
text += "[E015](E015_apfixed_w16a16_single_retry/E015.md), [E019](E019_apfixed_w10a10_retry/E019.md) and [E013](E013_apfixed_w8a8/E013.md) use real AMD ap_fixed and match numpy butterfly outputs bit for bit. "
text += "[E017](E017_apfixed_boundary_w10a10/E017.md) confirms real-ap_fixed boundaries and exact integer convolution on every supplied image. "
text += "[E049](E049_integer_boundary_exhaustive/E049.md) exhausts 25,165,824 signed accumulator/cast cases. "
text += "[E062](E062_layer_int8_scan/E062.md) finds Conv2-only 8-bit weights pass (-0.075890 dB with other layers at w10a10); genuine INT8 activation inputs and Conv1/Conv3 INT8 weights fail. [E065](E065_apfixed_mixed_conv2w8/E065.md) confirms real-ap_fixed boundaries on all 13 images; [E066](E066_full_apfixed_mixed_butterfly/E066.md) confirms the complete all-ap_fixed mixed network bit for bit on butterfly.\n\n"
text += "Metric: normalized float MSE PSNR, no clipping/cropping, against the same unchanged float golden; the original uint8 conversion metric is retained in test logs. Supplied-image acceptance is provisional because comic is absent.\n\n"
text += "## Compiler Controls\n\nSee [STAGE2.md](STAGE2.md). Whole feature maps require 11,064 BRAM18K at baseline, so all valid structure-preserving controls are infeasible. "
text += "The valid innermost pipeline reaches II=1 but 26.707 ns estimated clock; outer pixel pipeline reaches 3,811.217 ms with 11,114 BRAM18K. "
text += "Floating-point loop-carried addition, memory ports and automatically unrolled inner loops remain limiting. E023/E024/E025 used unsupported directives and were invalidated; E028/E029/E032 are the valid replacements.\n\n"
text += "## Streaming And Scans\n\nSee [STAGE3.md](STAGE3.md) and streaming_analysis.csv for per-layer numbers. "
text += "E030 float and E033 fixed T32 pass all butterfly pixels and six-pixel borders. E033 uses 168 BRAM18K but 136,868 LUT, and its 31.822 ns critical path gives 123.540 ms. "
text += "E044 T16 worsens to 63.218 ns and E045 T8 reaches 126.008 ns / 266,266 LUT; removing redundant accumulator saturation and explicitly binding multipliers separates arithmetic semantics from fabric mapping. "
text += "E047 maps exactly 251 scheduled products to DSPs and reaches 29.13855 ms, but 89,341 LUT exceeds the 81,984 cap. Banked memories and integer boundary primitives are measured follow-ups, not presumed improvements.\n\n"
text += "AXI float-array signature remains unchanged; weights/biases load once before DATAFLOW, intermediate maps stay on chip, and requested sequential bursts are up to 256 words. Inner II=1 does not imply T frame throughput: pixel-loop fill/drain and pad-row transactions add measured overhead.\n\n"
stream = [table_row(r) for r in network if r["design"].startswith(("designs/dataflow", "designs/scatter"))]
if stream:
    text += markdown_table(stream, list(stream[0])) + "\n"
text += "## Optional Experiments\n\n"
optional = [r for r in rows if str(r["stage"]) == "5"]
if optional:
    text += markdown_table([table_row(r) for r in optional], list(table_row(optional[0]))) + "\n"
text += "Multiplier kernels report their own cycle counts, never a network-frame latency. T4 mixed fabric/DSP feasibility and scatter preserve strict arithmetic checks; infeasible reports remain visible. "
text += "Packing prerequisites: uniform INT8 quality fails; exact integer decomposition or confirmed Conv2 weight-only quantization is required. Direct T8 paper DSP split is 648/256/100=1004; Winograd Conv1 T4 plus direct Conv2 and packed Conv3 is 576/512/100=1188 before other overhead. These budgets are unmeasured phase-two hypotheses.\n\n"
text += "## Verification\n\n"
verification = [r for r in rows if str(r["stage"]) == "6" and r["id"] != "E099"]
if verification:
    text += markdown_table([table_row(r) for r in verification], list(table_row(verification[0]))) + "\n"
else:
    text += "No implementation or C/RTL cosimulation result yet. Finite-FIFO deadlock freedom cannot be inferred from unbounded software streams.\n\n"
text += "## All Experiments\n\n"
ordered = sorted(rows, key=lambda r: number(r["latency_ms_est"]) if number(r["latency_ms_est"]) is not None else float("inf"))
text += markdown_table([table_row(r) for r in ordered], list(table_row(ordered[0])))
text += "\n## Failed And Timed-Out Runs\n\n"
failed = [{"id": f"[{r['id']}]({r['md_path']})", "status": r["status"], "reason": r["notes"]} for r in rows if r["status"] in {"fail", "timeout", "invalid_config", "precision_fail"}]
text += markdown_table(failed, ["id", "status", "reason"]) if failed else "None recorded.\n"
text += "\nE014 reached its 45-minute full-ap_fixed simulation limit after nine images; E010/E017 still cover all supplied pairs. Quoted absolute include paths broke Vitis C simulation; retries use verified unquoted whitespace-free paths. Lock-queue failures are distinct from subprocess synthesis timeouts.\n\n"
text += "## Figures\n\n![Pareto](figs/pareto.png)\n\n![Precision](figs/precision_heatmap.png)\n\n![Compiler vs architecture](figs/compiler_vs_architecture.png)\n\n"
text += "## Pending Human Decisions\n\nMissing comic input/GT pair blocks full 14-image acceptance. Windows Vitis environment was unavailable; verified Linux Vitis 2026.1 was used through existing SSH, with Windows environment-script support retained but untested. Review normalized-float PSNR versus the original wrapping uint8 metric before external benchmark claims. Detailed decisions and all tool failures remain in [LOG.md](LOG.md).\n\n"
text += "## Next Steps\n\nExecute the authorized second phase on exp/explore-arch after phase-one completion. Prioritize packing/Winograd PE mapping, gather/scatter borders, memory banking and a loop schedule with continuous pixel throughput; compare all variants to the measured exact streaming baseline. Implement and RTL-cosim the best feasible provisional candidates while reporting the missing full-Set14 evidence.\n\n"
text += "Generated from results.csv and archived reference evidence at " + utc() + ".\n"
(ROOT/"experiments/SUMMARY.md").write_text(text)
print("SUMMARY", "best=" + (best["id"] if best else "none"), "experiments=" + str(len(rows)))
