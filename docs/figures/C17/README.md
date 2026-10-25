# C17 report figures

Eight SVG figures describing the C17 design (`designs/winograd_t4_windows32_v1`, T = 4, 32-entry window FIFO) and its verification chain C17 (csim + csynth) → C20 (C/RTL co-simulation) → C22 (Vivado implementation at 5 ns).

| File | Content | Data |
| --- | --- | --- |
| `fig1_fold_timing.svg` | Per-cycle schedule of the three folded MAC loops: what each step computes, DSPs per cycle, iteration count, pipeline depth | `plain/C17_srcnn_plain.cpp`, `experiments/C17_t4_fifo/reports/*_fold_csynth.rpt` |
| `fig2_balance.svg` | Multiplications per frame, DSP allocation and loop cycles per layer; shows why the three layers take almost equal cycles | loop bounds in the source, C17 csynth |
| `fig3_dataflow_backpressure.svg` | Dataflow processes and FIFOs (depth × width) coloured by measured write/read blocking; inset compares the depth-2 (C14) and depth-32 (C20) window FIFO | `experiments/C20_ws_cosim_C17/profiling/`, `experiments/C14_ws_cosim_C13/profiling/` |
| `fig4_process_gantt.svg` | Activity span and waiting share of each process within one 273,052-cycle RTL frame, with HLS / RTL / C14 reference lines | `experiments/C20_ws_cosim_C17/profiling/processes.csv` |
| `fig5_bitwidth_flow.svg` | Fixed-point widths and fraction bits along the conv1 Winograd, conv2 packed and conv3 paths | `plain/C17_srcnn_plain.cpp` |
| `fig6_hls_vs_routed.svg` | HLS resource estimate vs Vivado post-route per module and for the whole design; timing summary | `experiments/C17_t4_fifo/C17.md`, `experiments/C22_ws_impl_C17/` |
| `fig7_conv2_packing.svg` (+ PNG) | conv2 packed multiply: bit layout of the 27-bit weight word, 10-bit activation and 37-bit product with borrow repair; per-cycle fold structure; measured PE alternatives | `plain/C17_srcnn_plain.cpp`, `experiments/P01`, `P02`, `P07` |
| `fig8_conv3_window_engine.svg` (+ PNG) | conv3 line buffer, 5x5x32 window split into two 4,000-bit streams, and the four-cycle fold with the 256-input adder tree | `plain/C17_srcnn_plain.cpp`, `experiments/C17_t4_fifo/reports/`, C22 routed BRAM |

Regenerate (no third-party dependencies):

```sh
python3 exp/figures/c17_report_figures.py            # writes docs/figures/C17/*.svg
python3 exp/figures/c17_report_figures.py --out DIR  # elsewhere
rsvg-convert -z 2 -f png -o docs/figures/C17/fig7_conv2_packing.png docs/figures/C17/fig7_conv2_packing.svg   # PNG for pasting
python3 exp/figures/c17_report_figures.py --no-title --out docs/figures/C17/notitle   # same figures without the in-figure title, for documents that add their own caption
```

`notitle/` holds the same eight figures with the title band cropped (SVG and PNG), for pasting where the document supplies the caption.
