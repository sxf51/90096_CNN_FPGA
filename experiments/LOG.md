# Overnight experiment log

## Events

- 2026-10-11: Started on branch `exp/overnight-1011` at source baseline `1f025dc`. Existing edits to `.gitignore`, both READMEs and untracked report documentation are user work and will not be committed by this task.
- Protected all 46 files under `src/` and `test/` using SHA256, including original source, six parameter files and all golden data. Never run `script.py`.
- Existing `tb_conv1` and `tb_srcnn` print MSE and always return zero; there is no existing numerical threshold. `test/csim.cpp` does not propagate return values. Set14 is disabled by a commented `tb_set14()` call; a new entry point under `exp/tb/` will enable evaluation without touching `test/`.
- External signature is eight float-array parameters: input `[1][255][255]`, weights `[64][1][9][9]`, bias `[64]`, weights `[32][64][1][1]`, bias `[32]`, weights `[1][32][5][5]`, bias `[1]`, output `[1][255][255]`. Parameters are little-endian float32 binary, output/input-channel/kernel-row/kernel-column order. There are 8,032 weights and 97 biases. Input bytes are divided by 255 as float32.
- `.gitignore` admits `hls_config.cfg`, synthesis/simulation/implementation report XML/RPT, `*_csim.log`, and selected HLS run logs throughout `workspace/exp_runs/`. Generated HDL, cache, executables and ordinary logs stay ignored. No changes to existing ignore rules are required. Archived log excerpts will additionally use a tracked `.txt` companion because `experiments/**/csim.log` is ignored.
- Mac has 8 cores and 16 GiB; verified remote Linux host has 12 logical cores, 15 GiB total RAM and about 13.5 GiB available. Choose one synthesis job (8 GiB budget per job); run precision analysis independently. Remote Vitis installation is `/home/lipuze/amdfpga/2026.1/Vitis`.

- 2026-10-10T16:33:08+00:00: E000: golden_baseline; status=infeasible; latency_ms_est=19601.13853; 

- 2026-10-10T16:35:51+00:00: E010: completed range analysis and 16-point scan on all 13 supplied pairs

- 2026-10-10T16:39:35+00:00: E020: auto_default_10ns; status=infeasible; latency_ms_est=19601.13853; 

- 2026-10-10T16:42:23+00:00: E021: auto_default_4ns; status=infeasible; latency_ms_est=17179.087404; 

- 2026-10-10T16:43:53+00:00: E011: apfixed_w16a16; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T16:45:12+00:00: E022: auto_pipeline_off; status=infeasible; latency_ms_est=44822.23011; 

- 2026-10-10T16:45:16+00:00: E011 archive correction: removed copied numpy input reference; compile failed before producing any model output. Output archival now selects csim/build only.

- 2026-10-10T16:46:17+00:00: E023: auto_inner_pipeline; status=infeasible; latency_ms_est=19601.13853; ; requested II missed

- 2026-10-10T16:47:23+00:00: E024: auto_pixel_pipeline; status=infeasible; latency_ms_est=19601.13853; ; requested II missed

- 2026-10-10T16:48:39+00:00: E025: auto_partition; status=infeasible; latency_ms_est=19601.13853; ; requested II missed

- 2026-10-10T16:49:28+00:00: E030: dataflow_float; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T16:49:45+00:00: E026: auto_unsafe_math; status=infeasible; latency_ms_est=19601.13671; 

- 2026-10-10T16:52:16+00:00: E023/E024/E025 invalidated: unsupported syn.directive silently ignored by Vitis. Added schema-based directive emission, unknown-option rejection and E028/E029/E032 retries.

- 2026-10-10T16:53:25+00:00: E028: auto_inner_pipeline_validcfg; status=infeasible; latency_ms_est=12170.258489978001; 

- 2026-10-10T16:58:49+00:00: E029: auto_pixel_pipeline_validcfg; status=infeasible; latency_ms_est=3811.21723; ; requested II missed

- 2026-10-10T16:59:58+00:00: E032: auto_partition_validcfg; status=infeasible; latency_ms_est=12170.258489978001; 

- 2026-10-10T17:00:13+00:00: E017: apfixed_boundary_w10a10; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T17:02:17+00:00: E027: auto_fixed16; status=infeasible; latency_ms_est=3912.56088; 

- 2026-10-10T17:27:57+00:00: E034: scan_T_T16_E034; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T17:28:10+00:00: E035: scan_T_T8_E035; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T17:28:35+00:00: E018: apfixed_w16a16_single; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T17:30:21+00:00: E014: apfixed_w16a16; status=timeout; latency_ms_est=unknown; ; C simulation not accepted (exit=124); synthesis not eligible

- 2026-10-10T17:30:45+00:00: E012: apfixed_w10a10; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T17:34:46+00:00: E015: apfixed_w16a16_single_retry; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T17:34:49+00:00: E013: apfixed_w8a8; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T17:35:35+00:00: E019: apfixed_w10a10_retry; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T17:39:33+00:00: E016: apfixed_w8a8_retry; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T17:40:11+00:00: E033: dataflow_fixed_T32_single; status=infeasible; latency_ms_est=123.540036662; 

- 2026-10-10T18:00:43+00:00: E044: scan_T_T16_E034_retry; status=infeasible; latency_ms_est=175.462633706; 

- 2026-10-10T18:18:21+00:00: E047: dataflow_dsp_T32; status=infeasible; latency_ms_est=29.13855; 

- 2026-10-10T18:36:37+00:00: E031: dataflow_fixed_T32; status=infeasible; latency_ms_est=123.540036662; 

- 2026-10-10T18:37:59+00:00: E049: integer_boundary_exhaustive; status=csim_pass; latency_ms_est=unknown; primitive validation only; no network latency or PSNR claimed

- 2026-10-10T18:40:27+00:00: E046: dataflow_wrap_T32; status=fail; latency_ms_est=unknown; ; Run lock exists: /home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/.synthesis.lock; inspect its PID before recovery

- 2026-10-10T18:42:02+00:00: E062: completed layer-specific INT8 eligibility study on 13 supplied pairs

- 2026-10-10T18:55:10+00:00: E065: apfixed_mixed_conv2w8; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T18:58:25+00:00: E066: full_apfixed_mixed_butterfly; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T19:01:02+00:00: E045: scan_T_T8_E035_retry; status=infeasible; latency_ms_est=280.01056732; 

