# First-phase evidence for the authorized architecture exploration

These are unimplemented hypotheses, retained across the phase-one finalizer's
PROGRESS.md rewrite. They are not synthesis results. Every phase-two idea still
needs its own pre-implementation estimate in the corresponding experiment file.

- Packing: split a generic signed10 coefficient into signed-low8 plus 256 times
  a residual in [-2,2]. Implement the residual with add/subtract/shift logic and
  retain fraction9. Gap18 permits one generic signed10-input term, two
  nonnegative activation terms in [0,511], or seven true signed-INT8 terms.
  Correct the high field when the signed low18 field is negative. Probe the DSP
  builtin separately: the installed SDK header rejects __PRESYNTHESIS__.
  Ordinary DSP-bound multiplication is a fallback; inspect actual pre-adder use.
- Conv3 packing: adjacent nonnegative activations share a coefficient. Pack
  ((a-256)<<18)+b in signed27, multiply by signed-low8, undo the borrow and add
  256*coefficient to the high result. Restore the coefficient residual exactly.
  A 5x6 window, padded260x259 stream and discarded neighbor column255 cover the
  odd width without changing the quantization points.
- Winograd: G2/BT/AT from SOURCES.md, full transform precision and an exact
  divide-by-four before the layer cast. Nine prior rows and a 10x10 window over
  padded264x264 produce 128x128 tiles; discard output row/column255. Two raster
  row FIFOs of depth512 are a conservative alternative to stream_of_blocks
  double buffering. Include their wide-memory cost and finite-FIFO ordering.
  Runtime integer weight transforms preserve incoming float parameters;
  archive equivalent offline transforms and measure load overhead.
- Continuous direct schedule: separate window generation from matrix engines,
  flatten pixel/fold iterations, and explicitly register a balanced fabric
  reduction. Wide shallow window streams need LUTRAM/register estimates. This
  targets measured Conv1 fill/drain and the E070 DSP cascade critical path.
- Online padding: cache the first row, emit its radius+1 copies, then read and
  emit each interior row concurrently while caching the latest row for the
  bottom repeats. Replicate the first/last pixel horizontally. This removes
  the existing full-row read/write serialization; validate finite-FIFO timing
  with two-frame cosim. Keep a measured control with the old padding schedule.
- Scatter boundary kernels: nine source classes (top/interior/bottom times
  left/interior/right), exact merged taps, fraction9 and wider coefficients.
  For output offset dy, interior ky=2-dy, top merges ky<=2-dy and bottom merges
  ky>=2-dy; analogous x. Five 32-bit row banks and a 5x5 register window; prime
  columns0/1 and flush two final rows/columns. Compare explicit-pad scatter at
  identical precision/T/clock.
- DDR scratch: srcnn's fixed eight-argument contract has no scratch parameters.
  Probe global m_axi support and retain any tool rejection; never append
  arguments or write outside supplied arrays. Tile fusion must replicate
  Conv2 features at real image edges. A BxB output needs (B+12)x(B+12) input and
  (B+4)x(B+4) feature areas. DS987 supplies 19.2 GB/s theoretical bandwidth;
  9.6 GB/s assumes the requested 50% efficiency and is not measured bandwidth.

After creating exp/explore-arch, migrate local and remote CSV schemas with
series, widen runner/commit ID guards, and support immutable preplanned archives
so EXXX.md estimates are committed before implementing each design. Derive CSV
scope markers for PE/layer/frame records so microkernel latency never enters
network rankings. Cosim uses two butterfly frames with Set14 disabled; full
supplied-image precision is validated separately. The missing comic pair still
prevents complete Set14 acceptance.

## Implementation notes from continued first-phase report inspection

These are still proposals, not second-phase results.

- P PE sequence: DSP-bound signed8 pair, direct two-product control, group7
  signed8 accumulation, auto-mapped add/multiply alternative, installed DSP
  builtin (may reject __PRESYNTHESIS__), group2 nonnegative activation, exact
  signed10 coefficient residual. Inspect actual DSP48E2 pre-adder attributes
  from a PE implementation checkpoint; an HLS DSP count alone cannot prove
  pre-adder use. Group2 is unsafe for generic signed10 input because
  2*(-128)*(-512)=131072 overflows signed18. It is safe for nonnegative
  raw activations 0..511. Test extrema and many deterministic random triples.
- Full P: Conv1/Conv2 pair output channels, share one input. Conv3 processes
  adjacent output pairs with a 5x6 window over 259x260 padded data. Use 2*T
  folds and 16/T input-channel lanes to halve Conv3 DSP at unchanged pixel
  throughput. Keep both high-borrow repair and +256*coefficient correction
  for a centered upper activation. Discard column255. Residual [-2,2]
  products use explicit shifts/adds, preserving original fraction9.
- C simulation must widen a packed27*coefficient8 product to int64, and a
  Winograd18*20 product to int64, without widening synthesis multiplier
  operands. Native carriers do not automatically wrap like ap_int; explicitly
  sign-extend extracted low18 bits rather than casting to word<18> on CPU.
  Avoid left-shifting negative native signed integers; constant multiplication
  or unsigned bit construction expresses the same hardware safely.
