# Report section draft: Final Architecture

Draft for the *Final Architecture* chapter of the course report (Notion page "Agent-Driven Design Space Exploration for HLS Acceleration of SRCNN on the Kria KV260"). It replaces the current *Algorithm optimization strategy* subsection and adds material to *Dataflow*. Every number is traceable to an experiment card under `experiments/` or to `plain/C17_srcnn_plain.cpp`; the figure files are in `docs/figures/C17/`.

Granularity rule used throughout: one design decision per paragraph, backed by one measured number. Code appears only where a line is itself the decision. The complete sources stay in the two linked sub-pages (original and readable version).

Sections marked **[keep]** are already on the Notion page and are not repeated here; sections marked **[replace]** or **[new]** are the draft text.

---

## 4 Final Architecture

### 4.0 Introduction  **[replace the two paragraphs after the code links]**

The selected design is the one carried through all four verification steps: C17 (C simulation and HLS synthesis), C20 (C/RTL co-simulation) and C22 (Vivado place and route at 5 ns). Its source was produced by the agent over about 200 experiments. For reading, we had the agent rewrite it as a plain version with the macros substituted and the templates expanded, and re-ran C simulation and synthesis on both: the outputs are bit-identical and the synthesis results are the same. The plain version is what the code excerpts below are taken from.

This chapter does not walk through the code. It explains the design one decision at a time: what constraint forced the decision, which experiment measured the alternatives, and what the chosen structure costs. Section 4.1 covers the dataflow skeleton that all three layers share, 4.2 the resource budget that decides what each layer may use, and 4.3 to 4.5 the three layers in turn.

### 4.1 Dataflow  **[keep, then add the table below after the FIFO paragraph]**

**[new]** Table 4.1 lists every process in the dataflow region with the shape and width of the element it passes on, the FIFO depth, the memory it keeps internally, and three numbers about time per frame. *Iterations* is the loop trip count read from the source: for a loop with II = 1 it is the number of cycles the stage needs when it is never blocked. The other two are measured in the C/RTL co-simulation C20, where every process is instrumented over two frames: *active cycles* is the process latency within the frame minus the cycles it spent waiting on a FIFO, and *stall* is that waiting share. The measured active cycles reproduce the source trip counts to within 0.1 % for every stage except the engines, which carry their weight-load prologue (about 700 to 2,200 cycles) and pipeline fill on top, and `read_input`, whose AXI reads add about 13,000 cycles. The three engines are busy for about 261,000 to 263,000 of the 273,052 cycles of the frame and wait 2.5 % to 4.4 % of the time; every other stage is busy for at most 79,000 cycles and waits 67 % to 76 %. The engines set the frame time, and the measured frame (273,023 cycles) is within 4 % of the 262,144-iteration bound of the slowest engine. Figure 3 and Figure 4 show the same measurement per FIFO and per process.

**Table 4.1** Stages of the dataflow region of the selected design (C17), in data order. Element widths are the aggregated stream width in bits; memory is what the stage keeps on chip (routed, C22); iterations are loop trip counts from the source per 255×255 frame; active cycles and stall are from co-simulation C20 (`profiling/processes.csv`, `process_latency_avg_cycles` minus half of `stall_cycles`, and `stall_pct`, over two frames).

