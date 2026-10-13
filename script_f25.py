"""Create the F25 HLS component for manual use in the Vitis GUI.
Run from the repository root: vitis -s script_f25.py
"""
from pathlib import Path
import shutil
import json
import subprocess
import vitis

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "f25_gui_assets"
CONFIG = ASSETS / "hls_config.cfg"
WORKSPACE = ROOT / "workspace_f25_gui"


# Rebuild the GUI inputs directly from the immutable F25 archive.
archive = ROOT / "experiments/F25_nested_weight_loader_T16_2p5ns"
observed = json.loads((archive / "config.json").read_text(encoding="utf-8"))
config = json.loads((ROOT / "exp/configs/F25.json").read_text(encoding="utf-8"))
metrics = json.loads((archive / "metrics.json").read_text(encoding="utf-8"))
commit = observed.get("frozen_source_commit", metrics["git_commit"])
ASSETS.mkdir(exist_ok=True)
source = ASSETS / "source"
shutil.copytree(archive / "source", source, dirs_exist_ok=True)
tbroot = ASSETS / "frozen_tb"
files = subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", commit, "--", "src", "test", "exp/tb"],
    cwd=ROOT, text=True,
).splitlines()
for name in files:
    if Path(name).suffix not in {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".inc"}:
        continue
    if name.startswith("exp/tb/replay_"):
        continue
    target = tbroot / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT))
# Add the original MSE calculation to the GUI testbench only.
validation = tbroot / "exp/tb/validate.cpp"
text = validation.read_text(encoding="utf-8")
text = text.replace('#include "srcnn.h"', '#include "srcnn.h"\n#include "../../test/util.h"', 1)
anchor = '        const double border_mse = mse(&output[0][0][0], &reference[0][0][0], H * W, true);'
addition = anchor + '\n        const double original_mse = calculate_mse(&reference[0][0][0], &output[0][0][0], N3 * H * W);\n        std::cout << std::setprecision(17) << "***** SRCNN Golden Reference *****" << std::endl\n                  << "  - Butterfly MSE (original calculate_mse): " << original_mse << std::endl;'
if anchor not in text:
    raise RuntimeError("Cannot locate the F25 MSE insertion point")
text = text.replace(anchor, addition, 1)
validation.write_text(text, encoding="utf-8")

reference = ASSETS / "fixed_reference.bin"
shutil.copyfile(ROOT / config["reference"], reference)
defines = dict(config["defines"])
defines.update(EXP_FIXED=1, EXP_SET14=0, EXP_REFERENCE=1, EXP_NUMPY_REFERENCE=0, EXP_QUICK=1)
flags = "-std=c++14 -ffp-contract=off " + " ".join("-D%s=%s" % item for item in defines.items())
flags += " -I" + source.as_posix() + " -I" + (tbroot / "src").as_posix()
lines = ["part=xck26-sfvc784-2LV-c", "[hls]", "flow_target=vivado", "clock=2.5ns",
         "package.output.format=ip_catalog", "syn.top=srcnn", "csim.O=true",
         "syn.cflags=" + flags, "tb.cflags=" + flags]
lines += ["syn.file=" + path.as_posix() for path in sorted(source.glob("*.cpp"))]
for name in ["exp/tb/validate.cpp", "exp/tb/golden.cpp", "test/tb_conv1.cpp", "test/tb_srcnn.cpp", "test/util.cpp"]:
    path = tbroot / name
    if not path.is_file():
        raise RuntimeError("Frozen testbench missing: " + str(path))
    lines.append("tb.file=" + path.as_posix())
for name in ["src/weights", "test/set5", "test/set14"]:
    path = ROOT / name
    if not path.is_dir():
        raise RuntimeError("Test data missing: " + str(path))
    lines.append("tb.file=" + path.as_posix())
lines.append("tb.file=" + reference.as_posix())
CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")

client = vitis.create_client()
try:
    client.set_workspace(path=str(WORKSPACE))
    if not (WORKSPACE / "F25_manual").exists():
        client.create_hls_component(
            name="F25_manual",
            cfg_file=["hls_config.cfg"],
            template="empty_hls_component",
        )
    else:
        print("Reusing existing F25_manual component; refreshing inputs and configuration.")
    target = WORKSPACE / "F25_manual/hls_config.cfg"
    shutil.copyfile(CONFIG, target)
    print("F25_manual is ready. Close this console, then open this workspace in Vitis:")
    print(WORKSPACE)
    print("Run C Simulation, then C Synthesis in the GUI.")
finally:
    vitis.dispose()
