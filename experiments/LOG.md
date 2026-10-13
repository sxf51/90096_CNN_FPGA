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

- 2026-10-12T06:52:37+00:00: F45: ws_cosim_F41; status=cosim_complete; latency_ms_est=1.74903921; cosim of F41; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T07:57:42+00:00: F46: ws_cosim_F42; status=fail; latency_ms_est=1.74903921; cosim of F42; HLS estimates inherited, real measurements in data.csv; Task terminated at the configured MemAvailable floor: {"available_gib": 0.4973716735839844, "floor_gib": 0.5}

- 2026-10-12T08:04:26+00:00: F43: ws_cosim_F39; status=cosim_complete; latency_ms_est=1.74903921; cosim of F39; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T08:14 UTC: F43 final changed-parameter RTL PASS at558758latency/558787interval, identical to F97 and within553171..564345. F49 independent4.5ns routing and W29 ROM5ns routing are queued; W28 FRP and C14 T4 mixed are actually running concurrently. F46 is retained as fail after actual MemAvailable0.497372GiB termination without a new OOM. Two completed telemetry traces establish3551.591seconds overlap and14.116714GiB aligned combined RSS (including shared mappings). F43's100 extra operand-register module monitors generate1517011599bytes of process event histories and reach9.507710GiB RSS. The installed2026.1 schema confirms cosim.setup, profiling enable and deadlock-detection options, but no aggregate-only mode was found. Preserve standard generated monitors and all correctness/cycle/FIFO gates; F50 is a separately planned retry of F42. No completed workspace, protected design or tool installation is changed.

- 2026-10-12T08:52:54+00:00: C14: ws_cosim_C13; status=cosim_complete; latency_ms_est=1.05236; cosim of C13; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T09:00:01+00:00: W28: ws_cosim_W27; status=fail; latency_ms_est=1.74903921; cosim of W27; HLS estimates inherited, real measurements in data.csv; Measured RTL cycles are below the preplanned acceptance bound

- 2026-10-12T09:54:29+00:00: F44: ws_cosim_F40; status=cosim_complete; latency_ms_est=1.74903921; cosim of F40; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T10:01:54+00:00: F49: ws_impl_F39; status=fail; latency_ms_est=1.74903921; impl of F39; HLS estimates inherited, real measurements in data.csv; Task terminated at the configured MemAvailable floor: {"available_gib": 0.3829193115234375, "floor_gib": 0.5}

- 2026-10-12T10:07:17+00:00: F48: ws_cosim_F47; status=cosim_complete; latency_ms_est=1.74903921; cosim of F47; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T10:08:40+00:00: W29: ws_impl_W24; status=fail; latency_ms_est=1.7460189000000002; impl of W24; HLS estimates inherited, real measurements in data.csv; Task terminated at the configured MemAvailable floor: {"available_gib": 0.4664421081542969, "floor_gib": 0.5}

- 2026-10-12T10:18 UTC: Live process and scheduler inspection confirms W23 and C15 independent implementations are active, not merely queued. F50 rasterFIFO RTL and newly launched wrapper F51 windowFIFO16 route await a free task slot. Persisted F48's measured535771/535800cycles,22987-cycle improvement and strict30-cycle WS-D miss. F49/W29 both stopped at the actual0.5GiB guard with unchanged OOM1; preserve host failures and prepare F52/W31 fresh-workspace retries. Reconciled recovery state; no completed workspace or frozen threshold is modified.

- 2026-10-12T10:19:42+00:00: W23: ws_clock_strategy_4p5_W21; status=fail; latency_ms_est=1.74903921; impl of W21; HLS estimates inherited, real measurements in data.csv; impl failed (exit=137)

- 2026-10-12T10:28:12+00:00: W23: kernel confirms host OOM killed Vivado; archived subrun/kernel evidence, numerical measurements unchanged. Preserve the failed workspace and use separately planned retry IDs.

- 2026-10-12T10:55:15+00:00: C15: ws_impl_C13; status=fail; latency_ms_est=1.05236; impl of C13; HLS estimates inherited, real measurements in data.csv; Task terminated at the configured MemAvailable floor: {"available_gib": 0.43378448486328125, "floor_gib": 0.5}