| Stage | Input → output element | Width (bits) | FIFO depth (out) | Internal memory | Iterations per frame (source) | Active cycles per frame (C20 measured) | Stall (C20 measured) |
|---|---|---|---|---|---|---|---|
| `read_input` | float from DDR → pixel `ap_int<10>` | 10 | 512 | none | 65,025 | 78,653 | 66.9 % |
| `online_pad1` | pixel → pixel, 255² → 264² replicate-padded | 10 | 16 | 1 row, 255 × 10 b (1 BRAM18K) | 69,696 | 69,962 | 72.9 % |
| `wino_windows` | pixel → transformed window, 9 sub-blocks × 16 × `ap_int<12>` | 1,728 | 32 (LUTRAM) | 9 rows × 264 × 10 b (9 BRAM18K) + 10×10 window registers | 69,696 | 69,699 | 73.1 % |
| `wino_engine` | window → tile, 2×2 pixels × 64 ch × 10 b | 2,560 | 2 (LUTRAM) | transformed weights 64 × 9 × 16 × 14 b = 129 kb (LUTRAM) | 262,144 | **262,924** | **2.5 %** |
| `distribute_tiles` | tile → 2 pixel streams (`top`, `bottom`), 64 ch × 10 b | 640 | 512 each (BRAM, 18 BRAM18K each) | none | 65,536 | 65,537 | 74.8 % |
| `reorder_rows` | 2 streams → raster-order pixel, 64 ch | 640 | 4 | none | 65,025 | 65,026 | 75.4 % |
| `conv2_stream` | 64-ch pixel → 32-ch pixel | 320 | 4 | packed weights 16 × 64 × 27 b = 27.6 kb (LUTRAM) | 260,100 | **262,275** | **3.2 %** |
| `online_pad3` | pixel → pixel, 255² → 259² padded | 320 | 16 | 1 row, 255 × 320 b (9 BRAM18K) | 67,081 | 67,347 | 75.3 % |
| `windows3` | pixel → two half windows, 25 taps × 16 ch × 10 b each | 4,000 + 4,000 | 2 + 2 | 4 rows × 259 × 320 b (36 BRAM18K) + 5×5×32 window registers | 67,081 | 67,084 | 75.4 % |
| `engine3` | two half windows → output pixel | 10 | 16 | weights 32 × 25 × 10 b = 8 kb (LUTRAM) | 260,100 | **260,977** | **4.4 %** |
| `write_output` | pixel → float to DDR | 32 | – | none | 65,025 | 65,042 | 76.2 % |
| `read_params` → `transform_params1` | 8,129 floats → three parameter streams | 224 / 10 / 10 | 4 / 16 / 16 | raw 9×9 kernel registers | 8,129 + 640 | 11,101 | 0.2 % / 1.4 % |

Two widths in the table are decisions rather than consequences. The window FIFO in front of the Winograd engine is 1,728 bits wide and 32 deep: the width is nine transformed 4×4 blocks and the depth is the one change between C13 and C17 (Figure 3 inset). The conv3 window is 8,000 bits and is carried as two 4,000-bit streams because Vitis HLS rejects an aggregated stream wider than 4,096 bits; the first attempt at this layer (C09) failed synthesis with exactly that error.

### 4.2 Resource allocation across the three layers  **[keep the MAC-share table, replace the rest with this]**

MACs decide resources. If a layer must deliver one output pixel every T cycles it needs MAC/T multipliers, so the layer with the largest MAC share also has the largest claim on DSPs, and the reduction techniques should go where the MACs are. The device has 1,248 DSP48E2 slices. Table 4.2 shows the DSP count for each fold factor T and each combination of the two multiplication-reducing techniques; it is a paper calculation, but every row marked with an experiment ID was synthesised and the measured DSP count is within ±4 of the paper number.

**Table 4.2** DSPs needed per layer as a function of the fold T (cycles per output pixel), for the direct algorithm and for the selected reductions. Products per pixel: conv1 direct 5,184, conv1 Winograd 2,304; conv2 direct 2,048, conv2 packed 1,024 DSP-equivalents; conv3 800. The device limit is 1,248.

