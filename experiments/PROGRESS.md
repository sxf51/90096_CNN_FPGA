# Current progress

<!-- ROM_CLOCK_CURRENT -->

## Active docs/0005 workstream

C18 leads; F51 verified; F50 RTL and C17 HLS run concurrently. C18/C14 is the verified mixed T4 leader at 5 ns and 1.503160 ms, with an archived IP handoff. W30/W28 closes 4.5 ns at 2.472471 ms for uniform T8. F51/F48 independently passes 5 ns at 2.678855 ms; its five paths and physical hierarchy are archived. C18 checkpoint paths and W32 final post-route-optimization generated paths are also archived. F50 RTL and C17 HLS are running concurrently; C16 has completed C simulation and waits for synthesis budget. W31 is temporarily held by the auto-resuming F50 priority supervisor. Finish these four results. Once C16/C17 pass all 13 images and HLS screening, plan fresh changed-parameter cosim C19/C20 and staged implementation C21/C22; recheck unused IDs before planning. Initial physical targets are 4.5 ns for T8 and 5 ns for T4, with no lower RTL cycle bound. W31 closing 5 ns can trigger a separate ROM 4.5 ns probe, which is not yet planned or running. No resource-driven T4 ROM retry is currently needed. Keep one heavy task, budgeted light admission, the 18 GiB implementation registration and serial_after_oom while legacy workers exist. Refresh CSV analyses and plots, then perform the final two-location audit. Precision, runtime interfaces and physical gates stay strict. No board results exist.

See [ROM_CLOCK.md](ROM_CLOCK.md) and [rom_clock_state.json](rom_clock_state.json). Current gates override historical missing-comic/HLS-only/serial-lock wording below: complete course Set14=13; final feasibility=routed; concurrency=one heavy task with light jobs admitted by measured headroom.

<!-- ROM_CLOCK_CURRENT -->

Updated 2026-10-12T15:27:50+00:00 from archived measurements.

Branch: `exp/explore-arch`, from phase-one final `2fa7249`. Original46 files and45 first-phase design files remain checksum protected. Preserve user README/.gitignore/docs-index edits.

## Completed

First phase stages0-6 closed in E099. The current complete course Set14 has13 images and final feasibility uses independently routed gates. Historical provisional statuses remain unchanged. No board validation has run.

141 architecture records completed: P01, P02, W01, P03, W02, P04, W03, P05, P06, P07, G01, G02, S01, G03, S02, P10, C01, C02, C03, S03, P11, S04, W07, S05, P12, W04, W05, W06, S06, F01, W10, F02, W11, C08, W12, P08, F03, W08, C09, W09, F08, F16, F17, F18, F19, C04, F04, W13, C07, F13, F05, C12, F06, F14, F07, W17, C05, P09, F09, C06, F15, W18, F10, F20, F11, F21, F22, F12, F23, W14, W15, W16, F24, C10, F25, C11, F80, F81, F82, F83, F84, F85, P13, P14, P15, P16, F86, F87, F88, F89, F26, F27, F94, F31, F92, F28, F93, W19, F29, F30, W20, W21, F96, F95, F97, F98, W22, F34, F32, F33, F38, F35, F36, F37, W24, W26, F41, W27, F42, F47, C13, W25, F40, F39, F45, F46, F43, C14, W28, F44, F49, F48, W29, W23, C15, F52, W32, C18, W30, F51, C17.

Fastest resource-feasible exact frame estimate: [W24](W24_constant_rom_T8/W24.md); 1.7460189000000002ms, T=8, DSP=630.0, BRAM18K=138.0, LUT=53316.0, deltaPSNR=-0.0695141811880653dB. HLS estimates are distinct from route/RTL results.

## Outstanding

Exploration: all required runs archived.

Final verification: F50, W31, C16.

## Weight Loading Workstream

Plan: [docs/0004](../docs/0004-t8-weight-loading-plan.md). Archived. Current gates and next tasks are in docs/0005 and the active block above.

2026-10-12 用户决定降低优先级: F88/F90/F91. F88 was deliberately interrupted with SIGTERM to release the hardware slot; no RTL verdict or measured cycles exist. P14-P16/F86/F87 already completed before the new priority and remain archived. F85/P13 were recovered without rerunning.

Current user decisions supersede the initial WS0 defaults: complete course set=13 images; final resources=routed; ROM=exploratory; scheduling=one heavy task with memory-bounded light jobs under docs/0005 section6.1. Runtime parameter interfaces, strict precision and no-push rules remain.

P08 routed DSP48E2 inspection confirms one cell, AMULTSEL=AD and ADREG=1. W10-W13/C07 split transformed-window generation from a fixed16384*(4*T) MAC loop to remove W07's conditional264x264 bound inflation. C08/C09 use independently verified Conv2-only8-bit weights, retain ten-bit activations, and omit coefficient residual repair. Vitis rejects the original8000-bit Conv3 stream at its4096-bit limit; F08-F12/W14-W16/C10-C11 use independent two4000-bit-stream retries with identical arithmetic. F13-F15 isolate Conv3 window rotation and tree-register overhead using F08's measured7013 multiplexer LUT. All new designs are independent; source and paper plans are committed before runs. Re-run CSV analyses, equivalent offline-weight archives and all plots after all evidence arrives. Finalize ARCH_SUMMARY.md, both checksum audits and final F99 commit.

F24 independently rewrites only F23's Conv1 weight-loader indices after its report locates the2.822ns global critical path in a15-bit address multiplier; the dataflow region is2.377ns. Keep T16, quantization and inference fixed, account for nested-load restart overhead, and accept only measured exact/resource-feasible results.

## Recovery

Read ARCH_SUMMARY.md, LOG.md, PHASE2_HANDOFF.md and arch_state.json. Check active local exec sessions and remote processes before resuming pending IDs; completed and active workspaces cannot be overwritten. SSH uses `ssh -F ../ssh-config -o BatchMode=yes xiaoxin-ubuntu`; remote root `/home/lipuze/amdprojects/90096_CNN_FPGA`; Vitis settings `/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh`. The current one-heavy scheduler uses `.memory_scheduler.json`; preserve serial_after_oom=true while old waiting workers exist. Recover only provably unlaunched waiting workers with `exp/resume_waiting.py`, and collect completed jobs with `--collect-only`. 60-minute csynth/45-minute issue tuning/six-hour cosim. Local plotting interpreter `workspace/exp_runs/_tools/venv/bin/python`. Never run script.py, modify protected data/designs, push, or substitute predicted results for actual evidence.
