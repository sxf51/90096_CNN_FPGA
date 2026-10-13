C37 passes all13 E065-exact images, including the unchanged six-pixel border
MSE and -0.0758903764 dB mean PSNR delta. All three compute folds achieve II1.
HLS counts are 1032 DSP, 128942 LUT, 194250 FF, 146 BRAM18K and zero URAM;
screening passes, while the historical HLS infeasible status remains until
independent physical validation. Relative to C32, this adds74 LUT and266 FF.

The read-only register_evidence.json confirms all16 14-bit transformed parameter
fields have posedge-ap_clk nonblocking assignments and registered return ports.
The caller feeds each from the matching FIFO slice and drives the same36 bank
write ports per field as the parent's direct path. No direct FIFO-to-bank bypass
is present. The helper report has latency1, interval1,226FF and2LUT. This is
HLS datapath evidence, not proof the stage survives physical optimization or
fixes routed fanout. Source hashes, exact line excerpts and the parent comparison
are archived; eight focused checks cover control-only/combinational/partial
stages, wrong clocks, concatenated fields and aliased bypasses.

The top HLS bound rises from263090 to263154 cycles,64cycles rather than the
128loaded-cycle allowance. That bound is distinct from the273153 paper estimate
of loaded RTL time, which starts from C35's measured273025 cycles. C39 will
measure every transaction under C35's unchanged per-call +1percent upper limits;
C40 may route4.5ns only after strict exact/zero-parameter-AXI RTL acceptance.
C36's measured Conv3-enable bottleneck remains relevant. C22 is the verified
fallback until matching physical timing closes; no board time is inferred.
