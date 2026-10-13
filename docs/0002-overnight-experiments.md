# Isolated SRCNN HLS experiments

## Problem and contract

Explore precision, compiler directives and streaming architectures while preserving `src/`, `test/`, weights, golden data and any existing workspace. Use branch `exp/overnight-1011`, commit local results after each experiment, never push. Network shape, replicate padding, float external parameter signature and data layout are unchanged.

## Plan

1. Archive checksums, audit tools, establish original C/HLS baseline.
2. Measure ranges on every supplied Set14 pair. Model AP_RND_CONV and AP_SAT explicitly; retain full product precision in an adequately sized accumulator and quantize only at layer boundaries. Verify a float numpy model against the unchanged C implementation before the scan, then check representative settings against actual AMD ap_fixed.
3. Copy golden with loop labels for configuration-only compiler studies.
4. Build a read/pad/conv12/pad/conv3/write stream pipeline using bounded line buffers. Parameterize integer schedule, unroll dimensions and weight memories. Prove token counts and border behavior; use fixed-point exact reference comparison before synthesis eligibility.
5. Scan T, bank/unroll/storage choices and target clocks by coordinate rounds. Keep failed, infeasible and timed-out jobs visible. Implement a validated feasible candidate only if one exists.
6. Explore scatter and small multiplier kernels, then regenerate plots and final summary.

## Experiment runner

Each ID owns `workspace/exp_runs/EXXX`, immutable input source snapshot, generated `hls_config.cfg`, process lock and timeout-managed log. Archive configurations, raw report excerpts, parsed metrics and narrative under `experiments/EXXX_name`. `results.csv` and markdown numeric tables are generated from structured reports/validation output, not manually copied. Unknown metrics remain blank, never zero. Original success-only tests run alongside a new failure-propagating testbench.

Windows subprocesses call `settings64.bat`; verified Linux subprocesses source `settings64.sh`. CLI options are probed with help before use. Settings and environment paths are configuration, never credentials. Local and remote protected inputs must match checksums before running.

## Failure modes

- Missing tools/data, compile errors, model mismatch, saturation and partial Set14 coverage are explicit failures or limitations.
- A 60-minute synthesis timeout kills the entire process group. Repeated tuning of one issue stops within 45 minutes; fallback module experiments remain labeled as module results.
- Float addition is order-sensitive; integer accumulation is reorder-invariant only when fractional precision is preserved and intermediate overflow is impossible. Boundary casts must match the precision reference.
- HLS array-port limits, accumulator dependencies, automatic outer-loop unrolling, FIFO deadlock and large line/window partitioning can prevent intended II or resource feasibility.
- HLS timing/resource estimates do not prove implementation timing, AXI system integration, or board operation. Actual implementation is recorded separately.

## Acceptance

Preserve protected SHA256 hashes and user edits. Float output is compared directly with unchanged C golden and binary references. Fixed output passes the supplied-image average PSNR drop of at most 0.1 dB and architecture output is bit-identical to actual ap_fixed reference on butterfly; all designs record six-pixel border MSE. Full 14-image acceptance needs the missing image. Resource caps are DSP 1,248, BRAM18K 288 (144 BRAM36), URAM 64, LUT 81,984, FF 163,968. Record every observed pipelined-loop II and separate requested from achieved II.

Reports, plots and reproduction instructions live in [experiments](../experiments/SUMMARY.md); [experiment progress](../experiments/PROGRESS.md) is the recovery entry point.

## Integer-carrier control

The independently copied `dataflow_int` design retains the streaming topology and
float external signature. AMD ap_fixed performs input/parameter quantization;
full-width integer products and bounded sums retain every fractional bit.
Layer casts explicitly implement signed floor, nearest-even rounding and
saturation. Native signed 32-bit C-simulation carriers and synthesized ap_int
carriers are equivalent under the archived trained-parameter absolute-sum bounds;
no CPU-only alternate convolution is used. Butterfly must match E019 bit for bit
before any synthesis, and selected final candidates must run every supplied image.
This control also measures whether simpler boundary logic reduces LUT overhead.

The authorized follow-on architecture phase is documented in
[architecture exploration](0003-architecture-exploration.md), with its own
branch, pre-implementation estimates and frozen first-phase designs.

