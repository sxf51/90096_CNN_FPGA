const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const outputIndex = process.argv.indexOf('--output');
const output = outputIndex < 0 ? '/tmp/srcnn-evolution-check' : process.argv[outputIndex + 1];
fs.mkdirSync(output, { recursive: true });
const read = name => JSON.parse(fs.readFileSync(path.join(__dirname, name), 'utf8'));
const layouts = ['layout.json', 'layout.en.json', 'layout.full.json', 'layout.full.en.json',
  'layout.milestones.json', 'layout.milestones.en.json']
  .flatMap(name => read(name).map(layout => ({ ...layout, english: name.includes('.en.') })));
const chinese = read('data.json'), english = read('data.en.json');
const fields = ['id', 'parents', 'status', 'execution_state', 'hls', 'functional', 'verification', 'acceptance_override'];
assert.deepEqual(chinese.records.map(record => fields.map(field => record[field])),
  english.records.map(record => fields.map(field => record[field])));
const byId = new Map(chinese.records.map(record => [record.id, record]));
for (const layout of layouts.filter(layout => layout.key === 'full')) {
  assert.equal(new Set(layout.nodes.map(node => node.id)).size, byId.size);
  assert.deepEqual(layout.nodes.map(node => node.id).sort(), [...byId.keys()].sort());
  const children = new Map(layout.nodes.map(node => [node.id, []]));
  for (const edge of layout.edges) {
    assert(byId.get(edge.to).parents.some(parent => parent.id === edge.from && parent.kind === edge.kind));
    children.get(edge.from).push(edge.to);
  }
  const visited = new Set(), visiting = new Set();
  const visit = id => {
    assert(!visiting.has(id), 'Dependency cycle at ' + id);
    if (visited.has(id)) return;
    visiting.add(id);
    children.get(id).forEach(visit);
    visiting.delete(id);
    visited.add(id);
  };
  visit('E000');
  assert.equal(visited.size, byId.size, 'Every experiment must be reachable from E000');
  for (const node of layout.nodes) {
    const record = byId.get(node.id);
    if (node.tone === 'candidate') assert(node.metric, node.id + ': green needs network latency');
    if (['failure', 'infeasible'].includes(node.tone)) {
      assert.equal(node.texts.filter(text => text.text === node.problem).length, 1, node.id + ': one problem line');
      assert(!node.texts.some(text => /ms\//.test(text.text) && text.bold), node.id + ': red latency must not be bold');
    }
    if (record.status === 'planned') assert.equal(node.metric, null);
    if (!node.metric) continue;
    const source = byId.get(node.metric.reference_id || node.id);
    if (node.metric.reference_id) assert(record.parents.some(parent => parent.id === source.id && parent.kind === 'verify'));
    const cycles = node.metric.source === 'rtl' ? source.verification.rtl_latency_max : source.hls.latency_cycles;
    if (node.metric.source === 'rtl') assert.equal(source.verification.rtl_status, 'Pass');
    assert.equal(node.metric.latency_cycles, cycles);
    assert.equal(node.metric.time_ms, cycles * 10 / 1e6);
  }
  assert.equal(layout.nodes.find(node => node.id === 'C18').metric.reference_id, 'C14');
  assert.equal(layout.nodes.find(node => node.id === 'W32').metric.reference_id, 'F97');
  assert.equal(layout.nodes.find(node => node.id === 'F52').metric.reference_id, 'F43');
  assert.equal(layout.nodes.find(node => node.id === 'W30').metric.reference_id, 'W28');
  assert.equal(byId.get('W30').verification.route_feasible, true);
  const frp = layout.nodes.find(node => node.id === 'W28');
  assert.equal(byId.get('W28').status, 'fail');
  assert.equal(byId.get('W28').acceptance_override.authorized_by, 'user');
  assert.equal(frp.metric.latency_cycles, 549438);
  assert.equal(frp.faded, false);
}

async function main() {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}) });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  const report = { browser_version: browser.version(), source_commit: chinese.source_commit,
    svg_count: 0, node_instances: 0, visible_arrowheads: 0, viewer_checks: [] };
  try {
    for (const layout of layouts) {
      const filename = layout.key + (layout.english ? '.en' : '') + '.svg';
      await page.goto(pathToFileURL(path.join(__dirname, filename)).href);
      const result = await page.evaluate(async ({ nodes, edges }) => {
        await document.fonts.ready;
        const root = document.documentElement;
        const errors = [];
        for (const node of nodes) {
          const group = root.querySelector('[data-id="' + node.id + '"]');
          if (!group) { errors.push('Missing node ' + node.id); continue; }
          const rect = group.querySelector('rect').getBBox();
          for (const text of group.querySelectorAll('text')) {
            const box = text.getBBox();
            if (box.x < rect.x + 12 || box.x + box.width > rect.x + rect.width - 12
                || box.y < rect.y + 3 || box.y + box.height > rect.y + rect.height - 5) {
              errors.push(node.id + ': rendered text outside node: ' + text.textContent);
            }
          }
        }
        const canvas = new OffscreenCanvas(14, 14);
        const context = canvas.getContext('2d', { willReadFrequently: true });
        for (const edge of edges) {
          const arrow = edge.arrow;
          const clone = root.cloneNode(true);
          clone.setAttribute('viewBox', [arrow.x, arrow.y, arrow.width, arrow.height].join(' '));
          clone.setAttribute('width', '14');
          clone.setAttribute('height', '14');
          const url = URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml' }));
          try {
            const picture = new Image();
            picture.src = url;
            await picture.decode();
            context.clearRect(0, 0, 14, 14);
            context.drawImage(picture, 0, 0);
            const pixels = context.getImageData(0, 0, 14, 14).data;
            const tip = edge.points[edge.points.length - 1];
            const before = edge.points[edge.points.length - 2];
            let offAxisInk = 0;
            for (let y = 0; y < 14; y++) for (let x = 0; x < 14; x++) {
              const offAxis = Math.abs((tip.y === before.y ? y : x) + 0.5 - 7) > 3.5;
              const offset = (y * 14 + x) * 4;
              if (offAxis && pixels[offset + 3] > 0 && Math.min(...pixels.slice(offset, offset + 3)) < 245) offAxisInk++;
            }
            // A plain line has no ink this far off its axis; the triangular marker must render.
            if (offAxisInk < 12) errors.push(edge.from + '/' + edge.to + ': invisible arrowhead (' + offAxisInk + ' pixels)');
          } finally {
            URL.revokeObjectURL(url);
          }
        }
        return { errors, nodeCount: root.querySelectorAll('[data-id]').length };
      }, layout);
      assert.deepEqual(result.errors, [], filename);
      assert.equal(result.nodeCount, layout.nodes.length);
      report.svg_count++;
      report.node_instances += result.nodeCount;
      report.visible_arrowheads += layout.edges.length;
      if (['overview', 't4', 'clock-fifo', 'rom', 'milestones'].includes(layout.key)) {
        const selected = layout.nodes.find(node => node.id === (['t4', 'milestones'].includes(layout.key) ? 'C18'
          : layout.key === 'clock-fifo' ? 'W32' : 'W25'));
        const box = selected ? [selected.x - 140, selected.y - 120, selected.width + 280, selected.height + 240]
          : [0, 0, layout.width, layout.height];
        await page.evaluate(viewBox => {
          document.documentElement.setAttribute('viewBox', viewBox.join(' '));
          document.documentElement.setAttribute('width', '1440');
          document.documentElement.setAttribute('height', '900');
        }, box);
        await page.screenshot({ path: path.join(output, filename + '.png') });
      }
    }

    for (const language of ['zh', 'en']) for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
      await page.setViewportSize(viewport);
      await page.goto(pathToFileURL(path.join(__dirname, language === 'en' ? 'full.en.html' : 'full.html')).href);
      assert.equal(await page.locator('#scene [data-id]').count(), chinese.counts.experiments);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      for (const id of ['C18', 'W32', 'W30', 'W28', 'C16']) {
        await page.locator('#query').fill(id);
        await page.locator('#query').press('Enter');
        assert.equal(await page.locator('#scene .selected').getAttribute('data-id'), id);
        assert(await page.locator('#scene .related-edge').count() > 0);
        assert(await page.locator('#scene .related-edge').evaluateAll(edges => edges.every(edge => getComputedStyle(edge).opacity === '1')));
        const visible = await page.locator('#scene .selected').boundingBox();
        const surface = await page.locator('#viewport').boundingBox();
        assert(visible.x >= surface.x - 1 && visible.y >= surface.y - 1
          && visible.x + visible.width <= surface.x + surface.width + 1
          && visible.y + visible.height <= surface.y + surface.height + 1);
        if (['C18', 'W32', 'W30'].includes(id)) await page.screenshot({ path: path.join(output,
          `${id}-${language}-${viewport.width}.png`) });
      }
      const previousZoom = await page.locator('#zoom').textContent();
      await page.locator('#in').click();
      assert.notEqual(await page.locator('#zoom').textContent(), previousZoom);
      await page.locator('#out').click();
      await page.locator('#query').fill('UNKNOWN');
      await page.locator('#query').press('Enter');
      assert.equal(await page.locator('#query').getAttribute('aria-invalid'), 'true');
      await page.locator('#clear').click();
      assert.equal(await page.locator('#scene .selected').count(), 0);
      const surface = await page.locator('#viewport').boundingBox();
      const beforeDrag = await page.locator('#scene').getAttribute('style');
      await page.mouse.move(surface.x + surface.width / 2, surface.y + surface.height / 2);
      await page.mouse.down();
      await page.mouse.move(surface.x + surface.width / 2 + 45, surface.y + surface.height / 2 + 25, { steps: 5 });
      await page.mouse.up();
      assert.notEqual(await page.locator('#scene').getAttribute('style'), beforeDrag);
      if (viewport.width === 390) {
        const session = await page.context().newCDPSession(page);
        const y = surface.y + surface.height / 2;
        const beforePinch = await page.locator('#scene').getAttribute('style');
        await session.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 150, y, id: 1 }, { x: 240, y, id: 2 }] });
        await session.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 120, y, id: 1 }, { x: 270, y, id: 2 }] });
        await session.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
        assert.notEqual(await page.locator('#scene').getAttribute('style'), beforePinch);
        await session.detach();
      }
      await page.locator('#fit').click();
      report.viewer_checks.push({ language, viewport });

      await page.goto(pathToFileURL(path.join(__dirname, 'milestones' + (language === 'en' ? '.en' : '') + '.html')).href);
      assert.equal(await page.locator('#scene [data-id]').count(), 10);
      assert.equal(await page.locator('#scene .selected').getAttribute('data-id'), 'E020');
      assert(!/100 MHz/.test(await page.locator('.legend').textContent()));
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      for (const [query, selected] of [['E070', 'E039'], ['F08', 'F25'], ['C14', 'C18']]) {
        await page.locator('#query').fill(query);
        await page.locator('#query').press('Enter');
        assert.equal(await page.locator('#scene .selected').getAttribute('data-id'), selected);
        const bounds = await page.locator('#scene .selected').boundingBox();
        const surface = await page.locator('#viewport').boundingBox();
        assert(bounds.x >= surface.x - 1 && bounds.x + bounds.width <= surface.x + surface.width + 1);
        assert(bounds.y >= surface.y - 1 && bounds.y + bounds.height <= surface.y + surface.height + 1);
      }
      await page.screenshot({ path: path.join(output, `milestones-${language}-${viewport.width}.png`) });
      report.viewer_checks.push({ language, viewport, graph: 'milestones' });
    }
    fs.writeFileSync(path.join(output, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
