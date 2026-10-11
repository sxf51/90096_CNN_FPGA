# 实验演进图与完整索引

入口：[实验思路说明](../0004-experiment-evolution.md)、[总览 SVG](overview.svg)、[全部实验记录](records.md)。SVG 可单独打开并放大；按节点的实验编号查阅逐项记录。每条路线另外提供 Mermaid 源码。

## 范围与证据

这是提交 `800a87a` 的档案快照，覆盖 `experiments/results.csv` 与 `exp/configs/*.json` 的并集：153 项，142 项有结果记录，11 项只有计划/准备。失败、无效配置及超时也是结果记录。未完成的其他工作区运行不算入此快照。

`catalog.json` 手工记录每项实验的思路和依赖。关系包括设计/参数基线、修复重试、数值依据、对照、模块集成、同一设计验证和复现；它不是 Git 提交祖先图。总览挑选主要因果关系，各路线保留该路线的全部依赖，灰色节点是外部来源。

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
node docs/experiment-evolution/render.cjs
node docs/experiment-evolution/render.cjs --check
git diff --check
```

`render.cjs` 优先加载 `DAGRE_MODULE`，其次加载本地 Node 模块，最后查找 npm `_npx` 缓存中的 0.8.5。缺依赖时可装到独立临时目录：

```sh
npm install --prefix /tmp/srcnn-map-tools dagre@0.8.5
DAGRE_MODULE=/tmp/srcnn-map-tools/node_modules/dagre node docs/experiment-evolution/render.cjs
```

布局采用 Dagre 有向图，SVG 连线为直角折线，节点与文字按内容尺寸计算。`--check` 核对生成物是否陈旧，检查节点/文字边界、节点重叠、直角连线及连线是否穿过节点。`layout.json` 保留检查所用几何数据。

## 渲染检查

本地预览和几何复核使用 `@larksuite/whiteboard-cli` 0.2.13，仅写本地图片，不创建飞书文档：

```sh
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.svg -f svg --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.svg -o /tmp/srcnn-experiment-overview.png -f svg -s 1
```

总览及每条路线都应能单独打开。新增实验时先核对原始证据、维护 `catalog.json` 和思路说明，再运行上述生成和检查；不要只复制上一项的成功结论。
