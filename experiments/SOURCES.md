# Architecture calculation sources

AMD, *Deep Learning with INT8 Optimization on Xilinx Devices*, WP486 v1.0.1,
2017-04-24, pages 3-4 and 7: [official document](https://docs.amd.com/v/u/en-US/wp486-deep-learning-int8).
The DSP48E2 has a signed 27x18 multiplier and 27-bit pre-adder. Page 4 specifies
packing the high signed INT8 operand at bit 18; this retains two sign bits at
the packed 27-bit port. The low product field guarantees at most seven terms
before unpacking or an additional accumulation DSP is needed. The published
1.75x MAC throughput includes that extra accumulation DSP and is different
from two independent products per multiplier. Negative low-product borrow must
be corrected. Wider activation operands require their own low-field bound.

AMD, *Kria K26 SOM Data Sheet*, DS987 v1.6, 2026-03-25, page 2,
Functional Overview and Block Diagram:
[official section](https://docs.amd.com/r/en-US/ds987-k26-som/Functional-Overview-and-Block-Diagram).
It specifies "4 GB 64-bit wide, 2400 Mb/s memory"; page 3 shows four x16 DDR4
devices. The theoretical bandwidth is `64 / 8 * 2.4e9 = 19.2e9 bytes/s`.
The requested 50% efficiency scenario is `9.6e9 bytes/s`, an assumption rather
than a measured KV260 AXI bandwidth. DDR-limited time is `bytes / bandwidth`;
it is a lower bound before controller, AXI, arbitration and non-burst overhead.

For float DDR feature maps, the traffic model counts one write and one read
of each full Conv1 and Conv2 intermediate map, plus input, output, weights
and biases. It assumes each map is read only once; a schedule that rereads
per output channel must report its larger actual byte count. Burst lengths
come from interface/burst synthesis evidence, not only pragma targets.

PDF copies used for inspection remain in the ignored
`workspace/exp_runs/_tools/wp486_source.pdf` and `ds987_source.pdf`.
Their download URLs are:

- `https://docs.amd.com/api/khub/documents/z7yAy_aweTmRYkGaTVyhbw/content`
- `https://docs.amd.com/api/khub/maps/gX6THsxXsWUzU8xcmObJnQ/attachments/SXafmCH9kPqXjywx_5dRBA-gX6THsxXsWUzU8xcmObJnQ/content`

Lavin and Gray, *Fast Algorithms for Convolutional Neural Networks*, CVPR 2016,
F(2x2,3x3): [paper](https://arxiv.org/abs/1509.09308).
The exact integer variant uses `G2=2G`, so transformed output has scale four;
the complete integer inverse transform must be divisible by four before any
layer-boundary quantization. Splitting a 9x9 kernel into nine 3x3 subkernels
requires nine 4x4 transformed products per 2x2 output tile: `9*16*64/4=2304`
multiplications per output pixel. Transforms, buffering, rounding and raster
reordering are additional costs and require separate measurements.

The inspected Vitis 2026.1 SDK provides `hls_dsp_builtins.h`,
`hls::dsp48e2::add_mul_add<flags>(d,a,b,c)` and the registered accumulator
class in `etc/dsp_functions.h`. They explicitly expose the pre-adder and
DSP48E2 rather than relying only on compiler pattern matching. Their presence
does not establish synthesizability in this unified flow: the header has an
`__PRESYNTHESIS__` unsupported guard, so a microbenchmark must test it.
The SDK also provides `hls_streamofblocks.h` with `write_lock` / `read_lock`
RAII ownership for raster-row reorder buffers. These SDK headers are used
from the installed toolchain and are not copied into tracked source.
