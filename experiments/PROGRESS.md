# Current progress

<!-- ROM_CLOCK_CURRENT -->

## Active docs/0005 workstream

WS-0 complete; WS-B HLS/RTL passed; WS-C/D and T4 RTL controls running; implementation awaiting memory admission. Eight independent designs have complete13-image exactness and HLS results: W24 ROM, W27 FRP, F39 registeredConv3 operands, F40 featureFIFO16, F41 featureFIFO32, F42 reordered-raster buffer, F47 windowFIFO16 and C13 prepackedConv2 T4. W25 ROM two-frame RTL passed at554226cycles,4532cycles/0.81pct below W21; parameter load duration is not an additive frame penalty. F45 runs; W28/F48/F46/C14/F44/F43 queue for independent two-frame finite-FIFO checks. F43/W28 use the preplanned553171..564345cycle gate. WS-D functional PASS is separate from the2percent performance goal535741cycles. C13 uses E065 mixed precision and passes the routed-policy HLS screen at1032DSP/127966LUT/192308FF/263090cycles, preserving its historical HLS-infeasible status. W26 preparation failure remains archived. W23/W29/W30/C15 routing plans remain unlaunched:12.5GiB reservation plus2GiB floor requires14.5GiB available, exceeding idle host~13.4GiB. Preserve memory gates. F98 board handoff is archived; board measurements are pending.

See [ROM_CLOCK.md](ROM_CLOCK.md) and [rom_clock_state.json](rom_clock_state.json). Current gates override historical missing-comic/HLS-only/serial-lock wording below: complete course Set14=13; final feasibility=routed; concurrency=budgeted after WS-0 validation.

<!-- ROM_CLOCK_CURRENT -->

Updated 2026-10-12T06:12:09+00:00 from archived measurements.

Branch: `exp/explore-arch`, from phase-one final `2fa7249`. Original46 files and45 first-phase design files remain checksum protected. Preserve user README/.gitignore/docs-index edits.

## Completed

First phase stages0-6 closed in E099. Missing comic prevents complete Set14 acceptance; every supplied-image candidate is provisional. No board validation has run.

124 architecture records completed: P01, P02, W01, P03, W02, P04, W03, P05, P06, P07, G01, G02, S01, G03, S02, P10, C01, C02, C03, S03, P11, S04, W07, S05, P12, W04, W05, W06, S06, F01, W10, F02, W11, C08, W12, P08, F03, W08, C09, W09, F08, F16, F17, F18, F19, C04, F04, W13, C07, F13, F05, C12, F06, F14, F07, W17, C05, P09, F09, C06, F15, W18, F10, F20, F11, F21, F22, F12, F23, W14, W15, W16, F24, C10, F25, C11, F80, F81, F82, F83, F84, F85, P13, P14, P15, P16, F86, F87, F88, F89, F26, F27, F94, F31, F92, F28, F93, W19, F29, F30, W20, W21, F96, F95, F97, F98, W22, F34, F32, F33, F38, F35, F36, F37, W24, W26, F41, W27, F42, F47, C13, W25, F40, F39.

Fastest resource-feasible exact frame estimate: [W24](W24_constant_rom_T8/W24.md); 1.7460189000000002ms, T=8, DSP=630.0, BRAM18K=138.0, LUT=53316.0, deltaPSNR=-0.0695141811880653dB. HLS estimates are distinct from route/RTL results.

## Outstanding

Exploration: all required runs archived.

Final verification: all planned operations archived, including failures/timeouts.

## Weight Loading Workstream

Plan: [docs/0004](../docs/0004-t8-weight-loading-plan.md). Review section6 decisions, missing comic and any failed route/RTL gates; use measured physical bottlenecks for the next independent design. No board acceptance or push.

2026-10-12 用户决定降低优先级: F88/F90/F91. F88 was deliberately interrupted with SIGTERM to release the hardware slot; no RTL verdict or measured cycles exist. P14-P16/F86/F87 already completed before the new priority and remain archived. F85/P13 were recovered without rerunning.

Section 6 conservative decisions: preserve runtime float weights and HLS resource gates; keep missing comic explicitly provisional; if serial implementation OOM recurs, archive evidence and continue WS2 without changing host swap or using an unverified machine. Revisit these decisions with the user tomorrow.

P08 routed DSP48E2 inspection confirms one cell, AMULTSEL=AD and ADREG=1. W10-W13/C07 split transformed-window generation from a fixed16384*(4*T) MAC loop to remove W07's conditional264x264 bound inflation. C08/C09 use independently verified Conv2-only8-bit weights, retain ten-bit activations, and omit coefficient residual repair. Vitis rejects the original8000-bit Conv3 stream at its4096-bit limit; F08-F12/W14-W16/C10-C11 use independent two4000-bit-stream retries with identical arithmetic. F13-F15 isolate Conv3 window rotation and tree-register overhead using F08's measured7013 multiplexer LUT. All new designs are independent; source and paper plans are committed before runs. Re-run CSV analyses, equivalent offline-weight archives and all plots after all evidence arrives. Finalize ARCH_SUMMARY.md, both checksum audits and final F99 commit.

F24 independently rewrites only F23's Conv1 weight-loader indices after its report locates the2.822ns global critical path in a15-bit address multiplier; the dataflow region is2.377ns. Keep T16, quantization and inference fixed, account for nested-load restart overhead, and accept only measured exact/resource-feasible results.

## Recovery

Read ARCH_SUMMARY.md, LOG.md, PHASE2_HANDOFF.md and arch_state.json. Check active local exec sessions and remote processes before resuming pending IDs; completed and active workspaces cannot be overwritten. SSH uses `ssh -F ../ssh-config -o BatchMode=yes xiaoxin-ubuntu`; remote root `/home/lipuze/amdprojects/90096_CNN_FPGA`; Vitis settings `/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh`. Hardware jobs serialize through `.synthesis.lock` for15GiB RAM;60-minute csynth/45-minute issue tuning/six-hour cosim. Local plotting interpreter `workspace/exp_runs/_tools/venv/bin/python`. Never run script.py, modify protected data/designs, push, or substitute predicted results for actual evidence.
