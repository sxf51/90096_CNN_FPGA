The independent 4.5 ns implementation completes but fails setup: WNS=-0.324 ns,
TNS=-51.194 ns, WHS=+0.032 ns, with zero unrouted and partially routed nets.
Its 1032 DSP, 59893 LUT, 101443 FF, 109 BRAM18K and zero URAM pass the physical
resource gates. C20 supplies the matching exact 273023-cycle RTL measurement;
273023*4.5 ns is conditional arithmetic, not verified frame time because timing
did not close. Preserve C22's independently closed 5 ns fallback.

The frozen HLS paper counts were 1032 DSP, 127985 LUT, 192308 FF and 146 BRAM18K.
DSP matches; the large LUT/FF/BRAM deviations already appear in Vivado synthesis
(60637 LUT, 100633 FF, 109 BRAM18K), before placement or the final strategy
optimization. They therefore reflect the HLS estimator versus the mapped,
optimized netlist rather than an arithmetic change or a benefit from routing.
The physical hierarchy localizes this: conv1_stream maps to 22773 LUT/25050 FF/
45 BRAM18K versus HLS 46402/49181/81; the Winograd engine maps to 17297 LUT/
11546 FF versus HLS 38414/41307. The reports do not identify every removed
register or estimator assumption, so the precise contribution of constant/width
optimization and memory mapping remains unmeasured. Final physical optimization
changes synthesis totals by only -744 LUT and +810 FF, with BRAM unchanged.
The routed 1728-bit, depth32 window FIFO is 1038 LUT, including 988 LUTRAM;
its small HLS LUT prediction cannot be used as its physical storage cost.

All five final setup paths are within the Winograd fold's arithmetic/output
conversion, with 8-11 logic levels. The worst data delay is 4.822 ns, split into
1.337 ns logic and 3.485 ns routing in the final post-route report, from a
result register to the truncation register. Balancing the nine-product sum may
leave this output-transform/quantization path, which needs its own measured
assessment. The report was copied without launching another Vivado process.

The archived child initialized general.maxThreads=1, although the plan requested
4. Physical optimization also reported a one-CPU limit. Separate-stage telemetry
measures 10.642868 GiB peak process-tree RSS and 9.633758 percent host CPU occupancy
across 12 logical CPUs. Thread limits and measured CPU occupancy are different
metrics. This is the actual one-thread result; W36 separately tests the repaired
four-thread flow. No 4 ns follow-up is eligible until a matching 4.5 ns point
independently closes, and no board or DDR timing is inferred.
