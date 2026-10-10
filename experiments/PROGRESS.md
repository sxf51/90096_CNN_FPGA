# Current progress

Baseline: `1f025dc`; branch: `exp/overnight-1011`; protected checksum manifest: `checksums.txt`.

## Stage status

- Stage 0: E000 completed; csim accepted, synthesis infeasible due to 11,064 BRAM18K; runner and checksums validated.
- Stage 1: complete on all 13 supplied images (missing comic still blocks full Set14 acceptance). E010 scan; E017 real-ap_fixed boundaries/int carrier; E015/E019/E013 full actual-ap_fixed butterfly representatives all match numpy bit for bit. E014 timed out at 45 minutes; E011/E012/E018 compile failures retained. E016 redundant w8 arithmetic confirmation running in session 37197.
- Stage 2: complete. All valid compiler-only studies are infeasible (full-frame BRAM). E023/E024/E025 invalidated because unsupported directive config was skipped; E028/E029/E032 are valid retries. See STAGE2.md.
- Stage 3: complete. E030 float and E033 fixed T32 pass butterfly bit identity and borders. E033 synthesis: 123.540 ms, 9 DSP, 168 BRAM18K, 136868 LUT (infeasible), 149111 FF, 31.822 ns estimated clock. Inner folds reach II=1 but outer spatial engines add fill/drain overhead. See STAGE3.md and streaming_analysis.csv. Legacy E031 csim remains running in session 20714 (45-minute timeout enforced).
- Stage 4: E034/E035 include-path failures retained. E044 T16: 175.463 ms, 63.218 ns, 167715 LUT, infeasible. T8 E045 running in session 48815. E046 no-overflow accumulator control in session 32023; E047 explicit DSP product binding in session 12261. Both passed butterfly and wait/use the single synthesis lock. Split/storage/clock rounds and conditional implementation pending.
- Stage 5: pending scatter comparison and multiplier microbenchmarks.
- Stage 6: pending final plots, summary, checksum verification and commit.

## Next action

Finish E045/E046/E047; select measured coordinate controls. Then run split/storage/clock, E050 scatter, E051-E055 multipliers and T4 mixed-fabric feasibility. `exp/verify_exp.py` is prepared for isolated parent-copy implementation and two-frame RTL cosimulation, but no verification has run. Archive internal port inventories as structured excerpts to avoid tens of megabytes per run; full remote raw reports remain intact. All HLS jobs use unique `workspace/exp_runs/EXXX` directories. Synthesis jobs run serially; each has a 60-minute process-tree timeout. No destructive workspace reset, no push, no protected-file edit.

## Recovery

Read LOG.md, results.csv and this file first. Inspect running remote jobs before starting another synthesis. Never overwrite an existing run; new attempts get new experiment IDs. Commit after each experiment; validate staged paths and sizes first. Full Set14 acceptance and Windows reproduction are unresolved, explicitly recorded in LOG.md.

## Queued second phase

After all first-phase stages, create `exp/explore-arch` from `exp/overnight-1011`. Read this file and SUMMARY.md first. User authorized S/G/P/W/C/F architecture exploration, including packing and Winograd, with estimates written before implementation, 45-minute issue limit, and final implementation/cosim for eligible best candidates. Preserve first-phase designs. See latest user task for full scope; no questions in unattended mode.

