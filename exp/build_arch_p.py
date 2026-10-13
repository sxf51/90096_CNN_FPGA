#!/usr/bin/env python3
"""Generate the exact ten-bit packing network from its committed plans."""
import shutil
from run_exp import ROOT, check_protected

HELPERS = r'''
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
'''

C1_BODY = r'''
                constexpr int PAIRS = N1/(2*T);
                c1_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < PAIRS; ++lane) {
#pragma HLS UNROLL
                        const int oc = 2*(step*PAIRS+lane);
                        acc1 first = bias1(biases[oc]), second = bias1(biases[oc+1]);
                        for (int tap = 0; tap < 81; ++tap) {
#pragma HLS UNROLL
                            acc1 p0, p1;
                            pair_weights(weights[oc][tap],weights[oc+1][tap],window[tap/9][tap%9],p0,p1);
                            first += p0;
                            second += p1;
                        }
                        result.v[oc] = relu1(first);
                        result.v[oc+1] = relu1(second);
                    }
                }
'''

C2_BODY = r'''
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
'''

C3 = r'''
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
'''


def main():
    check_protected()
    for exp_id in ("P10", "P11", "P12"):
        if not list((ROOT / "experiments").glob(exp_id + "_*/plan.json")):
            raise RuntimeError("Missing pre-implementation plan")
    target = ROOT / "designs/packing_network"
    if target.exists():
        raise RuntimeError("Design exists")
    shutil.copytree(ROOT / "designs/dataflow_int", target)
    text = (target / "srcnn.cpp").read_text()
    text = text.replace("using namespace numeric;", "using namespace numeric;\n" + HELPERS)
    start = text.index("#if EXP_C1_SPLIT")
    end = text.index("#endif", start)+len("#endif")
    text = text[:start]+C1_BODY+text[end:]
    start = text.index("#if EXP_C2_SPLIT")
    end = text.index("#endif", start)+len("#endif")
    text = text[:start]+C2_BODY+text[end:]
    start = text.index("static void conv3_stream")
    end = text.index("static void write_output", start)
    text = text[:start]+C3+"\n"+text[end:]
    text = text.replace("x < W + 2 * Radius", "x < W + 2 * Radius + (Radius == 2 ? 1 : 0)")
    text = text.replace("factor=C3_IC dim=1", "factor=(N2/(2*T)) dim=1")
    (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
