// Flattened version of C17 (designs/winograd_t4_windows32_v1), for reading and analysis only.
//
// Relationship to the original:
//   - Computation, dataflow structure, all HLS pragmas and FIFO depths are identical to the original.
//   - Compile-time macros are substituted: T=4, EXP_ALL_CONTINUOUS=1, EXP_ONLINE_PAD=1,
//     EXP_W_BITS=10, EXP_A_BITS=10, EXP_C*_SPLIT=0, EXP_ROW_LUTRAM is not defined.
//   - Bit widths are written as the ap_int types used during synthesis (__SYNTHESIS__);
//     the original uses int16/int32/int64 instead in C simulation.
//   - Function names, loop labels and variable names are kept as close to the original as possible,
//     so they can be matched against the HLS reports.
//
// Original name → how it is written here:
//   weight, bias, input, act1, act2, output   → ap_int<10>
//   weight2                                   → ap_int<8>
//   acc1, acc2, acc3                          → ap_int<23>
//   mixed_acc                                 → ap_int<21>
//   transformed_input / transformed_weight    → ap_int<12> / ap_int<14>
//   inverse                                   → ap_int<34>
//   word<27>                                  → ap_int<27>
//   Reduction<64>::sum, Reduction<256>::sum   → add_tree_64, add_tree_256
//   online_pad<input,4>, online_pad<pixel2,2> → online_pad1, online_pad3
//   quantize<9>, quantize<8>(21-bit), quantize<8>(23-bit) → quantize_conv1/2/3
//   load_local(...)                           → written directly into engine3
//   T=4, WOC=4, PAIRS=4, C3_IC=8, COUNT=256, TILE_H=TILE_W=128
//
// Fixed-point formats (stored integer = real value × 2^fraction_bits):
//   Input pixels, conv1 output, final output  ap_int<10>, 8 fractional bits (ap_fixed<10,2>)
//   conv2 output                              ap_int<10>, 7 fractional bits
//   conv1, conv3 weights and biases           ap_int<10>, 9 fractional bits (ap_fixed<10,1>)
//   conv2 weights and biases                  ap_int<8>,  7 fractional bits (ap_fixed<8,1>)
//   Accumulators                              ap_int<23>
//
// Dataflow (processes inside dataflow_region; arrows are hls::stream):
//   read_input → online_pad1 → conv1 → conv2 → online_pad3 → conv3 → write_output
//   conv1 = wino_windows → wino_engine → distribute_tiles → reorder_rows
//   conv3 = windows3 → engine3
//   read_params = read_raw_params → transform_params1, which sends the weights to each of the three layers

#include <ap_int.h>
#include <ap_fixed.h>
#include <hls_stream.h>
#include <utils/x_hls_utils.h>   // fp_struct<float>: builds a float directly from sign, exponent and mantissa

struct pixel1 { ap_int<10> v[64]; };               // One conv1 output pixel, 64 channels
struct pixel2 { ap_int<10> v[32]; };               // One conv2 output pixel, 32 channels
struct window3 { ap_int<10> v[400]; };             // 5x5 window for conv3, holding only half the channels: 25 × 16 = 400
struct transformed_params1 { ap_int<14> v[16]; };  // One 3x3 sub-kernel after the Winograd transform: 4x4 = 16 values
struct transformed_window { ap_int<12> v[9][16]; };// One 10x10 input block: 9 4x4 sub-blocks, 16 transformed values each
struct tile_block { pixel1 pixel[4]; };            // 2x2 = 4 output pixels produced by conv1 at once

// ---------------------------------------------------------------------------
// Float <-> fixed point
// ---------------------------------------------------------------------------

static ap_int<10> encode_input(float value) {      // Input pixel → 8 fractional bits
#pragma HLS INLINE
    ap_fixed<10, 2, AP_RND_CONV, AP_SAT> q = value;
    ap_int<10> bits = q.range();                    // Take the raw bits and use them as an integer
    return bits;
}

static ap_int<10> encode_weight(float value) {     // conv1, conv3 parameters → 9 fractional bits
#pragma HLS INLINE
    ap_fixed<10, 1, AP_RND_CONV, AP_SAT> q = value;
    ap_int<10> bits = q.range();
    return bits;
}

static ap_int<8> encode_weight2(float value) {     // conv2 parameters → 8 bits wide, 7 fractional bits
#pragma HLS INLINE
    ap_fixed<8, 1, AP_RND_CONV, AP_SAT> q = value;
    ap_int<8> bits = q.range();
    return bits;
}

// Returns the float equal to value / 256.
// Skips the int-to-float IP: finds the highest set bit and assembles the float bits directly, so the result is exact.
static float decode(ap_int<10> value) {
#pragma HLS INLINE
    const bool negative = value < 0;
    const ap_int<11> signed_value = value;          // One extra bit so that negating -512 does not overflow
    ap_uint<10> magnitude;
    if (negative) magnitude = -signed_value;
    else magnitude = signed_value;
    ap_uint<5> high = 0;                            // Position of the highest set bit
    ieee_high_bit: for (int bit = 0; bit < 10; ++bit) {
#pragma HLS UNROLL
        if (magnitude[bit]) high = bit;
    }
    fp_struct<float> result;
    result.sign = negative;
    result.exp = 0;
    if (magnitude != 0) result.exp = 127 - 8 + high;   // 8 = number of fractional bits
    result.sig = ap_uint<32>(magnitude) << (23 - high);
    return result.to_ieee();
}

