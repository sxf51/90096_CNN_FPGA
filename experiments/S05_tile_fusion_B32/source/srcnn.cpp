#include "types.h"
#include "srcnn.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif
using namespace numeric;


#ifndef EXP_BLOCK
#define EXP_BLOCK 32
#endif
constexpr int B = EXP_BLOCK, IW = B + 12, FW = B + 4;

static int clamp_image(int value) {
#pragma HLS INLINE
    return value < 0 ? 0 : value >= W ? W-1 : value;
}

static void tile_region(ftmap_t in[N0][H][W], ftmap_t out[N3][H][W],
                        weight w1[N1][81], bias b1[N1], weight w2[N2][N1], bias b2[N2],
                        weight w3[N2][25], bias b3[N3]) {
    static input image[IW][IW];
    static act2 features[FW][FW][N2];
#pragma HLS ARRAY_PARTITION variable=image cyclic factor=9 dim=1
#pragma HLS ARRAY_PARTITION variable=image cyclic factor=9 dim=2
#pragma HLS BIND_STORAGE variable=image type=ram_2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=features cyclic factor=5 dim=1
#pragma HLS ARRAY_PARTITION variable=features cyclic factor=5 dim=2
#pragma HLS ARRAY_PARTITION variable=features cyclic factor=C3_IC dim=3
#pragma HLS BIND_STORAGE variable=features type=ram_2p impl=lutram
    tile_rows: for (int oy = 0; oy < H; oy += B)
        tile_columns: for (int ox = 0; ox < W; ox += B) {
            tile_input_rows: for (int y = 0; y < IW; ++y)
                tile_input_columns: for (int x = 0; x < IW; ++x) {
#pragma HLS PIPELINE II=1
                    image[y][x] = encode_input(in[0][clamp_image(oy+y-6)][clamp_image(ox+x-6)]);
                }
            tile_feature_rows: for (int y = 0; y < FW; ++y)
                tile_feature_columns: for (int x = 0; x < FW; ++x) {
                    const int py = clamp_image(oy+y-2)-oy+2;
                    const int px = clamp_image(ox+x-2)-ox+2;
                    act1 value[N1];
#pragma HLS ARRAY_PARTITION variable=value complete
                    tile_c1_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                        for (int lane = 0; lane < C1_OC; ++lane) {
#pragma HLS UNROLL
                            const int oc = step*C1_OC+lane;
                            acc1 sum = bias1(b1[oc]);
                            for (int tap = 0; tap < 81; ++tap) {
#pragma HLS UNROLL
                                auto product = image[py+tap/9][px+tap%9]*w1[oc][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                                sum += product;
                            }
                            value[oc] = relu1(sum);
                        }
                    }
                    tile_c2_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                        for (int lane = 0; lane < C2_OC; ++lane) {
#pragma HLS UNROLL
                            const int oc = step*C2_OC+lane;
                            acc2 sum = bias1(b2[oc]);
                            for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
                                auto product = value[ic]*w2[oc][ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                                sum += product;
                            }
                            features[y][x][oc] = relu2(sum);
                        }
                    }
                }
            tile_output_rows: for (int y = 0; y < B; ++y)
                tile_output_columns: for (int x = 0; x < B; ++x) {
                    if (oy+y < H && ox+x < W) {
                        acc3 sum = bias3(b3[0]);
                        tile_c3_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                            for (int lane = 0; lane < C3_IC; ++lane) {
#pragma HLS UNROLL
                                const int ic = step*C3_IC+lane;
                                for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                                    auto product = features[y+tap/5][x+tap%5][ic]*w3[ic][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                                    sum += product;
                                }
                            }
                        }
                        out[0][oy+y][ox+x] = decode(quantize<EXP_W_BITS-2>(sum));
                    }
                }
        }
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
    tile_region(in, out, w1, b1, w2, b2, w3, b3);
}