- 2026-10-10T19:18:04+00:00: E063: dataflow_wrap_T32_retry; status=infeasible; latency_ms_est=29.13855; 

- 2026-10-10T19:35:05+00:00: E048: dataflow_integer_T32; status=infeasible; latency_ms_est=29.13855; 

- 2026-10-10T19:37:05+00:00: E039: scan_storage_T32_E039; status=provisional; latency_ms_est=29.83024; 

- 2026-10-10T19:39:05+00:00: E057: integer_lutram_T32; status=provisional; latency_ms_est=29.83024; 

- 2026-10-10T19:45:53+00:00: E071: archived exact coefficient ranges and phase-two paper budgets; no synthesis claim

- 2026-10-10T20:05:22+00:00: E070: first_feasible_implementation; status=impl_complete; latency_ms_est=29.83024; impl of E039; HLS estimates inherited, real measurements in data.csv

- 2026-10-10T20:05:25+00:00: E070: reparsed archived final verification reports; synthesis reports excluded; {"impl_DSP": 270.0, "impl_resource_report": "hls/impl/verilog/report/srcnn_utilization_routed.rpt", "impl_WNS_ns": -1.277, "impl_TNS_ns": -1206.071, "impl_timing_report": "hls/impl/verilog/report/srcnn_timing_routed.rpt", "impl_LUT": 20454.0, "impl_FF": 33844.0, "impl_BRAM36": 31.0, "impl_URAM": 0.0, "timing_met": false, "impl_clock_ns_est": 11.277}

- 2026-10-10T20:07:09+00:00: E070: reparsed archived final verification reports; synthesis reports excluded; {"impl_DSP": 270.0, "impl_resource_report": "hls/impl/verilog/report/srcnn_utilization_routed.rpt", "impl_WNS_ns": -1.277, "impl_TNS_ns": -1206.071, "impl_timing_report": "hls/impl/verilog/report/srcnn_timing_routed.rpt", "impl_LUT": 20454.0, "impl_FF": 33844.0, "impl_BRAM36": 31.0, "impl_URAM": 0.0, "timing_met": false, "impl_clock_ns_est": 11.277}

- 2026-10-10T20:07:36+00:00: E040: scan_storage_T32_E040; status=infeasible; latency_ms_est=29.83024; 

- 2026-10-10T20:10:12+00:00: E058: integer_lutram_T16; status=provisional; latency_ms_est=18.7632; 

- 2026-10-10T20:14:49+00:00: E059: integer_lutram_T8; status=infeasible; latency_ms_est=13.22968; 

- 2026-10-10T20:25:36+00:00: E036: scan_split_T16_E036; status=provisional; latency_ms_est=78.94023; ; requested II missed

- 2026-10-10T20:28:38+00:00: E037: scan_split_T16_E037; status=provisional; latency_ms_est=18.7632; 

- 2026-10-10T20:31:48+00:00: E038: scan_split_T16_E038; status=provisional; latency_ms_est=21.55352; 

- 2026-10-10T20:50:03+00:00: E064: storage_0_T16; status=infeasible; latency_ms_est=18.07151; 

- 2026-10-10T20:53:02+00:00: E067: storage_2_T16; status=infeasible; latency_ms_est=18.7632; 

- 2026-10-10T20:56:17+00:00: E041: scan_clock_T16_E041; status=provisional; latency_ms_est=9.7275; 

- 2026-10-10T20:59:16+00:00: E042: scan_clock_T16_E042; status=provisional; latency_ms_est=8.058712; 

- 2026-10-10T21:02:15+00:00: E043: scan_clock_T16_E043; status=provisional; latency_ms_est=6.93923049; 

- 2026-10-10T21:04:03+00:00: E060: scatter_integer_T32; status=provisional; latency_ms_est=37.70206; 

- 2026-10-10T21:04:51+00:00: E051: mul16_default; status=pass; latency_ms_est=0.00066; microbenchmark only; exclude latency from network Pareto; constants are explicit representative integers

- 2026-10-10T21:05:40+00:00: E052: mul16_constant_unroll; status=report_incomplete; latency_ms_est=unknown; microbenchmark only; exclude latency from network Pareto; constants are explicit representative integers

- 2026-10-10T21:06:25+00:00: E053: mul8_fabric; status=pass; latency_ms_est=0.00066; microbenchmark only; exclude latency from network Pareto; constants are explicit representative integers

- 2026-10-10T21:07:11+00:00: E054: mul16_default_4ns; status=pass; latency_ms_est=0.000264; microbenchmark only; exclude latency from network Pareto; constants are explicit representative integers

- 2026-10-10T21:07:56+00:00: E055: mul8_add_control; status=pass; latency_ms_est=0.00066; microbenchmark only; exclude latency from network Pareto; constants are explicit representative integers

- 2026-10-10T21:12:32+00:00: E052: corrected zero-cycle combinational report classification from archived XML; no rerun or resource-limit change

- 2026-10-10T21:27:31+00:00: E050: scatter_T32; status=infeasible; latency_ms_est=38.82221; 

- 2026-10-10T21:41:10+00:00: E056: mixed_T4_feasibility; status=infeasible; latency_ms_est=10.46292; 

- 2026-10-10T21:43:03+00:00: E069: final_candidate_all_supplied; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-10T21:43:06+00:00: E099: first-phase execution and final checksum audit complete; second-phase branch creation is next

- 2026-10-10T21:46:53+00:00: S00: architecture branch initialized from completed first phase; result schema gains series; 45 first-phase source files frozen by SHA256; no prior design modified

- 2026-10-10T21:53:48+00:00: P01: signed8_pair; status=pass; latency_ms_est=0.000244; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:54:37+00:00: P02: signed8_direct_control; status=pass; latency_ms_est=0.000232; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:55:11+00:00: W01: integer_f2_10bit; status=pass; latency_ms_est=0.000144; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:55:43+00:00: P03: signed8_group7; status=pass; latency_ms_est=0.000248; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:56:18+00:00: W02: direct_f2_control; status=pass; latency_ms_est=0.000152; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:56:50+00:00: P04: signed8_auto_mapping; status=pass; latency_ms_est=0.000244; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:57:25+00:00: W03: integer_f2_16bit; status=pass; latency_ms_est=0.000148; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:57:57+00:00: P05: signed8_builtin_preadder; status=pass; latency_ms_est=0.000252; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:58:45+00:00: P06: nonnegative10_group2; status=pass; latency_ms_est=0.000248; PE only; kernel latency is excluded from network rankings

