#!/usr/bin/env python3
"""Plan a runtime-loaded T4 W21 clone with once-per-frame Conv2 packing."""
import argparse
import json
import subprocess
import sys
from plan_arch import plan
from prepare_clock_variants import replace_once
from reproduce_exp import archived
from run_exp import ROOT, check_protected
import hashlib
import shutil


def build(config):
    archive = ROOT/"experiments"/(config["id"] + "_" + config["name"])
    subprocess.run(["git", "cat-file", "-e", "HEAD:" + str((archive/"plan.json").relative_to(ROOT))],
                   cwd=ROOT, check=True)
    if (archive/"metrics.json").exists() or (ROOT/config["design"]).exists():
        raise RuntimeError("Cannot overwrite an implemented or completed design")
    parent = archived("W21")
    source = parent/"source"
    expected = json.loads((parent/"config.json").read_text())["source_sha256"]
    actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.rglob("*") if path.is_file()}
    if actual != expected:
        raise RuntimeError("Frozen parent source mismatch")
    target = ROOT/config["design"]
    shutil.copytree(source, target)
    path = target/"srcnn.cpp"
    text = path.read_text()
    helpers = '''namespace numeric {
using weight2 = word<8>;
using mixed_acc = word<21>;
static weight2 encode_weight2(float value) {
#pragma HLS INLINE
    using Q = ap_fixed<8,1,AP_RND_CONV,AP_SAT>;
    return raw_value<Q,8>(Q(value));
}
}

'''
    text = replace_once(text, "using namespace numeric;", helpers + "using namespace numeric;")
    text = replace_once(text, "        const weight encoded = encode_weight(value);",
                        "        const weight encoded = i >= 5248 && i < 7328 ? weight(encode_weight2(value)) : encode_weight(value);")
    start = text.index("static void conv2_stream(", text.index("#if EXP_ALL_CONTINUOUS"))
    end = text.index("\n#else\nstatic void conv2_stream(", start)
    replacement = '''static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         hls::stream<weight> &params) {
    constexpr int PAIRS = N2/(2*T);
    static word<27> packed_weights[N2/2][N1];
    static weight2 biases[N2];
    weight2 first_row[N1];
#pragma HLS ARRAY_PARTITION variable=packed_weights cyclic factor=PAIRS dim=1
#pragma HLS ARRAY_PARTITION variable=packed_weights complete dim=2
#pragma HLS BIND_STORAGE variable=packed_weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=first_row complete
#pragma HLS ARRAY_PARTITION variable=biases complete
    packed_load_pairs: for (int pair = 0; pair < N2/2; ++pair) {
        packed_load_first: for (int ic = 0; ic < N1; ++ic) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            first_row[ic] = weight2(params.read());
        }
        packed_load_second: for (int ic = 0; ic < N1; ++ic) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const weight2 second = weight2(params.read());
            packed_weights[pair][ic] = word<27>(first_row[ic])*262144+word<27>(second);
        }
    }
    packed_load_bias: for (int i = 0; i < N2; ++i) {
#pragma HLS PIPELINE II=1
        for (int c = 0; c < N2-1; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[N2-1] = weight2(params.read());
    }
    pixel1 value;
    pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    continuous_c2_fold: for (int iteration = 0; iteration < H*W*T; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration%T;
        if (step == 0) value = in.read();
        act2 next[2*PAIRS];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < PAIRS; ++lane) {
#pragma HLS UNROLL
            const int pair = step*PAIRS+lane, oc = 2*pair;
            acc1 first[64], second[64];
#pragma HLS ARRAY_PARTITION variable=first complete
#pragma HLS ARRAY_PARTITION variable=second complete
            for (int ic = 0; ic < N1; ++ic) {
#pragma HLS UNROLL
#ifdef __SYNTHESIS__
                auto product = packed_weights[pair][ic]*value.v[ic];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
                const int64_t product = int64_t(packed_weights[pair][ic])*value.v[ic];
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
}'''
    text = text[:start] + replacement + text[end:]
    path.write_text(text)
    check_protected()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    check_protected()
    if args.build:
        build(json.loads((ROOT/"exp/configs"/(args.id + ".json")).read_text()))
        return
    parent = archived("W21")
    base = json.loads((parent/"plan.json").read_text())["configuration"]
    config = {**base, "id": args.id, "series": "C", "stage": "rom_clock_wsE",
              "name": "runtime_prepacked_conv2_T4", "design": "designs/winograd_prepacked_t4_v1",
              "control_experiment": "W21", "T": 4,
              "defines": {**base["defines"], "EXP_T": 4}, "clock": 4,
              "memory_scheduler": True, "resource_policy": "routed", "required_image_count": 13,
              "precision": "w10_8_10a10acc23_21_23", "set14": True,
              "reference": "experiments/E065_apfixed_mixed_conv2w8/butterfly_output.bin",
              "numpy_reference": "exp/numeric_reference/mixed_conv2w8/numpy_reference",
              "unroll": "G2 F2/once-loaded paired Cout signed8/direct Cin",
              "storage": "local_prepacked_lutram_s2p",
              "purpose": "WS-E early HLS screening while mainline clock/FIFO RTL controls run. "
                         "Use an independent runtime-loaded W21 clone atT4; keep Winograd Conv1 and direct "
                         "Conv3 exact10-bit, replace only Conv2 with E065's independently validated "
                         "signed8-bit weights/bias and21-bit accumulator. Pack each coefficient pair once "
                         "during its private parameter load, removing packing arithmetic from every pixel. "
                         "Unpack each37-bit27x10 product separately with signed-low borrow repair. "
                         "This is precision-exact against E065, not the uniform10-bit E017. "
                         "No route launch until DSP<=1100 and LUT<=170k and memory admission permits it.",
              "changes": "Copy frozen W21 only after committing the paper estimate. T=4, Conv2-only "
                         "8-bit quantization in the shared reader, private27-bit packed coefficient banks "
                         "and the verified per-product signed unpacking. Keep parameters bundle and token "
                         "counts8129/640/2080/801, padding and full-float top signature.",
              "estimates": {"DSP": 1032, "Conv1_DSP": 576, "Conv2_DSP": 256, "Conv3_DSP": 200,
                            "BRAM18K": 146, "URAM": 0, "T": 4, "LUT": 150000, "FF": 220000,
                            "latency_cycles": 292000,
                            "basis": "576=2304/4 Conv1,256=2048/(4*2) Conv2 packed pairs,200=800/4 "
                                     "Conv3 DSPs. Retain nine input/36 Conv3/raster buffering at approximately "
                                     "146BRAM18K.27-bit paired storage1024*27=27648bits replaces2048*8=16384 "
                                     "Conv2 bits, with256banked read ports and512bit first-row cache. "
                                     "C11 HLS measured1036DSP/198436LUT/231297FF/276979cycles with old top "
                                     "weight/load paths. W21 streamed/private banks reduce outside logic, "
                                     "but T4 controls and unpacking remain; budget150kLUT/220kFF without "
                                     "claiming routed feasibility. Nominal128*128*16=262144 foldcycles plus "
                                     "about30k startup/FIFO allowance gives292000 RTL estimate. If5-6ns "
                                     "closes, hypothesized1.46-1.752ms IP frame time; neither is measured."},
              "interpretation": "Compare all13 exact E065 references and mixed border/PSNR gates, then "
                                "parse layer DSPs, private packed bank ports, load overhead, foldII and "
                                "resources versus C11/W21. Explain deviations above20%. Integer packing "
                                "has no residual approximation and no multi-product low-field overflow.",
              "conclusion": "Continue to finite-FIFO RTL/routing only after the preplanned screen. "
                            "Stop at routed resource failure or a slower measured frame product than T8; "
                            "preserve runtime loading and the currently accepted W21 fallback."}
    config.pop("synthesis_after", None)
    config.pop("quality_reference", None)
    plan(config)
    subprocess.run([sys.executable, str(ROOT/"exp/commit_exp.py"), args.id,
                    "plan_runtime_prepacked_T4"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
