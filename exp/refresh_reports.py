#!/usr/bin/env python3
"""Reparse reports without rerunning an immutable experiment."""
import argparse
import csv
import json
from pathlib import Path
from run_exp import ROOT, FIELDS, CAPACITY, LIMIT, append_log, lock, markdown_table, number, parse_xml, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--classify-complete", action="store_true",
                        help="Correct report_incomplete only when archived C simulation and all metrics pass")
    parser.add_argument("--fill-measurements", action="store_true",
                        help="Fill parsed measurements while preserving an invalid/failing status")
    args = parser.parse_args()
    archive = next((ROOT / "experiments").glob(args.id + "_*"))
    config = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    work = ROOT / "workspace/exp_runs" / args.id
    reports = sorted(work.rglob(config.get("top", "srcnn") + "_csynth.xml"))
    if not reports:
        reports = list((archive / "reports").glob(config.get("top", "srcnn") + "_csynth.xml"))
    if not reports:
        raise RuntimeError("No archived synthesis report")
    parsed, _ = parse_xml(reports[-1])
    if args.classify_complete or args.fill_measurements:
        if args.fill_measurements:
            metrics.update({key:value for key,value in parsed.items() if value is not None})
            for key,cap in CAPACITY.items():
                if key != "URAM" and parsed.get(key) is not None:
                    pct_key = "BRAM_pct" if key == "BRAM18K" else key+"_pct"
                    metrics[pct_key] = 100*parsed[key]/cap
            if parsed.get("latency_cycles") is not None and parsed.get("clock_est_ns") is not None:
                metrics["latency_ms_est"] = parsed["latency_cycles"]*max(config["clock"],parsed["clock_est_ns"])/1e6
        if args.classify_complete:
            if metrics.get("csim_pass") is not True or metrics["status"] != "report_incomplete":
                raise RuntimeError("Classification correction requires an accepted simulation and an incomplete report")
            if any(parsed.get(key) is None for key in (*CAPACITY, "latency_cycles", "clock_est_ns")):
                raise RuntimeError("Report is still incomplete")
            metrics.update(parsed)
            metrics["latency_ms_est"] = parsed["latency_cycles"] * max(config["clock"], parsed["clock_est_ns"]) / 1e6
            feasible = all(parsed[key] <= CAPACITY[key] * LIMIT[key] for key in CAPACITY)
            metrics["status"] = "pass" if feasible else "infeasible"
            if feasible and config.get("fixed") and config.get("validation", {}).get("image_count", 0) < 14:
                metrics["status"] = "provisional"
        with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
            results = ROOT / "experiments/results.csv"
            rows = list(csv.DictReader(results.open(newline="")))
            with results.open("w", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=FIELDS)
                writer.writeheader()
                writer.writerows(metrics if row["id"] == args.id else row for row in rows)
            append_log(args.id + (": filled archived report measurements without changing experiment validity" if args.fill_measurements else
                                  ": corrected zero-cycle combinational report classification from archived XML; no rerun or resource-limit change"))
        write_json(archive / "metrics.json", metrics)
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
