#include "types.h"
#include "winograd_math.h"
#include "srcnn.h"
#include "rom_constants.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif
using namespace numeric;
#ifndef EXP_ALL_CONTINUOUS
#define EXP_ALL_CONTINUOUS 0
#endif
static_assert(EXP_ALL_CONTINUOUS && EXP_W_BITS == 10 && EXP_A_BITS == 10,
              "ROM content preserves the W21 continuous w10a10 precision contract");

#ifndef EXP_ONLINE_PAD
#define EXP_ONLINE_PAD 0
#endif
struct window1 { input v[81]; };
struct window3 { act2 v[400]; };

template<int Count> struct Reduction {
    static acc1 sum(acc1 values[Count]) {
#pragma HLS INLINE
        acc1 next[Count/2];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int i = 0; i < Count/2; ++i) {
#pragma HLS UNROLL
            acc1 value = values[2*i]+values[2*i+1];
#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1
            next[i] = value;
        }
        return Reduction<Count/2>::sum(next);
    }
};
template<> struct Reduction<1> {
    static acc1 sum(acc1 values[1]) {
#pragma HLS INLINE
        return values[0];
    }
};

constexpr int power2(int value) {
    return value <= 1 ? 1 : 2*power2((value+1)/2);
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
        pad_write_row: for (int x = 0; x < W + 2 * Radius + (Radius == 4 ? 1 : 0); ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : (x >= W + Radius ? W - 1 : x - Radius);
            out.write(row[sx]);
        }
    }
}



template<class Pixel, int Radius>
static void online_pad(hls::stream<Pixel> &in, hls::stream<Pixel> &out) {
    Pixel row[W];
#pragma HLS AGGREGATE variable=row compact=bit
#pragma HLS BIND_STORAGE variable=row type=ram_2p impl=bram
    online_first_read: for (int x = 0; x < W; ++x) {
#pragma HLS PIPELINE II=1
        row[x] = in.read();
    }
    online_first_repeats: for (int y = 0; y <= Radius; ++y)
        online_first_write: for (int x = 0; x < W+2*Radius+(Radius == 4 ? 1 : 0); ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : x >= W+Radius ? W-1 : x-Radius;
            out.write(row[sx]);
        }
    online_rows: for (int y = 1; y < H; ++y) {
        Pixel value;
        online_columns: for (int x = 0; x < W+2*Radius+(Radius == 4 ? 1 : 0); ++x) {
#pragma HLS PIPELINE II=1
            if (x == 0 || (x > Radius && x < W+Radius)) {
                value = in.read();
                row[x == 0 ? 0 : x-Radius] = value;
            }
            out.write(value);
        }
    }
    online_bottom_repeats: for (int y = 0; y < Radius+(Radius == 4 ? 1 : 0); ++y)
        online_bottom_write: for (int x = 0; x < W+2*Radius+(Radius == 4 ? 1 : 0); ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : x >= W+Radius ? W-1 : x-Radius;
            out.write(row[sx]);
        }
}
constexpr int WOC = N1/(4*T);
using transformed_weight = wino::Word<EXP_W_BITS+4>;
using transformed_input = wino::Word<EXP_A_BITS+2>;
using inverse = wino::Word<EXP_W_BITS+EXP_A_BITS+14>;


struct transformed_window { transformed_input v[9][16]; };
struct tile_block { pixel1 pixel[4]; };
constexpr int TILE_W = (W+1)/2;
constexpr int TILE_H = (H+1)/2;

static void wino_windows(hls::stream<input> &in, hls::stream<transformed_window> &out) {
    constexpr int PW = W+9;
    static input line[9][PW], window[10][10];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
#ifndef __SYNTHESIS__
    unsigned writes = 0;
#endif
    wino_make_windows: for (int p = 0; p < (H+9)*PW; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p/PW, x = p%PW;
        input column[10];
#pragma HLS ARRAY_PARTITION variable=column complete
        for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
            column[r] = line[r][x];
        }
        column[9] = in.read();
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
            transformed_window result;
#pragma HLS ARRAY_PARTITION variable=result.v complete dim=0
            for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
                wino::Word<EXP_A_BITS> data[16];
#pragma HLS ARRAY_PARTITION variable=data complete
                for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                    data[j] = window[group/3*3+j/4][group%3*3+j%4];
                }
                wino::input_transform<EXP_A_BITS>(data,result.v[group]);
            }
            out.write(result);
