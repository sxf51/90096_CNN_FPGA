# C17: T4 Winograd SRCNN (final deliverable)

[中文](README.md)

This is the fastest design from the architecture exploration that has complete IP-level verification:
- bit-exact on all 13 images;
- two-frame RTL co-simulation passes;
- Vivado routing closes at 5 ns (200 MHz);
- **1.365 ms** per frame at IP level (about 732 frames/s).

System integration and on-board measurement have not been done yet; see "Known limitations".

| Item | Result | Evidence |
| --- | --- | --- |
| Quality | Mean PSNR 29.083 dB over 13 images versus 29.158 dB for the float golden model, **ΔPSNR −0.0759 dB**; per image from −0.011 (monarch) to −0.268 dB (foreman) | C17, `reports/hls/quality.csv` |
| Bit exactness | The butterfly output is bit-identical to the independently verified fixed-point reference (E065); MSE against the float golden output is 1.77065e-05 | C17; re-run with the course testbench when packaging |
| RTL cycles | Both transactions PASS, latency **273,023** and interval 273,052 cycles; the second transaction changes the input, weights and biases | C20, `reports/cosim/` |
| Routed timing | 5.0 ns target: WNS +0.013 ns, WHS +0.032 ns, TNS 0, no unrouted nets | C22, `reports/impl/srcnn_timing_routed.rpt` |
| Routed resources | DSP 1,032 (82.7%), LUT 59,552 (50.8%), FF 100,499 (42.9%), BRAM18K 109 (37.8%), URAM 0 | C22, `reports/impl/srcnn_utilization_routed.rpt` |
| IP frame time | 273,023 × 5 ns = **1.365 ms** | C20 × C22 |

PSNR is the normalized floating-point MSE PSNR against the high-resolution ground truth, without clipping or cropping. "Set14" means the 13 images supplied by the course (comic is not included).

## Contents

| Path | Contents |
| --- | --- |
| `src/` | HLS sources, identical to `designs/winograd_t4_windows32_v1/` and to the archived C17 sources |
| `ip/srcnn.zip` | Packaged IP used by the C22 implementation (Vivado IP catalog format, with HDL, drivers and OOC constraints) |
| `driver/` | HLS-generated driver files (`xsrcnn*.c/h`) extracted from the IP for easy reading |
| `reports/hls/` | C17 HLS synthesis report and the 13-image quality table |
| `reports/cosim/` | C20 RTL co-simulation reports |
| `reports/impl/` | C22 routed timing, utilization and status reports and the worst paths |
| `scripts/run_csim.sh` | C simulation with the original course testbench |
| `provenance/` | Original C17 HLS configuration (absolute remote paths, kept for provenance) and the Vitis version |
| `SHA256SUMS` | Checksums of the sources and the IP package |

## Design summary

- **Whole-network streaming DATAFLOW**: 4 cycles per pixel (T4). DSPs are split 576 / 256 / 200 across the three layers, and no intermediate feature map is ever stored in full.
- **Conv1**: integer Winograd F(2×2,3×3). The 9×9 kernel is split into nine 3×3 sub-kernels, cutting multiplications from 5,184 to 2,304 per pixel.
- **Conv2**: 8-bit weights. Two output channels' weights are packed into one 27-bit operand, so one DSP computes two products.
- **Conv3**: direct convolution, 8 channels × 25 taps per cycle.
- **Precision**: 10-bit weights and activations (8-bit Conv2 weights) with 23-bit accumulators; rounding and saturation match the reference model.
- **Scheduling**: continuous folds in all three layers (II=1, no drain inside a frame) and online padding. The Winograd transformed-window FIFO is 32 deep, which saves 9.2% of cycles relative to C18.
- **Weights**: every call reloads all 8,129 parameters from DDR and performs the Winograd weight transform on chip.

## Interface

The top-level signature is identical to the course original:

```cpp
void srcnn(float in[1][255][255],
           float weights1[64][1][9][9], float biases1[64],
           float weights2[32][64][1][1], float biases2[32],
           float weights3[1][32][5][5], float biases3[1],
           float out[1][255][255]);
```

- **Data**: all float32, in the same layout as the course `.bin` files.
- **AXI master ports (m_axi)**: three of them, `image_in` (in), `image_out` (out) and `parameters` (the six parameter arrays), with a burst length of 256.
- **Control port (s_axilite `control`)**:

