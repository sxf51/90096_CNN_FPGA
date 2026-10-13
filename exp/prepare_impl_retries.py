#!/usr/bin/env python3
"""Preplan serial Vivado retries without changing accepted HLS designs."""
import json
import subprocess
import sys
from pathlib import Path
from plan_arch import plan
from run_exp import ROOT, append_log, write_json


def main():
    selection_path = ROOT / "experiments/final_selection.json"
    selection = json.loads(selection_path.read_text())
    retries = []
    for exp_id, template, validation, parent in (
            ("F89", "F81", "F80", "F25"),
            ("F90", "F84", "F83", "F24"),
            ("F91", "F87", "F86", "F23")):
        original = json.loads((ROOT / "exp/configs" / (template+".json")).read_text())
        config = {**original, "id":exp_id, "name":"serial_vivado_impl_"+parent,
                  "implementation_backend":"serial_generated_flow",
                  "implementation_template":template,
                  "validation_parent":validation,
                  "verification_hook":"exp/vivado_serial_hook.tcl",
                  "purpose":"Retry physical implementation of "+parent+
                            " after F81's documented kernel OOM killed the main Vivado synthesis process while four worker processes were active. Reuse the original HLS-generated IP/BD flow, target clock and synthesis/implementation directives in an independent workspace. Add a formal pre-synthesis hook setting general.maxThreads and synth.maxThreads to1. Expect unchanged HLS compute/DSP/memory estimates; physical resources and slack remain unknown until reports. Reserve one hardware slot and do not change system swap or global tool settings.",
                  "changes":"Copy the completed original implementation template "+template+
                            "; regenerate its private project with a per-run serial synthesis hook. No C/C++ design, quantization, data, clock or numerical/resource-gate change.",
                  "interpretation":"Compare actual routed utilization/slack against the frozen accepted parent. Kernel OOM is a host-capacity failure, not evidence of FPGA resource or timing feasibility. The retry keeps the official generated flow and changes only tool parallelism.",
                  "conclusion":"Require actual routed reports; retain OOM/timeout/timing failures and the missing-comic precision limitation."}
        config["estimates"] = {**original["estimates"],
            "basis":original["estimates"]["basis"]+
                    " Serial host scheduling changes no arithmetic or hardware budget. F81 kernel evidence shows four approximately2.4GiB Vivado workers plus its main process exceed available memory; hypothesize one worker avoids that host OOM, not that timing closes."}
        plan(config)
        subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),exp_id,
                        "plan_serial_vivado_retry"],cwd=ROOT,check=True)
        retries.append(exp_id)
    selection["original_queue"] = list(selection["queue"])
    selection["implementation_retry_queue"] = retries
    selection["queue"].extend(retries)
    write_json(selection_path,selection)
    append_log("F89: preplanned F89/F90/F91 serial Vivado retries of F25/F24/F23 after confirmed F81 host OOM; original runs and gates remain frozen, no host/global-setting changes.")


if __name__ == "__main__":
    main()
