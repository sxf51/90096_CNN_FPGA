# Documentation Index

[中文版](README.md)

| Document | Contents |
| --- | --- |
| [Experiment ideas and evolution](0004-experiment-evolution.en.md) | 207 experiments and 307 dependencies through C18 T4, W32/F52 4.5 ns, ROM/FRP/FIFOs, and pending combinations |
| [One complete evolution graph](experiment-evolution/full.en.svg) / [Local viewer](experiment-evolution/full.en.html) | 207 nodes, 217 main arrows, common network ms/frame; arrow clearance and rendered-pixel checks |
| [Key milestones](experiment-evolution/milestones.en.svg) / [Local viewer](experiment-evolution/milestones.en.html) | Ten compact nodes: IDs, title, one result; failed nodes show only the specific problem |
| [First-round experiment design](0002-overnight-experiments.md) | Acceptance constraints for golden, precision, compiler controls, and streaming scans |
| [Second-round architecture exploration](0003-architecture-exploration.md) | Packing, scatter, Winograd, combinations, continuous scheduling, and verification workflow |
| [T8 and weight-loading plan](0004-t8-weight-loading-plan.md) | Stage gates for private parameter banks, Winograd T8, parameter reload, and independent routing; closure in the [workflow results](../experiments/WEIGHT_LOADING.md) |
| [Constant weights, clocks, FIFOs, and T4](0005-rom-clock-t4-plan.md) | Current routed gates, host policy, and remaining acceptance; results in [ROM_CLOCK](../experiments/ROM_CLOCK.md) |
| [T4](experiment-evolution/t4.en.svg) / [T8 clocks and FIFOs](experiment-evolution/clock-fifo.en.svg) / [ROM](experiment-evolution/rom.en.svg) / [Host controls](experiment-evolution/host.en.svg) | 37 new experiments, independent verification, host failures, and retries |
| [Complete experiment ledger](experiment-evolution/records.en.md) | Each experiment's parents, configuration, measured results, limitations, and original evidence |
| [Diagram/data generation](experiment-evolution/README.en.md) | Snapshot scope, translation synchronization, regeneration, and layout checks |
| [KV260 tile fusion and INT8 trial](0004-kv260-tiled-int8.md) | Implementation and validation of the root `src/` tile-fusion baseline (board-tested, 2.2 s/frame) and the optional INT8 variant (Chinese) |
| [KV260 board clock and latency diagnosis](0005-kv260-board-clock.md) | Runtime PL clock 66.666 MHz versus the 100 MHz design value, and the latency gap analysis (Chinese) |
| [Hardware acceleration review](0006-hardware-acceleration-review.md) | Presentation record for the tile-fusion baseline (Chinese) |
| [Summary](re.md) / [Lecture script](srcnn-presentation-lecture-script.md) | Report text and lecture-based talk script for the tile-fusion baseline (Chinese) |
| [Frozen experiment reproduction](../experiments/REPRODUCE.md) | Restore archived design, tests, and settings under a fresh ID |

Root `src/` and `script.py` hold the KV260 tile-fusion baseline (see [0004-kv260-tiled-int8](0004-kv260-tiled-int8.md)). Architecture-exploration sources and frozen archives live in `designs/` and `experiments/`. Numbers 0004 and 0005 each cover two or three documents because two parallel lines of work were merged; distinguish them by file name. Read HLS estimates, RTL simulation, routed timing, and board measurements as separate evidence.
