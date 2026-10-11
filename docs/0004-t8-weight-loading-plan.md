# F25 之后：布线验证、权重加载重构与 T8

本文是接手 agent 的工作文档，2026-10-12 根据已归档证据整理。所有数字来自 `experiments/` 下的报告；标注“假设”或“估计”的内容还没有实验证据。

开工前按顺序读：两份 `AGENTS.md`（父目录和本项目）、[0002](0002-overnight-experiments.md)、[0003](0003-architecture-exploration.md)、[ARCH_SUMMARY](../experiments/ARCH_SUMMARY.md)、[PROGRESS](../experiments/PROGRESS.md)、[REPRODUCE](../experiments/REPRODUCE.md)。

## 1. 现状

### 1.1 主方案 F25

[F25](../experiments/F25_nested_weight_loader_T16_2p5ns/F25.md)（`designs/continuous_nested_load_v1`）是目前最快、资源可行、逐位精确的整网设计：

| 项目 | 值 | 证据 |
| --- | --- | --- |
| 结构 | 整网 DATAFLOW 流式，T16，三层 DSP 按 MAC 比例分配 324/128/50 | csynth |
| 精度 | w10a10acc23，13 张图 ΔPSNR −0.0695 dB | F80 C 仿真 |
| HLS 估计 | 1,056,904 周期，2.5 ns 目标 / 2.377 ns 估计，2.64 ms | csynth |
| 资源（HLS 估计） | DSP 502 (40%)，BRAM18K 73 (25%)，LUT 69,976 (59%)，FF 125,404 (53%) | csynth |
| RTL | 两帧 PASS，latency 1,068,183 / interval 1,068,212 周期 | F82 cosim |
| 布线 | **没有结果**：F81 在 Vivado 综合阶段被主机 OOM 杀掉 | F81 |
| 板上 | 没有 | — |

- T16 理论下限（65,025 × 16 = 1,040,400）占实际 HLS 周期的约 98.5%。在 T16 下主要靠时钟变快，而时钟恰恰是没验证的部分。
- F24 的协同仿真 F85 已在远程 PASS，但没有收回本地。

### 1.2 备选

- 备选不是 F08，而是**同一份 F25 RTL 在实际能达到的时钟下实现**：周期数不变，只换时钟。
  - F08 周期数和 F25 一样，用旧补边（逐行串行，有 FIFO 停顿风险），没做过协同仿真，LUT 也约 69k，不降低任何风险。
- 保底是 E039：唯一完成布线的整网（[E070](../experiments/E070_first_feasible_implementation/E070.md)）。
  - 10 ns 目标下 WNS −1.277 ns，约 11.3 ns。
  - 按 HLS 周期数算约 33.6 ms。

### 1.3 HLS 估计的可信度（目前只有 E070 一个校准点）

| 指标 | HLS 估计 | 布线后 | 比例 |
| --- | --- | --- | --- |
| 时钟 | 7.3 ns | 11.277 ns | 1.54× |
| LUT | 44,530 | 20,454 | 0.46× |
| FF | 46,123 | 33,844 | 0.73× |
| BRAM18K | 168 | 62（31 BRAM36） | 0.37× |
| DSP | 251 | 270 | 1.08× |

- E070 的关键路径：Conv1 fold 累加穿过 8 个没打拍的 DSP 级联，共 25 级逻辑。
- F 系列已经改成显式打拍的归约树，但没有布线验证。
- 不能把这个比例直接套到 F25 上，只能当作需要验证的提示。

### 1.4 瓶颈是 LUT，而且将近一半不在计算上

按 HLS 估计，DSP 和 BRAM 都有大量富余，所有 T8/T4 设计都卡在 LUT/FF 门限上。从 `csynth.rpt` 的 Instance 表把总 LUT 拆成 dataflow 区（计算）和区外：

