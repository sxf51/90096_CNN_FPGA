# W21 之后：常量权重、时钟与 T4

本文是接手 agent 的第二份工作文档，接在 [0004](0004-t8-weight-loading-plan.md) 之后，2026-10-12 根据已归档证据整理。标注“假设”或“估计”的内容还没有实验证据。

开工前按顺序读：两份 `AGENTS.md`、[0003](0003-architecture-exploration.md)、[0004](0004-t8-weight-loading-plan.md)（其中第 3、7 节的流程仍然有效）、[WEIGHT_LOADING](../experiments/WEIGHT_LOADING.md)、[route_calibration.csv](../experiments/route_calibration.csv)。

## 1. 现状

### 1.1 已经布线且时序收敛的设计

2026-10-13 更新：最快的已验证设计是 C17（C22 布线）。

| 设计 | 源码 | T | 布线时钟 | RTL 周期 | IP 级帧时间 | 布线后资源 |
| --- | --- | --- | --- | --- | --- | --- |
| **C17（[C22](../experiments/C22_ws_impl_C17/C22.md)）** | `designs/winograd_t4_windows32_v1` | 4 | 5.0 ns，WNS +0.013 | 273,023（C20） | **1.365 ms** | LUT 59,552 / FF 100,499 / DSP 1,032 / BRAM18K 109 |
| C13（[C18](../experiments/C18_ws_impl_C13/C18.md)） | `designs/winograd_prepacked_t4_v1` | 4 | 5.0 ns，WNS +0.047 | 300,632（C14） | 1.503 ms | LUT 58,529 / FF 102,072 / DSP 1,032 / BRAM18K 109 |
| C16（[C21](../experiments/C21_ws_impl_C16/C21.md)） | `designs/winograd_windows16_frp_v1` | 8 | 4.5 ns，WNS +0.053 | 535,976（C19） | 2.412 ms | LUT 54,139 / DSP 644 |
| W27（[W30](../experiments/W30_ws_impl_W27/W30.md)） | `designs/winograd_frp_v1` | 8 | 4.5 ns，WNS +0.027 | 549,438（W28） | 2.472 ms | LUT 54,091 / DSP 644 |
| W24 ROM（[W33](../experiments/W33_ws_impl_W24/W33.md)） | `designs/winograd_rom_v1` | 8 | 4.5 ns，WNS +0.063 | 554,226（W25） | 2.494 ms | LUT 33,829 / DSP 630 |
| W21（[W32](../experiments/W32_ws_clock_strategy_4p5_retry_W21/W32.md)） | `designs/winograd_subkernel_cache_v1` | 8 | 4.5 ns，WNS +0.144 | 558,758（F97） | 2.514 ms | LUT 45,030 / DSP 644 |
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

### WS-F 权重重装开关（用户 2026-10-13 批准，基于 C18/C13）

**问题。** 现在每次调用 `srcnn` 都从 DDR 重新读 8,129 个参数，Conv1 还要重新做 Winograd 变换。官方 `test/tb_set14.cpp` 的用法是“权重读一次，然后连续处理 13 张图”，硬件却每帧重装。

- T8 上实测，重装露出到帧时间里的代价约 4,532 周期（0.8%，W25 对比 F97）。
- 参数进程本身每帧约 11,230 周期。
- T4 每帧更短，估计露出 1.5–3.7%；这是假设，用本工作项实测。

**接口（用户批准的接口变更）。**

- 新顶层 `srcnn_reload(ftmap_t in[N0][H][W], 原有 6 个参数数组, ftmap_t out[N3][H][W], bool load_params)`，配置写 `"top": "srcnn_reload"`（runner 已支持自定义顶层，W24 的 `srcnn_rom` 是先例）。
- `load_params` 走 `s_axilite` 的 control bundle；其余端口、bundle、突发长度和 C13 完全相同。
- 保留 `srcnn(...)`，原 8 个参数不变，内部以 `load_params=true` 调用 `srcnn_reload`。这样 `test/` 下的官方 testbench 不用改也能编译运行。

**语义。**

