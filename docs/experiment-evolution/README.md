# 实验演进图与完整索引

[English](README.en.md)

入口：[实验思路说明](../0004-experiment-evolution.md)、[总览 SVG](overview.svg)、[全部实验记录](records.md)。SVG 可单独打开并放大；按节点的实验编号查阅逐项记录。每条路线另外提供 Mermaid 源码。

## 单张完整演进图

[完整紧凑图](full.svg) 保留全部 153 项实验，每个编号只出现一次；从档案的 207 条依赖中挑选 160 条主要优化关系，用加粗实线连接。[本地查看器](full.html) 可直接打开，支持拖动、缩放、编号定位及主要上下游关系高亮，不需要服务器或联网。节点显示编号、一句思路和整网单张延迟；红色节点另加一行具体问题，耗时不加粗。完整说明、全部来源与验证状态放在悬停提示中。

每项实验通常只连接一个主要来源；集成已有模块、引入关键精度方案或跨路线调度时保留必要的多个来源。参数扫描可沿档案中已有的对照关系串联，表示思路演进，不表示源码继承。`main-parents.json` 明确选择多来源实验的主图连线；`compact-titles.json` 只压缩中英文标签。完整的 207 条关系仍保留在 `data.json`、逐项记录与路线图中。

绿色表示有可比较整网耗时的当前阶段通过记录，不要求布线通过；琥珀色表示 HLS 时序告警；红色表示资源超预算、II 未达目标、配置无效、运行或实现失败，并逐项注明原因。灰色辅助节点表示 PE、单层、边界或只有 C 仿真的探索实验，缺少可引用的整网周期；青色表示软件分析。分路线图保留原档案的阶段配色。P08 仅有 PE 布线时序通过，E070 整网布线完成但时序失败；本快照没有整网布线时序通过记录。

运行失败、超时、无效配置、仅计划以及缺少功能通过记录的硬件实验整节点淡化，相邻连线也降低亮度。C 仿真通过但资源超预算的实验保留正常红色，便于看见失败路线的资源代价。软件分析不适用硬件仿真判定。实现节点只从明确的同设计验证依赖核对功能前提，不从普通设计祖先继承验证结论。

主图唯一性能指标是完整三层 SRCNN 处理一张 `255 x 255` 图像的加速器计算延迟，统一按 **100 MHz / 10 ns 参考时钟**折算：`ms/张 = 整网延迟周期数 x 10 / 1,000,000`。优先采用本实验有效的整网 RTL 最大延迟，其次采用本实验的整网 HLS 顶层延迟。已完成的同设计验证没有自己的延迟时，只通过明确的 `verify` 关系引用设计的实际报告，并用 `~` 和来源编号标明：E069 引用 E043，F80 引用 F25，F83 引用 F24，E070 引用 E039。这不是验证实验的新测量；设计本身的时序告警仍适用。启动、排空及内部数据传递以顶层报告覆盖范围为准，主机/DMA 传输不计入。

这是按现有报告周期归一化的参考值，不是重新以 10 ns 综合的结果，也不保证设计实际能在 100 MHz 运行。重新综合可能改变调度与周期数；HLS 估计与 RTL 仿真周期的来源在提示中明确区分。资源量、PE/单层周期、MSE/PSNR 和 WNS 不再放在节点上。

绿色与琥珀色节点的耗时加粗，红色节点已有的耗时保留为普通灰字，不能据此进入可行方案排名。红色不一律等于资源超量：例如 F81/F84 是主机 OOM，E070 是布线时序失败。没有有效整网周期时，辅助节点说明 PE/单层/C 仿真范围，计划节点显示未运行，红色节点显示具体问题。不从 PE 工作量、普通祖先、继承表格字段或计划估计构造时间，也不给失败或未执行的验证节点引用耗时。

本次修改的验收要求：全部编号恰好出现一次；主图连线必须是档案关系的子集且无环；节点只有上述统一指标；所有绿色节点都有可追溯的整网耗时；所有红色节点都有一行问题且耗时不加粗；引用估计只通过已完成的同设计验证关系；中英文共享数值与连线；原路线图和测量数据保持一致；检查生成一致性、几何布局及桌面/手机查看器交互。

## 范围与证据

这是提交 `800a87a` 的档案快照，覆盖 `experiments/results.csv` 与 `exp/configs/*.json` 的并集：153 项，142 项有结果记录，11 项只有计划/准备。失败、无效配置及超时也是结果记录。未完成的其他工作区运行不算入此快照。

`catalog.json` 手工记录每项实验的思路和依赖。关系包括设计/参数基线、修复重试、数值依据、对照、模块集成、同一设计验证和复现；它不是 Git 提交祖先图。总览挑选主要因果关系，各路线保留该路线的全部依赖，灰色节点是外部来源。

`catalog.en.json` 翻译说明文字；`generate.en.rb` 共用中文版本已解析的测量和依赖，生成 `data.en.json` 与 `records.en.md`，不另行维护英文数字或关系历史。

`generate.rb` 用 Ruby 标准 CSV/JSON 解析器合并注册表、实际归档配置、验证记录与 HLS 时序告警，生成 `data.json` 和 `records.md`。其中：

