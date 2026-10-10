#!/usr/bin/env python3
"""Bind exact fixed products to DSPs without changing numerical semantics."""
import json
import shutil
from run_exp import ROOT, write_json

destination = ROOT / "designs/dataflow_dsp"
if destination.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(ROOT / "designs/dataflow_wrap", destination)
path = destination / "srcnn.cpp"
text = path.read_text()
replacements = {
    "if (tap < 81) sums[oc] += window[tap / 9][tap % 9] * weights[oc][tap];":
        "if (tap < 81) {\n                            auto product = window[tap / 9][tap % 9] * weights[oc][tap];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                            sums[oc] += product;\n                        }",
    "sum += window[tap / 9][tap % 9] * weights[oc][tap];":
        "auto product = window[tap / 9][tap % 9] * weights[oc][tap];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                            sum += product;",
    "sums[oc] += value.v[ic] * weights[oc][ic];":
        "auto product = value.v[ic] * weights[oc][ic];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                    sums[oc] += product;",
    "sum += value.v[ic] * weights[oc][ic];":
        "auto product = value.v[ic] * weights[oc][ic];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                    sum += product;",
    "if (tap < 25) sum += window[tap / 5][tap % 5][ic] * weights[ic][tap];":
        "if (tap < 25) {\n                                auto product = window[tap / 5][tap % 5][ic] * weights[ic][tap];\n#pragma HLS BIND_OP variable=product op=mul impl=dsp\n                                sum += product;\n                            }",
}
for before, after in replacements.items():
    if before not in text:
        raise RuntimeError("Expected product missing: " + before)
    text = text.replace(before, after)
path.write_text(text)
config = json.loads((ROOT / "exp/configs/E046.json").read_text())
config.update(id="E047", name="dataflow_dsp_T32", design="designs/dataflow_dsp",
              purpose="Force the 251 direct-convolution products per cycle onto DSPs. "
                      "E033 default narrow multiplication used only 9 DSP but 136,868 LUT, "
                      "exceeding the 81,984 LUT limit. Expected MAC DSP split 162/64/25 plus "
                      "conversion/interface overhead; compute floor 2,080,800 cycles.",
              changes="Independent copy of E046 no-overflow design. Every fully-unrolled "
                      "product is an explicit local variable bound to op=mul, impl=dsp.",
              interpretation="Determine actual multiply mapping and the remaining weight-bank, "
                             "array-index mux, saturation-at-layer-boundary and AXI overhead. "
                             "Actual full-frame bit comparison remains mandatory.",
              conclusion="Choose a resource-feasible baseline for bank/storage and frequency scans.")
write_json(ROOT / "exp/configs/E047.json", config)
