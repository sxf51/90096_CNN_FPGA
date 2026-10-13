#!/usr/bin/env python3
"""Accept the measured WS-0 overlap trial before enabling hardware concurrency."""
import argparse
import csv
import json
from memory_scheduler import GIB_KIB, Scheduler
from run_exp import ROOT, number, utc, write_json


def validate(ids=("F32", "F33", "F34")):
    rows, stages, failures = [], {}, []
    for exp_id in ids:
        archive = next((ROOT / "experiments").glob(exp_id + "_*"))
        metrics = json.loads((archive / "metrics.json").read_text())
        config = json.loads((archive / "config.json").read_text())
        if metrics.get("csim_pass") is not True or metrics.get("bit_exact") is not True:
            failures.append(exp_id + " C simulation/exact gate")
        if exp_id != ids[2] and (metrics.get("ii_ok") is not True or
                                 metrics.get("status") not in {"pass", "provisional"}):
            failures.append(exp_id + " synthesis/II gate")
        if exp_id == ids[2] and (config["validation"].get("image_count") != 13 or
                                  number(metrics.get("delta_psnr")) is None or
                                  number(metrics["delta_psnr"]) < -.1):
            failures.append(exp_id + " complete course Set14 quality gate")
        for path in sorted(archive.glob("*_admission.json")):
            admission = json.loads(path.read_text())
            kind = admission["kind"]
            memory_file = archive / (kind + "_host_memory.csv")
            samples = list(csv.DictReader(memory_file.open(newline="")))
            peak = max(float(row["task_tree_rss_kib"]) for row in samples) / GIB_KIB
            available = min(float(row["available_kib"]) for row in samples) / GIB_KIB
            row = {"id": exp_id, "kind": kind, "start_epoch": admission["started"],
                   "finish_epoch": admission["finished"], "samples": len(samples),
                   "peak_task_rss_gib": peak, "registered_budget_gib": admission["budget_gib"],
                   "minimum_available_gib": available,
                   "peak_within_budget": peak <= admission["budget_gib"],
                   "floor_ok": available >= 2, "oom_delta": admission["oom_after"] - admission["oom_before"]}
            rows.append(row)
            if not row["peak_within_budget"] or not row["floor_ok"] or row["oom_delta"] or admission["memory_pressure"]:
                failures.append(exp_id + " " + kind + " memory/exit gate")
            stages[exp_id, kind] = row
    overlap_stages = [stages[ids[0], "csynth"], stages[ids[1], "csynth"], stages[ids[2], "csim"]]
    overlap = min(row["finish_epoch"] for row in overlap_stages) - max(row["start_epoch"] for row in overlap_stages)
    if overlap <= 0:
        failures.append("No measured simultaneous two-synthesis/C-simulation overlap")
    result = {"time": utc(), "passed": not failures, "overlap_seconds": max(0, overlap),
              "failures": failures, "measurements": rows}
    suffix = "" if ids[0] == "F32" else "_retry"
    write_json(ROOT / ("experiments/memory_validation" + suffix + ".json"), result)
    with (ROOT / ("experiments/memory_validation" + suffix + ".csv")).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    ids = ("F36", "F37", "F38") if args.retry else ("F32", "F33", "F34")
    result = validate(ids)
    if args.enable:
        if not result["passed"]:
            raise RuntimeError("Controlled trial failed; hardware concurrency stays disabled")
        with Scheduler(ROOT).state() as state:
            if state["serial_after_oom"] or state["tasks"]:
                raise RuntimeError("Cannot enable concurrency while tasks or unresolved OOM remain")
            state["parallel_validated"] = True
            state["validation"] = {"ids": list(ids), "time": result["time"],
                                   "overlap_seconds": result["overlap_seconds"]}
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
