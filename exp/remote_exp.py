#!/usr/bin/env python3
"""Run an experiment on the existing SSH host, then archive and commit locally."""
import argparse
import csv
import json
from pathlib import Path
import shlex
import subprocess
import sys
from run_exp import ROOT, FIELDS, append_log, check_protected, lock, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--host", default="xiaoxin-ubuntu")
    parser.add_argument("--ssh-config", type=Path, default=ROOT.parent / "ssh-config")
    parser.add_argument("--remote-root", default="/home/lipuze/amdprojects/90096_CNN_FPGA")
    args = parser.parse_args()
    check_protected()
    config = json.loads(args.config.read_text())
    exp_id = config["id"]
    config["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    scratch = ROOT / "workspace/exp_runs/_transfer"
    scratch.mkdir(parents=True, exist_ok=True)
    transfer = scratch / (exp_id + ".json")
    write_json(transfer, config)
    ssh = ["ssh", "-F", str(args.ssh_config), "-o", "BatchMode=yes"]
    rsync = ["rsync", "-az", "--exclude=__pycache__", "--exclude=AGENTS.md", "--exclude=agent.md", "-e", shlex.join(ssh)]
    for folder in ("exp", "designs"):
        if (ROOT / folder).exists():
            subprocess.run(rsync + [str(ROOT / folder), args.host + ":" + args.remote_root + "/"], check=True)
    subprocess.run(["scp", "-F", str(args.ssh_config), str(transfer),
                    args.host + ":" + args.remote_root + "/exp/configs/" + exp_id + ".json"], check=True)
    command = "cd " + shlex.quote(args.remote_root) + "\npython3 exp/run_exp.py --config " + shlex.quote("exp/configs/" + exp_id + ".json")
    result = subprocess.run(ssh + [args.host, command])
    folder = exp_id + "_" + config["name"]
    subprocess.run(rsync + [args.host + ":" + args.remote_root + "/experiments/" + folder,
                           str(ROOT / "experiments") + "/"], check=True)
    archive = ROOT / "experiments" / folder
    metrics = json.loads((archive / "metrics.json").read_text())
    results = ROOT / "experiments/results.csv"
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        rows = list(csv.DictReader(results.open(newline=""))) if results.exists() else []
        if any(row["id"] == exp_id for row in rows):
            raise RuntimeError("Duplicate experiment row")
        with results.open("a", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=FIELDS)
            if not rows:
                writer.writeheader()
            writer.writerow(metrics)
        append_log(f"{exp_id}: {config['name']}; status={metrics['status']}; "
                   f"latency_ms_est={metrics['latency_ms_est'] or 'unknown'}; {metrics['notes']}")
    check_protected()
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id, config["name"]], cwd=ROOT, check=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
