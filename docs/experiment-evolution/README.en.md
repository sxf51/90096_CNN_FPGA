# Experiment Evolution Diagrams and Ledger

[中文版](README.md)

Start with the [narrative guide](../0004-experiment-evolution.en.md), [overview SVG](overview.en.svg), and [complete ledger](records.en.md). Open SVGs separately to zoom; use experiment IDs to locate ledger entries. Each route also has Mermaid source.

## One Complete Evolution Graph

The [complete compact graph](full.en.svg) retains all 153 experiments, with each ID appearing once, and selects 160 main optimization relationships from the archive's 207 dependencies as thick solid arrows. The [local viewer](full.en.html) opens directly and supports pan, zoom, ID lookup, and highlighting the main upstream/downstream relationships without a server or network access. Nodes show the ID, a short idea, and network latency per image. Red nodes add one specific problem line and use regular-weight latency. Hover text contains the detailed explanation, all parents, and verification state.

Each experiment usually connects to one main parent. Module integration, essential precision changes, and scheduling ideas from another route retain multiple parents where needed. Parameter scans may follow existing control relationships to express idea progression, rather than source-code inheritance. `main-parents.json` explicitly selects graph edges for experiments with multiple parents; `compact-titles.json` only shortens bilingual labels. All 207 relationships remain in `data.en.json`, the ledger, and the route diagrams.

Green indicates evidence passing its current stage with comparable network latency; it does not require routed timing closure. Amber indicates HLS timing warnings. Red indicates resource budgets exceeded, missed II targets, invalid configurations, or run/implementation failures, with a specific reason on each node. Gray auxiliary nodes are PE, layer, boundary, or C-only exploration without reported or attributable network cycles; teal indicates software analysis. Route diagrams retain their original stage colors. P08 passes routed timing only for a PE. E070 completes network routing but fails timing; no network record passes routed timing in this snapshot.

Failed runs, timeouts, invalid configurations, plans, and hardware experiments without passing functional evidence are faded, along with their adjacent edges. Resource-infeasible designs with passing C simulation retain full red color so their costs remain visible. Hardware simulation does not apply to software analysis. Implementation nodes check functional prerequisites only through explicit same-design verification edges; ordinary design ancestry does not transfer acceptance.

The graph's only performance metric is accelerator latency for the complete three-layer SRCNN on one `255 x 255` image, normalized to a **100 MHz / 10 ns reference clock**: `ms/frame = network latency cycles x 10 / 1,000,000`. Prefer the current experiment's valid network RTL maximum latency, then its network HLS top-level latency. Completed checks of the same design without their own latency may reference an actual design report through an explicit `verify` relationship. A `~` prefix and source ID mark these references: E069 to E043, F80 to F25, F83 to F24, and E070 to E039. They are not new measurements by the verification run; design timing warnings still apply. Startup, drain, and internal transfers follow the top-level report's coverage; host/DMA transfers are excluded.

These values normalize existing report cycles. They are not synthesis results rerun at 10 ns and do not establish operation at 100 MHz. Rerunning synthesis can change scheduling and cycle counts. Hover text distinguishes HLS estimates from RTL simulation cycles. Resource quantities, PE/layer cycles, MSE/PSNR, and WNS are removed from node labels.

Green and amber latency values are bold. Red latency values remain as regular-weight gray text and cannot qualify a design for feasible-candidate ranking. Red does not always mean excessive resources: F81/F84 fail through host OOM, while E070 fails routed timing. Without valid network cycles, auxiliary labels state PE/layer/C scope, plans show "Not run", and red nodes show the specific problem. PE work counts, ordinary ancestors, inherited registry fields, and planned estimates do not supply latency. Failed or unrun verification nodes do not receive reference estimates.

Acceptance for this update requires each experiment ID exactly once, an acyclic subset of archive relationships, only the common node metric, traceable network latency on every green node, one specific problem line and no bold latency on every red node, reference estimates only through completed same-design verification relationships, identical numbers and edges in both languages, unchanged route diagrams and measurements, regeneration and geometry checks, and desktop/mobile viewer checks.

## Scope and Evidence

The snapshot is commit `800a87a`, covering the union of `experiments/results.csv` and `exp/configs/*.json`: 153 experiments, with 142 result records and 11 plans/preparation records. Failures, invalid configurations, and timeouts count as result records. Incomplete runs in other workspaces are outside this snapshot.

`catalog.json` curates ideas and dependencies. `catalog.en.json` translates titles, questions, changes, issues, and relationship labels. English generation reuses the Chinese version's parsed measurements and dependencies; it does not maintain a separate numerical or relationship history. The overview selects major causal relationships; route graphs retain every dependency for their local experiments and show external parents in gray.

`generate.rb` uses Ruby's standard CSV/JSON parsers to merge the registry, archived configurations, verification records, and raw HLS timing warnings into `data.json` and `records.md`. `generate.en.rb` applies the complete translation overlay to produce `data.en.json` and `records.en.md`. In both data files:

