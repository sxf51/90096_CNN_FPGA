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

## Pending Human Decisions / 待人工决策

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