#ifndef __SYNTHESIS__
            ++writes;
#endif
        }
    }
#ifndef __SYNTHESIS__
    assert(writes == TILE_H*TILE_W);
#endif
}

static void wino_engine(hls::stream<transformed_window> &in, hls::stream<tile_block> &out) {
    static const transformed_weight weights[N1][9][16] = EXP_ROM_W1;
    static const bias biases[N1] = EXP_ROM_B1;
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=WOC dim=1
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete dim=3
#pragma HLS BIND_STORAGE variable=weights type=rom_1p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    transformed_window value;
    tile_block tile;
#pragma HLS ARRAY_PARTITION variable=value.v complete dim=0
#pragma HLS ARRAY_PARTITION variable=tile.pixel complete dim=0
    continuous_wino_fold: for (int iteration = 0; iteration < TILE_H*TILE_W*4*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%(4*T);
        if (step == 0) value = in.read();
        act1 next[4][WOC];
#pragma HLS ARRAY_PARTITION variable=next complete dim=0
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
                    auto product = value.v[group][j]*weights[oc][group][j];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
                    const int64_t product = int64_t(value.v[group][j])*weights[oc][group][j];
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
                next[j][lane] = relu1(acc1(result[j] >> 2)+bias1(biases[oc]));
            }
        }
        for (int j = 0; j < 4; ++j) {
#pragma HLS UNROLL
            for (int c = 0; c < N1-WOC; ++c) {
#pragma HLS UNROLL
                tile.pixel[j].v[c] = tile.pixel[j].v[c+WOC];
            }
            for (int lane = 0; lane < WOC; ++lane) {
#pragma HLS UNROLL
                tile.pixel[j].v[N1-WOC+lane] = next[j][lane];
            }
        }
        if (step == 4*T-1) out.write(tile);
    }
}

static void distribute_tiles(hls::stream<tile_block> &in, hls::stream<pixel1> &top,
                              hls::stream<pixel1> &bottom) {
    tile_block value;
#pragma HLS ARRAY_PARTITION variable=value.pixel complete dim=0
#ifndef __SYNTHESIS__
    unsigned writes = 0;
#endif
    distribute_tile_pixels: for (int p = 0; p < TILE_H*TILE_W*4; ++p) {
#pragma HLS PIPELINE II=1
        const int j = p%4, tile = p/4;
        if (j == 0) value = in.read();
        const int y = 2*(tile/TILE_W)+j/2;
        const int x = 2*(tile%TILE_W)+j%2;
        if (y < H && x < W) {
            if (j < 2) top.write(value.pixel[j]);
            else bottom.write(value.pixel[j]);
#ifndef __SYNTHESIS__
            ++writes;
#endif
        }
    }
#ifndef __SYNTHESIS__
    assert(writes == H*W);
#endif
}

static void reorder_rows(hls::stream<pixel1> &top, hls::stream<pixel1> &bottom,
                          hls::stream<pixel1> &out) {
    raster_rows: for (int y = 0; y < H; ++y)
        raster_columns: for (int x = 0; x < W; ++x) {
#pragma HLS PIPELINE II=1
            out.write(y%2 ? bottom.read() : top.read());
        }
}

static void conv1_stream(hls::stream<input> &in, hls::stream<pixel1> &out) {
#pragma HLS DATAFLOW
    hls::stream<transformed_window> windows("wino_windows");
    hls::stream<tile_block> tiles("wino_tile_blocks");
    hls::stream<pixel1> top("wino_top_rows"), bottom("wino_bottom_rows");
#pragma HLS STREAM variable=windows depth=2
#pragma HLS STREAM variable=tiles depth=2
#pragma HLS BIND_STORAGE variable=windows type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=tiles type=fifo impl=lutram
#pragma HLS STREAM variable=top depth=512
#pragma HLS STREAM variable=bottom depth=512
#if EXP_ROW_LUTRAM
#pragma HLS BIND_STORAGE variable=top type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=bottom type=fifo impl=lutram
#endif
    wino_windows(in,windows);
    wino_engine(windows,tiles);
    distribute_tiles(tiles,top,bottom);
    reorder_rows(top,bottom,out);
}
#if EXP_ALL_CONTINUOUS