- `registry_raw` preserves original values, including inherited estimates in verification rows; those estimates are not displayed as new measurements.
- `hls` contains that experiment's synthesis metrics; `verification` contains actual RTL/implementation results.
- `quality.provenance` distinguishes independent precision references from quality measured in the current run.
- `planned_estimates` retains hypotheses rather than measured resources, II, or latency.
- `flags` independently labels budget overruns, missed II, invalid settings, HLS timing warnings, host OOM, and failed routed timing.

HLS budgets are DSP <= 1248, BRAM18K <= 288, URAM <= 64, LUT <= 81984, and FF <= 163968. LUT/FF budgets use 70% of device capacity. Resource feasibility does not establish physical timing. The ledger and original route diagrams retain `cycles * max(target period, HLS estimated period) / 10^6`; clock uncertainty must still be checked. Their clock basis differs from the complete graph's common 100 MHz normalization.

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
node docs/experiment-evolution/render.cjs --check
node docs/experiment-evolution/render.cjs --lang en --check
node docs/experiment-evolution/render.cjs --full --check
node docs/experiment-evolution/render.cjs --full --lang en --check
git diff --check
```

`render.cjs` first uses `DAGRE_MODULE`, then a local Node module, then version 0.8.5 in npm's `_npx` cache. If needed, install the dependency in an isolated temporary directory:

```sh
npm install --prefix /tmp/srcnn-map-tools dagre@0.8.5
DAGRE_MODULE=/tmp/srcnn-map-tools/node_modules/dagre node docs/experiment-evolution/render.cjs --lang en
```

Dagre lays out directed graphs, with orthogonal SVG edges and content-sized nodes. English labels wrap at word boundaries. `--check` detects stale diagrams, text/node boundaries, node overlap, nonorthogonal edges, and edges crossing nodes. `layout.json` and `layout.en.json` retain the geometry used by these checks.

`--full` separately generates `full.svg` / `full.en.svg`, their Mermaid sources, local HTML viewers, and `layout.full*.json`, preserving the original 13 route diagrams. Its checks also verify each ID exactly once, valid choices for multiple-parent experiments, and no duplicate or invented relationships. Layout files record the reference clock and each performance value's cycles and source; reference estimates add `metric.reference_id`, and red problem labels are recorded in `problem`. The viewers embed the same SVG. Icons come from `lucide-static@0.468.0`, with the license retained in `viewer-icons.json` and the generated HTML.

## Rendering Checks

Local preview and geometry checks use `@larksuite/whiteboard-cli` 0.2.13. They write local images and do not create external documents:

```sh
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.en.svg -f svg --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.en.svg -o /tmp/srcnn-experiment-overview-en.png -f svg -s 1
```

This language update verified identical measurements, statuses, evidence, and 207 dependencies across all 153 experiments. Regeneration consistency and layout checks passed for all 13 diagrams in each language. All 13 English SVGs passed XML parsing and external geometry checks with zero errors or warnings; the overview, continuous pipeline, and verification diagrams were rendered and visually inspected. All 3,000 local links and anchors across the 10 related Markdown files passed. HLS experiments were not rerun for this documentation update.

The simplified complete graph verified 153 unique nodes and 160 main links in both languages. Every link exists in the archive, all nodes are reachable from E000, and only eight nodes have two parents. All 207 archive relationships remain unchanged. There are 76 nodes with common network latency at a 100 MHz reference: 72 use their own reports and four cite reports through explicit same-design verification relationships with source IDs. All 15 green nodes have comparable latency. All 80 red nodes have a single problem line and regular-weight latency; 22 former green exploration nodes without network cycles are gray auxiliary nodes. Checks distinguish F25/F24 HLS cycles from F82 RTL cycles and verify all four reference sources. PE, layer-only, failed, invalid, planned, and inherited-only results do not supply network latency. The 45 failed/unrun nodes remain faded.

Both SVGs passed XML parsing, regeneration consistency, and external geometry checks with zero errors or warnings. Playwright verified text boundaries, no horizontal overflow, thick solid arrows throughout, ID lookup, invalid IDs, zoom, dragging, touch pinch, relationship highlighting, and clearing selection in both languages at 1440 x 900 desktop and 390 x 844 mobile sizes; screenshots were visually inspected. Additional checks cover F80's bold reference latency, C11/E070's regular-weight latency, F81's host OOM reason, and P08's local validation scope. All 3,018 local links and anchors across the 10 related Markdown files passed. Regeneration checks passed for the original 26 route diagrams, and measurements remain unchanged. This update did not rerun HLS or board tests.

For new experiments, verify original evidence, update both catalogs and guides, regenerate both languages, and check their coverage and layout. Translation generation rejects missing or duplicate IDs and preserves shared measurements and dependencies.
