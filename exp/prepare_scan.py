#!/usr/bin/env python3
"""Prepare sequential coordinate scans without overwriting completed runs."""
import argparse
import json
from run_exp import ROOT, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("round", choices=("T", "split", "storage", "clock"))
    parser.add_argument("--T", type=int, default=32)
    parser.add_argument("--base", default="exp/configs/E033.json")
    args = parser.parse_args()
    base = json.loads((ROOT / args.base).read_text())
    cases = {
        "T": [("E034", {"EXP_T": 16}), ("E035", {"EXP_T": 8})],
        "split": [("E036", {"EXP_C1_SPLIT": 1}), ("E037", {"EXP_C2_SPLIT": 1}),
                  ("E038", {"EXP_C3_SPLIT": 1})],
        "storage": [("E039", {"EXP_STORAGE": 1}), ("E040", {"EXP_STORAGE": 2})],
        "clock": [("E041", {"clock": 5}), ("E042", {"clock": 4}), ("E043", {"clock": 3.33})],
    }
    for exp_id, changes in cases[args.round]:
        path = ROOT / f"exp/configs/{exp_id}.json"
        if path.exists():
            raise RuntimeError("Refuse to overwrite " + str(path))
        defines = {**base["defines"], "EXP_T": args.T,
                   **{k: v for k, v in changes.items() if k != "clock"}}
        t = defines["EXP_T"]
        splits = ["tap" if defines.get("EXP_C1_SPLIT") else "Cout",
                  "Cin" if defines.get("EXP_C2_SPLIT") else "Cout",
                  "tap" if defines.get("EXP_C3_SPLIT") else "Cin"]
        storage = ("register", "lutram", "bram")[defines["EXP_STORAGE"]]
        clock = changes.get("clock", base["clock"])
        ideal = 8032 / t
        config = {**base, "id": exp_id, "name": f"scan_{args.round}_T{t}_{exp_id}",
                  "stage": 4, "T": t, "defines": defines, "clock": clock,
                  "unroll": "/".join(splits), "storage": storage,
                  "quality_reference": "experiments/E017_apfixed_boundary_w10a10/metrics.json",
                  "purpose": f"Coordinate scan {args.round}; ideal MAC budget {ideal:g} DSP, "
                             f"compute floor {65025*t} cycles before load/padding/control overhead.",
                  "changes": f"Independent snapshot of {base['design']}, changes {changes}; "
                             "same exact quantization boundaries and butterfly reference as E033.",
                  "interpretation": "Compare measured loops and resources with E033 and this coordinate's "
                                    "control. Runtime-loaded weights require writable storage; rom binding "
                                    "would contradict the unchanged external parameter contract.",
                  "conclusion": "Choose the next coordinate only from measured feasible candidates; "
                                "quality provenance is E017, with 13-image coverage explicitly provisional."}
        write_json(path, config)
        print(exp_id)


if __name__ == "__main__":
    main()
