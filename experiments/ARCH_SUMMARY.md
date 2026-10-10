# SRCNN K26 architecture exploration

The fastest resource-feasible supplied-image point is [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) at 4.194708ms HLS-estimated latency. Packing and integer Winograd primitives pass exact checks, while full-network results include fabric, memory and scheduling costs absent from DSP-only budgets. Missing comic keeps every precision acceptance provisional; routed timing, RTL cycles and board validation are distinct evidence.

## Current Best

| id | design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | delta_psnr | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | designs/continuous_direct_r2 | w10a10acc23 | 16 | 4 | 3.239 | 1048677.0 | 1048678.0 | 4.194708 | 505.0 | 96.0 | 0.0 | 69362.0 | 106171.0 | -0.0695141811880653 | provisional |

HLS-estimate improvement over first-phase E043: 1.6543x. This ratio is not a measured board speedup.

Actual verification of the current HLS winner:

| id | operation | status | impl_WNS_ns | timing_met | impl_DSP | impl_LUT | impl_FF | impl_BRAM36 | impl_URAM | rtl_status | rtl_latency_max | rtl_interval_max | cycle_deviation_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## P Direction

Signed INT8 packing is exact when shared operands, field range and negative borrowing are handled explicitly. P01 exhausts16777216 signed8 triples; P03/P06 compare unpack-every7/every2 schedules under their respective safe bounds. P05 tests the DSP builtin and P08 inspects actual primitive attributes. Full-network exact10 residual variants retain the passing precision point but add fabric and pipeline overhead. Uniform w8a8 remains rejected by first-phase precision evidence.

Measured direction result: none of its completed frame points satisfies all resource/precision gates. Their estimated latency cannot establish a feasible speedup.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [P01](P01_signed8_pair/P01.md) | PE | 1 | 61.0 | 0.000244 | 1.0 | 0.0 | 0.0 | 132.0 | 86.0 | True | unknown | True | pass |
| [P02](P02_signed8_direct_control/P02.md) | PE | 1 | 58.0 | 0.000232 | 2.0 | 0.0 | 0.0 | 57.0 | 16.0 | True | unknown | True | pass |
| [P03](P03_signed8_group7/P03.md) | PE | 1 | 62.0 | 0.000248 | 1.0 | 0.0 | 0.0 | 299.0 | 309.0 | True | unknown | True | pass |
| [P04](P04_signed8_auto_mapping/P04.md) | PE | 1 | 61.0 | 0.000244 | 1.0 | 0.0 | 0.0 | 132.0 | 86.0 | True | unknown | True | pass |
| [P05](P05_signed8_builtin_preadder/P05.md) | PE | 1 | 63.0 | 0.000252 | 1.0 | 0.0 | 0.0 | 127.0 | 162.0 | True | unknown | True | pass |
| [P06](P06_nonnegative10_group2/P06.md) | PE | 1 | 62.0 | 0.000248 | 1.0 | 0.0 | 0.0 | 274.0 | 424.0 | True | unknown | True | pass |
| [P07](P07_exact10_residual_pair/P07.md) | PE | 1 | 62.0 | 0.000248 | 1.0 | 0.0 | 0.0 | 454.0 | 453.0 | True | unknown | True | pass |
| [P10](P10_exact10_packing_T16/P10.md) | frame | 16 | 3039083.0 | 12.156332 | 254.0 | 168.0 | 0.0 | 101488.0 | 80563.0 | True | 1.661846957728205e-05 | True | infeasible |
| [P11](P11_exact10_packing_T8/P11.md) | frame | 8 | 1894302.0 | 7.577208 | 505.0 | 168.0 | 0.0 | 165606.0 | 106599.0 | True | 1.661846957728205e-05 | True | infeasible |
| [P12](P12_exact10_packing_T4/P12.md) | frame | 4 | 1355582.0 | 5.422328 | 1007.0 | 168.0 | 0.0 | 292053.0 | 159828.0 | True | 1.661846957728205e-05 | True | infeasible |

## W Direction

G2=2G makes the F2 inverse exactly divisible by4 before the ordinary layer cast. W01/W03 confirm one DSP per transformed product at10/16-bit operands. The layer and network designs retain complete transform precision, split9x9 into nine3x3 pieces, generate128x128 tiles and reorder two rows into raster streams. Equivalent offline tensors are archived; runtime transforms preserve the fixed incoming-weight contract. Header-order compilation failures and independent retries remain visible.

