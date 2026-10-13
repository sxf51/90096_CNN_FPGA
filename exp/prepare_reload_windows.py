#!/usr/bin/env python3
"""Plan WS-G from frozen C17; permit source copying only after strict C31 RTL."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from reproduce_exp import archived
from rtl_acceptance import accepted_cosim
from run_exp import ROOT, check_protected

DESIGN = "designs/winograd_t4_windows32_reload_v1"


def source_hashes(source):
    return {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in source.rglob("*") if path.is_file()}


def reviewed_patch():
    folders = []
    for exp_id in ("C13", "C28"):
        config = json.loads((archived(exp_id) / "config.json").read_text())
        folder = ROOT / config["design"]
        if source_hashes(folder) != config["source_sha256"]:
            raise RuntimeError("Frozen transplant source mismatch: " + exp_id)
        folders.append(str(folder.relative_to(ROOT)))
    result = subprocess.run(["git", "diff", "--no-index", "--", *folders], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 1 or not result.stdout or result.stderr:
        raise RuntimeError("Expected a nonempty frozen C13-to-C28 source diff")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--mode", choices=("quality", "sequence", "cold"))
    parser.add_argument("--copy-parent", action="store_true")
    parser.add_argument("--review-diff", action="store_true",
                        help="Archive the frozen transplant patch and dry-run it against C17 without editing source")
    args = parser.parse_args()
    check_protected()
    parent = archived("C17")
    if args.review_diff:
        record = ROOT / "experiments" / (args.id + "_reload_windows_quality") / "plan.json"
        subprocess.run(["git", "cat-file", "-e", "HEAD:" + str(record.relative_to(ROOT))],
                       cwd=ROOT, check=True)
        patch = reviewed_patch()
        original = json.loads((parent / "config.json").read_text())["design"]
        subprocess.run(["git", "apply", "--check", "--directory=" + original, "-p3"],
                       input=patch, cwd=ROOT, check=True)
        (record.parent / "source_patch.diff").write_bytes(patch)
        print("Archived C13-to-C28 transplant patch; C17 dry-run passed, source unchanged")
        return
    if args.copy_parent:
        proof = archived("C31")
        rtl_config = json.loads((proof / "config.json").read_text())
        rtl_metrics = json.loads((proof / "metrics.json").read_text())
        verification = rtl_config.get("verification", {})
        if (not accepted_cosim(rtl_metrics, rtl_config) or
                verification.get("reload_switch_bit_exact") is not True or
                verification.get("skip_parameter_axi_zero") is not True):
            raise RuntimeError("WS-G requires accepted exact, zero-AXI C31 before source integration")
        record = ROOT / "experiments" / (args.id + "_reload_windows_quality") / "plan.json"
        subprocess.run(["git", "cat-file", "-e", "HEAD:" + str(record.relative_to(ROOT))],
                       cwd=ROOT, check=True)
        source = parent / "source"
        expected = json.loads((parent / "config.json").read_text())["source_sha256"]
        actual = source_hashes(source)
        if actual != expected or (ROOT / DESIGN).exists():
            raise RuntimeError("Frozen C17 source mismatch or new design already exists")
        shutil.copytree(source, ROOT / DESIGN)
        patch = reviewed_patch()
        if patch != (record.parent / "source_patch.diff").read_bytes():
            raise RuntimeError("Transplant patch differs from the reviewed archive")
        subprocess.run(["git", "apply", "--check", "--directory=" + DESIGN, "-p3"],
                       input=patch, cwd=ROOT, check=True)
        subprocess.run(["git", "apply", "--directory=" + DESIGN, "-p3"],
                       input=patch, cwd=ROOT, check=True)
        guard = archived("C28") / "source"
        expected = source_hashes(guard)
        guard_cpp = (guard / "srcnn.cpp").read_bytes()
        old = b"#pragma HLS STREAM variable=windows depth=2\n"
        if guard_cpp.count(old) != 1:
            raise RuntimeError("Expected one unchanged C28 transformed-window FIFO")
        expected["srcnn.cpp"] = hashlib.sha256(guard_cpp.replace(
            old, b"#pragma HLS STREAM variable=windows depth=32\n", 1)).hexdigest()
        if source_hashes(ROOT / DESIGN) != expected:
            raise RuntimeError("Integrated source differs beyond the reviewed reload/FIFO changes")
        print("Integrated only the reviewed guard diff into frozen C17; all source hashes verified")
        return
    if args.mode is None:
        parser.error("--mode is required for a plan")
    base = json.loads((parent / "plan.json").read_text())["configuration"]
    estimates = {
        "DSP": 1032, "BRAM18K": 146, "URAM": 0, "LUT": 128868, "FF": 193184,
        "T": 4, "latency_cycles": 273023, "loaded_cycles": 273023, "reuse_cycles": 268506,
        "Conv1_DSP": 576, "Conv2_DSP": 256, "Conv3_DSP": 200,
        "basis": "C17 HLS1032DSP/146BRAM18K/127985LUT/192308FF; transplanting only C13-to-C28 "
                 "adds their measured883LUT/876FF with unchanged DSP/BRAM. C20 measures273023loaded "
                 "RTL cycles; C22 independently closes5ns at59552LUT/100499FF/109BRAM18K. "
                 "C27's failed-but-archived AXI diagnostic saves4517cycles, suggesting273023-4517=268506 "
                 "reuse cycles and conditional1.342530ms at5ns. These reuse/combined estimates are "
                 "hypotheses: C27 was rejected, C31 must pass before integration, and the new design "
                 "must independently pass four exact zero-AXI RTL calls and routed gates. Preserve "
                 "C17's32-entry1728-bit window FIFO, all arithmetic,quantization,foldII1 and interfaces."
    }
    config = {**base, "id": args.id, "name": "reload_windows_" + args.mode,
              "series": args.id[0], "stage": "rom_clock_wsG", "design": DESIGN,
              "control_experiment": "C17", "required_integration_rtl": "C31",
              "top": "srcnn_reload", "required_image_count": 13, "resource_policy": "routed",
              "memory_scheduler": True, "set14": args.mode == "quality",
              "csim_only": args.mode != "quality", "reload_switch_mode": args.mode,
              "defines": {**base["defines"], "EXP_RELOAD_SWITCH": 1}, "estimates": estimates,
              "purpose": "WS-G: after strict four-call exact/zero-parameter-AXI C31 acceptance, copy frozen "
                         "C17 and transplant only the C13-to-C28 guarded reload interface and persistent "
                         "bank semantics. Retain C17 FIFO32,arithmetic,quantization,clock and replicate "
                         "padding. Require four-call load/ignored-pointer reuse/reload/latest-bank retention, "
                         "fresh-process flag0 forced loading and complete13-image E065 exactness with unchanged "
                         "deltaPSNR>=-0.1dB and six-pixel border checks. Validation mode: " + args.mode + ".",
              "changes": "Use a new frozen-C17 source copy only after this committed plan and C31 acceptance. "
                         "Apply the reviewed C13-to-C28 diff: srcnn_reload plus compatible srcnn wrapper, "
                         "do_load propagation,uninitialized persistent banks,params_loaded safety flag and "
                         "top-level guarded volatile Conv3 scalar-bias capture. Change no FIFO or MAC.",
              "interpretation": "Compare combined HLS resources and independent loaded/reuse RTL with "
                                "the estimates; explain deviations above20percent. A successful C simulation "
                                "cannot prove zero hardware parameter traffic or physical timing.",
              "conclusion": "After quality,HLS,sequence and cold-start gates, commit and run four monitored "
                            "RTL calls, then staged5ns routing. Report first-load and steady reuse separately; "
                            "only independently closed clocks establish IP times. Keep C22 as fallback."}
    config.pop("synthesis_after", None)
    config.pop("quality_reference", None)
    if args.mode in {"sequence", "cold"}:
        config["tb_files"] = ["exp/tb/validate_reload_switch.cpp", "src/weights", "test/set5", "test/set14"]
        config["defines"].update(EXP_COLD_START=int(args.mode == "cold"),
                                 EXP_FRAMES=1 if args.mode == "cold" else 4)
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id,
                    "plan_" + config["name"]], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
