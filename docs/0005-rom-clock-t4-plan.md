# W21 之后：常量权重、时钟与 T4

本文是接手 agent 的第二份工作文档，接在 [0004](0004-t8-weight-loading-plan.md) 之后，2026-10-12 根据已归档证据整理。标注“假设”或“估计”的内容还没有实验证据。

开工前按顺序读：两份 `AGENTS.md`、[0003](0003-architecture-exploration.md)、[0004](0004-t8-weight-loading-plan.md)（其中第 3、7 节的流程仍然有效）、[WEIGHT_LOADING](../experiments/WEIGHT_LOADING.md)、[route_calibration.csv](../experiments/route_calibration.csv)。

## 1. 现状

### 1.1 已经布线且时序收敛的设计

| 设计 | 源码 | T | 布线时钟 | RTL 周期 | IP 级帧时间 | 布线后资源 |
| --- | --- | --- | --- | --- | --- | --- |
| W21（[W22](../experiments/W22_ws_clock_4p95_W21/W22.md)） | `designs/winograd_subkernel_cache_v1` | 8 | 4.95 ns，WNS +0.047 | 558,758（F97） | 2.766 ms | LUT 42,592 / FF 88,806 / DSP 644 / BRAM18K 109 |
| W21（[F98](../experiments/F98_ws_impl_W21/F98.md)） | 同上 | 8 | 5.0 ns，WNS +0.140 | 558,758 | 2.794 ms | 同上 |
| F28（[F95](../experiments/F95_ws_impl_F28/F95.md)） | `designs/continuous_param_noflat_v1` | 16 | 5.0 ns，WNS +0.282 | 1,059,506（F93） | 5.298 ms | LUT 30,140 / DSP 591 |
| F25（[F92](../experiments/F92_ws_impl_F25/F92.md)） | `designs/continuous_nested_load_v1` | 16 | 5.0 ns，WNS +0.568 | 1,068,183（F82） | 5.341 ms | LUT 32,400 / DSP 592 |

- W21 在 13 张图上逐位一致（F96）。两帧 RTL 仿真中，第二帧换了输入、权重和 bias，结果仍然逐位正确（F97）。
- 以上都是 out-of-context IP 结果：理想 AXI，不含 DDR、驱动和板上时钟。还没有上板。

### 1.2 从布线结果得到的结论

**HLS 时钟估计乐观约 2 倍。**
- W21 的 HLS 估计是 2.431 ns，实际 4.95 ns 勉强收敛。
- F25 的 HLS 估计是 2.377 ns；按 2.5 ns 布线跑 3 小时超时（F89），按 5 ns 收敛。
- 以后不再对着 HLS 时钟估计调参。

**HLS 资源估计和布线结果差别很大，五个点结论一致：**

| 设计 | 布线/HLS LUT | 布线/HLS FF | 布线/HLS BRAM18K | 布线/HLS DSP |
| --- | --- | --- | --- | --- |
| E070 | 0.459 | 0.734 | 0.369 | 1.076 |
| F92 | 0.463 | 0.620 | 0.986 | 1.179 |
| F95 | 0.490 | 0.627 | 0.986 | 1.177 |
| W20 | 0.460 | 0.733 | 0.747 | 1.074 |
| F98 | 0.525 | 0.683 | 0.747 | 1.000 |

DSP 在布线后可能变多：Vivado 会把一部分加法映射进 DSP。

**时钟被扇出和控制分发卡住，不是乘法。**
- W22 的五条最差路径里：
  - 四条从 Conv3 的流水线使能，经 4 级 LUT 到 DSP 输入，中间网络扇出 956，布线延迟占 83%；
  - 一条是 Conv3 参数 FIFO 写私有权重 LUTRAM，扇出 101，布线延迟占 97%。
- F98 最差的是 Conv2 参数 FIFO 写 LUTRAM（扇出 257）。
- 没有一条走 DSP 级联。

**T8 的 RTL 周期比 HLS 多 6.4%（33,521 周期），来自 FIFO 等待（F97 计数器）。**
- Conv1 到 Conv2 的特征 FIFO 深度只有 4，跑满了；
- `reorder_rows` 两帧合计写阻塞 903,830 周期；
- 参数进程每帧约 11,230 周期。

