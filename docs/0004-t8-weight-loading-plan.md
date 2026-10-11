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

2026-10-12 实测后调整：F27 区外3170 LUT、权重前驱警告为零，已达到面积目标，但局部加载的自动展平计数器使时钟2.419ns超过不放宽的2.377ns门限。因此先用独立 F28 关闭 `load_local` 内层的 `LOOP_FLATTEN`，保持计算、bank和参数流不变，单独测流水线重启的周期代价。SRL 改写不与这个时钟探针混合，若后续需要再用新 ID。

WS2 验收（F26/F27/F28 各自记录，不放宽门限）：

- butterfly 与 E017 逐位一致，边界 MSE 不变；
- 三个 fold 循环 II=1，HLS 周期数不超过 F25 的 101%（≤ 约 1.07M）；
- 区外 LUT 目标 ≤ 12k（F25 是 32.3k），总 LUT 相应下降；
- 时钟估计不比 F25 差；
- F27 不再出现针对权重的 200-1449 警告；
- 选定的变体再做两帧协同仿真（新 ID）。

选定加载器的第二帧使用不同的运行时参数，以实际覆盖重新装载：常量输入 0.5，Conv1/2/3 只保留通道 0 的中心权重 0.25/0.5/0.5，bias 为 0.5/0.25/0.125；其余权重清零。沿既有 w10a10 量化点，通道 0 依次得到 0.625、0.5625，最终所有像素精确为 104/256（0.40625）。第一帧仍按 E017 逐位比较完整 butterfly 及边界；第二帧也要求逐位相等，不放宽任何精度门限。新的 testbench 放 `exp/tb/`，随独立验证计划归档源码和提交。普通重复帧结果保留，不能冒称已检查不同参数。

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

若 F27 通过 WS2 门限，W19 的参数读取模块采用嵌套 DATAFLOW：唯一 `read_raw_params` 量化原始 8,129 个数，Conv1 原始流交给 `transform_params1`，后者每次缓存一个输出通道的 81 个原始系数、计算九组精确 G2 变换，再输出 16 个变换系数组成的数据包。Conv1 引擎私有 bank 在像素计算前读完 `64 × 9 + 64 = 640` 个包（末 64 包只用第一个字段装 bias）；Conv2/Conv3 仍为 2,080/801 个标量。变换位于参数读取模块内部，计算引擎不直接访问顶层参数。数据包在综合时为 `16 × 14 = 224 bit`，小于 4,096-bit FIFO 限制；变换不截断、不改变量化位置。正式 W19 计划需引用 WS2 实测数据并另留装载/变换/FIFO 开销，不能把区外 LUT 的归属迁移直接算作节省。

W19 先提交条件性纸面计划，代码与执行仍等严格 WS2 加载器结论。F27 实测总 LUT 只下降8320，而区外下降29124，说明原约61k估算低估了私有 bank 中保留的控制。正式假设改为78000总LUT、3200区外LUT、538500周期、648DSP和146BRAM18K；这仍是假设，不能写成资源可行。F94 可先对冻结的 F28 源码独立跑13图 C 验证；F93 的不同参数 RTL 验证仅在 F28 达到 WS2 门限后执行。

2026-10-12 W19 实测逐位及三个 fold II1 均通过，但总 LUT 超出原门限，保留 infeasible。下一项独立 W21 只改参数变换的 raw 缓存布局：报告中 `transform_groups` 的九个 `sparsemux_123_6_10_1_1` 共 2358 LUT，改用 `raw[子核][tap]` 让每个固定 tap 只选择九个来源。G2 算术、计算引擎、量化点、参数包数量和接口不变；估算与复现写入 W21 计划并先提交。其 C 仿真可与现有队列并行，综合等 W20 归档后再运行，不抢占当前 F29/F30/W20 顺序。若未满足资源门限仍如实失败，不放宽判定。

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

若 WS1 的布线 LUT 比例满足触发条件，W17 的额外实现仅用于校准。其 HLS 超 LUT 门限的原始判定保留；诊断实现必须显式设 `diagnostic_infeasible_parent=true`，仅允许逐位正确且精度通过的原设计，不能进入已验收候选排名。

默认 Vivado timing summary 只含一条 setup 路径。实现完成后，用 `python3 exp/archive_setup_paths.py F89` 从已有 routed checkpoint 额外导出前五条 setup 路径，再运行 `python3 exp/analyze_route.py E070 F89`。此只读网表操作仍使用综合锁；记录 checkpoint SHA256 和完整命令，不重新综合或布线。

