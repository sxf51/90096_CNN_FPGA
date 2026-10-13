#!/usr/bin/env python3
"""Preplan an affine Conv1 weight loader after its measured timing violation."""
import argparse
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT, check_protected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", choices=("F24", "F25"), default="F24")
    parser.add_argument("--copy-source", action="store_true")
    args = parser.parse_args()
    check_protected()
    parent_id = "F23" if args.id == "F24" else "F24"
    parent = next((ROOT / "experiments").glob(parent_id+"_*/config.json")).parent
    design = "designs/continuous_affine_load_v1" if args.id == "F24" else "designs/continuous_nested_load_v1"
    if args.copy_source:
        planned = next((ROOT / "experiments").glob(args.id+"_*/plan.json"))
        subprocess.run(["git", "cat-file", "-e", "HEAD:"+str(planned.relative_to(ROOT))],
                       cwd=ROOT, check=True)
        target = ROOT / design
        if target.exists():
            raise RuntimeError("Design exists; use a new name")
        shutil.copytree(parent / "source", target)
        check_protected()
        print(target)
        return
    measured = json.loads((parent / "metrics.json").read_text())
    if not (measured["csim_pass"] is True and measured["bit_exact"] is True):
        raise RuntimeError("Timing control is not exact")
    log = (parent / "csynth.log.txt").read_text()
    if args.id == "F25":
        if "kx_write_ln440" not in log or "2.699 ns" not in log:
            raise RuntimeError("Expected flattened-counter critical-path evidence is absent")
        base = json.loads((parent / "plan.json").read_text())["configuration"]
        config = {**base,"id":"F25","name":"nested_weight_loader_T16_2p5ns",
                  "design":design,"control_experiment":"F24",
                  "purpose":"F24 eliminates F23's address multiplier and reports2.830503377ms, but its automatically flattened channel/row/column loop has a2.699ns kx compare/and/select/add/store control path. The unchanged inference region remains2.377ns. Disable flattening only in the Conv1 weight loader to isolate the small nine-element inner counter and test whether that control path shortens. Keep the same float weight contract, T16 engines and exact quantization. Accept additional per-row pipeline drain only if its measured frame/clock product improves.",
                  "changes":"Independent frozen F24 source copy; add LOOP_FLATTEN off to the Conv1 weight loader. No inference, parameter format or precision change.",
                  "estimates":{"DSP":measured["DSP"],"Conv1_DSP":324,"Conv2_DSP":128,"Conv3_DSP":50,
                               "BRAM18K":measured["BRAM18K"],"URAM":measured["URAM"],
                               "LUT":measured["LUT"]+500,"FF":measured["FF"]+1000,
                               "T":16,"latency_cycles":measured["latency_cycles"]+20000,
                               "basis":"Use F24 measured502DSP/73BRAM18K/69290LUT/124577FF and1048723cycles. Preserve MACs, banking and I/O. The flattened load loop has5194cycles and10-stage depth;576 separate nine-element kernel rows could pay about576*10=5760 extra drain cycles. Reserve20000extra cycles,500LUT and1000FF for conservative restart/control overhead. Hypothesize the short inner counter can approach the2.5ns target; the unchanged inference region is2.377ns. Use actual top clock and frame cycles, not that hypothesis, for ranking."},
                  "interpretation":"Compare F24/F25 loader loop depth, restart cycles and clock, separately from unchanged inference II. Turning off flattening can trade a simpler counter path for repeated pipeline fill/drain. Preserve negative timing/resource outcomes and stop this control investigation after the measured comparison.",
                  "conclusion":"Prefer the lowest measured exact resource-feasible latency product; final candidates still require every supplied image, routing and two RTL transactions."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),"F25","plan_nested_weight_loader"],
                       cwd=ROOT,check=True)
        return
    if "mul_ln440" not in log or "2.822ns" not in log:
        raise RuntimeError("Expected loader critical-path evidence is absent")
    base = json.loads((parent / "plan.json").read_text())["configuration"]
    config = {**base, "id":"F24", "name":"affine_weight_loader_T16_2p5ns",
              "design":design, "control_experiment":"F23",
              "purpose":"F23 reports a2.822ns15-bit address mul in srcnn_Pipeline_load1 at the flattened Conv1 weight read; its dataflow_region is2.377ns and write_output is1.825ns. The one-time loader therefore controls the global HLS clock estimate despite unchanged T16 inference engines. Replace the division/modulo-derived Conv1 index with explicit channel/kernel-row/kernel-column counters. Keep the runtime float parameters, every quantization point, memory partitions, streams, padding and MAC schedule. Hypothesis: remove the magic-division address multiplier and approach the2.5ns target without altering output bits.",
              "changes":"Independent frozen F23 source copy; only the Conv1 weight-load loop is rewritten with affine three-dimensional indices. All other arithmetic and interfaces remain unchanged.",
              "estimates":{"DSP":measured["DSP"],"Conv1_DSP":324,"Conv2_DSP":128,"Conv3_DSP":50,
                           "BRAM18K":measured["BRAM18K"],"URAM":measured["URAM"],
                           "LUT":measured["LUT"]+500,"FF":measured["FF"]+1000,
                           "T":16,"latency_cycles":measured["latency_cycles"]+20000,
                           "basis":"Use F23 measured502DSP/73BRAM18K/70449LUT/125618FF and1048730cycles. MAC count and memory banking stay fixed. Reserve20000extra cycles for possible nested-loader restart/drain instead of assuming automatic flattening, and500LUT/1000FF for counters/control. The2.377ns dataflow and1.825ns writer suggest a2.5ns top target could be reachable once the measured2.822ns loader multiplier is eliminated; this is a timing hypothesis, not routed evidence. Use the parsed max(target,estimated) clock and require two-frame bit identity before synthesis."},
              "interpretation":"Compare load1 loop depth, module clock and any new inferred parameter bursts against F23. The explicit counters may eliminate quotient multipliers but can add loop restart overhead; the total frame estimate includes that cost. Separate unchanged inference II from loader latency and do not infer routed timing from an HLS estimate.",
              "conclusion":"Rank the new point only after exact C simulation and unchanged resource gates; selected candidates require all supplied images, implementation and finite-FIFO RTL validation."}
    plan(config)
    subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),"F24","plan_affine_weight_loader"],
                   cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