- `load_params=1`：与 C13 完全相同，先装全部参数再计算。
- `load_params=0`：不读任何参数（参数 AXI 口零流量），不做变换，直接用片上已有的权重计算。这一帧传进来的参数指针被忽略。
- 安全规则：顶层用一个 `static bool params_loaded`，上电初值为 false，实际装载 `do_load = load_params || !params_loaded`，调用结束后置 true。没装过就传 0 时，强制装载，不能用未初始化的权重算出垃圾结果。
- 主机侧约定：比特流加载后第一次调用、以及换权重的那次调用传 1，其余传 0。

**实现要点（只改这几处，算术、量化、调度、FIFO、时钟全部不变）。**

1. 从 `designs/winograd_prepacked_t4_v1` 复制出新目录（例如 `designs/winograd_prepacked_t4_reload_v1`），不改父目录。
2. `do_load` 作为标量传入 `dataflow_region`，再传给 `read_params`、`wino_engine`、`conv2_stream`、`engine3`。
   - 各进程照常无条件调用，保持 DATAFLOW 的规范形式；只在进程内部用 `if (do_load)` 包住参数读取、变换和本地装载循环。
   - `do_load=0` 时三条参数流保持为空；C 仿真末尾 `params1/2/3.empty()` 的断言必须仍然成立。
3. 片上权重和 bias（`wino_engine`、`conv2_stream` 的 `packed_weights`/`biases`、`engine3` 经 `load_local` 装载的数组）必须是 `static` 且没有初始化器，确保跨调用保留，复位也不清除。用 RTL 仿真确认，不能凭推断。
4. `read_raw_params` 的递增下标计数器每次装载都要从 0 开始，不能依赖上一帧残留。

**验证计划（全部要求逐位一致，基准与 C13/C14 相同：E065 定点参考）。**

1. C 仿真，单次运行内按顺序调用：
   - (a) `load=1`，正常权重，butterfly → 与 E065 逐位一致；
   - (b) `load=0`，参数指针换成 C14 第二帧用的构造测试参数，输入换成另一张图（如 lenna）→ 输出必须等于“正常权重 × lenna”的参考，证明硬件忽略了新指针、沿用片上权重；
   - (c) `load=1`，构造测试参数 → 每个输出都是 104/256，证明重装仍然有效；
   - (d) `load=0` → 仍然是 104/256，证明保留的是最近一次装载；
   - (e) 新建一个运行或进程，第一次调用就传 `load=0` → 按安全规则强制装载，结果正确。
2. 13 张图：第一张 `load=1`，其余 12 张 `load=0`。每张都与 E065 逐位一致，平均 ΔPSNR 仍是 −0.0759 dB。
3. RTL 协同仿真：至少 3 个事务，按 (a)(b)(c) 的顺序，三个都 PASS。分别记录 `load=1` 和 `load=0` 的事务延迟；`load=0` 的延迟必须不大于 `load=1`。原有的“第二帧换参数”检查由 (c) 覆盖。
4. 在 5 ns 下独立布线，按第 6 节的布线门限验收。资源应与 C18 基本相同；时序没有理由变好，因为参数分发路径仍然存在，只是不再每帧使用。

**测试代码。** `exp/tb/validate.cpp` 等共享 testbench 只能用新的编译宏（如 `EXP_RELOAD_SWITCH`）包住新调用序列，不得改变其他设计的行为；改完后至少回归一个旧设计的 C 仿真（如 C13），确认结果不变。

WS-F 的参数 AXI 证据采用工具 help 确认的 `cosim.setup=true`：先生成仿真工程，在生成的 testbench 中加入只读计数器，再通过 HLS Tcl 解释器运行工具原有 `run_sim.tcl`，保留输入向量检查、死锁检测、dataflow profiling 和 RTL 输出的 C 后校验。只观察 `parameters` 的 AR/R/AW/W 有效周期、握手与请求字节数，不修改综合 RTL；运行前后核对综合 RTL 的 SHA256。累计工具时间仍限 6 小时。归档四个事务（装载、复用、重装、保留）的独立周期与计数，复用时包括 ARVALID/RVALID 在内必须全为零；没有计数或 C/RTL 后校验就不能标为通过。原有两帧换参数门限继续单独保留。