- 2026-10-10T21:59:32+00:00: P07: exact10_residual_pair; status=pass; latency_ms_est=0.000248; PE only; kernel latency is excluded from network rankings

- 2026-10-10T22:02:24+00:00: G01: gather_control; status=provisional; latency_ms_est=29.83024; 

- 2026-10-10T22:04:11+00:00: G02: scatter_pad_control; status=provisional; latency_ms_est=37.70206; 

- 2026-10-10T22:06:17+00:00: S01: ddr_global_probe; status=invalid_config; latency_ms_est=unknown; ; Required external DDR AXI bundles not generated: scratch1, scratch2

- 2026-10-10T22:07:39+00:00: G03: scatter_edge_kernels; status=provisional; latency_ms_est=44.13926; 

- 2026-10-10T22:09:50+00:00: S02: whole_dataflow_control; status=provisional; latency_ms_est=29.83024; 

- 2026-10-10T22:13:31+00:00: P10: exact10_packing_T16; status=infeasible; latency_ms_est=12.156332; 

- 2026-10-10T22:14:22+00:00: C01: wino_packing_T4_all; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T22:14:36+00:00: C02: wino_packing_T4_conv3; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T22:14:51+00:00: C03: wino_packing_T8_all; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T22:18:01+00:00: S03: tile_fusion_B8; status=infeasible; latency_ms_est=228.03545; 

- 2026-10-10T22:18:05+00:00: C01-C03: compile failure from F2/F3 dimension macro collision with AMD ap_fixed identifiers. W04-W06 share the same header; retain their attempted runs. W07-W09/C04-C06 use independent source copies with SDK headers included first; no protected test/source changed.

- 2026-10-10T22:25:04+00:00: P11: exact10_packing_T8; status=infeasible; latency_ms_est=7.577208; 

- 2026-10-10T22:29:16+00:00: S04: tile_fusion_B16; status=infeasible; latency_ms_est=167.53977; 

- 2026-10-10T22:31:02+00:00: W07: winograd_conv1_T16_header_retry; status=provisional; latency_ms_est=22.88568; 

- 2026-10-10T22:31:05+00:00: S01: filled archived report measurements without changing experiment validity

- 2026-10-10T22:35:16+00:00: S05: tile_fusion_B32; status=infeasible; latency_ms_est=141.66377; 

- 2026-10-10T22:52:31+00:00: P12: exact10_packing_T4; status=infeasible; latency_ms_est=5.422328; 

- 2026-10-10T22:52:45+00:00: W04: winograd_conv1_T16; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T22:53:01+00:00: W05: winograd_network_T16; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T22:53:16+00:00: W06: winograd_network_T8; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T22:56:47+00:00: S06: tile_fusion_B64; status=infeasible; latency_ms_est=129.81873; 

- 2026-10-10T22:59:22+00:00: F01: fifo_lutram_control; status=provisional; latency_ms_est=8.058712; 

- 2026-10-10T23:03:00+00:00: W10: fixed_tiles_T16_c1only_4ns; status=provisional; latency_ms_est=7.548204; 

- 2026-10-10T23:05:36+00:00: F02: uram_line_control; status=provisional; latency_ms_est=8.058712; 

- 2026-10-10T23:06:43+00:00: W11: fixed_tiles_T8_allcontinuous_4ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:07:49+00:00: C08: wino_conv2w8_continuous_T8; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:08:45+00:00: W12: fixed_tiles_T16_allcontinuous_4ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:13:11+00:00: P08: builtin_mapping_implementation; status=impl_complete; latency_ms_est=0.000252; impl of P05; HLS estimates inherited, real measurements in data.csv

- 2026-10-10T23:14:05+00:00: P08: routed primitive inspection; {"completed": true, "DSP48E2_cells": 1, "pre_adder_used": true, "error": null}

- 2026-10-10T23:14:12+00:00: F03: continuous_T16_oldpad_4ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:17:23+00:00: W08: winograd_network_T16_header_retry; status=provisional; latency_ms_est=22.895404; 

- 2026-10-10T23:18:50+00:00: C09: wino_conv2w8_continuous_T4; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:19:34+00:00: F08: resumed queued architecture exploration; P08 primitive inspection is complete (one DSP48E2, AMULTSEL=AD, ADREG=1). Archived failures now include concrete compiler diagnostics and unchanged resource-cap violations. DATAFLOW scheduling warnings are derived into dataflow_warnings.csv and experiment interpretations; final two-frame RTL runs remain mandatory.

- 2026-10-10T23:19:34+00:00: F08-F12/W14-W16/C10-C11: independent retries split the Conv3 window into two4000-bit streams after W11 measured HLS214-256,8000 bits exceeding4096. Both sides carry65025 packets per frame; quantization points, weights and arithmetic remain identical. Original F03-F07/W11-W13/C08-C09 failures stay archived. The corrected queue is waiting for the serialized hardware slot.

- 2026-10-10T23:24:30+00:00: W09: winograd_network_T8_header_retry; status=infeasible; latency_ms_est=13.974316; 

- 2026-10-10T23:31:29+00:00: F08: continuous_T16_oldpad_4ns_split4000; status=provisional; latency_ms_est=4.194708; 

- 2026-10-10T23:38:28+00:00: F13-F15: paper plans committed before independent continuous_rotate_v1 generation. F08 engine3 reports7013 mux LUT/13268 totalLUT; rotate25x32 held channels to expose fixed input taps, compare T16/T8 with registered reductions and T8 latency0 fabric reductions. F13's two-frame simulation is bit-exact. Both T8 resource feasibility and latency0 clock behavior are unproven; final selection waits for all three measured records.

- 2026-10-10T23:46:08+00:00: F16: ieee_decode_bit_exact; status=fail; latency_ms_est=unknown; PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T23:46:24+00:00: F17: ieee_decode_legacy_control; status=fail; latency_ms_est=unknown; PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T23:47:53+00:00: F18: ieee_decode_bit_exact_sdk_retry; status=fail; latency_ms_est=unknown; PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T23:48:09+00:00: F19: ieee_decode_legacy_control_sdk_retry; status=fail; latency_ms_est=unknown; PE only; conversion-probe cycles are excluded from network rankings; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T23:48:44+00:00: C04: wino_packing_T4_all_header_retry; status=infeasible; latency_ms_est=9.513772; 

