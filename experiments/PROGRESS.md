# Current progress

Baseline: `1f025dc`; branch: `exp/overnight-1011`; protected checksum manifest: `checksums.txt`.

## Stage status

- Stage 0: E000 completed; csim accepted, synthesis infeasible due to 11,064 BRAM18K; runner and checksums validated.
- Stage 1: complete on all 13 supplied images (missing comic still blocks full Set14 acceptance). E010 scan; E017 real-ap_fixed boundaries/int carrier; E015/E019/E013 full actual-ap_fixed representatives all match numpy. E016 redundant w8 verification completed. E014 timeout and compile failures retained. E062 layer scan finds Conv2-only weight8 passes (-0.075890 dB); E065 all-image real-ap_fixed boundaries and E066 full all-ap_fixed butterfly verify it. E049 exhausts all 23-bit cast states (25,165,824 cases). Uniform w8 and genuinely eight-bit activation inputs still fail quality.
- Stage 2: complete. All valid compiler-only studies are infeasible (full-frame BRAM). E023/E024/E025 invalidated because unsupported directive config was skipped; E028/E029/E032 are valid retries. See STAGE2.md.
- Stage 3: complete. E030 float and E033 fixed T32 pass butterfly bit identity and borders. E033 synthesis: 123.540 ms, 9 DSP, 168 BRAM18K, 136868 LUT (infeasible), 149111 FF, 31.822 ns. Legacy E031 completed with identical synthesis. Inner folds reach II=1; spatial scheduling and row padding add overhead. See STAGE3.md and streaming_analysis.csv.
- Stage 4: T and split rounds completed. E058 is fastest feasible on supplied data: T16, 18.7632 ms, 505 DSP, 168 BRAM18K, 55212 LUT. E059 T8 exceeds the LUT cap (85147, 72.70%). E036 tap-split reaches Conv1 II=6 and 78.94023 ms; E037 Cin-split adds LUT without reducing the E058 latency; E038 Conv3 tap-split takes 21.55352 ms. E047/E048 register controls and E040 BRAM weights are infeasible. Resumable coordinate controller session 16904 is running E064, followed by E067 and E041-E043. E060 waits in session 28449. Single synthesis lock; queue wait 24h and actual synthesis timeout 60min.
- Stage 5: E051-E055 microbenchmarks, E050 scatter and E056 T4 mixed feasibility queued after E048 in session 74435. E060 exact integer scatter is queued after the banked T scan in 28449. New remote_exp entry points wait for every required Stage 4 coordinate; microbenchmarks additionally wait for E060 scatter, preserving the requested stage order. No Stage 5 run has started yet.
- Stage 6: E070 implementation of E039 completed: routed DSP270, BRAM36=31, LUT20454, FF33844, WNS=-1.277 ns at target10 ns (timing not closed). Worst routed Conv1 path is an eight-stage unregistered DSP-ALU reduction, 11.109 ns. Finalizer session 90189 waits for required queues, then runs E069 all-supplied-image validation and E099 plots/summary/checksum commit. All seven runner/parser tests pass. Stage 6 final closure remains pending.

## Next action

Finish E064/E067 storage and E041-E043 clocks, then E050/E060 scatter, E051-E055 multipliers and E056 T4 mixed-fabric feasibility. The optional queue is session 74435. Do not restart E070 or any completed ID. Two-frame cosimulation enables dataflow profiling and retains deadlock detection; it remains pending for final architecture candidates. Archive internal port inventories as structured excerpts; full remote raw reports remain intact. All jobs use unique workspace/exp_runs directories. No destructive workspace reset, no push, no protected-file edit.

## Recovery

Read LOG.md, results.csv and this file first. Inspect running remote jobs before starting another synthesis. Never overwrite an existing run; new attempts get new experiment IDs. Commit after each experiment; validate staged paths and sizes first. Full Set14 acceptance and Windows reproduction are unresolved, explicitly recorded in LOG.md.

## Queued second phase

After all first-phase stages, create `exp/explore-arch` from `exp/overnight-1011`. Read this file and SUMMARY.md first. User authorized S/G/P/W/C/F architecture exploration, including packing and Winograd, with estimates written before implementation, 45-minute issue limit, and final implementation/cosim for eligible best candidates. Preserve first-phase designs. See latest user task for full scope; no questions in unattended mode.

Exploration priorities from measured evidence: exact ten-bit coefficient packing via signed-low8 plus a small residual; mixed Conv2-weight8 using E065/E066; G2 integer Winograd with exact divide-by-four; continuous pixel schedules instead of inner-loop fill/drain; explicitly registered fabric reductions to test the E070 timing bottleneck; shallow wide FIFOs in LUTRAM. These are unimplemented hypotheses. Full Set14 coverage is still blocked by missing comic.


## Coordinate controller

2026-10-10T20:50:04+00:00: Running E067; preceding completed measurements remain archived.
