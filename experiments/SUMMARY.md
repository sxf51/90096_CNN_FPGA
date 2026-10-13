Architecture exploration: [ARCH_SUMMARY.md](ARCH_SUMMARY.md).

# SRCNN on K26: overnight experiments

The unchanged float baseline is functionally correct but infeasible (11064.0 BRAM18K; 19601.139 ms). Uniform w10a10 loses 0.069514 dB on all 13 supplied Set14 pairs; w8a8 loses 5.179955 dB. The fastest resource-feasible supplied-image candidate is [E043](E043_scan_clock_T16_E043/E043.md) at 6.939230 ms; missing comic prevents complete Set14 acceptance.

## Current best

| design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | ii_ok | status | id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| designs/dataflow_int | w10a10acc23 | 16 | 3.33 | 3.239 | 2083853.0 | 2083854.0 | 6.93923049 | 505.0 | 168.0 | 55325.0 | 67025.0 | -0.0695141811880653 | True | provisional | [E043](E043_scan_clock_T16_E043/E043.md) |

Implementation results are separate from HLS estimates; see verification experiments below. All performance is tool-estimated or explicitly labeled RTL/implementation evidence. No board validation was run.

## Precision

[E010](E010_precision_scan/E010.md) profiles every supplied image and establishes nearest-even AP_RND_CONV, AP_SAT, full product fractions and bounded accumulators. [E015](E015_apfixed_w16a16_single_retry/E015.md), [E019](E019_apfixed_w10a10_retry/E019.md) and [E013](E013_apfixed_w8a8/E013.md) use real AMD ap_fixed and match numpy butterfly outputs bit for bit. [E017](E017_apfixed_boundary_w10a10/E017.md) confirms real-ap_fixed boundaries and exact integer convolution on every supplied image. [E049](E049_integer_boundary_exhaustive/E049.md) exhausts 25,165,824 signed accumulator/cast cases. [E062](E062_layer_int8_scan/E062.md) finds Conv2-only 8-bit weights pass (-0.075890 dB with other layers at w10a10); genuine INT8 activation inputs and Conv1/Conv3 INT8 weights fail. [E065](E065_apfixed_mixed_conv2w8/E065.md) confirms real-ap_fixed boundaries on all 13 images; [E066](E066_full_apfixed_mixed_butterfly/E066.md) confirms the complete all-ap_fixed mixed network bit for bit on butterfly.

Metric: normalized float MSE PSNR, no clipping/cropping, against the same unchanged float golden; the original uint8 conversion metric is retained in test logs. Supplied-image acceptance is provisional because comic is absent.

## Compiler Controls

See [STAGE2.md](STAGE2.md). Whole feature maps require 11,064 BRAM18K at baseline, so all valid structure-preserving controls are infeasible. The valid innermost pipeline reaches II=1 but 26.707 ns estimated clock; outer pixel pipeline reaches 3,811.217 ms with 11,114 BRAM18K. Floating-point loop-carried addition, memory ports and automatically unrolled inner loops remain limiting. E023/E024/E025 used unsupported directives and were invalidated; E028/E029/E032 are the valid replacements.

## Streaming And Scans

See [STAGE3.md](STAGE3.md) and streaming_analysis.csv for per-layer numbers. E030 float and E033 fixed T32 pass all butterfly pixels and six-pixel borders. E033 uses 168 BRAM18K but 136,868 LUT, and its 31.822 ns critical path gives 123.540 ms. E044 T16 worsens to 63.218 ns and E045 T8 reaches 126.008 ns / 266,266 LUT; removing redundant accumulator saturation and explicitly binding multipliers separates arithmetic semantics from fabric mapping. E047 maps exactly 251 scheduled products to DSPs and reaches 29.13855 ms, but 89,341 LUT exceeds the 81,984 cap. Banked memories and integer boundary primitives are measured follow-ups, not presumed improvements.