新的 WS2/WS3 候选没有现成的 Vivado driver 时，使用 `implementation_backend=serial_packaged_flow` 和同一 `verification_hook`：先在独立验证目录用 `vitis-run --package`、`vivado.flow=none` 打包父 RTL。Vitis 2026.1 的帮助输出与 F25 工作目录核实：此模式不执行 RTL 综合或布局布线，但仍使用 Vivado 做 IP 打包，而且不会生成实现 driver。因此新候选保留自己的 IP，只从 `implementation_driver_template=F89` 复制官方 driver/settings/extraction/XDC 脚本；替换为新点的报告模块清单和实现时钟，再加单线程 hook 执行。脚本模板及修改后脚本分别归档 SHA256，绝不复制模板的 IP。正式候选仍须以实际打包/实现日志验收；打包和实现持有综合锁，不修改父设计、不重新 csynth。

参数重载验证使用 `prepare_ws_verify.py <父ID> --id <新ID> --operation cosim --reload-params`。先提交验证计划再创建独立 `exp/tb/validate_reload.cpp`，父 HLS RTL、设计编译宏不变，只替换 C/RTL 验证的 C++ testbench。testbench 源码及 SHA256 归档到实验目录的 `testbench/`；工具要求 C 仿真和 RTL 后检查均有精确通过标记。复现时优先使用该归档并校验 SHA256，不借用当前 testbench。

WS2/WS3 新候选可用 `python3 exp/prepare_ws_verify.py <父ID> --id <未占用ID> --operation all|cosim|impl` 生成并提交独立验证计划，再用 `run_queue.py <新ID>` 执行。`all` 在计划提交后复制已归档的父源码、跑全部 13 图和两帧 butterfly；`impl` 默认采用上述串行打包流程，`--template <ID>` 则复用已有 driver。`--implementation-clock <ns>` 只修改实现约束；`--diagnostic` 仅允许 C 仿真/逐位/精度已通过但 HLS 资源不可行的父点做诊断实现。最终实现用 `--validation-parent <全部13图验证ID>` 明确精度证据来源。

复用实现模板前逐文件比较父点与模板的 `hls/syn/verilog/` RTL 和初始化文件 SHA256；内容不同明确拒绝，不能仅凭 `srcnn` 签名相同就套用旧 IP。打包新候选后也核对原父 RTL，保证验证的是该父设计。

最终验证引用 `validation_parent` 时，先核对其已通过全部 13 张图、逐位及精度门限，再要求归档源码 SHA256、精度和设计编译宏与硬件父点一致。仅测试帧数、Set14 等 testbench 宏可不同；不能借用其他候选的精度报告。计划和执行入口都做此检查。

WS0–WS4 收尾使用 `python3 exp/close_weight_loading.py`。恢复状态需先明确 `ready_to_close=true`、本次全部 `experiment_ids` 及剩余限制；脚本要求这些 ID 全部归档，没有任何远程硬件任务，核对两份本地/远程校验和与报告来源，重跑全部绘图和汇总，再提交审计。失败、超时仍算已归档操作，但不算验收通过；已暂缓的 F90/F91 不加入本次完成清单。

实现失败或超时后，可用 `python3 exp/archive_route_progress.py <ID>` 只读收回综合、布局报告和中间路由日志。它把来源 SHA256、partial 资源与中间 WNS/TNS 单独归档，保留原失败状态，不填最终 routed 指标；这些来源同样进入收尾审计。

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
| 2026-10-12 | F89/F92 | F89 在原定三小时上限内未完成，timeout 归档，无最终 routed 报告；本次未观察到 OOM。F26 已接过综合槽。F92 预先提交同一 F25 RTL、5 ns 的单线程实现计划，待 F26/F27 综合后执行。 |

<!-- AUTO: WORKSTREAM START -->

已归档数字（脚本生成；HLS 与 RTL/布线分列）：

