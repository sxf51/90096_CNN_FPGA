#!/usr/bin/env python3
"""Preplan combinations using the passing P/W primitive evidence."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    base = json.loads((ROOT / "exp/configs/W06.json").read_text())
    for exp_id, folds, pack2, lutram_rows in (("C01",4,True,False), ("C02",4,False,False),
                                               ("C03",8,True,True)):
        c1 = 2304//folds
        c2 = 2048//(folds*(2 if pack2 else 1))
        c3 = 800//(2*folds)
        estimate_lut = c1*105+c2*(240 if pack2 else 75)+c3*170+18000+(10000 if lutram_rows else 0)
        config = {**base, "id": exp_id, "name": f"wino_packing_T{folds}_{'all' if pack2 else 'conv3'}",
                  "series": "C", "stage": "arch_c", "design": "designs/combination_network", "T": folds,
                  "defines": {**base["defines"], "EXP_T": folds, "EXP_PACK_C2": int(pack2), "EXP_ROW_LUTRAM": int(lutram_rows)},
                  "purpose": "Combine exact G2 Winograd Conv1 with exact10 adjacent-pixel packing Conv3" +
                             (" and exact10 output-channel packing Conv2." if pack2 else "; Conv2 keeps direct DSP products.") +
                             " P07 proves residual correction and W01 proves exact inverse scaling. The passing w10a10 precision is preserved. Full uniform INT8 quantization is excluded because of its measured5.18dB loss.",
                  "changes": "Independent combination source, original runtime weight/signature contract. Optional LUTRAM raster row FIFOs trade72 BRAM18K for about10000 LUT.",
                  "estimates": {"DSP": c1+c2+c3+3, "Conv1_DSP": c1, "Conv2_DSP": c2, "Conv3_DSP": c3,
                                "BRAM18K": 169 if lutram_rows else 241, "URAM": 0, "LUT": estimate_lut,
                                "T": folds, "latency_cycles": 16384*(4*folds+24)+60000,
                                "basis": "Measured1 DSP/exact10 packed pair and16 DSP/F2 PE. Paper products/pixel2304+2048+800; packing halves only chosen layers. Transform/reorder/fold fill cost24 cycles/tile and60000 startup/load allowance. LUT estimates include generic coefficient residuals and borrowed-field repairs; hardware excess is a possible outcome."},
                  "unroll": "integer Winograd/"+ ("paired Cout" if pack2 else "Cout") +"/adjacent pixels",
                  "interpretation": "Compare requested932/1188/466 MAC DSP budgets with actual resources, especially residual fabric, transformed accumulation and raster buffering. More than20% deviation needs per-module evidence.",
                  "conclusion": "Accept a combination only with exact outputs, resource limits and measured II; preserve negative feasibility evidence."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_"+config["name"]],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
