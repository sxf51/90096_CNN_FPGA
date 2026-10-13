# C17：T4 Winograd SRCNN（最终交付版本）

[English](README.en.md)

这是架构探索中最快、并且完成了完整 IP 级验证的设计：
- 13 张图逐位一致；
- 两帧 RTL 协同仿真通过；
- 5 ns（200 MHz）下 Vivado 布线收敛；
- IP 级每帧 **1.365 ms**（约 732 帧/秒）。

尚未完成整板集成与上板实测，见“已知限制”。

| 项目 | 结果 | 证据 |
| --- | --- | --- |
| 精度 | 13 张图平均 PSNR 29.083 dB，浮点 golden 为 29.158 dB，**ΔPSNR −0.0759 dB**；逐张从 −0.011（monarch）到 −0.268 dB（foreman） | C17，`reports/hls/quality.csv` |
| 逐位一致 | butterfly 输出与独立验证的定点参考（E065）逐位一致；与浮点 golden 的 MSE 为 1.77065e-05 | C17；打包时用课程 testbench 重跑确认 |
| RTL 周期 | 两帧事务都 PASS，延迟 **273,023**、间隔 273,052 周期；第二帧换了输入、权重和 bias | C20，`reports/cosim/` |
| 布线时序 | 目标 5.0 ns：WNS +0.013 ns，WHS +0.032 ns，TNS 0，没有未布通的网络 | C22，`reports/impl/srcnn_timing_routed.rpt` |
| 布线资源 | DSP 1,032（82.7%），LUT 59,552（50.8%），FF 100,499（42.9%），BRAM18K 109（37.8%），URAM 0 | C22，`reports/impl/srcnn_utilization_routed.rpt` |
| IP 级帧时间 | 273,023 × 5 ns = **1.365 ms** | C20 × C22 |

PSNR 的口径是对高清真值、按归一化浮点计算的 MSE PSNR，不裁剪、不截边。“Set14”指课程提供的 13 张图（没有 comic）。

## 目录

| 路径 | 内容 |
| --- | --- |
| `src/` | HLS 源码，与 `designs/winograd_t4_windows32_v1/` 和 C17 的归档源码逐字相同 |
| `ip/srcnn.zip` | C22 布线时使用的打包 IP（Vivado IP 目录格式，含 HDL、驱动和 OOC 约束） |
| `driver/` | 从 IP 包中取出的 HLS 生成驱动（`xsrcnn*.c/h`），方便直接查看 |
| `reports/hls/` | C17 的 HLS 综合报告和 13 张图的精度表 |
| `reports/cosim/` | C20 的 RTL 协同仿真报告 |
| `reports/impl/` | C22 的布线时序、资源、状态报告和最差路径 |
| `scripts/run_csim.sh` | 用课程原版 testbench 做 C 仿真 |
| `provenance/` | C17 原始 HLS 配置（远程绝对路径，作溯源用）和 Vitis 版本 |
| `SHA256SUMS` | 源码和 IP 包的校验和 |

## 设计概要

- **整网 DATAFLOW 流式结构**：每像素 4 个周期（T4）。三层 DSP 分配为 576 / 256 / 200，中间特征图不完整存储。
- **Conv1**：整数 Winograd F(2×2,3×3)。9×9 卷积核拆成 9 个 3×3 子核，每像素乘法从 5,184 降到 2,304。
- **Conv2**：权重 8 位，两个输出通道的权重拼成一个 27 位操作数，一个 DSP 同时算两个乘法。
- **Conv3**：直接卷积，每拍 8 个通道 × 25 个抽头。
- **精度**：权重和激活都是 10 位（Conv2 权重 8 位），累加器 23 位；舍入和饱和与参考模型一致。
- **调度**：三层都是连续折叠（II=1，整帧不排空）、在线补边；Winograd 变换窗口 FIFO 深 32（相对 C18 少 9.2% 周期）。
- **权重**：每次调用都从 DDR 重新装载 8,129 个参数，并在片上完成 Winograd 权重变换。

## 接口

顶层签名与课程原版相同：

```cpp
void srcnn(float in[1][255][255],
           float weights1[64][1][9][9], float biases1[64],
           float weights2[32][64][1][1], float biases2[32],
           float weights3[1][32][5][5], float biases3[1],
           float out[1][255][255]);
```

- **数据**：都是 float32，布局与课程的 `.bin` 文件相同。
- **AXI 主口（m_axi）**：三个，`image_in`（in）、`image_out`（out）、`parameters`（6 个参数数组）；突发长度 256。
- **控制口（s_axilite `control`）**：

