# 文档索引

- [HLS 报告位置与 Git 保留规则](0001-hls-reports.md)：C 仿真、综合、协同仿真及实现报告的用途、路径和保存方式。
- [隔离夜间实验](0002-overnight-experiments.md)：精度扫描、编译器对照、流架构、验收与实验记录。
- [架构探索](0003-architecture-exploration.md)：Packing、Winograd、scatter、分块融合、估算对照与最终 RTL 验证。
- [F25 之后：布线验证、权重加载重构与 T8](0004-t8-weight-loading-plan.md)：接手 agent 的工作文档，包括 F89 布线、权重加载重构和 T8 Winograd。
- [W21 之后：常量权重、时钟与 T4](0005-rom-clock-t4-plan.md)：第二份工作文档，记录改用布线门限等用户决定，以及上板、ROM 权重、时钟、FIFO 和 T4 的计划。
- [报告草稿：Agent-Driven Design Space Exploration](0006-report-agent-driven-dse.md)：课程报告中 agent 工作流一节的英文草稿、图片位置说明和待核对事项；中文对照版见 [0006-report-agent-driven-dse.zh.md](0006-report-agent-driven-dse.zh.md)。演化图数据在 `experiments/graph.json`，生成结果在 `experiments/evolution/`。
- [报告草稿：Final Architecture](0007-report-final-architecture.md)：课程报告最终架构一章的英文草稿：数据流各级宽度表、按 T 计算的 DSP 预算表、Conv1 Winograd（压缩版）、Conv2 DSP 打包、Conv3 直接卷积与 scatter 对照，以及每个数字的来源。
- [报告草稿：Introduction、Discussion、Conclusion 与参考文献](0008-report-intro-discussion.md)：课程报告第 1、6、7 节的英文替换稿：带明确目标 G1–G4 的引言、目标回溯表、从基线到板上 762× 的分块归因（含里程碑表）、方法评价、局限与后续工作、结论，以及参考文献列表和正文引用位置。
- [C17 报告图](figures/C17/README.md)：C17 折叠时序、层间平衡、数据流背压、进程甘特图、定点位宽、HLS 与布线资源对比、conv2 打包位图、conv3 窗口与引擎共八张 SVG，以及重新生成的脚本。
- [课程报告 LaTeX 版](../report/README.md)：Notion 页面 "Agent-Driven Design Space Exploration for HLS Acceleration of SRCNN on the Kria KV260" 的 LaTeX 转换（`report/`），含图片、两份代码附录、转换脚本和构建说明。
