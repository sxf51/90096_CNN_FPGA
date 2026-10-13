#include "types.h"
#include "winograd_math.h"
#include "srcnn.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif
namespace numeric {
using weight2 = word<8>;
using mixed_acc = word<21>;
static weight2 encode_weight2(float value) {
#pragma HLS INLINE
    using Q = ap_fixed<8,1,AP_RND_CONV,AP_SAT>;
    return raw_value<Q,8>(Q(value));
}
}

using namespace numeric;
#ifndef EXP_ALL_CONTINUOUS
#define EXP_ALL_CONTINUOUS 0
#endif

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
struct transformed_params1 { transformed_weight v[16]; };

static void read_raw_params(param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
                            param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
                            param_t weights3[N3][N2][F3][F3], param_t bias3_value,
                            hls::stream<weight> &raw1, hls::stream<weight> &params2,
                            hls::stream<weight> &params3, bool do_load) {
    if (!do_load) return;
    int oc1 = 0, ky1 = 0, kx1 = 0;
    int ic3 = 0, ky3 = 0, kx3 = 0;
    read_all_params: for (int i = 0; i < 8129; ++i) {
#pragma HLS PIPELINE II=1
        param_t value;
        if (i < 5184) {
            value = weights1[oc1][0][ky1][kx1];
            if (kx1 == F1-1) {
                kx1 = 0;
                if (ky1 == F1-1) { ky1 = 0; ++oc1; }
                else ++ky1;
            } else ++kx1;
        } else if (i < 5248) value = biases1[i-5184];
        else if (i < 7296) value = weights2[(i-5248)/N1][(i-5248)%N1][0][0];
        else if (i < 7328) value = biases2[i-7296];
        else if (i < 8128) {
            value = weights3[0][ic3][ky3][kx3];
            if (kx3 == F3-1) {
                kx3 = 0;
                if (ky3 == F3-1) { ky3 = 0; ++ic3; }
                else ++ky3;
            } else ++kx3;
        } else value = bias3_value;
        const weight encoded = i >= 5248 && i < 7328 ? weight(encode_weight2(value)) : encode_weight(value);
        if (i < 5248) raw1.write(encoded);
        else if (i < 7328) params2.write(encoded);
        else params3.write(encoded);
    }
}

