#!/usr/bin/env python3
"""Create independent scatter source by replacing only the Conv3 core."""
import json
import shutil
from run_exp import ROOT, write_json

source = ROOT / "designs/dataflow_v1"
destination = ROOT / "designs/scatter_v1"
shutil.copytree(source, destination)
text = (destination / "srcnn.cpp").read_text()
start, end = text.index("static void conv3_stream("), text.index("static void write_output(")
replacement = (ROOT / "exp/architectures/scatter3.inc").read_text()
(destination / "srcnn.cpp").write_text(text[:start] + replacement + text[end:])
config = json.loads((ROOT / "exp/configs/E033.json").read_text())
config.update(id="E050", name="scatter_T32", stage=5, design="designs/scatter_v1",
              purpose="Compare gather with channel-reduced scatter using 5x255x32-bit partial sums and a 5x5 register window. The register window should avoid five simultaneous read-modify-write accesses per physical BRAM bank. Ideal Conv3 budget 25 DSP at T32; padding adds 3.16% Conv3 input work.",
              changes="Independent copy of dataflow_v1. Conv1/Conv2 and interfaces unchanged; Conv3 uses scatter, one read/write per fixed physical cache bank and five-column register reuse. Explicit pad3 retained.",
              interpretation="Check exact reference output and all borders. Cache keeps full product fractions; supported settings require reference accumulator <=32 bits. Read/write bank roles rotate in registers. Declared partial storage 5x255x32 bits=5100 bytes, excluding existing pad3 row cache. Reports determine physical mapping and real II.",
              conclusion="Compare actual BRAM/LUT/FF/II against the same T32 gather baseline; retain failures.")
write_json(ROOT / "exp/configs/E050.json", config)
