#!/usr/bin/env python3
"""Serial remote queue, preserving failures and committing each completed run."""
import subprocess
import sys
from run_exp import ROOT


for exp_id in sys.argv[1:]:
    result = subprocess.run([sys.executable, str(ROOT / "exp/remote_exp.py"),
                             str(ROOT / "exp/configs" / (exp_id + ".json"))], cwd=ROOT)
    print("QUEUE", exp_id, "exit", result.returncode, flush=True)