- 2026-10-10T23:49:43+00:00: F04: continuous_T16_online_4ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:50:51+00:00: W13: fixed_tiles_T8_allcontinuous_3p33ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-10T23:51:12+00:00: C07: continuous_wino_packing_T8; status=fail; latency_ms_est=unknown; ; C simulation not accepted (exit=1); synthesis not eligible

- 2026-10-10T23:58:05+00:00: F13: rotate_c3_T16_tree1_4ns; status=provisional; latency_ms_est=4.194748; 

- 2026-10-10T23:59:30+00:00: F05: continuous_T8_online_4ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-11T00:06:41+00:00: C12: continuous_wino_packing_T8_guard_retry; status=infeasible; latency_ms_est=7.577212; 

- 2026-10-11T00:07:39+00:00: F06: continuous_T16_online_3p33ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-11T00:19:06+00:00: F14: rotate_c3_T8_tree1_4ns; status=infeasible; latency_ms_est=2.113952; 

- 2026-10-11T00:20:31+00:00: F07: continuous_T8_online_3p33ns; status=fail; latency_ms_est=unknown; ; Synthesis failed (exit=1)

- 2026-10-11T00:29:18+00:00: W17: narrow_raw_banks_T8; status=infeasible; latency_ms_est=2.130248; 

- 2026-10-11T00:44:52+00:00: C05: wino_packing_T4_conv3_header_retry; status=infeasible; latency_ms_est=9.513772; 

- 2026-10-11T00:45:34+00:00: P09: reproduction_P01; status=pass; latency_ms_est=0.000244; PE only; kernel latency is excluded from network rankings

- 2026-10-11T00:52:34+00:00: F09: continuous_T16_online_4ns_split4000; status=provisional; latency_ms_est=4.194748; 

- 2026-10-11T00:59:11+00:00: C06: wino_packing_T8_all_header_retry; status=infeasible; latency_ms_est=13.974316; 

- 2026-10-11T01:10:17+00:00: F15: rotate_c3_T8_tree0_4ns; status=infeasible; latency_ms_est=2.113924; 

- 2026-10-11T01:17:05+00:00: W18: narrow_raw_banks_T16; status=provisional; latency_ms_est=4.2274; 

- 2026-10-11T01:28:36+00:00: F10: continuous_T8_online_4ns_split4000; status=infeasible; latency_ms_est=2.113952; 

- 2026-10-11T01:29:07+00:00: F20: ieee_decode_bit_exact_sdk_retry_unique_object; status=pass; latency_ms_est=0.00341991; PE only; conversion-probe cycles are excluded from network rankings

- 2026-10-11T01:36:09+00:00: F11: continuous_T16_online_3p33ns_split4000; status=provisional; latency_ms_est=3.492171; 

- 2026-10-11T01:36:43+00:00: F21: ieee_decode_legacy_control_sdk_retry_unique_object; status=pass; latency_ms_est=0.00345987; PE only; conversion-probe cycles are excluded from network rankings

- 2026-10-11T01:43:46+00:00: F22: continuous_ieee_T16_3ns; status=provisional; latency_ms_est=3.146133; 

- 2026-10-11T01:55:16+00:00: F12: continuous_T8_online_3p33ns_split4000; status=infeasible; latency_ms_est=1.75990833; 

- 2026-10-11T02:02:19+00:00: F23: continuous_ieee_T16_2p5ns; status=provisional; latency_ms_est=2.95951606; 

- 2026-10-11T02:13:35+00:00: W14: fixed_tiles_T8_allcontinuous_4ns_split4000; status=infeasible; latency_ms_est=2.130248; 

- 2026-10-11T02:21:21+00:00: W15: fixed_tiles_T16_allcontinuous_4ns_split4000; status=infeasible; latency_ms_est=4.2274; 

- 2026-10-11T02:33:01+00:00: W16: fixed_tiles_T8_allcontinuous_3p33ns_split4000; status=infeasible; latency_ms_est=1.77345477; 

- 2026-10-11T02:40:06+00:00: F24: affine_weight_loader_T16_2p5ns; status=provisional; latency_ms_est=2.830503377; 

- 2026-10-11T02:51:50+00:00: C10: wino_conv2w8_continuous_T8_split4000; status=infeasible; latency_ms_est=2.130248; 

- 2026-10-11T02:58:54+00:00: F25: nested_weight_loader_T16_2p5ns; status=provisional; latency_ms_est=2.64226; 

- 2026-10-11T03:03:01+00:00: F25: archived existing routed/RTL source reports at Git-visible neutral report paths for E070, P08; original ignore rules, sources and measurements unchanged.

- 2026-10-11T03:11:05+00:00: F25: refreshed architecture index and CSV-derived figures; separated frame/layer and PE estimate panels, grouped identical labeled points and increased label separation. Audited all 75 completed frozen plans, metric records and archived sources without mismatch.

- 2026-10-11T03:24:56+00:00: C11: wino_conv2w8_continuous_T4_split4000; status=infeasible; latency_ms_est=1.081672; 

- 2026-10-11T03:27:54+00:00: F80: final_all_supplied_F25; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-11T03:32:52+00:00: F81: final_impl_F25; status=fail; latency_ms_est=2.64226; impl of F25; HLS estimates inherited, real measurements in data.csv; impl failed (exit=1)

- 2026-10-11T03:41:38+00:00: F89: preplanned F89/F90/F91 serial Vivado retries of F25/F24/F23 after confirmed F81 host OOM; original runs and gates remain frozen, no host/global-setting changes.

- 2026-10-11T03:44:15+00:00: F81: kernel confirms host OOM killed Vivado; archived subrun/kernel evidence, numerical measurements unchanged. Independent serial retries planned as F89-F91.

- 2026-10-11T04:54:40+00:00: F81: kernel confirms host OOM killed Vivado; archived subrun/kernel evidence, numerical measurements unchanged. Independent serial retries planned as F89-F91.

- 2026-10-11T05:15:39+00:00: F82: final_cosim_F25; status=cosim_complete; latency_ms_est=2.64226; cosim of F25; HLS estimates inherited, real measurements in data.csv

