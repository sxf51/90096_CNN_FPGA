# Report section draft: Introduction, Discussion, Conclusion, References

Draft replacement text for Sections 1, 6 and 7 of the course report (Notion page "Agent-Driven Design Space Exploration for HLS Acceleration of SRCNN on the Kria KV260"), plus a reference list the page currently lacks. Written for the report's readers (instructor and markers). Every number is taken from the existing Notion sections, `docs/0006` (milestone table), `experiments/ARCH_SUMMARY.md` or the per-experiment cards; nothing is re-derived. Section numbers assume the current page order: 1 Introduction, 2 Baseline, 3 Agent-driven DSE, 4 Final architecture, 5 Verification and deployment, 6 Discussion, 7 Conclusion, 8 References.

Markers: **[replace]** new text for an existing section, **[new]** a section that does not exist yet, **[keep]** existing text that stays, **[check]** something the authors must confirm before pasting.

Citation keys in square brackets refer to the reference list at the end. The body sections should pick up the same keys; the last part of this file lists where.

---

## 1 Introduction  **[replace the whole section]**

Single-image super-resolution (SR) reconstructs a high-resolution image from one low-resolution input [1]. SRCNN [2, 3] was the first convolutional network to do this end to end and remains the simplest learned SR method: three convolutional layers applied to a bicubically upscaled image, trained to minimise the mean squared error against the high-resolution original. Its successor FSRCNN [4] moves the upscaling into the network and is the variant most FPGA work targets; we keep the original because it is the algorithm set for the project. On the standard Set5 and Set14 benchmarks [5, 6] it improves the peak signal-to-noise ratio (PSNR) of the bicubic input by 1 to 3 dB depending on the image (Table 10).

**The algorithm.** Figure 1 shows the network. The first layer extracts features with 64 kernels of 9×9 on the single-channel input, the second maps them non-linearly with 32 kernels of 1×1, and the third reconstructs one output channel with a 5×5 kernel; the first two layers are followed by ReLU, the last is linear [7]. Conv1 and Conv3 pad by edge replication so that the output has the same size as the input [8, 9]. The model is small, 8,129 parameters in all, but a single 255×255 frame costs 522 million multiply-accumulate (MAC) operations, of which Conv1 alone is 64.5 % (Table 4). This combination, a tiny parameter set and a large, perfectly regular arithmetic load with abundant data reuse between neighbouring pixels, is what makes a convolutional network a good match for an FPGA [10]: the weights fit on chip, the computation can be unrolled across DSP slices, and the intermediate data never has to leave the device.

**Platform and tool flow.** The target is the AMD Kria KV260 Vision AI Starter Kit [11], whose Zynq UltraScale+ MPSoC (device xck26-sfvc784-2LV-c) offers 1,248 DSP48E2 slices, 117,120 LUTs, 234,240 flip-flops, 5.1 Mb of block RAM and 18 Mb of UltraRAM in the programmable logic, next to a quad-core Arm processing system with DDR4. The accelerator is written in C++ and synthesised with Vitis HLS [12], integrated with the processing system in Vivado, and driven from Python through PYNQ [13].

**Goals.** Four goals were fixed at the start of the optimisation phase and are used as the specification against which Sections 5 and 6 measure the result:

- **G1, function.** The accelerator keeps the original interface (the `srcnn` function with float arrays and parameters loaded from memory at run time), the 1-64-32-1 network and replicate padding. Its output must be bit-exact against a fixed-point reference on every one of the 13 Set14 images, and the mean PSNR of that reference on Set14 may be no more than 0.1 dB below the floating-point network.
- **G2, speed.** The primary metric is milliseconds per 255×255 frame, measured on the board. The goal is to make it as small as possible; no fixed target was set, because at the outset we had no basis for one beyond the baseline.
- **G3, fit.** The design must place, route and meet timing on the xck26 device as an integrated PS+PL system.
- **G4, evidence.** Every number reported must be traceable to an archived run, with its level of evidence stated: HLS estimate, RTL co-simulation, post-route implementation or on-board measurement.

