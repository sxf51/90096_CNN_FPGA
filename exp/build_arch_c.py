#!/usr/bin/env python3
"""Compose independently archived exact P and W engines."""
import shutil
from build_arch_p import C3, HELPERS
from run_exp import ROOT, check_protected


def main():
    check_protected()
    for exp_id in ("C01", "C02", "C03"):
        if not list((ROOT / "experiments").glob(exp_id+"_*/plan.json")):
            raise RuntimeError("Missing paper plan")
    source = ROOT / "designs/winograd_network"
    target = ROOT / "designs/combination_network"
    if target.exists():
        raise RuntimeError("Design exists")
    shutil.copytree(source,target)
    text = (source / "srcnn.cpp").read_text()
    text = text.replace("using namespace numeric;", "using namespace numeric;\n"+HELPERS)
    start,end = text.index("static void conv2_stream"),text.index("static void conv12")
    packed = (ROOT / "designs/packing_network/srcnn.cpp").read_text()
    pstart,pend = packed.index("static void conv2_stream"),packed.index("static void conv12")
    text = text[:start]+"#if EXP_PACK_C2\n"+packed[pstart:pend]+"#else\n"+text[start:end]+"#endif\n"+text[end:]
    start,end = text.index("static void conv3_stream"),text.index("static void write_output")
    text = text[:start]+C3+"\n"+text[end:]
    text = text.replace("x < W + 2 * Radius + (Radius == 4 ? 1 : 0)","x < W + 2 * Radius + 1")
    text = text.replace("factor=C3_IC dim=1","factor=(N2/(2*T)) dim=1")
    text = text.replace("#pragma HLS STREAM variable=bottom depth=512", "#pragma HLS STREAM variable=bottom depth=512\n#if EXP_ROW_LUTRAM\n"
                        "#pragma HLS BIND_STORAGE variable=top type=fifo impl=lutram\n"
                        "#pragma HLS BIND_STORAGE variable=bottom type=fifo impl=lutram\n#endif")
    (target / "srcnn.cpp").write_text(text)
    check_protected()


if __name__ == "__main__":
    main()
