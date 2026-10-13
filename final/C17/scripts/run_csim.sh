#!/usr/bin/env bash
# C simulation of the packaged C17 design with the original course testbench
# (test/csim.cpp: tb_conv1 + tb_srcnn on butterfly).
# Usage: source <Vitis 2026.1>/settings64.sh; bash final/C17/scripts/run_csim.sh [work_dir]
set -euo pipefail

PKG=$(cd "$(dirname "$0")/.." && pwd)
ROOT=$(cd "$PKG/../.." && pwd)
WORK=${1:-"$PKG/build/csim"}

case "$PKG$WORK" in
  *[[:space:]]*) echo "error: paths must not contain whitespace" >&2; exit 2 ;;
esac
command -v vitis-run >/dev/null || { echo "error: vitis-run not found; source Vitis settings64.sh first" >&2; exit 2; }
for f in "$ROOT/test/csim.cpp" "$ROOT/test/tb_conv1.cpp" "$ROOT/test/tb_srcnn.cpp" \
         "$ROOT/test/util.cpp" "$ROOT/test/util.h" "$ROOT/test/set5" "$ROOT/src/weights"; do
  [ -e "$f" ] || { echo "error: missing $f" >&2; exit 2; }
done

# Same part, HLS clock target and design macros as the archived C17 run
# (provenance/C17_hls_config.original.cfg); only the testbench differs.
FLAGS="-std=c++14 -ffp-contract=off -DEXP_FIXED=1 -DEXP_T=4 -DEXP_W_BITS=10 -DEXP_A_BITS=10 -DEXP_ALL_CONTINUOUS=1 -DEXP_ONLINE_PAD=1 -DEXP_STORAGE=1"
mkdir -p "$WORK"
cat > "$WORK/hls_config.cfg" <<EOF
part=xck26-sfvc784-2LV-c

[hls]
flow_target=vivado
clock=4ns
package.output.format=ip_catalog
syn.top=srcnn
csim.O=true
syn.cflags=$FLAGS
tb.cflags=$FLAGS -I$PKG/src
syn.file=$PKG/src/srcnn.cpp
syn.file=$PKG/src/conv1.cpp
tb.file=$ROOT/test/csim.cpp
tb.file=$ROOT/test/tb_conv1.cpp
tb.file=$ROOT/test/tb_srcnn.cpp
tb.file=$ROOT/test/util.cpp
tb.file=$ROOT/test/set5
tb.file=$ROOT/src/weights
EOF

vitis-run --mode hls --csim --config "$WORK/hls_config.cfg" --work_dir "$WORK"
log=$(find "$WORK" -name '*_csim.log' -path '*report*' | head -n 1)
[ -n "$log" ] || { echo "error: C simulation log not found under $WORK" >&2; exit 1; }
grep -E 'Golden Reference|MSE' "$log"
