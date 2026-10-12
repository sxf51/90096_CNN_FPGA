# Experiment Evolution Diagrams and Ledger

[中文版](README.md)

Start with the [narrative guide](../0004-experiment-evolution.en.md), [overview SVG](overview.en.svg), and [complete ledger](records.en.md). Open SVGs separately to zoom; use experiment IDs to locate ledger entries. Each route also has Mermaid source.

## One Complete Evolution Graph

The [complete compact graph](full.en.svg) retains all 170 experiments, with each ID appearing once, and selects 178 main optimization relationships from the archive's 242 dependencies as thick solid arrows. The [local viewer](full.en.html) opens directly and supports pan, zoom, ID lookup, and highlighting the main upstream/downstream relationships without a server or network access. Nodes show the ID, a short idea, and network latency per image. Red nodes add one specific problem line and use regular-weight latency. Hover text contains the detailed explanation, all parents, and verification state.

Each experiment usually connects to one main parent. Module integration, essential precision changes, and scheduling ideas from another route retain multiple parents where needed. Parameter scans may follow existing control relationships to express idea progression, rather than source-code inheritance. `main-parents.json` explicitly selects graph edges for experiments with multiple parents; `compact-titles.json` only shortens bilingual labels. All 242 relationships remain in `data.en.json`, the ledger, and the route diagrams.

Green indicates evidence passing its current stage with comparable network latency; it does not require routed timing closure. Amber indicates HLS timing warnings. Red indicates resource budgets exceeded, missed II targets, invalid configurations, or run/implementation failures, with a specific reason on each node. Gray auxiliary nodes are PE, layer, boundary, or C-only exploration without reported or attributable network cycles; teal indicates software analysis. Route diagrams retain their original stage colors. F92/F95/F98 pass network routing at 5 ns; W22 passes at 4.95 ns. P08 only verifies a PE, and E070 fails network routed timing. W20 passes physical timing at 5 ns but is explicitly diagnostic only: its parent W17 still exceeds the HLS LUT budget, so W20 stays red and outside candidate rankings.

Failed runs, timeouts, invalid configurations, plans, and hardware experiments without passing functional evidence are faded, along with their adjacent edges. Resource-infeasible designs with passing C simulation retain full red color so their costs remain visible. Hardware simulation does not apply to software analysis. Implementation nodes check functional prerequisites only through explicit same-design verification edges; ordinary design ancestry does not transfer acceptance.

The graph's only performance metric is accelerator latency for the complete three-layer SRCNN on one `255 x 255` image, normalized to a **100 MHz / 10 ns reference clock**: `ms/frame = network latency cycles x 10 / 1,000,000`. Prefer the current experiment's valid network RTL maximum latency, then its network HLS top-level latency. Completed checks of the same design without their own latency may reference an actual report through an explicit `verify` relationship, preferring RTL co-simulation over HLS and rejecting multiple equally preferred sources. A `~` prefix and source ID mark references, such as F92 to F82, F95 to F93, and F98/W22 to F97. They are not new measurements by the verification run; design timing warnings still apply. Startup, drain, and internal transfers follow the top-level report's coverage; host/DMA transfers are excluded.

These values normalize existing report cycles. They are not synthesis results rerun at 10 ns and do not establish operation at 100 MHz. Rerunning synthesis can change scheduling and cycle counts. Hover text distinguishes HLS estimates from RTL simulation cycles. Resource quantities, PE/layer cycles, MSE/PSNR, and WNS are removed from node labels.

Green and amber latency values are bold. Red latency values remain as regular-weight gray text and cannot qualify a design for feasible-candidate ranking. Red does not always mean excessive resources: F81/F84 fail through host OOM, while E070 fails routed timing. Without valid network cycles, auxiliary labels state PE/layer/C scope, plans show "Not run", and red nodes show the specific problem. PE work counts, ordinary ancestors, inherited registry fields, and planned estimates do not supply latency. Failed or unrun verification nodes do not receive reference estimates.

