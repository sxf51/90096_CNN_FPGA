const fs = require('node:fs');
const path = require('node:path');

function loadDagre() {
  if (process.env.DAGRE_MODULE) return require(process.env.DAGRE_MODULE);
  try { return require('dagre'); } catch (error) {
    if (error.code !== 'MODULE_NOT_FOUND') throw error;
  }
  const cache = path.join(process.env.HOME, '.npm', '_npx');
  if (fs.existsSync(cache)) {
    for (const entry of fs.readdirSync(cache).sort()) {
      const candidate = path.join(cache, entry, 'node_modules', 'dagre');
      const pkg = path.join(candidate, 'package.json');
      if (fs.existsSync(pkg) && JSON.parse(fs.readFileSync(pkg, 'utf8')).version === '0.8.5') {
        return require(candidate);
      }
    }
  }
  throw new Error('Install dagre@0.8.5 and set DAGRE_MODULE to its module directory.');
}

const dagre = loadDagre();
const langIndex = process.argv.indexOf('--lang');
const lang = langIndex < 0 ? 'zh' : process.argv[langIndex + 1];
if (!['zh', 'en'].includes(lang)) throw new Error('--lang must be zh or en');
const english = lang === 'en';
const suffix = english ? '.en' : '';
const fullGraph = process.argv.includes('--full');
const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'data' + suffix + '.json'), 'utf8'));
const byId = new Map(data.records.map(record => [record.id, record]));
const xml = value => String(value).replace(/[<>&"']/g, ch => ({
  '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;'
}[ch]));
const colors = {
  candidate: ['#f0f8f3', '#458365'], warning: ['#fff7e8', '#ac7b24'],
  failure: ['#fcf0f0', '#b16868'], infeasible: ['#fcf0f0', '#b16868'],
  planned: ['#ffffff', '#939b9b'], analysis: ['#edf7f8', '#49838a'],
  context: ['#f4f5f5', '#b7bfbf']
};
const solid = new Set(['source', 'retry', 'integrate']);
const nodeWidth = english ? 420 : 354;
const font = english ? 'Arial, Helvetica, sans-serif' : 'Noto Sans CJK SC, PingFang SC, Microsoft YaHei, sans-serif';

function textWidth(text, size) {
  return Array.from(text).reduce((width, ch) => width + size * (ch.codePointAt(0) > 255 ? 1 : english ? 0.66 : 0.63), 0);
}

function wrapCharacters(text, size, width) {
  const lines = [];
  let line = '';
  for (const ch of Array.from(text)) {
    if (ch === '\n' || (line && textWidth(line + ch, size) > width)) {
      lines.push(line);
      line = ch === '\n' ? '' : ch;
    } else {
      line += ch;
    }
  }
  if (line) lines.push(line);
  return lines;
}

function wrap(text, size, width) {
  if (!english) return wrapCharacters(text, size, width);
  const lines = [];
  for (const paragraph of text.split('\n')) {
    let line = '';
    for (const word of paragraph.split(/\s+/).filter(Boolean)) {
      if (textWidth(word, size) > width) {
        if (line) lines.push(line);
        const chunks = wrapCharacters(word, size, width);
        lines.push(...chunks.slice(0, -1));
        line = chunks[chunks.length - 1];
      } else if (line && textWidth(line + ' ' + word, size) > width) {
        lines.push(line);
        line = word;
      } else {
        line += (line ? ' ' : '') + word;
      }
    }
    if (line) lines.push(line);
  }
  return lines;
}

function block(node) {
  const rows = [];
  const width = node.width || nodeWidth;
  let y = 27;
  for (const [text, size, bold, ink] of node.lines) {
    for (const line of wrap(text, size, width - 48)) {
      rows.push({ text: line, size, bold, ink: ink || '#243031', y });
      y += size * 1.5;
    }
    y += 6;
  }
  return { ...node, width, height: Math.ceil(y + 12), rows };
}

function number(value, decimals = 4) {
  return value == null ? '?' : Number(value).toLocaleString('en-US', { maximumFractionDigits: decimals });
}

