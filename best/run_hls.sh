#!/usr/bin/env bash
# Re-run the C17 flow from this folder on a machine with Vitis 2026.1.
#   bash run_hls.sh csim     # C simulation (13 images, bit-exact check against data/)
#   bash run_hls.sh csynth   # HLS synthesis at 4 ns (reproduces results/C17_hls)
#   bash run_hls.sh cosim    # C/RTL co-simulation, two frames (reproduces results/C20_cosim); needs csynth first
# Place-and-route at 5 ns (results/C22_impl_5ns) used the staged Vivado scripts in
# results/C22_impl_5ns/implementation/ on the exported IP; it is not wrapped here.
# Source the Vitis settings first, e.g. `source /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh`.
set -euo pipefail
cd "$(dirname "$0")"
command -v vitis-run >/dev/null || { echo "vitis-run not found: source Vitis settings64.sh first" >&2; exit 1; }
mkdir -p work
case "${1:-}" in
  csim)   vitis-run --mode hls --csim   --config hls_config.cfg       --work_dir work ;;
  csynth) vitis-run --mode hls --csynth --config hls_config.cfg       --work_dir work ;;
  cosim)  vitis-run --mode hls --cosim  --config hls_config_cosim.cfg --work_dir work ;;
  *) echo "usage: $0 {csim|csynth|cosim}" >&2; exit 2 ;;
esac
