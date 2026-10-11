# 实验演进图与完整索引

[English](README.en.md)

入口：[实验思路说明](../0004-experiment-evolution.md)、[总览 SVG](overview.svg)、[全部实验记录](records.md)。SVG 可单独打开并放大；按节点的实验编号查阅逐项记录。每条路线另外提供 Mermaid 源码。

## 单张完整演进图

[完整紧凑图](full.svg) 将全部 153 项实验与 207 条依赖放在同一张有向图中，每个编号只出现一次。[本地查看器](full.html) 可直接打开，支持拖动、缩放、编号定位及上下游关系高亮，不需要服务器或联网。节点仅显示编号、一句思路和加粗指标；完整说明与验证状态放在悬停提示中。图的依赖仍来自 `data.json`，`compact-titles.json` 只压缩中英文标签。

颜色沿用现有图：绿色表示当前验证阶段通过，琥珀色表示 HLS 时序告警，红色表示资源/II/配置或实现失败，青色表示软件分析。绿色的 C/RTL 功能结果不能解释为布线时序通过；实际布线节点显示 WNS，P08 是小内核布线时序通过，E070 是整网布线完成但时序失败。

运行失败、超时、无效配置、仅计划以及缺少功能通过记录的硬件实验整节点淡化，相邻连线也降低亮度。C 仿真通过但资源超预算的实验保留正常红色，便于看见失败路线的资源代价。软件分析不适用硬件仿真判定。实现节点只从明确的同设计验证依赖核对功能前提，不从普通设计祖先继承验证结论。

加粗指标按阶段显示：整网/单层 HLS 时间及资源、小内核 HLS 周期、C 仿真的质量/MSE、RTL 周期、布线 WNS。无有效结果时显示失败或未运行，不使用继承的 HLS 字段和计划估计代替测量。HLS 时间仍是估计值，资源中的 B18 指 BRAM18K。

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

HLS 资源预算为 DSP≤1248、BRAM18K≤288、URAM≤64、LUT≤81984、FF≤163968；LUT/FF 为芯片容量的 70% 项目预算。满足资源预算不代表已通过物理时序。毫秒值沿用实验注册表的 cycles × max(目标周期, HLS 估计周期) / 10⁶ 公式，仍需检查 clock uncertainty 后的逻辑预算；PE/单层实验与整网分开。

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

`--full` 单独生成 `full.svg` / `full.en.svg`、相应 Mermaid 源码、本地 HTML 查看器与 `layout.full*.json`，不重写原有 13 张路线图；检查时额外核对所有编号和依赖恰好出现一次。查看器内嵌同一 SVG；图标取自 `lucide-static@0.468.0`，许可保留在 `viewer-icons.json` 和生成的 HTML 中。

## 渲染检查

本地预览和几何复核使用 `@larksuite/whiteboard-cli` 0.2.13，仅写本地图片，不创建飞书文档：

```sh
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.svg -f svg --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.svg -o /tmp/srcnn-experiment-overview.png -f svg -s 1
```

本次语言同步已核对 153 项实验及 207 条依赖，确认中英文测量、状态和证据一致；两种语言各 13 张图的生成一致性与布局检查通过。13 张英文 SVG 的 XML 和外部几何检查均通过，外部检查为零错误、零警告；总览、连续流水与验证关系图已渲染目视检查。10 份相关 Markdown 的 3,000 个本地链接和锚点通过检查。本次检查未重新运行 HLS 实验。

完整图更新另行检查了中英文各 153 个唯一节点与 207 条带类型的依赖，确认与档案逐项一致；45 个失败/未执行节点淡化，加粗指标与 C、RTL、HLS、布线阶段一致。两张 SVG 的 XML、生成一致性及外部几何检查通过，外部检查均为零错误、零警告。Playwright 在两种语言的 1440 x 900 桌面及 390 x 844 手机视口验证了非空渲染、无横向溢出、编号定位、异常编号、缩放、拖动、双指缩放、关系高亮与清除定位，并检查截图。10 份相关 Markdown 的 3,016 个本地链接和锚点通过检查；原有 26 张路线图及测量数据保持一致。

总览及每条路线都应能单独打开。新增实验时先核对原始证据、维护中英文 catalog 和思路说明，再运行两种语言的生成和检查；不要只复制上一项的成功结论。英文生成会拒绝缺失或重复编号，并保持测量和依赖共用。
