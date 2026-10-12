# F98 board handoff

Runtime-loaded mainline W21, independently implemented as [F98](F98_ws_impl_W21/F98.md). This is an out-of-context IP package; complete-system DDR/interconnect timing and board performance remain unmeasured. No ROM candidate replaces it.

## Package and provenance

Remote package: `/home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/F98/hls/impl/ip/xilinx_com_hls_srcnn_1_0.zip`.

Local collected package: `workspace/exp_runs/_handoff/F98/xilinx_com_hls_srcnn_1_0.zip`. Generated RTL and the ZIP remain outside Git; only driver sources/registers and this manifest are archived.

SHA256: `f9a93f91ace9b0367528fe8d4c2828ce9317e79288a753078db2599468215f38`.

[Manifest](board_handoff/F98/manifest.json), [register header](board_handoff/F98/xsrcnn_hw.h).

| metric | value |
| --- | --- |
| source_commit | 255fb6cd0c8f024696e33d9749cd6f2702311dee |
| rtl_latency_cycles | 558758.0 |
| rtl_interval_cycles | 558787.0 |
| route_clock_ns | 5.0 |
| max_ooc_clock_mhz | 200.0 |
| ideal_ip_frame_ms | 2.79379 |
| board_validation | unknown |

## Interface

The unchanged srcnn float32 signature exports image_in and image_out m_axi bundles, one shared parameters m_axi bundle, and control s_axilite. Images contain65025 row-major floats (260100bytes). Weights follow Cout/Cin/kernel-row/kernel-column: Conv1=5184, Conv2=2048, Conv3=800 floats, and biases=64/32/1 floats. Parameters load on every invocation. The generated control pointers are64-bit; offsets below are their low words and the high word is offset+4.

| argument | offset | pointer_bits |
| --- | --- | --- |
| in_r | 0x10 | 64 |
| weights1 | 0x1c | 64 |
| biases1 | 0x28 | 64 |
| weights2 | 0x34 | 64 |
| biases2 | 0x40 | 64 |
| weights3 | 0x4c | 64 |
| biases3 | 0x58 | 64 |
| out_r | 0x64 | 64 |

AP control=0x00; start bit0, done bit1(clear-on-read), idle bit2, ready bit3 and auto_restart bit7. Use the generated driver as the authoritative interface. Flush input/parameter caches before starting and invalidate output caches after completion when using cacheable host buffers.

## Board measurements

1. Integrate this IP and independently close the complete block-design timing. F98's OOC clock limit is200MHz.
2. Read the actual PL clock registers; record frequency and divider rather than assuming the requested frequency. With a1000MHz IOPLL, divide5 gives200MHz.
3. Use the same bitstream at two supported PL clocks. Record IP-start/done latency separately from allocations, cache maintenance, DDR and driver overhead. Convert measured elapsed time to PL cycles.
4. Measure one invocation and repeated invocations, retaining runtime weight reload. Check all output bits against the fixed reference and the six-pixel border before accepting performance.
5. Record actual board/bitstream/software commits, actual clocks, outputs and timing distributions here; no board measurement has been provided yet.
