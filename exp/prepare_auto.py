#!/usr/bin/env python3
"""Mechanically copy untouched golden and add stable labels only."""
import json
from pathlib import Path
import re
from run_exp import ROOT


def main():
    design = ROOT / "designs/golden_auto"
    design.mkdir(parents=True, exist_ok=False)
    for name in ("srcnn.cpp", "conv1.cpp", "srcnn.h"):
        text = (ROOT / "src" / name).read_text()
        count = [0]
        def label(match):
            count[0] += 1
            return match[1] + f"g_{count[0]:02d}_{match[2]}: " + match[0].lstrip()
        if name.endswith(".cpp"):
            text = re.sub(r"^(\s*)for \(int (\w+) = [^\n]*", label, text, flags=re.MULTILINE)
        (design / name).write_text(text)
    base = {"stage": 2, "design": "designs/golden_auto", "clock": 10,
            "settings": "/home/lipuze/amdfpga/2026.1/Vitis/settings64.sh",
            "source_commit": __import__("subprocess").check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "changes": "Golden copy with stable loop labels only; all experiment directives are configuration-controlled.",
            "interpretation": "Pending measured II, dependency, port and resource reports.",
            "conclusion": "Compare compiler-only scheduling with original baseline and streaming architecture."}
    inner = ["set_directive_pipeline -II 1 conv1/g_06_kx", "set_directive_pipeline -II 1 srcnn/g_06_kx",
             "set_directive_pipeline -II 1 srcnn/g_12_kx"]
    pixels = ["set_directive_pipeline -II 1 conv1/g_03_x", "set_directive_pipeline -II 1 srcnn/g_03_x",
              "set_directive_pipeline -II 1 srcnn/g_09_x"]
    partition = ["set_directive_array_partition -type cyclic -factor 4 -dim 4 conv1 conv1_weights",
                 "set_directive_array_partition -type cyclic -factor 4 -dim 1 srcnn conv1_ftmap",
                 "set_directive_array_partition -type cyclic -factor 4 -dim 1 srcnn conv2_ftmap"]
    cases = [
        ("E020", "auto_default_10ns", {"purpose": "Default automatic scheduling at 10 ns; labels should not change numeric behavior."}),
        ("E021", "auto_default_4ns", {"clock": 4, "purpose": "Measure whether tighter clock improves estimated frame time without architectural changes."}),
        ("E022", "auto_pipeline_off", {"options": {"syn.compile.pipeline_loops": 0}, "purpose": "Compare no automatic pipelining to default scheduling."}),
        ("E023", "auto_inner_pipeline", {"directives": inner, "ii_targets": {"g_06_kx": 1, "g_12_kx": 1}, "purpose": "Pipeline innermost MAC loops; expect float recurrence to limit II."}),
        ("E024", "auto_pixel_pipeline", {"directives": pixels, "ii_targets": {"g_03_x": 1, "g_09_x": 1}, "purpose": "Pipeline pixel loops; measure inner-loop expansion, memory ports and potential resource explosion."}),
        ("E025", "auto_partition", {"directives": inner + partition, "ii_targets": {"g_06_kx": 1, "g_12_kx": 1}, "purpose": "Add cyclic partitions and test whether port supply removes the inner-loop II bottleneck."}),
        ("E026", "auto_unsafe_math", {"options": {"syn.compile.unsafe_math_optimizations": True}, "purpose": "Test unsafe math scheduling and float-adder recurrence effects while preserving C test acceptance."}),
    ]
    for exp_id, name, options in cases:
        config = {**base, "id": exp_id, "name": name, **options}
        (ROOT / f"exp/configs/{exp_id}.json").write_text(json.dumps(config, indent=2) + "\n")


if __name__ == "__main__":
    main()