| T | conv1 direct | conv1 Winograd | conv2 direct | conv2 packed | conv3 direct | Total, all direct | Total, Winograd only | Total, Winograd + packing | Measured |
|---|---|---|---|---|---|---|---|
| 1 | 5,184 | 2,304 | 2,048 | 1,024 | 800 | 8,032 | 5,152 | 4,128 | – |
| 16 | 324 | 144 | 128 | 64 | 50 | 502 | 326 | 258 | W18: 326 |
| 8 | 648 | 288 | 256 | 128 | 100 | 1,004 | 644 | 516 | F29/F30: 1,004; W21: 644; C10: 520 |
| 4 | 1,296 | 576 | 512 | 256 | 200 | **2,008** | **1,288** | **1,032** | C13/C17: 1,032 |
| 2 | 2,592 | 1,152 | 1,024 | 512 | 400 | 4,016 | 2,576 | 2,064 | – |

The table says three things. At T = 16 and T = 8 the direct algorithm fits, so the reductions only save DSPs and do not shorten the frame; that is why W18 (T = 16, Winograd) has the same cycle count as the direct design with 326 instead of 502 DSPs. At T = 4 direct conv1 alone needs 1,296 DSPs, more than the device has, and even Winograd conv1 with direct conv2 needs 1,288. T = 4 is reachable only with both techniques together, and T = 2 is out of reach with any combination. So the selected design is the fastest fold that fits, and it needs Winograd on conv1 and packing on conv2 to get there; conv3 is small enough to stay direct.

Figure 2 shows the result: after the reductions the three layers need 151 M, 133 M and 52 M multiplications per frame, and with 576, 256 and 200 DSPs they take 262,144, 260,100 and 260,100 cycles. Because the stages run concurrently, the frame time is set by the slowest; the three loop counts are within 1 % of each other, which is the balance that T = 4 achieves. Figure 1 shows what each engine computes in each of its T cycles.

### 4.3 conv1: Winograd on nine 3×3 sub-kernels  **[replace the whole Winograd subsection]**

**Budget.** conv1 is 64.5 % of the MACs: 81 taps × 64 output channels = 5,184 products per pixel. At T = 4 that is 1,296 DSPs, which does not fit on its own (Table 4.2). The layer has to compute with fewer multiplications, not just fewer DSPs per multiplication, because its operands are 10-bit and cannot be packed two per DSP once they are transformed (see 4.4).

**Principle.** Winograd's minimal filtering trades multiplications for additions. The smallest case, F(2,3), computes two outputs of a 3-tap filter from four inputs with 4 multiplications instead of 6:

```txt
direct:   y0 = d0·g0 + d1·g1 + d2·g2        y1 = d1·g0 + d2·g1 + d3·g2       (6 mul)

Winograd: m1 = (d0 − d2)·g0                 m2 = (d1 + d2)·(g0 + g1 + g2)/2
          m3 = (d2 − d1)·(g0 − g1 + g2)/2   m4 = (d1 − d3)·g2
          y0 = m1 + m2 + m3                 y1 = m2 − m3 − m4                (4 mul)
```

The weight-side terms (g0 + g1 + g2)/2 are computed once when the weights are loaded; the input-side terms d0 − d2 and the output sums are additions, which go to LUTs. The 2-D form F(2×2, 3×3) applies the same transforms along rows and columns: a 4×4 input tile is transformed (Bᵀ d B), multiplied element-wise by the transformed 3×3 kernel (G g Gᵀ), and the 4×4 product is transformed back (Aᵀ m A) to a 2×2 output tile. That is 16 multiplications instead of 36 per 2×2 tile, 2.25× fewer.

**Keeping it exact in integers.** The only constants in these transforms are 1 and ½. We multiply G by 2, so the transformed weights are integers and the result is scaled by 4; the engine shifts right by 2 before rounding, and the result is bit-exact with direct integer convolution. W01 checked this exhaustively on a 32-tile processing element before any of it was integrated, and the full-frame designs compare every pixel, including the six-pixel border, with the independently computed numpy reference. With 10-bit pixels and weights the transformed operands are 12 and 14 bits, which is why one product is one DSP.