| 设计 | T | 总 LUT | dataflow 区 | 区外 | 区外占比 |
| --- | --- | --- | --- | --- | --- |
| F25 | 16 | 69,976 | 37,682 | 32,294 | 46% |
| [F14](../experiments/F14_rotate_c3_T8_tree1_4ns/F14.md)（直接卷积） | 8 | 96,488 | 50,066 | 46,422 | 48% |
| [W17](../experiments/W17_narrow_raw_banks_T8/W17.md)（Winograd） | 8 | 93,166 | 50,877 | 42,289 | 45% |

区外 LUT 的来源（以 F25 源码为例，W17 结构相同）：

1. 权重是 `srcnn()` 里的 `static` 数组，按 `C1_OC × C1_TAP` 等因子 cyclic 拆成大量 LUTRAM bank（`ram_2p`）。
   - T16 时 w1 有 4 × 81 = 324 个 bank，T8 时是 648 个。
   - 顶层加载循环写这些 bank，dataflow 区里的引擎读，HLS 给每个 bank 端口加了两边之间的多路选择器。
   - F14 顶层 Multiplexer 共 27,607 LUT，其中能直接认出是 w1/w2/w3 bank 端口的有 18,072（11,664 + 4,608 + 1,800）。F25 顶层 Multiplexer 是 14,134。
2. 三个加载流水线（load1/2/3）各自带一个 `encode_weight`，F25 中分别约 2.7k、2.5k、2.6k LUT。
3. 两个 bias 循环（F25 `srcnn.cpp` 第 455–456 行）各带一个 `encode_weight`，并用动态下标写完全拆分的寄存器，各约 2.1k LUT。
4. AXI 适配器约 3k LUT。这部分必须保留。

旁证：
- csynth 对 engine1、conv2_stream、engine3 等报 `HLS 200-1449`（进程既有前驱又直接读调用者输入），建议改由前驱进程传入。
- F23 的 HLS 关键路径是 Conv1 权重加载的地址乘法器（2.822 ns），F24 是加载计数器（2.699 ns）。加载器既占 LUT 又压时钟。

### 1.5 为什么不在 T16 上叠 packing、scatter、Winograd

这三种方法省的是 DSP 或 BRAM，代价是 LUT。T16 下 DSP 和 BRAM 都不紧张：

- packing：w8a8 掉 5.18 dB。保持 10 位要做重叠修正，每省 1 个 DSP 约多 400 LUT + 440 FF（P07 对 P02）。
- scatter：慢 26–48%，省下的 BRAM 用不上。
- Winograd：T16 下 W18 把 DSP 从 502 降到 326，周期不变，速度没有收益。

Winograd 只有在 T8 才有意义：直接卷积 T8 要 1007 个 DSP（81%），Winograd 只要 648 个（52%）。

## 2. 目标与范围

1. **G1**：拿到 F25 的实际布线时序和资源，并用它校准 HLS 估计。
2. **G2**：在不改顶层接口和算术的前提下，把区外 LUT 从约 32k（T16）、约 46k（T8）压到约 10k。
3. **G3**：做出资源可行、逐位精确、通过协同仿真的 T8 设计，周期约 0.53M。按 HLS 估计，这大约让吞吐翻倍；实际收益以布线时钟为准。

不做：
- 改精度、网络结构、补边方式或 `srcnn` 签名；
- packing（含 P13–P16）、scatter、DDR 分块、C 系列组合；
- 板端部署（秀夫负责）。

## 3. 不变的约束

- **接口**：`srcnn` 签名、float 数组、运行时加载权重、张量布局、复制补边都不变。所有设计顶层接口相同，所以板端工作不受选型影响。
- **精度**：
  - w10a10acc23，在原来的边界做 AP_RND_CONV/AP_SAT；
  - butterfly 输出与 E017 参考逐位一致，六像素边界 MSE 记录为 1.6618e-05；
  - 最终候选跑全部 13 张图，ΔPSNR 不低于 −0.1 dB（缺 comic，结论保持“暂定”）。
