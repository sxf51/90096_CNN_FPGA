#!/usr/bin/env python3
"""Close the completed architecture study with reproducible audits and figures."""
import argparse
import csv
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path
from prepare_final_arch import REQUIRED
from run_exp import ROOT, append_log, check_protected, lock, number, plan_digest, utc, write_json


def audit_checksums():
    records = []
    for name in ("checksums.txt", "phase1_design_checksums.txt"):
        manifest = ROOT / "experiments" / name
        values = []
        for line in manifest.read_text().splitlines():
            expected,path = line.split("  ",1)
            actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            values.append({"path":path,"expected_sha256":expected,"actual_sha256":actual,"pass":expected == actual})
        record = {"manifest":name,"checked_files":len(values),"pass":all(value["pass"] for value in values),"files":values}
        if not record["pass"]:
            raise RuntimeError("Protected checksum mismatch: "+name)
        records.append(record)
    return records


def audit_archives(rows):
    records = []
    for row in rows:
        if not row["series"]:
            continue
        archive = ROOT / "experiments" / Path(row["md_path"]).parent
        config = json.loads((archive / "config.json").read_text())
        plan = json.loads((archive / "plan.json").read_text())
        if plan_digest(plan["configuration"]) != plan["config_sha256"]:
            raise RuntimeError("Plan fingerprint mismatch: "+row["id"])
        text = (ROOT / "experiments" / row["md_path"]).read_text()
        purpose = text.split("## 1. Purpose and hypothesis / 目的与假设\n\n",1)[1].split("\n\n## 2.",1)[0]
        if purpose != plan["purpose_section"]:
            raise RuntimeError("Paper estimates changed after planning: "+row["id"])
        metrics = json.loads((archive / "metrics.json").read_text())
        for key,value in metrics.items():
            measured,listed = number(value),number(row.get(key))
            equal = measured == listed if measured is not None else str(value) == str(row.get(key))
            if not equal:
                raise RuntimeError("CSV/archive mismatch: "+row["id"]+" "+key)
        source_hashes = config.get("source_sha256", {})
        if config.get("operation"):
            parent = ROOT / "experiments" / config["parent_metrics"]["md_path"].split("/")[0]
            source_hashes = config["parent_config"].get("source_sha256", {})
            source_folder = parent / "source"
        else:
            source_folder = archive / "source"
        for name,digest in source_hashes.items():
            if hashlib.sha256((source_folder / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Archived source hash mismatch: "+row["id"]+" "+name)
        for name,digest in config.get("testbench_sha256", {}).items():
            if hashlib.sha256((archive / "testbench" / name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Archived testbench hash mismatch: "+row["id"]+" "+name)
            original = subprocess.check_output(["git", "show", config["frozen_source_commit"]+":"+name], cwd=ROOT)
            if hashlib.sha256(original).hexdigest() != digest:
                raise RuntimeError("Replayed testbench differs from recorded Git source: "+row["id"]+" "+name)
        if not config.get("operation") and number(row.get("latency_cycles")) is not None:
            expected = number(row["latency_cycles"])*max(number(row["clock_target_ns"]),number(row["clock_est_ns"]))/1e6
            if abs(expected-number(row["latency_ms_est"])) > 1e-9:
                raise RuntimeError("Latency formula mismatch: "+row["id"])
        records.append({"id":row["id"],"plan_unchanged":True,"csv_matches_archive":True,
                        "archived_source_files_checked":len(source_hashes),
                        "archived_testbench_files_checked":len(config.get("testbench_sha256", {}))})
    return records


def audit_verification_reports(rows):
    checks = []
    for row in rows:
        archive = ROOT / "experiments" / Path(row["md_path"]).parent
        config = json.loads((archive / "config.json").read_text())
        operation = config.get("operation")
        if operation not in {"impl", "cosim"}:
            continue
        reports = config.get("verification_reports", [])
        evidence = (reports + config.get("implementation_files", []) + config.get("implementation_driver_template_files", []) + config.get("verification_diagnostics", []) +
                    config.get("verification_profiles", []))
        if config.get("host_failure"):
            evidence.append(config["host_failure"])
        if row["status"] == operation + "_complete":
            if not reports:
                raise RuntimeError("Completed verification has no archived source reports: "+row["id"])
            names = {Path(record["archived_file"]).stem for record in reports}
            if operation == "impl" and any(not any(name.endswith(suffix) for name in names)
                    for suffix in ("timing_routed", "utilization_routed")):
                raise RuntimeError("Missing routed timing/resource archive: "+row["id"])
        for record in evidence:
            path = archive / record["archived_file"]
            if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
                raise RuntimeError("Verification source report hash mismatch: "+row["id"])
            relative = str(path.relative_to(ROOT))
            ignored = subprocess.run(["git", "check-ignore", "--no-index", "-q", relative], cwd=ROOT)
            if ignored.returncode != 1:
                raise RuntimeError("Verification source report is ignored or ignore check failed: "+relative)
            subprocess.run(["git", "ls-files", "--error-unmatch", "--", relative], cwd=ROOT,
                           stdout=subprocess.DEVNULL, check=True)
        checks.append({"id":row["id"], "operation":operation, "status":row["status"],
                       "reports_checked":len(reports), "sha256_pass":True,
                       "additional_evidence_files_checked":len(evidence)-len(reports),
                       "git_visible_and_tracked":True})
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checksums-only",action="store_true")
    args = parser.parse_args()
    if args.checksums_only:
        print(json.dumps(audit_checksums()))
        return
    branch = subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip()
    if branch != "exp/explore-arch":
        raise RuntimeError("Wrong closure branch")
    check_protected()
    with lock(ROOT / "workspace/exp_runs/.results.lock",wait_timeout=120):
        rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    selection = json.loads((ROOT / "experiments/final_selection.json").read_text())
    expected = set(REQUIRED)|set(selection["queue"])
    missing = expected-{row["id"] for row in rows}
    if missing:
        raise RuntimeError("Required jobs are still pending: "+", ".join(sorted(missing)))
    if len({row["id"] for row in rows}) != len(rows):
        raise RuntimeError("Duplicate experiment IDs")
    for row in rows:
        archive = ROOT / "experiments" / Path(row["md_path"]).parent
        config = json.loads((archive / "config.json").read_text())
        if (config.get("operation") == "cosim" and
                config.get("verification", {}).get("rtl_status") == "Pass" and
                not config.get("verification_profiles")):
            subprocess.run([sys.executable, str(ROOT / "exp/archive_cosim_profiles.py"),
                            row["id"], "--pull"], cwd=ROOT, check=True)
            subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"),
                            row["id"], "archive_missing_rtl_profile_counters"], cwd=ROOT, check=True)
    ssh_config = ROOT.parent / "ssh-config"
    host = "xiaoxin-ubuntu"
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    subprocess.run(["scp","-F",str(ssh_config),str(ROOT / "exp/close_arch.py"),
                    host+":"+remote_root+"/exp/close_arch.py"],check=True)
    command = "cd "+shlex.quote(remote_root)+"\npython3 exp/close_arch.py --checksums-only"
    remote = json.loads(subprocess.check_output(["ssh","-F",str(ssh_config),"-o","BatchMode=yes",host,command],text=True))
    checks = [{"location":location,**record} for location,records in (("local",audit_checksums()),("remote",remote))
              for record in records]
    archives = audit_archives(rows)
    verification_reports = audit_verification_reports(rows)
    large = [str(path.relative_to(ROOT)) for folder in ("exp", "designs", "experiments")
             for path in (ROOT / folder).rglob("*") if path.is_file() and path.stat().st_size>50_000_000]
    if large:
        raise RuntimeError("Files above50MB require exclusion/manual decision: "+", ".join(large))
    tracked_rules = subprocess.check_output(["git","ls-files","*AGENTS.md","*agent.md"],cwd=ROOT,text=True).strip()
    if tracked_rules:
        raise RuntimeError("Local rules must remain untracked")
    subprocess.run(["git","check-ignore","-q","AGENTS.md"],cwd=ROOT,check=True)
    write_json(ROOT / "experiments/architecture_audit.json",{
        "time":utc(),"branch":branch,"full_set14":False,"checks":checks,
        "architecture_archives":archives,
        "verification_report_archives":verification_reports,
        "required_exploration_records":len(REQUIRED),"final_verification_records":len(selection["queue"]),
        "completed_records":len(rows),"files_above50MB":large,"tracked_rules":tracked_rules,
        "board_validation":False,"pushed":False})
    for script in ("analyze_arch.py","update_arch_progress.py"):
        subprocess.run([sys.executable,str(ROOT / "exp" / script)],cwd=ROOT,check=True)
    python = ROOT / "workspace/exp_runs/_tools/venv/bin/python"
    subprocess.run([str(python),str(ROOT / "exp/architectures/archive_wino_weights.py")],cwd=ROOT,check=True)
    for script in sorted((ROOT / "exp/plots").glob("*.py")):
        subprocess.run([str(python),str(script)],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT / "exp/summarize_arch.py")],cwd=ROOT,check=True)
    state_path = ROOT / "experiments/arch_state.json"
    state = json.loads(state_path.read_text())
    state.update(closed_at=utc(),next="Resolve missing comic, any routed/cosim failures, DDR scratch/weight contracts and board integration.")
    write_json(state_path,state)
    progress = ROOT / "experiments/PROGRESS.md"
    text = progress.read_text()
    text += "\n## Closed\n\nArchitecture exploration and all planned final operations are archived, including failures/timeouts. Both checksum manifests match locally and remotely, plots are regenerated, and ARCH_SUMMARY.md records actual route/RTL evidence. No push or board acceptance. Next: "+state["next"]+"\n"
    progress.write_text(text)
    with lock(ROOT / "workspace/exp_runs/.results.lock",wait_timeout=120):
        append_log("F99: architecture study closed; "+str(len(REQUIRED))+" exploration and "+str(len(selection["queue"]))+
                   " final validation/route/cosim records archived; both checksum manifests verified locally/remotely; plots regenerated; missing comic keeps precision acceptance provisional; no board validation or push.")
    check_protected()
    subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),"F99","architecture_exploration_closure"],cwd=ROOT,check=True)
    print("ARCHITECTURE_CLOSED",flush=True)


if __name__ == "__main__":
    main()
