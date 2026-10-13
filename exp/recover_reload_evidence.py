#!/usr/bin/env python3
"""Recover failed monitored-run evidence without changing its verdict."""
import argparse
import csv
import hashlib
import json
import shlex
import subprocess
from analyze_arch import write_csv
from recover_remote_queue import inspect_remote
from reload_switch_evidence import check_rtl_metrics, parse_transactions
from reproduce_exp import archived
from run_exp import ROOT, append_log, check_protected, utc, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("id")
    args = parser.parse_args()
    check_protected()
    archive = archived(args.id)
    config = json.loads((archive / "config.json").read_text())
    metrics = json.loads((archive / "metrics.json").read_text())
    if (metrics["status"] not in {"fail", "timeout"} or
            not config.get("reload_switch_validation") or not config.get("parameter_axi_monitor")):
        raise RuntimeError("Recovery is restricted to failed monitored reload-switch runs")
    remote = inspect_remote(config)
    if remote["active_pids"] or not remote["complete"]:
        raise RuntimeError("Wait for the remote run to finish before recovering evidence")
    ssh = ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes", "xiaoxin-ubuntu"]
    remote_root = "/home/lipuze/amdprojects/90096_CNN_FPGA"
    work = remote_root + "/workspace/exp_runs/" + args.id
    program = (
        "import hashlib,json,sys\nfrom pathlib import Path\n"
        "sys.path.insert(0,'exp')\nfrom verify_exp import check_template_rtl\n"
        "work=Path(" + repr(work) + ")\n"
        "if (work/'.run.lock').exists(): raise RuntimeError('Run lock remains active')\n"
        "check=check_template_rtl(Path(" + repr(remote_root + "/workspace/exp_runs/" + config["verify_parent"]) + "),work)\n"
        "names=['hls/sim/verilog/srcnn_reload.performance.result.transaction.xml',"
        "'hls/sim/verilog/reload_parameter_axi.csv','cosim_execute.console.log']\n"
        "files=[{'raw_file':name,'sha256':hashlib.sha256((work/name).read_bytes()).hexdigest()} "
        "for name in names if (work/name).is_file()]\n"
        "print(json.dumps({'rtl_check_after':check,'files':files}))\n")
    observed = json.loads(subprocess.check_output(
        ssh + ["cd " + shlex.quote(remote_root) + "\npython3 -c " + shlex.quote(program)], text=True))
    if observed["rtl_check_after"] != config.get("verification_rtl_check"):
        raise RuntimeError("Synthesis RTL changed after the recorded pre-simulation check")
    records = []
    folder = archive / "parameter_axi_monitor"
    folder.mkdir(exist_ok=True)
    for item in observed["files"]:
        name = item["raw_file"].rsplit("/", 1)[-1]
        destination = folder / (name + ".txt" if name.endswith(".log") else name)
        subprocess.run(["scp", "-F", str(ROOT.parent / "ssh-config"),
                        "xiaoxin-ubuntu:" + work + "/" + item["raw_file"], str(destination)], check=True)
        if hashlib.sha256(destination.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError("Raw measurement changed during recovery")
        records.append({**item, "archived_file": str(destination.relative_to(archive))})
    if not records:
        raise RuntimeError("Failed run has no recoverable measurement files")
    diagnostic = {"time": utc(), "status_preserved": metrics["status"], "accepted": False,
                  "rtl_check_after": observed["rtl_check_after"], "files": records}
    performance = folder / "srcnn_reload.performance.result.transaction.xml"
    bus = folder / "reload_parameter_axi.csv"
    if performance.is_file() and bus.is_file():
        transactions = parse_transactions(performance.read_text())
        with bus.open(newline="") as stream:
            counts = list(csv.DictReader(stream))
        if len(counts) != len(transactions):
            raise RuntimeError("Recovered transaction and AXI counts differ")
        for row, count in zip(transactions, counts):
            if row["transaction"] != int(count["transaction"]):
                raise RuntimeError("Recovered transaction order differs")
            row.update({key: int(value) for key, value in count.items()})
        write_csv(folder / "failed_transactions.csv", transactions, list(transactions[0]))
        diagnostic["transactions"] = transactions
        log = folder / "cosim_execute.console.log.txt"
        if log.is_file():
            try:
                diagnostic["functional_postcheck"] = check_rtl_metrics(log.read_text(), config["parent_metrics"])
            except RuntimeError as exc:
                diagnostic["functional_postcheck_error"] = str(exc)
    write_json(folder / "failed_evidence.json", diagnostic)
    for name in ("failed_evidence.json", "failed_transactions.csv"):
        path = folder / name
        if path.is_file():
            records.append({"archived_file": str(path.relative_to(archive)),
                            "raw_file": "derived from recovered failed-run measurements",
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    existing = config.setdefault("verification_diagnostics", [])
    replaced = {item["archived_file"] for item in records}
    existing[:] = [item for item in existing if item["archived_file"] not in replaced] + records
    config["verification_rtl_check_after"] = observed["rtl_check_after"]
    write_json(archive / "config.json", config)
    append_log(args.id + ": recovered raw failed reload measurements and unchanged synthesis RTL SHA256; original verdict preserved.")
    print(json.dumps(diagnostic, indent=2))


if __name__ == "__main__":
    main()
