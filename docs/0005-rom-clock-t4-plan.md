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
5. **远程主机已开 zram（2026-10-12，用户要求）。** 这一条取代各处“不修改系统 swap”的约定。
   - 配置：8 GiB `/dev/zram0`，zstd 压缩，优先级 100；`vm.swappiness=100`、`vm.page-cluster=0`。
   - 配置文件 `/etc/systemd/zram-generator.conf`（systemd-zram-generator 0.3.2，用 `zram-fraction`/`max-zram-size`）和 `/etc/sysctl.d/99-zram.conf`，重启后自动生效。
   - 不使用硬盘 swap。
   - `MemAvailable` 不包含 swap，现有内存保护照常按它判断。内存记录里新增的 swap 使用量应作为观测值归档。
6. **远程工作区清理规则（用户批准）。**
   - 规则：已在本地归档报告的实验，删除远程 `hls/` 下可重新生成的工程、HDL、`.autopilot` 和仿真构建，保留 `hls/*/report/`、`hls/impl/*/report/`、`hls_data.json`、`config.cmdline`，以及工作区根目录下的全部文件（源码、日志、报告、打包 IP）。工作区目录本身保留，ID 保留规则不变。
   - 不清理：排队或运行中的任务、它们引用的父实验（两层），以及主线和上板相关的设计（W21、W22、W32、F52、F96–F98、F47/F48、W24/W25、W27/W28、F39/F42/F43、C13–C15、F28/F93–F95）。
   - 2026-10-12 已执行：清理 148 个工作区，删除 55.4 GiB，保留报告 1.4 GiB；系统盘剩余空间从 33 GB 增到 89 GB。
   - 每个被清理的工作区根目录有 `cleanup_2026-10-12_hls_manifest.tsv.gz`，记录删除的文件。汇总日志和脚本在远程与本地的 `workspace/exp_runs/_cleanup/`。
   - 以后要用某个已清理实验的生成 RTL，用 `exp/reproduce_exp.py` 在新 ID 下重新综合，不要去恢复旧工作区。

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

后续候选交付：已独立通过布线门限和同父两帧换参数 RTL 验证的运行时加载版本，可用
`python3 exp/prepare_board_handoff.py <implementation_ID> --cosim <cosim_ID>`
另行归档到 `experiments/board_handoff/<implementation_ID>/HANDOFF.md`。保留原 F98
交付物。脚本重新核对布线门限、父设计身份、换参数逐位结果、13 图验证及包的传输前后
SHA256，只归档软件驱动和元数据，IP ZIP 保持在 Git 排除的工作区。交付明确区分 HLS
打包元数据与独立收敛的布线时钟，板端实际 PL 时钟不得超过后者；不据此宣称上板通过。

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

2026-10-12 用户要求优先 C18。已启动的 W32 保持运行；C18 使用紧接其后的唯一重任务槽。通过 `exp/priority_waiters.py` 在调度锁内核实并暂停未准入的 F50/F51/W31/W30 等待进程，并用独立 `priority_light_waiters.json` 记录 C16/C17 的临时暂停，防止轻任务先占内存延后 C18。C18 的 package、综合报告和布线报告连续优先，完成后自动恢复全部等待队列。不得暂停已准入的工具进程；监督进程退出或等待超时也必须恢复被暂停的等待进程。恢复后轻任务继续遵守原内存预算。此操作不改任何实验计划、源码、工具时限或验收门槛。

1. WS-0，包括内存预算调度的受控验证。
2. 用 Vivado 槽跑 WS-C 第 1 步：W21，同一份 RTL，4.5 ns，布局布线 4 线程对照。同时用剩余预算并行编码，并对以下设计做 C 仿真和 csynth：
   - WS-C 第 2、3 步（在主线 W21 上做）；
   - WS-D；
   - WS-B（探索）。
3. 各设计 csynth 通过后，按 Vivado 槽的空闲情况排布线，优先主线（WS-C、WS-D），WS-B 其次。
4. WS-E：主线时钟和 FIFO 有结论后，按筛选门槛决定。T4 的 csynth（约 3.3 GiB、26 分钟，参照 C11）可以提前并行跑。
5. WS-A 由秀夫并行推进，有结果就记录。

C18 完成后的排队选择：F51 已准入，保持运行。随后优先 F50 的协同仿真，让
C16/C17 的 C 仿真和 HLS 筛选按余量准入；7.5 GiB cosim + 4 GiB csynth +
1.25 GiB csim 的登记总量为 12.75 GiB，实际可用余量检查仍必须通过。
用现有 `priority_waiters.py` 仅暂停尚未准入的 W31，`--basis` 归档这次自主排序
的依据；F50 归档、监督进程退出或超时后自动恢复 W31。C18/W32 的路径导出仍
按唯一重任务槽排队。保留 `serial_after_oom=true`、18 GiB 实现登记和全部保护线，
不将允许的预算组合写成实际并行证据。

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

