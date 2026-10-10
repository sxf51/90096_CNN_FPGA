# Current progress

Branch: `exp/explore-arch`, from completed `exp/overnight-1011` at `2fa7249eaecdfdc360d8d452fcbf52171c35abd2`.

## Completed

First phase stages0-6 closed in E099. E043 is fastest resource-feasible supplied-image candidate:6.93923049ms, DSP505, BRAM18K168, LUT55325. E069 matches every output bit on all13 supplied images. Missing comic prevents complete Set14 acceptance. E070 routed implementation of E039 fails timing with WNS-1.277ns. See SUMMARY.md and PHASE2_HANDOFF.md.

Architecture infrastructure supports series, immutable preplanned archives and additional first-phase design checksums. Original46-file SHA256 manifest remains unchanged. User README/.gitignore/docs-index edits remain outside task commits.

## Next Action

P01-P07/W01-W03 have completed strict C simulation and synthesis. P01 maps two products to1 DSP; P05's builtin also maps to1 DSP and awaits primitive inspection in P08 implementation. Exact10 residual P07 uses1 DSP/454 LUT. W01 uses16 DSP/1499 LUT versus direct W02's36 DSP/503 LUT; W03 retains16 DSP at16-bit input/weights.

G01-G03 completed two-frame exact comparisons. Gather is29.83024ms/168 BRAM18K; padded scatter37.70206ms/137; merged-edge scatter44.13926ms/87. S01 global scratch probe passed C simulation but is invalid: neither scratch AXI bundle exists, and11286 BRAM18K shows the arrays remained on chip. S02-S06/P08 queue28264 is active. Full exact P10-P12 and W04-W06 plans and independent designs have been committed; queue33156 is active. G queue6482 may need its final output drained, but its hardware work is complete.

Next: inspect numeric/synthesis failures without overwriting runs; preplan/implement C combinations and F continuous registered reductions, FIFO memory and online padding controls. Record estimates vs actuals and explain deviations over20%. Final best2-3 provisional frame candidates receive all supplied-image validation, routed implementation and two-frame cosim.

## Recovery

Read PROGRESS.md, ARCH_SUMMARY.md when present, LOG.md and arch_state.json. Remote host xiaoxin-ubuntu; root /home/lipuze/amdprojects/90096_CNN_FPGA; Vitis2026.1 settings /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh. Serialize hardware jobs with .synthesis.lock;60-minute csynth,45-minute issue limit,6-hour cosim. Keep Windows reproduction and missing comic in pending decisions. Never run script.py, overwrite an existing run, modify protected originals or first-phase designs, push, or claim board validation.