static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out) {
    static const weight weights[N2][N1] = EXP_ROM_W2;
    static const bias biases[N2] = EXP_ROM_B2;
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C2_OC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C2_IC dim=2
#pragma HLS BIND_STORAGE variable=weights type=rom_1p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    pixel1 value;
    pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    continuous_c2_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) value = in.read();
        act2 next[C2_OC];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < C2_OC; ++lane) {
#pragma HLS UNROLL
            const int oc = step*C2_OC+lane;
            acc1 products[64];
#pragma HLS ARRAY_PARTITION variable=products complete
            for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
                auto product = value.v[ic]*weights[oc][ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                products[ic] = product;
            }
            next[lane] = relu2(Reduction<64>::sum(products)+bias1(biases[oc]));
        }
        for (int c = 0; c < N2-C2_OC; ++c) {
#pragma HLS UNROLL
            result.v[c] = result.v[c+C2_OC];
        }
        for (int lane = 0; lane < C2_OC; ++lane) {
#pragma HLS UNROLL
            result.v[N2-C2_OC+lane] = next[lane];
        }
        if (step == T-1) out.write(result);
    }
}
#else
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         hls::stream<weight> &params) {
    static weight weights[N2][N1];
    static bias biases[N2];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C2_OC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C2_IC dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    load_local(params, weights, biases);
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

static void conv12(hls::stream<input> &in, hls::stream<pixel2> &out) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> features("conv1_features");
#pragma HLS STREAM variable=features depth=4
#if EXP_ALL_CONTINUOUS
#pragma HLS BIND_STORAGE variable=features type=fifo impl=lutram
#endif
    conv1_stream(in, features);
    conv2_stream(features, out);
}

#if EXP_ALL_CONTINUOUS

static void windows3(hls::stream<pixel2> &in, hls::stream<window3> &out0, hls::stream<window3> &out1) {
    constexpr int PW = W+4;
    static act2 line[4][PW][N2], window[5][5][N2];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS ARRAY_RESHAPE variable=line complete dim=3
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    make_windows3: for (int p = 0; p < (H+4)*PW; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p/PW, x = p%PW;
        const pixel2 value = in.read();
        window3 result0, result1;
#pragma HLS ARRAY_PARTITION variable=result0.v complete
#pragma HLS ARRAY_PARTITION variable=result1.v complete
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
                for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                    window[r][c][ic] = window[r][c+1][ic];
                }
                window[r][4][ic] = column[r];
                for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                    if (ic < N2/2) result0.v[(r*5+c)*(N2/2)+ic] = window[r][c][ic];
                    else result1.v[(r*5+c)*(N2/2)+ic-N2/2] = window[r][c][ic];
                }
            }
        }
        if (y >= 4 && x >= 4) {
            out0.write(result0);
            out1.write(result1);
        }
    }
}

static void engine3(hls::stream<window3> &in0, hls::stream<window3> &in1, hls::stream<output> &out) {
    static const weight weights[N2][25] = EXP_ROM_W3;
    static const bias biases[N3] = EXP_ROM_B3;
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_IC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_TAP dim=2
#pragma HLS BIND_STORAGE variable=weights type=rom_1p impl=lutram
    constexpr int COUNT = power2(C3_IC*25);
    window3 value0, value1;
    acc3 sum = 0;
#pragma HLS ARRAY_PARTITION variable=value0.v complete
#pragma HLS ARRAY_PARTITION variable=value1.v complete
    continuous_c3_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) { value0 = in0.read(); value1 = in1.read(); }
        acc1 products[COUNT];
#pragma HLS ARRAY_PARTITION variable=products complete
        for (int index = 0; index < COUNT; ++index) {
#pragma HLS UNROLL
            if (index < C3_IC*25) {
                const int ic = step*C3_IC+index/25, tap = index%25;
                auto product = (ic < N2/2 ? value0.v[tap*(N2/2)+ic] : value1.v[tap*(N2/2)+ic-N2/2])*weights[ic][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                products[index] = product;
            } else products[index] = 0;
        }
        const acc1 partial = Reduction<COUNT>::sum(products);
        acc3 next = (step == 0 ? bias3(biases[0]) : sum)+partial;
#pragma HLS BIND_OP variable=next op=add impl=fabric latency=1
        sum = next;
        if (step == T-1) out.write(quantize<EXP_W_BITS-2>(next));
    }
}

