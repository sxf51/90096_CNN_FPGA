#!/usr/bin/env python3
"""Create independent gather, explicit-pad scatter and edge-kernel sources."""
import json
import shutil
from run_exp import ROOT, check_plan, check_protected

EDGE = r'''static void make_edges(weight raw[N2][25], edge_weight merged[9][N2][25]) {
    merge_weights: for (int index = 0; index < 9 * N2 * 25; ++index) {
#pragma HLS PIPELINE II=1
        const int position = index / (N2 * 25), ic = (index / 25) % N2;
        const int tap = index % 25, row = tap / 5, col = tap % 5;
        const int cy = position / 3, cx = position % 3;
        edge_weight sum = 0;
        for (int ky = 0; ky < 5; ++ky) for (int kx = 0; kx < 5; ++kx) {
#pragma HLS UNROLL
            const bool selected_y = cy == 0 ? ky <= 4-row : cy == 2 ? ky >= 4-row : ky == 4-row;
            const bool selected_x = cx == 0 ? kx <= 4-col : cx == 2 ? kx >= 4-col : kx == 4-col;
            if (selected_y && selected_x) sum += edge_weight(raw[ic][ky*5+kx]);
        }
        merged[position][ic][tap] = sum;
    }
}

static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         edge_weight weights[9][N2][25], bias biases[N3]) {
    using partial = word<32>;
    static partial buffer[5][W];
    partial window[5][5];
#pragma HLS ARRAY_PARTITION variable=buffer complete dim=1
#pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    constexpr int LANES = N2 / T;
#ifndef __SYNTHESIS__
    unsigned reads = 0, writes = 0;
#endif
    edge_rows: for (int y = 0; y < H + 2; ++y) {
        const int base = (y + 3) % 5;
        for (int r = 0; r < 5; ++r) for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
            window[r][c] = 0;
        }
        edge_columns: for (int x = -2; x < W + 2; ++x) {
            if (x >= 3 && x - 3 < W)
                for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
                    buffer[bank][x-3] = window[(bank+5-base)%5][0];
                }
            partial column[5];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
                column[bank] = x+2 >= 0 && x+2 < W ? buffer[bank][x+2] : partial(0);
            }
            for (int r = 0; r < 5; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                    window[r][c] = window[r][c+1];
                }
                const int oy = y-2+r;
                window[r][4] = (y == 0 || r == 4 || oy < 0 || oy >= H) ? partial(0) : column[(base+r)%5];
            }
            if (y < H && x >= 0 && x < W) {
                const pixel2 value = in.read();
#ifndef __SYNTHESIS__
                ++reads;
#endif
                const int cy = y == 0 ? 0 : y == H-1 ? 2 : 1;
                const int cx = x == 0 ? 0 : x == W-1 ? 2 : 1;
                const int position = cy*3+cx;
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
                        const int ic = step*LANES+lane;
                        for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                            auto product = value.v[ic] * weights[position][ic][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                            contribution[tap] += product;
                        }
                    }
                }
                for (int r = 0; r < 5; ++r) for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                    const int oy = y-2+r, ox = x-2+c;
                    if (oy >= 0 && oy < H && ox >= 0 && ox < W)
                        window[r][c] += contribution[r*5+c];
                }
            }
            if (y >= 2 && x >= 2) {
                out.write(quantize<EXP_W_BITS-2>(partial(window[0][0] + bias3(biases[0]))));
#ifndef __SYNTHESIS__
                ++writes;
#endif
            }
        }
        for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
            buffer[bank][W-1] = window[(bank+5-base)%5][0];
        }
    }
#ifndef __SYNTHESIS__
    assert(reads == H*W && writes == H*W);
    std::cout << "EXP_STREAM {\"module\":\"conv3_edge\",\"reads\":" << reads << ",\"writes\":" << writes << "}" << std::endl;
#endif
}

'''


def replace(text, old, new):
    if old not in text:
        raise RuntimeError("Source pattern missing: " + old)
    return text.replace(old, new)


def main():
    check_protected()
    for exp_id, base in (("G01", "dataflow_int"), ("G02", "scatter_int"), ("G03", "dataflow_int")):
        config = json.loads((ROOT / "exp/configs" / (exp_id + ".json")).read_text())
        check_plan(config, ROOT / "experiments" / (exp_id + "_" + config["name"]))
        destination = ROOT / config["design"]
        if destination.exists():
            raise RuntimeError("New design already exists")
        shutil.copytree(ROOT / "designs" / base, destination)
        if exp_id != "G03":
            continue
        path = destination / "types.h"
        path.write_text(replace(path.read_text(), "struct pixel1", "using edge_weight = word<15>;\nstruct pixel1"))
        path = destination / "srcnn.cpp"
        text = path.read_text().replace("#include <cassert>", "#include <cassert>\n#include <iostream>")
        start, end = text.index("static void conv3_stream("), text.index("static void write_output(")
        text = text[:start] + EDGE + text[end:]
        text = replace(text, 'hls::stream<pixel2> features2("features2"), padded3("padded3");', 'hls::stream<pixel2> features2("features2");')
        text = replace(text, "#pragma HLS STREAM variable=padded3 depth=16\n", "")
        text = replace(text, "    replicate_pad<pixel2, 2>(features2, padded3);\n    conv3_stream(padded3, result, w3, b3);", "    conv3_stream(features2, result, w3, b3);")
        text = replace(text, "weight w3[N2][25], bias b3[N3])", "edge_weight w3[9][N2][25], bias b3[N3])")
        text = replace(text, "static bias b1[N1], b2[N2], b3[N3];", "static bias b1[N1], b2[N2], b3[N3];\n    static edge_weight edges[9][N2][25];\n#pragma HLS ARRAY_PARTITION variable=edges cyclic factor=C3_IC dim=2\n#pragma HLS ARRAY_PARTITION variable=edges complete dim=3\n#pragma HLS BIND_STORAGE variable=edges type=ram_2p impl=lutram")
        text = replace(text, "    dataflow_region(in, out, w1, b1, w2, b2, w3, b3);", "    make_edges(w3, edges);\n    dataflow_region(in, out, w1, b1, w2, b2, edges, b3);")
        path.write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