- **资源门限**（按 HLS 估计，不变）：DSP 1,248，BRAM18K 288，URAM 64，LUT 81,984，FF 163,968。是否改用实现后的数字，见第 6 节。
- **流程**（0003 已规定）：
  - 每个实验先用 `exp/plan_arch.py` 归档纸面估计并提交，再建设计目录；
  - 已完成的 ID 不可复用；
  - 设计放独立目录，不改已冻结的设计；
  - 每个实验用工具提交；
  - 不推送，不运行 `script.py`，不提交 `AGENTS.md`。
- **远程主机**（15 GiB 内存）：
  - csynth、impl、cosim 都通过 `workspace/exp_runs/.synthesis.lock` 串行，C 仿真不受此限；
  - csynth 每次 60 分钟超时，同一问题调参不超过 45 分钟；
  - 不改系统 swap 和全局 Vivado 设置。
- **SSH**：`ssh -F ../ssh-config -o BatchMode=yes xiaoxin-ubuntu`；远程根目录 `/home/lipuze/amdprojects/90096_CNN_FPGA`；Vitis 环境 `/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh`。

## 4. 工作项

### WS0 收尾（先做）

2026-10-12 检查时远程没有任务在跑；锁文件存在是正常的，以有没有进程为准。

1. 收回 F85（F24 协同仿真，远程已 PASS）：`python3 exp/remote_exp.py exp/configs/F85.json --collect-only`
2. 收回 P13（远程已有归档）：`python3 exp/remote_exp.py exp/configs/P13.json --collect-only`。如果缺 `metrics.json` 就如实记录状态，不重跑。
3. P14–P16、F86–F88、F90、F91 暂不运行，保留计划文件，在 `experiments/PROGRESS.md` 注明“2026-10-12 用户决定降低优先级”。
4. 本文档不在 `exp/commit_exp.py` 的 `OWNED` 列表里：把 `docs/0004-t8-weight-loading-plan.md` 加进去，随 WS0 一起提交，之后更新本文档时随实验一起提交。

### WS1 F25 布线（F89，最高优先级）

运行：`python3 exp/run_queue.py F89`（超时 3 小时）。它沿用 F81 生成的 Vivado 流程，只把 `general.maxThreads` 和 `synth.maxThreads` 设为 1（`exp/vivado_serial_hook.tcl`）。运行期间定期看远程 `free -g`，留下内存证据。

需要记录：

- WNS/TNS；实际周期 = 2.5 − WNS（ns）；
- 布线后的 LUT/FF/DSP/BRAM/URAM，以及与 HLS 估计的比例（和 1.3 节 E070 并列）；
- 前 5 条关键路径：起点和终点模块、逻辑级数、DSP 级联情况。

| 结果 | 下一步 |
| --- | --- |
| WNS ≥ 0 | F25 帧时间 = 1,068,183 × 2.5 ns ≈ 2.67 ms（RTL 周期 × 布线时钟） |
| WNS < 0 | 新开 ID，用同一份 RTL、放宽后的时钟重新实现。优先只改实现约束（沿用 F89 的 hook 机制）；如果流程必须重新 csynth，按新设计点记录，不能当作同一份 RTL。把关键路径交给 WS2/WS4 分析 |
| 关键路径在权重加载或 bank 选择 | WS2 优先级进一步提高 |
| 再次 OOM | 停止，归档证据，交给用户决定是否换大内存主机（第 6 节）。不改系统设置重试 |
| 布线 LUT ≤ HLS 估计的约 75% | 在 WS3 里直接给 W17 安排一次实现，验证 T8 是否已经放得下 |

### WS2 权重加载重构（先在 T16 上做）

以 F25 为基线，因为它有 13 张图和 RTL 的完整证据，任何差异都能归因到加载结构。下一个可用 ID 是 F26（F80–F91 已占用），开工前确认没有被占。

**F26：存储端口探针（成本最低）**
- 改动：
  - F25 拷贝，权重 bank 从 `ram_2p` 改为 `ram_s2p`：写端口只给加载循环，读端口只给引擎；
  - bias 改成常量下标展开或移位写入；
  - 其他完全不变。
- 假设：顶层 bank 端口的多路选择器大部分消失。
- 看：顶层 Multiplexer LUT、区外 LUT、时钟估计、周期数。

