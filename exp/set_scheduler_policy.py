#!/usr/bin/env python3
"""Apply the user's explicit two-task override without disturbing active leases."""
import json
from memory_scheduler import Scheduler
from run_exp import ROOT, utc, write_json


def main():
    scheduler = Scheduler(ROOT)
    with scheduler.state() as state:
        state.update(user_two_jobs=True, floor_gib=.5)
        state["user_override"] = {
            "time": utc(),
            "instruction": "User explicitly requested two concurrent tasks despite memory reservations.",
            "max_tasks": 2, "floor_gib": .5,
            "budgets_are_advisory": True,
            "oom_fallback": "serial", "pressure_victim": "newest task",
        }
        record = {"override": state["user_override"], "tasks_at_change": state["tasks"],
                  "registered_budgets": state["budgets"]}
    write_json(ROOT / "experiments/user_two_job_policy.json", record)
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