// Drops the extra fractional bits: round half to even, then saturate to 10 bits [-512, 511].
// conv1: 17 fractional bits (8+9) → 8 fractional bits, drops 9 bits
static ap_int<10> quantize_conv1(ap_int<23> sum) {
#pragma HLS INLINE
    ap_int<23> base = sum >> 9;
    const ap_int<23> remainder = sum & 511;          // The low 9 bits being dropped
    const int half = 256;
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    if (base < -512) return ap_int<10>(-512);
    if (base > 511) return ap_int<10>(511);
    return ap_int<10>(base);
}

// conv2: 15 fractional bits (8+7) → 7 fractional bits, drops 8 bits; the input is already truncated to 21 bits
static ap_int<10> quantize_conv2(ap_int<21> sum) {
#pragma HLS INLINE
    ap_int<21> base = sum >> 8;
    const ap_int<21> remainder = sum & 255;
    const int half = 128;
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    if (base < -512) return ap_int<10>(-512);
    if (base > 511) return ap_int<10>(511);
    return ap_int<10>(base);
}

// conv3: 16 fractional bits (7+9) → 8 fractional bits, drops 8 bits
static ap_int<10> quantize_conv3(ap_int<23> sum) {
#pragma HLS INLINE
    ap_int<23> base = sum >> 8;
    const ap_int<23> remainder = sum & 255;
    const int half = 128;
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    if (base < -512) return ap_int<10>(-512);
    if (base > 511) return ap_int<10>(511);
    return ap_int<10>(base);
}

static ap_int<10> relu1(ap_int<23> sum) {
#pragma HLS INLINE
    return sum > 0 ? quantize_conv1(sum) : ap_int<10>(0);
}

// Shift the bias (9 fractional bits) left to align it with the accumulator's fractional bits
static ap_int<23> bias1(ap_int<10> value) {         // → 17 fractional bits, used by conv1
#pragma HLS INLINE
    return ap_int<23>(value) * 256;
}
static ap_int<23> bias3(ap_int<10> value) {         // → 16 fractional bits, used by conv3
#pragma HLS INLINE
    return ap_int<23>(value) * 128;
}

// ---------------------------------------------------------------------------
// Adder tree: each level adds adjacent pairs, halving the count; each level's adds are
// implemented in LUTs and registered (latency=1)
// ---------------------------------------------------------------------------

static ap_int<23> add_tree_64(ap_int<23> x[64]) {   // 64→32→16→8→4→2→1, 6 levels
#pragma HLS INLINE
    for (int level = 0; level < 6; ++level) {
#pragma HLS UNROLL
        const int n = 32 >> level;                   // Number of adds at this level
        for (int i = 0; i < 32; ++i) {
#pragma HLS UNROLL
            if (i < n) {
                ap_int<23> value = x[2*i] + x[2*i+1];
#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1
                x[i] = value;
            }
        }
    }
    return x[0];
}

static ap_int<23> add_tree_256(ap_int<23> x[256]) { // 256→128→…→1, 8 levels
#pragma HLS INLINE
    for (int level = 0; level < 8; ++level) {
#pragma HLS UNROLL
        const int n = 128 >> level;
        for (int i = 0; i < 128; ++i) {
#pragma HLS UNROLL
            if (i < n) {
                ap_int<23> value = x[2*i] + x[2*i+1];
#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1
                x[i] = value;
            }
        }
    }
    return x[0];
}

// ---------------------------------------------------------------------------
// Winograd F(2x2, 3x3): 4x4 input block × 3x3 kernel → 2x2 output, 16 multiplies instead of 36.
// All adds and subtracts in the transforms are forced into LUTs (fabric) so HLS cannot place them in DSPs.
// ---------------------------------------------------------------------------