**packing 的代价（P13–P16）：每省 1 个 DSP，要多花约 270–750 LUT。** 只有 DSP 成为瓶颈时才值得做。

## 2. 用户决定（2026-10-12）

1. **资源门限改用布线后的实测数字**（定义见第 6 节）。HLS 资源数只用来筛选“值不值得去布线”。
   - 已归档的 `infeasible` 状态不改写；需要时重新布线评估。
2. **主机不换，但允许按内存预算并行和多线程**（规则见第 6.1 节）。
   - 主机 12 个逻辑 CPU、15 GiB 内存、没有 swap。瓶颈是内存，不是 CPU：Vivado 实现期间 CPU 平均只忙 9–13%。
   - 原来“全部串行”是因为 F81/F84/F87 三次被 OOM 杀掉；原因是 Vivado 综合默认开约 4 个约 2.4 GiB 的 worker 进程。
   - 每次实现上限 3 小时。没有 4.5 ns 的收敛证据前，不尝试 4 ns 以下的目标（2.5 ns 那次跑了 3 小时也没结果）。
3. **常量 ROM 权重作为探索方向，不是主线**（第 4 节 WS-B）。
   - 主线仍是运行时加载权重的版本（W21 及其后续）。
   - ROM 用来量化“去掉参数通路”到底值多少；收益明显时，再由用户决定是否作为板上版本。
4. **comic 图不管。** 课程提供的数据和 `test/tb_set14.cpp` 的参考 PSNR/MSE 表都只有 13 张。
   - 这 13 张就是完整测试集，报告写“Set14（课程提供的 13 张）”。
   - 以后不再因为缺 comic 标注“暂定”（provisional）；已归档的文字不必回改。

## 3. 不变的约束

- **精度**：
  - w10a10acc23；
  - 输出与 E017 butterfly 参考逐位一致，六像素边界 MSE 1.6618e-05；
  - 13 张图 ΔPSNR 不低于 −0.1 dB。
  - 只有 WS-E 的 T4 路线允许 Conv2 用 8 位权重。它的参考是 `experiments/E065_apfixed_mixed_conv2w8`，13 张图 ΔPSNR −0.0759 dB。
- **接口**：
  - 运行时加载版本的 `srcnn` 签名不变；
  - ROM 版本使用新的顶层（第 4 节）。
- **流程**：同 0004 第 3、7 节。
  - 每个实验先用 `exp/plan_arch.py` 归档估计并提交，再建设计；
  - 新 ID 开工前确认没有被占用。目前可用：F32–F79、W23 起、C13 起；F100 以上留给复现。
  - 不推送，不运行 `script.py`，不提交 `AGENTS.md`。

## 4. 工作项

### WS-0 准备（先做）

1. 在 `exp/commit_exp.py` 的 `OWNED` 里加入 `docs/0005-rom-clock-t4-plan.md`。
2. 加入布线门限判定：
   - 在实现结果的归档（`verify_exp.py` 和相应的 summarize 脚本）里新增 `route_feasible` 列；
   - 按第 6 节的规则从布线报告计算；
   - 保留原来的 HLS 判定列，不改写历史行。
3. 把单一的 `.synthesis.lock` 换成按内存预算准入的调度（第 6.1 节）：
   - 每类任务按实测峰值登记内存；
   - 启动前检查剩余预算和系统的 `MemAvailable`；
   - 运行中持续采样内存，沿用现有的 host_memory 记录。
   - 先跑一轮受控验证：两个 csynth 并行，加一个 C 仿真。确认峰值与登记值相符后再全面启用。
4. Vivado 线程：
   - 综合保持 `synth.maxThreads=1`（三次 OOM 都出在多进程综合）；
   - 布局布线的 `general.maxThreads` 从 2 提到 4 做一次对照，记录峰值 RSS 和耗时，再决定是否用 8；
   - 修改沿用现有的 per-run hook，不改全局设置。

### WS-A 上板（与秀夫协作）

agent 碰不到开发板，这一项负责准备交付物和记录结果：

