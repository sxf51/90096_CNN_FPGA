#!/usr/bin/env python3
"""Prepare a conservative T4 DSP/fabric split for feasibility measurement."""
import json
import shutil
from run_exp import ROOT, write_json

destination = ROOT / "designs/dataflow_mix"
if destination.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(ROOT / "designs/dataflow_dsp", destination)
path = destination / "srcnn.cpp"
text = path.read_text()
start, end = text.index("static void conv1_stream("), text.index("static void conv2_stream(")
section = text[start:end]
old = "auto product = window[tap / 9][tap % 9] * weights[oc][tap];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                            sum += product;"
new = "if (lane < C1_OC / 2) {\n                                auto dsp_product = window[tap / 9][tap % 9] * weights[oc][tap];\n#pragma HLS BIND_OP variable=dsp_product op=mul impl=dsp\n                                sum += dsp_product;\n                            } else {\n                                auto lut_product = window[tap / 9][tap % 9] * weights[oc][tap];\n#pragma HLS BIND_OP variable=lut_product op=mul impl=fabric\n                                sum += lut_product;\n                            }"
if old not in section:
    raise RuntimeError("Cout product binding missing")
section = section.replace(old, new)
text = text[:start] + section + text[end:]
start, end = text.index("static void conv3_stream("), text.index("static void write_output(")
section = text[start:end].replace("op=mul impl=dsp", "op=mul impl=fabric")
path.write_text(text[:start] + section + text[end:])
config = json.loads((ROOT / "exp/configs/E047.json").read_text())
config["defines"]["EXP_T"] = 4
config.update(id="E056", name="mixed_T4_feasibility", stage=5, T=4, design="designs/dataflow_mix",
              purpose="Measure T=4 feasibility with 648 Conv1 and 512 Conv2 DSP products (1160 total), "
                      "and 648 Conv1 plus 200 Conv3 fabric products. Ideal frame compute floor "
                      "260,100 cycles. At E033's 62 LUT per fabric 10x10 multiply the 848 fabric "
                      "products alone cost about 52,576 LUT before adders, weight muxes and AXI; "
                      "the 81,984 total-LUT cap may therefore be exceeded.",
              changes="Independent dataflow_dsp copy, T=4; first half of unrolled Conv1 output "
                      "lanes bind to DSP, second half to fabric. Conv2 stays DSP and Conv3 uses fabric. "
                      "All casts and no-overflow accumulators match E019/E017.",
              interpretation="This is a feasibility experiment, not assumed acceleration. "
                             "Check actual DSP/fabric mapping, achieved clock, LUT/FF limits and "
                             "all loop II. Effective latency must use the larger of target and estimated clock.",
              conclusion="If infeasible, retain measured resource excess for second-phase hybrid budgets.")
write_json(ROOT / "exp/configs/E056.json", config)