static ap_int<12> add12(ap_int<12> a, ap_int<12> b) {
#pragma HLS INLINE
    ap_int<12> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
static ap_int<12> sub12(ap_int<12> a, ap_int<12> b) {
#pragma HLS INLINE
    ap_int<12> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}
static ap_int<14> add14(ap_int<14> a, ap_int<14> b) {
#pragma HLS INLINE
    ap_int<14> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
static ap_int<14> sub14(ap_int<14> a, ap_int<14> b) {
#pragma HLS INLINE
    ap_int<14> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}
static ap_int<34> add34(ap_int<34> a, ap_int<34> b) {
#pragma HLS INLINE
    ap_int<34> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
static ap_int<34> sub34(ap_int<34> a, ap_int<34> b) {
#pragma HLS INLINE
    ap_int<34> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}

// Input transform B^T d B: 4x4 input (10 bits) → 4x4 (12 bits)
static void input_transform(const ap_int<10> data[16], ap_int<12> value[16]) {
#pragma HLS INLINE
    ap_int<12> temp[16];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
        temp[c]    = sub12(data[c],   data[8+c]);
        temp[4+c]  = add12(data[4+c], data[8+c]);
        temp[8+c]  = sub12(data[8+c], data[4+c]);
        temp[12+c] = sub12(data[4+c], data[12+c]);
    }
    for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
        value[4*r]   = sub12(temp[4*r],   temp[4*r+2]);
        value[4*r+1] = add12(temp[4*r+1], temp[4*r+2]);
        value[4*r+2] = sub12(temp[4*r+2], temp[4*r+1]);
        value[4*r+3] = sub12(temp[4*r+1], temp[4*r+3]);
    }
}

// Weight transform G g G^T: 3x3 kernel (10 bits) → 4x4 (14 bits).
// The standard G contains 1/2. Here G is multiplied by 2 to make it integer; since it is applied on
// both sides, the result is scaled by 4, and wino_engine shifts right by 2 at the end to undo it.
static void weight_transform(const ap_int<10> kernel[9], ap_int<14> value[16]) {
#pragma HLS INLINE
    ap_int<14> temp[12];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 3; ++c) {
#pragma HLS UNROLL
        temp[c]   = ap_int<14>(kernel[c]) * 2;
        temp[3+c] = add14(add14(kernel[c], kernel[3+c]), kernel[6+c]);
        temp[6+c] = add14(sub14(kernel[c], kernel[3+c]), kernel[6+c]);
        temp[9+c] = ap_int<14>(kernel[6+c]) * 2;
    }
    for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
        value[4*r]   = temp[3*r] * 2;
        value[4*r+1] = add14(add14(temp[3*r], temp[3*r+1]), temp[3*r+2]);
        value[4*r+2] = add14(sub14(temp[3*r], temp[3*r+1]), temp[3*r+2]);
        value[4*r+3] = temp[3*r+2] * 2;
    }
}

// Output transform A^T m A: 4x4 (34 bits) → 2x2 output
static void output_transform(const ap_int<34> value[16], ap_int<34> output[4]) {
#pragma HLS INLINE
    ap_int<34> temp[8];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
        temp[c]   = add34(add34(value[c], value[4+c]), value[8+c]);
        temp[4+c] = sub34(sub34(value[4+c], value[8+c]), value[12+c]);
    }
    for (int r = 0; r < 2; ++r) {
#pragma HLS UNROLL
        output[2*r]   = add34(add34(temp[4*r], temp[4*r+1]), temp[4*r+2]);
        output[2*r+1] = sub34(sub34(temp[4*r+1], temp[4*r+2]), temp[4*r+3]);
    }
}

// ---------------------------------------------------------------------------
// Input image: 255 x 255 float → fixed-point pixel stream
// ---------------------------------------------------------------------------

static void read_input(float in[1][255][255], hls::stream<ap_int<10> > &stream) {
    read_pixels: for (int i = 0; i < 255 * 255; ++i) {
#pragma HLS PIPELINE II=1
        stream.write(encode_input(in[0][i / 255][i % 255]));
    }
}

// ---------------------------------------------------------------------------
// Edge-replication padding (streaming: reads and writes on the fly, buffers only one row)
// ---------------------------------------------------------------------------

// Before conv1: pad 4 pixels on every side, plus 1 extra on the right and bottom → 264 x 264.
// The extra row and column make the 2x2 output blocks tile exactly: (264 - 10) / 2 + 1 = 128 blocks.
static void online_pad1(hls::stream<ap_int<10> > &in, hls::stream<ap_int<10> > &out) {
    ap_int<10> row[255];                             // Most recent row, used at the end to pad the bottom
#pragma HLS AGGREGATE variable=row compact=bit
#pragma HLS BIND_STORAGE variable=row type=ram_2p impl=bram
    online_first_read: for (int x = 0; x < 255; ++x) {
#pragma HLS PIPELINE II=1
        row[x] = in.read();
    }
    online_first_repeats: for (int y = 0; y <= 4; ++y)   // 4 top padding rows + row 0
        online_first_write: for (int x = 0; x < 264; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 4 ? 0 : x >= 259 ? 254 : x - 4;
            out.write(row[sx]);
        }
    online_rows: for (int y = 1; y < 255; ++y) {         // Rows 1..254
        ap_int<10> value;
        online_columns: for (int x = 0; x < 264; ++x) {
#pragma HLS PIPELINE II=1
            // x=0 reads column 0; x=1..4 repeat it (left pad); x=5..258 read columns 1..254; x>=259 repeat the last column (right pad)
            if (x == 0 || (x > 4 && x < 259)) {
                value = in.read();
                row[x == 0 ? 0 : x - 4] = value;
            }
            out.write(value);
        }
    }
    online_bottom_repeats: for (int y = 0; y < 5; ++y)   // 4 bottom padding rows + 1 extra row
        online_bottom_write: for (int x = 0; x < 264; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 4 ? 0 : x >= 259 ? 254 : x - 4;
            out.write(row[sx]);
        }
}

