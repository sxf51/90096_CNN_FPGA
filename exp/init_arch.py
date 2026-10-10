#!/usr/bin/env python3
"""Freeze first-phase designs and migrate the architecture result schema."""
import hashlib
import json
import subprocess
from run_exp import ROOT, append_log, check_protected, ensure_results_schema, lock, utc, write_json


def main():
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    if branch != "exp/explore-arch":
        raise RuntimeError("Architecture initialization requires exp/explore-arch")
    check_protected()
    manifest = ROOT / "experiments/phase1_design_checksums.txt"
    if manifest.exists():
        raise RuntimeError("First-phase design manifest already exists")
    paths = sorted(path for path in (ROOT / "designs").rglob("*") if path.is_file() and
                   path.suffix in {".h", ".cpp", ".inc"})
    manifest.write_text("".join(hashlib.sha256(path.read_bytes()).hexdigest() + "  " +
                                path.relative_to(ROOT).as_posix() + "\n" for path in paths))
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        ensure_results_schema(ROOT / "experiments/results.csv")
        append_log("S00: architecture branch initialized from completed first phase; result schema gains series; "
                   f"{len(paths)} first-phase source files frozen by SHA256; no prior design modified")
    state = {"time": utc(), "branch": branch, "first_phase_head": subprocess.check_output(
        ["git", "rev-parse", "exp/overnight-1011"], cwd=ROOT, text=True).strip(),
        "frozen_design_files": len(paths), "full_set14": False, "hardware_parallelism": 1,
        "next": "Commit pre-implementation P/W PE estimates, implement independent kernels, then run them."}
    write_json(ROOT / "experiments/arch_state.json", state)
    (ROOT / "experiments/PROGRESS.md").write_text(
        "# Current progress\n\nBranch: `exp/explore-arch`, from completed `exp/overnight-1011` at `" + state["first_phase_head"] + "`.\n\n"
        "## Completed\n\nFirst phase stages0-6 closed in E099. E043 is fastest resource-feasible supplied-image candidate:6.93923049ms, DSP505, BRAM18K168, LUT55325. E069 matches every output bit on all13 supplied images. Missing comic prevents complete Set14 acceptance. E070 routed implementation of E039 fails timing with WNS-1.277ns. See SUMMARY.md and PHASE2_HANDOFF.md.\n\n"
        "Architecture infrastructure supports series, immutable preplanned archives and additional first-phase design checksums. Original46-file SHA256 manifest remains unchanged. User README/.gitignore/docs-index edits remain outside task commits.\n\n"
        "## Next Action\n\nPlan and commit P/W microbenchmarks before implementation. Then execute G three-way Conv3 comparison, S dataflow/DDR/tile comparison, full P/W, C combinations and F scheduling/memory/timing ideas. Record estimates vs actuals and explain deviations over20%. Final best2-3 provisional candidates receive full supplied-image validation, implementation and two-frame cosim.\n\n"
        "## Recovery\n\nRead PROGRESS.md, ARCH_SUMMARY.md when present, LOG.md and arch_state.json. Remote host xiaoxin-ubuntu; root /home/lipuze/amdprojects/90096_CNN_FPGA; Vitis2026.1 settings /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh. Serialize hardware jobs with .synthesis.lock;60-minute csynth,45-minute issue limit,6-hour cosim. Keep Windows reproduction and missing comic in pending decisions. Never run script.py, overwrite an existing run, modify protected originals or first-phase designs, push, or claim board validation.\n")
    check_protected()
    print(json.dumps(state))


if __name__ == "__main__":
    main()
