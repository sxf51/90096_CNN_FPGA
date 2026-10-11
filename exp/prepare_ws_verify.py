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
from verify_exp import diagnostic_parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent")
    parser.add_argument("--id", required=True)
    parser.add_argument("--operation", choices=("all", "cosim", "impl"), required=True)
    parser.add_argument("--validation-parent")
    parser.add_argument("--implementation-clock", type=float)
    parser.add_argument("--template")
    parser.add_argument("--diagnostic", action="store_true")
    args = parser.parse_args()
    check_protected()
    archive = archived(args.parent)
    observed = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    base = json.loads((archive / "plan.json").read_text())["configuration"]
    probe = {"operation": args.operation, "diagnostic_infeasible_parent": args.diagnostic}
    if not eligible(metrics, base) and not diagnostic_parent(probe, metrics):
        raise RuntimeError("Parent is not an exact resource/quality-accepted frame point")
    if args.diagnostic and args.operation != "impl":
        raise RuntimeError("Diagnostic infeasible parents are only permitted for implementation")
    if args.operation != "impl" and (args.implementation_clock is not None or args.template):
        raise RuntimeError("Implementation options require operation=impl")
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
                              ("Run two complete butterfly transactions with finite-FIFO profiling and deadlock detection; measure actual latency and interval under a six-hour timeout."
                               if args.operation == "cosim" else
                               "Run serial Vivado synthesis, placement and routing; archive actual WNS/TNS and resources under a three-hour timeout. HLS resource gates remain unchanged."))
        if args.validation_parent:
            config["validation_parent"] = args.validation_parent
        if args.operation == "impl":
            config.update(implementation_backend="serial_generated_flow" if args.template else "serial_packaged_flow",
                          verification_hook="exp/vivado_serial_hook.tcl")
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
