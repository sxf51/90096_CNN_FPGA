#!/usr/bin/env python3
"""Commit P/W microbenchmark hypotheses before creating their source kernels."""
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def save(config):
    archive = ROOT / "experiments" / (config["id"] + "_" + config["name"])
    if archive.exists():
        raise RuntimeError("Existing plan; do not overwrite: " + config["id"])
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), config["id"],
                    "plan_" + config["name"]], cwd=ROOT, check=True)


def main():
    base = {"stage": "arch_pe", "scope": "PE", "clock": 4,
            "settings": "/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh",
            "interpretation": "Compare measured DSP/operator LUT, achieved II and pipeline depth with the paper estimate. Inspect pre-adder mapping separately; a DSP count alone is insufficient.",
            "conclusion": "Use only numerically exact and measured primitives in full-network integration.",
            "notes": "PE only; kernel latency is excluded from network rankings"}
    packing = [
        ("P01", "signed8_pair", 1, 1, 8, 8, 0, 1, 220,
         "Two signed8 coefficients share a signed8 input. Explicit 27-bit packed multiply, gap18, signed-low borrow repair; expect one DSP per pair."),
        ("P02", "signed8_direct_control", 0, 1, 8, 8, 0, 2, 100,
         "Two direct signed8 products with identical array/control interfaces are the unpacking-cost control."),
        ("P03", "signed8_group7", 1, 7, 8, 8, 0, 1, 300,
         "Accumulate seven packed products before decoding. Worst low magnitude7*16384=114688 is below signed18 capacity; expect one multiplier DSP with a fabric accumulator."),
        ("P04", "signed8_auto_mapping", 2, 1, 8, 8, 0, 1, 220,
         "Allow HLS to map the packing expression without BIND_OP and compare DSP count and add/multiply inference with P01."),
        ("P05", "signed8_builtin_preadder", 3, 1, 8, 8, 0, 1, 220,
         "Test installed hls::dsp48e2::add_mul_add with explicit pre-adder and pipeline flags. The SDK has an __PRESYNTHESIS__ unsupported guard, so compilation rejection is a plausible result."),
        ("P06", "nonnegative10_group2", 1, 2, 8, 10, 1, 1, 320,
         "Share nonnegative raw10 activations0..511 between signed8 weights, decode every two terms. The signed18 low field bound is2*128*511=130816; seven-term INT8 accumulation is invalid here."),
        ("P07", "exact10_residual_pair", 1, 1, 10, 10, 0, 1, 500,
         "Preserve generic signed10 coefficients as signed-low8 plus256*residual[-2,2]. Pack low coefficients, unpack each signed10-input product, and restore residuals using shifts/adds. This keeps the passing w10a10 precision despite failing uniform INT8 quality."),
    ]
    for exp_id, name, mode, group, bits, c_bits, nonnegative, dsp, lut, purpose in packing:
        config = {**base, "id": exp_id, "name": name, "series": "P", "design": "designs/packing_pe",
                  "top": "packing_pe", "T": 1, "precision": f"raw{bits}_raw{c_bits}_exact_pair",
                  "tb_files": ["exp/tb/packing.cpp"],
                  "defines": {"EXP_PACK_MODE": mode, "EXP_GROUP": group, "EXP_OPERAND_BITS": bits,
                              "EXP_C_BITS": c_bits, "EXP_NONNEG": nonnegative},
                  "ii_targets": {"pack_terms": 1}, "purpose": purpose,
                  "changes": "Independent PE kernel; 56 input triples per call. Exact direct-product checker, exhaustive signed8 triples, extremal homogeneous groups, and deterministic random wider data.",
                  "estimates": {"DSP": dsp, "BRAM18K": 0, "URAM": 0, "LUT": lut, "T": 1,
                                "latency_cycles": 64, "frame_projection_T": 4,
                                "frame_projection_cycles": 65025 * 4,
                                "frame_projection_DSP": 8032 // 8,
                                "basis": "56 terms plus <=8 pipeline cycles; array interfaces need no internal frame memory. DSP estimates count one 27x18 multiplier per packed pair, two for direct control; LUT budget includes repair, control and possible fabric accumulation. Frame projection assumes1004 such PEs and excludes buffering/DDR."}}
        save(config)
    for exp_id, name, bits, direct in (("W01", "integer_f2_10bit", 10, 0),
                                     ("W02", "direct_f2_control", 10, 1),
                                     ("W03", "integer_f2_16bit", 16, 0)):
        dsp = 36 if direct else 16
        config = {**base, "id": exp_id, "name": name, "series": "W", "design": "designs/winograd_pe",
                  "top": "winograd_pe", "T": 1, "precision": f"raw{bits}/v{bits+2}/G2w{bits+4}/acc{2*bits+14}",
                  "tb_files": ["exp/tb/winograd.cpp"], "defines": {"EXP_BITS": bits, "EXP_DIRECT": direct},
                  "ii_targets": {"wino_tiles": 1},
                  "purpose": "Compare exact integer F(2x2,3x3) and direct correlation. G2 is2G, so inverse outputs must divide by4 exactly before any quantization. "
                             f"At{bits} input/weight bits, transformed operands are{bits+2}x{bits+4}, within the27x18 DSP48E2 limits; expect one DSP per product.",
                  "changes": "Independent 32-tile PE kernel. Weights transformed before each call in testbench; input/output transforms use fabric adds/subtracts. Direct integer2x2 outputs are checked exhaustively for each deterministic random tile, including extrema.",
                  "estimates": {"DSP": dsp, "BRAM18K": 0, "URAM": 0, "LUT": 1100 if direct else 1500,
                                "T": 1, "latency_cycles": 44, "frame_projection_T": 8,
                                "frame_projection_cycles": 16384 * 32,
                                "frame_projection_Conv1_DSP": 648 if direct else 288,
                                "basis": "32 tiles plus12 pipeline cycles. F2 uses16 products per tile versus36 direct; all transforms are add/subtract/constant shifts in fabric. Nine subkernels and64 channels give2304 products/pixel;128x128 tiles account for the odd255 image edge."}}
        save(config)


if __name__ == "__main__":
    main()
