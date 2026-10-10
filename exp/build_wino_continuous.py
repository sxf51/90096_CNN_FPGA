#!/usr/bin/env python3
"""Generate the preplanned fixed-tripcount Winograd designs without overwrites."""
import shutil
from build_arch_f import C2, C3, PAD, REDUCE
from run_exp import ROOT, check_protected


C1 = r'''
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
                         transformed_weight weights[N1][9][16], bias biases[N1]) {
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
                         transformed_weight weights[N1][9][16], bias biases[N1]) {
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
    wino_engine(windows,tiles,weights,biases);
    distribute_tiles(tiles,top,bottom);
    reorder_rows(top,bottom,out);
}
'''


def main():
    check_protected()
    for exp_id in ("W10", "W11", "W12", "W13", "C07"):
        if not list((ROOT / "experiments").glob(exp_id+"_*/plan.json")):
            raise RuntimeError("Missing immutable paper plan: "+exp_id)
    for original_name, name in (("winograd_network_r1", "winograd_continuous"),
                                ("combination_network_r1", "combination_continuous")):
        original = ROOT / "designs" / original_name
        target = ROOT / "designs" / name
        if target.exists():
            raise RuntimeError("Design exists: "+name)
        shutil.copytree(original,target)
        text = (original / "srcnn.cpp").read_text()
        start, end = text.index("static void conv1_tiles"), text.index("static void conv2_stream")
        text = text[:start]+C1+text[end:]
        if name == "winograd_continuous":
            text = text.replace("using namespace numeric;", "using namespace numeric;\n"+
                                "#ifndef EXP_ALL_CONTINUOUS\n#define EXP_ALL_CONTINUOUS 0\n#endif\n"+REDUCE)
            padding = PAD.replace("W+2*Radius", "W+2*Radius+(Radius == 4 ? 1 : 0)")
            padding = padding.replace("y < Radius;", "y < Radius+(Radius == 4 ? 1 : 0);")
            pos = text.index("constexpr int WOC")
            text = text[:pos]+padding+text[pos:]
            for signature, end_signature, new in (("static void conv2_stream", "static void conv12", C2),
                                                    ("static void conv3_stream", "static void write_output", C3)):
                start, end = text.index(signature),text.index(end_signature)
                text = text[:start]+"#if EXP_ALL_CONTINUOUS\n"+new+"#else\n"+text[start:end]+"#endif\n\n"+text[end:]
            for old, online in (("replicate_pad<input, 4>(raw, padded1);", "online_pad<input,4>(raw,padded1);"),
                                ("replicate_pad<pixel2, 2>(features2, padded3);", "online_pad<pixel2,2>(features2,padded3);"),
                                ("replicate_pad<input,4>(raw,padded);", "online_pad<input,4>(raw,padded);")):
                text = text.replace(old,"#if EXP_ALL_CONTINUOUS\n    "+online+"\n#else\n    "+old+"\n#endif")
            # W10 retains the original shallow stream mapping as the control.
            for old, replacement in (("#pragma HLS STREAM variable=features depth=4", "features"),
                                      ("#pragma HLS STREAM variable=features2 depth=4", "features2"),
                                      ("#pragma HLS STREAM variable=padded3 depth=16", "padded3")):
                text = text.replace(old, old+"\n#if EXP_ALL_CONTINUOUS\n#pragma HLS BIND_STORAGE variable="+
                                    replacement+" type=fifo impl=lutram\n#endif")
        (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
