# All Experiments: Dependencies, Changes, Effects, and Issues

[中文版](records.md)

Snapshot: `800a87a`; 153 experiments, 142 result archives, and 11 plans/preparation records.

Result records include failures, timeouts, and invalid configurations. Edges represent design, parameter, integration, and acceptance dependencies, not sequential Git clone history.

HLS time uses cycles * max(target period, HLS estimated period) / 10^6 ms. This neither establishes timing closure after uncertainty nor measures board performance. Budgets: DSP <= 1248, BRAM18K <= 288, URAM <= 64, LUT <= 81984, FF <= 163968. LUT/FF budgets are 70% of device capacity.

Ordinary synthesis rows may inherit quality from an independent precision reference; provenance is shown below. Actual per-run image coverage is recorded by image_count in the original configuration. Implementation/RTL rows preserve inherited HLS fields only in data.en.json's registry_raw; displayed results come from that verification step.

[Guide](../0004-experiment-evolution.en.md) | [Overview](overview.en.svg) | [Machine-readable data](data.en.json)

## Route Index

| Route | IDs | Diagram |
| --- | --- | --- |
| [Baseline and precision: establish what may change](#precision) | [E000](#e000) [E010](#e010) [E011](#e011) [E012](#e012) [E013](#e013) [E014](#e014) [E018](#e018) [E015](#e015) [E016](#e016) [E017](#e017) [E019](#e019) [E049](#e049) [E062](#e062) [E065](#e065) [E066](#e066) [E071](#e071) | [Graph](precision.en.svg) |
| [Compiler controls: retaining full feature maps](#compiler) | [E020](#e020) [E021](#e021) [E022](#e022) [E023](#e023) [E024](#e024) [E025](#e025) [E026](#e026) [E027](#e027) [E028](#e028) [E029](#e029) [E032](#e032) | [Graph](compiler.en.svg) |
| [Initial streaming: remove full intermediate maps](#streaming) | [E030](#e030) [E031](#e031) [E033](#e033) [E046](#e046) [E063](#e063) [E047](#e047) [E048](#e048) [E050](#e050) [E060](#e060) [E056](#e056) | [Graph](streaming.en.svg) |
| [Parameter scans: parallelism, storage, and clock](#scans) | [E034](#e034) [E035](#e035) [E044](#e044) [E045](#e045) [E057](#e057) [E058](#e058) [E059](#e059) [E036](#e036) [E037](#e037) [E038](#e038) [E039](#e039) [E040](#e040) [E064](#e064) [E067](#e067) [E041](#e041) [E042](#e042) [E043](#e043) | [Graph](scans.en.svg) |
| [Multiplier controls: explain HLS mapping](#micro) | [E051](#e051) [E052](#e052) [E053](#e053) [E054](#e054) [E055](#e055) | [Graph](micro.en.svg) |
| [A: packing from exact primitives to network cost](#packing) | [P01](#p01) [P02](#p02) [P03](#p03) [P04](#p04) [P05](#p05) [P06](#p06) [P07](#p07) [P08](#p08) [P09](#p09) [P10](#p10) [P11](#p11) [P12](#p12) [P13](#p13) [P14](#p14) [P15](#p15) [P16](#p16) | [Graph](packing.en.svg) |
| [C: gather/scatter storage and control tradeoffs](#scatter) | [G01](#g01) [G02](#g02) [G03](#g03) | [Graph](scatter.en.svg) |
| [Storage routes: dataflow, DDR probe, and fused tiles](#memory) | [S01](#s01) [S02](#s02) [S03](#s03) [S04](#s04) [S05](#s05) [S06](#s06) | [Graph](memory.en.svg) |
| [D: Winograd transforms, scheduling, and weight banks](#winograd) | [W01](#w01) [W02](#w02) [W03](#w03) [W04](#w04) [W05](#w05) [W06](#w06) [W07](#w07) [W08](#w08) [W09](#w09) [W10](#w10) [W11](#w11) [W12](#w12) [W13](#w13) [W14](#w14) [W15](#w15) [W16](#w16) [W17](#w17) [W18](#w18) | [Graph](winograd.en.svg) |
| [Combinations: can Winograd and packing savings add up?](#combination) | [C01](#c01) [C02](#c02) [C03](#c03) [C04](#c04) [C05](#c05) [C06](#c06) [C07](#c07) [C12](#c12) [C08](#c08) [C09](#c09) [C10](#c10) [C11](#c11) | [Graph](combination.en.svg) |
| [Continuing B: pipelines, windows, and loader timing](#continuous) | [F01](#f01) [F02](#f02) [F03](#f03) [F04](#f04) [F05](#f05) [F06](#f06) [F07](#f07) [F08](#f08) [F09](#f09) [F10](#f10) [F11](#f11) [F12](#f12) [F13](#f13) [F14](#f14) [F15](#f15) [F16](#f16) [F17](#f17) [F18](#f18) [F19](#f19) [F20](#f20) [F21](#f21) [F22](#f22) [F23](#f23) [F24](#f24) [F25](#f25) | [Graph](continuous.en.svg) |
| [Candidate verification: separate acceptance steps](#verification) | [E069](#e069) [E070](#e070) [F80](#f80) [F81](#f81) [F82](#f82) [F83](#f83) [F84](#f84) [F85](#f85) [F86](#f86) [F87](#f87) [F88](#f88) [F89](#f89) [F90](#f90) [F91](#f91) | [Graph](verification.en.svg) |

<a id="precision"></a>

## Baseline and precision: establish what may change

Is the original correct and able to fit? How much quality is lost by reducing bit widths?

[Evolution graph](precision.en.svg). Route evidence: [experiments/E010_precision_scan/E010.md](../../experiments/E010_precision_scan/E010.md) | [exp/prepare_mix.py](../../exp/prepare_mix.py) | [exp/prepare_mixed_arch.py](../../exp/prepare_mixed_arch.py) | [exp/model/prerequisite_ranges.py](../../exp/model/prerequisite_ranges.py).

<a id="e000"></a>

### E000: Original floating-point baseline

**Based on:** Original src/ baseline; no preceding experiment.

**Change:** Preserve src/, network structure, and replicated edges; measure correctness and synthesis scale.

**Effects and issues:** Two full intermediate maps exceed BRAM capacity. Correct C simulation does not establish device fit.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.331 ns |
| Latency / interval | 1960113853 / 1960113854 cycles |
| Registry time conversion | 19601.13853 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.158458 dB; average delta PSNR against float = 0 dB. Source: current simulation (13 images; see original archive).

Tool: Vitis 2026.1; source commit: `1f025dccb9e5fb187213ff4aea10887e617ab078`.

**Original evidence:** [E000.json](../../exp/configs/E000.json) | [E000.md](../../experiments/E000_golden_baseline/E000.md) | [config.json](../../experiments/E000_golden_baseline/config.json) | [metrics.json](../../experiments/E000_golden_baseline/metrics.json) | [csynth.rpt](../../experiments/E000_golden_baseline/csynth.rpt) | [csynth.log.txt](../../experiments/E000_golden_baseline/csynth.log.txt) | [csim.log.txt](../../experiments/E000_golden_baseline/csim.log.txt).

<a id="e010"></a>

### E010: Layer ranges and bit-width scan

**Based on:** [E000](#e000) (Numerical reference or research motivation).

**Change:** Measure ranges on 13 inputs and scan 16/12/10/8-bit weight and activation combinations.

**Effects and issues:** 10/10 bits lose about 0.0695 dB average PSNR; 8/8 bits lose about 5.18 dB. Missing comic prevents full Set14 acceptance.

**Status:** `analysis_complete` / Analysis complete; scope `analysis`; step `analysis`.

Tool: Vitis version not recorded/not applicable; source commit: `1f025dccb9e5fb187213ff4aea10887e617ab078`.

**Original evidence:** [E010.md](../../experiments/E010_precision_scan/E010.md) | [config.json](../../experiments/E010_precision_scan/config.json).

<a id="e011"></a>

### E011: Real ap_fixed: 16/16 bits

**Based on:** [E010](#e010) (Numerical reference or research motivation).

**Change:** Check the software quantization model using AMD data types, with all supplied images planned.

**Effects and issues:** C simulation fails. Subsequent retries use separate IDs; this record is not a pass.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `653125de033085b7c7288effee7f6b5962bb4706`.

**Original evidence:** [E011.json](../../exp/configs/E011.json) | [E011.md](../../experiments/E011_apfixed_w16a16/E011.md) | [config.json](../../experiments/E011_apfixed_w16a16/config.json) | [metrics.json](../../experiments/E011_apfixed_w16a16/metrics.json) | [csim.log.txt](../../experiments/E011_apfixed_w16a16/csim.log.txt).

<a id="e012"></a>

### E012: Real ap_fixed: 10/10 bits

**Based on:** [E010](#e010) (Numerical reference or research motivation).

**Change:** Validate the butterfly output of the complete fixed-point convolution network.

**Effects and issues:** This C simulation fails. Valid E017/E019 checks later establish the numerical evidence.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `3c13a0f643c80790f84b4dd4e14b99790f484cb8`.

**Original evidence:** [E012.json](../../exp/configs/E012.json) | [E012.md](../../experiments/E012_apfixed_w10a10/E012.md) | [config.json](../../experiments/E012_apfixed_w10a10/config.json) | [metrics.json](../../experiments/E012_apfixed_w10a10/metrics.json) | [csim.log.txt](../../experiments/E012_apfixed_w10a10/csim.log.txt).

<a id="e013"></a>

### E013: Real ap_fixed: 8/8 bits

**Based on:** [E010](#e010) (Numerical reference or research motivation).

**Change:** Check agreement between the quantization model and actual fixed-point arithmetic despite the failed quality gate.

**Effects and issues:** Arithmetic agreement does not imply acceptable quality; the all-8-bit design remains rejected.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=0.002759333288601273; six-pixel border MSE=0.0016186038119685043. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `688168ce38d521d78f4db262d66d842c12a1b4af`.

**Original evidence:** [E013.json](../../exp/configs/E013.json) | [E013.md](../../experiments/E013_apfixed_w8a8/E013.md) | [config.json](../../experiments/E013_apfixed_w8a8/config.json) | [metrics.json](../../experiments/E013_apfixed_w8a8/metrics.json) | [csim.log.txt](../../experiments/E013_apfixed_w8a8/csim.log.txt).

<a id="e014"></a>

### E014: 16/16-bit full-dataset retry

**Based on:** [E011](#e011) (Retry after a fix).

**Change:** Retry complete ap_fixed simulation across the supplied images.

**Effects and issues:** Only some images finish within 45 minutes. Retain the timeout; do not claim a full-dataset pass.

**Status:** `timeout` / Timed out; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `ede43ae07ffde49141ed329dfb8cd4f9267fe9c5`.

**Original evidence:** [E014.json](../../exp/configs/E014.json) | [E014.md](../../experiments/E014_apfixed_w16a16/E014.md) | [config.json](../../experiments/E014_apfixed_w16a16/config.json) | [metrics.json](../../experiments/E014_apfixed_w16a16/metrics.json) | [csim.log.txt](../../experiments/E014_apfixed_w16a16/csim.log.txt).

<a id="e018"></a>

### E018: 16/16-bit single-image control

**Based on:** [E014](#e014) (Retry after a fix).

**Change:** Limit complete ap_fixed arithmetic checks to butterfly; retain E010 as the separate multi-image quality evaluation.

**Effects and issues:** Compilation/simulation fails in this attempt; E015 retries it.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `3c13a0f643c80790f84b4dd4e14b99790f484cb8`.

**Original evidence:** [E018.json](../../exp/configs/E018.json) | [E018.md](../../experiments/E018_apfixed_w16a16_single/E018.md) | [config.json](../../experiments/E018_apfixed_w16a16_single/config.json) | [metrics.json](../../experiments/E018_apfixed_w16a16_single/metrics.json) | [csim.log.txt](../../experiments/E018_apfixed_w16a16_single/csim.log.txt).

<a id="e015"></a>

### E015: Valid 16/16-bit single-image retry

**Based on:** [E018](#e018) (Retry after a fix).

**Change:** Fix run configuration and validate complete ap_fixed butterfly arithmetic.

**Effects and issues:** The pass covers a single-image arithmetic check, not an actual 13-image full-ap_fixed run.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.211354436427195e-08; six-pixel border MSE=7.1054134342970225e-09. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `688168ce38d521d78f4db262d66d842c12a1b4af`.

**Original evidence:** [E015.json](../../exp/configs/E015.json) | [E015.md](../../experiments/E015_apfixed_w16a16_single_retry/E015.md) | [config.json](../../experiments/E015_apfixed_w16a16_single_retry/config.json) | [metrics.json](../../experiments/E015_apfixed_w16a16_single_retry/metrics.json) | [csim.log.txt](../../experiments/E015_apfixed_w16a16_single_retry/csim.log.txt).

<a id="e016"></a>

### E016: 8/8-bit single-image retry

**Based on:** [E013](#e013) (Retry after a fix).

**Change:** Recheck narrow arithmetic using an independent configuration.

**Effects and issues:** The quality failure still applies; the retry does not relax the PSNR gate.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=0.002759333288601273; six-pixel border MSE=0.0016186038119685043. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `200a5bebe17203a1d9c71f3445d325b7d6d166cf`.

**Original evidence:** [E016.json](../../exp/configs/E016.json) | [E016.md](../../experiments/E016_apfixed_w8a8_retry/E016.md) | [config.json](../../experiments/E016_apfixed_w8a8_retry/config.json) | [metrics.json](../../experiments/E016_apfixed_w8a8_retry/metrics.json) | [csim.log.txt](../../experiments/E016_apfixed_w8a8_retry/csim.log.txt).

<a id="e017"></a>

### E017: 10-bit boundaries and integer reference

**Based on:** [E010](#e010) (Numerical reference or research motivation).

**Change:** Use real ap_fixed for input/parameter conversion and layer rounding/saturation; preserve full product and accumulation fractions in integers.

**Effects and issues:** Establish an independent precision reference across 13 images. This is numerical evidence, not a performance experiment.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: current simulation (13 images; see original archive).

Tool: Vitis 2026.1; source commit: `bece7ccf647c9625fd6661c974f7f017ee8a8aef`.

**Original evidence:** [E017.json](../../exp/configs/E017.json) | [E017.md](../../experiments/E017_apfixed_boundary_w10a10/E017.md) | [config.json](../../experiments/E017_apfixed_boundary_w10a10/config.json) | [metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json) | [csim.log.txt](../../experiments/E017_apfixed_boundary_w10a10/csim.log.txt).

<a id="e019"></a>

### E019: Complete 10/10-bit ap_fixed retry

**Based on:** [E012](#e012) (Retry after a fix); [E017](#e017) (Control experiment).

**Change:** Check the complete ap_fixed network against the independent integer reference on butterfly, bit for bit.

**Effects and issues:** Functionality passes. The hardware architecture still requires separate design and synthesis.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `688168ce38d521d78f4db262d66d842c12a1b4af`.

**Original evidence:** [E019.json](../../exp/configs/E019.json) | [E019.md](../../experiments/E019_apfixed_w10a10_retry/E019.md) | [config.json](../../experiments/E019_apfixed_w10a10_retry/config.json) | [metrics.json](../../experiments/E019_apfixed_w10a10_retry/metrics.json) | [csim.log.txt](../../experiments/E019_apfixed_w10a10_retry/csim.log.txt).

<a id="e049"></a>

### E049: Exhaustive layer-boundary rounding

**Based on:** [E017](#e017) (Numerical reference or research motivation); [E048](#e048) (Verify the same design).

**Change:** Exhaust all 25,165,824 states across three 23-bit accumulator boundaries.

**Effects and issues:** Validate ties-to-even rounding and saturation. No network latency or resource claim follows.

**Status:** `csim_pass` / C simulation passed; scope `boundary`; step `csim`.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `59f3e6d7983d89006c9014b6417f461953b79c39`.

**Original evidence:** [E049.json](../../exp/configs/E049.json) | [E049.md](../../experiments/E049_integer_boundary_exhaustive/E049.md) | [config.json](../../experiments/E049_integer_boundary_exhaustive/config.json) | [metrics.json](../../experiments/E049_integer_boundary_exhaustive/metrics.json) | [csim.log.txt](../../experiments/E049_integer_boundary_exhaustive/csim.log.txt).

<a id="e062"></a>

### E062: Layer-specific INT8 feasibility

**Based on:** [E010](#e010) (Numerical reference or research motivation); [E017](#e017) (Numerical reference or research motivation).

**Change:** Try 8-bit weights/activations one layer at a time instead of quantizing the entire network to INT8.

**Effects and issues:** Only 8-bit Conv2 weights meet the average quality gate. Actual 8-bit activations and Conv1/Conv3 weights fail.

**Status:** `analysis_complete` / Analysis complete; scope `analysis`; step `analysis`.

Tool: Vitis version not recorded/not applicable; source commit: `de1138d1c31b2e8933cef2420711c9ea1baf3bcd`.

**Original evidence:** [E062.md](../../experiments/E062_layer_int8_scan/E062.md) | [config.json](../../experiments/E062_layer_int8_scan/config.json).

<a id="e065"></a>

### E065: Conv2 8-bit-weight boundary validation

**Based on:** [E062](#e062) (Numerical reference or research motivation); [E017](#e017) (Design or parameter baseline).

**Change:** Retain 10-bit activations and validate mixed precision on 13 images with real ap_fixed boundaries.

**Effects and issues:** Average PSNR loss is about 0.07589 dB. This supplies independent evidence for combinations; comic remains missing.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.770653995278335e-05; six-pixel border MSE=1.405191888267716e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.082567 dB; average delta PSNR against float = -0.07589 dB. Source: current simulation (13 images; see original archive).

Tool: Vitis 2026.1; source commit: `04f613aecc98bb42d5023604146a03112d205523`.

**Original evidence:** [E065.json](../../exp/configs/E065.json) | [E065.md](../../experiments/E065_apfixed_mixed_conv2w8/E065.md) | [config.json](../../experiments/E065_apfixed_mixed_conv2w8/config.json) | [metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json) | [csim.log.txt](../../experiments/E065_apfixed_mixed_conv2w8/csim.log.txt).

<a id="e066"></a>

### E066: Complete mixed-precision ap_fixed control

**Based on:** [E065](#e065) (Control experiment); [E019](#e019) (Design or parameter baseline).

**Change:** Validate mixed-precision butterfly output using the complete ap_fixed network.

**Effects and issues:** Bit identity establishes when E065 quality evidence can be used by architectures with the same precision.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.770653995278335e-05; six-pixel border MSE=1.405191888267716e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.082567 dB; average delta PSNR against float = -0.07589 dB. Source: [experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json).

Tool: Vitis 2026.1; source commit: `818ae9a14872f5dfec2c07a1ccb825c86542c7de`.

**Original evidence:** [E066.json](../../exp/configs/E066.json) | [E066.md](../../experiments/E066_full_apfixed_mixed_butterfly/E066.md) | [config.json](../../experiments/E066_full_apfixed_mixed_butterfly/config.json) | [metrics.json](../../experiments/E066_full_apfixed_mixed_butterfly/metrics.json) | [csim.log.txt](../../experiments/E066_full_apfixed_mixed_butterfly/csim.log.txt).

<a id="e071"></a>

### E071: Packing/Winograd prerequisite ranges

**Based on:** [E017](#e017) (Numerical reference or research motivation); [E065](#e065) (Numerical reference or research motivation).

**Change:** Measure raw integer coefficients, transform widths, packed low-field accumulation limits, and paper DSP budgets.

**Effects and issues:** Range and budget analysis is not synthesis. New weights require checking the bounds again.

**Status:** `analysis_complete` / Analysis complete; scope `parameter analysis, no HLS measurement`; step `analysis`.

Tool: Vitis version not recorded/not applicable; source commit: `ff3804751b8a6f726aeda110ba87a1474717152b`.

**Original evidence:** [E071.md](../../experiments/E071_architecture_prerequisite_ranges/E071.md) | [config.json](../../experiments/E071_architecture_prerequisite_ranges/config.json) | [metrics.json](../../experiments/E071_architecture_prerequisite_ranges/metrics.json).

<a id="compiler"></a>

## Compiler controls: retaining full feature maps

Can clock, pipeline directives, partitioning, or data types alone make the original organization feasible?

[Evolution graph](compiler.en.svg). Route evidence: [experiments/STAGE2.md](../../experiments/STAGE2.md) | [exp/prepare_auto.py](../../exp/prepare_auto.py) | [exp/retry.py](../../exp/retry.py).

<a id="e020"></a>

### E020: Default automatic optimization, 10 ns

**Based on:** [E000](#e000) (Design or parameter baseline).

**Change:** Copy the original and add loop labels without changing computation or full-map storage.

**Effects and issues:** Latency and BRAM scale remain close to the original baseline.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.331 ns |
| Latency / interval | 1960113853 / 1960113854 cycles |
| Registry time conversion | 19601.13853 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `1f025dccb9e5fb187213ff4aea10887e617ab078`.

**Original evidence:** [E020.json](../../exp/configs/E020.json) | [E020.md](../../experiments/E020_auto_default_10ns/E020.md) | [config.json](../../experiments/E020_auto_default_10ns/config.json) | [metrics.json](../../experiments/E020_auto_default_10ns/metrics.json) | [csynth.rpt](../../experiments/E020_auto_default_10ns/csynth.rpt) | [csynth.log.txt](../../experiments/E020_auto_default_10ns/csynth.log.txt) | [csim.log.txt](../../experiments/E020_auto_default_10ns/csim.log.txt).

<a id="e021"></a>

### E021: Default automatic optimization, 4 ns

**Based on:** [E020](#e020) (Design or parameter baseline).

**Change:** Tighten only the target period and inspect default scheduling changes.

**Effects and issues:** Full intermediate maps still do not fit. A clock target is not an implementation result.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 2.913 ns |
| Latency / interval | 4294771851 / 4294771852 cycles |
| Registry time conversion | 17179.087404 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9997 / 9596 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `6df111ca1bacf266ef91c7df7ffb7f44e81e853c`.

**Original evidence:** [E021.json](../../exp/configs/E021.json) | [E021.md](../../experiments/E021_auto_default_4ns/E021.md) | [config.json](../../experiments/E021_auto_default_4ns/config.json) | [metrics.json](../../experiments/E021_auto_default_4ns/metrics.json) | [csynth.rpt](../../experiments/E021_auto_default_4ns/csynth.rpt) | [csynth.log.txt](../../experiments/E021_auto_default_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/E021_auto_default_4ns/csim.log.txt).

<a id="e022"></a>

### E022: Disable automatic pipelining

**Based on:** [E020](#e020) (Design or parameter baseline).

**Change:** Measure whether default pipeline behavior helps.

**Effects and issues:** Resource issues persist and latency increases.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.016 ns |
| Latency / interval | 4482223011 / 4482223012 cycles |
| Registry time conversion | 44822.23011 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 5 / 11064 / 0 |
| LUT / FF | 2217 / 1267 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `7c7c1a1888f171530bf36fd618e7ae936f42071b`.

**Original evidence:** [E022.json](../../exp/configs/E022.json) | [E022.md](../../experiments/E022_auto_pipeline_off/E022.md) | [config.json](../../experiments/E022_auto_pipeline_off/config.json) | [metrics.json](../../experiments/E022_auto_pipeline_off/metrics.json) | [csynth.rpt](../../experiments/E022_auto_pipeline_off/csynth.rpt) | [csynth.log.txt](../../experiments/E022_auto_pipeline_off/csynth.log.txt) | [csim.log.txt](../../experiments/E022_auto_pipeline_off/csim.log.txt).

<a id="e023"></a>

### E023: Inner-loop pipeline: invalid configuration

**Based on:** [E020](#e020) (Design or parameter baseline).

**Change:** Attempt to pipeline the innermost MAC loops through configuration.

**Effects and issues:** The tool skips the syn.directive key; the result does not measure the intended directive.

**Status:** `invalid_config` / Invalid configuration; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; II target missed; Invalid configuration.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.331 ns |
| Latency / interval | 1960113853 / 1960113854 cycles |
| Registry time conversion | 19601.13853 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| Checked II targets | Missed |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `ede43ae07ffde49141ed329dfb8cd4f9267fe9c5`.

**Original evidence:** [E023.json](../../exp/configs/E023.json) | [E023.md](../../experiments/E023_auto_inner_pipeline/E023.md) | [config.json](../../experiments/E023_auto_inner_pipeline/config.json) | [metrics.json](../../experiments/E023_auto_inner_pipeline/metrics.json) | [csynth.rpt](../../experiments/E023_auto_inner_pipeline/csynth.rpt) | [csynth.log.txt](../../experiments/E023_auto_inner_pipeline/csynth.log.txt) | [csim.log.txt](../../experiments/E023_auto_inner_pipeline/csim.log.txt).

<a id="e024"></a>

### E024: Pixel-loop pipeline: invalid configuration

**Based on:** [E020](#e020) (Design or parameter baseline).

**Change:** Attempt to pipeline the outer pixel loops.

**Effects and issues:** The configuration key is invalid. E029 is the subsequent valid control for this idea.

**Status:** `invalid_config` / Invalid configuration; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; II target missed; Invalid configuration.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.331 ns |
| Latency / interval | 1960113853 / 1960113854 cycles |
| Registry time conversion | 19601.13853 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| Checked II targets | Missed |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `9cbadb26fb00c6312eb4997cb8679f4ec6c191d0`.

**Original evidence:** [E024.json](../../exp/configs/E024.json) | [E024.md](../../experiments/E024_auto_pixel_pipeline/E024.md) | [config.json](../../experiments/E024_auto_pixel_pipeline/config.json) | [metrics.json](../../experiments/E024_auto_pixel_pipeline/metrics.json) | [csynth.rpt](../../experiments/E024_auto_pixel_pipeline/csynth.rpt) | [csynth.log.txt](../../experiments/E024_auto_pixel_pipeline/csynth.log.txt) | [csim.log.txt](../../experiments/E024_auto_pixel_pipeline/csim.log.txt).

<a id="e025"></a>

### E025: Array partition: invalid configuration

**Based on:** [E020](#e020) (Design or parameter baseline).

**Change:** Attempt to improve scheduling by adding array ports.

**Effects and issues:** The key is invalid; E032 corrects it.

**Status:** `invalid_config` / Invalid configuration; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; II target missed; Invalid configuration.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.331 ns |
| Latency / interval | 1960113853 / 1960113854 cycles |
| Registry time conversion | 19601.13853 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| Checked II targets | Missed |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `659a2dc83df568ba89ae85a83f8a86909663322b`.

**Original evidence:** [E025.json](../../exp/configs/E025.json) | [E025.md](../../experiments/E025_auto_partition/E025.md) | [config.json](../../experiments/E025_auto_partition/config.json) | [metrics.json](../../experiments/E025_auto_partition/metrics.json) | [csynth.rpt](../../experiments/E025_auto_partition/csynth.rpt) | [csynth.log.txt](../../experiments/E025_auto_partition/csynth.log.txt) | [csim.log.txt](../../experiments/E025_auto_partition/csim.log.txt).

<a id="e026"></a>

### E026: Allow floating-point reassociation

**Based on:** [E020](#e020) (Design or parameter baseline).

**Change:** Investigate unsafe-math effects on floating-point accumulation scheduling.

**Effects and issues:** Network latency improves little and full intermediate maps remain too large.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.331 ns |
| Latency / interval | 1960113671 / 1960113672 cycles |
| Registry time conversion | 19601.13671 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 7624 / 3154 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `6d13dcde76f6c4c4b373663a6d6178537ffc7011`.

**Original evidence:** [E026.json](../../exp/configs/E026.json) | [E026.md](../../experiments/E026_auto_unsafe_math/E026.md) | [config.json](../../experiments/E026_auto_unsafe_math/config.json) | [metrics.json](../../experiments/E026_auto_unsafe_math/metrics.json) | [csynth.rpt](../../experiments/E026_auto_unsafe_math/csynth.rpt) | [csynth.log.txt](../../experiments/E026_auto_unsafe_math/csynth.log.txt) | [csim.log.txt](../../experiments/E026_auto_unsafe_math/csim.log.txt).

<a id="e027"></a>

### E027: Change only to 16-bit fixed point

**Based on:** [E015](#e015) (Design or parameter baseline); [E020](#e020) (Control experiment).

**Change:** Retain the full-map architecture and measure changing data types alone.

**Effects and issues:** Storage decreases but still greatly exceeds capacity; LUTs also exceed the budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K/LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.177 ns |
| Latency / interval | 391256088 / 391256089 cycles |
| Registry time conversion | 3912.56088 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 66 / 5822 / 0 |
| LUT / FF | 137322 / 8096 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.211354436427195e-08; six-pixel border MSE=7.1054134342970225e-09. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `6dce2c2e7283d210156492d1c66dbda48f2c42c7`.

**Original evidence:** [E027.json](../../exp/configs/E027.json) | [E027.md](../../experiments/E027_auto_fixed16/E027.md) | [config.json](../../experiments/E027_auto_fixed16/config.json) | [metrics.json](../../experiments/E027_auto_fixed16/metrics.json) | [csynth.rpt](../../experiments/E027_auto_fixed16/csynth.rpt) | [csynth.log.txt](../../experiments/E027_auto_fixed16/csynth.log.txt) | [csim.log.txt](../../experiments/E027_auto_fixed16/csim.log.txt).

<a id="e028"></a>

### E028: Valid inner-loop pipeline retry

**Based on:** [E023](#e023) (Retry after a fix).

**Change:** Correct the directive key and measure actual innermost pipelining.

**Effects and issues:** Floating-point recurrence and full-map storage still limit the design.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 26.707 ns |
| Latency / interval | 455695454 / 455695455 cycles |
| Registry time conversion | 12170.25848998 ms (frame scope; converted at 26.707 ns) |
| DSP / BRAM18K / URAM | 12 / 11064 / 0 |
| LUT / FF | 9914 / 8948 |
| Checked II targets | Met |

HLS 200-871: logic budget 10 - 2.7 = 7.3 ns; maximum warned path estimate 26.707 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `6dce2c2e7283d210156492d1c66dbda48f2c42c7`.

**Original evidence:** [E028.json](../../exp/configs/E028.json) | [E028.md](../../experiments/E028_auto_inner_pipeline_validcfg/E028.md) | [config.json](../../experiments/E028_auto_inner_pipeline_validcfg/config.json) | [metrics.json](../../experiments/E028_auto_inner_pipeline_validcfg/metrics.json) | [csynth.rpt](../../experiments/E028_auto_inner_pipeline_validcfg/csynth.rpt) | [csynth.log.txt](../../experiments/E028_auto_inner_pipeline_validcfg/csynth.log.txt) | [csim.log.txt](../../experiments/E028_auto_inner_pipeline_validcfg/csim.log.txt).

<a id="e029"></a>

### E029: Valid pixel-loop pipeline retry

**Based on:** [E024](#e024) (Retry after a fix).

**Change:** Correct the key and apply the intended pixel-loop pipeline directives.

**Effects and issues:** The fastest valid float control still needs about 11,114 BRAM18K blocks, and not all II targets are met.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; II target missed.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.624 ns |
| Latency / interval | 381121723 / 381121724 cycles |
| Registry time conversion | 3811.21723 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 320 / 11114 / 0 |
| LUT / FF | 80812 / 123203 |
| Checked II targets | Missed |

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `bece7ccf647c9625fd6661c974f7f017ee8a8aef`.

**Original evidence:** [E029.json](../../exp/configs/E029.json) | [E029.md](../../experiments/E029_auto_pixel_pipeline_validcfg/E029.md) | [config.json](../../experiments/E029_auto_pixel_pipeline_validcfg/config.json) | [metrics.json](../../experiments/E029_auto_pixel_pipeline_validcfg/metrics.json) | [csynth.rpt](../../experiments/E029_auto_pixel_pipeline_validcfg/csynth.rpt) | [csynth.log.txt](../../experiments/E029_auto_pixel_pipeline_validcfg/csynth.log.txt) | [csim.log.txt](../../experiments/E029_auto_pixel_pipeline_validcfg/csim.log.txt).

<a id="e032"></a>

### E032: Valid array-partition retry

**Based on:** [E025](#e025) (Retry after a fix).

**Change:** Correct partition directives and inspect memory-port and pipeline effects.

**Effects and issues:** Retaining complete intermediate maps leaves the resource problem unresolved.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 26.707 ns |
| Latency / interval | 455695454 / 455695455 cycles |
| Registry time conversion | 12170.25848998 ms (frame scope; converted at 26.707 ns) |
| DSP / BRAM18K / URAM | 12 / 11096 / 0 |
| LUT / FF | 8585 / 10378 |
| Checked II targets | Met |

HLS 200-871: logic budget 10 - 2.7 = 7.3 ns; maximum warned path estimate 26.707 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `815b1da044d42b8d4383d1d7a499f2a57981b8dd`.

**Original evidence:** [E032.json](../../exp/configs/E032.json) | [E032.md](../../experiments/E032_auto_partition_validcfg/E032.md) | [config.json](../../experiments/E032_auto_partition_validcfg/config.json) | [metrics.json](../../experiments/E032_auto_partition_validcfg/metrics.json) | [csynth.rpt](../../experiments/E032_auto_partition_validcfg/csynth.rpt) | [csynth.log.txt](../../experiments/E032_auto_partition_validcfg/csynth.log.txt) | [csim.log.txt](../../experiments/E032_auto_partition_validcfg/csim.log.txt).

<a id="streaming"></a>

## Initial streaming: remove full intermediate maps

After line buffers and streams work, why do LUT use and timing remain limiting?

[Evolution graph](streaming.en.svg). Route evidence: [experiments/STAGE3.md](../../experiments/STAGE3.md) | [exp/prepare_int.py](../../exp/prepare_int.py) | [exp/prepare_dsp.py](../../exp/prepare_dsp.py) | [exp/prepare_wrap.py](../../exp/prepare_wrap.py).

<a id="e030"></a>

### E030: Floating-point streaming functional control

**Based on:** [E000](#e000) (Design or parameter baseline).

**Change:** Connect read/pad/Conv1/Conv2/pad/Conv3/write by streams and reuse windows in line buffers.

**Effects and issues:** First establish full-image and edge equivalence. This record contains C simulation only.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=3.1660971422452726e-14; six-pixel border MSE=2.1182492395563412e-14. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `6d13dcde76f6c4c4b373663a6d6178537ffc7011`.

**Original evidence:** [E030.json](../../exp/configs/E030.json) | [E030.md](../../experiments/E030_dataflow_float/E030.md) | [config.json](../../experiments/E030_dataflow_float/config.json) | [metrics.json](../../experiments/E030_dataflow_float/metrics.json) | [csim.log.txt](../../experiments/E030_dataflow_float/csim.log.txt).

<a id="e031"></a>

### E031: 10-bit streaming, T32

**Based on:** [E030](#e030) (Design or parameter baseline); [E017](#e017) (Numerical reference or research motivation).

**Change:** Convert the validated stream organization to 10-bit fixed point and T=32 partial unrolling.

**Effects and issues:** BRAM18K falls to 168, but multiplier/type logic maps heavily to LUTs, failing resource and estimated timing goals.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 31.822 ns |
| Latency / interval | 3882221 / 3882222 cycles |
| Registry time conversion | 123.54003666 ms (frame scope; converted at 31.822 ns) |
| DSP / BRAM18K / URAM | 9 / 168 / 0 |
| LUT / FF | 136868 / 149111 |
| Checked II targets | Met |

HLS 200-871: logic budget 10 - 2.7 = 7.3 ns; maximum warned path estimate 31.822 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `3c13a0f643c80790f84b4dd4e14b99790f484cb8`.

**Original evidence:** [E031.json](../../exp/configs/E031.json) | [E031.md](../../experiments/E031_dataflow_fixed_T32/E031.md) | [config.json](../../experiments/E031_dataflow_fixed_T32/config.json) | [metrics.json](../../experiments/E031_dataflow_fixed_T32/metrics.json) | [csynth.rpt](../../experiments/E031_dataflow_fixed_T32/csynth.rpt) | [csynth.log.txt](../../experiments/E031_dataflow_fixed_T32/csynth.log.txt) | [csim.log.txt](../../experiments/E031_dataflow_fixed_T32/csim.log.txt).

<a id="e033"></a>

### E033: T32 single-image synthesis control

**Based on:** [E031](#e031) (Design or parameter baseline).

**Change:** Shorten the C-simulation workload while retaining the same streaming hardware organization.

**Effects and issues:** Again obtain 136,868 LUTs and a 31.822 ns estimate. Inner II=1 does not establish high network throughput.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 31.822 ns |
| Latency / interval | 3882221 / 3882222 cycles |
| Registry time conversion | 123.54003666 ms (frame scope; converted at 31.822 ns) |
| DSP / BRAM18K / URAM | 9 / 168 / 0 |
| LUT / FF | 136868 / 149111 |
| Checked II targets | Met |

HLS 200-871: logic budget 10 - 2.7 = 7.3 ns; maximum warned path estimate 31.822 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `3c13a0f643c80790f84b4dd4e14b99790f484cb8`.

**Original evidence:** [E033.json](../../exp/configs/E033.json) | [E033.md](../../experiments/E033_dataflow_fixed_T32_single/E033.md) | [config.json](../../experiments/E033_dataflow_fixed_T32_single/config.json) | [metrics.json](../../experiments/E033_dataflow_fixed_T32_single/metrics.json) | [csynth.rpt](../../experiments/E033_dataflow_fixed_T32_single/csynth.rpt) | [csynth.log.txt](../../experiments/E033_dataflow_fixed_T32_single/csynth.log.txt) | [csim.log.txt](../../experiments/E033_dataflow_fixed_T32_single/csim.log.txt).

<a id="e046"></a>

### E046: Remove redundant accumulator saturation

**Based on:** [E033](#e033) (Design or parameter baseline); [E010](#e010) (Numerical reference or research motivation).

**Change:** Use archived range bounds to retain complete product precision and quantize only at layer boundaries.

**Effects and issues:** An existing synthesis lock blocks this attempt; it is not a hardware measurement.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `200a5bebe17203a1d9c71f3445d325b7d6d166cf`.

**Original evidence:** [E046.json](../../exp/configs/E046.json) | [E046.md](../../experiments/E046_dataflow_wrap_T32/E046.md) | [config.json](../../experiments/E046_dataflow_wrap_T32/config.json) | [metrics.json](../../experiments/E046_dataflow_wrap_T32/metrics.json) | [csim.log.txt](../../experiments/E046_dataflow_wrap_T32/csim.log.txt).

<a id="e063"></a>

### E063: Accumulator-control retry

**Based on:** [E046](#e046) (Retry after a fix).

**Change:** Measure removal of redundant saturation in a separate run.

**Effects and issues:** DSP mapping changes but LUTs remain above budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2913855 / 2913856 cycles |
| Registry time conversion | 29.13855 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 148 / 168 / 0 |
| LUT / FF | 95727 / 132430 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `6d7039b83f39b75f9b752a1b650b2e441b4180f3`.

**Original evidence:** [E063.json](../../exp/configs/E063.json) | [E063.md](../../experiments/E063_dataflow_wrap_T32_retry/E063.md) | [config.json](../../experiments/E063_dataflow_wrap_T32_retry/config.json) | [metrics.json](../../experiments/E063_dataflow_wrap_T32_retry/metrics.json) | [csynth.rpt](../../experiments/E063_dataflow_wrap_T32_retry/csynth.rpt) | [csynth.log.txt](../../experiments/E063_dataflow_wrap_T32_retry/csynth.log.txt) | [csim.log.txt](../../experiments/E063_dataflow_wrap_T32_retry/csim.log.txt).

<a id="e047"></a>

### E047: Explicit DSP multiplier binding

**Based on:** [E033](#e033) (Design or parameter baseline).

**Change:** Bind the T32 design's 162/64/25 parallel multipliers to DSPs.

**Effects and issues:** Estimated latency decreases substantially, but registered weights and selectors still exceed the LUT budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2913855 / 2913856 cycles |
| Registry time conversion | 29.13855 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 251 / 168 / 0 |
| LUT / FF | 89341 / 132430 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `af351bab36dcd4f95babc0f427342112b6c36bf2`.

**Original evidence:** [E047.json](../../exp/configs/E047.json) | [E047.md](../../experiments/E047_dataflow_dsp_T32/E047.md) | [config.json](../../experiments/E047_dataflow_dsp_T32/config.json) | [metrics.json](../../experiments/E047_dataflow_dsp_T32/metrics.json) | [csynth.rpt](../../experiments/E047_dataflow_dsp_T32/csynth.rpt) | [csynth.log.txt](../../experiments/E047_dataflow_dsp_T32/csynth.log.txt) | [csim.log.txt](../../experiments/E047_dataflow_dsp_T32/csim.log.txt).

<a id="e048"></a>

### E048: Integer carriers for fixed-point arithmetic

**Based on:** [E047](#e047) (Design or parameter baseline); [E017](#e017) (Numerical reference or research motivation).

**Change:** Store fixed-point raw bits in integers and implement layer rounding explicitly without changing numerical boundaries.

**Effects and issues:** The simplified representation still uses about 89,304 LUTs. Banking and selectors need further work.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2913855 / 2913856 cycles |
| Registry time conversion | 29.13855 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 89304 / 132635 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `0ceab1f21db6296227e5a524e37028e6ef2ffbc8`.

**Original evidence:** [E048.json](../../exp/configs/E048.json) | [E048.md](../../experiments/E048_dataflow_integer_T32/E048.md) | [config.json](../../experiments/E048_dataflow_integer_T32/config.json) | [metrics.json](../../experiments/E048_dataflow_integer_T32/metrics.json) | [csynth.rpt](../../experiments/E048_dataflow_integer_T32/csynth.rpt) | [csynth.log.txt](../../experiments/E048_dataflow_integer_T32/csynth.log.txt) | [csim.log.txt](../../experiments/E048_dataflow_integer_T32/csim.log.txt).

<a id="e050"></a>

### E050: Initial Conv3 scatter

**Based on:** [E031](#e031) (Design or parameter baseline).

**Change:** Reduce across channels before buffering partial sums on the side with fewer channels.

**Effects and issues:** BRAM decreases, but initial fixed-point/mapping logic exceeds the LUT budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 3882221 / 3882222 cycles |
| Registry time conversion | 38.82221 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 34 / 137 / 0 |
| LUT / FF | 127718 / 128434 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `f5990c904b80dc8aac23150897e5eda2375ba798`.

**Original evidence:** [E050.json](../../exp/configs/E050.json) | [E050.md](../../experiments/E050_scatter_T32/E050.md) | [config.json](../../experiments/E050_scatter_T32/config.json) | [metrics.json](../../experiments/E050_scatter_T32/metrics.json) | [csynth.rpt](../../experiments/E050_scatter_T32/csynth.rpt) | [csynth.log.txt](../../experiments/E050_scatter_T32/csynth.log.txt) | [csim.log.txt](../../experiments/E050_scatter_T32/csim.log.txt).

<a id="e060"></a>

### E060: Integer Conv3 scatter

**Based on:** [E048](#e048) (Design or parameter baseline); [E050](#e050) (Numerical reference or research motivation).

**Change:** Retain explicit padding and use 32-bit partial sums with rotating line buffers.

**Effects and issues:** Resources can meet the budget, but control and extra work make it slower than gather.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 3770206 / 3770207 cycles |
| Registry time conversion | 37.70206 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 137 / 0 |
| LUT / FF | 39135 / 24841 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `e25bcc9245725a41b041bb154138da29014df358`.

**Original evidence:** [E060.json](../../exp/configs/E060.json) | [E060.md](../../experiments/E060_scatter_integer_T32/E060.md) | [config.json](../../experiments/E060_scatter_integer_T32/config.json) | [metrics.json](../../experiments/E060_scatter_integer_T32/metrics.json) | [csynth.rpt](../../experiments/E060_scatter_integer_T32/csynth.rpt) | [csynth.log.txt](../../experiments/E060_scatter_integer_T32/csynth.log.txt) | [csim.log.txt](../../experiments/E060_scatter_integer_T32/csim.log.txt).

<a id="e056"></a>

### E056: T4 mixed DSP/fabric computation

**Based on:** [E048](#e048) (Design or parameter baseline); [E053](#e053) (Numerical reference or research motivation).

**Change:** Move some Conv1/Conv3 multipliers into fabric when DSP capacity limits greater parallelism.

**Effects and issues:** The paper DSP budget fits, but 237,025 LUTs do not. DSP count alone cannot select a candidate.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 1046292 / 1046293 cycles |
| Registry time conversion | 10.46292 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 1160 / 168 / 0 |
| LUT / FF | 237025 / 120073 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `fcd3ba401b3ba37f18e450be506eca80efa62521`.

**Original evidence:** [E056.json](../../exp/configs/E056.json) | [E056.md](../../experiments/E056_mixed_T4_feasibility/E056.md) | [config.json](../../experiments/E056_mixed_T4_feasibility/config.json) | [metrics.json](../../experiments/E056_mixed_T4_feasibility/metrics.json) | [csynth.rpt](../../experiments/E056_mixed_T4_feasibility/csynth.rpt) | [csynth.log.txt](../../experiments/E056_mixed_T4_feasibility/csynth.log.txt) | [csim.log.txt](../../experiments/E056_mixed_T4_feasibility/csim.log.txt).

<a id="scans"></a>

## Parameter scans: parallelism, storage, and clock

With precision fixed, what do T, unroll direction, weight banks, and target period change?

[Evolution graph](scans.en.svg). Route evidence: [exp/prepare_scan.py](../../exp/prepare_scan.py) | [exp/prepare_followup.py](../../exp/prepare_followup.py) | [exp/finish_coordinates.py](../../exp/finish_coordinates.py) | [experiments/SUMMARY.md](../../experiments/SUMMARY.md).

<a id="e034"></a>

### E034: Initial T16 scan

**Based on:** [E033](#e033) (Design or parameter baseline).

**Change:** Reduce computation rounds per pixel from 32 to 16, increasing parallel multipliers.

**Effects and issues:** C simulation fails; E044 retries the design.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `3c13a0f643c80790f84b4dd4e14b99790f484cb8`.

**Original evidence:** [E034.json](../../exp/configs/E034.json) | [E034.md](../../experiments/E034_scan_T_T16_E034/E034.md) | [config.json](../../experiments/E034_scan_T_T16_E034/config.json) | [metrics.json](../../experiments/E034_scan_T_T16_E034/metrics.json) | [csim.log.txt](../../experiments/E034_scan_T_T16_E034/csim.log.txt).

<a id="e035"></a>

### E035: Initial T8 scan

**Based on:** [E033](#e033) (Design or parameter baseline).

**Change:** Further reduce rounds per pixel to 8.

**Effects and issues:** C simulation fails; E045 retries it.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `3c13a0f643c80790f84b4dd4e14b99790f484cb8`.

**Original evidence:** [E035.json](../../exp/configs/E035.json) | [E035.md](../../experiments/E035_scan_T_T8_E035/E035.md) | [config.json](../../experiments/E035_scan_T_T8_E035/config.json) | [metrics.json](../../experiments/E035_scan_T_T8_E035/metrics.json) | [csim.log.txt](../../experiments/E035_scan_T_T8_E035/csim.log.txt).

<a id="e044"></a>

### E044: Valid initial T16 streaming scan

**Based on:** [E034](#e034) (Retry after a fix).

**Change:** Fix simulation settings and measure the same higher-parallelism idea.

**Effects and issues:** Default arithmetic/mapping produces a 63.218 ns estimate and excessive LUTs.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 63.218 ns |
| Latency / interval | 2775517 / 2775518 cycles |
| Registry time conversion | 175.46263371 ms (frame scope; converted at 63.218 ns) |
| DSP / BRAM18K / URAM | 18 / 168 / 0 |
| LUT / FF | 167715 / 135714 |
| Checked II targets | Met |

HLS 200-871: logic budget 10 - 2.7 = 7.3 ns; maximum warned path estimate 63.218 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `688168ce38d521d78f4db262d66d842c12a1b4af`.

**Original evidence:** [E044.json](../../exp/configs/E044.json) | [E044.md](../../experiments/E044_scan_T_T16_E034_retry/E044.md) | [config.json](../../experiments/E044_scan_T_T16_E034_retry/config.json) | [metrics.json](../../experiments/E044_scan_T_T16_E034_retry/metrics.json) | [csynth.rpt](../../experiments/E044_scan_T_T16_E034_retry/csynth.rpt) | [csynth.log.txt](../../experiments/E044_scan_T_T16_E034_retry/csynth.log.txt) | [csim.log.txt](../../experiments/E044_scan_T_T16_E034_retry/csim.log.txt).

<a id="e045"></a>

### E045: Valid initial T8 streaming scan

**Based on:** [E035](#e035) (Retry after a fix).

**Change:** Run the initial T8 configuration with valid settings.

**Effects and issues:** A 126.008 ns estimate and 266,266 LUTs show that greater parallelism does not accelerate this network.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 126.008 ns |
| Latency / interval | 2222165 / 2222166 cycles |
| Registry time conversion | 280.01056732 ms (frame scope; converted at 126.008 ns) |
| DSP / BRAM18K / URAM | 36 / 168 / 0 |
| LUT / FF | 266266 / 142153 |
| Checked II targets | Met |

HLS 200-871: logic budget 10 - 2.7 = 7.3 ns; maximum warned path estimate 126.008 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `9e45f25d0fbdb3f869511fbbee66eb29322ad8ff`.

**Original evidence:** [E045.json](../../exp/configs/E045.json) | [E045.md](../../experiments/E045_scan_T_T8_E035_retry/E045.md) | [config.json](../../experiments/E045_scan_T_T8_E035_retry/config.json) | [metrics.json](../../experiments/E045_scan_T_T8_E035_retry/metrics.json) | [csynth.rpt](../../experiments/E045_scan_T_T8_E035_retry/csynth.rpt) | [csynth.log.txt](../../experiments/E045_scan_T_T8_E035_retry/csynth.log.txt) | [csim.log.txt](../../experiments/E045_scan_T_T8_E035_retry/csim.log.txt).

<a id="e057"></a>

### E057: Integer T32 with LUTRAM weight banks

**Based on:** [E048](#e048) (Design or parameter baseline).

**Change:** Replace fully partitioned weight registers with writable LUTRAM banks matched to parallel ports.

**Effects and issues:** LUTs fall to about 44,493, establishing a resource-feasible baseline for further work.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2983024 / 2983025 cycles |
| Registry time conversion | 29.83024 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 44493 / 46328 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `2eb2ea43fc8b50176c8c2558d6cb59976ade68e2`.

**Original evidence:** [E057.json](../../exp/configs/E057.json) | [E057.md](../../experiments/E057_integer_lutram_T32/E057.md) | [config.json](../../experiments/E057_integer_lutram_T32/config.json) | [metrics.json](../../experiments/E057_integer_lutram_T32/metrics.json) | [csynth.rpt](../../experiments/E057_integer_lutram_T32/csynth.rpt) | [csynth.log.txt](../../experiments/E057_integer_lutram_T32/csynth.log.txt) | [csim.log.txt](../../experiments/E057_integer_lutram_T32/csim.log.txt).

<a id="e058"></a>

### E058: Integer T16 with LUTRAM weight banks

**Based on:** [E048](#e048) (Design or parameter baseline); [E057](#e057) (Control experiment).

**Change:** Use T16 in the same integer organization to measure the parallelism/resource tradeoff.

**Effects and issues:** About 18.7632 ms; this supplies the parameter baseline for clock and unroll-direction scans.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 1876320 / 1876321 cycles |
| Registry time conversion | 18.7632 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 55212 / 57723 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c39e5bf78a69d352d763266139e6d179494582af`.

**Original evidence:** [E058.json](../../exp/configs/E058.json) | [E058.md](../../experiments/E058_integer_lutram_T16/E058.md) | [config.json](../../experiments/E058_integer_lutram_T16/config.json) | [metrics.json](../../experiments/E058_integer_lutram_T16/metrics.json) | [csynth.rpt](../../experiments/E058_integer_lutram_T16/csynth.rpt) | [csynth.log.txt](../../experiments/E058_integer_lutram_T16/csynth.log.txt) | [csim.log.txt](../../experiments/E058_integer_lutram_T16/csim.log.txt).

<a id="e059"></a>

### E059: Integer T8 with LUTRAM weight banks

**Based on:** [E048](#e048) (Design or parameter baseline); [E058](#e058) (Control experiment).

**Change:** Increase parallelism again to T8.

**Effects and issues:** 85,147 LUTs exceed the project's 70% budget despite remaining DSP capacity.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 1322968 / 1322969 cycles |
| Registry time conversion | 13.22968 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 1007 / 168 / 0 |
| LUT / FF | 85147 / 88822 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `bcdfdc89d857215f353a911a37d63190d2f2d6fd`.

**Original evidence:** [E059.json](../../exp/configs/E059.json) | [E059.md](../../experiments/E059_integer_lutram_T8/E059.md) | [config.json](../../experiments/E059_integer_lutram_T8/config.json) | [metrics.json](../../experiments/E059_integer_lutram_T8/metrics.json) | [csynth.rpt](../../experiments/E059_integer_lutram_T8/csynth.rpt) | [csynth.log.txt](../../experiments/E059_integer_lutram_T8/csynth.log.txt) | [csim.log.txt](../../experiments/E059_integer_lutram_T8/csim.log.txt).

<a id="e036"></a>

### E036: T16 Conv1 unroll direction

**Based on:** [E058](#e058) (Design or parameter baseline).

**Change:** Shift Conv1 parallelism from output channels toward kernel grouping.

**Effects and issues:** II misses its target and cycles increase. A provisional label does not imply scheduling success.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: II target missed.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 7894023 / 7894024 cycles |
| Registry time conversion | 78.94023 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 565 / 168 / 0 |
| LUT / FF | 79846 / 76416 |
| Checked II targets | Missed |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `89c375b09c54cdba279942a7659114cfb7cd620e`.

**Original evidence:** [E036.json](../../exp/configs/E036.json) | [E036.md](../../experiments/E036_scan_split_T16_E036/E036.md) | [config.json](../../experiments/E036_scan_split_T16_E036/config.json) | [metrics.json](../../experiments/E036_scan_split_T16_E036/metrics.json) | [csynth.rpt](../../experiments/E036_scan_split_T16_E036/csynth.rpt) | [csynth.log.txt](../../experiments/E036_scan_split_T16_E036/csynth.log.txt) | [csim.log.txt](../../experiments/E036_scan_split_T16_E036/csim.log.txt).

<a id="e037"></a>

### E037: T16 Conv2 unroll direction

**Based on:** [E058](#e058) (Design or parameter baseline).

**Change:** Change Conv2 channel unrolling and its relationship to memory ports.

**Effects and issues:** Latency is unchanged and LUT use increases, yielding no better tradeoff.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 1876320 / 1876321 cycles |
| Registry time conversion | 18.7632 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 60050 / 56509 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `6989ca97e7f5dcad698f0b59a5266bd2dec25496`.

**Original evidence:** [E037.json](../../exp/configs/E037.json) | [E037.md](../../experiments/E037_scan_split_T16_E037/E037.md) | [config.json](../../experiments/E037_scan_split_T16_E037/config.json) | [metrics.json](../../experiments/E037_scan_split_T16_E037/metrics.json) | [csynth.rpt](../../experiments/E037_scan_split_T16_E037/csynth.rpt) | [csynth.log.txt](../../experiments/E037_scan_split_T16_E037/csynth.log.txt) | [csim.log.txt](../../experiments/E037_scan_split_T16_E037/csim.log.txt).

<a id="e038"></a>

### E038: T16 Conv3 unroll direction

**Based on:** [E058](#e058) (Design or parameter baseline).

**Change:** Change how Conv3 parallelism splits input channels and kernel computation.

**Effects and issues:** DSPs, LUTs, and cycles all increase.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2155352 / 2155353 cycles |
| Registry time conversion | 21.55352 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 519 / 168 / 0 |
| LUT / FF | 64526 / 57346 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `aa7e3c4172caddd39fb8d2759e28152d988561b8`.

**Original evidence:** [E038.json](../../exp/configs/E038.json) | [E038.md](../../experiments/E038_scan_split_T16_E038/E038.md) | [config.json](../../experiments/E038_scan_split_T16_E038/config.json) | [metrics.json](../../experiments/E038_scan_split_T16_E038/metrics.json) | [csynth.rpt](../../experiments/E038_scan_split_T16_E038/csynth.rpt) | [csynth.log.txt](../../experiments/E038_scan_split_T16_E038/csynth.log.txt) | [csim.log.txt](../../experiments/E038_scan_split_T16_E038/csim.log.txt).

<a id="e039"></a>

### E039: DSP T32 LUTRAM control

**Based on:** [E047](#e047) (Design or parameter baseline).

**Change:** Measure LUTRAM weight banking in the explicitly DSP-bound design.

**Effects and issues:** Establish the first resource-feasible candidate. E070 separately measures physical implementation.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2983024 / 2983025 cycles |
| Registry time conversion | 29.83024 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 251 / 168 / 0 |
| LUT / FF | 44530 / 46123 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `0ceab1f21db6296227e5a524e37028e6ef2ffbc8`.

**Original evidence:** [E039.json](../../exp/configs/E039.json) | [E039.md](../../experiments/E039_scan_storage_T32_E039/E039.md) | [config.json](../../experiments/E039_scan_storage_T32_E039/config.json) | [metrics.json](../../experiments/E039_scan_storage_T32_E039/metrics.json) | [csynth.rpt](../../experiments/E039_scan_storage_T32_E039/csynth.rpt) | [csynth.log.txt](../../experiments/E039_scan_storage_T32_E039/csynth.log.txt) | [csim.log.txt](../../experiments/E039_scan_storage_T32_E039/csim.log.txt).

<a id="e040"></a>

### E040: DSP T32 BRAM weight banks

**Based on:** [E047](#e047) (Design or parameter baseline); [E039](#e039) (Control experiment).

**Change:** Map the same weight banks to BRAM.

**Effects and issues:** Many shallow banks waste capacity: 419 BRAM18K blocks exceed the device limit.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2983024 / 2983025 cycles |
| Registry time conversion | 29.83024 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 251 / 419 / 0 |
| LUT / FF | 43275 / 41136 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c765a47c2f08e143c46526a4c62707f25f4afc2c`.

**Original evidence:** [E040.json](../../exp/configs/E040.json) | [E040.md](../../experiments/E040_scan_storage_T32_E040/E040.md) | [config.json](../../experiments/E040_scan_storage_T32_E040/config.json) | [metrics.json](../../experiments/E040_scan_storage_T32_E040/metrics.json) | [csynth.rpt](../../experiments/E040_scan_storage_T32_E040/csynth.rpt) | [csynth.log.txt](../../experiments/E040_scan_storage_T32_E040/csynth.log.txt) | [csim.log.txt](../../experiments/E040_scan_storage_T32_E040/csim.log.txt).

<a id="e064"></a>

### E064: T16 fully partitioned weights

**Based on:** [E058](#e058) (Design or parameter baseline).

**Change:** Retain T16 but replace banked weights with fully partitioned registers.

**Effects and issues:** 88,306 LUTs exceed the project budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 1807151 / 1807152 cycles |
| Registry time conversion | 18.07151 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 88306 / 138588 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `66ed993d94fe3043ad8b0f3468c2059e54d55ba0`.

**Original evidence:** [E064.json](../../exp/configs/E064.json) | [E064.md](../../experiments/E064_storage_0_T16/E064.md) | [config.json](../../experiments/E064_storage_0_T16/config.json) | [metrics.json](../../experiments/E064_storage_0_T16/metrics.json) | [csynth.rpt](../../experiments/E064_storage_0_T16/csynth.rpt) | [csynth.log.txt](../../experiments/E064_storage_0_T16/csynth.log.txt) | [csim.log.txt](../../experiments/E064_storage_0_T16/csim.log.txt).

<a id="e067"></a>

### E067: T16 BRAM weight banks

**Based on:** [E058](#e058) (Design or parameter baseline).

**Change:** Retain T16 and store weights in BRAM.

**Effects and issues:** Shallow banks consume 670 BRAM18K blocks, exceeding device capacity.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 1876320 / 1876321 cycles |
| Registry time conversion | 18.7632 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 505 / 670 / 0 |
| LUT / FF | 53706 / 47716 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `780c29efa88a8b7cd00927ac5f4f27c0c28fcf36`.

**Original evidence:** [E067.json](../../exp/configs/E067.json) | [E067.md](../../experiments/E067_storage_2_T16/E067.md) | [config.json](../../experiments/E067_storage_2_T16/config.json) | [metrics.json](../../experiments/E067_storage_2_T16/metrics.json) | [csynth.rpt](../../experiments/E067_storage_2_T16/csynth.rpt) | [csynth.log.txt](../../experiments/E067_storage_2_T16/csynth.log.txt) | [csim.log.txt](../../experiments/E067_storage_2_T16/csim.log.txt).

<a id="e041"></a>

### E041: T16 at a 5 ns target

**Based on:** [E058](#e058) (Design or parameter baseline).

**Change:** Keep precision/storage fixed and inspect scheduling and resources at a tighter period.

**Effects and issues:** About 9.7275 ms estimated; the target still requires physical implementation evidence.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 5 / 3.65 ns |
| Latency / interval | 1945500 / 1945501 cycles |
| Registry time conversion | 9.7275 ms (frame scope; converted at 5 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 55553 / 59959 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `f68c3ebd3f64750454e7e296f3882dde7c55e2af`.

**Original evidence:** [E041.json](../../exp/configs/E041.json) | [E041.md](../../experiments/E041_scan_clock_T16_E041/E041.md) | [config.json](../../experiments/E041_scan_clock_T16_E041/config.json) | [metrics.json](../../experiments/E041_scan_clock_T16_E041/metrics.json) | [csynth.rpt](../../experiments/E041_scan_clock_T16_E041/csynth.rpt) | [csynth.log.txt](../../experiments/E041_scan_clock_T16_E041/csynth.log.txt) | [csim.log.txt](../../experiments/E041_scan_clock_T16_E041/csim.log.txt).

<a id="e042"></a>

### E042: T16 at a 4 ns target

**Based on:** [E058](#e058) (Design or parameter baseline); [E041](#e041) (Control experiment).

**Change:** Tighten the target period again without changing the architecture.

**Effects and issues:** About 8.0587 ms estimated; FIFO and per-pixel pipeline overhead remain.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 2014678 / 2014679 cycles |
| Registry time conversion | 8.058712 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 56007 / 62948 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `2ac67f7ea3592df0e5b5297883b3dc15cbd20deb`.

**Original evidence:** [E042.json](../../exp/configs/E042.json) | [E042.md](../../experiments/E042_scan_clock_T16_E042/E042.md) | [config.json](../../experiments/E042_scan_clock_T16_E042/config.json) | [metrics.json](../../experiments/E042_scan_clock_T16_E042/metrics.json) | [csynth.rpt](../../experiments/E042_scan_clock_T16_E042/csynth.rpt) | [csynth.log.txt](../../experiments/E042_scan_clock_T16_E042/csynth.log.txt) | [csim.log.txt](../../experiments/E042_scan_clock_T16_E042/csim.log.txt).

<a id="e043"></a>

### E043: T16 at a 3.33 ns target

**Based on:** [E058](#e058) (Design or parameter baseline); [E042](#e042) (Control experiment).

**Change:** Continue tightening the target under the same resource and precision budgets.

**Effects and issues:** First-round fastest resource-qualified estimate: about 6.9392 ms. This is not board performance.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3.33 / 3.239 ns |
| Latency / interval | 2083853 / 2083854 cycles |
| Registry time conversion | 6.93923049 ms (frame scope; converted at 3.33 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 55325 / 67025 |
| Checked II targets | Met |

HLS 200-871: logic budget 3.33 - 0.899 = 2.431 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `dc06450d75219fbf2653c931711e5fb5f4445d8f`.

**Original evidence:** [E043.json](../../exp/configs/E043.json) | [E043.md](../../experiments/E043_scan_clock_T16_E043/E043.md) | [config.json](../../experiments/E043_scan_clock_T16_E043/config.json) | [metrics.json](../../experiments/E043_scan_clock_T16_E043/metrics.json) | [csynth.rpt](../../experiments/E043_scan_clock_T16_E043/csynth.rpt) | [csynth.log.txt](../../experiments/E043_scan_clock_T16_E043/csynth.log.txt) | [csim.log.txt](../../experiments/E043_scan_clock_T16_E043/csim.log.txt).

<a id="micro"></a>

## Multiplier controls: explain HLS mapping

Do narrow multipliers map to DSPs or LUTs, and how far can these local costs be generalized?

[Evolution graph](micro.en.svg). Route evidence: [exp/prepare_micro.py](../../exp/prepare_micro.py) | [experiments/micro_mapping.csv](../../experiments/micro_mapping.csv).

<a id="e051"></a>

### E051: Ordinary 16x16 multiplier

**Based on:** [E047](#e047) (Numerical reference or research motivation).

**Change:** Measure DSP mapping for one signed 16x16 multiplication in isolation.

**Effects and issues:** One multiplier maps to one DSP. These PE results are not frame performance.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 2.38 ns |
| Latency / interval | 66 / 64 cycles |
| Registry time conversion | 0.00066 ms (PE scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 62 / 16 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `628517e9377838d3168c654dcf48f20beae18bad`.

**Original evidence:** [E051.json](../../exp/configs/E051.json) | [E051.md](../../experiments/E051_mul16_default/E051.md) | [config.json](../../experiments/E051_mul16_default/config.json) | [metrics.json](../../experiments/E051_mul16_default/metrics.json) | [csynth.rpt](../../experiments/E051_mul16_default/csynth.rpt) | [csynth.log.txt](../../experiments/E051_mul16_default/csynth.log.txt) | [csim.log.txt](../../experiments/E051_mul16_default/csim.log.txt).

<a id="e052"></a>

### E052: Fully unrolled constant weights

**Based on:** [E051](#e051) (Control experiment).

**Change:** Fully unroll 64 multiplications by known constants to observe constant optimization.

**Effects and issues:** A constant-weight model differs from this project's runtime-loaded weight contract.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 2.38 ns |
| Latency / interval | 0 / 1 cycles |
| Registry time conversion | 0 ms (PE scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 60 / 0 / 0 |
| LUT / FF | 424 / 0 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `04cdfa1c1f2a556e42255dfcbe87df27463a2252`.

**Original evidence:** [E052.json](../../exp/configs/E052.json) | [E052.md](../../experiments/E052_mul16_constant_unroll/E052.md) | [config.json](../../experiments/E052_mul16_constant_unroll/config.json) | [metrics.json](../../experiments/E052_mul16_constant_unroll/metrics.json) | [csynth.rpt](../../experiments/E052_mul16_constant_unroll/csynth.rpt) | [csynth.log.txt](../../experiments/E052_mul16_constant_unroll/csynth.log.txt) | [csim.log.txt](../../experiments/E052_mul16_constant_unroll/csim.log.txt).

<a id="e053"></a>

### E053: 8x8 fabric multiplier

**Based on:** [E051](#e051) (Control experiment).

**Change:** Explicitly measure LUT multiplication and exhaust operand pairs.

**Effects and issues:** DSP savings come with LUT costs that accumulate at high parallelism.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 1.635 ns |
| Latency / interval | 66 / 64 cycles |
| Registry time conversion | 0.00066 ms (PE scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 0 / 0 / 0 |
| LUT / FF | 119 / 16 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `484fad30a0a9023c116ebdb0bbba0898c1a0c723`.

**Original evidence:** [E053.json](../../exp/configs/E053.json) | [E053.md](../../experiments/E053_mul8_fabric/E053.md) | [config.json](../../experiments/E053_mul8_fabric/config.json) | [metrics.json](../../experiments/E053_mul8_fabric/metrics.json) | [csynth.rpt](../../experiments/E053_mul8_fabric/csynth.rpt) | [csynth.log.txt](../../experiments/E053_mul8_fabric/csynth.log.txt) | [csim.log.txt](../../experiments/E053_mul8_fabric/csim.log.txt).

<a id="e054"></a>

### E054: 16x16 multiplier at 4 ns

**Based on:** [E051](#e051) (Design or parameter baseline).

**Change:** Change only the target period and check that single-DSP mapping persists.

**Effects and issues:** Still one DSP per multiplication; this does not validate INT16 packing.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 2.38 ns |
| Latency / interval | 66 / 64 cycles |
| Registry time conversion | 0.000264 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 62 / 16 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `15a28b62e30e437ebcd31cb9ac54f559720c84eb`.

**Original evidence:** [E054.json](../../exp/configs/E054.json) | [E054.md](../../experiments/E054_mul16_default_4ns/E054.md) | [config.json](../../experiments/E054_mul16_default_4ns/config.json) | [metrics.json](../../experiments/E054_mul16_default_4ns/metrics.json) | [csynth.rpt](../../experiments/E054_mul16_default_4ns/csynth.rpt) | [csynth.log.txt](../../experiments/E054_mul16_default_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/E054_mul16_default_4ns/csim.log.txt).

<a id="e055"></a>

### E055: Matched addition-only control

**Based on:** [E053](#e053) (Control experiment).

**Change:** Use the same array interface/loop to separate interface LUT cost from multiplier cost.

**Effects and issues:** The comparison applies to this microkernel; it cannot establish network timing.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 1.635 ns |
| Latency / interval | 66 / 64 cycles |
| Registry time conversion | 0.00066 ms (PE scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 0 / 0 / 0 |
| LUT / FF | 73 / 16 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `9c8ab0be2f3a7eb450aa40193cf2a391f4310e9e`.

**Original evidence:** [E055.json](../../exp/configs/E055.json) | [E055.md](../../experiments/E055_mul8_add_control/E055.md) | [config.json](../../experiments/E055_mul8_add_control/config.json) | [metrics.json](../../experiments/E055_mul8_add_control/metrics.json) | [csynth.rpt](../../experiments/E055_mul8_add_control/csynth.rpt) | [csynth.log.txt](../../experiments/E055_mul8_add_control/csynth.log.txt) | [csim.log.txt](../../experiments/E055_mul8_add_control/csim.log.txt).

<a id="packing"></a>

## A: packing from exact primitives to network cost

Do DSP savings from two shared-operand products outweigh decoding and recovery logic?

[Evolution graph](packing.en.svg). Route evidence: [exp/prepare_arch_pe.py](../../exp/prepare_arch_pe.py) | [exp/prepare_arch_full.py](../../exp/prepare_arch_full.py) | [exp/build_arch_p.py](../../exp/build_arch_p.py) | [exp/prepare_int16_packing.py](../../exp/prepare_int16_packing.py).

<a id="p01"></a>

### P01: Two shared-input INT8 products

**Based on:** [E051](#e051) (Numerical reference or research motivation); [E071](#e071) (Numerical reference or research motivation).

**Change:** Pack two coefficients with gap18, correct borrow for a negative low field, and exhaust signed8 operand triples.

**Effects and issues:** Two products use one DSP, with additional unpacking logic compared with the direct control.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 61 / 56 cycles |
| Registry time conversion | 0.000244 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 132 / 86 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `e5f44e0eb07817e651bd369f0638edf58de458fa`.

**Original evidence:** [P01.json](../../exp/configs/P01.json) | [P01.md](../../experiments/P01_signed8_pair/P01.md) | [config.json](../../experiments/P01_signed8_pair/config.json) | [metrics.json](../../experiments/P01_signed8_pair/metrics.json) | [csynth.rpt](../../experiments/P01_signed8_pair/csynth.rpt) | [csynth.log.txt](../../experiments/P01_signed8_pair/csynth.log.txt) | [csim.log.txt](../../experiments/P01_signed8_pair/csim.log.txt).

<a id="p02"></a>

### P02: Direct two-product control

**Based on:** [P01](#p01) (Control experiment).

**Change:** Compute both products separately with identical interfaces and inputs.

**Effects and issues:** Two DSPs provide the matched control for packing's LUT and pipeline costs.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 1.781 ns |
| Latency / interval | 58 / 56 cycles |
| Registry time conversion | 0.000232 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 2 / 0 / 0 |
| LUT / FF | 57 / 16 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `b73fad7dd87d951428b1be790bd79de00e844c3b`.

**Original evidence:** [P02.json](../../exp/configs/P02.json) | [P02.md](../../experiments/P02_signed8_direct_control/P02.md) | [config.json](../../experiments/P02_signed8_direct_control/config.json) | [metrics.json](../../experiments/P02_signed8_direct_control/metrics.json) | [csynth.rpt](../../experiments/P02_signed8_direct_control/csynth.rpt) | [csynth.log.txt](../../experiments/P02_signed8_direct_control/csynth.log.txt) | [csim.log.txt](../../experiments/P02_signed8_direct_control/csim.log.txt).

<a id="p03"></a>

### P03: Unpack after seven terms

**Based on:** [P01](#p01) (Design or parameter baseline).

**Change:** Accumulate seven packed products within the signed8 safety bound before decoding.

**Effects and issues:** Accumulation/decoding costs LUTs and FFs. The seven-term bound does not apply directly to 10-bit inputs.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 62 / 60 cycles |
| Registry time conversion | 0.000248 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 299 / 309 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `f89b4b1df40e067c8203b67ceae719fed999f9c1`.

**Original evidence:** [P03.json](../../exp/configs/P03.json) | [P03.md](../../experiments/P03_signed8_group7/P03.md) | [config.json](../../experiments/P03_signed8_group7/config.json) | [metrics.json](../../experiments/P03_signed8_group7/metrics.json) | [csynth.rpt](../../experiments/P03_signed8_group7/csynth.rpt) | [csynth.log.txt](../../experiments/P03_signed8_group7/csynth.log.txt) | [csim.log.txt](../../experiments/P03_signed8_group7/csim.log.txt).

<a id="p04"></a>

### P04: Automatic packing recognition

**Based on:** [P01](#p01) (Design or parameter baseline).

**Change:** Remove explicit DSP binding to test compiler recognition of the expression.

**Effects and issues:** A successful local mapping does not establish automatic optimal network architecture.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 61 / 56 cycles |
| Registry time conversion | 0.000244 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 132 / 86 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `21f3955ae9491415b39f1e283b5b96d37f13da84`.

**Original evidence:** [P04.json](../../exp/configs/P04.json) | [P04.md](../../experiments/P04_signed8_auto_mapping/P04.md) | [config.json](../../experiments/P04_signed8_auto_mapping/config.json) | [metrics.json](../../experiments/P04_signed8_auto_mapping/metrics.json) | [csynth.rpt](../../experiments/P04_signed8_auto_mapping/csynth.rpt) | [csynth.log.txt](../../experiments/P04_signed8_auto_mapping/csynth.log.txt) | [csim.log.txt](../../experiments/P04_signed8_auto_mapping/csim.log.txt).

<a id="p05"></a>

### P05: DSP pre-adder builtin

**Based on:** [P01](#p01) (Design or parameter baseline).

**Change:** Express pre-addition and pipeline stages with the SDK DSP48E2 builtin.

**Effects and issues:** P08 must inspect actual primitive attributes; DSP count alone does not prove pre-adder use.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 1.641 ns |
| Latency / interval | 63 / 56 cycles |
| Registry time conversion | 0.000252 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 127 / 162 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `646ed9406c60b0b21abde8152d382b51231f80e8`.

**Original evidence:** [P05.json](../../exp/configs/P05.json) | [P05.md](../../experiments/P05_signed8_builtin_preadder/P05.md) | [config.json](../../experiments/P05_signed8_builtin_preadder/config.json) | [metrics.json](../../experiments/P05_signed8_builtin_preadder/metrics.json) | [csynth.rpt](../../experiments/P05_signed8_builtin_preadder/csynth.rpt) | [csynth.log.txt](../../experiments/P05_signed8_builtin_preadder/csynth.log.txt) | [csim.log.txt](../../experiments/P05_signed8_builtin_preadder/csim.log.txt).

<a id="p06"></a>

### P06: Nonnegative 10-bit activations, two terms

**Based on:** [P01](#p01) (Design or parameter baseline); [E071](#e071) (Numerical reference or research motivation).

**Change:** Use shared activations in 0..511, allowing at most two safe low-field accumulations.

**Effects and issues:** Retain the range bound. General signed10 inputs cannot reuse this grouping.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 62 / 60 cycles |
| Registry time conversion | 0.000248 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 274 / 424 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `cc24997b60dd4532fe676e3b6b3f3761f685d633`.

**Original evidence:** [P06.json](../../exp/configs/P06.json) | [P06.md](../../experiments/P06_nonnegative10_group2/P06.md) | [config.json](../../experiments/P06_nonnegative10_group2/config.json) | [metrics.json](../../experiments/P06_nonnegative10_group2/metrics.json) | [csynth.rpt](../../experiments/P06_nonnegative10_group2/csynth.rpt) | [csynth.log.txt](../../experiments/P06_nonnegative10_group2/csynth.log.txt) | [csim.log.txt](../../experiments/P06_nonnegative10_group2/csim.log.txt).

<a id="p07"></a>

### P07: Exact 10-bit coefficient residual recovery

**Based on:** [P01](#p01) (Design or parameter baseline); [E017](#e017) (Numerical reference or research motivation).

**Change:** Split coefficients into signed low8 plus a residual scaled by 256, recovering results exactly in fabric.

**Effects and issues:** 10-bit quality is preserved, but per-product unpacking and residual recovery add logic.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 62 / 56 cycles |
| Registry time conversion | 0.000248 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 454 / 453 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `ceb5d2172224a4c94e1b41379086b242e997275f`.

**Original evidence:** [P07.json](../../exp/configs/P07.json) | [P07.md](../../experiments/P07_exact10_residual_pair/P07.md) | [config.json](../../experiments/P07_exact10_residual_pair/config.json) | [metrics.json](../../experiments/P07_exact10_residual_pair/metrics.json) | [csynth.rpt](../../experiments/P07_exact10_residual_pair/csynth.rpt) | [csynth.log.txt](../../experiments/P07_exact10_residual_pair/csynth.log.txt) | [csim.log.txt](../../experiments/P07_exact10_residual_pair/csim.log.txt).

<a id="p08"></a>

### P08: Inspect actual DSP pre-adder mapping

**Based on:** [P05](#p05) (Verify the same design).

**Change:** After Vivado implementation, inspect DSP48E2 AMULTSEL, ADREG, and related attributes.

**Effects and issues:** Evidence concerns this PE's physical mapping, not full SRCNN deployment.

**Status:** `impl_complete` / Implementation complete; check timing separately; scope `PE`; step `impl`.

Inherited HLS estimates come from [P05](#p05); they are not new measurements from this step.

Implementation: WNS=2.805 ns; TNS=0 ns; timing_met=true. Actual DSP / BRAM36 / URAM / LUT / FF = 1 / 0 / 0 / 21 / 41. BRAM36 and HLS BRAM18K are different units.

Tool: Vitis 2026.1; source commit: `6deee22d85535da7a17fffd4b7a6d574004f5670`.

**Original evidence:** [P08.json](../../exp/configs/P08.json) | [P08.md](../../experiments/P08_builtin_mapping_implementation/P08.md) | [config.json](../../experiments/P08_builtin_mapping_implementation/config.json) | [metrics.json](../../experiments/P08_builtin_mapping_implementation/metrics.json) | [verification.json](../../experiments/P08_builtin_mapping_implementation/verification.json) | [impl.log.txt](../../experiments/P08_builtin_mapping_implementation/impl.log.txt) | [primitive_probe.json](../../experiments/P08_builtin_mapping_implementation/primitive_probe.json) | [dsp_primitives.csv](../../experiments/P08_builtin_mapping_implementation/dsp_primitives.csv) | [packing_pe_timing_routed.rpt](../../experiments/P08_builtin_mapping_implementation/reports/impl/packing_pe_timing_routed.rpt) | [packing_pe_utilization_routed.rpt](../../experiments/P08_builtin_mapping_implementation/reports/impl/packing_pe_utilization_routed.rpt).

<a id="p09"></a>

### P09: Frozen-record reproduction

**Based on:** [P01](#p01) (Reproduce the same experiment).

**Change:** Restore P01 sources, tests, and parameters under a fresh ID to validate reproducibility.

**Effects and issues:** A reproduction control introduces no new packing algorithm.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 61 / 56 cycles |
| Registry time conversion | 0.000244 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 132 / 86 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `6c22c8658b1a543cac6dc6d16af57e5eb4a2c88b`.

**Original evidence:** [P09.json](../../exp/configs/P09.json) | [P09.md](../../experiments/P09_reproduction_P01/P09.md) | [config.json](../../experiments/P09_reproduction_P01/config.json) | [metrics.json](../../experiments/P09_reproduction_P01/metrics.json) | [csynth.rpt](../../experiments/P09_reproduction_P01/csynth.rpt) | [csynth.log.txt](../../experiments/P09_reproduction_P01/csynth.log.txt) | [csim.log.txt](../../experiments/P09_reproduction_P01/csim.log.txt).

<a id="p10"></a>

### P10: Exact 10-bit packing network, T16

**Based on:** [E048](#e048) (Design or parameter baseline); [P07](#p07) (Integrate an existing module).

**Change:** Pack output channels in Conv1/2 and adjacent output pixels in Conv3.

**Effects and issues:** DSP use falls, but 101,488 LUTs exceed budget. Per-pixel pipeline overhead remains substantial.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 3039083 / 3039084 cycles |
| Registry time conversion | 12.156332 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 101488 / 80563 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `4e606cdf69af0b43ae5cf7acbffb9806d278e6a6`.

**Original evidence:** [P10.json](../../exp/configs/P10.json) | [P10.md](../../experiments/P10_exact10_packing_T16/P10.md) | [config.json](../../experiments/P10_exact10_packing_T16/config.json) | [metrics.json](../../experiments/P10_exact10_packing_T16/metrics.json) | [csynth.rpt](../../experiments/P10_exact10_packing_T16/csynth.rpt) | [csynth.log.txt](../../experiments/P10_exact10_packing_T16/csynth.log.txt) | [csim.log.txt](../../experiments/P10_exact10_packing_T16/csim.log.txt).

<a id="p11"></a>

### P11: Exact 10-bit packing network, T8

**Based on:** [P10](#p10) (Design or parameter baseline).

**Change:** Increase parallelism with the same arithmetic.

**Effects and issues:** 165,606 LUTs exceed budget. Saving multipliers does not resolve selectors and recovery logic.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 1894302 / 1894303 cycles |
| Registry time conversion | 7.577208 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 165606 / 106599 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `ed612f4c08cfe64b772b55acb2ae440a3d4488d3`.

**Original evidence:** [P11.json](../../exp/configs/P11.json) | [P11.md](../../experiments/P11_exact10_packing_T8/P11.md) | [config.json](../../experiments/P11_exact10_packing_T8/config.json) | [metrics.json](../../experiments/P11_exact10_packing_T8/metrics.json) | [csynth.rpt](../../experiments/P11_exact10_packing_T8/csynth.rpt) | [csynth.log.txt](../../experiments/P11_exact10_packing_T8/csynth.log.txt) | [csim.log.txt](../../experiments/P11_exact10_packing_T8/csim.log.txt).

<a id="p12"></a>

### P12: Exact 10-bit packing network, T4

**Based on:** [P10](#p10) (Design or parameter baseline).

**Change:** Increase parallelism further and compare time/resource tradeoffs.

**Effects and issues:** 292,053 LUTs exceed budget; lower estimated latency cannot qualify this candidate.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 1355582 / 1355583 cycles |
| Registry time conversion | 5.422328 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1007 / 168 / 0 |
| LUT / FF | 292053 / 159828 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `580a5f33c3aa35ba7101090bf4ebd1d5d59e7a1e`.

**Original evidence:** [P12.json](../../exp/configs/P12.json) | [P12.md](../../experiments/P12_exact10_packing_T4/P12.md) | [config.json](../../experiments/P12_exact10_packing_T4/config.json) | [metrics.json](../../experiments/P12_exact10_packing_T4/metrics.json) | [csynth.rpt](../../experiments/P12_exact10_packing_T4/csynth.rpt) | [csynth.log.txt](../../experiments/P12_exact10_packing_T4/csynth.log.txt) | [csim.log.txt](../../experiments/P12_exact10_packing_T4/csim.log.txt).

<a id="p13"></a>

### P13: Complete INT16 two-product control

**Based on:** [E054](#e054) (Numerical reference or research motivation).

**Change:** Directly compute two signed16x16 products with matched interfaces and throughput as the new research baseline.

**Effects and issues:** Only plans/preparation exist in this snapshot; two measured DSPs or achieved II1 cannot be claimed.

**Status:** `planned` / Prepared; no archived measurements; scope `PE`; step `plan`.
Additional checks: No archived measurements.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [P13.json](../../exp/configs/P13.json).

<a id="p14"></a>

### P14: INT16 byte-limb packing

**Based on:** [P13](#p13) (Control experiment); [P01](#p01) (Numerical reference or research motivation).

**Change:** Split 16-bit operands, combine packed narrow products, and recover both complete 32-bit results.

**Effects and issues:** Count unpacking, partial products, and fabric multipliers. This snapshot has no measured result.

**Status:** `planned` / Prepared; no archived measurements; scope `PE`; step `plan`.
Additional checks: No archived measurements.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [P14.json](../../exp/configs/P14.json).

<a id="p15"></a>

### P15: INT16 overlapping fields with fabric recovery

**Based on:** [P13](#p13) (Control experiment); [P01](#p01) (Numerical reference or research motivation).

**Change:** Allow field overlap and exactly recover both complete products using fabric arithmetic.

**Effects and issues:** One DSP does not imply the total cost of two complete multiplications. Results await archiving.

**Status:** `planned` / Prepared; no archived measurements; scope `PE`; step `plan`.
Additional checks: No archived measurements.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [P15.json](../../exp/configs/P15.json).

<a id="p16"></a>

### P16: INT16 one-DSP/one-fabric control

**Based on:** [P13](#p13) (Control experiment).

**Change:** Directly map one product to DSP and one to LUTs, matching P15's resource types.

**Effects and issues:** Use this to assess whether overlap packing beats ordinary mixed mapping. No result exists in this snapshot.

**Status:** `planned` / Prepared; no archived measurements; scope `PE`; step `plan`.
Additional checks: No archived measurements.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [P16.json](../../exp/configs/P16.json).

<a id="scatter"></a>

## C: gather/scatter storage and control tradeoffs

How much BRAM can channel reduction before buffering save, and what does it cost?

[Evolution graph](scatter.en.svg). Route evidence: [exp/prepare_arch_g.py](../../exp/prepare_arch_g.py) | [exp/build_arch_g.py](../../exp/build_arch_g.py).

<a id="g01"></a>

### G01: Matched gather control

**Based on:** [E057](#e057) (Design or parameter baseline).

**Change:** Independently rerun the same T32, 10 ns, 10-bit Conv3 line-buffer organization.

**Effects and issues:** This supplies the scatter control; compare all three organizations under identical parameters.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2983024 / 2983025 cycles |
| Registry time conversion | 29.83024 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 44493 / 46328 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `7b367963c469edd1c60c605a12797428270e24ec`.

**Original evidence:** [G01.json](../../exp/configs/G01.json) | [G01.md](../../experiments/G01_gather_control/G01.md) | [config.json](../../experiments/G01_gather_control/config.json) | [metrics.json](../../experiments/G01_gather_control/metrics.json) | [csynth.rpt](../../experiments/G01_gather_control/csynth.rpt) | [csynth.log.txt](../../experiments/G01_gather_control/csynth.log.txt) | [csim.log.txt](../../experiments/G01_gather_control/csim.log.txt).

<a id="g02"></a>

### G02: Scatter with explicit padding

**Based on:** [E060](#e060) (Design or parameter baseline); [G01](#g01) (Control experiment).

**Change:** Store five rows of 32-bit partial sums while retaining 32-channel padding.

**Effects and issues:** BRAM18K falls from 168 to 137, but estimated time rises from 29.83 to 37.70 ms.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 3770206 / 3770207 cycles |
| Registry time conversion | 37.70206 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 137 / 0 |
| LUT / FF | 39135 / 24841 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `98c6287b7606373b795bfd0436a67879931184f0`.

**Original evidence:** [G02.json](../../exp/configs/G02.json) | [G02.md](../../experiments/G02_scatter_pad_control/G02.md) | [config.json](../../experiments/G02_scatter_pad_control/config.json) | [metrics.json](../../experiments/G02_scatter_pad_control/metrics.json) | [csynth.rpt](../../experiments/G02_scatter_pad_control/csynth.rpt) | [csynth.log.txt](../../experiments/G02_scatter_pad_control/csynth.log.txt) | [csim.log.txt](../../experiments/G02_scatter_pad_control/csim.log.txt).

<a id="g03"></a>

### G03: Scatter with merged boundary kernels

**Based on:** [G02](#g02) (Design or parameter baseline).

**Change:** Merge repeated taps for nine boundary classes and remove the wide-channel padding buffer.

**Effects and issues:** BRAM18K falls further to 87, but kernel selection, loading, and control increase estimated time to about 44.14 ms.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 4413926 / 4413927 cycles |
| Registry time conversion | 44.13926 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 87 / 0 |
| LUT / FF | 40677 / 25230 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `d0ccc144c6d39a9b2aa08e3c29b32ad1a7cf8976`.

**Original evidence:** [G03.json](../../exp/configs/G03.json) | [G03.md](../../experiments/G03_scatter_edge_kernels/G03.md) | [config.json](../../experiments/G03_scatter_edge_kernels/config.json) | [metrics.json](../../experiments/G03_scatter_edge_kernels/metrics.json) | [csynth.rpt](../../experiments/G03_scatter_edge_kernels/csynth.rpt) | [csynth.log.txt](../../experiments/G03_scatter_edge_kernels/csynth.log.txt) | [csim.log.txt](../../experiments/G03_scatter_edge_kernels/csim.log.txt).

<a id="memory"></a>

## Storage routes: dataflow, DDR probe, and fused tiles

Can external memory or small tiles replace full maps while preserving boundary behavior?

[Evolution graph](memory.en.svg). Route evidence: [exp/prepare_arch_s.py](../../exp/prepare_arch_s.py) | [exp/build_arch_s.py](../../exp/build_arch_s.py) | [experiments/bursts.csv](../../experiments/bursts.csv).

<a id="s01"></a>

### S01: Global-array DDR interface probe

**Based on:** [E048](#e048) (Design or parameter baseline).

**Change:** Attempt to export AXI ports for global scratch arrays and examine layer-to-layer external storage.

**Effects and issues:** scratch1/2 ports are not generated; storage remains enormous on-chip arrays. This is not a valid DDR implementation.

**Status:** `invalid_config` / Invalid configuration; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: BRAM18K; Invalid configuration.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 16730473 / 16730474 cycles |
| Registry time conversion | 167.30473 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 11286 / 0 |
| LUT / FF | 48121 / 49034 |
| Checked II targets | Not recorded |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `1fa3d1916402d43dca0d9b0e4c68685a956dde39`.

**Original evidence:** [S01.json](../../exp/configs/S01.json) | [S01.md](../../experiments/S01_ddr_global_probe/S01.md) | [config.json](../../experiments/S01_ddr_global_probe/config.json) | [metrics.json](../../experiments/S01_ddr_global_probe/metrics.json) | [csynth.rpt](../../experiments/S01_ddr_global_probe/csynth.rpt) | [csynth.log.txt](../../experiments/S01_ddr_global_probe/csynth.log.txt) | [csim.log.txt](../../experiments/S01_ddr_global_probe/csim.log.txt).

<a id="s02"></a>

### S02: Whole-network dataflow control

**Based on:** [G01](#g01) (Design or parameter baseline).

**Change:** Reuse the matched gather design as the network control for tile fusion.

**Effects and issues:** This remeasures the same design rather than introducing a different network.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 2983024 / 2983025 cycles |
| Registry time conversion | 29.83024 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 44493 / 46328 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `3071af7264b43754e13820760c80952f77907b55`.

**Original evidence:** [S02.json](../../exp/configs/S02.json) | [S02.md](../../experiments/S02_whole_dataflow_control/S02.md) | [config.json](../../experiments/S02_whole_dataflow_control/config.json) | [metrics.json](../../experiments/S02_whole_dataflow_control/metrics.json) | [csynth.rpt](../../experiments/S02_whole_dataflow_control/csynth.rpt) | [csynth.log.txt](../../experiments/S02_whole_dataflow_control/csynth.log.txt) | [csim.log.txt](../../experiments/S02_whole_dataflow_control/csim.log.txt).

<a id="s03"></a>

### S03: Three-layer fused output tiles, B8

**Based on:** [E048](#e048) (Design or parameter baseline); [S02](#s02) (Control experiment).

**Change:** Recompute each tile's halo, fuse local Conv1/2 computation, and buffer a small Conv2 tile.

**Effects and issues:** BRAM is low, but halo recomputation, banking, and address selection cost time and LUTs.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 22803545 / 22803546 cycles |
| Registry time conversion | 228.03545 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 113576 / 73880 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `0fc4d3ff9afb1d36f0b457debcbb06406e50fefc`.

**Original evidence:** [S03.json](../../exp/configs/S03.json) | [S03.md](../../experiments/S03_tile_fusion_B8/S03.md) | [config.json](../../experiments/S03_tile_fusion_B8/config.json) | [metrics.json](../../experiments/S03_tile_fusion_B8/metrics.json) | [csynth.rpt](../../experiments/S03_tile_fusion_B8/csynth.rpt) | [csynth.log.txt](../../experiments/S03_tile_fusion_B8/csynth.log.txt) | [csim.log.txt](../../experiments/S03_tile_fusion_B8/csim.log.txt).

<a id="s04"></a>

### S04: Three-layer fused output tiles, B16

**Based on:** [S03](#s03) (Design or parameter baseline).

**Change:** Increase tile size to reduce relative halo recomputation.

**Effects and issues:** Sequential tiles still lack whole-network engine overlap; LUTs exceed budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 16753977 / 16753978 cycles |
| Registry time conversion | 167.53977 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 114061 / 73901 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c1e9023e9d890ec0552489a75ae43da5583dce12`.

**Original evidence:** [S04.json](../../exp/configs/S04.json) | [S04.md](../../experiments/S04_tile_fusion_B16/S04.md) | [config.json](../../experiments/S04_tile_fusion_B16/config.json) | [metrics.json](../../experiments/S04_tile_fusion_B16/metrics.json) | [csynth.rpt](../../experiments/S04_tile_fusion_B16/csynth.rpt) | [csynth.log.txt](../../experiments/S04_tile_fusion_B16/csynth.log.txt) | [csim.log.txt](../../experiments/S04_tile_fusion_B16/csim.log.txt).

<a id="s05"></a>

### S05: Three-layer fused output tiles, B32

**Based on:** [S03](#s03) (Design or parameter baseline).

**Change:** Increase output tile size again to compare buffer and recomputation costs.

**Effects and issues:** Traffic lower bounds improve, but synthesized latency and LUT use remain unacceptable.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 14166377 / 14166378 cycles |
| Registry time conversion | 141.66377 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 120033 / 74038 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `976b14de2be87aa7320f621c9f8043f92d710ebe`.

**Original evidence:** [S05.json](../../exp/configs/S05.json) | [S05.md](../../experiments/S05_tile_fusion_B32/S05.md) | [config.json](../../experiments/S05_tile_fusion_B32/config.json) | [metrics.json](../../experiments/S05_tile_fusion_B32/metrics.json) | [csynth.rpt](../../experiments/S05_tile_fusion_B32/csynth.rpt) | [csynth.log.txt](../../experiments/S05_tile_fusion_B32/csynth.log.txt) | [csim.log.txt](../../experiments/S05_tile_fusion_B32/csim.log.txt).

<a id="s06"></a>

### S06: Three-layer fused output tiles, B64

**Based on:** [S03](#s03) (Design or parameter baseline).

**Change:** Scan the largest tile, including actual replicated edges and incomplete boundary tiles.

**Effects and issues:** A smaller halo ratio still does not offset control/storage costs. Bandwidth is modeled, not measured on board.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 10 / 7.3 ns |
| Latency / interval | 12981873 / 12981874 cycles |
| Registry time conversion | 129.81873 ms (frame scope; converted at 10 ns) |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 136162 / 74127 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `2f507fd6b535a9c3762731134d2ce3b2517f9887`.

**Original evidence:** [S06.json](../../exp/configs/S06.json) | [S06.md](../../experiments/S06_tile_fusion_B64/S06.md) | [config.json](../../experiments/S06_tile_fusion_B64/config.json) | [metrics.json](../../experiments/S06_tile_fusion_B64/metrics.json) | [csynth.rpt](../../experiments/S06_tile_fusion_B64/csynth.rpt) | [csynth.log.txt](../../experiments/S06_tile_fusion_B64/csynth.log.txt) | [csim.log.txt](../../experiments/S06_tile_fusion_B64/csim.log.txt).

<a id="winograd"></a>

## D: Winograd transforms, scheduling, and weight banks

After reducing multiplication, do transforms, reordering, and wider buffers become the larger costs?

[Evolution graph](winograd.en.svg). Route evidence: [exp/prepare_arch_pe.py](../../exp/prepare_arch_pe.py) | [exp/prepare_arch_full.py](../../exp/prepare_arch_full.py) | [exp/prepare_header_retry.py](../../exp/prepare_header_retry.py) | [exp/prepare_wino_continuous.py](../../exp/prepare_wino_continuous.py) | [exp/prepare_split_windows.py](../../exp/prepare_split_windows.py) | [exp/prepare_raw_weight_banks.py](../../exp/prepare_raw_weight_banks.py).

<a id="w01"></a>

### W01: 10-bit integer F(2x2,3x3) PE

**Based on:** [E071](#e071) (Numerical reference or research motivation).

**Change:** Use G2=2G for integer transforms and divide the inverse result exactly by four before quantization.

**Effects and issues:** Local multiplication falls, but transform adders, width growth, reordering, and network scheduling are not yet included.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 2.895 ns |
| Latency / interval | 36 / 32 cycles |
| Registry time conversion | 0.000144 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 16 / 0 / 0 |
| LUT / FF | 1499 / 1124 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `8460ada1708647dfab881c05b9e638bb6fa0450b`.

**Original evidence:** [W01.json](../../exp/configs/W01.json) | [W01.md](../../experiments/W01_integer_f2_10bit/W01.md) | [config.json](../../experiments/W01_integer_f2_10bit/config.json) | [metrics.json](../../experiments/W01_integer_f2_10bit/metrics.json) | [csynth.rpt](../../experiments/W01_integer_f2_10bit/csynth.rpt) | [csynth.log.txt](../../experiments/W01_integer_f2_10bit/csynth.log.txt) | [csim.log.txt](../../experiments/W01_integer_f2_10bit/csim.log.txt).

<a id="w02"></a>

### W02: Direct-convolution PE control

**Based on:** [W01](#w01) (Control experiment).

**Change:** Use the same tile to compare 36 direct products against Winograd's 16.

**Effects and issues:** DSP savings accompany higher LUT use. PE cycles are not frame latency.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 2.463 ns |
| Latency / interval | 38 / 32 cycles |
| Registry time conversion | 0.000152 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 36 / 0 / 0 |
| LUT / FF | 503 / 1025 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `f7e68f798215348867fb3be8b25fe71b5991f861`.

**Original evidence:** [W02.json](../../exp/configs/W02.json) | [W02.md](../../experiments/W02_direct_f2_control/W02.md) | [config.json](../../experiments/W02_direct_f2_control/config.json) | [metrics.json](../../experiments/W02_direct_f2_control/metrics.json) | [csynth.rpt](../../experiments/W02_direct_f2_control/csynth.rpt) | [csynth.log.txt](../../experiments/W02_direct_f2_control/csynth.log.txt) | [csim.log.txt](../../experiments/W02_direct_f2_control/csim.log.txt).

<a id="w03"></a>

### W03: 16-bit Winograd PE

**Based on:** [W01](#w01) (Design or parameter baseline).

**Change:** Increase input/weight widths and measure mapping of transformed 18x20-bit products.

**Effects and issues:** A Winograd primitive passes; this establishes neither INT16 packing nor a deployed 16-bit network.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 2.179 ns |
| Latency / interval | 37 / 32 cycles |
| Registry time conversion | 0.000148 ms (PE scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 16 / 0 / 0 |
| LUT / FF | 2155 / 1932 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `b55d6e3e8eb84c9cb1214335125512f610b61f30`.

**Original evidence:** [W03.json](../../exp/configs/W03.json) | [W03.md](../../experiments/W03_integer_f2_16bit/W03.md) | [config.json](../../experiments/W03_integer_f2_16bit/config.json) | [metrics.json](../../experiments/W03_integer_f2_16bit/metrics.json) | [csynth.rpt](../../experiments/W03_integer_f2_16bit/csynth.rpt) | [csynth.log.txt](../../experiments/W03_integer_f2_16bit/csynth.log.txt) | [csim.log.txt](../../experiments/W03_integer_f2_16bit/csim.log.txt).

<a id="w04"></a>

### W04: Winograd Conv1 layer, T16

**Based on:** [E048](#e048) (Design or parameter baseline); [W01](#w01) (Integrate an existing module).

**Change:** Split the 9x9 kernel into nine 3x3 kernels, transform weights at runtime, and reorder tile outputs.

**Effects and issues:** Dimension macros F2/F3 collide with AMD header identifiers; compilation fails.

**Status:** `fail` / Run failed; scope `layer`; step `csim`.

Tool: Vitis 2026.1; source commit: `9e69c4831a7dfd219383f72ae97ef36914ff483d`.

**Original evidence:** [W04.json](../../exp/configs/W04.json) | [W04.md](../../experiments/W04_winograd_conv1_T16/W04.md) | [config.json](../../experiments/W04_winograd_conv1_T16/config.json) | [metrics.json](../../experiments/W04_winograd_conv1_T16/metrics.json) | [csim.log.txt](../../experiments/W04_winograd_conv1_T16/csim.log.txt).

<a id="w05"></a>

### W05: Winograd network, T16

**Based on:** [W04](#w04) (Design or parameter baseline).

**Change:** Connect Winograd Conv1 to Conv2/3 and measure the complete frame.

**Effects and issues:** The same header collision prevents valid synthesis results.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `82a84d9a0885c02bbe05cfaf366a312b9fbf27fa`.

**Original evidence:** [W05.json](../../exp/configs/W05.json) | [W05.md](../../experiments/W05_winograd_network_T16/W05.md) | [config.json](../../experiments/W05_winograd_network_T16/config.json) | [metrics.json](../../experiments/W05_winograd_network_T16/metrics.json) | [csim.log.txt](../../experiments/W05_winograd_network_T16/csim.log.txt).

<a id="w06"></a>

### W06: Winograd network, T8

**Based on:** [W05](#w05) (Design or parameter baseline).

**Change:** Change parallelism while retaining the numerical contract.

**Effects and issues:** Compilation still fails. W09 independently retries the design.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `5be485ae1b731a750192cbae423efb082ea0ee56`.

**Original evidence:** [W06.json](../../exp/configs/W06.json) | [W06.md](../../experiments/W06_winograd_network_T8/W06.md) | [config.json](../../experiments/W06_winograd_network_T8/config.json) | [metrics.json](../../experiments/W06_winograd_network_T8/metrics.json) | [csim.log.txt](../../experiments/W06_winograd_network_T8/csim.log.txt).

<a id="w07"></a>

### W07: Single-layer header-order fix

**Based on:** [W04](#w04) (Retry after a fix).

**Change:** Include AMD type headers before defining network dimension macros.

**Effects and issues:** Valid layer results emerge, but conditional tile loops inflate HLS's computation iteration estimate.

**Status:** `provisional` / Candidate; final acceptance pending; scope `layer`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 2.92 ns |
| Latency / interval | 5721420 / 5721421 cycles |
| Registry time conversion | 22.88568 ms (layer scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 145 / 99 / 0 |
| LUT / FF | 30872 / 25564 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true; butterfly MSE=5.154311903422524e-06; six-pixel border MSE=4.121844856441791e-06. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `ed8ca280b9c20de633502eea77a4d12f859df26e`.

**Original evidence:** [W07.json](../../exp/configs/W07.json) | [W07.md](../../experiments/W07_winograd_conv1_T16_header_retry/W07.md) | [config.json](../../experiments/W07_winograd_conv1_T16_header_retry/config.json) | [metrics.json](../../experiments/W07_winograd_conv1_T16_header_retry/metrics.json) | [csynth.rpt](../../experiments/W07_winograd_conv1_T16_header_retry/csynth.rpt) | [csynth.log.txt](../../experiments/W07_winograd_conv1_T16_header_retry/csynth.log.txt) | [csim.log.txt](../../experiments/W07_winograd_conv1_T16_header_retry/csim.log.txt).

<a id="w08"></a>

### W08: T16 network header fix

**Based on:** [W05](#w05) (Retry after a fix).

**Change:** Fix include order in an independent source copy.

**Effects and issues:** About 22.8954 ms; legal and exact, with substantial tile scheduling and buffering costs.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 5723851 / 5723852 cycles |
| Registry time conversion | 22.895404 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 326 / 241 / 0 |
| LUT / FF | 75814 / 69105 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `23c3e163beadc2007e17a75e66bc93010b718832`.

**Original evidence:** [W08.json](../../exp/configs/W08.json) | [W08.md](../../experiments/W08_winograd_network_T16_header_retry/W08.md) | [config.json](../../experiments/W08_winograd_network_T16_header_retry/config.json) | [metrics.json](../../experiments/W08_winograd_network_T16_header_retry/metrics.json) | [csynth.rpt](../../experiments/W08_winograd_network_T16_header_retry/csynth.rpt) | [csynth.log.txt](../../experiments/W08_winograd_network_T16_header_retry/csynth.log.txt) | [csim.log.txt](../../experiments/W08_winograd_network_T16_header_retry/csim.log.txt).

<a id="w09"></a>

### W09: T8 network header fix

**Based on:** [W06](#w06) (Retry after a fix).

**Change:** Apply the same fix at T8 parallelism.

**Effects and issues:** 135,496 LUTs exceed budget; runtime transform loading has costly selectors and registers.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 3493579 / 3493580 cycles |
| Registry time conversion | 13.974316 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 648 / 241 / 0 |
| LUT / FF | 135496 / 148761 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `42da116108fa1635f7e63b49fb19b6d9fe457f82`.

**Original evidence:** [W09.json](../../exp/configs/W09.json) | [W09.md](../../experiments/W09_winograd_network_T8_header_retry/W09.md) | [config.json](../../experiments/W09_winograd_network_T8_header_retry/config.json) | [metrics.json](../../experiments/W09_winograd_network_T8_header_retry/metrics.json) | [csynth.rpt](../../experiments/W09_winograd_network_T8_header_retry/csynth.rpt) | [csynth.log.txt](../../experiments/W09_winograd_network_T8_header_retry/csynth.log.txt) | [csim.log.txt](../../experiments/W09_winograd_network_T8_header_retry/csim.log.txt).

<a id="w10"></a>

### W10: Fixed tile loops, continuous Conv1 only

**Based on:** [W08](#w08) (Design or parameter baseline); [F03](#f03) (Numerical reference or research motivation).

**Change:** Separate window generation from a fixed-count MAC loop to remove conditional-boundary iteration inflation.

**Effects and issues:** About 7.5482 ms and 241 BRAM18K blocks. Conv2/3 still have per-pixel pipeline overhead.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 1887051 / 1887052 cycles |
| Registry time conversion | 7.548204 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 326 / 241 / 0 |
| LUT / FF | 79158 / 76052 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `d048887dade9486661e7bab5265ac970c15255e5`.

**Original evidence:** [W10.json](../../exp/configs/W10.json) | [W10.md](../../experiments/W10_fixed_tiles_T16_c1only_4ns/W10.md) | [config.json](../../experiments/W10_fixed_tiles_T16_c1only_4ns/config.json) | [metrics.json](../../experiments/W10_fixed_tiles_T16_c1only_4ns/metrics.json) | [csynth.rpt](../../experiments/W10_fixed_tiles_T16_c1only_4ns/csynth.rpt) | [csynth.log.txt](../../experiments/W10_fixed_tiles_T16_c1only_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/W10_fixed_tiles_T16_c1only_4ns/csim.log.txt).

<a id="w11"></a>

### W11: Three continuous layers, T8, 4 ns

**Based on:** [W10](#w10) (Design or parameter baseline).

**Change:** Extend continuous scheduling to the other layers and scan T8.

**Effects and issues:** C simulation is exact, but Conv3's 8000-bit stream exceeds the tool's 4096-bit limit.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `3dee20bd819d52cfe2ce81e22aaa4d3f10cdb27c`.

**Original evidence:** [W11.json](../../exp/configs/W11.json) | [W11.md](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/W11.md) | [config.json](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/config.json) | [metrics.json](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/metrics.json) | [csynth.log.txt](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/csim.log.txt).

<a id="w12"></a>

### W12: Three continuous layers, T16, 4 ns

**Based on:** [W10](#w10) (Design or parameter baseline).

**Change:** Measure continuous three-layer organization at T16.

**Effects and issues:** The same stream-width limit causes synthesis failure; numerical precision is not the failure.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `8a51d12f0fa70218d0493eeaf8d09c59d6e6265c`.

**Original evidence:** [W12.json](../../exp/configs/W12.json) | [W12.md](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/W12.md) | [config.json](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/config.json) | [metrics.json](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/metrics.json) | [csynth.log.txt](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/csim.log.txt).

<a id="w13"></a>

### W13: Three continuous layers, T8, 3.33 ns

**Based on:** [W11](#w11) (Design or parameter baseline).

**Change:** Tighten the period for the same continuous organization.

**Effects and issues:** Stream width remains invalid, so no performance result is obtained.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `6bce6339078e0cd50e10f2cfbe39485d5e465a94`.

**Original evidence:** [W13.json](../../exp/configs/W13.json) | [W13.md](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/W13.md) | [config.json](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/config.json) | [metrics.json](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/metrics.json) | [csynth.log.txt](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/csynth.log.txt) | [csim.log.txt](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/csim.log.txt).

<a id="w14"></a>

### W14: T8 dual 4000-bit window streams

**Based on:** [W11](#w11) (Retry after a fix).

**Change:** Split each complete Conv3 window into two synchronized channels without changing arithmetic.

**Effects and issues:** Legal synthesis estimates about 2.1302 ms, but LUT/FF budgets are exceeded.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 532562 / 532563 cycles |
| Registry time conversion | 2.130248 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 648 / 146 / 0 |
| LUT / FF | 148013 / 182409 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `74adcad868fcc049ace36cb3232eaa337adafa4d`.

**Original evidence:** [W14.json](../../exp/configs/W14.json) | [W14.md](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) | [config.json](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/config.json) | [metrics.json](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/metrics.json) | [csynth.rpt](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/csim.log.txt).

<a id="w15"></a>

### W15: T16 split-window streams

**Based on:** [W12](#w12) (Retry after a fix).

**Change:** Correct the T16 stream representation.

**Effects and issues:** About 4.2274 ms, but 89,114 LUTs still exceed the project budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 1056850 / 1056851 cycles |
| Registry time conversion | 4.2274 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 326 / 146 / 0 |
| LUT / FF | 89114 / 92946 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `03a4a03eb8e1166b3c9d18cf18593028b2b6ff82`.

**Original evidence:** [W15.json](../../exp/configs/W15.json) | [W15.md](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) | [config.json](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/config.json) | [metrics.json](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/metrics.json) | [csynth.rpt](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/csim.log.txt).

<a id="w16"></a>

### W16: T8 split-window streams, 3.33 ns

**Based on:** [W13](#w13) (Retry after a fix).

**Change:** Fix stream width and measure the tighter period.

**Effects and issues:** The 1.7735 ms estimate exceeds LUT/FF budgets and cannot qualify as a candidate.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3.33 / 3.239 ns |
| Latency / interval | 532569 / 532570 cycles |
| Registry time conversion | 1.77345477 ms (frame scope; converted at 3.33 ns) |
| DSP / BRAM18K / URAM | 648 / 146 / 0 |
| LUT / FF | 145767 / 192756 |
| Checked II targets | Met |

HLS 200-871: logic budget 3.33 - 0.899 = 2.431 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c7d8ad219ced5b2047082c15ab2817a3e9dcef41`.

**Original evidence:** [W16.json](../../exp/configs/W16.json) | [W16.md](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) | [config.json](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/config.json) | [metrics.json](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/metrics.json) | [csynth.rpt](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/csim.log.txt).

<a id="w17"></a>

### W17: T8 narrow raw-weight banks

**Based on:** [W14](#w14) (Design or parameter baseline); [W09](#w09) (Numerical reference or research motivation).

**Change:** Reduce channel banking for raw weights used only by sequential transforms; retain transformed MAC banks.

**Effects and issues:** LUTs decrease substantially but remain at 93,166, above budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 532562 / 532563 cycles |
| Registry time conversion | 2.130248 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 648 / 146 / 0 |
| LUT / FF | 93166 / 122399 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `d6f7b25ddca67aa9464617c1ee514c5bc8569bd7`.

**Original evidence:** [W17.json](../../exp/configs/W17.json) | [W17.md](../../experiments/W17_narrow_raw_banks_T8/W17.md) | [config.json](../../experiments/W17_narrow_raw_banks_T8/config.json) | [metrics.json](../../experiments/W17_narrow_raw_banks_T8/metrics.json) | [csynth.rpt](../../experiments/W17_narrow_raw_banks_T8/csynth.rpt) | [csynth.log.txt](../../experiments/W17_narrow_raw_banks_T8/csynth.log.txt) | [csim.log.txt](../../experiments/W17_narrow_raw_banks_T8/csim.log.txt).

<a id="w18"></a>

### W18: T16 narrow raw-weight banks

**Based on:** [W15](#w15) (Design or parameter baseline).

**Change:** Measure the same loader/banking adjustment at T16.

**Effects and issues:** About 4.2274 ms, 326 DSPs, and 74,480 LUTs meet this route's resource budget. Final RTL/implementation remain pending.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 1056850 / 1056851 cycles |
| Registry time conversion | 4.2274 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 326 / 146 / 0 |
| LUT / FF | 74480 / 87869 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `e6ecd9e072d21de4892870138cdf9484a81bce50`.

**Original evidence:** [W18.json](../../exp/configs/W18.json) | [W18.md](../../experiments/W18_narrow_raw_banks_T16/W18.md) | [config.json](../../experiments/W18_narrow_raw_banks_T16/config.json) | [metrics.json](../../experiments/W18_narrow_raw_banks_T16/metrics.json) | [csynth.rpt](../../experiments/W18_narrow_raw_banks_T16/csynth.rpt) | [csynth.log.txt](../../experiments/W18_narrow_raw_banks_T16/csynth.log.txt) | [csim.log.txt](../../experiments/W18_narrow_raw_banks_T16/csim.log.txt).

<a id="combination"></a>

## Combinations: can Winograd and packing savings add up?

After local multiplier savings, are enough LUTs, FFs, and buffers left for the whole network?

[Evolution graph](combination.en.svg). Route evidence: [exp/build_arch_c.py](../../exp/build_arch_c.py) | [exp/prepare_arch_c.py](../../exp/prepare_arch_c.py) | [exp/prepare_header_retry.py](../../exp/prepare_header_retry.py) | [exp/prepare_combination_guard.py](../../exp/prepare_combination_guard.py) | [exp/prepare_mixed_arch.py](../../exp/prepare_mixed_arch.py) | [exp/prepare_split_windows.py](../../exp/prepare_split_windows.py).

<a id="c01"></a>

### C01: Winograd plus Conv2/3 packing, T4

**Based on:** [W05](#w05) (Design or parameter baseline); [P07](#p07) (Integrate an existing module).

**Change:** Combine Conv1 Winograd with exact 10-bit packing in both later layers.

**Effects and issues:** Header dimension macros collide and compilation fails. A paper DSP budget is not a hardware result.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `2fb8016dd9b9d08be0410ba4578400a1d63a9b46`.

**Original evidence:** [C01.json](../../exp/configs/C01.json) | [C01.md](../../experiments/C01_wino_packing_T4_all/C01.md) | [config.json](../../experiments/C01_wino_packing_T4_all/config.json) | [metrics.json](../../experiments/C01_wino_packing_T4_all/metrics.json) | [csim.log.txt](../../experiments/C01_wino_packing_T4_all/csim.log.txt).

<a id="c02"></a>

### C02: Winograd plus Conv3 packing only, T4

**Based on:** [C01](#c01) (Design or parameter baseline).

**Change:** Keep Conv2 direct to isolate its packing cost.

**Effects and issues:** The same header collision applies; C05 retries it.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `f4fe7dd06b73a823ebb040448cc3d4e4f421e0ad`.

**Original evidence:** [C02.json](../../exp/configs/C02.json) | [C02.md](../../experiments/C02_wino_packing_T4_conv3/C02.md) | [config.json](../../experiments/C02_wino_packing_T4_conv3/config.json) | [metrics.json](../../experiments/C02_wino_packing_T4_conv3/metrics.json) | [csim.log.txt](../../experiments/C02_wino_packing_T4_conv3/csim.log.txt).

<a id="c03"></a>

### C03: Winograd plus Conv2/3 packing, T8

**Based on:** [C01](#c01) (Design or parameter baseline).

**Change:** Lower parallelism to control resource use.

**Effects and issues:** The same compilation problem applies; C06 independently fixes it.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `7ffec327e99090d09eda62e33f6dcb9aebfc1f8c`.

**Original evidence:** [C03.json](../../exp/configs/C03.json) | [C03.md](../../experiments/C03_wino_packing_T8_all/C03.md) | [config.json](../../experiments/C03_wino_packing_T8_all/config.json) | [metrics.json](../../experiments/C03_wino_packing_T8_all/metrics.json) | [csim.log.txt](../../experiments/C03_wino_packing_T8_all/csim.log.txt).

<a id="c04"></a>

### C04: Two-layer packing header fix

**Based on:** [C01](#c01) (Retry after a fix).

**Change:** Fix only include order, retaining mathematics, precision, and parameters.

**Effects and issues:** LUT/FF use greatly exceeds budget. Fitting 936 DSPs does not establish overall feasibility.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 2378443 / 2378444 cycles |
| Registry time conversion | 9.513772 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 936 / 241 / 0 |
| LUT / FF | 293222 / 253809 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `8ee5a6eede0df4ef6cef4049b737a652f2f0f363`.

**Original evidence:** [C04.json](../../exp/configs/C04.json) | [C04.md](../../experiments/C04_wino_packing_T4_all_header_retry/C04.md) | [config.json](../../experiments/C04_wino_packing_T4_all_header_retry/config.json) | [metrics.json](../../experiments/C04_wino_packing_T4_all_header_retry/metrics.json) | [csynth.rpt](../../experiments/C04_wino_packing_T4_all_header_retry/csynth.rpt) | [csynth.log.txt](../../experiments/C04_wino_packing_T4_all_header_retry/csynth.log.txt) | [csim.log.txt](../../experiments/C04_wino_packing_T4_all_header_retry/csim.log.txt).

<a id="c05"></a>

### C05: Conv3-only packing header fix

**Based on:** [C02](#c02) (Retry after a fix).

**Change:** Run the valid control with one fewer packed layer.

**Effects and issues:** About 260,882 LUTs still prevent a resource-qualified combination.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 2378443 / 2378444 cycles |
| Registry time conversion | 9.513772 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1192 / 241 / 0 |
| LUT / FF | 260882 / 263747 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c5d03ed51f94cd65ed96224535098a4e71987dd3`.

**Original evidence:** [C05.json](../../exp/configs/C05.json) | [C05.md](../../experiments/C05_wino_packing_T4_conv3_header_retry/C05.md) | [config.json](../../experiments/C05_wino_packing_T4_conv3_header_retry/config.json) | [metrics.json](../../experiments/C05_wino_packing_T4_conv3_header_retry/metrics.json) | [csynth.rpt](../../experiments/C05_wino_packing_T4_conv3_header_retry/csynth.rpt) | [csynth.log.txt](../../experiments/C05_wino_packing_T4_conv3_header_retry/csynth.log.txt) | [csim.log.txt](../../experiments/C05_wino_packing_T4_conv3_header_retry/csim.log.txt).

<a id="c06"></a>

### C06: T8 combination header fix

**Based on:** [C03](#c03) (Retry after a fix).

**Change:** Validly measure the combination at lower parallelism.

**Effects and issues:** 470 DSPs fit, but 170,165 LUTs exceed budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 3493579 / 3493580 cycles |
| Registry time conversion | 13.974316 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 470 / 169 / 0 |
| LUT / FF | 170165 / 153644 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `eb17e26908d4eb725d4b7aa2700b68731d168a1e`.

**Original evidence:** [C06.json](../../exp/configs/C06.json) | [C06.md](../../experiments/C06_wino_packing_T8_all_header_retry/C06.md) | [config.json](../../experiments/C06_wino_packing_T8_all_header_retry/config.json) | [metrics.json](../../experiments/C06_wino_packing_T8_all_header_retry/metrics.json) | [csynth.rpt](../../experiments/C06_wino_packing_T8_all_header_retry/csynth.rpt) | [csynth.log.txt](../../experiments/C06_wino_packing_T8_all_header_retry/csynth.log.txt) | [csim.log.txt](../../experiments/C06_wino_packing_T8_all_header_retry/csim.log.txt).

<a id="c07"></a>

### C07: Continuously scheduled 10-bit combination

**Based on:** [C04](#c04) (Design or parameter baseline); [W10](#w10) (Numerical reference or research motivation).

**Change:** Separate window generation from fixed MAC loops in the combined architecture.

**Effects and issues:** C simulation does not pass. C12 records a separate corrective retry.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Tool: Vitis 2026.1; source commit: `356030a37bdb7c76ba159851fd885eb2a535d789`.

**Original evidence:** [C07.json](../../exp/configs/C07.json) | [C07.md](../../experiments/C07_continuous_wino_packing_T8/C07.md) | [config.json](../../experiments/C07_continuous_wino_packing_T8/config.json) | [metrics.json](../../experiments/C07_continuous_wino_packing_T8/metrics.json) | [csim.log.txt](../../experiments/C07_continuous_wino_packing_T8/csim.log.txt).

<a id="c12"></a>

### C12: Continuous-combination guard fix

**Based on:** [C07](#c07) (Retry after a fix).

**Change:** Fix control/representation while preserving the arithmetic contract.

**Effects and issues:** Functionality is exact, but 174,591 LUTs exceed budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 1894303 / 1894304 cycles |
| Registry time conversion | 7.577212 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 470 / 169 / 0 |
| LUT / FF | 174591 / 161653 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `072cc6640d060cce720492c32bff33844743dd96`.

**Original evidence:** [C12.json](../../exp/configs/C12.json) | [C12.md](../../experiments/C12_continuous_wino_packing_T8_guard_retry/C12.md) | [config.json](../../experiments/C12_continuous_wino_packing_T8_guard_retry/config.json) | [metrics.json](../../experiments/C12_continuous_wino_packing_T8_guard_retry/metrics.json) | [csynth.rpt](../../experiments/C12_continuous_wino_packing_T8_guard_retry/csynth.rpt) | [csynth.log.txt](../../experiments/C12_continuous_wino_packing_T8_guard_retry/csynth.log.txt) | [csim.log.txt](../../experiments/C12_continuous_wino_packing_T8_guard_retry/csim.log.txt).

<a id="c08"></a>

### C08: Conv2 8-bit-weight combination, T8

**Based on:** [C07](#c07) (Design or parameter baseline); [E065](#e065) (Numerical reference or research motivation).

**Change:** Use validated 8-bit weights only in Conv2 to remove its 10-bit coefficient residual recovery.

**Effects and issues:** The 8000-bit Conv3 stream exceeds the tool limit; synthesis fails.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.770653995278335e-05; six-pixel border MSE=1.405191888267716e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.082567 dB; average delta PSNR against float = -0.07589 dB. Source: [experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json).

Tool: Vitis 2026.1; source commit: `016cb46553ae5468239d0d08f19d7d7303c8db33`.

**Original evidence:** [C08.json](../../exp/configs/C08.json) | [C08.md](../../experiments/C08_wino_conv2w8_continuous_T8/C08.md) | [config.json](../../experiments/C08_wino_conv2w8_continuous_T8/config.json) | [metrics.json](../../experiments/C08_wino_conv2w8_continuous_T8/metrics.json) | [csynth.log.txt](../../experiments/C08_wino_conv2w8_continuous_T8/csynth.log.txt) | [csim.log.txt](../../experiments/C08_wino_conv2w8_continuous_T8/csim.log.txt).

<a id="c09"></a>

### C09: Conv2 8-bit-weight combination, T4

**Based on:** [C08](#c08) (Design or parameter baseline).

**Change:** Scan greater parallelism with the same mixed precision.

**Effects and issues:** The same stream-width limit applies; C11 fixes it.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.770653995278335e-05; six-pixel border MSE=1.405191888267716e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.082567 dB; average delta PSNR against float = -0.07589 dB. Source: [experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json).

Tool: Vitis 2026.1; source commit: `65cd93d5bbff4397e1f71171a85bb7c2752d0b94`.

**Original evidence:** [C09.json](../../exp/configs/C09.json) | [C09.md](../../experiments/C09_wino_conv2w8_continuous_T4/C09.md) | [config.json](../../experiments/C09_wino_conv2w8_continuous_T4/config.json) | [metrics.json](../../experiments/C09_wino_conv2w8_continuous_T4/metrics.json) | [csynth.log.txt](../../experiments/C09_wino_conv2w8_continuous_T4/csynth.log.txt) | [csim.log.txt](../../experiments/C09_wino_conv2w8_continuous_T4/csim.log.txt).

<a id="c10"></a>

### C10: T8 mixed combination with split windows

**Based on:** [C08](#c08) (Retry after a fix).

**Change:** Use two synchronized 4000-bit channels while retaining quantization and MAC arithmetic.

**Effects and issues:** About 2.1302 ms and 520 DSPs, but 150,851 LUTs exceed budget.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 532562 / 532563 cycles |
| Registry time conversion | 2.130248 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 520 / 146 / 0 |
| LUT / FF | 150851 / 179452 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.770653995278335e-05; six-pixel border MSE=1.405191888267716e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.082567 dB; average delta PSNR against float = -0.07589 dB. Source: [experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json).

Tool: Vitis 2026.1; source commit: `d9747f754d5c180cfd4ee58398dd75f7eb34bf20`.

**Original evidence:** [C10.json](../../exp/configs/C10.json) | [C10.md](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/C10.md) | [config.json](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/config.json) | [metrics.json](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/metrics.json) | [csynth.rpt](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/csim.log.txt).

<a id="c11"></a>

### C11: T4 mixed combination with split windows

**Based on:** [C09](#c09) (Retry after a fix).

**Change:** Fix window representation at T4.

**Effects and issues:** The 1.0817 ms estimate needs 248,797 LUTs and 307,525 FFs, so it cannot be selected as a deployment candidate.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.392 ns |
| Latency / interval | 270418 / 270419 cycles |
| Registry time conversion | 1.081672 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1036 / 146 / 0 |
| LUT / FF | 248797 / 307525 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.392 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.770653995278335e-05; six-pixel border MSE=1.405191888267716e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.082567 dB; average delta PSNR against float = -0.07589 dB. Source: [experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json).

Tool: Vitis 2026.1; source commit: `708916fea3c5594cd8b5c43ebc16720f3af0e0b4`.

**Original evidence:** [C11.json](../../exp/configs/C11.json) | [C11.md](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/C11.md) | [config.json](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/config.json) | [metrics.json](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/metrics.json) | [csynth.rpt](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/csim.log.txt).

<a id="continuous"></a>

## Continuing B: pipelines, windows, and loader timing

Can direct convolution avoid pixel pipeline restarts, wide selectors, and a one-time loader critical path?

[Evolution graph](continuous.en.svg). Route evidence: [exp/prepare_arch_f.py](../../exp/prepare_arch_f.py) | [exp/build_arch_f.py](../../exp/build_arch_f.py) | [exp/prepare_split_windows.py](../../exp/prepare_split_windows.py) | [exp/prepare_rotating_arch.py](../../exp/prepare_rotating_arch.py) | [exp/prepare_ieee_network.py](../../exp/prepare_ieee_network.py) | [exp/prepare_load_arch.py](../../exp/prepare_load_arch.py).

<a id="f01"></a>

### F01: Shallow wide FIFOs in LUTRAM

**Based on:** [E048](#e048) (Design or parameter baseline); [E042](#e042) (Control experiment).

**Change:** Retain T16 and per-pixel scheduling; explicitly bind shallow wide feature FIFOs to LUTRAM.

**Effects and issues:** BRAM18K falls from 168 to 96 without reducing estimated cycles.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 2014678 / 2014679 cycles |
| Registry time conversion | 8.058712 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 96 / 0 |
| LUT / FF | 56081 / 62800 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `865a5949667e31cc0862cad5bd08e03bf766be79`.

**Original evidence:** [F01.json](../../exp/configs/F01.json) | [F01.md](../../experiments/F01_fifo_lutram_control/F01.md) | [config.json](../../experiments/F01_fifo_lutram_control/config.json) | [metrics.json](../../experiments/F01_fifo_lutram_control/metrics.json) | [csynth.rpt](../../experiments/F01_fifo_lutram_control/csynth.rpt) | [csynth.log.txt](../../experiments/F01_fifo_lutram_control/csynth.log.txt) | [csim.log.txt](../../experiments/F01_fifo_lutram_control/csim.log.txt).

<a id="f02"></a>

### F02: Conv3 line buffers in URAM

**Based on:** [E048](#e048) (Design or parameter baseline); [E042](#e042) (Control experiment).

**Change:** Move four wide buffer rows into 20 URAM blocks.

**Effects and issues:** BRAM18K falls to 132, but URAM depth utilization is low and latency is unchanged.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 2014678 / 2014679 cycles |
| Registry time conversion | 8.058712 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 132 / 20 |
| LUT / FF | 56007 / 62948 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `de27817cf1c748966fd19c6e90c90a0d12fbe080`.

**Original evidence:** [F02.json](../../exp/configs/F02.json) | [F02.md](../../experiments/F02_uram_line_control/F02.md) | [config.json](../../experiments/F02_uram_line_control/config.json) | [metrics.json](../../experiments/F02_uram_line_control/metrics.json) | [csynth.rpt](../../experiments/F02_uram_line_control/csynth.rpt) | [csynth.log.txt](../../experiments/F02_uram_line_control/csynth.log.txt) | [csim.log.txt](../../experiments/F02_uram_line_control/csim.log.txt).

<a id="f03"></a>

### F03: Continuous MACs with original padding

**Based on:** [E048](#e048) (Design or parameter baseline); [E070](#e070) (Numerical reference or research motivation); [F01](#f01) (Numerical reference or research motivation).

**Change:** Separate window generation and MAC engines; run all pixels/groups in continuous II1 loops with registered balanced adder trees.

**Effects and issues:** The tool rejects the 8000-bit Conv3 window stream. Original padding control may also stall finite FIFOs.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `e0da6b444ba3b62e3c529e90f87455e6f1035fa4`.

**Original evidence:** [F03.json](../../exp/configs/F03.json) | [F03.md](../../experiments/F03_continuous_T16_oldpad_4ns/F03.md) | [config.json](../../experiments/F03_continuous_T16_oldpad_4ns/config.json) | [metrics.json](../../experiments/F03_continuous_T16_oldpad_4ns/metrics.json) | [csynth.log.txt](../../experiments/F03_continuous_T16_oldpad_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/F03_continuous_T16_oldpad_4ns/csim.log.txt).

<a id="f04"></a>

### F04: Continuous MACs and online padding, T16

**Based on:** [F03](#f03) (Design or parameter baseline).

**Change:** Read later rows while emitting replicated boundaries to reduce whole-row read-then-write serial phases.

**Effects and issues:** The same stream-width limit applies. F09 later obtains valid synthesis.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `57104507d29b7245aa095a88f8c48871bb40b151`.

**Original evidence:** [F04.json](../../exp/configs/F04.json) | [F04.md](../../experiments/F04_continuous_T16_online_4ns/F04.md) | [config.json](../../experiments/F04_continuous_T16_online_4ns/config.json) | [metrics.json](../../experiments/F04_continuous_T16_online_4ns/metrics.json) | [csynth.log.txt](../../experiments/F04_continuous_T16_online_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/F04_continuous_T16_online_4ns/csim.log.txt).

<a id="f05"></a>

### F05: Continuous MACs and online padding, T8

**Based on:** [F04](#f04) (Design or parameter baseline).

**Change:** Increase parallelism and measure T8 time/resource costs.

**Effects and issues:** Stream width prevents valid synthesis in this run.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `26f6a403e116b267fff9fba42963cd50bd73aa41`.

**Original evidence:** [F05.json](../../exp/configs/F05.json) | [F05.md](../../experiments/F05_continuous_T8_online_4ns/F05.md) | [config.json](../../experiments/F05_continuous_T8_online_4ns/config.json) | [metrics.json](../../experiments/F05_continuous_T8_online_4ns/metrics.json) | [csynth.log.txt](../../experiments/F05_continuous_T8_online_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/F05_continuous_T8_online_4ns/csim.log.txt).

<a id="f06"></a>

### F06: Continuous T16, 3.33 ns

**Based on:** [F04](#f04) (Design or parameter baseline).

**Change:** Retain T16 and tighten the target period.

**Effects and issues:** Stream width still prevents synthesis; F11 fixes it.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `145d1d0801d2dedd3dfe9523a60934a5e584eeea`.

**Original evidence:** [F06.json](../../exp/configs/F06.json) | [F06.md](../../experiments/F06_continuous_T16_online_3p33ns/F06.md) | [config.json](../../experiments/F06_continuous_T16_online_3p33ns/config.json) | [metrics.json](../../experiments/F06_continuous_T16_online_3p33ns/metrics.json) | [csynth.log.txt](../../experiments/F06_continuous_T16_online_3p33ns/csynth.log.txt) | [csim.log.txt](../../experiments/F06_continuous_T16_online_3p33ns/csim.log.txt).

<a id="f07"></a>

### F07: Continuous T8, 3.33 ns

**Based on:** [F05](#f05) (Design or parameter baseline).

**Change:** Combine greater parallelism with a tighter target.

**Effects and issues:** Stream width remains invalid. This run provides no speed evidence.

**Status:** `fail` / Run failed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `060280c82e7b6fa07ab8d565f2545c10dc2740db`.

**Original evidence:** [F07.json](../../exp/configs/F07.json) | [F07.md](../../experiments/F07_continuous_T8_online_3p33ns/F07.md) | [config.json](../../experiments/F07_continuous_T8_online_3p33ns/config.json) | [metrics.json](../../experiments/F07_continuous_T8_online_3p33ns/metrics.json) | [csynth.log.txt](../../experiments/F07_continuous_T8_online_3p33ns/csynth.log.txt) | [csim.log.txt](../../experiments/F07_continuous_T8_online_3p33ns/csim.log.txt).

<a id="f08"></a>

### F08: Legal split windows, original padding

**Based on:** [F03](#f03) (Retry after a fix).

**Change:** Replace the complete window stream with two 4000-bit FIFOs while retaining continuous computation and original padding.

**Effects and issues:** About 4.1947 ms estimated. Dynamic Conv3 channel selectors and finite-FIFO costs motivate further work.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 1048677 / 1048678 cycles |
| Registry time conversion | 4.194708 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 96 / 0 |
| LUT / FF | 69362 / 106171 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c1ed3c5aab6433b4cc89a3f5ba3a0887edec5b82`.

**Original evidence:** [F08.json](../../exp/configs/F08.json) | [F08.md](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/F08.md) | [config.json](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/config.json) | [metrics.json](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/metrics.json) | [csynth.rpt](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/csim.log.txt).

<a id="f09"></a>

### F09: Legal split windows, online padding, T16

**Based on:** [F04](#f04) (Retry after a fix); [F08](#f08) (Control experiment).

**Change:** Retain synchronized split channels and measure online padding at T16.

**Effects and issues:** BRAM18K falls to 73. HLS cycles barely change; padding throughput needs RTL checks.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 1048687 / 1048688 cycles |
| Registry time conversion | 4.194748 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 73 / 0 |
| LUT / FF | 69179 / 106647 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `088f4fe4d5a3de629b3cada74e54464d0ff1fd7f`.

**Original evidence:** [F09.json](../../exp/configs/F09.json) | [F09.md](../../experiments/F09_continuous_T16_online_4ns_split4000/F09.md) | [config.json](../../experiments/F09_continuous_T16_online_4ns_split4000/config.json) | [metrics.json](../../experiments/F09_continuous_T16_online_4ns_split4000/metrics.json) | [csynth.rpt](../../experiments/F09_continuous_T16_online_4ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/F09_continuous_T16_online_4ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/F09_continuous_T16_online_4ns_split4000/csim.log.txt).

<a id="f10"></a>

### F10: Legal split windows, online padding, T8

**Based on:** [F05](#f05) (Retry after a fix).

**Change:** Fix wide streams and measure greater parallelism.

**Effects and issues:** Estimated time improves, but LUT/FF budgets are exceeded.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 528488 / 528489 cycles |
| Registry time conversion | 2.113952 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 96764 / 171240 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `71dda9c0c101064aee7d206a709a3153cd0e0fc3`.

**Original evidence:** [F10.json](../../exp/configs/F10.json) | [F10.md](../../experiments/F10_continuous_T8_online_4ns_split4000/F10.md) | [config.json](../../experiments/F10_continuous_T8_online_4ns_split4000/config.json) | [metrics.json](../../experiments/F10_continuous_T8_online_4ns_split4000/metrics.json) | [csynth.rpt](../../experiments/F10_continuous_T8_online_4ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/F10_continuous_T8_online_4ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/F10_continuous_T8_online_4ns_split4000/csim.log.txt).

<a id="f11"></a>

### F11: Legal continuous T16, 3.33 ns

**Based on:** [F06](#f06) (Retry after a fix); [F09](#f09) (Control experiment).

**Change:** Fix stream representation and measure the tighter T16 target.

**Effects and issues:** About 3.4922 ms estimated. Target frequency is not achieved physical frequency.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3.33 / 3.239 ns |
| Latency / interval | 1048700 / 1048701 cycles |
| Registry time conversion | 3.492171 ms (frame scope; converted at 3.33 ns) |
| DSP / BRAM18K / URAM | 505 / 73 / 0 |
| LUT / FF | 69427 / 121372 |
| Checked II targets | Met |

HLS 200-871: logic budget 3.33 - 0.899 = 2.431 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `37f7f6657d33d1ac38c51f1c7e20db3628835c3f`.

**Original evidence:** [F11.json](../../exp/configs/F11.json) | [F11.md](../../experiments/F11_continuous_T16_online_3p33ns_split4000/F11.md) | [config.json](../../experiments/F11_continuous_T16_online_3p33ns_split4000/config.json) | [metrics.json](../../experiments/F11_continuous_T16_online_3p33ns_split4000/metrics.json) | [csynth.rpt](../../experiments/F11_continuous_T16_online_3p33ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/F11_continuous_T16_online_3p33ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/F11_continuous_T16_online_3p33ns_split4000/csim.log.txt).

<a id="f12"></a>

### F12: Legal continuous T8, 3.33 ns

**Based on:** [F07](#f07) (Retry after a fix).

**Change:** Fix stream representation and measure the tighter T8 target.

**Effects and issues:** The 1.7599 ms estimate comes with excessive LUT/FF use.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3.33 / 3.239 ns |
| Latency / interval | 528501 / 528502 cycles |
| Registry time conversion | 1.75990833 ms (frame scope; converted at 3.33 ns) |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 97112 / 196314 |
| Checked II targets | Met |

HLS 200-871: logic budget 3.33 - 0.899 = 2.431 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `90c31a33cad1bf67abc99be3658d9879cf2ceb1e`.

**Original evidence:** [F12.json](../../exp/configs/F12.json) | [F12.md](../../experiments/F12_continuous_T8_online_3p33ns_split4000/F12.md) | [config.json](../../experiments/F12_continuous_T8_online_3p33ns_split4000/config.json) | [metrics.json](../../experiments/F12_continuous_T8_online_3p33ns_split4000/metrics.json) | [csynth.rpt](../../experiments/F12_continuous_T8_online_3p33ns_split4000/csynth.rpt) | [csynth.log.txt](../../experiments/F12_continuous_T8_online_3p33ns_split4000/csynth.log.txt) | [csim.log.txt](../../experiments/F12_continuous_T8_online_3p33ns_split4000/csim.log.txt).

<a id="f13"></a>

### F13: Rotating Conv3 channels, T16

**Based on:** [F09](#f09) (Design or parameter baseline); [F08](#f08) (Numerical reference or research motivation).

**Change:** Rotate used channels away each round so multipliers read fixed positions; retain registered adder trees.

**Effects and issues:** Dynamic selectors shrink and cycles remain similar. Float output conversion still limits the global timing estimate.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 1048687 / 1048688 cycles |
| Registry time conversion | 4.194748 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 505 / 73 / 0 |
| LUT / FF | 68903 / 106661 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `996788fa2117f80a869a3ed798f8d1208194086d`.

**Original evidence:** [F13.json](../../exp/configs/F13.json) | [F13.md](../../experiments/F13_rotate_c3_T16_tree1_4ns/F13.md) | [config.json](../../experiments/F13_rotate_c3_T16_tree1_4ns/config.json) | [metrics.json](../../experiments/F13_rotate_c3_T16_tree1_4ns/metrics.json) | [csynth.rpt](../../experiments/F13_rotate_c3_T16_tree1_4ns/csynth.rpt) | [csynth.log.txt](../../experiments/F13_rotate_c3_T16_tree1_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/F13_rotate_c3_T16_tree1_4ns/csim.log.txt).

<a id="f14"></a>

### F14: Rotating channels, T8, registered tree

**Based on:** [F13](#f13) (Design or parameter baseline).

**Change:** Change T to measure fixed-position reads at greater parallelism.

**Effects and issues:** LUT/FF budgets are exceeded.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT/FF; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 528488 / 528489 cycles |
| Registry time conversion | 2.113952 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 96488 / 171235 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `17b9dabda308f7a83b7d4e870f4ff028c75f6eaa`.

**Original evidence:** [F14.json](../../exp/configs/F14.json) | [F14.md](../../experiments/F14_rotate_c3_T8_tree1_4ns/F14.md) | [config.json](../../experiments/F14_rotate_c3_T8_tree1_4ns/config.json) | [metrics.json](../../experiments/F14_rotate_c3_T8_tree1_4ns/metrics.json) | [csynth.rpt](../../experiments/F14_rotate_c3_T8_tree1_4ns/csynth.rpt) | [csynth.log.txt](../../experiments/F14_rotate_c3_T8_tree1_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/F14_rotate_c3_T8_tree1_4ns/csim.log.txt).

<a id="f15"></a>

### F15: Rotating channels, T8, unregistered tree

**Based on:** [F14](#f14) (Design or parameter baseline).

**Change:** Bind adder-tree latency to zero to isolate register-stage effects on FFs and timing.

**Effects and issues:** FF use falls but LUTs exceed budget. Removing registers does not guarantee timing.

**Status:** `infeasible` / Resource/performance gate not met; scope `frame`; step `csim_csynth`.
Additional checks: Over budget: LUT; HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 4 / 3.239 ns |
| Latency / interval | 528481 / 528482 cycles |
| Registry time conversion | 2.113924 ms (frame scope; converted at 4 ns) |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 101994 / 86073 |
| Checked II targets | Met |

HLS 200-871: logic budget 4 - 1.08 = 2.92 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `3dbe07a95f51308c6af8ec0c3919f0b683657749`.

**Original evidence:** [F15.json](../../exp/configs/F15.json) | [F15.md](../../experiments/F15_rotate_c3_T8_tree0_4ns/F15.md) | [config.json](../../experiments/F15_rotate_c3_T8_tree0_4ns/config.json) | [metrics.json](../../experiments/F15_rotate_c3_T8_tree0_4ns/metrics.json) | [csynth.rpt](../../experiments/F15_rotate_c3_T8_tree0_4ns/csynth.rpt) | [csynth.log.txt](../../experiments/F15_rotate_c3_T8_tree0_4ns/csynth.log.txt) | [csim.log.txt](../../experiments/F15_rotate_c3_T8_tree0_4ns/csim.log.txt).

<a id="f16"></a>

### F16: Exact float-output construction PE

**Based on:** [F08](#f08) (Numerical reference or research motivation).

**Change:** Since all raw 10-bit outputs are exactly representable as float, construct sign/exponent/mantissa directly.

**Effects and issues:** SDK namespace and ap_int conditional-expression type mismatches cause compilation failure.

**Status:** `fail` / Run failed; scope `PE`; step `csim`.

Tool: Vitis 2026.1; source commit: `4f32b356dbf645918f7fc027d284cf67298b3a4a`.

**Original evidence:** [F16.json](../../exp/configs/F16.json) | [F16.md](../../experiments/F16_ieee_decode_bit_exact/F16.md) | [config.json](../../experiments/F16_ieee_decode_bit_exact/config.json) | [metrics.json](../../experiments/F16_ieee_decode_bit_exact/metrics.json) | [csim.log.txt](../../experiments/F16_ieee_decode_bit_exact/csim.log.txt).

<a id="f17"></a>

### F17: Ordinary float-conversion PE control

**Based on:** [F16](#f16) (Control experiment).

**Change:** Measure the original conversion/division on the same input set.

**Effects and issues:** Compilation problems in the probe project require a separate retry.

**Status:** `fail` / Run failed; scope `PE`; step `csim`.

Tool: Vitis 2026.1; source commit: `a5d31057b4d36fec23d2b44c5e7e8a8a5b37bb4b`.

**Original evidence:** [F17.json](../../exp/configs/F17.json) | [F17.md](../../experiments/F17_ieee_decode_legacy_control/F17.md) | [config.json](../../experiments/F17_ieee_decode_legacy_control/config.json) | [metrics.json](../../experiments/F17_ieee_decode_legacy_control/metrics.json) | [csim.log.txt](../../experiments/F17_ieee_decode_legacy_control/csim.log.txt).

<a id="f18"></a>

### F18: Exact-float SDK fix

**Based on:** [F16](#f16) (Retry after a fix).

**Change:** Fix fp_struct naming and explicit sign branches for the installed SDK.

**Effects and issues:** Design/test translation units share a name and produce duplicate objects; linking fails.

**Status:** `fail` / Run failed; scope `PE`; step `csim`.

Tool: Vitis 2026.1; source commit: `5b1e51fd0433bb6a2a011b4960a05f8600baf7ff`.

**Original evidence:** [F18.json](../../exp/configs/F18.json) | [F18.md](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/F18.md) | [config.json](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/config.json) | [metrics.json](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/metrics.json) | [csim.log.txt](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/csim.log.txt).

<a id="f19"></a>

### F19: Ordinary-conversion SDK fix control

**Based on:** [F17](#f17) (Retry after a fix).

**Change:** Retain ordinary conversion in the corrected probe project.

**Effects and issues:** Object-name collisions persist; F21 fixes them.

**Status:** `fail` / Run failed; scope `PE`; step `csim`.

Tool: Vitis 2026.1; source commit: `3d8f8ffafd4d6ec4329a56554aeab6749475aa5e`.

**Original evidence:** [F19.json](../../exp/configs/F19.json) | [F19.md](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/F19.md) | [config.json](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/config.json) | [metrics.json](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/metrics.json) | [csim.log.txt](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/csim.log.txt).

<a id="f20"></a>

### F20: Valid exact-float construction probe

**Based on:** [F18](#f18) (Retry after a fix).

**Change:** Rename only the design translation unit to kernel.cpp and exhaust all 1024 output encodings.

**Effects and issues:** Zero DSPs and 242 LUTs. This measures only output encoding; the network critical path may shift elsewhere.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3.33 / 2.051 ns |
| Latency / interval | 1027 / 1024 cycles |
| Registry time conversion | 0.00341991 ms (PE scope; converted at 3.33 ns) |
| DSP / BRAM18K / URAM | 0 / 0 / 0 |
| LUT / FF | 242 / 52 |
| Checked II targets | Met |

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `8aaeb2c5e62cc56295c0a2c5c0fcc71dffddda65`.

**Original evidence:** [F20.json](../../exp/configs/F20.json) | [F20.md](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/F20.md) | [config.json](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/config.json) | [metrics.json](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/metrics.json) | [csynth.rpt](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/csynth.rpt) | [csynth.log.txt](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/csynth.log.txt) | [csim.log.txt](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/csim.log.txt).

<a id="f21"></a>

### F21: Valid ordinary-conversion control

**Based on:** [F19](#f19) (Retry after a fix); [F20](#f20) (Control experiment).

**Change:** Measure ordinary float conversion with matching interfaces and samples.

**Effects and issues:** Three DSPs and a 3.239 ns estimated path provide a valid control for F20.

**Status:** `pass` / Local experiment passed; scope `PE`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3.33 / 3.239 ns |
| Latency / interval | 1039 / 1024 cycles |
| Registry time conversion | 0.00345987 ms (PE scope; converted at 3.33 ns) |
| DSP / BRAM18K / URAM | 3 / 0 / 0 |
| LUT / FF | 220 / 343 |
| Checked II targets | Met |

HLS 200-871: logic budget 3.33 - 0.899 = 2.431 ns; maximum warned path estimate 3.239 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Tool: Vitis 2026.1; source commit: `ef39b7f46dd04f73cf3e5633ec9acd94bc4f77ae`.

**Original evidence:** [F21.json](../../exp/configs/F21.json) | [F21.md](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/F21.md) | [config.json](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/config.json) | [metrics.json](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/metrics.json) | [csynth.rpt](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/csynth.rpt) | [csynth.log.txt](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/csynth.log.txt) | [csim.log.txt](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/csim.log.txt).

<a id="f22"></a>

### F22: Integrate exact output encoding, 3 ns

**Based on:** [F13](#f13) (Design or parameter baseline); [F20](#f20) (Integrate an existing module).

**Change:** Replace only fixed-point-to-float output encoding, retaining 10-bit values and continuous inference engines.

**Effects and issues:** DSPs fall from 505 to 502. Loader addresses and inference control may limit the clock after conversion is removed.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 3 / 2.377 ns |
| Latency / interval | 1048711 / 1048712 cycles |
| Registry time conversion | 3.146133 ms (frame scope; converted at 3 ns) |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 69483 / 121696 |
| Checked II targets | Met |

HLS 200-871: logic budget 3 - 0.81 = 2.19 ns; maximum warned path estimate 2.377 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `c6e962c679f9bbe81e0c0656b1f308913796b06d`.

**Original evidence:** [F22.json](../../exp/configs/F22.json) | [F22.md](../../experiments/F22_continuous_ieee_T16_3ns/F22.md) | [config.json](../../experiments/F22_continuous_ieee_T16_3ns/config.json) | [metrics.json](../../experiments/F22_continuous_ieee_T16_3ns/metrics.json) | [csynth.rpt](../../experiments/F22_continuous_ieee_T16_3ns/csynth.rpt) | [csynth.log.txt](../../experiments/F22_continuous_ieee_T16_3ns/csynth.log.txt) | [csim.log.txt](../../experiments/F22_continuous_ieee_T16_3ns/csim.log.txt).

<a id="f23"></a>

### F23: Integrate exact output encoding, 2.5 ns

**Based on:** [F13](#f13) (Design or parameter baseline); [F20](#f20) (Integrate an existing module); [F22](#f22) (Control experiment).

**Change:** Tighten the target to locate the global critical path.

**Effects and issues:** Address multiplication in the one-time Conv1 weight loader sets the global estimate to 2.822 ns.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 2.5 / 2.822 ns |
| Latency / interval | 1048730 / 1048731 cycles |
| Registry time conversion | 2.95951606 ms (frame scope; converted at 2.822 ns) |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 70449 / 125618 |
| Checked II targets | Met |

HLS 200-871: logic budget 2.5 - 0.675 = 1.825 ns; maximum warned path estimate 2.822 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `42ffdd70e9363069b79ac6eac25b3c6ec1fe0850`.

**Original evidence:** [F23.json](../../exp/configs/F23.json) | [F23.md](../../experiments/F23_continuous_ieee_T16_2p5ns/F23.md) | [config.json](../../experiments/F23_continuous_ieee_T16_2p5ns/config.json) | [metrics.json](../../experiments/F23_continuous_ieee_T16_2p5ns/metrics.json) | [csynth.rpt](../../experiments/F23_continuous_ieee_T16_2p5ns/csynth.rpt) | [csynth.log.txt](../../experiments/F23_continuous_ieee_T16_2p5ns/csynth.log.txt) | [csim.log.txt](../../experiments/F23_continuous_ieee_T16_2p5ns/csim.log.txt).

<a id="f24"></a>

### F24: Explicit three-dimensional loader indices

**Based on:** [F23](#f23) (Design or parameter baseline).

**Change:** Replace division/modulo-derived addresses with output-channel/kernel-row/kernel-column counters.

**Effects and issues:** The address multiplier disappears, but automatically flattened counter control still has a 2.699 ns estimate.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 2.5 / 2.699 ns |
| Latency / interval | 1048723 / 1048724 cycles |
| Registry time conversion | 2.83050338 ms (frame scope; converted at 2.699 ns) |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 69290 / 124577 |
| Checked II targets | Met |

HLS 200-871: logic budget 2.5 - 0.675 = 1.825 ns; maximum warned path estimate 2.699 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `192c24087f0d50710dc5461fa984e3149e864dd4`.

**Original evidence:** [F24.json](../../exp/configs/F24.json) | [F24.md](../../experiments/F24_affine_weight_loader_T16_2p5ns/F24.md) | [config.json](../../experiments/F24_affine_weight_loader_T16_2p5ns/config.json) | [metrics.json](../../experiments/F24_affine_weight_loader_T16_2p5ns/metrics.json) | [csynth.rpt](../../experiments/F24_affine_weight_loader_T16_2p5ns/csynth.rpt) | [csynth.log.txt](../../experiments/F24_affine_weight_loader_T16_2p5ns/csynth.log.txt) | [csim.log.txt](../../experiments/F24_affine_weight_loader_T16_2p5ns/csim.log.txt).

<a id="f25"></a>

### F25: Disable weight-loader loop flattening

**Based on:** [F24](#f24) (Design or parameter baseline).

**Change:** Add LOOP_FLATTEN off only to the Conv1 loader inner loop; retain all inference engines.

**Effects and issues:** About 2.64226 ms and 73 BRAM18K blocks. Loading cycles increase slightly; 2.5 ns still has HLS timing warnings after uncertainty.

**Status:** `provisional` / Candidate; final acceptance pending; scope `frame`; step `csim_csynth`.
Additional checks: HLS timing warning.

| HLS measurement/estimate | Value |
| --- | --- |
| Target / estimated period | 2.5 / 2.377 ns |
| Latency / interval | 1056904 / 1056905 cycles |
| Registry time conversion | 2.64226 ms (frame scope; converted at 2.5 ns) |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 69976 / 125404 |
| Checked II targets | Met |

HLS 200-871: logic budget 2.5 - 0.675 = 1.825 ns; maximum warned path estimate 2.377 ns. See the original synthesis log.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `ab5c5e94beb6f6f1374e9bb547b27bf6fe1e055a`.

**Original evidence:** [F25.json](../../exp/configs/F25.json) | [F25.md](../../experiments/F25_nested_weight_loader_T16_2p5ns/F25.md) | [config.json](../../experiments/F25_nested_weight_loader_T16_2p5ns/config.json) | [metrics.json](../../experiments/F25_nested_weight_loader_T16_2p5ns/metrics.json) | [csynth.rpt](../../experiments/F25_nested_weight_loader_T16_2p5ns/csynth.rpt) | [csynth.log.txt](../../experiments/F25_nested_weight_loader_T16_2p5ns/csynth.log.txt) | [csim.log.txt](../../experiments/F25_nested_weight_loader_T16_2p5ns/csim.log.txt).

<a id="verification"></a>

## Candidate verification: separate acceptance steps

What is established for function, RTL cycles, routed timing, and board execution?

[Evolution graph](verification.en.svg). Route evidence: [exp/prepare_final_arch.py](../../exp/prepare_final_arch.py) | [exp/prepare_impl_retries.py](../../exp/prepare_impl_retries.py) | [experiments/final_selection.json](../../experiments/final_selection.json) | [experiments/F82_final_cosim_F25/reports/sim/srcnn_cosim.rpt](../../experiments/F82_final_cosim_F25/reports/sim/srcnn_cosim.rpt).

<a id="e069"></a>

### E069: Multi-image acceptance for E043

**Based on:** [E043](#e043) (Verify the same design); [E017](#e017) (Numerical reference or research motivation).

**Change:** Compare the best first-round candidate bit for bit on all 13 supplied images.

**Effects and issues:** Multi-image checks pass, but comic remains missing. This is not board acceptance.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: [experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json).

Tool: Vitis 2026.1; source commit: `ce0fa16f724dfd50c87fe09cb64e3320bf77fce7`.

**Original evidence:** [E069.json](../../exp/configs/E069.json) | [E069.md](../../experiments/E069_final_candidate_all_supplied/E069.md) | [config.json](../../experiments/E069_final_candidate_all_supplied/config.json) | [metrics.json](../../experiments/E069_final_candidate_all_supplied/metrics.json) | [csim.log.txt](../../experiments/E069_final_candidate_all_supplied/csim.log.txt).

<a id="e070"></a>

### E070: Physical implementation of E039

**Based on:** [E039](#e039) (Verify the same design).

**Change:** Run Vivado synthesis, placement, and routing; record actual utilization and timing.

**Effects and issues:** Implementation completes, but WNS=-1.277 ns at 10 ns means timing fails.

**Status:** `impl_complete` / Implementation complete; check timing separately; scope `frame`; step `impl`.
Additional checks: Routed timing failed.

Inherited HLS estimates come from [E039](#e039); they are not new measurements from this step.

Implementation: WNS=-1.277 ns; TNS=-1206.071 ns; timing_met=false. Actual DSP / BRAM36 / URAM / LUT / FF = 270 / 31 / 0 / 20454 / 33844. BRAM36 and HLS BRAM18K are different units.

Tool: Vitis 2026.1; source commit: `2e47aa68288ac1c912a8563d4452474b785a9a7d`.

**Original evidence:** [E070.json](../../exp/configs/E070.json) | [E070.md](../../experiments/E070_first_feasible_implementation/E070.md) | [config.json](../../experiments/E070_first_feasible_implementation/config.json) | [metrics.json](../../experiments/E070_first_feasible_implementation/metrics.json) | [verification.json](../../experiments/E070_first_feasible_implementation/verification.json) | [impl.log.txt](../../experiments/E070_first_feasible_implementation/impl.log.txt) | [srcnn_timing_routed.rpt](../../experiments/E070_first_feasible_implementation/reports/impl/srcnn_timing_routed.rpt) | [srcnn_utilization_routed.rpt](../../experiments/E070_first_feasible_implementation/reports/impl/srcnn_utilization_routed.rpt).

<a id="f80"></a>

### F80: F25 C simulation on 13 images

**Based on:** [F25](#f25) (Verify the same design); [E017](#e017) (Numerical reference or research motivation).

**Change:** Check all supplied Set14 pairs and two butterfly frames, comparing every output bit with the independent fixed-point reference.

**Effects and issues:** The average quality gate passes, but missing comic prevents full 14-image acceptance.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: current simulation (13 images; see original archive).

Tool: Vitis 2026.1; source commit: `f503f1ea505bebf5e425862603c52e70d4bf260e`.

**Original evidence:** [F80.json](../../exp/configs/F80.json) | [F80.md](../../experiments/F80_final_all_supplied_F25/F80.md) | [config.json](../../experiments/F80_final_all_supplied_F25/config.json) | [metrics.json](../../experiments/F80_final_all_supplied_F25/metrics.json) | [csim.log.txt](../../experiments/F80_final_all_supplied_F25/csim.log.txt).

<a id="f81"></a>

### F81: F25 Vivado implementation

**Based on:** [F25](#f25) (Verify the same design); [F80](#f80) (Numerical reference or research motivation).

**Change:** Run physical implementation in an independent workspace.

**Effects and issues:** Kernel logs confirm host OOM kills synthesis. No routed resource/timing results exist.

**Status:** `fail` / Run failed; scope `frame`; step `impl`.
Additional checks: Host OOM.

Inherited HLS estimates come from [F25](#f25); they are not new measurements from this step.

Tool: Vitis 2026.1; source commit: `511c75f3652dd9a522e3592d1285203bc0b8eb07`.

**Original evidence:** [F81.json](../../exp/configs/F81.json) | [F81.md](../../experiments/F81_final_impl_F25/F81.md) | [config.json](../../experiments/F81_final_impl_F25/config.json) | [metrics.json](../../experiments/F81_final_impl_F25/metrics.json) | [verification.json](../../experiments/F81_final_impl_F25/verification.json) | [impl.log.txt](../../experiments/F81_final_impl_F25/impl.log.txt) | [kernel_oom.txt](../../experiments/F81_final_impl_F25/diagnostics/kernel_oom.txt).

<a id="f82"></a>

### F82: F25 two-frame C/RTL co-simulation

**Based on:** [F25](#f25) (Verify the same design); [F80](#f80) (Numerical reference or research motivation).

**Change:** Run the same F25 RTL on two frames with finite-FIFO profiling and deadlock checks.

**Effects and issues:** Pass; maximum latency is 1,068,183 cycles, about 1.07% above synthesis, with about 103 minutes wall time. Functionality does not prove physical timing.

**Status:** `cosim_complete` / RTL co-simulation complete; scope `frame`; step `cosim`.

Inherited HLS estimates come from [F25](#f25); they are not new measurements from this step.

RTL: Pass; maximum latency 1068183 cycles; maximum interval 1068212 cycles; 1.0672% more cycles than HLS.

Tool: Vitis 2026.1; source commit: `c46ae06ec1080ca1af3fe48c4131e089d2ec95f9`.

**Original evidence:** [F82.json](../../exp/configs/F82.json) | [F82.md](../../experiments/F82_final_cosim_F25/F82.md) | [config.json](../../experiments/F82_final_cosim_F25/config.json) | [metrics.json](../../experiments/F82_final_cosim_F25/metrics.json) | [verification.json](../../experiments/F82_final_cosim_F25/verification.json) | [cosim.log.txt](../../experiments/F82_final_cosim_F25/cosim.log.txt) | [srcnn_cosim.rpt](../../experiments/F82_final_cosim_F25/reports/sim/srcnn_cosim.rpt).

<a id="f83"></a>

### F83: F24 C simulation on 13 images

**Based on:** [F24](#f24) (Verify the same design); [E017](#e017) (Numerical reference or research motivation).

**Change:** Validate the second candidate on the complete supplied image set.

**Effects and issues:** Outputs match the reference bit for bit. Precision matches F25, while hardware verification remains separate.

**Status:** `csim_pass` / C simulation passed; scope `frame`; step `csim`.

Function: C simulation passed; bit_exact=true; butterfly MSE=1.8197758558556394e-05; six-pixel border MSE=1.661846957728205e-05. See the original tests for bit_exact/MSE comparison targets; equality to a fixed-point reference does not mean equality to floating-point golden output.

Quality: average PSNR against GT = 29.088943 dB; average delta PSNR against float = -0.069514 dB. Source: current simulation (13 images; see original archive).

Tool: Vitis 2026.1; source commit: `be7c2bc15393168a25df52ce90a7765015cb39f0`.

**Original evidence:** [F83.json](../../exp/configs/F83.json) | [F83.md](../../experiments/F83_final_all_supplied_F24/F83.md) | [config.json](../../experiments/F83_final_all_supplied_F24/config.json) | [metrics.json](../../experiments/F83_final_all_supplied_F24/metrics.json) | [csim.log.txt](../../experiments/F83_final_all_supplied_F24/csim.log.txt).

<a id="f84"></a>

### F84: F24 Vivado implementation

**Based on:** [F24](#f24) (Verify the same design); [F83](#f83) (Numerical reference or research motivation).

**Change:** Independently measure the second candidate's physical results.

**Effects and issues:** Host OOM interrupts the run. No routed results exist, so timing cannot be marked passed.

**Status:** `fail` / Run failed; scope `frame`; step `impl`.
Additional checks: Host OOM.

Inherited HLS estimates come from [F24](#f24); they are not new measurements from this step.

Tool: Vitis 2026.1; source commit: `cb2bcc80a424bb07cf6fe41abcf8c160f61ac3ad`.

**Original evidence:** [F84.json](../../exp/configs/F84.json) | [F84.md](../../experiments/F84_final_impl_F24/F84.md) | [config.json](../../experiments/F84_final_impl_F24/config.json) | [metrics.json](../../experiments/F84_final_impl_F24/metrics.json) | [verification.json](../../experiments/F84_final_impl_F24/verification.json) | [impl.log.txt](../../experiments/F84_final_impl_F24/impl.log.txt) | [kernel_oom.txt](../../experiments/F84_final_impl_F24/diagnostics/kernel_oom.txt).

<a id="f85"></a>

### F85: F24 two-frame RTL plan

**Based on:** [F24](#f24) (Verify the same design); [F83](#f83) (Numerical reference or research motivation).

**Change:** Plan finite-FIFO, state-reset, and RTL-cycle validation.

**Effects and issues:** This snapshot contains a plan only; no completed result is archived.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Inherited HLS estimates come from [F24](#f24); they are not new measurements from this step.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F85.json](../../exp/configs/F85.json).

<a id="f86"></a>

### F86: F23 multi-image C-simulation plan

**Based on:** [F23](#f23) (Verify the same design); [E017](#e017) (Numerical reference or research motivation).

**Change:** Plan acceptance of the third candidate on all supplied images.

**Effects and issues:** No run results exist in this snapshot.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F86.json](../../exp/configs/F86.json).

<a id="f87"></a>

### F87: F23 Vivado implementation plan

**Based on:** [F23](#f23) (Verify the same design); [F86](#f86) (Numerical reference or research motivation).

**Change:** Plan routed utilization and timing measurements for the third candidate.

**Effects and issues:** No completed report exists in this snapshot.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Inherited HLS estimates come from [F23](#f23); they are not new measurements from this step.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F87.json](../../exp/configs/F87.json).

<a id="f88"></a>

### F88: F23 two-frame RTL plan

**Based on:** [F23](#f23) (Verify the same design); [F86](#f86) (Numerical reference or research motivation).

**Change:** Plan finite-FIFO RTL verification for the third candidate.

**Effects and issues:** No completed result exists in this snapshot.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Inherited HLS estimates come from [F23](#f23); they are not new measurements from this step.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F88.json](../../exp/configs/F88.json).

<a id="f89"></a>

### F89: F25 serial implementation retry plan

**Based on:** [F81](#f81) (Retry after a fix); [F25](#f25) (Verify the same design).

**Change:** Retain the generated IP/BD flow and limit Vivado internal threads through a per-run Tcl hook.

**Effects and issues:** This addresses host memory pressure; estimates cannot replace actual routed results.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Inherited HLS estimates come from [F25](#f25); they are not new measurements from this step.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F89.json](../../exp/configs/F89.json).

<a id="f90"></a>

### F90: F24 serial implementation retry plan

**Based on:** [F84](#f84) (Retry after a fix); [F24](#f24) (Verify the same design).

**Change:** Apply the same flow control to the second candidate.

**Effects and issues:** No actual result exists in this snapshot; timing and precision gates are unchanged.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Inherited HLS estimates come from [F24](#f24); they are not new measurements from this step.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F90.json](../../exp/configs/F90.json).

<a id="f91"></a>

### F91: F23 serial implementation plan

**Based on:** [F87](#f87) (Retry after a fix); [F23](#f23) (Verify the same design).

**Change:** Plan the same thread-limited verification flow for the third candidate.

**Effects and issues:** F87 is also a plan. This relationship describes verification flow and does not claim F87 already failed from OOM.

**Status:** `planned` / Prepared; no archived measurements; scope `frame`; step `plan`.
Additional checks: No archived measurements.

Inherited HLS estimates come from [F23](#f23); they are not new measurements from this step.

Planned estimates remain hypotheses in the configuration/data.en.json. They are not displayed as measured resources, II, or latency.

Tool: Vitis version not recorded/not applicable; source commit: run source commit not yet archived.

**Original evidence:** [F91.json](../../exp/configs/F91.json).
