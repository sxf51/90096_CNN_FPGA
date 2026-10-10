#!/usr/bin/env python3
"""Write reproducible multiplier microbenchmark experiment configurations."""
from run_exp import ROOT, write_json

base = {"stage": 5, "design": "designs/micro_multiplier", "top": "benchmark", "clock": 10,
        "tb_files": ["exp/tb/micro_multiplier.cpp"], "settings": "/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh",
        "changes": "Standalone PE microbenchmark, not a complete SRCNN design. 64 sample operands; explicit bit-exact integer checker.",
        "interpretation": "Pending actual mapping, loop II and resource report. Whole-kernel latency does not describe a network frame.",
        "conclusion": "Record operator mapping evidence and compare to network DSP/LUT budgets.",
        "notes": "microbenchmark only; exclude latency from network Pareto; constants are explicit representative integers"}
cases = [
    ("E051", "mul16_default", {"EXP_MUL_WIDTH": 16}, 10, "Does one scheduled signed 16x16 multiplier map to one DSP?", "i16_i16_i32"),
    ("E052", "mul16_constant_unroll", {"EXP_MUL_WIDTH": 16, "EXP_CONSTANT": 1}, 10, "How does HLS map 64 fully unrolled constant-weight multipliers?", "i16_constant_i32"),
    ("E053", "mul8_fabric", {"EXP_MUL_WIDTH": 8, "EXP_FABRIC": 1}, 10, "Measure LUT/FF for signed 8x8 fabric multiply with II=1 and exhaustive operand-pair testing.", "i8_i8_i16"),
    ("E054", "mul16_default_4ns", {"EXP_MUL_WIDTH": 16}, 4, "Check whether the signed 16x16 one-DSP mapping survives a 4 ns target.", "i16_i16_i32"),
    ("E055", "mul8_add_control", {"EXP_MUL_WIDTH": 8, "EXP_ADD_ONLY": 1}, 10, "Use an add-only kernel with same array loop as a control for fabric multiplication overhead.", "i8_add_i16"),
]
for exp_id, name, defines, clock, purpose, precision in cases:
    config = {**base, "id": exp_id, "name": name, "defines": defines, "clock": clock,
              "purpose": purpose, "precision": precision, "ii_targets": {} if defines.get("EXP_CONSTANT") else {"samples": 1}}
    write_json(ROOT / f"exp/configs/{exp_id}.json", config)
