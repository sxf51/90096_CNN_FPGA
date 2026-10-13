#!/usr/bin/env python3
"""Plan independent WS-H register/tree variants from a measured WS-G parent."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from prepare_clock_variants import replace_once
from reproduce_exp import archived
from rtl_acceptance import accepted_cosim
from run_exp import ROOT, check_protected, number
from verify_exp import check_image_validation, screened_parent


def source_hashes(folder):
    return {str(path.relative_to(folder)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in folder.rglob("*") if path.is_file()}


def parent_evidence(parent_id, rtl_id):
    parent = archived(parent_id)
    config = json.loads((parent / "config.json").read_text())
    metrics = json.loads((parent / "metrics.json").read_text())
    check_image_validation(config, config)
    if (config.get("top") != "srcnn_reload" or config.get("T") != 4 or
            config.get("precision") != "w10_8_10a10acc23_21_23" or
            not screened_parent({"resource_policy": "routed"}, metrics, config)):
        raise RuntimeError("WS-H requires a complete, screened, mixed-T4 reload parent")
    rtl = archived(rtl_id)
    rtl_config = json.loads((rtl / "config.json").read_text())
    rtl_metrics = json.loads((rtl / "metrics.json").read_text())
    proof = rtl_config.get("verification", {})
    if (rtl_config.get("verify_parent") != parent_id or
            not accepted_cosim(rtl_metrics, rtl_config) or
            proof.get("reload_switch_bit_exact") is not True or
            proof.get("skip_parameter_axi_zero") is not True):
        raise RuntimeError("WS-H requires the matching four-call exact, zero-AXI RTL parent")
    return parent, config, metrics, proof


def generate(text, variant):
    anchor = "struct transformed_params1 { transformed_weight v[16]; };\n"
    if variant == "paramreg":
        helper = """
static transformed_params1 params1_write_register(transformed_params1 value) {
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
#pragma HLS LATENCY min=1 max=1
    return value;
}
"""
        text = replace_once(text, anchor, anchor + helper)
        old = """            const transformed_params1 packet = params.read();
            for (int tap = 0; tap < 16; ++tap) {
#pragma HLS UNROLL
                weights[oc][group][tap] = packet.v[tap];
"""
        return replace_once(text, old, old.replace(
            "params.read()", "params1_write_register(params.read())"))
    helper = """
template<int Count> struct WinoReduction {
    static inverse sum(inverse values[Count]) {
#pragma HLS INLINE
        inverse next[Count/2];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int i = 0; i < Count/2; ++i) {
#pragma HLS UNROLL
            inverse value = values[2*i] + values[2*i+1];
#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1
            next[i] = value;
        }
        return WinoReduction<Count/2>::sum(next);
    }
};
template<> struct WinoReduction<1> {
    static inverse sum(inverse values[1]) {
#pragma HLS INLINE
        return values[0];
    }
};
"""
    text = replace_once(text, anchor, anchor + helper)
    start = """                inverse sum = 0;
                for (int group = 0; group < 9; ++group) {
"""
    text = replace_once(text, start, """                inverse products[16];
#pragma HLS ARRAY_PARTITION variable=products complete
                for (int group = 0; group < 9; ++group) {
""")
    finish = """                    sum = wino::add<EXP_W_BITS+EXP_A_BITS+14>(sum,inverse(product));
                }
                m[j] = sum;
"""
    return replace_once(text, finish, """                    products[group] = inverse(product);
                }
                for (int group = 9; group < 16; ++group) {
#pragma HLS UNROLL
                    products[group] = 0;
                }
                m[j] = WinoReduction<16>::sum(products);