**Approach.** The work has three stages. We first wrote a tiled, pipelined floating-point implementation of the original algorithm and verified it on the board (Section 2). It is correct and slow, and its profile shows why: the three layers run one after another, almost all DSP slices are idle, and all arithmetic is in single-precision float. Closing that gap is a search over a large space of HLS techniques, and each point in the space costs tens of minutes of synthesis and up to three hours of place-and-route to evaluate. Rather than search by hand, we handed the loop to general-purpose LLM coding agents (OpenAI Codex and Anthropic Claude Code [14]) operating under a written experimental protocol: a fixed functional contract, one primary metric, explicit acceptance gates, an experiment card committed before every run, and an archive of every result including failures. We wrote the plans and reviewed the results; the agents wrote, ran and documented the experiments (Section 3). The design that emerged, a whole-network dataflow pipeline in 10-bit fixed point with Winograd convolution [15, 16] on Conv1 and two-products-per-DSP packing [17] on Conv2, is explained decision by decision in Section 4. Finally, the IP was integrated, verified on the board and profiled, and the difference between its simulated and measured speed was traced to its causes (Section 5).

**Contributions.** The report makes three. First, a verified SRCNN accelerator whose on-board hardware time per frame falls from 2.238 s for the baseline to 2.938 ms, bit-exact against its fixed-point reference on every test image. Second, an auditable protocol for using general coding agents to search an HLS design space, with the finding that for this network the HLS logic estimates are pessimistic by about 2× and the clock estimates optimistic by about 2×, so that a search ranked on HLS estimates would have chosen the wrong design. Third, a measured account of the gap between RTL simulation and the board, attributed with hardware counters to the clock configuration and to single-beat AXI reads on the input path.

The remainder of the report is organised as follows. Section 2 analyses the algorithm and the baseline. Section 3 describes the agent-driven exploration: the protocol, what it caught, and the decisions that shaped the search. Section 4 explains the final architecture layer by layer. Section 5 covers Vivado integration, on-board verification and performance debugging. Section 6 discusses the results against the goals, the sources of the speedup, the method, and its limitations; Section 7 concludes.

---

## 6 Discussion  **[replace the section; 6.3 keeps the existing text]**

### 6.1 Results against the goals  **[new]**

Table 18 closes the loop from the goals of Section 1 to the evidence of Section 5. Every row of the specification is met except that G2 has no numeric target by construction; its row reports the achieved value and the level of evidence at which it was obtained.

**Table 18.** Goals of Section 1 traced to the specification used in the search (Section 3, Table 2) and to the evidence that closes each one.

| Goal | Specification | Evidence level | Result | Where |
|---|---|---|---|---|
| G1 interface and network | `srcnn` signature with float arrays, parameters read from DDR on every call, 1-64-32-1, replicate padding | Board | Parameter-reload test returns the analytically expected 104/256; original parameters restore the bit-exact output | Section 5.2, Table 9 |
| G1 correctness | Bit-exact against the fixed-point reference on all 13 Set14 images | Board | 13 / 13 bit-exact, plus Butterfly (Set5) | Table 10 |
| G1 quality | Mean PSNR on Set14 no worse than −0.1 dB against float | Board | 29.083 dB on the board, identical to co-simulation; −0.076 dB against the float golden; worst image −0.268 dB (foreman) | Table 6, Table 9 |
| G2 speed | ms per frame, as low as possible | RTL × routed clock | 1.365 ms (273,023 cycles at 5.0 ns) | Section 3, Section 4 |
| G2 speed | same | Board, hardware counter | 2.938 ms (489,585 cycles at 166.665 MHz), 762× faster than the 2.238 s baseline measured on the same board | Table 16, Table 17 |
| G3 fit | Post-route timing met, zero unrouted nets, resources within the device, as an integrated system | Vivado implementation of the PS+PL system | Met at 5.333 ns (WNS +0.043 ns); 1,032 DSP (82.7 %), 63,078 LUT (53.9 %), 54.5 BRAM36 (37.9 %), 97.7 % of CLBs occupied | Table 8 |
| G4 evidence | Every number traceable to an archived run with its evidence level | Repository | 231 registered experiments, 71 design directories, registry generated from reports, evolution graph | Section 3, Figure 2 |

Two things in the table deserve comment. The board figure for G2 is 2.15× the RTL figure; Section 6.3 shows that this is not a defect of the datapath but of the memory path and the clock configuration, and both are measured rather than assumed. And the G3 row shows a design that fits the device but only just: the DSP budget is 83 % used and the logic is spread over 98 % of the CLBs, which is the reason the final gate of the search had to be a routed result and not an HLS estimate.

### 6.2 Where the speedup comes from  **[new]**

The 762× between the baseline and the final design is not one idea. It is a chain of structural changes, each of which was measured against a control at the time (Section 3), and the chain can be read off the milestones of the search. Table 19 lists them with the level of evidence of each number; the HLS column and the routed column are kept apart because they differ by about two times for the same design.

