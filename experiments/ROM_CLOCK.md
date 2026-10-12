# ROM, clock, FIFO and T4 workstream

Plan: [docs/0005](../docs/0005-rom-clock-t4-plan.md). Updated 2026-10-12T18:05:52+00:00.

The user-accepted F47/F48 deep-window design is the T8 mainline basis; W21 remains the independently routed integration fallback. ROM is an independent experiment. Set14 means the complete 13-image course-provided set. Final resource acceptance uses independent OOC routed timing/utilization; archived HLS statuses are unchanged. No board performance is inferred.

## Current state

F50 RTL archived; C20 RTL active; W31/C19 queued; C21/C22 conditional. Five planned verification results remain: active C20 changed-parameter RTL, queued C19 RTL and W31 ROM5ns implementation, then conditional C21 T8 staged4.5ns implementation and C22 T4 staged5ns implementation. F50 passes both exact changed-parameter transactions at558760 latency/558789 interval cycles, two cycles slower than W21, so its raster output buffer gives no acceleration. Its supervisor completed and automatically resumed W31. C16/C17 all13-image precision and II1 HLS screens are complete; C17 keeps its historical HLS infeasible status. Launch C21 only after accepted C19 and C22 only after accepted C20; faster RTL has no lower cycle bound. C18/C14 remains the fastest verified runtime IP at1.503160ms, with its handoff archived; W30/W28 is the uniform T8 leader at2.472471ms. W31 closing5ns can trigger a separately planned ROM4.5ns probe. No resource-driven T4 ROM retry is required. Preserve one heavy task, budgeted light admission, the18GiB implementation registration and serial_after_oom while legacy workers exist. Complete plots, interpretations, two-location protected checksums and idle audit after runnable jobs finish. The16:06UTC snapshot audit passed with five pending plans and active remote jobs; it is not closure. No board results exist.

