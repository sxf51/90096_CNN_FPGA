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

## Pending Human Decisions / 待人工决策

- 2026-10-10T17:33 UTC: E014 exceeded its 45-minute simulation limit after nine Set14 images; retained as timeout. E010/E017 cover all 13 supplied images. Full all-ap_fixed representatives now use one complete butterfly inference, mandatory bit comparison to numpy and the original border metric.
- 2026-10-10T17:33 UTC: E018/E034/E035 and E012 failed compilation because Vitis prepended a relative prefix to quoted absolute include paths (`-I../../\"/home/...\"`). Restore verified unquoted paths and reject whitespace in the checkout path; corrected runs use new IDs E015/E019/E016/E044/E045. No failed synthesis is counted.
- 2026-10-10T17:33 UTC: Commit checks rejected a trailing blank line in the generated scatter template. Removed that whitespace and retained all failed-run archives in commit E034. Serial Git commit lock added to prevent independent simulation queues from racing over the index.


- Requested Windows Vitis 2026.1 environment is not available from this Mac. The existing project SSH shortcut reaches Linux Vitis 2026.1. Use that verified installation, record OS/tool version in each config and provide Windows settings-batch support in the runner. Windows reproduction remains unverified.
- The supplied Set14 directory contains 13 pairs, with `comic` absent. Evaluate every supplied image and report `image_count=13`; do not describe that as all 14 images or as complete Set14 acceptance. Any final candidate remains provisional until the missing pair is supplied and tested.
- No existing MSE threshold exists. Conservatively require float outputs bit-identical to an independently compiled unchanged golden model under the same compiler settings, while recording MSE against the supplied binary references and six-pixel border MSE separately. No original test or threshold will be altered.
- Existing `calculate_PSNR` converts model output to uint8 without clamping and may wrap outside [0,1]. Use explicitly defined normalized float MSE PSNR (`10 log10(1/MSE)`, no clipping/cropping) for the new precision gate against the same float golden; also preserve original testbench output. Metric choice must be reviewed before claiming external benchmark equivalence.