**Table 19.** Milestones from the original source to the board. "HLS" is estimated cycles × target clock; "RTL × routed" is co-simulated cycles × an independently closed post-route clock; "Board" is the hardware cycle counter at the configured PL clock. Rows 1 and 3 to 9 are from the experiment registry; row 2 is the hand-written baseline of Section 2.

| # | Design | What changed relative to the previous row | Evidence | ms / frame | DSP |
|---|---|---|---|---|---|
| 1 | E000, original float source, 10 ns target | — | HLS | 19,601 | — (11,064 BRAM18K, does not fit) |
| 2 | Baseline (Section 2): 16×16 tiles, channel parallelism, pipelining, float | Tiling makes it fit; layers still sequential | Board | 2,238 | 46 (3.69 %) |
| 3 | E039: streaming dataflow, 10-bit fixed point, T = 32, 10 ns | Whole-network dataflow, no intermediate maps, one DSP per product | HLS | 29.83 | 251 |
| 4 | E043: T = 16, 3.33 ns target | Fold halved, clock target tightened | HLS | 6.94 | 505 |
| 5 | F25 / F92: continuous direct convolution, loader off the critical path, T = 16 | Window multiplexers removed; loader restructured | HLS / RTL × routed at 5.0 ns | 2.64 / 5.34 | 592 |
| 6 | W21 / W32: Winograd on Conv1, T = 8 | Conv1 products 5,184 → 2,304 per pixel, so T = 8 fits | HLS / RTL × routed at 4.5 ns | 1.75 / 2.51 | 644 |
| 7 | C16 / C21: window FIFO 16 deep, free-running pipelines, T = 8 | Stalls on the transformed-window FIFO removed | RTL × routed at 4.5 ns | 2.41 | 644 |
| 8 | C13 / C18: T = 4 with 8-bit packed weights on Conv2 | Two Conv2 products per DSP, so T = 4 fits in 1,032 DSPs | HLS / RTL × routed at 5.0 ns | 1.05 / 1.50 | 1,032 |
| 9 | **C17 / C22: window FIFO 32 deep (selected)** | One change: FIFO depth 2 → 32 | HLS / RTL × routed at 5.0 ns | 1.05 / **1.365** | 1,032 |
| 10 | C22 on the board, first bitstream | PL clock actually 125 MHz, three AXI masters on HP0 | Board | 5.05 | 1,032 |
| 11 | C22, PL0 divider 8 → 6 | 166.665 MHz | Board | 3.984 | 1,032 |
| 12 | **C22, output on its own HP port** | Write bursts no longer contend with reads | Board | **2.938** | 1,032 |

Read as three blocks, the chain is:

