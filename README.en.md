# SRCNN Super-Resolution Inference (Vitis HLS)

This project implements a three-layer SRCNN in C++, with `srcnn` as the Vitis HLS synthesis top function. It loads pretrained weights and reconstructs a single-channel 255 × 255 image at the same dimensions. `UP=3` identifies the 3× super-resolution test data; the input has already been scaled to 255 × 255, so this network does not resize it.

## Network

| Layer | Input channels | Output channels | Kernel | Activation |
| --- | ---: | ---: | ---: | --- |
| Conv1 | 1 | 64 | 9 × 9 | ReLU |
| Conv2 | 64 | 32 | 1 × 1 | ReLU |
| Conv3 | 32 | 1 | 5 × 5 | None |

All convolutions have stride 1. Conv1 and Conv3 replicate the nearest edge pixel outside the image, preserving 255 × 255 feature maps. Weights, biases, and feature maps currently use single-precision floating point. The project implements inference, not training or image interpolation.

## Files

| Path | Purpose |
| --- | --- |
| `src/srcnn.h` | Image dimensions, network constants, types, and declarations |
| `src/conv1.cpp` | First convolution and ReLU |
| `src/srcnn.cpp` | Top function and all three layers |
| `src/weights/` | Pretrained weights and biases |
| `test/tb_conv1.cpp` | Conv1 output comparison against golden data |
| `test/tb_srcnn.cpp` | Full-network output comparison against golden data |
| `test/tb_set14.cpp` | Set14 MSE and PSNR evaluation; disabled by default |
| `test/set5/`, `test/set14/` | Input images, ground truth, and reference data |
| `script.py` | Creates and configures the Vitis HLS component |
| `workspace/` | Generated Vitis workspace, excluded by `.gitignore` |

## Run C simulation in Vitis

1. Install Vitis 2026.1 and locate its installation directory.
2. Open Windows **Command Prompt (CMD)** in the project root and run:

   ```bat
   chcp 65001
   call "<Vitis installation prefix>\AMDDesignTools\2026.1\Vitis\settings64.bat"
   vitis -s script.py
   ```

   Replace `<Vitis installation prefix>` with the actual location. `chcp 65001` selects UTF-8; `call` loads the Vitis environment and returns to the same CMD session. **The script deletes and recreates the root `workspace/` directory on every run.** Move any files you need to retain out of it first.

3. After the script finishes, open Vitis GUI with the root `workspace/` as its workspace, select the `baseline` component, and run **C Simulation**.

The generated configuration is `workspace/baseline/hls_config.cfg`. The target part is `xck26-sfvc784-2LV-c` and the target clock is 10 ns. Passing C simulation verifies functional output; run HLS synthesis separately to assess area, timing, and estimated hardware latency.

The default `test/csim.cpp` entry runs Conv1 and full-network tests. Enable `tb_set14()` there to run the Set14 evaluation. The testbench reads `./weights/` and `./set5/` by relative path; the Vitis component includes those directories as test files.

## Current validation

Local C simulation with the supplied butterfly input, weights, and golden outputs produced:

| Output | MSE against golden data |
| --- | ---: |
| Conv1 | About 3.46 × 10⁻¹⁵ |
| Full SRCNN | About 3.17 × 10⁻¹⁴ |

These values indicate close agreement with the floating-point reference; they are not image-quality scores against high-resolution ground truth. Use the Set14 MSE and PSNR test for image-quality evaluation.

## FPGA optimization plan

The following is a **plan, not an implemented feature list**. It follows the lecture material on tiled convolution, model quantization, dataflow, and overlapping load/compute/store, while using the actual 255 × 255 dimensions in this code. Each change must preserve the current edge-replication behavior and be checked against the golden reference before performance is compared.

### Quantitative baseline

Direct convolution requires `H × W × Cin × Cout × K²` multiply-accumulate operations (MACs), excluding bias, activation, and transfer overhead. Here, `H × W = 255² = 65,025`.

| Layer | MACs | Share of total MACs | Full output map (float32) | Weights (float32) |
| --- | ---: | ---: | ---: | ---: |
| Conv1: 1→64, 9×9 | 337,089,600 | 64.54% | 16,646,400 B | 20,736 B |
| Conv2: 64→32, 1×1 | 133,171,200 | 25.50% | 8,323,200 B | 8,192 B |
| Conv3: 32→1, 5×5 | 52,020,000 | 9.96% | 260,100 B | 3,200 B |
| Total | 522,280,800 | 100% | — | 32,128 B |

The current top function holds complete Conv1 and Conv2 intermediate maps, together `24,969,600 B ≈ 23.81 MiB`. Writing each map to external memory and reading it back once would transfer at least `2 × 24,969,600 = 49,939,200 B`; this is a data-movement lower bound, **not measured DRAM traffic** for the current code. All weights total only about 31.38 KiB, excluding biases, so feature-map reuse deserves priority. The XCK26 on-chip BRAM and URAM capacities shown in the lecture are insufficient for both complete float32 intermediate maps.

