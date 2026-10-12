# Experiment Evolution Diagrams and Ledger

[中文版](README.md)

Start with the [narrative guide](../0004-experiment-evolution.en.md), [overview SVG](overview.en.svg), and [complete ledger](records.en.md). Open SVGs separately to zoom; use experiment IDs to locate ledger entries. Each route also has Mermaid source.

## One Complete Evolution Graph

The [complete compact graph](full.en.svg) retains all 207 experiments, each ID appearing once, and selects 217 main relationships from 307 archive dependencies as thick solid arrows. The [local viewer](full.en.html) opens directly with pan, zoom, ID lookup, and relationship highlighting, without a server or network. Nodes show IDs, short ideas, and network latency. Red nodes add one specific problem line with regular-weight latency; hover text gives details, all parents, and verification state.

Each experiment usually connects to one main parent; integration, precision changes, and cross-route scheduling retain multiple parents where needed. There are 11 two-parent nodes. Parameter scans follow archived controls as idea progression, rather than source inheritance. `main-parents.json` selects these edges and `compact-titles.json` shortens bilingual labels. All 307 relationships remain in data, ledgers, and route graphs.

Green indicates stage evidence with comparable network latency, without requiring routed closure. Amber indicates HLS timing warnings. Red gives specific budget, II, configuration, or run/implementation problems. Gray auxiliary nodes have no reported or attributable network cycles; teal indicates software analysis. In this snapshot C18 T4 passes every 5 ns route gate; W32/F52/W30 T8 pass 4.5 ns. Their closed-target 1.503160 / 2.514411 / 2.472471 ms/frame are listed in the guide, while the graph retains its common 100 MHz metric. Preserve C13's historical HLS overruns and W20's diagnostic exclusion; physical acceptance is not inherited.

Failed runs, timeouts, invalid settings, plans, and hardware experiments without passing function are faded with adjacent edges. Resource-infeasible designs with passing C retain full red color. W28 is an explicitly authorized exception: numerical/reload RTL Pass, faster than the original lower bound, original `fail` and red problem retained, later upper-only acceptance noted, actual RTL time visible without fading. This requires archived authorization and matching Pass. Selected relationships regain full brightness. Implementations check function only through explicit same-design verification, never ordinary ancestry.

The graph's only performance metric is accelerator latency for the complete three-layer SRCNN on one `255 x 255` image, normalized to a **100 MHz / 10 ns reference clock**: `ms/frame = network latency cycles x 10 / 1,000,000`. Prefer the current experiment's valid network RTL maximum latency, then its network HLS top-level latency. Completed checks of the same design without their own latency may reference an actual report through an explicit `verify` relationship, preferring RTL co-simulation over HLS and rejecting multiple equally preferred sources. A `~` prefix and source ID mark references, such as F92 to F82, F95 to F93, and F98/W22 to F97. They are not new measurements by the verification run; design timing warnings still apply. Startup, drain, and internal transfers follow the top-level report's coverage; host/DMA transfers are excluded.

These values normalize existing report cycles. They are not synthesis results rerun at 10 ns and do not establish operation at 100 MHz. Rerunning synthesis can change scheduling and cycle counts. Hover text distinguishes HLS estimates from RTL simulation cycles. Resource quantities, PE/layer cycles, MSE/PSNR, and WNS are removed from node labels.

Green and amber latency is bold; red latency uses regular-weight gray text and does not establish feasible ranking. Red includes host OOM and routed timing failures, beyond resource overruns. Without valid cycles, auxiliary labels state scope, plans state queued/running without a result or not run, and red nodes state problems. PE work counts, ordinary ancestors, inherited registry fields, and planned estimates do not supply latency. Failed or unrun verification nodes do not receive reference estimates.

Acceptance for this update requires each experiment ID exactly once, an acyclic subset of archive relationships, only the common node metric, traceable network latency on every green node, one specific problem line and no bold latency on every red node, reference estimates only through completed same-design verification relationships, identical numbers and edges in both languages, all route diagrams consistent with archived measurements, regeneration and geometry checks, and desktop/mobile viewer checks.

## Key Milestones

The [standalone SVG](milestones.en.svg) / [local viewer](milestones.en.html) connect the ten user-selected stages in narrative order, showing only IDs, titles, and one result without dates or explanatory paragraphs. Failed nodes show the specific problem, such as E033's 136,868 LUTs, 17% over capacity; passing and warning nodes label the latency source. The palette, fonts, and arrow clearance follow the existing graphs. These arrows introduce no archive dependencies. Copy is in [milestones.json](milestones.json); the data remains frozen at `653ceb9`, excluding later results.

Times use the stated HLS report clock or passing routed target, distinct from the complete graph's fixed 100 MHz metric. The E039/E070 node shows only E039's HLS 29.83 ms/frame; W22/W32/C18 show compute time at passing routed targets. Full verification and failure history remain in the original evolution graph and ledger.

## Scope and Evidence

Snapshot `653ceb9` covers the union of `experiments/results.csv` and `exp/configs/*.json`: 207 experiments, 200 result records, and seven without results. It adds 37 experiments since `a3d78b7`, with new bilingual host, ROM, T8 clock/FIFO, and T4 routes. F50/F51/W31/C16/C17 are queued/running in workflow state without archived measurements; F90/F91 remain deferred. This edition is frozen through W30 and excludes later results. Failures, invalid settings, and timeouts count as results. F99 is a closure/audit event without an invented experiment node.

`catalog.json` curates ideas and dependencies. `catalog.en.json` translates titles, questions, changes, issues, and relationship labels. English generation reuses the Chinese version's parsed measurements and dependencies; it does not maintain a separate numerical or relationship history. The overview selects major causal relationships; route graphs retain every dependency for their local experiments and show external parents in gray.

