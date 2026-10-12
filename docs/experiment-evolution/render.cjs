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
const milestoneGraph = process.argv.includes('--milestones');
if (fullGraph && milestoneGraph) throw new Error('--full and --milestones are separate diagrams.');
const viewerGraph = fullGraph || milestoneGraph;
const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'data' + suffix + '.json'), 'utf8'));
const byId = new Map(data.records.map(record => [record.id, record]));
const dependencyCount = data.records.reduce((count, record) => count + record.parents.length, 0);
const referenceClockNs = 10;
const arrowGap = 8;
const arrowLength = 14;
const arrowHalfWidth = 7;
const terminalLength = 28;
const routeClearance = 10;
const xml = value => String(value).replace(/[<>&"']/g, ch => ({
  '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&apos;'
}[ch]));
const colors = {
  candidate: ['#f0f8f3', '#458365'], warning: ['#fff7e8', '#ac7b24'],
  failure: ['#fcf0f0', '#b16868'], infeasible: ['#fcf0f0', '#b16868'],
  planned: ['#ffffff', '#939b9b'], analysis: ['#edf7f8', '#49838a'],
  context: ['#f4f5f5', '#b7bfbf'],
  ...(fullGraph ? { auxiliary: ['#f4f5f5', '#939f9b'] } : {})
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
  if (!english) {
    const lines = [];
    let line = '';
    for (const token of text.match(/[A-Za-z0-9_][A-Za-z0-9_./:+%=-]*|[\s\S]/gu) || []) {
      if (token === '\n' || (line && textWidth(line + token, size) > width)) {
        lines.push(line.trimEnd());
        line = '';
      }
      if (token === '\n') continue;
      if (textWidth(token, size) > width) {
        const chunks = wrapCharacters(token, size, width);
        lines.push(...chunks.slice(0, -1));
        line = chunks[chunks.length - 1];
      } else {
        line += token;
      }
    }
    if (line) lines.push(line.trimEnd());
    return lines;
  }
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

function acceptedCycleOverride(record) {
  const override = record.acceptance_override;
  return override?.authorized_by === 'user' && override.policy === 'upper_latency_bound_only'
    && record.verification.rtl_status === 'Pass' && record.verification.changed_params_bit_exact === true
    && Number.isFinite(override.max_cycles) && Number.isFinite(record.verification.rtl_latency_max)
    && record.verification.rtl_latency_max > 0 && record.verification.rtl_latency_max <= override.max_cycles;
}

function reportedFrameMetric(record) {
  if (record.scope !== 'frame' || ['planned', 'timeout', 'invalid_config'].includes(record.status)
      || (record.status === 'fail' && !acceptedCycleOverride(record))) return null;
  const rtl = record.verification;
  const source = rtl.rtl_status === 'Pass' && Number.isFinite(rtl.rtl_latency_max) && rtl.rtl_latency_max > 0
    ? 'rtl' : 'hls';
  const cycles = source === 'rtl' ? rtl.rtl_latency_max : record.hls?.latency_cycles;
  if (!Number.isFinite(cycles) || cycles <= 0) return null;
  return { source, latency_cycles: cycles, time_ms: cycles * referenceClockNs / 1e6 };
}

function frameMetric(record) {
  const metric = reportedFrameMetric(record);
  if (metric) return metric;
  if (record.scope !== 'frame' || ['planned', 'fail', 'timeout', 'invalid_config'].includes(record.status)) return null;
  const completed = record.functional?.csim_pass === true || record.verification.rtl_status === 'Pass'
    || (record.run_kind === 'impl' && record.verification.impl_WNS_ns != null);
  if (!completed) return null;
  // Only explicit same-design checks may cite an existing top-level report.
  const references = record.parents.filter(parent => parent.kind === 'verify')
    .map(parent => ({ id: parent.id, metric: reportedFrameMetric(byId.get(parent.id)) }))
    .filter(parent => parent.metric);
  const rtlReferences = references.filter(parent => parent.metric.source === 'rtl');
  const preferred = rtlReferences.length ? rtlReferences : references;
  if (preferred.length > 1) throw new Error('Ambiguous same-design latency: ' + record.id);
  return preferred.length ? { ...preferred[0].metric, reference_id: preferred[0].id } : null;
}

function compactMetricText(record, metric) {
  if (metric) return (metric.reference_id ? '~' : '')
    + metric.time_ms.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    + (english ? ' ms/frame' : ' ms/张') + (metric.reference_id ? ' (' + metric.reference_id + ')' : '');
  if (record.status === 'planned') return record.execution_state
    ? english ? 'Queued/running; no result' : '等待/运行中，未归档'
    : english ? 'Not run' : '未运行';
  if (record.status === 'invalid_config') return english ? 'Invalid configuration' : '配置无效';
  if (record.status === 'timeout') return english ? 'Timed out' : '运行超时';
  if (record.status === 'fail') return record.run_kind === 'impl'
    ? english ? 'No routed result' : '未得到布线结果'
    : english ? 'Run failed' : '运行失败';
  if (record.verification.impl_WNS_ns != null) return record.verification.timing_met
    ? record.scope === 'PE' ? english ? 'PE only; routed timing passes' : '仅 PE，布线时序通过'
      : english ? 'Routed timing passes; latency unmeasured' : '布线时序通过，延迟未测'
    : english ? 'Routed timing failed' : '布线时序未通过';
  if (record.scope === 'PE') return english ? 'PE only; no network latency' : '仅 PE，未测整网延迟';
  if (record.scope === 'layer') return english ? 'Layer only; no network latency' : '仅单层，未测整网延迟';
  if (record.scope === 'boundary') return english ? 'Boundary check; no network latency' : '边界验证，无整网延迟';
  if (record.functional?.csim_pass === true) return english ? 'C passes; latency unmeasured' : 'C 仿真通过，延迟未测';
  return english ? 'No network latency recorded' : '无整网延迟记录';
}

const problemLabels = new Map([
  [['E023', 'E024', 'E025'], ['指令配置键被忽略', 'Directive key ignored']],
  [['S01'], ['未导出 DDR scratch AXI 端口', 'AXI scratch ports not exported']],
  [['E014'], ['C 仿真超时', 'C simulation timed out']],
  [['E046'], ['综合锁阻止运行', 'Synthesis lock blocked run']],
  [['W04', 'W05', 'W06', 'C01', 'C02', 'C03'], ['尺寸宏与头文件冲突', 'Dimension macro/header clash']],
  [['W11', 'W12', 'W13', 'C08', 'C09', 'F03', 'F04', 'F05', 'F06', 'F07'],
    ['流位宽 8000 > 4096 bit 上限', 'Stream 8000 > 4096-bit limit']],
  [['F16', 'F17'], ['SDK / 数据类型编译失败', 'SDK/type compilation failure']],
  [['F18', 'F19'], ['目标文件重名，链接失败', 'Duplicate objects; link failed']],
  [['F88'], ['RTL 仿真被 SIGTERM 中断', 'RTL interrupted by SIGTERM']],
  [['F89'], ['布线超时（3 小时）', 'Routing timed out after 3 hours']],
  [['E011', 'E012', 'E018', 'E034', 'E035', 'C07'], ['C 编译或仿真失败', 'C compilation/simulation failed']],
  [['W26'], ['独立设计目录缺失', 'Independent design missing']],
  [['W28'], ['低于原周期下限；现已接受', 'Below old gate; accepted']]
].flatMap(([ids, labels]) => ids.map(id => [id, labels])));

function compactProblem(record) {
  if (!['failure', 'infeasible'].includes(record.graph.tone)) return null;
  const curated = problemLabels.get(record.id);
  if (curated) return curated[english ? 1 : 0];
  if (record.diagnostic_only) return (english ? 'Diagnostic: ' : '仅诊断：') + record.inherited_hls_parent
    + (english ? ' HLS LUT budget' : ' HLS LUT 超预算');
  if (record.flags.some(flag => flag.includes('OOM'))) return english ? 'Host OOM; no routed report' : '主机 OOM，无布线报告';
  if (record.flags.some(flag => flag === '主机内存保护中止' || flag === 'Host memory guard stopped the job')) {
    return english ? 'Host memory guard stopped run' : '主机内存保护中止';
  }
  if (record.verification.timing_met === false) return english ? 'Routed timing failed' : '布线时序未通过';
  const budget = record.flags.find(flag => /^(Over budget: |超预算: )/.test(flag));
  if (budget) {
    const resources = budget.slice(budget.indexOf(': ') + 2);
    return resources + (english ? ' over budget' : ' 超预算')
      + (record.hls?.ii_ok === false ? english ? '; II missed' : '；II 未达目标' : '');
  }
  if (record.hls?.ii_ok === false) return english ? 'II target missed' : 'II 未达目标';
  throw new Error('Missing specific problem label: ' + record.id);
}

function mainEdges() {
  const selected = JSON.parse(fs.readFileSync(path.join(__dirname, 'main-parents.json'), 'utf8'));
  if (selected.source_commit !== data.source_commit) throw new Error('Main-parent selection must match the snapshot.');
  for (const id of Object.keys(selected.parents)) {
    if (!byId.has(id) || byId.get(id).parents.length < 2) throw new Error('Unexpected main-parent selection: ' + id);
  }
  return data.records.flatMap(record => {
    const parents = record.parents.length > 1 ? selected.parents[record.id] : record.parents.map(parent => parent.id);
    if (!Array.isArray(parents) || (record.parents.length && !parents.length) || new Set(parents).size !== parents.length
        || parents.some(id => !record.parents.some(parent => parent.id === id))) {
      throw new Error('Missing, duplicate, or invented main parents: ' + record.id);
    }
    return parents.map((id, index) => ({ from: id, to: record.id,
      kind: record.parents.find(parent => parent.id === id).kind, key: record.id + '-' + index }));
  });
}

function compactNode(record, titles) {
  const verification = record.verification;
  const sameDesign = record.run_kind === 'impl' && record.parents
    .filter(parent => parent.kind === 'verify')
    .map(parent => byId.get(parent.id))
    .some(parent => parent.functional?.csim_pass === true);
  const simulationPassed = record.functional?.csim_pass === true || verification.rtl_status === 'Pass' || !!sameDesign;
  const failed = ['timeout', 'invalid_config'].includes(record.status)
    || (record.status === 'fail' && !acceptedCycleOverride(record));
  const faded = failed || record.status === 'planned' || (!simulationPassed && record.run_kind !== 'analysis');
  const metric = frameMetric(record);
  const metricText = compactMetricText(record, metric);
  const stage = verification.impl_WNS_ns != null ? verification.timing_met ? 'routed-pass' : 'routed-fail'
    : record.run_kind === 'cosim' ? 'rtl' : record.hls ? 'hls' : record.run_kind;
  const tone = record.graph.tone === 'candidate' && !metric ? 'auxiliary' : record.graph.tone;
  const problem = compactProblem(record);
  const title = titles.get(record.id)[english ? 2 : 1];
  const provenance = metric
    ? (metric.reference_id
      ? (english ? 'Same-design reference from ' : '引用同设计 ') + metric.reference_id
        + (english ? ' (not a new measurement): ' : '（非本实验新测量）：')
      : english ? 'Current experiment: ' : '本实验：')
      + (metric.source === 'rtl' ? english ? 'RTL maximum latency ' : 'RTL 最大延迟 '
        : english ? 'HLS top-level latency estimate ' : 'HLS 顶层延迟估计 ')
      + number(metric.latency_cycles) + (english ? ' cycles.' : ' 周期。')
    : english ? 'No valid network latency recorded in this experiment.' : '本实验没有有效的整网延迟记录。';
  const referenceWarning = metric?.reference_id && byId.get(metric.reference_id).hls_timing_warnings.length
    ? english ? 'The referenced design still has HLS timing warnings; this functional check does not resolve them.'
      : '引用设计仍有 HLS 时序告警；本次功能验证未解决这些告警。' : '';
  const routed = verification.impl_WNS_ns == null ? ''
    : (verification.timing_met ? english ? 'Routed timing passes; ' : '布线时序通过；'
      : english ? 'Routed timing fails; ' : '布线时序未通过；')
      + 'WNS ' + (verification.impl_WNS_ns >= 0 ? '+' : '') + number(verification.impl_WNS_ns) + ' ns';
  const parents = record.parents.map(parent => parent.id + ' (' + data.edge_kinds[parent.kind] + ')').join('; ');
  const tooltip = [record.id + ': ' + record.title, record.change, record.issue, record.graph.flags, routed,
    metricText, provenance, referenceWarning, (english ? 'All archive parents: ' : '全部档案来源：') + (parents || (english ? 'None' : '无')),
    english ? 'Reference: existing cycles at 100 MHz (10 ns), excluding host/DMA transfers. No 10 ns synthesis rerun or board measurement. C/RTL passes do not establish routed timing.'
      : '参考口径：现有周期数按 100 MHz（10 ns）折算，不含主机/DMA 传输。未按 10 ns 重新综合，未板端实测；C/RTL 通过不代表布线时序通过。'
  ].filter(Boolean).join('\n');
  return block({ id: record.id, tone, width: english ? 340 : 320,
    opacity: faded ? 0.4 : 1, faded, stage, simulationPassed, tooltip, metric, problem,
    href: 'records' + suffix + '.md#' + record.id.toLowerCase(),
    lines: [[record.id, 19, true], [title, 17, false],
      ...(problem ? [[problem, 14, false, '#955555']] : []),
      ...(metric || !problem ? [[metricText, metric && !problem ? 18 : 14,
        !!metric && !problem, metric && !problem ? '#243031' : '#687570']] : [])] });
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
  ['precision', 'E010-E019 / E062-E071', 'Precision and independent references', '10-bit avg delta PSNR -0.0695 dB\nAll 8-bit: about -5.18 dB', 'Complete course set: 13 images; exact fixed reference', 'analysis', 'precision'],
  ['compiler', 'E020-E029 / E032', 'Compiler directives only', 'Valid float control: about 3811 ms\nBRAM18K 11114', 'Fixing invalid keys still leaves full-map storage', 'infeasible', 'compiler'],
  ['streaming', 'E030-E033 / E047-E048', 'Network streams and line buffers', 'Remove intermediate maps: BRAM18K 168\nDSP binding and integer carriers', 'Weight selectors remain large: LUT 89304', 'infeasible', 'streaming'],
  ['scans', 'E034-E043 / E057-E067 scans', 'LUTRAM banks, unrolling, and clock', 'E043: HLS about 6.9392 ms\nDSP 505 / BRAM18K 168', 'Within resource budget; HLS timing warning', 'warning', 'scans'],
  ['micro', 'E051-E055 / E071', 'Multiplier and range controls', 'DSP / fabric / constant-weight controls', 'Primitive costs are not network results', 'analysis', 'micro'],
  ['packing', 'A / P01-P16', 'Packing: the cost of saving DSPs', 'INT8 and exact10 primitives pass\nP10-P12 networks exceed LUT budget', 'P13-P16 measured: direct mixed mapping beats INT16 packing', 'infeasible', 'packing'],
  ['scatter', 'C / E050 / E060 / G01-G03', 'Conv3 scatter', 'BRAM18K 168 -> 137 -> 87\n29.83 -> 37.70 -> 44.14 ms', 'Less storage; more control and work', 'analysis', 'scatter'],
  ['memory', 'S01-S06', 'DDR probe and fused tiles', 'DDR scratch ports not exported\nB8-B64: less BRAM, halo recomputation', 'DDR invalid; tiles miss LUT/time budgets', 'infeasible', 'memory'],
  ['winograd', 'D / W01-W18', 'Winograd, continuous tiles, narrow banks', 'W18: HLS about 4.2274 ms\nDSP 326 / LUT 74480', 'Within resource budget; HLS timing warning', 'warning', 'winograd'],
  ['continuous', 'B / F01-F15', 'Continuous pipelines and fixed reads', 'LUTRAM FIFOs, online padding\nSplit windows, channel rotation, registered trees', 'Avoid pixel restarts and reduce wide selectors', 'candidate', 'continuous'],
  ['combination', 'C01-C12 / combined experiments', 'Winograd plus packing/mixed precision', 'Lowest raw estimate C11: 1.0817 ms\nLUT 248797 / FF 307525', 'Resource limits exclude it from candidate ranking', 'infeasible', 'combination'],
  ['loader', 'F16-F24', 'Output conversion and loader timing', 'F20: exact float encoding, zero DSPs\nF24: explicit 3D weight-loader indices', 'Global critical path moves to loader counters', 'warning', 'continuous'],
  ['f25', 'F25 / direct-convolution candidate', 'Disable F24 weight-loader flattening', 'HLS about 2.64226 ms / DSP 502\nBRAM18K 73 / LUT 69976', '2.5 ns still warns after clock uncertainty', 'warning', 'continuous'],
  ['private', 'F26-F28 / private parameters', 'Stream parameters into engine-owned banks', 'F28: HLS 2.6151 ms / outside LUT 3170\nF26 area hypothesis fails; F27 misses loader-clock gate', 'F28 passes WS2; F93/F94/F95 verify reload, images, routing', 'warning', 'continuous'],
  ['t8', 'W19-W21 / F29-F30', 'Winograd T8 with subkernel-indexed cache', 'W19 misses LUT budget; W21 fits with 898 LUT spare\nDirect T8 controls still exceed budgets', 'W21: HLS 525237 cycles; F97: RTL 558758 cycles', 'warning', 'winograd'],
  ['verification', 'E069-E070 / F80-F98 / W20', 'Numerical, RTL, and physical checks', 'F93/F97: changed-parameter two-frame RTL Pass\nF92/F95/F98: independent 5 ns routing passes', 'W20 remains diagnostic; no board acceptance', 'candidate', 'verification'],
  ['w22', 'W22 / W21 integration fallback', 'Same W21 RTL, routed at 4.95 ns', 'F97 cycles at the closed target: 2.7658521 ms\nWNS +0.047 ns; retain F98 at 5 ns', 'Later W32 closes 4.5 ns on identical RTL', 'candidate', 'verification'],
  ['host', 'F32-F38 / host controls', 'Correct measured memory registrations', 'Unchanged F28/W21 designs; C checks and syntheses\nLater overlapping heavy jobs hit memory limits', 'Current policy: one heavy plus budgeted light jobs', 'analysis', 'host'],
  ['rom', 'F35 / W24-W25 / W29-W31', 'Fixed ROM removes parameter path', 'Exact banks; 13 images and changed-input RTL pass\nRTL 554226 cycles; HLS 630 DSP / 53316 LUT', 'W29 memory guard; W31 has no archived result', 'warning', 'rom'],
  ['clock', 'W23-W32 / F39-F43-F49-F52', 'Route strategies and Conv3 operand registers', 'W32 / F52 both close 4.5 ns\n558758 RTL cycles: 2.514411 ms/frame', 'Route gates pass; earlier OOM/guard failures retained', 'candidate', 'clock-fifo'],
  ['fifo', 'F40-F48 / F50-F51', 'Buffer transformed windows at depth 16', 'Feature FIFO16/32: no cycle benefit\nF48: 535771 cycles; saves 22987 vs F97', '30-cycle miss is diagnostic; user accepts T8 basis', 'candidate', 'clock-fifo'],
  ['frp', 'W26-W30', 'Free-running MAC fold pipelines', 'W28: exact reload RTL, 549438 cycles\nW30 closes 4.5 ns: 2.472471 ms/frame', 'Route gates pass; original W28 fail and later acceptance retained', 'candidate', 'clock-fifo'],
  ['t4', 'C13-C15 / C18', 'T4 prepack Conv2 during runtime loading', 'C14: 300632 RTL cycles; C18 closes 5 ns\n1.503160 ms/frame / 1032 DSP / 58529 routed LUT', 'E065 mixed precision; route gates pass, no board result', 'candidate', 't4'],
  ['next', 'C16-C17 / pending combinations', 'T8 FIFO16 + FRP; T4 window FIFO32', 'Started plans without archived result rows\nAll-image, reload RTL and routing still required', 'Individual gains and physical closure cannot be inherited', 'planned', 'clock-fifo']
] : [
  ['baseline', 'E000 / 起点', '原始浮点、完整中间图', '522.28 M MAC / frame\nBRAM18K 11064，器件仅 288', '功能成立，存储结构不可行', 'infeasible', 'precision'],
  ['precision', 'E010-E019 / E062-E071', '精度与独立参考', '10 位平均 ΔPSNR −0.0695 dB\n全 8 位约 −5.18 dB', '课程完整测试集为 13 图；逐位对照定点参考', 'analysis', 'precision'],
  ['compiler', 'E020-E029 / E032', '只改编译指令', '有效浮点控制约 3811 ms\nBRAM18K 11114', '修复无效配置后，仍需改存储组织', 'infeasible', 'compiler'],
  ['streaming', 'E030-E033 / E047-E048', '整网流连接与行缓存', '中间图取消，BRAM18K 168\nDSP 绑定、整数承载', '权重选择器仍大：LUT 89304', 'infeasible', 'streaming'],
  ['scans', 'E034-E043 / E057-E067 扫描', 'LUTRAM 银行、展开与时钟', 'E043：HLS 约 6.9392 ms\nDSP 505 / BRAM18K 168', '资源合格；存在 HLS 时序告警', 'warning', 'scans'],
  ['micro', 'E051-E055 / E071', '乘法器和范围控制', 'DSP / fabric / 常数权重对照', '小内核成本不能当作整网结果', 'analysis', 'micro'],
  ['packing', 'A / P01-P16', 'Packing：省 DSP 的代价', 'INT8 与精确十位 PE 成立\nP10-P12 整网 LUT 超预算', 'P13-P16 已测：普通混合映射优于完整 INT16 Packing', 'infeasible', 'packing'],
  ['scatter', 'C / E050 / E060 / G01-G03', 'Conv3 Scatter', 'BRAM18K 168 → 137 → 87\n29.83 → 37.70 → 44.14 ms', '缓存变少，控制与额外工作变多', 'analysis', 'scatter'],
  ['memory', 'S01-S06', 'DDR 探针与分块融合', 'DDR 探针未导出 scratch 端口\nB8-B64：少 BRAM、重算 halo', '无有效 DDR；分块 LUT/时间不合格', 'infeasible', 'memory'],
  ['winograd', 'D / W01-W18', 'Winograd → 连续 tile → 窄银行', 'W18：HLS 约 4.2274 ms\nDSP 326 / LUT 74480', '资源合格；存在 HLS 时序告警', 'warning', 'winograd'],
  ['continuous', 'B / F01-F15', '连续流水与固定窗口读取', 'FIFO LUTRAM、在线补边\n双窗口流、通道轮换、注册加法树', '去像素间重启，减少宽选择器', 'candidate', 'continuous'],
  ['combination', 'C01-C12 / 组合实验', 'Winograd + Packing / 混合精度', '最快原始估计 C11：1.0817 ms\nLUT 248797 / FF 307525', '明显超量，不能按最小时间选择', 'infeasible', 'combination'],
  ['loader', 'F16-F24', '移除输出转换与加载路径瓶颈', 'F20：精确 float 编码，0 DSP\nF24：显式三维权重加载索引', '全局关键路径转到加载循环控制', 'warning', 'continuous'],
  ['f25', 'F25 / 当前直接卷积候选', '关闭 F24 的权重加载循环合并', 'HLS 约 2.64226 ms / DSP 502\nBRAM18K 73 / LUT 69976', '2.5 ns 有 uncertainty 后的时序告警', 'warning', 'continuous'],
  ['private', 'F26-F28 / 私有参数', '参数流接入各层私有权重银行', 'F28：HLS 2.6151 ms / 区外 LUT 3170\nF26 面积假设失败，F27 未达加载器时钟门槛', 'F28 达 WS2 门槛；F93/F94/F95 验证重载、多图、布线', 'warning', 'continuous'],
  ['t8', 'W19-W21 / F29-F30', 'Winograd T8，缓存按子卷积索引', 'W19 LUT 超预算；W21 剩 898 LUT 余量\n直接卷积 T8 对照仍超预算', 'W21：HLS 525237 周期；F97：RTL 558758 周期', 'warning', 'winograd'],
  ['verification', 'E069-E070 / F80-F98 / W20', '数值、RTL、物理分别验收', 'F93/F97：换参数双帧 RTL Pass\nF92/F95/F98：独立 5 ns 布线通过', 'W20 仍仅诊断；板端验收未完成', 'candidate', 'verification'],
  ['w22', 'W22 / W21 集成后备', '相同 W21 RTL，4.95 ns 布线', 'F97 周期按通过目标折算：2.7658521 ms\nWNS +0.047 ns；保留 F98 的 5 ns 后备', '后续 W32 已使相同 RTL 在 4.5 ns 收敛', 'candidate', 'verification'],
  ['host', 'F32-F38 / 主机对照', '按实测峰值修正内存登记', 'F28/W21 设计不变，并行 C 仿真与综合\n后续两重任务重叠触发内存失败', '当前：一个重任务加预算内轻任务', 'analysis', 'host'],
  ['rom', 'F35 / W24-W25 / W29-W31', '固定 ROM，移除参数通路', '银行等价、13 图和换输入 RTL 通过\nRTL 554226 周期；HLS 630 DSP / 53316 LUT', 'W29 被内存保护中止；W31 尚无归档结果', 'warning', 'rom'],
  ['clock', 'W23-W32 / F39-F43-F49-F52', '物理策略与 Conv3 操作数寄存', 'W32 / F52 均在 4.5 ns 收敛\n558758 RTL 周期：2.514411 ms/张', '布线门限通过；原 OOM/内存保护失败保留', 'candidate', 'clock-fifo'],
  ['fifo', 'F40-F48 / F50-F51', '变换窗口 FIFO 加深到 16', '层间特征 FIFO16/32 不减周期\nF48：535771 周期，比 F97 少 22987', '原 2% 目标差 30 周期；用户接受为 T8 依据', 'candidate', 'clock-fifo'],
  ['frp', 'W26-W30', 'MAC fold 使用 FRP 流水', 'W28 换参数 RTL 精确，549438 周期\nW30：4.5 ns 收敛，2.472471 ms/张', '布线门限通过；W28 原失败与后续授权保留', 'candidate', 'clock-fifo'],
  ['t4', 'C13-C15 / C18', 'T4 在运行时加载阶段预拼 Conv2', 'C14：300632 周期；C18：5 ns 收敛\n1.503160 ms/张 / 1032 DSP / 布线 LUT 58529', 'E065 混合精度；布线门限通过，未板测', 'candidate', 't4'],
  ['next', 'C16-C17 / 待验收组合', 'T8 窗口16加 FRP；T4 窗口32', '计划已启动，尚无归档结果行\n仍需多图、换参数 RTL 和独立布线', '单项收益不能相加，物理通过不能继承', 'planned', 'clock-fifo']
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
  ['scans', 'verification', 'verify'], ['f25', 'private', 'source'],
  ['private', 't8', 'integrate'], ['winograd', 't8', 'source'],
  ['private', 'verification', 'verify'], ['t8', 'verification', 'verify'],
  ['verification', 'w22', 'retry'], ['t8', 'host', 'compare'],
  ['t8', 'rom', 'source'], ['w22', 'clock', 'verify'], ['host', 'clock', 'reference'],
  ['t8', 'fifo', 'source'], ['t8', 'frp', 'source'], ['t8', 't4', 'source'],
  ['packing', 't4', 'reference'], ['precision', 't4', 'reference'],
  ['fifo', 'next', 'integrate'], ['frp', 'next', 'integrate'], ['t4', 'next', 'source']
].map(([from, to, kind], index) => ({ from, to, kind, key: 'overview-' + index }));

function mermaid(nodes, edges, title) {
  const quote = value => value.replace(/"/g, '&quot;').replace(/\n/g, '<br/>');
  const lines = ['%% ' + title, fullGraph ? 'flowchart LR' : 'flowchart TB'];
  for (const node of nodes) {
    const label = node.lines.map(row => fullGraph && row[2] ? '<b>' + row[0] + '</b>' : row[0]).join('\n');
    lines.push('  ' + node.id + '["' + quote(label) + '"]');
  }
  for (const edge of edges) {
    lines.push(fullGraph ? '  ' + edge.from + ' ==> ' + edge.to
      : '  ' + edge.from + (solid.has(edge.kind) ? ' -->|' : ' -.->|')
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
    lines.push('  linkStyle default stroke:#62756f,stroke-width:3.4px');
    const fadedEdges = edges.map((edge, index) => nodes.find(node => node.id === edge.from).faded
      || nodes.find(node => node.id === edge.to).faded ? index : null).filter(index => index != null);
    if (fadedEdges.length) lines.push('  linkStyle ' + fadedEdges.join(',') + ' opacity:0.25');
  }
  return lines.join('\n') + '\n';
}

function segmentHitsNode(a, b, node, padding = 0) {
  const left = node.x - node.width / 2 - padding, right = node.x + node.width / 2 + padding;
  const top = node.y - node.height / 2 - padding, bottom = node.y + node.height / 2 + padding;
  if (a.x === b.x) return a.x > left && a.x < right && Math.min(a.y, b.y) < bottom && Math.max(a.y, b.y) > top;
  if (a.y === b.y) return a.y > top && a.y < bottom && Math.min(a.x, b.x) < right && Math.max(a.x, b.x) > left;
  return false;
}

function clearRoute(points, nodes, padding = routeClearance) {
  return points.slice(1).every((point, i) => nodes.every(node => !segmentHitsNode(points[i], point, node, padding)));
}

function simplifyRoute(points) {
  const result = [];
  for (const point of points) {
    const last = result[result.length - 1];
    if (last && last.x === point.x && last.y === point.y) continue;
    const before = result[result.length - 2];
    if (before && ((before.x === last.x && last.x === point.x && (last.y - before.y) * (point.y - last.y) >= 0)
      || (before.y === last.y && last.y === point.y && (last.x - before.x) * (point.x - last.x) >= 0))) {
      result.pop();
    }
    result.push(point);
  }
  return result;
}

function pointHitsNode(point, node, padding = routeClearance) {
  return Math.abs(point.x - node.x) < node.width / 2 + padding
    && Math.abs(point.y - node.y) < node.height / 2 + padding;
}

function detour(a, b, nodes) {
  const xs = [...new Set([a.x, b.x, ...nodes.flatMap(node => [node.x - node.width / 2 - routeClearance - 1,
    node.x + node.width / 2 + routeClearance + 1])])];
  const ys = [...new Set([a.y, b.y, ...nodes.flatMap(node => [node.y - node.height / 2 - routeClearance - 1,
    node.y + node.height / 2 + routeClearance + 1])])];
  const candidates = xs.map(x => [a, { x, y: a.y }, { x, y: b.y }, b])
    .concat(ys.map(y => [a, { x: a.x, y }, { x: b.x, y }, b]));
  const length = route => route.slice(1).reduce((sum, point, i) => sum
    + Math.abs(point.x - route[i].x) + Math.abs(point.y - route[i].y), 0);
  candidates.sort((first, second) => length(first) - length(second));
  const simple = candidates.find(route => clearRoute(route, nodes));
  if (simple) return simple.slice(1);

  // A local visibility grid handles channels requiring more than two bends.
  for (const margin of [96, 384]) {
    const gridX = xs.filter(x => x >= Math.min(a.x, b.x) - margin && x <= Math.max(a.x, b.x) + margin).sort((x, y) => x - y);
    const gridY = ys.filter(y => y >= Math.min(a.y, b.y) - margin && y <= Math.max(a.y, b.y) + margin).sort((x, y) => x - y);
    const graph = new dagre.graphlib.Graph();
    const columns = new Map();
    for (let iy = 0; iy < gridY.length; iy++) {
      let previous;
      for (let ix = 0; ix < gridX.length; ix++) {
        const point = { x: gridX[ix], y: gridY[iy] };
        if (nodes.some(node => pointHitsNode(point, node))) continue;
        const id = ix + ':' + iy;
        graph.setNode(id, point);
        for (const neighbor of [previous, columns.get(ix)].filter(Boolean)) {
          const other = graph.node(neighbor);
          if (!clearRoute([other, point], nodes)) continue;
          const distance = Math.abs(other.x - point.x) + Math.abs(other.y - point.y);
          graph.setEdge(neighbor, id, distance);
          graph.setEdge(id, neighbor, distance);
        }
        previous = id;
        columns.set(ix, id);
      }
    }
    const start = gridX.indexOf(a.x) + ':' + gridY.indexOf(a.y);
    const end = gridX.indexOf(b.x) + ':' + gridY.indexOf(b.y);
    if (!graph.hasNode(start) || !graph.hasNode(end)) continue;
    const distances = dagre.graphlib.alg.dijkstra(graph, start, edge => graph.edge(edge));
    if (!Number.isFinite(distances[end].distance)) continue;
    const route = [];
    for (let id = end; id !== start; id = distances[id].predecessor) route.unshift(graph.node(id));
    return route;
  }
  throw new Error('No clear orthogonal channel between ' + JSON.stringify(a) + ' and ' + JSON.stringify(b));
}

function orthogonal(points, nodes) {
  const result = [points[0]];
  for (let i = 1; i < points.length; i++) {
    const a = result[result.length - 1], b = points[i];
    const midY = (a.y + b.y) / 2;
    const midX = (a.x + b.x) / 2;
    const verticalFirst = [{ x: a.x, y: b.y }, b];
    const horizontalFirst = [{ x: b.x, y: a.y }, b];
    const middle = [{ x: a.x, y: midY }, { x: b.x, y: midY }, b];
    const middleX = [{ x: midX, y: a.y }, { x: midX, y: b.y }, b];
    const choices = fullGraph ? [horizontalFirst, verticalFirst, middleX, middle]
      : [verticalFirst, horizontalFirst, middle, middleX];
    const choice = choices.find(route => {
      return clearRoute([a, ...route], nodes);
    });
    result.push(...(choice || detour(a, b, nodes)));
  }
  return simplifyRoute(result);
}

function routeEdge(edge, graph) {
  const source = graph.node(edge.from), target = graph.node(edge.to);
  const nodes = graph.nodes().map(id => graph.node(id));
  const incoming = graph.inEdges(edge.to).sort((first, second) => {
    const a = graph.node(first.v), b = graph.node(second.v);
    return (fullGraph ? a.y - b.y : a.x - b.x) || first.name.localeCompare(second.name);
  });
  const index = incoming.findIndex(ref => ref.name === edge.key);
  const span = (fullGraph ? target.height : target.width) - 40;
  const offset = span * ((index + 1) / (incoming.length + 1) - 0.5);
  const first = edge.points[0];
  const start = fullGraph
    ? { x: source.x + source.width / 2 + arrowGap, y: Math.max(source.y - source.height / 2 + 20,
      Math.min(source.y + source.height / 2 - 20, first.y)) }
    : { x: Math.max(source.x - source.width / 2 + 20, Math.min(source.x + source.width / 2 - 20, first.x)),
      y: source.y + source.height / 2 + arrowGap };
  const end = fullGraph ? { x: target.x - target.width / 2 - arrowGap, y: target.y + offset }
    : { x: target.x + offset, y: target.y - target.height / 2 - arrowGap };
  const startStub = fullGraph ? { x: start.x + terminalLength, y: start.y } : { x: start.x, y: start.y + terminalLength };
  const endStub = fullGraph ? { x: end.x - terminalLength, y: end.y } : { x: end.x, y: end.y - terminalLength };
  const guides = edge.points.slice(1, -1).filter(point => !nodes.some(node => pointHitsNode(point, node)));
  return simplifyRoute([start, ...orthogonal([startStub, ...guides, endStub], nodes), end]);
}

function render(key, title, subtitle, nodes, edges) {
  const g = new dagre.graphlib.Graph({ multigraph: true });
  g.setGraph({ rankdir: fullGraph ? 'LR' : 'TB', ranksep: fullGraph ? 110 : milestoneGraph ? 64 : 96,
    nodesep: fullGraph ? 34 : 44, edgesep: 20, marginx: 48, marginy: 28 });
  g.setDefaultEdgeLabel(() => ({}));
  nodes.forEach(node => g.setNode(node.id, node));
  edges.forEach(edge => g.setEdge(edge.from, edge.to, { ...edge, weight: fullGraph || solid.has(edge.kind) ? 3 : 1 }, edge.key));
  dagre.layout(g);
  const routed = g.edges().map(ref => ({ edge: g.edge(ref), points: routeEdge(g.edge(ref), g) }));
  const allPoints = routed.flatMap(route => route.points);
  const minimumX = Math.min(0, ...allPoints.map(point => point.x));
  const minimumY = Math.min(0, ...allPoints.map(point => point.y));
  const shiftX = minimumX < 0 ? 24 - minimumX : 0;
  const shiftY = minimumY < 0 ? 28 - minimumY : 0;
  const width = Math.max(milestoneGraph ? english ? 600 : 500 : english ? 1250 : 920, Math.ceil(shiftX
    + Math.max(g.graph().width, ...allPoints.map(point => point.x + 24))));
  let header = 170;
  let headerTexts;
  if (milestoneGraph) {
    headerTexts = [];
    let y = 16;
    for (const [text, size, weight, fill] of [
      [title, 27, '700', '#182c2d'], [subtitle, 16, '400', '#435654']
    ]) {
      for (const line of wrap(text, size, width - 96)) {
        headerTexts.push('<text x="48" y="' + (y + size) + '" font-size="' + size + '" font-weight="' + weight + '" fill="' + fill + '">' + xml(line) + '</text>');
        y += size * 1.5;
      }
      y += 8;
    }
    header = Math.ceil(y + 16);
  } else if (english || fullGraph) {
    headerTexts = [];
    let y = 16;
    for (const [text, size, weight, fill] of [
      [title, 27, '700', '#182c2d'], [subtitle, 17, '400', '#435654'],
      [fullGraph
        ? english ? 'Thick solid arrows: main optimization relationships. Multiple parents only where needed; all archive relationships remain in the ledger.'
          : '加粗实线：主要优化演进；必要时保留多个来源。完整档案关系见逐项记录。'
        : english ? 'Solid: baseline, retry, integration. Dashed: references, controls, verification, reproduction.'
          : '实线：基线、修复、集成；虚线：参考、对照、同设计验证、复现。', 16, '400', '#526461'],
      [fullGraph
        ? english ? 'Green: current stage passes with network latency; amber: HLS timing warning; red: specific problem shown; gray: auxiliary; teal: analysis.'
          : '绿：当前阶段通过且有整网耗时；琥珀：HLS 时序告警；红：注明具体问题；灰：辅助实验；青：分析。'
        : 'Green: stage evidence passed; red: over budget/failed; amber: timing pending; dashed border: plan; gray: external parent.', 16, '400', '#526461'],
      ...(fullGraph ? [[english ? 'Bold: comparable network ms/frame at 100 MHz; red times are not bold. ~ plus ID: estimate cited from the same design.'
        : '加粗：100 MHz 参考整网 ms/张；红色耗时不加粗。~ 和编号：引用同一设计的报告估计。', 16, '400', '#526461'],
      [english ? 'Existing HLS/RTL cycles only; no 10 ns synthesis rerun or board measurement; host/DMA excluded. Green does not establish routed timing.'
        : '现有 HLS/RTL 周期折算；未按 10 ns 重新综合或板端实测，不含主机/DMA。绿色不代表布线时序通过。', 16, '400', '#526461'],
      [english ? 'Faded: failed/unrun/no passing functionality. Auxiliary labels state C/PE/layer scope; hover for provenance and verification status.'
        : '淡化：失败、未运行或无功能通过记录。辅助节点注明 C/PE/单层范围；来源与验证状态见悬停提示。', 16, '400', '#526461']] : [])
    ]) {
      for (const line of wrap(text, size, fullGraph ? 650 : width - 96)) {
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
  const height = Math.ceil(shiftY + header + 38 + Math.max(g.graph().height, ...allPoints.map(point => point.y + 28)));
  const pieces = ['<svg xmlns="http://www.w3.org/2000/svg" font-family="' + font + '" width="' + width + '" height="' + height + '" viewBox="0 0 ' + width + ' ' + height + '">',
    '<title>' + xml(title) + '</title>',
    '<desc>' + xml(subtitle + (english ? '. Snapshot ' + data.source_commit + '. Experiment relationships are not Git ancestry.' : '。数据快照 ' + data.source_commit + '。实验关系不是 Git 提交历史。')) + '</desc>',
    '<defs><marker id="arrow" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" refX="14" refY="7" orient="auto"><path d="M0 0 L14 7 L0 14 Z" fill="' + (viewerGraph ? '#62756f' : '#778482') + '"/></marker></defs>',
    '<rect x="0" y="0" width="' + width + '" height="' + height + '" fill="#ffffff"/>',
    ...headerTexts];
  const layout = { key, width, height, nodes: [], edges: [] };
  if (fullGraph) Object.assign(layout, { reference_clock_ns: referenceClockNs, archive_dependency_count: dependencyCount });
  for (const route of routed) {
    const edge = route.edge;
    const points = route.points.map(p => ({ x: p.x + shiftX, y: p.y + header + shiftY }));
    const d = points.map((p, i) => (i ? 'L' : 'M') + p.x.toFixed(2) + ' ' + p.y.toFixed(2)).join(' ');
    const faded = fullGraph && (g.node(edge.from).faded || g.node(edge.to).faded);
    pieces.push('<path d="' + d + '" fill="none" stroke="' + (viewerGraph ? '#62756f' : '#778482')
      + '" stroke-width="' + (viewerGraph ? '3.4' : '1.7') + '"'
      + (viewerGraph ? ' opacity="' + (faded ? '0.25' : '0.9') + '" data-from="' + edge.from + '" data-to="' + edge.to + '"' : '')
      + (viewerGraph || solid.has(edge.kind) ? '' : ' stroke-dasharray="6 5"') + ' marker-end="url(#arrow)"'
      + (viewerGraph ? '><title>' + xml(edge.from + ' → ' + edge.to + ': '
        + (milestoneGraph ? english ? 'milestone sequence' : '里程碑顺序' : data.edge_kinds[edge.kind])) + '</title></path>' : '/>'));
    const tip = points[points.length - 1];
    layout.edges.push({ from: edge.from, to: edge.to, kind: edge.kind, points,
      arrow: fullGraph ? { x: tip.x - arrowLength, y: tip.y - arrowHalfWidth, width: arrowLength, height: arrowHalfWidth * 2 }
        : { x: tip.x - arrowHalfWidth, y: tip.y - arrowLength, width: arrowHalfWidth * 2, height: arrowLength } });
  }
  for (const id of g.nodes()) {
    const node = g.node(id);
    const x = node.x - node.width / 2 + shiftX, y = node.y - node.height / 2 + header + shiftY;
    const [fill, stroke] = colors[node.tone];
    pieces.push('<g data-id="' + xml(id) + '"' + (fullGraph ? ' opacity="' + node.opacity + '" data-stage="' + node.stage + '" data-faded="' + node.faded + '"' : '') + '>');
    if (viewerGraph) pieces.push('<title>' + xml(node.tooltip) + '</title>');
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
    if (milestoneGraph) Object.assign(layout.nodes[layout.nodes.length - 1], {
      tone: node.tone, aliases: node.aliases, evidence_ids: node.aliases });
    if (fullGraph) Object.assign(layout.nodes[layout.nodes.length - 1], {
      tone: node.tone, faded: node.faded, stage: node.stage, simulationPassed: node.simulationPassed,
      metric: node.metric, problem: node.problem });
  }
  pieces.push('</svg>');
  return { svg: pieces.join('\n') + '\n', layout, mmd: mermaid(nodes, edges, title) };
}

let graphs = [{ key: 'overview', title: english ? 'SRCNN experiment overview / Baseline to C18' : 'SRCNN 实验总览 / 从原始结构到 C18',
  subtitle: data.counts.experiments + (english ? ' experiments / ' : ' 项档案 / ') + data.counts.with_result_record
    + (english ? ' result records / ' : ' 项有结果记录 / ') + data.counts.plan_only
    + (english ? ' planned / HLS times retain report clocks; routed times use closed targets'
      : ' 项仅计划 / HLS 时间沿用报告时钟；布线时间按通过目标折算'),
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
  const edges = mainEdges();
  const dependencyGraph = new dagre.graphlib.Graph();
  nodes.forEach(node => dependencyGraph.setNode(node.id));
  edges.forEach(edge => dependencyGraph.setEdge(edge.from, edge.to));
  if (!dagre.graphlib.alg.isAcyclic(dependencyGraph)) throw new Error('Experiment dependencies contain a cycle.');
  graphs = [{ key: 'full', title: english ? 'SRCNN / Complete experiment evolution' : 'SRCNN / 全部实验演进',
    subtitle: data.records.length + (english ? ' experiments / ' : ' 项实验 / ') + edges.length
      + (english ? ' main links / 100 MHz reference / snapshot ' : ' 条主要连线 / 100 MHz 参考时钟 / 快照 ') + data.source_commit,
    nodes, edges }];
}

if (milestoneGraph) {
  const milestones = JSON.parse(fs.readFileSync(path.join(__dirname, 'milestones.json'), 'utf8'));
  if (milestones.source_commit !== data.source_commit || milestones.nodes.length !== 10
      || new Set(milestones.nodes.map(node => node.id)).size !== 10) {
    throw new Error('Milestones must retain ten unique stages from the frozen snapshot.');
  }
  const nodes = milestones.nodes.map(entry => {
    if (!byId.has(entry.id) || entry.evidence_ids.some(id => !byId.has(id))) {
      throw new Error('Milestone has an unknown archived ID: ' + entry.id);
    }
    const content = entry[lang];
    const problem = ['failure', 'infeasible'].includes(entry.tone);
    return block({ id: entry.id, tone: entry.tone, width: english ? 420 : 360,
      aliases: entry.evidence_ids,
      tooltip: content.label + '\n' + content.title + '\n' + content.result,
      lines: [[content.label, 17, true], [content.title, 20, true],
        [content.result, problem ? 14 : 18, !problem, problem ? '#b16868' : '#243031']] });
  });
  const edges = nodes.slice(1).map((node, index) => ({ from: nodes[index].id, to: node.id,
    kind: 'source', key: 'milestone-' + index }));
  graphs = [{ key: 'milestones', title: milestones.title[lang], subtitle: milestones.subtitle[lang], nodes, edges }];
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
    const target = layout.nodes.find(node => node.id === edge.to);
    const last = edge.points[edge.points.length - 1], before = edge.points[edge.points.length - 2];
    const gap = fullGraph ? target.x - last.x : target.y - last.y;
    const straight = fullGraph ? last.x - before.x : last.y - before.y;
    if (gap < arrowGap - 0.01 || straight < terminalLength || (fullGraph ? before.y !== last.y : before.x !== last.x)) {
      errors.push(edge.from + '/' + edge.to + ': arrow lacks a clear perpendicular terminal');
    }
    for (const node of layout.nodes) {
      const arrow = edge.arrow;
      if (arrow.x < node.x + node.width + 2 && arrow.x + arrow.width > node.x - 2
          && arrow.y < node.y + node.height + 2 && arrow.y + arrow.height > node.y - 2) {
        errors.push(edge.from + '/' + edge.to + ': arrow overlaps ' + node.id);
      }
    }
    for (let i = 1; i < edge.points.length; i++) {
      const a = edge.points[i - 1], b = edge.points[i];
      if (a.x !== b.x && a.y !== b.y) errors.push(edge.from + '/' + edge.to + ': nonorthogonal edge');
      if ([a, b].some(point => point.x < 0 || point.y < 0 || point.x > layout.width || point.y > layout.height)) {
        errors.push(edge.from + '/' + edge.to + ': edge outside canvas');
      }
      for (const node of layout.nodes) {
        const centered = { ...node, x: node.x + node.width / 2, y: node.y + node.height / 2 };
        if (segmentHitsNode(a, b, centered, 6)) errors.push(edge.from + '/' + edge.to + ': edge lacks clearance from ' + node.id);
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
      || result.layout.edges.length !== graph.edges.length
      || new Set(result.layout.edges.map(edge => edge.from + '/' + edge.to)).size !== graph.edges.length)) {
    throw new Error('Full graph is missing or duplicating experiment IDs/main relationships.');
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
  if (viewerGraph) {
    const icons = JSON.parse(fs.readFileSync(path.join(__dirname, 'viewer-icons.json'), 'utf8'));
    let html = fs.readFileSync(path.join(__dirname, 'viewer.template.html'), 'utf8');
    const replacements = {
      LANG: english ? 'en' : 'zh-CN', PAGE_TITLE: milestoneGraph
        ? english ? 'SRCNN key milestones' : 'SRCNN 关键里程碑'
        : english ? 'SRCNN experiment evolution' : 'SRCNN 实验演进',
      NODE_COUNT: result.layout.nodes.length, EDGE_COUNT: result.layout.edges.length,
      SVG_FILE: graph.key + suffix + '.svg', SVG: result.svg,
      GRAPH_JSON: JSON.stringify({ ...result.layout, source_commit: data.source_commit }).replace(/</g, '\\u003c'),
      ICON_LICENSE: icons.source + '\n' + icons.license,
      ...Object.fromEntries(Object.entries(icons.icons).map(([name, svg]) => ['ICON_' + name, svg]))
    };
    for (const [key, value] of Object.entries(replacements)) html = html.replaceAll('[[' + key + ']]', () => value);
    if (/\[\[[A-Za-z_-]+\]\]/.test(html)) throw new Error('Unfilled viewer template placeholder');
    const htmlPath = path.join(__dirname, graph.key + suffix + '.html');
    if (checkOnly) {
      if (fs.readFileSync(htmlPath, 'utf8') !== html) throw new Error('Full graph viewer is stale');
    } else fs.writeFileSync(htmlPath, html);
  }
  layouts.push(result.layout);
}
const layoutPath = path.join(__dirname, 'layout' + (fullGraph ? '.full' : milestoneGraph ? '.milestones' : '') + suffix + '.json');
const layoutJson = JSON.stringify(layouts, null, 2) + '\n';
if (!checkOnly) fs.writeFileSync(layoutPath, layoutJson);
else if (viewerGraph && fs.readFileSync(layoutPath, 'utf8') !== layoutJson) throw new Error('Viewer graph layout is stale');
console.log((checkOnly ? 'Checked' : 'Generated') + ' ' + graphs.length + ' ' + lang + ' graphs; '
  + (fullGraph ? data.records.length + ' unique experiments and ' + graphs[0].edges.length + ' main relationships in one graph.'
    : milestoneGraph ? 'ten selected milestones; original experiment results remain frozen.' : 'every experiment appears in its own route.'));
