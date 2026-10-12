# ROM, clock, FIFO and T4 workstream

Plan: [docs/0005](../docs/0005-rom-clock-t4-plan.md). Updated 2026-10-12T04:35:46+00:00.

Runtime-loaded W21 remains the mainline. ROM is an independent experiment. Set14 means the complete 13-image course-provided set. Final resource acceptance uses independent OOC routed timing/utilization; archived HLS statuses are unchanged. No board performance is inferred.

## Current state

WS-0 complete; WS-B validation; WS-C1 awaiting memory admission. F36/F37/F38 corrected trial passed with77.827s triple overlap, peak synth3.430GiB, minimum10.706GiB available and no OOM. Remote budgeted concurrency is enabled with csynth4GiB/csim1.25GiB. F35 validates all12161 ROM carriers exactly. Run W24 complete13-image C validation and synthesis, then same-weight/changed-input two-frame RTL. W23 same-RTL4.5ns strategy/threads are prepared but unlaunched:12.5GiB reservation requires14.5GiB available, while idle host has about13.4GiB. Keep the2GiB floor and13GiB total cap; report the decision before any implementation.

| id | parent | operation | status | md_path | bit_exact | delta_psnr | HLS_cycles | HLS_DSP | HLS_LUT | route_feasible | route_clock_ns | route_WNS_ns | route_WHS_ns | DSP | BRAM18K | URAM | LUT | FF | rtl_cycles | rtl_source | rtl_cycles_x_route_clock_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [F32](F32_ws0_memory_control_F28/F32.md) | F28 | csim/csynth | provisional | F32_ws0_memory_control_F28/F32.md | True | -0.0695141811880653 | 1046029.0 | 502.0 | 61553.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F33](F33_ws0_memory_control_W21/F33.md) | W21 | csim/csynth | provisional | F33_ws0_memory_control_W21/F33.md | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F34](F34_ws0_memory_control_F96/F34.md) | F96 | csim | csim_pass | F34_ws0_memory_control_F96/F34.md | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F36](F36_ws0_memory_control_F28/F36.md) | F28 | csim/csynth | provisional | F36_ws0_memory_control_F28/F36.md | True | -0.0695141811880653 | 1046029.0 | 502.0 | 61553.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F37](F37_ws0_memory_control_W21/F37.md) | W21 | csim/csynth | provisional | F37_ws0_memory_control_W21/F37.md | True | -0.0695141811880653 | 525237.0 | 644.0 | 81086.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F38](F38_ws0_memory_control_F96/F38.md) | F96 | csim | csim_pass | F38_ws0_memory_control_F96/F38.md | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [F35](F35_runtime_rom_bank_equivalence/F35.md) | W19 | csim | csim_pass | F35_runtime_rom_bank_equivalence/F35.md | True | -0.0695141811880653 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |
| [W24](W24_constant_rom_T8/W24.md) | W19 | csim/csynth | pass | W24_constant_rom_T8/W24.md | True | -0.0695141811880653 | 524330.0 | 630.0 | 53316.0 | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown |

Missing measurements are unknown. A frame time is shown only for independently closed/resource-feasible routing plus matching-parent measured RTL cycles.

## Pending human decisions / 待人工决策

- Initial remote MemAvailable=14091148 KiB (13.438 GiB), below 14.5 GiB required by the 12.5 GiB implementation reservation plus 2 GiB floor. Keep both stated memory gates; if unchanged after WS-0, record W23 as waiting for memory and continue independent coding/C simulations/syntheses.