| id | parent | T_target | clock_target_ns | clock_est_ns | latency_cycles | interval_cycles | latency_ms_est | DSP | BRAM18K | LUT | outside_LUT | FF | bit_exact | border_mse | delta_psnr | ws2_all_gates | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F25](../experiments/F25_nested_weight_loader_T16_2p5ns/F25.md) | unknown | 16 | 2.5 | 2.377 | 1056904.0 | 1056905.0 | 2.64226 | 502.0 | 73.0 | 69976.0 | 32294.0 | 125404.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | provisional |
| [F26](../experiments/F26_s2p_bias_shift_T16/F26.md) | unknown | 16 | 2.5 | 2.377 | 1056908.0 | 1056909.0 | 2.64227 | 502.0 | 73.0 | 70808.0 | 33126.0 | 126285.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | provisional |
| [F27](../experiments/F27_local_streamed_params_T16/F27.md) | unknown | 16 | 2.5 | 2.419 | 1045713.0 | 1045714.0 | 2.6142825 | 502.0 | 73.0 | 61656.0 | 3170.0 | 122055.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | provisional |
| [F28](../experiments/F28_local_load_no_flatten_T16/F28.md) | unknown | 16 | 2.5 | 2.377 | 1046029.0 | 1046030.0 | 2.6150725 | 502.0 | 73.0 | 61553.0 | 3170.0 | 122061.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | True | provisional |
| [F29](../experiments/F29_streamed_direct_T8_tree1/F29.md) | unknown | 8 | 3.33 | 2.431 | 525761.0 | 525762.0 | 1.7507841300000002 | 1004.0 | 73.0 | 87869.0 | 3170.0 | 194668.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | infeasible |
| [F30](../experiments/F30_streamed_direct_T8_tree0/F30.md) | unknown | 8 | 3.33 | 2.431 | 525757.0 | 525758.0 | 1.7507708100000001 | 1004.0 | 73.0 | 93631.0 | 3170.0 | 104834.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | infeasible |
| [F31](../experiments/F31_reload_testbench_csim_F28/F31.md) | unknown | 16 | 2.5 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | unknown | unknown | csim_pass |
| [F89](../experiments/F89_serial_vivado_impl_F25/F89.md) | F25 | 16 | 2.5 | 2.377 | 1056904.0 | 1056905.0 | 2.64226 | 502.0 | 73.0 | 69976.0 | unknown | 125404.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | unknown | timeout |
| [F92](../experiments/F92_ws_impl_F25/F92.md) | F25 | 16 | 2.5 | 2.377 | 1056904.0 | 1056905.0 | 2.64226 | 502.0 | 73.0 | 69976.0 | unknown | 125404.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | unknown | impl_complete |
| [F93](../experiments/F93_ws_reload_cosim_F28/F93.md) | F28 | 16 | 2.5 | 2.377 | 1046029.0 | 1046030.0 | 2.6150725 | 502.0 | 73.0 | 61553.0 | unknown | 122061.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | unknown | cosim_complete |
| [F94](../experiments/F94_ws_all_F28/F94.md) | unknown | 16 | 2.5 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | True | 1.661846957728205e-05 | -0.0695141811880653 | unknown | csim_pass |
| [W17](../experiments/W17_narrow_raw_banks_T8/W17.md) | unknown | 8 | 4 | 3.239 | 532562.0 | 532563.0 | 2.130248 | 648.0 | 146.0 | 93166.0 | 42289.0 | 122399.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | infeasible |
| [W19](../experiments/W19_streamed_winograd_T8/W19.md) | unknown | 8 | 3.33 | 2.431 | 525237.0 | 525238.0 | 1.74903921 | 645.0 | 146.0 | 83623.0 | 3170.0 | 130843.0 | True | 1.661846957728205e-05 | -0.0695141811880653 | False | infeasible |

| id | parent | rtl_source | rtl_latency_cycles | rtl_interval_cycles | route_target_ns | route_WNS_ns | route_TNS_ns | route_period_from_slack_ns | route_DSP | route_BRAM18K | route_LUT | route_FF | timing_met | rtl_frame_ms_at_route_target | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F89](../experiments/F89_serial_vivado_impl_F25/F89.md) | F25 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | timeout |
| [F92](../experiments/F92_ws_impl_F25/F92.md) | F25 | F82 | 1068183.0 | 1068212.0 | 5.0 | 0.568 | 0.0 | 4.432 | 592.0 | 72.0 | 32400.0 | 77757.0 | True | 5.340915 | impl_complete |
| [F93](../experiments/F93_ws_reload_cosim_F28/F93.md) | F28 | unknown | 1059506.0 | 1059535.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | cosim_complete |

负 WNS 对应的周期只作估计，不能当作时序通过；缺失值为 unknown。

<!-- AUTO: WORKSTREAM END -->

### 第 6 节暂定决策（2026-10-12）

按用户授权先保守执行，明日再复核：继续使用运行时 float 参数，不做常量 ROM；继续按 HLS 数字判断资源，不放宽门限；缺 comic 时只能称 13 张已提供图像暂定通过。F89 若再次 OOM，归档内核和内存证据，继续 WS2，不改变 swap、不擅自迁移到未知主机；更大内存主机留待明日决定。
