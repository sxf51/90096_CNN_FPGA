# 文档索引

[English](README.en.md)

| 文档 | 内容 |
| --- | --- |
| [实验思路与演进图](0004-experiment-evolution.md) | 170 项实验的因果关系、路线调整、效果与失败点；从 F25 到 F28、W21/W22 及验证记录 |
| [单张完整演进图](experiment-evolution/full.svg) / [本地查看器](experiment-evolution/full.html) | 170 个节点、178 条主要实线、统一整网 ms/张；绿色都有耗时，红色注明问题且耗时不加粗 |
| [第一轮实验设计](0002-overnight-experiments.md) | 从 golden 到精度、编译指令和流式参数扫描的验收约束 |
| [第二轮架构探索](0003-architecture-exploration.md) | Packing、Scatter、Winograd、组合和连续调度的设计与验收流程 |
| [T8 与权重加载计划](0004-t8-weight-loading-plan.md) | 私有参数银行、Winograd T8、参数重载与独立布线的阶段门槛；收尾见 [工作流结果](../experiments/WEIGHT_LOADING.md) |
| [逐项实验索引](experiment-evolution/records.md) | 每个实验的来源、参数、实际结果、问题及原始证据 |
| [图和数据的生成说明](experiment-evolution/README.md) | 快照范围、结构、重新生成和排版检查 |
| [冻结实验复现](../experiments/REPRODUCE.md) | 使用独立编号恢复冻结设计、测试和配置 |

根目录 `src/` 与 `script.py` 是原始浮点基线；优化实验源码及冻结档案分别位于 `designs/`、`experiments/`。HLS 估计、RTL 仿真、实现后时序和板端实测须分别阅读。
