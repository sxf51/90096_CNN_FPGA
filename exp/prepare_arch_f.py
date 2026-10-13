#!/usr/bin/env python3
"""Preplan memory and continuous scheduling alternatives."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def save(config):
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), config["id"],
                    "plan_" + config["name"]], cwd=ROOT, check=True)


def main():
    base = json.loads((ROOT / "exp/configs/G01.json").read_text())
    base.update(series="F", stage="arch_f", clock=4, T=16)
    base["defines"] = {**base["defines"], "EXP_T": 16}
    for exp_id, name, bram, uram, purpose in (
            ("F01", "fifo_lutram_control", 96, 0,
             "Map shallow wide feature FIFOs explicitly to LUTRAM, retaining all depths and the original nested-loop schedule. The first-phase reports map about72 BRAM18K to Conv1 features,features2 and padded3; trade these for LUTs without changing arithmetic."),
            ("F02", "uram_line_control", 132, 20,
             "Move Conv3's four320-bit-wide line banks from BRAM to URAM. Each bank needs ceil320/72=5 URAM, despite only259 useful addresses. Expect20 URAM to save36 BRAM18K, with latency/timing measured rather than presumed.")):
        save({**base, "id": exp_id, "name": name, "design": "designs/"+name,
              "purpose": purpose, "changes": "Independent gather source clone with one storage policy changed.",
              "estimates": {"DSP": 505, "Conv1_DSP": 324, "Conv2_DSP": 128, "Conv3_DSP": 50,
                            "BRAM18K": bram, "URAM": uram, "LUT": 60000, "T": 16,
                            "latency_cycles": 2014678,
                            "basis": "E042 T16/4ns measured schedule and505 DSP. FIFO memory saving is72 BRAM18K; URAM line control replaces36 BRAM18K with4*5 URAM. HLS may insert different storage latency."},
              "interpretation": "Separate memory capacity from granularity/wide-port fragmentation. Compare II, FIFO mapping and timing, then verify finite FIFO behavior on final candidates.",
              "conclusion": "Keep storage only if measured resources improve while exact results and scheduling remain accepted."})
    for exp_id, folds, online, clock in (("F03",16,False,4), ("F04",16,True,4),
                                          ("F05",8,True,4), ("F06",16,True,3.33),
                                          ("F07",8,True,3.33)):
        save({**base, "id": exp_id, "name": f"continuous_T{folds}_{'online' if online else 'oldpad'}_{str(clock).replace('.','p')}ns",
              "design": "designs/continuous_direct", "T": folds, "clock": clock,
              "defines": {**base["defines"], "EXP_T": folds, "EXP_ONLINE_PAD": int(online)},
              "purpose": "Separate window production from convolution engines, flatten pixel/fold loops into oneII1 loop and shift fixed channel registers each fold. Register balanced fabric reductions to break E070's eight-DSP unregistered adder path. " +
                         ("Online padding caches the first row and reads/emits subsequent rows together, avoiding pad3's serialized row phases." if online else "Retain original row-read/row-write padding to isolate the continuous schedule; finite-FIFO stalls may dominate RTL cycles."),
              "changes": "New continuous source, wide two-entry LUTRAM window FIFOs, unchanged input/output/weight contract and layer quantization points. Padding mode is an explicit compile-time control.",
              "estimates": {"DSP": 8032//folds+3, "Conv1_DSP": 5184//folds,
                            "Conv2_DSP": 2048//folds, "Conv3_DSP": 800//folds,
                            "BRAM18K": 96, "URAM": 0, "LUT": 58000 if folds == 16 else 100000,
                            "T": folds, "latency_cycles": 65025*folds+100000,
                            "basis": "Onefold/cycle,65025*T plus input/pad startup, weight load and drain allowance100000 cycles. All502 or1004 products bind to DSP; balanced23-bit additions have explicit fabric latency1. Keep line/pad memory, replace tiny wide BRAM FIFOs with LUTRAM. HLS maximum-component estimates may miss old-pad finite-FIFO row serialization."},
              "interpretation": "Compare continuous engine II and whole-frame cycles against ideal65025*T. Report registered reduction cost, stream warnings and actual RTL backpressure; HLS II alone is insufficient.",
              "conclusion": "Select feasible exact candidates and validate two-frame RTL latency/deadlock before attributing an end-to-end speedup."})


if __name__ == "__main__":
    main()