**Why nine 3×3 sub-kernels, and why 2×2 output tiles.** The 9×9 kernel is cut into a 3×3 grid of 3×3 sub-kernels (the `group` index in the code). A 9-tap convolution is the sum of three 3-tap convolutions applied to the input at offsets 0, 3 and 6, and in two dimensions the 9×9 convolution is the sum of nine 3×3 convolutions at offsets (3a, 3b); nothing is approximated by the split. Each of the nine 3×3 convolutions is then computed with Winograd F(2×2, 3×3), which produces a 2×2 block of outputs from a 4×4 block of inputs with 16 multiplications instead of 36. The 2×2 output tile therefore needs a 10×10 input window (2 + 9 − 1 in each direction), and sub-kernel (a, b) reads the 4×4 sub-block of that window starting at row 3a and column 3b; neighbouring sub-blocks share one row or column because a 3×3 kernel on a 2×2 tile needs 4×4 input. The nine 4×4 products are added in the transformed domain and the output transform runs once on the sum, which is valid because the transform is linear. One tile costs 9 × 16 = 144 multiplications for 4 pixels, 36 per pixel against 81 direct, a 2.25× reduction.

Working in 2×2 tiles has a price downstream. The engine emits one tile every 16 cycles, but conv2 consumes pixels in raster order, so two processes after the engine (`distribute_tiles`, `reorder_rows`) split each tile into its upper and lower pixel pair and interleave even and odd rows back into scan order. Holding the odd rows until the even rows have gone out takes two 512-deep, 640-bit FIFOs, 36 BRAM18K, which is the largest memory cost of this layer, larger than the 9-row line buffer itself (9 BRAM18K). The padded image is also made 264×264 instead of 263×263 so that 128 × 128 tiles cover it exactly; the extra output row and column are discarded.

The tile size is a free parameter of Winograd: F(m, 3) computes m outputs per 1-D tile for any m, and m = 255 would process a whole image row at once. Larger tiles save more multiplications (per output pixel, ((m + 2)/m)² against 9: 4 for m = 2, 2.25 for m = 4, approaching 1), so the question is why m = 2 is used. The answer is the transform constants. F(m, r) is built from polynomial interpolation at m + r − 1 points; for m = 2 those are 0, 1, −1 and ∞, and the resulting matrices contain only 0, ±1 and ½, which is why multiplying G by 2 makes everything integer and a 2-bit shift restores the result exactly. For m = 4 the interpolation needs six points (adding ±2), and G contains 1/4, 1/6, 1/12 and 1/24: the smallest integer scaling is 24 per dimension, the result comes out 576 times too large, and dividing by 576 is no longer a shift, so the exactness argument of the previous paragraph is lost and a divider or a rounding step has to be added. For m = 6 and beyond the constants grow to 1/180 and smaller and the operand widths with them; these tiles are known to be numerically unstable even in floating point. The hardware adds a second limit. The transformed window is streamed as one element every T cycles, and its width is 9 sub-blocks × (m + 2)² values × the transformed width: 1,728 bits for m = 2, but about 5,500 bits for m = 4 (36 values per sub-block, 17-bit operands), above the 4,096-bit aggregate stream limit of Vitis HLS that C09 ran into. Finally, a smaller conv1 would not shorten the frame on its own: with m = 4 conv1 needs 324 DSPs instead of 576 at T = 4, but the frame time is set by T, and moving the whole network to T = 2 fails on conv2 and conv3 regardless (Table 4.2). Table 4.3 collects the options. F(2×2, 3×3) is the only tile that is exact with shifts, nine of them cover the 9×9 kernel without padding, and it is the one that was built and measured.

**Table 4.3** Options for conv1 at T = 4. Only the first two were synthesised; the F(4×4, 3×3) row is a paper estimate and was not pursued for the reasons in the text.