### Phase 0: Measure the baseline

Run C simulation and HLS synthesis. Record loop latency and initiation interval (II), achieved clock, DSP/LUT/BRAM/URAM use, and interface traffic. The configured 10 ns is a **target**, not an achieved board frequency. At an ideal 100 MHz and one MAC per cycle, the arithmetic alone would take `522,280,800 / 10⁸ ≈ 5.223 s`. This is only a reference for comparing parallel designs; floating-point latency, memory ports, and transfers also matter.

### Phase 1: Tiling and local reuse

Tile output channels (`Tn`), height (`Th`), width (`Tw`), and input channels (`Tc`). Start a design-space sweep at `Th=Tw=32, Tn=8, Tc=8`; these are candidates, not proven optima. Use an **output-stationary** schedule: accumulate an output tile locally over all input-channel tiles and write it once, avoiding external read/write of partial sums for each `Tc`. Buffer input and weight tiles locally and partition arrays according to the required parallel read ports.

For a 32×32 Conv1 output tile, the 9×9 kernel needs a four-pixel halo, so the input region is 40×40: `1,600×4=6,400 B`. An eight-channel float32 output accumulator tile occupies `8×32×32×4=32,768 B`; its weight tile is `8×1×9×9×4=2,592 B`. Conv3 needs a two-pixel halo, giving a 36×36 input region per input channel for a 32×32 output tile. Smaller spatial tiles increase repeated halo loading: `40²/32²=1.5625` for Conv1 at 32×32, versus `72²/64²≈1.266` at 64×64. Larger tiles also need more on-chip memory; synthesis will determine the useful balance.

Add line buffers and sliding windows within Conv1 and Conv3 tiles to reuse neighboring pixels. Partially unroll and pipeline `Tn`, `Tc`, and kernel computation, with matching partitions for weights and accumulators. Implement Conv2 separately as a per-pixel 64→32 matrix-vector operation; its 1×1 kernel needs neither spatial kernel loops nor boundary checks. Sweep parameters and select a configuration from the measured II, latency, and resource use.

### Phase 2: Streaming and dataflow

First split each tile into `load → compute → store` tasks. Use double buffers and FIFO/PIPO channels with HLS `DATAFLOW` to overlap stages. If their standalone times are `L`, `C`, and `S` cycles, the steady-state goal is closer to `max(L,C,S)` cycles per tile than sequential `L+C+S`; startup, drain, and bus contention still require measurement. Use a burst-friendly AXI memory-mapped interface for external DRAM. An internal `hls::stream` does not itself make DRAM accesses burst.

Then progressively stream Conv1→Conv2→Conv3 through on-chip buffers to reduce full intermediate-map transfers. Conv2 needs all 64 Conv1 channels for each pixel. Conv3 needs all 32 Conv2 channels across a 5×5 neighborhood, so channel order, line buffers, and FIFO depth must be designed together. A fused 32×32 final-output tile has a combined input receptive-field radius of `4+2=6`: it needs at least a 44×44 source region, with the current edge-replication rule at image boundaries. If fusion eliminates one external write and read of both full intermediate maps, it could remove about **49.94 MB/image** of that traffic. Confirm the actual gain with interface counters and board timing.

### Phase 3: Quantization and board validation

Once the float32 design is stable, measure layer-wise activation, weight, and bias ranges on multiple images. Choose fixed-point widths per layer and sufficiently wide accumulators, then check overflow and output quality. Storing the two full intermediate maps at 16 bits would halve their theoretical capacity from about 23.81 MiB to 11.91 MiB, but quality may change. Decide from MSE/PSNR, synthesis resources, and latency. Finally, measure AXI burst behavior, transfer time, and PYNQ host overhead, comparing C simulation, synthesis estimates, and board results.

### Acceptance evidence by phase

| Phase | Record |
| --- | --- |
| Baseline | C-simulation MSE; HLS latency, II, area, clock; board time if available |
| Tiling | Golden comparison including all edges and corners; resource, II, and latency sweep over `Th/Tw/Tn/Tc` |
| Streaming | No FIFO deadlock; matching tile and full-image outputs; interface traffic and stage overlap |
| Quantization | Per-layer ranges and overflow; full-network MSE/PSNR; area, speed, and quality tradeoff |

Lecture references: `Lecture 08 - Project & CNNs.pdf` (blocked matrix multiplication and HLS dataflow) and `Lecture 09 - CNN Optimizations.pdf` (tiled convolution, quantization, dataflow, and AXI interfaces).

## Reference

- [sharc-lab FPGA_ECE8893 Lab2](https://github.com/sharc-lab/FPGA_ECE8893/tree/main/2023_Spring/Lab2): convolution and HLS implementation reference. Its network differs from this project's three-layer SRCNN.