- 2026-10-12T11:40:15+00:00: F52: ws_impl_F39; status=impl_complete; latency_ms_est=1.74903921; impl of F39; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T12:20:59+00:00: W32: ws_clock_strategy_4p5_retry_W21; status=impl_complete; latency_ms_est=1.74903921; impl of W21; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T12:53 UTC C18：综合及综合报告已于12:42:08UTC成功退出，第二阶段重新打开原project.xpr进行5ns布局布线，无重新综合。12:53UTC检查全部六个等待worker仍为T状态、两个优先监督存活；当前唯一重任务为C18。远程实际MemAvailable=7630408KiB，SwapTotal=SwapFree=8388604KiB，/dev/zram0为8GiB zstd、优先级100；swap使用量0。docs/0005的用户新增记录说明zram与清理由外部已授权操作完成，本agent未修改系统配置。最终内存改善需同时分析分阶段和swap数据，不能全部归因于流程拆分。

- 2026-10-12T13:00 UTC C18：swap采样新增容量和实际使用量，汇总明确旧样本字段缺失，不根据SwapFree推断历史使用；12项内存/分阶段/并行测试和11项路径测试通过。C18正在运行的原逐阶段CSV保持原schema，另存runtime_host_environment.csv作当前主机观测，不能充当整次工具峰值。外部已授权的zram/清理记录保持原文，调度仍最多一项重任务。

- 2026-10-12T13:32:31+00:00: C18: ws_impl_C13; status=impl_complete; latency_ms_est=1.05236; impl of C13; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T13:35 UTC C18：已独立5ns布线收敛，WNS+0.047/WHS+0.031/TNS0，1032DSP/58529LUT/102072FF/109BRAM18K/URAM0，全部routed门槛通过。关联同父C14的300632/300661RTL周期、C13全部13图E065逐位和ΔPSNR-0.075890dB，IP帧时间1.503160ms；未上板。分阶段进程树峰值综合10.640743GiB、实现8.169937GiB，最低可用4.822098GiB，工具70.538872分钟；完整swap使用因旧字段缺失仍unknown。两个优先监督13:32:30UTC恢复全部六项等待，实际进程已从T变S，W30已启动。保留C13原HLS判定及C15失败；当前资源无需T4 ROM，继续C16/C17和其后独立RTL/实现。

- 2026-10-12T13:57:35+00:00: C18: regenerated CSV-only route calibration and ROM-clock figures; separated resource panels and retained external ID annotations with tight image bounds. Hardware measurements and acceptance gates are unchanged.

- 2026-10-12T14:06:23+00:00: C18: archived verified runtime IP package provenance and generated driver/register map in experiments/board_handoff/C18; preserved F98 handoff. Transfer SHA256 agrees before/after collection. Route, same-parent exact reload RTL, all13-image precision and six handoff gate checks passed. OOC limit200MHz, no board result; ZIP/HDL stay outside Git.

- 2026-10-12T14:11:15+00:00: C18: interim --snapshot audit passed for local/remote protected checksums and immutable source/report hashes; six planned experiments remain unmeasured and remote jobs are active. Snapshot is not closure. Board results remain unavailable; no push.

- 2026-10-12T14:22:21+00:00: W30: ws_impl_W27; status=impl_complete; latency_ms_est=1.74903921; impl of W27; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T14:25:11+00:00: F52: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-12T14:31:55+00:00: W30: independent4.5ns route passes all physical gates; W28 authorized exact549438cycles gives2.472471ms uniform T8. Five generated-final setup paths and physical hierarchy archived, first slack matches final summary; F52 checkpoint paths archived too. F51 is now the sole running implementation. Preserve18GiB registration, serial-after-OOM and old W28 fail. C18 remains fastest1.503160ms; five queued experiments remain before conditional combination RTL/routing.

- 2026-10-12T14:39 UTC W30 supplemental plots: regenerated the ROM/clock and routed calibration plots from the current CSV files and inspected the two changed figures. F51 has completed Vivado synthesis and is the sole heavy task; F50/W31/C16/C17 remain queued. C19-C22 are unused in both locations. After C16/C17 pass all13-image and HLS screening, plan changed-parameter cosim C19/C20 and staged implementation C21/C22, then run them under the existing one-heavy admission policy. First physical targets are4.5ns forT8 and5ns forT4, backed by W30/W32 and C18 respectively; faster RTL remains allowed. These four follow-ups are conditional preparation, not measured or launched experiments. Final path exports, plots and integrity audit remain pending.