2026-10-13 C26 在启动任何 Vitis 工具前因调度器的采样阶段白名单缺少
`cosim_setup` / `cosim_execute` 而失败，保留原 ID 和原始失败证据。
两个阶段都必须申请 `cosim` 重任务预算，并分别保留准入和内存记录；禁止使用轻任务
预算绕过保护。新增检查覆盖真实调度入口的阶段注册、独立记录、释放和错误预算拒绝。
修复后用新的 C27 验证同一 C23 RTL，所有数值、AXI、六小时累计时限和物理门槛保持原样。

2026-10-13 C27 的第一个复用事务实际观察到 1 次 AR/R 握手、4 字节读取，
不满足零参数 AXI 门槛。生成 RTL 将 `biases3[0]` 标量化成
`biases3_0_0_val`，在顶层无条件预读后才进入带 `do_load` 的 DATAFLOW 区域。
保留 C23/C27，并让原四事务及输出后校验跑完；该版本不得据此进入布线。
新设计从冻结 C23 复制，只在非 DATAFLOW 顶层的 `if (do_load)` 中经
`const volatile param_t *` 读取最后一个 bias，再向内部进程传递标量。
复用时传入的零占位标量不得写入已有 bank。C28 重新检查 13 图及 HLS，
C29/C30 分别检查四次调用和冷启动；三项通过后用新 ID 重做同样的四事务
RTL、零 AXI 计数及独立 5 ns 布线，不降低任何门槛。允许这些轻任务在
C27 运行期间按现有内存预算准入；新重任务仍等待 C27 释放。
参数观测的原始 CSV 与逐事务性能 XML 必须在判定前复制，并在失败或超时时
仍作为带 SHA256 的诊断证据归档。只有经过全部门槛的事务才写入已验证汇总；
不把“完整输出正确但参数口仍有读取”的结果改成通过。

**ID 与估计。** 计划用下一个可用的 C 编号（C19–C22 已占用，开工前再确认）。纸面估计：

- DSP 1,032，BRAM18K 146（HLS），URAM 0，T 4；
- LUT 约等于 C13 的 127,966 再加不到 1k；
- `load=1` 周期约等于 C14 的 300,632；`load=0` 预期少 4.5k–11k 周期。

**验收后的结论。** 连续处理视频时，帧时间以 `load=0` 的 RTL 周期 × 收敛时钟为准；第一帧（`load=1`）单独报告。

`exp/analyze_rom_clock.py` 将四个实际事务和参数 AXI 计数整理到
`experiments/reload_switch_measurements.csv`；两个汇总脚本从该表分别展示首帧、复用、重装和保留。
只有同父且门限通过的独立布线结果可以提供时钟和毫秒数。新图脚本
`exp/plots/reload_switch.py` 只读 CSV，没有实测数据时不生成图。

**后续。** 如果 C17（T4 + 32 深窗口 FIFO）胜出，这个开关与 FIFO 修改互不干扰，可以再合成一个组合版本；但必须在两者各自验证之后，另立计划。

**上板。** 交给秀夫时说明：多了一个 `load_params` 控制寄存器（HLS 生成的驱动里会有对应的设置函数）。第一帧写 1，之后写 0。

独立实现驱动和 `exp/prepare_board_handoff.py` 支持 `srcnn_reload`；交付必须先有同父的
四事务逐位、零参数 AXI 及独立布线证据。脚本读取实际打包 IP 的生成寄存器头文件，
将一位 `load_params` 与八个指针分开列出，并单独给出四次调用的 IP 时间。
旧 `srcnn` 交付继续使用原两帧换参数门槛，不继承新接口的验证结论。

### WS-G 重装开关 + 32 深窗口 FIFO 合并（用户 2026-10-13 批准）

**前提。** C31（C28 修复版重装开关的 4 帧 RTL 仿真）必须通过，包括跳过装载时参数 AXI 零流量这条检查。C31 失败时先修重装开关，不做合并。

**做法。**
- 以 C17 的 `designs/winograd_t4_windows32_v1` 为父，复制出新目录，只移植 C28 相对 C13 的重装开关改动：
  - `srcnn_reload` 顶层、`srcnn` 兼容包装；
  - `do_load` 标量和 `params_loaded` 标志；
  - 各进程内的 `if (do_load)`；
  - C28 对 `biases3[0]` 的受控读取修复。