**F27：参数流式加载**
- 改动：
  - 在 `dataflow_region` 里加一个 `read_params` 进程：唯一读取 `parameters` bundle，只用一个 `encode_weight`，按层输出权重和 bias 流；
  - 每个引擎拥有自己的局部 bank（保持现有 cyclic 分组，`ram_s2p` LUTRAM），先装载（II=1）再进入现有的 compute 循环；
  - 去掉顶层的 load1/2/3 和 bias 循环。
- 要解决：消除 200-1449 警告；bank 只有一个访问函数。
- 周期：F25 中 dataflow 区之外约 16.4k 周期（总 1,056,904 减 dataflow 区 1,040,467），主要是串行在前面的加载循环和不展平的 Conv1 加载的排空。改后 Conv1 先装 5,184 个权重再开算，其余层的装载被 Conv1 的启动时间掩盖，总周期应该持平或略少（假设）。
- 风险：
  - 每个消费者必须先读完自己的参数流再读像素流，参数流要分层，不能共用一条按顺序交错的流，否则可能死锁；
  - `read_params` 和 `read_input` 用不同 bundle，没有端口冲突；
  - 两帧协同仿真必须覆盖每次调用重新装载的情况。

**F28（可选）**：如果 F27 之后 bank 写地址译码仍然很大，试可寻址移位寄存器（SRL）bank：装载时移位写入，计算时按 `step` 寻址读出，没有写地址译码。

WS2 验收（F26/F27/F28 各自记录，不放宽门限）：

- butterfly 与 E017 逐位一致，边界 MSE 不变；
- 三个 fold 循环 II=1，HLS 周期数不超过 F25 的 101%（≤ 约 1.07M）；
- 区外 LUT 目标 ≤ 12k（F25 是 32.3k），总 LUT 相应下降；
- 时钟估计不比 F25 差；
- F27 不再出现针对权重的 200-1449 警告；
- 选定的变体再做两帧协同仿真（新 ID）。

区外 LUT 的读法：

```sh
awk '/== Utilization Estimates/,/\* DSP:/' experiments/<ID>_*/csynth.rpt \
  | grep -E '^\|(Total|Multiplexer)|grp_dataflow_region'
```

区外 = Total 的 LUT 减去 `grp_dataflow_region_*` 行的 LUT。

### WS3 T8

WS2 有结论后再做。先做 Winograd，直接卷积作对照。

**W19：Winograd T8**（基于 `designs/winograd_rawbank_v1`，下一个可用 W 编号，开工前确认）
- 移植 WS2 选定的加载结构。运行时 Winograd 权重变换（`transform_weights`）放进参数读取进程，变换和精度保持不变。
- 显式打开 `EXP_ONLINE_PAD=1`。源码复核发现 W17 虽未设此宏，但由 `EXP_ALL_CONTINUOUS=1` 分支已调用 `online_pad`；W19 用独立宏明确控制，保持同一复制补边语义。
- 换用 F20/F22 的 IEEE 输出编码（`ieee_decode.h`）。
- 时钟先定 3.33 ns，有布线证据后再提。
- 纸面估计（假设，写进计划）：
  - DSP 648，BRAM18K ≤ 146，URAM 0，T 8；
  - 周期约 532,562 + 加载（约 5k）；
  - LUT ≈ W17 的 dataflow 区 50.9k + 区外约 10k ≈ 61k；FF ≤ 122k。

**F 系列直接卷积 T8 对照**（F14/F15 结构 + 新加载结构）
- DSP 1007（81%）。
- 注意 F14 的打拍归约树把 FF 推到 171k，超了门限；不打拍的版本（F15，FF 86k）可能更慢。
- 只作对照，不作主线。

**T8 胜出者的最终验证**（新 ID，参照 F80–F82）：全部 13 张图 C 仿真、串行 Vivado 实现、两帧协同仿真。

### WS4 时钟（F89 之后）

- 只根据布线报告里的关键路径修改，不再对着 HLS 时钟估计调参。
- 每次修改只动一处，并记录周期数和时钟的乘积。

