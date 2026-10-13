#!/usr/bin/env python3
"""Generate storage controls and a continuous exact direct engine."""
import shutil
from run_exp import ROOT, check_protected

REDUCE = r'''
#ifndef EXP_ONLINE_PAD
#define EXP_ONLINE_PAD 0
#endif
struct window1 { input v[81]; };
struct window3 { act2 v[800]; };

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
'''

PAD = r'''
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
        online_first_write: for (int x = 0; x < W+2*Radius; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : x >= W+Radius ? W-1 : x-Radius;
            out.write(row[sx]);
        }
    online_rows: for (int y = 1; y < H; ++y) {
        Pixel value;
        online_columns: for (int x = 0; x < W+2*Radius; ++x) {
#pragma HLS PIPELINE II=1
            if (x == 0 || (x > Radius && x < W+Radius)) {
                value = in.read();
                row[x == 0 ? 0 : x-Radius] = value;
            }
            out.write(value);
        }
    }
    online_bottom_repeats: for (int y = 0; y < Radius; ++y)
        online_bottom_write: for (int x = 0; x < W+2*Radius; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < Radius ? 0 : x >= W+Radius ? W-1 : x-Radius;
            out.write(row[sx]);
        }
}
'''

C1 = r'''
static void windows1(hls::stream<input> &in, hls::stream<window1> &out) {
    constexpr int PW = W+8;
    static input line[8][PW], window[9][9];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    make_windows1: for (int p = 0; p < (H+8)*PW; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p/PW, x = p%PW;
        input column[9];
#pragma HLS ARRAY_PARTITION variable=column complete
        for (int r = 0; r < 8; ++r) {
#pragma HLS UNROLL
            column[r] = line[r][x];
        }
        column[8] = in.read();
        for (int r = 0; r < 8; ++r) {
#pragma HLS UNROLL
            line[r][x] = column[r+1];
        }
        window1 value;
#pragma HLS ARRAY_PARTITION variable=value.v complete
        for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
            for (int c = 0; c < 8; ++c) {
#pragma HLS UNROLL
                window[r][c] = window[r][c+1];
            }
            window[r][8] = column[r];
            for (int c = 0; c < 9; ++c) {
#pragma HLS UNROLL
                value.v[9*r+c] = window[r][c];
            }
        }
        if (y >= 8 && x >= 8) out.write(value);
    }
}

static void engine1(hls::stream<window1> &in, hls::stream<pixel1> &out,
                     weight weights[N1][81], bias biases[N1]) {
    window1 value;
    pixel1 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    continuous_c1_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) value = in.read();
        act1 next[C1_OC];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < C1_OC; ++lane) {
#pragma HLS UNROLL
            const int oc = step*C1_OC+lane;
            acc1 products[128];
#pragma HLS ARRAY_PARTITION variable=products complete
            for (int t = 0; t < 128; ++t) {
#pragma HLS UNROLL
                if (t < 81) {
                    auto product = value.v[t]*weights[oc][t];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                    products[t] = product;
                } else products[t] = 0;
            }
            next[lane] = relu1(Reduction<128>::sum(products)+bias1(biases[oc]));
        }
        for (int c = 0; c < N1-C1_OC; ++c) {
#pragma HLS UNROLL
            result.v[c] = result.v[c+C1_OC];
        }
        for (int lane = 0; lane < C1_OC; ++lane) {
#pragma HLS UNROLL
            result.v[N1-C1_OC+lane] = next[lane];
        }
        if (step == T-1) out.write(result);
    }
}

static void conv1_stream(hls::stream<input> &in, hls::stream<pixel1> &out,
                         weight weights[N1][81], bias biases[N1]) {
#pragma HLS DATAFLOW
    hls::stream<window1> windows("windows1");
#pragma HLS STREAM variable=windows depth=2
#pragma HLS BIND_STORAGE variable=windows type=fifo impl=lutram
    windows1(in,windows);
    engine1(windows,out,weights,biases);
}
'''