- 先对 C13 → C28 做 diff，逐项移植，不顺带其他改动。窗口 FIFO、算术、量化、时钟全部保持 C17 不变。

**验证。** 与 WS-F 相同，基准是 E065：
- C 仿真四步序列（装、跳过且塞错误指针、重装、保留），加冷启动强制装载；
- 13 张图（第一张装载，其余跳过）；
- 4 帧 RTL 仿真，检查跳过帧的参数口零流量，分别记录装载帧和跳过帧的周期；
- 5 ns 独立分阶段布线，按第 6 节的布线门限验收。

**纸面估计（假设）。**
- DSP 1,032；HLS LUT 约 129k；
- 装载帧约 273,023 周期，跳过帧约 268.5k 周期（按 C27 实测的 4,517 周期节省推算）；
- 5 ns 下跳过帧约 1.343 ms。

**结论口径。** 连续处理视频时，用跳过帧的 RTL 周期 × 收敛时钟；装载帧单独报告。

汇总实施计划：保留已有 `rtl_frame_ms`（事务最大延迟），另从同父、已验收的四事务
及独立收敛布线计算 `first_load_frame_ms`、`steady_state_frame_ms` 和
`ranking_frame_ms`。连续帧取两次跳过调用的最大延迟，避免挑选较快样本；原接口
候选的排序值仍为其已验证最大延迟。没有严格逐位、零参数 AXI 或匹配布线证据时，
不产生复用排序值。表格和 Pareto 图标明连续帧口径，不改变历史结果或任何验收门槛。

### WS-H T4 冲 4.5 ns / 4 ns（用户 2026-10-13 批准）

**目标。**
- 4.5 ns：273k × 4.5 ≈ 1.23 ms；
- 4 ns：约 1.09 ms。4 ns 即 250 MHz，正好是 1000 MHz 除以 4，最适合上板。
- 不尝试 4 ns 以下。

**基线和依据。** 以 WS-G 的结果为父；WS-G 没完成时以 C17 为父，并在结论里写明父设计。C22 在 5 ns 下的两类最差路径：
1. `params1` FIFO（224 位宽、深 4）→ Winograd 私有权重 LUTRAM 的写数据：0 级逻辑，4.83 ns 几乎全是走线，扇出到很多 bank。
2. DSP 输出 → `wino_engine` 里的加法链（`add_ln14_393`）：11–12 级逻辑，4.94 ns。源码 `srcnn.cpp` 中对 9 个 group 的乘积是 `sum = wino::add(sum, product)` 的线性累加，后面再接输出变换。

**步骤。** 每次只改一处，每一步都要独立布线验证。
1. **同一份 RTL，只换 Vivado 策略**（`Performance_Explore` + 布线后物理优化），目标 4.5 ns。W32 曾用这个方法把 T8 从 4.95 ns 提到 4.5 ns。不改 RTL，成本最低。
2. **参数写入路径加寄存器。** 在 `params1` 出口到权重 bank 写口之间加一到两级寄存器，必要时按 bank 组复制寄存器以降低扇出。装载每帧最多一次（WS-G 之后通常为零次），多几拍延迟不影响帧时间。
3. **Winograd 9 项累加改为带寄存器的平衡加法树。** 把线性累加改成每层打一拍的平衡树（同 `Reduction` 模板，`latency=1`），必要时在输出变换前再加一级寄存器。连续折叠下，流水线多几级只增加整帧开头的一次填充。
4. 可选（探索）：T4 版 ROM，彻底去掉第 1 类路径。只有在第 2 步无效时才做，并沿用 WS-B 的接口约定。

2026-10-13 执行细化：第 2、3 步分别从已测量的 WS-G 父设计复制，互不叠加。参数版本先用独立、II=1、固定一拍延迟的函数，在 224 位 `params1` 读取与权重写入之间加一级寄存器；综合后核对返回端的实际寄存器，若被消掉则记录失败，不用源码 pragma 当作成功证据。必要时再单独计划按 bank 复制的版本。算术版本把九个完整乘积补零到 16 项，用四级平衡树，每级 fabric 加法绑定 `latency=1`；保留 34 位 `inverse`、右移两位及原量化点，输出变换暂不改动。每个新设计先提交自己的资源/周期估算，再生成源码并跑 13 图、四调用零参数 AXI RTL 和独立布线；周期只设父点的 +1% 上限。4.5 ns 先验证，只有收敛后才单独计划 4 ns。

