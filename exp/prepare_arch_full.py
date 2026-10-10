#!/usr/bin/env python3
"""Preplan exact packing and Winograd layer/network integrations."""
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
    for exp_id, folds in (("P10", 16), ("P11", 8), ("P12", 4)):
        dsp = 8032 // (2 * folds) + 3
        save({**base, "id": exp_id, "name": f"exact10_packing_T{folds}", "series": "P",
              "stage": "arch_p", "design": "designs/packing_network", "clock": 4, "T": folds,
              "defines": {**base["defines"], "EXP_T": folds},
              "precision": "w10a10acc23", "unroll": "paired Cout/paired Cout/adjacent pixels",
              "purpose": "Integrate the measured exact10 residual PE. Conv1/Conv2 pair output channels sharing each input. Conv3 pairs adjacent outputs sharing each weight, centers the upper nonnegative activation by256, repairs signed-low borrowing, then restores both coefficient residuals. Decode every product, so no low-field accumulation bound is assumed. Preserve all first-phase quantization points.",
              "changes": "New network source;5x6 Conv3 window and259x260 pad stream handle adjacent pairs and discard output column255. Weight coefficients are split signed-low8+256*residual[-2,2] inside the PE; no accuracy loss.",
              "estimates": {"DSP": dsp, "Conv1_DSP": 5184 // (2 * folds),
                            "Conv2_DSP": 2048 // (2 * folds), "Conv3_DSP": 800 // (2 * folds),
                            "BRAM18K": 168, "URAM": 0, "LUT": int(8032 / (2 * folds) * 240 + 12000),
                            "T": folds, "latency_cycles": int(65025 * (folds + 16) + 50000),
                            "basis": "P07 maps one exact10 pair to1 DSP but454 total LUT, including scalar interface/control. Estimate240 LUT per parallel pair in the full engine, plus12000 fixed overhead. Conv3 uses2*T folds per adjacent pair and32/(2*T) channel lanes. Baseline pixel fill/drain adds about16 cycles; line/FIFO storage follows gather control."},
              "interpretation": "Compare DSP halving to residual/borrow LUT cost and pixel scheduling. Preserve any resource excess; exact10 is chosen because uniform INT8 loses5.18dB.",
              "conclusion": "Use the passing exact10 point only if all resource caps hold; full INT8 is not accepted."})
    for exp_id, folds, layer in (("W04", 16, True), ("W05", 16, False), ("W06", 8, False)):
        c1 = 2304 // folds
        dsp = c1 + (0 if layer else 2848 // folds) + (0 if layer else 3)
        config = {**base, "id": exp_id, "name": ("winograd_conv1_T" if layer else "winograd_network_T") + str(folds),
                  "series": "W", "stage": "arch_w", "scope": "layer" if layer else "frame",
                  "design": "designs/winograd_network", "T": folds, "clock": 4,
                  "defines": {**base["defines"], "EXP_T": folds},
                  "unroll": "G2 F2 nine subkernels/Cout/Cin", "precision": "w10a10acc23",
                  "purpose": "Apply exact integer F2 to nine3x3 pieces of Conv1's9x9 kernel. Full input transforms add2 bits, G2 weights add4 bits;12x14 products fit one DSP. The34-bit inverse is divisible by4 before the ordinary bias/ReLU cast. Runtime transforms preserve arbitrary incoming float weights. Use9 previous input rows,10x10 window and264x264 padded input;128x128 output tiles discard row/column255. Two512-deep row FIFOs reorder to raster before Conv2.",
                  "changes": "Independent Winograd network/layer source. Equivalent offline transformed weights will be archived for inspection, while the internal load stage retains the original top contract.",
                  "estimates": {"DSP": dsp, "Conv1_DSP": c1,
                                "Conv2_DSP": 0 if layer else 2048 // folds,
                                "Conv3_DSP": 0 if layer else 800 // folds,
                                "BRAM18K": 117 if layer else 241, "URAM": 0,
                                "LUT": c1 * 125 + (4000 if layer else 23000), "T": folds,
                                "latency_cycles": int(16384 * (4 * folds + 20) + 55000),
                                "basis": "Nine*16 products per output-channel lane,64/(4*T) lanes. W01 confirms16 DSP/F2 PE and1499 LUT including transforms/interface. Two512x640-bit row FIFOs add72 BRAM18K to gather's168; one extra input line adds1. Latency uses16384 tiles,4*T folds and20 fill/drain cycles. Layer estimate includes input9-line buffers and raster FIFO costs."},
                  "interpretation": "Measure transforms, wider arithmetic, runtime weight load, raster FIFO and pipeline fill/drain separately. Explain more than20% deviation from the multiplier-only budget.",
                  "conclusion": "Require exact butterfly output, then integrate only resource-feasible results. Numerical transforms are exact; FIFO progress still needs RTL cosim."}
        if layer:
            for key in ("quality_reference", "reference", "quick"):
                config.pop(key, None)
            config.update(top="wino_conv1", tb_files=["exp/tb/winograd_layer.cpp", "src/weights", "test/set5"])
        save(config)


if __name__ == "__main__":
    main()
