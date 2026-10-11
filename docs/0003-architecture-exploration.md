# SRCNN architecture exploration

## Contract and acceptance

Start from completed first-phase commit on `exp/overnight-1011` and work on
`exp/explore-arch`, committing locally after each experiment. Preserve original
source/data and all first-phase designs. The float-array `srcnn` signature,
runtime parameter loading, tensor layout and replicate padding remain fixed.
Missing comic prevents full Set14 acceptance; all supplied-image candidates
remain explicitly provisional.

Packing must preserve integer results exactly. Integer G2 Winograd transforms
retain complete intermediate precision and divide the inverse result exactly
by four before applying the ordinary layer cast. Keep AP_RND_CONV/AP_SAT at
the same boundaries. Frame designs compare all butterfly pixels and six-pixel
borders against the independently verified first-phase precision reference;
new frame simulations run twice. Final candidates also cover every supplied
image and receive implementation and two-frame RTL cosimulation.

## Experiment lifecycle

Each S/G/P/W/C/F experiment first archives a purpose, paper DSP/memory/T/cycle
estimate and its assumptions via `exp/plan_arch.py`. Commit that plan before
creating the design. The runner rejects changed parameters, changed purpose,
reused workspaces and already-run archives. Its generated numeric sections
remain derived from reports. `results.csv` gains `series`, preserving all
first-phase rows through a checked schema migration.

Explore P/W PEs, G padding/edge scatter, S dataflow/DDR/tile organization,
full P/W, combinations, then F scheduling/memory/timing ideas. New designs
live in independent directories. PE/layer/frame scope is recorded in config
and derived CSV; microkernel cycle counts cannot enter frame rankings.
Explain estimate deviations over20 percent using scheduling/resource evidence.
Completed IDs are reserved. `exp/reproduce_exp.py` allocates a new ID, restores
the archived design and the recorded Git testbench sources, and uses the existing
runner to replay the measurement. P09 validates this path against P01; see
[reproduction instructions](../experiments/REPRODUCE.md).

## Failure modes

- Packed low fields have precision-dependent limits; signed10 input needs
  unpacking every product, while nonnegative0..511 allows two terms at gap18.
- Native CPU products must widen without widening synthesized DSP operands.
- Winograd needs wider transforms, exact inverse scaling, raster reordering
  and separately measured FIFO memory. Runtime transforms preserve the fixed
  incoming-weight contract; equivalent offline transforms are also archived.
- Scatter must reset new partial-sum rows, prime/flush columns, merge edge
  kernels exactly and avoid BRAM read/modify/write hazards.
- Tile features must replicate real edge features. Clamping virtual input
  coordinates alone does not reproduce Conv3 feature padding.
- DDR scratch requires real exported AXI ports; ignored global directives
  invalidate that architecture. DDR estimates use DS98719.2GB/s and the
  requested9.6GB/s scenario, and HLS timings remain lower bounds.
- Software streams do not prove finite-FIFO progress. Retain deadlock detection
  in RTL cosimulation, with a six-hour process-tree timeout.
- Wide held-window dynamic selectors and explicitly registered reductions can
  dominate LUT/FF after II1 is reached. F13-F15 test channel rotation and
  reduction latency using the measured F08 module costs; retain any LUT/FF
  infeasibility or increased estimated clock instead of changing the gates.
- W17/W18 isolate raw-weight channel banking after W09/C12 measured large
  register and selector costs in the T8 transform loader. Original weights
  serve only the sequential transform, so a deeper single channel bank may
  reduce those costs while retaining the MAC engines' transformed banks.
  This attribution is a hypothesis; compare exact outputs, loader reports,
  total resources and achieved II before accepting it.
- F20 exhausts all signed ten-bit output carriers and measures exact IEEE
  construction with zero DSP. F22/F23 retain the archived F13 network and
  replace only output decoding at3ns/2.5ns target clocks. The PE's2.051ns
  estimate cannot establish the full network's critical path or routed timing.
- F23's2.822ns global HLS path is the one-time Conv1 weight loader's address
  multiplier, while its dataflow region reports2.377ns. F24 preplans an
  independent affine channel/row/column loader to test that measured bottleneck.
  Keep runtime weights and all inference stages fixed; account for nested-loop
  restart overhead and require exact outputs before accepting clock changes.
- F24's affine loader removes that multiplier but automatic flattening leaves
  a2.699ns compare/and/select/add/store counter path. F25 preplans a separate
  LOOP_FLATTEN-off control, budgeting per-row pipeline drains and preserving
  every inference stage. Compare actual clock times actual cycles before
  selecting either loader; end this control investigation after that comparison.

Synthesis is serialized for the15GiB remote host, with60-minute per-run timeout
and45-minute issue-tuning limit. Generated HDL/cache/binaries remain outside
commits. Existing ignore rules and user edits stay preserved. See
[progress](../experiments/PROGRESS.md), [sources](../experiments/SOURCES.md) and
the eventual [architecture summary](../experiments/ARCH_SUMMARY.md).

## Physical verification recovery

F81's kernel OOM evidence shows that Vivado's internal synthesis workers can
exceed the host memory budget even with one HLS operation active. Preplan
independent F89-F91 retries of the three selected candidates. Reuse the original
HLS-generated IP/BD implementation driver and its target clock/directives, adding
a formal pre-synthesis Tcl hook for `general.maxThreads=1` and
`synth.maxThreads=1`. Run this generated flow directly in a fresh workspace;
do not alter global Vivado settings, system swap, frozen parents or gates.
Archive the patched driver, hook, original-template provenance and SHA256 values.
Require actual routed utilization/timing reports and keep the original OOM
records. All-supplied-image validation and two-frame RTL cosim remain independent.
