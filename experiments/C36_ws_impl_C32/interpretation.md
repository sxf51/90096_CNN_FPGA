C36 completes independent default-strategy 5 ns implementation, but fails setup:
WNS=-0.102 ns and TNS=-122.006 ns. WHS=+0.032 ns, zero unrouted/partial nets,
1032 DSP, 59891 LUT, 102084 FF, 109 BRAM18K and zero URAM pass the other gates.
The matching C35 four-call RTL is exact and has zero parameter AXI on both
267022-cycle reuse calls. Neither their conditional 1.335110 ms at 5 ns nor the
slack-derived 5.102 ns period establishes a verified frame time. C22 remains
the independently closed 1.365115 ms fallback.

The five final setup paths originate at the Conv3 window FIFO full_n register
and terminate at window-result register enables. The worst 4.973 ns data path
has only three logic levels: 0.381 ns logic and 4.592 ns routing (92.339%).
Thus this implementation's limiting reported paths concern window backpressure
and enable distribution, unlike W34's Winograd arithmetic/output conversion.
C37/C38 address their preplanned parameter and arithmetic hypotheses; their
new routing must establish which paths remain. Do not assume either change
repairs this newly observed Conv3 path.

The HLS paper estimates were 128868 LUT, 193984 FF and 146 BRAM18K. Large
deviations already appear in Vivado synthesis: 60913 LUT, 102248 FF and
109 BRAM18K, with the same 1032 DSP. The mapped/optimized netlist differs from
HLS operator, register and memory estimates before routing. Final implementation
changes those synthesis totals by -1022 LUT and -164 FF, with BRAM unchanged;
it cannot explain the initial greater-than-20-percent differences. The archived
synthesis and routed hierarchy CSVs localize the change; parent/child resource
rows overlap and must not be added. The exact contribution of each removed
register or width simplification is not established by these reports.

Actual child initialization and runtime hooks both report four implementation
threads and one synthesis thread. Staged telemetry reports 10.656689 GiB peak
process-tree RSS and 17.164562 percent host CPU occupancy across 12 logical CPUs.
The generated final report, its SHA256, the five paths and the synthesis/routed
hierarchies were copied without starting another Vivado process. Preserve this
failed baseline and every gate; proceed with independent WS-H screening, then
matching RTL/physical verification, required W35 and WS-I last.
