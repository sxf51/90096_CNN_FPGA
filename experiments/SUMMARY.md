# SRCNN on K26: overnight experiments

E000 establishes correct float behavior but is infeasible: 11,064 BRAM18K against 288 available and estimated frame latency 19,601.14 ms. E010 finds w10a10 within the 0.1 dB gate on the 13 supplied images, while w8a8 loses 5.18 dB. No validated feasible fastest architecture exists yet; complete Set14 and Windows reproduction remain pending.

## Stage 0

[E000](E000_golden_baseline/E000.md): original testbench MSE Conv1 3.46254e-15, SRCNN 3.16610e-14; strict float comparison passes for butterfly and all 13 supplied pairs. The default schedule reports inner Conv1 II 5, Conv2 pixel II 32 and Conv3 MAC II 4. Full float intermediate arrays dominate BRAM; faster scheduling alone cannot remove their storage.

## Stage 1 (numerical scan complete; ap_fixed verification pending)

[E010](E010_precision_scan/E010.md): weight integer bits 1/1/1; activations input/Conv1/Conv2/output 2/2/3/2. Accumulator sizing uses an analytical bound and preserves full product precision. w16a16 mean PSNR difference is +0.000268 dB, w10a10 is -0.069514 dB, w8a8 is -5.179955 dB. No scan point saturated. Real ap_fixed confirmation is required before architecture selection.

See [LOG.md](LOG.md), [PROGRESS.md](PROGRESS.md), and [checksums.txt](checksums.txt). Supplied Set14 has 13 image pairs; complete 14-image acceptance remains pending.

