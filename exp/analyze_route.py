#!/usr/bin/env python3
"""Archive routed-clock calibration and the first five reported setup paths."""
import argparse
import csv
import json
import re
from analyze_arch import write_csv
from host_memory import cpu_summary
from route_gates import evaluate_route
from rtl_acceptance import accepted_cosim
from run_exp import ROOT, markdown_table, number


def setup_paths(text):
    records = []
    for block in re.split(r"(?=^Slack \()", text, flags=re.MULTILINE):
        if not re.search(r"Path Type:\s+Setup", block):
            continue
        fields = {}
        for key, pattern in {
            "slack_ns": r"^Slack \([^)]*\)\s*:\s*([-\d.]+)ns",
            "source": r"^\s*Source:\s*(\S+)",
            "destination": r"^\s*Destination:\s*(\S+)",
            "logic_levels": r"^\s*Logic Levels:\s*(\d+)",
            "data_path_ns": r"^\s*Data Path Delay:\s*([-\d.]+)ns",
        }.items():
            match = re.search(pattern, block, re.MULTILINE)
            fields[key] = match.group(1) if match else None
        for key in ("slack_ns", "logic_levels", "data_path_ns"):
            fields[key] = number(fields[key])
        fields["path"] = len(records)+1
        fields["DSP_sites"] = len(set(re.findall(r"DSP48E2_X\d+Y\d+", block)))
        fields["DSP_cascade_PCIN_PCOUT"] = "PCIN" in block or "PCOUT" in block
        records.append(fields)
        if len(records) == 5:
            break
    return records


def hierarchy(text):
    columns = ["Instance", "Module", "Total LUTs", "Logic LUTs", "LUTRAMs", "SRLs", "FFs",
               "RAMB36", "RAMB18", "URAM", "DSP Blocks"]
    records, active = [], False
    for cells in csv.reader(text.splitlines(), delimiter="|"):
        values = [cell.strip() for cell in cells[1:-1]]
        if values == columns:
            active = True
            continue
        if not active or len(values) != len(columns):
            continue
        record = dict(zip(columns, values))
        for key in columns[2:]:
            record[key] = number(record[key])
        if record["Total LUTs"] is None:
            continue
        record["BRAM18K"] = 2*record["RAMB36"]+record["RAMB18"] if record["RAMB36"] is not None and record["RAMB18"] is not None else None
        records.append(record)
    return records


