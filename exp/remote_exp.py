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
from run_exp import ROOT, FIELDS, append_log, check_protected, check_plan, ensure_results_schema, lock, plan_digest, write_json


def record_archive(config, archive):
    metrics = json.loads((archive / "metrics.json").read_text())
    exp_id = config["id"]
    if set(metrics) != set(FIELDS) or metrics["id"] != exp_id or metrics["md_path"] != archive.name + "/" + exp_id + ".md":
        raise RuntimeError("Unexpected completed archive identity or results schema")
    if not exp_id.startswith("E"):
        plan = json.loads((archive / "plan.json").read_text())
        if plan["config_sha256"] != plan_digest(config):
            raise RuntimeError("Completed archive differs from the local planned configuration")
        purpose = (archive / (exp_id + ".md")).read_text().split(
            "## 1. Purpose and hypothesis / 目的与假设\n\n", 1)[1].split("\n\n## 2.", 1)[0]
        if purpose != plan["purpose_section"]:
            raise RuntimeError("Completed archive differs from its pre-implementation purpose")
    results = ROOT / "experiments/results.csv"
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        ensure_results_schema(results)
        rows = []
        if results.exists():
            with results.open(newline="") as stream:
                rows = list(csv.DictReader(stream))
        existing = [row for row in rows if row["id"] == exp_id]
        if existing:
            serialized = {key: "" if value is None else str(value) for key, value in metrics.items()}
            if len(existing) != 1 or existing[0] != serialized:
                raise RuntimeError("Existing result conflicts with the completed archive")
            print("ALREADY_ARCHIVED", exp_id, flush=True)
            return metrics
        with results.open("a", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=FIELDS)
            if not rows:
                writer.writeheader()
            writer.writerow(metrics)
        append_log(f"{exp_id}: {config['name']}; status={metrics['status']}; "
                   f"latency_ms_est={metrics['latency_ms_est'] or 'unknown'}; {metrics['notes']}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--host", default="xiaoxin-ubuntu")
    parser.add_argument("--ssh-config", type=Path, default=ROOT.parent / "ssh-config")
    parser.add_argument("--remote-root", default="/home/lipuze/amdprojects/90096_CNN_FPGA")
    parser.add_argument("--collect-only", action="store_true",
                        help="Retrieve a completed remote archive without launching or uploading a run")
    args = parser.parse_args()
    check_protected()
    config = json.loads(args.config.read_text())
    exp_id = config["id"]
    if not exp_id.startswith("E") and not args.collect_only:
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
    ssh = ["ssh", "-F", str(args.ssh_config), "-o", "BatchMode=yes"]
    rsync = ["rsync", "-az", "--exclude=__pycache__", "--exclude=AGENTS.md", "--exclude=agent.md", "-e", shlex.join(ssh)]
    folder = exp_id + "_" + config["name"]
    archive = ROOT / "experiments" / folder
    collected = args.collect_only and (archive / "metrics.json").is_file()
    if args.collect_only:
        if not collected:
            work = args.remote_root + "/workspace/exp_runs/" + exp_id
            command = "if test -e " + shlex.quote(work + "/.run.lock") + "; then exit 1; fi\n"
            command += "test -f " + shlex.quote(args.remote_root + "/experiments/" + folder + "/metrics.json")
            subprocess.run(ssh + [args.host, command], check=True)
        result_code = 0
    else:
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id,
                        "prepare_" + config["name"]], cwd=ROOT, check=True)
        config["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        scratch = ROOT / "workspace/exp_runs/_transfer"
        scratch.mkdir(parents=True, exist_ok=True)
        transfer = scratch / (exp_id + ".json")
        write_json(transfer, config)
        for path in ("exp", "designs"):
            if (ROOT / path).exists():
                subprocess.run(rsync + [str(ROOT / path), args.host + ":" + args.remote_root + "/"], check=True)
        if not exp_id.startswith("E"):
            plan_folder = ROOT / "experiments" / folder
            subprocess.run(rsync + [str(plan_folder), args.host + ":" + args.remote_root + "/experiments/"], check=True)
            manifest = ROOT / "experiments/phase1_design_checksums.txt"
            subprocess.run(rsync + [str(manifest), args.host + ":" + args.remote_root + "/experiments/"], check=True)
        if config.get("implementation_template_archive"):
            subprocess.run(rsync + [str(ROOT / config["implementation_template_archive"]),
                                   args.host+":"+args.remote_root+"/experiments/"],check=True)
        subprocess.run(["scp", "-F", str(args.ssh_config), str(transfer),
                        args.host + ":" + args.remote_root + "/exp/configs/" + exp_id + ".json"], check=True)
        command = "cd " + shlex.quote(args.remote_root) + "\npython3 exp/run_exp.py --config " + shlex.quote("exp/configs/" + exp_id + ".json")
        result_code = subprocess.run(ssh + [args.host, command]).returncode
    if not collected:
        subprocess.run(rsync + [args.host + ":" + args.remote_root + "/experiments/" + folder,
                               str(ROOT / "experiments") + "/"], check=True)
    record_archive(config, archive)
    check_protected()
    if config.get("series"):
        subprocess.run([sys.executable,str(ROOT / "exp/update_arch_progress.py")],cwd=ROOT,check=True)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id, config["name"]], cwd=ROOT, check=True)
    return result_code


if __name__ == "__main__":
    sys.exit(main())
