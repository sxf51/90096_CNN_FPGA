# best：C17 方案（T4 Winograd + 32 深窗口 FIFO）的源码与结果打包

这是本项目探索实验中最终选定的方案，对应实验卡 **C17**（设计 `designs/winograd_t4_windows32_v1`），
由 **C20**（C/RTL 协同仿真）和 **C22**（Vivado 5 ns 布局布线）完成验证。
本文件夹是从 `experiments/` 归档和仓库源码复制出来的独立快照，内容本身没有重新运行。

## 方案概要

- 三层 SRCNN（1 -> 64 -> 32 -> 1，核 9x9 / 1x1 / 5x5），输入 255 x 255 单通道，顶层 `srcnn`，float32 接口不变（AXI m_axi 图像输入输出、共享参数 m_axi、s_axilite 控制），权重每次调用在线加载并在片上量化、重排。
- 定点：权重/激活 10 bit，Conv2 权重 8 bit，累加器 23/21/23 bit（记作 `w10_8_10a10acc23_21_23`）。
- Conv1 用 F(2x2,3x3) 整数 Winograd（9x9 核拆成 9 个 3x3 子核），T=4 并行；Conv2 用 DSP 内两路 signed8 打包；Conv3 直接卷积。全部是 dataflow 流式结构，无完整中间特征图；Conv1、Conv3 边缘复制填充在线生成。
- 相对父设计 C13 的唯一改动：变换后窗口 FIFO 深度从 2 增到 32，消除了 C14 中测到的窗口读阻塞。

## 关键结果（按证据层级区分）

| 层级 | 实验 | 结果 |
| --- | --- | --- |
| C 仿真 | C17 | 13 张图（Set5 butterfly + Set14 其余 12 张，缺 comic）与 E065 参考逐位一致；相对 float golden 的平均 deltaPSNR -0.0759 dB（门限 -0.1 dB）；butterfly 六像素边界 MSE 1.41e-5 |
| HLS 综合（4 ns 目标） | C17 | 1032 DSP，146 BRAM18K，127985 LUT，192308 FF，0 URAM；三条 MAC 折叠 II=1；延迟下界 263090 周期。LUT/FF 超过 HLS 门限，按历史记录状态为 `infeasible`，由布线结果作为最终判据 |
| C/RTL 协同仿真 | C20 | 两帧不同参数均通过；延迟 273023 周期，间隔 273052 周期；窗口读阻塞为 0 |
| Vivado 布局布线（5 ns，脱离上下文 OOC） | C22 | 时序收敛：WNS +0.013 ns，WHS +0.032 ns，TNS 0，无未布线网络；1032 DSP，59552 LUT，100499 FF，109 BRAM18K，0 URAM |
| 推算 IP 帧时间 | C20 x C22 | 273023 周期 x 5 ns = **1.365 ms**，不含 DDR 传输和驱动开销 |
| 4.5 ns 尝试 | W34 / W36 | 均时序失败（WNS -0.324 / -0.216 ns），关键路径在 Winograd 算术与量化，8 到 11 级逻辑 |
| 板上验证 | 无 | **尚未进行**。本方案不能描述为已可部署 |

HLS 估计与布线结果差约两倍（LUT 0.47 倍、FF 0.52 倍、BRAM 0.75 倍），原因是 Vivado 对生成 RTL 的映射和优化，不是算术改动。排名和验收只用布线后的数字。

## 目录说明