| id | parent | operation | status | bit_exact | delta_psnr | HLS_cycles | HLS_DSP | HLS_LUT | rtl_cycles | rtl_acceptance_basis | route_clock_ns | route_feasible | rtl_cycles_x_route_clock_ms | rtl_hls_excess_pct | wsD_goal_met |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F32](F32_ws0_memory_control_F28/F32.md) | F28 | csim/csynth | provisional | True | -0.0695141811880653 | 1046029.0 | 502.0 | 61553.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F33](F33_ws0_memory_control_W21/F33.md) | W21 | csim/csynth | provisional | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F34](F34_ws0_memory_control_F96/F34.md) | F96 | csim | csim_pass | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F36](F36_ws0_memory_control_F28/F36.md) | F28 | csim/csynth | provisional | True | -0.0695141811880653 | 1046029.0 | 502.0 | 61553.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F37](F37_ws0_memory_control_W21/F37.md) | W21 | csim/csynth | provisional | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F38](F38_ws0_memory_control_F96/F38.md) | F96 | csim | csim_pass | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F35](F35_runtime_rom_bank_equivalence/F35.md) | W19 | csim | csim_pass | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [W23](W23_ws_clock_strategy_4p5_W21/W23.md) | W21 | impl | fail | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | 6.382071331608397 | unknown |
| [W24](W24_constant_rom_T8/W24.md) | W19 | csim/csynth | pass | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown | unknown | unknown | 5.701752712986097 | unknown |
| [W25](W25_rom_changed_input_cosim_W24/W25.md) | W24 | cosim | cosim_complete | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | 554226.0 | original_verification_pass | unknown | unknown | unknown | 5.701752712986097 | unknown |
| [W26](W26_frp_W21_T8/W26.md) | W21 | csim/csynth | fail | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [W27](W27_frp_W21_T8/W27.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81484.0 | unknown | unknown | unknown | unknown | unknown | 4.6076342679590265 | unknown |
| [F39](F39_c3_select_W21_T8/F39.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81518.0 | unknown | unknown | unknown | unknown | unknown | 6.382071331608397 | unknown |
| [F40](F40_fifo16_W21_T8/F40.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | 6.382071331608397 | False |
| [F41](F41_fifo32_W21_T8/F41.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81105.0 | unknown | unknown | unknown | unknown | unknown | 6.382071331608397 | False |
| [F42](F42_reorder_W21_T8/F42.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81550.0 | unknown | unknown | unknown | unknown | unknown | 6.382452112094161 | False |
| [C13](C13_runtime_prepacked_conv2_T4/C13.md) | W21 | csim/csynth | infeasible | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127966.0 | unknown | unknown | unknown | unknown | unknown | 14.269641567524417 | unknown |
| [F43](F43_ws_cosim_F39/F43.md) | F39 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81518.0 | 558758.0 | original_verification_pass | unknown | unknown | unknown | 6.382071331608397 | unknown |
| [F44](F44_ws_cosim_F40/F44.md) | F40 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | 558758.0 | original_verification_pass | unknown | unknown | unknown | 6.382071331608397 | False |
| [F45](F45_ws_cosim_F41/F45.md) | F41 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81105.0 | 558758.0 | original_verification_pass | unknown | unknown | unknown | 6.382071331608397 | False |
| [F47](F47_windows16_W21_T8/F47.md) | W21 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | 2.0055708185066967 | False |
| [W28](W28_ws_cosim_W27/W28.md) | W27 | cosim | fail | True | -0.0695141811880653 | 525237.0 | 644.0 | 81484.0 | 549438.0 | user_authorized_upper_only | unknown | unknown | unknown | 4.6076342679590265 | unknown |
| [W29](W29_ws_impl_W24/W29.md) | W24 | impl | fail | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown | unknown | unknown | 5.701752712986097 | unknown |
| [W30](W30_ws_impl_W27/W30.md) | W27 | impl | impl_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81484.0 | 549438.0 | unknown | 4.5 | True | 2.472471 | 4.6076342679590265 | unknown |
| [F48](F48_ws_cosim_F47/F48.md) | F47 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | 535771.0 | original_verification_pass | unknown | unknown | unknown | 2.0055708185066967 | False |
| [F46](F46_ws_cosim_F42/F46.md) | F42 | cosim | fail | True | -0.0695141811880653 | 525237.0 | 644.0 | 81550.0 | unknown | rejected_or_unmeasured | unknown | unknown | unknown | unknown | unknown |
| [C14](C14_ws_cosim_C13/C14.md) | C13 | cosim | cosim_complete | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127966.0 | 300632.0 | original_verification_pass | unknown | unknown | unknown | 14.269641567524417 | unknown |
| [C15](C15_ws_impl_C13/C15.md) | C13 | impl | fail | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127966.0 | unknown | unknown | unknown | unknown | unknown | 14.269641567524417 | unknown |
| [F49](F49_ws_impl_F39/F49.md) | F39 | impl | fail | True | -0.0695141811880653 | 525237.0 | 644.0 | 81518.0 | unknown | unknown | unknown | unknown | unknown | 6.382071331608397 | unknown |
| [F50](F50_ws_cosim_F42/F50.md) | F42 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81550.0 | 558760.0 | original_verification_pass | unknown | unknown | unknown | 6.382452112094161 | False |
| [F51](F51_ws_impl_F47/F51.md) | F47 | impl | impl_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | 535771.0 | unknown | 5.0 | True | 2.678855 | 2.0055708185066967 | unknown |
| [F52](F52_ws_impl_F39/F52.md) | F39 | impl | impl_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81518.0 | 558758.0 | unknown | 4.5 | True | 2.514411 | 6.382071331608397 | unknown |
| [W31](W31_ws_impl_W24/W31.md) | W24 | impl | impl_complete | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | 554226.0 | unknown | 5.0 | True | 2.77113 | unknown | unknown |
| [W32](W32_ws_clock_strategy_4p5_retry_W21/W32.md) | W21 | impl | impl_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | 558758.0 | unknown | 4.5 | True | 2.514411 | 6.382071331608397 | unknown |
| [C16](C16_t8_fifo_frp/C16.md) | F47 | csim/csynth | pass | True | -0.0695141811880653 | 525237.0 | 644.0 | 81485.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [C17](C17_t4_fifo/C17.md) | C13 | csim/csynth | infeasible | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127985.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [C18](C18_ws_impl_C13/C18.md) | C13 | impl | impl_complete | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127966.0 | 300632.0 | unknown | 5.0 | True | 1.50316 | 14.269641567524417 | unknown |
| [C19](C19_ws_cosim_C16/C19.md) | C16 | cosim | cosim_complete | True | -0.0695141811880653 | 525237.0 | 644.0 | 81485.0 | 535976.0 | original_verification_pass | unknown | unknown | unknown | unknown | unknown |
| [C20](C20_ws_cosim_C17/C20.md) | C17 | cosim | cosim_complete | True | -0.07589037644656216 | 263090.0 | 1032.0 | 127985.0 | 273023.0 | original_verification_pass | unknown | unknown | unknown | unknown | unknown |

Missing measurements are unknown. A frame time is shown only for independently closed/resource-feasible routing plus matching-parent measured RTL cycles.

WS-D performance is separate from a successful functional cosimulation. With the525237-cycle HLS bound, the2% goal allows at most535741 integer RTL cycles (535741.74 before flooring); never round the threshold upward.
User revision in docs/0005 section6.2 accepts F48 as the new mainline basis despite its30-cycle diagnostic miss, and accepts faster W28 under the original upper bound only. Original result statuses and paper plans remain unchanged; the explicit acceptance basis records this authorization.

## Unmeasured plans

| id | parent | operation | status | condition |
| --- | --- | --- | --- | --- |
| [C21](C21_ws_impl_C16/C21.md) | C16 | impl | unlaunched_conditional | C19 must pass both exact changed-parameter RTL transactions before staged4.5ns implementation; compare the independently closed frame product to W30 |
| [C22](C22_ws_impl_C17/C22.md) | C17 | impl | unlaunched_conditional | C20 must pass both exact changed-parameter RTL transactions before staged5ns implementation; compare the independently closed frame product to C18 |

These plans have no result row. In particular, unlaunched implementation is neither a timeout nor a timing failure.

## Verified IP timing

| id | parent | rtl_source | rtl_cycles | route_clock_ns | route_WNS_ns | route_DSP | route_BRAM18K | route_LUT | route_FF | rtl_frame_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [C18](C18_ws_impl_C13/C18.md) | C13 | C14 | 300632.0 | 5.0 | 0.047 | 1032.0 | 109.0 | 58529.0 | 102072.0 | 1.50316 |
| [W30](W30_ws_impl_W27/W30.md) | W27 | W28 | 549438.0 | 4.5 | 0.027 | 644.0 | 109.0 | 54091.0 | 77784.0 | 2.472471 |
| [F52](F52_ws_impl_F39/F52.md) | F39 | F43 | 558758.0 | 4.5 | 0.072 | 644.0 | 109.0 | 43468.0 | 89030.0 | 2.514411 |
| [W32](W32_ws_clock_strategy_4p5_retry_W21/W32.md) | W21 | F97 | 558758.0 | 4.5 | 0.144 | 644.0 | 109.0 | 45030.0 | 89096.0 | 2.514411 |
| [F51](F51_ws_impl_F47/F51.md) | F47 | F48 | 535771.0 | 5.0 | 0.055 | 644.0 | 109.0 | 43617.0 | 87203.0 | 2.678855 |
| [W22](W22_ws_clock_4p95_W21/W22.md) | W21 | F97 | 558758.0 | 4.95 | 0.047 | 644.0 | 109.0 | 42592.0 | 88806.0 | 2.7658521 |
| [F98](F98_ws_impl_W21/F98.md) | W21 | F97 | 558758.0 | 5.0 | 0.14 | 644.0 | 109.0 | 42594.0 | 88806.0 | 2.79379 |

IP times exclude DDR, driver and board overhead. W21 remains the runtime-loaded integration fallback.

Verified candidate IP packages and register maps: [C18](board_handoff/C18/HANDOFF.md). Retain the [F98 integration handoff](BOARD_HANDOFF.md); board verification is pending.

## Figures

![Verified IP frame time versus routed DSP](figs/verified_ip_pareto.png)

![HLS screening](figs/rom_clock_pareto.png)

![DSP composition](figs/rom_clock_dsp.png)

![DSP estimates and measurements](figs/rom_clock_estimate_DSP.png)

![Cycle estimates and measurements](figs/rom_clock_estimate_latency_cycles.png)

![Two-frame RTL cycles](figs/rom_clock_rtl_cycles.png)


## Measured Parallel Execution

Current policy permits one heavy task with light jobs subject to registered budgets and actual memory headroom. The earlier two-heavy overlap failures remain visible. Completed tool intervals and per-task telemetry are in [parallel_jobs.csv](parallel_jobs.csv) and [parallel_overlap.csv](parallel_overlap.csv). Active tasks enter these tables only after a release record is archived.

| first_id | second_id | overlap_seconds | aligned_samples | peak_combined_process_tree_rss_GiB | minimum_available_GiB | cpu_busy_pct |
| --- | --- | --- | --- | --- | --- | --- |
| F43 | F46 | 3551.590785264969 | 1729 | 14.116714477539062 | 0.5022239685058594 | 18.49030818100524 |
| F43 | W28 | 401.79360151290894 | 191 | 11.563800811767578 | 2.8226356506347656 | 23.84113872200983 |
| W28 | C14 | 2752.318102836609 | 1337 | 12.649986267089844 | 2.3129348754882812 | 19.501111310893567 |
| W28 | F44 | 565.5901737213135 | 270 | 8.877937316894531 | 5.957366943359375 | 25.37125178827922 |
| F44 | F48 | 3247.45014834404 | 1581 | 13.121932983398438 | 1.8951187133789062 | 18.443802018977454 |
| F48 | F49 | 43.14403319358826 | 21 | 8.312904357910156 | 6.773231506347656 | 20.898714694065205 |
| F48 | F49 | 438.4953441619873 | 212 | 14.549797058105469 | 0.3904838562011719 | 22.087114337568057 |
| F48 | W23 | 12.646668434143066 | 6 | 6.898990631103516 | 6.786403656005859 | 27.73913043478261 |
| W23 | W29 | 48.38542175292969 | 23 | 6.715301513671875 | 9.157615661621094 | 31.001502937559774 |
| W23 | W29 | 342.5068440437317 | 161 | 16.554981231689453 | 0.5088157653808594 | 31.89580124556352 |
| W23 | C15 | 73.9129331111908 | 36 | 10.116344451904297 | 4.914371490478516 | 26.598767270810896 |
| W23 | C15 | 587.7770907878876 | 279 | 14.542190551757812 | 0.20591354370117188 | 29.55477371313919 |
| F50 | C17 | 121.88273620605469 | 59 | 3.2512283325195312 | 10.243728637695312 | 42.10668926993302 |
| F50 | C16 | 123.70464706420898 | 60 | 3.2514190673828125 | 10.243728637695312 | 42.08153758938877 |
| F50 | C17 | 901.2647974491119 | 441 | 6.877098083496094 | 8.201549530029297 | 17.577913663558654 |
| F50 | C16 | 538.6181435585022 | 262 | 7.094631195068359 | 7.980602264404297 | 17.747602567828178 |
| C17 | C16 | 121.87702989578247 | 59 | 1.9005126953125 | 10.32436752319336 | 42.15509217454121 |
| C16 | C17 | 1.8211803436279297 | 1 | 0.3324623107910156 | 11.27688217163086 | 20.689655172413794 |

Process-tree RSS sums include shared mappings; minimum MemAvailable is measured for the entire host. Sampling alignment tolerance is4seconds. A hatch marks nonzero tool exit, not failed timing closure.

![Measured task intervals](figs/parallel_timeline.png)

## Pending human decisions / 待人工决策

- Board validation remains unavailable to the agent; F98 handoff is archived.
- T4 ROM is conditional on C15/new combination routed pressure; preserve runtime interfaces until that separate experiment is planned.
