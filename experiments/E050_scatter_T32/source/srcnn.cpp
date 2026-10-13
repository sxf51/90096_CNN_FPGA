#include "types.h"
#include "srcnn.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif
using namespace numeric;

static void read_input(ftmap_t in[N0][H][W], hls::stream<input> &stream) {
    read_pixels: for (int i = 0; i < H * W; ++i) {
#pragma HLS PIPELINE II=1
        stream.write(input(in[0][i / W][i % W]));
    }
}

template<class Pixel, int Radius>
static void replicate_pad(hls::stream<Pixel> &in, hls::stream<Pixel> &out) {
    Pixel row[W];
    int previous = -1;
    pad_rows: for (int y = 0; y < H + 2 * Radius; ++y) {
        const int sy = y < Radius ? 0 : (y >= H + Radius ? H - 1 : y - Radius);
        if (sy != previous) {
            pad_read_row: for (int x = 0; x < W; ++x) {
#pragma HLS PIPELINE II=1
                row[x] = in.read();
            }
            previous = sy;
        }
        pad_write_row: for (int x = 0; x < W + 2 * Radius; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : (x >= W + Radius ? W - 1 : x - Radius);
            out.write(row[sx]);
        }
    }
}

static void conv1_stream(hls::stream<input> &in, hls::stream<pixel1> &out,
                         weight weights[N1][81], bias biases[N1]) {
    constexpr int PW = W + 8;
    static input line[8][PW];
    static input window[9][9];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    c1_rows: for (int y = 0; y < H + 8; ++y)
        c1_columns: for (int x = 0; x < PW; ++x) {
            input column[9];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int r = 0; r < 8; ++r) {
#pragma HLS UNROLL
                column[r] = line[r][x];
            }
            column[8] = in.read();
            for (int r = 0; r < 8; ++r) {
#pragma HLS UNROLL
                line[r][x] = column[r + 1];
            }
            for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 8; ++c) {
#pragma HLS UNROLL
                    window[r][c] = window[r][c + 1];
                }
                window[r][8] = column[r];
            }
            if (y >= 8 && x >= 8) {
                pixel1 result;
#pragma HLS ARRAY_PARTITION variable=result.v complete
#if EXP_C1_SPLIT
                acc1 sums[N1];
#pragma HLS ARRAY_PARTITION variable=sums complete
                for (int oc = 0; oc < N1; ++oc) {
#pragma HLS UNROLL
                    sums[oc] = biases[oc];
                }
                c1_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                    for (int oc = 0; oc < N1; ++oc) {
#pragma HLS UNROLL
                        for (int j = 0; j < C1_TAP; ++j) {
#pragma HLS UNROLL
                            const int tap = step * C1_TAP + j;
                            if (tap < 81) sums[oc] += window[tap / 9][tap % 9] * weights[oc][tap];
                        }
                    }
                }
                for (int oc = 0; oc < N1; ++oc) {
#pragma HLS UNROLL
                    result.v[oc] = sums[oc] > 0 ? act1(sums[oc]) : act1(0);
                }
#else
                c1_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < C1_OC; ++lane) {
#pragma HLS UNROLL
                        const int oc = step * C1_OC + lane;
                        acc1 sum = biases[oc];
                        for (int tap = 0; tap < 81; ++tap) {
#pragma HLS UNROLL
                            sum += window[tap / 9][tap % 9] * weights[oc][tap];
                        }
                        result.v[oc] = sum > 0 ? act1(sum) : act1(0);
                    }
                }
#endif
                out.write(result);
            }
        }
}