// Before conv3: pad 2 pixels on every side → 259 x 259, 32 channels per pixel
static void online_pad3(hls::stream<pixel2> &in, hls::stream<pixel2> &out) {
    pixel2 row[255];
#pragma HLS AGGREGATE variable=row compact=bit
#pragma HLS BIND_STORAGE variable=row type=ram_2p impl=bram
    online_first_read: for (int x = 0; x < 255; ++x) {
#pragma HLS PIPELINE II=1
        row[x] = in.read();
    }
    online_first_repeats: for (int y = 0; y <= 2; ++y)   // 2 top padding rows + row 0
        online_first_write: for (int x = 0; x < 259; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 2 ? 0 : x >= 257 ? 254 : x - 2;
            out.write(row[sx]);
        }
    online_rows: for (int y = 1; y < 255; ++y) {
        pixel2 value;
        online_columns: for (int x = 0; x < 259; ++x) {
#pragma HLS PIPELINE II=1
            if (x == 0 || (x > 2 && x < 257)) {
                value = in.read();
                row[x == 0 ? 0 : x - 2] = value;
            }
            out.write(value);
        }
    }
    online_bottom_repeats: for (int y = 0; y < 2; ++y)   // 2 bottom padding rows
        online_bottom_write: for (int x = 0; x < 259; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 2 ? 0 : x >= 257 ? 254 : x - 2;
            out.write(row[sx]);
        }
}

// ---------------------------------------------------------------------------
// Parameters: read floats from DDR, convert to fixed point, split into three streams by layer
// ---------------------------------------------------------------------------

// 8129 parameters in total, read in this order:
//   [0, 5184)     conv1 weights 64 × 81
//   [5184, 5248)  conv1 biases 64
//   [5248, 7296)  conv2 weights 32 × 64 (encoded as 8 bits)
//   [7296, 7328)  conv2 biases 32 (encoded as 8 bits)
//   [7328, 8128)  conv3 weights 32 × 25
//   [8128, 8129)  conv3 bias 1
static void read_raw_params(float weights1[64][1][9][9], float biases1[64],
                            float weights2[32][64][1][1], float biases2[32],
                            float weights3[1][32][5][5], float biases3[1],
                            hls::stream<ap_int<10> > &raw1, hls::stream<ap_int<10> > &params2,
                            hls::stream<ap_int<10> > &params3) {
    int oc1 = 0, ky1 = 0, kx1 = 0;                   // Counters replace division for index computation
    int ic3 = 0, ky3 = 0, kx3 = 0;
    read_all_params: for (int i = 0; i < 8129; ++i) {
#pragma HLS PIPELINE II=1
        float value;
        if (i < 5184) {
            value = weights1[oc1][0][ky1][kx1];
            if (kx1 == 8) {
                kx1 = 0;
                if (ky1 == 8) { ky1 = 0; ++oc1; }
                else ++ky1;
            } else ++kx1;
        } else if (i < 5248) value = biases1[i - 5184];
        else if (i < 7296) value = weights2[(i - 5248) / 64][(i - 5248) % 64][0][0];
        else if (i < 7328) value = biases2[i - 7296];
        else if (i < 8128) {
            value = weights3[0][ic3][ky3][kx3];
            if (kx3 == 4) {
                kx3 = 0;
                if (ky3 == 4) { ky3 = 0; ++ic3; }
                else ++ky3;
            } else ++kx3;
        } else value = biases3[0];
        // conv2 parameters are 8 bits: sign-extend to 10 bits to share the same stream type, then truncate back to 8 bits inside conv2
        const ap_int<10> encoded = i >= 5248 && i < 7328 ? ap_int<10>(encode_weight2(value))
                                                         : encode_weight(value);
        if (i < 5248) raw1.write(encoded);
        else if (i < 7328) params2.write(encoded);
        else params3.write(encoded);
    }
}

// Splits conv1's 9x9 kernel into 3x3 sub-kernels of size 3x3 (groups) and applies the Winograd weight transform to each.
// Output: transform results for 64 channels × 9 sub-kernels, followed by 64 biases (stored in packet.v[0]).
static void transform_params1(hls::stream<ap_int<10> > &raw1, hls::stream<transformed_params1> &params1) {
    ap_int<10> raw[9][9];                            // [sub-kernel index][position within sub-kernel]
#pragma HLS ARRAY_PARTITION variable=raw complete dim=0
    transform_channels: for (int oc = 0; oc < 64; ++oc) {
        transform_read_rows: for (int row = 0; row < 9; ++row)
            transform_read_columns: for (int column = 0; column < 9; ++column) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
                const int group = (row / 3) * 3 + column / 3;
                const int tap = (row % 3) * 3 + column % 3;
                raw[group][tap] = raw1.read();
            }
        transform_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS PIPELINE II=1
            ap_int<10> kernel[9];
            transformed_params1 packet;
#pragma HLS ARRAY_PARTITION variable=kernel complete
#pragma HLS ARRAY_PARTITION variable=packet.v complete
            for (int tap = 0; tap < 9; ++tap) {
#pragma HLS UNROLL
                kernel[tap] = raw[group][tap];
            }
            weight_transform(kernel, packet.v);
            params1.write(packet);
        }
    }
    transform_bias: for (int oc = 0; oc < 64; ++oc) {
#pragma HLS PIPELINE II=1
        transformed_params1 packet;
        for (int field = 0; field < 16; ++field) {
#pragma HLS UNROLL
            packet.v[field] = 0;
        }
        packet.v[0] = raw1.read();
        params1.write(packet);
    }
}

