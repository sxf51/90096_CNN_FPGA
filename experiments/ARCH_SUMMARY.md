# SRCNN K26 architecture exploration

The fastest resource-feasible supplied-image point is [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) at 2.64226ms HLS-estimated latency. Packing and integer Winograd primitives pass exact checks, while full-network results include fabric, memory and scheduling costs absent from DSP-only budgets. Missing comic keeps every precision acceptance provisional; routed timing, RTL cycles and board validation are distinct evidence.

Re-run frozen HLS records with fresh IDs using the [reproduction guide](REPRODUCE.md). Original reserved IDs remain immutable.

## Current Best

| id | design | precision_w_a_acc | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | delta_psnr | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) | designs/continuous_nested_load_v1 | w10a10acc23 | 16 | 2.5 | 2.377 | 1056904.0 | 1056905.0 | 2.64226 | 502.0 | 73.0 | 0.0 | 69976.0 | 125404.0 | -0.0695141811880653 | provisional |

HLS-estimate improvement over first-phase E043: 2.6262x. This ratio is not a measured board speedup.

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
| [P09](P09_reproduction_P01/P09.md) | PE | 1 | 61.0 | 0.000244 | 1.0 | 0.0 | 0.0 | 132.0 | 86.0 | True | unknown | True | pass |

## W Direction

G2=2G makes the F2 inverse exactly divisible by4 before the ordinary layer cast. W01/W03 confirm one DSP per transformed product at10/16-bit operands. The layer and network designs retain complete transform precision, split9x9 into nine3x3 pieces, generate128x128 tiles and reorder two rows into raster streams. Equivalent offline tensors are archived; runtime transforms preserve the fixed incoming-weight contract. Header-order compilation failures and independent retries remain visible.