**From the baseline to the first routed streaming design, 419× (rows 2 to 5).** This is the largest block and it comes from changing the shape of the computation, not from tuning it. The baseline runs the three layers in sequence inside each 16×16 tile, re-fetches a 28×28 window from DDR per tile, keeps 46 DSPs busy and carries floating-point arithmetic, whose multiply-add on this device needs several DSPs and a deep pipeline per operation. The streaming design replaces all of that: the three layers run concurrently on different pixels of the same frame, the 23.81 MiB of intermediate feature maps that the direct form needs (and that E020 to E032 showed cannot be pragma'd away: 11,064 BRAM18K regardless of directives) are reduced to a few line buffers and FIFOs, and 10-bit fixed point lets one DSP48E2 compute one product per cycle so that 592 of them can work at once. The precision was chosen before the architecture and then frozen (Table 6): 10-bit weights and activations cost 0.070 dB of mean PSNR, uniform 8-bit would have cost 5.18 dB, and every later design had to match the fixed-point reference bit for bit, so that the whole chain below is attributable to structure and not to numerics. Within this block the HLS numbers show the order of the gains even though they are not board-comparable: streaming (rows 1 to 3), then halving the fold and tightening the clock (row 4, 4.3×), then the continuous engine and the loader (row 5, 2.6× at the HLS level). The loader step is worth singling out because its evidence was a resource breakdown rather than a timing number: in F25, 46 % of the LUTs sat outside the dataflow region in the multiplexers between the weight banks and the engines, and streaming the parameters instead (F27) cut those out-of-region LUTs from 32 k to 3.2 k, which is what later made the larger designs routable.

**From the first routed design to the selected one, 3.9× at the same clock (rows 5 to 9).** The routed clock is 5.0 ns in both rows 5 and 9, so this whole factor is cycles: 1,068,183 → 273,023, which is almost exactly the fold going from T = 16 to T = 4. The fold is bounded by DSPs, and Table 5 shows that direct convolution cannot go below T = 8 on this device (T = 8 direct needs 1,004 DSPs, F29 and F30; T = 4 direct needs 2,008). The two arithmetic reductions are what make T = 4 reachable, and the controls say exactly what each one does and does not do:

- *Winograd is an enabler, not a speedup by itself.* At T = 16 the Winograd network W18 uses 326 DSPs instead of 502 but takes the same number of cycles as the direct design (1,056,850 against 1,048,687), because the frame time is set by the fold, not by the multiplier count. The processing-element pair W01 and W02 measured the trade at the smallest scale: 16 DSPs instead of 36 per 2×2 tile, for roughly 1,000 extra LUTs of transform adders (1,499 against 503). Winograd pays off only where the direct design no longer fits, which is at T = 8 (644 DSPs against 1,004) and T = 4 (576 for Conv1 against 1,296). The 2.25× reduction in multiplications is the textbook figure for F(2×2, 3×3) [16]; the design keeps it exact in integers by scaling the kernel transform by two and shifting the result, which is why the bit-exact gate holds through this layer.
- *Packing is what closes the last gap.* With Winograd on Conv1 and direct Conv2, T = 4 still needs 1,288 DSPs, 40 more than the device has. Packing two Conv2 weights into one 27-bit DSP operand [17] halves that layer's DSPs to 256 and brings the total to 1,032. The exhaustive processing-element check P01 and the mixed-precision runs E062 and E065 bound its cost: it is exact for signed 8-bit weights, and 8-bit weights on Conv2 alone cost 0.006 dB more than the 10-bit baseline, against the 5 dB that uniform 8-bit would have cost. The alternative that keeps 10-bit weights everywhere (P07's residual correction) is also exact but costs 454 LUTs per product pair instead of 132, and applied to the whole network at T = 4 (P12) it needs 292 k LUTs, 2.5× the device.
- *Fold balance.* Once the three engines are at T = 4, their iteration counts are within 1 % of each other (262,144, 260,100, 260,100), and the measured frame (273,023 cycles) is within 4 % of the slowest engine's bound. The RTL design is therefore compute-bound and balanced; there is no further cycle to be had at T = 4 without changing the fold, and T = 2 is out of reach by a factor of two on DSPs with any combination of techniques (Table 5).
- *FIFO depth.* The remaining 10 % between rows 8 and 9 came from one parameter. Co-simulation of W21 (F97) had shown 45,974 stall cycles on the transformed-window FIFO; deepening it (F47 at T = 8, then C17 at T = 4) took the T = 4 design from 300,632 to 273,023 cycles. Only co-simulation sees this: HLS estimates the same cycle count for C13 and C17.

What did *not* move in this block is the clock. The routed period stayed at 5.0 ns from F92 to C22 while HLS estimated 2.4 to 2.9 ns for the same designs, and the three attempts to close 4.5 ns on the T = 4 RTL (W36, C36, C40) all failed timing with their worst paths in the Winograd arithmetic. The calibration data behind the gate change of Section 3 (routed LUTs 0.46 to 0.66 of the HLS estimate, routed clock 1.7 to 2× the estimate across 18 implemented designs) is the quantitative form of that observation.

**From the RTL to the board, ÷2.15 (rows 9 to 12).** The last block is a loss, and Section 6.3 decomposes it: 0.27 ms is the PL clock at 166.665 MHz instead of 200 MHz, and 1.30 ms is single-beat AXI reads on the input and parameter paths. Of the 5.05 ms of the first bitstream, 1.07 ms was recovered by reading the actual IOPLL configuration and changing one divider, and 1.05 ms by giving the output master its own HP port so that its writes no longer contend with the two read masters [19, 20]. Multiplying the three blocks together, 419 × 3.9 ÷ 2.15, gives the 762× of Table 16.

**What the final number means.** On the board the accelerator performs the 522 million MACs of the original network in 2.938 ms, an effective 178 GMAC/s, against a raw capacity of 1,032 DSPs × 166.665 MHz = 172 G multiplications per second; the effective rate exceeds the raw one because Winograd and packing remove multiplications rather than perform them. The ratio of RTL to on-board cycles, 273,023 / 489,585 = 56 %, is the fraction of board cycles in which the datapath does the work it was built for. At the RTL level the same datapath is at 96 % of its structural bound. The design is therefore finished as a datapath and unfinished as a system, and that is the order in which the next iteration should spend its effort.

### 6.3 Where the time goes between the RTL and the board  **[keep the existing text of the current 6.1 unchanged, including the burst-trial paragraph]**

