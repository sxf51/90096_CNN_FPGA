#!/usr/bin/env python3
"""Apply an explicit user scheduling policy without disturbing active leases."""
import json
import argparse
from memory_scheduler import Scheduler
from run_exp import ROOT, utc, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("two-jobs", "one-heavy"), default="two-jobs")
    args = parser.parse_args()
    scheduler = Scheduler(ROOT)
    with scheduler.state() as state:
        state.update(user_two_jobs=True, floor_gib=.5)
        state["one_heavy"] = args.mode == "one-heavy"
        state["user_override"] = {
            "time": utc(),
            "instruction": "User explicitly requested two concurrent tasks despite memory reservations.",
            "max_tasks": 2, "floor_gib": .5,
            "budgets_are_advisory": True,
            "oom_fallback": "serial", "pressure_victim": "newest task",
        }
        record = {"override": state["user_override"], "tasks_at_change": state["tasks"],
                  "registered_budgets": state["budgets"]}
        if state["one_heavy"]:
            state["user_override"].update(
                instruction="User revised policy to one heavy impl/cosim plus memory-bounded csynth/C simulation.",
                max_tasks=4, max_heavy=1, max_light=3, light_available_floor_gib=2,
                pressure_victim="newest light task, otherwise the heavy task",
                budgets_are_advisory=False)
    write_json(ROOT / "experiments" / ("one_heavy_policy.json" if args.mode == "one-heavy" else "user_two_job_policy.json"), record)
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
