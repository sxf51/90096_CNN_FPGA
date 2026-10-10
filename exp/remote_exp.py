#!/usr/bin/env python3
"""Run an experiment on the existing SSH host, then archive and commit locally."""
import argparse
import csv
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
from run_exp import ROOT, FIELDS, append_log, check_protected, check_plan, ensure_results_schema, lock, write_json


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
    if not exp_id.startswith("E"):
        check_plan(config, ROOT / "experiments" / (exp_id + "_" + config["name"]))
    if exp_id.startswith("E") and config["stage"] == 5:
        expected = {"E036", "E037", "E038", "E039", "E040", "E041", "E042", "E043",
                    "E045", "E048", "E057", "E058", "E059", "E063", "E064", "E067"}
        while True:
            with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
                completed = {row["id"] for row in csv.DictReader((ROOT / "experiments/results.csv").open(newline=""))}
            if expected <= completed:
                break
            time.sleep(5)
        if exp_id in {"E051", "E052", "E053", "E054", "E055"}:
            while "E060" not in completed:
                time.sleep(5)
                with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
                    completed = {row["id"] for row in csv.DictReader((ROOT / "experiments/results.csv").open(newline=""))}
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id,
                    "prepare_" + config["name"]], cwd=ROOT, check=True)
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
    if not exp_id.startswith("E"):
        plan_folder = ROOT / "experiments" / (exp_id + "_" + config["name"])
        subprocess.run(rsync + [str(plan_folder), args.host + ":" + args.remote_root + "/experiments/"], check=True)
        manifest = ROOT / "experiments/phase1_design_checksums.txt"
        subprocess.run(rsync + [str(manifest), args.host + ":" + args.remote_root + "/experiments/"], check=True)
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
        ensure_results_schema(results)
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
    if config.get("series"):
        subprocess.run([sys.executable,str(ROOT / "exp/update_arch_progress.py")],cwd=ROOT,check=True)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id, config["name"]], cwd=ROOT, check=True)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