Lead-in sentence to add before the existing first paragraph: *The last block of Table 19 is the only one in which the design got slower, and because it was invisible at every evidence level available during the search, it is worth decomposing in full.*

### 6.4 On the method  **[new]**

Section 3 described the protocol and what it caught. This section asks whether it was worth it, what it did not do, and how far the findings generalise.

**What the protocol bought.** Three things that a hand search of the same length would probably not have produced. The first is the calibration of HLS estimates against routed results. It exists only because every run was archived with its evidence level and because the rule "a lower level may not be reported as a higher one" forced the HLS and routed numbers for the same design to sit side by side; the moment five such pairs existed the 2× pattern was obvious, and acting on it (the gate change of 2026-10-12) is what admitted the T = 4 designs that an HLS-ranked search would have discarded on LUT count (C13: 127,966 LUTs estimated, 58,529 routed). The second is the negative results. Of 231 registered experiments, 100 ended in failure, infeasibility, invalid configuration or timeout, and several of those closed a direction for good: output-tile fusion (S03 to S06, 130 to 228 ms), DDR scratch buffers (S01, whose ports were never exported and silently became 11,286 BRAM18K), scatter-based Conv3 (G03, 1.56× the cycles of the gather control), and the naive combination of Winograd with packing (C11, 249 k LUTs). Each is recorded with its card, its prediction and its measurement, so the report can say why the final design has the shape it has and not only that it works. The third is attribution: because every card changes one thing against a named control, Table 19 and the bullets of Section 6.2 can be written at all.

**What it cost.** The search ran for about four days of wall-clock time on a 12-core, 15 GiB host that was busy essentially continuously, with timeouts of 60 minutes for synthesis, 6 hours for co-simulation and 3 hours for implementation; the archive is several gigabytes; and the humans spent roughly one review per 10 to 20 experiments reading interpretations and rewriting plans. Against that, the hand-written baseline took the same two people from 2026-09-29 to the start of the search to reach 2.238 s, a 30× cycle reduction over the original source at the HLS level. The agent-driven phase delivered the remaining three orders of magnitude in less time. We do not claim this ratio generalises: the baseline phase included learning the tools, and the search phase benefited from the baseline's analysis of where the time went.

**What the agents did not do.** The rules stopped the agents from changing several things at once and from inflating evidence; they did not stop them from spending experiments on a direction that had stopped making sense, and the plan reviews are where that was corrected. All goal-level decisions were human: the choice of directions (Winograd and packing were explored because the course covered them), the precision freeze, the gate change, the scope decisions that closed open-ended workstreams (13 images are the test set; ROM parameter storage stays exploratory), and the choice of C22 over a rescue re-route of C36. The log also records clerical slips that the protocol caught after the fact rather than preventing: an experiment launched before its design existed (W26), a plan that specified three co-simulation calls where four were needed, and conditional implementation jobs that were never started. One of the costliest failures was a human instruction (running two implementations at once caused the W23 out-of-memory kill); the rule that replaced it came from the agent's own measurement of memory peaks.

**Threats to validity.** The quantitative findings are specific in three ways. The 2× HLS calibration is for one network, one device family and one tool version (Vitis HLS and Vivado 2026.1 [check]); it should be re-measured rather than assumed for a different design, although the direction of the error (pessimistic logic, optimistic clock, exact DSP count) is consistent with the design being dominated by wide adder trees that Vivado retimes. The bit-exact gate was checked on the 13 supplied images plus one Set5 image, and the 21-bit Conv2 accumulator relies on an observed range rather than a worst-case bound; a wider test set could in principle find an overflow that these images do not. And the experiment counts depend on the counting rule: 231 registered runs include retries, controls and verification runs of the same design at another evidence level; about 50 of the 71 design directories are distinct architectural points.

**Relation to other work.** Using LLMs to tune HLS designs is an active topic: reasoning-model agents that insert pragmas and restructure code with tool feedback [21], and, most directly comparable, an IBM study that drives Claude Code with Vitis HLS over benchmark kernels and reports mean speedups of about 7× [22]. Those works optimise single kernels at the HLS-estimate level. This project differs in three ways: the object is a whole network carried through co-simulation, place-and-route and the board; the ranking deliberately refuses HLS estimates; and the contribution is not a search algorithm but a protocol that makes a general coding agent's search auditable by a reader who was not present. On the hardware side, Winograd on FPGAs [18] and two-products-per-DSP packing [17] are established techniques; what this report adds is the measured interaction between them on a small network, in particular that Winograd buys nothing until the fold is DSP-bound (Table 19, row 6 and W18) and that packing is only affordable where 8-bit weights are affordable (Table 6). We found the LLM-for-HLS literature after designing the method, and the comparison in this paragraph was not used to shape it.

