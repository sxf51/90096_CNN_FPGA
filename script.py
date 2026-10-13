# Create and configure the current SRCNN HLS component.
#
# IMPORTANT: run this from the 'golden' folder itself (the one containing
# this file, src/ and test/):
#
#     vitis -s script.py
#
# Afterwards, close this console window - otherwise Vitis will report that
# the workspace is already in use when you try to open it in the GUI.

import os
from datetime import datetime
from pathlib import Path
import vitis

# Resolve paths from this script, even when launched from another directory.
project_root = Path(__file__).resolve().parent
workspace = project_root / "workspace"
if workspace.exists():
    workspace = project_root / ("workspace_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
print("Creating workspace:", workspace)

client = vitis.create_client()

# Workspace that will hold the component
client.set_workspace(path=workspace.as_posix())

# Create the HLS component 'baseline' with a new (empty) config file
print("Creating HLS component 'baseline' ...")
comp = client.create_hls_component(
    name="baseline",
    cfg_file=["hls_config.cfg"],
    template="empty_hls_component",
)

# Absolute paths avoid Windows HLS relative-path resolution problems.
cfg = client.get_config_file(path=(workspace / "baseline" / "hls_config.cfg").as_posix())
root = project_root.as_posix() + "/"
src = root + "src/"
test = root + "test/"

# Kria SOM as target part
cfg.set_value(key="part", value="xck26-sfvc784-2LV-c")

cfg.set_value(section="hls", key="flow_target", value="vivado")
cfg.set_value(section="hls", key="clock", value="10ns")
cfg.set_value(section="hls", key="package.output.format", value="ip_catalog")
# Use only the explicit bounded parallelism in src/. Keep numeric results
# reproducible; set SRCNN_INT8=1 before running to select the INT8 experiment.
numeric_flags = "-std=c++14 -ffp-contract=off -DSRCNN_INT8=" + (
    "1" if os.environ.get("SRCNN_INT8") == "1" else "0"
)
cfg.set_value(section="hls", key="syn.compile.pipeline_loops", value="0")
cfg.set_value(section="hls", key="syn.cflags", value=numeric_flags)

# Top function and design source files 
cfg.set_value(section="hls", key="syn.top", value="srcnn")
cfg.set_values(section="hls", key="syn.file",
               values=[src + "srcnn.h",
                       src + "tile.h",
                       src + "srcnn.cpp",
                       src + "conv1.cpp"])

# Testbench sources, plus the weight and image DIRECTORIES.
cfg.set_values(section="hls", key="tb.file",
               values=[test + "csim.cpp",
                       test + "tb_srcnn.cpp",
                       test + "tb_conv1.cpp",
                       test + "tb_set14.cpp",
                       test + "util.h",
                       test + "util.cpp",
                       src + "weights",
                       test + "set5",
                       test + "set14"])

# Testbenches include "srcnn.h" from src/ (Tcl: add_files -tb -cflags -I./src)
cfg.set_value(section="hls", key="tb.cflags",
              value="-I" + src + " " + numeric_flags)

print("Done. Please exit the current console, then set the workspace in")
print("Vitis ('Set Workspace' -> " + str(workspace) + ") and run")
print("C SIMULATION.")

# Uncomment to run C SIMULATION here instead of clicking it in the GUI:
# comp = client.get_component(name="baseline")
# comp.run(operation="C_SIMULATION")

vitis.dispose()
