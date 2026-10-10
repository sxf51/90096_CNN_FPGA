# Current progress

Updated 2026-10-10T22:52:46+00:00 from archived measurements.

Branch: `exp/explore-arch`, from phase-one final `2fa7249`. Original46 files and45 first-phase design files remain checksum protected. Preserve user README/.gitignore/docs-index edits.

## Completed

First phase stages0-6 closed in E099. Missing comic prevents complete Set14 acceptance; every supplied-image candidate is provisional. No board validation has run.

26 architecture records completed: P01, P02, W01, P03, W02, P04, W03, P05, P06, P07, G01, G02, S01, G03, S02, P10, C01, C02, C03, S03, P11, S04, W07, S05, P12, W04.

Fastest resource-feasible exact frame estimate: [E043](E043_scan_clock_T16_E043/E043.md); 6.93923049ms, T=16, DSP=505.0, BRAM18K=168.0, LUT=55325.0, deltaPSNR=-0.0695141811880653dB. HLS estimates are distinct from route/RTL results.

## Outstanding

Exploration: C04, C05, C06, C07, C08, C09, F01, F02, F03, F04, F05, F06, F07, P08, S06, W05, W06, W08, W09, W10, W11, W12, W13.

Final verification: awaiting global candidate selection.

P08 needs actual DSP48E2 pre-adder/register inspection. W10-W13/C07 split transformed-window generation from a fixed16384*(4*T) MAC loop to remove W07's conditional264x264 bound inflation. C08/C09 use independently verified Conv2-only8-bit weights, retain ten-bit activations, and omit coefficient residual repair. All new designs are independent; source and paper plans are committed before runs. Re-run CSV analyses, equivalent offline-weight archives and all plots after all evidence arrives. Finalize ARCH_SUMMARY.md, both checksum audits and final F99 commit.

## Recovery

Read ARCH_SUMMARY.md, LOG.md, PHASE2_HANDOFF.md and arch_state.json. Check active local exec sessions and remote processes before resuming pending IDs; completed and active workspaces cannot be overwritten. SSH uses `ssh -F ../ssh-config -o BatchMode=yes xiaoxin-ubuntu`; remote root `/home/lipuze/amdprojects/90096_CNN_FPGA`; Vitis settings `/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh`. Hardware jobs serialize through `.synthesis.lock` for15GiB RAM;60-minute csynth/45-minute issue tuning/six-hour cosim. Local plotting interpreter `workspace/exp_runs/_tools/venv/bin/python`. Never run script.py, modify protected data/designs, push, or substitute predicted results for actual evidence.
