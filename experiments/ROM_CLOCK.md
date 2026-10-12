# ROM, clock, FIFO and T4 workstream

Plan: [docs/0005](../docs/0005-rom-clock-t4-plan.md). Updated 2026-10-12T07:05:37+00:00.

Runtime-loaded W21 remains the mainline. ROM is an independent experiment. Set14 means the complete 13-image course-provided set. Final resource acceptance uses independent OOC routed timing/utilization; archived HLS statuses are unchanged. No board performance is inferred.

## Current state

WS-0 complete; eight HLS designs passed; two concurrent RTL simulations active under explicit user authorization. F43 registeredConv3 and F46 rasterFIFO cosim run concurrently. W28/F48/C14/F44 waiting workers have been migrated without changing plans or prepared RTL and now use the two-task scheduler. Collect each finished remote archive with --collect-only. F45 featureFIFO32 passed changed-parameter RTL at558758cycles, identical to F97; reduced producer write blocking did not meet the WS-D535741-cycle goal. W25 ROM passed at554226cycles. F43/W28 retain the553171..564345 gate. C13 remains E065-exact on all13 images, with1032DSP/127966LUT/192308FF/263090HLS cycles; C14 must pass before C15 routing. Run W23/W29/W30/C15 and an independent registeredConv3 route after their prerequisites; the prior impossible12.5+2GiB admission is superseded by explicit user authorization for two concurrent tasks. Keep actual memory sampling, newest-task pressure termination at0.5GiB, OOM evidence and serial fallback. F98 board handoff is archived; board measurements remain pending.

| id | parent | operation | status | bit_exact | delta_psnr | HLS_cycles | HLS_DSP | HLS_LUT | rtl_cycles | route_clock_ns | route_feasible | rtl_cycles_x_route_clock_ms | rtl_hls_excess_pct | wsD_goal_met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F32](F32_ws0_memory_control_F28/F32.md) | F28 | csim/csynth | provisional | True | -0.0695141811880653 | 1046029.0 | 502.0 | 61553.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F33](F33_ws0_memory_control_W21/F33.md) | W21 | csim/csynth | provisional | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F34](F34_ws0_memory_control_F96/F34.md) | F96 | csim | csim_pass | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F36](F36_ws0_memory_control_F28/F36.md) | F28 | csim/csynth | provisional | True | -0.0695141811880653 | 1046029.0 | 502.0 | 61553.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F37](F37_ws0_memory_control_W21/F37.md) | W21 | csim/csynth | provisional | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F38](F38_ws0_memory_control_F96/F38.md) | F96 | csim | csim_pass | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F35](F35_runtime_rom_bank_equivalence/F35.md) | W19 | csim | csim_pass | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [W24](W24_constant_rom_T8/W24.md) | W19 | csim/csynth | pass | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown | unknown | 5.701752712986097 | unknown |
| [W25](W25_rom_changed_input_cosim_W24/W25.md) | W24 | cosim | cosim_complete | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | 554226.0 | unknown | unknown | unknown | 5.701752712986097 | unknown |
| [W26](W26_frp_W21_T8/W26.md) | W21 | csim/csynth | fail | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [W27](W27_frp_W21_T8/W27.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81484.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F39](F39_c3_select_W21_T8/F39.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81518.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F40](F40_fifo16_W21_T8/F40.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F41](F41_fifo32_W21_T8/F41.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81105.0 | unknown | unknown | unknown | unknown | 6.382071331608397 | False |
| [F42](F42_reorder_W21_T8/F42.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81550.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [C13](C13_runtime_prepacked_conv2_T4/C13.md) | W21 | csim/csynth | infeasible | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127966.0 | unknown | unknown | unknown | unknown | unknown | unknown |
| [F45](F45_ws_cosim_F41/F45.md) | F41 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81105.0 | 558758.0 | unknown | unknown | unknown | 6.382071331608397 | False |
| [F47](F47_windows16_W21_T8/F47.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown |

Missing measurements are unknown. A frame time is shown only for independently closed/resource-feasible routing plus matching-parent measured RTL cycles.

WS-D performance is separate from a successful functional cosimulation. With the525237-cycle HLS bound, the2% goal allows at most535741 integer RTL cycles (535741.74 before flooring); never round the threshold upward.

## Unmeasured plans

| id | parent | operation | status | condition |
| --- | --- | --- | --- | --- |
| [W23](W23_ws_clock_strategy_4p5_W21/W23.md) | W21 | impl | unlaunched_conditional | unknown |
| [F43](F43_ws_cosim_F39/F43.md) | F39 | cosim | queued_or_running | unknown |
| [F44](F44_ws_cosim_F40/F44.md) | F40 | cosim | queued_or_running | unknown |
| [W28](W28_ws_cosim_W27/W28.md) | W27 | cosim | queued_or_running | unknown |
| [W29](W29_ws_impl_W24/W29.md) | W24 | impl | unlaunched_conditional | W25 same-ROM/changed-input two-frame RTL must pass before implementation |
| [W30](W30_ws_impl_W27/W30.md) | W27 | impl | unlaunched_conditional | W28 FRP changed-parameter RTL must pass the preplanned plus/minus1 percent cycle gate before implementation |
| [F48](F48_ws_cosim_F47/F48.md) | F47 | cosim | queued_or_running | unknown |
| [F46](F46_ws_cosim_F42/F46.md) | F42 | cosim | queued_or_running | unknown |
| [C14](C14_ws_cosim_C13/C14.md) | C13 | cosim | queued_or_running | unknown |
| [C15](C15_ws_impl_C13/C15.md) | C13 | impl | unlaunched_conditional | C14 mixed-precision changed-parameter RTL must pass before implementation; compare its frame product to W22 |

These plans have no result row. In particular, unlaunched implementation is neither a timeout nor a timing failure.

## Verified IP timing

| id | parent | rtl_source | rtl_cycles | route_clock_ns | route_WNS_ns | route_DSP | route_BRAM18K | route_LUT | route_FF | rtl_frame_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [W22](W22_ws_clock_4p95_W21/W22.md) | W21 | F97 | 558758.0 | 4.95 | 0.047 | 644.0 | 109.0 | 42592.0 | 88806.0 | 2.7658521 |
| [F98](F98_ws_impl_W21/F98.md) | W21 | F97 | 558758.0 | 5.0 | 0.14 | 644.0 | 109.0 | 42594.0 | 88806.0 | 2.79379 |

IP times exclude DDR, driver and board overhead. W21 remains the runtime-loaded integration fallback.

## Figures

![HLS screening](figs/rom_clock_pareto.png)

![DSP composition](figs/rom_clock_dsp.png)

![DSP estimates and measurements](figs/rom_clock_estimate_DSP.png)

![Cycle estimates and measurements](figs/rom_clock_estimate_latency_cycles.png)

![Two-frame RTL cycles](figs/rom_clock_rtl_cycles.png)


## Pending human decisions / 待人工决策