AXI float-array signature remains unchanged; weights/biases load once before DATAFLOW, intermediate maps stay on chip, and requested sequential bursts are up to 256 words. Inner II=1 does not imply T frame throughput: pixel-loop fill/drain and pad-row transactions add measured overhead.

| design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | ii_ok | status | id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| designs/dataflow_int | w10a10acc23 | 16 | 3.33 | 3.239 | 2083853.0 | 2083854.0 | 6.93923049 | 505.0 | 168.0 | 55325.0 | 67025.0 | -0.0695141811880653 | True | provisional | [E043](E043_scan_clock_T16_E043/E043.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 4 | 3.239 | 2014678.0 | 2014679.0 | 8.058712 | 505.0 | 168.0 | 56007.0 | 62948.0 | -0.0695141811880653 | True | provisional | [E042](E042_scan_clock_T16_E042/E042.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 5 | 3.65 | 1945500.0 | 1945501.0 | 9.7275 | 505.0 | 168.0 | 55553.0 | 59959.0 | -0.0695141811880653 | True | provisional | [E041](E041_scan_clock_T16_E041/E041.md) |
| designs/dataflow_mix | w10a10acc23 | 4 | 10 | 7.3 | 1046292.0 | 1046293.0 | 10.46292 | 1160.0 | 168.0 | 237025.0 | 120073.0 | -0.0695141811880653 | True | infeasible | [E056](E056_mixed_T4_feasibility/E056.md) |
| designs/dataflow_int | w10a10acc23 | 8 | 10 | 7.3 | 1322968.0 | 1322969.0 | 13.22968 | 1007.0 | 168.0 | 85147.0 | 88822.0 | -0.0695141811880653 | True | infeasible | [E059](E059_integer_lutram_T8/E059.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1807151.0 | 1807152.0 | 18.07151 | 505.0 | 168.0 | 88306.0 | 138588.0 | -0.0695141811880653 | True | infeasible | [E064](E064_storage_0_T16/E064.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1876320.0 | 1876321.0 | 18.7632 | 505.0 | 168.0 | 55212.0 | 57723.0 | -0.0695141811880653 | True | provisional | [E058](E058_integer_lutram_T16/E058.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1876320.0 | 1876321.0 | 18.7632 | 505.0 | 168.0 | 60050.0 | 56509.0 | -0.0695141811880653 | True | provisional | [E037](E037_scan_split_T16_E037/E037.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1876320.0 | 1876321.0 | 18.7632 | 505.0 | 670.0 | 53706.0 | 47716.0 | -0.0695141811880653 | True | infeasible | [E067](E067_storage_2_T16/E067.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 2155352.0 | 2155353.0 | 21.55352 | 519.0 | 168.0 | 64526.0 | 57346.0 | -0.0695141811880653 | True | provisional | [E038](E038_scan_split_T16_E038/E038.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2913855.0 | 2913856.0 | 29.13855 | 251.0 | 168.0 | 89341.0 | 132430.0 | -0.0695141811880653 | True | infeasible | [E047](E047_dataflow_dsp_T32/E047.md) |
| designs/dataflow_wrap | w10a10acc23 | 32 | 10 | 7.3 | 2913855.0 | 2913856.0 | 29.13855 | 148.0 | 168.0 | 95727.0 | 132430.0 | -0.0695141811880653 | True | infeasible | [E063](E063_dataflow_wrap_T32_retry/E063.md) |
| designs/dataflow_int | w10a10acc23 | 32 | 10 | 7.3 | 2913855.0 | 2913856.0 | 29.13855 | 254.0 | 168.0 | 89304.0 | 132635.0 | -0.0695141811880653 | True | infeasible | [E048](E048_dataflow_integer_T32/E048.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 251.0 | 168.0 | 44530.0 | 46123.0 | -0.0695141811880653 | True | provisional | [E039](E039_scan_storage_T32_E039/E039.md) |
| designs/dataflow_int | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 254.0 | 168.0 | 44493.0 | 46328.0 | -0.0695141811880653 | True | provisional | [E057](E057_integer_lutram_T32/E057.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 251.0 | 419.0 | 43275.0 | 41136.0 | -0.0695141811880653 | True | infeasible | [E040](E040_scan_storage_T32_E040/E040.md) |
| designs/scatter_int | w10a10acc23 | 32 | 10 | 7.3 | 3770206.0 | 3770207.0 | 37.70206 | 254.0 | 137.0 | 39135.0 | 24841.0 | -0.0695141811880653 | True | provisional | [E060](E060_scatter_integer_T32/E060.md) |
| designs/scatter_v1 | w10a10acc23 | 32 | 10 | 7.3 | 3882221.0 | 3882222.0 | 38.82221 | 34.0 | 137.0 | 127718.0 | 128434.0 | -0.0695141811880653 | True | infeasible | [E050](E050_scatter_T32/E050.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 7894023.0 | 7894024.0 | 78.94023 | 565.0 | 168.0 | 79846.0 | 76416.0 | -0.0695141811880653 | False | provisional | [E036](E036_scan_split_T16_E036/E036.md) |
| designs/dataflow_v1 | w10a10acc23 | 32 | 10 | 31.822 | 3882221.0 | 3882222.0 | 123.540036662 | 9.0 | 168.0 | 136868.0 | 149111.0 | -0.0695141811880653 | True | infeasible | [E033](E033_dataflow_fixed_T32_single/E033.md) |
| designs/dataflow_v1 | w10a10acc23 | 32 | 10 | 31.822 | 3882221.0 | 3882222.0 | 123.540036662 | 9.0 | 168.0 | 136868.0 | 149111.0 | -0.0695141811880653 | True | infeasible | [E031](E031_dataflow_fixed_T32/E031.md) |
| designs/dataflow_v1 | w10a10acc23 | 16 | 10 | 63.218 | 2775517.0 | 2775518.0 | 175.462633706 | 18.0 | 168.0 | 167715.0 | 135714.0 | -0.0695141811880653 | True | infeasible | [E044](E044_scan_T_T16_E034_retry/E044.md) |
| designs/dataflow_v1 | w10a10acc23 | 8 | 10 | 126.008 | 2222165.0 | 2222166.0 | 280.01056732 | 36.0 | 168.0 | 266266.0 | 142153.0 | -0.0695141811880653 | True | infeasible | [E045](E045_scan_T_T8_E035_retry/E045.md) |

## Optional Experiments

| design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | ii_ok | status | id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| designs/scatter_int | w10a10acc23 | 32 | 10 | 7.3 | 3770206.0 | 3770207.0 | 37.70206 | 254.0 | 137.0 | 39135.0 | 24841.0 | -0.0695141811880653 | True | provisional | [E060](E060_scatter_integer_T32/E060.md) |
| designs/micro_multiplier | i16_i16_i32 | unknown | 10 | 2.38 | 66.0 | 64.0 | 0.00066 | 1.0 | 0.0 | 62.0 | 16.0 | unknown | True | pass | [E051](E051_mul16_default/E051.md) |
| designs/micro_multiplier | i16_constant_i32 | unknown | 10 | 2.38 | 0.0 | 1.0 | 0.0 | 60.0 | 0.0 | 424.0 | 0.0 | unknown | unknown | pass | [E052](E052_mul16_constant_unroll/E052.md) |
| designs/micro_multiplier | i8_i8_i16 | unknown | 10 | 1.635 | 66.0 | 64.0 | 0.00066 | 0.0 | 0.0 | 119.0 | 16.0 | unknown | True | pass | [E053](E053_mul8_fabric/E053.md) |
| designs/micro_multiplier | i16_i16_i32 | unknown | 4 | 2.38 | 66.0 | 64.0 | 0.000264 | 1.0 | 0.0 | 62.0 | 16.0 | unknown | True | pass | [E054](E054_mul16_default_4ns/E054.md) |
| designs/micro_multiplier | i8_add_i16 | unknown | 10 | 1.635 | 66.0 | 64.0 | 0.00066 | 0.0 | 0.0 | 73.0 | 16.0 | unknown | True | pass | [E055](E055_mul8_add_control/E055.md) |
| designs/scatter_v1 | w10a10acc23 | 32 | 10 | 7.3 | 3882221.0 | 3882222.0 | 38.82221 | 34.0 | 137.0 | 127718.0 | 128434.0 | -0.0695141811880653 | True | infeasible | [E050](E050_scatter_T32/E050.md) |
| designs/dataflow_mix | w10a10acc23 | 4 | 10 | 7.3 | 1046292.0 | 1046293.0 | 10.46292 | 1160.0 | 168.0 | 237025.0 | 120073.0 | -0.0695141811880653 | True | infeasible | [E056](E056_mixed_T4_feasibility/E056.md) |

Multiplier kernels report their own cycle counts, never a network-frame latency. T4 mixed fabric/DSP feasibility and scatter preserve strict arithmetic checks; infeasible reports remain visible. [E071](E071_architecture_prerequisite_ranges/E071.md) archives exact raw coefficient ranges, G2 transform bounds and independently checked paper budgets; nonnegative nine-bit activations permit only two terms in a signed18 low field. Packing prerequisites: uniform INT8 quality fails; exact integer decomposition or confirmed Conv2 weight-only quantization is required. Direct T8 paper DSP split is 648/256/100=1004; Winograd Conv1 T4 plus direct Conv2 and packed Conv3 is 576/512/100=1188 before other overhead. These budgets are unmeasured phase-two hypotheses.

## Verification

| design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | ii_ok | status | id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| parameter_range_analysis | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | analysis_complete | [E071](E071_architecture_prerequisite_ranges/E071.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 251.0 | 168.0 | 44530.0 | 46123.0 | -0.0695141811880653 | True | impl_complete | [E070](E070_first_feasible_implementation/E070.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 3.33 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | unknown | csim_pass | [E069](E069_final_candidate_all_supplied/E069.md) |


Actual verification of E070:

| metric | value |
| --- | --- |
| impl_BRAM36 | 31.0 |
| impl_DSP | 270.0 |
| impl_FF | 33844.0 |
| impl_LUT | 20454.0 |
| impl_TNS_ns | -1206.071 |
| impl_URAM | 0.0 |
| impl_WNS_ns | -1.277 |
| impl_clock_ns_est | 11.277 |
| impl_resource_report | hls/impl/verilog/report/srcnn_utilization_routed.rpt |
| impl_timing_report | hls/impl/verilog/report/srcnn_timing_routed.rpt |
| timing_met | False |

Placement/routing completed but the target clock did not close. The reports concern out-of-context internal timing; AXI system and board timing remain unverified.
## All Experiments

| design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | ii_ok | status | id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| designs/micro_multiplier | i16_constant_i32 | unknown | 10 | 2.38 | 0.0 | 1.0 | 0.0 | 60.0 | 0.0 | 424.0 | 0.0 | unknown | unknown | pass | [E052](E052_mul16_constant_unroll/E052.md) |
| designs/micro_multiplier | i16_i16_i32 | unknown | 4 | 2.38 | 66.0 | 64.0 | 0.000264 | 1.0 | 0.0 | 62.0 | 16.0 | unknown | True | pass | [E054](E054_mul16_default_4ns/E054.md) |
| designs/micro_multiplier | i16_i16_i32 | unknown | 10 | 2.38 | 66.0 | 64.0 | 0.00066 | 1.0 | 0.0 | 62.0 | 16.0 | unknown | True | pass | [E051](E051_mul16_default/E051.md) |
| designs/micro_multiplier | i8_i8_i16 | unknown | 10 | 1.635 | 66.0 | 64.0 | 0.00066 | 0.0 | 0.0 | 119.0 | 16.0 | unknown | True | pass | [E053](E053_mul8_fabric/E053.md) |
| designs/micro_multiplier | i8_add_i16 | unknown | 10 | 1.635 | 66.0 | 64.0 | 0.00066 | 0.0 | 0.0 | 73.0 | 16.0 | unknown | True | pass | [E055](E055_mul8_add_control/E055.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 3.33 | 3.239 | 2083853.0 | 2083854.0 | 6.93923049 | 505.0 | 168.0 | 55325.0 | 67025.0 | -0.0695141811880653 | True | provisional | [E043](E043_scan_clock_T16_E043/E043.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 4 | 3.239 | 2014678.0 | 2014679.0 | 8.058712 | 505.0 | 168.0 | 56007.0 | 62948.0 | -0.0695141811880653 | True | provisional | [E042](E042_scan_clock_T16_E042/E042.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 5 | 3.65 | 1945500.0 | 1945501.0 | 9.7275 | 505.0 | 168.0 | 55553.0 | 59959.0 | -0.0695141811880653 | True | provisional | [E041](E041_scan_clock_T16_E041/E041.md) |
| designs/dataflow_mix | w10a10acc23 | 4 | 10 | 7.3 | 1046292.0 | 1046293.0 | 10.46292 | 1160.0 | 168.0 | 237025.0 | 120073.0 | -0.0695141811880653 | True | infeasible | [E056](E056_mixed_T4_feasibility/E056.md) |
| designs/dataflow_int | w10a10acc23 | 8 | 10 | 7.3 | 1322968.0 | 1322969.0 | 13.22968 | 1007.0 | 168.0 | 85147.0 | 88822.0 | -0.0695141811880653 | True | infeasible | [E059](E059_integer_lutram_T8/E059.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1807151.0 | 1807152.0 | 18.07151 | 505.0 | 168.0 | 88306.0 | 138588.0 | -0.0695141811880653 | True | infeasible | [E064](E064_storage_0_T16/E064.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1876320.0 | 1876321.0 | 18.7632 | 505.0 | 168.0 | 55212.0 | 57723.0 | -0.0695141811880653 | True | provisional | [E058](E058_integer_lutram_T16/E058.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1876320.0 | 1876321.0 | 18.7632 | 505.0 | 168.0 | 60050.0 | 56509.0 | -0.0695141811880653 | True | provisional | [E037](E037_scan_split_T16_E037/E037.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 1876320.0 | 1876321.0 | 18.7632 | 505.0 | 670.0 | 53706.0 | 47716.0 | -0.0695141811880653 | True | infeasible | [E067](E067_storage_2_T16/E067.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 2155352.0 | 2155353.0 | 21.55352 | 519.0 | 168.0 | 64526.0 | 57346.0 | -0.0695141811880653 | True | provisional | [E038](E038_scan_split_T16_E038/E038.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2913855.0 | 2913856.0 | 29.13855 | 251.0 | 168.0 | 89341.0 | 132430.0 | -0.0695141811880653 | True | infeasible | [E047](E047_dataflow_dsp_T32/E047.md) |
| designs/dataflow_wrap | w10a10acc23 | 32 | 10 | 7.3 | 2913855.0 | 2913856.0 | 29.13855 | 148.0 | 168.0 | 95727.0 | 132430.0 | -0.0695141811880653 | True | infeasible | [E063](E063_dataflow_wrap_T32_retry/E063.md) |
| designs/dataflow_int | w10a10acc23 | 32 | 10 | 7.3 | 2913855.0 | 2913856.0 | 29.13855 | 254.0 | 168.0 | 89304.0 | 132635.0 | -0.0695141811880653 | True | infeasible | [E048](E048_dataflow_integer_T32/E048.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 251.0 | 168.0 | 44530.0 | 46123.0 | -0.0695141811880653 | True | provisional | [E039](E039_scan_storage_T32_E039/E039.md) |
| designs/dataflow_int | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 254.0 | 168.0 | 44493.0 | 46328.0 | -0.0695141811880653 | True | provisional | [E057](E057_integer_lutram_T32/E057.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 251.0 | 168.0 | 44530.0 | 46123.0 | -0.0695141811880653 | True | impl_complete | [E070](E070_first_feasible_implementation/E070.md) |
| designs/dataflow_dsp | w10a10acc23 | 32 | 10 | 7.3 | 2983024.0 | 2983025.0 | 29.83024 | 251.0 | 419.0 | 43275.0 | 41136.0 | -0.0695141811880653 | True | infeasible | [E040](E040_scan_storage_T32_E040/E040.md) |
| designs/scatter_int | w10a10acc23 | 32 | 10 | 7.3 | 3770206.0 | 3770207.0 | 37.70206 | 254.0 | 137.0 | 39135.0 | 24841.0 | -0.0695141811880653 | True | provisional | [E060](E060_scatter_integer_T32/E060.md) |
| designs/scatter_v1 | w10a10acc23 | 32 | 10 | 7.3 | 3882221.0 | 3882222.0 | 38.82221 | 34.0 | 137.0 | 127718.0 | 128434.0 | -0.0695141811880653 | True | infeasible | [E050](E050_scatter_T32/E050.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 10 | 7.3 | 7894023.0 | 7894024.0 | 78.94023 | 565.0 | 168.0 | 79846.0 | 76416.0 | -0.0695141811880653 | False | provisional | [E036](E036_scan_split_T16_E036/E036.md) |
| designs/dataflow_v1 | w10a10acc23 | 32 | 10 | 31.822 | 3882221.0 | 3882222.0 | 123.540036662 | 9.0 | 168.0 | 136868.0 | 149111.0 | -0.0695141811880653 | True | infeasible | [E033](E033_dataflow_fixed_T32_single/E033.md) |
| designs/dataflow_v1 | w10a10acc23 | 32 | 10 | 31.822 | 3882221.0 | 3882222.0 | 123.540036662 | 9.0 | 168.0 | 136868.0 | 149111.0 | -0.0695141811880653 | True | infeasible | [E031](E031_dataflow_fixed_T32/E031.md) |
| designs/dataflow_v1 | w10a10acc23 | 16 | 10 | 63.218 | 2775517.0 | 2775518.0 | 175.462633706 | 18.0 | 168.0 | 167715.0 | 135714.0 | -0.0695141811880653 | True | infeasible | [E044](E044_scan_T_T16_E034_retry/E044.md) |
| designs/dataflow_v1 | w10a10acc23 | 8 | 10 | 126.008 | 2222165.0 | 2222166.0 | 280.01056732 | 36.0 | 168.0 | 266266.0 | 142153.0 | -0.0695141811880653 | True | infeasible | [E045](E045_scan_T_T8_E035_retry/E045.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.624 | 381121723.0 | 381121724.0 | 3811.21723 | 320.0 | 11114.0 | 80812.0 | 123203.0 | unknown | False | infeasible | [E029](E029_auto_pixel_pipeline_validcfg/E029.md) |
| designs/fixed_ref | w16a16acc35 | unknown | 10 | 7.177 | 391256088.0 | 391256089.0 | 3912.56088 | 66.0 | 5822.0 | 137322.0 | 8096.0 | unknown | unknown | infeasible | [E027](E027_auto_fixed16/E027.md) |
| designs/golden_auto | float32 | unknown | 10 | 26.707 | 455695454.0 | 455695455.0 | 12170.258489978001 | 12.0 | 11064.0 | 9914.0 | 8948.0 | unknown | True | infeasible | [E028](E028_auto_inner_pipeline_validcfg/E028.md) |
| designs/golden_auto | float32 | unknown | 10 | 26.707 | 455695454.0 | 455695455.0 | 12170.258489978001 | 12.0 | 11096.0 | 8585.0 | 10378.0 | unknown | True | infeasible | [E032](E032_auto_partition_validcfg/E032.md) |
| designs/golden_auto | float32 | unknown | 4 | 2.913 | 4294771851.0 | 4294771852.0 | 17179.087404 | 10.0 | 11064.0 | 9997.0 | 9596.0 | unknown | unknown | infeasible | [E021](E021_auto_default_4ns/E021.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.331 | 1960113671.0 | 1960113672.0 | 19601.13671 | 10.0 | 11064.0 | 7624.0 | 3154.0 | unknown | unknown | infeasible | [E026](E026_auto_unsafe_math/E026.md) |
| src | float32 | unknown | 10 | 7.331 | 1960113853.0 | 1960113854.0 | 19601.13853 | 10.0 | 11064.0 | 9377.0 | 8027.0 | 0 | unknown | infeasible | [E000](E000_golden_baseline/E000.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.331 | 1960113853.0 | 1960113854.0 | 19601.13853 | 10.0 | 11064.0 | 9377.0 | 8027.0 | unknown | unknown | infeasible | [E020](E020_auto_default_10ns/E020.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.331 | 1960113853.0 | 1960113854.0 | 19601.13853 | 10.0 | 11064.0 | 9377.0 | 8027.0 | unknown | False | invalid_config | [E023](E023_auto_inner_pipeline/E023.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.331 | 1960113853.0 | 1960113854.0 | 19601.13853 | 10.0 | 11064.0 | 9377.0 | 8027.0 | unknown | False | invalid_config | [E024](E024_auto_pixel_pipeline/E024.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.331 | 1960113853.0 | 1960113854.0 | 19601.13853 | 10.0 | 11064.0 | 9377.0 | 8027.0 | unknown | False | invalid_config | [E025](E025_auto_partition/E025.md) |
| designs/golden_auto | float32 | unknown | 10 | 7.016 | 4482223011.0 | 4482223012.0 | 44822.23011 | 5.0 | 11064.0 | 2217.0 | 1267.0 | unknown | unknown | infeasible | [E022](E022_auto_pipeline_off/E022.md) |
| numpy_precision_scan | 16/12/10/8 scan | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | analysis_complete | [E010](E010_precision_scan/E010.md) |
| designs/fixed_ref | w16a16acc35 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail | [E011](E011_apfixed_w16a16/E011.md) |
| designs/dataflow_v1 | float32 | 32 | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass | [E030](E030_dataflow_float/E030.md) |
| designs/fixed_ref_raw | w10a10acc23 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | unknown | csim_pass | [E017](E017_apfixed_boundary_w10a10/E017.md) |
| designs/dataflow_v1 | w10a10acc23 | 16 | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail | [E034](E034_scan_T_T16_E034/E034.md) |
| designs/dataflow_v1 | w10a10acc23 | 8 | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail | [E035](E035_scan_T_T8_E035/E035.md) |
| designs/fixed_ref | w16a16acc35 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail | [E018](E018_apfixed_w16a16_single/E018.md) |
| designs/fixed_ref | w16a16acc35 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | timeout | [E014](E014_apfixed_w16a16/E014.md) |
| designs/fixed_ref | w10a10acc23 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail | [E012](E012_apfixed_w10a10/E012.md) |
| designs/fixed_ref | w16a16acc35 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass | [E015](E015_apfixed_w16a16_single_retry/E015.md) |
| designs/fixed_ref | w8a8acc19 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass | [E013](E013_apfixed_w8a8/E013.md) |
| designs/fixed_ref | w10a10acc23 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass | [E019](E019_apfixed_w10a10_retry/E019.md) |
| designs/fixed_ref | w8a8acc19 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass | [E016](E016_apfixed_w8a8_retry/E016.md) |
| designs/dataflow_int | boundary_w10a10 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass | [E049](E049_integer_boundary_exhaustive/E049.md) |
| designs/dataflow_wrap | w10a10acc23 | 32 | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | unknown | fail | [E046](E046_dataflow_wrap_T32/E046.md) |
| numpy_layer_precision_scan | mixed layer scan | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | analysis_complete | [E062](E062_layer_int8_scan/E062.md) |
| designs/fixed_ref_mixed_raw | w10_8_10a10acc23_21_23 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | -0.07589037644656216 | unknown | csim_pass | [E065](E065_apfixed_mixed_conv2w8/E065.md) |
| designs/fixed_ref_mixed | w10_8_10a10acc23_21_23 | unknown | 10 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | -0.07589037644656216 | unknown | csim_pass | [E066](E066_full_apfixed_mixed_butterfly/E066.md) |
| parameter_range_analysis | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | analysis_complete | [E071](E071_architecture_prerequisite_ranges/E071.md) |
| designs/dataflow_int | w10a10acc23 | 16 | 3.33 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | unknown | csim_pass | [E069](E069_final_candidate_all_supplied/E069.md) |

## Failed And Timed-Out Runs

| id | status | reason |
| --- | --- | --- |
| [E011](E011_apfixed_w16a16/E011.md) | fail | ; C simulation not accepted (exit=1); synthesis not eligible |
| [E023](E023_auto_inner_pipeline/E023.md) | invalid_config | ; requested II missed; Vitis skipped unknown syn.directive; numbers describe default scheduling, not intended directive experiment |
| [E024](E024_auto_pixel_pipeline/E024.md) | invalid_config | ; requested II missed; Vitis skipped unknown syn.directive; numbers describe default scheduling, not intended directive experiment |
| [E025](E025_auto_partition/E025.md) | invalid_config | ; requested II missed; Vitis skipped unknown syn.directive; numbers describe default scheduling, not intended directive experiment |
| [E034](E034_scan_T_T16_E034/E034.md) | fail | ; C simulation not accepted (exit=1); synthesis not eligible |
| [E035](E035_scan_T_T8_E035/E035.md) | fail | ; C simulation not accepted (exit=1); synthesis not eligible |
| [E018](E018_apfixed_w16a16_single/E018.md) | fail | ; C simulation not accepted (exit=1); synthesis not eligible |
| [E014](E014_apfixed_w16a16/E014.md) | timeout | ; C simulation not accepted (exit=124); synthesis not eligible |
| [E012](E012_apfixed_w10a10/E012.md) | fail | ; C simulation not accepted (exit=1); synthesis not eligible |
| [E046](E046_dataflow_wrap_T32/E046.md) | fail | ; Run lock exists: /home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/.synthesis.lock; inspect its PID before recovery |

E014 reached its 45-minute full-ap_fixed simulation limit after nine images; E010/E017 still cover all supplied pairs. Quoted absolute include paths broke Vitis C simulation; retries use verified unquoted whitespace-free paths. Lock-queue failures are distinct from subprocess synthesis timeouts.

## Figures

![Pareto](figs/pareto.png)

![Precision](figs/precision_heatmap.png)

![Compiler vs architecture](figs/compiler_vs_architecture.png)

## Pending Human Decisions

Missing comic input/GT pair blocks full 14-image acceptance. Windows Vitis environment was unavailable; verified Linux Vitis 2026.1 was used through existing SSH, with Windows environment-script support retained but untested. Review normalized-float PSNR versus the original wrapping uint8 metric before external benchmark claims. Detailed decisions and all tool failures remain in [LOG.md](LOG.md).

## Next Steps

Execute the authorized second phase on exp/explore-arch after phase-one completion. Prioritize packing/Winograd PE mapping, gather/scatter borders, memory banking and a loop schedule with continuous pixel throughput; compare all variants to the measured exact streaming baseline. Implement and RTL-cosim the best feasible provisional candidates while reporting the missing full-Set14 evidence.

Generated from results.csv and archived reference evidence at 2026-10-10T21:43:03+00:00.
