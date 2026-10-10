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

### Handoff hypotheses (not implemented or synthesized)

- Packing: split a generic signed10 coefficient into signed-low8 plus 256 times a residual in [-2,2], implement the residual with add/subtract/shift logic, and retain the original fraction9. At gap18, generic signed10 input should unpack every product; nonnegative raw activations in [0,511] permit two terms; true signed INT8 permits seven. Correct the high field when the signed low18 field is negative. Probe the DSP builtin separately because its SDK header rejects __PRESYNTHESIS__; ordinary DSP-bound multiplication is a fallback, with actual pre-adder mapping to be inspected.
- Conv3 packing: two adjacent nonnegative activation values share a coefficient. Pack ((a-256)<<18)+b in signed27, multiply by signed-low8, undo the borrow and add 256*coefficient to the high result; restore the coefficient residual exactly. A 5x6 window, padded260x259 stream and discarded neighbor column255 cover the odd image width.
- Winograd: use the G2/BT/AT matrices in SOURCES.md, full transform precision and exact divide-by-four before any layer cast. Nine prior rows and a 10x10 window over padded264x264 input produce 128x128 tiles; discard output row/column255. Two raster-row FIFOs of depth512 are a conservative alternative to stream_of_blocks double buffering; include their wide-memory cost and finite-FIFO ordering in estimates. Runtime integer weight transforms preserve the incoming float-weight signature; archive the equivalent offline transforms and measure load overhead.
- Continuous direct schedule: separate line/window generation from the matrix engines, flatten pixel and fold iterations, and explicitly register a balanced fabric reduction. Window streams are wide and shallow; estimate LUTRAM/register cost before adding them. This targets the measured Conv1 spatial-loop fill/drain and E070 DSP cascade path.
- Scatter edge kernels: nine source classes (top/interior/bottom times left/interior/right) merge taps exactly, retaining fraction9 and a wider coefficient. For output offset dy, interior ky=2-dy, top merges ky<=2-dy and bottom ky>=2-dy; analogous x. Use five 32-bit row banks plus a 5x5 register window, prime columns0/1 and flush two final rows/columns. Compare to explicit-pad scatter at identical precision/T/clock.
- DDR scratch: the fixed eight-argument srcnn contract has no scratch parameters. Probe global m_axi support and preserve any synthesis rejection; never silently append arguments or write outside the supplied arrays. Tile fusion must replicate Conv2 features at real image edges, rather than convolving at virtual feature centers. A BxB output tile needs (B+12)x(B+12) input and (B+4)x(B+4) feature areas. DS987 gives 19.2 GB/s theoretical DDR bandwidth; the requested 50% scenario is 9.6 GB/s and is not a board measurement.

After branch creation, add series to local and remote CSV schemas, widen the run/commit ID guards, and support immutable preplanned EXXX.md archives so paper estimates are committed before design implementation. Scope PE/layer/frame experiments separately in derived CSV files so microkernel latency cannot enter the network Pareto ranking. Final cosimulation should use two butterfly frames with Set14 disabled to keep the RTL workload bounded, while full supplied-image precision is validated separately.


## Coordinate controller

2026-10-10T21:02:16+00:00: All coordinate rounds completed; pending optional queues, candidate Set14 validation and first-phase finalization.