### 6.5 Limitations and future work  **[replace; same five items as the current 6.2, tightened, plus power and system throughput]**

Each limitation below has a concrete next step that is resource-neutral or nearly so, which matters because the device is 83 % full on DSPs and 98 % on CLBs.

**Memory access pattern.** The on-board cycle count is 1.8× the RTL count, and the AXI statistics attribute this to single-beat reads on the input and parameter paths, with the image channel waiting for data during 77.7 % of the frame. The cause is in the HLS source: the loader reads, converts and writes to a stream in one pipelined loop with a division and a modulo in the address, so Vitis HLS cannot prove the accesses consecutive and generates one transaction per word [12]. Section 6.3 shows the fix at the HLS level: splitting the loader into a load-only row loop and a separate encode loop makes HLS infer a burst of length 65,025 on the image port with no change to the interface, the cycle estimate or the DSP count, at the cost of one BRAM18K. The remaining steps are to co-simulate that variant, package it, rebuild the system with the same HP0/HP1 topology and monitors, and compare 20 hardware-counted runs against the 489,584.5-cycle baseline, accepting it only if the output stays bit-exact and the measured average burst length exceeds 1. The parameter loaders need the same treatment, or, since the parameters are constant across frames, could stay on chip behind a `load_params` switch as explored in Section 3. If the 216 k stall cycles were removed the board would approach the 1.638 ms the RTL predicts at the present clock. A more radical option is an AXI-Stream input fed by a DMA engine, which takes burst generation out of the accelerator entirely.

**Clock.** The IP was routed at 5 ns out of context, but the integrated system is implemented at the 5.333 ns Vivado derives from the PS preset, and on the board it runs at 166.665 MHz because the clock debugging stopped at a divider of 6 once the dependence of time on frequency had been established. The next divider, 5, gives 200 MHz, above the 187.5 MHz the system was implemented for; with 43 ps of setup slack at 5.333 ns it cannot be assumed to work. Reaching 200 MHz means re-implementing the full system at a 5 ns constraint, with the monitoring modules removed, and verifying timing and correctness again; the out-of-context result (+13 ps at 5 ns) suggests it is attainable but does not prove it. If it closes, the hardware time falls by a further 17 % to about 2.45 ms with the present loader, or to the RTL's 1.365 ms once the memory path is fixed. Going below 5 ns is a different project: W36, C36 and C40 place the critical path inside the Winograd arithmetic with 8 to 11 logic levels, so a faster clock would need that engine re-pipelined.

**Resources.** With 82.7 % of the DSPs and 97.7 % of the CLBs in use there is no room for more buffers or parallel units; any architectural change beyond the two above would have to trade DSPs for LUTs or accept a different fold. The one place where a trade exists on paper is Conv1: F(4×4, 3×3) Winograd would need 324 DSPs instead of 576, but its transform constants are not powers of two, so the bit-exact-with-shifts property would be lost, and its window stream would exceed the 4,096-bit limit (Table 4.3 [check: Notion table number]). It was not pursued and is listed here as a known, unmeasured option.

**Software path and system throughput.** A full PYNQ invocation takes about 6 ms against 2.94 ms of hardware time (Table 17), so the system as delivered sustains about 167 frames per second while the accelerator alone would sustain 340. The difference is cache maintenance on four buffers, the NaN pre-fill, the output copy and the NaN/Inf check, all of which exist for verification. A production driver would keep the parameters resident and flush them once, drop the pre-fill and the check, and double-buffer input and output so that transfers overlap execution; the hardware time would then be the frame time. The 255×255 frame size is fixed by the contract; a general accelerator would need variable sizes and a wider test set than the 14 images used here.

**Power.** Power was not measured. The only figure is Vivado's 5.8 W estimate at medium confidence (Section 5.1). The KV260 exposes its rails through PMBus [11], so a measurement under load, and the energy per frame that follows from it, would be a short addition and would allow a comparison with GPU and CPU implementations of the same network, which this report does not attempt.

**Verification scope of the method.** The search ranked designs on co-simulated cycles and routed clocks and never on the board, so the 2.15× gap of Section 6.3 was invisible at every level the agents could reach. The most valuable methodological change is to add automated on-board measurement as the top evidence level of the protocol, so that memory-path effects feed back into the search instead of being discovered after it. The hardware for it already exists: the cycle monitor and the AXI statistics module of Section 5 are exactly the instruments such a gate would read.

---

