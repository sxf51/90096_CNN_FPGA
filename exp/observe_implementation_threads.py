#!/usr/bin/env python3
"""Archive read-only Vivado thread evidence without opening or changing a project."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import xml.etree.ElementTree as ET
from run_exp import ROOT, append_log, utc, write_json


def observe(work):
    folder = work / "hls/impl/verilog"
    project = folder / "project.xpr"
    runs = ET.parse(project).findall(".//Run")
    selected = [run for run in runs if run.get("Id") == "impl_1"]
    if len(selected) != 1:
        raise RuntimeError("Need one implementation run in the saved project")
    run = selected[0]
    strategy = run.find("Strategy/StratHandle")
    hooks = [step.get("PreStepTclHook") for step in run.findall(".//Step")
             if step.get("Id") == "opt_design" and step.get("PreStepTclHook")]
    scripts = list((folder / "project.runs/impl_1").glob("*.tcl"))
    if len(scripts) != 1:
        raise RuntimeError("Need one generated implementation child script")
    script = scripts[0]
    text = script.read_text()
    initial = re.findall(r"^\s*set_param general\.maxThreads (\d+)\s*$", text, re.MULTILINE)
    logs = list(script.parent.glob("*.vdi"))
    if len(logs) != 1 or not initial:
        raise RuntimeError("Missing generated child thread initialization or runtime log")
    raw = logs[0].read_bytes()
    runtime = raw.decode(errors="replace")
    reports = re.findall(r"EXP_VIVADO_IMPL_THREADS general=(\d+) synth=(\d+)", runtime)
    limits = re.findall(r"Multithreading enabled for phys_opt_design using a maximum of (\d+) CPUs", runtime)
    return {"time": utc(), "project_sha256": hashlib.sha256(project.read_bytes()).hexdigest(),
            "strategy": strategy.get("Name") if strategy is not None else None,
            "opt_pre_hooks": hooks,
            "child_script": str(script.relative_to(work)),
            "child_script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
            "child_initial_max_threads": [int(value) for value in initial],
            "child_runtime_thread_reports": [{"general": int(general), "synth": int(synth)}
                                             for general, synth in reports],
            "phys_opt_cpu_limits": [int(value) for value in limits],
            "runtime_log_sha256_at_observation": hashlib.sha256(raw).hexdigest(),
            "runtime_log_bytes_at_observation": len(raw),
            "scope": "Read-only snapshot; configured thread limits are distinct from measured CPU utilization. "
                     "No Vivado process, RTL change, project save or rerouting was performed."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--remote-root", default="/home/lipuze/amdprojects/90096_CNN_FPGA")
    args = parser.parse_args()
    if not re.fullmatch(r"[SGPWCF]\d{2,}", args.id):
        parser.error("Need an architecture experiment ID")
    if args.probe:
        print(json.dumps(observe(ROOT / "workspace/exp_runs" / args.id)))
        return
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes"]
    subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), str(Path(__file__).resolve()),
                    "xiaoxin-ubuntu:" + args.remote_root + "/exp/"], check=True)
    command = "cd " + shlex.quote(args.remote_root) + "\n" + shlex.join(
        ["python3", "exp/observe_implementation_threads.py", args.id, "--probe"])
    evidence = json.loads(subprocess.check_output(ssh + ["xiaoxin-ubuntu", command], text=True))
    config = json.loads((ROOT / "exp/configs" / (args.id + ".json")).read_text())
    archive = ROOT / "experiments" / (args.id + "_" + config["name"])
    if not (archive / "plan.json").is_file():
        raise RuntimeError("Missing committed experiment plan")
    evidence["planned_max_threads"] = config.get("implementation_threads", 1)
    target = archive / "implementation/thread_observation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, evidence)
    append_log(args.id + ": read-only child thread snapshot; planned=" + str(evidence["planned_max_threads"]) +
               "; initialized=" + str(evidence["child_initial_max_threads"]) +
               "; runtime_hook=" + str(evidence["child_runtime_thread_reports"]) +
               "; phys_opt_CPU_limits=" + str(evidence["phys_opt_cpu_limits"]) + ". See implementation/thread_observation.json.")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
