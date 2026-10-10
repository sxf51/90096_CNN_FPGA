#!/usr/bin/env python3
"""Retain measured outputs but invalidate experiments with skipped directives."""
import csv
import json
from run_exp import ROOT, FIELDS, append_log, write_json

for exp_id in ("E023", "E024", "E025"):
    folder = next((ROOT / "experiments").glob(exp_id + "_*"))
    metrics = json.loads((folder / "metrics.json").read_text())
    metrics["status"] = "invalid_config"
    metrics["notes"] += "; Vitis skipped unknown syn.directive; numbers describe default scheduling, not intended directive experiment"
    write_json(folder / "metrics.json", metrics)
    md = folder / (exp_id + ".md")
    text = md.read_text()
    text = text.replace("| status | infeasible |", "| status | invalid_config |")
    text = text.replace("Pending measured II, dependency, port and resource reports.",
                        "Vitis logged HLS 200-1921: syn.directive was skipped as an unknown configuration key. Requested directives were not applied. These reports describe default scheduling and cannot answer the intended experiment. Retained for diagnosis; rerun with supported syn.directive.pipeline and syn.directive.array_partition entries.")
    md.write_text(text)
    rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))
    for row in rows:
        if row["id"] == exp_id:
            row.update(status=metrics["status"], notes=metrics["notes"])
    with (ROOT / "experiments/results.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    config = json.loads((ROOT / f"exp/configs/{exp_id}.json").read_text())
    retry = {"E023": "E028", "E024": "E029", "E025": "E032"}[exp_id]
    config.update(id=retry, name=config["name"] + "_validcfg")
    write_json(ROOT / f"exp/configs/{retry}.json", config)
append_log("E023/E024/E025 invalidated: unsupported syn.directive silently ignored by Vitis. Added schema-based directive emission, unknown-option rejection and E028/E029/E032 retries.")