## 7 Conclusion  **[replace]**

This project set out to accelerate SRCNN inference on the Kria KV260 and to find the design by a search that two students could not have carried out by hand in the time available. The accelerator delivered runs one 255×255 frame in 2.938 ms of hardware time on the board, bit-exact against its fixed-point reference on all 13 Set14 images at a mean PSNR within 0.08 dB of the floating-point network, 762× faster than the floating-point baseline measured on the same board. The speedup decomposes into three measured blocks: 419× from replacing a sequential, tiled, floating-point computation with a whole-network fixed-point dataflow pipeline; 3.9× from reaching a fold of four cycles per pixel, which Winograd on Conv1 and packed multiplications on Conv2 make fit in 1,032 of the device's 1,248 DSP slices; and a loss of 2.15× between the RTL and the board, attributed with hardware counters to the clock configuration and to single-beat AXI reads. The search that found the design registered 231 experiments in four days under a protocol that commits each experiment's prediction before it runs and records its evidence level with its result; its most consequential finding was that HLS estimates for this network are wrong by about 2× in both directions, so the final gate had to be a routed result. The next steps are local and already prototyped: make the loaders burst, then raise the system clock to 200 MHz, and the on-board time should approach the 1.365 ms the RTL already achieves.

---

## 8 References  **[new]**

Numbered in order of first citation. IEEE style. Entries 1, 3, 4, 7, 8 and 9 were supplied by the authors from the course reading list and are reproduced as given; every other entry contains only details confirmed against a publisher, arXiv or vendor page on 2026-10-26, with author lists omitted where they could not be confirmed.

1. Z. Wang, J. Chen and S. C. H. Hoi, "Deep Learning for Image Super-Resolution: A Survey," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 43, no. 10, pp. 3365–3387, Oct. 2021, doi 10.1109/TPAMI.2020.2982166.
2. C. Dong, C. C. Loy, K. He and X. Tang, "Image Super-Resolution Using Deep Convolutional Networks," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 38, no. 2, pp. 295–307, Feb. 2016.
3. C. Dong, C. C. Loy, K. He and X. Tang, "Learning a Deep Convolutional Network for Image Super-Resolution," in *Computer Vision – ECCV 2014*, Part IV, Springer, 2014.
4. C. Dong, C. C. Loy and X. Tang, "Accelerating the Super-Resolution Convolutional Neural Network," in *Computer Vision – ECCV 2016*, Part II, Springer, 2016.
5. R. Zeyde, M. Elad and M. Protter, "On Single Image Scale-Up Using Sparse-Representations," in *Curves and Surfaces 2010*, LNCS 6920, Springer, 2012, pp. 711–730. (Source of Set14.)
6. M. Bevilacqua, A. Roumy, C. Guillemot and M.-L. Alberi Morel, "Low-Complexity Single-Image Super-Resolution Based on Nonnegative Neighbor Embedding," in *Proc. British Machine Vision Conference (BMVC)*, 2012, pp. 135.1–135.10, doi 10.5244/C.26.135. (Source of Set5.)
7. I. Goodfellow, Y. Bengio and A. Courville, *Deep Learning*, MIT Press, 2016, http://www.deeplearningbook.org (accessed 12 Sep. 2023).
8. V. Dumoulin and F. Visin, "A Guide to Convolution Arithmetic for Deep Learning," arXiv:1603.07285 (accessed 12 Sep. 2023).
9. A. Amidi and S. Amidi, "Convolutional Neural Networks Cheatsheet," Stanford CS 230, https://stanford.edu/~shervine/teaching/cs-230/cheatsheet-convolutional-neural-networks (accessed 12 Sep. 2023).
10. C. Zhang, P. Li, G. Sun, Y. Guan, B. Xiao and J. Cong, "Optimizing FPGA-based Accelerator Design for Deep Convolutional Neural Networks," in *Proc. ACM/SIGDA Int. Symp. on Field-Programmable Gate Arrays (FPGA)*, 2015, pp. 161–170, doi 10.1145/2684746.2689060.
11. AMD, *Kria KV260 Vision AI Starter Kit*, product documentation, AMD/Xilinx.
12. AMD, *Vitis High-Level Synthesis User Guide* (UG1399), v2026.1, sections "AXI Burst Transfers" and "Options for Controlling AXI4 Burst Behavior".
13. PYNQ: Python productivity for Zynq, v3.0.1, http://www.pynq.io (accessed Oct. 2026).
14. Anthropic, *Claude Code*; OpenAI, *Codex*. Software, versions as used in October 2026.
15. S. Winograd, *Arithmetic Complexity of Computations*, SIAM, 1980.
16. A. Lavin and S. Gray, "Fast Algorithms for Convolutional Neural Networks," in *Proc. IEEE Conf. on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 4013–4021, doi 10.1109/CVPR.2016.435.
17. Xilinx, "Deep Learning with INT8 Optimization on Xilinx Devices," white paper, 2016.
18. Y. Liang, L. Lu, Q. Xiao and S. Yan, "Evaluating Fast Algorithms for Convolutional Neural Networks on FPGAs," *IEEE Trans. on Computer-Aided Design of Integrated Circuits and Systems*, vol. 39, no. 4, pp. 857–870, 2020, doi 10.1109/TCAD.2019.2897701. (First presented at FCCM 2017.)
19. AMD, *Zynq UltraScale+ Device Technical Reference Manual*, chapter on the PS–PL AXI interfaces and interconnect.
20. AMD, "Traffic Shaping of HP Ports on Zynq UltraScale+," Xilinx Wiki, https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/688128001 (accessed Oct. 2026).
21. L. Collini, A. Hennessee, R. Karri and S. Garg, "Can Reasoning Models Reason about Hardware? An Agentic HLS Perspective," arXiv:2503.12721, 2025.
22. A. Bhandwaldar, M. Choudhury, R. Puri and A. Srivastava, "Agent Factories for High Level Synthesis: How Far Can General-Purpose Coding Agents Go in Hardware Optimization?," arXiv:2603.25719, 2026.