Measured direction result: [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) is its fastest provisional resource-feasible point at 7.548204ms, with 326.0 DSP and 79158.0 LUT. RTL and routing must be assessed separately.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [W01](W01_integer_f2_10bit/W01.md) | PE | 1 | 36.0 | 0.000144 | 16.0 | 0.0 | 0.0 | 1499.0 | 1124.0 | True | unknown | True | pass |
| [W02](W02_direct_f2_control/W02.md) | PE | 1 | 38.0 | 0.000152 | 36.0 | 0.0 | 0.0 | 503.0 | 1025.0 | True | unknown | True | pass |
| [W03](W03_integer_f2_16bit/W03.md) | PE | 1 | 37.0 | 0.000148 | 16.0 | 0.0 | 0.0 | 2155.0 | 1932.0 | True | unknown | True | pass |
| [W07](W07_winograd_conv1_T16_header_retry/W07.md) | layer | 16 | 5721420.0 | 22.88568 | 145.0 | 99.0 | 0.0 | 30872.0 | 25564.0 | True | 4.121844856441791e-06 | True | provisional |
| [W04](W04_winograd_conv1_T16/W04.md) | layer | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [W05](W05_winograd_network_T16/W05.md) | frame | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [W06](W06_winograd_network_T8/W06.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) | frame | 16 | 1887051.0 | 7.548204 | 326.0 | 241.0 | 0.0 | 79158.0 | 76052.0 | True | 1.661846957728205e-05 | True | provisional |
| [W11](W11_fixed_tiles_T8_allcontinuous_4ns/W11.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [W12](W12_fixed_tiles_T16_allcontinuous_4ns/W12.md) | frame | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | frame | 16 | 5723851.0 | 22.895404 | 326.0 | 241.0 | 0.0 | 75814.0 | 69105.0 | True | 1.661846957728205e-05 | True | provisional |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | frame | 8 | 3493579.0 | 13.974316 | 648.0 | 241.0 | 0.0 | 135496.0 | 148761.0 | True | 1.661846957728205e-05 | True | infeasible |

## G Direction

Three Conv3 organizations share precision,T32 and10ns. Gather keeps four channel-wide lines; explicit-pad scatter keeps five32-bit partial rows plus a channel-wide pad row; merged-edge scatter replaces replicate padding with nine exact source-position kernels. Every output and border is checked on two butterfly frames. Memory savings carry control, load and cycle costs.

Measured direction result: [G01](G01_gather_control/G01.md) is its fastest provisional resource-feasible point at 29.83024ms, with 254.0 DSP and 44493.0 LUT. RTL and routing must be assessed separately.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [G01](G01_gather_control/G01.md) | frame | 32 | 2983024.0 | 29.83024 | 254.0 | 168.0 | 0.0 | 44493.0 | 46328.0 | True | 1.661846957728205e-05 | True | provisional |
| [G02](G02_scatter_pad_control/G02.md) | frame | 32 | 3770206.0 | 37.70206 | 254.0 | 137.0 | 0.0 | 39135.0 | 24841.0 | True | 1.661846957728205e-05 | True | provisional |
| [G03](G03_scatter_edge_kernels/G03.md) | frame | 32 | 4413926.0 | 44.13926 | 254.0 | 87.0 | 0.0 | 40677.0 | 25230.0 | True | 1.661846957728205e-05 | True | provisional |

## S Direction

Whole-network DATAFLOW is compared to sequential layers and8/16/32/64 output tiles. S01 did not export the required global scratch AXI bundles and is invalid as a DDR implementation; its oversized on-chip result is retained. Tile fusion preserves Conv3 replicate semantics by clamping feature centers before their input neighborhoods, and counts complete partial-edge halos. DDR payload divided by19.2GB/s (DS98764-bit DDR4-2400) and9.6GB/s (assumed50% efficiency) is a lower-bound model, never measured bandwidth. Requested256-word bursts are distinguished from actual compiler inference in bursts.csv.

Measured direction result: [S02](S02_whole_dataflow_control/S02.md) is its fastest provisional resource-feasible point at 29.83024ms, with 254.0 DSP and 44493.0 LUT. RTL and routing must be assessed separately.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [S01](S01_ddr_global_probe/S01.md) | frame | 32 | 16730473.0 | 167.30473 | 254.0 | 11286.0 | 0.0 | 48121.0 | 49034.0 | True | 1.661846957728205e-05 | unknown | invalid_config |
| [S02](S02_whole_dataflow_control/S02.md) | frame | 32 | 2983024.0 | 29.83024 | 254.0 | 168.0 | 0.0 | 44493.0 | 46328.0 | True | 1.661846957728205e-05 | True | provisional |
| [S03](S03_tile_fusion_B8/S03.md) | frame | 32 | 22803545.0 | 228.03545 | 296.0 | 18.0 | 0.0 | 113576.0 | 73880.0 | True | 1.661846957728205e-05 | True | infeasible |
| [S04](S04_tile_fusion_B16/S04.md) | frame | 32 | 16753977.0 | 167.53977 | 296.0 | 18.0 | 0.0 | 114061.0 | 73901.0 | True | 1.661846957728205e-05 | True | infeasible |
| [S05](S05_tile_fusion_B32/S05.md) | frame | 32 | 14166377.0 | 141.66377 | 296.0 | 18.0 | 0.0 | 120033.0 | 74038.0 | True | 1.661846957728205e-05 | True | infeasible |
| [S06](S06_tile_fusion_B64/S06.md) | frame | 32 | 12981873.0 | 129.81873 | 296.0 | 18.0 | 0.0 | 136162.0 | 74127.0 | True | 1.661846957728205e-05 | True | infeasible |

## C Direction

Exact Winograd Conv1 combines with output-channel packing Conv2 and/or adjacent-pixel packing Conv3. The paper T4 MAC budgets are932 DSP for both packed layers and1188 for only packed Conv3, before interfaces/converters. Exact10 residual restoration avoids the failed uniform INT8 precision point but adds LUT cost. A T8 control trades raster FIFO BRAM for LUTRAM. HLS estimates include transform/load/reorder overhead.

Completed PE/layer evidence is listed below; it does not establish a resource-feasible frame design.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C01](C01_wino_packing_T4_all/C01.md) | frame | 4 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C02](C02_wino_packing_T4_conv3/C02.md) | frame | 4 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C03](C03_wino_packing_T8_all/C03.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C08](C08_wino_conv2w8_continuous_T8/C08.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.405191888267716e-05 | unknown | fail |
| [C09](C09_wino_conv2w8_continuous_T4/C09.md) | frame | 4 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.405191888267716e-05 | unknown | fail |

## F Direction

Storage controls map shallow wide FIFOs to LUTRAM and Conv3 line banks to20 URAM. Continuous engines separate window generation, flatten pixel/fold iterations, shift fixed channel registers and register balanced fabric reductions. Old padding versus online read/emit padding isolates finite-FIFO row serialization. Clock/T controls test actual II, resource and timing limits; final RTL and routed measurements are separate from HLS estimates.

Measured direction result: [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) is its fastest provisional resource-feasible point at 4.194708ms, with 505.0 DSP and 69362.0 LUT. RTL and routing must be assessed separately.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F01](F01_fifo_lutram_control/F01.md) | frame | 16 | 2014678.0 | 8.058712 | 505.0 | 96.0 | 0.0 | 56081.0 | 62800.0 | True | 1.661846957728205e-05 | True | provisional |
| [F02](F02_uram_line_control/F02.md) | frame | 16 | 2014678.0 | 8.058712 | 505.0 | 132.0 | 20.0 | 56007.0 | 62948.0 | True | 1.661846957728205e-05 | True | provisional |
| [F03](F03_continuous_T16_oldpad_4ns/F03.md) | frame | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | frame | 16 | 1048677.0 | 4.194708 | 505.0 | 96.0 | 0.0 | 69362.0 | 106171.0 | True | 1.661846957728205e-05 | True | provisional |

