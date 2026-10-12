#!/usr/bin/env python3
"""Preplan the controlled scheduler validation and the identical-RTL clock probe."""
import argparse
import json
from plan_arch import plan
from run_exp import ROOT


def prepare_ws0():
    for exp_id, parent, csim_only in (("F32", "F28", False), ("F33", "W21", False),
                                      ("F34", "F96", True)):
        archive = next((ROOT / "experiments").glob(parent + "_*/metrics.json"))
        metrics = json.loads(archive.read_text())
        original = json.loads(archive.with_name("plan.json").read_text())["configuration"]
        config = {**original, "id": exp_id, "name": "ws0_memory_control_" + parent,
                  "series": "F", "stage": "rom_clock_ws0", "scope": "frame",
                  "control_experiment": parent, "csim_only": csim_only,
                  "memory_scheduler": True, "controlled_parallel_validation": True,
                  "required_image_count": 13, "resource_policy": "routed",
                  "purpose": "Controlled WS-0 memory admission validation using unchanged " + parent +
                             " source/arithmetic. Run F32 and F33 synthesis concurrently with F34 C simulation. "
                             "Measure individual process-tree RSS, overlapping task timestamps, MemAvailable and CPU. "
                             "Do not enable general hardware concurrency until this trial passes. No architecture speedup is claimed.",
                  "changes": "Only the runner scheduling and telemetry change; reuse the immutable parent design and flags.",
                  "interpretation": "Compare reports with the parent and observed peak RSS with the registered budget. "
                                    "Overlap must be measured; numerical, II and timeout checks remain unchanged.",
                  "conclusion": "Enable budgeted concurrency only after both syntheses and C simulation pass, "
                                "measured peaks fit their budgets and host available memory stays at least 2 GiB."}
        config.pop("synthesis_after", None)
        config["estimates"] = {key: metrics.get(key) for key in
                               ("DSP", "BRAM18K", "URAM", "LUT", "FF", "latency_cycles")}
        if csim_only:
            measured = json.loads(next((ROOT / "experiments").glob("W21_*/metrics.json")).read_text())
            config["estimates"].update({key: measured[key] for key in config["estimates"]})
        config["estimates"].update(T=original["T"], basis="Measured unchanged parent HLS counts; "
                                   "registered synth budget 2.5 GiB each, C simulation 1 GiB. "
                                   "Total trial reservation 6 GiB, below 13 GiB with a 2 GiB available-memory floor.")
        plan(config)


def prepare_clock():
    original = json.loads((ROOT / "exp/configs/W22.json").read_text())
    config = {**original, "id": "W23", "name": "ws_clock_strategy_4p5_W21",
              "stage": "rom_clock_wsC1", "implementation_clock_ns": 4.5,
              "implementation_template": "F98", "implementation_threads": 4,
              "implementation_strategy": "Performance_Explore",
              "memory_scheduler": True, "resource_policy": "routed", "required_image_count": 13,
              "purpose": "WS-C step 1: implement identical W21 RTL at 4.5 ns with Performance_Explore, "
                         "including its post-route physical optimization. Verify supported strategy properties "
                         "with this Vivado installation before launch. Compare independent timing, physical "
                         "resources, four-thread placement/routing memory and runtime with W22/F98. "
                         "Synthesis remains one thread. Preserve F97 exact two-frame runtime-parameter evidence.",
              "changes": "Change only physical clock/strategy/thread settings in a fresh workspace; "
                         "check every RTL/init hash against W21 and F98. No HLS rerun or source change.",
              "interpretation": "Compare actual route with W22, report timing/control fanout and memory. "
                                "Clock, strategy and thread settings all change; elapsed differences do not isolate thread speedup.",
              "conclusion": "Accept only nonnegative setup/hold, zero unrouted nets and routed resource gates. "
                            "Keep W22/F98 fallbacks when 4.5 ns does not close; no sub-4 ns probe without 4.5 ns evidence."}
    config["estimates"] = {"DSP": 644, "BRAM18K": 109, "URAM": 0, "LUT": 42592,
                           "FF": 88806, "T": 8, "latency_cycles": 558758,
                           "basis": "W22 routed resource counts on matching W21 RTL; F97 measured 558758 latency "
                                    "and 558787 interval cycles. T8 lower bound is 65025*8=520200 cycles. "
                                    "If 4.5 ns closes, IP frame time is 2.514411 ms (9.09% below W22), "
                                    "not board time. Registered implementation budget remains 12.5 GiB. "
                                    "Admission also requires MemAvailable-budget >=2 GiB. No gate is waived."}
    plan(config)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("ws0", "clock"))
    args = parser.parse_args()
    (prepare_ws0 if args.step == "ws0" else prepare_clock)()


if __name__ == "__main__":
    main()
