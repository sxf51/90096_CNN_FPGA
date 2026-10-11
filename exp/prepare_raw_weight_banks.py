#!/usr/bin/env python3
"""Preplan isolated Winograd raw-weight banking controls from measured evidence."""
import argparse
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT, check_protected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    check_protected()
    target = ROOT / "designs/winograd_rawbank_v1"
    if args.build:
        if not (ROOT / "exp/configs/W17.json").exists() or target.exists():
            raise RuntimeError("Committed plans required; existing designs cannot be overwritten")
        shutil.copytree(ROOT / "designs/winograd_continuous_r2", target)
        path = target / "srcnn.cpp"
        text = path.read_text()
        for directive in ("#pragma HLS ARRAY_PARTITION variable=w1 cyclic factor=C1_OC dim=1\n",
                          "#pragma HLS ARRAY_PARTITION variable=raw cyclic factor=WOC dim=1\n"):
            if text.count(directive) != 1:
                raise RuntimeError("Unexpected raw-weight partition directive")
            text = text.replace(directive, "", 1)
        path.write_text(text)
        check_protected()
        print(target)
        return
    for exp_id, parent, lut, ff in (("W17", "W14", 110000, 128000),
                                   ("W18", "W15", 90000, 85000)):
        base = json.loads((ROOT / "exp/configs" / (parent + ".json")).read_text())
        config = {**base, "id": exp_id, "name": "narrow_raw_banks_T" + str(base["T"]),
                  "design": "designs/winograd_rawbank_v1",
                  "purpose": "W09 and C12 measure transform_weights=40992 LUT/48601 FF at T8, with 48533 register FF and 19305 instance LUT in C12. W10 at T16 measures10459 LUT/495 FF. Original coefficients are read only during the sequential load/transform stage, so they need one output-channel bank rather than Conv1 MAC-lane banking. Remove only raw output-channel partitioning, retain all81 tap banks and every transformed compute bank. Test whether deeper64-entry LUTRAM avoids short-bank register/multiplexer growth; attribution remains a hypothesis until synthesis.",
                  "changes": "Independent split-window Winograd copy; remove output-channel partition directives for raw w1 and layer-only raw. Keep transformed weights, all arithmetic, runtime parameter loading, precision, online padding and FIFO schedules identical.",
                  "estimates": {**base["estimates"], "DSP": 648 if base["T"] == 8 else 326,
                                "LUT": lut, "FF": ff,
                                "basis": "Keep the parent's MAC counts, memory and65025*T+100000 cycle allowance. T8 starts from measured W09 total135496LUT/148761FF and subtracts the30533LUT/48106FF transform delta against W10, then reserves about5000LUT/27000FF for continuous engine/FIFO changes. T16 allows90000LUT/85000FF because the measured T16 transform is already small. Raw cache is64*81*10=51840bits, about810 six-input LUTRAM bit lanes at depth64, before selectors. Both LUT estimates deliberately exceed81984; no feasible result is assumed."},
                  "interpretation": "Compare transform_weights resources and top totals against W14/W15 and the measured W09/W10 controls. Distinguish raw-bank depth from transformed compute banks; check whether scheduling II or load cycles changed. A resource saving alone cannot establish frame feasibility or RTL throughput.",
                  "conclusion": "Retain exact measured controls even if LUT remains infeasible. Use actual banks/registers to decide whether further weight-loading changes have value."}
        plan(config)
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id,
                        "plan_raw_weight_bank_control"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