- 2026-10-11T05:18:29+00:00: F83: final_all_supplied_F24; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-11T05:22:58+00:00: F84: final_impl_F24; status=fail; latency_ms_est=2.830503377; impl of F24; HLS estimates inherited, real measurements in data.csv; impl failed (exit=1)

- 2026-10-11T05:25:27+00:00: F84: kernel confirms host OOM killed Vivado; archived subrun/kernel evidence, numerical measurements unchanged. Independent serial retries planned as F89-F91.

- 2026-10-11T05:29:16+00:00: F82: archived RTL FIFO/process counters and their source prefixes; large per-cycle histories retained only in workspace; arithmetic/timing measurements unchanged.

- 2026-10-11T06:25:23+00:00: P13-P16: user requested complete INT16 packing research; preplanned direct, four-DSP byte limbs, one-DSP overlap/fabric repair and ordinary mixed controls. Exact32-bit product checks cover all16-bit values in each operand role, boundary cubes and deterministic random triples. Existing final verification queues continue.

- 2026-10-11T14:40:53+00:00: F85: final_cosim_F24; status=cosim_complete; latency_ms_est=2.830503377; cosim of F24; HLS estimates inherited, real measurements in data.csv

- 2026-10-11T14:41:03+00:00: P13: int16_direct_pair; status=pass; latency_ms_est=0.000264; PE only; two complete signed16 products per term, no network latency or Set14 claim

- 2026-10-11T14:42:01+00:00: F85: archived RTL FIFO/process counters and their source prefixes; large per-cycle histories retained only in workspace; arithmetic/timing measurements unchanged.

- 2026-10-11T14:42:06+00:00: P14: int16_limb_packing; status=pass; latency_ms_est=0.000272; PE only; two complete signed16 products per term, no network latency or Set14 claim

- 2026-10-11T14:42:58+00:00: P15: int16_overlap_fabric_repair; status=pass; latency_ms_est=0.000276; PE only; two complete signed16 products per term, no network latency or Set14 claim

- 2026-10-11T14:43:46+00:00: P16: int16_direct_mixed_control; status=pass; latency_ms_est=0.000264; PE only; two complete signed16 products per term, no network latency or Set14 claim

- 2026-10-11T14:46:35+00:00: F86: final_all_supplied_F23; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-11T14:52:06+00:00: F87: final_impl_F23; status=fail; latency_ms_est=2.95951606; impl of F23; HLS estimates inherited, real measurements in data.csv; impl failed (exit=1)

- 2026-10-11T14:53:34+00:00: F87: kernel confirms host OOM killed Vivado; archived subrun/kernel evidence, numerical measurements unchanged. Independent serial retries planned as F89-F91.

- 2026-10-11T15:11:04+00:00: F88: final_cosim_F23; status=fail; latency_ms_est=2.95951606; cosim of F23; HLS estimates inherited, real measurements in data.csv; cosim failed (exit=-15)

- 2026-10-11T16:42:26+00:00: F89: setup-path recovery now checks the parsed five paths, CSV, operation record, script digest and manifest instead of report presence alone; retry registration is idempotent. Infrastructure tests:45 PASS; routed result remains pending.

- 2026-10-11T16:47:17+00:00: F89/WS3: verified Vitis2026.1 export_design/config_export help: flow=none packages RTL without running Vivado. Added serial_packaged_flow for fresh WS2/WS3 verification workspaces, package logs and independent constraints/hooks;47 infrastructure tests PASS. Actual generated driver and routed verdict still required.

- 2026-10-11T16:52:33+00:00: WS2/WS3: documented conditional packetized exact G2 loading after F27 acceptance;48 infrastructure tests PASS. Loader analysis now recognizes continuous_wino_fold, preserving W17 II1 evidence. Added generated workstream table with separate HLS/RTL/routed columns; pending runs have no invented numeric results.

- 2026-10-11T16:55:16+00:00: F89: congestion rerouting continues, overlaps4157->2476; no final routed verdict. Workstream numeric tables now regenerate both WEIGHT_LOADING.md and docs0004 section9; future ARCH_SUMMARY regeneration preserves the active priority and tomorrow-review decisions.

- 2026-10-11T17:08:20+00:00: WS2/WS3: added fresh-ID verification planning with frozen source checks and separate all13/cosim/serial-impl operations. Serial templates now require byte-identical parent RTL/init files; package export also checks parent RTL.49 infrastructure tests PASS. Live F89 retains its original loaded runner and timeout.

- 2026-10-11T17:17:22+00:00: F89/WS3: observed F25 flow=none package has IP but no run_vivado.tcl. Clarification: flow=none skips RTL synthesis/route, while IP packaging still uses Vivado. Fresh serial candidates now copy only official driver/settings/extraction/XDC boilerplate, regenerate module lists/clock, preserve their independently packaged IP, and archive original/patched scripts for replay.50 infrastructure tests PASS. Live route overlaps2476->1277.

- 2026-10-11T17:35:00+00:00: F89/WS2 recovery: verified original local sessions95149/11690/51861 and remote runners remain active; no restart. F89 congestion overlaps now476, about4.1GiB available memory, original three-hour timeout unchanged. Read both AGENTS and docs0002/0003/0004 plus recovery/summary records; protected sources and existing user edits remain preserved. F26/F27 C validation is exact; hardware gates are pending.

- 2026-10-11T17:37:29+00:00: F89/WS3: final verification now checks validation_parent source SHA256, precision and design defines against the frozen hardware candidate at both plan and execution entry points; testbench-only flags may differ.52 infrastructure tests PASS, including recorded F25/F80 provenance. Live F89 congestion overlaps down to296; no final routed verdict.

- 2026-10-11T17:41:41+00:00: F89/WS4: added close_weight_loading.py for the current workstream instead of restoring deferred F90/F91. Closure requires explicit ready state, every current ID archived, no active remote HLS/Vivado processes, source/report provenance and local/remote checksums, then all CSV summaries/plots. Syntax, early-closure rejection and live process detection verified; no closure executed while F89/F26/F27 remain active.

- 2026-10-11T18:13:53+00:00: F89: serial_vivado_impl_F25; status=timeout; latency_ms_est=2.64226; impl of F25; HLS estimates inherited, real measurements in data.csv; impl failed (exit=124)

- 2026-10-11T18:19:02+00:00: F89: archived partial synth/placed reports and intermediate route summaries; final routed metrics remain unknown and failure/timeout unchanged.

