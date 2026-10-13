#!/usr/bin/env python3
"""Increase future cosim reservations from completed process-tree measurements."""
import argparse
import csv
import hashlib
import json
import math
from memory_scheduler import GIB_KIB, Scheduler
from reproduce_exp import archived
from rtl_acceptance import accepted_cosim
from run_exp import ROOT, utc, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent")
    args = parser.parse_args()
    archive = archived(args.parent)
    metrics = json.loads((archive / "metrics.json").read_text())
    config = json.loads((archive / "config.json").read_text())
    if not accepted_cosim(metrics, config):
        raise RuntimeError("Budget calibration requires a completed accepted cosimulation")
    destination = archive / "cosim_memory_budget_revision.json"
    if destination.exists():
        raise RuntimeError("Budget revision already recorded; inspect it before repeating")
    paths = sorted(archive.glob("cosim*_host_memory.csv"))
    records = []
    for path in paths:
        rows = list(csv.DictReader(path.open(newline="")))
        if not rows or any(not row.get("task_tree_rss_kib") for row in rows):
            raise RuntimeError("Missing complete process-tree memory samples")
        records.append({"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "samples": len(rows), "peak_tree_rss_GiB": max(
                            float(row["task_tree_rss_kib"]) for row in rows) / GIB_KIB})
    if not records:
        raise RuntimeError("No cosimulation process-tree measurements")
    peak = max(row["peak_tree_rss_GiB"] for row in records)
    if not math.isfinite(peak) or peak <= 0:
        raise RuntimeError("Invalid measured memory peak")
    with Scheduler(ROOT).state() as state:
        if any(task["kind"] == "cosim" for task in state["tasks"].values()):
            raise RuntimeError("Cannot revise cosim registration while a cosim lease is active")
        before = state["budgets"]["cosim"]
        after = max(before, math.ceil(peak * 1.10 * 2) / 2)
        record = {"time": utc(), "parent": args.parent, "old_budget_GiB": before,
                  "new_budget_GiB": after, "peak_tree_rss_GiB": peak,
                  "margin_ratio": 1.10, "round_up_GiB": 0.5, "sources": records,
                  "tasks_unchanged": state["tasks"], "policy_unchanged": {
                      key: state.get(key) for key in ("one_heavy", "total_gib", "floor_gib", "serial_after_oom")}}
        state["budgets"]["cosim"] = after
        state["cosim_budget_evidence"] = str(destination.relative_to(ROOT))
        write_json(destination, record)
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
