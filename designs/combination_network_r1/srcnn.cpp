#include "types.h"
#include "winograd_math.h"
#include "srcnn.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif
using namespace numeric;

using Packed = word<27>;
using Low8 = word<8>;
using Residual = word<3>;
using Wide = word<48>;

static Low8 low8(weight value) {
#pragma HLS INLINE
#ifdef __SYNTHESIS__
    return Low8(value);
#else
    const int bits = int(value) & 255;
    return bits >= 128 ? bits-256 : bits;
#endif
}

template<class Value>
static acc1 restore(Residual residual, Value value) {
#pragma HLS INLINE
    acc1 result = 0;
    if (residual == 1) result = value;
    else if (residual == -1) result = -acc1(value);
    else if (residual == 2) result = acc1(value)*2;
    else if (residual == -2) result = -acc1(value)*2;
    return result*256;
}

static void pair_weights(weight a, weight b, input c, acc1 &first, acc1 &second) {
#pragma HLS INLINE
    const Low8 la = low8(a), lb = low8(b);
    const Residual ra = (word<11>(a)-word<11>(la)) >> 8;
    const Residual rb = (word<11>(b)-word<11>(lb)) >> 8;
    const Packed packed = Packed(la)*262144+Packed(lb);
#ifdef __SYNTHESIS__
    auto product = packed*c;
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
    const Wide product = Wide(packed)*c;
#endif
    const int bits = int(product & 262143);
    const int low = bits >= 131072 ? bits-262144 : bits;
    const Wide high = (product >> 18)+(low < 0 ? 1 : 0);
    first = acc1(high)+restore(ra,c);
    second = acc1(low)+restore(rb,c);
}

static void pair_pixels(act2 a, act2 b, weight coefficient, acc3 &first, acc3 &second) {
#pragma HLS INLINE
    const Low8 low_weight = low8(coefficient);
    const Residual residual = (word<11>(coefficient)-word<11>(low_weight)) >> 8;
    const Packed packed = Packed(word<11>(a)-256)*262144+Packed(b);
#ifdef __SYNTHESIS__
    auto product = packed*low_weight;
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
    const Wide product = Wide(packed)*low_weight;
#endif
    const int bits = int(product & 262143);
    const int low = bits >= 131072 ? bits-262144 : bits;
    const Wide high = (product >> 18)+(low < 0 ? 1 : 0)+Wide(low_weight)*256;
    first = acc3(high)+restore(residual,a);
    second = acc3(low)+restore(residual,b);
}


static void read_input(ftmap_t in[N0][H][W], hls::stream<input> &stream) {
    read_pixels: for (int i = 0; i < H * W; ++i) {
#pragma HLS PIPELINE II=1
        stream.write(encode_input(in[0][i / W][i % W]));
    }
}

template<class Pixel, int Radius>
static void replicate_pad(hls::stream<Pixel> &in, hls::stream<Pixel> &out) {
    Pixel row[W];
    int previous = -1;
    pad_rows: for (int y = 0; y < H + 2 * Radius + (Radius == 4 ? 1 : 0); ++y) {
        const int sy = y < Radius ? 0 : (y >= H + Radius ? H - 1 : y - Radius);
        if (sy != previous) {
            pad_read_row: for (int x = 0; x < W; ++x) {
#pragma HLS PIPELINE II=1
                row[x] = in.read();
            }
            previous = sy;
        }
        pad_write_row: for (int x = 0; x < W + 2 * Radius + 1; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : (x >= W + Radius ? W - 1 : x - Radius);
            out.write(row[sx]);
        }
    }
}


constexpr int WOC = N1/(4*T);
using transformed_weight = wino::Word<EXP_W_BITS+4>;
using transformed_input = wino::Word<EXP_A_BITS+2>;
using inverse = wino::Word<EXP_W_BITS+EXP_A_BITS+14>;

static void transform_weights(weight raw[N1][81], transformed_weight transformed[N1][9][16]) {
    wino_load_channels: for (int oc = 0; oc < N1; ++oc)
        wino_load_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS PIPELINE II=1
            wino::Word<EXP_W_BITS> kernel[9];
            transformed_weight value[16];
#pragma HLS ARRAY_PARTITION variable=kernel complete
#pragma HLS ARRAY_PARTITION variable=value complete
            for (int tap = 0; tap < 9; ++tap) {
#pragma HLS UNROLL
                kernel[tap] = raw[oc][(group/3*3+tap/3)*9+group%3*3+tap%3];
            }
            wino::weight_transform<EXP_W_BITS>(kernel,value);
            for (int tap = 0; tap < 16; ++tap) {
#pragma HLS UNROLL
                transformed[oc][group][tap] = value[tap];
            }
        }
}

