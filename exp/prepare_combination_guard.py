#!/usr/bin/env python3
"""Preserve C07 and preplan an independent correction to its Conv2 guard."""
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
    target = ROOT / "designs/combination_continuous_r1"
    if args.build:
        if not (ROOT / "exp/configs/C12.json").exists() or target.exists():
            raise RuntimeError("Committed plan required; existing designs cannot be overwritten")
        shutil.copytree(ROOT / "designs/combination_continuous", target)
        path = target / "srcnn.cpp"
        text = path.read_text()
        marker = "static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,"
        if text.count(marker) != 2:
            raise RuntimeError("Unexpected C07 Conv2 branches")
        path.write_text(text.replace(marker, "#if EXP_PACK_C2\n" + marker, 1))
        check_protected()
        print(target)
        return
    base = json.loads((ROOT / "exp/configs/C07.json").read_text())
    config = {**base, "id": "C12", "name": "continuous_wino_packing_T8_guard_retry",
              "design": "designs/combination_continuous_r1",
              "purpose": "C07 failed preprocessing because the packed Conv2 branch lacks its opening #if EXP_PACK_C2. Restore the matching guard in an independent source copy, preserving both branches and every numerical expression. The unchanged paper estimates remain deliberately above the LUT cap. " + base["purpose"],
              "changes": "Independent C07 copy with one opening conditional directive before packed conv2_stream. Preserve C07's failed source and diagnostics; no arithmetic, stream, weight or precision change."}
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), "C12",
                    "plan_independent_conv2_guard_retry"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
