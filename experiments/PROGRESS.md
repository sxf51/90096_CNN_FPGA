# Current progress

Baseline: `1f025dc`; branch: `exp/overnight-1011`; protected checksum manifest: `checksums.txt`.

## Stage status

- Stage 0: E000 completed; csim accepted, synthesis infeasible due to 11,064 BRAM18K; runner and checksums validated.
- Stage 1: E010 completed; w10a10 is smallest passing uniform point; w8a8 fails. E011 compile failed (macro/header conflict), fixed in E014, now running full ap_fixed. E017 is an independent actual-ap_fixed-boundary/integer-carrier cross-check.
- Stage 2: E020/E021/E022/E026 complete and infeasible (full-frame BRAM). E023/E024/E025 invalidated because unsupported directive config was skipped. Schema-correct E028/E029/E032 retries running; E027 fixed16 csim running.
- Stage 3: E030 float streaming csim passed bit-exact on butterfly, including borders. Pending fixed bit comparison and T=32 synthesis.
- Stage 4: pending coordinate scan and conditional implementation.
- Stage 5: pending scatter comparison and multiplier microbenchmarks.
- Stage 6: pending final plots, summary, checksum verification and commit.

## Next action

Run compiler-only E020 onward remotely while implementing actual ap_fixed reference. All HLS jobs use unique `workspace/exp_runs/EXXX` directories. Synthesis jobs run serially; each has a 60-minute process-tree timeout. No destructive workspace reset, no push, no protected-file edit.

## Recovery

Read LOG.md, results.csv and this file first. Inspect running remote jobs before starting another synthesis. Never overwrite an existing run; new attempts get new experiment IDs. Commit after each experiment; validate staged paths and sizes first. Full Set14 acceptance and Windows reproduction are unresolved, explicitly recorded in LOG.md.

## Queued second phase

After all first-phase stages, create `exp/explore-arch` from `exp/overnight-1011`. Read this file and SUMMARY.md first. User authorized S/G/P/W/C/F architecture exploration, including packing and Winograd, with estimates written before implementation, 45-minute issue limit, and final implementation/cosim for eligible best candidates. Preserve first-phase designs. See latest user task for full scope; no questions in unattended mode.

