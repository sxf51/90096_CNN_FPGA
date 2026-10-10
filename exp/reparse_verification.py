#!/usr/bin/env python3
"""Reparse archived verification reports without rerunning or altering hardware."""
import argparse
import csv
import json
import subprocess
import sys
import time
from run_exp import ROOT, FIELDS, append_log, lock, markdown_table, number, write_json
from verify_exp import parse_verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    results = ROOT / "experiments/results.csv"
    while True:
        with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
            rows = list(csv.DictReader(results.open(newline="")))
        row = next((r for r in rows if r["id"] == args.id), None)
        if row is not None:
            break
        if not args.wait:
            raise RuntimeError("Verification row is not archived")
        time.sleep(5)
    archive = ROOT / "experiments" / row["md_path"].split("/")[0]
    config = json.loads((archive / "config.json").read_text())
    operation = config["operation"]
    observed, detail = parse_verification(archive / "reports", operation)
    previous = config.get("verification", {})
    if operation == "impl":
        complete = all(observed.get(k) is not None for k in ("impl_WNS_ns", "impl_DSP", "impl_LUT", "impl_FF"))
        if not complete and row["status"] == "impl_complete":
            row["status"] = "report_incomplete"
        if complete:
            observed["timing_met"] = observed["impl_WNS_ns"] >= 0
            observed["impl_clock_ns_est"] = float(config["clock"]) - observed["impl_WNS_ns"]
    elif operation == "cosim":
        if observed.get("rtl_status") != "Pass" and row["status"] == "cosim_complete":
            row["status"] = "report_incomplete"
        actual, estimate = observed.get("rtl_latency_max"), number(row["latency_cycles"])
        if actual is not None and estimate:
            observed["cycle_deviation_pct"] = 100 * (actual / estimate - 1)
    config["verification"] = observed
    config["report_parser_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    config["previous_verification_parse"] = previous
    write_json(archive / "config.json", config)
    write_json(archive / "verification.json", observed)
    metrics = json.loads((archive / "metrics.json").read_text())
    metrics["status"] = row["status"]
    write_json(archive / "metrics.json", metrics)
    detail.extend({"file": "derived", "metric": k, "value": v} for k, v in observed.items()
                  if k in {"cycle_deviation_pct", "timing_met", "impl_clock_ns_est"})
    with (archive / "data.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["file", "metric", "value"])
        writer.writeheader()
        writer.writerows(detail)
    path = ROOT / "experiments" / row["md_path"]
    text = path.read_text()
    a, b = text.index("## 5."), text.index("## 6.")
    table = markdown_table([{"metric": k, "value": v} for k, v in observed.items()], ["metric", "value"])
    text = text[:a] + "## 5. Results / 结果\n\n<!-- AUTO: archived final reports only -->\n\n" + table + "\n" + text[b:]
    a, b = text.index("## 6."), text.index("## 7.")
    text = text[:a] + "## 6. Interpretation / 解读\n\nFinal routed reports exclusively determine implementation timing and resources. Synthesis-stage reports are retained but excluded from these measurements. Original HLS estimates and source/precision provenance remain in metrics.json and the parent archive. No board validation is implied.\n\n" + text[b:]
    path.write_text(text)
    with lock(ROOT / "workspace/exp_runs/.results.lock", wait_timeout=120):
        current = list(csv.DictReader(results.open(newline="")))
        with results.open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(row if r["id"] == args.id else r for r in current)
        append_log(args.id + ": reparsed archived final verification reports; synthesis reports excluded; " + json.dumps(observed))
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), args.id, "final_report_parse"], cwd=ROOT, check=True)
    print(json.dumps(observed), flush=True)


if __name__ == "__main__":
    main()
