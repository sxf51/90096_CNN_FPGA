# 实验演进图与完整索引

[English](README.en.md)

入口：[实验思路说明](../0004-experiment-evolution.md)、[总览 SVG](overview.svg)、[全部实验记录](records.md)。SVG 可单独打开并放大；按节点的实验编号查阅逐项记录。每条路线另外提供 Mermaid 源码。

## 单张完整演进图

[完整紧凑图](full.svg) 保留全部 207 项实验，每个编号只出现一次；从档案的 307 条依赖中挑选 217 条主要优化关系，用加粗实线连接。[本地查看器](full.html) 可直接打开，支持拖动、缩放、编号定位及主要上下游关系高亮，不需要服务器或联网。节点显示编号、一句思路和整网单张延迟；红色节点另加一行具体问题，耗时不加粗。完整说明、全部来源与验证状态放在悬停提示中。

每项实验通常只连接一个主要来源；集成已有模块、引入关键精度方案或跨路线调度时保留必要的多个来源，当前有 11 个双来源节点。参数扫描可沿档案中已有的对照关系串联，表示思路演进，不表示源码继承。`main-parents.json` 明确选择多来源实验的主图连线；`compact-titles.json` 只压缩中英文标签。完整的 307 条关系仍保留在 `data.json`、逐项记录与路线图中。

绿色表示有可比较整网耗时的当前阶段通过记录，不要求布线通过；琥珀色表示 HLS 时序告警；红色表示资源超预算、II 未达目标、配置无效、运行或实现失败，并逐项注明原因。灰色辅助节点表示 PE、单层、边界或只有 C 仿真的探索实验，缺少可引用的整网周期；青色表示软件分析。分路线图保留档案的阶段配色。本快照 C18 的 T4 在 5 ns 通过全部布线门限，W32/F52/W30 的 T8 在 4.5 ns 通过；主图仍显示统一 100 MHz 时间，实际通过目标下的 1.503160 / 2.514411 / 2.472471 ms/张另列于思路说明。C13 历史 HLS 超预算和 W20 的仅诊断排除保留，不从父设计继承物理通过。

运行失败、超时、无效配置、仅计划以及缺少功能通过记录的硬件实验整节点淡化，相邻连线也降低亮度。C 仿真通过但资源超预算的实验保留正常红色。W28 是明确授权的特例：RTL 数值与换参数 Pass，周期低于原下限，保留原 `fail` 和红色问题行，注明后获单边上限接受，显示真实 RTL 时间且不淡化。只有归档授权元数据和对应 Pass 同时存在时适用。选中关系时连线恢复完整亮度。实现节点只从明确的同设计验证依赖核对功能前提，不从普通设计祖先继承验证结论。

主图唯一性能指标是完整三层 SRCNN 处理一张 `255 x 255` 图像的加速器计算延迟，统一按 **100 MHz / 10 ns 参考时钟**折算：`ms/张 = 整网延迟周期数 x 10 / 1,000,000`。优先采用本实验有效的整网 RTL 最大延迟，其次采用本实验的整网 HLS 顶层延迟。已完成的同设计验证没有自己的延迟时，只通过明确的 `verify` 关系引用实际报告，优先引用 RTL 协仿，缺少 RTL 时引用 HLS；同等优先级出现多个来源即报错。用 `~` 和来源编号标明引用，例如 F92 引用 F82、F95 引用 F93、F98/W22 引用 F97。这不是验证实验的新测量；设计本身的时序告警仍适用。启动、排空及内部数据传递以顶层报告覆盖范围为准，主机/DMA 传输不计入。

这是按现有报告周期归一化的参考值，不是重新以 10 ns 综合的结果，也不保证设计实际能在 100 MHz 运行。重新综合可能改变调度与周期数；HLS 估计与 RTL 仿真周期的来源在提示中明确区分。资源量、PE/单层周期、MSE/PSNR 和 WNS 不再放在节点上。

绿色与琥珀色节点的耗时加粗，红色耗时保留为普通灰字，不能据此进入可行方案排名。红色也包括主机 OOM 和布线时序失败。没有有效整网周期时，辅助节点说明 PE/单层/C 范围，计划节点标注等待/运行中、未归档或未运行，红色节点显示具体问题。不从 PE 工作量、普通祖先、继承表格字段或计划估计构造时间，也不给失败或未执行的验证节点引用耗时。

