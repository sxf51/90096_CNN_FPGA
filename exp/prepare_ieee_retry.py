#!/usr/bin/env python3
"""Preplan SDK-namespace and explicit-width fixes without rewriting failures."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    for exp_id,parent in (("F18","F16"),("F19","F17")):
        base = json.loads((ROOT / "exp/configs" / (parent+".json")).read_text())
        config = {**base,"id":exp_id,"name":base["name"]+"_sdk_retry",
                  "design":"designs/ieee_decode_pe_r1",
                  "purpose":"F16 fails compilation: this installed utils/x_hls_utils.h exposes fp_struct globally, and unary-minus ap_int<11> returns ap_int<12>, making a conditional with ap_int<11> ambiguous. Use the actual SDK symbol and explicit sign/magnitude branches. This is a source-typing fix with the same paper estimates and exact arithmetic. "+base["purpose"],
                  "changes":"Independent ieee_decode_pe_r1 source. Global fp_struct<float>, explicit widened signed magnitude and an explicit zero-exponent branch. Preserve F16/F17 attempted sources and diagnostics."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_ieee_sdk_retry"],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