## 5. 顺序与并行

1. WS0（几分钟）→ 启动 F89（硬件槽最多占 3 小时）。
2. F89 运行期间，在本地写 F26/F27 的计划和代码，并跑 C 仿真（C 仿真不占综合锁）。
3. F89 结束后依次跑 F26、F27 的 csynth（串行）。
4. WS2 有结论后做 W19；W19 可行后做最终验证。

## 6. 需要用户决定的事项

- F89 再次 OOM 时：是否换大内存主机。
- 是否允许把权重做成常量 ROM。这会改变运行时参数契约；收益是再去掉写端口和加载逻辑。没有批准前不做。
- 资源门限是否改用 Vivado 综合或实现后的数字。E070 显示 LUT 估计约偏高 2 倍，但只有一个点。没有批准前继续用 HLS 估计。
- 补上 comic 图，完成全部 14 张图的验收。

## 7. 新实验的操作步骤

1. 以 `exp/configs/F25.json`（或 `W17.json`）为模板写配置：
   - 新 ID、新 `name`、新 `design` 目录；
   - `purpose`、`changes`、`estimates`（必须包含 DSP、BRAM18K、URAM、T、latency_cycles、basis）。
2. `python3 exp/plan_arch.py --config <配置>` 生成 `experiments/<ID>_<name>/` 和 `exp/configs/<ID>.json`。
3. `python3 exp/commit_exp.py <ID> plan_<name>` 先提交计划。
4. 复制父设计到新的 `designs/<目录>` 后修改，不改父目录。
5. `python3 exp/remote_exp.py exp/configs/<ID>.json`：上传、远程 C 仿真与综合、归档、提交。
6. 如果 SSH 或本地队列中断而远程已完成，用 `--collect-only` 收回（见 REPRODUCE）。

当前执行补充：F26/F27 各启动一个 `remote_exp.py`，先完成 C 仿真后等待同一综合锁；F27 的配置设 `synthesis_after=F26`，只有 F26 归档后才能综合，等待超过 24 小时明确报错。C 仿真成功前不允许综合。`analyze_weight_loading.py` 从归档报告生成加载器门限表，`analyze_route.py` 从布线报告和内存 CSV 生成校准与前五条 setup 路径。

## 8. 汇报格式

每个实验完成后，在第 9 节追加一行，并按 `AGENTS.md` 说明改动、验证方法、结果和限制：

| ID | 内容 | T | 时钟 目标/估计/布线 (ns) | 周期 HLS/RTL | ms | DSP | BRAM18K | LUT 总/区外 | FF | 逐位一致 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

布线数字和 HLS 估计分列。没有测到的写 unknown，不填 0，也不用估计代替。

## 9. 进展记录

| 日期 | ID | 结果 |
| --- | --- | --- |
| 2026-10-12 | — | 文档建立；远程空闲；F85、P13 待收回；F89 未运行 |
| 2026-10-12 | WS0 | F85/P13 已收回；P14–P16/F86/F87 在新指令前已完成并保留。F88 因用户优先级调整主动 SIGTERM 中止并归档，没有 RTL 判定；F90/F91 暂缓。下一步 F89 优先，期间准备 F26/F27。 |
| 2026-10-12 | F89 | 单线程 hook 生效，Vivado IP 子综合已成功；内存采样持续归档到 host_memory.csv，布线结果待出。 |
| 2026-10-12 | F26/F27 | 先提交估算再独立实现；两帧 butterfly C 仿真逐位通过，综合等待 F89，顺序 F26→F27。自动数字和归因表见 [WEIGHT_LOADING](../experiments/WEIGHT_LOADING.md)。 |

### 第 6 节暂定决策（2026-10-12）

按用户授权先保守执行，明日再复核：继续使用运行时 float 参数，不做常量 ROM；继续按 HLS 数字判断资源，不放宽门限；缺 comic 时只能称 13 张已提供图像暂定通过。F89 若再次 OOM，归档内核和内存证据，继续 WS2，不改变 swap、不擅自迁移到未知主机；更大内存主机留待明日决定。