2026-10-12 后续用户再次收紧规则：最多一个重任务（Vivado 实现、checkpoint 路径导出或 C/RTL 协同仿真）；可以搭配轻任务（csynth/C 仿真），但必须同时满足登记总预算13GiB和 `MemAvailable - 新轻任务预算 >= 2GiB`。轻任务最多3项，具体能启动几项由实测余量决定。单个重任务独立启动时不使用15GiB的历史OOM登记阻止空闲主机准入；已有C15保持原0.5GiB实际保护，不在运行中改变其计划。发生压力时优先终止最新轻任务，保留重任务；没有轻任务时保护重任务。下述两重任务政策作为历史记录保留，已被本次明确指令替代。原始OOM及内存保护失败不删除。

2026-10-12 后续明确指令“我觉得不用担心，直接干进去，同时跑两项”优先于下面的原始预留预算规则。当前采用显式 `user_two_jobs` 模式：最多同时两个任务，登记预算继续作为观测依据，不再用预算相加或新任务完整预留阻止第二项。实际 `MemAvailable` 每两秒采样；低于 0.5 GiB 时只终止最近启动的一项，保留原始日志、退出状态和 OOM 计数。发生 OOM 后仍退回串行并记录证据。实现继续使用每次独立的综合单线程、布局布线四线程 hook，不修改系统 swap。等待中的旧调度进程只在确认工具未启动后迁移，保留原 ID、计划和已准备工作区。

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

### 6.2 用户授权的性能验收修订与组合

2026-10-12 用户明确指令：F48实测535771周期虽然比原WS-D的535741目标多30周期，仍比W21快4.1%，用它作为新T8主线的基础。原2%数字继续作为诊断指标，不能再单独阻止改进候选；数值、逐位、边框、13图精度和布线资源/时序门槛不变。

W28原始记录因低于±1%区间被记fail，保留原始状态、报告、计划指纹。用户将周期门槛修订为单边上限：允许变快，仍不得超过原上限564345周期；在已通过两帧RTL、换参数和逐位验证的证据上追加用户授权元数据。W30按新授权启动，不制造重跑记录，也不将原始fail伪装成原门槛通过。汇总新增RTL验收依据，只有独立布线收敛后才关联真实帧时间。

C15结束后，先提交纸面估算，再实现两个独立组合：T8=W21+16深变换窗口FIFO+三个fold的FRP；T4=C13+32深变换窗口FIFO。T4的32深度覆盖约264周期的行扫描空隙（每tile16周期，16深只有256周期；32深覆盖512）。T8参考E017，T4参考E065，保留运行时权重接口。两者均先13图精度/HLS，再两帧换参数RTL和独立实现。若C15/组合的布线资源或时序吃紧，再另立T4 ROM计划，不提前改变接口。FRP和FIFO都减少窗口等待，纸面收益不可直接相加当作实测。

## 7. 汇报格式

### C15 单重任务内存失败后的补跑方案

C15 在布线阶段被0.5GiB保护终止，实际 `MemAvailable=0.433784GiB`，没有最终布线报告。运行中父Vivado保留 `hls_vivado_reports_synth` 的 `open_run` 综合设计，同时另起实现子进程；仅串行重任务仍会叠加这两个设计数据库。原C15工作区、失败和中间时序保持归档，不能据此宣称T4物理不可行。

新独立实验使用两阶段驱动：第一Vivado进程完成原生成流程的综合与综合报告后退出；第二进程重新打开同一新工作区的 `project.xpr`，检查综合完成，再执行原实现步骤及完整布线报告。每阶段仍占唯一重任务槽，累计实际工具运行上限3小时，保留单线程综合、既定实现线程、RTL、时钟、约束和最终资源/时序门槛。两阶段分别采样进程树内存并归档Tcl与SHA256；第二阶段不得重新创建项目、重置综合或重新启动综合。此修改仅应用于新计划和新工作区。

验收先检查脚本的项目恢复、阶段互斥、超时和失败传播，再用C13同一RTL/5ns独立补跑验证真实报告及峰值。预期每阶段峰值接近单一设计数据库而不再叠加父综合与子实现；这是待验证的主机运行假设，不是FPGA面积优化。C16/C17已满足用户“等C15出结果”的启动条件；T4是否需ROM仍由最终布线资源/时序决定。

分阶段实现的内存汇总必须使用 `impl_synth_host_memory.csv` 和 `impl_route_host_memory.csv`，另存 `host_memory_phases.csv`。总峰值取两阶段实测最大值；CPU利用率只累加各阶段内部的计数器差，排除调度等待、package和阶段之间的空隙。任一阶段缺少采样时写明缺失，不能回退到包含其他任务的全局等待期 `host_memory.csv` 并宣称该任务占用。旧的单进程实现仍使用自己的 `impl_host_memory.csv`。