static void read_params(float weights1[64][1][9][9], float biases1[64],
                        float weights2[32][64][1][1], float biases2[32],
                        float weights3[1][32][5][5], float biases3[1],
                        hls::stream<transformed_params1> &params1,
                        hls::stream<ap_int<10> > &params2, hls::stream<ap_int<10> > &params3) {
#pragma HLS DATAFLOW
    hls::stream<ap_int<10> > raw1("raw_conv1_params");
#pragma HLS STREAM variable=raw1 depth=16
#pragma HLS BIND_STORAGE variable=raw1 type=fifo impl=lutram
    read_raw_params(weights1, biases1, weights2, biases2, weights3, biases3, raw1, params2, params3);
    transform_params1(raw1, params1);
}

// ---------------------------------------------------------------------------
// conv1: 9x9 convolution, 1 → 64 channels, Winograd
// ---------------------------------------------------------------------------

// Slides a 10x10 window over the 264 x 264 padded image using a 9-row line buffer, stepping 2 in both directions.
// Each 10x10 window maps to 2x2 output pixels; it is split into 3x3 overlapping 4x4 sub-blocks (start points 3 apart),
// and each sub-block goes through the input transform. 128 x 128 windows in total.
static void wino_windows(hls::stream<ap_int<10> > &in, hls::stream<transformed_window> &out) {
    static ap_int<10> line[9][264], window[10][10];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    wino_make_windows: for (int p = 0; p < 264 * 264; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p / 264, x = p % 264;
        ap_int<10> column[10];                       // The 10 pixels of the current column, top to bottom
#pragma HLS ARRAY_PARTITION variable=column complete
        for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
            column[r] = line[r][x];
        }
        column[9] = in.read();
        for (int r = 0; r < 9; ++r) {                // Shift the whole line buffer up by one row
#pragma HLS UNROLL
            line[r][x] = column[r+1];
        }
        for (int r = 0; r < 10; ++r) {               // Shift the window left by one column, new column goes on the right
#pragma HLS UNROLL
            for (int c = 0; c < 9; ++c) {
#pragma HLS UNROLL
                window[r][c] = window[r][c+1];
            }
            window[r][9] = column[r];
        }
        if (y >= 9 && x >= 9 && (y - 9) % 2 == 0 && (x - 9) % 2 == 0) {
            transformed_window result;
#pragma HLS ARRAY_PARTITION variable=result.v complete dim=0
            for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
                ap_int<10> data[16];
#pragma HLS ARRAY_PARTITION variable=data complete
                for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                    data[j] = window[group / 3 * 3 + j / 4][group % 3 * 3 + j % 4];
                }
                input_transform(data, result.v[group]);
            }
            out.write(result);
        }
    }
}

// 16 cycles per window: each cycle computes 4 output channels (4 lanes), so 16 cycles cover all 64 channels.
// Each lane does 9 sub-blocks × 16 = 144 multiplies per cycle; 4 lanes use 576 DSP multipliers in total.
static void wino_engine(hls::stream<transformed_window> &in, hls::stream<tile_block> &out,
                        hls::stream<transformed_params1> &params) {
    static ap_int<14> weights[64][9][16];            // [output channel][sub-kernel][transformed position]
    static ap_int<10> biases[64];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete dim=3
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    wino_local_load_channels: for (int oc = 0; oc < 64; ++oc)
        wino_local_load_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const transformed_params1 packet = params.read();
            for (int tap = 0; tap < 16; ++tap) {
#pragma HLS UNROLL
                weights[oc][group][tap] = packet.v[tap];
            }
        }
    wino_local_load_bias: for (int oc = 0; oc < 64; ++oc) {   // Load biases through a shift register
#pragma HLS PIPELINE II=1
        const transformed_params1 packet = params.read();
        for (int c = 0; c < 63; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[63] = ap_int<10>(packet.v[0]);
    }
    transformed_window value;
    tile_block tile;
#pragma HLS ARRAY_PARTITION variable=value.v complete dim=0
#pragma HLS ARRAY_PARTITION variable=tile.pixel complete dim=0
    continuous_wino_fold: for (int iteration = 0; iteration < 128 * 128 * 16; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration % 16;
        if (step == 0) value = in.read();            // Read a new window every 16 cycles
        ap_int<10> next[4][4];                        // [which pixel of the 2x2][lane]
#pragma HLS ARRAY_PARTITION variable=next complete dim=0
        for (int lane = 0; lane < 4; ++lane) {
#pragma HLS UNROLL
            const int oc = step * 4 + lane;
            ap_int<34> m[16], result[4];
#pragma HLS ARRAY_PARTITION variable=m complete
#pragma HLS ARRAY_PARTITION variable=result complete
            for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                ap_int<34> sum = 0;                  // The 9 sub-blocks are summed directly in the transform domain
                for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
                    ap_int<26> product = value.v[group][j] * weights[oc][group][j];   // 12 bits × 14 bits
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                    sum = add34(sum, product);
                }
                m[j] = sum;
            }
            output_transform(m, result);
            for (int j = 0; j < 4; ++j) {
#pragma HLS UNROLL
                // The weight transform scaled everything by 4, so result is always a multiple of 4; shift right by 2 to restore it
                next[j][lane] = relu1(ap_int<23>(result[j] >> 2) + bias1(biases[oc]));
            }
        }
        // The 64 channels in tile act as a shift register: shift left by 4 every cycle and append the 4 new channels
        // at the end; after 16 cycles they are in order 0..63
        for (int j = 0; j < 4; ++j) {
#pragma HLS UNROLL
            for (int c = 0; c < 60; ++c) {
#pragma HLS UNROLL
                tile.pixel[j].v[c] = tile.pixel[j].v[c+4];
            }
            for (int lane = 0; lane < 4; ++lane) {
#pragma HLS UNROLL
                tile.pixel[j].v[60 + lane] = next[j][lane];
            }
        }
        if (step == 15) out.write(tile);
    }
}