- 2026-10-11T18:21:12+00:00: F26: s2p_bias_shift_T16; status=provisional; latency_ms_est=2.64227; 

- 2026-10-11T18:21:57+00:00: F89: archived partial synth/placed reports and intermediate route summaries; final routed metrics remain unknown and failure/timeout unchanged.

- 2026-10-11T18:28:11+00:00: F27: local_streamed_params_T16; status=provisional; latency_ms_est=2.6142825; 

- 2026-10-11T18:33:48+00:00: F27/F28: parsed ownership results (total61656/outside3170/mux184LUT, zero HLS200-1449); clock2.419ns is the sole WS2 gate miss. Planned/committed independent F28 local-load LOOP_FLATTEN off before copying its frozen parent; C simulation overlaps the active F92 serial5ns implementation. All resource, precision and clock thresholds remain unchanged.

- 2026-10-11T18:39:00+00:00: WS2 verification infrastructure: added --reload-params planning, independent archived testbench replacement, pre/post cosim RTL SHA checks, exact C/RTL reload/border markers, and archive-based verification replay.60 tests PASS. No changed-parameter RTL result or fresh-candidate routed result is yet claimed.

- 2026-10-11T18:47:08+00:00: F94: ws_all_F28; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-11T18:53:13+00:00: F31: reload_testbench_csim_F28; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-11T19:18:19+00:00: F92: ws_impl_F25; status=impl_complete; latency_ms_est=2.64226; impl of F25; HLS estimates inherited, real measurements in data.csv

- 2026-10-11T19:25:16+00:00: F28: local_load_no_flatten_T16; status=provisional; latency_ms_est=2.6150725; 

- 2026-10-11T19:27:41+00:00: F92: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-11T21:22:19+00:00: F93: ws_reload_cosim_F28; status=cosim_complete; latency_ms_est=2.6150725; cosim of F28; HLS estimates inherited, real measurements in data.csv

- 2026-10-11T21:31:03+00:00: W19: streamed_winograd_T8; status=infeasible; latency_ms_est=1.74903921; 

- 2026-10-11T21:42:35+00:00: F29: streamed_direct_T8_tree1; status=infeasible; latency_ms_est=1.7507841300000002; 

- 2026-10-11T21:51:24+00:00: WS3 recovery: resumed active queue64528 and W21 queue44013 without restarting their workspaces. W19/F29 are archived infeasible with exact butterflies, unchanged borders and foldII1; their manual interpretations now compare total/private-loader resources and paper estimates. W21 two-call C simulation is bit-exact and waits for W20 before synthesis. Updated recovery state and CSV-only area figure; F95 remains planned. F93 actual changed-parameter RTL PASS and latency1059506/interval1059535 are preserved separately from HLS and routed timing.

- 2026-10-11T21:53:45+00:00: F30: streamed_direct_T8_tree0; status=infeasible; latency_ms_est=1.7507708100000001; 

- 2026-10-11T22:57:22+00:00: W20: ws_impl_W17; status=impl_complete; latency_ms_est=2.130248; impl of W17; HLS estimates inherited, real measurements in data.csv; diagnostic only: parent remains HLS-resource-infeasible and cannot enter accepted rankings

- 2026-10-11T23:06:11+00:00: W21: subkernel_raw_cache_T8; status=provisional; latency_ms_est=1.74903921; 

- 2026-10-11T23:09:04+00:00: W20: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-11T23:09:27+00:00: F96: ws_all_W21; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-11T23:24:08+00:00: F95/F98: user requests higher remote utilization. Independent 30-second proc snapshot: {'cpu_intervals': 6, 'logical_cpus': 12, 'cpu_busy_pct': 8.863906306107229, 'mean_load1': 1.0471428571428572, 'max_load1': 1.06}. Preserve active serial hardware queue and frozen F95/F97/F98 plans; added per-run1/2/4 implementation-thread limits with synthesis1, CPU/memory telemetry and63 passing infrastructure tests. No global/swap/threshold changes; thread-speed benefit awaits a measured independent WS4 run.

- 2026-10-11T23:56:15+00:00: F95: ws_impl_F28; status=impl_complete; latency_ms_est=2.6150725; impl of F28; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T00:03 UTC: F95 route calibration and manual interpretation archived:5ns target passes with WNS+0.282ns/TNS0,591DSP/30140LUT/76498FF/72BRAM18K. F93 measured RTL latency gives5.29753ms at that closed target, not board time. Its initial worst path is Conv1 local-load address to LUTRAM WADR1; five-path export waits behind active F97. Updated recovery state to three remaining hardware operations: F97, F98 and one WS4 clock/thread probe; no further exploration will be added.

- 2026-10-12T00:48:27+00:00: F97: ws_cosim_W21; status=cosim_complete; latency_ms_est=1.74903921; cosim of W21; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T00:50:51+00:00: F95: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-12T00:55 UTC: F97 changed-parameter two-frame RTL PASS: measured latency558758/interval558787,6.382071% above HLS; first butterfly and six-pixel border remain exact to the precision reference, second outputs all104/256. F95 checkpoint five-path/hierarchy export also archived with SHA256; all paths are Conv1 local-load address to LUTRAM WADR1. Updated recovery to active F98 and one WS4 clock/thread probe, then F99 closure. Parsed profiles distinguish overlapping FIFO stalls from the frame-cycle deviation.

- 2026-10-12T01:54:26+00:00: F98: ws_impl_W21; status=impl_complete; latency_ms_est=1.74903921; impl of W21; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T02:01:09+00:00: F98: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-12T02:10 UTC: F98 routed analysis completed:5ns WNS+0.140ns/TNS0,644DSP/42594LUT/88806FF/109BRAM18K. F97 RTL cycles imply2.79379ms at the closed target. Three critical paths are Conv2 parameter FIFO to weight LUTRAM write data; two are Conv3 step control to DSP. Minimum available memory3.011604GiB/peak toolRSS11.642307GiB. Select one final W22 same-RTL4.95ns probe, placement/routing2 threads/synthesis1; preserve original HLS gates and5ns fallback. Remote hardware is idle; obsolete F98 session cleared. No further exploration will be added.