C2 = r'''
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         weight weights[N2][N1], bias biases[N2]) {
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
'''

C3 = r'''
static void windows3(hls::stream<pixel2> &in, hls::stream<window3> &out) {
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
        window3 result;
#pragma HLS ARRAY_PARTITION variable=result.v complete
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
                    result.v[(r*5+c)*N2+ic] = window[r][c][ic];
                }
            }
        }
        if (y >= 4 && x >= 4) out.write(result);
    }
}

static void engine3(hls::stream<window3> &in, hls::stream<output> &out,
                     weight weights[N2][25], bias biases[N3]) {
    constexpr int COUNT = power2(C3_IC*25);
    window3 value;
    acc3 sum = 0;
#pragma HLS ARRAY_PARTITION variable=value.v complete
    continuous_c3_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) value = in.read();
        acc1 products[COUNT];
#pragma HLS ARRAY_PARTITION variable=products complete
        for (int index = 0; index < COUNT; ++index) {
#pragma HLS UNROLL
            if (index < C3_IC*25) {
                const int ic = step*C3_IC+index/25, tap = index%25;
                auto product = value.v[tap*N2+ic]*weights[ic][tap];
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
                         weight weights[N2][25], bias biases[N3]) {
#pragma HLS DATAFLOW
    hls::stream<window3> windows("windows3");
#pragma HLS STREAM variable=windows depth=2
#pragma HLS BIND_STORAGE variable=windows type=fifo impl=lutram
    windows3(in,windows);
    engine3(windows,out,weights,biases);
}
'''


def fifo_storage(text):
    return text.replace("#pragma HLS STREAM variable=features depth=4", "#pragma HLS STREAM variable=features depth=4\n#pragma HLS BIND_STORAGE variable=features type=fifo impl=lutram").replace(
        "#pragma HLS STREAM variable=features2 depth=4", "#pragma HLS STREAM variable=features2 depth=4\n#pragma HLS BIND_STORAGE variable=features2 type=fifo impl=lutram").replace(
        "#pragma HLS STREAM variable=padded3 depth=16", "#pragma HLS STREAM variable=padded3 depth=16\n#pragma HLS BIND_STORAGE variable=padded3 type=fifo impl=lutram")


def main():
    check_protected()
    for exp_id in ("F01", "F02", "F03", "F04", "F05", "F06", "F07"):
        if not list((ROOT / "experiments").glob(exp_id+"_*/plan.json")):
            raise RuntimeError("Missing paper plan")
    base = ROOT / "designs/dataflow_int"
    original = (base / "srcnn.cpp").read_text()
    for name in ("fifo_lutram_control", "uram_line_control", "continuous_direct"):
        target = ROOT / "designs" / name
        if target.exists():
            raise RuntimeError("Design exists")
        shutil.copytree(base,target)
        text = original
        if name == "fifo_lutram_control":
            text = fifo_storage(text)
        elif name == "uram_line_control":
            start = text.index("static void conv3_stream")
            text = text[:start]+text[start:].replace("variable=line type=ram_2p impl=bram", "variable=line type=ram_2p impl=uram",1)
        else:
            text = text.replace("using namespace numeric;", "using namespace numeric;\n"+REDUCE)
            start,end = text.index("static void conv1_stream"),text.index("static void conv12")
            text = text[:start]+PAD+C1+C2+text[end:]
            start,end = text.index("static void conv3_stream"),text.index("static void write_output")
            text = text[:start]+C3+text[end:]
            text = fifo_storage(text)
            text = text.replace("replicate_pad<input, 4>(raw, padded1);", "#if EXP_ONLINE_PAD\n    online_pad<input,4>(raw,padded1);\n#else\n    replicate_pad<input,4>(raw,padded1);\n#endif")
            text = text.replace("replicate_pad<pixel2, 2>(features2, padded3);", "#if EXP_ONLINE_PAD\n    online_pad<pixel2,2>(features2,padded3);\n#else\n    replicate_pad<pixel2,2>(features2,padded3);\n#endif")
        (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