static void conv1_tiles(hls::stream<input> &in, hls::stream<pixel1> &top,
                        hls::stream<pixel1> &bottom, transformed_weight weights[N1][9][16], bias biases[N1]) {
    constexpr int PW = W+9;
    static input line[9][PW], window[10][10];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
#ifndef __SYNTHESIS__
    unsigned reads = 0, writes = 0;
#endif
    wino_rows: for (int y = 0; y < H+9; ++y)
        wino_columns: for (int x = 0; x < PW; ++x) {
            input column[10];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
                column[r] = line[r][x];
            }
            column[9] = in.read();
#ifndef __SYNTHESIS__
            ++reads;
#endif
            for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
                line[r][x] = column[r+1];
            }
            for (int r = 0; r < 10; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 9; ++c) {
#pragma HLS UNROLL
                    window[r][c] = window[r][c+1];
                }
                window[r][9] = column[r];
            }
            if (y >= 9 && x >= 9 && (y-9)%2 == 0 && (x-9)%2 == 0) {
                transformed_input v[9][16];
                pixel1 tile[4];
#pragma HLS ARRAY_PARTITION variable=v complete dim=0
#pragma HLS ARRAY_PARTITION variable=tile complete dim=0
                for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
                    wino::Word<EXP_A_BITS> data[16];
#pragma HLS ARRAY_PARTITION variable=data complete
                    for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                        data[j] = window[group/3*3+j/4][group%3*3+j%4];
                    }
                    wino::input_transform<EXP_A_BITS>(data,v[group]);
                }
                wino_fold: for (int step = 0; step < 4*T; ++step) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < WOC; ++lane) {
#pragma HLS UNROLL
                        const int oc = step*WOC+lane;
                        inverse m[16], result[4];
#pragma HLS ARRAY_PARTITION variable=m complete
#pragma HLS ARRAY_PARTITION variable=result complete
                        for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                            inverse sum = 0;
                            for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
#ifdef __SYNTHESIS__
                                auto product = v[group][j]*weights[oc][group][j];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
                                const int64_t product = int64_t(v[group][j])*weights[oc][group][j];
#endif
                                sum = wino::add<EXP_W_BITS+EXP_A_BITS+14>(sum,inverse(product));
                            }
                            m[j] = sum;
                        }
                        wino::output_transform<EXP_W_BITS+EXP_A_BITS+14>(m,result);
                        for (int j = 0; j < 4; ++j) {
#pragma HLS UNROLL
#ifndef __SYNTHESIS__
                            assert((result[j] & 3) == 0);
#endif
                            tile[j].v[oc] = relu1(acc1(result[j] >> 2)+bias1(biases[oc]));
                        }
                    }
                }
                top.write(tile[0]);
#ifndef __SYNTHESIS__
                ++writes;
#endif
                if (x-8 < W) {
                    top.write(tile[1]);
#ifndef __SYNTHESIS__
                    ++writes;
#endif
                }
                if (y-8 < H) {
                    bottom.write(tile[2]);
#ifndef __SYNTHESIS__
                    ++writes;
#endif
                    if (x-8 < W) {
                        bottom.write(tile[3]);
#ifndef __SYNTHESIS__
                        ++writes;
#endif
                    }
                }
            }
        }
#ifndef __SYNTHESIS__
    assert(reads == (H+9)*(W+9) && writes == H*W);
#endif
}

static void reorder_rows(hls::stream<pixel1> &top, hls::stream<pixel1> &bottom, hls::stream<pixel1> &out) {
    raster_rows: for (int y = 0; y < H; ++y)
        raster_columns: for (int x = 0; x < W; ++x) {
#pragma HLS PIPELINE II=1
            out.write(y%2 ? bottom.read() : top.read());
        }
}

static void conv1_stream(hls::stream<input> &in, hls::stream<pixel1> &out,
                         transformed_weight weights[N1][9][16], bias biases[N1]) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> top("wino_top_rows"), bottom("wino_bottom_rows");