function compactMetrics(record) {
  const v = record.verification;
  if (record.status === 'planned') return [english ? 'Not run' : '未运行'];
  if (record.status === 'invalid_config') return [english ? 'Invalid configuration' : '配置无效'];
  if (record.status === 'timeout') return [english ? 'Timed out' : '运行超时'];
  if (record.status === 'fail') {
    if (record.flags.some(flag => flag.includes('OOM'))) return [english ? 'OOM / no routed result' : 'OOM / 无布线结果'];
    return [record.functional?.csim_pass === true
      ? english ? 'Run failed / C Pass' : '运行失败 / C Pass'
      : english ? 'No passing simulation' : '仿真未通过'];
  }
  if (v.impl_WNS_ns != null) return [
    'WNS ' + (v.impl_WNS_ns >= 0 ? '+' : '') + number(v.impl_WNS_ns) + ' ns',
    'DSP ' + number(v.impl_DSP) + ' / B36 ' + number(v.impl_BRAM36),
    'LUT ' + number(v.impl_LUT) + ' / FF ' + number(v.impl_FF)
  ];
  if (v.rtl_latency_max != null) return ['RTL ' + number(v.rtl_latency_max) + ' cyc', 'RTL ' + v.rtl_status];
  const hls = record.hls;
  if (hls) {
    const primary = record.scope === 'PE'
      ? 'PE ' + number(hls.latency_cycles) + ' cyc'
      : (record.scope === 'layer' ? english ? 'Layer HLS ' : '单层 HLS ' : 'HLS ')
        + number(hls.latency_ms_est, 5) + ' ms';
    return [primary,
      'DSP ' + number(hls.DSP) + ' / B18 ' + number(hls.BRAM18K) + (hls.URAM ? ' / U ' + number(hls.URAM) : ''),
      'LUT ' + number(hls.LUT) + ' / FF ' + number(hls.FF)];
  }
  if (record.quality?.delta_vs_float_db != null) return [
    (english ? 'Avg ' : '均值 ') + 'ΔPSNR ' + number(record.quality.delta_vs_float_db) + ' dB',
    record.functional?.bit_exact ? 'C Pass / bit-exact' : 'C Pass'
  ];
  if (record.functional?.csim_pass === true) {
    const mse = record.functional.butterfly_mse;
    const result = record.functional.bit_exact ? 'C Pass / bit-exact' : 'C Pass';
    return mse == null ? [result] : ['MSE ' + Number(mse).toExponential(2), result];
  }
  return [record.run_kind === 'analysis' ? english ? 'Software analysis' : '软件分析' : english ? 'No measurement' : '无测量记录'];
}

function compactNode(record, titles) {
  const verification = record.verification;
  const sameDesign = record.run_kind === 'impl' && record.parents
    .filter(parent => parent.kind === 'verify')
    .map(parent => byId.get(parent.id))
    .some(parent => parent.functional?.csim_pass === true);
  const simulationPassed = record.functional?.csim_pass === true || verification.rtl_status === 'Pass' || !!sameDesign;
  const failed = ['fail', 'timeout', 'invalid_config'].includes(record.status);
  const faded = failed || record.status === 'planned' || (!simulationPassed && record.run_kind !== 'analysis');
  const metrics = compactMetrics(record);
  const stage = verification.impl_WNS_ns != null ? verification.timing_met ? 'routed-pass' : 'routed-fail'
    : record.run_kind === 'cosim' ? 'rtl' : record.hls ? 'hls' : record.run_kind;
  const title = titles.get(record.id)[english ? 2 : 1];
  const tooltip = [record.id + ': ' + record.title, record.change, record.issue,
    record.graph.flags, metrics.join('; '),
    english ? 'Passing C/RTL functionality does not establish routed timing. HLS times are estimates.'
      : 'C/RTL 功能通过不代表布线时序通过；HLS 时间是估计。'].join('\n');
  return block({ id: record.id, tone: record.graph.tone, width: english ? 340 : 320,
    opacity: faded ? 0.4 : 1, faded, stage, simulationPassed, tooltip,
    href: 'records' + suffix + '.md#' + record.id.toLowerCase(),
    lines: [[record.id, 19, true], [title, 17, false],
      ...metrics.map((metric, index) => [metric, index === 0 ? 18 : 14, true])] });
}

function experimentNode(record, context = false) {
  const lines = [
    [record.id + (context ? english ? ' / external parent' : ' / 外部来源' : ''), 17, true],
    [record.title, 20, true]
  ];
  if (!context) lines.push([record.change, 16, false]);
  lines.push([record.graph.result, 16, true]);
  if (!context) lines.push([record.graph.flags, 15, false, '#5c6160']);
  return block({ id: record.id, tone: context ? 'context' : record.graph.tone,
    context, href: 'records' + suffix + '.md#' + record.id.toLowerCase(), lines });
}

