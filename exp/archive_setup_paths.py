#!/usr/bin/env python3
"""Read five setup paths from an existing remote routed checkpoint, without rerouting."""
import argparse
import hashlib
import json
import shlex
import subprocess
from pathlib import Path
from analyze_arch import write_csv
from analyze_route import setup_paths
from run_exp import ROOT, append_log, check_protected, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    args = parser.parse_args()
    check_protected()
    archive = next((ROOT / "experiments").glob(args.id+"_*/metrics.json")).parent
    config = json.loads((archive / "config.json").read_text())
    if config.get("operation") != "impl" or not config.get("verification", {}).get("impl_timing_report"):
        raise RuntimeError("A completed routed implementation is required")
    destination = archive / "reports/impl/srcnn_setup5_routed.rpt"
    if destination.is_file():
        print("Already archived setup paths:", args.id)
        return
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    remote_work = remote_root + "/workspace/exp_runs/" + args.id
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    paths = subprocess.check_output(ssh + ["find " + shlex.quote(remote_work) + " -type f -name '*_routed.dcp'"], text=True).splitlines()
    if len(paths) != 1:
        raise RuntimeError("Require one unique routed checkpoint")
    script = ROOT / "exp/report_setup_paths.tcl"
    subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), str(script),
                    "xiaoxin-ubuntu:"+remote_work+"/report_setup_paths.tcl"], check=True)
    output = remote_work+"/srcnn_setup5_routed.rpt"
    command = "cd " + shlex.quote(remote_root) + "\npython3 -c "
    code = ("import sys,hashlib\nfrom pathlib import Path\n"
            "sys.path.insert(0,"+repr(remote_root+"/exp")+")\nfrom run_exp import invoke,lock\n"
            "work=Path("+repr(remote_work)+")\n"
            "with lock(Path('workspace/exp_runs/.synthesis.lock'),wait_timeout=86400):\n"
            "    print('CHECKPOINT_SHA256',hashlib.sha256(Path("+repr(paths[0])+").read_bytes()).hexdigest(),flush=True)\n"
            "    result=invoke(['vivado','-mode','batch','-source',str(work/'report_setup_paths.tcl'),'-notrace','-nojournal','-tclargs',"+repr(paths[0])+","+repr(output)+"],Path("+repr(config["settings"])+"),work,work/'setup_paths.console.log',1800)\n"
            "print(result)\nraise SystemExit(result[0])\n")
    command += shlex.quote(code)
    diagnostic = subprocess.run(ssh + [command], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (archive / "setup_paths_operation.txt").write_text("COMMAND "+command+"\n"+diagnostic.stdout)
    if diagnostic.returncode:
        raise RuntimeError("Post-route path export failed; see setup_paths_operation.txt")
    destination.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), "xiaoxin-ubuntu:"+output, str(destination)],check=True)
    rows = setup_paths(destination.read_text())
    if len(rows) != 5:
        raise RuntimeError("The exported report does not contain five setup paths")
    config["verification_reports"].append({"raw_file":"srcnn_setup5_routed.rpt", "archived_file":str(destination.relative_to(archive)),
                                           "sha256":hashlib.sha256(destination.read_bytes()).hexdigest()})
    report_dir = str(Path(config["verification"]["impl_resource_report"]).parent)
    for state in ("synth", "routed"):
        filename = "srcnn_utilization_hierarchical_"+state+".rpt"
        raw_file = report_dir+"/"+filename
        source = remote_work+"/"+raw_file
        present = subprocess.run(ssh+["test -f "+shlex.quote(source)]).returncode == 0
        if present:
            target = destination.parent / filename
            subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), "xiaoxin-ubuntu:"+source, str(target)], check=True)
            config["verification_reports"].append({"raw_file":raw_file,"archived_file":str(target.relative_to(archive)),
                                                   "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
    config["setup_paths_script_sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
    write_json(archive / "config.json",config)
    write_csv(archive / "critical_paths.csv", rows, list(rows[0]))
    append_log(args.id+": exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.")
    print("Archived five setup paths:", args.id)


if __name__ == "__main__":
    main()
