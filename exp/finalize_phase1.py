#!/usr/bin/env python3
"""Wait for authorized phase-one runs, validate the best candidate, and close records."""
import csv
import json
import subprocess
import sys
import time
from run_exp import ROOT, append_log, check_protected, lock, number, utc, write_json

REQUIRED = {"E036", "E037", "E038", "E039", "E040", "E041", "E042", "E043", "E045", "E048",
            "E050", "E051", "E052", "E053", "E054", "E055", "E056", "E057", "E058", "E059",
            "E060", "E063", "E064", "E065", "E066", "E067"}


def read_rows():
    with lock(ROOT/"workspace/exp_runs/.results.lock", wait_timeout=120):
        return list(csv.DictReader((ROOT/"experiments/results.csv").open(newline="")))


def other_local_jobs():
    lines = subprocess.check_output(["ps", "-axo", "pid,command"], text=True).splitlines()
    return [line for line in lines if any(name in line for name in
        ("exp/run_queue.py", "exp/remote_exp.py", "exp/finish_coordinates.py"))]


def main():
    print("FINALIZER Waiting for phase-one required runs", flush=True)
    while not REQUIRED <= {r["id"] for r in read_rows()}:
        time.sleep(5)
    while other_local_jobs():
        time.sleep(5)
    rows = read_rows()
    accepted = [r for r in rows if r["id"].startswith("E") and
        r["design"].startswith(("designs/dataflow", "designs/scatter")) and r["status"] in {"pass", "provisional"} and
        r["csim_pass"] == "True" and number(r["delta_psnr"]) is not None and float(r["delta_psnr"]) >= -.1]
    best = min(accepted, key=lambda r: float(r["latency_ms_est"])) if accepted else None
    if best:
        base = json.loads((ROOT/f"exp/configs/{best['id']}.json").read_text())
        config = {**base, "id": "E069", "name": "final_candidate_all_supplied", "stage": 6, "csim_only": True,
                  "set14": True, "quick": True,
                  "numpy_reference": "exp/numeric_reference/w10a10/numpy_reference",
                  "purpose": f"Run the final measured first-phase candidate {best['id']} on every supplied "
                             "Set14 image, compare every output bit to the independently validated precision reference, "
                             "and measure border MSE. Missing comic remains explicit.",
                  "changes": "Frozen selected source and parameters; only full-image validation is enabled. "
                             "Hardware estimates remain in the linked parent experiment.",
                  "interpretation": "All 13 outputs must match the precision reference. This extends architecture "
                                    "coverage beyond butterfly and does not imply complete 14-image acceptance.",
                  "conclusion": "Preserve supplied-image numerical acceptance and separate implementation evidence."}
        config.pop("quality_reference", None)
        write_json(ROOT/"exp/configs/E069.json", config)
        subprocess.run([sys.executable, str(ROOT/"exp/remote_exp.py"), str(ROOT/"exp/configs/E069.json")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT/"exp/analyze_streaming.py")], check=True)
    subprocess.run([sys.executable, str(ROOT/"exp/summarize_phase1.py")], check=True)
    subprocess.run([str(ROOT/"workspace/exp_runs/_tools/venv/bin/python"), str(ROOT/"exp/plots/overview.py")], check=True)
    check_protected()
    ssh = ["ssh", "-F", str(ROOT.parent/"ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu",
           "cd /home/lipuze/amdprojects/90096_CNN_FPGA\nsha256sum -c experiments/checksums.txt"]
    subprocess.run(ssh, check=True)
    state = {"time": utc(), "branch": "exp/overnight-1011", "stages_executed": list(range(7)),
             "best_supplied_image_candidate": best["id"] if best else None,
             "protected_sha256": "all 46 files match locally and remotely", "full_set14": False,
             "pending": ["comic input/GT pair absent", "Windows reproduction unavailable", "no board validation"],
             "next": "Create exp/explore-arch from exp/overnight-1011, then execute S/G/P/W/C/F."}
    write_json(ROOT/"experiments/phase1_completion.json", state)
    text = "# Current progress\n\n"
    text += "First-phase execution complete on `exp/overnight-1011`; full Set14 acceptance remains pending because comic is absent. Read SUMMARY.md, LOG.md and phase1_completion.json.\n\n"
    text += "## Completed First Phase\n\nStages 0-6 executed; failed/infeasible/timeout records retained. All 46 protected files match local and remote SHA256. User README/.gitignore/documentation edits remain outside task commits. No push or board operation.\n\n"
    text += "Best supplied-image candidate: " + (best["id"] if best else "none") + ". Full candidate validation is E069 when a feasible candidate exists. Implementation is E070 when a provisional candidate qualified. Actual implementation and HLS estimates are distinct.\n\n"
    text += "## Next Action\n\nCreate `exp/explore-arch` from the completed first-phase branch. Phase two has not started. Read SUMMARY.md before proceeding. Preserve all first-phase designs; new designs get new directories and S/G/P/W/C/F IDs. Extend results.csv with series and write paper estimates before implementing each new idea. Start packing and Winograd microbenchmarks, then G, S, integration, combinations and free exploration.\n\n"
    text += "## Environment And Recovery\n\nSSH host xiaoxin-ubuntu, remote root /home/lipuze/amdprojects/90096_CNN_FPGA, Linux Vitis 2026.1 settings /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh. One synthesis/implementation/cosim at a time under the shared memory lock. Each synthesis timeout 60 minutes, issue tuning limit 45 minutes, final cosim timeout six hours. All raw HLS workspaces are immutable under workspace/exp_runs/. Never run script.py. Verify no first-phase subprocess remains before switching branch.\n\n"
    text += "## Numeric References\n\nE019/E017 establish uniform w10a10; E049 exhausts raw boundary casts. E065/E066 establish mixed Conv2-weight8 with ten-bit activations: delta PSNR -0.075890 dB on 13 images, butterfly bit identity. E062 demonstrates true eight-bit activations and Conv1/Conv3 weight8 do not pass. Conv3 quantized w10 coefficients fit signed8 without changing their fractional scale, enabling exact packing exploration. See SOURCES.md for WP486, DDR bandwidth and Winograd references.\n"
    (ROOT/"experiments/PROGRESS.md").write_text(text)
    append_log("E099: first-phase execution and final checksum audit complete; second-phase branch creation is next")
    subprocess.run([sys.executable, str(ROOT/"exp/commit_exp.py"), "E099", "phase1_complete"], cwd=ROOT, check=True)
    print("FINALIZER PHASE1 COMPLETE; create exp/explore-arch next", flush=True)


if __name__ == "__main__":
    main()
