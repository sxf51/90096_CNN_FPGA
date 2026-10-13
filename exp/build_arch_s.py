#!/usr/bin/env python3
"""Generate structure variants only after their committed paper plans exist."""
import shutil
from run_exp import ROOT, check_protected

TILE = r'''
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
'''

DDR = r'''
float feature1[H*W*N1], feature2[H*W*N2];

template<class Pixel, int Channels>
static void write_features(hls::stream<Pixel> &in, float memory[H*W*Channels]) {
    ddr_write_pixels: for (int p = 0; p < H*W; ++p) {
        const Pixel value = in.read();
        ddr_write_channels: for (int c = 0; c < Channels; ++c) {
#pragma HLS PIPELINE II=1
            memory[p*Channels+c] = float(value.v[c]);
        }
    }
}

template<class Pixel, int Channels>
static void read_features(float memory[H*W*Channels], hls::stream<Pixel> &out) {
    ddr_read_pixels: for (int p = 0; p < H*W; ++p) {
        Pixel value;
        ddr_read_channels: for (int c = 0; c < Channels; ++c) {
#pragma HLS PIPELINE II=1
            value.v[c] = act1(memory[p*Channels+c]);
        }
        out.write(value);
    }
}

static void ddr_layer1(ftmap_t in[N0][H][W], weight w1[N1][81], bias b1[N1]) {
#pragma HLS DATAFLOW
    hls::stream<input> raw("ddr_raw"), padded("ddr_pad1");
    hls::stream<pixel1> result("ddr_features1");
#pragma HLS STREAM variable=raw depth=512
#pragma HLS STREAM variable=padded depth=16
#pragma HLS STREAM variable=result depth=4
    read_input(in, raw);
    replicate_pad<input,4>(raw,padded);
    conv1_stream(padded,result,w1,b1);
    write_features<pixel1,N1>(result,feature1);
}

static void ddr_layer2(weight w2[N2][N1], bias b2[N2]) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> in("ddr_layer2_in");
    hls::stream<pixel2> out("ddr_layer2_out");
#pragma HLS STREAM variable=in depth=4
#pragma HLS STREAM variable=out depth=4
    read_features<pixel1,N1>(feature1,in);
    conv2_stream(in,out,w2,b2);
    write_features<pixel2,N2>(out,feature2);
}

static void ddr_layer3(ftmap_t out[N3][H][W], weight w3[N2][25], bias b3[N3]) {
#pragma HLS DATAFLOW
    hls::stream<pixel2> in("ddr_layer3_in"), padded("ddr_pad3");
    hls::stream<output> result("ddr_result");
#pragma HLS STREAM variable=in depth=4
#pragma HLS STREAM variable=padded depth=16
#pragma HLS STREAM variable=result depth=16
    read_features<pixel2,N2>(feature2,in);
    replicate_pad<pixel2,2>(in,padded);
    conv3_stream(padded,result,w3,b3);
    write_output(result,out);
}
'''


def main():
    check_protected()
    for exp_id in ("S01", "S03", "S04", "S05", "S06"):
        if not list((ROOT / "experiments").glob(exp_id + "_*/plan.json")):
            raise RuntimeError("Missing committed plan: " + exp_id)
    base = ROOT / "designs/dataflow_int"
    source = (base / "srcnn.cpp").read_text()
    for name in ("tile_fusion", "ddr_global_probe"):
        target = ROOT / "designs" / name
        if target.exists():
            raise RuntimeError("Design already exists")
        shutil.copytree(base, target)
        head, top = source.split("void srcnn(", 1)
        if name == "tile_fusion":
            head = head[:head.index("static void read_input")]
            text = head + TILE + "\nvoid srcnn(" + top.replace(
                "dataflow_region(in, out, w1, b1, w2, b2, w3, b3);",
                "tile_region(in, out, w1, b1, w2, b2, w3, b3);")
        else:
            text = head + DDR + "\nvoid srcnn(" + top.replace(
                "dataflow_region(in, out, w1, b1, w2, b2, w3, b3);",
                "ddr_layer1(in,w1,b1);\n    ddr_layer2(w2,b2);\n    ddr_layer3(out,w3,b3);")
            marker = "#pragma HLS INTERFACE mode=m_axi port=in"
            text = text.replace(marker, "#pragma HLS INTERFACE mode=m_axi port=feature1 bundle=scratch1 depth=4161600 max_read_burst_length=256 max_write_burst_length=256\n"
                                "#pragma HLS INTERFACE mode=m_axi port=feature2 bundle=scratch2 depth=2080800 max_read_burst_length=256 max_write_burst_length=256\n" + marker)
        (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