## All Architectures

Frame records only, ordered by HLS-estimated latency. Microkernels and validation operations are excluded; infeasible/failed results remain visible.

| id | series | design | T_target | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | F | designs/continuous_direct_r2 | 16 | 4.194708 | 505.0 | 96.0 | 69362.0 | 106171.0 | -0.0695141811880653 | provisional |
| [P12](P12_exact10_packing_T4/P12.md) | P | designs/packing_network | 4 | 5.422328 | 1007.0 | 168.0 | 292053.0 | 159828.0 | -0.0695141811880653 | infeasible |
| [E043](E043_scan_clock_T16_E043/E043.md) | unknown | designs/dataflow_int | 16 | 6.93923049 | 505.0 | 168.0 | 55325.0 | 67025.0 | -0.0695141811880653 | provisional |
| [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) | W | designs/winograd_continuous | 16 | 7.548204 | 326.0 | 241.0 | 79158.0 | 76052.0 | -0.0695141811880653 | provisional |
| [P11](P11_exact10_packing_T8/P11.md) | P | designs/packing_network | 8 | 7.577208 | 505.0 | 168.0 | 165606.0 | 106599.0 | -0.0695141811880653 | infeasible |
| [E042](E042_scan_clock_T16_E042/E042.md) | unknown | designs/dataflow_int | 16 | 8.058712 | 505.0 | 168.0 | 56007.0 | 62948.0 | -0.0695141811880653 | provisional |
| [F01](F01_fifo_lutram_control/F01.md) | F | designs/fifo_lutram_control | 16 | 8.058712 | 505.0 | 96.0 | 56081.0 | 62800.0 | -0.0695141811880653 | provisional |
| [F02](F02_uram_line_control/F02.md) | F | designs/uram_line_control | 16 | 8.058712 | 505.0 | 132.0 | 56007.0 | 62948.0 | -0.0695141811880653 | provisional |
| [E041](E041_scan_clock_T16_E041/E041.md) | unknown | designs/dataflow_int | 16 | 9.7275 | 505.0 | 168.0 | 55553.0 | 59959.0 | -0.0695141811880653 | provisional |
| [E056](E056_mixed_T4_feasibility/E056.md) | unknown | designs/dataflow_mix | 4 | 10.46292 | 1160.0 | 168.0 | 237025.0 | 120073.0 | -0.0695141811880653 | infeasible |
| [P10](P10_exact10_packing_T16/P10.md) | P | designs/packing_network | 16 | 12.156332 | 254.0 | 168.0 | 101488.0 | 80563.0 | -0.0695141811880653 | infeasible |
| [E059](E059_integer_lutram_T8/E059.md) | unknown | designs/dataflow_int | 8 | 13.22968 | 1007.0 | 168.0 | 85147.0 | 88822.0 | -0.0695141811880653 | infeasible |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | W | designs/winograd_network_r1 | 8 | 13.974316 | 648.0 | 241.0 | 135496.0 | 148761.0 | -0.0695141811880653 | infeasible |
| [E064](E064_storage_0_T16/E064.md) | unknown | designs/dataflow_int | 16 | 18.07151 | 505.0 | 168.0 | 88306.0 | 138588.0 | -0.0695141811880653 | infeasible |
| [E058](E058_integer_lutram_T16/E058.md) | unknown | designs/dataflow_int | 16 | 18.7632 | 505.0 | 168.0 | 55212.0 | 57723.0 | -0.0695141811880653 | provisional |
| [E037](E037_scan_split_T16_E037/E037.md) | unknown | designs/dataflow_int | 16 | 18.7632 | 505.0 | 168.0 | 60050.0 | 56509.0 | -0.0695141811880653 | provisional |
| [E067](E067_storage_2_T16/E067.md) | unknown | designs/dataflow_int | 16 | 18.7632 | 505.0 | 670.0 | 53706.0 | 47716.0 | -0.0695141811880653 | infeasible |
| [E038](E038_scan_split_T16_E038/E038.md) | unknown | designs/dataflow_int | 16 | 21.55352 | 519.0 | 168.0 | 64526.0 | 57346.0 | -0.0695141811880653 | provisional |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | W | designs/winograd_network_r1 | 16 | 22.895404 | 326.0 | 241.0 | 75814.0 | 69105.0 | -0.0695141811880653 | provisional |
| [E047](E047_dataflow_dsp_T32/E047.md) | unknown | designs/dataflow_dsp | 32 | 29.13855 | 251.0 | 168.0 | 89341.0 | 132430.0 | -0.0695141811880653 | infeasible |
| [E063](E063_dataflow_wrap_T32_retry/E063.md) | unknown | designs/dataflow_wrap | 32 | 29.13855 | 148.0 | 168.0 | 95727.0 | 132430.0 | -0.0695141811880653 | infeasible |
| [E048](E048_dataflow_integer_T32/E048.md) | unknown | designs/dataflow_int | 32 | 29.13855 | 254.0 | 168.0 | 89304.0 | 132635.0 | -0.0695141811880653 | infeasible |
| [E039](E039_scan_storage_T32_E039/E039.md) | unknown | designs/dataflow_dsp | 32 | 29.83024 | 251.0 | 168.0 | 44530.0 | 46123.0 | -0.0695141811880653 | provisional |
| [E057](E057_integer_lutram_T32/E057.md) | unknown | designs/dataflow_int | 32 | 29.83024 | 254.0 | 168.0 | 44493.0 | 46328.0 | -0.0695141811880653 | provisional |
| [E040](E040_scan_storage_T32_E040/E040.md) | unknown | designs/dataflow_dsp | 32 | 29.83024 | 251.0 | 419.0 | 43275.0 | 41136.0 | -0.0695141811880653 | infeasible |
| [G01](G01_gather_control/G01.md) | G | designs/gather_control | 32 | 29.83024 | 254.0 | 168.0 | 44493.0 | 46328.0 | -0.0695141811880653 | provisional |
| [S02](S02_whole_dataflow_control/S02.md) | S | designs/gather_control | 32 | 29.83024 | 254.0 | 168.0 | 44493.0 | 46328.0 | -0.0695141811880653 | provisional |
| [E060](E060_scatter_integer_T32/E060.md) | unknown | designs/scatter_int | 32 | 37.70206 | 254.0 | 137.0 | 39135.0 | 24841.0 | -0.0695141811880653 | provisional |
| [G02](G02_scatter_pad_control/G02.md) | G | designs/scatter_pad_control | 32 | 37.70206 | 254.0 | 137.0 | 39135.0 | 24841.0 | -0.0695141811880653 | provisional |
| [E050](E050_scatter_T32/E050.md) | unknown | designs/scatter_v1 | 32 | 38.82221 | 34.0 | 137.0 | 127718.0 | 128434.0 | -0.0695141811880653 | infeasible |
| [G03](G03_scatter_edge_kernels/G03.md) | G | designs/scatter_edge | 32 | 44.13926 | 254.0 | 87.0 | 40677.0 | 25230.0 | -0.0695141811880653 | provisional |
| [E036](E036_scan_split_T16_E036/E036.md) | unknown | designs/dataflow_int | 16 | 78.94023 | 565.0 | 168.0 | 79846.0 | 76416.0 | -0.0695141811880653 | provisional |
| [E033](E033_dataflow_fixed_T32_single/E033.md) | unknown | designs/dataflow_v1 | 32 | 123.540036662 | 9.0 | 168.0 | 136868.0 | 149111.0 | -0.0695141811880653 | infeasible |
| [E031](E031_dataflow_fixed_T32/E031.md) | unknown | designs/dataflow_v1 | 32 | 123.540036662 | 9.0 | 168.0 | 136868.0 | 149111.0 | -0.0695141811880653 | infeasible |
| [S06](S06_tile_fusion_B64/S06.md) | S | designs/tile_fusion | 32 | 129.81873 | 296.0 | 18.0 | 136162.0 | 74127.0 | -0.0695141811880653 | infeasible |
| [S05](S05_tile_fusion_B32/S05.md) | S | designs/tile_fusion | 32 | 141.66377 | 296.0 | 18.0 | 120033.0 | 74038.0 | -0.0695141811880653 | infeasible |
| [S01](S01_ddr_global_probe/S01.md) | S | designs/ddr_global_probe | 32 | 167.30473 | 254.0 | 11286.0 | 48121.0 | 49034.0 | -0.0695141811880653 | invalid_config |
| [S04](S04_tile_fusion_B16/S04.md) | S | designs/tile_fusion | 32 | 167.53977 | 296.0 | 18.0 | 114061.0 | 73901.0 | -0.0695141811880653 | infeasible |
| [E044](E044_scan_T_T16_E034_retry/E044.md) | unknown | designs/dataflow_v1 | 16 | 175.462633706 | 18.0 | 168.0 | 167715.0 | 135714.0 | -0.0695141811880653 | infeasible |
| [S03](S03_tile_fusion_B8/S03.md) | S | designs/tile_fusion | 32 | 228.03545 | 296.0 | 18.0 | 113576.0 | 73880.0 | -0.0695141811880653 | infeasible |
| [E045](E045_scan_T_T8_E035_retry/E045.md) | unknown | designs/dataflow_v1 | 8 | 280.01056732 | 36.0 | 168.0 | 266266.0 | 142153.0 | -0.0695141811880653 | infeasible |
| [E030](E030_dataflow_float/E030.md) | unknown | designs/dataflow_v1 | 32 | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass |
| [E034](E034_scan_T_T16_E034/E034.md) | unknown | designs/dataflow_v1 | 16 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [E035](E035_scan_T_T8_E035/E035.md) | unknown | designs/dataflow_v1 | 8 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [E049](E049_integer_boundary_exhaustive/E049.md) | unknown | designs/dataflow_int | unknown | unknown | unknown | unknown | unknown | unknown | unknown | csim_pass |
| [E046](E046_dataflow_wrap_T32/E046.md) | unknown | designs/dataflow_wrap | 32 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [E069](E069_final_candidate_all_supplied/E069.md) | unknown | designs/dataflow_int | 16 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | csim_pass |
| [C01](C01_wino_packing_T4_all/C01.md) | C | designs/combination_network | 4 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C02](C02_wino_packing_T4_conv3/C02.md) | C | designs/combination_network | 4 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C03](C03_wino_packing_T8_all/C03.md) | C | designs/combination_network | 8 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [W05](W05_winograd_network_T16/W05.md) | W | designs/winograd_network | 16 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [W06](W06_winograd_network_T8/W06.md) | W | designs/winograd_network | 8 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [W11](W11_fixed_tiles_T8_allcontinuous_4ns/W11.md) | W | designs/winograd_continuous | 8 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [C08](C08_wino_conv2w8_continuous_T8/C08.md) | C | designs/winograd_mixed_packing | 8 | unknown | unknown | unknown | unknown | unknown | -0.07589037644656216 | fail |
| [W12](W12_fixed_tiles_T16_allcontinuous_4ns/W12.md) | W | designs/winograd_continuous | 16 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [F03](F03_continuous_T16_oldpad_4ns/F03.md) | F | designs/continuous_direct | 16 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [C09](C09_wino_conv2w8_continuous_T4/C09.md) | C | designs/winograd_mixed_packing | 4 | unknown | unknown | unknown | unknown | unknown | -0.07589037644656216 | fail |

