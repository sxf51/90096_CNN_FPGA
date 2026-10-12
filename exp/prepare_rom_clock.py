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


def prepare_rom():
    base = json.loads((ROOT / "exp/configs/W21.json").read_text())
    base.pop("synthesis_after", None)
    estimates = {"DSP": 644, "BRAM18K": 146, "URAM": 0, "T": 8,
                 "LUT": 81086, "FF": 130057, "latency_cycles": 525237,
                 "basis": "Frozen W21 reports. C-only probe changes no synthesized arithmetic; export "
                          "9216 transformed Conv1 coefficients, 2048 Conv2 coefficients, 800 Conv3 "
                          "coefficients and 97 biases after the ordinary runtime load. Compare all 12161 "
                          "signed integer carriers with separately generated AP_RND_CONV/AP_SAT/G2 ROM content."}
    probe = {**base, "id": "F35", "series": "F", "stage": "rom_clock_wsB_banks",
             "name": "runtime_rom_bank_equivalence", "design": "designs/rom_bank_probe_v1",
             "csim_only": True, "memory_scheduler": True, "resource_policy": "routed",
             "required_image_count": 13,
             "tb_files": ["exp/tb/rom_banks.cpp", "exp/tb/golden.cpp", "test/tb_conv1.cpp",
                          "test/tb_srcnn.cpp", "test/util.cpp", "src/weights", "test/set5", "test/set14"],
             "purpose": "WS-B equivalence prerequisite: export the exact post-load private banks from "
                        "a frozen W21 copy during two butterfly C calls, compare every stored integer "
                        "against generated constant ROM contents and retain the ordinary exact output/border checks. "
                        "No synthesis is permitted for the ROM candidate before this prerequisite passes.",
             "changes": "Independent W21 source copy with simulation-only bank exports; arithmetic, "
                        "streams, parameter signature and quantization stay identical. Testbench wraps the existing validator.",
             "estimates": estimates, "interpretation": "Require equality for each layer coefficient and bias, "
                                                     "including ordering, saturation and convergent rounding. "
                                                     "This C-only export is not a hardware resource measurement.",
             "conclusion": "Only an exact bank and butterfly match allows W24 C synthesis."}
    plan(probe)
    rom = {**base, "id": "W24", "series": "W", "stage": "rom_clock_wsB",
           "name": "constant_rom_T8", "design": "designs/winograd_rom_v1", "top": "srcnn_rom",
           "memory_scheduler": True, "resource_policy": "routed", "required_image_count": 13,
           "required_bank_validation": "F35", "set14": True,
           "numpy_reference": "exp/numeric_reference/w10a10/numpy_reference",
           "tb_files": ["exp/tb/rom_validate.cpp", "exp/tb/golden.cpp", "test/tb_conv1.cpp",
                        "test/tb_srcnn.cpp", "test/util.cpp", "src/weights", "test/set5", "test/set14"],
           "required_axi_bundles": ["image_in", "image_out"], "storage": "constant_lutram_rom",
           "purpose": "WS-B independent constant-weight exploration. Fix the exact training parameters "
                      "at compile time, remove parameter AXI/reader/transformer/FIFOs/private write ports, "
                      "and keep W21 compute, raster order, quantization and replicate padding. "
                      "The new srcnn_rom top has only image input/output and control ports. "
                      "Runtime-loaded W21 remains the mainline. Require exact bank equivalence before synthesis, "
                      "all 13 course Set14 images, then two-frame same-weight/changed-input RTL and routed gates.",
           "changes": "Independent W21 copy, offline-generated integer coefficients/biases and new image-only top. "
                      "Remove runtime parameter processes, retain cyclic bank factors and DSP-bound products.",
           "estimates": {"DSP": 644, "BRAM18K": 146, "URAM": 0, "T": 8,
                         "Conv1_DSP": 288, "Conv2_DSP": 256, "Conv3_DSP": 100,
                         "LUT": 65000, "FF": 120000, "latency_cycles": 547500,
                         "basis": "644 MACs preserve W21 parallelism: 2304/8+2048/8+800/8. "
                                  "Line/raster buffers are unchanged, so budget146 BRAM18K and zeroURAM. "
                                  "Remove converter, raw G2 transform, parameter FIFOs and private write control "
                                  "from W21 HLS81086LUT/130057FF; allow approximately65kLUT/120kFF, "
                                  "with real constant-ROM optimization unknown. Cycles estimate is RTL-based: "
                                  "F97 558758 minus approximately11230 parameter startup=547528, rounded547500. "
                                  "HLS nominal lower bound remains524288 Winograd fold cycles, not a claimed RTL number. "
                                  "Predict route LUT35k-43k; first independently route at5ns when admitted."},
           "interpretation": "Compare parameter-free HLS and matching RTL/route reports with W21, "
                             "including all deviations above20%. Constant coefficients may optimize DSP/fabric "
                             "even with BIND_OP; only actual resources decide. Changed-parameter testing is inapplicable.",
           "conclusion": "Measure removed-parameter startup/control/timing cost while preserving the mainline "
                         "runtime interface. Do not select ROM as the board version without the user's decision."}
    rom.pop("quality_reference", None)
    plan(rom)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step", choices=("ws0", "clock", "rom"))
    args = parser.parse_args()
    {"ws0": prepare_ws0, "clock": prepare_clock, "rom": prepare_rom}[args.step]()


if __name__ == "__main__":
    main()
