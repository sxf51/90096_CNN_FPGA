#!/usr/bin/env python3
"""Wait for exploration evidence, then run the frozen final-verification plans."""
import csv
import importlib
import subprocess
import sys
import time
import prepare_final_arch
from run_exp import ROOT, lock


def main():
    while True:
        with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
            rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
        missing = set(importlib.reload(prepare_final_arch).REQUIRED)-{row["id"] for row in rows}
        if not missing:
            break
        print("FINAL_WAIT "+", ".join(sorted(missing)), flush=True)
        time.sleep(40)
    subprocess.run([sys.executable,str(ROOT / "exp/prepare_final_arch.py")],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),"F80","freeze_final_selection"],cwd=ROOT,check=True)
    import json
    selection = json.loads((ROOT / "experiments/final_selection.json").read_text())
    subprocess.run([sys.executable,str(ROOT / "exp/run_queue.py"),*selection["queue"]],cwd=ROOT,check=True)
    print("FINAL_VERIFICATION_QUEUE_COMPLETED",flush=True)


if __name__ == "__main__":
    main()
