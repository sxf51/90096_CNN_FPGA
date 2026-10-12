#!/usr/bin/env python3
"""Preplan and independently build the user-requested FIFO/FRP combinations."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from plan_arch import plan
from prepare_clock_variants import replace_once
from reproduce_exp import archived
from run_exp import ROOT, check_protected


def build(config):
    if not list((ROOT/"experiments").glob("C15_*/metrics.json")):
        raise RuntimeError("User requested waiting for C15's result before implementing combinations")
    archive = ROOT/"experiments"/(config["id"]+"_"+config["name"])
    subprocess.run(["git", "cat-file", "-e", "HEAD:"+str((archive/"plan.json").relative_to(ROOT))],
                   cwd=ROOT, check=True)
    if (archive/"metrics.json").exists() or (ROOT/config["design"]).exists():
        raise RuntimeError("Combination workspace/design already exists")
    parent = archived(config["control_experiment"])
    source = parent/"source"
    expected = json.loads((parent/"config.json").read_text())["source_sha256"]
    actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.rglob("*") if path.is_file()}
    if actual != expected:
        raise RuntimeError("Frozen combination parent source mismatch")
    target = ROOT/config["design"]
    shutil.copytree(source, target)
    path = target/"srcnn.cpp"
    text = path.read_text()
    if config["combination_variant"] == "t8_fifo_frp":
        for label, bound in (("wino", "TILE_H*TILE_W*4*T"), ("c2", "H*W*T"), ("c3", "H*W*T")):
            old = ("continuous_"+label+"_fold: for (int iteration = 0; iteration < "+bound+
                   "; ++iteration) {\n#pragma HLS PIPELINE II=1")
            text = replace_once(text, old, old+" style=frp")
        if text.count("#pragma HLS STREAM variable=windows depth=16") != 1:
            raise RuntimeError("Frozen T8 parent does not contain its verified16-entry window FIFO")
    else:
        text = replace_once(text, "#pragma HLS STREAM variable=windows depth=2",
                            "#pragma HLS STREAM variable=windows depth=32")
    path.write_text(text)
    check_protected()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--variant", choices=("t8_fifo_frp", "t4_fifo"))
    parser.add_argument("--build", action="store_true")
    args = parser.parse_args()
    check_protected()
    if args.build:
        build(json.loads((ROOT/"exp/configs"/(args.id+".json")).read_text()))
        return
    if not args.variant:
        parser.error("--variant is required for a paper plan")
    t8 = args.variant == "t8_fifo_frp"
    parent_id = "F47" if t8 else "C13"
    parent = archived(parent_id)
    base = json.loads((parent/"plan.json").read_text())["configuration"]
    measured = json.loads((parent/"metrics.json").read_text())
    estimates = {key: measured[key] for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF")}
    estimates.update(T=8 if t8 else 4, latency_cycles=535771 if t8 else 272000)
    if t8:
        estimates.update(Conv1_DSP=288, Conv2_DSP=256, Conv3_DSP=100, LUT=82050, FF=131000,
                         basis="F47/F48 windowFIFO16 exact535771 RTL cycles; W27/W28 FRP exact549438. "
                               "Both remove transformed-window stalls, so savings cannot be added as proven "
                               "benefit. Conservatively predict535771cycles; additive526451 is only an "
                               "optimistic comparison. Keep644DSP/146BRAM18K/zeroURAM. Three FRP folds "
                               "added398HLS LUT and60FF in W27; budget82050LUT/131000FF for combined control. "
                               "16*1728bits window FIFO covers512 compute cycles at4*T=32 per tile. "
                               "Physical resource/timing and finite-FIFO behavior require new measurements.")
    else:
        estimates.update(Conv1_DSP=576, Conv2_DSP=256, Conv3_DSP=200,
                         LUT=float(measured["LUT"])+1100, FF=float(measured["FF"])+800,
                         basis="C13 HLS counts; C14 exact300632RTL cycles, window reads58166blocked "
                               "cycles over two frames, fold291234 versus262144nominal. Recovering "
                               "58166/2=29083 gives271549; conservatively estimate272000. AtT4 a tile "
                               "takes16cycles: FIFO16 covers256, FIFO32 covers512 versus264 row-scan "
                               "cycles. Extra30*1728=51840bits,810LUT6 under64bits/LUT plus control: "
                               "budget1100additionalLUT and800FF. Retain1032DSP/146BRAM18K/zeroURAM. "
                               "C15's actual routed result decides the first physical target and any ROM retry; "
                               "no clock or frame-time closure is assumed.")
    purpose = ("Combine the user-accepted F48 deep-window basis with W27's three FRP MAC folds in "
               "an independent T8 runtime-weight design. Require E017 exactness on all13 images "
               "and both changed-parameter RTL transactions; measure whether FIFO and FRP benefits "
               "overlap before routing. " if t8 else
               "Add only a32-entry transformed-window FIFO to frozen C13's runtime-prepacked T4 "
               "design. Preserve E065 mixed Conv2-w8 precision, all13-image deltaPSNR and exact "
               "changed-parameter two-frame RTL. Test whether deeper lookahead removes C14's "
               "window stalls without changing arithmetic or replicate padding. ")
    config = {**base, "id": args.id, "name": args.variant, "series": "C", "scope": "frame",
              "stage": "rom_clock_ws_combo8" if t8 else "rom_clock_ws_combo4",
              "design": "designs/winograd_windows16_frp_v1" if t8 else "designs/winograd_t4_windows32_v1",
              "control_experiment": parent_id, "combination_variant": args.variant,
              "memory_scheduler": True, "resource_policy": "routed", "required_image_count": 13,
              "set14": True, "estimates": estimates,
              "purpose": purpose+"User requested implementation only after C15 has a recorded result. "
                                 "Use one heavy task with budgeted light work. Runtime srcnn signature, "
                                 "source weights, quantization, original tests and physical gates stay fixed.",
              "changes": "Copy the frozen measured "+parent_id+" source after committing this plan; "
                         +( "keep its16-entry FIFO and change only three continuous fold pipelines to FRP."
                            if t8 else "change only the transformed-window FIFO depth from2 to32."),
              "interpretation": "Compare parsed HLS/RTL/routed measurements with paper estimates, "
                                "explain deviations above20%, and use FIFO/process counters rather than "
                                "summing overlapping stall totals. HLS estimates cannot prove physical closure.",
              "conclusion": "Run13-image exact/precision screening, then changed-parameter two-frame RTL "
                            "and an independent implementation. Keep the validated integration fallback "
                            "until the new design independently passes all physical gates."}
    config.pop("synthesis_after", None)
    config.pop("quality_reference", None)
    plan(config)
    subprocess.run([sys.executable, str(ROOT/"exp/commit_exp.py"), args.id,
                    "plan_"+args.variant], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