// Overview edges select the main causal steps; detailed graphs retain every catalog edge.
const overviewNodes = (english ? [
  ['baseline', 'E000 / starting point', 'Original float32, full maps', '522.28 M MAC / frame\nBRAM18K 11064; device has 288', 'Function passes; storage cannot fit', 'infeasible', 'precision'],
  ['precision', 'E010-E019 / E062-E071', 'Precision and independent references', '10-bit avg delta PSNR -0.0695 dB\nAll 8-bit: about -5.18 dB', '13 images; missing comic; bit-exact to fixed reference', 'analysis', 'precision'],
  ['compiler', 'E020-E029 / E032', 'Compiler directives only', 'Valid float control: about 3811 ms\nBRAM18K 11114', 'Fixing invalid keys still leaves full-map storage', 'infeasible', 'compiler'],
  ['streaming', 'E030-E033 / E047-E048', 'Network streams and line buffers', 'Remove intermediate maps: BRAM18K 168\nDSP binding and integer carriers', 'Weight selectors remain large: LUT 89304', 'infeasible', 'streaming'],
  ['scans', 'E034-E043 / E057-E067 scans', 'LUTRAM banks, unrolling, and clock', 'E043: HLS about 6.9392 ms\nDSP 505 / BRAM18K 168', 'Within resource budget; HLS timing warning', 'warning', 'scans'],
  ['micro', 'E051-E055 / E071', 'Multiplier and range controls', 'DSP / fabric / constant-weight controls', 'Primitive costs are not network results', 'analysis', 'micro'],
  ['packing', 'A / P01-P16', 'Packing: the cost of saving DSPs', 'INT8 and exact10 primitives pass\nP10-P12 networks exceed LUT budget', 'P13-P16: complete INT16; preparation only', 'infeasible', 'packing'],
  ['scatter', 'C / E050 / E060 / G01-G03', 'Conv3 scatter', 'BRAM18K 168 -> 137 -> 87\n29.83 -> 37.70 -> 44.14 ms', 'Less storage; more control and work', 'analysis', 'scatter'],
  ['memory', 'S01-S06', 'DDR probe and fused tiles', 'DDR scratch ports not exported\nB8-B64: less BRAM, halo recomputation', 'DDR invalid; tiles miss LUT/time budgets', 'infeasible', 'memory'],
  ['winograd', 'D / W01-W18', 'Winograd, continuous tiles, narrow banks', 'W18: HLS about 4.2274 ms\nDSP 326 / LUT 74480', 'Within resource budget; HLS timing warning', 'warning', 'winograd'],
  ['continuous', 'B / F01-F15', 'Continuous pipelines and fixed reads', 'LUTRAM FIFOs, online padding\nSplit windows, channel rotation, registered trees', 'Avoid pixel restarts and reduce wide selectors', 'candidate', 'continuous'],
  ['combination', 'C01-C12 / combined experiments', 'Winograd plus packing/mixed precision', 'Lowest raw estimate C11: 1.0817 ms\nLUT 248797 / FF 307525', 'Resource limits exclude it from candidate ranking', 'infeasible', 'combination'],
  ['loader', 'F16-F24', 'Output conversion and loader timing', 'F20: exact float encoding, zero DSPs\nF24: explicit 3D weight-loader indices', 'Global critical path moves to loader counters', 'warning', 'continuous'],
  ['f25', 'F25 / direct-convolution candidate', 'Disable F24 weight-loader flattening', 'HLS about 2.64226 ms / DSP 502\nBRAM18K 73 / LUT 69976', '2.5 ns still warns after clock uncertainty', 'warning', 'continuous'],
  ['verification', 'E069-E070 / F80-F91', 'Numerical, RTL, and physical checks', 'F80: 13 images; F82: two-frame RTL Pass\nF81/F84: host OOM; no routed reports', 'E070 WNS<0; physical timing and board acceptance pending', 'warning', 'verification']
] : [
  ['baseline', 'E000 / 起点', '原始浮点、完整中间图', '522.28 M MAC / frame\nBRAM18K 11064，器件仅 288', '功能成立，存储结构不可行', 'infeasible', 'precision'],
  ['precision', 'E010-E019 / E062-E071', '精度与独立参考', '10 位平均 ΔPSNR −0.0695 dB\n全 8 位约 −5.18 dB', '13 图，缺 comic；bit-exact 指定点参考', 'analysis', 'precision'],
  ['compiler', 'E020-E029 / E032', '只改编译指令', '有效浮点控制约 3811 ms\nBRAM18K 11114', '修复无效配置后，仍需改存储组织', 'infeasible', 'compiler'],
  ['streaming', 'E030-E033 / E047-E048', '整网流连接与行缓存', '中间图取消，BRAM18K 168\nDSP 绑定、整数承载', '权重选择器仍大：LUT 89304', 'infeasible', 'streaming'],
  ['scans', 'E034-E043 / E057-E067 扫描', 'LUTRAM 银行、展开与时钟', 'E043：HLS 约 6.9392 ms\nDSP 505 / BRAM18K 168', '资源合格；存在 HLS 时序告警', 'warning', 'scans'],
  ['micro', 'E051-E055 / E071', '乘法器和范围控制', 'DSP / fabric / 常数权重对照', '小内核成本不能当作整网结果', 'analysis', 'micro'],
  ['packing', 'A / P01-P16', 'Packing：省 DSP 的代价', 'INT8 与精确十位 PE 成立\nP10-P12 整网 LUT 超预算', 'P13-P16：完整 INT16，仅准备记录', 'infeasible', 'packing'],
  ['scatter', 'C / E050 / E060 / G01-G03', 'Conv3 Scatter', 'BRAM18K 168 → 137 → 87\n29.83 → 37.70 → 44.14 ms', '缓存变少，控制与额外工作变多', 'analysis', 'scatter'],
  ['memory', 'S01-S06', 'DDR 探针与分块融合', 'DDR 探针未导出 scratch 端口\nB8-B64：少 BRAM、重算 halo', '无有效 DDR；分块 LUT/时间不合格', 'infeasible', 'memory'],
  ['winograd', 'D / W01-W18', 'Winograd → 连续 tile → 窄银行', 'W18：HLS 约 4.2274 ms\nDSP 326 / LUT 74480', '资源合格；存在 HLS 时序告警', 'warning', 'winograd'],
  ['continuous', 'B / F01-F15', '连续流水与固定窗口读取', 'FIFO LUTRAM、在线补边\n双窗口流、通道轮换、注册加法树', '去像素间重启，减少宽选择器', 'candidate', 'continuous'],
  ['combination', 'C01-C12 / 组合实验', 'Winograd + Packing / 混合精度', '最快原始估计 C11：1.0817 ms\nLUT 248797 / FF 307525', '明显超量，不能按最小时间选择', 'infeasible', 'combination'],
  ['loader', 'F16-F24', '移除输出转换与加载路径瓶颈', 'F20：精确 float 编码，0 DSP\nF24：显式三维权重加载索引', '全局关键路径转到加载循环控制', 'warning', 'continuous'],
  ['f25', 'F25 / 当前直接卷积候选', '关闭 F24 的权重加载循环合并', 'HLS 约 2.64226 ms / DSP 502\nBRAM18K 73 / LUT 69976', '2.5 ns 有 uncertainty 后的时序告警', 'warning', 'continuous'],
  ['verification', 'E069-E070 / F80-F91', '数值、RTL、物理分别验收', 'F80：13 图；F82：双帧 RTL Pass\nF81/F84：主机 OOM，无 routed 报告', 'E070 WNS<0；物理时序与上板未闭环', 'warning', 'verification']
]).map(([id, label, title, result, issue, tone, section]) => block({ id, tone,
  href: section + suffix + '.svg', lines: [[label, 17, true], [title, 20, true],
    [result, 17, true], [issue, 16, false, '#5c6160']] }));
