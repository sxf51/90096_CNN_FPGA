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
from run_exp import ROOT, append_log, check_protected, lock, utc, write_json


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
    ssh_config = ROOT.parent / "ssh-config"
    host = "xiaoxin-ubuntu"
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    subprocess.run(["scp","-F",str(ssh_config),str(ROOT / "exp/close_arch.py"),
                    host+":"+remote_root+"/exp/close_arch.py"],check=True)
    command = "cd "+shlex.quote(remote_root)+"\npython3 exp/close_arch.py --checksums-only"
    remote = json.loads(subprocess.check_output(["ssh","-F",str(ssh_config),"-o","BatchMode=yes",host,command],text=True))
    checks = [{"location":location,**record} for location,records in (("local",audit_checksums()),("remote",remote))
              for record in records]
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