## Estimates And Actuals

All numeric values come from frozen plans and parsed reports. Actual means csynth for ordinary runs, routed resources for implementation, and RTL latency for cosim; no cycle measurement is inferred from implementation. Memory/LUT audits are in estimate_actual.csv and each experiment.

| id | scope | DSP_estimate | DSP_actual | DSP_deviation_pct | cycles_estimate | cycles_actual | cycles_deviation_pct | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [P01](P01_signed8_pair/P01.md) | PE | 1.0 | 1.0 | 0.0 | 64.0 | 61.0 | -4.6875 | pass |
| [P02](P02_signed8_direct_control/P02.md) | PE | 2.0 | 2.0 | 0.0 | 64.0 | 58.0 | -9.375 | pass |
| [W01](W01_integer_f2_10bit/W01.md) | PE | 16.0 | 16.0 | 0.0 | 44.0 | 36.0 | -18.181818181818176 | pass |
| [P03](P03_signed8_group7/P03.md) | PE | 1.0 | 1.0 | 0.0 | 64.0 | 62.0 | -3.125 | pass |
| [W02](W02_direct_f2_control/W02.md) | PE | 36.0 | 36.0 | 0.0 | 44.0 | 38.0 | -13.636363636363635 | pass |
| [P04](P04_signed8_auto_mapping/P04.md) | PE | 1.0 | 1.0 | 0.0 | 64.0 | 61.0 | -4.6875 | pass |
| [W03](W03_integer_f2_16bit/W03.md) | PE | 16.0 | 16.0 | 0.0 | 44.0 | 37.0 | -15.909090909090907 | pass |
| [P05](P05_signed8_builtin_preadder/P05.md) | PE | 1.0 | 1.0 | 0.0 | 64.0 | 63.0 | -1.5625 | pass |
| [P06](P06_nonnegative10_group2/P06.md) | PE | 1.0 | 1.0 | 0.0 | 64.0 | 62.0 | -3.125 | pass |
| [P07](P07_exact10_residual_pair/P07.md) | PE | 1.0 | 1.0 | 0.0 | 64.0 | 62.0 | -3.125 | pass |
| [G01](G01_gather_control/G01.md) | frame | 254.0 | 254.0 | 0.0 | 2983024.0 | 2983024.0 | 0.0 | provisional |
| [G02](G02_scatter_pad_control/G02.md) | frame | 254.0 | 254.0 | 0.0 | 3770206.0 | 3770206.0 | 0.0 | provisional |
| [S01](S01_ddr_global_probe/S01.md) | frame | 254.0 | 254.0 | 0.0 | 6250529.0 | 16730473.0 | 167.6649128417771 | invalid_config |
| [G03](G03_scatter_edge_kernels/G03.md) | frame | 254.0 | 254.0 | 0.0 | 3700000.0 | 4413926.0 | 19.29529729729729 | provisional |
| [S02](S02_whole_dataflow_control/S02.md) | frame | 254.0 | 254.0 | 0.0 | 2983024.0 | 2983024.0 | 0.0 | provisional |
| [P10](P10_exact10_packing_T16/P10.md) | frame | 254.0 | 254.0 | 0.0 | 2130800.0 | 3039083.0 | 42.62638445654214 | infeasible |
| [C01](C01_wino_packing_T4_all/C01.md) | frame | 935.0 | unknown | unknown | 715360.0 | unknown | unknown | fail |
| [C02](C02_wino_packing_T4_conv3/C02.md) | frame | 1191.0 | unknown | unknown | 715360.0 | unknown | unknown | fail |
| [C03](C03_wino_packing_T8_all/C03.md) | frame | 469.0 | unknown | unknown | 977504.0 | unknown | unknown | fail |
| [S03](S03_tile_fusion_B8/S03.md) | frame | 254.0 | 296.0 | 16.535433070866134 | 11935713.0 | 22803545.0 | 91.05306067597303 | infeasible |
| [P11](P11_exact10_packing_T8/P11.md) | frame | 505.0 | 505.0 | 0.0 | 1610600.0 | 1894302.0 | 17.614677759841047 | infeasible |
| [S04](S04_tile_fusion_B16/S04.md) | frame | 254.0 | 296.0 | 16.535433070866134 | 8843233.0 | 16753977.0 | 89.45533833610399 | infeasible |
| [W07](W07_winograd_conv1_T16_header_retry/W07.md) | layer | 144.0 | 145.0 | 0.694444444444442 | 1431256.0 | 5721420.0 | 299.7481931953473 | provisional |
| [S05](S05_tile_fusion_B32/S05.md) | frame | 254.0 | 296.0 | 16.535433070866134 | 7521249.0 | 14166377.0 | 88.3513895099072 | infeasible |
| [P12](P12_exact10_packing_T4/P12.md) | frame | 1007.0 | 1007.0 | 0.0 | 1350500.0 | 1355582.0 | 0.3763050721954819 | infeasible |
| [W04](W04_winograd_conv1_T16/W04.md) | layer | 144.0 | unknown | unknown | 1431256.0 | unknown | unknown | fail |
| [W05](W05_winograd_network_T16/W05.md) | frame | 325.0 | unknown | unknown | 1431256.0 | unknown | unknown | fail |
| [W06](W06_winograd_network_T8/W06.md) | frame | 647.0 | unknown | unknown | 906968.0 | unknown | unknown | fail |
| [S06](S06_tile_fusion_B64/S06.md) | frame | 254.0 | 296.0 | 16.535433070866134 | 6916321.0 | 12981873.0 | 87.69911055313946 | infeasible |
| [F01](F01_fifo_lutram_control/F01.md) | frame | 505.0 | 505.0 | 0.0 | 2014678.0 | 2014678.0 | 0.0 | provisional |
| [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) | frame | 325.0 | 326.0 | 0.3076923076922977 | 2100000.0 | 1887051.0 | -10.140428571428572 | provisional |
| [F02](F02_uram_line_control/F02.md) | frame | 505.0 | 505.0 | 0.0 | 2014678.0 | 2014678.0 | 0.0 | provisional |
| [W11](W11_fixed_tiles_T8_allcontinuous_4ns/W11.md) | frame | 647.0 | unknown | unknown | 620200.0 | unknown | unknown | fail |
| [C08](C08_wino_conv2w8_continuous_T8/C08.md) | frame | 519.0 | unknown | unknown | 620200.0 | unknown | unknown | fail |
| [W12](W12_fixed_tiles_T16_allcontinuous_4ns/W12.md) | frame | 325.0 | unknown | unknown | 1140400.0 | unknown | unknown | fail |
| [P08](P08_builtin_mapping_implementation/P08.md) | PE | 1.0 | 1.0 | 0.0 | 63.0 | unknown | unknown | impl_complete |
| [F03](F03_continuous_T16_oldpad_4ns/F03.md) | frame | 505.0 | unknown | unknown | 1140400.0 | unknown | unknown | fail |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | frame | 325.0 | 326.0 | 0.3076923076922977 | 1431256.0 | 5723851.0 | 299.9180440116932 | provisional |
| [C09](C09_wino_conv2w8_continuous_T4/C09.md) | frame | 1035.0 | unknown | unknown | 360100.0 | unknown | unknown | fail |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | frame | 647.0 | 648.0 | 0.15455950540959051 | 906968.0 | 3493579.0 | 285.1931931446313 | infeasible |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | frame | 505.0 | 505.0 | 0.0 | 1140400.0 | 1048677.0 | -8.043055068397054 | provisional |