const overviewEdges = [
  ['baseline', 'precision', 'reference'], ['baseline', 'compiler', 'source'],
  ['baseline', 'streaming', 'source'], ['precision', 'streaming', 'reference'],
  ['compiler', 'streaming', 'reference'], ['streaming', 'scans', 'source'],
  ['streaming', 'micro', 'reference'], ['scans', 'packing', 'source'],
  ['micro', 'packing', 'reference'], ['scans', 'scatter', 'source'],
  ['scans', 'memory', 'source'], ['scans', 'winograd', 'source'],
  ['scans', 'continuous', 'source'], ['packing', 'combination', 'integrate'],
  ['winograd', 'combination', 'integrate'], ['continuous', 'loader', 'source'],
  ['loader', 'f25', 'source'], ['f25', 'verification', 'verify'],
  ['scans', 'verification', 'verify']
].map(([from, to, kind], index) => ({ from, to, kind, key: 'overview-' + index }));

function mermaid(nodes, edges, title) {
  const quote = value => value.replace(/"/g, '&quot;').replace(/\n/g, '<br/>');
  const lines = ['%% ' + title, fullGraph ? 'flowchart LR' : 'flowchart TB'];
  for (const node of nodes) {
    const label = node.lines.map(row => fullGraph && row[2] ? '<b>' + row[0] + '</b>' : row[0]).join('\n');
    lines.push('  ' + node.id + '["' + quote(label) + '"]');
  }
  for (const edge of edges) {
    lines.push('  ' + edge.from + (solid.has(edge.kind) ? ' -->|' : ' -.->|')
      + data.edge_kinds[edge.kind] + '| ' + edge.to);
  }
  for (const [tone, [fill, stroke]] of Object.entries(colors)) {
    lines.push('  classDef ' + tone + ' fill:' + fill + ',stroke:' + stroke + ',color:#243031');
    const selected = nodes.filter(node => node.tone === tone).map(node => node.id);
    if (selected.length) lines.push('  class ' + selected.join(',') + ' ' + tone);
  }
  if (fullGraph) {
    lines.push('  classDef faded opacity:0.4');
    lines.push('  class ' + nodes.filter(node => node.faded).map(node => node.id).join(',') + ' faded');
  }
  return lines.join('\n') + '\n';
}

function segmentHitsNode(a, b, node) {
  const left = node.x - node.width / 2 + 1, right = left + node.width - 2;
  const top = node.y - node.height / 2 + 1, bottom = top + node.height - 2;
  if (a.x === b.x) return a.x > left && a.x < right && Math.min(a.y, b.y) < bottom && Math.max(a.y, b.y) > top;
  if (a.y === b.y) return a.y > top && a.y < bottom && Math.min(a.x, b.x) < right && Math.max(a.x, b.x) > left;
  return false;
}

function orthogonal(points, nodes) {
  const result = [points[0]];
  for (let i = 1; i < points.length; i++) {
    const a = result[result.length - 1], b = points[i];
    const midY = (a.y + b.y) / 2;
    const verticalFirst = [{ x: a.x, y: b.y }, b];
    const horizontalFirst = [{ x: b.x, y: a.y }, b];
    const middle = [{ x: a.x, y: midY }, { x: b.x, y: midY }, b];
    const choices = i === points.length - 1 ? [horizontalFirst, verticalFirst, middle] : [verticalFirst, horizontalFirst, middle];
    const choice = choices.find(route => {
      const full = [a, ...route];
      return full.slice(1).every((p, index) => nodes.every(node => !segmentHitsNode(full[index], p, node)));
    });
    if (!choice) throw new Error('No clear orthogonal path between ' + JSON.stringify(a) + ' and ' + JSON.stringify(b));
    result.push(...choice);
  }
  return result.filter((p, i) => !i || p.x !== result[i - 1].x || p.y !== result[i - 1].y);
}

function render(key, title, subtitle, nodes, edges) {
  const g = new dagre.graphlib.Graph({ multigraph: true });
  g.setGraph({ rankdir: fullGraph ? 'LR' : 'TB', ranksep: fullGraph ? 110 : 96,
    nodesep: fullGraph ? 34 : 44, edgesep: 20, marginx: 48, marginy: 28 });
  g.setDefaultEdgeLabel(() => ({}));
  nodes.forEach(node => g.setNode(node.id, node));
  edges.forEach(edge => g.setEdge(edge.from, edge.to, { ...edge, weight: solid.has(edge.kind) ? 3 : 1 }, edge.key));
  dagre.layout(g);
  const width = Math.max(english ? 1250 : 920, Math.ceil(g.graph().width));
  let header = 170;
  let headerTexts;
  if (english || fullGraph) {
    headerTexts = [];
    let y = 16;
    for (const [text, size, weight, fill] of [
      [title, 27, '700', '#182c2d'], [subtitle, 17, '400', '#435654'],
      [english ? 'Solid: baseline, retry, integration. Dashed: references, controls, verification, reproduction.'
        : '实线：基线、修复、集成；虚线：参考、对照、同设计验证、复现。', 16, '400', '#526461'],
      [fullGraph
        ? english ? 'Green: current stage passes (C/RTL is not routed timing); amber: HLS timing warning; red: budget/II/configuration/routing failure; teal: analysis.'
          : '绿：当前阶段通过（C/RTL 不代表布线时序）；琥珀：HLS 时序告警；红：资源、II、配置或实现失败；青：软件分析。'
        : 'Green: stage evidence passed; red: over budget/failed; amber: timing pending; dashed border: plan; gray: external parent.', 16, '400', '#526461'],
      ...(fullGraph ? [[english ? 'Faded: failed/unrun/no functional pass. Bold: measured-stage metrics. HLS time is an estimate; B18 = BRAM18K; B36 = BRAM36; WNS = routed timing.'
        : '淡化：运行失败、未运行或无功能通过记录；加粗：本阶段指标。HLS 为时间估计；B18 / B36 区分 BRAM 单位；WNS 为实际布线时序。', 16, '400', '#526461']] : [])
    ]) {
      for (const line of wrap(text, size, width - 96)) {
        headerTexts.push('<text x="48" y="' + (y + size) + '" font-size="' + size + '" font-weight="' + weight + '" fill="' + fill + '">' + xml(line) + '</text>');
        y += size * 1.5;
      }
      y += 8;
    }
    header = Math.ceil(y + 16);
  } else {
    headerTexts = [
      '<text x="48" y="43" font-size="27" font-weight="700" fill="#182c2d">' + xml(title) + '</text>',
      '<text x="48" y="76" font-size="17" fill="#435654">' + xml(subtitle) + '</text>',
      '<text x="48" y="105" font-size="16" fill="#526461">实线：基线、修复、集成；虚线：数值依据、对照、同一设计验证、复现。</text>',
      '<text x="48" y="133" font-size="16" fill="#526461">绿：阶段证据通过；红：超预算或失败；琥珀：时序待处理；虚边：仅计划；灰：外部来源。</text>'
    ];
  }
  const height = Math.ceil(g.graph().height + header + 38);
  const pieces = ['<svg xmlns="http://www.w3.org/2000/svg" font-family="' + font + '" width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + ' ' + height + '">',
    '<title>' + xml(title) + '</title>',
    '<desc>' + xml(subtitle + (english ? '. Snapshot ' + data.source_commit + '. Experiment relationships are not Git ancestry.' : '。数据快照 ' + data.source_commit + '。实验关系不是 Git 提交历史。')) + '</desc>',
    '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="#778482"/></marker></defs>',
    '<rect x="0" y="0" width="' + width + '" height="' + height + '" fill="#ffffff"/>',
    ...headerTexts];
  const layout = { key, width, height, nodes: [], edges: [] };
  for (const edgeRef of g.edges()) {
    const edge = g.edge(edgeRef);
    const points = orthogonal(edge.points, g.nodes().map(id => g.node(id))).map(p => ({ x: p.x, y: p.y + header }));
    const d = points.map((p, i) => (i ? 'L' : 'M') + p.x.toFixed(2) + ' ' + p.y.toFixed(2)).join(' ');
    const faded = fullGraph && (g.node(edge.from).faded || g.node(edge.to).faded);
    pieces.push('<path d="' + d + '" fill="none" stroke="#778482" stroke-width="1.7"'
      + (fullGraph ? ' opacity="' + (faded ? '0.25' : solid.has(edge.kind) ? '0.85' : '0.55') + '" data-from="' + edge.from + '" data-to="' + edge.to + '"' : '')
      + (solid.has(edge.kind) ? '' : ' stroke-dasharray="6 5"') + ' marker-end="url(#arrow)"/>');
    layout.edges.push({ from: edge.from, to: edge.to, kind: edge.kind, points });
  }
  for (const id of g.nodes()) {
    const node = g.node(id);
    const x = node.x - node.width / 2, y = node.y - node.height / 2 + header;
    const [fill, stroke] = colors[node.tone];
    pieces.push('<g data-id="' + xml(id) + '"' + (fullGraph ? ' opacity="' + node.opacity + '" data-stage="' + node.stage + '" data-faded="' + node.faded + '"' : '') + '>');
    if (fullGraph) pieces.push('<title>' + xml(node.tooltip) + '</title>');
    pieces.push('<rect x="' + x.toFixed(2) + '" y="' + y.toFixed(2) + '" width="' + node.width
      + '" height="' + node.height + '" rx="4" fill="' + fill + '" stroke="' + stroke + '" stroke-width="'
      + (id === 'F25' || id === 'f25' || (fullGraph && node.stage.startsWith('routed-')) ? '3' : '1.5') + '"'
      + (node.tone === 'planned' || node.context ? ' stroke-dasharray="6 5"' : '') + '/>');
    const texts = [];
    for (const row of node.rows) {
      const text = { ...row, x: x + 24, y: y + row.y, width: textWidth(row.text, row.size) };
      pieces.push('<text x="' + text.x.toFixed(2) + '" y="' + text.y.toFixed(2) + '" font-size="'
        + row.size + '" font-weight="' + (row.bold ? '700' : '400') + '" fill="' + row.ink + '">' + xml(row.text) + '</text>');
      texts.push(text);
    }
    pieces.push('</g>');
    layout.nodes.push({ id, context: !!node.context, x, y, width: node.width, height: node.height, texts });
    if (fullGraph) Object.assign(layout.nodes[layout.nodes.length - 1], {
      tone: node.tone, faded: node.faded, stage: node.stage, simulationPassed: node.simulationPassed });
  }
  pieces.push('</svg>');
  return { svg: pieces.join('\n') + '\n', layout, mmd: mermaid(nodes, edges, title) };
}

let graphs = [{ key: 'overview', title: english ? 'SRCNN experiment overview / Baseline to F25' : 'SRCNN 实验总览 / 从原始结构到 F25',
  subtitle: english ? '153 experiments | 142 result records | 11 planned/prepared | HLS ms use max(target, estimated period)' : '153 项档案 · 142 项有结果记录 · 11 项仅计划/准备 · HLS ms 按 max(目标周期, 估计周期) 换算',
  nodes: overviewNodes, edges: overviewEdges }];
for (const section of data.sections) {
  const records = data.records.filter(record => record.section === section.key);
  const local = new Set(records.map(record => record.id));
  const context = new Set(records.flatMap(record => record.parents.map(parent => parent.id)).filter(id => !local.has(id)));
  const nodes = records.map(record => experimentNode(record)).concat(Array.from(context).sort().map(id => experimentNode(byId.get(id), true)));
  const edges = records.flatMap(record => record.parents.map((parent, index) => ({
    from: parent.id, to: record.id, kind: parent.kind, key: record.id + '-' + index
  })));
  graphs.push({ key: section.key, title: section.title, subtitle: section.question, nodes, edges });
}

if (fullGraph) {
  const compact = JSON.parse(fs.readFileSync(path.join(__dirname, 'compact-titles.json'), 'utf8'));
  const titles = new Map(compact.labels.map(row => [row[0], row]));
  if (compact.source_commit !== data.source_commit || titles.size !== data.records.length
      || compact.labels.length !== titles.size || data.records.some(record => !titles.has(record.id))) {
    throw new Error('Compact titles must match the complete snapshot with no duplicate/missing IDs.');
  }
  const nodes = data.records.map(record => compactNode(record, titles));
  const edges = data.records.flatMap(record => record.parents.map((parent, index) => ({
    from: parent.id, to: record.id, kind: parent.kind, key: record.id + '-' + index
  })));
  const dependencyGraph = new dagre.graphlib.Graph();
  nodes.forEach(node => dependencyGraph.setNode(node.id));
  edges.forEach(edge => dependencyGraph.setEdge(edge.from, edge.to));
  if (!dagre.graphlib.alg.isAcyclic(dependencyGraph)) throw new Error('Experiment dependencies contain a cycle.');
  graphs = [{ key: 'full', title: english ? 'SRCNN / Complete experiment evolution' : 'SRCNN / 全部实验演进',
    subtitle: data.records.length + (english ? ' experiments / ' : ' 项实验 / ') + edges.length
      + (english ? ' dependencies / snapshot ' : ' 条依赖 / 快照 ') + data.source_commit,
    nodes, edges }];
}

function checkLayout(layout) {
  const errors = [];
  for (const node of layout.nodes) {
    if (node.x < 0 || node.y < 0 || node.x + node.width > layout.width || node.y + node.height > layout.height) {
      errors.push(node.id + ': outside canvas');
    }
    for (const text of node.texts) {
      if (text.x < node.x + 15 || text.x + text.width > node.x + node.width - 15
          || text.y - text.size < node.y + 6 || text.y > node.y + node.height - 8) {
        errors.push(node.id + ': text outside node: ' + text.text);
      }
    }
  }
  for (let i = 0; i < layout.nodes.length; i++) {
    for (let j = i + 1; j < layout.nodes.length; j++) {
      const a = layout.nodes[i], b = layout.nodes[j];
      if (a.x < b.x + b.width && a.x + a.width > b.x && a.y < b.y + b.height && a.y + a.height > b.y) {
        errors.push(a.id + '/' + b.id + ': overlapping nodes');
      }
    }
  }
  for (const edge of layout.edges) {
    for (let i = 1; i < edge.points.length; i++) {
      const a = edge.points[i - 1], b = edge.points[i];
      if (a.x !== b.x && a.y !== b.y) errors.push(edge.from + '/' + edge.to + ': nonorthogonal edge');
      for (const node of layout.nodes) {
        const centered = { ...node, x: node.x + node.width / 2, y: node.y + node.height / 2 };
        if (segmentHitsNode(a, b, centered)) errors.push(edge.from + '/' + edge.to + ': edge crosses ' + node.id);
      }
    }
  }
  if (errors.length) throw new Error(layout.key + '\n' + errors.join('\n'));
}

const layouts = [];
const checkOnly = process.argv.includes('--check');
for (const graph of graphs) {
  const result = render(graph.key, graph.title, graph.subtitle, graph.nodes, graph.edges);
  checkLayout(result.layout);
  if (fullGraph && (result.layout.nodes.length !== data.records.length
      || new Set(result.layout.nodes.map(node => node.id)).size !== data.records.length
      || result.layout.edges.length !== data.records.reduce((count, record) => count + record.parents.length, 0))) {
    throw new Error('Full graph is missing or duplicating experiment IDs/dependencies.');
  }
  const svgPath = path.join(__dirname, graph.key + suffix + '.svg');
  const mmdPath = path.join(__dirname, graph.key + suffix + '.mmd');
  if (checkOnly) {
    if (fs.readFileSync(svgPath, 'utf8') !== result.svg || fs.readFileSync(mmdPath, 'utf8') !== result.mmd) {
      throw new Error(graph.key + ': generated diagram is stale');
    }
  } else {
    fs.writeFileSync(svgPath, result.svg);
    fs.writeFileSync(mmdPath, result.mmd);
  }
  if (fullGraph) {
    const icons = JSON.parse(fs.readFileSync(path.join(__dirname, 'viewer-icons.json'), 'utf8'));
    let html = fs.readFileSync(path.join(__dirname, 'viewer.template.html'), 'utf8');
    const replacements = {
      LANG: english ? 'en' : 'zh-CN', PAGE_TITLE: english ? 'SRCNN experiment evolution' : 'SRCNN 实验演进',
      SVG_FILE: 'full' + suffix + '.svg', SVG: result.svg,
      GRAPH_JSON: JSON.stringify({ ...result.layout, source_commit: data.source_commit }).replace(/</g, '\\u003c'),
      ICON_LICENSE: icons.source + '\n' + icons.license,
      ...Object.fromEntries(Object.entries(icons.icons).map(([name, svg]) => ['ICON_' + name, svg]))
    };
    for (const [key, value] of Object.entries(replacements)) html = html.replaceAll('[[' + key + ']]', () => value);
    if (/\[\[[A-Za-z_-]+\]\]/.test(html)) throw new Error('Unfilled viewer template placeholder');
    const htmlPath = path.join(__dirname, 'full' + suffix + '.html');
    if (checkOnly) {
      if (fs.readFileSync(htmlPath, 'utf8') !== html) throw new Error('Full graph viewer is stale');
    } else fs.writeFileSync(htmlPath, html);
  }
  layouts.push(result.layout);
}
const layoutPath = path.join(__dirname, 'layout' + (fullGraph ? '.full' : '') + suffix + '.json');
const layoutJson = JSON.stringify(layouts, null, 2) + '\n';
if (!checkOnly) fs.writeFileSync(layoutPath, layoutJson);
else if (fullGraph && fs.readFileSync(layoutPath, 'utf8') !== layoutJson) throw new Error('Full graph layout is stale');
console.log((checkOnly ? 'Checked' : 'Generated') + ' ' + graphs.length + ' ' + lang + ' graphs; '
  + (fullGraph ? data.records.length + ' unique experiments and ' + graphs[0].edges.length + ' dependencies in one graph.' : 'every experiment appears in its own route.'));