参数寄存器证据由只读脚本归档：核对生成 helper 的 16 个 14 位字段都有
`posedge ap_clk` 非阻塞赋值和对应返回端，调用者从 `params1_dout` 接入，
权重写数据使用已注册返回值；同时对照父设计直接写 FIFO 数据的路径。
记录生成 RTL 的路径、SHA256、相关行号/片段和解析的 helper latency/II/资源，
不提交完整生成 HDL。仅控制寄存器、组合返回或缺失任一字段时不能通过此检查；
这只证明 HLS 生成了数据阶段，仍须由新 RTL 仿真和独立布线验证功能及物理收益。

**验收。**
- 逐位一致：butterfly、13 张图、换参数的多帧 RTL 仿真；
- RTL 周期相对父设计变化不超过 +1%（变快不设下限）；
- 在新目标下独立布线收敛，并通过布线门限。

### WS-I 整板时序与上板时钟（与秀夫协作，用户 2026-10-13 批准）

**问题。** C22 在 OOC 下 5 ns 的余量只有 13 ps，C18 只有 47 ps。放进 KV260 整板 block design（PS、互联、时钟）后，200 MHz 可能收不住。

**agent 能做的部分（不需要开发板）。**
1. 确认 Vivado 2026.1 里有 KV260 的板卡和器件支持文件；没有时明确报告，不要自行下载未知来源的板卡文件。
2. 用 Tcl 搭一个最小整板 block design：Zynq UltraScale+ PS、AXI 互联、C22（或 WS-G/WS-H 的胜出者）的打包 IP，PL 时钟取 PS 的 FCLK。
3. 先按 200 MHz（1000 ÷ 5）做完整实现：
   - 收敛：记录时序和资源；
   - 不收敛：改用 166.67 MHz（1000 ÷ 6）再实现。这时 C22 约 1.64 ms，C18 约 1.80 ms。
4. 导出比特流和硬件描述（`.bit`、`.hwh` 或 `.xsa`）交给秀夫，连同寄存器映射和调用约定（WS-G 版本：第一帧 `load_params=1`，之后为 0）。
5. 整板实现同样占一个重任务槽，按第 6.1 节排队。

**秀夫在板上做的部分。**
- 读回实际 PL 时钟（他之前设定 100 MHz，读回是 66.666 MHz）；
- 测单帧和连续多帧的时间；
- 同一个比特流在两个时钟下各测一次，把 PL 周期和固定开销（驱动、轮询、DDR）分开；
- 结果记入第 8 节，不做推断。

**2026-10-13 整板执行前的准备约束。** 只读检查发现安装目录已有
`data/xhub/boards/XilinxBoardStore/boards/Xilinx/kv260_som/2.0/`：
`board.xml` 指定 `xck26-sfvc784-2LV-c`，`preset_s4.xml` 提供
`mpsoc_preset_vsom`、64-bit DDR4-2400 参数；器件目录也已安装。
这只是文件证据，实际板卡对象、PS IP 和目标时钟仍须在 WS-I 启动后由 Vivado 核对。
不在其他重任务运行时另起 Vivado 做探针。

WS-I 的新实验在 WS-G/WS-H 和 C28 独立布线结束后，按已经通过同父 RTL、
质量及独立布线的候选选优，再提交该候选的独立纸面计划；准备工作不提前创建整板工程。
最小系统使用安装的板卡 preset，PS HPM 控制口接控制互联与 HLS 的 AXI-Lite，
三路 HLS AXI 主接口经数据互联接一个 PS 高性能 DDR 口，全 PL 数据路径共用
PS PL0 时钟和同步释放的低有效复位。初版采用轮询，不假定已有中断驱动。
先请求 200 MHz，记录 Vivado 生成的实际 PL0 频率和 PLL/分频参数；请求与实际
不一致时不拿请求值计算性能。控制地址和可达 DDR 地址从已验证的 BD 自动分配结果
归档，不从 OOC 驱动头文件猜系统地址。

