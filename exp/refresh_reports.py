#!/usr/bin/env python3
"""Reparse reports without rerunning an immutable experiment."""
import argparse
import csv
import json
from pathlib import Path
from run_exp import ROOT, FIELDS, CAPACITY, markdown_table, parse_xml, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    args = parser.parse_args()
    archive = next((ROOT / "experiments").glob(args.id + "_*"))
    config = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    work = ROOT / "workspace/exp_runs" / args.id
    reports = sorted(work.rglob(config.get("top", "srcnn") + "_csynth.xml"))
    if not reports:
        reports = list((archive / "reports").glob(config.get("top", "srcnn") + "_csynth.xml"))
    loops, modules = [], []
    for xml in sorted(reports[-1].parent.glob("*_csynth.xml")):
        module, found = parse_xml(xml)
        module["module"] = xml.stem.removesuffix("_csynth")
        modules.append(module)
        for item in found:
            item["module"] = module["module"]
            targets = config.get("ii_targets", {})
            item["target_ii"] = next((v for k, v in targets.items() if k in item["loop"]), None)
            item["ii_ok"] = None if item["target_ii"] is None else item["actual_ii"] == item["target_ii"]
            loops.append(item)
    config.update(parsed_loops=loops, parsed_modules=modules)
    write_json(archive / "config.json", config)
    detail = [{"kind": "loop", **p} for p in loops] + [{"kind": "module", **p} for p in modules]
    if detail:
        with (archive / "data.csv").open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=sorted(set().union(*(p.keys() for p in detail))))
            writer.writeheader()
            writer.writerows(detail)
    md = archive / (args.id + ".md")
    text = md.read_text()
    start, end = text.index("## 5."), text.index("## 6.")
    replacement = "## 5. Results / 结果\n\n<!-- AUTO: parsed measurements -->\n\n"
    replacement += markdown_table([{"metric": k, "value": metrics.get(k)} for k in FIELDS], ["metric", "value"])
    replacement += "\n### Pipeline loops\n\n" + markdown_table(loops, ["module", "loop", "target_ii", "actual_ii", "ii_ok"])
    replacement += "\n### Module resources\n\n" + markdown_table(modules, ["module", "DSP", "BRAM18K", "URAM", "LUT", "FF"]) + "\n"
    md.write_text(text[:start] + replacement + text[end:])


if __name__ == "__main__":
    main()