- `registry_raw` 保留原表值，包括验证记录继承的估计；不将这些值作为新测量展示。
- `hls` 只存该实验实际综合解析的指标；`verification` 存 RTL 或实现的真实结果。
- `quality.provenance` 说明多图质量是否引用独立数值参考。
- `planned_estimates` 明确保存为假设，不作为实际资源、II 或延迟。
- `flags` 对资源预算、II、无效配置、HLS 时序告警、主机 OOM 及实现时序分别标记。

HLS 资源预算为 DSP≤1248、BRAM18K≤288、URAM≤64、LUT≤81984、FF≤163968；LUT/FF 为芯片容量的 70% 项目预算。满足资源预算不代表已通过物理时序。逐项记录与原路线图的毫秒值沿用实验注册表的 cycles × max(目标周期, HLS 估计周期) / 10⁶ 公式，仍需检查 clock uncertainty 后的逻辑预算；它们与主图的统一 100 MHz 折算值有不同的时钟口径。

## 重新生成

需要 Ruby、Node.js 与 `dagre@0.8.5`。Ruby 只使用标准库；不修改 HLS 工作区，不运行硬件实验。

从仓库根目录运行：

```sh
ruby docs/experiment-evolution/generate.rb
ruby docs/experiment-evolution/generate.en.rb
node docs/experiment-evolution/render.cjs
node docs/experiment-evolution/render.cjs --lang en
node docs/experiment-evolution/render.cjs --full
node docs/experiment-evolution/render.cjs --full --lang en
node docs/experiment-evolution/render.cjs --check
node docs/experiment-evolution/render.cjs --lang en --check
node docs/experiment-evolution/render.cjs --full --check
node docs/experiment-evolution/render.cjs --full --lang en --check
git diff --check
```

`render.cjs` 优先加载 `DAGRE_MODULE`，其次加载本地 Node 模块，最后查找 npm `_npx` 缓存中的 0.8.5。缺依赖时可装到独立临时目录：

```sh
npm install --prefix /tmp/srcnn-map-tools dagre@0.8.5
DAGRE_MODULE=/tmp/srcnn-map-tools/node_modules/dagre node docs/experiment-evolution/render.cjs
```

布局采用 Dagre 有向图，SVG 连线为直角折线，节点与文字按内容尺寸计算；英文按单词换行。`--check` 核对生成物是否陈旧，检查节点/文字边界、节点重叠、直角连线及连线是否穿过节点。`layout.json` 与 `layout.en.json` 保留检查所用几何数据。

`--full` 单独生成 `full.svg` / `full.en.svg`、相应 Mermaid 源码、本地 HTML 查看器与 `layout.full*.json`，不重写原有 13 张路线图；检查时额外核对所有编号恰好出现一次、多来源选择有效、主图连线属于原始关系且无重复。布局文件记录参考时钟、每个性能数值的周期与来源；引用估计另有 `metric.reference_id`，红色问题记录在 `problem`。查看器内嵌同一 SVG；图标取自 `lucide-static@0.468.0`，许可保留在 `viewer-icons.json` 和生成的 HTML 中。

## 渲染检查

本地预览和几何复核使用 `@larksuite/whiteboard-cli` 0.2.13，仅写本地图片，不创建飞书文档：

```sh
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.svg -f svg --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.svg -o /tmp/srcnn-experiment-overview.png -f svg -s 1
```

本次语言同步已核对 153 项实验及 207 条依赖，确认中英文测量、状态和证据一致；两种语言各 13 张图的生成一致性与布局检查通过。13 张英文 SVG 的 XML 和外部几何检查均通过，外部检查为零错误、零警告；总览、连续流水与验证关系图已渲染目视检查。10 份相关 Markdown 的 3,000 个本地链接和锚点通过检查。本次检查未重新运行 HLS 实验。

简化后的完整图已核对中英文各 153 个唯一节点与 160 条主要连线；每条连线都属于档案关系，从 E000 可到达全部节点，只有 8 个节点有两个来源。完整的 207 条关系未改动。76 个节点显示统一的 100 MHz 参考整网延迟，其中 72 个来自本实验报告，4 个通过明确同设计验证关系引用报告并标明来源。15 个绿色节点全部有可比较时间；80 个红色节点都有单行问题，耗时均不加粗；22 个缺少整网周期的原绿色探索节点改为灰色辅助节点。已核对 F25/F24 的 HLS 周期、F82 的 RTL 周期和四项引用来源；PE、单层、失败、无效配置、计划及只有继承字段的记录不会产生整网指标。45 个失败/未执行节点继续淡化。

两张 SVG 的 XML、生成一致性及外部几何检查通过，外部检查均为零错误、零警告。Playwright 在两种语言的 1440 x 900 桌面及 390 x 844 手机视口验证了文字边界、无横向溢出、全部连线为加粗实线、编号定位、异常编号、缩放、拖动、双指缩放、关系高亮与清除定位，并目视检查截图。额外核对 F80 的加粗引用时间、C11/E070 的普通字重耗时、F81 的主机 OOM 原因与 P08 的局部验证范围。10 份相关 Markdown 的 3,018 个本地链接和锚点通过检查；原有 26 张路线图的生成一致性检查通过，测量数据未改动。本次更新未重新运行 HLS 或板端测试。

总览及每条路线都应能单独打开。新增实验时先核对原始证据、维护中英文 catalog 和思路说明，再运行两种语言的生成和检查；不要只复制上一项的成功结论。英文生成会拒绝缺失或重复编号，并保持测量和依赖共用。
