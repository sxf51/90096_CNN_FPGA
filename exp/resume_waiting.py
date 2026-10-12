#!/usr/bin/env python3
"""Replace only an unadmitted cosimulation worker with the current scheduler."""
import argparse
import json
import os
from pathlib import Path
import signal
import time
from memory_scheduler import Scheduler, process_start
from run_exp import ROOT, check_plan
from verify_exp import run_verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    exp_id = config["id"]
    work = ROOT / "workspace/exp_runs" / exp_id
    archive = ROOT / "experiments" / (exp_id + "_" + config["name"])
    check_plan(config, archive)
    if config.get("operation") != "cosim" or not config.get("memory_scheduler"):
        raise RuntimeError("Only waiting scheduled cosim workers can be migrated")
    scheduler = Scheduler(ROOT)
    with scheduler.state() as state:
        if any(task["id"] == exp_id for task in state["tasks"].values()):
            raise RuntimeError("Task already admitted; leave its active process intact")
        if (work / "cosim.console.log").exists():
            raise RuntimeError("Tool already launched; leave its workspace intact")
        events = [json.loads(line) for line in (archive / "scheduler_events.jsonl").read_text().splitlines()]
        if not events or any(item["event"] != "waiting" for item in events):
            raise RuntimeError("Worker is not exclusively waiting for admission")
        pid = int((work / ".run.lock").read_text().split()[0])
        command = (Path("/proc") / str(pid) / "cmdline").read_bytes().split(b"\0")
        if b"exp/run_exp.py" not in command or ("exp/configs/" + exp_id + ".json").encode() not in command:
            raise RuntimeError("Waiting PID does not match this experiment")
        started = process_start(pid)
        os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 10
    while process_start(pid) == started and time.monotonic() < deadline:
        time.sleep(.1)
    return run_verification(config, resume_waiting=True)


if __name__ == "__main__":
    raise SystemExit(main())
