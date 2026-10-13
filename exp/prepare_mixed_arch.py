#!/usr/bin/env python3
"""Preplan mixed-precision packing using the independently verified E065 point."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    base = json.loads((ROOT / "exp/configs/W11.json").read_text())
    for exp_id, folds in (("C08",8),("C09",4)):
        config = {**base,"id":exp_id,"series":"C","stage":"arch_c",
                  "name":f"wino_conv2w8_continuous_T{folds}","design":"designs/winograd_mixed_packing",
                  "T":folds,"defines":{**base["defines"],"EXP_T":folds},
                  "precision":"w10_8_10a10acc23_21_23",
                  "reference":"experiments/E065_apfixed_mixed_conv2w8/butterfly_output.bin",
                  "quality_reference":"experiments/E065_apfixed_mixed_conv2w8/metrics.json",
                  "unroll":"G2 F2/paired Cout signed8 weights/direct Cin",
                  "purpose":"E065 independently verifies Conv2-only signed8 weights/bias at the mixed precision point with13-image deltaPSNR=-0.07589037644656216dB. Pair those coefficients with shared ten-bit activations in one27x10 DSP product, with borrow correction but no coefficient residual restoration. Combine continuous integer Winograd Conv1 and direct Conv3; this avoids the failed uniformINT8 gate and full exact10 packing's large residual fabric cost.",
                  "changes":"Independent continuous Winograd clone. Conv2 weights/bias use signed8 fraction7, its accumulator21 bits fraction15, and the output boundary removes8 bits to the existing ten-bit activation fraction7. All other layer types and padding remain unchanged. A packed pair is decoded every product; no accumulated low-field bound is assumed.",
                  "estimates":{"DSP":4128//folds+3,"Conv1_DSP":2304//folds,
                               "Conv2_DSP":1024//folds,"Conv3_DSP":800//folds,
                               "BRAM18K":155,"URAM":0,"LUT":65000 if folds == 8 else 100000,
                               "T":folds,"latency_cycles":65025*folds+100000,
                               "basis":"OneDSP per transformed Conv1 product or packed Conv2 pair; direct Conv3 products. Continuous engine65025*T projection plus100000 cycles for load/startup/reorder. Retain72 raster FIFO BRAM18K and direct gather storage. LUT budget removes residual[-2,2] restoration from Conv2 but retains signed unpacking, wide transformed-window FIFO, inverse34-bit arithmetic, and registered direct Conv3 reduction. T4 is an explicit LUT-feasibility probe, not assumed deployable."},
                  "interpretation":"Compare mixed Conv2 packing against W11's direct uniform10 layers and C07's full residual packing. Require every butterfly output bit to equal E065, retaining its original rounding/overflow/quantization boundaries. Final selected points must rerun all13 images before RTL/route verification.",
                  "conclusion":"Rank only the unchanged0.1dB precision gate and resource-feasible results; never infer accuracy from a DSP count."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_"+config["name"]],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
