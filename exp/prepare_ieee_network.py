#!/usr/bin/env python3
"""Preplan full-network use of the measured exact IEEE output converter."""
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
    parent = next((ROOT / "experiments").glob("F13_*/config.json")).parent
    probe = next((ROOT / "experiments").glob("F20_*/config.json")).parent
    measured = json.loads((probe / "metrics.json").read_text())
    if not (measured["csim_pass"] is True and measured["bit_exact"] is True and
            measured["DSP"] == 0 and measured["ii_ok"] is True):
        raise RuntimeError("Exact zero-DSP conversion has not been demonstrated")
    if args.copy_source:
        for exp_id in ("F22", "F23"):
            folder = next((ROOT / "experiments").glob(exp_id+"_*/plan.json"))
            subprocess.run(["git", "cat-file", "-e", "HEAD:"+str(folder.relative_to(ROOT))],
                           cwd=ROOT, check=True)
        target = ROOT / "designs/continuous_ieee_v1"
        if target.exists():
            raise RuntimeError("Design exists; use a new name")
        shutil.copytree(parent / "source", target)
        shutil.copyfile(probe / "source/ieee_decode.h", target / "ieee_decode.h")
        check_protected()
        print(target)
        return
    base = json.loads((parent / "plan.json").read_text())["configuration"]
    parent_metrics = json.loads((parent / "metrics.json").read_text())
    for exp_id, clock, label in (("F22", 3, "3ns"), ("F23", 2.5, "2p5ns")):
        config = {**base, "id":exp_id, "name":"continuous_ieee_T16_"+label,
                  "design":"designs/continuous_ieee_v1", "clock":clock,
                  "control_experiment":"F13",
                  "purpose":"F20 exhausts all signed ten-bit output values across three orderings with exact binary32 equality and measures zero DSP, 242 LUT, 52 FF and 2.051ns. F13's output writer uses three DSP and the 3.239ns sitofp critical path. Replace only raw-to-float output encoding with the proven sign/exponent/significand construction, retain online replicate padding and Conv3 rotation, and test a faster target clock. Every butterfly output bit must retain the first-phase precision reference; no precision or weight-contract change.",
                  "changes":"Independent copy of the archived F13 design and F20 converter header. Include the converter before size macros and replace numeric::decode only; all MAC, load, streams and quantization remain fixed. Target clock is the second changed parameter.",
                  "estimates":{"DSP":parent_metrics["DSP"]-3,
                               "Conv1_DSP":324, "Conv2_DSP":128, "Conv3_DSP":50,
                               "BRAM18K":parent_metrics["BRAM18K"], "URAM":0,
                               "LUT":parent_metrics["LUT"]+500, "FF":parent_metrics["FF"]+1000,
                               "T":16, "latency_cycles":65025*16+100000,
                               "basis":"F13 measured 505DSP/73BRAM18K/68903LUT/106661FF; removing the three-DSP output scale predicts 502DSP. Keep F13 LUT/FF plus scheduling/control allowances because the PE omits AXI logic and the higher clock may add registers. Reserve 100000 cycles beyond 65025*T for load/start/drain. A 2.051ns PE path does not imply the full network meets either clock; use max(target,estimated) and later RTL/route evidence."},
                  "interpretation":"Compare achieved II, each module's clock and top resource counts against F13. The output converter may cease to be the critical path; memory/address, carried addition or input casts may then dominate. Record any over20percent estimate deviation from parsed reports. Two-frame equality precedes synthesis eligibility.",
                  "conclusion":"Keep only exact resource-feasible points in final ranking; selected points require all supplied images, actual route and two-frame RTL verification."}
        plan(config)
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id,
                        "plan_exact_ieee_network"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
