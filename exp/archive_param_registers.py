#!/usr/bin/env python3
"""Read-only evidence for the planned 224-bit parameter write register."""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path
from run_exp import ROOT, EXPERIMENT_ID, append_log, parse_xml, utc, write_json
from reproduce_exp import archived


def register_fields(helper, caller, baseline):
    clocked = "\n".join(re.findall(
        r"always\s*@\s*\(\s*posedge\s+ap_clk\s*\)(.*?)(?=\balways\s*@|\bassign\b|\bendmodule\b|\Z)",
        helper, re.DOTALL))
    instances = re.findall(r"^\w+_params1_write_register\s+(\w+)\s*\((.*?)^\);",
                           caller, re.MULTILINE | re.DOTALL)
    if len(instances) != 1:
        raise RuntimeError("Need exactly one parameter-register instance")
    instance, ports = instances[0]
    fields = []
    for index in range(16):
        candidates = re.findall(r"\b(value_"+str(index)+r"_read_reg_\d+)\s*<=\s*value_"+
                                str(index)+r"\s*;", clocked)
        if len(candidates) != 1:
            raise RuntimeError("Missing clocked data field: "+str(index))
        register = candidates[0]
        if not re.search(r"\breg\s*\[\s*13\s*:\s*0\s*\]\s*"+register+r"\s*;", helper):
            raise RuntimeError("Unexpected registered field width")
        if not re.search(r"\bassign\s+ap_return_"+str(index)+r"\s*=\s*"+register+r"\s*;", helper):
            raise RuntimeError("Return does not use the data register")
        incoming, outgoing = instance+"_value_"+str(index), instance+"_ap_return_"+str(index)
        for port, wire in (("value_"+str(index), incoming), ("ap_return_"+str(index), outgoing)):
            if not re.search(r"\."+port+r"\s*\(\s*"+wire+r"\s*\)", ports):
                raise RuntimeError("Unexpected helper port connection")
        high, low = 14*index+13, 14*index
        if not re.search(r"\bassign\s+"+incoming+r"\s*=\s*params1_dout\["+
                         str(high)+":"+str(low)+r"\]\s*;", caller):
            raise RuntimeError("Helper input is not the matching FIFO field")
        writes = re.findall(r"\bassign\s+(\w+_d1)\s*=\s*"+outgoing+r"\s*;", caller)
        direct = re.findall(r"\bassign\s+(\w+_d1)\s*=\s*\{*params1_dout\["+
                            str(high)+":"+str(low)+r"\]\}*\s*;", baseline)
        if not writes or len(writes) != len(direct):
            raise RuntimeError("Registered write ports do not match the parent direct ports")
        fields.append({"field": index, "bits": 14, "register": register,
                       "registered_write_ports": len(writes), "parent_direct_write_ports": len(direct),
                       "example_write_port": writes[0]})
    if re.search(r"\bassign\s+\w+_d1\s*=\s*\{*params1_dout\[", caller):
        raise RuntimeError("Caller retains a direct FIFO-to-bank bypass")
    return fields


def evidence(exp_id):
    archive = archived(exp_id)
    config = json.loads((archive / "config.json").read_text())
    if config.get("timing_variant") != "paramreg":
        raise RuntimeError("Expected the independent parameter-register variant")
    work = ROOT / "workspace/exp_runs" / exp_id
    parent = ROOT / "workspace/exp_runs" / config["control_experiment"]
    top = config["top"]
    helper = work / ("hls/syn/verilog/"+top+"_params1_write_register.v")
    caller = work / ("hls/syn/verilog/"+top+"_wino_engine_Pipeline_wino_local_load_groups.v")
    baseline = parent / caller.relative_to(work)
    files = {"helper": helper, "caller": caller, "parent_caller": baseline}
    texts = {key: path.read_text() for key, path in files.items()}
    fields = register_fields(texts["helper"], texts["caller"], texts["parent_caller"])
    report = work / "hls/syn/report/params1_write_register_csynth.xml"
    metrics, _ = parse_xml(report)
    if metrics.get("latency_cycles") != 1 or metrics.get("interval_cycles") != 1 or metrics.get("FF", 0) < 224:
        raise RuntimeError("Helper report lacks the planned one-cycle/II1 data stage")
    records = []
    for kind, path in files.items():
        root = parent if kind == "parent_caller" else work
        lines = texts[kind].splitlines()
        selected = [index for index, line in enumerate(lines) if
                    (re.search(r"value_\d+_read_reg_\d+", line) if kind == "helper" else
                     re.search(r"assign .*_d1 = .*"+("params1_dout" if kind == "parent_caller" else
                                                   "grp_params1_write_register"), line))]
        if kind != "helper":
            selected = selected[:16]
        records.append({"kind": kind, "workspace_id": root.name, "raw_file": str(path.relative_to(root)),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                        "excerpts": [{"line": index+1, "text": lines[index]} for index in selected]})
    records.append({"kind": "helper_report", "workspace_id": exp_id,
                    "raw_file": str(report.relative_to(work)),
                    "sha256": hashlib.sha256(report.read_bytes()).hexdigest()})
    return {"time": utc(), "id": exp_id, "parent": config["control_experiment"],
            "source_commit": config["source_commit"], "data_register_stage_present": True,
            "data_register_bits": sum(field["bits"] for field in fields),
            "helper_metrics": metrics, "fields": fields, "files": records,
            "scope": "HLS RTL structural evidence only; physical retention, timing and RTL functionality require independent verification."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(EXPERIMENT_ID, args.id):
        parser.error("Need an experiment ID")
    if args.probe:
        print(json.dumps(evidence(args.id)))
        return
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes"]
    remote = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), str(Path(__file__).resolve()),
                    "xiaoxin-ubuntu:"+remote+"/exp/"], check=True)
    command = "cd "+shlex.quote(remote)+"\n"+shlex.join(
        ["python3", "exp/archive_param_registers.py", args.id, "--probe"])
    result = json.loads(subprocess.check_output(ssh+["xiaoxin-ubuntu", command], text=True))
    archive = archived(args.id)
    write_json(archive / "register_evidence.json", result)
    append_log(args.id+": confirmed all224parameter data bits are clocked before bank writes; "
               "helper latency/II1; generated RTL hashes and excerpts in register_evidence.json. Physical benefit remains unverified.")
    print(json.dumps({key: result[key] for key in ("id", "data_register_stage_present", "data_register_bits", "helper_metrics")}))


if __name__ == "__main__":
    main()