- 2026-10-12T14:50 UTC F50 queue ordering: priority_waiters now accepts an explicit decision basis (four existing pause/resume tests pass). In the scheduler lock, W31's package waiter PID80160 was proven unadmitted and paused; active F51 was untouched. F50 will be favored over W31 after F51, permitting C16/C17 screening if the13GiB total budget and2GiB light headroom both pass. A7.5GiB cosim, one4GiB synth and one1.25GiB csim total12.75GiB; actual overlap remains unmeasured. Supervisor session1570 automatically resumes W31 on F50 completion, timeout or exit. Preserve18GiB impl registration, serial_after_oom=true, all original plans, tool timeouts and gates. C18/W32 checkpoint exports remain under the same one-heavy cap.

- 2026-10-12T15:06:59+00:00: F51: ws_impl_F47; status=impl_complete; latency_ms_est=1.74903921; impl of F47; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T15:10:49+00:00: C18: exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.

- 2026-10-12T15:15:51+00:00: W32: archived five setup paths from the matching final generated report; no additional Vivado run.

- 2026-10-12T15:16:52+00:00: F51: archived five setup paths from the matching final generated report; no additional Vivado run.

- 2026-10-12T15:27:50+00:00: C17: t4_fifo; status=infeasible; latency_ms_est=1.05236; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T15:29:09+00:00: F51: independently route-feasible at5ns with535771 matching F48 RTL cycles,2.678855ms IP frame time and644DSP/43617LUT/87203FF/109BRAM18K. Archive all five final paths and physical hierarchy. C18 checkpoint export completed after it had already admitted; leave the active export intact. W32 unadmitted export was deliberately cancelled under the scheduler lock at15:10UTC and replaced by the matching final postroute_physopted report; preserve original console and cancellation SHA256 proof. The generated-report archive path passes13 focused tests. F50 RTL and C17 HLS now actually overlap; C16 waits for synthesis budget and W31 is auto-resuming after F50. Four planned experiment results remain, followed by conditional combination RTL/routing and any justified clock probe. No gate, source interface, protected file or existing workspace is changed.

- 2026-10-12T15:36:50+00:00: C16: t8_fifo_frp; status=pass; latency_ms_est=1.74903921; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-12T16:00:21Z C19/C21: both local and remote IDs were unused. C16 all13 E017-exact images and all three II1 folds have passed; prepared and committed changed-parameter C19 RTL and conditional staged4.5ns C21 route plans. C19 wrapper session64820 is queued behind the existing one-heavy scheduler, not measured; C21 remains unlaunched until accepted C19. Removed finished C16 session9972 from recovery state. Six planned results remain, plus a separate ROM4.5ns probe only if W31 closes5ns. F50 is the sole actual heavy task and has completed the first of two RTL transactions. Keep18GiB implementation registration, serial_after_oom, exact/quality/physical gates and no-push. analyze_route now fills missing legacy physical-gate fields from archived raw reports without changing config/metrics or historical statuses;20 focused route/path tests passed. Regenerate verified plots before final closure.

- 2026-10-12T16:04:57+00:00: F50: ws_cosim_F42; status=cosim_complete; latency_ms_est=1.74903921; cosim of F42; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T16:08:43Z F50: exact changed-parameter RTL PASS at558760 latency/558789 interval cycles, two cycles slower than F97/W21; no raster-buffer throughput gain and WS-D diagnostic target remains unmet. reorder_rows two-frame write stalls become15256, but forward_raster inherits903826 against the four-entry features FIFO; counters overlap and cannot be summed. Preserve F46's host-memory failure and archive the successful unchanged retry. Supervisor released W31 at16:04:56UTC; verified C20 is now the sole heavy task. Five plans remain C19/C20/C21/C22/W31. Author C16/F50 interpretations and refresh recovery state. Interim16:06UTC audit passed both-location protected checksums and source/report integrity with active jobs; final idle audit and closure remain pending. No push or board result.