| 偏移 | 寄存器 |
| --- | --- |
| 0x00 | AP_CTRL（bit0 ap_start，bit1 ap_done，bit2 ap_idle） |
| 0x04 / 0x08 / 0x0c | GIE / IER / ISR（中断） |
| 0x10 | `in` 地址（64 位：0x10 低 32 位，0x14 高 32 位） |
| 0x1c / 0x28 | `weights1` / `biases1` 地址 |
| 0x34 / 0x40 | `weights2` / `biases2` 地址 |
| 0x4c / 0x58 | `weights3` / `biases3` 地址 |
| 0x64 | `out` 地址 |

调用方式：写入 8 个缓冲区的物理地址，置 `ap_start`，轮询 `ap_done` 或等中断。缓冲区必须是 DDR 中的连续物理内存（PYNQ 用 `pynq.allocate`）；启动前要把 CPU 缓存刷回内存，读取结果前要使缓存失效。

## 使用方法

### C 仿真（已验证）

```sh
source <Vitis 2026.1>/settings64.sh
bash final/C17/scripts/run_csim.sh            # 默认输出到 final/C17/build/csim
```

使用仓库的 `test/csim.cpp`、`test/tb_conv1.cpp`、`test/tb_srcnn.cpp`、`test/util.cpp`、`test/set5/` 和 `src/weights/`。2026-10-13 打包时在远程 Vitis 2026.1 上实际运行过，34 秒完成，输出：

```
***** CONV1 Golden Reference *****
  - Butterfly MSE: 5.15431e-06
***** SRCNN Golden Reference *****
  - Butterfly MSE: 1.77065e-05
```

课程 testbench 只打印 MSE、总是返回 0，所以要看数值本身。逐位一致和 13 张图的验收用的是实验框架里的 testbench（见下文“完整复现”）。

### 重新综合和打包（打包时未重跑）

先运行一次 `run_csim.sh` 生成 `build/csim/hls_config.cfg`（`clock=4ns`、`syn.top=srcnn`、相同宏定义），然后在 `final/C17/` 目录下运行：

```sh
v++ -c --mode hls --config build/csim/hls_config.cfg --work_dir build/syn
vitis-run --mode hls --package --config build/csim/hls_config.cfg --work_dir build/syn
```

在原实验中，T4 的 HLS 综合约需 26 分钟、3.3 GB 内存。`ip/srcnn.zip` 来自原实验流程，它的 HDL 与 C17 打包时的 HDL 逐文件相同，只有 `component.xml` 的版本号和创建时间不同。

### 完整复现（实验框架）

在仓库根目录运行 `python3 exp/reproduce_exp.py C17 --run`。这会用新的编号重放 C17 的 C 仿真和综合，复现说明见 [experiments/REPRODUCE.md](../../experiments/REPRODUCE.md)。

### 上板集成（尚未执行，仅为步骤说明）

1. 解压 `ip/srcnn.zip`，在 Vivado 中把它加为 IP 仓库。
2. 搭 block design：
   - Zynq UltraScale+ MPSoC（KV260）；
   - 控制口 `s_axi_control` 经互联接到 `M_AXI_HPM0_FPD`；
   - 三个 m_axi 口接到 `S_AXI_HP*_FPD`。
3. PL 时钟设为 200 MHz（1000 MHz ÷ 5）。OOC 布线余量只有 13 ps，**必须重新检查整板时序**；收不住时改用 166.67 MHz（1000 MHz ÷ 6），每帧约 1.64 ms。
4. 上板后用 `pynq.Clocks` 读回实际 PL 时钟。秀夫的上一版设定 100 MHz，读回的是 66.666 MHz。

## 已知限制

- 所有数字都是 IP 级结果：理想 AXI，不含 DDR、驱动、互联和板上时钟。还没有做整板实现和上板实测。
- 5 ns 下建立时间余量只有 13 ps。
- 每帧都重装权重：在 T4 上实测每帧多约 4.5k–6k 周期（约 2%）。带“权重重装开关”的版本 C32 已通过 RTL 验证，但在 5 ns 下差 0.102 ns 没收敛，所以没有放进这个交付。
- 平均 ΔPSNR 为 −0.0759 dB（门限 −0.1 dB）；但单张 foreman 是 −0.268 dB。全 10 位的版本 foreman 也有 −0.226 dB。
- 推到 4.5 ns 的尝试（W34、W36）都没收敛。

## 来源

- 源码：`designs/winograd_t4_windows32_v1`（最初提交于 013a306）。
- 实验：
  - C17：C 仿真、HLS 综合、13 张图，[记录](../../experiments/C17_t4_fifo/C17.md)；
  - C20：两帧 RTL 仿真，[记录](../../experiments/C20_ws_cosim_C17/C20.md)；
  - C22：分阶段 Vivado 实现，5 ns，[记录](../../experiments/C22_ws_impl_C17/C22.md)。
- 设计方案：[docs/0005](../../docs/0005-rom-clock-t4-plan.md)。
- 工具：Vitis/Vivado 2026.1（SW Build 6497934），器件 `xck26-sfvc784-2LV-c`。