| Algorithm | Products per output pixel (64 ch) | DSPs at T = 4 | Transform constants | Exact with integer shifts | Window stream width |
|---|---|---|---|---|---|
| Direct 9×9 | 5,184 | 1,296 (> 1,248) | – | yes | 10 b pixel |
| Nine 3×3 sub-kernels, F(2×2, 3×3) **(selected)** | 2,304 | 576 | 1, ½ | yes (G × 2, result >> 2) | 1,728 b |
| Nine 3×3 sub-kernels, F(4×4, 3×3) | 1,296 | 324 | 1, ½, ¼, 1/6, 1/12, 1/24 | no (scale 24², division by 9 remains) | ≈ 5,500 b (> 4,096 limit) |

**What it costs.** The PE experiments W01 and W02 measured the trade on one kernel: 16 DSPs against 36 for the direct control, both at II = 1, for about 1,000 extra LUTs of add/subtract transforms (1,499 against 503). In the full design the Winograd engine is 576 DSPs and, after routing, 17,139 LUTs; the window generator with its 9-row line buffer is 3,290 LUTs and 9 BRAM18K. The largest memory cost of this layer is not the Winograd arithmetic but the raster re-ordering it forces: the engine produces 2×2 tiles, so two 512-deep, 640-bit FIFOs (36 BRAM18K) hold the odd rows until the even rows have gone out.

**Pipeline.** The layer is four processes (Table 4.1). `wino_windows` slides a 10×10 window over the padded 264×264 image with a 9-row line buffer, and every second row and column emits the nine transformed 4×4 sub-blocks as one 1,728-bit element. `wino_engine` spends 16 cycles per window: in each cycle 4 output channels (4 lanes × 9 sub-blocks × 16 taps = 576 DSP products) are accumulated in the transformed domain, output-transformed, shifted, biased, and passed through ReLU and the round-to-10-bit quantiser; the 64 channels of the 2×2 tile are collected in a shift register and written after cycle 15. `distribute_tiles` and `reorder_rows` turn tiles back into raster order and drop the extra row and column that the padding added so that 2×2 tiles cover 255 pixels. The fixed-point widths along this path are the top row of Figure 5.

### 4.4 conv2: two output channels per DSP  **[new]**

**Budget.** conv2 is 25.5 % of the MACs: 64 input channels × 32 output channels = 2,048 products per pixel, 512 DSPs at T = 4. Winograd does not apply to a 1×1 kernel: there is no spatial overlap to exploit. Table 4.2 shows that without a reduction here the design does not fit (1,288 DSPs). The reduction used is to make each DSP compute two products.

**Principle.** A DSP48E2 multiplies a 27-bit by an 18-bit signed operand. The conv2 operands are a 10-bit activation and an 8-bit weight, so most of the 27-bit port is unused. Two weights for two output channels, w0 and w1, which share the same input activation x, are placed in one 27-bit word with a gap of 18 bits, `packed = w0 × 2^18 + w1`. The single product is then

```txt
packed × x = (w0 × x) × 2^18 + (w1 × x)
```

Because |w1 × x| ≤ 128 × 512 = 2^16 < 2^17, the term w1 × x fits in the low 18 bits as a two's-complement number and never spills into the high field; the high field holds w0 × x. One subtlety makes the scheme exact rather than approximate: when w1 × x is negative, the low field borrows 1 from the high field, so the high field reads w0 × x − 1. The engine reads the low 18 bits as a signed value and adds the borrow back (Figure 7). P01 verified this on a processing element against direct products for all 2^24 combinations of two signed-8 weights and a signed-8 input, and the full design compares every pixel with the numpy reference. The packing itself is done once per frame when the weights are loaded (2,192 cycles), so no packing arithmetic runs per pixel; what remains per pixel is the borrow repair and the two adder trees, which the C13 card identifies as the layer's main fabric cost.