static void transform_params1(hls::stream<weight> &raw1, hls::stream<transformed_params1> &params1,
                              bool do_load) {
    if (!do_load) return;
    weight raw[9][9];
#pragma HLS ARRAY_PARTITION variable=raw complete dim=0
    transform_channels: for (int oc = 0; oc < N1; ++oc) {
        transform_read_rows: for (int row = 0; row < 9; ++row)
            transform_read_columns: for (int column = 0; column < 9; ++column) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
                const int group = (row/3)*3+column/3;
                const int tap = (row%3)*3+column%3;
                raw[group][tap] = raw1.read();
            }
        transform_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS PIPELINE II=1
            wino::Word<EXP_W_BITS> kernel[9];
            transformed_params1 packet;
#pragma HLS ARRAY_PARTITION variable=kernel complete
#pragma HLS ARRAY_PARTITION variable=packet.v complete
            for (int tap = 0; tap < 9; ++tap) {
#pragma HLS UNROLL
                kernel[tap] = raw[group][tap];
            }
            wino::weight_transform<EXP_W_BITS>(kernel,packet.v);
            params1.write(packet);
        }
    }
    transform_bias: for (int oc = 0; oc < N1; ++oc) {
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

static void read_params(param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
                        param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
                        param_t weights3[N3][N2][F3][F3], param_t bias3_value,
                        hls::stream<transformed_params1> &params1,
                        hls::stream<weight> &params2, hls::stream<weight> &params3, bool do_load) {
#pragma HLS DATAFLOW
    hls::stream<weight> raw1("raw_conv1_params");
#pragma HLS STREAM variable=raw1 depth=16
#pragma HLS BIND_STORAGE variable=raw1 type=fifo impl=lutram
    read_raw_params(weights1,biases1,weights2,biases2,weights3,bias3_value,raw1,params2,params3,do_load);
    transform_params1(raw1,params1,do_load);
#ifndef __SYNTHESIS__
    assert(raw1.empty());
#endif
}

template<int Outputs, int Taps, int BiasCount>
static void load_local(hls::stream<weight> &params, weight (&weights)[Outputs][Taps],
                        bias (&biases)[BiasCount]) {
#pragma HLS INLINE
    local_load_channels: for (int oc = 0; oc < Outputs; ++oc)
        local_load_taps: for (int tap = 0; tap < Taps; ++tap) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            weights[oc][tap] = params.read();
        }
    local_load_bias: for (int i = 0; i < BiasCount; ++i) {
#pragma HLS PIPELINE II=1
        for (int c = 0; c < BiasCount-1; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[BiasCount-1] = params.read();
    }
}


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

static void wino_engine(hls::stream<transformed_window> &in, hls::stream<tile_block> &out,
                         hls::stream<transformed_params1> &params, bool do_load) {
    static transformed_weight weights[N1][9][16];
    static bias biases[N1];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=WOC dim=1
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete dim=3
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    if (do_load) {
    wino_local_load_channels: for (int oc = 0; oc < N1; ++oc)
        wino_local_load_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const transformed_params1 packet = params.read();
            for (int tap = 0; tap < 16; ++tap) {
#pragma HLS UNROLL
                weights[oc][group][tap] = packet.v[tap];
            }
        }
    wino_local_load_bias: for (int oc = 0; oc < N1; ++oc) {
#pragma HLS PIPELINE II=1
        const transformed_params1 packet = params.read();
        for (int c = 0; c < N1-1; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[N1-1] = bias(packet.v[0]);
    }
    }
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

static void conv1_stream(hls::stream<input> &in, hls::stream<pixel1> &out,
                         hls::stream<transformed_params1> &params, bool do_load) {
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
    wino_engine(windows,tiles,params,do_load);
    distribute_tiles(tiles,top,bottom);
    reorder_rows(top,bottom,out);
}
#if EXP_ALL_CONTINUOUS

static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         hls::stream<weight> &params, bool do_load) {
    constexpr int PAIRS = N2/(2*T);
    static word<27> packed_weights[N2/2][N1];
    static weight2 biases[N2];
    weight2 first_row[N1];
#pragma HLS ARRAY_PARTITION variable=packed_weights cyclic factor=PAIRS dim=1
#pragma HLS ARRAY_PARTITION variable=packed_weights complete dim=2
#pragma HLS BIND_STORAGE variable=packed_weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=first_row complete
#pragma HLS ARRAY_PARTITION variable=biases complete
    if (do_load) {
    packed_load_pairs: for (int pair = 0; pair < N2/2; ++pair) {
        packed_load_first: for (int ic = 0; ic < N1; ++ic) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            first_row[ic] = weight2(params.read());
        }
        packed_load_second: for (int ic = 0; ic < N1; ++ic) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const weight2 second = weight2(params.read());
            packed_weights[pair][ic] = word<27>(first_row[ic])*262144+word<27>(second);
        }
    }
    packed_load_bias: for (int i = 0; i < N2; ++i) {
#pragma HLS PIPELINE II=1
        for (int c = 0; c < N2-1; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[N2-1] = weight2(params.read());
    }
    }
    pixel1 value;
    pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    continuous_c2_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) value = in.read();
        act2 next[2*PAIRS];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < PAIRS; ++lane) {
#pragma HLS UNROLL
            const int pair = step*PAIRS+lane, oc = 2*pair;
            acc1 first[64], second[64];
#pragma HLS ARRAY_PARTITION variable=first complete
#pragma HLS ARRAY_PARTITION variable=second complete
            for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
#ifdef __SYNTHESIS__
                auto product = packed_weights[pair][ic]*value.v[ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
                const int64_t product = int64_t(packed_weights[pair][ic])*value.v[ic];
#endif
                const int bits = int(product & 262143);
                const int low = bits >= 131072 ? bits-262144 : bits;
                first[ic] = acc1(product >> 18)+(low < 0 ? 1 : 0);
                second[ic] = low;
            }
            const acc1 sum0 = Reduction<64>::sum(first)+acc1(biases[oc])*256;
            const acc1 sum1 = Reduction<64>::sum(second)+acc1(biases[oc+1])*256;
#ifndef __SYNTHESIS__
            assert(sum0 >= -(1<<20) && sum0 < (1<<20));
            assert(sum1 >= -(1<<20) && sum1 < (1<<20));
#endif
            const mixed_acc s0 = sum0, s1 = sum1;
            next[2*lane] = s0 > 0 ? quantize<8>(s0) : act2(0);
            next[2*lane+1] = s1 > 0 ? quantize<8>(s1) : act2(0);
        }
        for (int c = 0; c < N2-2*PAIRS; ++c) {
#pragma HLS UNROLL
            result.v[c] = result.v[c+2*PAIRS];
        }
        for (int c = 0; c < 2*PAIRS; ++c) {
#pragma HLS UNROLL
            result.v[N2-2*PAIRS+c] = next[c];
        }
        if (step == T-1) out.write(result);
    }
}
#else
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         hls::stream<weight> &params, bool do_load) {
    static weight weights[N2][N1];
    static bias biases[N2];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C2_OC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C2_IC dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    if (do_load) load_local(params, weights, biases);
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
                   hls::stream<transformed_params1> &params1, hls::stream<weight> &params2,
                   bool do_load) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> features("conv1_features");
