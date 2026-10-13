#!/usr/bin/env python3
"""Preplan independent W21 clock/FIFO controls before copying frozen sources."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from reproduce_exp import archived
from run_exp import ROOT, check_protected


VARIANTS = {
    "frp": ("winograd_frp_v1", "rom_clock_wsC2", 644, 146, 85000, 140000, 558758,
            "Change only the three continuous MAC fold pipelines to style=frp. "
            "Hypothesis: remove the global stall-enable distribution identified in W22's Conv3 "
            "956-fanout path without changing any arithmetic or FIFO token counts.",
            "Keep 288/256/100 DSPs and146 BRAM18K; allow approximately3914 additional LUT and9943 FF "
            "for free-running valid/flush control. RTL latency is expected within1% of F97's558758, "
            "but finite-FIFO backpressure and FRP support must be tested. Target4.5ns only in a later "
            "independent implementation, never infer clock closure from HLS."),
    "c3_select": ("winograd_c3_select_reg_v1", "rom_clock_wsC3", 644, 146, 83000, 133000, 558760,
                  "Insert one registered activation/coefficient pair before each of Conv3's100 DSP "
                  "multipliers. Keep the original pipeline style, all other layers, fold tags and arithmetic. "
                  "Hypothesis: split the step-controlled channel selection from the DSP input path.",
                  "Keep288/256/100 DSPs,146 BRAM18K andzeroURAM.100 pairs of10-bit values add2000 data "
                  "FF plus validity/control, budget2943 FF and1914 LUT above W21. One selection register "
                  "stage should add only startup/drain cycles atII1, within1% of558758. The native integer "
                  "C model remains unchanged; require actual synthesized register/latency evidence."),
    "fifo16": ("winograd_feature_fifo16_v1", "rom_clock_wsD1", 644, 146, 81500, 130500, 550000,
               "Change only the Conv1-to-Conv2 conv1_features LUTRAM FIFO depth from4 to16. "
               "Measure whether extra buffering reduces F97's finite-FIFO stalls and558758-cycle latency.",
               "Keep644 DSPs/146 BRAM18K.12 extra640-bit entries add7680bits, approximately120 LUT6 "
               "storage bits at64bits/LUT, plus control; reserve414 LUT/443FF. Nominal T8 Winograd "
               "fold is524288cycles. Paper RTL estimate550000 allows about8758cycles recovery; the "
               "WS-D target is at most1.02*525237=535741.74cycles and only RTL can establish it."),
    "fifo32": ("winograd_feature_fifo32_v1", "rom_clock_wsD1", 644, 146, 81750, 130750, 543000,
               "Change only conv1_features LUTRAM FIFO depth from4 to32. Compare against both "
               "unchanged W21 and the separately measured16-entry control.",
               "Keep644 DSPs/146 BRAM18K.28 extra640-bit entries add17920bits, about280 LUT6 at64bits/LUT "
               "plus control; reserve664LUT/693FF. Estimate543000 RTL cycles, not HLS cycles. Maximum "
               "recoverable F97 overestimate is33521cycles, approximately6%; only profiling/RTL can "
               "support the target at most535741.74cycles."),
    "reorder": ("winograd_reorder_buffer_v1", "rom_clock_wsD2", 644, 146, 84100, 131000, 540000,
                "Keep the original4-entry inter-layer FIFO and add a256-entry LUTRAM buffer after "
                "reorder_rows with an independent forwarding process. Test row-burst decoupling "
                "without changing raster order or adding a full-frame feature map.",
                "Keep644DSP/146BRAM18K/zeroURAM.256*640=163840 extra FIFO bits cost approximately2560 "
                "LUT6 at64bits/LUT plus pointers/forwarding; budget3014LUT/943FF. Estimate540000 RTL "
                "cycles; parent33521-cycle FIFO/startup excess is the absolute upper recovery bound. "
                "Require all13 images and changed-parameter two-frame finite-FIFO RTL evidence."),
    "windows16": ("winograd_window_fifo16_v1", "rom_clock_wsD3", 644, 146, 81650, 130600, 535500,
                  "Change only the transformed-window FIFO in conv1_stream from2 to16 LUTRAM entries. "
                  "F97's windows_U records45974 read-block cycles over two frames, while wino_engine "
                  "has zero write stalls and its fold takes547283 rather than524288 nominal cycles. "
                  "Hypothesis: a deeper window lookahead covers the no-tile scan row between paired tile rows, "
                  "which a deeper raster feature FIFO may not address.",
                  "Keep288/256/100 DSPs and146 BRAM18K;14 additional9*16*12-bit windows store24192bits, "
                  "about378LUT6 at64bits/LUT plus control. Budget564LUT/543FF. At4*T=32cycles per "
                  "tile,16 buffered tiles cover512 compute cycles versus a roughly264-cycle row-scan "
                  "gap, whereas2 entries cover64cycles. F97's22995 excess fold cycles closely match "
                  "45974/2=22987 window-read blocks per frame. Predict558758-22995=535763cycles, "
                  "rounded535500 as a testable estimate; the2% target535741.74 is deliberately marginal. "
                  "Counter totals overlap across processes and are not independently additive."),
}


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError("Frozen parent edit anchor is not unique: " + old[:80])
    return text.replace(old, new)


def build(config, parent):
    plans = list((ROOT/"experiments").glob(config["id"] + "_*/plan.json"))
    if len(plans) != 1:
        raise RuntimeError("Expected one committed variant plan")
    archive = plans[0].parent
    if (archive/"metrics.json").exists():
        raise RuntimeError("Completed IDs cannot be implemented or rerun")
    subprocess.run(["git", "cat-file", "-e", "HEAD:" + str((archive/"plan.json").relative_to(ROOT))],
                   cwd=ROOT, check=True)
    target = ROOT/config["design"]
    if target.exists():
        raise RuntimeError("Independent design already exists")
    source = parent/"source"
    expected = json.loads((parent/"config.json").read_text())["source_sha256"]
    actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.rglob("*") if path.is_file()}
    if actual != expected:
        raise RuntimeError("Frozen W21 source mismatch")
    shutil.copytree(source, target)
    path = target/"srcnn.cpp"
    text = path.read_text()
    variant = config["clock_variant"]
    if variant == "frp":
        for label, bound in (("wino", "TILE_H*TILE_W*4*T"), ("c2", "H*W*T"), ("c3", "H*W*T")):
            old = "continuous_" + label + "_fold: for (int iteration = 0; iteration < " + bound + "; ++iteration) {\n#pragma HLS PIPELINE II=1"
            text = replace_once(text, old, old + " style=frp")
    elif variant == "c3_select":
        helper = '''struct c3_operands { act2 activation; weight coefficient; };

static c3_operands register_c3_operands(act2 activation, weight coefficient) {
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
#pragma HLS LATENCY min=1 max=1
    c3_operands result;
    result.activation = activation;
    result.coefficient = coefficient;
    return result;
}

'''
        text = replace_once(text, "static void engine3(", helper + "static void engine3(")
        old = "                auto product = (ic < N2/2 ? value0.v[tap*(N2/2)+ic] : value1.v[tap*(N2/2)+ic-N2/2])*weights[ic][tap];"
        new = '''                const c3_operands operands = register_c3_operands(
                    ic < N2/2 ? value0.v[tap*(N2/2)+ic] : value1.v[tap*(N2/2)+ic-N2/2], weights[ic][tap]);
                auto product = operands.activation*operands.coefficient;'''
        text = replace_once(text, old, new)
    elif variant == "windows16":
        text = replace_once(text, "#pragma HLS STREAM variable=windows depth=2",
                            "#pragma HLS STREAM variable=windows depth=16")
    elif variant in {"fifo16", "fifo32"}:
        text = replace_once(text, "#pragma HLS STREAM variable=features depth=4",
                            "#pragma HLS STREAM variable=features depth=" + variant[4:])
    elif variant == "reorder":
        helper = '''static void forward_raster(hls::stream<pixel1> &in, hls::stream<pixel1> &out) {
    forward_pixels: for (int p = 0; p < H*W; ++p) {
#pragma HLS PIPELINE II=1
        out.write(in.read());
    }
}

'''
        text = replace_once(text, "static void conv1_stream(", helper + "static void conv1_stream(")
        text = replace_once(text, '    hls::stream<tile_block> tiles("wino_tile_blocks");',
                            '    hls::stream<tile_block> tiles("wino_tile_blocks");\n'
                            '    hls::stream<pixel1> raster("buffered_raster");\n'
                            '#pragma HLS STREAM variable=raster depth=256\n'
                            '#pragma HLS BIND_STORAGE variable=raster type=fifo impl=lutram')
        text = replace_once(text, "    reorder_rows(top,bottom,out);",
                            "    reorder_rows(top,bottom,raster);\n    forward_raster(raster,out);")
    else:
        raise RuntimeError("Unsupported variant")
    path.write_text(text)
    check_protected()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--variant", choices=VARIANTS)
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    check_protected()
    parent = archived("W21")
    if args.build:
        config = json.loads((ROOT/"exp/configs"/(args.id + ".json")).read_text())
        build(config, parent)
        return
    if not args.variant:
        parser.error("--variant is required when planning")
    design, stage, dsp, bram, lut, ff, cycles, purpose, basis = VARIANTS[args.variant]
    base = json.loads((parent/"plan.json").read_text())["configuration"]
    config = {**base, "id": args.id, "name": args.variant + "_W21_T8",
              "series": args.id[0], "stage": stage, "scope": "frame",
              "design": "designs/" + design, "control_experiment": "W21",
              "clock_variant": args.variant, "memory_scheduler": True,
              "required_image_count": 13, "resource_policy": "routed",
              "set14": True, "numpy_reference": "exp/numeric_reference/w10a10/numpy_reference",
              "purpose": purpose + " Runtime weights, w10a10acc23, replicate padding and srcnn signature "
                         "remain the frozen W21 contract. This is a separately measurable mainline control.",
              "changes": "Independent frozen W21 copy after committing the paper plan. " + purpose,
              "estimates": {"DSP": dsp, "Conv1_DSP": 288, "Conv2_DSP": 256, "Conv3_DSP": 100,
                            "BRAM18K": bram, "URAM": 0, "T": 8, "LUT": lut, "FF": ff,
                            "latency_cycles": cycles,
                            "basis": "W21 HLS baseline644DSP/146BRAM18K/81086LUT/130057FF/525237cycles; "
                                     "F97 RTL558758cycles, W22 independent4.95ns route. " + basis},
              "interpretation": "Compare HLS resource/II/schedule evidence and separately measured RTL "
                                "cycles with the committed estimates and unchanged W21. Explain deviations "
                                "above20%. No target-clock closure, finite-FIFO performance or board claim "
                                "is justified before the corresponding measurements.",
              "conclusion": "Screen at HLS DSP<=1100, LUT<=160k, FF<=230k; final acceptance requires "
                            "independent routed gates and exact changed-parameter RTL. Keep W21/W22 fallback."}
    config.pop("synthesis_after", None)
    config.pop("quality_reference", None)
    plan(config)
    subprocess.run([sys.executable, str(ROOT/"exp/commit_exp.py"), args.id,
                    "plan_" + args.variant + "_W21"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