1. 交付 F98（5 ns）的打包 IP 路径、寄存器映射（HLS 生成的驱动头文件）和接口说明。顶层签名和原 `srcnn` 相同。
2. 预期值：558,758 周期；在 200 MHz 下 IP 级 2.794 ms。
3. 测量规程：
   - 读回板上实际 PL 时钟（秀夫的板子上设定 100 MHz，读回来是 66.666 MHz）；
   - 同一个比特流在两个时钟下各测一次，把 PL 周期和不随时钟变化的开销分开；
   - 分开记录单帧时间和多帧连续调用的时间。
4. 时钟：F98 只在 5 ns 下收敛，板上 PL 时钟不能超过 200 MHz。如果板上 IOPLL 是 1000 MHz，除数 5 正好是 200 MHz。整板 block design 要重新检查时序：OOC 收敛不包含互联。
5. 结果写进第 8 节，不做推断。

### WS-B 常量 ROM 权重（探索，W23 起）

目的：权重在编译时固定，去掉参数 AXI 口、参数读取和变换进程、参数 FIFO 和私有权重的写端口。F98/W22 的参数分发路径正是关键路径之一。

这是探索方向，主线仍是运行时加载版本。它的价值是量化参数通路的代价（周期、LUT、时钟）。WS-C/D/E 不依赖它的结果，可以并行。

1. **生成 ROM 内容。** 新脚本（如 `exp/gen_rom_weights.py`）：
   - 读入 `src/weights/*.bin`；
   - 用和运行时完全相同的量化（`encode_weight`：AP_RND_CONV、AP_SAT、10 位）；
   - Conv1 再做和 `transform_params` 相同的整数 G2 变换；
   - 生成常量头文件，写入源文件的 SHA256。
2. **等价性先验。** 在 W21 的 C 仿真里导出运行时装载后的全部 bank 内容，与 ROM 头文件逐元素比较，必须完全相同。这一步通过前不综合。
3. **设计。**
   - 复制 `designs/winograd_subkernel_cache_v1` 为新目录；
   - 新顶层 `srcnn_rom(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W])`，保留 `image_in`/`image_out` 的 m_axi 和 control 的 s_axilite；
   - 删除 `parameters` bundle 及其进程和流；
   - 引擎用常量数组，保持原有 bank 划分，乘法保持 `BIND_OP impl=dsp`。
4. **测试。**
   - 新的 testbench 包装调用 `srcnn_rom`，golden 对比仍从 `src/weights` 读权重；
   - 两帧 RTL 仿真改为“同一组权重、第二帧换输入”。原来的“换参数”检查对 ROM 版不适用，要写明。
5. **预期（假设）：**
   - 每帧少约 11k 周期的参数启动；
   - 区外 LUT 和变换逻辑消失；
   - 参数分发路径消失，剩下 Conv3 使能扇出这一类路径；
   - 先按 5 ns 布线，收敛后再试 4.5 ns。
6. **验收：**
   - butterfly 逐位一致，13 张图通过；
   - 两帧 RTL 仿真 PASS，周期不多于 W21 的 558,758；
   - 布线门限通过；
   - 时序收敛的时钟不比 W21 差。

### WS-C 时钟（4.95 → 4.5 → 4 ns）

不改功能，每次只改一处，每次都单独布线验证。可以先对 W21 做第 1 步，和 WS-B 的编码并行。

1. **同一份 RTL，只换 Vivado 策略。**
   - 例如 `Performance_Explore`，以及带扇出复制的布线后 phys_opt；
   - 先用工具的 help 确认 HLS 配置里的选项名；
   - 目标先定 4.5 ns。
2. **流水线改成 free-running 风格。** 对三个 fold 循环试 `#pragma HLS PIPELINE II=1 style=frp`（或对应的全局配置），去掉 Conv3 那条扇出 956 的全局使能。要记录它增加的寄存器和 FIFO，以及周期变化。
3. **给 Conv3 的 step/选择路径加寄存器**，切断从 step 寄存器经多级 LUT 到 DSP 输入的路径。

验收：在新目标下独立布线收敛；RTL 周期变化在 ±1% 以内；布线门限通过。

