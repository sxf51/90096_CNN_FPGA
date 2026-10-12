# ROM, clock, FIFO and T4 workstream

Plan: [docs/0005](../docs/0005-rom-clock-t4-plan.md). Updated 2026-10-12T03:56:14+00:00.

Runtime-loaded W21 remains the mainline. ROM is an independent experiment. Set14 means the complete 13-image course-provided set. Final resource acceptance uses independent OOC routed timing/utilization; archived HLS statuses are unchanged. No board performance is inferred.

## Current state

WS-0 preparation. Implement and test route gates and memory admission; run controlled two-synthesis plus C-simulation trial before enabling concurrency. Prepare WS-B during the W23 physical run when admitted.

| id | status | route_feasible |
| --- | --- | --- |

Missing measurements are unknown. A frame time is shown only for independently closed/resource-feasible routing plus matching-parent measured RTL cycles.

## Pending human decisions / 待人工决策

- Initial remote MemAvailable=14091148 KiB (13.438 GiB), below 14.5 GiB required by the 12.5 GiB implementation reservation plus 2 GiB floor. Keep both stated memory gates; if unchanged after WS-0, record W23 as waiting for memory and continue independent coding/C simulations/syntheses.
