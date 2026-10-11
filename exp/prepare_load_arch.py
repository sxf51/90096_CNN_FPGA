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
    parser.add_argument("--copy-source", action="store_true")
    args = parser.parse_args()
    check_protected()
    parent = next((ROOT / "experiments").glob("F23_*/config.json")).parent
    if args.copy_source:
        planned = next((ROOT / "experiments").glob("F24_*/plan.json"))
        subprocess.run(["git", "cat-file", "-e", "HEAD:"+str(planned.relative_to(ROOT))],
                       cwd=ROOT, check=True)
        target = ROOT / "designs/continuous_affine_load_v1"
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
    if "mul_ln440" not in log or "2.822ns" not in log:
        raise RuntimeError("Expected loader critical-path evidence is absent")
    base = json.loads((parent / "plan.json").read_text())["configuration"]
    config = {**base, "id":"F24", "name":"affine_weight_loader_T16_2p5ns",
              "design":"designs/continuous_affine_load_v1", "control_experiment":"F23",
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
