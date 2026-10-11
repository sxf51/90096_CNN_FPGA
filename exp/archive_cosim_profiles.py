#!/usr/bin/env python3
"""Archive bounded counter summaries from Vitis 2026.1 RTL profiling."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import subprocess
import zipfile
from run_exp import ROOT, append_log, check_protected, markdown_table, write_json


CHANNEL_FIELDS = ("blocking_flags", "write_block_cycles", "read_block_cycles",
                  "monitor_cycles", "peak_depth")
PROCESS_FIELDS = ("stall_cycles", "monitor_cycles", "process_interval_avg_cycles",
                  "process_interval_max_cycles", "process_interval_min_cycles",
                  "process_latency_avg_cycles", "process_latency_max_cycles",
                  "process_latency_min_cycles", "start_wait_cycles",
                  "continue_wait_cycles", "read_stall_cycles", "write_stall_cycles")


def counter_prefix(handle, fields):
    reader = csv.reader(handle)
    raw, values = [], {}
    for key in fields:
        row = next(reader, None)
        if row is None or len(row) != 1:
            raise ValueError("Incomplete or malformed profiling counter: "+key)
        value = int(row[0])
        if not 0 <= value <= 0xffffffff:
            raise ValueError("Profiling counter outside unsigned32 range: "+key)
        raw.append(row)
        values[key] = None if value == 0xffffffff else value
    return raw, values


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def archive_profiles(work, archive):
    db = work / "hls/.autopilot/db"
    files, channels, processes = [], [], []

    def record(path, raw_file, **extra):
        files.append({"raw_file":raw_file, "archived_file":str(path.relative_to(archive)),
                      "sha256":hashlib.sha256(path.read_bytes()).hexdigest(), **extra})

    for kind, folder, index, fields, output in (
            ("channel", "channel_depth_info/channel.zip", "channel_info.csv", CHANNEL_FIELDS, channels),
            ("process", "process_stalling_info/process.zip", "process_info.csv", PROCESS_FIELDS, processes)):
        container, mapping = db / folder, db / index
        if not container.is_file() or not mapping.is_file():
            raise FileNotFoundError("RTL profiling source not produced: "+str(container))
        digest = hashlib.sha256(container.read_bytes()).hexdigest()
        target = archive / "profiling/raw" / index
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(mapping.read_bytes())
        record(target, str(mapping.relative_to(work)))
        with zipfile.ZipFile(container) as zipped, mapping.open(newline="") as source:
            for row in csv.reader(source):
                if len(row) != 4:
                    raise ValueError("Unexpected profiling index format: "+index)
                parent, name, trace, member = row
                if Path(member).name != member or not member.endswith(".csv"):
                    raise ValueError("Unsafe profiling member: "+member)
                with zipped.open(member) as stream, io.TextIOWrapper(stream, encoding="utf-8") as text:
                    raw, values = counter_prefix(text, fields)
                target = archive / "profiling/raw" / member
                with target.open("w", newline="") as out:
                    csv.writer(out, lineterminator="\n").writerows(raw)
                record(target, str(container.relative_to(work))+"!"+member,
                       excerpt=True, source_container_sha256=digest)
                values.update(parent=parent, name=name,
                              kind=kind if kind == "channel" or trace else "module")
                for counter in (("write_block_cycles", "read_block_cycles") if kind == "channel" else ("stall_cycles",)):
                    cycles, total = values[counter], values["monitor_cycles"]
                    values[counter.replace("_cycles", "_pct")] = 100*cycles/total if cycles is not None and total else None
                output.append(values)
    for name, rows, fields in (("channels.csv",channels,(*CHANNEL_FIELDS,"write_block_pct","read_block_pct")),
                              ("processes.csv",processes,(*PROCESS_FIELDS,"stall_pct"))):
        target = archive / "profiling" / name
        write_csv(target, rows, ("parent","name","kind",*fields))
        record(target, "Derived from the archived counter prefixes and index CSVs")
    schema = archive / "profiling/schema.json"
    write_json(schema, {"channel_prefix_fields":CHANNEL_FIELDS, "process_prefix_fields":PROCESS_FIELDS,
                        "source_format":"Vitis2026.1 df_fifo_monitor, df_process_monitor and nodf_module_monitor",
                        "scope":"Counters span both RTL transactions, including startup and inactive cycles. Process intervals are invocation intervals, not pipeline-loop II. Stall categories can overlap; never sum them across processes.",
                        "omitted":"Per-cycle traces and large event histories stay in the original workspace. Only the first5/12 scalar CSV rows are archived.",
                        "parser_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    record(schema, "Counter schema and extraction-script provenance")
    return files


def profile_results(archive):
    paths = [archive / "profiling" / name for name in ("channels.csv", "processes.csv")]
    if not all(path.is_file() for path in paths):
        return ""
    data = []
    for path in paths:
        with path.open(newline="") as handle:
            data.append(list(csv.DictReader(handle)))
    channels, processes = data
    engines = [row for row in processes if row["name"] in {"engine1_U0","conv2_stream_U0","engine3_U0"}]
    text = "\n<!-- AUTO: RTL profiling -->\n\nFinite-FIFO profiling over both transactions: [channel counters](profiling/channels.csv), [process/module counters](profiling/processes.csv), [schema](profiling/schema.json). Counter prefixes and source index CSVs are archived; per-cycle traces remain in the workspace. Process intervals below are invocation intervals, not inner-loop II. Percentages use the entire monitor period; parallel/overlapping stall counters cannot be added.\n\n"
    text += markdown_table(channels,["name","peak_depth","write_block_cycles","read_block_cycles","write_block_pct","read_block_pct"])
    text += "\n"+markdown_table(engines,["name","process_latency_max_cycles","process_interval_max_cycles","stall_cycles","read_stall_cycles","write_stall_cycles"])
    return text+"\n<!-- END: RTL profiling -->\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--pull",action="store_true",help="Fetch profiling inputs from the existing SSH workspace")
    parser.add_argument("--host",default="xiaoxin-ubuntu")
    parser.add_argument("--remote-root",default="/home/lipuze/amdprojects/90096_CNN_FPGA")
    parser.add_argument("--ssh-config",type=Path,default=ROOT.parent / "ssh-config")
    args = parser.parse_args()
    check_protected()
    exp_id = args.id
    archive = next((ROOT / "experiments").glob(exp_id+"_*/config.json")).parent
    config = json.loads((archive / "config.json").read_text())
    if config.get("operation") != "cosim" or config.get("verification",{}).get("rtl_status") != "Pass":
        raise ValueError("Profiling backfill requires a completed passing RTL run")
    work = ROOT / "workspace/exp_runs" / exp_id
    if args.pull:
        for relative in ("channel_info.csv", "process_info.csv", "channel_depth_info/channel.zip",
                         "process_stalling_info/process.zip"):
            target = work / "hls/.autopilot/db" / relative
            target.parent.mkdir(parents=True,exist_ok=True)
            remote = args.host+":"+args.remote_root+"/workspace/exp_runs/"+exp_id+"/hls/.autopilot/db/"+relative
            subprocess.run(["scp","-F",str(args.ssh_config),"-o","BatchMode=yes",remote,str(target)],check=True)
    config["verification_profiles"] = archive_profiles(work, archive)
    write_json(archive / "config.json", config)
    md = archive / (exp_id+".md")
    text = md.read_text()
    start, end = "\n<!-- AUTO: RTL profiling -->", "<!-- END: RTL profiling -->\n"
    if start in text:
        left = text.index(start)
        right = text.index(end,left)+len(end)
        text = text[:left]+text[right:]
    position = text.index("## 6. Interpretation")
    md.write_text(text[:position]+profile_results(archive)+"\n"+text[position:])
    append_log(exp_id+": archived RTL FIFO/process counters and their source prefixes; large per-cycle histories retained only in workspace; arithmetic/timing measurements unchanged.")
    print("Archived",len(config["verification_profiles"]),"RTL profiling evidence files")


if __name__ == "__main__":
    main()
