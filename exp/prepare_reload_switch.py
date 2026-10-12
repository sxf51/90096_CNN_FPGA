#!/usr/bin/env python3
"""Commit WS-F hypotheses before copying the immutable C13 parameter banks."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from reproduce_exp import archived
from run_exp import ROOT, check_protected


DESIGN = "designs/winograd_prepacked_t4_reload_v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--mode", choices=("quality", "sequence", "cold", "regression"))
    parser.add_argument("--copy-parent", action="store_true")
    args = parser.parse_args()
    check_protected()
    parent = archived("C13")
    if args.copy_parent:
        record = ROOT / "experiments" / (args.id + "_reload_switch_quality") / "plan.json"
        subprocess.run(["git", "cat-file", "-e", "HEAD:" + str(record.relative_to(ROOT))],
                       cwd=ROOT, check=True)
        source = parent / "source"
        expected = json.loads((parent / "config.json").read_text())["source_sha256"]
        actual = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in source.rglob("*") if p.is_file()}
        if actual != expected or (ROOT / DESIGN).exists():
            raise RuntimeError("Frozen source mismatch or new design already exists")
        shutil.copytree(source, ROOT / DESIGN)
        return
    if args.mode is None:
        parser.error("--mode is required for a plan")
    base = json.loads((parent / "plan.json").read_text())["configuration"]
    regression = args.mode == "regression"
    estimates = dict(DSP=1032, BRAM18K=146, URAM=0, LUT=128900, FF=193500, T=4,
                     latency_cycles=300632, loaded_cycles=300632,
                     reuse_cycles_low=289632, reuse_cycles_high=296132,
                     Conv1_DSP=576, Conv2_DSP=256, Conv3_DSP=200,
                     basis="Frozen C13 HLS1032DSP/146BRAM18K/127966LUT; C14 RTL300632cycles. "
                           "C18 independently closed5ns. Keep arithmetic, banks, FIFOdepths and T4 folds. "
                           "Budget934extraLUT for load predicate/control and one loaded-state register. "
                           "A skip removes all8129float parameter reads and Winograd transform/load loops; "
                           "predict4500-11000exposed saved cycles, not the entire overlapped parameter process. "
                           "These are hypotheses; actual per-call AXI handshakes, cycles, route resources and "
                           "reset/cold-start behavior require independent evidence.")
    config = {**base, "id": args.id, "name": "legacy_C13_regression" if regression else
              "reload_switch_" + args.mode, "series": args.id[0], "stage": "rom_clock_wsF",
              "design": base["design"] if regression else DESIGN,
              "control_experiment": "C13", "estimates": estimates,
              "top": "srcnn" if regression else "srcnn_reload", "required_image_count": 13,
              "resource_policy": "routed", "memory_scheduler": True,
              "set14": args.mode in {"quality", "regression"},
              "csim_only": args.mode != "quality", "reload_switch_mode": args.mode,
              "defines": {**base["defines"], **({} if regression else {"EXP_RELOAD_SWITCH": 1})},
              "purpose": "WS-F: gate runtime parameter reading/transformation/private-bank loading inside "
                         "unconditionally called DATAFLOW processes. Retain the original srcnn wrapper with "
                         "load=true and add srcnn_reload with a control load_params bit. Force the first call "
                         "to load even when its flag isfalse; skipped calls must ignore all incoming parameter "
                         "pointers and reuse the most recent persistent banks. Require unchanged E065 exact "
                         "arithmetic, six-pixel border checking and13-image deltaPSNR>=-0.1dB. "
                         "Validation mode: " + args.mode + ".",
              "changes": "Use independently copied frozen C13 sources; add only the user-approved "
                         "parameter-load predicate and compatible wrapper. Shared quality testbench changes "
                         "are guarded by EXP_RELOAD_SWITCH; old C13 receives a fresh regression ID. "
                         "No original tests, golden data, thresholds or first-phase designs change.",
              "interpretation": "Compare measured load/reuse/cold-start exactness, AXI traffic and per-call "
                                "cycles with the committed estimates. Explain deviations above20%. "
                                "HLS estimates cannot prove reset persistence, zero RTL AXI traffic or routing.",
              "conclusion": "After all C checks and the legacy regression, plan independent multi-call "
                            "RTL verification and staged5ns routing. Keep C18 as fallback until all gates pass."}
    config.pop("synthesis_after", None)
    config.pop("quality_reference", None)
    if args.mode in {"sequence", "cold"}:
        config.update(tb_files=["exp/tb/validate_reload_switch.cpp", "src/weights", "test/set5", "test/set14"])
        config["defines"].update(EXP_COLD_START=int(args.mode == "cold"),
                                 EXP_FRAMES=1 if args.mode == "cold" else 4)
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id,
                    "plan_" + config["name"]], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