#pragma HLS STREAM variable=top depth=512
#pragma HLS STREAM variable=bottom depth=512
#if EXP_ROW_LUTRAM
#pragma HLS BIND_STORAGE variable=top type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=bottom type=fifo impl=lutram
#endif
    conv1_tiles(in,top,bottom,weights,biases);
    reorder_rows(top,bottom,out);
}

#if EXP_PACK_C2
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         weight weights[N2][N1], bias biases[N2]) {
    c2_pixels: for (int p = 0; p < H * W; ++p) {
        const pixel1 value = in.read();
        pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete

        constexpr int PAIRS = N2/(2*T);
        c2_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
            for (int lane = 0; lane < PAIRS; ++lane) {
#pragma HLS UNROLL
                const int oc = 2*(step*PAIRS+lane);
                acc2 first = bias1(biases[oc]), second = bias1(biases[oc+1]);
                for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
                    acc1 p0, p1;
                    pair_weights(weights[oc][ic],weights[oc+1][ic],value.v[ic],p0,p1);
                    first += p0;
                    second += p1;
                }
                result.v[oc] = relu2(first);
                result.v[oc+1] = relu2(second);
            }
        }

        out.write(result);
    }
}

#else
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
            sums[oc] = bias1(biases[oc]);
        }
        c2_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
            for (int oc = 0; oc < N2; ++oc) {
#pragma HLS UNROLL
                for (int lane = 0; lane < C2_IC; ++lane) {
#pragma HLS UNROLL
                    const int ic = step * C2_IC + lane;
                    auto product = value.v[ic] * weights[oc][ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                    sums[oc] += product;
                }
            }
        }
        for (int oc = 0; oc < N2; ++oc) {
#pragma HLS UNROLL
            result.v[oc] = relu2(sums[oc]);
        }
#else
        c2_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
            for (int lane = 0; lane < C2_OC; ++lane) {
#pragma HLS UNROLL
                const int oc = step * C2_OC + lane;
                acc2 sum = bias1(biases[oc]);
                for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
                    auto product = value.v[ic] * weights[oc][ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                    sum += product;
                }
                result.v[oc] = relu2(sum);
            }
        }
#endif
        out.write(result);
    }
}

#endif
static void conv12(hls::stream<input> &in, hls::stream<pixel2> &out,
                   transformed_weight w1[N1][9][16], bias b1[N1], weight w2[N2][N1], bias b2[N2]) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> features("conv1_features");
#pragma HLS STREAM variable=features depth=4
    conv1_stream(in, features, w1, b1);
    conv2_stream(features, out, w2, b2);
}


static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         weight weights[N2][25], bias biases[N3]) {
    constexpr int PW = W+5, LANES = N2/(2*T);
    static act2 line[4][PW][N2];
    static act2 window[5][6][N2];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS ARRAY_RESHAPE variable=line complete dim=3
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
#ifndef __SYNTHESIS__
    unsigned reads = 0, writes = 0;
#endif
    c3_rows: for (int y = 0; y < H+4; ++y)
        c3_columns: for (int x = 0; x < PW; ++x) {
            const pixel2 value = in.read();
#ifndef __SYNTHESIS__
            ++reads;
#endif
            for (int ic = 0; ic < N2; ++ic) {
#pragma HLS UNROLL
                act2 column[5];
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
                    for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                        window[r][c][ic] = window[r][c+1][ic];
                    }
                    window[r][5][ic] = column[r];
                }
            }
            if (y >= 4 && x >= 5 && (x-5)%2 == 0) {
                acc3 first = bias3(biases[0]), second = bias3(biases[0]);
                c3_fold: for (int step = 0; step < 2*T; ++step) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < LANES; ++lane) {
#pragma HLS UNROLL
                        const int ic = step*LANES+lane;
                        for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                            acc3 p0, p1;
                            pair_pixels(window[tap/5][tap%5][ic],window[tap/5][tap%5+1][ic],weights[ic][tap],p0,p1);
                            first += p0;
                            second += p1;
                        }
                    }
                }
                out.write(quantize<EXP_W_BITS-2>(first));
#ifndef __SYNTHESIS__
                ++writes;
