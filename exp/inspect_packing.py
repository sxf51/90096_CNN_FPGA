#!/usr/bin/env python3
"""Inspect P08's actual routed primitive without archiving generated netlists."""
import argparse
import csv
import json
import shlex
import subprocess
import sys
import time
from run_exp import ROOT, append_log, check_protected, lock, utc, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait",action="store_true")
    args = parser.parse_args()
    check_protected()
    while True:
        with lock(ROOT / "workspace/exp_runs/.results.lock",wait_timeout=120):
            row = next((row for row in csv.DictReader((ROOT / "experiments/results.csv").open(newline=""))
                        if row["id"] == "P08"),None)
        if row:
            break
        if not args.wait:
            raise RuntimeError("P08 is still running")
        print("PRIMITIVE_WAIT P08",flush=True)
        time.sleep(40)
    archive = ROOT / "experiments" / row["md_path"].split("/")[0]
    config_path = archive / "config.json"
    config = json.loads(config_path.read_text())
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    host = "xiaoxin-ubuntu"
    ssh = ["ssh","-F",str(ROOT.parent / "ssh-config"),"-o","BatchMode=yes",host]
    work = remote_root+"/workspace/exp_runs/P08"
    probe = {"time":utc(),"completed":False}
    try:
        paths = subprocess.check_output(ssh+["find "+shlex.quote(work)+" -name '*routed*.dcp'"],text=True).splitlines()
        if not paths:
            raise RuntimeError("No routed checkpoint exists; pre-adder mapping remains unverified")
        checkpoint = sorted(paths)[-1]
        output = work+"/dsp_primitives.csv"
        command = "source "+shlex.quote(config["settings"])+"\n"+shlex.join([
            "vivado","-mode","batch","-nolog","-nojournal","-source",remote_root+"/exp/inspect_dsp.tcl",
            "-tclargs",checkpoint,output])
        probe.update(checkpoint=checkpoint,command=command)
        with (archive / "primitive_inspection.log.txt").open("w") as log:
            subprocess.run(ssh+[command],stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
        subprocess.run(["scp","-F",str(ROOT.parent / "ssh-config"),host+":"+output,
                        str(archive / "dsp_primitives.csv")],check=True)
        cells = {}
        for record in csv.DictReader((archive / "dsp_primitives.csv").open(newline="")):
            cells.setdefault(record["cell"],{})[record["property"]] = record["value"]
        probe.update(completed=True,DSP48E2_cells=len(cells),
                     pre_adder_used=bool(cells) and all(cell.get("AMULTSEL") == "AD" for cell in cells.values()),
                     cells=cells)
    except (subprocess.SubprocessError,RuntimeError) as exc:
        probe["error"] = str(exc)
    config["primitive_probe"] = probe
    write_json(config_path,config)
    write_json(archive / "primitive_probe.json",probe)
    with lock(ROOT / "workspace/exp_runs/.results.lock",wait_timeout=120):
        append_log("P08: routed primitive inspection; "+json.dumps({key:probe.get(key) for key in
                   ("completed","DSP48E2_cells","pre_adder_used","error")}))
    subprocess.run([sys.executable,str(ROOT / "exp/analyze_arch.py")],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT / "exp/commit_exp.py"),"P08","routed_DSP48E2_primitive_attributes"],cwd=ROOT,check=True)
    print(json.dumps({key:probe.get(key) for key in ("completed","DSP48E2_cells","pre_adder_used","error")}),flush=True)


if __name__ == "__main__":
    main()
