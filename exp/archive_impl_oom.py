#!/usr/bin/env python3
"""Archive observed host OOM evidence without revising numerical measurements."""
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from run_exp import ROOT, append_log, check_protected, markdown_table, utc, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    parser.add_argument("--since",required=True)
    parser.add_argument("--until",required=True)
    args = parser.parse_args()
    check_protected()
    archive = next((ROOT / "experiments").glob(args.id+"_*/config.json")).parent
    ssh = ["ssh","-F",str(ROOT.parent / "ssh-config"),"-o","BatchMode=yes","xiaoxin-ubuntu"]
    kernel = "journalctl -k --since "+shlex.quote(args.since)+" --until "+shlex.quote(args.until)+" --no-pager"
    raw = subprocess.check_output(ssh+[kernel],text=True)
    selected = [line for line in raw.splitlines() if any(marker in line for marker in
                ("invoked oom-killer","Total swap", "oom-kill:","Out of memory:"," vivado"))]
    if not any("Out of memory:" in line and "(vivado)" in line for line in selected):
        raise RuntimeError("No confirmed Vivado kernel OOM in the requested interval")
    dest = archive / "diagnostics/kernel_oom.txt"
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text("Retrieved "+utc()+"\nCOMMAND "+kernel+"\n\n"+"\n".join(selected)+"\n")
    config = json.loads((archive / "config.json").read_text())
    config["host_failure"] = {"kind":"kernel_oom","source_command":kernel,
                              "archived_file":"diagnostics/kernel_oom.txt",
                              "sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    remote = "/home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/"+args.id
    command = "find "+shlex.quote(remote+"/hls/impl")+" -path '*/project.runs/*/runme.log' -type f"
    records = []
    for filename in subprocess.check_output(ssh+[command],text=True).splitlines():
        data = subprocess.check_output(ssh+["tail -n 100 "+shlex.quote(filename)],text=True)
        target = archive / "diagnostics" / (Path(filename).parent.name+".txt")
        target.write_text(data)
        records.append({"raw_file":filename,"archived_file":str(target.relative_to(archive)),
                        "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"excerpt":True})
    config["verification_diagnostics"] = records
    write_json(archive / "config.json",config)
    md = archive / (args.id+".md")
    text = md.read_text()
    marker = "\n<!-- AUTO: host failure -->\n"
    section = marker+"\nKernel OOM confirmed during technology mapping; original status stays fail and no routed results are inferred. See diagnostics/kernel_oom.txt and subrun excerpts.\n\n"
    section += markdown_table([config["host_failure"]],["kind","archived_file","sha256"]) + "\n"
    position = text.index("## 7. Conclusion")
    md.write_text(text[:position]+section+text[position:])
    append_log(args.id+": kernel confirms host OOM killed Vivado; archived subrun/kernel evidence, numerical measurements unchanged. Independent serial retries planned as F89-F91.")
    check_protected()


if __name__ == "__main__":
    main()
