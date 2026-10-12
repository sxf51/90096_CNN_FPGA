#!/usr/bin/env python3
"""Temporarily pause unadmitted workers so an existing priority job runs next."""
import argparse
import json
import os
from pathlib import Path
import signal
import time

from memory_scheduler import Scheduler, process_start
from run_exp import ROOT, utc, write_json


def waiting_worker(scheduler, state, exp_id):
    if any(task["id"] == exp_id for task in state["tasks"].values()):
        raise RuntimeError("Task already admitted: " + exp_id)
    work = scheduler.directory / exp_id
    pid = int((work / ".run.lock").read_text().split()[0])
    command = (Path("/proc") / str(pid) / "cmdline").read_bytes().split(b"\0")
    if b"exp/run_exp.py" not in command or ("exp/configs/" + exp_id + ".json").encode() not in command:
        raise RuntimeError("Waiting PID does not match this experiment: " + exp_id)
    paths = list((ROOT / "experiments").glob(exp_id + "_*/scheduler_events.jsonl"))
    if len(paths) != 1:
        raise RuntimeError("Require one waiting worker event log: " + exp_id)
    events = [json.loads(line) for line in paths[0].read_text().splitlines()]
    if not events or events[-1]["event"] != "waiting":
        raise RuntimeError("Worker is not waiting for admission: " + exp_id)
    started = process_start(pid)
    if started is None:
        raise RuntimeError("Worker exited during inspection: " + exp_id)
    return {"id": exp_id, "pid": pid, "process_start": started,
            "waiting_phase": events[-1]["phase"]}


def resume(records):
    for record in records:
        if process_start(record["pid"]) == record["process_start"]:
            try:
                os.kill(record["pid"], signal.SIGCONT)
            except ProcessLookupError:
                pass


def pause(scheduler, ids):
    records = []
    # The scheduler lock prevents admission while waiting workers are inspected and stopped.
    with scheduler.state() as state:
        candidates = [waiting_worker(scheduler, state, exp_id) for exp_id in ids]
        try:
            for record in candidates:
                records.append(record)
                os.kill(record["pid"], signal.SIGSTOP)
        except BaseException:
            resume(records)
            raise
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("priority")
    parser.add_argument("waiters", nargs="+")
    parser.add_argument("--timeout", type=float, default=18000)
    args = parser.parse_args()
    if args.priority in args.waiters or len(set(args.waiters)) != len(args.waiters) or args.timeout <= 0:
        raise RuntimeError("Require a separate priority job and distinct waiting jobs")
    scheduler = Scheduler(ROOT)
    archives = list((ROOT / "experiments").glob(args.priority + "_*/plan.json"))
    if len(archives) != 1 or (archives[0].parent / "metrics.json").exists():
        raise RuntimeError("Priority job is absent or already completed")
    work = scheduler.directory / args.priority
    priority_pid = int((work / ".run.lock").read_text().split()[0])
    priority_start = process_start(priority_pid)
    if priority_start is None:
        raise RuntimeError("Priority worker is not running")
    priority_command = (Path("/proc") / str(priority_pid) / "cmdline").read_bytes().split(b"\0")
    if (b"exp/run_exp.py" not in priority_command or
            ("exp/configs/" + args.priority + ".json").encode() not in priority_command):
        raise RuntimeError("Priority worker PID does not match this experiment")
    evidence = archives[0].parent / "priority_waiters.json"
    if evidence.exists():
        raise RuntimeError("Priority hold already recorded; inspect it before repeating")
    record = {"priority": args.priority, "started": utc(), "pid": os.getpid(),
              "timeout_seconds": args.timeout, "waiters": [],
              "basis": "User requested C18 priority; retain the active heavy task and pause only unadmitted workers. Resume automatically when the priority worker finishes or this supervisor exits."}
    def interrupted(signum, _frame):
        raise RuntimeError("Priority supervisor interrupted: " + str(signum))
    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(signum, interrupted)
    started = time.monotonic()
    records = []
    try:
        records = pause(scheduler, args.waiters)
        record["waiters"] = records
        write_json(evidence, record)
        print("EXP_PRIORITY_HOLD", args.priority, json.dumps(records), flush=True)
        while not (archives[0].parent / "metrics.json").exists():
            if process_start(priority_pid) != priority_start:
                raise RuntimeError("Priority worker exited before archiving a result")
            if time.monotonic() - started >= args.timeout:
                raise RuntimeError("Priority wait timeout")
            time.sleep(3)
        record["result"] = "priority_result_archived"
    except BaseException as error:
        record["result"] = str(error)
        raise
    finally:
        resume(records)
        record["released"] = utc()
        record["elapsed_seconds"] = time.monotonic() - started
        write_json(evidence, record)
        print("EXP_PRIORITY_RELEASE", args.priority, record["result"], flush=True)


if __name__ == "__main__":
    main()