// 2x2 output block → split into upper and lower rows: the top two pixels go to top, the bottom two go to bottom.
// Row 255 and column 255 come from the extra padding and are discarded.
static void distribute_tiles(hls::stream<tile_block> &in, hls::stream<pixel1> &top,
                             hls::stream<pixel1> &bottom) {
    tile_block value;
#pragma HLS ARRAY_PARTITION variable=value.pixel complete dim=0
    distribute_tile_pixels: for (int p = 0; p < 128 * 128 * 4; ++p) {
#pragma HLS PIPELINE II=1
        const int j = p % 4, tile = p / 4;
        if (j == 0) value = in.read();
        const int y = 2 * (tile / 128) + j / 2;
        const int x = 2 * (tile % 128) + j % 2;
        if (y < 255 && x < 255) {
            if (j < 2) top.write(value.pixel[j]);
            else bottom.write(value.pixel[j]);
        }
    }
}

// Restore raster-scan order: even rows come from top, odd rows from bottom
static void reorder_rows(hls::stream<pixel1> &top, hls::stream<pixel1> &bottom,
                         hls::stream<pixel1> &out) {
    raster_rows: for (int y = 0; y < 255; ++y)
        raster_columns: for (int x = 0; x < 255; ++x) {
#pragma HLS PIPELINE II=1
            out.write(y % 2 ? bottom.read() : top.read());
        }
}

static void conv1_stream(hls::stream<ap_int<10> > &in, hls::stream<pixel1> &out,
                         hls::stream<transformed_params1> &params) {
#pragma HLS DATAFLOW
    hls::stream<transformed_window> windows("wino_windows");
    hls::stream<tile_block> tiles("wino_tile_blocks");
    hls::stream<pixel1> top("wino_top_rows"), bottom("wino_bottom_rows");
#pragma HLS STREAM variable=windows depth=32
#pragma HLS STREAM variable=tiles depth=2
#pragma HLS BIND_STORAGE variable=windows type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=tiles type=fifo impl=lutram
#pragma HLS STREAM variable=top depth=512
#pragma HLS STREAM variable=bottom depth=512
    wino_windows(in, windows);
    wino_engine(windows, tiles, params);
    distribute_tiles(tiles, top, bottom);
    reorder_rows(top, bottom, out);
}

// ---------------------------------------------------------------------------
// conv2: 1x1 convolution, 64 → 32 channels
// ---------------------------------------------------------------------------