### WS-D FIFO 等待（目标从 +6.4% 降到 +2% 以内）

1. Conv1 到 Conv2 的特征 FIFO 深度从 4 加到 16 或 32，用 LUTRAM/SRL 实现。
2. 给 `reorder_rows` 的输出加缓冲，或者调整它的写出顺序。
3. 只用两帧 RTL 仿真的周期和 FIFO 计数器判断效果，HLS 的估计看不出 FIFO 等待。
4. 上限：最多收回约 33k 周期，约 6%。

### WS-E T4（拓展目标，按条件决定做不做）

- **纸面估计（假设）：**
  - Conv1 Winograd 576 DSP + Conv2 用 8 位权重 packing 256 DSP + Conv3 200 DSP，合计约 1,032 DSP（HLS）；
  - 布线后可能多出约 0–18%；
  - 周期约 280–300k。
- 以主线 W21（运行时加载）为基础。
  - Conv2 的两个 8 位权重在参数装载阶段拼进同一个 27 位操作数：每帧只拼一次，不在计算路径上。
  - 如果 WS-B 证明 ROM 收益明显，可以另做 ROM 版本，改成离线拼装。
- **筛选门槛：** HLS DSP ≤ 1,100 且 HLS LUT ≤ 约 170k，才去布线。按 LUT 布线/HLS ≈ 0.5 推算，布线后约 85k，接近 70% 门限。
- **停止条件：**
  - 布线门限不过；
  - 或者收敛时钟 × RTL 周期不比当时最好的 T8 设计更快。
- 预期（假设）：时钟可能降到 5–6 ns，帧时间约 1.5–1.8 ms。

## 5. 顺序与并行

1. WS-0，包括内存预算调度的受控验证。
2. 用 Vivado 槽跑 WS-C 第 1 步：W21，同一份 RTL，4.5 ns，布局布线 4 线程对照。同时用剩余预算并行编码，并对以下设计做 C 仿真和 csynth：
   - WS-C 第 2、3 步（在主线 W21 上做）；
   - WS-D；
   - WS-B（探索）。
3. 各设计 csynth 通过后，按 Vivado 槽的空闲情况排布线，优先主线（WS-C、WS-D），WS-B 其次。
4. WS-E：主线时钟和 FIFO 有结论后，按筛选门槛决定。T4 的 csynth（约 3.3 GiB、26 分钟，参照 C11）可以提前并行跑。
5. WS-A 由秀夫并行推进，有结果就记录。

## 6. 门限与筛选规则

**最终可行性（用户 2026-10-12 批准）：** 以独立 OOC 实现的布线报告为准，同时满足：

- 在所述时钟下 WNS ≥ 0、TNS = 0、WHS ≥ 0，没有未布线网络；
- LUT ≤ 81,984（70%），FF ≤ 163,968（70%），DSP ≤ 1,248，BRAM18K ≤ 288，URAM ≤ 64；
- DSP 超过 90% 时单独标注布线风险。

**HLS 筛选（决定要不要布线，不能据此宣称可行）：**

- HLS LUT ≤ 约 160k、HLS FF ≤ 约 230k、HLS DSP ≤ 1,100；
- 超出时说明理由再决定是否布线。

**帧时间：**

- 只用“RTL 实测周期 × 收敛的布线时钟”；
- 用目标减负 WNS 得到的周期只作估计，不作为结论。

### 6.1 主机并行规则（用户 2026-10-12 批准并行）

各类任务的实测内存峰值（来自已归档的 host_memory 和工具日志）：

| 任务 | 实测峰值 | 实测耗时 | 登记预算 |
| --- | --- | --- | --- |
| Vivado 实现（单线程 / 2 线程） | 10.4–12.0 GiB RSS | 44–63 分钟 | 12.5 GiB |
| C/RTL 协同仿真（T8 两帧） | 6.8 GiB RSS | 约 52 分钟 | 7.5 GiB |
| csynth（T16/T8） | 1.5–1.8 GB | 7–9 分钟 | 2.5 GiB |
| csynth（T4，参照 C11） | 3.3 GB | 约 26 分钟 | 4 GiB |
| C 仿真 | 未单独测量，先按 1 GiB 登记，受控验证时实测 | — | 1 GiB |

