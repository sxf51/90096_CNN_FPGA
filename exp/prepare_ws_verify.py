#!/usr/bin/env python3
"""Plan fresh WS2/WS3 verification IDs from immutable measured parents."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from analyze_arch import eligible
from plan_arch import plan
from reproduce_exp import archived
from run_exp import ROOT, check_protected, number
from verify_exp import check_image_validation, diagnostic_parent, screened_parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent")
    parser.add_argument("--id", required=True)
    parser.add_argument("--operation", choices=("all", "cosim", "impl"), required=True)
    parser.add_argument("--validation-parent")
    parser.add_argument("--implementation-clock", type=float)
    parser.add_argument("--implementation-threads", type=int, choices=(1, 2, 4))
    parser.add_argument("--staged-implementation", action="store_true",
                        help="Run synthesis/report and implementation/report in separate Vivado processes")
    parser.add_argument("--rtl-min-cycles", type=int)
    parser.add_argument("--rtl-max-cycles", type=int)
    parser.add_argument("--template")
    parser.add_argument("--diagnostic", action="store_true")
    parser.add_argument("--reload-params", action="store_true",
                        help="Use independent exact changed-parameter two-frame testbench (cosim only)")
    parser.add_argument("--reload-switch", action="store_true",
                        help="WS-F four-call exact reuse/reload verification with parameter AXI observation")
    parser.add_argument("--rationale", help="Measured trigger and conservative decision to archive before execution")
    args = parser.parse_args()
    check_protected()
    archive = archived(args.parent)
    observed = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    base = json.loads((archive / "plan.json").read_text())["configuration"]
    probe = {"operation": args.operation, "diagnostic_infeasible_parent": args.diagnostic,
             "resource_policy": base.get("resource_policy")}
    if not eligible(metrics, base) and not diagnostic_parent(probe, metrics) and not screened_parent(probe, metrics, observed):
        raise RuntimeError("Parent is not an exact resource/quality-accepted frame point")
    if args.diagnostic and args.operation != "impl":
        raise RuntimeError("Diagnostic infeasible parents are only permitted for implementation")
    if args.reload_params and (args.operation != "cosim" or base.get("precision") not in
                              {"w10a10acc23", "w10_8_10a10acc23_21_23"}):
        raise RuntimeError("Changed-parameter testbench requires a verified ten-bit-activation cosimulation")
    if args.reload_switch and (args.operation != "cosim" or args.reload_params or
                              base.get("top") != "srcnn_reload" or
                              base.get("precision") != "w10_8_10a10acc23_21_23"):
        raise RuntimeError("WS-F observation requires the independently validated mixed srcnn_reload top")
    if args.rtl_min_cycles is not None or args.rtl_max_cycles is not None:
        if args.operation != "cosim" or any(value is not None and value < 1 for value in
                                           (args.rtl_min_cycles, args.rtl_max_cycles)):
            raise RuntimeError("Positive RTL cycle bounds require cosimulation")
        if (args.rtl_min_cycles is not None and args.rtl_max_cycles is not None and
                args.rtl_min_cycles > args.rtl_max_cycles):
            raise RuntimeError("RTL lower bound exceeds upper bound")
    if args.operation != "impl" and (args.implementation_clock is not None or args.template or args.implementation_threads is not None):
        raise RuntimeError("Implementation options require operation=impl")
    if args.staged_implementation and (args.operation != "impl" or args.template):
        raise RuntimeError("Staged implementation requires an independently packaged implementation")
    if args.validation_parent:
        if args.operation == "all":
            raise RuntimeError("An all-image run must produce its own validation evidence")
        full = archived(args.validation_parent)
        check_image_validation(observed, json.loads((full / "config.json").read_text()))
    estimates = {key: number(metrics.get(key)) for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF", "latency_cycles")}
    estimates.update(T=number(metrics["T_target"]),
                     basis="Frozen "+args.parent+" HLS resource/cycle measurements. Full-image C validation preserves arithmetic; RTL includes finite-FIFO/AXI behavior. Physical resources and timing remain unknown until routed reports. No board measurement is inferred.")
    config = {"id": args.id, "name": "ws_"+args.operation+"_"+args.parent,
              "series": args.id[0], "stage": "arch_ws_verify", "scope": "frame",
              "design": base["design"], "clock": base["clock"], "settings": base["settings"],
              "estimates": estimates,
              "changes": "Use frozen parent "+args.parent+" sources and flags in an independent verification workspace; no quantization, parameter interface, dataset, threshold or parent-workspace changes.",
              "interpretation": "Keep parsed HLS, RTL and routed results separate. Missing comic prevents complete Set14 acceptance; retain failed timing, deadlock, host OOM and timeout evidence.",
              "conclusion": "Compare measured frame cycles and implementation timing before selecting the final integration candidate. Review unattended section6 decisions with the user tomorrow."}
    if base.get("resource_policy") == "routed":
        config.update(resource_policy="routed", memory_scheduler=base.get("memory_scheduler", False),
                      required_image_count=13,
                      interpretation="Set14 is the complete13-image course-provided set. Final acceptance "
                                     "requires independently routed setup/hold, route status and resource gates; "
                                     "HLS screening cannot establish feasibility. Keep RTL/route evidence distinct.")
    source = None
    if args.operation == "all":
        if base.get("precision") != "w10a10acc23":
            raise RuntimeError("No all-image reference configured for this precision")
        source = archive / "source"
        hashes = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in source.rglob("*") if path.is_file()}
        if not hashes or hashes != observed.get("source_sha256"):
            raise RuntimeError("Parent source snapshot mismatch")
        config = {**base, **config, "design": "designs/ws_validate_"+args.id,
                  "control_experiment": args.parent, "csim_only": True, "set14": True,
                  "quick": True, "defines": {**base.get("defines", {}), "EXP_FRAMES": 2},
                  "numpy_reference": "exp/numeric_reference/w10a10/numpy_reference",
                  "purpose": "Validate frozen "+args.parent+" on all13 supplied Set14 pairs and two complete butterfly calls. Every output bit must match the independently ap_fixed-verified reference, six-pixel borders remain checked, and deltaPSNR must be>=-0.1dB. Missing comic remains explicit."}
        config.pop("quality_reference", None)
        config.pop("synthesis_after", None)
    else:
        config.update(operation=args.operation, verify_parent=args.parent,
                      timeout=21600 if args.operation == "cosim" else 10800,
                      purpose="Verify frozen "+args.parent+" using "+args.operation+" in a new workspace. "+
                              (("Run four complete load/reuse/reload/retain transactions" if args.reload_switch else
                                "Run two complete butterfly transactions") +
                               " with finite-FIFO profiling and deadlock detection; measure actual latency and interval under a six-hour timeout."
                               if args.operation == "cosim" else
                               "Run serial Vivado synthesis, placement and routing; archive actual WNS/TNS and resources under a three-hour timeout. HLS resource gates remain unchanged."))
        if base.get("resource_policy") == "routed":
            config["purpose"] = config["purpose"].replace("HLS resource gates remain unchanged.",
                                                         "Final resource gates use the independent routed report.")
        for key, value in (("rtl_min_cycles", args.rtl_min_cycles), ("rtl_max_cycles", args.rtl_max_cycles)):
            if value is not None:
                config[key] = value
                config["purpose"] += " Require " + key + "=" + str(value) + "."
        if args.validation_parent:
            config["validation_parent"] = args.validation_parent
        if args.operation == "impl":
            config.update(implementation_backend="serial_generated_flow" if args.template else "serial_packaged_flow",
                          verification_hook="exp/vivado_serial_hook.tcl")
            if args.implementation_threads is not None:
                config["implementation_threads"] = args.implementation_threads
                config["changes"] += f" Limit per-run placement/routing to {args.implementation_threads} threads while synthesis remains single-threaded; preserve the serial hardware lock."
            if not args.template:
                config["implementation_driver_template"] = "F89"
            if args.staged_implementation:
                config["implementation_backend"] = "staged_packaged_flow"
                config["changes"] += (" Exit Vivado after synthesis/report, then reopen the new project "
                                      "in a fresh process for implementation/report; retain the cumulative "
                                      "three-hour tool timeout and one-heavy scheduling.")
            if args.template:
                config["implementation_template"] = args.template
            if args.implementation_clock is not None:
                if args.implementation_clock <= 0:
                    raise RuntimeError("Implementation clock must be positive")
                config["implementation_clock_ns"] = args.implementation_clock
                config["changes"] += " Change only the implementation clock constraint; preserve parent HLS RTL."
            if args.diagnostic:
                config["diagnostic_infeasible_parent"] = True
                config["purpose"] += " Diagnostic calibration only: the parent remains HLS-resource-infeasible and cannot enter accepted rankings."
    if args.rationale:
        config["purpose"] += "\n\nDecision basis: "+args.rationale
        config["estimates"]["basis"] += " Decision basis: "+args.rationale
    if args.reload_params:
        precision_reference = "E065 mixed Conv2-w8" if base.get("precision") == "w10_8_10a10acc23_21_23" else "E017"
        config.update(reload_params=True, verification_testbench="exp/tb/validate_reload.cpp")
        config["purpose"] += " The independent second transaction changes weights/biases and uses constant0.5 input; every pixel must equal104/256 exactly. The first remains " + precision_reference + "-exact butterfly with unchanged border MSE."
        config["changes"] += " Override only verification C++ testbench, archive its SHA256/source commit and preserve identical parent RTL."
    if args.reload_switch:
        config.update(reload_switch_validation=True, parameter_axi_monitor=True, verification_frames=4,
                      verification_testbench="exp/tb/validate_reload_switch.cpp")
        config["purpose"] += (" Run load/reuse/reload/latest-bank retention as four complete transactions. "
                              "Butterfly and ignored-pointer lenna must be E065-exact; constructed loaded "
                              "and retained outputs must equal104/256 everywhere. Require zero parameter "
                              "AXI valid cycles and handshakes on both skipped calls and no parameter writes. "
                              "Each skipped-call latency must not exceed its corresponding loaded call.")
        config["changes"] += (" Use documented cosim.setup=true, add a read-only AXI observer only to the "
                              "generated simulation testbench, then execute the unchanged generated simulation "
                              "and RTL post-check driver with a cumulative six-hour tool limit. Preserve "
                              "deadlock detection, FIFO profiling and synthesis RTL SHA256 before/after. "
                              "Archive every transaction's cycles and bus counts; do not use the old two-call gate.")
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id,
                    "plan_"+config["name"]], cwd=ROOT, check=True)
    if source is not None:
        target = ROOT / config["design"]
        if target.exists():
            raise RuntimeError("Validation source directory already exists")
        shutil.copytree(source, target)
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id,
                        "freeze_validation_parent"], cwd=ROOT, check=True)
    print("Prepared", args.id, "; run: python3 exp/run_queue.py", args.id)


if __name__ == "__main__":
    main()