Largest percentage deviations (a zero paper denominator has no percentage):

| id | metric | estimate | actual | deviation_pct | status |
| --- | --- | --- | --- | --- | --- |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | latency_cycles | 1431256.0 | 5723851.0 | 299.9180440116932 | provisional |
| [W07](W07_winograd_conv1_T16_header_retry/W07.md) | latency_cycles | 1431256.0 | 5721420.0 | 299.7481931953473 | provisional |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | latency_cycles | 906968.0 | 3493579.0 | 285.1931931446313 | infeasible |
| [S01](S01_ddr_global_probe/S01.md) | latency_cycles | 6250529.0 | 16730473.0 | 167.6649128417771 | invalid_config |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | LUT | 59000.0 | 135496.0 | 129.65423728813562 | infeasible |
| [S03](S03_tile_fusion_B8/S03.md) | latency_cycles | 11935713.0 | 22803545.0 | 91.05306067597303 | infeasible |
| [S04](S04_tile_fusion_B16/S04.md) | latency_cycles | 8843233.0 | 16753977.0 | 89.45533833610399 | infeasible |
| [S05](S05_tile_fusion_B32/S05.md) | latency_cycles | 7521249.0 | 14166377.0 | 88.3513895099072 | infeasible |
| [S06](S06_tile_fusion_B64/S06.md) | latency_cycles | 6916321.0 | 12981873.0 | 87.69911055313946 | infeasible |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | LUT | 41000.0 | 75814.0 | 84.91219512195123 | provisional |
| [W02](W02_direct_f2_control/W02.md) | LUT | 1100.0 | 503.0 | -54.27272727272727 | pass |
| [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) | LUT | 55000.0 | 79158.0 | 43.92363636363636 | provisional |