def analyze(archive):
    config = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    observed = config.get("verification", {})
    routed_policy = config.get("resource_policy") == "routed"
    route_feasible = evaluate_route(observed).get("route_feasible")
    target = config.get("implementation_clock_ns", config["clock"])
    wns = number(observed.get("impl_WNS_ns"))
    values = {"id": config["id"], "parent": config["verify_parent"], "status": metrics["status"],
              "target_ns": target, "WNS_ns": wns, "TNS_ns": number(observed.get("impl_TNS_ns")),
              "period_from_slack_ns": target-wns if wns is not None else None,
              "timing_met": observed.get("timing_met"), "route_feasible": route_feasible}
    for key in ("DSP", "LUT", "FF", "BRAM18K", "URAM"):
        actual = (2*number(observed["impl_BRAM36"]) if observed.get("impl_BRAM36") is not None else None) if key == "BRAM18K" else number(observed.get("impl_"+key))
        prediction = number(metrics.get(key))
        values["HLS_"+key] = prediction
        values["route_"+key] = actual
        values["route_to_HLS_"+key] = actual/prediction if actual is not None and prediction else None
    for path in sorted((ROOT / "experiments").glob("*_*/config.json")):
        candidate = json.loads(path.read_text())
        if candidate.get("operation") == "cosim" and candidate.get("verify_parent") == config["verify_parent"]:
            verdict_path = path.parent / "metrics.json"
            if not verdict_path.is_file() or not accepted_cosim(json.loads(verdict_path.read_text()), candidate):
                continue
            rtl = number(candidate.get("verification", {}).get("rtl_latency_max"))
            if rtl is not None:
                values["rtl_source_id"] = candidate["id"]
                values["rtl_latency_cycles"] = rtl
                values["rtl_interval_cycles"] = number(candidate.get("verification", {}).get("rtl_interval_max"))
                values["rtl_frame_ms_at_target"] = (rtl*target/1e6
                                                    if not routed_policy or route_feasible is True else None)
                values["rtl_frame_ms_from_slack"] = rtl*(target-wns)/1e6 if wns is not None else None
    paths = []
    for record in config.get("verification_reports", []):
        if record["raw_file"] == observed.get("impl_timing_report"):
            paths = setup_paths((archive / record["archived_file"]).read_text())
    extra_paths = archive / "reports/impl/srcnn_setup5_routed.rpt"
    if extra_paths.is_file():
        paths = setup_paths(extra_paths.read_text())
    write_csv(archive / "route_analysis.csv", [values], list(values))
    write_csv(archive / "critical_paths.csv", paths, ["path","slack_ns","source","destination","logic_levels","data_path_ns","DSP_sites","DSP_cascade_PCIN_PCOUT"])
    memory = archive / ("impl_host_memory.csv" if (archive / "impl_host_memory.csv").is_file()
                        else "host_memory.csv")
    samples = list(csv.DictReader(memory.open(newline=""))) if memory.is_file() else []
    memory_values = {"samples":len(samples), "min_available_GiB":min(float(item["available_kib"]) for item in samples)/1048576 if samples else None,
                     "peak_tool_RSS_GiB":max(float(item["tool_rss_kib"]) for item in samples)/1048576 if samples else None,
                     "peak_process_tree_RSS_GiB":max(float(item["task_tree_rss_kib"]) for item in samples)/1048576
                     if samples and "task_tree_rss_kib" in samples[0] else None,
                     "telemetry_file": memory.name,
                     "implementation_threads": config.get("implementation_threads", 1),
                     **cpu_summary(samples)}
    write_csv(archive / "host_memory_summary.csv", [memory_values], list(memory_values))
    block = "<!-- AUTO: ROUTE ANALYSIS START -->\n\n"
    block += ("Routed calibration (final timing/resource acceptance uses independent routed gates):\n\n"
              if routed_policy else "Routed calibration (HLS resources remain the acceptance gate):\n\n")
    block += markdown_table([{"metric":key,"value":value} for key,value in values.items()], ["metric","value"])
    block += "\n`period_from_slack_ns = implementation target - WNS` is a slack-derived estimate. Negative slack requires a fresh relaxed-constraint implementation; this arithmetic alone does not prove timing closure. No board result is inferred.\n\n"
    block += "First five available setup paths:\n\n" + markdown_table(paths, ["path","slack_ns","source","destination","logic_levels","data_path_ns","DSP_sites","DSP_cascade_PCIN_PCOUT"])
    block += "\nHost memory during the operation:\n\n" + markdown_table([memory_values], list(memory_values))
    block += "\nTool RSS and CPU utilization cover the entire host; process-tree RSS covers this task. Shared mappings may be counted more than once.\n"
    hierarchy_rows = []
    top = config.get("parent_config", {}).get("top", "srcnn")
    for state in ("synth", "routed"):
        path = archive / ("reports/impl/"+top+"_utilization_hierarchical_"+state+".rpt")
        if path.is_file():
            parts = hierarchy(path.read_text())
            write_csv(archive / ("physical_hierarchy_"+state+".csv"), parts, list(parts[0]) if parts else ["Instance","Module"])
            selected = [part for part in parts if part["Module"] == "(top)" or part["Module"].endswith(
                tuple(top+"_"+role for role in ("dataflow_region", "conv12", "conv1_stream", "conv3_stream",
                                               "engine1", "conv2_stream", "engine3")))]
            hierarchy_rows.extend({"state":state,**part} for part in selected)
    if hierarchy_rows:
        block += "\nPhysical hierarchy (parent totals include children; do not sum nested rows):\n\n"
        block += markdown_table(hierarchy_rows,["state","Instance","Total LUTs","FFs","BRAM18K","DSP Blocks"])
    block += "\n<!-- AUTO: ROUTE ANALYSIS END -->\n\n"
    md = archive / (config["id"]+".md")
    text = md.read_text()
    start, end = "<!-- AUTO: ROUTE ANALYSIS START -->", "<!-- AUTO: ROUTE ANALYSIS END -->"
    if start in text:
        before, after = text.split(start,1)
        text = before+block+after.split(end,1)[1].lstrip("\n")
    else:
        text = text.replace("## 6. Interpretation", block+"## 6. Interpretation",1)
    md.write_text(text)
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="+")
    args = parser.parse_args()
    for exp_id in args.ids:
        archive = next((ROOT / "experiments").glob(exp_id+"_*/metrics.json")).parent
        print(json.dumps(analyze(archive), sort_keys=True))
    rows = []
    for path in sorted((ROOT / "experiments").glob("*_*/route_analysis.csv")):
        rows.extend(csv.DictReader(path.open(newline="")))
    columns = list(dict.fromkeys(key for row in rows for key in row))
    write_csv(ROOT / "experiments/route_calibration.csv", rows, columns)


if __name__ == "__main__":
    main()