static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out) {
#pragma HLS DATAFLOW

    hls::stream<window3> windows0("windows3_low_channels"), windows1("windows3_high_channels");
#pragma HLS STREAM variable=windows0 depth=2
#pragma HLS STREAM variable=windows1 depth=2
#pragma HLS BIND_STORAGE variable=windows0 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=windows1 type=fifo impl=lutram
    windows3(in,windows0,windows1);
    engine3(windows0,windows1,out);
}
#else
static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         hls::stream<weight> &params) {
    static weight weights[N2][25];
    static bias biases[N3];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_IC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_TAP dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
    load_local(params, weights, biases);
    constexpr int PW = W + 4;
    static act2 line[4][PW][N2];
    static act2 window[5][5][N2];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS ARRAY_RESHAPE variable=line complete dim=3
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    c3_rows: for (int y = 0; y < H + 4; ++y)
        c3_columns: for (int x = 0; x < PW; ++x) {
            const pixel2 value = in.read();
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
                    line[r][x][ic] = column[r + 1];
                }
                for (int r = 0; r < 5; ++r) {
#pragma HLS UNROLL
                    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                        window[r][c][ic] = window[r][c + 1][ic];
                    }
                    window[r][4][ic] = column[r];
                }
            }
            if (y >= 4 && x >= 4) {
                acc3 sum = bias3(biases[0]);
                c3_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < C3_IC; ++lane) {
#pragma HLS UNROLL
                        for (int j = 0; j < C3_TAP; ++j) {
#pragma HLS UNROLL
#if EXP_C3_SPLIT
                            const int ic = lane, tap = step * C3_TAP + j;
#else
                            const int ic = step * C3_IC + lane, tap = j;
#endif
                            if (tap < 25) {
                                auto product = window[tap / 5][tap % 5][ic] * weights[ic][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                                sum += product;
                            }
                        }
                    }
                }
                out.write(quantize<EXP_W_BITS - 2>(sum));
            }
        }
}

#endif

static void write_output(hls::stream<output> &stream, ftmap_t out[N3][H][W]) {
    write_pixels: for (int i = 0; i < H * W; ++i) {
#pragma HLS PIPELINE II=1
        out[0][i / W][i % W] = decode(stream.read());
    }
}

static void dataflow_region(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W]) {
#pragma HLS DATAFLOW
    hls::stream<input> raw("raw"), padded1("padded1");
    hls::stream<pixel2> features2("features2"), padded3("padded3");
    hls::stream<output> result("result");
#pragma HLS STREAM variable=raw depth=512
#pragma HLS STREAM variable=padded1 depth=16
#pragma HLS STREAM variable=features2 depth=4
#if EXP_ALL_CONTINUOUS
#pragma HLS BIND_STORAGE variable=features2 type=fifo impl=lutram
#endif
#pragma HLS STREAM variable=padded3 depth=16
#if EXP_ALL_CONTINUOUS
#pragma HLS BIND_STORAGE variable=padded3 type=fifo impl=lutram
#endif
#pragma HLS STREAM variable=result depth=16
    read_input(in, raw);
    #if EXP_ONLINE_PAD
    online_pad<input,4>(raw,padded1);
#else
    replicate_pad<input, 4>(raw, padded1);
#endif
    conv12(padded1, features2);
    #if EXP_ONLINE_PAD
    online_pad<pixel2,2>(features2,padded3);
#else
    replicate_pad<pixel2, 2>(features2, padded3);
#endif
    conv3_stream(padded3, result);
    write_output(result, out);
}

void srcnn_rom(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W]) {
#pragma HLS INTERFACE mode=m_axi port=in offset=slave bundle=image_in depth=65025 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=out offset=slave bundle=image_out depth=65025 max_write_burst_length=256
#pragma HLS INTERFACE mode=s_axilite port=in bundle=control
#pragma HLS INTERFACE mode=s_axilite port=out bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return bundle=control
    dataflow_region(in, out);
}
