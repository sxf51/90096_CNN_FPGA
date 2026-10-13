#!/usr/bin/env python3
"""Preplan same-weight/changed-input verification of an exact all-image ROM parent."""
import argparse
import json
import subprocess
import sys
from plan_arch import plan
from reproduce_exp import archived
from run_exp import ROOT, number
from verify_exp import check_image_validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent")
    parser.add_argument("--id", required=True)
    args = parser.parse_args()
    archive = archived(args.parent)
    parent = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    check_image_validation(parent, parent)
    if parent.get("top") != "srcnn_rom" or parent.get("hls_screen_pass") is not True:
        raise RuntimeError("Parent is not a numerically accepted and HLS-screened ROM candidate")
    estimates = {key: number(metrics.get(key)) for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF")}
    estimates.update(T=parent["T"], latency_cycles=547500,
                     basis="Use the exact parent HLS resource report. Expected RTL latency547500 is "
                           "F97 measured558758 minus approximately11230 parameter startup. "
                           "The 558758-cycle acceptance bound is unchanged, and no timing/board inference is made.")
    config = {"id": args.id, "name": "rom_changed_input_cosim_" + args.parent,
              "series": args.id[0], "stage": "rom_clock_wsB_cosim", "scope": "frame",
              "design": parent["design"], "clock": parent["clock"], "settings": parent["settings"],
              "operation": "cosim", "verify_parent": args.parent, "validation_parent": args.parent,
              "verification_testbench": "exp/tb/rom_cosim.cpp", "same_weights_changed_input": True,
              "rtl_max_cycles": 558758, "memory_scheduler": True, "resource_policy": "routed",
              "required_image_count": 13, "timeout": 21600, "estimates": estimates,
              "purpose": "WS-B finite-FIFO RTL validation of frozen " + args.parent +
                         ". Two transactions use unchanged compile-time ROM weights, first butterfly and "
                         "then a different lenna input. Require every output bit to match E017/independent "
                         "w10a10 reference, original six-pixel border MSE, finite-FIFO progress and measured "
                         "latency no greater than W21's558758 cycles. A changed-runtime-parameter test is "
                         "inapplicable because the ROM top has no parameter port.",
              "changes": "Copy the frozen ROM HLS workspace, override only the verification testbench and "
                         "keep RTL/init hashes identical before/after cosimulation. Enable dataflow profiling.",
              "interpretation": "Measure actual latency/interval and removed-parameter startup versus F97; "
                                "explain deviations above20%. Same weights and changed input prove state "
                                "reset for this ROM contract, not arbitrary runtime parameters.",
              "conclusion": "Keep ROM as an exploratory candidate pending routed timing/resource gates "
                            "and the user's board-version decision."}
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id, "plan_rom_changed_input_cosim"],
                   cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