- 2026-10-12T16:42:53+00:00: C20: ws_cosim_C17; status=cosim_complete; latency_ms_est=1.05236; cosim of C17; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T17:34:51+00:00: C19: ws_cosim_C16; status=cosim_complete; latency_ms_est=1.74903921; cosim of C16; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T18:05:51+00:00: W31: ws_impl_W24; status=impl_complete; latency_ms_est=1.7460189000000002; impl of W24; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T22:21:00Z C22/C21: C19/C20 exact RTL and W31 route completed in the existing workers; the conditional implementation plans were not automatically launched, leaving the host idle. Confirmed empty remote scheduler and unused C21/C22 workspaces, then started sequential queue46657 with C22 first and C21 next. C22 package completed and staged synthesis is actually running. C20 measures273023latency/273052interval versus C14's300632; C19 measures535976/536005 versus F48's535771. W31 closes5ns at630DSP/33771LUT/82635FF/101BRAM18K, WNS+0.470/WHS+0.038, and triggers committed W33 fresh4.5ns ROM plan. Keep mainline queue first and all one-heavy/memory/physical gates. docs/0005 also contains approved WS-F added by the user; prepare independent reload-switch work and run its verification after C19-C22, before final closure. No push or board validation.

- 2026-10-12T22:39:38+00:00: W31: archived five setup paths from the matching final generated report; no additional Vivado run.

- 2026-10-12T22:39 UTC C22 recovery / C23 preparation: SSH transient failure ended local queue46657 during archive transfer; remote C22 worker119223 and staged synthesis survived, while C21 never launched. Confirmed live process and scheduler identity, then started recovery supervisor33324 to collect C22 before launching C21 and W33. It refuses to overwrite any stopped incomplete workspace. C23-C27/F53 were unused remotely and locally; committed C23 WS-F paper estimate before copying frozen C13 to an independent reload-switch directory. Gate only parameter-read/transform/load processes, preserve static uninitialized banks, original wrapper and all arithmetic/FIFO/precision. New sequence checks cover load/reuse/reload/latest-bank retention; fresh-process fallback and all13-image reused weights remain separate mandatory checks. No protected file, existing workspace, numerical gate or physical gate changed.

- 2026-10-12T23:32:35+00:00: C22: ws_impl_C17; status=impl_complete; latency_ms_est=1.05236; impl of C17; HLS estimates inherited, real measurements in data.csv

- 2026-10-12T23:34 UTC C22: recovered completed remote route without rerunning the workspace. Final5ns WNS+0.013/WHS+0.032,TNS0 and no unrouted/partial nets pass;1032DSP/59552LUT/100499FF/109BRAM18K. Matching C20 exact273023cycles establishes1.365115ms,9.18percent faster than C18. Recovery supervisor33324 has actually started C21; W33 follows. WS-F source, guarded13-image test, four-call sequence and fresh-process fallback are committed; C23 wrapper65418 and C24/C25/F53 wrapper2446 wait for C21 before unchanged memory-budget admission. Six new gate tests and existing runner/verification/profile/architecture tests pass; no WS-F hardware result yet. Monitored cosim uses documented setup plus unchanged generated simulation/post-check scripts, an observer only in the generated testbench, per-call zero-AXI gates and synthesis RTL hashes. No original or first-phase design file changed; no push or board claim.

- 2026-10-12T23:35:41+00:00: C22: archived five setup paths from the matching final generated report; no additional Vivado run.

- 2026-10-12T23:40 UTC C22: matching C20 handoff and IP-package SHA256 are archived; route/architecture/ROM-clock CSV analyses, summaries and three comparison plot scripts refreshed. Eleven ROM-clock checks and five simulation-observer workflow checks pass. Observer tests cover immutable synthesis RTL, rejected duplicate/wrong-count instrumentation, setup failure, cumulative timeout and retained logs. The real monitored HLS driver remains unvalidated until WS-F RTL runs; no unit-test result is substituted for hardware evidence. C21 is the sole active heavy task, with W33 and C23/C24/C25/F53 preserved in their existing supervisor queues.

