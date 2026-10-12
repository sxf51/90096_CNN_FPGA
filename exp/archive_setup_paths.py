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


def select_checkpoint(paths, require_post_route=False):
    final = [path for path in paths if path.endswith("_postroute_physopt.dcp")]
    routed = [path for path in paths if path.endswith("_routed.dcp")]
    if require_post_route and not final:
        raise RuntimeError("Final post-route physical optimization checkpoint is missing")
    selected = final or routed
    if len(selected) != 1:
        raise RuntimeError("Require one unique final implementation checkpoint")
    return selected[0]


def archive_complete(archive, config, script):
    destination = archive / "reports/impl/srcnn_setup5_routed.rpt"
    if (not destination.is_file() or not (archive / "critical_paths.csv").is_file() or
            not (archive / "setup_paths_operation.txt").is_file() or
            config.get("setup_paths_script_sha256") != hashlib.sha256(script.read_bytes()).hexdigest()):
        return False
    if len(setup_paths(destination.read_text())) != 5:
        return False
    if (config.get("implementation_strategy") == "Performance_Explore" and
            config.get("setup_paths_checkpoint", {}).get("stage") != "post_route_phys_opt"):
        return False
    records = [item for item in config.get("verification_reports", [])
               if item["archived_file"] == str(destination.relative_to(archive))]
    return (len(records) == 1 and
            records[0]["sha256"] == hashlib.sha256(destination.read_bytes()).hexdigest())


def register_report(config, archive, target, raw_file):
    relative = str(target.relative_to(archive))
    records = config.setdefault("verification_reports", [])
    records[:] = [item for item in records if item["archived_file"] != relative]
    records.append({"raw_file": raw_file, "archived_file": relative,
                    "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})


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
    script = ROOT / "exp/report_setup_paths.tcl"
    if archive_complete(archive, config, script):
        print("Already archived setup paths:", args.id)
        return
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    remote_work = remote_root + "/workspace/exp_runs/" + args.id
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    paths = subprocess.check_output(ssh + ["find " + shlex.quote(remote_work)
                                          + " -type f \\( -name '*_routed.dcp' -o -name '*_postroute_physopt.dcp' \\)"],
                                    text=True).splitlines()
    checkpoint = select_checkpoint(paths, config.get("implementation_strategy") == "Performance_Explore")
    subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), str(script),
                    "xiaoxin-ubuntu:"+remote_work+"/report_setup_paths.tcl"], check=True)
    output = remote_work+"/srcnn_setup5_routed.rpt"
    command = "cd " + shlex.quote(remote_root) + "\npython3 -c "
    code = ("import sys,hashlib,json\nfrom pathlib import Path\n"
            "sys.path.insert(0,"+repr(remote_root+"/exp")+")\nfrom run_exp import invoke,lock\n"
            "work=Path("+repr(remote_work)+")\n"
            "archive=Path("+repr(remote_root+"/experiments/"+archive.name)+")\n"
            "config=json.loads((archive/'config.json').read_text())\n"
            "print('CHECKPOINT_SHA256',hashlib.sha256(Path("+repr(checkpoint)+").read_bytes()).hexdigest(),flush=True)\n"
            "args=['vivado','-mode','batch','-source',str(work/'report_setup_paths.tcl'),'-notrace','-nojournal','-tclargs',"+repr(checkpoint)+","+repr(output)+"]\n"
            "if config.get('memory_scheduler'):\n"
            "    from memory_scheduler import scheduled_invoke\n"
            "    result=scheduled_invoke(config,archive,'impl',args,Path(config['settings']),work,work/'setup_paths.console.log',1800,telemetry_name='setup_paths')\n"
            "else:\n"
            "    with lock(Path('workspace/exp_runs/.synthesis.lock'),wait_timeout=86400):\n"
            "        result=invoke(args,Path(config['settings']),work,work/'setup_paths.console.log',1800)\n"
            "print(result)\nraise SystemExit(result[0])\n")
    command += shlex.quote(code)
    diagnostic = subprocess.run(ssh + [command], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (archive / "setup_paths_operation.txt").write_text("COMMAND "+command+"\n"+diagnostic.stdout)
    if config.get("memory_scheduler"):
        records = config.setdefault("verification_diagnostics", [])
        for filename in ("setup_paths_admission.json", "setup_paths_host_memory.csv", "scheduler_events.jsonl"):
            raw_file = "experiments/"+archive.name+"/"+filename
            source = remote_root+"/"+raw_file
            present = subprocess.run(ssh+["test -f "+shlex.quote(source)]).returncode
            if present == 1:
                continue
            if present:
                raise RuntimeError("Cannot inspect path-export telemetry: "+raw_file)
            target = archive / filename
            subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), "xiaoxin-ubuntu:"+source,
                            str(target)], check=True)
            records[:] = [item for item in records if item["archived_file"] != filename]
            records.append({"raw_file": raw_file, "archived_file": filename,
                            "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
        write_json(archive / "config.json", config)
    if diagnostic.returncode:
        raise RuntimeError("Post-route path export failed; see setup_paths_operation.txt")
    destination.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), "xiaoxin-ubuntu:"+output, str(destination)],check=True)
    rows = setup_paths(destination.read_text())
    if len(rows) != 5:
        raise RuntimeError("The exported report does not contain five setup paths")
    register_report(config, archive, destination, "srcnn_setup5_routed.rpt")
    report_dir = str(Path(config["verification"]["impl_resource_report"]).parent)
    top = config.get("parent_config", {}).get("top", "srcnn")
    for state in ("synth", "routed"):
        filename = top+"_utilization_hierarchical_"+state+".rpt"
        raw_file = report_dir+"/"+filename
        source = remote_work+"/"+raw_file
        present = subprocess.run(ssh+["test -f "+shlex.quote(source)]).returncode == 0
        if present:
            target = destination.parent / filename
            subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"), "xiaoxin-ubuntu:"+source, str(target)], check=True)
            register_report(config, archive, target, raw_file)
    config["setup_paths_script_sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
    config["setup_paths_checkpoint"] = {
        "raw_file": str(Path(checkpoint).relative_to(Path(remote_work))),
        "stage": "post_route_phys_opt" if checkpoint.endswith("_postroute_physopt.dcp") else "routed"}
    write_csv(archive / "critical_paths.csv", rows, list(rows[0]))
    write_json(archive / "config.json",config)
    append_log(args.id+": exported five setup paths from the existing routed checkpoint; no RTL or constraints changed.")
    print("Archived five setup paths:", args.id)


if __name__ == "__main__":
    main()
