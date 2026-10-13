#!/usr/bin/env python3
"""Preplan fixed-tripcount Winograd scheduling after W07's bound inflation."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def save(config):
    plan(config)
    subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),config["id"],"plan_"+config["name"]],cwd=ROOT,check=True)


def main():
    base = json.loads((ROOT / "exp/configs/W08.json").read_text())
    for exp_id,folds,continuous,clock in (("W10",16,False,4),("W11",8,True,4),
                                         ("W12",16,True,4),("W13",8,True,3.33)):
        save({**base,"id":exp_id,"name":f"fixed_tiles_T{folds}_{'allcontinuous' if continuous else 'c1only'}_{str(clock).replace('.','p')}ns",
              "design":"designs/winograd_continuous","T":folds,"clock":clock,
              "defines":{**base["defines"],"EXP_T":folds,"EXP_ALL_CONTINUOUS":int(continuous)},
              "purpose":"W07 reports5715601 Conv1 cycles because the conditional nested264x264 scan takes its82-cycle tile branch at every position in the worst-case bound, even though only16384 tiles exist. Separate transformed-window production from a fixed16384*(4*T)II1 MAC loop; emit four-pixel blocks through a separate raster-row distributor. "+
                        ("Use continuous direct Conv2/Conv3 and online padding as well, so their nested drains cannot dominate." if continuous else "Keep direct Conv2/Conv3 and old padding unchanged to isolate the Conv1 scheduling change."),
              "changes":"New independent Winograd source based on the passing r1 layer. Shallow1728-bit transformed-window and2560-bit tile FIFOs use LUTRAM. Exact34-bit inverse arithmetic and all layer casts are retained.",
              "estimates":{"DSP":5152//folds+3,"Conv1_DSP":2304//folds,"Conv2_DSP":2048//folds,"Conv3_DSP":800//folds,
                           "BRAM18K":155 if continuous else 241,"URAM":0,"LUT":72000 if folds == 8 else 55000,
                           "T":folds,"latency_cycles":65025*folds+100000 if continuous else 2100000,
                           "basis":"W07 proves exact layer outputs,144 MAC DSP and82 worst-case cycles per scanned location, with raster reorder65027 cycles. Fixed engine iterations represent16384 actual tiles; extra511 positions are discarded. Keep72 row-FIFO BRAM18K; continuous mode removes72 shallow-FIFO BRAM and packs the pad row to save14 more. LUT budget adds4288 wide shallow FIFO bits and the continuous Conv3 window FIFO."},
              "interpretation":"Compare fixed-tripcount MAC latency against W07's conservative branch bound. Separate actual throughput improvement from report-bound tightening, and require final finite-FIFO RTL cycles for the selected points.",
              "conclusion":"Rank only exact resource-feasible frame results; retain both nested and continuous evidence."})
    combination = json.loads((ROOT / "exp/configs/C06.json").read_text())
    save({**combination,"id":"C07","name":"continuous_wino_packing_T8","design":"designs/combination_continuous",
          "defines":{**combination["defines"],"EXP_ALL_CONTINUOUS":0},
          "purpose":"Replace the combination's inflated conditional Conv1 schedule with fixed-tile Winograd, retaining exact10 packed Conv2/Conv3 and LUTRAM row FIFOs. This isolates how much its previous worst-case cycle bound hides, without assuming residual fabric cost disappears.",
          "changes":"Independent combination r1 clone with transformed-window/fixed-MAC/tile-distribution Conv1. Packed layers and odd-column handling stay identical.",
          "estimates":{"DSP":469,"Conv1_DSP":288,"Conv2_DSP":128,"Conv3_DSP":50,
                       "BRAM18K":169,"URAM":0,"LUT":105000,"T":8,"latency_cycles":2100000,
                       "basis":"P11 already shows exact10 residuals cause165606 full-network LUT atT8, so105000 LUT for two packed layers plus Winograd is an explicit infeasibility hypothesis. Fixed16384 tile engine removes W07's fourfold branch-bound inflation; remaining nested packed Conv3 controls the2.1M cycle estimate."},
          "interpretation":"Measure report-bound improvement separately from resource feasibility; preserve exact10 residual and signed borrowing semantics.",
          "conclusion":"Do not accept a faster report if LUT/FF/DSP caps fail."})


if __name__ == "__main__":
    main()
