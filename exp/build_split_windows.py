#!/usr/bin/env python3
"""Generate independent legal-width window channels for the committed retries."""
import shutil
from build_arch_f import C3
from prepare_split_windows import CASES
from run_exp import ROOT, check_protected


def split_kernel():
    text = C3.replace("hls::stream<window3> &out)",
                      "hls::stream<window3> &out0, hls::stream<window3> &out1)",1)
    text = text.replace("window3 result;", "window3 result0, result1;",1)
    text = text.replace("#pragma HLS ARRAY_PARTITION variable=result.v complete",
                        "#pragma HLS ARRAY_PARTITION variable=result0.v complete\n#pragma HLS ARRAY_PARTITION variable=result1.v complete",1)
    text = text.replace("result.v[(r*5+c)*N2+ic] = window[r][c][ic];",
                        "if (ic < N2/2) result0.v[(r*5+c)*(N2/2)+ic] = window[r][c][ic];\n"
                        "                    else result1.v[(r*5+c)*(N2/2)+ic-N2/2] = window[r][c][ic];",1)
    text = text.replace("if (y >= 4 && x >= 4) out.write(result);",
                        "if (y >= 4 && x >= 4) {\n            out0.write(result0);\n            out1.write(result1);\n        }",1)
    text = text.replace("static void engine3(hls::stream<window3> &in,", "static void engine3(hls::stream<window3> &in0, hls::stream<window3> &in1,",1)
    text = text.replace("window3 value;", "window3 value0, value1;",1)
    text = text.replace("#pragma HLS ARRAY_PARTITION variable=value.v complete",
                        "#pragma HLS ARRAY_PARTITION variable=value0.v complete\n#pragma HLS ARRAY_PARTITION variable=value1.v complete",1)
    text = text.replace("if (step == 0) value = in.read();",
                        "if (step == 0) { value0 = in0.read(); value1 = in1.read(); }",1)
    text = text.replace("value.v[tap*N2+ic]",
                        "(ic < N2/2 ? value0.v[tap*(N2/2)+ic] : value1.v[tap*(N2/2)+ic-N2/2])",1)
    start = text.index('    hls::stream<window3> windows("windows3");')
    text = text[:start]+r'''
    hls::stream<window3> windows0("windows3_low_channels"), windows1("windows3_high_channels");
#pragma HLS STREAM variable=windows0 depth=2
#pragma HLS STREAM variable=windows1 depth=2
#pragma HLS BIND_STORAGE variable=windows0 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=windows1 type=fifo impl=lutram
    windows3(in,windows0,windows1);
    engine3(windows0,windows1,out,weights,biases);
}
'''
    return text


def main():
    check_protected()
    for exp_id,_,_ in CASES:
        if not list((ROOT / "experiments").glob(exp_id+"_*/plan.json")):
            raise RuntimeError("Missing immutable paper plan: "+exp_id)
    new_kernel = split_kernel()
    for base,name in (("continuous_direct","continuous_direct_r2"),
                      ("winograd_continuous","winograd_continuous_r2"),
                      ("winograd_mixed_packing","winograd_mixed_packing_r2")):
        original = ROOT / "designs" / base
        target = ROOT / "designs" / name
        if target.exists():
            raise RuntimeError("Design exists")
        shutil.copytree(original,target)
        text = (original / "srcnn.cpp").read_text()
        if text.count(C3) != 1:
            raise RuntimeError("Unexpected frozen continuous kernel shape")
        text = text.replace(C3,new_kernel,1)
        text = text.replace("struct window3 { act2 v[800]; };", "struct window3 { act2 v[400]; };",1)
        (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
