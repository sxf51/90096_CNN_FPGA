# 文档索引

[English](README.en.md)

| 文档 | 内容 |
| --- | --- |
| [实验思路与演进图](0004-experiment-evolution.md) | 207 项实验、307 条档案依赖；更新到 C18 的 T4、W32/F52 的 4.5 ns、ROM/FRP/FIFO 与待验收组合 |
| [单张完整演进图](experiment-evolution/full.svg) / [本地查看器](experiment-evolution/full.html) | 207 个节点、217 条主要实线、统一整网 ms/张；箭头留白与实际像素检查 |
| [关键里程碑图](experiment-evolution/milestones.svg) / [本地查看器](experiment-evolution/milestones.html) | 10 个紧凑节点：编号、标题、一行结果；失败节点只写具体问题 |
| [第一轮实验设计](0002-overnight-experiments.md) | 从 golden 到精度、编译指令和流式参数扫描的验收约束 |
| [第二轮架构探索](0003-architecture-exploration.md) | Packing、Scatter、Winograd、组合和连续调度的设计与验收流程 |
| [T8 与权重加载计划](0004-t8-weight-loading-plan.md) | 私有参数银行、Winograd T8、参数重载与独立布线的阶段门槛；收尾见 [工作流结果](../experiments/WEIGHT_LOADING.md) |
| [常量权重、时钟、FIFO 与 T4](0005-rom-clock-t4-plan.md) | 当前布线门限、主机策略与后续验收；结果见 [ROM_CLOCK](../experiments/ROM_CLOCK.md) |
| [T4 路线](experiment-evolution/t4.svg) / [T8 时钟与 FIFO](experiment-evolution/clock-fifo.svg) / [ROM 路线](experiment-evolution/rom.svg) / [主机对照](experiment-evolution/host.svg) | 新增 37 项实验及其独立验证、主机失败与重试 |
| [逐项实验索引](experiment-evolution/records.md) | 每个实验的来源、参数、实际结果、问题及原始证据 |
| [图和数据的生成说明](experiment-evolution/README.md) | 快照范围、结构、重新生成和排版检查 |
| [冻结实验复现](../experiments/REPRODUCE.md) | 使用独立编号恢复冻结设计、测试和配置 |

根目录 `src/` 与 `script.py` 是原始浮点基线；优化实验源码及冻结档案分别位于 `designs/`、`experiments/`。HLS 估计、RTL 仿真、实现后时序和板端实测须分别阅读。
