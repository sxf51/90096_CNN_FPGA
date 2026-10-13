#!/usr/bin/env python3
"""Commit structure hypotheses before generating independent implementations."""
import json
import math
import subprocess
import sys
from plan_arch import plan
from run_exp import ROOT


def save(config):
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), config["id"],
                    "plan_" + config["name"]], cwd=ROOT, check=True)


def main():
    base = json.loads((ROOT / "exp/configs/G01.json").read_text())
    base.update(stage="arch_s", series="S", scope="frame")
    base.pop("estimates")
    base.pop("purpose")
    ddr_bytes = 2 * 65025 * (64 + 32) * 4 + 2 * 65025 * 4 + 8129 * 4
    save({**base, "id": "S01", "name": "ddr_global_probe", "design": "designs/ddr_global_probe",
          "required_axi_bundles": ["scratch1", "scratch2"],
          "purpose": "Can the fixed srcnn signature expose two global feature arrays through m_axi? Execute each layer sequentially with float carriers for quantized features. The scratch arrays must become real external ports; ignored/rejected pragmas invalidate this DDR experiment. No supplied input/output buffer is used out of bounds.",
          "changes": "Independent direct integer layer engine with global float scratch arrays. Probe global-port INTERFACE support without changing any srcnn argument.",
          "ddr_bytes_per_frame": ddr_bytes, "requested_burst_words": 256,
          "ddr_bandwidth_GB_s": [19.2, 9.6], "bandwidth_source": "AMD DS987 K26 SOM data sheet: 64-bit DDR4 at 2400Mb/s;19.2GB/s theoretical,9.6GB/s assumed50% efficiency. See experiments/SOURCES.md.",
          "ddr_lower_bound_ms": [ddr_bytes / b / 1e6 for b in (19.2, 9.6)],
          "estimates": {"DSP": 254, "Conv1_DSP": 162, "Conv2_DSP": 64, "Conv3_DSP": 25,
                        "BRAM18K": 0, "URAM": 0, "T": 96, "latency_cycles": 65025 * 96 + 8129,
                        "basis": "Three sequential T32 layer schedules,251 dedicated MACs plus3 boundary converters. Full feature maps are external DDR only if both scratch AXI ports exist. DDR payload includes two writes/two reads of float64/32-channel features, float IO and all parameters; csynth omits realistic DDR stalls."},
          "interpretation": "Require both scratch AXI bundles before interpreting this as a DDR implementation. Compare ideal sequential cycles with reported memory-port stalls and report bandwidth lower bounds separately.",
          "conclusion": "If global m_axi is unsupported, preserve the failure and record scratch-pointer contract as pending human decision; proceed with tile fusion."})
    save({**base, "id": "S02", "name": "whole_dataflow_control", "design": "designs/gather_control",
          "purpose": "Common T32/10ns exact whole-network DATAFLOW control for structure comparisons. Use the independent G01 gather source unchanged.",
          "estimates": {"DSP": 254, "Conv1_DSP": 162, "Conv2_DSP": 64, "Conv3_DSP": 25,
                        "BRAM18K": 168, "URAM": 0, "T": 32, "latency_cycles": 2983024,
                        "basis": "Measured first-phase E057 schedule/resources, including pixel pipeline fill/drain and row-padding overhead; not ideal65025*T."},
          "ddr_bytes_per_frame": 65025 * 8 + 8129 * 4,
          "changes": "Repeat existing independently copied gather source, with two frames and exact reference gate.",
          "interpretation": "Compare sequential/tiled schedules to measured DATAFLOW overlap and its line/FIFO memory cost.",
          "conclusion": "Use as the common organization baseline; all internal feature maps remain on chip."})
    for exp_id, block in (("S03", 8), ("S04", 16), ("S05", 32), ("S06", 64)):
        count = math.ceil(255 / block) ** 2
        features = count * (block + 4) ** 2
        reads = count * (block + 12) ** 2
        bytes_ = reads * 4 + 65025 * 4 + 8129 * 4
        save({**base, "id": exp_id, "name": f"tile_fusion_B{block}", "design": "designs/tile_fusion",
              "defines": {**base["defines"], "EXP_BLOCK": block},
              "purpose": f"Explore B={block} output-tile fusion. Cache(B+12)^2 input values and(B+4)^2 Conv2 features, fusing Conv1/Conv2 per feature center. Clamp each feature center to the true image before selecting its9x9 input patch, preserving replicate at Conv3. Partial edge blocks still schedule complete feature halos; unused output cells are skipped.",
              "changes": "Independent tile engine, no DATAFLOW between tiles/layers. Same exact fixed-point arithmetic and original float-array interface; on-chip input and feature2 caches use spatial banks.",
              "ddr_bytes_per_frame": bytes_, "requested_burst_words": 256,
              "scheduled_feature_centers": features, "input_values_read": reads,
              "feature_recompute_ratio": features / 65025, "input_repetition_ratio": reads / 65025,
              "cache_bits": (block + 12) ** 2 * 10 + (block + 4) ** 2 * 32 * 10,
              "ddr_bandwidth_GB_s": [19.2, 9.6], "ddr_lower_bound_ms": [bytes_ / b / 1e6 for b in (19.2, 9.6)],
              "estimates": {"DSP": 254, "Conv1_DSP": 162, "Conv2_DSP": 64, "Conv3_DSP": 25,
                            "BRAM18K": 0, "URAM": 0, "T": 96,
                            "latency_cycles": (2 * features + 65025) * 32 + reads + 8129,
                            "basis": "Sequential T32 Conv1 and Conv2 for every scheduled halo feature, then T32 Conv3 for65025 valid outputs. Input cyclic9x9 and feature2 cyclic5x5/channel banks use LUTRAM; no full feature1 array. Count ceil255/B partial tiles and their complete halo; bandwidth times remain lower bounds."},
              "interpretation": "Compare measured per-tile scheduling overhead, cache LUT use, halo recomputation and requested versus inferred burst lengths. DDR stalls are outside csynth's accurate model.",
              "conclusion": "Select the best block only from measured feasible exact variants; tile recomputation trades line buffers for sequential work."})
    parent = json.loads((ROOT / "exp/configs/P05.json").read_text())
    save({"id": "P08", "name": "builtin_mapping_implementation", "series": "P", "stage": "arch_verify", "scope": "PE",
          "operation": "impl", "verify_parent": "P05", "design": parent["design"], "clock": 4,
          "settings": parent["settings"], "timeout": 10800,
          "purpose": "Inspect routed DSP48E2 primitive attributes for the passing pre-adder builtin. One HLS DSP does not establish pre-adder use; check PREADDINSEL,AMULTSEL,INMODE and pipeline registers from the implementation checkpoint.",
          "estimates": {"DSP": 1, "BRAM18K": 0, "URAM": 0, "T": 1, "latency_cycles": 63,
                        "basis": "P05 HLS evidence: one explicitly requested DSP48E2 pre-adder primitive; routed result and attributes need independent verification."},
          "notes": "PE implementation only; no network frame ranking"})


if __name__ == "__main__":
    main()