zram 启用后的新采样同时保存 `/proc/meminfo` 的 `SwapTotal`、`SwapFree` 和两者之差，按阶段及整次工具运行汇总最大 swap 用量与有完整 swap 字段的样本数。旧 CSV 仅有 `SwapFree` 时不能反推总容量或宣称零使用；汇总保留 unknown 和字段覆盖率。主机 swap 用量不等于单个 Vivado 的用量，不能将它加到任务 RSS 当作峰值。正在运行的任务保持原采样模式，在新启动进程中启用新增字段；C18 的运行时主机快照单独归档。

同 0004 第 8 节的表格；另加 `route_feasible` 和 `rtl_cycles × route_clock` 两列。没有测到的写 unknown。

新布线结果的路径分析同样采用本工作流的布线门限。只关联 `cosim_complete` 且 RTL 报告为 PASS 的同父设计周期；失败、超时或周期门槛未通过的仿真不能进入已验证帧时间。布线未收敛时，目标时钟乘周期不能标为已验证时间。

从已有 routed checkpoint 导出五条路径也属于 Vivado 任务，使用双任务调度和独立 `setup_paths` 内存采样，避免在两个硬件任务之外另起一个 Vivado。导出仅打开 checkpoint 并读报告，不重新布线；其失败不改写已有实现结果，保留诊断后再重试。ROM 的模块资源报告按实际顶层 `srcnn_rom` 归档，不能套用运行时版本的文件名。

启用布线后物理优化的 `Performance_Explore` 实验必须从最终 `*_postroute_physopt.dcp` 导出路径，而不是优化前的 `*_routed.dcp`；归档选用的相对路径、阶段和SHA256。最终checkpoint缺失或同阶段有多个文件时明确报错，不能回退到较早状态。默认策略继续使用最终routed checkpoint。C18优先期间不另行占槽导出。

已有最终工程报告包含至少五条 setup 路径时，可以用
`python3 exp/archive_setup_paths.py <ID> --generated-report <工作区相对报告路径>`
直接归档。脚本核对传输 SHA256、最差 slack 与已归档最终结果一致；
`Performance_Explore` 必须使用 `*_timing_summary_postroute_physopted.rpt`，不能使用
较早的 routed 报告。记录源报告、阶段和未重新运行 Vivado，保留被替代的等待进程
诊断。此路径不宣称打开过 checkpoint，也不更改实现结果或门限；内容不足或阶段
不符时继续使用最终 checkpoint 导出。已经准入的导出任务保持运行。

`python3 exp/audit_rom_clock.py --snapshot` 可在任务运行时校验两地原始文件、冻结设计、已归档报告及未测量计划；去掉 `--snapshot` 则要求远程无实验进程。审计结果写到 `experiments/rom_clock_audit.json`，明确保留未启动计划和未完成状态。审计通过本身不代表布线或上板验收完成。

条件任务的前置验收失败时，保留原计划和门槛，在状态文件中记录未运行原因及对应失败实验。汇总单独标为 `not_run_condition_failed`，不得制造 results.csv 行、周期或布线结果。收尾审计校验失败证据后可将此条件任务计为已处理；`all_operations_archived` 仍反映有没有实际结果，另用 `all_required_operations_resolved` 区分计划已处理和全部实际运行。

## 8. 进展记录

| 日期 | ID | 结果 |
| --- | --- | --- |
| 2026-10-12 | — | 文档建立。当前最快：W21，在 W22 的 4.95 ns 下 2.766 ms（IP 级）。用户决定见第 2 节。 |
| 2026-10-12 | — | 用户补充决定：ROM 只作探索，主线保持运行时加载；不再追 comic，13 张即完整测试集；允许按内存预算并行和多线程（第 6.1 节）。 |
| 2026-10-12 | — | 远程开启 8 GiB zstd zram；按清理规则清理 148 个已归档工作区的 `hls/` 生成物（55.4 GiB），系统盘剩余 89 GB。详见第 2 节第 5、6 条。 |

<!-- ROM_CLOCK_MEASUREMENTS -->

### 自动归档的进展

完整指标和解读见 [ROM_CLOCK.md](../experiments/ROM_CLOCK.md)；下表数字由报告解析生成。

