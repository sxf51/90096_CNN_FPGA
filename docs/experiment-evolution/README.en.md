# Experiment Evolution Diagrams and Ledger

[中文版](README.md)

Start with the [narrative guide](../0004-experiment-evolution.en.md), [overview SVG](overview.en.svg), and [complete ledger](records.en.md). Open SVGs separately to zoom; use experiment IDs to locate ledger entries. Each route also has Mermaid source.

## Scope and Evidence

The snapshot is commit `800a87a`, covering the union of `experiments/results.csv` and `exp/configs/*.json`: 153 experiments, with 142 result records and 11 plans/preparation records. Failures, invalid configurations, and timeouts count as result records. Incomplete runs in other workspaces are outside this snapshot.

`catalog.json` curates ideas and dependencies. `catalog.en.json` translates titles, questions, changes, issues, and relationship labels. English generation reuses the Chinese version's parsed measurements and dependencies; it does not maintain a separate numerical or relationship history. The overview selects major causal relationships; route graphs retain every dependency for their local experiments and show external parents in gray.

`generate.rb` uses Ruby's standard CSV/JSON parsers to merge the registry, archived configurations, verification records, and raw HLS timing warnings into `data.json` and `records.md`. `generate.en.rb` applies the complete translation overlay to produce `data.en.json` and `records.en.md`. In both data files:

- `registry_raw` preserves original values, including inherited estimates in verification rows; those estimates are not displayed as new measurements.
- `hls` contains that experiment's synthesis metrics; `verification` contains actual RTL/implementation results.
- `quality.provenance` distinguishes independent precision references from quality measured in the current run.
- `planned_estimates` retains hypotheses rather than measured resources, II, or latency.
- `flags` independently labels budget overruns, missed II, invalid settings, HLS timing warnings, host OOM, and failed routed timing.

HLS budgets are DSP <= 1248, BRAM18K <= 288, URAM <= 64, LUT <= 81984, and FF <= 163968. LUT/FF budgets use 70% of device capacity. Resource feasibility does not establish physical timing. Millisecond values retain `cycles * max(target period, HLS estimated period) / 10^6`; clock uncertainty must still be checked. PE/layer results are separate from frame results.

## Regeneration

Requirements: Ruby, Node.js, and `dagre@0.8.5`. Ruby uses only standard libraries. These commands do not modify HLS workspaces or execute hardware experiments.

From the repository root:

```sh
ruby docs/experiment-evolution/generate.rb
ruby docs/experiment-evolution/generate.en.rb
node docs/experiment-evolution/render.cjs
node docs/experiment-evolution/render.cjs --lang en
node docs/experiment-evolution/render.cjs --check
node docs/experiment-evolution/render.cjs --lang en --check
git diff --check
```

`render.cjs` first uses `DAGRE_MODULE`, then a local Node module, then version 0.8.5 in npm's `_npx` cache. If needed, install the dependency in an isolated temporary directory:

```sh
npm install --prefix /tmp/srcnn-map-tools dagre@0.8.5
DAGRE_MODULE=/tmp/srcnn-map-tools/node_modules/dagre node docs/experiment-evolution/render.cjs --lang en
```

Dagre lays out directed graphs, with orthogonal SVG edges and content-sized nodes. English labels wrap at word boundaries. `--check` detects stale diagrams, text/node boundaries, node overlap, nonorthogonal edges, and edges crossing nodes. `layout.json` and `layout.en.json` retain the geometry used by these checks.

## Rendering Checks

Local preview and geometry checks use `@larksuite/whiteboard-cli` 0.2.13. They write local images and do not create external documents:

```sh
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.en.svg -f svg --check
npx -y @larksuite/whiteboard-cli@0.2.13 -i docs/experiment-evolution/overview.en.svg -o /tmp/srcnn-experiment-overview-en.png -f svg -s 1
```

This language update verified identical measurements, statuses, evidence, and 207 dependencies across all 153 experiments. Regeneration consistency and layout checks passed for all 13 diagrams in each language. All 13 English SVGs passed XML parsing and external geometry checks with zero errors or warnings; the overview, continuous pipeline, and verification diagrams were rendered and visually inspected. All 3,000 local links and anchors across the 10 related Markdown files passed. HLS experiments were not rerun for this documentation update.

For new experiments, verify original evidence, update both catalogs and guides, regenerate both languages, and check their coverage and layout. Translation generation rejects missing or duplicate IDs and preserves shared measurements and dependencies.