本次修改的验收要求：全部编号恰好出现一次；主图连线必须是档案关系的子集且无环；节点只有上述统一指标；所有绿色节点都有可追溯的整网耗时；所有红色节点都有一行问题且耗时不加粗；引用估计只通过已完成的同设计验证关系；中英文共享数值与连线；全部路线图与归档测量一致；检查生成一致性、几何布局及桌面/手机查看器交互。

## 关键里程碑图

[独立 SVG](milestones.svg) / [本地查看器](milestones.html) 将用户选定的 10 个阶段按讲述顺序串联，只写编号、标题和一行结果，不写日期或解释段落。失败节点仅标具体问题，例如 E033 的“LUT 136,868，超量 17%”；通过与告警节点标注明来源的耗时。沿用现有配色、字体和箭头留白。连线表示里程碑顺序，不新增档案依赖。文案保存在 [milestones.json](milestones.json)，数据仍固定为 `653ceb9`，不加入后续结果。

这张图的时间沿用注明的 HLS 报告时钟或已通过的布线目标，区别于完整图的固定 100 MHz 指标。E039/E070 节点仅显示 E039 的 HLS 29.83 ms/张；W22/W32/C18 显示通过目标下的折算耗时。完整验证与失败历史保留在原演进图和记录中。

## 范围与证据

这是提交 `653ceb9` 的档案快照，覆盖 `experiments/results.csv` 与 `exp/configs/*.json` 的并集：207 项，200 项有结果记录，7 项无结果行。比上一版 `a3d78b7` 新增 37 项，新增主机、ROM、T8 时钟/FIFO、T4 四张路线图及英文版。F50/F51/W31/C16/C17 在工作流中为等待/运行中，但不当作归档测量；F90/F91 继续暂缓。本版固定到 W30，后续结果不纳入。失败、无效配置及超时也是结果记录。F99 是工作流收尾/审计事件，不另造实验节点。

`catalog.json` 手工记录每项实验的思路和依赖。关系包括设计/参数基线、修复重试、数值依据、对照、模块集成、同一设计验证和复现；它不是 Git 提交祖先图。总览挑选主要因果关系，各路线保留该路线的全部依赖，灰色节点是外部来源。

`catalog.en.json` 翻译说明文字；`generate.en.rb` 共用中文版本已解析的测量和依赖，生成 `data.en.json` 与 `records.en.md`，不另行维护英文数字或关系历史。

`generate.rb` 用 Ruby 标准 CSV/JSON 解析器合并注册表、实际归档配置、验证记录与 HLS 时序告警，生成 `data.json` 和 `records.md`。其中：

- `registry_raw` 保留原表值，包括验证记录继承的估计；不将这些值作为新测量展示。
- `hls` 只存该实验实际综合解析的指标；`verification` 存 RTL 或实现的真实结果。
- `quality.provenance` 说明多图质量是否引用独立数值参考。
- `planned_estimates` 明确保存为假设，不作为实际资源、II 或延迟。
- `flags` 对资源预算、II、无效配置、HLS 时序告警、主机 OOM 及实现时序分别标记。
- `diagnostic_only` 读取归档配置的 `diagnostic_infeasible_parent`，保留 W20 的诊断排除；物理时序通过不改变原 HLS 门槛。
- `execution_state` 区分已排队/运行但未归档与暂缓计划；没有结果行的节点不显示测量。
- `acceptance_override` 保存 W28 后续用户授权；原始状态和验证记录保持不变。
- `verification.route_feasible` 单列新政策的独立布线门限，不改写历史 HLS 状态。