static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         weight weights[N2][N1], bias biases[N2]) {
    c2_pixels: for (int p = 0; p < H * W; ++p) {
        const pixel1 value = in.read();
        pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
#if EXP_C2_SPLIT
        acc2 sums[N2];
#pragma HLS ARRAY_PARTITION variable=sums complete
        for (int oc = 0; oc < N2; ++oc) {
#pragma HLS UNROLL
            sums[oc] = biases[oc];
        }
        c2_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
            for (int oc = 0; oc < N2; ++oc) {
#pragma HLS UNROLL
                for (int lane = 0; lane < C2_IC; ++lane) {
#pragma HLS UNROLL
                    const int ic = step * C2_IC + lane;
                    sums[oc] += value.v[ic] * weights[oc][ic];
                }
            }
        }
        for (int oc = 0; oc < N2; ++oc) {
#pragma HLS UNROLL
            result.v[oc] = sums[oc] > 0 ? act2(sums[oc]) : act2(0);
        }
#else
        c2_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
            for (int lane = 0; lane < C2_OC; ++lane) {
#pragma HLS UNROLL
                const int oc = step * C2_OC + lane;
                acc2 sum = biases[oc];
                for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
                    sum += value.v[ic] * weights[oc][ic];
                }
                result.v[oc] = sum > 0 ? act2(sum) : act2(0);
            }
        }
#endif
        out.write(result);
    }
}

static void conv12(hls::stream<input> &in, hls::stream<pixel2> &out,
                   weight w1[N1][81], bias b1[N1], weight w2[N2][N1], bias b2[N2]) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> features("conv1_features");
#pragma HLS STREAM variable=features depth=4
    conv1_stream(in, features, w1, b1);
    conv2_stream(features, out, w2, b2);
}

static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         weight weights[N2][25], bias biases[N3]) {
#if EXP_FIXED
    static_assert(EXP_W_BITS + EXP_A_BITS + 3 <= 32, "32-bit scatter cache must preserve reference accumulator precision");
    using partial = ap_fixed<32, 32 - (EXP_W_BITS + EXP_A_BITS - 4), AP_TRN, AP_WRAP>;
#else
    using partial = float;
#endif
    static partial buffer[5][W];
    partial window[5][5];
#pragma HLS ARRAY_PARTITION variable=buffer complete dim=1
#pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    constexpr int LANES = N2 / T;
    scatter_rows: for (int y = 0; y < H + 4; ++y) {
        const int base = (y + 1) % 5;
        for (int r = 0; r < 5; ++r)
            for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                window[r][c] = 0;
            }
        scatter_columns: for (int x = 0; x < W + 4; ++x) {
            const pixel2 value = in.read();
            // Fixed physical banks each get at most one read and one write.
            if (x >= 5 && x - 5 < W)
                for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
                    buffer[bank][x - 5] = window[(bank + 5 - base) % 5][0];
                }
            partial column[5];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
                column[bank] = x < W ? buffer[bank][x] : partial(0);
            }
            for (int r = 0; r < 5; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                    window[r][c] = window[r][c + 1];
                }
                const int output_y = y - 4 + r;
                window[r][4] = (r == 4 || output_y < 0 || output_y >= H) ? partial(0) : column[(base + r) % 5];
            }
            partial contribution[25];
#pragma HLS ARRAY_PARTITION variable=contribution complete
            for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                contribution[tap] = 0;
            }
            c3_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                for (int lane = 0; lane < LANES; ++lane) {
#pragma HLS UNROLL
                    const int ic = step * LANES + lane;
                    for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                        contribution[tap] += value.v[ic] * weights[ic][tap];
                    }
                }
            }
            for (int ky = 0; ky < 5; ++ky) {
#pragma HLS UNROLL
                for (int kx = 0; kx < 5; ++kx) {
#pragma HLS UNROLL
                    if (y >= ky && y - ky < H && x >= kx && x - kx < W)
                        window[4 - ky][4 - kx] += contribution[ky * 5 + kx];
                }
            }
            if (y >= 4 && x >= 4) out.write(output(window[0][0] + biases[0]));
        }
        // Last valid column remains in registers at the end of the padded row.
        for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
            buffer[bank][W - 1] = window[(bank + 5 - base) % 5][0];
        }
    }
}