- 2026-10-12 23:44:26 UTC C23: prepared separate first-load/reuse/reload/retain reporting and CSV-only plots. All154 experiment-infrastructure tests pass, including rejection of failed RTL, mismatched/unclosed routing and nonzero parameter read-valid counts on a skipped call. No reload hardware measurements exist yet; the empty measurement CSV is explicit and no plot or milliseconds are fabricated.

- 2026-10-12 23:52:10 UTC C23: extend independently packaged Vivado flow and verified IP handoff to the approved srcnn_reload top. Legacy srcnn still requires its exact changed-parameter two-call proof; reload handoff independently requires all four exact calls and measured zero skipped-call parameter traffic. Generated one-bit load_params register is distinct from eight64-bit pointers. Archive the original per-transaction performance table and AXI CSV as tracked source evidence even when setup/standalone simulation does not emit the conventional cosim report. Eleven handoff and24 verification checks pass; actual reload RTL/package/route results remain outstanding.

- 2026-10-13T00:17:45+00:00: C21: ws_impl_C16; status=impl_complete; latency_ms_est=1.74903921; impl of C16; HLS estimates inherited, real measurements in data.csv

- 2026-10-13T00:18:04+00:00: C21: archived five setup paths from the matching final generated report; no additional Vivado run.

- 2026-10-13 00:21 UTC C21: independently closed 4.5 ns, exact matching C19 frame 535976 cycles gives 2.411892 ms; all physical gates pass. Archive interpretation of the five parameter-load/local-weight-memory setup paths and the greater-than-20-percent HLS-to-route resource differences. C21 package/register handoff is complete; C22 remains the 1.365115 ms leader. W33 is the sole admitted implementation; C23/C24 runners wait for memory, with C25/F53 following. Refresh current state, derived tables and plots without changing frozen plans or rerunning completed workspaces. No board measurement or push.

- 2026-10-13 00:29 UTC C21: snapshot integrity audit passed for local/remote original 46 files, 45 frozen phase-one design files, immutable paper plans, archived source/testbench/report hashes and Git exclusions. It records 41 measured workstream records and five unmeasured plans with active remote workers; this is not the final idle audit. W33 synthesized 630 DSP and is generating its synthesis reports before the independent implementation stage. No extra hardware job or changed memory threshold.

- 2026-10-13T00:53:10+00:00: W33: ws_impl_W24; status=impl_complete; latency_ms_est=1.7460189000000002; impl of W24; HLS estimates inherited, real measurements in data.csv

- 2026-10-13T00:53:39+00:00: C24: reload_switch_sequence; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-13T00:53:39+00:00: W33: archived five setup paths from the matching final generated report; no additional Vivado run.

- 2026-10-13T00:54:07+00:00: C25: reload_switch_cold; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-13 00:55 UTC W33/C24/C25: W33 independently closes 4.5 ns at WNS +0.063/WHS +0.032, all routed resource gates and zero unrouted/partial nets. Matching W25 establishes 2.494017 ms; the five worst paths are Conv3 wide-window FIFO enables, with 92.83 percent routing delay and fanout 4000 on the worst path. C24 four-call load/reuse/reload/retain and C25 fresh-process load=0 checks pass exactly. C23's all13-image C quality passes at unchanged deltaPSNR -0.07589037644656216 dB, with HLS screening still running; F53 legacy regression follows. Refresh interpretations and recovery state. Correct future reload verification plan wording to four calls; frozen plans and thresholds stay unchanged. No RTL reload verdict or board result exists yet.

- 2026-10-13T00:56:05+00:00: F53: legacy_C13_regression; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-13T01:09:55+00:00: C23: reload_switch_quality; status=infeasible; latency_ms_est=1.05236; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-13T01:11:14+00:00: C26: ws_cosim_C23; status=fail; latency_ms_est=1.05236; cosim of C23; HLS estimates inherited, real measurements in data.csv; Unsupported memory telemetry phase

- 2026-10-13T01:43 UTC C27 checkpoint: the first of four monitored RTL transactions completes with load=1,8129 parameter AR requests and R beats,32516read bytes,and zero writes. The other calls and generated C/RTL output post-check remain outstanding. The generated AXI-Lite sequence writes the load flag and waits for argument writes before setting start; the read-only observer therefore samples the programmed flag. All164 experiment-infrastructure unit checks pass locally. One heavy task remains active with about10GiB available; no physical or reuse verdict is inferred from this partial result.