**Why the weights are 8-bit here and nowhere else.** Packing two 10-bit weights would need a gap of at least 20 bits and 30-bit words, more than the 27-bit port; two 8-bit weights at gap 18 is the widest pair that fits. The agent first tried to keep 10-bit precision with 8-bit packing by splitting each weight into an 8-bit low part and a residual that is corrected afterwards (P07: exact, 1 DSP, but 454 LUTs per pair instead of 132). Applied to the whole network that costs 292,000 LUTs at T = 4 (P12), 2.5× the device. The alternative is to accept 8-bit weights where the image quality allows it. The precision scan in Table 4.4 shows that uniform 8-bit weights lose about 5 dB, but 8-bit weights in conv2 alone (E062, confirmed on all 13 images in E065) cost 0.006 dB more than the 10-bit baseline. So conv2 carries 8-bit weights and a 21-bit accumulator; conv1 and conv3 keep 10-bit weights and are not packed. Packing conv1 is also ruled out by its arithmetic: the transformed weights are 14 bits and the transformed inputs 12 bits, so neither two weights nor the low-field product fit the 27 × 18 fields.

**Table 4.4** Mean PSNR change of the fixed-point network against the float golden output over 13 images, from the precision scan E010 and the mixed-precision runs E062/E065. The gate for a design to be ranked was −0.1 dB.

| Weights | Activations | ΔPSNR (dB) | Worst image (dB) | Passes −0.1 dB gate |
|---|---|---|---|---|
| 16 | 10 | −0.046 | −0.171 | yes |
| 10 | 10 | −0.070 | −0.226 | yes |
| 10 | 8 | −0.645 | −1.958 | no |
| 8 | 10 | −4.955 | −11.84 | no |
| 8 | 8 | −5.180 | −12.14 | no |
| 10, conv2 only 8 **(selected)** | 10 | −0.076 | −0.268 (foreman) | yes |

**Pipeline.** `conv2_stream` is one II = 1 loop that spends 4 cycles per pixel (Figure 1, middle). In each cycle four lanes each take one channel pair: 64 packed multiplies, 64 borrow repairs, two 64-input adder trees (6 fabric levels, one register each), bias, truncation to 21 bits, ReLU and rounding to 10 bits; the 8 channels per cycle are collected in a shift register and the 32-channel pixel is written after cycle 3. Per cycle that is 256 DSPs producing 512 products. The widths are the middle row of Figure 5: 37-bit product, 23-bit sums, 21-bit accumulator before ReLU, 10-bit output with 7 fraction bits. The 21-bit truncation relies on the sum range, which the C simulation checks with an assertion over the test set; it is the one place in the design where the width is set by observed range rather than by a worst-case bound, and Table 4.4's worst image is the evidence that it holds for the course data.

**Cost.** HLS estimate: 256 DSPs, 37,074 LUTs, 80,091 FFs. Routed (C22): 256 DSPs, 16,009 LUTs, 17,759 FFs, no BRAM. The 2.3× LUT and 4.5× FF difference between estimate and routed result is the largest of the three layers and comes from the register-heavy adder trees that Vivado retimes; Figure 6 shows the same ratio per module.

### 4.5 conv3: direct 5×5 convolution, folded over four cycles  **[new]**

**Budget.** conv3 is 10 % of the MACs: 25 taps × 32 input channels = 800 products per output pixel, 200 DSPs at T = 4. This is the layer where the question is not how to reduce multiplications but whether any reduction is worth its cost, because the frame time is set by the slowest stage and conv3 at 200 DSPs is already level with the other two (260,100 cycles against 262,144 for conv1, Figure 2). Reducing conv3 DSPs would not make the frame faster unless conv1 and conv2 shrink as well, and Table 4.2 shows that the next fold, T = 2, is out of reach by a factor of two regardless of conv3.

