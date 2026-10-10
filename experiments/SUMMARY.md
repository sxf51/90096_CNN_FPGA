# SRCNN on K26: overnight experiments

E000 establishes correct float behavior but is infeasible: 11,064 BRAM18K against 288 available and estimated frame latency 19,601.14 ms. E010 finds w10a10 within the 0.1 dB gate on the 13 supplied images, while w8a8 loses 5.18 dB. No validated feasible fastest architecture exists yet; complete Set14 and Windows reproduction remain pending.

## Stage 0

[E000](E000_golden_baseline/E000.md): original testbench MSE Conv1 3.46254e-15, SRCNN 3.16610e-14; strict float comparison passes for butterfly and all 13 supplied pairs. The default schedule reports inner Conv1 II 5, Conv2 pixel II 32 and Conv3 MAC II 4. Full float intermediate arrays dominate BRAM; faster scheduling alone cannot remove their storage.

## Stage 1

[E010](E010_precision_scan/E010.md): weight integer bits 1/1/1; activations input/Conv1/Conv2/output 2/2/3/2. Accumulator sizing uses an analytical bound and preserves full product precision. w16a16 mean PSNR difference is +0.000268 dB, w10a10 is -0.069514 dB, w8a8 is -5.179955 dB. No scan point saturated. Full actual-ap_fixed butterfly models [E015](E015_apfixed_w16a16_single_retry/E015.md), [E019](E019_apfixed_w10a10_retry/E019.md) and [E013](E013_apfixed_w8a8/E013.md) match numpy bit for bit. E019, the integer-carrier E017 and numpy share the same butterfly binary hash. E017 separately matches numpy on every one of the 13 supplied images. E014 full-image all-ap_fixed attempt reached its 45-minute limit and remains a timeout.

INT8 packing is ineligible for the uniform network: even w8a16 loses 4.97 dB. Layer-specific quantization needs a separate scan before any mixed packing candidate can be accepted. Precision is not monotonic in width here: w12 quantization fails while w10 passes for these trained weights; use measured results.

## Stage 2

See [STAGE2.md](STAGE2.md). Every compiler-only control is infeasible because full feature maps exceed BRAM capacity. Correct inner-loop pipeline reaches II=1 but a 26.707 ns clock estimate; outer pixel pipeline reaches 3,811 ms while retaining 11,114 BRAM18K. Configuration-only scheduling cannot resolve full-frame storage.

## Stage 3

See [STAGE3.md](STAGE3.md) and [E033](E033_dataflow_fixed_T32_single/E033.md). Streaming reduces BRAM18K from 11,064 to 168. Correctness and requested fold II=1 pass, but 136,868 LUT exceeds the 81,984 cap. Default 10-bit products mostly map to fabric: Conv1 report lists 62 LUT and no DSP per `mul_10s_10s_20_1_1` instance; only selected fused MACs use DSP. Conv3 serial saturating sum sets the 31.822 ns estimate. T16 gives 63.218 ns and 175.463 ms, showing that II=1 is insufficient when effective clock worsens.

See [LOG.md](LOG.md), [PROGRESS.md](PROGRESS.md), and [checksums.txt](checksums.txt). Supplied Set14 has 13 image pairs; complete 14-image acceptance remains pending.

