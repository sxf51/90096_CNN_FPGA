# Current progress

Branch: `exp/explore-arch`, from completed `exp/overnight-1011` at `2fa7249eaecdfdc360d8d452fcbf52171c35abd2`.

## Completed

First phase stages0-6 closed in E099. E043 is fastest resource-feasible supplied-image candidate:6.93923049ms, DSP505, BRAM18K168, LUT55325. E069 matches every output bit on all13 supplied images. Missing comic prevents complete Set14 acceptance. E070 routed implementation of E039 fails timing with WNS-1.277ns. See SUMMARY.md and PHASE2_HANDOFF.md.

Architecture infrastructure supports series, immutable preplanned archives and additional first-phase design checksums. Original46-file SHA256 manifest remains unchanged. User README/.gitignore/docs-index edits remain outside task commits.

## Next Action

P01-P07/W01-W03 estimates were committed before source implementation. Packing queue48817 and Winograd queue14118 are running; hardware is serialized, C simulations may overlap. P01 exhausts all16777216 signed8 triples plus homogeneous extrema; W01 checks524288 exact inverse outputs. Both C simulations pass; synthesis mapping remains pending. G01-G03 are being preplanned at common T32/10ns. Then execute S dataflow/DDR/tile comparison, full P/W, C combinations and F scheduling/memory/timing ideas. Record estimates vs actuals and explain deviations over20%. Final best2-3 provisional candidates receive full supplied-image validation, implementation and two-frame cosim.

## Recovery

Read PROGRESS.md, ARCH_SUMMARY.md when present, LOG.md and arch_state.json. Remote host xiaoxin-ubuntu; root /home/lipuze/amdprojects/90096_CNN_FPGA; Vitis2026.1 settings /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh. Serialize hardware jobs with .synthesis.lock;60-minute csynth,45-minute issue limit,6-hour cosim. Keep Windows reproduction and missing comic in pending decisions. Never run script.py, overwrite an existing run, modify protected originals or first-phase designs, push, or claim board validation.
