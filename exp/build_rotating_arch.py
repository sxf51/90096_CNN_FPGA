#!/usr/bin/env python3
"""Generate a separate held-window rotation experiment from the frozen control."""
import shutil
from run_exp import ROOT, check_protected

ENGINE = r'''static void engine3(hls::stream<window3> &in0, hls::stream<window3> &in1, hls::stream<output> &out,
                     weight weights[N2][25], bias biases[N3]) {
    constexpr int COUNT = power2(C3_IC*25);
    act2 held[25][N2];
    acc3 sum = 0;
#pragma HLS ARRAY_PARTITION variable=held complete dim=0
    continuous_c3_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) {
            const window3 low = in0.read(), high = in1.read();
            for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                for (int ic = 0; ic < N2; ++ic) {
#pragma HLS UNROLL
                    held[tap][ic] = ic < N2/2 ? low.v[tap*(N2/2)+ic]
                                            : high.v[tap*(N2/2)+ic-N2/2];
                }
            }
        }
        acc1 products[COUNT];
#pragma HLS ARRAY_PARTITION variable=products complete
        for (int index = 0; index < COUNT; ++index) {
#pragma HLS UNROLL
            if (index < C3_IC*25) {
                const int lane = index/25, tap = index%25;
                auto product = held[tap][lane]*weights[step*C3_IC+lane][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                products[index] = product;
            } else products[index] = 0;
        }
        const acc1 partial = Reduction<COUNT>::sum(products);
        acc3 next = (step == 0 ? bias3(biases[0]) : sum)+partial;
#pragma HLS BIND_OP variable=next op=add impl=fabric latency=1
        sum = next;
        if (step == T-1) out.write(quantize<EXP_W_BITS-2>(next));
        // Ascending channel order reads each source before that source is changed.
        for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
            for (int ic = 0; ic < N2-C3_IC; ++ic) {
#pragma HLS UNROLL
                held[tap][ic] = held[tap][ic+C3_IC];
            }
            for (int ic = N2-C3_IC; ic < N2; ++ic) {
#pragma HLS UNROLL
                held[tap][ic] = 0;
            }
        }
    }
}
'''


def main():
    check_protected()
    source = ROOT / "designs/continuous_direct_r2"
    target = ROOT / "designs/continuous_rotate_v1"
    if target.exists():
        raise RuntimeError("Rotating design already exists; use a new design name")
    shutil.copytree(source,target)
    path = target / "srcnn.cpp"
    text = path.read_text()
    start = text.index("static void engine3(")
    end = text.index("\nstatic void conv3_stream(",start)
    text = text[:start]+ENGINE+text[end:]
    text = text.replace("struct window1 {", "#ifndef EXP_TREE_ADD_LATENCY\n#define EXP_TREE_ADD_LATENCY 1\n#endif\nstatic_assert(EXP_TREE_ADD_LATENCY == 0 || EXP_TREE_ADD_LATENCY == 1, \"Supported reduction latency\");\nstruct window1 {",1)
    text = text.replace("#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1",
                        "#if EXP_TREE_ADD_LATENCY == 0\n#pragma HLS BIND_OP variable=value op=add impl=fabric latency=0\n#else\n#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1\n#endif",1)
    path.write_text(text)
    check_protected()
    print(target)


if __name__ == "__main__":
    main()
