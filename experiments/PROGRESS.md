# Current progress

Branch: `exp/explore-arch`, from completed `exp/overnight-1011` at `2fa7249eaecdfdc360d8d452fcbf52171c35abd2`.

## Completed

First phase stages0-6 closed in E099. E043 is fastest resource-feasible supplied-image candidate:6.93923049ms, DSP505, BRAM18K168, LUT55325. E069 matches every output bit on all13 supplied images. Missing comic prevents complete Set14 acceptance. E070 routed implementation of E039 fails timing with WNS-1.277ns. See SUMMARY.md and PHASE2_HANDOFF.md.

Architecture infrastructure supports series, immutable preplanned archives and additional first-phase design checksums. Original46-file SHA256 manifest remains unchanged. User README/.gitignore/docs-index edits remain outside task commits.

## Next Action

P01-P07/W01-W03 have completed strict C simulation and synthesis. P01 maps two products to1 DSP; P05's builtin also maps to1 DSP and awaits primitive inspection in P08 implementation. Exact10 residual P07 uses1 DSP/454 LUT. W01 uses16 DSP/1499 LUT versus direct W02's36 DSP/503 LUT; W03 retains16 DSP at16-bit input/weights.

G01-G03 completed two-frame exact comparisons. Gather is29.83024ms/168 BRAM18K; padded scatter37.70206ms/137; merged-edge scatter44.13926ms/87. S01 global scratch probe passed C simulation but is invalid: neither scratch AXI bundle exists, and11286 BRAM18K shows the arrays remained on chip. S02-S06/P08 queue28264 is active. Full exact P10-P12 and W04-W06 plans and independent designs have been committed; queue33156 is active. G queue6482 may need its final output drained, but its hardware work is complete.

P10 passed two-frame exact comparison and halves T16 DSP to254, but101488 LUT is infeasible and latency is12.156332ms. S03 B8 tile fusion passes exactly but113576 LUT is infeasible; larger blocks remain in queue. All S/P/W/C/F initial designs and pre-implementation plans now exist. F01-F07 queue46328 is active; it covers shallow-FIFO LUTRAM,20-URAM line banks, continuous registered reductions, old/online padding and T16/T8 at4/3.33ns.

C01-C03 failed before synthesis because srcnn.h included AMD ap_fixed after the network F2/F3 macros. W04-W06 are retained attempted controls in queue33156. Independent corrected winograd_network_r1 and combination_network_r1 designs use W07-W09/C04-C06, queue33716. C initial queue14065 is complete and drained. Report-derived architecture_data.csv, estimate_actual.csv, dsp_composition.csv and bursts.csv plus five initial architecture plots exist. Re-run exp/analyze_arch.py and plots after all results arrive.

Next: inspect corrected W layer/full-network correctness and F continuous-II/resource results. P08 implementation needs DSP48E2 attribute inspection through exp/inspect_dsp.tcl. Archive equivalent offline G2 weights. Select best2-3 provisional frame points from both phases for all supplied-image validation, routed implementation and two-frame6-hour cosim. Add concrete deviations/causes and finalize ARCH_SUMMARY.md, SUMMARY backlink, both checksum audits and commits. Never overwrite a completed run/design or stop while required queues remain active.

Continuation2026-10-10T22:40UTC: W10-W13/C07 plans committed, followed by independent winograd_continuous/combination_continuous source at d048887. Their queue17874 is active. Fixed16384*(4*T) MAC iterations replace W07's inflated conditional264x264 scan bound; window/tile packets use separate LUTRAM streams and a raster distributor. W11-W13 additionally use continuous direct Conv2/Conv3 and264x264 online first padding. Queue28264/33156/46328/33716 still active; no duplicate run IDs. S04/S05 are exact but exceed the LUT cap. Updated report analysis includes first-phase E043 and tiled per-layer DSP counts plus explicit >20% deviation explanations. Local matplotlib/numpy interpreter is workspace/exp_runs/_tools/venv/bin/python.

## Recovery

Read PROGRESS.md, ARCH_SUMMARY.md when present, LOG.md and arch_state.json. Remote host xiaoxin-ubuntu; root /home/lipuze/amdprojects/90096_CNN_FPGA; Vitis2026.1 settings /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh. Serialize hardware jobs with .synthesis.lock;60-minute csynth,45-minute issue limit,6-hour cosim. Keep Windows reproduction and missing comic in pending decisions. Never run script.py, overwrite an existing run, modify protected originals or first-phase designs, push, or claim board validation.
