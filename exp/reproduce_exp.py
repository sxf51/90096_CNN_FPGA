#!/usr/bin/env python3
"""Replay an archived HLS experiment without overwriting its evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from plan_arch import plan
from run_exp import ARCH_ID, EXPERIMENT_ID, ROOT, check_protected, number


def archived(exp_id):
    if not re.fullmatch(EXPERIMENT_ID, exp_id):
        raise ValueError("Invalid archived experiment ID")
    matches = list((ROOT / "experiments").glob(exp_id + "_*/metrics.json"))
    if len(matches) != 1:
        raise ValueError("Expected one completed archive for " + exp_id)
    return matches[0].parent


def next_id(series):
    used = [int(path.stem[1:]) for path in (ROOT / "exp/configs").glob(series + "*.json")
            if re.fullmatch(ARCH_ID, path.stem)]
    return series + str(max([99] + used) + 1)


def make_config(parent_id, new_id, settings=None):
    if not re.fullmatch(ARCH_ID, new_id):
        raise ValueError("A new architecture-prefixed ID is required")
    if ((ROOT / "exp/configs" / (new_id + ".json")).exists() or
            (ROOT / "workspace/exp_runs" / new_id).exists() or
            any((ROOT / "experiments").glob(new_id + "_*"))):
        raise ValueError("Replay ID already reserved: " + new_id)
    folder = archived(parent_id)
    observed = json.loads((folder / "config.json").read_text())
    metrics = json.loads((folder / "metrics.json").read_text())
    original_plan = folder / "plan.json"
    base = (json.loads(original_plan.read_text())["configuration"] if original_plan.is_file()
            else json.loads((ROOT / "exp/configs" / (parent_id + ".json")).read_text()))
    estimates = dict(base.get("estimates", {}))
    for key in ("DSP", "BRAM18K", "URAM", "LUT", "FF", "latency_cycles"):
        value = number(metrics.get(key))
        if value is not None:
            estimates[key] = value
    estimates["T"] = base.get("T", estimates.get("T", 1))
    estimates["basis"] = "Frozen " + parent_id + " measurements where available, otherwise its original paper estimates. Replay the same source, testbench, flags, inputs and tool configuration in an independent workspace; report any deviation."
    if not {"DSP", "BRAM18K", "URAM", "T", "latency_cycles"} <= set(estimates):
        raise ValueError("Non-HLS analyses retain their original script commands")
    config = {**base, "id": new_id, "name": "reproduction_" + parent_id,
              "series": new_id[0], "stage": "arch_reproduction", "estimates": estimates,
              "reproduce_parent": parent_id,
              "frozen_source_commit": observed.get("frozen_source_commit", metrics["git_commit"]),
              "purpose": "Reproduce archived " + parent_id + " using frozen design and testbench sources, unchanged numerical/resource gates and a fresh experiment ID. Original reports and workspaces remain immutable.",
              "changes": "Copy the archived design snapshot and restore code used by its testbench from the recorded Git commit. Parameter flags and protected binary inputs remain unchanged.",
              "interpretation": "Compare exact numerical checks and report values against the frozen parent. A replay is independent evidence and cannot replace the original record.",
              "conclusion": "Retain both records and explain tool/configuration differences if observed."}
    if settings:
        config["settings"] = settings
    if config.get("operation"):
        if config.get("verification_testbench"):
            files = observed.get("testbench_sha256")
            if not files:
                raise ValueError("Frozen verification testbench manifest missing")
            for name, digest in files.items():
                path = folder / "testbench" / name
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    raise ValueError("Frozen verification testbench changed: " + name)
            config["verification_testbench_parent_archive"] = str(folder.relative_to(ROOT))
            config["verification_testbench_manifest"] = files
        return config, None
    source = folder / "source"
    hashes = observed.get("source_sha256", {})
    actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.rglob("*") if path.is_file()}
    if not hashes or actual != hashes:
        raise ValueError("Frozen source snapshot missing or changed: " + parent_id)
    config["design"] = "designs/reproduce_" + new_id
    config["frozen_testbench_root"] = "exp/tb/replay_" + new_id + "/root"
    files = base.get("tb_files", ["exp/tb/validate.cpp", "exp/tb/golden.cpp", "test/tb_conv1.cpp",
                                  "test/tb_srcnn.cpp", "test/util.cpp", "src/weights", "test/set5", "test/set14"])
    old_root = base.get("frozen_testbench_root", "")
    if old_root:
        files = [name[len(old_root) + 1:] if name.startswith(old_root + "/") else name for name in files]
    config["tb_files"] = [config["frozen_testbench_root"] + "/" + name
                          if Path(name).suffix in {".c", ".cc", ".cpp", ".cxx"} else name
                          for name in files]
    return config, source


def prepare(config, source):
    plan(config)
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), config["id"],
                    "plan_reproduction_" + config["reproduce_parent"]], cwd=ROOT, check=True)
    if source is None:
        return
    target = ROOT / config["design"]
    replay = ROOT / config["frozen_testbench_root"]
    if target.exists() or replay.exists():
        raise RuntimeError("Replay source directories already exist")
    shutil.copytree(source, target)
    commit = config["frozen_source_commit"]
    files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", commit,
                                     "--", "src", "test", "exp/tb"], cwd=ROOT, text=True).splitlines()
    for name in files:
        if Path(name).suffix not in {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".inc"}:
            continue
        if name.startswith("exp/tb/replay_"):
            continue
        destination = replay / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(subprocess.check_output(["git", "show", commit + ":" + name], cwd=ROOT))
    for name in config["tb_files"]:
        if Path(name).suffix in {".c", ".cc", ".cpp", ".cxx"} and not (ROOT / name).is_file():
            raise RuntimeError("Recorded testbench unavailable at its source commit: " + name)
    check_protected()
    subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), config["id"],
                    "freeze_reproduction_sources"], cwd=ROOT, check=True)


def execute(exp_id, local):
    script = "run_exp.py" if local else "remote_exp.py"
    args = [sys.executable, str(ROOT / "exp" / script)]
    if local:
        args.append("--config")
    args.append(str(ROOT / "exp/configs" / (exp_id + ".json")))
    result = subprocess.run(args, cwd=ROOT)
    if local:
        subprocess.run([sys.executable, str(ROOT / "exp/commit_exp.py"), exp_id,
                        "reproduction_result"], cwd=ROOT, check=True)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parent")
    parser.add_argument("--id", help="Unused ID; defaults to the next number >=100")
    parser.add_argument("--run", action="store_true", help="Execute after preparing frozen sources")
    parser.add_argument("--local", action="store_true", help="Run Vitis on this machine")
    parser.add_argument("--settings", help="Local settings64.bat/sh override")
    args = parser.parse_args()
    check_protected()
    series = args.parent[0] if re.fullmatch(ARCH_ID, args.parent) else "F"
    exp_id = args.id or next_id(series)
    config, source = make_config(args.parent, exp_id, args.settings)
    if config.get("operation"):
        if not args.run:
            raise ValueError("Verification replay requires --run to rebuild its frozen HLS parent first")
        parent_id = config["verify_parent"]
        parent_new = next_id(parent_id[0] if re.fullmatch(ARCH_ID, parent_id) else "F")
        if parent_new == exp_id:
            parent_new = parent_new[0] + str(int(parent_new[1:]) + 1)
        parent_config, parent_source = make_config(parent_id, parent_new, args.settings)
        prepare(parent_config, parent_source)
        if execute(parent_new, args.local):
            raise RuntimeError("Frozen HLS parent replay failed")
        parent_metrics = json.loads((archived(parent_new) / "metrics.json").read_text())
        if parent_metrics["status"] not in {"pass", "provisional"}:
            from verify_exp import screened_parent
            if not screened_parent(config, parent_metrics, json.loads((archived(parent_new) / "config.json").read_text())):
                raise RuntimeError("Replayed parent is not numerically/resource accepted; verification is ineligible")
        config["verify_parent"] = parent_new
        config["design"] = parent_config["design"]
        if config.get("implementation_backend") == "serial_generated_flow":
            config["implementation_template"] = parent_new
            config["implementation_template_archive"] = str(archived(args.parent).relative_to(ROOT))
        elif config.get("implementation_backend") in {"serial_packaged_flow", "staged_packaged_flow"}:
            config["implementation_driver_archive"] = str(archived(args.parent).relative_to(ROOT))
    prepare(config, source)
    print("Prepared", exp_id, "from", args.parent, flush=True)
    return execute(exp_id, args.local) if args.run else 0


if __name__ == "__main__":
    sys.exit(main())