- 2026-10-12T02:56:23+00:00: W22: ws_clock_4p95_W21; status=impl_complete; latency_ms_est=1.74903921; impl of W21; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T03:00:07+00:00: W22: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-12 收尾审计修复：首次 changed-parameter cosim 的 `testbench_sha256` 使用 basename，源码提交记录在 `source_commit`；旧审计只接受重放实验的 `frozen_source_commit` 和仓库相对路径，导致 KeyError。修正提交/路径解析后仍逐字节对比归档 SHA256 和 `git show`，重放优先冻结提交，不跳过校验、不改实验配置或硬件结果。补充首次验证、Git 内容篡改、重放提交优先级和缺失提交四种检查。

- 2026-10-12 F99: 审计修复后的完整基础设施检查通过，67 tests；其中新增四项 testbench 源码来源检查，原有重放、报告解析、时钟隔离、CPU/内存和远程恢复检查全部通过。

- 2026-10-12T03:09:20+00:00: F99: WS0-WS4 operations archived and audited; 20 workstream records, local/remote protected checksums and report SHA256 verified; all plots regenerated. Failures remain explicit; no board acceptance or push.

- 2026-10-12T03:13:41+00:00: F99: WS0-WS4 operations archived and audited; 20 workstream records, local/remote protected checksums and report SHA256 verified; all plots regenerated. Failures remain explicit; no board acceptance or push.

- 2026-10-12T03:59:19+00:00: F34: ws0_memory_control_F96; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-12T04:05:22+00:00: F32: ws0_memory_control_F28; status=provisional; latency_ms_est=2.6150725; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T04:07:23+00:00: F33: ws0_memory_control_W21; status=provisional; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T04:13:55+00:00: F38: ws0_memory_control_F96; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-12T04:17:39+00:00: F35: runtime_rom_bank_equivalence; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-12T04:20:15+00:00: F36: ws0_memory_control_F28; status=provisional; latency_ms_est=2.6150725; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T04:22:30+00:00: F37: ws0_memory_control_W21; status=provisional; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T04:35:46+00:00: W24: constant_rom_T8; status=pass; latency_ms_est=1.7460189000000002; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T04:53:12+00:00: W26: frp_W21_T8; status=fail; latency_ms_est=unknown; ; Design not found: /home/lipuze/amdprojects/90096_CNN_FPGA/designs/winograd_frp_v1

- 2026-10-12T05:06:45+00:00: F41: fifo32_W21_T8; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T05:16:32+00:00: W27: frp_W21_T8; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T05:25:53+00:00: F42: reorder_W21_T8; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T05:35:02+00:00: F47: windows16_W21_T8; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T05:50:52+00:00: C13: runtime_prepacked_conv2_T4; status=infeasible; latency_ms_est=1.05236; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T05:52 UTC: ROM/clock/FIFO progress recovered without rerunning active jobs. F48 (window FIFO16) and F46 (reorder output FIFO256) paper plans committed and queued for changed-parameter two-frame RTL. State now includes W28/W29/W30 and removes completed sessions. Summary includes unmeasured plans separately and refuses to attach a failed cosim cycle gate to an accepted routed frame time;89 infrastructure tests pass. CSV-only plots group overlapping IDs, and interpretations compare the actual HLS reports with paper estimates. Implementation W23/W29/W30 remains unlaunched under the unchanged12.5+2GiB admission requirement.

- 2026-10-12T05:58:13+00:00: W25: rom_changed_input_cosim_W24; status=cosim_complete; latency_ms_est=1.7460189000000002; cosim of W24; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T06:01:26+00:00: F40: fifo16_W21_T8; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T06:12:09+00:00: F39: c3_select_W21_T8; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T06:18 UTC: F39 synthesis collected and committed; all13 images E017-exact, foldsII1,644DSP/146BRAM18K/81518LUT/130422FF/525237cycles. F43 changed-parameter RTL plan committed before queuing; retain553171..564345cycle acceptance. Reconciled live sessions and addedF44. Derived comparisons now use matching successful RTL cycles for architecture paper estimates (W24 estimate547500 versus W25 actual554226) and separately report the WS-D2% performance goal with maximum integer535741cycles.95 infrastructure tests pass; arithmetic/deadlock PASS cannot silently establish the performance goal.

## Pending Human Decisions / 待人工决策

- 2026-10-12 HLS FIFO accounting: F47's1728-bit transformed-window FIFO reports67LUT at both depth2 and16; F42's163840-bit raster FIFO reports347LUT. The logical capacities require much more storage under a naive64bits/LUT model. Preserve these raw estimates and require routed utilization to resolve the discrepancy; do not claim near-zero physical storage cost or alter any resource gate.

- 2026-10-12T04:24 UTC，0005 内存准入：远程 MemTotal=15724196 KiB（14.996 GiB），空闲 MemAvailable 约13.4 GiB；WS-C1 的12.5 GiB登记预算加2 GiB保留要求至少14.5 GiB可用，因此空闲时也不能准入。保守保留0005的总预算13 GiB、2 GiB可用内存保留和实现12.5 GiB登记，不通过关闭调度或改swap启动W23。其W21/F98同RTL、4.5ns、Performance_Explore、综合1/布线4线程计划已提交；工具探针确认策略与布线后phys_opt属性支持。继续独立ROM编码/功能验证/综合；实际启动实现需要人工澄清登记口径或调整内存规则。当前不宣称W23已经启动、超时或时序失败。

- 2026-10-12T04:24 UTC，WS-0登记修正：初次F32/F33进程树RSS3.119/3.430 GiB高于2.5 GiB登记；工具报告的1.460/1.779 GB是allocated memory，并非完整进程树RSS。F36/F37/F38以csynth4 GiB、csim1.25 GiB重验，实际三任务重叠77.827秒、最低可用10.706 GiB、无OOM且功能/II与冻结父实验相同，已启用按预算准入。这会使13 GiB总预算下的csynth实际最多3个，并使7.5 GiB cosim最多同时容纳1个4 GiB csynth；规则中的4/2个为上限，不保证全部能同时准入。原失败登记证据保留。

- 2026-10-12 收尾展示材料：最终两地 checksum 与全部报告 SHA256 已通过。修复 CPU 图例颜色，折行样本作用域标签，增大资源校准图以容纳实验 ID；等价离线 G2 归档补入 `winograd_param_stream` 和 `winograd_subkernel_cache`，原始权重及运行时接口不变。以上均为归档/展示更新，不新增硬件运行。