Cause analysis is in each linked interpretation: ignored external scratch ports allocate full on-chip maps; dynamic tiled memory banks add address/multiplexer logic; packing residual/borrow stages increase both LUT and per-pixel pipeline drain; wider Winograd inverse arithmetic and raster FIFOs exceed pure-product budgets; explicit register reductions change timing and FF.

## Implementation And Cosim

HLS estimates are inherited only for provenance. Routed WNS/resources and two-frame RTL cycles are parsed independently; none is a board measurement.

| id | scope | parent | operation | status | impl_DSP | impl_BRAM36 | impl_LUT | impl_FF | impl_URAM | impl_WNS_ns | timing_met | rtl_status | rtl_latency_max | rtl_interval_max | cycle_deviation_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [E070](E070_first_feasible_implementation/E070.md) | frame | E039 | impl | impl_complete | 270.0 | 31.0 | 20454.0 | 33844.0 | 0.0 | -1.277 | False | unknown | unknown | unknown | unknown |
| [P08](P08_builtin_mapping_implementation/P08.md) | PE | P05 | impl | impl_complete | 1.0 | 0.0 | 21.0 | 41.0 | 0.0 | 2.805 | True | unknown | unknown | unknown | unknown |

DATAFLOW warnings are retained in [dataflow_warnings.csv](dataflow_warnings.csv) and the linked experiment interpretations. Caller-weight/predecessor synchronization is a possible throughput limit; reported II1 alone does not prove finite-FIFO progress.