Acceptance for this update requires each experiment ID exactly once, an acyclic subset of archive relationships, only the common node metric, traceable network latency on every green node, one specific problem line and no bold latency on every red node, reference estimates only through completed same-design verification relationships, identical numbers and edges in both languages, all route diagrams consistent with archived measurements, regeneration and geometry checks, and desktop/mobile viewer checks.

## Scope and Evidence

The snapshot is commit `a3d78b7`, covering the union of `experiments/results.csv` and `exp/configs/*.json`: 170 experiments, with 168 result records and two deferred plans, F90/F91. Compared with `800a87a`, 17 experiments are new and nine former plans, P13-P16 and F85-F89, have actual results. Failures, invalid configurations, and timeouts count as result records. F99 is workflow closure/auditing without a separate configuration or registry row, so no experiment node is invented. Unarchived workspace runs are outside this snapshot.

`catalog.json` curates ideas and dependencies. `catalog.en.json` translates titles, questions, changes, issues, and relationship labels. English generation reuses the Chinese version's parsed measurements and dependencies; it does not maintain a separate numerical or relationship history. The overview selects major causal relationships; route graphs retain every dependency for their local experiments and show external parents in gray.

`generate.rb` uses Ruby's standard CSV/JSON parsers to merge the registry, archived configurations, verification records, and raw HLS timing warnings into `data.json` and `records.md`. `generate.en.rb` applies the complete translation overlay to produce `data.en.json` and `records.en.md`. In both data files:

- `registry_raw` preserves original values, including inherited estimates in verification rows; those estimates are not displayed as new measurements.
- `hls` contains that experiment's synthesis metrics; `verification` contains actual RTL/implementation results.
- `quality.provenance` distinguishes independent precision references from quality measured in the current run.
- `planned_estimates` retains hypotheses rather than measured resources, II, or latency.
- `flags` independently labels budget overruns, missed II, invalid settings, HLS timing warnings, host OOM, and failed routed timing.
- `diagnostic_only` reads the archived `diagnostic_infeasible_parent` setting to retain W20's exclusion; passing physical timing does not change the original HLS gates.

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

This update verified 170 unique nodes, 178 main links, and 242 archive dependencies in each language. Every main link exists in the archive, all nodes are reachable from E000, and only nine nodes retain two main parents. Both languages share measurements, functional results, verification statuses, diagnostic flags, and dependencies.

There are 95 nodes with common network latency at 100 MHz: 82 use their own reports and 13 cite explicit same-design verification reports with source IDs. All 27 green nodes have latency; all 87 red nodes have a single problem line and regular-weight latency. The 25 auxiliary nodes do not invent network metrics, and 39 failed/unrun nodes remain faded. Checks cover F28/W21 HLS cycles, original F85/F93/F97 RTL verification records, and original F92/F95/F98/W22 physical results and target-clock times. W22 prefers F97's RTL cycles; W20 retains its red diagnostic exclusion. F88's SIGTERM, F89's three-hour timeout, and the deferred F90/F91 plans match the archive.

Regeneration consistency, XML, and layout checks passed for each language's 13 route diagrams and complete graph. All 28 SVGs passed external geometry checks with zero errors or warnings. Playwright checked text boundaries, no horizontal overflow, thick solid arrows, ID lookup, invalid IDs, zoom, dragging, touch pinch, relationship highlighting, and clearing selection in both languages at 1440 x 900 desktop and 390 x 844 mobile sizes. Screenshots including F28, W21/W22, and W20 were visually inspected. All 3,526 local links and anchors across the 10 related Markdown files passed. This update reads archived experiment results without rerunning HLS or board tests.

The edited documentation and generators pass `git diff --check`. Original tool reports, logs, and CSVs retain upstream whitespace, so checking the full merge still reports trailing spaces or CRLF in those archives. Original evidence is not rewritten to suppress these diagnostics.

For new experiments, verify original evidence, update both catalogs and guides, regenerate both languages, and check their coverage and layout. Translation generation rejects missing or duplicate IDs and preserves shared measurements and dependencies.