整板综合、布局布线仍分进程释放数据库，使用唯一重任务槽、累计三小时工具上限、
综合单线程和实现四线程。分别归档整板 setup/hold、所有时钟、未布线网、资源、
关键路径和 DRC；检查完整系统约束覆盖，不能套用 IP 的 OOC 时序结论。
200 MHz 失败时先保留失败报告，再为同一冻结系统的 166.67 MHz（6 ns）独立重试
提交新计划，不覆盖原工作区。两档均失败时记录后交人工决定，不继续降低门槛。
通过者生成 bit/hwh/xsa，留在独立工作区及本地交付目录；`experiments/` 归档
文件 SHA256、大小、源码提交、板卡 preset 指纹、寄存器和调用约定，生成产物不作为源码提交。
父 RTL 周期乘系统收敛时钟只能作为理想 IP 时间，PS DDR、驱动和上板实测继续待测。

### 不再运行的旧计划

F90、F91（F24、F23 的串行布线重试）已经过时，保留计划文件，不再运行，状态记为“用户 2026-10-13 取消”。

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
| C/RTL 协同仿真（T4 四帧，C31） | 10.407 GiB 进程树 RSS | 见 C31 自动归档 | 11.5 GiB |
| csynth（T16/T8） | 1.5–1.8 GB | 7–9 分钟 | 2.5 GiB |
| csynth（T4，参照 C11） | 3.3 GB | 约 26 分钟 | 4 GiB |
| C 仿真 | 未单独测量，先按 1 GiB 登记，受控验证时实测 | — | 1 GiB |

2026-10-13 按 C31 完整四帧采样提高后续 cosim 登记值：取已完成任务的进程树峰值乘 1.10，再向上取整到 0.5 GiB。用 `exp/register_cosim_budget.py C31` 在调度锁内执行，拒绝修改正在运行的 cosim 登记；保留现有实现 18 GiB、轻任务预算、单重任务规则和 `serial_after_oom=true`。原 C31 的 7.5 GiB 准入记录原样保留，新值只影响后续任务。这是基于实测上调预算，不是新增并行授权。

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

2026-10-13 W34 运行中发现线程设置未生效：计划为布局布线 4 线程，实际实现子进程
初始化 `general.maxThreads=1`，物理优化也报告最多 1 CPU。保存的 project.xpr
有 `Performance_Explore`，但没有预期的 `OPT_DESIGN.TCL.PRE`。原因是先设置线程
hook 再换 strategy，后者重置了步骤属性；分阶段重新打开工程也只设置了默认 1。
修复计划：新驱动先设置 strategy，再设置线程 hook；重新打开已完成综合的工程后
按同样顺序重放这两项设置，并输出实际参数。用 Tcl 行为测试模拟 strategy 清除
步骤属性，确认实现启动时 hook 和线程数仍正确；保持综合单线程、三小时累计限制、
单重任务与所有数值/物理门槛。W34 继续原任务，归档其实际单线程证据，不修改运行中
脚本，不据此重写历史耗时或制造四线程测量。

修复已在 `e684bbb` 提交，177 项脚本检查通过。用
`python3 exp/observe_implementation_threads.py <ID>` 读取并归档已生成的子进程 Tcl、
保存工程的 strategy/hook 和运行日志；只做 SSH 文件读取，不启动另一项 Vivado。
W34 的实际证据见 `experiments/W34_t4_strategy_4p5_C17/implementation/thread_observation.json`。
后续实现必须核对新的子进程日志，不能只根据配置里的线程数宣称多线程已生效。

主机利用率分析也应将计划线程上限和观察到的子进程上限分开：从归档的
`implementation/thread_observation.json` 读取 child 初始化及运行时 hook，
两者矛盾时记录 unknown；没有观测文件时保留 unknown，不拿配置代替实测。
图只从派生 CSV 读取此字段。线程上限仍不代表实际 CPU 占用，后者使用各阶段采样。

主机利用率图随实验增加时，横轴用旋转的实验 ID 与短测量范围代码，
图下注明代码含义，图宽随点数增加；柱顶只标数值，避免重复 ID 和多行范围互相遮挡。
这项展示修订先提交计划，再修改绘图脚本并检查生成图；测量字段和验收门槛不变。