| Offset | Register |
| --- | --- |
| 0x00 | AP_CTRL (bit0 ap_start, bit1 ap_done, bit2 ap_idle) |
| 0x04 / 0x08 / 0x0c | GIE / IER / ISR (interrupts) |
| 0x10 | `in` address (64-bit: low word at 0x10, high word at 0x14) |
| 0x1c / 0x28 | `weights1` / `biases1` addresses |
| 0x34 / 0x40 | `weights2` / `biases2` addresses |
| 0x4c / 0x58 | `weights3` / `biases3` addresses |
| 0x64 | `out` address |

To run it: write the physical addresses of the eight buffers, set `ap_start`, then poll `ap_done` or wait for the interrupt. Buffers must be physically contiguous DDR memory (use `pynq.allocate` on PYNQ). Flush the CPU cache to memory before starting, and invalidate it before reading the results.

## Usage

### C simulation (verified)

```sh
source <Vitis 2026.1>/settings64.sh
bash final/C17/scripts/run_csim.sh            # writes to final/C17/build/csim by default
```

This uses the repository's `test/csim.cpp`, `test/tb_conv1.cpp`, `test/tb_srcnn.cpp`, `test/util.cpp`, `test/set5/` and `src/weights/`. It was actually run with remote Vitis 2026.1 while packaging on 2026-10-13, finished in 34 s, and printed:

```
***** CONV1 Golden Reference *****
  - Butterfly MSE: 5.15431e-06
***** SRCNN Golden Reference *****
  - Butterfly MSE: 1.77065e-05
```

The course testbench only prints the MSE and always returns 0, so check the printed values. Bit-exactness and the 13-image acceptance used the testbench of the experiment framework (see "Full reproduction" below).

### Re-synthesis and packaging (not re-run when packaging)

First run `run_csim.sh` once to generate `build/csim/hls_config.cfg` (`clock=4ns`, `syn.top=srcnn`, same macros). Then, from the `final/C17/` directory, run:

```sh
v++ -c --mode hls --config build/csim/hls_config.cfg --work_dir build/syn
vitis-run --mode hls --package --config build/csim/hls_config.cfg --work_dir build/syn
```

In the original experiment, T4 HLS synthesis took about 26 minutes and 3.3 GB of memory. `ip/srcnn.zip` comes from the original experiment flow. Its HDL is file-for-file identical to the HDL packaged by C17; only the revision and creation time in `component.xml` differ.

### Full reproduction (experiment framework)

From the repository root, run `python3 exp/reproduce_exp.py C17 --run`. This replays the C17 C simulation and synthesis under a new ID; see [experiments/REPRODUCE.md](../../experiments/REPRODUCE.md).

### Board integration (not yet executed; steps only)

1. Unzip `ip/srcnn.zip` and add it to Vivado as an IP repository.
2. Build the block design:
   - Zynq UltraScale+ MPSoC (KV260);
   - connect `s_axi_control` to `M_AXI_HPM0_FPD` through an interconnect;
   - connect the three m_axi ports to `S_AXI_HP*_FPD`.
3. Set the PL clock to 200 MHz (1000 MHz ÷ 5). The OOC routing slack is only 13 ps, so **full-system timing must be re-checked**. If it fails, use 166.67 MHz (1000 MHz ÷ 6), about 1.64 ms per frame.
4. On the board, read the actual PL clock back with `pynq.Clocks`. The earlier board baseline requested 100 MHz but read back 66.666 MHz.

## Known limitations

- All numbers are IP-level results: ideal AXI, excluding DDR, drivers, interconnect and the board clock. Full-system implementation and on-board measurement have not been done.
- The setup slack at 5 ns is only 13 ps.
- Weights are reloaded every frame, which costs about 4.5k–6k cycles per frame on T4 (about 2%, measured). C32, the version with a weight-reload switch, passed RTL verification but missed 5 ns by 0.102 ns, so it is not part of this deliverable.
- The mean ΔPSNR is −0.0759 dB (gate −0.1 dB), but foreman alone is −0.268 dB. The all-10-bit version also gives −0.226 dB on foreman.
- Attempts to reach 4.5 ns (W34, W36) did not close timing.

## Provenance

- Sources: `designs/winograd_t4_windows32_v1` (first committed in 013a306).
- Experiments:
  - C17: C simulation, HLS synthesis, 13 images, [record](../../experiments/C17_t4_fifo/C17.md);
  - C20: two-frame RTL simulation, [record](../../experiments/C20_ws_cosim_C17/C20.md);
  - C22: staged Vivado implementation at 5 ns, [record](../../experiments/C22_ws_impl_C17/C22.md).
- Design plan: [docs/0005](../../docs/0005-rom-clock-t4-plan.md).
- Tools: Vitis/Vivado 2026.1 (SW Build 6497934), part `xck26-sfvc784-2LV-c`.