```
best/
  README.md                  本文件
  hls_config.cfg             C 仿真 / HLS 综合配置（相对路径版，由 results/C17_hls/hls_config.cfg 重建）
  hls_config_cosim.cfg       协同仿真配置（由 results/C20_cosim/hls_config.cfg 重建）
  run_hls.sh                 在本文件夹内调用 vitis-run 的包装脚本
  checksums.txt              全部文件的 SHA256
  src/                       综合用源码，与 experiments/C17_t4_fifo/source 和 designs/winograd_t4_windows32_v1 逐字节一致
    srcnn.cpp conv1.cpp srcnn.h types.h winograd_math.h ieee_decode.h integer_numeric.inc
  src_plain/C17_srcnn_plain.cpp  宏已代入的平铺阅读版（2026-10-23 整理），只用于阅读，不是综合输入
  testbench/                 C17 源码提交 013a306 时的 testbench
    validate.cpp golden.cpp tb_conv1.cpp tb_srcnn.cpp util.cpp util.h   C 仿真用
    validate_reload.cpp                                                 C20 协同仿真用（两帧、换参数）
  data/
    weights/                 预训练 float 参数（src/weights）
    set5/ set14/             课程测试数据（test/）
    fixed_reference.bin      butterfly 定点参考（experiments/E065_apfixed_mixed_conv2w8/butterfly_output.bin）
    numpy_reference/         13 张图的 numpy 定点参考（exp/numeric_reference/mixed_conv2w8/numpy_reference）
  results/
    C17_hls/                 实验卡 C17.md、metrics.json、quality.csv（逐图 PSNR）、csynth.rpt、分模块报告 reports/、csim/csynth 日志
    C20_cosim/               C20.md、verification.json（RTL 周期）、cosim 报告、dataflow 通道/进程计数 profiling/、cosim 日志
    C22_impl_5ns/            C22.md、verification.json（布线门限）、vivado_reports/（时序、利用率、setup 路径）、critical_paths.csv、
                             implementation/（实际使用的 Vivado tcl 与 5 ns xdc）、diagnostics/、impl 日志
    W34_W36_impl_4p5ns_failed/  两次 4.5 ns 失败尝试的实验卡、时序报告和关键路径
  board_handoff/
    xilinx_com_hls_srcnn_1_0.zip   C22 导出的 IP 包（SHA256 d423415a...，见 manifest.json）
    HANDOFF.md manifest.json       接口、寄存器偏移、来源提交、板上测量步骤
    xsrcnn*.c xsrcnn*.h            HLS 生成的驱动源码
```

## 来源与版本

- 源码提交：`013a306867f6292bb87227062b3298e42d2362d2`（C17 综合与 C22 布线使用的源码）；C20 验证提交 `806f30a3`，C22 验证提交 `daa9eec1`。
- 工具：Vitis / Vitis HLS 2026.1（SW Build 6497934），远程 Linux 主机；器件 `xck26-sfvc784-2LV-c`。
- HLS 目标时钟 4 ns；布局布线约束 5 ns（`results/C22_impl_5ns/implementation/srcnn.xdc`）。
- 编译宏：`EXP_T=4 EXP_ALL_CONTINUOUS=1 EXP_ONLINE_PAD=1 EXP_STORAGE=1 EXP_W_BITS=10 EXP_A_BITS=10 EXP_FRAMES=2 EXP_FIXED=1 EXP_SET14=1 EXP_REFERENCE=1 EXP_NUMPY_REFERENCE=1 EXP_QUICK=1`，以及 `-std=c++14 -ffp-contract=off`。

## 复现

在装有 Vitis 2026.1 的 Linux 机器上，把整个 `best/` 复制过去，先 `source .../Vitis/settings64.sh`，然后在本文件夹内：

```sh
bash run_hls.sh csim     # C 仿真，输出 quality.csv 和各图 *_output.bin，与 data/ 中参考逐位比较
bash run_hls.sh csynth   # HLS 综合，对应 results/C17_hls
bash run_hls.sh cosim    # 协同仿真（需先综合），对应 results/C20_cosim
```

两份 cfg 是把归档配置里的远程绝对路径改成相对本文件夹的路径，其余选项逐行一致；本次打包没有重新执行它们。
5 ns 布局布线不在脚本内：C22 使用 `results/C22_impl_5ns/implementation/` 中的分阶段 Vivado 脚本对导出 IP 单独运行，单线程综合，受内存限制一次只跑一个重任务。
仓库内的正式复现入口仍是 `python3 exp/reproduce_exp.py C17 --run`（见 `experiments/REPRODUCE.md`）。

## 限制

- 没有板上测量；1.365 ms 是 RTL 周期乘以独立收敛的 5 ns，不含 DDR、驱动与缓存维护开销。
- OOC 实现只证明 IP 自身在 5 ns 收敛，整体 block design 时序需单独收敛。
- Set14 缺少 comic 图像对，13 张图的验收不等于完整 Set14。
- 4.5 ns 未收敛，不能推断更快时钟。
