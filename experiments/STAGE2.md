# Stage 2: compiler controls

All valid compiler-only variants are resource-infeasible. The fastest float control is E029; type-change E027 approaches its latency but has a very expensive parameter load and still stores full feature maps. No compiler flag removes the need to redesign storage and streaming.

| id | latency_ms_est | DSP | BRAM18K | LUT | status |
| --- | --- | --- | --- | --- | --- |
| E020 | 19601.13853 | 10.0 | 11064.0 | 9377.0 | infeasible |
| E021 | 17179.087404 | 10.0 | 11064.0 | 9997.0 | infeasible |
| E022 | 44822.23011 | 5.0 | 11064.0 | 2217.0 | infeasible |
| E026 | 19601.13671 | 10.0 | 11064.0 | 7624.0 | infeasible |
| E027 | 3912.56088 | 66.0 | 5822.0 | 137322.0 | infeasible |
| E028 | 12170.258489978001 | 12.0 | 11064.0 | 9914.0 | infeasible |
| E029 | 3811.21723 | 320.0 | 11114.0 | 80812.0 | infeasible |
| E032 | 12170.258489978001 | 12.0 | 11096.0 | 8585.0 | infeasible |

E023/E024/E025 remain invalid_config because their original directive key was skipped. They are not evidence for the intended configurations.