- 2026-10-13T02:12 UTC C27: after two complete RTL transactions,the loaded call reads8129floats/32516bytes and the skipped call still makes1AR/R handshake,4bytes. The generated top passes biases3_0_0_val into dataflow_region after an unconditional top-level read; the internal do_load guard cannot suppress it. Preserve the active four-call run through the C/RTL post-check and keep the strict zero-AXI failure. Do not route C23. C28-C30 are unused and will independently copy C23,guard the scalar bias read at the non-DATAFLOW top,and repeat complete quality/HLS,sequence,cold-start and subsequent RTL/route checks. These are light-job plans subject to existing memory admission; no second heavy task or threshold change is authorized by this repair.

- 2026-10-13T02:19:05+00:00: C30: reload_guard_cold; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-13T02:19:13+00:00: C29: reload_guard_sequence; status=csim_pass; latency_ms_est=unknown; 

- 2026-10-13T02:35:41+00:00: C27: ws_cosim_C23; status=fail; latency_ms_est=1.05236; cosim of C23; HLS estimates inherited, real measurements in data.csv; Skipped-load transaction has parameter AXI traffic

- 2026-10-13T02:36:00+00:00: C28: reload_guard_quality; status=infeasible; latency_ms_est=1.05236; ; HLS status retained; final feasibility requires independent routed gates

- 2026-10-13T02:36:23+00:00: C27: recovered raw failed reload measurements and unchanged synthesis RTL SHA256; original verdict preserved.

- 2026-10-13T02:40:30+00:00: C27: recovered raw failed reload measurements and unchanged synthesis RTL SHA256; original verdict preserved.

- 2026-10-13T02:48:58+00:00 F90/F91: user cancelled obsolete unlaunched F24/F23 routing retries. Verified no corresponding local or remote workspace and no remote process; retain immutable paper/config plans and archive cancellation.json in each experiment folder. Remove both IDs from the active retry queue and deferred list; no result row, tool time or hardware verdict is fabricated. C31 repaired four-call RTL remains active under supervisor59926, and independent C32 routing remains conditional on its strict acceptance.

- 2026-10-13T03:31:56+00:00: C32/W34: committed WS-G quality/sequence/cold plans and C17 same-RTL4.5ns Performance_Explore plan before implementation. C31 alone executes RTL; W34 is an unadmitted heavy-slot waiter. Snapshot audit at03:30UTC verifies both-location protected hashes and plan/report provenance, records51 archived workstream operations and five unmeasured plans.17 targeted audit/summary/analysis tests pass; conditional plans remain unmeasured. F90/F91 cancellation records preserve original plans and no result rows. WS-G source copy is gated by accepted exact/zero-AXI C31; WS-I remains last.

## Pending Human Decisions / 待人工决策

- 2026-10-13 01:34 UTC C27: snapshot audit passes local/remote original46 and frozen phase-one45 file hashes, immutable plans, source/testbench/report provenance and Git exclusions. It records47 archived workstream operations and one active unarchived C27, never idle closure. C27 has completed setup and genuinely runs the generated simulation/post-check driver with the read-only AXI observer; its first RTL transaction remains in progress. Separate5ns routing still requires actual exact/zero-AXI acceptance.

- 2026-10-13 01:13 UTC C23/C26/C27: C23's complete13-image E065 exactness, unchanged deltaPSNR and three fold II1 checks pass; HLS screening permits independent hardware validation while retaining the original infeasible status. C26 is rejected before any Vitis process due to unregistered monitored telemetry phases. Preserve the original fail record, register both phases strictly as cosim heavy leases, and pass21 targeted scheduler/observer checks. Fresh C27 now actually runs setup under supervisor31264; four-call exactness, zero skipped parameter AXI and independent5ns routing remain outstanding. No numerical, memory or physical gate is relaxed.