// One DSP multiply computes two output channels at once by packing two 8-bit weights into one 27-bit value:
//   packed = first * 2^18 + second
//   packed * x = first*x * 2^18 + second*x
// second*x fits in an 18-bit signed range, so the low 18 bits are second*x and the high bits are first*x
// (when the low 18 bits are negative, the high part has had 1 borrowed from it, which must be added back).
// 4 cycles per pixel: 4 lanes per cycle, each lane computes 2 channels, so 4 cycles cover all 32 channels.
// 4 × 64 = 256 DSP multiplies per cycle.
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         hls::stream<ap_int<10> > &params) {
    static ap_int<27> packed_weights[16][64];        // [channel pair][input channel]
    static ap_int<8> biases[32];
    ap_int<8> first_row[64];
#pragma HLS ARRAY_PARTITION variable=packed_weights cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=packed_weights complete dim=2
#pragma HLS BIND_STORAGE variable=packed_weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=first_row complete
#pragma HLS ARRAY_PARTITION variable=biases complete
    packed_load_pairs: for (int pair = 0; pair < 16; ++pair) {
        packed_load_first: for (int ic = 0; ic < 64; ++ic) {     // Weights of channel 2*pair
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            first_row[ic] = ap_int<8>(params.read());
        }
        packed_load_second: for (int ic = 0; ic < 64; ++ic) {    // Weights of channel 2*pair+1
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const ap_int<8> second = ap_int<8>(params.read());
            packed_weights[pair][ic] = ap_int<27>(first_row[ic]) * 262144 + ap_int<27>(second);   // 262144 = 2^18
        }
    }
    packed_load_bias: for (int i = 0; i < 32; ++i) {
#pragma HLS PIPELINE II=1
        for (int c = 0; c < 31; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[31] = ap_int<8>(params.read());
    }
    pixel1 value;
    pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    continuous_c2_fold: for (int iteration = 0; iteration < 255 * 255 * 4; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration % 4;
        if (step == 0) value = in.read();            // Read a new pixel every 4 cycles
        ap_int<10> next[8];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < 4; ++lane) {
#pragma HLS UNROLL
            const int pair = step * 4 + lane, oc = 2 * pair;
            ap_int<23> first[64], second[64];
#pragma HLS ARRAY_PARTITION variable=first complete
#pragma HLS ARRAY_PARTITION variable=second complete
            for (int ic = 0; ic < 64; ++ic) {
#pragma HLS UNROLL
                ap_int<37> product = packed_weights[pair][ic] * value.v[ic];     // 27 bits × 10 bits
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                const int bits = int(product & 262143);                 // Low 18 bits
                const int low = bits >= 131072 ? bits - 262144 : bits;  // Interpreted as an 18-bit signed number
                first[ic] = ap_int<23>(product >> 18) + (low < 0 ? 1 : 0);
                second[ic] = low;
            }
            // Bias has 7 fractional bits; multiply by 256 to align with the product's 15 fractional bits
            const ap_int<23> sum0 = add_tree_64(first) + ap_int<23>(biases[oc]) * 256;
            const ap_int<23> sum1 = add_tree_64(second) + ap_int<23>(biases[oc+1]) * 256;
            // Truncate to 21 bits: the original C simulation uses an assert to check that the test data
            // stays within the 21-bit signed range (this depends on the weights)
            const ap_int<21> s0 = sum0, s1 = sum1;
            next[2*lane]   = s0 > 0 ? quantize_conv2(s0) : ap_int<10>(0);   // ReLU
            next[2*lane+1] = s1 > 0 ? quantize_conv2(s1) : ap_int<10>(0);
        }
        // The 32 channels act as a shift register: shift left by 8 every cycle; after 4 cycles they are in order 0..31
        for (int c = 0; c < 24; ++c) {
#pragma HLS UNROLL
            result.v[c] = result.v[c+8];
        }
        for (int c = 0; c < 8; ++c) {
#pragma HLS UNROLL
            result.v[24 + c] = next[c];
        }
        if (step == 3) out.write(result);
    }
}

static void conv12(hls::stream<ap_int<10> > &in, hls::stream<pixel2> &out,
                   hls::stream<transformed_params1> &params1, hls::stream<ap_int<10> > &params2) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> features("conv1_features");
#pragma HLS STREAM variable=features depth=4
#pragma HLS BIND_STORAGE variable=features type=fifo impl=lutram
    conv1_stream(in, features, params1);
    conv2_stream(features, out, params2);
}

// ---------------------------------------------------------------------------
// conv3: 5x5 convolution, 32 → 1 channel
// ---------------------------------------------------------------------------

// Slides a 5x5 window over the 259 x 259 padded image using a 4-row line buffer, producing one window per position.
// The window is too wide, so it is split by channel into two halves: 0..15 go to out0, 16..31 go to out1.
static void windows3(hls::stream<pixel2> &in, hls::stream<window3> &out0, hls::stream<window3> &out1) {
    static ap_int<10> line[4][259][32], window[5][5][32];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS ARRAY_RESHAPE variable=line complete dim=3
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    make_windows3: for (int p = 0; p < 259 * 259; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p / 259, x = p % 259;
        const pixel2 value = in.read();
        window3 result0, result1;
#pragma HLS ARRAY_PARTITION variable=result0.v complete
#pragma HLS ARRAY_PARTITION variable=result1.v complete
        for (int ic = 0; ic < 32; ++ic) {
#pragma HLS UNROLL
            ap_int<10> column[5];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
                column[r] = line[r][x][ic];
            }
            column[4] = value.v[ic];
            for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
                line[r][x][ic] = column[r+1];
            }
            for (int r = 0; r < 5; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                    window[r][c][ic] = window[r][c+1][ic];
                }
                window[r][4][ic] = column[r];
                for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                    if (ic < 16) result0.v[(r * 5 + c) * 16 + ic] = window[r][c][ic];
                    else result1.v[(r * 5 + c) * 16 + ic - 16] = window[r][c][ic];
                }
            }
        }
        if (y >= 4 && x >= 4) {
            out0.write(result0);
            out1.write(result1);
        }
    }
}

// 4 cycles per output pixel: each cycle computes 8 input channels × 25 = 200 multiplies (200 DSPs),
// zero-padded to 256 and fed through the adder tree, then accumulated into sum.
static void engine3(hls::stream<window3> &in0, hls::stream<window3> &in1, hls::stream<ap_int<10> > &out,
                    hls::stream<ap_int<10> > &params) {
    static ap_int<10> weights[32][25];               // [input channel][5x5 position]
    static ap_int<10> biases[1];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=8 dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=25 dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
    local_load_channels: for (int oc = 0; oc < 32; ++oc)
        local_load_taps: for (int tap = 0; tap < 25; ++tap) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            weights[oc][tap] = params.read();
        }
    local_load_bias: for (int i = 0; i < 1; ++i) {   // Only 1 bias; the loop is kept to match the original load_local
#pragma HLS PIPELINE II=1
        biases[0] = params.read();
    }
    window3 value0, value1;
    ap_int<23> sum = 0;
