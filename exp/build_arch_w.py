#!/usr/bin/env python3
"""Generate exact integer Winograd layer/frame designs from committed plans."""
import shutil
from run_exp import ROOT, check_protected

WINO = r'''
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
    conv1_tiles(in,top,bottom,weights,biases);
    reorder_rows(top,bottom,out);
}
'''

LAYER = r'''
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
'''


def main():
    check_protected()
    for exp_id in ("W04", "W05", "W06"):
        if not list((ROOT / "experiments").glob(exp_id + "_*/plan.json")):
            raise RuntimeError("Missing paper plan")
    target = ROOT / "designs/winograd_network"
    if target.exists():
        raise RuntimeError("Design exists")
    shutil.copytree(ROOT / "designs/dataflow_int", target)
    shutil.copyfile(ROOT / "designs/winograd_pe/winograd_math.h", target / "winograd_math.h")
    text = (target / "srcnn.cpp").read_text().replace('#include "types.h"', '#include "types.h"\n#include "winograd_math.h"')
    start, end = text.index("static void conv1_stream"), text.index("static void conv2_stream")
    text = text[:start]+WINO+"\n"+text[end:]
    text = text.replace("weight w1[N1][81], bias b1[N1], weight w2", "transformed_weight w1[N1][9][16], bias b1[N1], weight w2")
    text = text.replace("y < H + 2 * Radius", "y < H + 2 * Radius + (Radius == 4 ? 1 : 0)")
    text = text.replace("x < W + 2 * Radius", "x < W + 2 * Radius + (Radius == 4 ? 1 : 0)")
    text = text.replace("    static bias b1", "    static transformed_weight transformed[N1][9][16];\n"
                        "#pragma HLS ARRAY_PARTITION variable=transformed cyclic factor=WOC dim=1\n"
                        "#pragma HLS ARRAY_PARTITION variable=transformed complete dim=2\n"
                        "#pragma HLS ARRAY_PARTITION variable=transformed complete dim=3\n"
                        "#pragma HLS BIND_STORAGE variable=transformed type=ram_2p impl=lutram\n    static bias b1")
    text = text.replace("dataflow_region(in, out, w1, b1, w2, b2, w3, b3);", "transform_weights(w1,transformed);\n    dataflow_region(in, out, transformed, b1, w2, b2, w3, b3);")
    text += r'''
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
''' + LAYER
    (target / "srcnn.cpp").write_text(text)
    header = target / "srcnn.h"
    header.write_text(header.read_text()+ '\n#include "types.h"\nvoid wino_conv1(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1], param_t biases1[N1], hls::stream<numeric::pixel1> &out);\n')
    check_protected()


if __name__ == "__main__":
    main()
