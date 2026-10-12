#!/usr/bin/env python3
"""Collect surviving remote runs before launching the next immutable workspace."""
import argparse
import json
import shlex
import subprocess
import sys
import time
from run_exp import ROOT, check_plan, check_protected


def inspect_remote(config):
    work = "/home/lipuze/amdprojects/90096_CNN_FPGA/workspace/exp_runs/" + config["id"]
    archive = "/home/lipuze/amdprojects/90096_CNN_FPGA/experiments/" + config["id"] + "_" + config["name"]
    program = ("import json,pathlib\nwork=pathlib.Path(" + repr(work) + ")\n"
               "archive=pathlib.Path(" + repr(archive) + ")\n"
               "needle=" + repr(("exp/configs/" + config["id"] + ".json").encode()) + "\n"
               "pids=[]\nfor p in pathlib.Path('/proc').glob('[0-9]*/cmdline'):\n"
               " try:\n  args=p.read_bytes().split(b'\\0')\n"
               " except OSError:\n  continue\n"
               " if b'exp/run_exp.py' in args and needle in args:\n  pids.append(p.parent.name)\n"
               "print(json.dumps(dict(workspace=work.exists(), "
               "complete=(archive/'metrics.json').is_file(), active_pids=pids)))")
    result = subprocess.run(
        ["ssh", "-F", str(ROOT.parent / "ssh-config"), "-o", "BatchMode=yes",
         "-o", "ConnectTimeout=15", "xiaoxin-ubuntu", "python3 -c " + shlex.quote(program)],
        capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ConnectionError(result.stderr.strip())
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="+")
    args = parser.parse_args()
    check_protected()
    for exp_id in args.ids:
        config_path = ROOT / "exp/configs" / (exp_id + ".json")
        config = json.loads(config_path.read_text())
        archive = ROOT / "experiments" / (exp_id + "_" + config["name"])
        check_plan(config, archive)
        while True:
            try:
                remote = inspect_remote(config)
            except (ConnectionError, subprocess.TimeoutExpired) as exc:
                print("RECONNECT", exp_id, str(exc), flush=True)
                time.sleep(30)
                continue
            print("REMOTE", exp_id, json.dumps(remote), flush=True)
            if remote["active_pids"]:
                time.sleep(30)
                continue
            command = [sys.executable, str(ROOT / "exp/remote_exp.py"), str(config_path)]
            if remote["complete"]:
                command.append("--collect-only")
            elif remote["workspace"]:
                raise RuntimeError("Stopped incomplete workspace requires diagnosis; refusing to overwrite " + exp_id)
            result = subprocess.run(command, cwd=ROOT)
            print("RECOVERY", exp_id, "exit", result.returncode, flush=True)
            if (archive / "metrics.json").is_file():
                # Collect again when a transfer succeeded but local bookkeeping was interrupted.
                subprocess.run([sys.executable, str(ROOT / "exp/remote_exp.py"), str(config_path),
                                "--collect-only"], cwd=ROOT, check=True)
                break
            time.sleep(30)


if __name__ == "__main__":
    main()