- 2026-10-13 00:05:47 UTC C23: standalone Vitis Tcl interpreter probe confirms ::AP::printMsg, ::AP::check_bin_exist and ::AESL_AUTOSIM::gDebug are available without a project or simulation. Archive the original tool log in C23/tool_probes/monitor_environment.txt and reproducible exp/hls_monitor_environment.tcl; this is an environment query, not RTL validation. C21 progresses through rerouting; C22 handoff/path completion and outstanding conditions are refreshed in the recovery state.

- 2026-10-13 00:02:11 UTC C23: existing C20 logs confirm HLS executes C vector generation before creating the standalone run_sim driver. The generated driver then runs its own C vector generation and RTL C post-check. Monitored acceptance now requires exactly two successful metric blocks from cosim_execute.console.log, with setup/vector-generation evidence separately retained in the combined log. A regression test rejects missing execution-phase C/RTL checks and verifies all four cycle/AXI source measurements; seven observer checks pass. Actual WS-F execution remains outstanding.

- 2026-10-12 23:58:38 UTC C23: intermediate snapshot audit verifies original46files and45frozen phase-one design files at both locations, immutable paper plans, archived source/report SHA256 and Git tracking. Six requested plans remain unmeasured; idle closure is not claimed. Add SHA256-protected copies of generated run_sim/check_sim/dataflow-monitor/run_xsim drivers and verify they remain unchanged during monitored execution;161 infrastructure tests pass. The monitoring backend still requires actual HLS/RTL execution.

- 2026-10-12T12:21 UTC C18：在W32退出后获得唯一重任务槽（12:20:58UTC），package成功，12:21:57UTC开始分阶段综合。其余六个未启动等待进程保持暂停并自动恢复，C18不是仅排队。分阶段内存汇总已补齐，按两个工具阶段取峰值并排除CPU计数器的等待空隙；19项相关测试通过。W32已在4.5ns独立收敛，WNS+0.144/WHS+0.029，IP级2.514411ms；五条路径必须从postroute_physopt最终checkpoint导出，11项路径测试通过，导出顺延至C18之后。

- 2026-10-12T12:12 UTC C18优先执行补充：C16/C17仍未准入、未启动C仿真，已在调度锁内核实后暂时暂停，防止W32释放时先启动轻任务而占据预算、拖后C18。独立监督会话18976和priority_light_waiters.json保证C18完成或监督退出时自动恢复这两项。原95744监督继续管理四项重任务等待进程；当前只有W32实际运行工具。此为队列优先级调整，无新增实验或改变原计划。

- 2026-10-12T11:44 UTC 用户要求优先C18：W32在11:40UTC已进入Vivado综合，保留其正在执行的工作；C18获得下一个重任务槽，package/综合报告/布线报告连续优先。用exp/priority_waiters.py在调度锁内确认F50/F51/W31/W30未准入后暂停其Python等待进程（不是工具），C18结束或监督进程退出后自动SIGCONT恢复。4项安全/恢复测试通过，远程监督会话95744已实测开始。C16/C17轻任务仍受预算限制；F52路径导出顺延至C18之后。实验计划和验收门槛不变，无新增失败或重跑。

- 2026-10-12T11:40 UTC F52：独立4.5ns布线完成且route_feasible=true，WNS+0.072/TNS0/WHS+0.032，644DSP/43468LUT/89030FF/109BRAM18K/URAM0，无未布线网络。关联同父设计F43逐位及换参数RTL558758/558787cycles，得到IP级2.514411ms，比W22快9.090909%；不是板端实测。44.274936工具分钟、最低可用2.301548GiB、进程树峰值12.214828GiB，保留原F49内存失败。五条checkpoint路径待唯一重槽空闲后导出。

- 2026-10-12T11:02 UTC C15: 单重任务仍在布线阶段触发内存保护（0.433784GiB，exit-15），没有最终布线/时序/资源结论。诊断为生成驱动的综合报告open_run保留父进程设计，另起实现子进程导致数据库内存叠加。自行决定新ID补跑：综合与报告后退出，第二Vivado进程重开project.xpr做原实现与报告，累计3小时且不改数值/布线门槛、不改原工作区或swap。C16/C17现在建设并跑13图/HLS；ROM仍待实际物理证据决定。C15 OOM1→2涵盖先前W23的实际OOM，不能重复归因成C15的新内核杀进程。