**Principle.** The layer is a classic streaming convolution: a line buffer plus a sliding window (Figure 8). `windows3` keeps the last four rows of the padded 259×259 feature map, 32 channels of 10 bits each, in BRAM (4 × 259 × 320 bits = 36 BRAM18K), and a 5×5×32 window in registers. Each incoming pixel shifts the window one column: the new column is the four stored rows plus the new pixel, and the line buffer shifts up one row at the same address. From the fifth row and column on, every pixel yields a complete window, so the stage emits 65,025 windows for 67,081 input pixels. The window is 8,000 bits and goes out as two 4,000-bit halves (channels 0 to 15 and 16 to 31) because of the 4,096-bit stream limit noted in 4.1.

`engine3` folds the 800 products over 4 cycles: in cycle k it multiplies input channels 8k to 8k+7 by all 25 taps (200 DSPs, 10 × 10 → 20 bits), zero-pads the 200 products to 256 and adds them in an 8-level fabric adder tree with one register per level, then adds the partial to a 23-bit running sum that starts from the bias in cycle 0. After cycle 3 the sum is rounded half to even to 10 bits with saturation and written out. There is no ReLU; the 10-bit integer is decoded to a float exactly by assembling the IEEE fields rather than by a float-conversion core. The widths are the bottom row of Figure 5. The pipeline depth of 13 cycles is mostly the adder tree; at II = 1 this depth is paid once per frame, not per pixel.

**Why direct and not scatter.** The agent compared two ways of forming the 5×5 sum. *Gather*, the structure above, stores four input rows and reads 25 taps per output. *Scatter* stores five rows of partial sums instead: each input pixel is multiplied by all 25 taps and the products are added into the 25 output positions it contributes to, so the stored rows are 32-bit sums rather than 32-channel pixels. Table 4.5 shows the controlled comparison at T = 32 (G01 to G03, same precision, same clock): scatter cuts conv3 BRAM from 36 to 5 blocks and FFs by a factor of 7, but costs 33 % to 56 % more cycles, because it must visit every padded source pixel and prime and flush partial rows at every image edge, and the edge-kernel variant also needs nine coefficient sets. In this design conv3 cycles are on the critical balance and BRAM is not (the routed design uses 38 % of the block RAM), so the cheaper memory buys nothing and the slower schedule would lengthen every frame. Gather stayed.

**Table 4.5** conv3 alternatives, synthesised at T = 32 and 10 ns on an otherwise identical network (G01 gather control, G02 scatter with explicit padding, G03 scatter with merged edge kernels). All three are bit-exact including borders.

| Variant | conv3 DSP | conv3 BRAM18K | conv3 LUT | conv3 FF | conv3 cycles per frame | Relative cycles |
|---|---|---|---|---|---|---|---|
| Gather (line buffer + window) **(selected structure)** | 25 | 36 | 10,491 | 25,184 | 2,817,921 | 1.00 |
| Scatter, explicit padding | 25 | 5 | 5,133 | 3,697 | 3,761,976 | 1.34 |
| Scatter, merged edge kernels | 25 | 5 | 3,847 | 2,254 | 4,398,556 | 1.56 |

**Why not packed or Winograd.** conv3 has 10-bit weights, so packing would need the residual scheme of P07; the attempt that combined Winograd conv1 with packed conv3 (C05, T = 4) synthesised to 260,882 LUTs and 2.38 M cycles because the adjacent-pixel pairing needs a 5×6 window, odd-column disposal and per-product residual repair, and was marked infeasible. Winograd on a 5×5 kernel would need padding to 6×6 (four 3×3 sub-kernels, 16 instead of 25 products per pixel) and would save at most 72 DSPs, 6 % of the device, for the same transform fabric that conv1 pays; it was not tried. The honest statement for this layer is that its best optimisation was to leave it alone and spend the effort on the two layers that dominate the MACs.

**Cost.** HLS estimate: 200 DSPs, 36 BRAM18K, 29,835 LUTs, 53,879 FFs. Routed: 200 DSPs, 36 BRAM18K, 13,515 LUTs, 48,418 FFs, of which the window generator is 3,248 LUTs and 17,692 FFs and the engine 10,243 LUTs and 14,705 FFs. The 36 BRAM18K line buffer is the single largest memory in the design after the two raster FIFOs of conv1.

