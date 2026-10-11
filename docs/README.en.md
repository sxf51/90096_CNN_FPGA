# Documentation Index

[中文版](README.md)

| Document | Contents |
| --- | --- |
| [Experiment ideas and evolution](0004-experiment-evolution.en.md) | Dependencies, design changes, outcomes, and failure points for 153 experiments; explains F25 and its verification records |
| [One complete evolution graph](experiment-evolution/full.en.svg) / [Local viewer](experiment-evolution/full.en.html) | All 153 compact nodes and 207 dependencies, bold metrics, status colors, and faded failures |
| [First-round experiment design](0002-overnight-experiments.md) | Acceptance constraints for golden, precision, compiler controls, and streaming scans |
| [Second-round architecture exploration](0003-architecture-exploration.md) | Packing, scatter, Winograd, combinations, continuous scheduling, and verification workflow |
| [Complete experiment ledger](experiment-evolution/records.en.md) | Each experiment's parents, configuration, measured results, limitations, and original evidence |
| [Diagram/data generation](experiment-evolution/README.en.md) | Snapshot scope, translation synchronization, regeneration, and layout checks |
| [Frozen experiment reproduction](../experiments/REPRODUCE.md) | Restore archived design, tests, and settings under a fresh ID |

Root `src/` and `script.py` remain the original floating-point baseline. Optimized sources and frozen archives live in `designs/` and `experiments/`. Read HLS estimates, RTL simulation, routed timing, and board measurements as separate evidence.