- 2026-10-12T10:43 UTC 用户更新决定（已授权执行）：F48作为新T8主线基础，原2%差30周期只保留诊断；W28按单边上限564345接受变快的549438周期，原fail、±1%计划和报告不改，追加用户授权元数据后启动W30。并行改为最多一个重任务，轻任务按13GiB登记预算及2GiB可用余量准入；当前C15保持既有0.5GiB保护，避免运行中改计划。C15结束后实施T8窗口16+FRP和T4窗口32两条独立组合；T4 ROM依据实际布线压力再决定。本条明确替代下面较早的门槛与两重任务决策。

- 2026-10-12T10:22 UTC W23: 实际同时运行两项实现时，21:19:41本地/10:19:41UTC内核杀掉Vivado77025，anon-RSS5946660KiB，exit137，OOM1→2。调度按原规则自动置serial_after_oom=true、实现登记15GiB（仍仅作观察），C15继续，后续硬件串行回退；不擅自重新启用会重复OOM的并行、不改swap。另立W32保留同一RTL、4.5ns、Performance_Explore、综合1/布局布线4线程补跑。完整待跑仍6项，当前估计5–7小时，条件时钟探针另计。规则及保护未放宽。

- 2026-10-12T10:18 UTC F49/W29: 两次独立实现均被实际可用内存0.5GiB保护终止，分别为0.382919/0.466442GiB，exit-15，OOM计数均1→1；不是RTL、时序或FPGA资源不可行。自行决定保留失败并以F52/W31新ID补跑，继续用户授权的两项并行及实际内存监测，不恢复预留预算拦截、不改swap。若同一方向反复内存失败达到45分钟问题上限，记录后先完成其他方向，再依据实际空槽安排重试。

- 2026-10-12T10:18 UTC F48: windowFIFO16逐位PASS，实测535771周期比F97少22987（4.113943%），但严格WS-D上限535741仍差30周期，目标未达。自行决定对最快已测FIFO候选另立F51做5ns独立实现；不放宽2%门槛。F51已冻结计划中的条件收益百分比存在算术勘误，正确为3.145399568%，在持久解读说明，保留原计划指纹。

- 2026-10-12T09:07 UTC W28: FRP 两帧数值与换参数检查均 PASS，实测549438周期比F97少9320（约1.668%）；超出预先提交的±1%门槛553171..564345，按原规则记fail，W30不启动。原计划和全部RTL/FIFO证据保留；明日复核是否另立新实验评估更快FRP，不改本次门槛或历史状态。C14已逐位PASS，300632latency/300661interval；其前置条件满足，C15独立5ns布线已排队。

- 2026-10-12T07:05 UTC 用户明确授权覆盖原预留预算规则：“我觉得不用担心，直接干进去，同时跑两项”。06:58:29 UTC F46 已在 F43 仍运行时准入，两项分别验证 rasterFIFO 与 Conv3 操作数寄存器；不是仅有两个排队任务。调度改为最多两项，预算保留作观察，不再用预算相加拦截第二项，实际可用内存0.5GiB以下中止最近启动项，OOM仍退回串行。W28/F48/C14/F44 的原 Python 等待进程确认未获准入、未启动 Vitis 后迁移到新调度，保留 ID、原计划 SHA256、RTL/init、配置和冻结 testbench；旧 SSH 包装器因任务未完成而退出并报缺 metrics.json，此为等待进程迁移退出，不是 RTL 失败，新进程完成后使用 collect-only 归档。原等待期全局 host_memory 会由恢复进程重新开始采样；它不是工具峰值或性能测量，工具启动后的逐任务 telemetry 单独保存。此前 W23 空闲主机也无法准入的问题已由该授权解决，无需人工重复确认。

- 2026-10-12 F45: FIFO32 的两帧 RTL 功能通过，但558758周期与F97完全相同，未达到535741周期的 WS-D 门槛。feature FIFO 写阻塞903830→801394、峰值深度4→32，消费者读阻塞仍46990，说明缓冲改变背压但未缩短整帧关键调度。详见F45 interpretation 和原始FIFO计数器；不将功能PASS当作加速成功。

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