""")


def build(config):
    archive = ROOT / "experiments" / (config["id"] + "_" + config["name"])
    subprocess.run(["git", "cat-file", "-e", "HEAD:" + str(
        (archive / "plan.json").relative_to(ROOT))], cwd=ROOT, check=True)
    parent, observed, _, _ = parent_evidence(config["control_experiment"], config["parent_rtl"])
    target = ROOT / config["design"]
    if target.exists() or (archive / "metrics.json").exists():
        raise RuntimeError("New timing design or completed archive already exists")
    source = parent / "source"
    if source_hashes(source) != observed["source_sha256"]:
        raise RuntimeError("Frozen timing parent source mismatch")
    shutil.copytree(source, target)
    path = target / "srcnn.cpp"
    path.write_text(generate(path.read_text(), config["timing_variant"]))
    expected = dict(observed["source_sha256"])
    expected["srcnn.cpp"] = hashlib.sha256(path.read_bytes()).hexdigest()
    if source_hashes(target) != expected:
        raise RuntimeError("Timing source differs outside its planned srcnn.cpp change")
    check_protected()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--parent")
    parser.add_argument("--parent-rtl")
    parser.add_argument("--variant", choices=("paramreg", "balanced"))
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    check_protected()
    if args.build:
        build(json.loads((ROOT / "exp/configs" / (args.id + ".json")).read_text()))
        return
    if not args.parent or not args.parent_rtl or not args.variant:
        parser.error("A plan requires --parent, --parent-rtl and --variant")
    parent, observed, metrics, proof = parent_evidence(args.parent, args.parent_rtl)
    base = json.loads((parent / "plan.json").read_text())["configuration"]
    estimates = {key: number(metrics[key]) for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF")}
    overhead_ff = 256 if args.variant == "paramreg" else 32640
    overhead_lut = 256 if args.variant == "paramreg" else 2048
    cycles = proof["reload_switch_transactions"]
    loaded = max(item["latency_cycles"] for item in cycles if item["load_params"])
    reuse = max(item["latency_cycles"] for item in cycles if not item["load_params"])
    extra_cycles = 128 if args.variant == "paramreg" else 4
    detail = ("One224-bit transformed packet register plus32controlFF; fixed one-cycle, II1 "
              "helper between params1 and private bank writes. Budget256LUT and128loaded "
              "cycles for channel-loop drains; skipped calls never enter the helper. Check "
              "the generated helper's actual registered return before claiming the stage."
              if args.variant == "paramreg" else
              "Nine full products padded to16; four registered fabric-add levels at34bits. "
              "A conservative full16-leaf tree budget is4lanes*16transform taps*15nodes*34="
              "32640extraFF; constant-zero pruning should reduce this, and old scheduler "
              "registers may be reused. Budget2048additionalLUT for rescheduling/control. "
              "The multiply count and complete34-bit inverse/shift2 quantization stay fixed. "
              "Only four startup/drain cycles are predicted, assuming all fold II remain1.")
    estimates.update(T=4, LUT=estimates["LUT"] + overhead_lut, FF=estimates["FF"] + overhead_ff,
                     latency_cycles=loaded + extra_cycles, loaded_cycles=loaded + extra_cycles,
                     reuse_cycles=reuse + (0 if args.variant == "paramreg" else extra_cycles),
                     Conv1_DSP=576, Conv2_DSP=256, Conv3_DSP=200,
                     basis="Measured " + args.parent + " HLS counts and matching " + args.parent_rtl +
                           " four-call zero-parameter-AXI RTL cycles. " + detail +
                           " Retain146BRAM18K/zeroURAM/1032DSP. MAC lower bound65025*4="
                           "260100cycles. Independent4.5ns routing is required; no clock "
                           "closure or board time is assumed. Per-call upper bound is the "
                           "matching parent latency*101//100; faster results remain accepted.")
    config = {**base, "id": args.id, "name": "t4_reload_" + args.variant,
              "series": args.id[0], "stage": "rom_clock_wsH2" if args.variant == "paramreg" else "rom_clock_wsH3",
              "design": "designs/winograd_t4_reload_" + args.variant + "_v1",
              "control_experiment": args.parent, "parent_rtl": args.parent_rtl,
              "timing_variant": args.variant, "set14": True, "csim_only": False,
              "estimates": estimates,
              "purpose": "WS-H independent " + args.variant + " probe: " + detail +
                         " Use a new frozen " + args.parent + " copy; preserve the other timing path, "
                         "FIFO32, runtime float-array interface, guarded reload, precision and replicate "
                         "padding. Require all13 E065-exact images, per-call <=parent+1percent RTL, "
                         "four-call changed-parameter/zero-AXI evidence and independent physical gates.",
              "changes": "Only srcnn.cpp " + ("adds a one-cycle noninlined parameter-write helper."
                         if args.variant == "paramreg" else "replaces the nine-item linear sum with a full-width registered balanced tree."),
              "interpretation": "Compare parsed HLS, RTL and routed metrics with the pre-implementation "
                                "budget, explain deviations above20percent and inspect actual pipeline "
                                "registers plus final five setup paths. No unchanged path is presumed fixed.",
              "conclusion": "After C/HLS gates, independently verify four RTL calls and route4.5ns. "
                            "Only a closed4.5ns point may receive a separate4ns plan. Preserve the "
                            "verified5ns fallback and do not combine these probes prematurely."}
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id,
                    "plan_" + config["name"]], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