static void write_output(hls::stream<output> &stream, ftmap_t out[N3][H][W]) {
    write_pixels: for (int i = 0; i < H * W; ++i) {
#pragma HLS PIPELINE II=1
        out[0][i / W][i % W] = static_cast<float>(stream.read());
    }
}

static void dataflow_region(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W],
                            weight w1[N1][81], bias b1[N1], weight w2[N2][N1], bias b2[N2],
                            weight w3[N2][25], bias b3[N3]) {
#pragma HLS DATAFLOW
    hls::stream<input> raw("raw"), padded1("padded1");
    hls::stream<pixel2> features2("features2"), padded3("padded3");
    hls::stream<output> result("result");
#pragma HLS STREAM variable=raw depth=512
#pragma HLS STREAM variable=padded1 depth=16
#pragma HLS STREAM variable=features2 depth=4
#pragma HLS STREAM variable=padded3 depth=16
#pragma HLS STREAM variable=result depth=16
    read_input(in, raw);
    replicate_pad<input, 4>(raw, padded1);
    conv12(padded1, features2, w1, b1, w2, b2);
    replicate_pad<pixel2, 2>(features2, padded3);
    conv3_stream(padded3, result, w3, b3);
    write_output(result, out);
}

void srcnn(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
           param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
           param_t weights3[N3][N2][F3][F3], param_t biases3[N3], ftmap_t out[N3][H][W]) {
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
    static weight w1[N1][81], w2[N2][N1], w3[N2][25];
    static bias b1[N1], b2[N2], b3[N3];
#pragma HLS ARRAY_PARTITION variable=b1 complete
#pragma HLS ARRAY_PARTITION variable=b2 complete
#if EXP_STORAGE == 0
#pragma HLS ARRAY_PARTITION variable=w1 complete dim=0
#pragma HLS ARRAY_PARTITION variable=w2 complete dim=0
#pragma HLS ARRAY_PARTITION variable=w3 complete dim=0
#else
#pragma HLS ARRAY_PARTITION variable=w1 cyclic factor=C1_OC dim=1
#pragma HLS ARRAY_PARTITION variable=w1 cyclic factor=C1_TAP dim=2
#pragma HLS ARRAY_PARTITION variable=w2 cyclic factor=C2_OC dim=1
#pragma HLS ARRAY_PARTITION variable=w2 cyclic factor=C2_IC dim=2
#pragma HLS ARRAY_PARTITION variable=w3 cyclic factor=C3_IC dim=1
#pragma HLS ARRAY_PARTITION variable=w3 cyclic factor=C3_TAP dim=2
#if EXP_STORAGE == 1
#pragma HLS BIND_STORAGE variable=w1 type=ram_2p impl=lutram
#pragma HLS BIND_STORAGE variable=w2 type=ram_2p impl=lutram
#pragma HLS BIND_STORAGE variable=w3 type=ram_2p impl=lutram
#else
#pragma HLS BIND_STORAGE variable=w1 type=ram_2p impl=bram
#pragma HLS BIND_STORAGE variable=w2 type=ram_2p impl=bram
#pragma HLS BIND_STORAGE variable=w3 type=ram_2p impl=bram
#endif
#endif
    load1: for (int i = 0; i < 5184; ++i) {
#pragma HLS PIPELINE II=1
        w1[i / 81][i % 81] = weights1[i / 81][0][(i % 81) / 9][i % 9];
    }
    load2: for (int i = 0; i < 2048; ++i) {
#pragma HLS PIPELINE II=1
        w2[i / N1][i % N1] = weights2[i / N1][i % N1][0][0];
    }
    load3: for (int i = 0; i < 800; ++i) {
#pragma HLS PIPELINE II=1
        w3[i / 25][i % 25] = weights3[0][i / 25][(i % 25) / 5][i % 5];
    }
    for (int i = 0; i < N1; ++i) b1[i] = biases1[i];
    for (int i = 0; i < N2; ++i) b2[i] = biases2[i];
    b3[0] = biases3[0];
    dataflow_region(in, out, w1, b1, w2, b2, w3, b3);
}
