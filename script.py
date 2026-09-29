# Create and configure the SRCNN golden-reference HLS component.
#
# IMPORTANT: run this from the 'golden' folder itself (the one containing
# this file, src/ and test/):
#
#     vitis -s script.py
#
# Afterwards, close this console window - otherwise Vitis will report that
# the workspace is already in use when you try to open it in the GUI.

import os
import shutil
import vitis

# Start from a clean workspace each run.
if os.path.exists("./workspace"):
    print("Deleting the existing 'workspace' folder ...")
    shutil.rmtree("./workspace")

client = vitis.create_client()

# Workspace that will hold the component
client.set_workspace(path="./workspace")

# Create the HLS component 'baseline' with a new (empty) config file
print("Creating HLS component 'baseline' ...")
comp = client.create_hls_component(
    name="baseline",
    cfg_file=["hls_config.cfg"],
    template="empty_hls_component",
)

# Configure the component. File paths are relative to the generated config
# at workspace/baseline/hls_config.cfg, so ../../ points back to this folder.
cfg = client.get_config_file(path="./workspace/baseline/hls_config.cfg")
root = "../../"
src = root + "src/"
test = root + "test/"

# Kria SOM as target part
cfg.set_value(key="part", value="xck26-sfvc784-2LV-c")

cfg.set_value(section="hls", key="flow_target", value="vivado")
cfg.set_value(section="hls", key="clock", value="10ns")
cfg.set_value(section="hls", key="package.output.format", value="ip_catalog")

# Top function and design source files 
cfg.set_value(section="hls", key="syn.top", value="srcnn")
cfg.set_values(section="hls", key="syn.file",
               values=[src + "srcnn.h",
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
cfg.set_value(section="hls", key="tb.cflags", value="-I" + src)

print("Done. Please exit the current console, then set the workspace in")
print("Vitis ('Set Workspace' -> the new 'workspace' folder) and run")
print("C SIMULATION.")

# Uncomment to run C SIMULATION here instead of clicking it in the GUI:
# comp = client.get_component(name="baseline")
# comp.run(operation="C_SIMULATION")

vitis.dispose()
