# Streaming structure and measured overhead

| id | T | ideal_MAC_DSP | actual_DSP | compute_floor_cycles | actual_cycles | cycle_overhead_pct | C1_DSP | C2_DSP | C3_DSP | C1_cycles | C2_cycles | C3_cycles | clock_ns | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E033 | 32.0 | 251.0 | 9.0 | 2080800.0 | 3882221.0 | 86.57348135332566 | 6.0 | 3.0 | 0.0 | 3873991.0 | 2080820.0 | 2549597.0 | 31.822 | infeasible |
| E044 | 16.0 | 502.0 | 18.0 | 1040400.0 | 2775517.0 | 166.77402921953095 | 12.0 | 6.0 | 0.0 | 2767287.0 | 1040420.0 | 1476301.0 | 63.218 | infeasible |
| E047 | 32.0 | 251.0 | 251.0 | 2080800.0 | 2913855.0 | 40.03532295271051 | 162.0 | 64.0 | 25.0 | 2905625.0 | 2080808.0 | 2750840.0 | 7.3 | infeasible |
| E031 | 32.0 | 251.0 | 9.0 | 2080800.0 | 3882221.0 | 86.57348135332566 | 6.0 | 3.0 | 0.0 | 3873991.0 | 2080820.0 | 2549597.0 | 31.822 | infeasible |

E030 float and fixed architecture butterfly outputs match their respective references bit for bit. All 65,025 output pixels and the six-pixel border are checked. Padding emits 69,169 first-layer and 67,081 third-layer tokens; output remains 65,025. AXI input/output/weights retain float arrays, sequential bursts up to 256 words, and AXI-Lite pointer/control registers. No intermediate feature map goes to DDR. Weight and bias load happens before DATAFLOW. Inferred burst lengths and throughput are report values, not measured board bandwidth.
