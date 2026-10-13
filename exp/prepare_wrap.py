#!/usr/bin/env python3
"""Prepare a no-overflow accumulator control with identical layer casts."""
import json
import shutil
from run_exp import ROOT, write_json

source = ROOT / "designs/dataflow_v1"
destination = ROOT / "designs/dataflow_wrap"
if destination.exists():
    raise RuntimeError("Design already exists")
shutil.copytree(source, destination)
path = destination / "types.h"
text = path.read_text()
text = text.replace("6, AP_RND_CONV, AP_SAT>", "6, AP_TRN, AP_WRAP>")
text = text.replace("7, AP_RND_CONV, AP_SAT>", "7, AP_TRN, AP_WRAP>")
path.write_text(text)
config = json.loads((ROOT / "exp/configs/E033.json").read_text())
config.update(id="E046", name="dataflow_wrap_T32", stage=4, design="designs/dataflow_wrap",
              quality_reference="experiments/E017_apfixed_boundary_w10a10/metrics.json",
              purpose="Remove redundant saturation logic from exact fractional accumulators. "
                      "The E010 analytical absolute-sum bounds fit integer bits 6/6/7 for the "
                      "protected trained weights and every representable activation. Ideal budget "
                      "251 DSP, 2,080,800 compute cycles, unchanged buffers.",
              changes="Independent dataflow_v1 copy; only accumulator overflow/rounding modes "
                      "change to AP_WRAP/AP_TRN. Input, weight, bias and layer-output casts "
                      "retain AP_RND_CONV/AP_SAT. Products have full fractional precision.",
              interpretation="No discarded accumulator fraction exists, and analytical bounds "
                             "prevent overflow, so the arithmetic must match the AP_SAT reference "
                             "bit for bit. This bound is specific to the protected trained parameters; "
                             "replacing weights requires range revalidation. HLS may balance "
                             "additions once saturating partial-sum semantics are removed.",
              conclusion="Compare clock, fold II and LUT with E033; retain exact butterfly gate.")
write_json(ROOT / "exp/configs/E046.json", config)
