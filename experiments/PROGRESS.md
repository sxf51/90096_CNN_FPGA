# Current progress

First-phase execution complete on `exp/overnight-1011`; full Set14 acceptance remains pending because comic is absent. Read SUMMARY.md, LOG.md and phase1_completion.json.

## Completed First Phase

Stages 0-6 executed; failed/infeasible/timeout records retained. All 46 protected files match local and remote SHA256. User README/.gitignore/documentation edits remain outside task commits. No push or board operation.

Best supplied-image candidate: E043. Full candidate validation is E069 when a feasible candidate exists. Implementation is E070 when a provisional candidate qualified. Actual implementation and HLS estimates are distinct.

## Next Action

Create `exp/explore-arch` from the completed first-phase branch. Phase two has not started. Read SUMMARY.md before proceeding. Preserve all first-phase designs; new designs get new directories and S/G/P/W/C/F IDs. Extend results.csv with series and write paper estimates before implementing each new idea. Start packing and Winograd microbenchmarks, then G, S, integration, combinations and free exploration.

## Environment And Recovery

SSH host xiaoxin-ubuntu, remote root /home/lipuze/amdprojects/90096_CNN_FPGA, Linux Vitis 2026.1 settings /home/lipuze/amdfpga/2026.1/Vitis/settings64.sh. One synthesis/implementation/cosim at a time under the shared memory lock. Each synthesis timeout 60 minutes, issue tuning limit 45 minutes, final cosim timeout six hours. All raw HLS workspaces are immutable under workspace/exp_runs/. Never run script.py. Verify no first-phase subprocess remains before switching branch.

## Numeric References

E019/E017 establish uniform w10a10; E049 exhausts raw boundary casts. E065/E066 establish mixed Conv2-weight8 with ten-bit activations: delta PSNR -0.075890 dB on 13 images, butterfly bit identity. E062 demonstrates true eight-bit activations and Conv1/Conv3 weight8 do not pass. Conv3 quantized w10 coefficients fit signed8 without changing their fractional scale, enabling exact packing exploration. See SOURCES.md for WP486, DDR bandwidth and Winograd references.