- W PE sequence: exact G2 integer F2 kernel at10 bits, direct36-product
  control, then16-bit mapping. Random matrix algebra already checked40000
  outputs per width without recording a hardware result. Full inverse
  intermediates conservatively need W+A+14 signed bits (34 for10-bit,
  46 for16-bit). Divide by4 exactly before adding the ordinary Conv1 bias
  and applying its layer cast. Full network can retain w10a10 acceptance.
- W layer: top-layer-only output should be a pixel1 AXIS stream to avoid
  a64-channel scalar DDR writer dominating the compute measurement. A new
  exp/tb checker can compare every channel/pixel with first-phase direct
  Conv1 and actual-ap_fixed boundary casts. Full SRCNN still uses its original
  float-array signature. Weight G2 transforms must run in the internal load
  stage to honor arbitrary runtime weights; archive equivalent offline
  transformed parameters and document that contract conflict explicitly.
- W full schedule: 9 prior rows, 10x10 window,264x264 padding (left/top4,
  right/bottom5),128x128 output tiles. Each tile costs4*T folds; output-channel
  lanes are64/(4*T), so beginT16 orT8. Unroll9*16 products per lane.
  Raster reorder can route each tile into top/bottom pixel FIFOs depth512,
  then consume255 pixels from the appropriate FIFO per raster row.
  Two FIFOs allow the next tile row to overlap bottom-row consumption;
  a read-whole-tile-row/write-whole-bottom-row schedule adds about50%
  overhead. Bind shallow wide tile/window FIFOs to LUTRAM, and separately
  report the BRAM cost of the two640-bit row FIFOs.
- G edge: process source rows0..H-1 and flush2 rows. Prime with x=-2,-1,
  consume source columns0..W-1, then flushW,W+1. Before shifting, write the
  old window column to cache columnx-3; load cache columnx+2 into the new
  rightmost window. Map physical row banks to output rowy-2+r, reset the
  newest row, and emit window[0][0] when y>=2,x>=2. Last columnW-1 is saved
  after each row. Nine source-position classes merge taps; coefficients
  need15 bits for generic signed10 inputs and preserve fraction9. The
  merged kernel is9*32*25*15=108000 bits, much larger than the original
 8000-bit Conv3 weights; include LUTRAM banking and load overhead.
- F continuous: split window production from matrix filtering. Flatten
  pixels/folds into a single H*W*T loop with II1, consume a new window or
  pixel only on step0, and emit on stepT-1. Shift a fixed channel register
  array by the output-lane count each iteration instead of writing at
  variable channel indices. Use balanced reductions with fabric adders
  explicitly bound to latency1 to test the E070 unregistered DSP cascade.
  Conv3's per-fold partial reduction plus one registered carried sum can
  keep II1. Measure an old-padding control and the online-padding follow-up.
- F memory: first-phase dataflow has BRAM-mapped tiny wide FIFOs: Conv1
  features36, features2~18, padded3~18 BRAM18K. Explicit LUTRAM FIFOs may
  save about72 BRAM18K for modest LUT cost; retain depths for the first
  control and verify finite-FIFO behavior by two-frame cosimulation.
  An URAM Conv3 line-buffer control needs roughly4*ceil(320/72)=20 URAM,
  trading much wasted capacity for the36-BRAM18K gather line buffer.
- F optional boundary encoding: use installed hls::fp_struct<float> to
  implement finite IEEEfloat nearest-even/saturating casts and exact
  raw10/256 output encoding without FP converters. Preplan a microbenchmark
  against real ap_fixed first, with exponent/extreme/tie and random finite
  bit patterns plus all1024 raw outputs. Do not use unsafe pointer aliasing.
- S tiling: output blocks8/16/32/64 need inputB+12 and featuresB+4. Clamp
  the global feature center before locating its9x9 input patch, so virtual
  feature centers replicate actual Conv2 features at borders. Suggested
  banks: input cyclic9x9 LUTRAM; feature1 packed640-bit BRAM; feature2
  spatial cyclic5x5 with C3_IC channel banks in LUTRAM. Write Conv2 channels
  per fold to respect the limited channel-bank ports. Sequential layer
  execution per block removes dataflow overlap, and halo work must be
  counted separately from input traffic. B64 feature1 alone may exhaust BRAM.
  A preferable first tile implementation can fuse Conv1 then Conv2 per feature
  pixel, retaining only a64-channel register vector and the full feature2
  cache. This eliminates feature1 BRAM entirely. Use spatial5x5/channel-C3_IC
  LUTRAM banks for feature2. For a clamped feature center cy, the input-cache
  9x9 patch begins at cy-tile_origin+2; interior centers simplify that index
  to the feature-grid row. Fixed-size partial edge blocks may compute unused
  cells; count scheduled feature centers and input reads, not only valid outputs.
- S DDR: probe global m_axi first; enforce the presence of the requested
  scratch AXI bundles in the generated interface before calling any result
  DDR. If rejected/ignored, retain the failure and a bandwidth-only model,
  and put the need for a scratch-pointer contract in pending decisions.

Final-phase infrastructure must support pre-existing plan-only archives and
preserve their purpose/estimate text. Transfer those plans to the remote host.
Create a SHA256 manifest for all first-phase design files when phase two starts
and verify it alongside the original46-file manifest. Model/kernel experiments
must be scoped outside frame rankings; derive all numerical comparison tables
and CSV-only plots from results/config/report records. Candidate verification
IDs can use F80+, with separate actual routed and RTL measurements.
