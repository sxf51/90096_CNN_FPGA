#!/usr/bin/env python3
"""Refresh recovery state from completed evidence, never from expected results."""
import csv
import json
from analyze_arch import eligible
from prepare_final_arch import REQUIRED
from run_exp import ROOT, check_protected, lock, number, utc, write_json


def main():
    check_protected()
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    ids = {row["id"] for row in rows}
    pending = sorted(set(REQUIRED)-ids)
    accepted = []
    for row in rows:
        path = ROOT / "experiments" / row["md_path"].split("/")[0] / "config.json"
        if path.is_file() and eligible(row,json.loads(path.read_text())) and number(row["latency_ms_est"]) is not None:
            accepted.append(row)
    accepted.sort(key=lambda row:number(row["latency_ms_est"]))
    selection_path = ROOT / "experiments/final_selection.json"
    selection = json.loads(selection_path.read_text()) if selection_path.is_file() else {}
    final_pending = [exp_id for exp_id in selection.get("queue", []) if exp_id not in ids]
    ws_path = ROOT / "experiments/weight_loading_state.json"
    ws = json.loads(ws_path.read_text()) if ws_path.is_file() else None
    if ws:
        final_pending = [exp_id for exp_id in ws["verification_queue"] if exp_id not in ids]
    arch = [row for row in rows if row["series"]]
    probe_path = ROOT / "experiments/P08_builtin_mapping_implementation/primitive_probe.json"
    probe = json.loads(probe_path.read_text()) if probe_path.is_file() else {}
    state = {"branch":"exp/explore-arch","first_phase_head":"2fa7249eaecdfdc360d8d452fcbf52171c35abd2",
             "frozen_design_files":45,"full_set14":False,"hardware_parallelism":1,"time":utc(),
             "completed_architecture_ids":[row["id"] for row in arch],"pending_exploration_ids":pending,
             "pending_final_verification_ids":final_pending,"selected":selection.get("selected", []),
             "best_provisional":accepted[0] if accepted else None,
             "packing_pre_adder_verified":probe.get("pre_adder_used") is True,
             "next":ws["next"] if ws else "Finish existing queues, then final verification and closure."}
    if ws:
        state["weight_loading_workstream"] = ws
    rom_path = ROOT / "experiments/rom_clock_state.json"
    if rom_path.exists():
        rom = json.loads(rom_path.read_text())
        final_pending = list(dict.fromkeys(final_pending + [exp_id for exp_id in rom["experiment_ids"] if exp_id not in ids]))
        final_pending = [exp_id for exp_id in final_pending if exp_id not in rom.get("skipped_plans", {})]
        serial_after_oom = rom.get("hardware_serial_after_oom", False)
        state.update(full_set14=True, complete_image_count=13, resource_policy="routed",
                     hardware_parallelism=1 if serial_after_oom else 2 if rom.get("concurrency_policy") == "user_two_jobs" else None,
                     hardware_scheduler=("serial hardware fallback after measured OOM; two-task policy retained"
                                         if serial_after_oom else "user-authorized two-task scheduling with actual memory telemetry"
                                         if rom.get("concurrency_policy") == "user_two_jobs"
                                         else "validated memory-budget admission"),
                     pending_final_verification_ids=final_pending, skipped_conditional_plans=rom.get("skipped_plans", {}),
                     rom_clock_workstream=rom, next=rom["next"])
    write_json(ROOT / "experiments/arch_state.json",state)
    text = "# Current progress\n\nUpdated "+state["time"]+" from archived measurements.\n\n"
    text += "Branch: `exp/explore-arch`, from phase-one final `2fa7249`. Original46 files and45 first-phase design files remain checksum protected. Preserve user README/.gitignore/docs-index edits.\n\n"
    text += "## Completed\n\nFirst phase stages0-6 closed in E099. "
    text += ("The current complete course Set14 has13 images and final feasibility uses independently routed gates. Historical provisional statuses remain unchanged. "
             if rom_path.exists() else "Missing comic prevents complete Set14 acceptance; every supplied-image candidate is provisional. ")
    text += "No board validation has run.\n\n"
    text += str(len(arch))+" architecture records completed: "+", ".join(row["id"] for row in arch)+".\n\n"
    if accepted:
        best = accepted[0]
        text += "Fastest resource-feasible exact frame estimate: ["+best["id"]+"]("+best["md_path"]+"); "+best["latency_ms_est"]+"ms, T="+best["T_target"]+", DSP="+best["DSP"]+", BRAM18K="+best["BRAM18K"]+", LUT="+best["LUT"]+", deltaPSNR="+best["delta_psnr"]+"dB. HLS estimates are distinct from route/RTL results.\n\n"
    text += "## Outstanding\n\nExploration: "+(", ".join(pending) or "all required runs archived")+".\n\n"
    completed_label = ("all runnable planned operations archived, including failures/timeouts; conditional omissions listed below"
                       if state.get("skipped_conditional_plans") else
                       "all planned operations archived, including failures/timeouts")
    text += "Final verification: "+((", ".join(final_pending) or completed_label) if selection else "awaiting global candidate selection")+".\n\n"
    if rom_path.exists() and rom.get("skipped_plans"):
        text += "Conditional plans not run (failed prerequisite, no fabricated result):\n\n"
        text += "\n".join("- " + exp_id + ": " + record["reason"] for exp_id, record in rom["skipped_plans"].items()) + "\n\n"
    if ws:
        text += "## Weight Loading Workstream\n\nPlan: [docs/0004](../docs/0004-t8-weight-loading-plan.md). "
        text += ("Archived. Current gates and next tasks are in docs/0005 and the active block above.\n\n"
                 if rom_path.exists() else ws["next"] + "\n\n")
        text += "2026-10-12 用户决定降低优先级: F88/F90/F91. F88 was deliberately interrupted with SIGTERM to release the hardware slot; no RTL verdict or measured cycles exist. P14-P16/F86/F87 already completed before the new priority and remain archived. F85/P13 were recovered without rerunning.\n\n"
        text += ("Current user decisions supersede the initial WS0 defaults: complete course set=13 images; final resources=routed; ROM=exploratory; scheduling=explicit two-task mode with actual memory telemetry and the agreed serial hardware fallback after measured OOM. Runtime parameter interfaces, strict precision and no-push rules remain.\n\n"
                 if rom_path.exists() else "Section 6 conservative decisions: preserve runtime float weights and HLS resource gates; keep missing comic explicitly provisional; if serial implementation OOM recurs, archive evidence and continue WS2 without changing host swap or using an unverified machine. Revisit these decisions with the user tomorrow.\n\n")
    text += ("P08 routed DSP48E2 inspection confirms one cell, AMULTSEL=AD and ADREG=1. " if state["packing_pre_adder_verified"] else "P08 needs actual DSP48E2 pre-adder/register inspection. ")
    text += "W10-W13/C07 split transformed-window generation from a fixed16384*(4*T) MAC loop to remove W07's conditional264x264 bound inflation. C08/C09 use independently verified Conv2-only8-bit weights, retain ten-bit activations, and omit coefficient residual repair. Vitis rejects the original8000-bit Conv3 stream at its4096-bit limit; F08-F12/W14-W16/C10-C11 use independent two4000-bit-stream retries with identical arithmetic. F13-F15 isolate Conv3 window rotation and tree-register overhead using F08's measured7013 multiplexer LUT. All new designs are independent; source and paper plans are committed before runs. Re-run CSV analyses, equivalent offline-weight archives and all plots after all evidence arrives. Finalize ARCH_SUMMARY.md, both checksum audits and final F99 commit.\n\n"
    text += "F24 independently rewrites only F23's Conv1 weight-loader indices after its report locates the2.822ns global critical path in a15-bit address multiplier; the dataflow region is2.377ns. Keep T16, quantization and inference fixed, account for nested-load restart overhead, and accept only measured exact/resource-feasible results.\n\n"
    text += "## Recovery\n\nRead ARCH_SUMMARY.md, LOG.md, PHASE2_HANDOFF.md and arch_state.json. Check active local exec sessions and remote processes before resuming pending IDs; completed and active workspaces cannot be overwritten. SSH uses `ssh -F ../ssh-config -o BatchMode=yes xiaoxin-ubuntu`; remote root `/home/lipuze/amdprojects/90096_CNN_FPGA`; Vitis settings `/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh`. "
    text += ("The current two-task scheduler uses `.memory_scheduler.json`; recover only provably unlaunched waiting workers with `exp/resume_waiting.py`, and collect completed jobs with `--collect-only`. "
             if rom_path.exists() else "Hardware jobs serialize through `.synthesis.lock` for15GiB RAM. ")
    text += "60-minute csynth/45-minute issue tuning/six-hour cosim. Local plotting interpreter `workspace/exp_runs/_tools/venv/bin/python`. Never run script.py, modify protected data/designs, push, or substitute predicted results for actual evidence.\n"
    (ROOT / "experiments/PROGRESS.md").write_text(text)
    if (ROOT / "experiments/rom_clock_state.json").exists():
        from summarize_rom_clock import main as summarize_current_workstream
        summarize_current_workstream()
    print("Progress:",len(arch),"completed;",len(pending),"exploration and",len(final_pending),"final jobs pending")


if __name__ == "__main__":
    main()
