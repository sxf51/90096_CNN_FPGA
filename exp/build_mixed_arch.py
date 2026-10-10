#!/usr/bin/env python3
"""Generate the preplanned mixed Conv2 packing network as an independent source."""
import shutil
from run_exp import ROOT, check_protected


C2 = r'''
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         weight2 weights[N2][N1], weight2 biases[N2]) {
    constexpr int PAIRS = N2/(2*T);
    pixel1 value;
    pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    mixed_c2_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) value = in.read();
        act2 next[2*PAIRS];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < PAIRS; ++lane) {
#pragma HLS UNROLL
            const int oc = 2*(step*PAIRS+lane);
            acc1 first[64], second[64];
#pragma HLS ARRAY_PARTITION variable=first complete
#pragma HLS ARRAY_PARTITION variable=second complete
            for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
                const word<27> packed = word<27>(weights[oc][ic])*262144+word<27>(weights[oc+1][ic]);
#ifdef __SYNTHESIS__
                auto product = packed*value.v[ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
                const int64_t product = int64_t(packed)*value.v[ic];
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
'''

TYPES = r'''
namespace numeric {
using weight2 = word<8>;
using mixed_acc = word<21>;
static weight2 encode_weight2(float value) {
#pragma HLS INLINE
    using Q = ap_fixed<8,1,AP_RND_CONV,AP_SAT>;
    return raw_value<Q,8>(Q(value));
}
}
'''


def main():
    check_protected()
    for exp_id in ("C08", "C09"):
        if not list((ROOT / "experiments").glob(exp_id+"_*/plan.json")):
            raise RuntimeError("Missing immutable paper plan: "+exp_id)
    original = ROOT / "designs/winograd_continuous"
    target = ROOT / "designs/winograd_mixed_packing"
    if target.exists():
        raise RuntimeError("Design exists")
    shutil.copytree(original,target)
    text = (original / "srcnn.cpp").read_text()
    text = text.replace("using namespace numeric;", TYPES+"\nusing namespace numeric;",1)
    start = text.index("#if EXP_ALL_CONTINUOUS\n\nstatic void conv2_stream")
    end = text.index("static void conv12",start)
    text = text[:start]+C2+"\n"+text[end:]
    text = text.replace("weight w2[N2][N1], bias b2[N2]", "weight2 w2[N2][N1], weight2 b2[N2]")
    text = text.replace("static weight w1[N1][81], w2[N2][N1], w3[N2][25];",
                        "static weight w1[N1][81], w3[N2][25];\n    static weight2 w2[N2][N1];")
    text = text.replace("static bias b1[N1], b2[N2], b3[N3];",
                        "static bias b1[N1], b3[N3];\n    static weight2 b2[N2];")
    text = text.replace("encode_weight(weights2[", "encode_weight2(weights2[")
    text = text.replace("encode_weight(biases2[", "encode_weight2(biases2[")
    (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
