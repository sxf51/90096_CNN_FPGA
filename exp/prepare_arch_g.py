#!/usr/bin/env python3
"""Preplan same-precision/T/clock Conv3 organization controls."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    base = json.loads((ROOT / "exp/configs/E057.json").read_text())
    cases = [
        ("G01", "gather_control", "designs/gather_control", 168, 44500, 2983024,
         "Repeat the measured gather topology with an independent source copy. Conv3 keeps4*259*32*10 line bits plus5x5x32 register window; expected36 Conv3 line BRAM18K. This is the common control for both scatter variants."),
        ("G02", "scatter_pad_control", "designs/scatter_pad_control", 137, 39200, 3770206,
         "Repeat explicit-pad scatter with identical T32 and10ns. Conv3 partial cache is5*255*32=40800bits,5 banked BRAM18K; explicit pad3 still needs255*32*10=81600bits and32 measured BRAM18K. Expect less memory/FF than gather but more scheduling work."),
        ("G03", "scatter_edge_kernels", "designs/scatter_edge", 87, 46000, 3700000,
         "Merge replicate taps into nine source-position kernels and remove the32-channel padding row/FIFO. Five rotating32-bit sum rows and a5x5 register window avoid BRAM RMW dependencies. Merged coefficients retain fraction9 and need15 bits;9*32*25*15=108000bits of LUTRAM replaces8000 raw weight bits. Expect near-scatter latency with50 fewer BRAM18K, offset by kernel selection and wider arithmetic."),
    ]
    for exp_id, name, design, bram, lut, cycles, purpose in cases:
        config = {**base, "id": exp_id, "name": name, "series": "G", "stage": "arch_g", "scope": "frame",
                  "design": design, "defines": {**base["defines"], "EXP_FRAMES": 2},
                  "purpose": purpose,
                  "changes": "Independent first-phase integer design copy; original float srcnn signature, ap_fixed input/weight casts and exact layer quantization remain unchanged.",
                  "interpretation": "Compare all three variants at identical precision, T32 and10ns. Separate partial-sum, pad-row, FIFO and merged-weight memory; explain estimates differing by over20 percent using per-module loops/resources.",
                  "conclusion": "Keep only exact borders and measured resource/latency evidence; finite-FIFO correctness requires final RTL verification.",
                  "estimates": {"DSP": 254, "Conv1_DSP": 162, "Conv2_DSP": 64, "Conv3_DSP": 25,
                                "boundary_DSP": 3, "BRAM18K": bram, "URAM": 0, "LUT": lut,
                                "T": 32, "latency_cycles": cycles,
                                "basis": "251 scheduled multipliers plus3 measured output converters. Controls use E057/E060 timing; edge estimate scales source work and adds kernel/load control. BRAM87 is137 minus32 pad-row and18 padded-feature FIFO. Runtime merged weights require writable LUTRAM."}}
        plan(config)
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id, "plan_" + name], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
