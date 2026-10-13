# 文档索引

[English](README.en.md)

| 文档 | 内容 |
| --- | --- |
| [实验思路与演进图](0004-experiment-evolution.md) | 207 项实验、307 条档案依赖；更新到 C18 的 T4、W32/F52 的 4.5 ns、ROM/FRP/FIFO 与待验收组合 |
| [单张完整演进图](experiment-evolution/full.svg) / [本地查看器](experiment-evolution/full.html) | 207 个节点、217 条主要实线、统一整网 ms/张；箭头留白与实际像素检查 |
| [关键里程碑图](experiment-evolution/milestones.svg) / [本地查看器](experiment-evolution/milestones.html) | 10 个紧凑节点：编号、标题、一行结果；失败节点只写具体问题 |
| [最终交付：C17（T4 Winograd）](../final/C17/README.md) | 源码、打包 IP、驱动、关键报告和使用说明；IP 级 1.365 ms/张（5 ns 布线收敛） |
| [第一轮实验设计](0002-overnight-experiments.md) | 从 golden 到精度、编译指令和流式参数扫描的验收约束 |
| [第二轮架构探索](0003-architecture-exploration.md) | Packing、Scatter、Winograd、组合和连续调度的设计与验收流程 |
| [T8 与权重加载计划](0004-t8-weight-loading-plan.md) | 私有参数银行、Winograd T8、参数重载与独立布线的阶段门槛；收尾见 [工作流结果](../experiments/WEIGHT_LOADING.md) |
| [常量权重、时钟、FIFO 与 T4](0005-rom-clock-t4-plan.md) | 当前布线门限、主机策略与后续验收；结果见 [ROM_CLOCK](../experiments/ROM_CLOCK.md) |
| [T4 路线](experiment-evolution/t4.svg) / [T8 时钟与 FIFO](experiment-evolution/clock-fifo.svg) / [ROM 路线](experiment-evolution/rom.svg) / [主机对照](experiment-evolution/host.svg) | 新增 37 项实验及其独立验证、主机失败与重试 |
| [逐项实验索引](experiment-evolution/records.md) | 每个实验的来源、参数、实际结果、问题及原始证据 |
| [图和数据的生成说明](experiment-evolution/README.md) | 快照范围、结构、重新生成和排版检查 |
| [KV260 分块融合与 INT8 试验](0004-kv260-tiled-int8.md) | 根目录 `src/` 的分块融合基线（已上板，2.2 s/张）与可选 INT8 版本的实现和验证记录 |
| [KV260 板端时钟与延迟诊断](0005-kv260-board-clock.md) | 板端实际 PL 时钟 66.666 MHz（设计 100 MHz）及延迟差额分析 |
| [硬件加速效果与下一步](0006-hardware-acceleration-review.md) | 分块基线的汇报记录 |
| [优化概括](re.md) / [讲稿](srcnn-presentation-lecture-script.md) | 分块基线的报告用文字与结合讲义的讲稿 |
| [冻结实验复现](../experiments/REPRODUCE.md) | 使用独立编号恢复冻结设计、测试和配置 |

根目录 `src/` 与 `script.py` 是 KV260 分块融合基线（见 [0004-kv260-tiled-int8](0004-kv260-tiled-int8.md)）；架构探索的设计源码及冻结档案分别位于 `designs/`、`experiments/`。编号 0004、0005 各有两三份文档，来自两条并行的工作线合并，按文件名区分。HLS 估计、RTL 仿真、实现后时序和板端实测须分别阅读。
