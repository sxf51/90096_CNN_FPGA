#!/usr/bin/env python3
"""Preplan measured Conv3 selection and reduction-register follow-ups."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    base = json.loads((ROOT / "exp/configs/F09.json").read_text())
    for exp_id,t,tree_latency,lut,ff in (("F13",16,1,67400,114000),
                                       ("F14",8,1,88000,178000),
                                       ("F15",8,0,87000,125000)):
        config = {**base,"id":exp_id,"name":f"rotate_c3_T{t}_tree{tree_latency}_4ns",
                  "design":"designs/continuous_rotate_v1","T":t,
                  "defines":{**base["defines"],"EXP_T":t,"EXP_TREE_ADD_LATENCY":tree_latency},
                  "purpose":"F08 measures7013 multiplexer LUT out of13268 in Conv3 engine3, with505DSP and106171 totalFF. Rotate each25x32 held window by C3_IC channels per fold, so products read fixed front-channel taps rather than variable32-channel selectors. Keep the two4000-bit FIFO contract and online replicate padding. "+
                            ("Use the registered reduction control." if tree_latency else "Bind fabric tree additions to latency0 to test whether the compiler can schedule fewer registers without violating useful clock/II. The whole tree may lengthen the estimated clock; use the required max(target,estimated) latency metric."),
                  "changes":"Independent continuous_direct_r2 copy. Only Conv3 held-window channel access/rotation and configurable reduction-adder latency change. Weight lanes, product counts, quantization and incoming float-array contract remain identical.",
                  "estimates":{"DSP":8032//t+3,"Conv1_DSP":5184//t,"Conv2_DSP":2048//t,
                               "Conv3_DSP":800//t,"BRAM18K":96,"URAM":0,"LUT":lut,"FF":ff,
                               "T":t,"latency_cycles":65025*t+100000,
                               "basis":"F08 supplies actual per-module costs: engine1 LUT8741, Conv2 LUT3617, engine3 LUT13268 including7013 mux LUT, and total69362LUT/106171FF. T16 planning allows~2000 net mux-LUT saving after8000-bit parallel-load/shift selection and~8000 extraFF. T8 doubles MAC/reduction lanes while fixed line/FIFO/interface costs stay constant; LUT/FF feasibility is deliberately uncertain. The latency0 variant discounts register overhead but reserves similar combinational LUT.65025*T plus100000 load/start/drain allowance, and no DDR timing substituted."},
                  "interpretation":"Compare exact outputs and per-foldII before using resource/latency measurements. Isolate mux savings from added load/shift selection and registered-tree FF. T8 may exceed the unchanged LUT/FF caps; latency0 may miss target clock, so neither is presumed feasible.",
                  "conclusion":"Retain measured feasible points only. If the reduction or rotation cannot meetII1 within45minutes, preserve its failure and use the existing accepted continuous control."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_rotating_window"],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
