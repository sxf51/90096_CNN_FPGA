# Current progress

Baseline: `1f025dc`; branch: `exp/overnight-1011`; protected checksum manifest: `checksums.txt`.

## Stage status

- Stage 0: E000 completed; csim accepted, synthesis infeasible due to 11,064 BRAM18K; runner and checksums validated.
- Stage 1: E010 completed; ranges and 16-point scan on all 13 supplied pairs. w10a10 is the smallest passing uniform point; w8a8 fails. Real ap_fixed verification next.
- Stage 2: pending compiler directive comparisons.
- Stage 3: pending streaming architecture, float correctness, fixed bit comparison and T=32 synthesis.
- Stage 4: pending coordinate scan and conditional implementation.
- Stage 5: pending scatter comparison and multiplier microbenchmarks.
- Stage 6: pending final plots, summary, checksum verification and commit.

## Next action

Run compiler-only E020 onward remotely while implementing actual ap_fixed reference. All HLS jobs use unique `workspace/exp_runs/EXXX` directories. Synthesis jobs run serially; each has a 60-minute process-tree timeout. No destructive workspace reset, no push, no protected-file edit.

## Recovery

Read LOG.md, results.csv and this file first. Inspect running remote jobs before starting another synthesis. Never overwrite an existing run; new attempts get new experiment IDs. Commit after each experiment; validate staged paths and sizes first. Full Set14 acceptance and Windows reproduction are unresolved, explicitly recorded in LOG.md.

## Queued second phase

After all first-phase stages, create `exp/explore-arch` from `exp/overnight-1011`. Read this file and SUMMARY.md first. User authorized S/G/P/W/C/F architecture exploration, including packing and Winograd, with estimates written before implementation, 45-minute issue limit, and final implementation/cosim for eligible best candidates. Preserve first-phase designs. See latest user task for full scope; no questions in unattended mode.