Measured direction result: [W18](W18_narrow_raw_banks_T16/W18.md) is its fastest provisional resource-feasible point at 4.2274ms, with 326.0 DSP and 74480.0 LUT. RTL and routing must be assessed separately.

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
| [W13](W13_fixed_tiles_T8_allcontinuous_3p33ns/W13.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [W17](W17_narrow_raw_banks_T8/W17.md) | frame | 8 | 532562.0 | 2.130248 | 648.0 | 146.0 | 0.0 | 93166.0 | 122399.0 | True | 1.661846957728205e-05 | True | infeasible |
| [W18](W18_narrow_raw_banks_T16/W18.md) | frame | 16 | 1056850.0 | 4.2274 | 326.0 | 146.0 | 0.0 | 74480.0 | 87869.0 | True | 1.661846957728205e-05 | True | provisional |
| [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | frame | 8 | 532562.0 | 2.130248 | 648.0 | 146.0 | 0.0 | 148013.0 | 182409.0 | True | 1.661846957728205e-05 | True | infeasible |
| [W15](W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) | frame | 16 | 1056850.0 | 4.2274 | 326.0 | 146.0 | 0.0 | 89114.0 | 92946.0 | True | 1.661846957728205e-05 | True | infeasible |
| [W16](W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | frame | 8 | 532569.0 | 1.77345477 | 648.0 | 146.0 | 0.0 | 145767.0 | 192756.0 | True | 1.661846957728205e-05 | True | infeasible |

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

Traffic/cache models and inferred image burst lengths (words):

| id | ddr_bytes_per_frame | feature_recompute_ratio | cache_bits | inferred_image_read_bursts | inferred_image_write_bursts | ddr_theoretical_lower_bound_ms | ddr_50pct_lower_bound_ms | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [S01](S01_ddr_global_probe/S01.md) | 50491916 | unknown | unknown | none reported | none reported | 2.629787291666667 | 5.259574583333334 | invalid_config |
| [S02](S02_whole_dataflow_control/S02.md) | 552716 | unknown | unknown | none reported | none reported | unknown | unknown | provisional |
| [S03](S03_tile_fusion_B8/S03.md) | 1931016 | 2.267681660899654 | 50080 | none reported | none reported | 0.10057375 | 0.2011475 | infeasible |
| [S04](S04_tile_fusion_B16/S04.md) | 1095432 | 1.5747789311803153 | 135840 | none reported | none reported | 0.05705375 | 0.1141075 | infeasible |
| [S05](S05_tile_fusion_B32/S05.md) | 788232 | 1.2755709342560553 | 434080 | none reported | none reported | 0.04105375 | 0.0821075 | infeasible |
| [S06](S06_tile_fusion_B64/S06.md) | 662280 | 1.1377777777777778 | 1537440 | none reported | none reported | 0.03449375 | 0.0689875 | infeasible |

Bandwidth inputs are from [DS987 and calculation sources](SOURCES.md). S01's traffic is a hypothetical sequential-DDR payload because its scratch ports were absent; tile/dataflow payloads describe their implemented interfaces. Missing burst inference is shown as 'none reported'; requested256-word limits remain configuration bounds.

## C Direction

Exact Winograd Conv1 combines with output-channel packing Conv2 and/or adjacent-pixel packing Conv3. The paper T4 MAC budgets are932 DSP for both packed layers and1188 for only packed Conv3, before interfaces/converters. Exact10 residual restoration avoids the failed uniform INT8 precision point but adds LUT cost. C10/C11 instead use independently verified Conv2-only8-bit weights and ten-bit activations, removing coefficient residual repair in that layer. HLS estimates include transform/load/reorder overhead.

Measured direction result: none of its completed frame points satisfies all resource/precision gates. Their estimated latency cannot establish a feasible speedup.

An unimplemented raw-bank combination follow-up would still need about 96004.0 LUT if [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) reused the measured 54847.0-LUT whole-network saving from [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) to [W17](W17_narrow_raw_banks_T8/W17.md). This transfer projection is above the unchanged 81984.0-LUT gate and is not a synthesis result; no follow-up is treated as feasible on that assumption.

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C01](C01_wino_packing_T4_all/C01.md) | frame | 4 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C02](C02_wino_packing_T4_conv3/C02.md) | frame | 4 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C03](C03_wino_packing_T8_all/C03.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C08](C08_wino_conv2w8_continuous_T8/C08.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.405191888267716e-05 | unknown | fail |
| [C09](C09_wino_conv2w8_continuous_T4/C09.md) | frame | 4 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.405191888267716e-05 | unknown | fail |
| [C04](C04_wino_packing_T4_all_header_retry/C04.md) | frame | 4 | 2378443.0 | 9.513772 | 936.0 | 241.0 | 0.0 | 293222.0 | 253809.0 | True | 1.661846957728205e-05 | True | infeasible |
| [C07](C07_continuous_wino_packing_T8/C07.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [C12](C12_continuous_wino_packing_T8_guard_retry/C12.md) | frame | 8 | 1894303.0 | 7.577212 | 470.0 | 169.0 | 0.0 | 174591.0 | 161653.0 | True | 1.661846957728205e-05 | True | infeasible |
| [C05](C05_wino_packing_T4_conv3_header_retry/C05.md) | frame | 4 | 2378443.0 | 9.513772 | 1192.0 | 241.0 | 0.0 | 260882.0 | 263747.0 | True | 1.661846957728205e-05 | True | infeasible |
| [C06](C06_wino_packing_T8_all_header_retry/C06.md) | frame | 8 | 3493579.0 | 13.974316 | 470.0 | 169.0 | 0.0 | 170165.0 | 153644.0 | True | 1.661846957728205e-05 | True | infeasible |
| [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) | frame | 8 | 532562.0 | 2.130248 | 520.0 | 146.0 | 0.0 | 150851.0 | 179452.0 | True | 1.405191888267716e-05 | True | infeasible |
| [C11](C11_wino_conv2w8_continuous_T4_split4000/C11.md) | frame | 4 | 270418.0 | 1.081672 | 1036.0 | 146.0 | 0.0 | 248797.0 | 307525.0 | True | 1.405191888267716e-05 | True | infeasible |

## F Direction

Storage controls map shallow wide FIFOs to LUTRAM and Conv3 line banks to20 URAM. Continuous engines separate window generation, flatten pixel/fold iterations, shift fixed channel registers and register balanced fabric reductions. Old padding versus online read/emit padding isolates finite-FIFO row serialization. Clock/T controls test actual II, resource and timing limits; final RTL and routed measurements are separate from HLS estimates.

Measured direction result: [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) is its fastest provisional resource-feasible point at 2.64226ms, with 502.0 DSP and 69976.0 LUT. RTL and routing must be assessed separately.

The exact IEEE output encoder [F20](F20_ieee_decode_bit_exact_sdk_retry_unique_object/F20.md) uses 0.0 DSP, 242.0 LUT and 52.0 FF at 2.051ns estimated clock; its legacy control [F21](F21_ieee_decode_legacy_control_sdk_retry_unique_object/F21.md) uses 3.0 DSP at 3.239ns. The independent network copy [F23](F23_continuous_ieee_T16_2p5ns/F23.md) keeps the same quantization and weights, reaches 2.822ns estimated clock and removes the legacy output scaling DSPs. Continuous folds reduce the repeated per-pixel pipeline fill/drain; assess finite-FIFO RTL cycles and routed timing in the final verification table independently of that HLS estimate.

Loader controls preserve all inference engines, precision and runtime parameters. F24 removes the quotient-address multiplier; F25 tests the flattened counter versus repeated inner-loop drain. Compare the measured top clock/frame product:

| id | clock_target_ns | clock_est_ns | latency_cycles | latency_ms_est | DSP | BRAM18K | LUT | FF | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F23](F23_continuous_ieee_T16_2p5ns/F23.md) | 2.5 | 2.822 | 1048730.0 | 2.95951606 | 502.0 | 73.0 | 70449.0 | 125618.0 | provisional |
| [F24](F24_affine_weight_loader_T16_2p5ns/F24.md) | 2.5 | 2.699 | 1048723.0 | 2.830503377 | 502.0 | 73.0 | 69290.0 | 124577.0 | provisional |
| [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) | 2.5 | 2.377 | 1056904.0 | 2.64226 | 502.0 | 73.0 | 69976.0 | 125404.0 | provisional |

| id | scope | T_target | latency_cycles | latency_ms_est | DSP | BRAM18K | URAM | LUT | FF | bit_exact | border_mse | ii_ok | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F01](F01_fifo_lutram_control/F01.md) | frame | 16 | 2014678.0 | 8.058712 | 505.0 | 96.0 | 0.0 | 56081.0 | 62800.0 | True | 1.661846957728205e-05 | True | provisional |
| [F02](F02_uram_line_control/F02.md) | frame | 16 | 2014678.0 | 8.058712 | 505.0 | 132.0 | 20.0 | 56007.0 | 62948.0 | True | 1.661846957728205e-05 | True | provisional |
| [F03](F03_continuous_T16_oldpad_4ns/F03.md) | frame | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | frame | 16 | 1048677.0 | 4.194708 | 505.0 | 96.0 | 0.0 | 69362.0 | 106171.0 | True | 1.661846957728205e-05 | True | provisional |
| [F16](F16_ieee_decode_bit_exact/F16.md) | PE | 1 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [F17](F17_ieee_decode_legacy_control/F17.md) | PE | 1 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [F18](F18_ieee_decode_bit_exact_sdk_retry/F18.md) | PE | 1 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [F19](F19_ieee_decode_legacy_control_sdk_retry/F19.md) | PE | 1 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [F04](F04_continuous_T16_online_4ns/F04.md) | frame | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [F13](F13_rotate_c3_T16_tree1_4ns/F13.md) | frame | 16 | 1048687.0 | 4.194748 | 505.0 | 73.0 | 0.0 | 68903.0 | 106661.0 | True | 1.661846957728205e-05 | True | provisional |
| [F05](F05_continuous_T8_online_4ns/F05.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [F06](F06_continuous_T16_online_3p33ns/F06.md) | frame | 16 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [F14](F14_rotate_c3_T8_tree1_4ns/F14.md) | frame | 8 | 528488.0 | 2.113952 | 1007.0 | 73.0 | 0.0 | 96488.0 | 171235.0 | True | 1.661846957728205e-05 | True | infeasible |
| [F07](F07_continuous_T8_online_3p33ns/F07.md) | frame | 8 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | fail |
| [F09](F09_continuous_T16_online_4ns_split4000/F09.md) | frame | 16 | 1048687.0 | 4.194748 | 505.0 | 73.0 | 0.0 | 69179.0 | 106647.0 | True | 1.661846957728205e-05 | True | provisional |
| [F15](F15_rotate_c3_T8_tree0_4ns/F15.md) | frame | 8 | 528481.0 | 2.113924 | 1007.0 | 73.0 | 0.0 | 101994.0 | 86073.0 | True | 1.661846957728205e-05 | True | infeasible |
| [F10](F10_continuous_T8_online_4ns_split4000/F10.md) | frame | 8 | 528488.0 | 2.113952 | 1007.0 | 73.0 | 0.0 | 96764.0 | 171240.0 | True | 1.661846957728205e-05 | True | infeasible |
| [F20](F20_ieee_decode_bit_exact_sdk_retry_unique_object/F20.md) | PE | 1 | 1027.0 | 0.00341991 | 0.0 | 0.0 | 0.0 | 242.0 | 52.0 | True | unknown | True | pass |
| [F11](F11_continuous_T16_online_3p33ns_split4000/F11.md) | frame | 16 | 1048700.0 | 3.492171 | 505.0 | 73.0 | 0.0 | 69427.0 | 121372.0 | True | 1.661846957728205e-05 | True | provisional |
| [F21](F21_ieee_decode_legacy_control_sdk_retry_unique_object/F21.md) | PE | 1 | 1039.0 | 0.00345987 | 3.0 | 0.0 | 0.0 | 220.0 | 343.0 | True | unknown | True | pass |
| [F22](F22_continuous_ieee_T16_3ns/F22.md) | frame | 16 | 1048711.0 | 3.146133 | 502.0 | 73.0 | 0.0 | 69483.0 | 121696.0 | True | 1.661846957728205e-05 | True | provisional |
| [F12](F12_continuous_T8_online_3p33ns_split4000/F12.md) | frame | 8 | 528501.0 | 1.75990833 | 1007.0 | 73.0 | 0.0 | 97112.0 | 196314.0 | True | 1.661846957728205e-05 | True | infeasible |
| [F23](F23_continuous_ieee_T16_2p5ns/F23.md) | frame | 16 | 1048730.0 | 2.95951606 | 502.0 | 73.0 | 0.0 | 70449.0 | 125618.0 | True | 1.661846957728205e-05 | True | provisional |
| [F24](F24_affine_weight_loader_T16_2p5ns/F24.md) | frame | 16 | 1048723.0 | 2.830503377 | 502.0 | 73.0 | 0.0 | 69290.0 | 124577.0 | True | 1.661846957728205e-05 | True | provisional |
| [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) | frame | 16 | 1056904.0 | 2.64226 | 502.0 | 73.0 | 0.0 | 69976.0 | 125404.0 | True | 1.661846957728205e-05 | True | provisional |

## All Architectures

Frame records only, ordered by HLS-estimated latency. Microkernels and validation operations are excluded; infeasible/failed results remain visible.

| id | series | design | T_target | latency_ms_est | DSP | BRAM18K | LUT | FF | delta_psnr | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C11](C11_wino_conv2w8_continuous_T4_split4000/C11.md) | C | designs/winograd_mixed_packing_r2 | 4 | 1.081672 | 1036.0 | 146.0 | 248797.0 | 307525.0 | -0.07589037644656216 | infeasible |
| [F12](F12_continuous_T8_online_3p33ns_split4000/F12.md) | F | designs/continuous_direct_r2 | 8 | 1.75990833 | 1007.0 | 73.0 | 97112.0 | 196314.0 | -0.0695141811880653 | infeasible |
| [W16](W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | W | designs/winograd_continuous_r2 | 8 | 1.77345477 | 648.0 | 146.0 | 145767.0 | 192756.0 | -0.0695141811880653 | infeasible |
| [F15](F15_rotate_c3_T8_tree0_4ns/F15.md) | F | designs/continuous_rotate_v1 | 8 | 2.113924 | 1007.0 | 73.0 | 101994.0 | 86073.0 | -0.0695141811880653 | infeasible |
| [F14](F14_rotate_c3_T8_tree1_4ns/F14.md) | F | designs/continuous_rotate_v1 | 8 | 2.113952 | 1007.0 | 73.0 | 96488.0 | 171235.0 | -0.0695141811880653 | infeasible |
| [F10](F10_continuous_T8_online_4ns_split4000/F10.md) | F | designs/continuous_direct_r2 | 8 | 2.113952 | 1007.0 | 73.0 | 96764.0 | 171240.0 | -0.0695141811880653 | infeasible |
| [W17](W17_narrow_raw_banks_T8/W17.md) | W | designs/winograd_rawbank_v1 | 8 | 2.130248 | 648.0 | 146.0 | 93166.0 | 122399.0 | -0.0695141811880653 | infeasible |
| [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | W | designs/winograd_continuous_r2 | 8 | 2.130248 | 648.0 | 146.0 | 148013.0 | 182409.0 | -0.0695141811880653 | infeasible |
| [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) | C | designs/winograd_mixed_packing_r2 | 8 | 2.130248 | 520.0 | 146.0 | 150851.0 | 179452.0 | -0.07589037644656216 | infeasible |
| [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) | F | designs/continuous_nested_load_v1 | 16 | 2.64226 | 502.0 | 73.0 | 69976.0 | 125404.0 | -0.0695141811880653 | provisional |
| [F24](F24_affine_weight_loader_T16_2p5ns/F24.md) | F | designs/continuous_affine_load_v1 | 16 | 2.830503377 | 502.0 | 73.0 | 69290.0 | 124577.0 | -0.0695141811880653 | provisional |
| [F23](F23_continuous_ieee_T16_2p5ns/F23.md) | F | designs/continuous_ieee_v1 | 16 | 2.95951606 | 502.0 | 73.0 | 70449.0 | 125618.0 | -0.0695141811880653 | provisional |
| [F22](F22_continuous_ieee_T16_3ns/F22.md) | F | designs/continuous_ieee_v1 | 16 | 3.146133 | 502.0 | 73.0 | 69483.0 | 121696.0 | -0.0695141811880653 | provisional |
| [F11](F11_continuous_T16_online_3p33ns_split4000/F11.md) | F | designs/continuous_direct_r2 | 16 | 3.492171 | 505.0 | 73.0 | 69427.0 | 121372.0 | -0.0695141811880653 | provisional |
| [F08](F08_continuous_T16_oldpad_4ns_split4000/F08.md) | F | designs/continuous_direct_r2 | 16 | 4.194708 | 505.0 | 96.0 | 69362.0 | 106171.0 | -0.0695141811880653 | provisional |
| [F13](F13_rotate_c3_T16_tree1_4ns/F13.md) | F | designs/continuous_rotate_v1 | 16 | 4.194748 | 505.0 | 73.0 | 68903.0 | 106661.0 | -0.0695141811880653 | provisional |
| [F09](F09_continuous_T16_online_4ns_split4000/F09.md) | F | designs/continuous_direct_r2 | 16 | 4.194748 | 505.0 | 73.0 | 69179.0 | 106647.0 | -0.0695141811880653 | provisional |
| [W18](W18_narrow_raw_banks_T16/W18.md) | W | designs/winograd_rawbank_v1 | 16 | 4.2274 | 326.0 | 146.0 | 74480.0 | 87869.0 | -0.0695141811880653 | provisional |
| [W15](W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) | W | designs/winograd_continuous_r2 | 16 | 4.2274 | 326.0 | 146.0 | 89114.0 | 92946.0 | -0.0695141811880653 | infeasible |
| [P12](P12_exact10_packing_T4/P12.md) | P | designs/packing_network | 4 | 5.422328 | 1007.0 | 168.0 | 292053.0 | 159828.0 | -0.0695141811880653 | infeasible |
| [E043](E043_scan_clock_T16_E043/E043.md) | unknown | designs/dataflow_int | 16 | 6.93923049 | 505.0 | 168.0 | 55325.0 | 67025.0 | -0.0695141811880653 | provisional |
| [W10](W10_fixed_tiles_T16_c1only_4ns/W10.md) | W | designs/winograd_continuous | 16 | 7.548204 | 326.0 | 241.0 | 79158.0 | 76052.0 | -0.0695141811880653 | provisional |
| [P11](P11_exact10_packing_T8/P11.md) | P | designs/packing_network | 8 | 7.577208 | 505.0 | 168.0 | 165606.0 | 106599.0 | -0.0695141811880653 | infeasible |
| [C12](C12_continuous_wino_packing_T8_guard_retry/C12.md) | C | designs/combination_continuous_r1 | 8 | 7.577212 | 470.0 | 169.0 | 174591.0 | 161653.0 | -0.0695141811880653 | infeasible |
| [E042](E042_scan_clock_T16_E042/E042.md) | unknown | designs/dataflow_int | 16 | 8.058712 | 505.0 | 168.0 | 56007.0 | 62948.0 | -0.0695141811880653 | provisional |
| [F01](F01_fifo_lutram_control/F01.md) | F | designs/fifo_lutram_control | 16 | 8.058712 | 505.0 | 96.0 | 56081.0 | 62800.0 | -0.0695141811880653 | provisional |
| [F02](F02_uram_line_control/F02.md) | F | designs/uram_line_control | 16 | 8.058712 | 505.0 | 132.0 | 56007.0 | 62948.0 | -0.0695141811880653 | provisional |
| [C04](C04_wino_packing_T4_all_header_retry/C04.md) | C | designs/combination_network_r1 | 4 | 9.513772 | 936.0 | 241.0 | 293222.0 | 253809.0 | -0.0695141811880653 | infeasible |
| [C05](C05_wino_packing_T4_conv3_header_retry/C05.md) | C | designs/combination_network_r1 | 4 | 9.513772 | 1192.0 | 241.0 | 260882.0 | 263747.0 | -0.0695141811880653 | infeasible |
| [E041](E041_scan_clock_T16_E041/E041.md) | unknown | designs/dataflow_int | 16 | 9.7275 | 505.0 | 168.0 | 55553.0 | 59959.0 | -0.0695141811880653 | provisional |
| [E056](E056_mixed_T4_feasibility/E056.md) | unknown | designs/dataflow_mix | 4 | 10.46292 | 1160.0 | 168.0 | 237025.0 | 120073.0 | -0.0695141811880653 | infeasible |
| [P10](P10_exact10_packing_T16/P10.md) | P | designs/packing_network | 16 | 12.156332 | 254.0 | 168.0 | 101488.0 | 80563.0 | -0.0695141811880653 | infeasible |
| [E059](E059_integer_lutram_T8/E059.md) | unknown | designs/dataflow_int | 8 | 13.22968 | 1007.0 | 168.0 | 85147.0 | 88822.0 | -0.0695141811880653 | infeasible |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | W | designs/winograd_network_r1 | 8 | 13.974316 | 648.0 | 241.0 | 135496.0 | 148761.0 | -0.0695141811880653 | infeasible |
| [C06](C06_wino_packing_T8_all_header_retry/C06.md) | C | designs/combination_network_r1 | 8 | 13.974316 | 470.0 | 169.0 | 170165.0 | 153644.0 | -0.0695141811880653 | infeasible |
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
| [E046](E046_dataflow_wrap_T32/E046.md) | unknown | designs/dataflow_wrap | 32 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
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
| [F04](F04_continuous_T16_online_4ns/F04.md) | F | designs/continuous_direct | 16 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [W13](W13_fixed_tiles_T8_allcontinuous_3p33ns/W13.md) | W | designs/winograd_continuous | 8 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [C07](C07_continuous_wino_packing_T8/C07.md) | C | designs/combination_continuous | 8 | unknown | unknown | unknown | unknown | unknown | unknown | fail |
| [F05](F05_continuous_T8_online_4ns/F05.md) | F | designs/continuous_direct | 8 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [F06](F06_continuous_T16_online_3p33ns/F06.md) | F | designs/continuous_direct | 16 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |
| [F07](F07_continuous_T8_online_3p33ns/F07.md) | F | designs/continuous_direct | 8 | unknown | unknown | unknown | unknown | unknown | -0.0695141811880653 | fail |

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
| [F16](F16_ieee_decode_bit_exact/F16.md) | PE | 0.0 | unknown | unknown | 1045.0 | unknown | unknown | fail |
| [F17](F17_ieee_decode_legacy_control/F17.md) | PE | 3.0 | unknown | unknown | 1045.0 | unknown | unknown | fail |
| [F18](F18_ieee_decode_bit_exact_sdk_retry/F18.md) | PE | 0.0 | unknown | unknown | 1045.0 | unknown | unknown | fail |
| [F19](F19_ieee_decode_legacy_control_sdk_retry/F19.md) | PE | 3.0 | unknown | unknown | 1045.0 | unknown | unknown | fail |
| [C04](C04_wino_packing_T4_all_header_retry/C04.md) | frame | 935.0 | 936.0 | 0.10695187165774556 | 715360.0 | 2378443.0 | 232.48196712144934 | infeasible |
| [F04](F04_continuous_T16_online_4ns/F04.md) | frame | 505.0 | unknown | unknown | 1140400.0 | unknown | unknown | fail |
| [W13](W13_fixed_tiles_T8_allcontinuous_3p33ns/W13.md) | frame | 647.0 | unknown | unknown | 620200.0 | unknown | unknown | fail |
| [C07](C07_continuous_wino_packing_T8/C07.md) | frame | 469.0 | unknown | unknown | 2100000.0 | unknown | unknown | fail |
| [F13](F13_rotate_c3_T16_tree1_4ns/F13.md) | frame | 505.0 | 505.0 | 0.0 | 1140400.0 | 1048687.0 | -8.04217818309365 | provisional |
| [F05](F05_continuous_T8_online_4ns/F05.md) | frame | 1007.0 | unknown | unknown | 620200.0 | unknown | unknown | fail |
| [C12](C12_continuous_wino_packing_T8_guard_retry/C12.md) | frame | 469.0 | 470.0 | 0.2132196162046851 | 2100000.0 | 1894303.0 | -9.795095238095241 | infeasible |
| [F06](F06_continuous_T16_online_3p33ns/F06.md) | frame | 505.0 | unknown | unknown | 1140400.0 | unknown | unknown | fail |
| [F14](F14_rotate_c3_T8_tree1_4ns/F14.md) | frame | 1007.0 | 1007.0 | 0.0 | 620200.0 | 528488.0 | -14.787487907126728 | infeasible |
| [F07](F07_continuous_T8_online_3p33ns/F07.md) | frame | 1007.0 | unknown | unknown | 620200.0 | unknown | unknown | fail |
| [W17](W17_narrow_raw_banks_T8/W17.md) | frame | 648.0 | 648.0 | 0.0 | 620200.0 | 532562.0 | -14.13060303128023 | infeasible |
| [C05](C05_wino_packing_T4_conv3_header_retry/C05.md) | frame | 1191.0 | 1192.0 | 0.08396305625524292 | 715360.0 | 2378443.0 | 232.48196712144934 | infeasible |
| [P09](P09_reproduction_P01/P09.md) | PE | 1.0 | 1.0 | 0.0 | 61.0 | 61.0 | 0.0 | pass |
| [F09](F09_continuous_T16_online_4ns_split4000/F09.md) | frame | 505.0 | 505.0 | 0.0 | 1140400.0 | 1048687.0 | -8.04217818309365 | provisional |
| [C06](C06_wino_packing_T8_all_header_retry/C06.md) | frame | 469.0 | 470.0 | 0.2132196162046851 | 977504.0 | 3493579.0 | 257.39792369136086 | infeasible |
| [F15](F15_rotate_c3_T8_tree0_4ns/F15.md) | frame | 1007.0 | 1007.0 | 0.0 | 620200.0 | 528481.0 | -14.788616575298285 | infeasible |
| [W18](W18_narrow_raw_banks_T16/W18.md) | frame | 326.0 | 326.0 | 0.0 | 1140400.0 | 1056850.0 | -7.3263767099263415 | provisional |
| [F10](F10_continuous_T8_online_4ns_split4000/F10.md) | frame | 1007.0 | 1007.0 | 0.0 | 620200.0 | 528488.0 | -14.787487907126728 | infeasible |
| [F20](F20_ieee_decode_bit_exact_sdk_retry_unique_object/F20.md) | PE | 0.0 | 0.0 | unknown | 1045.0 | 1027.0 | -1.7224880382775143 | pass |
| [F11](F11_continuous_T16_online_3p33ns_split4000/F11.md) | frame | 505.0 | 505.0 | 0.0 | 1140400.0 | 1048700.0 | -8.041038232199227 | provisional |
| [F21](F21_ieee_decode_legacy_control_sdk_retry_unique_object/F21.md) | PE | 3.0 | 3.0 | 0.0 | 1045.0 | 1039.0 | -0.5741626794258381 | pass |
| [F22](F22_continuous_ieee_T16_3ns/F22.md) | frame | 502.0 | 502.0 | 0.0 | 1140400.0 | 1048711.0 | -8.040073658365488 | provisional |
| [F12](F12_continuous_T8_online_3p33ns_split4000/F12.md) | frame | 1007.0 | 1007.0 | 0.0 | 620200.0 | 528501.0 | -14.78539180909384 | infeasible |
| [F23](F23_continuous_ieee_T16_2p5ns/F23.md) | frame | 502.0 | 502.0 | 0.0 | 1140400.0 | 1048730.0 | -8.03840757628902 | provisional |
| [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | frame | 647.0 | 648.0 | 0.15455950540959051 | 620200.0 | 532562.0 | -14.13060303128023 | infeasible |
| [W15](W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) | frame | 325.0 | 326.0 | 0.3076923076922977 | 1140400.0 | 1056850.0 | -7.3263767099263415 | infeasible |
| [W16](W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | frame | 647.0 | 648.0 | 0.15455950540959051 | 620200.0 | 532569.0 | -14.129474363108674 | infeasible |
| [F24](F24_affine_weight_loader_T16_2p5ns/F24.md) | frame | 502.0 | 502.0 | 0.0 | 1068730.0 | 1048723.0 | -1.8720350322345203 | provisional |
| [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) | frame | 519.0 | 520.0 | 0.19267822736031004 | 620200.0 | 532562.0 | -14.13060303128023 | infeasible |
| [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) | frame | 502.0 | 502.0 | 0.0 | 1068723.0 | 1056904.0 | -1.1058992835374593 | provisional |
| [C11](C11_wino_conv2w8_continuous_T4_split4000/C11.md) | frame | 1035.0 | 1036.0 | 0.09661835748793202 | 360100.0 | 270418.0 | -24.904748680921962 | infeasible |

Largest percentage deviations (a zero paper denominator has no percentage):

| id | metric | estimate | actual | deviation_pct | status |
| --- | --- | --- | --- | --- | --- |
| [W08](W08_winograd_network_T16_header_retry/W08.md) | latency_cycles | 1431256.0 | 5723851.0 | 299.9180440116932 | provisional |
| [W07](W07_winograd_conv1_T16_header_retry/W07.md) | latency_cycles | 1431256.0 | 5721420.0 | 299.7481931953473 | provisional |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | latency_cycles | 906968.0 | 3493579.0 | 285.1931931446313 | infeasible |
| [C06](C06_wino_packing_T8_all_header_retry/C06.md) | latency_cycles | 977504.0 | 3493579.0 | 257.39792369136086 | infeasible |
| [C04](C04_wino_packing_T4_all_header_retry/C04.md) | latency_cycles | 715360.0 | 2378443.0 | 232.48196712144934 | infeasible |
| [C05](C05_wino_packing_T4_conv3_header_retry/C05.md) | latency_cycles | 715360.0 | 2378443.0 | 232.48196712144934 | infeasible |
| [S01](S01_ddr_global_probe/S01.md) | latency_cycles | 6250529.0 | 16730473.0 | 167.6649128417771 | invalid_config |
| [C11](C11_wino_conv2w8_continuous_T4_split4000/C11.md) | LUT | 100100.0 | 248797.0 | 148.54845154845157 | infeasible |
| [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) | LUT | 65100.0 | 150851.0 | 131.7219662058372 | infeasible |
| [W09](W09_winograd_network_T8_header_retry/W09.md) | LUT | 59000.0 | 135496.0 | 129.65423728813562 | infeasible |
| [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | LUT | 72100.0 | 148013.0 | 105.28848821081831 | infeasible |
| [W16](W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | LUT | 72100.0 | 145767.0 | 102.1733703190014 | infeasible |

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
| [C04](C04_wino_packing_T4_all_header_retry/C04.md) | 3 | infeasible |
| [F13](F13_rotate_c3_T16_tree1_4ns/F13.md) | 5 | provisional |
| [C12](C12_continuous_wino_packing_T8_guard_retry/C12.md) | 4 | infeasible |
| [F14](F14_rotate_c3_T8_tree1_4ns/F14.md) | 5 | infeasible |
| [W17](W17_narrow_raw_banks_T8/W17.md) | 5 | infeasible |
| [C05](C05_wino_packing_T4_conv3_header_retry/C05.md) | 3 | infeasible |
| [F09](F09_continuous_T16_online_4ns_split4000/F09.md) | 5 | provisional |
| [C06](C06_wino_packing_T8_all_header_retry/C06.md) | 3 | infeasible |
| [F15](F15_rotate_c3_T8_tree0_4ns/F15.md) | 5 | infeasible |
| [W18](W18_narrow_raw_banks_T16/W18.md) | 5 | provisional |
| [F10](F10_continuous_T8_online_4ns_split4000/F10.md) | 5 | infeasible |
| [F11](F11_continuous_T16_online_3p33ns_split4000/F11.md) | 5 | provisional |
| [F22](F22_continuous_ieee_T16_3ns/F22.md) | 5 | provisional |
| [F12](F12_continuous_T8_online_3p33ns_split4000/F12.md) | 5 | infeasible |
| [F23](F23_continuous_ieee_T16_2p5ns/F23.md) | 5 | provisional |
| [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | 5 | infeasible |
| [W15](W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) | 5 | infeasible |
| [W16](W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | 5 | infeasible |
| [F24](F24_affine_weight_loader_T16_2p5ns/F24.md) | 5 | provisional |
| [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) | 5 | infeasible |
| [F25](F25_nested_weight_loader_T16_2p5ns/F25.md) | 5 | provisional |
| [C11](C11_wino_conv2w8_continuous_T4_split4000/C11.md) | 5 | infeasible |

Selected candidates were ranked globally across both phases before validation. Mandatory full-supplied-image C simulation:

| id | design | image_count | csim_pass | bit_exact | set14_psnr | delta_psnr | border_mse | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Routed timing closes for 0 selected implementation runs; 0 selected two-frame RTL runs pass. Completion of a route with negative WNS is retained as a timing failure.

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
| [F16](F16_ieee_decode_bit_exact/F16.md) | F | fail | /home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/F16/source/ieee_decode.h:18:5: error: no template named 'fp_struct' in namespace 'hls'; did you mean simply 'fp_struct'?; /home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/F16/source/ieee_decode.h:12:46: error: conditional expression is ambiguous; 'ap_int<12 aka 12>' can be converted to 'ap_int<10 + 1 aka 11>' and vice versa | PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible |
| [F17](F17_ieee_decode_legacy_control/F17.md) | F | fail | /home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/F17/source/ieee_decode.h:18:5: error: no template named 'fp_struct' in namespace 'hls'; did you mean simply 'fp_struct'?; ERROR: [SIM 211-100] 'csim_design' failed: compilation error(s). | PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible |
| [F18](F18_ieee_decode_bit_exact_sdk_retry/F18.md) | F | fail | ld.lld: error: duplicate symbol: ieee_decode_pe(ap_int<10> const*, float*); clang++: error: linker command failed with exit code 1 (use -v to see invocation) | PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible |
| [F19](F19_ieee_decode_legacy_control_sdk_retry/F19.md) | F | fail | ld.lld: error: duplicate symbol: ieee_decode_pe(ap_int<10> const*, float*); clang++: error: linker command failed with exit code 1 (use -v to see invocation) | PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible |
| [C04](C04_wino_packing_T4_all_header_retry/C04.md) | C | infeasible | LUT=293222.0 exceeds 81984; FF=253809.0 exceeds 163968 | unknown |
| [F04](F04_continuous_T16_online_4ns/F04.md) | F | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (F04/source/srcnn.cpp:312:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [W13](W13_fixed_tiles_T8_allcontinuous_3p33ns/W13.md) | W | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (W13/source/srcnn.cpp:488:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [C07](C07_continuous_wino_packing_T8/C07.md) | C | fail | ../../../source/srcnn.cpp:332:2: error: #else without #if; ../../../source/srcnn.cpp:333:13: error: redefinition of 'conv2_stream' | ; C simulation not accepted (exit=1); synthesis not eligible |
| [F05](F05_continuous_T8_online_4ns/F05.md) | F | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (F05/source/srcnn.cpp:312:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [C12](C12_continuous_wino_packing_T8_guard_retry/C12.md) | C | infeasible | LUT=174591.0 exceeds 81984 | unknown |
| [F06](F06_continuous_T16_online_3p33ns/F06.md) | F | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (F06/source/srcnn.cpp:312:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [F14](F14_rotate_c3_T8_tree1_4ns/F14.md) | F | infeasible | LUT=96488.0 exceeds 81984; FF=171235.0 exceeds 163968 | unknown |
| [F07](F07_continuous_T8_online_3p33ns/F07.md) | F | fail | ERROR: [HLS 214-256] in function 'conv3_stream(hls::stream<numeric::pixel2, 0>&, hls::stream<ap_int<10>, 0>&, ap_int<10> (*) [25], ap_int<10>*)': Unsupported aggregate pragma/directive on variable 'windows' as the bit-width after aggregation (8000) is larger than 4096 (F07/source/srcnn.cpp:312:26); ERROR: [HLS 200-1715] Encountered problem during source synthesis | ; Synthesis failed (exit=1) |
| [W17](W17_narrow_raw_banks_T8/W17.md) | W | infeasible | LUT=93166.0 exceeds 81984 | unknown |
| [C05](C05_wino_packing_T4_conv3_header_retry/C05.md) | C | infeasible | LUT=260882.0 exceeds 81984; FF=263747.0 exceeds 163968 | unknown |
| [C06](C06_wino_packing_T8_all_header_retry/C06.md) | C | infeasible | LUT=170165.0 exceeds 81984 | unknown |
| [F15](F15_rotate_c3_T8_tree0_4ns/F15.md) | F | infeasible | LUT=101994.0 exceeds 81984 | unknown |
| [F10](F10_continuous_T8_online_4ns_split4000/F10.md) | F | infeasible | LUT=96764.0 exceeds 81984; FF=171240.0 exceeds 163968 | unknown |
| [F12](F12_continuous_T8_online_3p33ns_split4000/F12.md) | F | infeasible | LUT=97112.0 exceeds 81984; FF=196314.0 exceeds 163968 | unknown |
| [W14](W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | W | infeasible | LUT=148013.0 exceeds 81984; FF=182409.0 exceeds 163968 | unknown |
| [W15](W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) | W | infeasible | LUT=89114.0 exceeds 81984 | unknown |
| [W16](W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | W | infeasible | LUT=145767.0 exceeds 81984; FF=192756.0 exceeds 163968 | unknown |
| [C10](C10_wino_conv2w8_continuous_T8_split4000/C10.md) | C | infeasible | LUT=150851.0 exceeds 81984; FF=179452.0 exceeds 163968 | unknown |
| [C11](C11_wino_conv2w8_continuous_T4_split4000/C11.md) | C | infeasible | LUT=248797.0 exceeds 81984; FF=307525.0 exceeds 163968 | unknown |

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

Generated from archived evidence at 2026-10-11T03:25:51+00:00.