历史 HLS 资源预算为 DSP≤1248、BRAM18K≤288、URAM≤64、LUT≤81984、FF≤163968；LUT/FF 为芯片容量的 70% 项目预算。当前最终资源与时序验收以 [0005](../0005-rom-clock-t4-plan.md) 的独立布线门限为准，HLS 只作筛选。逐项记录与分路线图的毫秒值沿用注册表的 cycles × max(目标周期, HLS 估计周期) / 10⁶ 公式；它们与主图统一 100 MHz 的口径不同，均不当作板端实测。Set14 采用课程提供的完整 13 图，不再以缺 comic 标注暂定；原档案措辞不改写。

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
node docs/experiment-evolution/render.cjs --milestones
node docs/experiment-evolution/render.cjs --milestones --lang en
node docs/experiment-evolution/render.cjs --check
node docs/experiment-evolution/render.cjs --lang en --check
node docs/experiment-evolution/render.cjs --full --check
node docs/experiment-evolution/render.cjs --full --lang en --check
node docs/experiment-evolution/render.cjs --milestones --check
node docs/experiment-evolution/render.cjs --milestones --lang en --check
git diff --check
```

`render.cjs` 优先加载 `DAGRE_MODULE`，其次加载本地 Node 模块，最后查找 npm `_npx` 缓存中的 0.8.5。缺依赖时可装到独立临时目录：

```sh
npm install --prefix /tmp/srcnn-map-tools dagre@0.8.5
DAGRE_MODULE=/tmp/srcnn-map-tools/node_modules/dagre node docs/experiment-evolution/render.cjs
```

布局采用 Dagre 有向图和避障直角折线。箭头沿节点边的法线进入，尖端离边框 8 px，最后一段至少 28 px，14 px 的箭头三角形完全在节点外；连线与节点至少留 6 px。多来源使用独立入口，必要时绕过扩张后的节点边界。中文换行保留英文词，英文按单词换行。`--check` 检查生成一致性、节点/文字边界、节点重叠、画布范围、连线留白、箭头方向/直线段及三角形遮挡。`layout*.json` 保存实际路径和箭头边界。

`--full` 单独生成完整 SVG、Mermaid、本地 HTML 与 `layout.full*.json`，不重写总览和 16 张分路线图；额外核对全部编号恰好一次、多来源选择有效、主图连线属于原始关系且无重复。布局记录参考时钟、周期与来源，引用估计含 `metric.reference_id`，红色问题在 `problem`。查看器内嵌同一 SVG；图标来自 `lucide-static@0.468.0`，许可保留在 `viewer-icons.json` 和 HTML 中。

## 渲染检查

浏览器回归脚本 [verify-browser.cjs](verify-browser.cjs) 检查所有 SVG 的实际文字边界，并把每个箭头裁切到 canvas 检查轴线以外的三角形像素，避免仅有线段、箭头被遮住却仍通过几何检查。截图与结果写到 `/tmp/srcnn-evolution-check/`：

```sh
npm install --prefix /tmp/srcnn-map-tools playwright@1.64.0
/tmp/srcnn-map-tools/node_modules/.bin/playwright install chromium
PLAYWRIGHT_MODULE=/tmp/srcnn-map-tools/node_modules/playwright node docs/experiment-evolution/verify-browser.cjs
```

已有 Chromium 可用 `PLAYWRIGHT_CHROMIUM_EXECUTABLE` 指定可执行文件，跳过浏览器安装。本次在 Mac 使用 Node 25.8.0、Ruby 2.6.10、Dagre 0.8.5、Playwright 1.64.0 与已有 Chromium。没有运行 HLS、修改远程调度或执行板端测试。

中英文各 207 个唯一节点、217 条主要连线与 307 条归档依赖一致，全部主图连线属于档案且从 E000 可达。119 个节点显示统一时间：101 个用本实验报告，18 个引用明确的同设计报告。47 个绿色节点都有时间，95 个红色节点都有单行问题且耗时不加粗；27 个辅助节点不构造时间，50 个失败/未归档节点淡化。C18 引用 C14，W32 引用 F97，F52 引用 F43，W30 引用 W28；C13 的历史 HLS 超量、W28 的原失败与后续授权均保留。

全部 38 张 SVG 的生成、XML、几何和实际文字检查通过，1,140 个箭头通过逐个像素可见性检查。中英文查看器在 1440 x 900 桌面和 390 x 844 手机验证编号定位、异常编号、缩放、拖动、双指缩放、关系高亮、清除定位与无横向溢出；里程碑查看器另检查合并节点的编号定位与时间口径。目视检查 C18、W32、W30、T4 与里程碑截图。相关 Markdown 的本地路径和锚点另作检查。

本次图文与生成器通过 `git diff --check`；原始实验配置、日志、报告、注册表、HLS 工作区及浮点源码保持原样。

总览及每条路线都应能单独打开。新增实验时先核对原始证据、维护中英文 catalog 和思路说明，再运行两种语言的生成和检查；不要只复制上一项的成功结论。英文生成会拒绝缺失或重复编号，并保持测量和依赖共用。
