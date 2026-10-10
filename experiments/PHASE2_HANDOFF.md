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