全架构 Pareto 图在新增 C37/C38 后，低延迟区域的完整精度字符串相互遮挡。
展示修订先提交本计划：保留所有 CSV 数据点、实验 ID、T、精度和判定，
只用较短的精度显示名称、折行长 ID 组，并把图例作为标签排布的避让对象。
同坐标的点只在 series、T、精度及判定都相同时合并显示；完整精度仍保留在 CSV。
生成后检查 PNG 的标签、图例和坐标单位，不为样式调整增加硬件实验或修改历史结果。

W34 最终在实际单线程下完成，但4.5ns 的 WNS=-0.324ns，没有收敛。
用新 ID W36 对冻结 C17 RTL 补做原计划的四线程策略对照；保留 W34 原结果和
线程诊断，不覆盖其工作区。W36 先提交独立纸面计划，排在优先 WS-G 的 C35/C36
验证之后，使用已修复的 strategy-before-thread 和分阶段重放驱动。
不因这次重试允许两个重任务；只有实际4.5ns 收敛才另立4ns计划。

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
| 2026-10-13 | C36/C38 | 用户决定：C36（WS-G 在 5 ns 差 0.102 ns）不做补救重布线；C38（平衡树，HLS FF 248,672 超过 230k 筛选线）不放行布线。当前交付基准保持 C17/C22（5 ns，1.365 ms，IP 级）。 |
| 2026-10-12 | — | 文档建立。当前最快：W21，在 W22 的 4.95 ns 下 2.766 ms（IP 级）。用户决定见第 2 节。 |
| 2026-10-12 | — | 用户补充决定：ROM 只作探索，主线保持运行时加载；不再追 comic，13 张即完整测试集；允许按内存预算并行和多线程（第 6.1 节）。 |
| 2026-10-13 | — | 当前最快：C17，C22 布线 5 ns，1.365 ms（IP 级）。用户批准 WS-G（重装开关 + 32 深窗口 FIFO）、WS-H（T4 冲 4.5/4 ns）、WS-I（整板时序与上板时钟）；F90/F91 取消。顺序：C31 → WS-G；WS-H 第 1 步（同 RTL 换策略）可先用 C17 做；WS-I 等 WS-G 或 WS-H 出结果。 |
| 2026-10-13 | — | 用户批准 WS-F：在 C18/C13 基础上加权重重装开关 `load_params`（新顶层 `srcnn_reload`，保留 `srcnn` 兼容包装），规格和验证计划见第 4 节 WS-F。排在当前 C19–C22 验证之后。 |
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
| [F50](../experiments/F50_ws_cosim_F42/F50.md) | F42 | cosim_complete | 525237.0 | 644.0 | 81550.0 | 558760.0 | unknown | unknown |
| [F51](../experiments/F51_ws_impl_F47/F51.md) | F47 | impl_complete | 525237.0 | 644.0 | 81086.0 | 535771.0 | True | 2.678855 |
| [F52](../experiments/F52_ws_impl_F39/F52.md) | F39 | impl_complete | 525237.0 | 644.0 | 81518.0 | 558758.0 | True | 2.514411 |
| [W31](../experiments/W31_ws_impl_W24/W31.md) | W24 | impl_complete | 524330.0 | 630.0 | 53316.0 | 554226.0 | True | 2.77113 |
| [W32](../experiments/W32_ws_clock_strategy_4p5_retry_W21/W32.md) | W21 | impl_complete | 525237.0 | 644.0 | 81086.0 | 558758.0 | True | 2.514411 |
| [C16](../experiments/C16_t8_fifo_frp/C16.md) | F47 | pass | 525237.0 | 644.0 | 81485.0 | unknown | unknown | unknown |
| [C17](../experiments/C17_t4_fifo/C17.md) | C13 | infeasible | 263090.0 | 1032.0 | 127985.0 | unknown | unknown | unknown |
| [C18](../experiments/C18_ws_impl_C13/C18.md) | C13 | impl_complete | 263090.0 | 1032.0 | 127966.0 | 300632.0 | True | 1.50316 |
| [C19](../experiments/C19_ws_cosim_C16/C19.md) | C16 | cosim_complete | 525237.0 | 644.0 | 81485.0 | 535976.0 | unknown | unknown |
| [C20](../experiments/C20_ws_cosim_C17/C20.md) | C17 | cosim_complete | 263090.0 | 1032.0 | 127985.0 | 273023.0 | unknown | unknown |
| [C21](../experiments/C21_ws_impl_C16/C21.md) | C16 | impl_complete | 525237.0 | 644.0 | 81485.0 | 535976.0 | True | 2.411892 |
| [C22](../experiments/C22_ws_impl_C17/C22.md) | C17 | impl_complete | 263090.0 | 1032.0 | 127985.0 | 273023.0 | True | 1.365115 |
| [W33](../experiments/W33_ws_impl_W24/W33.md) | W24 | impl_complete | 524330.0 | 630.0 | 53316.0 | 554226.0 | True | 2.494017 |
| [C23](../experiments/C23_reload_switch_quality/C23.md) | C13 | infeasible | 263090.0 | 1032.0 | 128840.0 | unknown | unknown | unknown |
| [C24](../experiments/C24_reload_switch_sequence/C24.md) | C13 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [C25](../experiments/C25_reload_switch_cold/C25.md) | C13 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [F53](../experiments/F53_legacy_C13_regression/F53.md) | C13 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [C26](../experiments/C26_ws_cosim_C23/C26.md) | C23 | fail | 263090.0 | 1032.0 | 128840.0 | unknown | unknown | unknown |
| [C27](../experiments/C27_ws_cosim_C23/C27.md) | C23 | fail | 263090.0 | 1032.0 | 128840.0 | unknown | unknown | unknown |
| [C28](../experiments/C28_reload_guard_quality/C28.md) | C23 | infeasible | 263090.0 | 1032.0 | 128849.0 | unknown | unknown | unknown |
| [C29](../experiments/C29_reload_guard_sequence/C29.md) | C23 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [C30](../experiments/C30_reload_guard_cold/C30.md) | C23 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [C31](../experiments/C31_ws_cosim_C28/C31.md) | C28 | cosim_complete | 263090.0 | 1032.0 | 128849.0 | 300634 | unknown | unknown |
| [W34](../experiments/W34_t4_strategy_4p5_C17/W34.md) | C17 | impl_complete | 263090.0 | 1032.0 | 127985.0 | unknown | False | unknown |
| [C32](../experiments/C32_reload_windows_quality/C32.md) | C17 | infeasible | 263090.0 | 1032.0 | 128868.0 | unknown | unknown | unknown |
| [C33](../experiments/C33_reload_windows_sequence/C33.md) | C17 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [C34](../experiments/C34_reload_windows_cold/C34.md) | C17 | csim_pass | unknown | unknown | unknown | unknown | unknown | unknown |
| [C35](../experiments/C35_ws_cosim_C32/C35.md) | C32 | cosim_complete | 263090.0 | 1032.0 | 128868.0 | 273025 | unknown | unknown |
| [C36](../experiments/C36_ws_impl_C32/C36.md) | C32 | impl_complete | 263090.0 | 1032.0 | 128868.0 | unknown | False | unknown |
| [W36](../experiments/W36_ws_impl_C17/W36.md) | C17 | impl_complete | 263090.0 | 1032.0 | 127985.0 | unknown | False | unknown |
| [C37](../experiments/C37_t4_reload_paramreg/C37.md) | C32 | infeasible | 263154.0 | 1032.0 | 128942.0 | unknown | unknown | unknown |
| [C38](../experiments/C38_t4_reload_balanced/C38.md) | C32 | infeasible | 263092.0 | 1032.0 | 131780.0 | unknown | unknown | unknown |

未测量的计划：

| id | parent | status | condition |
| --- | --- | --- | --- |
| W35 | C28 | unlaunched_conditional | C31 strict acceptance complete; required C28 standalone5ns route runs after prioritized WS-G/WS-H and before WS-I, on the sole heavy slot |
| C39 | C37 | queued_or_running | C37 complete13-image quality,allfoldII1,HLS screening and224-bit clocked-data evidence pass; after W36 require four exact RTL calls,zero skipped parameter AXI,unchanged RTL and matching C35 per-call upper-only+1percent limits |
| C40 | C37 | unlaunched_conditional | Launch only after strict C39 acceptance; independent4.5ns Performance_Explore staged implementation of frozen C37,observed synthesis1/route4threads and unchanged physical gates; no4ns plan until matching closure |
