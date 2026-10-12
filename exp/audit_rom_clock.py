#!/usr/bin/env python3
"""Audit measured docs/0005 evidence and separately identify unmeasured plans."""
import argparse
import csv
import hashlib
import json
import shlex
import subprocess
from close_arch import audit_archives, audit_checksums, audit_verification_reports
from run_exp import ROOT, check_protected, lock, plan_digest, utc, write_json


def inventory(state, rows):
    ids = [row["id"] for row in rows]
    requested = state["experiment_ids"]
    if len(ids) != len(set(ids)) or len(requested) != len(set(requested)):
        raise RuntimeError("Duplicate result or workstream experiment IDs")
    measured = sorted(set(requested) & set(ids))
    unmeasured = sorted(set(requested) - set(ids))
    waiting = set(state.get("waiting_for_memory", []))
    active = {exp_id for jobs in state.get("session_jobs", {}).values() for exp_id in jobs}
    unexplained = set(unmeasured) - waiting - active - set(state.get("deferred", []))
    if unexplained:
        raise RuntimeError("Unmeasured experiments have no recovery state: " + ", ".join(sorted(unexplained)))
    if waiting & set(measured):
        raise RuntimeError("Measured IDs still listed as unlaunched for memory")
    return measured, unmeasured


def audit_pending(state, unmeasured):
    records = []
    for exp_id in unmeasured:
        plans = list((ROOT / "experiments").glob(exp_id + "_*/plan.json"))
        if len(plans) != 1:
            raise RuntimeError("Expected one pending plan: " + exp_id)
        path = plans[0]
        planned = json.loads(path.read_text())
        config = json.loads((ROOT / "exp/configs" / (exp_id + ".json")).read_text())
        if plan_digest(config) != planned["config_sha256"]:
            raise RuntimeError("Pending config fingerprint differs: " + exp_id)
        recorded = subprocess.check_output(["git", "show", "HEAD:" + str(path.relative_to(ROOT))], cwd=ROOT)
        if hashlib.sha256(recorded).digest() != hashlib.sha256(path.read_bytes()).digest():
            raise RuntimeError("Pending paper plan differs from committed version: " + exp_id)
        waiting = exp_id in state.get("waiting_for_memory", [])
        if waiting and config.get("operation") != "impl":
            raise RuntimeError("Unexpected class of unlaunched memory-blocked plan: " + exp_id)
        records.append({"id": exp_id, "plan_sha256": hashlib.sha256(recorded).hexdigest(),
                        "operation": config.get("operation", "csim/csynth"),
                        "unlaunched_for_memory": waiting,
                        "condition": state.get("planned_conditions", {}).get(exp_id),
                        "has_measured_result": False})
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="store_true", help="Audit while jobs remain active; never mark work complete")
    args = parser.parse_args()
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() != "exp/explore-arch":
        raise RuntimeError("Wrong audit branch")
    check_protected()
    state = json.loads((ROOT / "experiments/rom_clock_state.json").read_text())
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    probe = "pgrep -af " + shlex.quote(r"exp/run_exp\.py|unwrapped/.*/vivado|vitis-run.*--(csim|cosim|impl)|v\+\+.*--mode hls")
    running = subprocess.run(ssh + [probe], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if running.returncode not in {0, 1}:
        raise RuntimeError("Remote process query failed: " + running.stderr)
    if running.returncode == 0 and not args.snapshot:
        raise RuntimeError("Remote experiments remain active; use --snapshot for an interim audit")
    remote_code = "import sys,json\nsys.path.insert(0,'exp')\nfrom close_arch import audit_checksums\nprint(json.dumps(audit_checksums()))"
    remote = json.loads(subprocess.check_output(ssh + [
        "cd " + shlex.quote(remote_root) + "\npython3 -c " + shlex.quote(remote_code)], text=True))
    with lock(ROOT / "workspace/exp_runs/.commit.lock", wait_timeout=120):
        with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
            rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
        measured, unmeasured = inventory(state, rows)
        pending = audit_pending(state, unmeasured)
        sources = audit_archives(rows)
        reports = audit_verification_reports(rows)
    large = [str(path.relative_to(ROOT)) for folder in ("exp", "designs", "experiments")
             for path in (ROOT / folder).rglob("*") if path.is_file() and path.stat().st_size > 50_000_000]
    if large:
        raise RuntimeError("Files above50MB need exclusion or human decision: " + ", ".join(large))
    if subprocess.check_output(["git", "ls-files", "*AGENTS.md", "*agent.md"], cwd=ROOT).strip():
        raise RuntimeError("Local collaboration rules must remain untracked")
    subprocess.run(["git", "check-ignore", "-q", "AGENTS.md"], cwd=ROOT, check=True)
    checks = [{"location": location, **record}
              for location, records in (("local", audit_checksums()), ("remote", remote)) for record in records]
    record = {"time": utc(), "mode": "snapshot" if args.snapshot else "idle_audit",
              "measured_workstream_ids": measured, "unmeasured_plans": pending,
              "all_operations_archived": not unmeasured, "remote_jobs_active": running.returncode == 0,
              "remote_processes": running.stdout.splitlines(), "checks": checks,
              "architecture_archives": sources, "verification_report_archives": reports,
              "files_above50MB": large, "board_validation": False, "pushed": False,
              "test_set": "Set14 (complete13-image course-provided set)", "resource_policy": "routed"}
    write_json(ROOT / "experiments/rom_clock_audit.json", record)
    print(json.dumps({key: record[key] for key in ("time", "mode", "all_operations_archived", "remote_jobs_active")}, indent=2))
    print("Measured workstream records:", len(measured), "; unmeasured plans:", ", ".join(unmeasured))


if __name__ == "__main__":
    main()