| id | parent | status | HLS_cycles | HLS_DSP | HLS_LUT | rtl_cycles | route_feasible | rtl_cycles_x_route_clock_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F35](../experiments/F35_runtime_rom_bank_equivalence/F35.md) | W19 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [W23](../experiments/W23_ws_clock_strategy_4p5_W21/W23.md) | W21 | fail | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown |
| [W24](../experiments/W24_constant_rom_T8/W24.md) | W19 | pass | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown |
| [W25](../experiments/W25_rom_changed_input_cosim_W24/W25.md) | W24 | cosim_complete | 524330.0 | 630.0 | 53316.0 | 554226.0 | unknown | unknown |
| [W26](../experiments/W26_frp_W21_T8/W26.md) | W21 | fail | unknown | unknown | unknown | unknown | unknown | unknown |
| [W27](../experiments/W27_frp_W21_T8/W27.md) | W21 | pass | 525237.0 | 644.0 | 81484.0 | unknown | unknown | unknown |
| [F39](../experiments/F39_c3_select_W21_T8/F39.md) | W21 | pass | 525237.0 | 644.0 | 81518.0 | unknown | unknown | unknown |
| [F40](../experiments/F40_fifo16_W21_T8/F40.md) | W21 | pass | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown |
| [F41](../experiments/F41_fifo32_W21_T8/F41.md) | W21 | pass | 525237.0 | 644.0 | 81105.0 | unknown | unknown | unknown |
| [F42](../experiments/F42_reorder_W21_T8/F42.md) | W21 | pass | 525237.0 | 644.0 | 81550.0 | unknown | unknown | unknown |
| [C13](../experiments/C13_runtime_prepacked_conv2_T4/C13.md) | W21 | infeasible | 263090.0 | 1032.0 | 127966.0 | unknown | unknown | unknown |
| [F43](../experiments/F43_ws_cosim_F39/F43.md) | F39 | cosim_complete | 525237.0 | 644.0 | 81518.0 | 558758.0 | unknown | unknown |
| [F44](../experiments/F44_ws_cosim_F40/F44.md) | F40 | cosim_complete | 525237.0 | 644.0 | 81086.0 | 558758.0 | unknown | unknown |
| [F45](../experiments/F45_ws_cosim_F41/F45.md) | F41 | cosim_complete | 525237.0 | 644.0 | 81105.0 | 558758.0 | unknown | unknown |
| [F47](../experiments/F47_windows16_W21_T8/F47.md) | W21 | pass | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown |
| [W28](../experiments/W28_ws_cosim_W27/W28.md) | W27 | fail | 525237.0 | 644.0 | 81484.0 | 549438.0 | unknown | unknown |
| [W29](../experiments/W29_ws_impl_W24/W29.md) | W24 | fail | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown |
| [W30](../experiments/W30_ws_impl_W27/W30.md) | W27 | impl_complete | 525237.0 | 644.0 | 81484.0 | 549438.0 | True | 2.472471 |
| [F48](../experiments/F48_ws_cosim_F47/F48.md) | F47 | cosim_complete | 525237.0 | 644.0 | 81086.0 | 535771.0 | unknown | unknown |
| [F46](../experiments/F46_ws_cosim_F42/F46.md) | F42 | fail | 525237.0 | 644.0 | 81550.0 | unknown | unknown | unknown |
| [C14](../experiments/C14_ws_cosim_C13/C14.md) | C13 | cosim_complete | 263090.0 | 1032.0 | 127966.0 | 300632.0 | unknown | unknown |
| [C15](../experiments/C15_ws_impl_C13/C15.md) | C13 | fail | 263090.0 | 1032.0 | 127966.0 | unknown | unknown | unknown |
| [F49](../experiments/F49_ws_impl_F39/F49.md) | F39 | fail | 525237.0 | 644.0 | 81518.0 | unknown | unknown | unknown |
| [F51](../experiments/F51_ws_impl_F47/F51.md) | F47 | impl_complete | 525237.0 | 644.0 | 81086.0 | 535771.0 | True | 2.678855 |
| [F52](../experiments/F52_ws_impl_F39/F52.md) | F39 | impl_complete | 525237.0 | 644.0 | 81518.0 | 558758.0 | True | 2.514411 |
| [W32](../experiments/W32_ws_clock_strategy_4p5_retry_W21/W32.md) | W21 | impl_complete | 525237.0 | 644.0 | 81086.0 | 558758.0 | True | 2.514411 |
| [C16](../experiments/C16_t8_fifo_frp/C16.md) | F47 | pass | 525237.0 | 644.0 | 81485.0 | unknown | unknown | unknown |
| [C17](../experiments/C17_t4_fifo/C17.md) | C13 | infeasible | 263090.0 | 1032.0 | 127985.0 | unknown | unknown | unknown |
| [C18](../experiments/C18_ws_impl_C13/C18.md) | C13 | impl_complete | 263090.0 | 1032.0 | 127966.0 | 300632.0 | True | 1.50316 |

未测量的计划：

| id | parent | status | condition |
| --- | --- | --- | --- |
| F50 | F42 | queued_or_running | unknown |
| W31 | W24 | queued_or_running | unknown |
