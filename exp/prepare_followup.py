#!/usr/bin/env python3
"""Prepare measured-control follow-ups without changing archived designs."""
import json
import shutil
from run_exp import ROOT, write_json

base = json.loads((ROOT / "exp/configs/E048.json").read_text())
for exp_id, t, storage in (("E057", 32, 1), ("E058", 16, 1), ("E059", 8, 1)):
    config = {**base, "id": exp_id, "name": f"integer_lutram_T{t}", "T": t,
              "defines": {**base["defines"], "EXP_T": t, "EXP_STORAGE": storage},
              "storage": "lutram",
              "purpose": f"Banked writable LUTRAM with T={t}. Ideal DSP {8032/t:g}, "
                         f"compute floor {65025*t} cycles. Gather buffer control 168 BRAM18K. "
                         "Banked weight storage should remove E047's large register write/read muxes.",
              "changes": "E048 exact integer-carrier design; only T and weight storage parameter change."}
    write_json(ROOT / f"exp/configs/{exp_id}.json", config)

destination = ROOT / "designs/scatter_int"
if destination.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(ROOT / "designs/dataflow_int", destination)
text = (destination / "srcnn.cpp").read_text()
start, end = text.index("static void conv3_stream("), text.index("static void write_output(")
scatter = (ROOT / "exp/architectures/scatter3.inc").read_text()
begin, finish = scatter.index("#if EXP_FIXED"), scatter.index("    static partial buffer")
scatter = scatter[:begin] + "    using partial = word<32>;\n" + scatter[finish:]
scatter = scatter.replace("contribution[tap] += value.v[ic] * weights[ic][tap];",
    "auto product = value.v[ic] * weights[ic][tap];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                        contribution[tap] += product;")
scatter = scatter.replace("out.write(output(window[0][0] + biases[0]))",
    "out.write(quantize<EXP_W_BITS - 2>(partial(window[0][0] + bias3(biases[0]))))")
(destination / "srcnn.cpp").write_text(text[:start] + scatter + text[end:])
config = {**base, "id": "E060", "name": "scatter_integer_T32", "stage": 5,
          "design": "designs/scatter_int", "storage": "lutram",
          "defines": {**base["defines"], "EXP_STORAGE": 1},
          "purpose": "Exact 32-bit partial-sum scatter with explicit padding. Ideal DSP 162/64/25=251; "
                     "Conv3 partial cache 5*255*32=40800 bits (~5 BRAM18K with row banks), "
                     "plus pad3 row cache 255*32*10 bits. Nominal frame floor 2080800 cycles, "
                     "scatter processes 67081 rather than 65025 pixels (3.16% work overhead).",
          "changes": "Independent E048 copy with channel-reduced Conv3 scatter. Five rotating physical "
                     "row banks and a 5x5 register window avoid overlapping BRAM RMW accesses. "
                     "Weight storage set to banked LUTRAM; full fractions and layer casts retained.",
          "interpretation": "Compare against the same banked gather control E057. Separate explicit "
                            "padding-row memory from partial-sum storage. All border pixels must match "
                            "E019 bit for bit; report actual loops and dataflow warnings.",
          "conclusion": "Keep measured scatter evidence for phase-two boundary-kernel comparison."}
write_json(ROOT / "exp/configs/E060.json", config)