- 2026-10-12 W22: 最后一个 WS4 探针已完成，4.95 ns 下 WNS +0.047 ns / WHS +0.032 ns，IP 推导帧时间 2.7658521 ms，比 F98 5 ns 低 1%，但 setup 余量从 140 ps 降至 47 ps。按最小延迟目标保留 W22 为当前最快已验证时钟点，同时保留 F98 为更保守的集成起点，板端团队可在系统时钟验收时选择。不得把 4.903 ns 的 slack 推导值当作已验证时钟；缺 comic、资源口径、常量 ROM 和大内存主机仍按第 6 节待复核。

- 2026-10-11T18:56:00+00:00: WS2/WS3 preparation: F94 independently passed all13-image exactness and mean deltaPSNR=-0.069514dB. F31 independent changed-parameter C preflight passed, with every second output bit equal104/256 and unchanged first-frame borders; this is not RTL evidence. W19/F29/F30 paper plans are committed and conditional on measured loader selection; no parent design is modified. F92 remains in placement and F28 synthesis waits for its lock.

- 2026-10-11T18:33:48+00:00: WS2: F27 passes exact/area/II/cycle gates but misses clock2.419>2.377ns. Conservatively retain the gate and use an independent local-load loop-flatten control F28 before selecting the loader. F92 is running on unchanged F25 RTL with5ns implementation constraints; no partial F89 timing or LUT ratio is treated as final route acceptance.

- 2026-10-12 WS0: 用户授权第 6 节先自行决策并执行、明日复核。暂定保留运行时 float 权重接口及 HLS 资源门限，不做常量 ROM；缺 comic 保持 13 图暂定结论。F89 若再次 OOM，保留内核/内存证据并继续 WS2，不改 swap 或全局设置，不迁移到未经验证的主机。明日复核大内存主机、ROM 专用版本、资源口径和 comic 数据。

- 2026-10-12 WS0: 2026-10-12 用户决定降低优先级：F88/F90/F91。F88 主动中止（SIGTERM），无 RTL 判定；P14–P16/F86/F87 新指令前已完成，保留实测结果。F85/P13 已收回无需重跑；当前硬件队列仅 F89，随后 WS2→WS3。

- 2026-10-11T03:45 UTC: F81 failed in Vivado technology mapping because kernel OOM killed the main synthesis process while four internal worker processes used about2.4GiB each. F89-F91 are independent preplanned serial retries; a checked per-run Tcl hook sets general.maxThreads and synth.maxThreads to1, preserving target clocks, directives and HLS sources. No system swap/global tool setting is changed. If serial implementation still cannot complete within host capacity, a larger-memory host is required for routed evidence; failed synthesis is not implementation or timing acceptance.

- 2026-10-10T23:19:34+00:00: Winograd's requested offline weight transform conflicts with accepting arbitrary original float weight arrays at the frozen srcnn signature. Keep the internal runtime load/transform stage, include its measured cycles/resources and archive the equivalent pretrained G2 tensor. Removing runtime transformation requires an approved transformed-weight contract or a specialized constant-weight wrapper; no such interface change is made in this unattended run.

- 2026-10-10T22:20 UTC: S01's global m_axi pragmas did not export scratch1/scratch2. The two float feature arrays became11286 BRAM18K; the run is invalid_config and cannot count as DDR architecture evidence. A full sequential DDR implementation needs two explicit scratch pointer arguments or an approved wrapper/memory contract. Keep the frozen srcnn signature now; compare tile/dataflow hardware and separately archive the50,491,916-byte DDR payload model at19.2/9.6GB/s.

- Recovery reference: [PHASE2_HANDOFF.md](PHASE2_HANDOFF.md) preserves unimplemented architecture hypotheses derived from E058/E070/E071 across the first-phase finalizer. Phase two must still be executed on the new branch with estimates archived before implementation.

- 2026-10-10T19:08 UTC: Row-buffer padding has separate read-row and write-row phases. C synthesis does not execute finite-FIFO backpressure, so the reported maximum-component dataflow latency may underestimate the real schedule when pad3 serializes row production and consumption. Verify with the authorized RTL cosimulation; phase-two online padding is a proposed measured control, not a claimed speedup.

- 2026-10-10T18:47 UTC: E046 passed C simulation and exact comparison but its older runner exhausted a 60-minute synthesis-lock wait while other runs held the single memory-budget slot. No synthesis was launched, so no hardware result is claimed. E063 retries with the new independent 24-hour queue wait; each actual synthesis still has a 60-minute process-tree timeout.

- 2026-10-10T17:33 UTC: E014 exceeded its 45-minute simulation limit after nine Set14 images; retained as timeout. E010/E017 cover all 13 supplied images. Full all-ap_fixed representatives now use one complete butterfly inference, mandatory bit comparison to numpy and the original border metric.
- 2026-10-10T17:33 UTC: E018/E034/E035 and E012 failed compilation because Vitis prepended a relative prefix to quoted absolute include paths (`-I../../\"/home/...\"`). Restore verified unquoted paths and reject whitespace in the checkout path; corrected runs use new IDs E015/E019/E016/E044/E045. No failed synthesis is counted.
- 2026-10-10T17:33 UTC: Commit checks rejected a trailing blank line in the generated scatter template. Removed that whitespace and retained all failed-run archives in commit E034. Serial Git commit lock added to prevent independent simulation queues from racing over the index.


- Requested Windows Vitis 2026.1 environment is not available from this Mac. The existing project SSH shortcut reaches Linux Vitis 2026.1. Use that verified installation, record OS/tool version in each config and provide Windows settings-batch support in the runner. Windows reproduction remains unverified.
- The supplied Set14 directory contains 13 pairs, with `comic` absent. Evaluate every supplied image and report `image_count=13`; do not describe that as all 14 images or as complete Set14 acceptance. Any final candidate remains provisional until the missing pair is supplied and tested.
- No existing MSE threshold exists. Conservatively require float outputs bit-identical to an independently compiled unchanged golden model under the same compiler settings, while recording MSE against the supplied binary references and six-pixel border MSE separately. No original test or threshold will be altered.
- Existing `calculate_PSNR` converts model output to uint8 without clamping and may wrap outside [0,1]. Use explicitly defined normalized float MSE PSNR (`10 log10(1/MSE)`, no clipping/cropping) for the new precision gate against the same float golden; also preserve original testbench output. Metric choice must be reviewed before claiming external benchmark equivalence.