`generate.rb` uses Ruby's standard CSV/JSON parsers to merge the registry, archived configurations, verification records, and raw HLS timing warnings into `data.json` and `records.md`. `generate.en.rb` applies the complete translation overlay to produce `data.en.json` and `records.en.md`. In both data files:

- `registry_raw` preserves original values, including inherited estimates in verification rows; those estimates are not displayed as new measurements.
- `hls` contains that experiment's synthesis metrics; `verification` contains actual RTL/implementation results.
- `quality.provenance` distinguishes independent precision references from quality measured in the current run.
- `planned_estimates` retains hypotheses rather than measured resources, II, or latency.
- `flags` independently labels budget overruns, missed II, invalid settings, HLS timing warnings, host OOM, and failed routed timing.
- `diagnostic_only` reads the archived `diagnostic_infeasible_parent` setting to retain W20's exclusion; passing physical timing does not change the original HLS gates.
- `execution_state` distinguishes queued/running without an archived result from deferred plans; neither supplies measurements.
- `acceptance_override` retains W28's later user authorization without changing raw status or verification.
- `verification.route_feasible` records independent routed gates under the new policy, preserving historical HLS status.

Historical HLS budgets are DSP <= 1248, BRAM18K <= 288, URAM <= 64, LUT <= 81984, and FF <= 163968, with LUT/FF at 70% of capacity. Current final acceptance uses independent routed gates in [0005](../0005-rom-clock-t4-plan.md); HLS only screens. Ledger/route times retain `cycles * max(target period, HLS estimated period) / 10^6`, distinct from the graph's 100 MHz basis and from board measurements. Set14 means the complete 13-image course set without a provisional comic requirement; original archive wording remains.

## Regeneration

Requirements: Ruby, Node.js, and `dagre@0.8.5`. Ruby uses only standard libraries. These commands do not modify HLS workspaces or execute hardware experiments.

From the repository root:

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

`render.cjs` first uses `DAGRE_MODULE`, then a local Node module, then version 0.8.5 in npm's `_npx` cache. If needed, install the dependency in an isolated temporary directory:

```sh
npm install --prefix /tmp/srcnn-map-tools dagre@0.8.5
DAGRE_MODULE=/tmp/srcnn-map-tools/node_modules/dagre node docs/experiment-evolution/render.cjs --lang en
```

Dagre places nodes with obstacle-aware orthogonal routes. Arrowheads enter perpendicular to node borders, stop 8 px outside them, and have at least 28 px of final straight path; the 14 px triangle stays outside every node and lines retain at least 6 px clearance. Multiple parents use separate ports. Chinese wrapping preserves Latin words and English wraps at words. `--check` validates regeneration, node/text bounds, node overlap, canvas bounds, line clearance, arrow direction/terminal length, and marker occlusion. `layout*.json` retain paths and arrow bounds.

`--full` separately generates complete SVGs, Mermaid, HTML, and layouts without rewriting the overview and 16 route graphs. It checks every ID exactly once, valid multiple-parent selection, and no invented/duplicate links. Layouts retain reference clocks, cycles, sources, `metric.reference_id`, and red `problem` labels. Viewers embed the same SVG; icons are from `lucide-static@0.468.0`, with its license retained in `viewer-icons.json` and HTML.

## Rendering Checks

The [browser regression script](verify-browser.cjs) checks actual text bounds in every SVG and crops each arrow into canvas, checking triangle pixels away from the line axis. This catches missing/occluded markers beyond geometric line checks. Screenshots and results go to `/tmp/srcnn-evolution-check/`:

```sh
npm install --prefix /tmp/srcnn-map-tools playwright@1.64.0
/tmp/srcnn-map-tools/node_modules/.bin/playwright install chromium
PLAYWRIGHT_MODULE=/tmp/srcnn-map-tools/node_modules/playwright node docs/experiment-evolution/verify-browser.cjs
```

Existing Chromium can be selected with `PLAYWRIGHT_CHROMIUM_EXECUTABLE`, skipping browser installation. This update used Mac, Node 25.8.0, Ruby 2.6.10, Dagre 0.8.5, Playwright 1.64.0, and installed Chromium. No HLS runs, remote scheduling changes, or board tests were performed.

Both languages share 207 unique nodes, 217 main links, and 307 dependencies; every main link is archived and every node is reachable from E000. There are 119 common-time nodes: 101 own reports and 18 explicit same-design references. All 47 green nodes have latency; all 95 red nodes have one problem line and regular-weight latency. The 27 auxiliary nodes invent no time and 50 failed/unarchived nodes are faded. C18 cites C14, W32 cites F97, F52 cites F43, and W30 cites W28. Preserve C13 historical HLS overruns and W28 original failure plus later authorization.

All 38 SVGs pass regeneration, XML, geometry, and actual text checks; all 1,140 arrows pass individual rendered-pixel visibility checks. Both full viewers pass ID lookup, invalid IDs, zoom, dragging, pinch, highlighting, clearing, and no horizontal overflow at 1440 x 900 desktop and 390 x 844 mobile sizes. Milestone viewers also verify grouped IDs and the stated time basis. C18, W32, W30, T4, and milestone screenshots were visually inspected. Local paths and anchors in related Markdown are checked separately.

The diagrams, documentation, and generators pass `git diff --check`. Original experiment configurations, logs, reports, registries, HLS workspaces, and floating-point sources remain unchanged.

For new experiments, verify original evidence, update both catalogs and guides, regenerate both languages, and check their coverage and layout. Translation generation rejects missing or duplicate IDs and preserves shared measurements and dependencies.