准入规则：

- 总预算 13 GiB，并且始终保留至少 2 GiB `MemAvailable`；
- 任一新任务启动前，`MemAvailable` 减去它的登记预算后必须 ≥ 2 GiB；
- Vivado 实现运行时只允许再跑 C 仿真；
- 协同仿真可以和最多 2 个 csynth 同时运行；
- 没有 Vivado 和协同仿真时，csynth 最多 4 个并行；
- 同一工作目录不得并发，已完成的工作区仍不可覆盖；
- 任一任务被 OOM 杀掉时，立即退回串行，归档内核证据，并上调该类任务的登记预算。

## 7. 汇报格式

同 0004 第 8 节的表格；另加 `route_feasible` 和 `rtl_cycles × route_clock` 两列。没有测到的写 unknown。

## 8. 进展记录

| 日期 | ID | 结果 |
| --- | --- | --- |
| 2026-10-12 | — | 文档建立。当前最快：W21，在 W22 的 4.95 ns 下 2.766 ms（IP 级）。用户决定见第 2 节。 |
| 2026-10-12 | — | 用户补充决定：ROM 只作探索，主线保持运行时加载；不再追 comic，13 张即完整测试集；允许按内存预算并行和多线程（第 6.1 节）。 |

<!-- ROM_CLOCK_MEASUREMENTS -->

### 自动归档的进展

完整指标和解读见 [ROM_CLOCK.md](../experiments/ROM_CLOCK.md)；下表数字由报告解析生成。

| id | parent | status | HLS_cycles | HLS_DSP | HLS_LUT | rtl_cycles | route_feasible | rtl_cycles_x_route_clock_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F35](../experiments/F35_runtime_rom_bank_equivalence/F35.md) | W19 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [W24](../experiments/W24_constant_rom_T8/W24.md) | W19 | pass | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown |
| [W25](../experiments/W25_rom_changed_input_cosim_W24/W25.md) | W24 | cosim_complete | 524330.0 | 630.0 | 53316.0 | 554226.0 | unknown | unknown |
| [W26](../experiments/W26_frp_W21_T8/W26.md) | W21 | fail | unknown | unknown | unknown | unknown | unknown | unknown |
| [W27](../experiments/W27_frp_W21_T8/W27.md) | W21 | pass | 525237.0 | 644.0 | 81484.0 | unknown | unknown | unknown |
| [F40](../experiments/F40_fifo16_W21_T8/F40.md) | W21 | pass | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown |
| [F41](../experiments/F41_fifo32_W21_T8/F41.md) | W21 | pass | 525237.0 | 644.0 | 81105.0 | unknown | unknown | unknown |
| [F42](../experiments/F42_reorder_W21_T8/F42.md) | W21 | pass | 525237.0 | 644.0 | 81550.0 | unknown | unknown | unknown |
| [C13](../experiments/C13_runtime_prepacked_conv2_T4/C13.md) | W21 | infeasible | 263090.0 | 1032.0 | 127966.0 | unknown | unknown | unknown |
| [F47](../experiments/F47_windows16_W21_T8/F47.md) | W21 | pass | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown |

未测量的计划：

| id | parent | status | condition |
| --- | --- | --- | --- |
| W23 | W21 | unlaunched_memory | unknown |
| F39 | W21 | queued_or_running | unknown |
| F45 | F41 | queued_or_running | unknown |
| W28 | W27 | queued_or_running | unknown |
| W29 | W24 | unlaunched_memory | W25 same-ROM/changed-input two-frame RTL must pass before implementation |
| W30 | W27 | unlaunched_memory | W28 FRP changed-parameter RTL must pass the preplanned plus/minus1 percent cycle gate before implementation |
| F48 | F47 | queued_or_running | unknown |
| F46 | F42 | queued_or_running | unknown |
| C14 | C13 | queued_or_running | unknown |
| C15 | C13 | unlaunched_memory | C14 mixed-precision changed-parameter RTL must pass before implementation; compare its frame product to W22 |
