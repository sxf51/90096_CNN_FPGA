#!/usr/bin/env python3
"""Archive partial implementation evidence without promoting it to routed results."""
import argparse
import csv
import hashlib
import json
import re
import shlex
import subprocess
from analyze_arch import write_csv
from analyze_route import hierarchy
from run_exp import ROOT, append_log, check_protected, markdown_table, number, write_json


def resources(text):
    keys = {"CLB LUTs": "LUT", "Slice LUTs": "LUT", "CLB Registers": "FF",
            "Slice Registers": "FF", "DSPs": "DSP", "DSP48E2": "DSP",
            "Block RAM Tile": "BRAM36", "URAM": "URAM"}
    values = {}
    for cells in csv.reader(text.splitlines(), delimiter="|"):
        row = [cell.strip() for cell in cells[1:-1]]
        key = keys.get(row[0].rstrip("* ")) if len(row) >= 2 else None
        value = number(row[1]) if key else None
        if value is not None:
            if key in values and values[key] != value:
                raise RuntimeError("Conflicting partial resource rows: "+key)
            values[key] = value
    if "BRAM36" in values:
        values["BRAM18K"] = 2*values["BRAM36"]
    return values


def routing_progress(text):
    rows, iteration = [], None
    for line in text.splitlines():
        phase = re.match(r"^Phase \d+\.\d+ Global Iteration (\d+)$", line)
        if phase:
            iteration = int(phase[1])
        match = re.search(r"Intermediate Timing Summary \| WNS=([-\d.]+) \| TNS=([-\d.]+)", line)
        if match:
            rows.append({"iteration": iteration, "WNS_ns": number(match[1]),
                         "TNS_ns": number(match[2]), "final_routed_verdict": False})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    args = parser.parse_args()
    check_protected()
    archive = next((ROOT / "experiments").glob(args.id+"_*/metrics.json")).parent
    config = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    if config.get("operation") != "impl" or metrics["status"] not in {"timeout", "fail"}:
        raise RuntimeError("Partial recovery requires an archived failed/timed-out implementation")
    ssh_config = str(ROOT.parent / "ssh-config")
    ssh = ["ssh", "-F", ssh_config, "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    remote = "/home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/"+args.id
    subprocess.run(ssh+["test ! -e "+shlex.quote(remote+"/.run.lock")], check=True)
    files = [("synth", "hls/impl/verilog/report/srcnn_utilization_synth.rpt"),
             ("hierarchy_synth", "hls/impl/verilog/report/srcnn_utilization_hierarchical_synth.rpt"),
             ("timing_synth", "hls/impl/verilog/report/srcnn_timing_synth.rpt"),
             ("paths_synth", "hls/impl/verilog/report/srcnn_timing_paths_synth.rpt"),
             ("placed", "hls/impl/verilog/project.runs/impl_1/bd_0_wrapper_utilization_placed.rpt"),
             ("progress", "hls/impl/verilog/project.runs/impl_1/runme.log")]
    evidence, area, progress, modules = [], [], [], []
    for stage, relative in files:
        source = remote+"/"+relative
        present = subprocess.run(ssh+["test -f "+shlex.quote(source)]).returncode
        if present == 1:
            continue
        if present:
            raise RuntimeError("Cannot inspect partial report: "+relative)
        target = archive / "diagnostics/pre_route" / ("impl_runme.txt" if stage == "progress" else source.rsplit("/", 1)[1])
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["scp", "-F", ssh_config, "xiaoxin-ubuntu:"+source, str(target)], check=True)
        evidence.append({"raw_file": relative, "archived_file": str(target.relative_to(archive)),
                         "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                         "stage": stage, "final_routed_evidence": False})
        text = target.read_text()
        if stage in {"synth", "placed"}:
            values = resources(text)
            area.append({"stage": stage, "source": str(target.relative_to(archive)), **values})
        if stage == "progress":
            progress = routing_progress(text)
        if stage == "hierarchy_synth":
            modules = hierarchy(text)
    config["partial_implementation_reports"] = evidence
    write_json(archive / "config.json", config)
    write_csv(archive / "partial_resources.csv", area, ["stage", "source", "DSP", "LUT", "FF", "BRAM36", "BRAM18K", "URAM"])
    write_csv(archive / "routing_progress.csv", progress, ["iteration", "WNS_ns", "TNS_ns", "final_routed_verdict"])
    write_csv(archive / "partial_hierarchy.csv", modules, list(modules[0]) if modules else ["Instance", "Module"])
    block = "<!-- AUTO: PARTIAL ROUTE START -->\n\n"
    block += "Partial synthesis/placement and intermediate route evidence; none proves final routed resources or timing. The original timeout/failure status and routed unknowns are unchanged.\n\n"
    block += markdown_table(area, ["stage", "DSP", "LUT", "FF", "BRAM18K", "URAM", "source"])
    block += "\n"+markdown_table(progress, ["iteration", "WNS_ns", "TNS_ns", "final_routed_verdict"])
    selected = [row for row in modules if not row["Instance"].startswith("(") and
                row["Module"].endswith(("srcnn_dataflow_region", "srcnn_read_input", "srcnn_engine1",
                                        "srcnn_conv2_stream", "srcnn_engine3", "srcnn_windows1", "srcnn_windows3"))]
    block += "\nSynthesized hierarchy only (parent totals include children; never sum nested rows):\n\n"
    block += markdown_table(selected, ["Instance", "Module", "Total LUTs", "FFs", "BRAM18K", "DSP Blocks"])
    block += "\n<!-- AUTO: PARTIAL ROUTE END -->\n\n"
    md = archive / (args.id+".md")
    text = md.read_text()
    start, end = "<!-- AUTO: PARTIAL ROUTE START -->", "<!-- AUTO: PARTIAL ROUTE END -->"
    if start in text:
        before, after = text.split(start, 1)
        text = before+block+after.split(end, 1)[1].lstrip("\n")
    else:
        text = text.replace("## 6. Interpretation", block+"## 6. Interpretation", 1)
    md.write_text(text)
    append_log(args.id+": archived partial synth/placed reports and intermediate route summaries; final routed metrics remain unknown and failure/timeout unchanged.")
    print(json.dumps({"partial_resources": area, "intermediate_routing": progress}))


if __name__ == "__main__":
    main()