#pragma HLS STREAM variable=features depth=4
#if EXP_ALL_CONTINUOUS
#pragma HLS BIND_STORAGE variable=features type=fifo impl=lutram
#endif
    conv1_stream(in, features, params1,do_load);
    conv2_stream(features, out, params2,do_load);
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

static void engine3(hls::stream<window3> &in0, hls::stream<window3> &in1, hls::stream<output> &out,
                     hls::stream<weight> &params, bool do_load) {
    static weight weights[N2][25];
    static bias biases[N3];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_IC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_TAP dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
    if (do_load) load_local(params, weights, biases);
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

static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         hls::stream<weight> &params, bool do_load) {
#pragma HLS DATAFLOW

    hls::stream<window3> windows0("windows3_low_channels"), windows1("windows3_high_channels");
#pragma HLS STREAM variable=windows0 depth=2
#pragma HLS STREAM variable=windows1 depth=2
#pragma HLS BIND_STORAGE variable=windows0 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=windows1 type=fifo impl=lutram
    windows3(in,windows0,windows1);
    engine3(windows0,windows1,out,params,do_load);
}
#else
static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         hls::stream<weight> &params, bool do_load) {
    static weight weights[N2][25];
    static bias biases[N3];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_IC dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=C3_TAP dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
    if (do_load) load_local(params, weights, biases);
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

static void dataflow_region(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W],
                            param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
                            param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
                            param_t weights3[N3][N2][F3][F3], param_t bias3_value, bool do_load) {
#pragma HLS DATAFLOW
    hls::stream<input> raw("raw"), padded1("padded1");
    hls::stream<pixel2> features2("features2"), padded3("padded3");
    hls::stream<output> result("result");
    hls::stream<transformed_params1> params1("params1");
    hls::stream<weight> params2("params2"), params3("params3");
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
#if EXP_ALL_CONTINUOUS
#pragma HLS BIND_STORAGE variable=features2 type=fifo impl=lutram
#endif
#pragma HLS STREAM variable=padded3 depth=16
#if EXP_ALL_CONTINUOUS
#pragma HLS BIND_STORAGE variable=padded3 type=fifo impl=lutram
#endif
#pragma HLS STREAM variable=result depth=16
    read_input(in, raw);
    read_params(weights1,biases1,weights2,biases2,weights3,bias3_value,params1,params2,params3,do_load);
    #if EXP_ONLINE_PAD
    online_pad<input,4>(raw,padded1);
#else
    replicate_pad<input, 4>(raw, padded1);
#endif
    conv12(padded1, features2, params1, params2,do_load);
    #if EXP_ONLINE_PAD
    online_pad<pixel2,2>(features2,padded3);
#else
    replicate_pad<pixel2, 2>(features2, padded3);
#endif
    conv3_stream(padded3, result, params3,do_load);
    write_output(result, out);
#ifndef __SYNTHESIS__
    assert(params1.empty() && params2.empty() && params3.empty());
#endif
}

void srcnn_reload(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
           param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
           param_t weights3[N3][N2][F3][F3], param_t biases3[N3], ftmap_t out[N3][H][W],
           bool load_params) {
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
#pragma HLS INTERFACE mode=s_axilite port=load_params bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return bundle=control
    static bool params_loaded = false;
    const bool do_load = load_params || !params_loaded;
    param_t bias3_value = 0;
    if (do_load) {
        // Keep the one-element bias read behind the guard before HLS scalarization.
        const volatile param_t *last_bias = biases3;
        bias3_value = last_bias[0];
    }
    dataflow_region(in, out, weights1, biases1, weights2, biases2, weights3, bias3_value, do_load);
    params_loaded = true;
}

void srcnn(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
           param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
           param_t weights3[N3][N2][F3][F3], param_t biases3[N3], ftmap_t out[N3][H][W]) {
    srcnn_reload(in, weights1, biases1, weights2, biases2, weights3, biases3, out, true);
}
