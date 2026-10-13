#!/usr/bin/env python3
"""Wait for original final operations, then serialize independent route retries."""
import csv
import json
import subprocess
import sys
import time
from run_exp import ROOT, lock


def main():
    selection = json.loads((ROOT / "experiments/final_selection.json").read_text())
    while True:
        with lock(ROOT / "workspace/exp_runs/.results.lock",wait_timeout=120):
            ids = {row["id"] for row in csv.DictReader((ROOT / "experiments/results.csv").open(newline=""))}
        pending = set(selection["original_queue"])-ids
        if not pending:
            break
        time.sleep(40)
    subprocess.run([sys.executable,str(ROOT / "exp/run_queue.py"),
                    *selection["implementation_retry_queue"]],cwd=ROOT,check=True)
    print("SERIAL_IMPLEMENTATION_RETRIES_COMPLETED",flush=True)


if __name__ == "__main__":
    main()