#endif
                if (x-4 < W) {
                    out.write(quantize<EXP_W_BITS-2>(second));
#ifndef __SYNTHESIS__
                    ++writes;
#endif
                }
            }
        }
#ifndef __SYNTHESIS__
    assert(reads == (H+4)*(W+5) && writes == H*W);
#endif
}

static void write_output(hls::stream<output> &stream, ftmap_t out[N3][H][W]) {
    write_pixels: for (int i = 0; i < H * W; ++i) {
#pragma HLS PIPELINE II=1
        out[0][i / W][i % W] = decode(stream.read());
    }
}

static void dataflow_region(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W],
                            transformed_weight w1[N1][9][16], bias b1[N1], weight w2[N2][N1], bias b2[N2],
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
    static transformed_weight transformed[N1][9][16];
#pragma HLS ARRAY_PARTITION variable=transformed cyclic factor=WOC dim=1
#pragma HLS ARRAY_PARTITION variable=transformed complete dim=2
#pragma HLS ARRAY_PARTITION variable=transformed complete dim=3
#pragma HLS BIND_STORAGE variable=transformed type=ram_2p impl=lutram
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
#pragma HLS ARRAY_PARTITION variable=w3 cyclic factor=(N2/(2*T)) dim=1
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
        w1[i / 81][i % 81] = encode_weight(weights1[i / 81][0][(i % 81) / 9][i % 9]);
    }
    load2: for (int i = 0; i < 2048; ++i) {
#pragma HLS PIPELINE II=1
        w2[i / N1][i % N1] = encode_weight(weights2[i / N1][i % N1][0][0]);
    }
    load3: for (int i = 0; i < 800; ++i) {
#pragma HLS PIPELINE II=1
        w3[i / 25][i % 25] = encode_weight(weights3[0][i / 25][(i % 25) / 5][i % 5]);
    }
    for (int i = 0; i < N1; ++i) b1[i] = encode_weight(biases1[i]);
    for (int i = 0; i < N2; ++i) b2[i] = encode_weight(biases2[i]);
    b3[0] = encode_weight(biases3[0]);
    transform_weights(w1,transformed);
    dataflow_region(in, out, transformed, b1, w2, b2, w3, b3);
}

static void layer_region(ftmap_t in[N0][H][W], hls::stream<pixel1> &out,
                         transformed_weight weights[N1][9][16], bias biases[N1]) {
#pragma HLS DATAFLOW
    hls::stream<input> raw("layer_raw"), padded("layer_padded");
#pragma HLS STREAM variable=raw depth=512
#pragma HLS STREAM variable=padded depth=16
    read_input(in,raw);
    replicate_pad<input,4>(raw,padded);
    conv1_stream(padded,out,weights,biases);
}

void wino_conv1(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1],
                param_t biases1[N1], hls::stream<pixel1> &out) {
#pragma HLS INTERFACE mode=m_axi port=in offset=slave bundle=image_in depth=65025 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=weights1 offset=slave bundle=parameters depth=5184 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases1 offset=slave bundle=parameters depth=64
#pragma HLS INTERFACE mode=axis port=out
#pragma HLS AGGREGATE variable=out compact=bit
#pragma HLS INTERFACE mode=s_axilite port=in bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights1 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases1 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return bundle=control
    static weight raw[N1][81];
    static transformed_weight transformed[N1][9][16];
    bias b1[N1];
#pragma HLS ARRAY_PARTITION variable=raw cyclic factor=WOC dim=1
#pragma HLS ARRAY_PARTITION variable=raw complete dim=2
#pragma HLS BIND_STORAGE variable=raw type=ram_2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=transformed cyclic factor=WOC dim=1
#pragma HLS ARRAY_PARTITION variable=transformed complete dim=2
#pragma HLS ARRAY_PARTITION variable=transformed complete dim=3
#pragma HLS BIND_STORAGE variable=transformed type=ram_2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=b1 complete
    layer_load: for (int i = 0; i < 5184; ++i) {
#pragma HLS PIPELINE II=1
        raw[i/81][i%81] = encode_weight(weights1[i/81][0][(i%81)/9][i%9]);
    }
    for (int i = 0; i < N1; ++i) b1[i] = encode_weight(biases1[i]);
    transform_weights(raw,transformed);
    layer_region(in,out,transformed,b1);
}
