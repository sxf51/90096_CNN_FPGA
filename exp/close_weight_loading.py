#!/usr/bin/env python3
"""Audit and close the current WS0-WS4 queue, preserving historical deferred IDs."""
import csv
import json
import shlex
import subprocess
import sys
from pathlib import Path
from close_arch import audit_archives, audit_checksums, audit_verification_reports
from run_exp import ROOT, append_log, check_protected, lock, utc, write_json


def main():
    if subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() != "exp/explore-arch":
        raise RuntimeError("Wrong closure branch")
    check_protected()
    state_path = ROOT / "experiments/weight_loading_state.json"
    state = json.loads(state_path.read_text())
    required = set(state.get("experiment_ids", []))
    if state.get("ready_to_close") is not True or not {"F89", "F26", "F27"} <= required:
        raise RuntimeError("Workstream is not ready to close; record all decisions and experiment IDs first")
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    ids = [row["id"] for row in rows]
    if len(ids) != len(set(ids)) or required-set(ids):
        raise RuntimeError("Duplicate or unarchived workstream experiments: "+", ".join(sorted(required-set(ids))))
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    probe = "pgrep -af " + shlex.quote(r"exp/run_exp\.py|unwrapped/.*/vivado|vitis-run.*--(csim|cosim|impl)|v\+\+.*--mode hls")
    active = subprocess.run(ssh+[probe], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if active.returncode not in {0, 1}:
        raise RuntimeError("Could not check remote experiment processes: "+active.stderr)
    if active.returncode == 0:
        raise RuntimeError("Remote experiments are still active:\n"+active.stdout)
    remote_code = ("import sys,json\nsys.path.insert(0,'exp')\n"
                   "from close_arch import audit_checksums\nprint(json.dumps(audit_checksums()))")
    remote = json.loads(subprocess.check_output(ssh+[
        "cd "+shlex.quote(remote_root)+"\npython3 -c "+shlex.quote(remote_code)], text=True))
    checks = [{"location": location, **record}
              for location, records in (("local", audit_checksums()), ("remote", remote)) for record in records]
    archive_audit = audit_archives(rows)
    report_audit = audit_verification_reports(rows)
    large = [str(path.relative_to(ROOT)) for folder in ("exp", "designs", "experiments")
             for path in (ROOT / folder).rglob("*") if path.is_file() and path.stat().st_size > 50_000_000]
    if large:
        raise RuntimeError("Files above50MB require exclusion/manual decision: "+", ".join(large))
    if subprocess.check_output(["git", "ls-files", "*AGENTS.md", "*agent.md"], cwd=ROOT).strip():
        raise RuntimeError("Local rules must remain untracked")
    subprocess.run(["git", "check-ignore", "-q", "AGENTS.md"], cwd=ROOT, check=True)
    write_json(ROOT / "experiments/weight_loading_audit.json", {
        "time": utc(), "experiment_ids": sorted(required), "checks": checks,
        "architecture_archives": archive_audit, "verification_report_archives": report_audit,
        "deferred": state.get("deferred", []), "board_validation": False, "pushed": False,
        "full_set14": False, "files_above50MB": large})
    state.update(next="Review section6 decisions, missing comic and any failed route/RTL gates; use measured physical bottlenecks for the next independent design. No board acceptance or push.")
    write_json(state_path, state)
    for name in ("analyze_arch.py", "analyze_weight_loading.py", "update_arch_progress.py",
                 "summarize_weight_loading.py", "summarize_arch.py"):
        extra = state.get("loader_ids", []) if name == "analyze_weight_loading.py" else []
        subprocess.run([sys.executable, str(ROOT / "exp" / name), *extra], cwd=ROOT, check=True)
    plotting_python = ROOT / "workspace/exp_runs/_tools/venv/bin/python"
    subprocess.run([str(plotting_python), str(ROOT / "exp/architectures/archive_wino_weights.py")], cwd=ROOT, check=True)
    for script in sorted((ROOT / "exp/plots").glob("*.py")):
        subprocess.run([str(plotting_python), str(script)], cwd=ROOT, check=True)
    state["closed_at"] = utc()
    write_json(state_path, state)
    progress = ROOT / "experiments/PROGRESS.md"
    text = progress.read_text()
    if "## Weight Loading Closed" not in text:
        progress.write_text(text+"\n## Weight Loading Closed\n\nAll current workstream operations are archived, including failures/timeouts. Source/data checksums match locally/remotely; report provenance is audited and all figures are regenerated. See [weight_loading_audit.json](weight_loading_audit.json) and [WEIGHT_LOADING.md](WEIGHT_LOADING.md). Historical deferred IDs remain deferred. No board validation or push.\n")
    append_log("F99: WS0-WS4 operations archived and audited; "+str(len(required))+" workstream records, local/remote protected checksums and report SHA256 verified; all plots regenerated. Failures remain explicit; no board acceptance or push.")
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), "F99", "weight_loading_workstream_closure"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