| id | dataflow_warning_count | status |
| --- | --- | --- |
| [G01](G01_gather_control/G01.md) | 3 | provisional |
| [G02](G02_scatter_pad_control/G02.md) | 3 | provisional |
| [S01](S01_ddr_global_probe/S01.md) | 8 | invalid_config |
| [G03](G03_scatter_edge_kernels/G03.md) | 3 | provisional |
| [S02](S02_whole_dataflow_control/S02.md) | 3 | provisional |
| [P10](P10_exact10_packing_T16/P10.md) | 3 | infeasible |
| [P11](P11_exact10_packing_T8/P11.md) | 3 | infeasible |
| [W07](W07_winograd_conv1_T16_header_retry/W07.md) | 1 | provisional |
| [P12](P12_exact10_packing_T4/P12.md) | 3 | infeasible |
| [F01](F01_fifo_lutram_control/F01.md) | 3 | provisional |
| [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) | 4 | provisional |
| [F02](F02_uram_line_control/F02.md) | 3 | provisional |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | 3 | provisional |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | 3 | infeasible |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | 5 | provisional |

## Failed Directions

| id | series | status | failure_reason | notes |
| --- | --- | --- | --- | --- |
| [S01](S01_ddr_global_probe/S01.md) | S | invalid_config | ; Required external DDR AXI bundles not generated: scratch1, scratch2 | ; Required external DDR AXI bundles not generated: scratch1, scratch2 |
| [P10](P10_exact10_packing_T16/P10.md) | P | infeasible | LUT=101488.0 exceeds 81984 | unknown |
| [C01](C01_wino_packing_T4_all/C01.md) | C | fail | F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:125:7: error: expected identifier; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:570:77: error: expected ';' at end of declaration | ; C simulation not accepted (exit=1); synthesis not eligible |
| [C02](C02_wino_packing_T4_conv3/C02.md) | C | fail | F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:125:7: error: expected identifier; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:570:77: error: expected ';' at end of declaration | ; C simulation not accepted (exit=1); synthesis not eligible |
| [C03](C03_wino_packing_T8_all/C03.md) | C | fail | F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:125:7: error: expected identifier; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:570:77: error: expected ';' at end of declaration | ; C simulation not accepted (exit=1); synthesis not eligible |
| [S03](S03_tile_fusion_B8/S03.md) | S | infeasible | LUT=113576.0 exceeds 81984 | unknown |
| [P11](P11_exact10_packing_T8/P11.md) | P | infeasible | LUT=165606.0 exceeds 81984 | unknown |
| [S04](S04_tile_fusion_B16/S04.md) | S | infeasible | LUT=114061.0 exceeds 81984 | unknown |
| [S05](S05_tile_fusion_B32/S05.md) | S | infeasible | LUT=120033.0 exceeds 81984 | unknown |
| [P12](P12_exact10_packing_T4/P12.md) | P | infeasible | LUT=292053.0 exceeds 81984 | unknown |
| [W04](W04_winograd_conv1_T16/W04.md) | W | fail | F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:125:7: error: expected identifier; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:570:77: error: expected ';' at end of declaration | ; C simulation not accepted (exit=1); synthesis not eligible |
| [W05](W05_winograd_network_T16/W05.md) | W | fail | F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:125:7: error: expected identifier; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:570:77: error: expected ';' at end of declaration | ; C simulation not accepted (exit=1); synthesis not eligible |
| [W06](W06_winograd_network_T8/W06.md) | W | fail | F2/F3 size macros collide with AMD ap_fixed header identifiers; independent header-order retries preserve the failed source; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:125:7: error: expected identifier; /home/lipuze/amdfpga/2026.1/Vitis/include/etc/ap_fixed_base.h:570:77: error: expected ';' at end of declaration | ; C simulation not accepted (exit=1); synthesis not eligible |
| [S06](S06_tile_fusion_B64/S06.md) | S | infeasible | LUT=136162.0 exceeds 81984 | unknown |
| [W11](W11_fixed_tiles_T8_allcontinuous_4ns/W11.md) | W | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (W11/source/srcnn.cpp:488:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [C08](C08_wino_conv2w8_continuous_T8/C08.md) | C | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (C08/source/srcnn.cpp:462:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [W12](W12_fixed_tiles_T16_allcontinuous_4ns/W12.md) | W | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (W12/source/srcnn.cpp:488:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [F03](F03_continuous_T16_oldpad_4ns/F03.md) | F | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (F03/source/srcnn.cpp:312:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [C09](C09_wino_conv2w8_continuous_T4/C09.md) | C | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (C09/source/srcnn.cpp:462:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | W | infeasible | LUT=135496.0 exceeds 81984 | unknown |

## Pending Human Decisions

- Supply the missing comic pair before complete14-image precision acceptance. All13 supplied pairs remain mandatory.
- DDR sequential layers need explicit scratch pointers or an approved wrapper; global m_axi did not export ports in S01.
- Runtime transformed-weight loading preserves the frozen top signature; true offline-transformed input parameters require an approved new weight contract.
- Windows settings-batch execution and board integration remain unverified. The existing Linux Vitis2026.1 SSH installation was used.
- Review normalized-float PSNR against the original wrapping uint8 metric before external benchmark claims. See [LOG.md](LOG.md).

## Next Steps

Use the best exact resource-feasible architecture as the integration candidate only after checking routed slack and finite-FIFO RTL evidence. Prioritize the measured limiting loop/path or memory bank; retain strict precision, border and resource gates. Complete the missing image and board/AXI system measurements before claiming deployable performance.

## Figures

![Latency vs DSP by series](figs/architecture_pareto.png)

![DSP composition](figs/architecture_dsp_layers.png)

![DSP estimates vs actual](figs/estimate_actual_dsp.png)

![Cycle estimates vs actual](figs/estimate_actual_cycles.png)

![Conv3 resource comparison](figs/conv3_resources.png)

![Conv3 core and pad resource comparison](figs/conv3_core_resources.png)

Generated from archived evidence at 2026-10-10T23:32:22+00:00.
