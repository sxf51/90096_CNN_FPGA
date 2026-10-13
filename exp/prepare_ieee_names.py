#!/usr/bin/env python3
"""Preplan distinct HLS object basenames after an observed linker collision."""
import json
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def main():
    for exp_id,parent in (("F20","F18"),("F21","F19")):
        base = json.loads((ROOT / "exp/configs" / (parent+".json")).read_text())
        config = {**base,"id":exp_id,"name":base["name"]+"_unique_object",
                  "design":"designs/ieee_decode_pe_r2",
                  "purpose":"F18 reaches linking but both syn.file and tb.file have basename ieee_decode.cpp. Vitis generates the same obj/ieee_decode.o twice and reports duplicate ieee_decode_pe symbols. Rename only the independent design translation unit to kernel.cpp; arithmetic, ports, checker and estimates remain identical. "+base["purpose"],
                  "changes":"Independent source copy of ieee_decode_pe_r1 with kernel.cpp basename; no expression or quantization change. Preserve F18/F19 linker failures."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,"plan_unique_hls_object"],cwd=ROOT,check=True)


if __name__ == "__main__":
    main()