### 4.6 Fixed-point widths along the three paths  **[keep]**

---

## Figures used by this draft

| Figure | File | Caption |
|---|---|---|
| 1 | `docs/figures/C17/fig1_fold_timing.svg` | existing |
| 2 | `docs/figures/C17/fig2_balance.svg` | existing |
| 3 | `docs/figures/C17/fig3_dataflow_backpressure.svg` | existing |
| 5 | `docs/figures/C17/fig5_bitwidth_flow.svg` | existing |
| 6 | `docs/figures/C17/fig6_hls_vs_routed.svg` | existing |
| 7 | `docs/figures/C17/fig7_conv2_packing.svg` (PNG alongside) | *conv2: one DSP48E2 multiply computes two output channels. Bit layout of the packed 27-bit weight word, the 10-bit activation and the 37-bit product; the low 18 bits hold w1·x, the rest w0·x, and a negative low field is repaired by adding 1 to the high field. Bottom: the per-cycle structure of the fold loop and the measured processing-element alternatives P01, P02 and P07.* |
| 8 | `docs/figures/C17/fig8_conv3_window_engine.svg` (PNG alongside) | *conv3: window generation and folded engine. Left: four line-buffer rows and the 5×5×32 register window; the window leaves as two 4,000-bit halves. Right: the four-cycle fold, 200 DSP products and a 256-input adder tree per cycle, accumulated into a 23-bit sum.* |

Regenerate with `python3 exp/figures/c17_report_figures.py`; PNGs with `rsvg-convert -z 2 -f png -o X.png X.svg`.

## Sources for the numbers

| Number | Source |
|---|---|
| Stage widths, depths, loop bounds | `plain/C17_srcnn_plain.cpp`; FIFO instance names in `experiments/C22_ws_impl_C17/physical_hierarchy_routed.csv` (`fifo_w1728_d32`, `fifo_w4000_d2`, …) |
| Routed per-module LUT/FF/BRAM/DSP | `experiments/C22_ws_impl_C17/physical_hierarchy_routed.csv` |
| HLS per-module estimates, pipeline depths 8/11/13 | `experiments/C17_t4_fifo/C17.md` (Module resources; Pipeline depth table) |
| DSP table rows | W18, F29, F30, W21, C10, C13, C17 metrics in `experiments/ARCH_SUMMARY.md` |
| Winograd PE | `experiments/W01_integer_f2_10bit`, `W02_direct_f2_control` |
| Packing PE | `experiments/P01_signed8_pair` (exhaustive), `P02_signed8_direct_control`, `P07_exact10_residual_pair`, `P12_exact10_packing_T4` |
| Prepacking at load | `experiments/C13_runtime_prepacked_conv2_T4/C13.md` §6 |
| Precision scan | `experiments/E010_precision_scan/data.csv`; `E065_apfixed_mixed_conv2w8`; per-image values `experiments/C17_t4_fifo/quality.csv` |
| conv3 gather vs scatter | `experiments/conv3_comparison.csv`; G01, G02, G03, E060 cards |
| conv3 packing attempt | `experiments/C05_wino_packing_T4_conv3_header_retry/C05.md` |
| 4,096-bit stream limit | `experiments/C09_wino_conv2w8_continuous_T4/C09.md` (archived error) |

## Things to check before pasting

- The P01 exhaustive check used a signed-8 input; the network's activation is 10-bit and non-negative after ReLU. The text says so; do not shorten it to "all cases verified".
- The F(4×4, 3×3) row in Table 4.3 and the Winograd-on-conv3 estimate in 4.5 are paper calculations, flagged as not synthesised. Keep the flags.
- The E062 card was not re-read for this draft; E065 is the 13-image confirmation and is the one cited in the table.