### Where the body should cite them

| Place | Keys |
|---|---|
| Section 1 and Section 2, SR background, SRCNN, FSRCNN, test sets | [1], [2], [3], [4], [5], [6] |
| Section 2, convolution, ReLU, padding, MAC counting | [7], [8], [9] |
| Section 2, feasibility of FPGA acceleration (parallelism, reuse, roofline argument) | [10] |
| Section 3, "Why an agent" and the closing sentence on related work | [14], [21], [22] |
| Section 4.3, Winograd principle and tile-size discussion | [15], [16], [18] |
| Section 4.4, packing principle | [17] |
| Section 4.1, 4,096-bit stream limit; Section 6.3, burst inference | [12] |
| Section 5, HP port arbitration (replace the bare bookmark with a citation) | [19], [20] |
| Section 5, platform and PYNQ | [11], [13] |
| Section 6.4, relation to other work | [4], [17], [18], [21], [22] |

---
|---|
| Section 2, algorithm description and test sets | [2], [5], [6] |
| Section 2, feasibility of FPGA acceleration (parallelism, reuse, roofline argument) | [10] |
| Section 3, "Why an agent" and the closing sentence on related work | [14], [21], [22] |
| Section 4.3, Winograd principle and tile-size discussion | [15], [16], [18] |
| Section 4.4, packing principle | [17] |
| Section 4.1, 4,096-bit stream limit; Section 6.3, burst inference | [12] |
| Section 5, HP port arbitration (replace the bare bookmark with a citation) | [19], [20] |
| Section 5, platform and PYNQ | [11], [13] |
| Section 6.4, relation to other work | [18], [17], [21], [22] |

---

## Notes for pasting

- **New Figure 1 (network diagram).** The Introduction refers to a figure of the three-layer network with kernel sizes, channel counts, padding and activations; the authors will draw it. The current Figure 1 (AGENTS.md excerpt) and all later figures then shift by one.
- **Section 2 overlap.** The new Introduction states the network, the MAC count and the parameter count once. The per-layer bullet list at the top of Section 2 can stay (it is the detailed version) but its first sentence should no longer re-introduce SRCNN.
- **Duplicate "Limitations".** Section 3 ends with "Limitations and lessons". With the new 6.4 and 6.5, trim that subsection to the method-execution items (expensive; counts depend on counting rule; clerical slips) and move "HLS estimates cannot be used for ranking" and "no on-board feedback" to Section 6, where they now live.
- **Table and figure numbers.** The draft uses Table 18 and Table 19 (the page currently ends at Table 17) and refers to Table 4, Table 5, Table 6 and "Table 4.3" from the Section 4 draft; check the final numbers on the page. The row for G3 cites Table 8.
- **The baseline row of Table 19.** 2.238 s is a board measurement of the hand-tiled design of Section 2 and is not in the experiment registry (docs/0006 notes this). The HLS-level figure in the same row is deliberately left blank; if the baseline's HLS cycle count and clock are available from the September workspace, add them.
- **Tool version.** Section 6.4 says Vitis 2026.1; confirm against the host installation.
