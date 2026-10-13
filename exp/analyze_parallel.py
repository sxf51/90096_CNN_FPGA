#!/usr/bin/env python3
"""Summarize actual task overlap after the explicit two-job authorization."""
import bisect
import csv
from datetime import datetime
import itertools
import json
from analyze_arch import write_csv
from host_memory import cpu_summary, swap_summary
from run_exp import ROOT

GIB_KIB = 1048576


def epoch(sample):
    return datetime.fromisoformat(sample["time"]).timestamp()


def overlap(first, second):
    start = max(first["admission"]["started"], second["admission"]["started"])
    finish = min(first["admission"]["finished"], second["admission"]["finished"])
    if finish <= start:
        return None
    left = [row for row in first["samples"] if start <= epoch(row) <= finish]
    right = [row for row in second["samples"] if start <= epoch(row) <= finish]
    times = [epoch(row) for row in right]
    pairs = []
    for sample in left:
        stamp = epoch(sample)
        position = bisect.bisect_left(times, stamp)
        candidates = [index for index in (position-1, position) if 0 <= index < len(right)]
        if candidates:
            nearest = min(candidates, key=lambda index: abs(times[index]-stamp))
            if abs(times[nearest]-stamp) <= 4:
                pairs.append((sample, right[nearest]))
    samples = sorted(left + right, key=epoch)
    return {
        "first_id": first["admission"]["id"], "second_id": second["admission"]["id"],
        "first_kind": first["admission"]["kind"], "second_kind": second["admission"]["kind"],
        "start_epoch": start, "finish_epoch": finish, "overlap_seconds": finish-start,
        "aligned_samples": len(pairs),
        "peak_combined_process_tree_rss_GiB": max(
            (float(a["task_tree_rss_kib"])+float(b["task_tree_rss_kib"]))/GIB_KIB
            for a, b in pairs) if pairs else None,
        "minimum_available_GiB": min(float(row["available_kib"])/GIB_KIB for row in samples)
        if samples else None,
        "cpu_busy_pct": cpu_summary(samples).get("cpu_busy_pct") if len(samples) >= 2 else None,
        **swap_summary(samples),
        "notes": "RSS sum includes shared mappings; MemAvailable is a host measurement. "
                 "Paired task samples are at most4seconds apart. Overlap ends at process exit, including failure.",
    }


def main():
    policy = json.loads((ROOT / "experiments/user_two_job_policy.json").read_text())
    changed = datetime.fromisoformat(policy["override"]["time"]).timestamp()
    tasks = []
    for path in sorted((ROOT / "experiments").glob("*_*/*_admission.json")):
        admission = json.loads(path.read_text())
        if admission["finished"] <= changed:
            continue
        phase = admission.get("phase", admission["kind"])
        telemetry = path.parent / (phase + "_host_memory.csv")
        with telemetry.open(newline="") as stream:
            samples = list(csv.DictReader(stream))
        if not samples or "task_tree_rss_kib" not in samples[0]:
            raise RuntimeError("Missing per-task memory evidence: " + str(telemetry))
        tasks.append({"admission": admission, "samples": samples, "path": path})
    tasks.sort(key=lambda task: task["admission"]["started"])
    jobs = []
    for task in tasks:
        admission, samples = task["admission"], task["samples"]
        jobs.append({"id": admission["id"], "kind": admission["kind"],
                     "phase": admission.get("phase", admission["kind"]),
                     "start_epoch": admission["started"], "finish_epoch": admission["finished"],
                     "operation_seconds": admission["finished"]-admission["started"],
                     "policy_change_epoch": changed, "exit_code": admission["exit_code"],
                     "peak_process_tree_rss_GiB": max(float(row["task_tree_rss_kib"])/GIB_KIB for row in samples),
                     "minimum_available_GiB": min(float(row["available_kib"])/GIB_KIB for row in samples),
                     "oom_delta": (admission["oom_after"]-admission["oom_before"]
                                   if admission.get("oom_before") is not None and admission.get("oom_after") is not None
                                   else None), "memory_pressure": json.dumps(admission.get("memory_pressure")),
                     **swap_summary(samples),
                     "admission_path": str(task["path"].relative_to(ROOT))})
    pairs = [record for first, second in itertools.combinations(tasks, 2)
             if (record := overlap(first, second)) is not None]
    write_csv(ROOT / "experiments/parallel_jobs.csv", jobs, list(jobs[0]) if jobs else ["id"])
    write_csv(ROOT / "experiments/parallel_overlap.csv", pairs, list(pairs[0]) if pairs else ["first_id", "second_id"])
    print("Measured parallel tasks:", len(jobs), "; overlapping pairs:", len(pairs))


if __name__ == "__main__":
    main()