#pragma HLS ARRAY_PARTITION variable=value0.v complete
#pragma HLS ARRAY_PARTITION variable=value1.v complete
    continuous_c3_fold: for (int iteration = 0; iteration < 255 * 255 * 4; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration % 4;
        if (step == 0) { value0 = in0.read(); value1 = in1.read(); }
        ap_int<23> products[256];
#pragma HLS ARRAY_PARTITION variable=products complete
        for (int index = 0; index < 256; ++index) {
#pragma HLS UNROLL
            if (index < 200) {
                const int ic = step * 8 + index / 25, tap = index % 25;
                ap_int<20> product = (ic < 16 ? value0.v[tap * 16 + ic] : value1.v[tap * 16 + ic - 16]) * weights[ic][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                products[index] = product;
            } else products[index] = 0;
        }
        const ap_int<23> partial = add_tree_256(products);
        // Cycle 0 starts from the bias; later cycles accumulate onto the previous cycle's sum
        ap_int<23> next = (step == 0 ? bias3(biases[0]) : sum) + partial;
#pragma HLS BIND_OP variable=next op=add impl=fabric latency=1
        sum = next;
        if (step == 3) out.write(quantize_conv3(next));   // No ReLU
    }
}

static void conv3_stream(hls::stream<pixel2> &in, hls::stream<ap_int<10> > &out,
                         hls::stream<ap_int<10> > &params) {
#pragma HLS DATAFLOW
    hls::stream<window3> windows0("windows3_low_channels"), windows1("windows3_high_channels");
#pragma HLS STREAM variable=windows0 depth=2
#pragma HLS STREAM variable=windows1 depth=2
#pragma HLS BIND_STORAGE variable=windows0 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=windows1 type=fifo impl=lutram
    windows3(in, windows0, windows1);
    engine3(windows0, windows1, out, params);
}

// ---------------------------------------------------------------------------
// Output and top level
// ---------------------------------------------------------------------------

static void write_output(hls::stream<ap_int<10> > &stream, float out[1][255][255]) {
    write_pixels: for (int i = 0; i < 255 * 255; ++i) {
#pragma HLS PIPELINE II=1
        out[0][i / 255][i % 255] = decode(stream.read());
    }
}

static void dataflow_region(float in[1][255][255], float out[1][255][255],
                            float weights1[64][1][9][9], float biases1[64],
                            float weights2[32][64][1][1], float biases2[32],
                            float weights3[1][32][5][5], float biases3[1]) {
#pragma HLS DATAFLOW
    hls::stream<ap_int<10> > raw("raw"), padded1("padded1");
    hls::stream<pixel2> features2("features2"), padded3("padded3");
    hls::stream<ap_int<10> > result("result");
    hls::stream<transformed_params1> params1("params1");
    hls::stream<ap_int<10> > params2("params2"), params3("params3");
#pragma HLS AGGREGATE variable=params1 compact=bit
#pragma HLS STREAM variable=params1 depth=4
#pragma HLS STREAM variable=params2 depth=16
#pragma HLS STREAM variable=params3 depth=16
#pragma HLS BIND_STORAGE variable=params1 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=params2 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=params3 type=fifo impl=lutram
#pragma HLS STREAM variable=raw depth=512
#pragma HLS STREAM variable=padded1 depth=16
#pragma HLS STREAM variable=features2 depth=4
#pragma HLS BIND_STORAGE variable=features2 type=fifo impl=lutram
#pragma HLS STREAM variable=padded3 depth=16
#pragma HLS BIND_STORAGE variable=padded3 type=fifo impl=lutram
#pragma HLS STREAM variable=result depth=16
    read_input(in, raw);
    read_params(weights1, biases1, weights2, biases2, weights3, biases3, params1, params2, params3);
    online_pad1(raw, padded1);
    conv12(padded1, features2, params1, params2);
    online_pad3(features2, padded3);
    conv3_stream(padded3, result, params3);
    write_output(result, out);
}

void srcnn(float in[1][255][255], float weights1[64][1][9][9], float biases1[64],
           float weights2[32][64][1][1], float biases2[32],
           float weights3[1][32][5][5], float biases3[1], float out[1][255][255]) {
#pragma HLS INTERFACE mode=m_axi port=in offset=slave bundle=image_in depth=65025 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=out offset=slave bundle=image_out depth=65025 max_write_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=weights1 offset=slave bundle=parameters depth=5184 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases1 offset=slave bundle=parameters depth=64
#pragma HLS INTERFACE mode=m_axi port=weights2 offset=slave bundle=parameters depth=2048 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases2 offset=slave bundle=parameters depth=32
#pragma HLS INTERFACE mode=m_axi port=weights3 offset=slave bundle=parameters depth=800 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases3 offset=slave bundle=parameters depth=1
#pragma HLS INTERFACE mode=s_axilite port=in bundle=control
#pragma HLS INTERFACE mode=s_axilite port=out bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights1 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases1 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights2 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases2 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights3 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases3 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return bundle=control
    dataflow_region(in, out, weights1, biases1, weights2, biases2, weights3, biases3);
}
