#!/usr/bin/env python3
"""Commit WS-F hypotheses before copying immutable parameter-bank designs."""
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
GUARD_DESIGN = "designs/winograd_prepacked_t4_reload_guard_v1"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--mode", choices=("quality", "sequence", "cold", "regression"))
    parser.add_argument("--copy-parent", action="store_true")
    parser.add_argument("--guard-bias3", action="store_true",
                        help="Plan an independent C23 retry with an explicitly guarded scalar bias load")
    args = parser.parse_args()
    check_protected()
    if args.guard_bias3 and args.mode == "regression":
        parser.error("The scalar-load retry uses its own design; the frozen legacy regression stays unchanged")
    parent_id = "C23" if args.guard_bias3 else "C13"
    design = GUARD_DESIGN if args.guard_bias3 else DESIGN
    prefix = "reload_guard_" if args.guard_bias3 else "reload_switch_"
    parent = archived(parent_id)
    if args.copy_parent:
        record = ROOT / "experiments" / (args.id + "_" + prefix + "quality") / "plan.json"
        subprocess.run(["git", "cat-file", "-e", "HEAD:" + str(record.relative_to(ROOT))],
                       cwd=ROOT, check=True)
        source = parent / "source"
        expected = json.loads((parent / "config.json").read_text())["source_sha256"]
        actual = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in source.rglob("*") if p.is_file()}
        if actual != expected or (ROOT / design).exists():
            raise RuntimeError("Frozen source mismatch or new design already exists")
        shutil.copytree(source, ROOT / design)
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
    if args.guard_bias3:
        estimates.update(LUT=129000, FF=194150,
                         basis="Frozen C23 HLS1032DSP/146BRAM18K/128840LUT/193984FF and C14 "
                               "accepted300632loaded RTL cycles. C27's first skipped call observes "
                               "one4byte parameter read; its generated top unconditionally reads "
                               "biases3[0] before passing a scalar into the guarded loader. "
                               "Capture that scalar only inside the top do_load branch through "
                               "a const volatile pointer; keep all MACs,banks,FIFOdepths,T4,8129loaded "
                               "values and E065 arithmetic. Budget160LUT/166FF for guard/mux/control; "
                               "no multiplier or frame storage is added. Loaded/reuse cycle estimates "
                               "remain hypotheses; require independent zero-AXI RTL evidence and5ns routing.")
    config = {**base, "id": args.id, "name": "legacy_C13_regression" if regression else
              prefix + args.mode, "series": args.id[0], "stage": "rom_clock_wsF",
              "design": base["design"] if regression else design,
              "control_experiment": parent_id, "estimates": estimates,
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
    if args.guard_bias3:
        config["purpose"] = ("Repair C27's observed4byte skipped-call parameter read in an independent "
                             "C23-derived design. HLS scalarizes biases3[0] and hoists its read into "
                             "the top before the inner do_load guard. Explicitly capture the scalar "
                             "through a const volatile pointer only in the non-DATAFLOW top do_load "
                             "branch,then pass the value internally. Preserve the nine-argument reload "
                             "top,the compatible original wrapper,all arithmetic,parameter counts,FIFO "
                             "depths,loaded-state semantics,E065 precision and strict zero parameter "
                             "AR/R/AW/W activity on skipped calls. Validation mode: " + args.mode + ".")
        config["changes"] = ("Copy frozen C23 into a new design and change only the scalar Conv3 bias "
                             "capture and internal argument plumbing. A skipped call's zero placeholder "
                             "is unused and must not replace the retained bank. Preserve C23/C27 and "
                             "all original tests,thresholds,source workspaces and numeric references.")
        config["conclusion"] = ("Require all13-image quality,HLS screening,four-call C sequence and "
                                "fresh-process fallback before independent four-call monitored RTL. "
                                "Only a zero-AXI exact RTL pass permits fresh staged5ns routing.")
    if args.mode in {"sequence", "cold"}:
        config.update(tb_files=["exp/tb/validate_reload_switch.cpp", "src/weights", "test/set5", "test/set14"])
        config["defines"].update(EXP_COLD_START=int(args.mode == "cold"),
                                 EXP_FRAMES=1 if args.mode == "cold" else 4)
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id,
                    "plan_" + config["name"]], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
