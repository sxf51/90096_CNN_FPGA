# 全部实验：来源、调整、效果与问题

快照：`800a87a`；153 项，142 项有结果档案，11 项仅有计划/准备。

有结果档案包括失败、超时和无效配置，不表示全部成功。箭头表示设计、参数、模块与验收依赖，不能当成逐次 Git clone 历史。

HLS 时间沿用注册表公式：cycles × max(目标周期, HLS 估计周期) / 10⁶ ms。这个估计不证明 uncertainty 后时序达标，也不是板端测量。资源预算为 DSP≤1248、BRAM18K≤288、URAM≤64、LUT≤81984、FF≤163968；后两项是全芯片容量的 70%。

普通综合记录的多图质量可能引用独立精度参考；下方会标出来源。本次逐图验收范围以原始配置的 image_count 为准。实现/RTL 记录继承的 HLS 指标只保存在 data.json 的 registry_raw，展示时使用该步骤的真实测量。

[返回说明](../0004-experiment-evolution.md) · [总览图](overview.svg) · [机器可读数据](data.json)

## 路线索引

| 路线 | 编号 | |
| --- | --- | --- |
| [基线与精度：先确定可以改变什么](#precision) | [E000](#e000) [E010](#e010) [E011](#e011) [E012](#e012) [E013](#e013) [E014](#e014) [E018](#e018) [E015](#e015) [E016](#e016) [E017](#e017) [E019](#e019) [E049](#e049) [E062](#e062) [E065](#e065) [E066](#e066) [E071](#e071) | [图](precision.svg) |
| [编译器对照：保留整幅特征图会怎样](#compiler) | [E020](#e020) [E021](#e021) [E022](#e022) [E023](#e023) [E024](#e024) [E025](#e025) [E026](#e026) [E027](#e027) [E028](#e028) [E029](#e029) [E032](#e032) | [图](compiler.svg) |
| [第一轮流式架构：消除完整中间图](#streaming) | [E030](#e030) [E031](#e031) [E033](#e033) [E046](#e046) [E063](#e063) [E047](#e047) [E048](#e048) [E050](#e050) [E060](#e060) [E056](#e056) | [图](streaming.svg) |
| [参数扫描：位宽固定后寻找可行并行度与存储](#scans) | [E034](#e034) [E035](#e035) [E044](#e044) [E045](#e045) [E057](#e057) [E058](#e058) [E059](#e059) [E036](#e036) [E037](#e037) [E038](#e038) [E039](#e039) [E040](#e040) [E064](#e064) [E067](#e067) [E041](#e041) [E042](#e042) [E043](#e043) | [图](scans.svg) |
| [乘法器小实验：解释 HLS 的映射选择](#micro) | [E051](#e051) [E052](#e052) [E053](#e053) [E054](#e054) [E055](#e055) | [图](micro.svg) |
| [A：Packing，从局部精确性到整网成本](#packing) | [P01](#p01) [P02](#p02) [P03](#p03) [P04](#p04) [P05](#p05) [P06](#p06) [P07](#p07) [P08](#p08) [P09](#p09) [P10](#p10) [P11](#p11) [P12](#p12) [P13](#p13) [P14](#p14) [P15](#p15) [P16](#p16) | [图](packing.svg) |
| [C：Gather 与 Scatter 的存储/控制取舍](#scatter) | [G01](#g01) [G02](#g02) [G03](#g03) | [图](scatter.svg) |
| [存储路线：整网数据流、外存探针和分块融合](#memory) | [S01](#s01) [S02](#s02) [S03](#s03) [S04](#s04) [S05](#s05) [S06](#s06) | [图](memory.svg) |
| [D：Winograd，从精确变换到连续调度和权重银行](#winograd) | [W01](#w01) [W02](#w02) [W03](#w03) [W04](#w04) [W05](#w05) [W06](#w06) [W07](#w07) [W08](#w08) [W09](#w09) [W10](#w10) [W11](#w11) [W12](#w12) [W13](#w13) [W14](#w14) [W15](#w15) [W16](#w16) [W17](#w17) [W18](#w18) | [图](winograd.svg) |
| [组合路线：Winograd 与 Packing 能否叠加收益](#combination) | [C01](#c01) [C02](#c02) [C03](#c03) [C04](#c04) [C05](#c05) [C06](#c06) [C07](#c07) [C12](#c12) [C08](#c08) [C09](#c09) [C10](#c10) [C11](#c11) | [图](combination.svg) |
| [B 的后续：连续流水、窗口控制和加载时序](#continuous) | [F01](#f01) [F02](#f02) [F03](#f03) [F04](#f04) [F05](#f05) [F06](#f06) [F07](#f07) [F08](#f08) [F09](#f09) [F10](#f10) [F11](#f11) [F12](#f12) [F13](#f13) [F14](#f14) [F15](#f15) [F16](#f16) [F17](#f17) [F18](#f18) [F19](#f19) [F20](#f20) [F21](#f21) [F22](#f22) [F23](#f23) [F24](#f24) [F25](#f25) | [图](continuous.svg) |
| [候选验证：同一设计的不同验收步骤](#verification) | [E069](#e069) [E070](#e070) [F80](#f80) [F81](#f81) [F82](#f82) [F83](#f83) [F84](#f84) [F85](#f85) [F86](#f86) [F87](#f87) [F88](#f88) [F89](#f89) [F90](#f90) [F91](#f91) | [图](verification.svg) |

<a id="precision"></a>

## 基线与精度：先确定可以改变什么

原版是否正确、能否装下？减少位宽会损失多少图像质量？

[演进图](precision.svg)；路线依据：[experiments/E010_precision_scan/E010.md](../../experiments/E010_precision_scan/E010.md) · [exp/prepare_mix.py](../../exp/prepare_mix.py) · [exp/prepare_mixed_arch.py](../../exp/prepare_mixed_arch.py) · [exp/model/prerequisite_ranges.py](../../exp/model/prerequisite_ranges.py)。

<a id="e000"></a>

### E000：原始浮点基线

**基于：** 原始 src/ 基线，没有前置实验。

**调整：** 保持 src/、网络结构及边缘复制不变，测量功能和综合规模。

**效果与问题：** 两张完整中间图使 BRAM 严重超量；C 仿真正确不能说明器件容得下。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.331 ns |
| 延迟 / 间隔 | 1960113853 / 1960113854 cycles |
| 注册表换算时间 | 19601.13853 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.158458 dB；相对浮点平均 ΔPSNR=0 dB。来源：本次仿真（13 张；见原始记录）。

工具：Vitis 2026.1；源码提交：`1f025dccb9e5fb187213ff4aea10887e617ab078`。

**原始证据：** [E000.json](../../exp/configs/E000.json) · [E000.md](../../experiments/E000_golden_baseline/E000.md) · [config.json](../../experiments/E000_golden_baseline/config.json) · [metrics.json](../../experiments/E000_golden_baseline/metrics.json) · [csynth.rpt](../../experiments/E000_golden_baseline/csynth.rpt) · [csynth.log.txt](../../experiments/E000_golden_baseline/csynth.log.txt) · [csim.log.txt](../../experiments/E000_golden_baseline/csim.log.txt)。

<a id="e010"></a>

### E010：逐层范围与位宽扫描

**基于：** [E000](#e000)（数值依据或研究启发）。

**调整：** 在 13 张输入上统计范围，并扫描 16/12/10/8 位权重与激活组合。

**效果与问题：** 10/10 位平均 PSNR 降幅约 0.0695 dB；8/8 位降约 5.18 dB。缺 comic，尚非完整 Set14。

**记录状态：** `analysis_complete` / 分析完成；范围 `analysis`；步骤 `analysis`。

工具：未记录 Vitis 版本/不适用；源码提交：`1f025dccb9e5fb187213ff4aea10887e617ab078`。

**原始证据：** [E010.md](../../experiments/E010_precision_scan/E010.md) · [config.json](../../experiments/E010_precision_scan/config.json)。

<a id="e011"></a>

### E011：实际 ap_fixed：16/16 位

**基于：** [E010](#e010)（数值依据或研究启发）。

**调整：** 用 AMD 数据类型复核软件量化模型，计划覆盖所有已有图像。

**效果与问题：** C 仿真失败；后续重试保留独立编号，不把它当成通过记录。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`653125de033085b7c7288effee7f6b5962bb4706`。

**原始证据：** [E011.json](../../exp/configs/E011.json) · [E011.md](../../experiments/E011_apfixed_w16a16/E011.md) · [config.json](../../experiments/E011_apfixed_w16a16/config.json) · [metrics.json](../../experiments/E011_apfixed_w16a16/metrics.json) · [csim.log.txt](../../experiments/E011_apfixed_w16a16/csim.log.txt)。

<a id="e012"></a>

### E012：实际 ap_fixed：10/10 位

**基于：** [E010](#e010)（数值依据或研究启发）。

**调整：** 验证完整定点卷积的 butterfly 输出。

**效果与问题：** 本次 C 仿真失败，数值结论由 E017/E019 的有效验证补齐。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`3c13a0f643c80790f84b4dd4e14b99790f484cb8`。

**原始证据：** [E012.json](../../exp/configs/E012.json) · [E012.md](../../experiments/E012_apfixed_w10a10/E012.md) · [config.json](../../experiments/E012_apfixed_w10a10/config.json) · [metrics.json](../../experiments/E012_apfixed_w10a10/metrics.json) · [csim.log.txt](../../experiments/E012_apfixed_w10a10/csim.log.txt)。

<a id="e013"></a>

### E013：实际 ap_fixed：8/8 位

**基于：** [E010](#e010)（数值依据或研究启发）。

**调整：** 验证量化模型与真实定点运算是否一致，即使质量门槛已失败。

**效果与问题：** 算术一致不等于质量合格；全 8 位方案仍被拒绝。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=0.002759333288601273；六像素边界 MSE=0.0016186038119685043。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`688168ce38d521d78f4db262d66d842c12a1b4af`。

**原始证据：** [E013.json](../../exp/configs/E013.json) · [E013.md](../../experiments/E013_apfixed_w8a8/E013.md) · [config.json](../../experiments/E013_apfixed_w8a8/config.json) · [metrics.json](../../experiments/E013_apfixed_w8a8/metrics.json) · [csim.log.txt](../../experiments/E013_apfixed_w8a8/csim.log.txt)。

<a id="e014"></a>

### E014：16/16 位完整数据重试

**基于：** [E011](#e011)（修复后重试）。

**调整：** 再次尝试全图像的完整 ap_fixed 仿真。

**效果与问题：** 45 分钟限时内只完成部分图像，按 timeout 保留；不能补算为全图通过。

**记录状态：** `timeout` / 超时；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`ede43ae07ffde49141ed329dfb8cd4f9267fe9c5`。

**原始证据：** [E014.json](../../exp/configs/E014.json) · [E014.md](../../experiments/E014_apfixed_w16a16/E014.md) · [config.json](../../experiments/E014_apfixed_w16a16/config.json) · [metrics.json](../../experiments/E014_apfixed_w16a16/metrics.json) · [csim.log.txt](../../experiments/E014_apfixed_w16a16/csim.log.txt)。

<a id="e018"></a>

### E018：16/16 位单图控制

**基于：** [E014](#e014)（修复后重试）。

**调整：** 把完整 ap_fixed 运算检查缩到 butterfly；多图质量由 E010 单独评估。

**效果与问题：** 本次编译/仿真失败，随后 E015 重试。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`3c13a0f643c80790f84b4dd4e14b99790f484cb8`。

**原始证据：** [E018.json](../../exp/configs/E018.json) · [E018.md](../../experiments/E018_apfixed_w16a16_single/E018.md) · [config.json](../../experiments/E018_apfixed_w16a16_single/config.json) · [metrics.json](../../experiments/E018_apfixed_w16a16_single/metrics.json) · [csim.log.txt](../../experiments/E018_apfixed_w16a16_single/csim.log.txt)。

<a id="e015"></a>

### E015：16/16 位单图有效重试

**基于：** [E018](#e018)（修复后重试）。

**调整：** 修正运行配置，验证完整 ap_fixed butterfly 算术。

**效果与问题：** 通过的是单图算术复核；不能替代 13 图的实际全 ap_fixed 运行。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.211354436427195e-08；六像素边界 MSE=7.1054134342970225e-09。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`688168ce38d521d78f4db262d66d842c12a1b4af`。

**原始证据：** [E015.json](../../exp/configs/E015.json) · [E015.md](../../experiments/E015_apfixed_w16a16_single_retry/E015.md) · [config.json](../../experiments/E015_apfixed_w16a16_single_retry/config.json) · [metrics.json](../../experiments/E015_apfixed_w16a16_single_retry/metrics.json) · [csim.log.txt](../../experiments/E015_apfixed_w16a16_single_retry/csim.log.txt)。

<a id="e016"></a>

### E016：8/8 位单图重试

**基于：** [E013](#e013)（修复后重试）。

**调整：** 以独立配置再次检查低位宽算术。

**效果与问题：** 质量失败仍然成立；重试没有放宽 PSNR 门槛。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=0.002759333288601273；六像素边界 MSE=0.0016186038119685043。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`200a5bebe17203a1d9c71f3445d325b7d6d166cf`。

**原始证据：** [E016.json](../../exp/configs/E016.json) · [E016.md](../../experiments/E016_apfixed_w8a8_retry/E016.md) · [config.json](../../experiments/E016_apfixed_w8a8_retry/config.json) · [metrics.json](../../experiments/E016_apfixed_w8a8_retry/metrics.json) · [csim.log.txt](../../experiments/E016_apfixed_w8a8_retry/csim.log.txt)。

<a id="e017"></a>

### E017：10 位边界与整数参考

**基于：** [E010](#e010)（数值依据或研究启发）。

**调整：** 真实 ap_fixed 负责输入、参数及层间舍入/饱和，整数保留完整乘积与累加小数。

**效果与问题：** 建立 13 图的独立精度参考；这是后续架构的数值依据，不是性能实验。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：本次仿真（13 张；见原始记录）。

工具：Vitis 2026.1；源码提交：`bece7ccf647c9625fd6661c974f7f017ee8a8aef`。

**原始证据：** [E017.json](../../exp/configs/E017.json) · [E017.md](../../experiments/E017_apfixed_boundary_w10a10/E017.md) · [config.json](../../experiments/E017_apfixed_boundary_w10a10/config.json) · [metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json) · [csim.log.txt](../../experiments/E017_apfixed_boundary_w10a10/csim.log.txt)。

<a id="e019"></a>

### E019：10/10 位完整 ap_fixed 重试

**基于：** [E012](#e012)（修复后重试）；[E017](#e017)（对照实验）。

**调整：** 在 butterfly 上验证完整 ap_fixed 网络与独立整数参考逐位相同。

**效果与问题：** 功能通过；硬件架构仍需要另行设计和综合。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`688168ce38d521d78f4db262d66d842c12a1b4af`。

**原始证据：** [E019.json](../../exp/configs/E019.json) · [E019.md](../../experiments/E019_apfixed_w10a10_retry/E019.md) · [config.json](../../experiments/E019_apfixed_w10a10_retry/config.json) · [metrics.json](../../experiments/E019_apfixed_w10a10_retry/metrics.json) · [csim.log.txt](../../experiments/E019_apfixed_w10a10_retry/csim.log.txt)。

<a id="e049"></a>

### E049：层边界舍入穷举

**基于：** [E017](#e017)（数值依据或研究启发）；[E048](#e048)（验证同一设计）。

**调整：** 穷举三个层边界共 25,165,824 个 23 位累加器状态。

**效果与问题：** 证明最近偶数舍入及饱和边界；没有整网延迟或资源结论。

**记录状态：** `csim_pass` / C 仿真通过；范围 `boundary`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`59f3e6d7983d89006c9014b6417f461953b79c39`。

**原始证据：** [E049.json](../../exp/configs/E049.json) · [E049.md](../../experiments/E049_integer_boundary_exhaustive/E049.md) · [config.json](../../experiments/E049_integer_boundary_exhaustive/config.json) · [metrics.json](../../experiments/E049_integer_boundary_exhaustive/metrics.json) · [csim.log.txt](../../experiments/E049_integer_boundary_exhaustive/csim.log.txt)。

<a id="e062"></a>

### E062：逐层 INT8 可用性

**基于：** [E010](#e010)（数值依据或研究启发）；[E017](#e017)（数值依据或研究启发）。

**调整：** 分别尝试单层 8 位权重/激活，而不是把整个网络直接降到 INT8。

**效果与问题：** 仅 Conv2 的 8 位权重候选满足平均质量门槛；真实 8 位激活及 Conv1/Conv3 8 位权重量化失败。

**记录状态：** `analysis_complete` / 分析完成；范围 `analysis`；步骤 `analysis`。

工具：未记录 Vitis 版本/不适用；源码提交：`de1138d1c31b2e8933cef2420711c9ea1baf3bcd`。

**原始证据：** [E062.md](../../experiments/E062_layer_int8_scan/E062.md) · [config.json](../../experiments/E062_layer_int8_scan/config.json)。

<a id="e065"></a>

### E065：Conv2 权重 8 位边界复核

**基于：** [E062](#e062)（数值依据或研究启发）；[E017](#e017)（设计或参数基线）。

**调整：** 保留 10 位激活，使用真实 ap_fixed 检查混合精度的 13 张图。

**效果与问题：** 平均 PSNR 降约 0.07589 dB；为组合路线提供独立依据，仍缺 comic。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.770653995278335e-05；六像素边界 MSE=1.405191888267716e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.082567 dB；相对浮点平均 ΔPSNR=-0.07589 dB。来源：本次仿真（13 张；见原始记录）。

工具：Vitis 2026.1；源码提交：`04f613aecc98bb42d5023604146a03112d205523`。

**原始证据：** [E065.json](../../exp/configs/E065.json) · [E065.md](../../experiments/E065_apfixed_mixed_conv2w8/E065.md) · [config.json](../../experiments/E065_apfixed_mixed_conv2w8/config.json) · [metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json) · [csim.log.txt](../../experiments/E065_apfixed_mixed_conv2w8/csim.log.txt)。

<a id="e066"></a>

### E066：混合精度完整 ap_fixed 单图

**基于：** [E065](#e065)（对照实验）；[E019](#e019)（设计或参数基线）。

**调整：** 完整 ap_fixed 网络验证混合精度 butterfly 输出。

**效果与问题：** 逐位一致后才能把 E065 的质量记录用于相同精度的架构。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.770653995278335e-05；六像素边界 MSE=1.405191888267716e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.082567 dB；相对浮点平均 ΔPSNR=-0.07589 dB。来源：[experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json)。

工具：Vitis 2026.1；源码提交：`818ae9a14872f5dfec2c07a1ccb825c86542c7de`。

**原始证据：** [E066.json](../../exp/configs/E066.json) · [E066.md](../../experiments/E066_full_apfixed_mixed_butterfly/E066.md) · [config.json](../../experiments/E066_full_apfixed_mixed_butterfly/config.json) · [metrics.json](../../experiments/E066_full_apfixed_mixed_butterfly/metrics.json) · [csim.log.txt](../../experiments/E066_full_apfixed_mixed_butterfly/csim.log.txt)。

<a id="e071"></a>

### E071：Packing/Winograd 前置范围

**基于：** [E017](#e017)（数值依据或研究启发）；[E065](#e065)（数值依据或研究启发）。

**调整：** 统计原始整数系数、变换位宽、低字段累加上限和纸面 DSP 预算。

**效果与问题：** 范围与预算分析不等于综合结果；泛化到新权重需要重新检查边界。

**记录状态：** `analysis_complete` / 分析完成；范围 `parameter analysis, no HLS measurement`；步骤 `analysis`。

工具：未记录 Vitis 版本/不适用；源码提交：`ff3804751b8a6f726aeda110ba87a1474717152b`。

**原始证据：** [E071.md](../../experiments/E071_architecture_prerequisite_ranges/E071.md) · [config.json](../../experiments/E071_architecture_prerequisite_ranges/config.json) · [metrics.json](../../experiments/E071_architecture_prerequisite_ranges/metrics.json)。

<a id="compiler"></a>

## 编译器对照：保留整幅特征图会怎样

只改时钟、流水指令、分区或数据类型，能否让原结构可行？

[演进图](compiler.svg)；路线依据：[experiments/STAGE2.md](../../experiments/STAGE2.md) · [exp/prepare_auto.py](../../exp/prepare_auto.py) · [exp/retry.py](../../exp/retry.py)。

<a id="e020"></a>

### E020：默认自动优化，10 ns

**基于：** [E000](#e000)（设计或参数基线）。

**调整：** 复制原版并加循环标签，不改变计算和整图存储。

**效果与问题：** 延迟和 BRAM 规模仍接近原始基线。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.331 ns |
| 延迟 / 间隔 | 1960113853 / 1960113854 cycles |
| 注册表换算时间 | 19601.13853 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`1f025dccb9e5fb187213ff4aea10887e617ab078`。

**原始证据：** [E020.json](../../exp/configs/E020.json) · [E020.md](../../experiments/E020_auto_default_10ns/E020.md) · [config.json](../../experiments/E020_auto_default_10ns/config.json) · [metrics.json](../../experiments/E020_auto_default_10ns/metrics.json) · [csynth.rpt](../../experiments/E020_auto_default_10ns/csynth.rpt) · [csynth.log.txt](../../experiments/E020_auto_default_10ns/csynth.log.txt) · [csim.log.txt](../../experiments/E020_auto_default_10ns/csim.log.txt)。

<a id="e021"></a>

### E021：默认自动优化，4 ns

**基于：** [E020](#e020)（设计或参数基线）。

**调整：** 只收紧目标周期，观察默认调度变化。

**效果与问题：** 完整中间图依然装不下；时钟目标本身不是实现结果。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 2.913 ns |
| 延迟 / 间隔 | 4294771851 / 4294771852 cycles |
| 注册表换算时间 | 17179.087404 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9997 / 9596 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`6df111ca1bacf266ef91c7df7ffb7f44e81e853c`。

**原始证据：** [E021.json](../../exp/configs/E021.json) · [E021.md](../../experiments/E021_auto_default_4ns/E021.md) · [config.json](../../experiments/E021_auto_default_4ns/config.json) · [metrics.json](../../experiments/E021_auto_default_4ns/metrics.json) · [csynth.rpt](../../experiments/E021_auto_default_4ns/csynth.rpt) · [csynth.log.txt](../../experiments/E021_auto_default_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/E021_auto_default_4ns/csim.log.txt)。

<a id="e022"></a>

### E022：关闭自动流水

**基于：** [E020](#e020)（设计或参数基线）。

**调整：** 测量默认流水策略是否有效。

**效果与问题：** 资源问题未解决，延迟还增大。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.016 ns |
| 延迟 / 间隔 | 4482223011 / 4482223012 cycles |
| 注册表换算时间 | 44822.23011 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 5 / 11064 / 0 |
| LUT / FF | 2217 / 1267 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`7c7c1a1888f171530bf36fd618e7ae936f42071b`。

**原始证据：** [E022.json](../../exp/configs/E022.json) · [E022.md](../../experiments/E022_auto_pipeline_off/E022.md) · [config.json](../../experiments/E022_auto_pipeline_off/config.json) · [metrics.json](../../experiments/E022_auto_pipeline_off/metrics.json) · [csynth.rpt](../../experiments/E022_auto_pipeline_off/csynth.rpt) · [csynth.log.txt](../../experiments/E022_auto_pipeline_off/csynth.log.txt) · [csim.log.txt](../../experiments/E022_auto_pipeline_off/csim.log.txt)。

<a id="e023"></a>

### E023：最内层流水：无效配置

**基于：** [E020](#e020)（设计或参数基线）。

**调整：** 尝试配置最内层 MAC 流水。

**效果与问题：** syn.directive 键被工具跳过，结果不能代表预期指令。

**记录状态：** `invalid_config` / 配置无效；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；II 未达目标；配置无效。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.331 ns |
| 延迟 / 间隔 | 1960113853 / 1960113854 cycles |
| 注册表换算时间 | 19601.13853 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| 所检查的 II 目标 | 未达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`ede43ae07ffde49141ed329dfb8cd4f9267fe9c5`。

**原始证据：** [E023.json](../../exp/configs/E023.json) · [E023.md](../../experiments/E023_auto_inner_pipeline/E023.md) · [config.json](../../experiments/E023_auto_inner_pipeline/config.json) · [metrics.json](../../experiments/E023_auto_inner_pipeline/metrics.json) · [csynth.rpt](../../experiments/E023_auto_inner_pipeline/csynth.rpt) · [csynth.log.txt](../../experiments/E023_auto_inner_pipeline/csynth.log.txt) · [csim.log.txt](../../experiments/E023_auto_inner_pipeline/csim.log.txt)。

<a id="e024"></a>

### E024：像素循环流水：无效配置

**基于：** [E020](#e020)（设计或参数基线）。

**调整：** 尝试流水外层像素循环。

**效果与问题：** 配置键无效；后续 E029 才是有效的同思路对照。

**记录状态：** `invalid_config` / 配置无效；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；II 未达目标；配置无效。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.331 ns |
| 延迟 / 间隔 | 1960113853 / 1960113854 cycles |
| 注册表换算时间 | 19601.13853 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| 所检查的 II 目标 | 未达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`9cbadb26fb00c6312eb4997cb8679f4ec6c191d0`。

**原始证据：** [E024.json](../../exp/configs/E024.json) · [E024.md](../../experiments/E024_auto_pixel_pipeline/E024.md) · [config.json](../../experiments/E024_auto_pixel_pipeline/config.json) · [metrics.json](../../experiments/E024_auto_pixel_pipeline/metrics.json) · [csynth.rpt](../../experiments/E024_auto_pixel_pipeline/csynth.rpt) · [csynth.log.txt](../../experiments/E024_auto_pixel_pipeline/csynth.log.txt) · [csim.log.txt](../../experiments/E024_auto_pixel_pipeline/csim.log.txt)。

<a id="e025"></a>

### E025：数组分区：无效配置

**基于：** [E020](#e020)（设计或参数基线）。

**调整：** 尝试增加数组端口来改善调度。

**效果与问题：** 配置键无效；后续 E032 修正。

**记录状态：** `invalid_config` / 配置无效；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；II 未达目标；配置无效。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.331 ns |
| 延迟 / 间隔 | 1960113853 / 1960113854 cycles |
| 注册表换算时间 | 19601.13853 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 9377 / 8027 |
| 所检查的 II 目标 | 未达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`659a2dc83df568ba89ae85a83f8a86909663322b`。

**原始证据：** [E025.json](../../exp/configs/E025.json) · [E025.md](../../experiments/E025_auto_partition/E025.md) · [config.json](../../experiments/E025_auto_partition/config.json) · [metrics.json](../../experiments/E025_auto_partition/metrics.json) · [csynth.rpt](../../experiments/E025_auto_partition/csynth.rpt) · [csynth.log.txt](../../experiments/E025_auto_partition/csynth.log.txt) · [csim.log.txt](../../experiments/E025_auto_partition/csim.log.txt)。

<a id="e026"></a>

### E026：允许浮点数学重排

**基于：** [E020](#e020)（设计或参数基线）。

**调整：** 研究 unsafe-math 对浮点累加调度的影响。

**效果与问题：** 对整网延迟改善很小，完整中间图仍超量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.331 ns |
| 延迟 / 间隔 | 1960113671 / 1960113672 cycles |
| 注册表换算时间 | 19601.13671 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 10 / 11064 / 0 |
| LUT / FF | 7624 / 3154 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`6d13dcde76f6c4c4b373663a6d6178537ffc7011`。

**原始证据：** [E026.json](../../exp/configs/E026.json) · [E026.md](../../experiments/E026_auto_unsafe_math/E026.md) · [config.json](../../experiments/E026_auto_unsafe_math/config.json) · [metrics.json](../../experiments/E026_auto_unsafe_math/metrics.json) · [csynth.rpt](../../experiments/E026_auto_unsafe_math/csynth.rpt) · [csynth.log.txt](../../experiments/E026_auto_unsafe_math/csynth.log.txt) · [csim.log.txt](../../experiments/E026_auto_unsafe_math/csim.log.txt)。

<a id="e027"></a>

### E027：只改 16 位定点类型

**基于：** [E015](#e015)（设计或参数基线）；[E020](#e020)（对照实验）。

**调整：** 保留整幅特征图，只替换数值类型。

**效果与问题：** 存储减少但 BRAM、LUT 仍超量；量化本身不能解决整图组织。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K/LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.177 ns |
| 延迟 / 间隔 | 391256088 / 391256089 cycles |
| 注册表换算时间 | 3912.56088 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 66 / 5822 / 0 |
| LUT / FF | 137322 / 8096 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.211354436427195e-08；六像素边界 MSE=7.1054134342970225e-09。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`6dce2c2e7283d210156492d1c66dbda48f2c42c7`。

**原始证据：** [E027.json](../../exp/configs/E027.json) · [E027.md](../../experiments/E027_auto_fixed16/E027.md) · [config.json](../../experiments/E027_auto_fixed16/config.json) · [metrics.json](../../experiments/E027_auto_fixed16/metrics.json) · [csynth.rpt](../../experiments/E027_auto_fixed16/csynth.rpt) · [csynth.log.txt](../../experiments/E027_auto_fixed16/csynth.log.txt) · [csim.log.txt](../../experiments/E027_auto_fixed16/csim.log.txt)。

<a id="e028"></a>

### E028：有效最内层流水

**基于：** [E023](#e023)（修复后重试）。

**调整：** 用工具接受的指令重做最内层 MAC 流水。

**效果与问题：** 可达到内层 II=1，但估计关键路径和整图存储限制仍在。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 26.707 ns |
| 延迟 / 间隔 | 455695454 / 455695455 cycles |
| 注册表换算时间 | 12170.25848998 ms（frame 范围，以 26.707 ns 换算） |
| DSP / BRAM18K / URAM | 12 / 11064 / 0 |
| LUT / FF | 9914 / 8948 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 10 − 2.7 = 7.3 ns；告警路径最高估计 26.707 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`6dce2c2e7283d210156492d1c66dbda48f2c42c7`。

**原始证据：** [E028.json](../../exp/configs/E028.json) · [E028.md](../../experiments/E028_auto_inner_pipeline_validcfg/E028.md) · [config.json](../../experiments/E028_auto_inner_pipeline_validcfg/config.json) · [metrics.json](../../experiments/E028_auto_inner_pipeline_validcfg/metrics.json) · [csynth.rpt](../../experiments/E028_auto_inner_pipeline_validcfg/csynth.rpt) · [csynth.log.txt](../../experiments/E028_auto_inner_pipeline_validcfg/csynth.log.txt) · [csim.log.txt](../../experiments/E028_auto_inner_pipeline_validcfg/csim.log.txt)。

<a id="e029"></a>

### E029：有效像素循环流水

**基于：** [E024](#e024)（修复后重试）。

**调整：** 用有效配置研究外层流水和自动内层展开。

**效果与问题：** 编译器对照中较快，但仍约 11,114 BRAM18K，且有 II 未达标记录。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；II 未达目标。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.624 ns |
| 延迟 / 间隔 | 381121723 / 381121724 cycles |
| 注册表换算时间 | 3811.21723 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 320 / 11114 / 0 |
| LUT / FF | 80812 / 123203 |
| 所检查的 II 目标 | 未达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`bece7ccf647c9625fd6661c974f7f017ee8a8aef`。

**原始证据：** [E029.json](../../exp/configs/E029.json) · [E029.md](../../experiments/E029_auto_pixel_pipeline_validcfg/E029.md) · [config.json](../../experiments/E029_auto_pixel_pipeline_validcfg/config.json) · [metrics.json](../../experiments/E029_auto_pixel_pipeline_validcfg/metrics.json) · [csynth.rpt](../../experiments/E029_auto_pixel_pipeline_validcfg/csynth.rpt) · [csynth.log.txt](../../experiments/E029_auto_pixel_pipeline_validcfg/csynth.log.txt) · [csim.log.txt](../../experiments/E029_auto_pixel_pipeline_validcfg/csim.log.txt)。

<a id="e032"></a>

### E032：有效数组分区

**基于：** [E025](#e025)（修复后重试）。

**调整：** 修正分区指令，再观察存储端口与流水。

**效果与问题：** 保持整幅中间图时，资源问题依然没有消除。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 26.707 ns |
| 延迟 / 间隔 | 455695454 / 455695455 cycles |
| 注册表换算时间 | 12170.25848998 ms（frame 范围，以 26.707 ns 换算） |
| DSP / BRAM18K / URAM | 12 / 11096 / 0 |
| LUT / FF | 8585 / 10378 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 10 − 2.7 = 7.3 ns；告警路径最高估计 26.707 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`815b1da044d42b8d4383d1d7a499f2a57981b8dd`。

**原始证据：** [E032.json](../../exp/configs/E032.json) · [E032.md](../../experiments/E032_auto_partition_validcfg/E032.md) · [config.json](../../experiments/E032_auto_partition_validcfg/config.json) · [metrics.json](../../experiments/E032_auto_partition_validcfg/metrics.json) · [csynth.rpt](../../experiments/E032_auto_partition_validcfg/csynth.rpt) · [csynth.log.txt](../../experiments/E032_auto_partition_validcfg/csynth.log.txt) · [csim.log.txt](../../experiments/E032_auto_partition_validcfg/csim.log.txt)。

<a id="streaming"></a>

## 第一轮流式架构：消除完整中间图

行缓存和流连接有效后，为什么 LUT 与时序仍然成为瓶颈？

[演进图](streaming.svg)；路线依据：[experiments/STAGE3.md](../../experiments/STAGE3.md) · [exp/prepare_int.py](../../exp/prepare_int.py) · [exp/prepare_dsp.py](../../exp/prepare_dsp.py) · [exp/prepare_wrap.py](../../exp/prepare_wrap.py)。

<a id="e030"></a>

### E030：浮点流式功能控制

**基于：** [E000](#e000)（设计或参数基线）。

**调整：** read/pad/Conv1/Conv2/pad/Conv3/write 用流连接，并用行缓存复用窗口。

**效果与问题：** 先证明整图及边缘功能一致；此记录只有 C 仿真。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=3.1660971422452726e-14；六像素边界 MSE=2.1182492395563412e-14。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`6d13dcde76f6c4c4b373663a6d6178537ffc7011`。

**原始证据：** [E030.json](../../exp/configs/E030.json) · [E030.md](../../experiments/E030_dataflow_float/E030.md) · [config.json](../../experiments/E030_dataflow_float/config.json) · [metrics.json](../../experiments/E030_dataflow_float/metrics.json) · [csim.log.txt](../../experiments/E030_dataflow_float/csim.log.txt)。

<a id="e031"></a>

### E031：10 位流式，T32

**基于：** [E030](#e030)（设计或参数基线）；[E017](#e017)（数值依据或研究启发）。

**调整：** 把已验证流结构改为 10 位定点、T=32 部分展开。

**效果与问题：** BRAM 已降到 168，但大量乘法/类型逻辑落在 LUT，资源和估计时序失败。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 31.822 ns |
| 延迟 / 间隔 | 3882221 / 3882222 cycles |
| 注册表换算时间 | 123.54003666 ms（frame 范围，以 31.822 ns 换算） |
| DSP / BRAM18K / URAM | 9 / 168 / 0 |
| LUT / FF | 136868 / 149111 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 10 − 2.7 = 7.3 ns；告警路径最高估计 31.822 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`3c13a0f643c80790f84b4dd4e14b99790f484cb8`。

**原始证据：** [E031.json](../../exp/configs/E031.json) · [E031.md](../../experiments/E031_dataflow_fixed_T32/E031.md) · [config.json](../../experiments/E031_dataflow_fixed_T32/config.json) · [metrics.json](../../experiments/E031_dataflow_fixed_T32/metrics.json) · [csynth.rpt](../../experiments/E031_dataflow_fixed_T32/csynth.rpt) · [csynth.log.txt](../../experiments/E031_dataflow_fixed_T32/csynth.log.txt) · [csim.log.txt](../../experiments/E031_dataflow_fixed_T32/csim.log.txt)。

<a id="e033"></a>

### E033：T32 单图综合控制

**基于：** [E031](#e031)（设计或参数基线）。

**调整：** 缩短 C 仿真任务，保持同一流式硬件组织。

**效果与问题：** 重复测得 136,868 LUT、31.822 ns 估计路径；内层 II=1 不等于整网高吞吐。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 31.822 ns |
| 延迟 / 间隔 | 3882221 / 3882222 cycles |
| 注册表换算时间 | 123.54003666 ms（frame 范围，以 31.822 ns 换算） |
| DSP / BRAM18K / URAM | 9 / 168 / 0 |
| LUT / FF | 136868 / 149111 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 10 − 2.7 = 7.3 ns；告警路径最高估计 31.822 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`3c13a0f643c80790f84b4dd4e14b99790f484cb8`。

**原始证据：** [E033.json](../../exp/configs/E033.json) · [E033.md](../../experiments/E033_dataflow_fixed_T32_single/E033.md) · [config.json](../../experiments/E033_dataflow_fixed_T32_single/config.json) · [metrics.json](../../experiments/E033_dataflow_fixed_T32_single/metrics.json) · [csynth.rpt](../../experiments/E033_dataflow_fixed_T32_single/csynth.rpt) · [csynth.log.txt](../../experiments/E033_dataflow_fixed_T32_single/csynth.log.txt) · [csim.log.txt](../../experiments/E033_dataflow_fixed_T32_single/csim.log.txt)。

<a id="e046"></a>

### E046：去掉冗余累加饱和

**基于：** [E033](#e033)（设计或参数基线）；[E010](#e010)（数值依据或研究启发）。

**调整：** 利用已归档范围界，保留完整乘积精度，只在层边界量化。

**效果与问题：** 本次被已有综合锁挡住，不能作为硬件测量。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`200a5bebe17203a1d9c71f3445d325b7d6d166cf`。

**原始证据：** [E046.json](../../exp/configs/E046.json) · [E046.md](../../experiments/E046_dataflow_wrap_T32/E046.md) · [config.json](../../experiments/E046_dataflow_wrap_T32/config.json) · [metrics.json](../../experiments/E046_dataflow_wrap_T32/metrics.json) · [csim.log.txt](../../experiments/E046_dataflow_wrap_T32/csim.log.txt)。

<a id="e063"></a>

### E063：累加控制重试

**基于：** [E046](#e046)（修复后重试）。

**调整：** 在独立运行中测量去冗余饱和的方案。

**效果与问题：** DSP 映射变化，但 LUT 仍超预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2913855 / 2913856 cycles |
| 注册表换算时间 | 29.13855 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 148 / 168 / 0 |
| LUT / FF | 95727 / 132430 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`6d7039b83f39b75f9b752a1b650b2e441b4180f3`。

**原始证据：** [E063.json](../../exp/configs/E063.json) · [E063.md](../../experiments/E063_dataflow_wrap_T32_retry/E063.md) · [config.json](../../experiments/E063_dataflow_wrap_T32_retry/config.json) · [metrics.json](../../experiments/E063_dataflow_wrap_T32_retry/metrics.json) · [csynth.rpt](../../experiments/E063_dataflow_wrap_T32_retry/csynth.rpt) · [csynth.log.txt](../../experiments/E063_dataflow_wrap_T32_retry/csynth.log.txt) · [csim.log.txt](../../experiments/E063_dataflow_wrap_T32_retry/csim.log.txt)。

<a id="e047"></a>

### E047：明确把乘法绑定到 DSP

**基于：** [E033](#e033)（设计或参数基线）。

**调整：** 把 T32 的 162/64/25 路乘法指定到 DSP。

**效果与问题：** 估计延迟明显降低，但寄存器化权重及选择器仍使 LUT 超量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2913855 / 2913856 cycles |
| 注册表换算时间 | 29.13855 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 251 / 168 / 0 |
| LUT / FF | 89341 / 132430 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`af351bab36dcd4f95babc0f427342112b6c36bf2`。

**原始证据：** [E047.json](../../exp/configs/E047.json) · [E047.md](../../experiments/E047_dataflow_dsp_T32/E047.md) · [config.json](../../experiments/E047_dataflow_dsp_T32/config.json) · [metrics.json](../../experiments/E047_dataflow_dsp_T32/metrics.json) · [csynth.rpt](../../experiments/E047_dataflow_dsp_T32/csynth.rpt) · [csynth.log.txt](../../experiments/E047_dataflow_dsp_T32/csynth.log.txt) · [csim.log.txt](../../experiments/E047_dataflow_dsp_T32/csim.log.txt)。

<a id="e048"></a>

### E048：整数承载的定点运算

**基于：** [E047](#e047)（设计或参数基线）；[E017](#e017)（数值依据或研究启发）。

**调整：** 用整数保存定点原始位，显式实现层边界舍入，保持数值契约。

**效果与问题：** 简化数值表达后仍有约 89,304 LUT，下一步需要处理存储银行和选择器。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2913855 / 2913856 cycles |
| 注册表换算时间 | 29.13855 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 89304 / 132635 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`0ceab1f21db6296227e5a524e37028e6ef2ffbc8`。

**原始证据：** [E048.json](../../exp/configs/E048.json) · [E048.md](../../experiments/E048_dataflow_integer_T32/E048.md) · [config.json](../../experiments/E048_dataflow_integer_T32/config.json) · [metrics.json](../../experiments/E048_dataflow_integer_T32/metrics.json) · [csynth.rpt](../../experiments/E048_dataflow_integer_T32/csynth.rpt) · [csynth.log.txt](../../experiments/E048_dataflow_integer_T32/csynth.log.txt) · [csim.log.txt](../../experiments/E048_dataflow_integer_T32/csim.log.txt)。

<a id="e050"></a>

### E050：初版 Conv3 Scatter

**基于：** [E031](#e031)（设计或参数基线）。

**调整：** 先跨通道归约，再缓存少通道的部分和。

**效果与问题：** BRAM 降低，但初版定点/映射逻辑导致 LUT 超量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 3882221 / 3882222 cycles |
| 注册表换算时间 | 38.82221 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 34 / 137 / 0 |
| LUT / FF | 127718 / 128434 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`f5990c904b80dc8aac23150897e5eda2375ba798`。

**原始证据：** [E050.json](../../exp/configs/E050.json) · [E050.md](../../experiments/E050_scatter_T32/E050.md) · [config.json](../../experiments/E050_scatter_T32/config.json) · [metrics.json](../../experiments/E050_scatter_T32/metrics.json) · [csynth.rpt](../../experiments/E050_scatter_T32/csynth.rpt) · [csynth.log.txt](../../experiments/E050_scatter_T32/csynth.log.txt) · [csim.log.txt](../../experiments/E050_scatter_T32/csim.log.txt)。

<a id="e060"></a>

### E060：整数版 Conv3 Scatter

**基于：** [E048](#e048)（设计或参数基线）；[E050](#e050)（数值依据或研究启发）。

**调整：** 保留显式补边，用 32 位部分和与轮换行缓存。

**效果与问题：** 资源可进入预算，但控制和额外工作使速度慢于 gather。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 3770206 / 3770207 cycles |
| 注册表换算时间 | 37.70206 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 137 / 0 |
| LUT / FF | 39135 / 24841 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`e25bcc9245725a41b041bb154138da29014df358`。

**原始证据：** [E060.json](../../exp/configs/E060.json) · [E060.md](../../experiments/E060_scatter_integer_T32/E060.md) · [config.json](../../experiments/E060_scatter_integer_T32/config.json) · [metrics.json](../../experiments/E060_scatter_integer_T32/metrics.json) · [csynth.rpt](../../experiments/E060_scatter_integer_T32/csynth.rpt) · [csynth.log.txt](../../experiments/E060_scatter_integer_T32/csynth.log.txt) · [csim.log.txt](../../experiments/E060_scatter_integer_T32/csim.log.txt)。

<a id="e056"></a>

### E056：T4 的 DSP/LUT 混合计算

**基于：** [E048](#e048)（设计或参数基线）；[E053](#e053)（数值依据或研究启发）。

**调整：** DSP 不够时让部分 Conv1/Conv3 乘法落在 fabric，提高并行度。

**效果与问题：** 纸面 DSP 能装下，但 237,025 LUT 超量；不能仅按 DSP 数选择方案。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 1046292 / 1046293 cycles |
| 注册表换算时间 | 10.46292 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 1160 / 168 / 0 |
| LUT / FF | 237025 / 120073 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`fcd3ba401b3ba37f18e450be506eca80efa62521`。

**原始证据：** [E056.json](../../exp/configs/E056.json) · [E056.md](../../experiments/E056_mixed_T4_feasibility/E056.md) · [config.json](../../experiments/E056_mixed_T4_feasibility/config.json) · [metrics.json](../../experiments/E056_mixed_T4_feasibility/metrics.json) · [csynth.rpt](../../experiments/E056_mixed_T4_feasibility/csynth.rpt) · [csynth.log.txt](../../experiments/E056_mixed_T4_feasibility/csynth.log.txt) · [csim.log.txt](../../experiments/E056_mixed_T4_feasibility/csim.log.txt)。

<a id="scans"></a>

## 参数扫描：位宽固定后寻找可行并行度与存储

T、展开方向、权重银行及目标周期各自改变了什么？

[演进图](scans.svg)；路线依据：[exp/prepare_scan.py](../../exp/prepare_scan.py) · [exp/prepare_followup.py](../../exp/prepare_followup.py) · [exp/finish_coordinates.py](../../exp/finish_coordinates.py) · [experiments/SUMMARY.md](../../experiments/SUMMARY.md)。

<a id="e034"></a>

### E034：初版 T16 扫描

**基于：** [E033](#e033)（设计或参数基线）。

**调整：** 把每像素计算轮数从 32 改成 16，增加并行乘法。

**效果与问题：** C 仿真失败，后续 E044 重试。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`3c13a0f643c80790f84b4dd4e14b99790f484cb8`。

**原始证据：** [E034.json](../../exp/configs/E034.json) · [E034.md](../../experiments/E034_scan_T_T16_E034/E034.md) · [config.json](../../experiments/E034_scan_T_T16_E034/config.json) · [metrics.json](../../experiments/E034_scan_T_T16_E034/metrics.json) · [csim.log.txt](../../experiments/E034_scan_T_T16_E034/csim.log.txt)。

<a id="e035"></a>

### E035：初版 T8 扫描

**基于：** [E033](#e033)（设计或参数基线）。

**调整：** 进一步把每像素计算轮数降到 8。

**效果与问题：** C 仿真失败，后续 E045 重试。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`3c13a0f643c80790f84b4dd4e14b99790f484cb8`。

**原始证据：** [E035.json](../../exp/configs/E035.json) · [E035.md](../../experiments/E035_scan_T_T8_E035/E035.md) · [config.json](../../experiments/E035_scan_T_T8_E035/config.json) · [metrics.json](../../experiments/E035_scan_T_T8_E035/metrics.json) · [csim.log.txt](../../experiments/E035_scan_T_T8_E035/csim.log.txt)。

<a id="e044"></a>

### E044：有效 T16 初版流式扫描

**基于：** [E034](#e034)（修复后重试）。

**调整：** 修正仿真配置后测量同一高并行思路。

**效果与问题：** 默认数值/映射路径变得更长，估计 63.218 ns，LUT 仍超量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 63.218 ns |
| 延迟 / 间隔 | 2775517 / 2775518 cycles |
| 注册表换算时间 | 175.46263371 ms（frame 范围，以 63.218 ns 换算） |
| DSP / BRAM18K / URAM | 18 / 168 / 0 |
| LUT / FF | 167715 / 135714 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 10 − 2.7 = 7.3 ns；告警路径最高估计 63.218 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`688168ce38d521d78f4db262d66d842c12a1b4af`。

**原始证据：** [E044.json](../../exp/configs/E044.json) · [E044.md](../../experiments/E044_scan_T_T16_E034_retry/E044.md) · [config.json](../../experiments/E044_scan_T_T16_E034_retry/config.json) · [metrics.json](../../experiments/E044_scan_T_T16_E034_retry/metrics.json) · [csynth.rpt](../../experiments/E044_scan_T_T16_E034_retry/csynth.rpt) · [csynth.log.txt](../../experiments/E044_scan_T_T16_E034_retry/csynth.log.txt) · [csim.log.txt](../../experiments/E044_scan_T_T16_E034_retry/csim.log.txt)。

<a id="e045"></a>

### E045：有效 T8 初版流式扫描

**基于：** [E035](#e035)（修复后重试）。

**调整：** 有效运行初版 T8 配置。

**效果与问题：** 估计 126.008 ns、266,266 LUT；更大并行度并未换来更快整网。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 126.008 ns |
| 延迟 / 间隔 | 2222165 / 2222166 cycles |
| 注册表换算时间 | 280.01056732 ms（frame 范围，以 126.008 ns 换算） |
| DSP / BRAM18K / URAM | 36 / 168 / 0 |
| LUT / FF | 266266 / 142153 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 10 − 2.7 = 7.3 ns；告警路径最高估计 126.008 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`9e45f25d0fbdb3f869511fbbee66eb29322ad8ff`。

**原始证据：** [E045.json](../../exp/configs/E045.json) · [E045.md](../../experiments/E045_scan_T_T8_E035_retry/E045.md) · [config.json](../../experiments/E045_scan_T_T8_E035_retry/config.json) · [metrics.json](../../experiments/E045_scan_T_T8_E035_retry/metrics.json) · [csynth.rpt](../../experiments/E045_scan_T_T8_E035_retry/csynth.rpt) · [csynth.log.txt](../../experiments/E045_scan_T_T8_E035_retry/csynth.log.txt) · [csim.log.txt](../../experiments/E045_scan_T_T8_E035_retry/csim.log.txt)。

<a id="e057"></a>

### E057：整数 T32 + LUTRAM 权重银行

**基于：** [E048](#e048)（设计或参数基线）。

**调整：** 把完全拆开的权重寄存器改为可写、按并行端口分银行的 LUTRAM。

**效果与问题：** LUT 降至约 44,493，得到可继续优化的资源合格基线。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2983024 / 2983025 cycles |
| 注册表换算时间 | 29.83024 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 44493 / 46328 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`2eb2ea43fc8b50176c8c2558d6cb59976ade68e2`。

**原始证据：** [E057.json](../../exp/configs/E057.json) · [E057.md](../../experiments/E057_integer_lutram_T32/E057.md) · [config.json](../../experiments/E057_integer_lutram_T32/config.json) · [metrics.json](../../experiments/E057_integer_lutram_T32/metrics.json) · [csynth.rpt](../../experiments/E057_integer_lutram_T32/csynth.rpt) · [csynth.log.txt](../../experiments/E057_integer_lutram_T32/csynth.log.txt) · [csim.log.txt](../../experiments/E057_integer_lutram_T32/csim.log.txt)。

<a id="e058"></a>

### E058：整数 T16 + LUTRAM 权重银行

**基于：** [E048](#e048)（设计或参数基线）；[E057](#e057)（对照实验）。

**调整：** 同一整数组织改为 T16，测量并行度与资源平衡。

**效果与问题：** 约 18.7632 ms；是时钟和展开方向扫描的参数基线。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 1876320 / 1876321 cycles |
| 注册表换算时间 | 18.7632 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 55212 / 57723 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c39e5bf78a69d352d763266139e6d179494582af`。

**原始证据：** [E058.json](../../exp/configs/E058.json) · [E058.md](../../experiments/E058_integer_lutram_T16/E058.md) · [config.json](../../experiments/E058_integer_lutram_T16/config.json) · [metrics.json](../../experiments/E058_integer_lutram_T16/metrics.json) · [csynth.rpt](../../experiments/E058_integer_lutram_T16/csynth.rpt) · [csynth.log.txt](../../experiments/E058_integer_lutram_T16/csynth.log.txt) · [csim.log.txt](../../experiments/E058_integer_lutram_T16/csim.log.txt)。

<a id="e059"></a>

### E059：整数 T8 + LUTRAM 权重银行

**基于：** [E048](#e048)（设计或参数基线）；[E058](#e058)（对照实验）。

**调整：** 继续增加并行度至 T8。

**效果与问题：** LUT 85,147 超过项目 70% 预算；DSP 有余量也不能接受。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 1322968 / 1322969 cycles |
| 注册表换算时间 | 13.22968 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 1007 / 168 / 0 |
| LUT / FF | 85147 / 88822 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`bcdfdc89d857215f353a911a37d63190d2f2d6fd`。

**原始证据：** [E059.json](../../exp/configs/E059.json) · [E059.md](../../experiments/E059_integer_lutram_T8/E059.md) · [config.json](../../experiments/E059_integer_lutram_T8/config.json) · [metrics.json](../../experiments/E059_integer_lutram_T8/metrics.json) · [csynth.rpt](../../experiments/E059_integer_lutram_T8/csynth.rpt) · [csynth.log.txt](../../experiments/E059_integer_lutram_T8/csynth.log.txt) · [csim.log.txt](../../experiments/E059_integer_lutram_T8/csim.log.txt)。

<a id="e036"></a>

### E036：T16：Conv1 展开方向

**基于：** [E058](#e058)（设计或参数基线）。

**调整：** 把 Conv1 并行度从输出通道方向调整到核内分组。

**效果与问题：** II 未达目标，周期增多；状态 provisional 不表示调度达标。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：II 未达目标。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 7894023 / 7894024 cycles |
| 注册表换算时间 | 78.94023 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 565 / 168 / 0 |
| LUT / FF | 79846 / 76416 |
| 所检查的 II 目标 | 未达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`89c375b09c54cdba279942a7659114cfb7cd620e`。

**原始证据：** [E036.json](../../exp/configs/E036.json) · [E036.md](../../experiments/E036_scan_split_T16_E036/E036.md) · [config.json](../../experiments/E036_scan_split_T16_E036/config.json) · [metrics.json](../../experiments/E036_scan_split_T16_E036/metrics.json) · [csynth.rpt](../../experiments/E036_scan_split_T16_E036/csynth.rpt) · [csynth.log.txt](../../experiments/E036_scan_split_T16_E036/csynth.log.txt) · [csim.log.txt](../../experiments/E036_scan_split_T16_E036/csim.log.txt)。

<a id="e037"></a>

### E037：T16：Conv2 展开方向

**基于：** [E058](#e058)（设计或参数基线）。

**调整：** 调整 Conv2 通道展开与存储端口的配合。

**效果与问题：** 延迟相同、LUT 增多，没有形成更好的取舍。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 1876320 / 1876321 cycles |
| 注册表换算时间 | 18.7632 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 60050 / 56509 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`6989ca97e7f5dcad698f0b59a5266bd2dec25496`。

**原始证据：** [E037.json](../../exp/configs/E037.json) · [E037.md](../../experiments/E037_scan_split_T16_E037/E037.md) · [config.json](../../experiments/E037_scan_split_T16_E037/config.json) · [metrics.json](../../experiments/E037_scan_split_T16_E037/metrics.json) · [csynth.rpt](../../experiments/E037_scan_split_T16_E037/csynth.rpt) · [csynth.log.txt](../../experiments/E037_scan_split_T16_E037/csynth.log.txt) · [csim.log.txt](../../experiments/E037_scan_split_T16_E037/csim.log.txt)。

<a id="e038"></a>

### E038：T16：Conv3 展开方向

**基于：** [E058](#e058)（设计或参数基线）。

**调整：** 调整 Conv3 输入通道/核内的并行拆分。

**效果与问题：** DSP、LUT 和周期均增加。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2155352 / 2155353 cycles |
| 注册表换算时间 | 21.55352 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 519 / 168 / 0 |
| LUT / FF | 64526 / 57346 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`aa7e3c4172caddd39fb8d2759e28152d988561b8`。

**原始证据：** [E038.json](../../exp/configs/E038.json) · [E038.md](../../experiments/E038_scan_split_T16_E038/E038.md) · [config.json](../../experiments/E038_scan_split_T16_E038/config.json) · [metrics.json](../../experiments/E038_scan_split_T16_E038/metrics.json) · [csynth.rpt](../../experiments/E038_scan_split_T16_E038/csynth.rpt) · [csynth.log.txt](../../experiments/E038_scan_split_T16_E038/csynth.log.txt) · [csim.log.txt](../../experiments/E038_scan_split_T16_E038/csim.log.txt)。

<a id="e039"></a>

### E039：DSP 版 T32：LUTRAM 控制

**基于：** [E047](#e047)（设计或参数基线）。

**调整：** 在 DSP 绑定版本中测量权重 LUTRAM 银行。

**效果与问题：** 得到第一项资源合格候选，后续 E070 单独做实际实现。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2983024 / 2983025 cycles |
| 注册表换算时间 | 29.83024 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 251 / 168 / 0 |
| LUT / FF | 44530 / 46123 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`0ceab1f21db6296227e5a524e37028e6ef2ffbc8`。

**原始证据：** [E039.json](../../exp/configs/E039.json) · [E039.md](../../experiments/E039_scan_storage_T32_E039/E039.md) · [config.json](../../experiments/E039_scan_storage_T32_E039/config.json) · [metrics.json](../../experiments/E039_scan_storage_T32_E039/metrics.json) · [csynth.rpt](../../experiments/E039_scan_storage_T32_E039/csynth.rpt) · [csynth.log.txt](../../experiments/E039_scan_storage_T32_E039/csynth.log.txt) · [csim.log.txt](../../experiments/E039_scan_storage_T32_E039/csim.log.txt)。

<a id="e040"></a>

### E040：DSP 版 T32：BRAM 权重银行

**基于：** [E047](#e047)（设计或参数基线）；[E039](#e039)（对照实验）。

**调整：** 把相同权重银行放到 BRAM。

**效果与问题：** 大量浅银行浪费 BRAM，达到 419 BRAM18K，超过器件容量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2983024 / 2983025 cycles |
| 注册表换算时间 | 29.83024 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 251 / 419 / 0 |
| LUT / FF | 43275 / 41136 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c765a47c2f08e143c46526a4c62707f25f4afc2c`。

**原始证据：** [E040.json](../../exp/configs/E040.json) · [E040.md](../../experiments/E040_scan_storage_T32_E040/E040.md) · [config.json](../../experiments/E040_scan_storage_T32_E040/config.json) · [metrics.json](../../experiments/E040_scan_storage_T32_E040/metrics.json) · [csynth.rpt](../../experiments/E040_scan_storage_T32_E040/csynth.rpt) · [csynth.log.txt](../../experiments/E040_scan_storage_T32_E040/csynth.log.txt) · [csim.log.txt](../../experiments/E040_scan_storage_T32_E040/csim.log.txt)。

<a id="e064"></a>

### E064：T16：完全拆分权重

**基于：** [E058](#e058)（设计或参数基线）。

**调整：** 保留 T16，将权重银行换回完全分区寄存器控制。

**效果与问题：** LUT 达 88,306，超项目预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 1807151 / 1807152 cycles |
| 注册表换算时间 | 18.07151 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 88306 / 138588 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`66ed993d94fe3043ad8b0f3468c2059e54d55ba0`。

**原始证据：** [E064.json](../../exp/configs/E064.json) · [E064.md](../../experiments/E064_storage_0_T16/E064.md) · [config.json](../../experiments/E064_storage_0_T16/config.json) · [metrics.json](../../experiments/E064_storage_0_T16/metrics.json) · [csynth.rpt](../../experiments/E064_storage_0_T16/csynth.rpt) · [csynth.log.txt](../../experiments/E064_storage_0_T16/csynth.log.txt) · [csim.log.txt](../../experiments/E064_storage_0_T16/csim.log.txt)。

<a id="e067"></a>

### E067：T16：BRAM 权重银行

**基于：** [E058](#e058)（设计或参数基线）。

**调整：** 保留 T16，改用 BRAM 存权重。

**效果与问题：** 浅银行使 BRAM18K 达 670，超器件容量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 1876320 / 1876321 cycles |
| 注册表换算时间 | 18.7632 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 670 / 0 |
| LUT / FF | 53706 / 47716 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`780c29efa88a8b7cd00927ac5f4f27c0c28fcf36`。

**原始证据：** [E067.json](../../exp/configs/E067.json) · [E067.md](../../experiments/E067_storage_2_T16/E067.md) · [config.json](../../experiments/E067_storage_2_T16/config.json) · [metrics.json](../../experiments/E067_storage_2_T16/metrics.json) · [csynth.rpt](../../experiments/E067_storage_2_T16/csynth.rpt) · [csynth.log.txt](../../experiments/E067_storage_2_T16/csynth.log.txt) · [csim.log.txt](../../experiments/E067_storage_2_T16/csim.log.txt)。

<a id="e041"></a>

### E041：T16：5 ns 目标

**基于：** [E058](#e058)（设计或参数基线）。

**调整：** 固定精度/存储，观察收紧周期后的调度和资源。

**效果与问题：** 估计约 9.7275 ms；时钟目标仍需要实际实现验证。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 5 / 3.65 ns |
| 延迟 / 间隔 | 1945500 / 1945501 cycles |
| 注册表换算时间 | 9.7275 ms（frame 范围，以 5 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 55553 / 59959 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`f68c3ebd3f64750454e7e296f3882dde7c55e2af`。

**原始证据：** [E041.json](../../exp/configs/E041.json) · [E041.md](../../experiments/E041_scan_clock_T16_E041/E041.md) · [config.json](../../experiments/E041_scan_clock_T16_E041/config.json) · [metrics.json](../../experiments/E041_scan_clock_T16_E041/metrics.json) · [csynth.rpt](../../experiments/E041_scan_clock_T16_E041/csynth.rpt) · [csynth.log.txt](../../experiments/E041_scan_clock_T16_E041/csynth.log.txt) · [csim.log.txt](../../experiments/E041_scan_clock_T16_E041/csim.log.txt)。

<a id="e042"></a>

### E042：T16：4 ns 目标

**基于：** [E058](#e058)（设计或参数基线）；[E041](#e041)（对照实验）。

**调整：** 相同架构进一步收紧周期。

**效果与问题：** 估计约 8.0587 ms，FIFO/逐像素流水开销仍在。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 2014678 / 2014679 cycles |
| 注册表换算时间 | 8.058712 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 56007 / 62948 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`2ac67f7ea3592df0e5b5297883b3dc15cbd20deb`。

**原始证据：** [E042.json](../../exp/configs/E042.json) · [E042.md](../../experiments/E042_scan_clock_T16_E042/E042.md) · [config.json](../../experiments/E042_scan_clock_T16_E042/config.json) · [metrics.json](../../experiments/E042_scan_clock_T16_E042/metrics.json) · [csynth.rpt](../../experiments/E042_scan_clock_T16_E042/csynth.rpt) · [csynth.log.txt](../../experiments/E042_scan_clock_T16_E042/csynth.log.txt) · [csim.log.txt](../../experiments/E042_scan_clock_T16_E042/csim.log.txt)。

<a id="e043"></a>

### E043：T16：3.33 ns 目标

**基于：** [E058](#e058)（设计或参数基线）；[E042](#e042)（对照实验）。

**调整：** 在同一资源/精度预算下继续收紧目标周期。

**效果与问题：** 第一轮最快资源合格估计约 6.9392 ms；尚非板端性能。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3.33 / 3.239 ns |
| 延迟 / 间隔 | 2083853 / 2083854 cycles |
| 注册表换算时间 | 6.93923049 ms（frame 范围，以 3.33 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 55325 / 67025 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 3.33 − 0.899 = 2.431 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`dc06450d75219fbf2653c931711e5fb5f4445d8f`。

**原始证据：** [E043.json](../../exp/configs/E043.json) · [E043.md](../../experiments/E043_scan_clock_T16_E043/E043.md) · [config.json](../../experiments/E043_scan_clock_T16_E043/config.json) · [metrics.json](../../experiments/E043_scan_clock_T16_E043/metrics.json) · [csynth.rpt](../../experiments/E043_scan_clock_T16_E043/csynth.rpt) · [csynth.log.txt](../../experiments/E043_scan_clock_T16_E043/csynth.log.txt) · [csim.log.txt](../../experiments/E043_scan_clock_T16_E043/csim.log.txt)。

<a id="micro"></a>

## 乘法器小实验：解释 HLS 的映射选择

小位宽乘法会落在 DSP 还是 LUT？这种成本能否用于更大的设计？

[演进图](micro.svg)；路线依据：[exp/prepare_micro.py](../../exp/prepare_micro.py) · [experiments/micro_mapping.csv](../../experiments/micro_mapping.csv)。

<a id="e051"></a>

### E051：16x16 普通乘法

**基于：** [E047](#e047)（数值依据或研究启发）。

**调整：** 独立测量一条 16x16 有符号乘法的 DSP 映射。

**效果与问题：** 一个乘法映射到一个 DSP；这是 PE 结果，不能作为整图速度。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 2.38 ns |
| 延迟 / 间隔 | 66 / 64 cycles |
| 注册表换算时间 | 0.00066 ms（PE 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 62 / 16 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`628517e9377838d3168c654dcf48f20beae18bad`。

**原始证据：** [E051.json](../../exp/configs/E051.json) · [E051.md](../../experiments/E051_mul16_default/E051.md) · [config.json](../../experiments/E051_mul16_default/config.json) · [metrics.json](../../experiments/E051_mul16_default/metrics.json) · [csynth.rpt](../../experiments/E051_mul16_default/csynth.rpt) · [csynth.log.txt](../../experiments/E051_mul16_default/csynth.log.txt) · [csim.log.txt](../../experiments/E051_mul16_default/csim.log.txt)。

<a id="e052"></a>

### E052：常数权重完全展开

**基于：** [E051](#e051)（对照实验）。

**调整：** 64 个已知常数乘法完全展开，观察常数优化。

**效果与问题：** 常数模型不等同于本项目运行时加载权重的契约。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 2.38 ns |
| 延迟 / 间隔 | 0 / 1 cycles |
| 注册表换算时间 | 0 ms（PE 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 60 / 0 / 0 |
| LUT / FF | 424 / 0 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`04cdfa1c1f2a556e42255dfcbe87df27463a2252`。

**原始证据：** [E052.json](../../exp/configs/E052.json) · [E052.md](../../experiments/E052_mul16_constant_unroll/E052.md) · [config.json](../../experiments/E052_mul16_constant_unroll/config.json) · [metrics.json](../../experiments/E052_mul16_constant_unroll/metrics.json) · [csynth.rpt](../../experiments/E052_mul16_constant_unroll/csynth.rpt) · [csynth.log.txt](../../experiments/E052_mul16_constant_unroll/csynth.log.txt) · [csim.log.txt](../../experiments/E052_mul16_constant_unroll/csim.log.txt)。

<a id="e053"></a>

### E053：8x8 fabric 乘法

**基于：** [E051](#e051)（对照实验）。

**调整：** 显式测量 LUT 乘法并穷举操作数对。

**效果与问题：** 可减少 DSP，但乘法器 LUT 成本会在大并行度下累积。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 1.635 ns |
| 延迟 / 间隔 | 66 / 64 cycles |
| 注册表换算时间 | 0.00066 ms（PE 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 0 / 0 / 0 |
| LUT / FF | 119 / 16 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`484fad30a0a9023c116ebdb0bbba0898c1a0c723`。

**原始证据：** [E053.json](../../exp/configs/E053.json) · [E053.md](../../experiments/E053_mul8_fabric/E053.md) · [config.json](../../experiments/E053_mul8_fabric/config.json) · [metrics.json](../../experiments/E053_mul8_fabric/metrics.json) · [csynth.rpt](../../experiments/E053_mul8_fabric/csynth.rpt) · [csynth.log.txt](../../experiments/E053_mul8_fabric/csynth.log.txt) · [csim.log.txt](../../experiments/E053_mul8_fabric/csim.log.txt)。

<a id="e054"></a>

### E054：16x16，4 ns 控制

**基于：** [E051](#e051)（设计或参数基线）。

**调整：** 只改变目标时钟，检查单 DSP 映射是否保持。

**效果与问题：** 保持一条乘法一 DSP；没有验证 INT16 Packing。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 2.38 ns |
| 延迟 / 间隔 | 66 / 64 cycles |
| 注册表换算时间 | 0.000264 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 62 / 16 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`15a28b62e30e437ebcd31cb9ac54f559720c84eb`。

**原始证据：** [E054.json](../../exp/configs/E054.json) · [E054.md](../../experiments/E054_mul16_default_4ns/E054.md) · [config.json](../../experiments/E054_mul16_default_4ns/config.json) · [metrics.json](../../experiments/E054_mul16_default_4ns/metrics.json) · [csynth.rpt](../../experiments/E054_mul16_default_4ns/csynth.rpt) · [csynth.log.txt](../../experiments/E054_mul16_default_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/E054_mul16_default_4ns/csim.log.txt)。

<a id="e055"></a>

### E055：仅加法的匹配控制

**基于：** [E053](#e053)（对照实验）。

**调整：** 使用同样数组接口/循环，分离接口与乘法本体的 LUT 成本。

**效果与问题：** 比较只对这个微内核有效；不能直接外推整网时序。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 1.635 ns |
| 延迟 / 间隔 | 66 / 64 cycles |
| 注册表换算时间 | 0.00066 ms（PE 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 0 / 0 / 0 |
| LUT / FF | 73 / 16 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`9c8ab0be2f3a7eb450aa40193cf2a391f4310e9e`。

**原始证据：** [E055.json](../../exp/configs/E055.json) · [E055.md](../../experiments/E055_mul8_add_control/E055.md) · [config.json](../../experiments/E055_mul8_add_control/config.json) · [metrics.json](../../experiments/E055_mul8_add_control/metrics.json) · [csynth.rpt](../../experiments/E055_mul8_add_control/csynth.rpt) · [csynth.log.txt](../../experiments/E055_mul8_add_control/csynth.log.txt) · [csim.log.txt](../../experiments/E055_mul8_add_control/csim.log.txt)。

<a id="packing"></a>

## A：Packing，从局部精确性到整网成本

一个 DSP 做两个共享操作数乘法，省下的 DSP 是否抵得过修复逻辑？

[演进图](packing.svg)；路线依据：[exp/prepare_arch_pe.py](../../exp/prepare_arch_pe.py) · [exp/prepare_arch_full.py](../../exp/prepare_arch_full.py) · [exp/build_arch_p.py](../../exp/build_arch_p.py) · [exp/prepare_int16_packing.py](../../exp/prepare_int16_packing.py)。

<a id="p01"></a>

### P01：共享输入的双 INT8 乘法

**基于：** [E051](#e051)（数值依据或研究启发）；[E071](#e071)（数值依据或研究启发）。

**调整：** 以 gap18 拼接两个系数，修正低字段为负时的借位；穷举 signed8 三元组。

**效果与问题：** 两路乘法用一 DSP，但比直接控制多出拆包逻辑。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 61 / 56 cycles |
| 注册表换算时间 | 0.000244 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 132 / 86 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`e5f44e0eb07817e651bd369f0638edf58de458fa`。

**原始证据：** [P01.json](../../exp/configs/P01.json) · [P01.md](../../experiments/P01_signed8_pair/P01.md) · [config.json](../../experiments/P01_signed8_pair/config.json) · [metrics.json](../../experiments/P01_signed8_pair/metrics.json) · [csynth.rpt](../../experiments/P01_signed8_pair/csynth.rpt) · [csynth.log.txt](../../experiments/P01_signed8_pair/csynth.log.txt) · [csim.log.txt](../../experiments/P01_signed8_pair/csim.log.txt)。

<a id="p02"></a>

### P02：两路直接乘法控制

**基于：** [P01](#p01)（对照实验）。

**调整：** 相同接口和输入，分别计算两个乘积。

**效果与问题：** 使用两 DSP；为 Packing 的 LUT、流水成本提供对照。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 1.781 ns |
| 延迟 / 间隔 | 58 / 56 cycles |
| 注册表换算时间 | 0.000232 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 2 / 0 / 0 |
| LUT / FF | 57 / 16 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`b73fad7dd87d951428b1be790bd79de00e844c3b`。

**原始证据：** [P02.json](../../exp/configs/P02.json) · [P02.md](../../experiments/P02_signed8_direct_control/P02.md) · [config.json](../../experiments/P02_signed8_direct_control/config.json) · [metrics.json](../../experiments/P02_signed8_direct_control/metrics.json) · [csynth.rpt](../../experiments/P02_signed8_direct_control/csynth.rpt) · [csynth.log.txt](../../experiments/P02_signed8_direct_control/csynth.log.txt) · [csim.log.txt](../../experiments/P02_signed8_direct_control/csim.log.txt)。

<a id="p03"></a>

### P03：七项后再拆包

**基于：** [P01](#p01)（设计或参数基线）。

**调整：** 在 signed8 安全界内累加七个打包乘积，再解码。

**效果与问题：** 累加/解码增加 LUT 和 FF；七项界不能直接用于十位输入。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 62 / 60 cycles |
| 注册表换算时间 | 0.000248 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 299 / 309 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`f89b4b1df40e067c8203b67ceae719fed999f9c1`。

**原始证据：** [P03.json](../../exp/configs/P03.json) · [P03.md](../../experiments/P03_signed8_group7/P03.md) · [config.json](../../experiments/P03_signed8_group7/config.json) · [metrics.json](../../experiments/P03_signed8_group7/metrics.json) · [csynth.rpt](../../experiments/P03_signed8_group7/csynth.rpt) · [csynth.log.txt](../../experiments/P03_signed8_group7/csynth.log.txt) · [csim.log.txt](../../experiments/P03_signed8_group7/csim.log.txt)。

<a id="p04"></a>

### P04：自动识别 Packing 表达式

**基于：** [P01](#p01)（设计或参数基线）。

**调整：** 去掉显式 DSP 绑定，观察编译器是否识别表达式。

**效果与问题：** 局部映射成功不证明整个网络可以自动得到最优架构。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 61 / 56 cycles |
| 注册表换算时间 | 0.000244 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 132 / 86 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`21f3955ae9491415b39f1e283b5b96d37f13da84`。

**原始证据：** [P04.json](../../exp/configs/P04.json) · [P04.md](../../experiments/P04_signed8_auto_mapping/P04.md) · [config.json](../../experiments/P04_signed8_auto_mapping/config.json) · [metrics.json](../../experiments/P04_signed8_auto_mapping/metrics.json) · [csynth.rpt](../../experiments/P04_signed8_auto_mapping/csynth.rpt) · [csynth.log.txt](../../experiments/P04_signed8_auto_mapping/csynth.log.txt) · [csim.log.txt](../../experiments/P04_signed8_auto_mapping/csim.log.txt)。

<a id="p05"></a>

### P05：DSP pre-adder builtin

**基于：** [P01](#p01)（设计或参数基线）。

**调整：** 使用 SDK 的 DSP48E2 builtin 显式表达预加和流水级。

**效果与问题：** 需要 P08 检查实际 primitive 属性，DSP 数量本身不是 pre-adder 使用证据。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 1.641 ns |
| 延迟 / 间隔 | 63 / 56 cycles |
| 注册表换算时间 | 0.000252 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 127 / 162 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`646ed9406c60b0b21abde8152d382b51231f80e8`。

**原始证据：** [P05.json](../../exp/configs/P05.json) · [P05.md](../../experiments/P05_signed8_builtin_preadder/P05.md) · [config.json](../../experiments/P05_signed8_builtin_preadder/config.json) · [metrics.json](../../experiments/P05_signed8_builtin_preadder/metrics.json) · [csynth.rpt](../../experiments/P05_signed8_builtin_preadder/csynth.rpt) · [csynth.log.txt](../../experiments/P05_signed8_builtin_preadder/csynth.log.txt) · [csim.log.txt](../../experiments/P05_signed8_builtin_preadder/csim.log.txt)。

<a id="p06"></a>

### P06：非负十位激活，两项拆包

**基于：** [P01](#p01)（设计或参数基线）；[E071](#e071)（数值依据或研究启发）。

**调整：** 共享激活范围 0..511 时，低字段最多安全累加两项。

**效果与问题：** 必须保留范围界；泛化 signed10 不能沿用此分组。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 62 / 60 cycles |
| 注册表换算时间 | 0.000248 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 274 / 424 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`cc24997b60dd4532fe676e3b6b3f3761f685d633`。

**原始证据：** [P06.json](../../exp/configs/P06.json) · [P06.md](../../experiments/P06_nonnegative10_group2/P06.md) · [config.json](../../experiments/P06_nonnegative10_group2/config.json) · [metrics.json](../../experiments/P06_nonnegative10_group2/metrics.json) · [csynth.rpt](../../experiments/P06_nonnegative10_group2/csynth.rpt) · [csynth.log.txt](../../experiments/P06_nonnegative10_group2/csynth.log.txt) · [csim.log.txt](../../experiments/P06_nonnegative10_group2/csim.log.txt)。

<a id="p07"></a>

### P07：精确十位系数残差修复

**基于：** [P01](#p01)（设计或参数基线）；[E017](#e017)（数值依据或研究启发）。

**调整：** 系数拆成低八位与 256 倍残差，在 fabric 中精确恢复。

**效果与问题：** 保留十位质量，但每个乘积拆包和残差修复增加成本。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 62 / 56 cycles |
| 注册表换算时间 | 0.000248 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 454 / 453 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`ceb5d2172224a4c94e1b41379086b242e997275f`。

**原始证据：** [P07.json](../../exp/configs/P07.json) · [P07.md](../../experiments/P07_exact10_residual_pair/P07.md) · [config.json](../../experiments/P07_exact10_residual_pair/config.json) · [metrics.json](../../experiments/P07_exact10_residual_pair/metrics.json) · [csynth.rpt](../../experiments/P07_exact10_residual_pair/csynth.rpt) · [csynth.log.txt](../../experiments/P07_exact10_residual_pair/csynth.log.txt) · [csim.log.txt](../../experiments/P07_exact10_residual_pair/csim.log.txt)。

<a id="p08"></a>

### P08：检查实际 DSP pre-adder

**基于：** [P05](#p05)（验证同一设计）。

**调整：** Vivado 实现后检查 DSP48E2 的 AMULTSEL、ADREG 等属性。

**效果与问题：** 证明的是该 PE 的硬件映射，不是 SRCNN 整网部署。

**记录状态：** `impl_complete` / 实现完成，另看时序；范围 `PE`；步骤 `impl`。

继承的 HLS 估计来自 [P05](#p05)，不作为本步骤的新测量。

实现：WNS=2.805 ns；TNS=0 ns；timing_met=true。实际 DSP / BRAM36 / URAM / LUT / FF = 1 / 0 / 0 / 21 / 41。BRAM36 与 HLS 的 BRAM18K 单位不同。

工具：Vitis 2026.1；源码提交：`6deee22d85535da7a17fffd4b7a6d574004f5670`。

**原始证据：** [P08.json](../../exp/configs/P08.json) · [P08.md](../../experiments/P08_builtin_mapping_implementation/P08.md) · [config.json](../../experiments/P08_builtin_mapping_implementation/config.json) · [metrics.json](../../experiments/P08_builtin_mapping_implementation/metrics.json) · [verification.json](../../experiments/P08_builtin_mapping_implementation/verification.json) · [impl.log.txt](../../experiments/P08_builtin_mapping_implementation/impl.log.txt) · [primitive_probe.json](../../experiments/P08_builtin_mapping_implementation/primitive_probe.json) · [dsp_primitives.csv](../../experiments/P08_builtin_mapping_implementation/dsp_primitives.csv) · [packing_pe_timing_routed.rpt](../../experiments/P08_builtin_mapping_implementation/reports/impl/packing_pe_timing_routed.rpt) · [packing_pe_utilization_routed.rpt](../../experiments/P08_builtin_mapping_implementation/reports/impl/packing_pe_utilization_routed.rpt)。

<a id="p09"></a>

### P09：冻结记录复现

**基于：** [P01](#p01)（复现同一实验）。

**调整：** 新 ID 恢复 P01 的源码、测试和参数，验证复现机制。

**效果与问题：** 复现控制没有提出新 Packing 算法。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 61 / 56 cycles |
| 注册表换算时间 | 0.000244 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1 / 0 / 0 |
| LUT / FF | 132 / 86 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`6c22c8658b1a543cac6dc6d16af57e5eb4a2c88b`。

**原始证据：** [P09.json](../../exp/configs/P09.json) · [P09.md](../../experiments/P09_reproduction_P01/P09.md) · [config.json](../../experiments/P09_reproduction_P01/config.json) · [metrics.json](../../experiments/P09_reproduction_P01/metrics.json) · [csynth.rpt](../../experiments/P09_reproduction_P01/csynth.rpt) · [csynth.log.txt](../../experiments/P09_reproduction_P01/csynth.log.txt) · [csim.log.txt](../../experiments/P09_reproduction_P01/csim.log.txt)。

<a id="p10"></a>

### P10：精确十位 Packing 整网 T16

**基于：** [E048](#e048)（设计或参数基线）；[P07](#p07)（集成已有模块）。

**调整：** Conv1/2 打包输出通道，Conv3 打包相邻输出像素。

**效果与问题：** DSP 减少，但 LUT 101,488 超项目预算；逐像素流水开销仍大。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 3039083 / 3039084 cycles |
| 注册表换算时间 | 12.156332 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 101488 / 80563 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`4e606cdf69af0b43ae5cf7acbffb9806d278e6a6`。

**原始证据：** [P10.json](../../exp/configs/P10.json) · [P10.md](../../experiments/P10_exact10_packing_T16/P10.md) · [config.json](../../experiments/P10_exact10_packing_T16/config.json) · [metrics.json](../../experiments/P10_exact10_packing_T16/metrics.json) · [csynth.rpt](../../experiments/P10_exact10_packing_T16/csynth.rpt) · [csynth.log.txt](../../experiments/P10_exact10_packing_T16/csynth.log.txt) · [csim.log.txt](../../experiments/P10_exact10_packing_T16/csim.log.txt)。

<a id="p11"></a>

### P11：精确十位 Packing 整网 T8

**基于：** [P10](#p10)（设计或参数基线）。

**调整：** 相同算术加大并行度。

**效果与问题：** LUT 165,606 超量；省乘法器没有解决选择器和修复成本。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 1894302 / 1894303 cycles |
| 注册表换算时间 | 7.577208 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 168 / 0 |
| LUT / FF | 165606 / 106599 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`ed612f4c08cfe64b772b55acb2ae440a3d4488d3`。

**原始证据：** [P11.json](../../exp/configs/P11.json) · [P11.md](../../experiments/P11_exact10_packing_T8/P11.md) · [config.json](../../experiments/P11_exact10_packing_T8/config.json) · [metrics.json](../../experiments/P11_exact10_packing_T8/metrics.json) · [csynth.rpt](../../experiments/P11_exact10_packing_T8/csynth.rpt) · [csynth.log.txt](../../experiments/P11_exact10_packing_T8/csynth.log.txt) · [csim.log.txt](../../experiments/P11_exact10_packing_T8/csim.log.txt)。

<a id="p12"></a>

### P12：精确十位 Packing 整网 T4

**基于：** [P10](#p10)（设计或参数基线）。

**调整：** 进一步提高并行度，比较时间与资源的取舍。

**效果与问题：** LUT 292,053 超量；较低估计延迟不能进入合格候选排名。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 1355582 / 1355583 cycles |
| 注册表换算时间 | 5.422328 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1007 / 168 / 0 |
| LUT / FF | 292053 / 159828 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`580a5f33c3aa35ba7101090bf4ebd1d5d59e7a1e`。

**原始证据：** [P12.json](../../exp/configs/P12.json) · [P12.md](../../experiments/P12_exact10_packing_T4/P12.md) · [config.json](../../experiments/P12_exact10_packing_T4/config.json) · [metrics.json](../../experiments/P12_exact10_packing_T4/metrics.json) · [csynth.rpt](../../experiments/P12_exact10_packing_T4/csynth.rpt) · [csynth.log.txt](../../experiments/P12_exact10_packing_T4/csynth.log.txt) · [csim.log.txt](../../experiments/P12_exact10_packing_T4/csim.log.txt)。

<a id="p13"></a>

### P13：完整 INT16 双乘法控制

**基于：** [E054](#e054)（数值依据或研究启发）。

**调整：** 在相同输入/输出和吞吐率下直接计算两路 signed16x16，作为新研究基线。

**效果与问题：** 此快照仅有计划/准备，不能填入已测两 DSP 或 II1。

**记录状态：** `planned` / 已准备，未归档测量；范围 `PE`；步骤 `plan`。
附加检查：未归档测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [P13.json](../../exp/configs/P13.json)。

<a id="p14"></a>

### P14：INT16 拆肢 Packing

**基于：** [P13](#p13)（对照实验）；[P01](#p01)（数值依据或研究启发）。

**调整：** 拆分十六位操作数，组合小位宽打包乘积，完整恢复两个 32 位结果。

**效果与问题：** 拆包、部分积和 fabric 乘法都要计成本；此快照没有结果。

**记录状态：** `planned` / 已准备，未归档测量；范围 `PE`；步骤 `plan`。
附加检查：未归档测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [P14.json](../../exp/configs/P14.json)。

<a id="p15"></a>

### P15：INT16 重叠字段与 fabric 修复

**基于：** [P13](#p13)（对照实验）；[P01](#p01)（数值依据或研究启发）。

**调整：** 允许字段重叠，再用精确 fabric 算术恢复两路完整乘积。

**效果与问题：** 不能预设一 DSP 等于两路完整乘法的总成本；结果待归档。

**记录状态：** `planned` / 已准备，未归档测量；范围 `PE`；步骤 `plan`。
附加检查：未归档测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [P15.json](../../exp/configs/P15.json)。

<a id="p16"></a>

### P16：INT16 一 DSP 加一 fabric 控制

**基于：** [P13](#p13)（对照实验）。

**调整：** 直接把一条乘法放在 DSP、一条放在 LUT，匹配 P15 的资源类型。

**效果与问题：** 用它判断重叠 Packing 是否优于普通混合映射；此快照没有结果。

**记录状态：** `planned` / 已准备，未归档测量；范围 `PE`；步骤 `plan`。
附加检查：未归档测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [P16.json](../../exp/configs/P16.json)。

<a id="scatter"></a>

## C：Gather 与 Scatter 的存储/控制取舍

先跨通道求和再缓存，能节省多少 BRAM，代价是什么？

[演进图](scatter.svg)；路线依据：[exp/prepare_arch_g.py](../../exp/prepare_arch_g.py) · [exp/build_arch_g.py](../../exp/build_arch_g.py)。

<a id="g01"></a>

### G01：Gather 统一控制

**基于：** [E057](#e057)（设计或参数基线）。

**调整：** 独立复测相同 T32、10 ns、十位精度的 Conv3 行缓存组织。

**效果与问题：** 作为 Scatter 对照；三种组织必须在相同参数下比较。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2983024 / 2983025 cycles |
| 注册表换算时间 | 29.83024 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 44493 / 46328 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`7b367963c469edd1c60c605a12797428270e24ec`。

**原始证据：** [G01.json](../../exp/configs/G01.json) · [G01.md](../../experiments/G01_gather_control/G01.md) · [config.json](../../experiments/G01_gather_control/config.json) · [metrics.json](../../experiments/G01_gather_control/metrics.json) · [csynth.rpt](../../experiments/G01_gather_control/csynth.rpt) · [csynth.log.txt](../../experiments/G01_gather_control/csynth.log.txt) · [csim.log.txt](../../experiments/G01_gather_control/csim.log.txt)。

<a id="g02"></a>

### G02：显式补边 Scatter

**基于：** [E060](#e060)（设计或参数基线）；[G01](#g01)（对照实验）。

**调整：** 存五行 32 位部分和，保留原来的 32 通道补边。

**效果与问题：** BRAM18K 168 降到 137，但估计延迟 29.83 增至 37.70 ms。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 3770206 / 3770207 cycles |
| 注册表换算时间 | 37.70206 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 137 / 0 |
| LUT / FF | 39135 / 24841 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`98c6287b7606373b795bfd0436a67879931184f0`。

**原始证据：** [G02.json](../../exp/configs/G02.json) · [G02.md](../../experiments/G02_scatter_pad_control/G02.md) · [config.json](../../experiments/G02_scatter_pad_control/config.json) · [metrics.json](../../experiments/G02_scatter_pad_control/metrics.json) · [csynth.rpt](../../experiments/G02_scatter_pad_control/csynth.rpt) · [csynth.log.txt](../../experiments/G02_scatter_pad_control/csynth.log.txt) · [csim.log.txt](../../experiments/G02_scatter_pad_control/csim.log.txt)。

<a id="g03"></a>

### G03：合并边界核 Scatter

**基于：** [G02](#g02)（设计或参数基线）。

**调整：** 把九种边界位置的重复 taps 合并，移除宽通道补边缓存。

**效果与问题：** BRAM18K 进一步降到 87，但核选择、加载和控制使延迟增至约 44.14 ms。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 4413926 / 4413927 cycles |
| 注册表换算时间 | 44.13926 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 87 / 0 |
| LUT / FF | 40677 / 25230 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`d0ccc144c6d39a9b2aa08e3c29b32ad1a7cf8976`。

**原始证据：** [G03.json](../../exp/configs/G03.json) · [G03.md](../../experiments/G03_scatter_edge_kernels/G03.md) · [config.json](../../experiments/G03_scatter_edge_kernels/config.json) · [metrics.json](../../experiments/G03_scatter_edge_kernels/metrics.json) · [csynth.rpt](../../experiments/G03_scatter_edge_kernels/csynth.rpt) · [csynth.log.txt](../../experiments/G03_scatter_edge_kernels/csynth.log.txt) · [csim.log.txt](../../experiments/G03_scatter_edge_kernels/csim.log.txt)。

<a id="memory"></a>

## 存储路线：整网数据流、外存探针和分块融合

外存或小块缓存能否替代全图存储，且保持正确边界？

[演进图](memory.svg)；路线依据：[exp/prepare_arch_s.py](../../exp/prepare_arch_s.py) · [exp/build_arch_s.py](../../exp/build_arch_s.py) · [experiments/bursts.csv](../../experiments/bursts.csv)。

<a id="s01"></a>

### S01：全局数组 DDR 接口探针

**基于：** [E048](#e048)（设计或参数基线）。

**调整：** 尝试给全局 scratch 数组导出 AXI 端口，研究层间外存组织。

**效果与问题：** scratch1/2 端口没有生成；实际仍是巨大片上数组，此记录不是有效 DDR 实现。

**记录状态：** `invalid_config` / 配置无效；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: BRAM18K；配置无效。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 16730473 / 16730474 cycles |
| 注册表换算时间 | 167.30473 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 11286 / 0 |
| LUT / FF | 48121 / 49034 |
| 所检查的 II 目标 | 未记录 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`1fa3d1916402d43dca0d9b0e4c68685a956dde39`。

**原始证据：** [S01.json](../../exp/configs/S01.json) · [S01.md](../../experiments/S01_ddr_global_probe/S01.md) · [config.json](../../experiments/S01_ddr_global_probe/config.json) · [metrics.json](../../experiments/S01_ddr_global_probe/metrics.json) · [csynth.rpt](../../experiments/S01_ddr_global_probe/csynth.rpt) · [csynth.log.txt](../../experiments/S01_ddr_global_probe/csynth.log.txt) · [csim.log.txt](../../experiments/S01_ddr_global_probe/csim.log.txt)。

<a id="s02"></a>

### S02：整网数据流对照

**基于：** [G01](#g01)（设计或参数基线）。

**调整：** 复用统一 gather 设计，作为分块融合的整网对照。

**效果与问题：** 这是同一设计的复测，不是另外一种网络。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 2983024 / 2983025 cycles |
| 注册表换算时间 | 29.83024 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 254 / 168 / 0 |
| LUT / FF | 44493 / 46328 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`3071af7264b43754e13820760c80952f77907b55`。

**原始证据：** [S02.json](../../exp/configs/S02.json) · [S02.md](../../experiments/S02_whole_dataflow_control/S02.md) · [config.json](../../experiments/S02_whole_dataflow_control/config.json) · [metrics.json](../../experiments/S02_whole_dataflow_control/metrics.json) · [csynth.rpt](../../experiments/S02_whole_dataflow_control/csynth.rpt) · [csynth.log.txt](../../experiments/S02_whole_dataflow_control/csynth.log.txt) · [csim.log.txt](../../experiments/S02_whole_dataflow_control/csim.log.txt)。

<a id="s03"></a>

### S03：三层融合输出块 B8

**基于：** [E048](#e048)（设计或参数基线）；[S02](#s02)（对照实验）。

**调整：** 每块重算所需 halo，局部融合 Conv1/2 并缓存 Conv2 小块。

**效果与问题：** BRAM 很少，但 halo 重算、分银行和地址选择带来时间与 LUT 开销。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 22803545 / 22803546 cycles |
| 注册表换算时间 | 228.03545 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 113576 / 73880 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`0fc4d3ff9afb1d36f0b457debcbb06406e50fefc`。

**原始证据：** [S03.json](../../exp/configs/S03.json) · [S03.md](../../experiments/S03_tile_fusion_B8/S03.md) · [config.json](../../experiments/S03_tile_fusion_B8/config.json) · [metrics.json](../../experiments/S03_tile_fusion_B8/metrics.json) · [csynth.rpt](../../experiments/S03_tile_fusion_B8/csynth.rpt) · [csynth.log.txt](../../experiments/S03_tile_fusion_B8/csynth.log.txt) · [csim.log.txt](../../experiments/S03_tile_fusion_B8/csim.log.txt)。

<a id="s04"></a>

### S04：三层融合输出块 B16

**基于：** [S03](#s03)（设计或参数基线）。

**调整：** 扩大块，减少相对 halo 重算量。

**效果与问题：** 仍是顺序块执行，无法获得整网流引擎的重叠；LUT 超量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 16753977 / 16753978 cycles |
| 注册表换算时间 | 167.53977 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 114061 / 73901 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c1e9023e9d890ec0552489a75ae43da5583dce12`。

**原始证据：** [S04.json](../../exp/configs/S04.json) · [S04.md](../../experiments/S04_tile_fusion_B16/S04.md) · [config.json](../../experiments/S04_tile_fusion_B16/config.json) · [metrics.json](../../experiments/S04_tile_fusion_B16/metrics.json) · [csynth.rpt](../../experiments/S04_tile_fusion_B16/csynth.rpt) · [csynth.log.txt](../../experiments/S04_tile_fusion_B16/csynth.log.txt) · [csim.log.txt](../../experiments/S04_tile_fusion_B16/csim.log.txt)。

<a id="s05"></a>

### S05：三层融合输出块 B32

**基于：** [S03](#s03)（设计或参数基线）。

**调整：** 继续扩大输出块，比较缓存与重算。

**效果与问题：** 流量下界降低，但实际综合延迟和 LUT 仍不合格。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 14166377 / 14166378 cycles |
| 注册表换算时间 | 141.66377 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 120033 / 74038 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`976b14de2be87aa7320f621c9f8043f92d710ebe`。

**原始证据：** [S05.json](../../exp/configs/S05.json) · [S05.md](../../experiments/S05_tile_fusion_B32/S05.md) · [config.json](../../experiments/S05_tile_fusion_B32/config.json) · [metrics.json](../../experiments/S05_tile_fusion_B32/metrics.json) · [csynth.rpt](../../experiments/S05_tile_fusion_B32/csynth.rpt) · [csynth.log.txt](../../experiments/S05_tile_fusion_B32/csynth.log.txt) · [csim.log.txt](../../experiments/S05_tile_fusion_B32/csim.log.txt)。

<a id="s06"></a>

### S06：三层融合输出块 B64

**基于：** [S03](#s03)（设计或参数基线）。

**调整：** 扫描中最大输出块，含真实图像边缘复制与不完整块。

**效果与问题：** 减少 halo 比例仍未抵消控制/缓存代价；带宽计算是模型，不是板端测量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 10 / 7.3 ns |
| 延迟 / 间隔 | 12981873 / 12981874 cycles |
| 注册表换算时间 | 129.81873 ms（frame 范围，以 10 ns 换算） |
| DSP / BRAM18K / URAM | 296 / 18 / 0 |
| LUT / FF | 136162 / 74127 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`2f507fd6b535a9c3762731134d2ce3b2517f9887`。

**原始证据：** [S06.json](../../exp/configs/S06.json) · [S06.md](../../experiments/S06_tile_fusion_B64/S06.md) · [config.json](../../experiments/S06_tile_fusion_B64/config.json) · [metrics.json](../../experiments/S06_tile_fusion_B64/metrics.json) · [csynth.rpt](../../experiments/S06_tile_fusion_B64/csynth.rpt) · [csynth.log.txt](../../experiments/S06_tile_fusion_B64/csynth.log.txt) · [csim.log.txt](../../experiments/S06_tile_fusion_B64/csim.log.txt)。

<a id="winograd"></a>

## D：Winograd，从精确变换到连续调度和权重银行

乘法减少以后，变换、重排和宽位缓存是否成为更大的成本？

[演进图](winograd.svg)；路线依据：[exp/prepare_arch_pe.py](../../exp/prepare_arch_pe.py) · [exp/prepare_arch_full.py](../../exp/prepare_arch_full.py) · [exp/prepare_header_retry.py](../../exp/prepare_header_retry.py) · [exp/prepare_wino_continuous.py](../../exp/prepare_wino_continuous.py) · [exp/prepare_split_windows.py](../../exp/prepare_split_windows.py) · [exp/prepare_raw_weight_banks.py](../../exp/prepare_raw_weight_banks.py)。

<a id="w01"></a>

### W01：十位整数 F(2x2,3x3) PE

**基于：** [E071](#e071)（数值依据或研究启发）。

**调整：** 用 G2=2G 保留整数变换，逆变换精确除以四再量化。

**效果与问题：** 局部乘法数减少，但变换加法、位宽、重排和整网调度尚未计入。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 2.895 ns |
| 延迟 / 间隔 | 36 / 32 cycles |
| 注册表换算时间 | 0.000144 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 16 / 0 / 0 |
| LUT / FF | 1499 / 1124 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`8460ada1708647dfab881c05b9e638bb6fa0450b`。

**原始证据：** [W01.json](../../exp/configs/W01.json) · [W01.md](../../experiments/W01_integer_f2_10bit/W01.md) · [config.json](../../experiments/W01_integer_f2_10bit/config.json) · [metrics.json](../../experiments/W01_integer_f2_10bit/metrics.json) · [csynth.rpt](../../experiments/W01_integer_f2_10bit/csynth.rpt) · [csynth.log.txt](../../experiments/W01_integer_f2_10bit/csynth.log.txt) · [csim.log.txt](../../experiments/W01_integer_f2_10bit/csim.log.txt)。

<a id="w02"></a>

### W02：直接卷积 PE 控制

**基于：** [W01](#w01)（对照实验）。

**调整：** 相同 tile 的直接 36 次乘法，比较 Winograd 的 16 次乘法。

**效果与问题：** DSP 减少伴随更多 LUT；PE 周期不能当作整图延迟。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 2.463 ns |
| 延迟 / 间隔 | 38 / 32 cycles |
| 注册表换算时间 | 0.000152 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 36 / 0 / 0 |
| LUT / FF | 503 / 1025 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`f7e68f798215348867fb3be8b25fe71b5991f861`。

**原始证据：** [W02.json](../../exp/configs/W02.json) · [W02.md](../../experiments/W02_direct_f2_control/W02.md) · [config.json](../../experiments/W02_direct_f2_control/config.json) · [metrics.json](../../experiments/W02_direct_f2_control/metrics.json) · [csynth.rpt](../../experiments/W02_direct_f2_control/csynth.rpt) · [csynth.log.txt](../../experiments/W02_direct_f2_control/csynth.log.txt) · [csim.log.txt](../../experiments/W02_direct_f2_control/csim.log.txt)。

<a id="w03"></a>

### W03：十六位 Winograd PE

**基于：** [W01](#w01)（设计或参数基线）。

**调整：** 增加输入/权重位宽，测量变换后的 18x20 位乘法映射。

**效果与问题：** 通过的是 Winograd 小内核；不是 INT16 Packing 或整网十六位部署。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 2.179 ns |
| 延迟 / 间隔 | 37 / 32 cycles |
| 注册表换算时间 | 0.000148 ms（PE 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 16 / 0 / 0 |
| LUT / FF | 2155 / 1932 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`b55d6e3e8eb84c9cb1214335125512f610b61f30`。

**原始证据：** [W03.json](../../exp/configs/W03.json) · [W03.md](../../experiments/W03_integer_f2_16bit/W03.md) · [config.json](../../experiments/W03_integer_f2_16bit/config.json) · [metrics.json](../../experiments/W03_integer_f2_16bit/metrics.json) · [csynth.rpt](../../experiments/W03_integer_f2_16bit/csynth.rpt) · [csynth.log.txt](../../experiments/W03_integer_f2_16bit/csynth.log.txt) · [csim.log.txt](../../experiments/W03_integer_f2_16bit/csim.log.txt)。

<a id="w04"></a>

### W04：Winograd Conv1 单层 T16

**基于：** [E048](#e048)（设计或参数基线）；[W01](#w01)（集成已有模块）。

**调整：** 把 9x9 核拆为九个 3x3，运行时变换权重并重排 tile 输出。

**效果与问题：** 维度宏 F2/F3 与 AMD 头文件标识符冲突，编译失败。

**记录状态：** `fail` / 运行失败；范围 `layer`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`9e69c4831a7dfd219383f72ae97ef36914ff483d`。

**原始证据：** [W04.json](../../exp/configs/W04.json) · [W04.md](../../experiments/W04_winograd_conv1_T16/W04.md) · [config.json](../../experiments/W04_winograd_conv1_T16/config.json) · [metrics.json](../../experiments/W04_winograd_conv1_T16/metrics.json) · [csim.log.txt](../../experiments/W04_winograd_conv1_T16/csim.log.txt)。

<a id="w05"></a>

### W05：Winograd 整网 T16

**基于：** [W04](#w04)（设计或参数基线）。

**调整：** 把 Conv1 Winograd 与 Conv2/3 接起来测整图。

**效果与问题：** 相同头文件冲突；未得到有效综合结果。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`82a84d9a0885c02bbe05cfaf366a312b9fbf27fa`。

**原始证据：** [W05.json](../../exp/configs/W05.json) · [W05.md](../../experiments/W05_winograd_network_T16/W05.md) · [config.json](../../experiments/W05_winograd_network_T16/config.json) · [metrics.json](../../experiments/W05_winograd_network_T16/metrics.json) · [csim.log.txt](../../experiments/W05_winograd_network_T16/csim.log.txt)。

<a id="w06"></a>

### W06：Winograd 整网 T8

**基于：** [W05](#w05)（设计或参数基线）。

**调整：** 改变并行度，在相同数值契约下测更快目标。

**效果与问题：** 同样未通过编译，后续 W09 独立重试。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`5be485ae1b731a750192cbae423efb082ea0ee56`。

**原始证据：** [W06.json](../../exp/configs/W06.json) · [W06.md](../../experiments/W06_winograd_network_T8/W06.md) · [config.json](../../experiments/W06_winograd_network_T8/config.json) · [metrics.json](../../experiments/W06_winograd_network_T8/metrics.json) · [csim.log.txt](../../experiments/W06_winograd_network_T8/csim.log.txt)。

<a id="w07"></a>

### W07：单层头文件顺序修复

**基于：** [W04](#w04)（修复后重试）。

**调整：** 先包含 AMD 类型头文件，再定义网络尺寸宏。

**效果与问题：** 得到有效单层结果，但条件 tile 循环被 HLS 估成过多计算迭代。

**记录状态：** `provisional` / 候选，仍需验收；范围 `layer`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 2.92 ns |
| 延迟 / 间隔 | 5721420 / 5721421 cycles |
| 注册表换算时间 | 22.88568 ms（layer 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 145 / 99 / 0 |
| LUT / FF | 30872 / 25564 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true；butterfly MSE=5.154311903422524e-06；六像素边界 MSE=4.121844856441791e-06。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`ed8ca280b9c20de633502eea77a4d12f859df26e`。

**原始证据：** [W07.json](../../exp/configs/W07.json) · [W07.md](../../experiments/W07_winograd_conv1_T16_header_retry/W07.md) · [config.json](../../experiments/W07_winograd_conv1_T16_header_retry/config.json) · [metrics.json](../../experiments/W07_winograd_conv1_T16_header_retry/metrics.json) · [csynth.rpt](../../experiments/W07_winograd_conv1_T16_header_retry/csynth.rpt) · [csynth.log.txt](../../experiments/W07_winograd_conv1_T16_header_retry/csynth.log.txt) · [csim.log.txt](../../experiments/W07_winograd_conv1_T16_header_retry/csim.log.txt)。

<a id="w08"></a>

### W08：整网 T16 头文件修复

**基于：** [W05](#w05)（修复后重试）。

**调整：** 在独立源码副本修复包含顺序。

**效果与问题：** 约 22.8954 ms；合法且精确，但 tile 调度与缓存开销很大。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 5723851 / 5723852 cycles |
| 注册表换算时间 | 22.895404 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 326 / 241 / 0 |
| LUT / FF | 75814 / 69105 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`23c3e163beadc2007e17a75e66bc93010b718832`。

**原始证据：** [W08.json](../../exp/configs/W08.json) · [W08.md](../../experiments/W08_winograd_network_T16_header_retry/W08.md) · [config.json](../../experiments/W08_winograd_network_T16_header_retry/config.json) · [metrics.json](../../experiments/W08_winograd_network_T16_header_retry/metrics.json) · [csynth.rpt](../../experiments/W08_winograd_network_T16_header_retry/csynth.rpt) · [csynth.log.txt](../../experiments/W08_winograd_network_T16_header_retry/csynth.log.txt) · [csim.log.txt](../../experiments/W08_winograd_network_T16_header_retry/csim.log.txt)。

<a id="w09"></a>

### W09：整网 T8 头文件修复

**基于：** [W06](#w06)（修复后重试）。

**调整：** 相同修复下测 T8 并行度。

**效果与问题：** 约 135,496 LUT 超预算，权重变换加载中的选择器/寄存器成本很高。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 3493579 / 3493580 cycles |
| 注册表换算时间 | 13.974316 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 648 / 241 / 0 |
| LUT / FF | 135496 / 148761 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`42da116108fa1635f7e63b49fb19b6d9fe457f82`。

**原始证据：** [W09.json](../../exp/configs/W09.json) · [W09.md](../../experiments/W09_winograd_network_T8_header_retry/W09.md) · [config.json](../../experiments/W09_winograd_network_T8_header_retry/config.json) · [metrics.json](../../experiments/W09_winograd_network_T8_header_retry/metrics.json) · [csynth.rpt](../../experiments/W09_winograd_network_T8_header_retry/csynth.rpt) · [csynth.log.txt](../../experiments/W09_winograd_network_T8_header_retry/csynth.log.txt) · [csim.log.txt](../../experiments/W09_winograd_network_T8_header_retry/csim.log.txt)。

<a id="w10"></a>

### W10：固定 tile 循环，仅 Conv1 连续

**基于：** [W08](#w08)（设计或参数基线）；[F03](#f03)（数值依据或研究启发）。

**调整：** 分离窗口生成与固定次数 MAC 循环，消除条件边界对循环估计的膨胀。

**效果与问题：** 约 7.5482 ms；Conv2/3 逐像素流水开销仍在，使用 241 BRAM18K。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 1887051 / 1887052 cycles |
| 注册表换算时间 | 7.548204 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 326 / 241 / 0 |
| LUT / FF | 79158 / 76052 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`d048887dade9486661e7bab5265ac970c15255e5`。

**原始证据：** [W10.json](../../exp/configs/W10.json) · [W10.md](../../experiments/W10_fixed_tiles_T16_c1only_4ns/W10.md) · [config.json](../../experiments/W10_fixed_tiles_T16_c1only_4ns/config.json) · [metrics.json](../../experiments/W10_fixed_tiles_T16_c1only_4ns/metrics.json) · [csynth.rpt](../../experiments/W10_fixed_tiles_T16_c1only_4ns/csynth.rpt) · [csynth.log.txt](../../experiments/W10_fixed_tiles_T16_c1only_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/W10_fixed_tiles_T16_c1only_4ns/csim.log.txt)。

<a id="w11"></a>

### W11：三层连续，T8，4 ns

**基于：** [W10](#w10)（设计或参数基线）。

**调整：** 推广连续调度到其他层，扫描 T8。

**效果与问题：** C 仿真精确，但 Conv3 的 8000 位流超过工具 4096 位限制。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`3dee20bd819d52cfe2ce81e22aaa4d3f10cdb27c`。

**原始证据：** [W11.json](../../exp/configs/W11.json) · [W11.md](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/W11.md) · [config.json](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/config.json) · [metrics.json](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/metrics.json) · [csynth.log.txt](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/W11_fixed_tiles_T8_allcontinuous_4ns/csim.log.txt)。

<a id="w12"></a>

### W12：三层连续，T16，4 ns

**基于：** [W10](#w10)（设计或参数基线）。

**调整：** 在 T16 下测连续三层组织。

**效果与问题：** 相同宽流限制导致综合失败；不是数值精度失败。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`8a51d12f0fa70218d0493eeaf8d09c59d6e6265c`。

**原始证据：** [W12.json](../../exp/configs/W12.json) · [W12.md](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/W12.md) · [config.json](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/config.json) · [metrics.json](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/metrics.json) · [csynth.log.txt](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/W12_fixed_tiles_T16_allcontinuous_4ns/csim.log.txt)。

<a id="w13"></a>

### W13：三层连续，T8，3.33 ns

**基于：** [W11](#w11)（设计或参数基线）。

**调整：** 在同一连续组织收紧目标周期。

**效果与问题：** 宽流限制仍未修复，未得到性能结果。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`6bce6339078e0cd50e10f2cfbe39485d5e465a94`。

**原始证据：** [W13.json](../../exp/configs/W13.json) · [W13.md](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/W13.md) · [config.json](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/config.json) · [metrics.json](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/metrics.json) · [csynth.log.txt](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/csynth.log.txt) · [csim.log.txt](../../experiments/W13_fixed_tiles_T8_allcontinuous_3p33ns/csim.log.txt)。

<a id="w14"></a>

### W14：T8 双 4000 位窗口流

**基于：** [W11](#w11)（修复后重试）。

**调整：** 把一个完整 Conv3 窗口分成同步的两个通道，不改变算术。

**效果与问题：** 综合合法、估计约 2.1302 ms，但 LUT/FF 超预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 532562 / 532563 cycles |
| 注册表换算时间 | 2.130248 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 648 / 146 / 0 |
| LUT / FF | 148013 / 182409 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`74adcad868fcc049ace36cb3232eaa337adafa4d`。

**原始证据：** [W14.json](../../exp/configs/W14.json) · [W14.md](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/W14.md) · [config.json](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/config.json) · [metrics.json](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/metrics.json) · [csynth.rpt](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/W14_fixed_tiles_T8_allcontinuous_4ns_split4000/csim.log.txt)。

<a id="w15"></a>

### W15：T16 双窗口流

**基于：** [W12](#w12)（修复后重试）。

**调整：** 修正 T16 的流表示。

**效果与问题：** 约 4.2274 ms，但 LUT 89,114 仍高于项目预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 1056850 / 1056851 cycles |
| 注册表换算时间 | 4.2274 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 326 / 146 / 0 |
| LUT / FF | 89114 / 92946 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`03a4a03eb8e1166b3c9d18cf18593028b2b6ff82`。

**原始证据：** [W15.json](../../exp/configs/W15.json) · [W15.md](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/W15.md) · [config.json](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/config.json) · [metrics.json](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/metrics.json) · [csynth.rpt](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/W15_fixed_tiles_T16_allcontinuous_4ns_split4000/csim.log.txt)。

<a id="w16"></a>

### W16：T8 双窗口流，3.33 ns

**基于：** [W13](#w13)（修复后重试）。

**调整：** 修正宽流后再测较紧时钟。

**效果与问题：** 约 1.7735 ms 的估计伴随 LUT/FF 超量，不能作为合格候选。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3.33 / 3.239 ns |
| 延迟 / 间隔 | 532569 / 532570 cycles |
| 注册表换算时间 | 1.77345477 ms（frame 范围，以 3.33 ns 换算） |
| DSP / BRAM18K / URAM | 648 / 146 / 0 |
| LUT / FF | 145767 / 192756 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 3.33 − 0.899 = 2.431 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c7d8ad219ced5b2047082c15ab2817a3e9dcef41`。

**原始证据：** [W16.json](../../exp/configs/W16.json) · [W16.md](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/W16.md) · [config.json](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/config.json) · [metrics.json](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/metrics.json) · [csynth.rpt](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/W16_fixed_tiles_T8_allcontinuous_3p33ns_split4000/csim.log.txt)。

<a id="w17"></a>

### W17：T8 原始权重窄银行

**基于：** [W14](#w14)（设计或参数基线）；[W09](#w09)（数值依据或研究启发）。

**调整：** 原始权重只供顺序变换，减少其通道分银行；保留变换后 MAC 银行。

**效果与问题：** LUT 大幅下降但仍为 93,166，超过项目预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 532562 / 532563 cycles |
| 注册表换算时间 | 2.130248 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 648 / 146 / 0 |
| LUT / FF | 93166 / 122399 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`d6f7b25ddca67aa9464617c1ee514c5bc8569bd7`。

**原始证据：** [W17.json](../../exp/configs/W17.json) · [W17.md](../../experiments/W17_narrow_raw_banks_T8/W17.md) · [config.json](../../experiments/W17_narrow_raw_banks_T8/config.json) · [metrics.json](../../experiments/W17_narrow_raw_banks_T8/metrics.json) · [csynth.rpt](../../experiments/W17_narrow_raw_banks_T8/csynth.rpt) · [csynth.log.txt](../../experiments/W17_narrow_raw_banks_T8/csynth.log.txt) · [csim.log.txt](../../experiments/W17_narrow_raw_banks_T8/csim.log.txt)。

<a id="w18"></a>

### W18：T16 原始权重窄银行

**基于：** [W15](#w15)（设计或参数基线）。

**调整：** 在 T16 下测量相同加载/银行调整。

**效果与问题：** 约 4.2274 ms、326 DSP、74,480 LUT，成为 Winograd 路线资源合格候选；RTL/实现尚未完成。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 1056850 / 1056851 cycles |
| 注册表换算时间 | 4.2274 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 326 / 146 / 0 |
| LUT / FF | 74480 / 87869 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`e6ecd9e072d21de4892870138cdf9484a81bce50`。

**原始证据：** [W18.json](../../exp/configs/W18.json) · [W18.md](../../experiments/W18_narrow_raw_banks_T16/W18.md) · [config.json](../../experiments/W18_narrow_raw_banks_T16/config.json) · [metrics.json](../../experiments/W18_narrow_raw_banks_T16/metrics.json) · [csynth.rpt](../../experiments/W18_narrow_raw_banks_T16/csynth.rpt) · [csynth.log.txt](../../experiments/W18_narrow_raw_banks_T16/csynth.log.txt) · [csim.log.txt](../../experiments/W18_narrow_raw_banks_T16/csim.log.txt)。

<a id="combination"></a>

## 组合路线：Winograd 与 Packing 能否叠加收益

局部节省乘法之后，是否还有足够 LUT、FF 和缓存支持整网？

[演进图](combination.svg)；路线依据：[exp/build_arch_c.py](../../exp/build_arch_c.py) · [exp/prepare_arch_c.py](../../exp/prepare_arch_c.py) · [exp/prepare_header_retry.py](../../exp/prepare_header_retry.py) · [exp/prepare_combination_guard.py](../../exp/prepare_combination_guard.py) · [exp/prepare_mixed_arch.py](../../exp/prepare_mixed_arch.py) · [exp/prepare_split_windows.py](../../exp/prepare_split_windows.py)。

<a id="c01"></a>

### C01：Winograd + Conv2/3 Packing，T4

**基于：** [W05](#w05)（设计或参数基线）；[P07](#p07)（集成已有模块）。

**调整：** 组合 Conv1 Winograd 和后两层精确十位 Packing。

**效果与问题：** 头文件尺寸宏冲突，编译失败；纸面 DSP 预算不是硬件结果。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`2fb8016dd9b9d08be0410ba4578400a1d63a9b46`。

**原始证据：** [C01.json](../../exp/configs/C01.json) · [C01.md](../../experiments/C01_wino_packing_T4_all/C01.md) · [config.json](../../experiments/C01_wino_packing_T4_all/config.json) · [metrics.json](../../experiments/C01_wino_packing_T4_all/metrics.json) · [csim.log.txt](../../experiments/C01_wino_packing_T4_all/csim.log.txt)。

<a id="c02"></a>

### C02：Winograd + 仅 Conv3 Packing，T4

**基于：** [C01](#c01)（设计或参数基线）。

**调整：** 保留直接 Conv2，隔离 Conv2 Packing 的代价。

**效果与问题：** 相同头文件冲突，后续 C05 重试。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`f4fe7dd06b73a823ebb040448cc3d4e4f421e0ad`。

**原始证据：** [C02.json](../../exp/configs/C02.json) · [C02.md](../../experiments/C02_wino_packing_T4_conv3/C02.md) · [config.json](../../experiments/C02_wino_packing_T4_conv3/config.json) · [metrics.json](../../experiments/C02_wino_packing_T4_conv3/metrics.json) · [csim.log.txt](../../experiments/C02_wino_packing_T4_conv3/csim.log.txt)。

<a id="c03"></a>

### C03：Winograd + Conv2/3 Packing，T8

**基于：** [C01](#c01)（设计或参数基线）。

**调整：** 降低并行度以控制资源。

**效果与问题：** 相同编译问题，后续 C06 独立修复。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`7ffec327e99090d09eda62e33f6dcb9aebfc1f8c`。

**原始证据：** [C03.json](../../exp/configs/C03.json) · [C03.md](../../experiments/C03_wino_packing_T8_all/C03.md) · [config.json](../../experiments/C03_wino_packing_T8_all/config.json) · [metrics.json](../../experiments/C03_wino_packing_T8_all/metrics.json) · [csim.log.txt](../../experiments/C03_wino_packing_T8_all/csim.log.txt)。

<a id="c04"></a>

### C04：双层 Packing 头文件修复

**基于：** [C01](#c01)（修复后重试）。

**调整：** 只修复包含顺序，保持数学、精度和参数。

**效果与问题：** LUT/FF 严重超量；DSP 936 能装下不代表整体可行。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 2378443 / 2378444 cycles |
| 注册表换算时间 | 9.513772 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 936 / 241 / 0 |
| LUT / FF | 293222 / 253809 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`8ee5a6eede0df4ef6cef4049b737a652f2f0f363`。

**原始证据：** [C04.json](../../exp/configs/C04.json) · [C04.md](../../experiments/C04_wino_packing_T4_all_header_retry/C04.md) · [config.json](../../experiments/C04_wino_packing_T4_all_header_retry/config.json) · [metrics.json](../../experiments/C04_wino_packing_T4_all_header_retry/metrics.json) · [csynth.rpt](../../experiments/C04_wino_packing_T4_all_header_retry/csynth.rpt) · [csynth.log.txt](../../experiments/C04_wino_packing_T4_all_header_retry/csynth.log.txt) · [csim.log.txt](../../experiments/C04_wino_packing_T4_all_header_retry/csim.log.txt)。

<a id="c05"></a>

### C05：仅 Conv3 Packing 头文件修复

**基于：** [C02](#c02)（修复后重试）。

**调整：** 有效运行少一个 Packing 层的控制。

**效果与问题：** 仍约 260,882 LUT，未形成资源合格组合。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 2378443 / 2378444 cycles |
| 注册表换算时间 | 9.513772 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1192 / 241 / 0 |
| LUT / FF | 260882 / 263747 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c5d03ed51f94cd65ed96224535098a4e71987dd3`。

**原始证据：** [C05.json](../../exp/configs/C05.json) · [C05.md](../../experiments/C05_wino_packing_T4_conv3_header_retry/C05.md) · [config.json](../../experiments/C05_wino_packing_T4_conv3_header_retry/config.json) · [metrics.json](../../experiments/C05_wino_packing_T4_conv3_header_retry/metrics.json) · [csynth.rpt](../../experiments/C05_wino_packing_T4_conv3_header_retry/csynth.rpt) · [csynth.log.txt](../../experiments/C05_wino_packing_T4_conv3_header_retry/csynth.log.txt) · [csim.log.txt](../../experiments/C05_wino_packing_T4_conv3_header_retry/csim.log.txt)。

<a id="c06"></a>

### C06：T8 组合头文件修复

**基于：** [C03](#c03)（修复后重试）。

**调整：** 有效测量较低并行度的组合方案。

**效果与问题：** 470 DSP，但 170,165 LUT 超项目预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 3493579 / 3493580 cycles |
| 注册表换算时间 | 13.974316 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 470 / 169 / 0 |
| LUT / FF | 170165 / 153644 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`eb17e26908d4eb725d4b7aa2700b68731d168a1e`。

**原始证据：** [C06.json](../../exp/configs/C06.json) · [C06.md](../../experiments/C06_wino_packing_T8_all_header_retry/C06.md) · [config.json](../../experiments/C06_wino_packing_T8_all_header_retry/config.json) · [metrics.json](../../experiments/C06_wino_packing_T8_all_header_retry/metrics.json) · [csynth.rpt](../../experiments/C06_wino_packing_T8_all_header_retry/csynth.rpt) · [csynth.log.txt](../../experiments/C06_wino_packing_T8_all_header_retry/csynth.log.txt) · [csim.log.txt](../../experiments/C06_wino_packing_T8_all_header_retry/csim.log.txt)。

<a id="c07"></a>

### C07：连续调度的十位组合

**基于：** [C04](#c04)（设计或参数基线）；[W10](#w10)（数值依据或研究启发）。

**调整：** 把组合架构的窗口生成与固定 MAC 循环分开。

**效果与问题：** C 仿真未通过；后续 C12 保留独立修复记录。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`356030a37bdb7c76ba159851fd885eb2a535d789`。

**原始证据：** [C07.json](../../exp/configs/C07.json) · [C07.md](../../experiments/C07_continuous_wino_packing_T8/C07.md) · [config.json](../../experiments/C07_continuous_wino_packing_T8/config.json) · [metrics.json](../../experiments/C07_continuous_wino_packing_T8/metrics.json) · [csim.log.txt](../../experiments/C07_continuous_wino_packing_T8/csim.log.txt)。

<a id="c12"></a>

### C12：连续组合的 guard 修复

**基于：** [C07](#c07)（修复后重试）。

**调整：** 修正连续组织的控制/表示，保留数学契约。

**效果与问题：** 功能精确，但 174,591 LUT 超预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 1894303 / 1894304 cycles |
| 注册表换算时间 | 7.577212 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 470 / 169 / 0 |
| LUT / FF | 174591 / 161653 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`072cc6640d060cce720492c32bff33844743dd96`。

**原始证据：** [C12.json](../../exp/configs/C12.json) · [C12.md](../../experiments/C12_continuous_wino_packing_T8_guard_retry/C12.md) · [config.json](../../experiments/C12_continuous_wino_packing_T8_guard_retry/config.json) · [metrics.json](../../experiments/C12_continuous_wino_packing_T8_guard_retry/metrics.json) · [csynth.rpt](../../experiments/C12_continuous_wino_packing_T8_guard_retry/csynth.rpt) · [csynth.log.txt](../../experiments/C12_continuous_wino_packing_T8_guard_retry/csynth.log.txt) · [csim.log.txt](../../experiments/C12_continuous_wino_packing_T8_guard_retry/csim.log.txt)。

<a id="c08"></a>

### C08：Conv2 八位权重组合，T8

**基于：** [C07](#c07)（设计或参数基线）；[E065](#e065)（数值依据或研究启发）。

**调整：** 仅 Conv2 使用已验证的八位权重，去掉该层十位系数残差修复。

**效果与问题：** 8000 位 Conv3 流超过工具限制，综合失败。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.770653995278335e-05；六像素边界 MSE=1.405191888267716e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.082567 dB；相对浮点平均 ΔPSNR=-0.07589 dB。来源：[experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json)。

工具：Vitis 2026.1；源码提交：`016cb46553ae5468239d0d08f19d7d7303c8db33`。

**原始证据：** [C08.json](../../exp/configs/C08.json) · [C08.md](../../experiments/C08_wino_conv2w8_continuous_T8/C08.md) · [config.json](../../experiments/C08_wino_conv2w8_continuous_T8/config.json) · [metrics.json](../../experiments/C08_wino_conv2w8_continuous_T8/metrics.json) · [csynth.log.txt](../../experiments/C08_wino_conv2w8_continuous_T8/csynth.log.txt) · [csim.log.txt](../../experiments/C08_wino_conv2w8_continuous_T8/csim.log.txt)。

<a id="c09"></a>

### C09：Conv2 八位权重组合，T4

**基于：** [C08](#c08)（设计或参数基线）。

**调整：** 扫描更高并行度并保留混合精度。

**效果与问题：** 相同宽流限制，后续 C11 修复。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.770653995278335e-05；六像素边界 MSE=1.405191888267716e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.082567 dB；相对浮点平均 ΔPSNR=-0.07589 dB。来源：[experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json)。

工具：Vitis 2026.1；源码提交：`65cd93d5bbff4397e1f71171a85bb7c2752d0b94`。

**原始证据：** [C09.json](../../exp/configs/C09.json) · [C09.md](../../experiments/C09_wino_conv2w8_continuous_T4/C09.md) · [config.json](../../experiments/C09_wino_conv2w8_continuous_T4/config.json) · [metrics.json](../../experiments/C09_wino_conv2w8_continuous_T4/metrics.json) · [csynth.log.txt](../../experiments/C09_wino_conv2w8_continuous_T4/csynth.log.txt) · [csim.log.txt](../../experiments/C09_wino_conv2w8_continuous_T4/csim.log.txt)。

<a id="c10"></a>

### C10：T8 混合组合双窗口流

**基于：** [C08](#c08)（修复后重试）。

**调整：** 改成两个同步 4000 位通道，保持量化和 MAC。

**效果与问题：** 约 2.1302 ms、520 DSP，但 150,851 LUT 超预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 532562 / 532563 cycles |
| 注册表换算时间 | 2.130248 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 520 / 146 / 0 |
| LUT / FF | 150851 / 179452 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.770653995278335e-05；六像素边界 MSE=1.405191888267716e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.082567 dB；相对浮点平均 ΔPSNR=-0.07589 dB。来源：[experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json)。

工具：Vitis 2026.1；源码提交：`d9747f754d5c180cfd4ee58398dd75f7eb34bf20`。

**原始证据：** [C10.json](../../exp/configs/C10.json) · [C10.md](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/C10.md) · [config.json](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/config.json) · [metrics.json](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/metrics.json) · [csynth.rpt](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/C10_wino_conv2w8_continuous_T8_split4000/csim.log.txt)。

<a id="c11"></a>

### C11：T4 混合组合双窗口流

**基于：** [C09](#c09)（修复后重试）。

**调整：** 在 T4 下修正窗口流表示。

**效果与问题：** 约 1.0817 ms 的估计需要 248,797 LUT / 307,525 FF，不能选为可部署候选。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.392 ns |
| 延迟 / 间隔 | 270418 / 270419 cycles |
| 注册表换算时间 | 1.081672 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1036 / 146 / 0 |
| LUT / FF | 248797 / 307525 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.392 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.770653995278335e-05；六像素边界 MSE=1.405191888267716e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.082567 dB；相对浮点平均 ΔPSNR=-0.07589 dB。来源：[experiments/E065_apfixed_mixed_conv2w8/metrics.json](../../experiments/E065_apfixed_mixed_conv2w8/metrics.json)。

工具：Vitis 2026.1；源码提交：`708916fea3c5594cd8b5c43ebc16720f3af0e0b4`。

**原始证据：** [C11.json](../../exp/configs/C11.json) · [C11.md](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/C11.md) · [config.json](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/config.json) · [metrics.json](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/metrics.json) · [csynth.rpt](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/C11_wino_conv2w8_continuous_T4_split4000/csim.log.txt)。

<a id="continuous"></a>

## B 的后续：连续流水、窗口控制和加载时序

保持直接卷积时，能否减少像素间流水重启、宽选择器和一次性加载关键路径？

[演进图](continuous.svg)；路线依据：[exp/prepare_arch_f.py](../../exp/prepare_arch_f.py) · [exp/build_arch_f.py](../../exp/build_arch_f.py) · [exp/prepare_split_windows.py](../../exp/prepare_split_windows.py) · [exp/prepare_rotating_arch.py](../../exp/prepare_rotating_arch.py) · [exp/prepare_ieee_network.py](../../exp/prepare_ieee_network.py) · [exp/prepare_load_arch.py](../../exp/prepare_load_arch.py)。

<a id="f01"></a>

### F01：浅宽 FIFO 改用 LUTRAM

**基于：** [E048](#e048)（设计或参数基线）；[E042](#e042)（对照实验）。

**调整：** 保留 T16 和原有逐像素调度，把浅宽特征 FIFO 显式绑定到 LUTRAM。

**效果与问题：** BRAM18K 168 降到 96，估计周期没有减少。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 2014678 / 2014679 cycles |
| 注册表换算时间 | 8.058712 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 96 / 0 |
| LUT / FF | 56081 / 62800 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`865a5949667e31cc0862cad5bd08e03bf766be79`。

**原始证据：** [F01.json](../../exp/configs/F01.json) · [F01.md](../../experiments/F01_fifo_lutram_control/F01.md) · [config.json](../../experiments/F01_fifo_lutram_control/config.json) · [metrics.json](../../experiments/F01_fifo_lutram_control/metrics.json) · [csynth.rpt](../../experiments/F01_fifo_lutram_control/csynth.rpt) · [csynth.log.txt](../../experiments/F01_fifo_lutram_control/csynth.log.txt) · [csim.log.txt](../../experiments/F01_fifo_lutram_control/csim.log.txt)。

<a id="f02"></a>

### F02：Conv3 行缓存改用 URAM

**基于：** [E048](#e048)（设计或参数基线）；[E042](#e042)（对照实验）。

**调整：** 把四行宽缓存换到 20 个 URAM。

**效果与问题：** BRAM18K 降到 132，但 URAM 深度利用率低，延迟不变。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 2014678 / 2014679 cycles |
| 注册表换算时间 | 8.058712 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 132 / 20 |
| LUT / FF | 56007 / 62948 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`de27817cf1c748966fd19c6e90c90a0d12fbe080`。

**原始证据：** [F02.json](../../exp/configs/F02.json) · [F02.md](../../experiments/F02_uram_line_control/F02.md) · [config.json](../../experiments/F02_uram_line_control/config.json) · [metrics.json](../../experiments/F02_uram_line_control/metrics.json) · [csynth.rpt](../../experiments/F02_uram_line_control/csynth.rpt) · [csynth.log.txt](../../experiments/F02_uram_line_control/csynth.log.txt) · [csim.log.txt](../../experiments/F02_uram_line_control/csim.log.txt)。

<a id="f03"></a>

### F03：连续 MAC，保留旧补边

**基于：** [E048](#e048)（设计或参数基线）；[E070](#e070)（数值依据或研究启发）；[F01](#f01)（数值依据或研究启发）。

**调整：** 窗口生成与 MAC 引擎分离，所有像素/分组组成连续 II1 循环，并注册平衡加法树。

**效果与问题：** 8000 位 Conv3 窗口流不被工具接受；旧补边控制仍可能引起有限 FIFO 停顿。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`e0da6b444ba3b62e3c529e90f87455e6f1035fa4`。

**原始证据：** [F03.json](../../exp/configs/F03.json) · [F03.md](../../experiments/F03_continuous_T16_oldpad_4ns/F03.md) · [config.json](../../experiments/F03_continuous_T16_oldpad_4ns/config.json) · [metrics.json](../../experiments/F03_continuous_T16_oldpad_4ns/metrics.json) · [csynth.log.txt](../../experiments/F03_continuous_T16_oldpad_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/F03_continuous_T16_oldpad_4ns/csim.log.txt)。

<a id="f04"></a>

### F04：连续 MAC + 边读边补边，T16

**基于：** [F03](#f03)（设计或参数基线）。

**调整：** 在后续行同步读取输入并输出复制边界，减少整行先读后写串行阶段。

**效果与问题：** 相同宽流限制，后续 F09 才有有效综合。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`57104507d29b7245aa095a88f8c48871bb40b151`。

**原始证据：** [F04.json](../../exp/configs/F04.json) · [F04.md](../../experiments/F04_continuous_T16_online_4ns/F04.md) · [config.json](../../experiments/F04_continuous_T16_online_4ns/config.json) · [metrics.json](../../experiments/F04_continuous_T16_online_4ns/metrics.json) · [csynth.log.txt](../../experiments/F04_continuous_T16_online_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/F04_continuous_T16_online_4ns/csim.log.txt)。

<a id="f05"></a>

### F05：连续 MAC + 在线补边，T8

**基于：** [F04](#f04)（设计或参数基线）。

**调整：** 提高并行度，测 T8 的时间/资源代价。

**效果与问题：** 宽流限制使本次没有有效综合结果。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`26f6a403e116b267fff9fba42963cd50bd73aa41`。

**原始证据：** [F05.json](../../exp/configs/F05.json) · [F05.md](../../experiments/F05_continuous_T8_online_4ns/F05.md) · [config.json](../../experiments/F05_continuous_T8_online_4ns/config.json) · [metrics.json](../../experiments/F05_continuous_T8_online_4ns/metrics.json) · [csynth.log.txt](../../experiments/F05_continuous_T8_online_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/F05_continuous_T8_online_4ns/csim.log.txt)。

<a id="f06"></a>

### F06：连续 T16，3.33 ns

**基于：** [F04](#f04)（设计或参数基线）。

**调整：** 保持 T16 并收紧目标周期。

**效果与问题：** 仍受宽流限制，后续 F11 修复。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`145d1d0801d2dedd3dfe9523a60934a5e584eeea`。

**原始证据：** [F06.json](../../exp/configs/F06.json) · [F06.md](../../experiments/F06_continuous_T16_online_3p33ns/F06.md) · [config.json](../../experiments/F06_continuous_T16_online_3p33ns/config.json) · [metrics.json](../../experiments/F06_continuous_T16_online_3p33ns/metrics.json) · [csynth.log.txt](../../experiments/F06_continuous_T16_online_3p33ns/csynth.log.txt) · [csim.log.txt](../../experiments/F06_continuous_T16_online_3p33ns/csim.log.txt)。

<a id="f07"></a>

### F07：连续 T8，3.33 ns

**基于：** [F05](#f05)（设计或参数基线）。

**调整：** 扫描更高并行度和更紧时钟的组合。

**效果与问题：** 宽流限制未解决，不能引用为速度证据。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`060280c82e7b6fa07ab8d565f2545c10dc2740db`。

**原始证据：** [F07.json](../../exp/configs/F07.json) · [F07.md](../../experiments/F07_continuous_T8_online_3p33ns/F07.md) · [config.json](../../experiments/F07_continuous_T8_online_3p33ns/config.json) · [metrics.json](../../experiments/F07_continuous_T8_online_3p33ns/metrics.json) · [csynth.log.txt](../../experiments/F07_continuous_T8_online_3p33ns/csynth.log.txt) · [csim.log.txt](../../experiments/F07_continuous_T8_online_3p33ns/csim.log.txt)。

<a id="f08"></a>

### F08：合法双窗口流，旧补边

**基于：** [F03](#f03)（修复后重试）。

**调整：** 完整窗口改用两个 4000 位 FIFO，保持连续计算与旧补边。

**效果与问题：** 估计 4.1947 ms；Conv3 动态通道选择器和有限 FIFO 成本成为下一步问题。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 1048677 / 1048678 cycles |
| 注册表换算时间 | 4.194708 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 96 / 0 |
| LUT / FF | 69362 / 106171 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c1ed3c5aab6433b4cc89a3f5ba3a0887edec5b82`。

**原始证据：** [F08.json](../../exp/configs/F08.json) · [F08.md](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/F08.md) · [config.json](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/config.json) · [metrics.json](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/metrics.json) · [csynth.rpt](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/F08_continuous_T16_oldpad_4ns_split4000/csim.log.txt)。

<a id="f09"></a>

### F09：合法双窗口流，在线补边 T16

**基于：** [F04](#f04)（修复后重试）；[F08](#f08)（对照实验）。

**调整：** 保留同步双通道并测在线补边的 T16 版本。

**效果与问题：** BRAM18K 降到 73；HLS 周期几乎不变，补边吞吐必须用 RTL 检查。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 1048687 / 1048688 cycles |
| 注册表换算时间 | 4.194748 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 73 / 0 |
| LUT / FF | 69179 / 106647 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`088f4fe4d5a3de629b3cada74e54464d0ff1fd7f`。

**原始证据：** [F09.json](../../exp/configs/F09.json) · [F09.md](../../experiments/F09_continuous_T16_online_4ns_split4000/F09.md) · [config.json](../../experiments/F09_continuous_T16_online_4ns_split4000/config.json) · [metrics.json](../../experiments/F09_continuous_T16_online_4ns_split4000/metrics.json) · [csynth.rpt](../../experiments/F09_continuous_T16_online_4ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/F09_continuous_T16_online_4ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/F09_continuous_T16_online_4ns_split4000/csim.log.txt)。

<a id="f10"></a>

### F10：合法双窗口流，在线补边 T8

**基于：** [F05](#f05)（修复后重试）。

**调整：** 修正宽流后测较高并行度。

**效果与问题：** 估计更快，但 LUT/FF 超预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 528488 / 528489 cycles |
| 注册表换算时间 | 2.113952 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 96764 / 171240 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`71dda9c0c101064aee7d206a709a3153cd0e0fc3`。

**原始证据：** [F10.json](../../exp/configs/F10.json) · [F10.md](../../experiments/F10_continuous_T8_online_4ns_split4000/F10.md) · [config.json](../../experiments/F10_continuous_T8_online_4ns_split4000/config.json) · [metrics.json](../../experiments/F10_continuous_T8_online_4ns_split4000/metrics.json) · [csynth.rpt](../../experiments/F10_continuous_T8_online_4ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/F10_continuous_T8_online_4ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/F10_continuous_T8_online_4ns_split4000/csim.log.txt)。

<a id="f11"></a>

### F11：合法 T16，3.33 ns

**基于：** [F06](#f06)（修复后重试）；[F09](#f09)（对照实验）。

**调整：** 修正流表示后测紧时钟 T16 配置。

**效果与问题：** 估计约 3.4922 ms；目标频率仍不是已实现频率。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3.33 / 3.239 ns |
| 延迟 / 间隔 | 1048700 / 1048701 cycles |
| 注册表换算时间 | 3.492171 ms（frame 范围，以 3.33 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 73 / 0 |
| LUT / FF | 69427 / 121372 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 3.33 − 0.899 = 2.431 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`37f7f6657d33d1ac38c51f1c7e20db3628835c3f`。

**原始证据：** [F11.json](../../exp/configs/F11.json) · [F11.md](../../experiments/F11_continuous_T16_online_3p33ns_split4000/F11.md) · [config.json](../../experiments/F11_continuous_T16_online_3p33ns_split4000/config.json) · [metrics.json](../../experiments/F11_continuous_T16_online_3p33ns_split4000/metrics.json) · [csynth.rpt](../../experiments/F11_continuous_T16_online_3p33ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/F11_continuous_T16_online_3p33ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/F11_continuous_T16_online_3p33ns_split4000/csim.log.txt)。

<a id="f12"></a>

### F12：合法 T8，3.33 ns

**基于：** [F07](#f07)（修复后重试）。

**调整：** 修正流表示后测紧时钟 T8 配置。

**效果与问题：** 约 1.7599 ms 的估计伴随 LUT/FF 超量。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3.33 / 3.239 ns |
| 延迟 / 间隔 | 528501 / 528502 cycles |
| 注册表换算时间 | 1.75990833 ms（frame 范围，以 3.33 ns 换算） |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 97112 / 196314 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 3.33 − 0.899 = 2.431 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`90c31a33cad1bf67abc99be3658d9879cf2ceb1e`。

**原始证据：** [F12.json](../../exp/configs/F12.json) · [F12.md](../../experiments/F12_continuous_T8_online_3p33ns_split4000/F12.md) · [config.json](../../experiments/F12_continuous_T8_online_3p33ns_split4000/config.json) · [metrics.json](../../experiments/F12_continuous_T8_online_3p33ns_split4000/metrics.json) · [csynth.rpt](../../experiments/F12_continuous_T8_online_3p33ns_split4000/csynth.rpt) · [csynth.log.txt](../../experiments/F12_continuous_T8_online_3p33ns_split4000/csynth.log.txt) · [csim.log.txt](../../experiments/F12_continuous_T8_online_3p33ns_split4000/csim.log.txt)。

<a id="f13"></a>

### F13：Conv3 窗口通道轮换，T16

**基于：** [F09](#f09)（设计或参数基线）；[F08](#f08)（数值依据或研究启发）。

**调整：** 每轮把已用通道移走，让乘法器读取固定位置；保留注册加法树。

**效果与问题：** 减少动态选择器，估计周期基本不变；浮点输出转换仍限制全局时钟估计。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 1048687 / 1048688 cycles |
| 注册表换算时间 | 4.194748 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 505 / 73 / 0 |
| LUT / FF | 68903 / 106661 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`996788fa2117f80a869a3ed798f8d1208194086d`。

**原始证据：** [F13.json](../../exp/configs/F13.json) · [F13.md](../../experiments/F13_rotate_c3_T16_tree1_4ns/F13.md) · [config.json](../../experiments/F13_rotate_c3_T16_tree1_4ns/config.json) · [metrics.json](../../experiments/F13_rotate_c3_T16_tree1_4ns/metrics.json) · [csynth.rpt](../../experiments/F13_rotate_c3_T16_tree1_4ns/csynth.rpt) · [csynth.log.txt](../../experiments/F13_rotate_c3_T16_tree1_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/F13_rotate_c3_T16_tree1_4ns/csim.log.txt)。

<a id="f14"></a>

### F14：窗口轮换，T8，注册加法树

**基于：** [F13](#f13)（设计或参数基线）。

**调整：** 改变 T，观察固定读位置在高并行度下的资源取舍。

**效果与问题：** LUT/FF 超预算。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT/FF；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 528488 / 528489 cycles |
| 注册表换算时间 | 2.113952 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 96488 / 171235 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`17b9dabda308f7a83b7d4e870f4ff028c75f6eaa`。

**原始证据：** [F14.json](../../exp/configs/F14.json) · [F14.md](../../experiments/F14_rotate_c3_T8_tree1_4ns/F14.md) · [config.json](../../experiments/F14_rotate_c3_T8_tree1_4ns/config.json) · [metrics.json](../../experiments/F14_rotate_c3_T8_tree1_4ns/metrics.json) · [csynth.rpt](../../experiments/F14_rotate_c3_T8_tree1_4ns/csynth.rpt) · [csynth.log.txt](../../experiments/F14_rotate_c3_T8_tree1_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/F14_rotate_c3_T8_tree1_4ns/csim.log.txt)。

<a id="f15"></a>

### F15：窗口轮换，T8，无树级寄存

**基于：** [F14](#f14)（设计或参数基线）。

**调整：** 把加法树延迟绑定为零，隔离寄存级对 FF/时序的影响。

**效果与问题：** FF 减少，但 LUT 超预算；减少寄存器不能自动保证时序。

**记录状态：** `infeasible` / 资源/性能门槛未满足；范围 `frame`；步骤 `csim_csynth`。
附加检查：超预算: LUT；HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 4 / 3.239 ns |
| 延迟 / 间隔 | 528481 / 528482 cycles |
| 注册表换算时间 | 2.113924 ms（frame 范围，以 4 ns 换算） |
| DSP / BRAM18K / URAM | 1007 / 73 / 0 |
| LUT / FF | 101994 / 86073 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 4 − 1.08 = 2.92 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`3dbe07a95f51308c6af8ec0c3919f0b683657749`。

**原始证据：** [F15.json](../../exp/configs/F15.json) · [F15.md](../../experiments/F15_rotate_c3_T8_tree0_4ns/F15.md) · [config.json](../../experiments/F15_rotate_c3_T8_tree0_4ns/config.json) · [metrics.json](../../experiments/F15_rotate_c3_T8_tree0_4ns/metrics.json) · [csynth.rpt](../../experiments/F15_rotate_c3_T8_tree0_4ns/csynth.rpt) · [csynth.log.txt](../../experiments/F15_rotate_c3_T8_tree0_4ns/csynth.log.txt) · [csim.log.txt](../../experiments/F15_rotate_c3_T8_tree0_4ns/csim.log.txt)。

<a id="f16"></a>

### F16：精确构造 float 输出的小内核

**基于：** [F08](#f08)（数值依据或研究启发）。

**调整：** 十位原始输出都能被 float 精确表示，尝试直接构造符号/指数/尾数。

**效果与问题：** SDK 名称空间与 ap_int 条件表达式类型不匹配，编译失败。

**记录状态：** `fail` / 运行失败；范围 `PE`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`4f32b356dbf645918f7fc027d284cf67298b3a4a`。

**原始证据：** [F16.json](../../exp/configs/F16.json) · [F16.md](../../experiments/F16_ieee_decode_bit_exact/F16.md) · [config.json](../../experiments/F16_ieee_decode_bit_exact/config.json) · [metrics.json](../../experiments/F16_ieee_decode_bit_exact/metrics.json) · [csim.log.txt](../../experiments/F16_ieee_decode_bit_exact/csim.log.txt)。

<a id="f17"></a>

### F17：普通 float 转换的小内核控制

**基于：** [F16](#f16)（对照实验）。

**调整：** 用同一输入集合测原有转换/除法。

**效果与问题：** 同一探针工程存在编译问题，需独立重试。

**记录状态：** `fail` / 运行失败；范围 `PE`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`a5d31057b4d36fec23d2b44c5e7e8a8a5b37bb4b`。

**原始证据：** [F17.json](../../exp/configs/F17.json) · [F17.md](../../experiments/F17_ieee_decode_legacy_control/F17.md) · [config.json](../../experiments/F17_ieee_decode_legacy_control/config.json) · [metrics.json](../../experiments/F17_ieee_decode_legacy_control/metrics.json) · [csim.log.txt](../../experiments/F17_ieee_decode_legacy_control/csim.log.txt)。

<a id="f18"></a>

### F18：精确 float 构造 SDK 修复

**基于：** [F16](#f16)（修复后重试）。

**调整：** 按安装版本修正 fp_struct 符号及显式符号分支。

**效果与问题：** 同名设计/测试翻译单元产生重复目标文件，链接失败。

**记录状态：** `fail` / 运行失败；范围 `PE`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`5b1e51fd0433bb6a2a011b4960a05f8600baf7ff`。

**原始证据：** [F18.json](../../exp/configs/F18.json) · [F18.md](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/F18.md) · [config.json](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/config.json) · [metrics.json](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/metrics.json) · [csim.log.txt](../../experiments/F18_ieee_decode_bit_exact_sdk_retry/csim.log.txt)。

<a id="f19"></a>

### F19：普通转换 SDK 修复控制

**基于：** [F17](#f17)（修复后重试）。

**调整：** 保持普通转换，在同一修正工程中测量。

**效果与问题：** 目标文件重名问题仍在，后续 F21 修复。

**记录状态：** `fail` / 运行失败；范围 `PE`；步骤 `csim`。

工具：Vitis 2026.1；源码提交：`3d8f8ffafd4d6ec4329a56554aeab6749475aa5e`。

**原始证据：** [F19.json](../../exp/configs/F19.json) · [F19.md](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/F19.md) · [config.json](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/config.json) · [metrics.json](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/metrics.json) · [csim.log.txt](../../experiments/F19_ieee_decode_legacy_control_sdk_retry/csim.log.txt)。

<a id="f20"></a>

### F20：精确 float 构造有效探针

**基于：** [F18](#f18)（修复后重试）。

**调整：** 仅把设计翻译单元改名为 kernel.cpp，穷举 1024 个输出编码。

**效果与问题：** 0 DSP、242 LUT；这只是输出编码模块，整网关键路径可能转移。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3.33 / 2.051 ns |
| 延迟 / 间隔 | 1027 / 1024 cycles |
| 注册表换算时间 | 0.00341991 ms（PE 范围，以 3.33 ns 换算） |
| DSP / BRAM18K / URAM | 0 / 0 / 0 |
| LUT / FF | 242 / 52 |
| 所检查的 II 目标 | 达到 |

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`8aaeb2c5e62cc56295c0a2c5c0fcc71dffddda65`。

**原始证据：** [F20.json](../../exp/configs/F20.json) · [F20.md](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/F20.md) · [config.json](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/config.json) · [metrics.json](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/metrics.json) · [csynth.rpt](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/csynth.rpt) · [csynth.log.txt](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/csynth.log.txt) · [csim.log.txt](../../experiments/F20_ieee_decode_bit_exact_sdk_retry_unique_object/csim.log.txt)。

<a id="f21"></a>

### F21：普通转换有效控制

**基于：** [F19](#f19)（修复后重试）；[F20](#f20)（对照实验）。

**调整：** 相同接口/样本下测普通 float 转换。

**效果与问题：** 使用 3 DSP，估计路径 3.239 ns；为 F20 提供有效对照。

**记录状态：** `pass` / 局部实验通过；范围 `PE`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3.33 / 3.239 ns |
| 延迟 / 间隔 | 1039 / 1024 cycles |
| 注册表换算时间 | 0.00345987 ms（PE 范围，以 3.33 ns 换算） |
| DSP / BRAM18K / URAM | 3 / 0 / 0 |
| LUT / FF | 220 / 343 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 3.33 − 0.899 = 2.431 ns；告警路径最高估计 3.239 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

工具：Vitis 2026.1；源码提交：`ef39b7f46dd04f73cf3e5633ec9acd94bc4f77ae`。

**原始证据：** [F21.json](../../exp/configs/F21.json) · [F21.md](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/F21.md) · [config.json](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/config.json) · [metrics.json](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/metrics.json) · [csynth.rpt](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/csynth.rpt) · [csynth.log.txt](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/csynth.log.txt) · [csim.log.txt](../../experiments/F21_ieee_decode_legacy_control_sdk_retry_unique_object/csim.log.txt)。

<a id="f22"></a>

### F22：集成精确输出编码，3 ns

**基于：** [F13](#f13)（设计或参数基线）；[F20](#f20)（集成已有模块）。

**调整：** 只替换定点到 float 的输出编码，保留十位数值与连续推理引擎。

**效果与问题：** DSP 505 降到 502；移除转换瓶颈后，加载地址和推理控制仍可能限制时钟。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 3 / 2.377 ns |
| 延迟 / 间隔 | 1048711 / 1048712 cycles |
| 注册表换算时间 | 3.146133 ms（frame 范围，以 3 ns 换算） |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 69483 / 121696 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 3 − 0.81 = 2.19 ns；告警路径最高估计 2.377 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`c6e962c679f9bbe81e0c0656b1f308913796b06d`。

**原始证据：** [F22.json](../../exp/configs/F22.json) · [F22.md](../../experiments/F22_continuous_ieee_T16_3ns/F22.md) · [config.json](../../experiments/F22_continuous_ieee_T16_3ns/config.json) · [metrics.json](../../experiments/F22_continuous_ieee_T16_3ns/metrics.json) · [csynth.rpt](../../experiments/F22_continuous_ieee_T16_3ns/csynth.rpt) · [csynth.log.txt](../../experiments/F22_continuous_ieee_T16_3ns/csynth.log.txt) · [csim.log.txt](../../experiments/F22_continuous_ieee_T16_3ns/csim.log.txt)。

<a id="f23"></a>

### F23：集成精确输出编码，2.5 ns

**基于：** [F13](#f13)（设计或参数基线）；[F20](#f20)（集成已有模块）；[F22](#f22)（对照实验）。

**调整：** 进一步收紧目标周期，定位全局关键路径。

**效果与问题：** Conv1 一次性权重加载的地址乘法使全局估计为 2.822 ns。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 2.5 / 2.822 ns |
| 延迟 / 间隔 | 1048730 / 1048731 cycles |
| 注册表换算时间 | 2.95951606 ms（frame 范围，以 2.822 ns 换算） |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 70449 / 125618 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 2.5 − 0.675 = 1.825 ns；告警路径最高估计 2.822 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`42ffdd70e9363069b79ac6eac25b3c6ec1fe0850`。

**原始证据：** [F23.json](../../exp/configs/F23.json) · [F23.md](../../experiments/F23_continuous_ieee_T16_2p5ns/F23.md) · [config.json](../../experiments/F23_continuous_ieee_T16_2p5ns/config.json) · [metrics.json](../../experiments/F23_continuous_ieee_T16_2p5ns/metrics.json) · [csynth.rpt](../../experiments/F23_continuous_ieee_T16_2p5ns/csynth.rpt) · [csynth.log.txt](../../experiments/F23_continuous_ieee_T16_2p5ns/csynth.log.txt) · [csim.log.txt](../../experiments/F23_continuous_ieee_T16_2p5ns/csim.log.txt)。

<a id="f24"></a>

### F24：显式三维权重加载索引

**基于：** [F23](#f23)（设计或参数基线）。

**调整：** 用输出通道/核行/核列计数器替代除法和取余推导的地址。

**效果与问题：** 加载地址乘法消失，但自动合并的计数控制仍有 2.699 ns 估计路径。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 2.5 / 2.699 ns |
| 延迟 / 间隔 | 1048723 / 1048724 cycles |
| 注册表换算时间 | 2.83050338 ms（frame 范围，以 2.699 ns 换算） |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 69290 / 124577 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 2.5 − 0.675 = 1.825 ns；告警路径最高估计 2.699 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`192c24087f0d50710dc5461fa984e3149e864dd4`。

**原始证据：** [F24.json](../../exp/configs/F24.json) · [F24.md](../../experiments/F24_affine_weight_loader_T16_2p5ns/F24.md) · [config.json](../../experiments/F24_affine_weight_loader_T16_2p5ns/config.json) · [metrics.json](../../experiments/F24_affine_weight_loader_T16_2p5ns/metrics.json) · [csynth.rpt](../../experiments/F24_affine_weight_loader_T16_2p5ns/csynth.rpt) · [csynth.log.txt](../../experiments/F24_affine_weight_loader_T16_2p5ns/csynth.log.txt) · [csim.log.txt](../../experiments/F24_affine_weight_loader_T16_2p5ns/csim.log.txt)。

<a id="f25"></a>

### F25：关闭权重加载循环合并

**基于：** [F24](#f24)（设计或参数基线）。

**调整：** 只在 Conv1 权重加载内层加入 LOOP_FLATTEN off，推理引擎保持相同。

**效果与问题：** 估计 2.64226 ms、73 BRAM18K；加载周期稍增。2.5 ns 下仍有 uncertainty 后的 HLS 时序告警。

**记录状态：** `provisional` / 候选，仍需验收；范围 `frame`；步骤 `csim_csynth`。
附加检查：HLS 时序警告。

| HLS 测量/估计 | 值 |
| --- | --- |
| 目标周期 / 估计周期 | 2.5 / 2.377 ns |
| 延迟 / 间隔 | 1056904 / 1056905 cycles |
| 注册表换算时间 | 2.64226 ms（frame 范围，以 2.5 ns 换算） |
| DSP / BRAM18K / URAM | 502 / 73 / 0 |
| LUT / FF | 69976 / 125404 |
| 所检查的 II 目标 | 达到 |

HLS 200-871：逻辑预算 2.5 − 0.675 = 1.825 ns；告警路径最高估计 2.377 ns。详见原始综合日志。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`ab5c5e94beb6f6f1374e9bb547b27bf6fe1e055a`。

**原始证据：** [F25.json](../../exp/configs/F25.json) · [F25.md](../../experiments/F25_nested_weight_loader_T16_2p5ns/F25.md) · [config.json](../../experiments/F25_nested_weight_loader_T16_2p5ns/config.json) · [metrics.json](../../experiments/F25_nested_weight_loader_T16_2p5ns/metrics.json) · [csynth.rpt](../../experiments/F25_nested_weight_loader_T16_2p5ns/csynth.rpt) · [csynth.log.txt](../../experiments/F25_nested_weight_loader_T16_2p5ns/csynth.log.txt) · [csim.log.txt](../../experiments/F25_nested_weight_loader_T16_2p5ns/csim.log.txt)。

<a id="verification"></a>

## 候选验证：同一设计的不同验收步骤

功能、RTL 周期、布局布线时序和板端运行分别验证到了哪里？

[演进图](verification.svg)；路线依据：[exp/prepare_final_arch.py](../../exp/prepare_final_arch.py) · [exp/prepare_impl_retries.py](../../exp/prepare_impl_retries.py) · [experiments/final_selection.json](../../experiments/final_selection.json) · [experiments/F82_final_cosim_F25/reports/sim/srcnn_cosim.rpt](../../experiments/F82_final_cosim_F25/reports/sim/srcnn_cosim.rpt)。

<a id="e069"></a>

### E069：第一轮 E043 的多图验收

**基于：** [E043](#e043)（验证同一设计）；[E017](#e017)（数值依据或研究启发）。

**调整：** 在所有 13 张已有图像上逐位比较最佳第一轮候选。

**效果与问题：** 多图通过仍缺 comic；不是板端验收。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：[experiments/E017_apfixed_boundary_w10a10/metrics.json](../../experiments/E017_apfixed_boundary_w10a10/metrics.json)。

工具：Vitis 2026.1；源码提交：`ce0fa16f724dfd50c87fe09cb64e3320bf77fce7`。

**原始证据：** [E069.json](../../exp/configs/E069.json) · [E069.md](../../experiments/E069_final_candidate_all_supplied/E069.md) · [config.json](../../experiments/E069_final_candidate_all_supplied/config.json) · [metrics.json](../../experiments/E069_final_candidate_all_supplied/metrics.json) · [csim.log.txt](../../experiments/E069_final_candidate_all_supplied/csim.log.txt)。

<a id="e070"></a>

### E070：第一项可行 E039 的实际实现

**基于：** [E039](#e039)（验证同一设计）。

**调整：** 运行 Vivado 综合、布局和布线，记录真实利用率及时序。

**效果与问题：** 实现完成，但 10 ns 目标下 WNS=-1.277 ns，时序没有达标。

**记录状态：** `impl_complete` / 实现完成，另看时序；范围 `frame`；步骤 `impl`。
附加检查：实现时序未达标。

继承的 HLS 估计来自 [E039](#e039)，不作为本步骤的新测量。

实现：WNS=-1.277 ns；TNS=-1206.071 ns；timing_met=false。实际 DSP / BRAM36 / URAM / LUT / FF = 270 / 31 / 0 / 20454 / 33844。BRAM36 与 HLS 的 BRAM18K 单位不同。

工具：Vitis 2026.1；源码提交：`2e47aa68288ac1c912a8563d4452474b785a9a7d`。

**原始证据：** [E070.json](../../exp/configs/E070.json) · [E070.md](../../experiments/E070_first_feasible_implementation/E070.md) · [config.json](../../experiments/E070_first_feasible_implementation/config.json) · [metrics.json](../../experiments/E070_first_feasible_implementation/metrics.json) · [verification.json](../../experiments/E070_first_feasible_implementation/verification.json) · [impl.log.txt](../../experiments/E070_first_feasible_implementation/impl.log.txt) · [srcnn_timing_routed.rpt](../../experiments/E070_first_feasible_implementation/reports/impl/srcnn_timing_routed.rpt) · [srcnn_utilization_routed.rpt](../../experiments/E070_first_feasible_implementation/reports/impl/srcnn_utilization_routed.rpt)。

<a id="f80"></a>

### F80：F25 的 13 图 C 仿真

**基于：** [F25](#f25)（验证同一设计）；[E017](#e017)（数值依据或研究启发）。

**调整：** 验证所有已有 Set14 图像与两帧 butterfly；每个输出位对照独立定点参考。

**效果与问题：** 平均质量门槛通过；缺 comic，14 图验收未完成。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：本次仿真（13 张；见原始记录）。

工具：Vitis 2026.1；源码提交：`f503f1ea505bebf5e425862603c52e70d4bf260e`。

**原始证据：** [F80.json](../../exp/configs/F80.json) · [F80.md](../../experiments/F80_final_all_supplied_F25/F80.md) · [config.json](../../experiments/F80_final_all_supplied_F25/config.json) · [metrics.json](../../experiments/F80_final_all_supplied_F25/metrics.json) · [csim.log.txt](../../experiments/F80_final_all_supplied_F25/csim.log.txt)。

<a id="f81"></a>

### F81：F25 的 Vivado 实现

**基于：** [F25](#f25)（验证同一设计）；[F80](#f80)（数值依据或研究启发）。

**调整：** 在独立工作区做实际物理实现。

**效果与问题：** 内核日志确认主机 OOM 杀死综合；没有 routed 时序/资源结果。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `impl`。
附加检查：主机 OOM。

继承的 HLS 估计来自 [F25](#f25)，不作为本步骤的新测量。

工具：Vitis 2026.1；源码提交：`511c75f3652dd9a522e3592d1285203bc0b8eb07`。

**原始证据：** [F81.json](../../exp/configs/F81.json) · [F81.md](../../experiments/F81_final_impl_F25/F81.md) · [config.json](../../experiments/F81_final_impl_F25/config.json) · [metrics.json](../../experiments/F81_final_impl_F25/metrics.json) · [verification.json](../../experiments/F81_final_impl_F25/verification.json) · [impl.log.txt](../../experiments/F81_final_impl_F25/impl.log.txt) · [kernel_oom.txt](../../experiments/F81_final_impl_F25/diagnostics/kernel_oom.txt)。

<a id="f82"></a>

### F82：F25 的双帧 C/RTL 协仿

**基于：** [F25](#f25)（验证同一设计）；[F80](#f80)（数值依据或研究启发）。

**调整：** 同一 F25 RTL 跑两帧，启用有限 FIFO profiling 和死锁检查。

**效果与问题：** Pass；最大延迟 1,068,183 周期，较综合周期多约 1.07%，墙钟耗时约 103 分钟。功能仿真不证明物理时序。

**记录状态：** `cosim_complete` / RTL 协仿完成；范围 `frame`；步骤 `cosim`。

继承的 HLS 估计来自 [F25](#f25)，不作为本步骤的新测量。

RTL：Pass；最大延迟 1068183 cycles；最大间隔 1068212 cycles；相对 HLS 周期增加 1.0672%。

工具：Vitis 2026.1；源码提交：`c46ae06ec1080ca1af3fe48c4131e089d2ec95f9`。

**原始证据：** [F82.json](../../exp/configs/F82.json) · [F82.md](../../experiments/F82_final_cosim_F25/F82.md) · [config.json](../../experiments/F82_final_cosim_F25/config.json) · [metrics.json](../../experiments/F82_final_cosim_F25/metrics.json) · [verification.json](../../experiments/F82_final_cosim_F25/verification.json) · [cosim.log.txt](../../experiments/F82_final_cosim_F25/cosim.log.txt) · [srcnn_cosim.rpt](../../experiments/F82_final_cosim_F25/reports/sim/srcnn_cosim.rpt)。

<a id="f83"></a>

### F83：F24 的 13 图 C 仿真

**基于：** [F24](#f24)（验证同一设计）；[E017](#e017)（数值依据或研究启发）。

**调整：** 验证第二候选的完整已有图像集。

**效果与问题：** 逐位与参考一致；精度结果和 F25 相同，硬件验证独立。

**记录状态：** `csim_pass` / C 仿真通过；范围 `frame`；步骤 `csim`。

功能：C 仿真通过；bit_exact=true；butterfly MSE=1.8197758558556394e-05；六像素边界 MSE=1.661846957728205e-05。bit_exact 与 MSE 的比较对象见原始测试，不能把定点参考一致解释为浮点 golden 一致。

质量：对 GT 的平均 PSNR=29.088943 dB；相对浮点平均 ΔPSNR=-0.069514 dB。来源：本次仿真（13 张；见原始记录）。

工具：Vitis 2026.1；源码提交：`be7c2bc15393168a25df52ce90a7765015cb39f0`。

**原始证据：** [F83.json](../../exp/configs/F83.json) · [F83.md](../../experiments/F83_final_all_supplied_F24/F83.md) · [config.json](../../experiments/F83_final_all_supplied_F24/config.json) · [metrics.json](../../experiments/F83_final_all_supplied_F24/metrics.json) · [csim.log.txt](../../experiments/F83_final_all_supplied_F24/csim.log.txt)。

<a id="f84"></a>

### F84：F24 的 Vivado 实现

**基于：** [F24](#f24)（验证同一设计）；[F83](#f83)（数值依据或研究启发）。

**调整：** 独立测量第二候选的物理结果。

**效果与问题：** 主机 OOM 中断；没有 routed 结果，不能判为时序通过。

**记录状态：** `fail` / 运行失败；范围 `frame`；步骤 `impl`。
附加检查：主机 OOM。

继承的 HLS 估计来自 [F24](#f24)，不作为本步骤的新测量。

工具：Vitis 2026.1；源码提交：`cb2bcc80a424bb07cf6fe41abcf8c160f61ac3ad`。

**原始证据：** [F84.json](../../exp/configs/F84.json) · [F84.md](../../experiments/F84_final_impl_F24/F84.md) · [config.json](../../experiments/F84_final_impl_F24/config.json) · [metrics.json](../../experiments/F84_final_impl_F24/metrics.json) · [verification.json](../../experiments/F84_final_impl_F24/verification.json) · [impl.log.txt](../../experiments/F84_final_impl_F24/impl.log.txt) · [kernel_oom.txt](../../experiments/F84_final_impl_F24/diagnostics/kernel_oom.txt)。

<a id="f85"></a>

### F85：F24 的双帧 RTL 计划

**基于：** [F24](#f24)（验证同一设计）；[F83](#f83)（数值依据或研究启发）。

**调整：** 计划验证有限 FIFO、状态复位与 RTL 周期。

**效果与问题：** 此快照只有计划，尚未归档完成结果。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

继承的 HLS 估计来自 [F24](#f24)，不作为本步骤的新测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F85.json](../../exp/configs/F85.json)。

<a id="f86"></a>

### F86：F23 的多图 C 仿真计划

**基于：** [F23](#f23)（验证同一设计）；[E017](#e017)（数值依据或研究启发）。

**调整：** 计划对第三候选执行全部已有图像验收。

**效果与问题：** 此快照没有运行结果。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F86.json](../../exp/configs/F86.json)。

<a id="f87"></a>

### F87：F23 的 Vivado 实现计划

**基于：** [F23](#f23)（验证同一设计）；[F86](#f86)（数值依据或研究启发）。

**调整：** 计划测量第三候选的 routed 资源和时序。

**效果与问题：** 此快照没有完成报告。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

继承的 HLS 估计来自 [F23](#f23)，不作为本步骤的新测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F87.json](../../exp/configs/F87.json)。

<a id="f88"></a>

### F88：F23 的双帧 RTL 计划

**基于：** [F23](#f23)（验证同一设计）；[F86](#f86)（数值依据或研究启发）。

**调整：** 计划执行第三候选的有限 FIFO RTL 验证。

**效果与问题：** 此快照没有完成结果。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

继承的 HLS 估计来自 [F23](#f23)，不作为本步骤的新测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F88.json](../../exp/configs/F88.json)。

<a id="f89"></a>

### F89：F25 的单线程实现重试计划

**基于：** [F81](#f81)（修复后重试）；[F25](#f25)（验证同一设计）。

**调整：** 保留生成的 IP/BD 流程，仅用本次 Tcl hook 限制 Vivado 内部线程。

**效果与问题：** 针对主机内存问题；不能用预计值替代实际 routed 结果。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

继承的 HLS 估计来自 [F25](#f25)，不作为本步骤的新测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F89.json](../../exp/configs/F89.json)。

<a id="f90"></a>

### F90：F24 的单线程实现重试计划

**基于：** [F84](#f84)（修复后重试）；[F24](#f24)（验证同一设计）。

**调整：** 相同流程控制用于第二候选。

**效果与问题：** 此快照没有实际结果；不改变时序/精度门槛。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

继承的 HLS 估计来自 [F24](#f24)，不作为本步骤的新测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F90.json](../../exp/configs/F90.json)。

<a id="f91"></a>

### F91：F23 的单线程实现计划

**基于：** [F87](#f87)（修复后重试）；[F23](#f23)（验证同一设计）。

**调整：** 计划用相同线程限制流程验证第三候选。

**效果与问题：** F87 也是计划记录；这条是验证流程关系，不声称 F87 已经 OOM。

**记录状态：** `planned` / 已准备，未归档测量；范围 `frame`；步骤 `plan`。
附加检查：未归档测量。

继承的 HLS 估计来自 [F23](#f23)，不作为本步骤的新测量。

计划中的 estimates 仅为假设，保留在配置和 data.json；此处不展示为实际资源、II 或延迟。

工具：未记录 Vitis 版本/不适用；源码提交：尚未归档运行源码提交。

**原始证据：** [F91.json](../../exp/configs/F91.json)。
