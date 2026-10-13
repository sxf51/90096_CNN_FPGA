#!/usr/bin/env python3
"""Archive a fingerprinted paper hypothesis before implementing a design."""
import argparse
import json
import subprocess
from pathlib import Path
from run_exp import ROOT, ARCH_ID, check_protected, markdown_table, plan_digest, utc, write_json
import re


def plan(config):
    check_protected()
    if not re.fullmatch(ARCH_ID, config["id"]):
        raise ValueError("Architecture plan requires a direction-prefixed ID")
    estimates = config["estimates"]
    required = {"DSP", "BRAM18K", "URAM", "T", "latency_cycles", "basis"}
    if not required <= set(estimates):
        raise ValueError("Missing paper estimates: " + ", ".join(sorted(required - set(estimates))))
    config.setdefault("series", config["id"][0])
    config.setdefault("scope", "frame")
    if config["series"] != config["id"][0]:
        raise ValueError("Series must agree with experiment ID")
    archive = ROOT / "experiments" / (config["id"] + "_" + config["name"])
    if archive.exists() or (ROOT / "workspace/exp_runs" / config["id"]).exists():
        raise RuntimeError("Plan ID already exists")
    archive.mkdir(parents=True)
    created = utc()
    purpose = config["purpose"] + "\n\nPre-implementation paper estimates (scope: " + config["scope"] + "):\n\n"
    purpose += markdown_table([{"metric": key, "estimate": value} for key, value in estimates.items()], ["metric", "estimate"]).rstrip()
    purpose += "\n\nPlanned at " + created + "; estimates are hypotheses, not tool measurements."
    fingerprint = plan_digest(config)
    record = {"created_at": created, "config_sha256": fingerprint, "purpose_section": purpose,
              "created_from_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "configuration": config}
    write_json(archive / "plan.json", record)
    write_json(ROOT / "exp/configs" / (config["id"] + ".json"), config)
    text = "# " + config["id"] + ": " + config["name"] + "\n\n## 1. Purpose and hypothesis / 目的与假设\n\n" + purpose + "\n\n"
    text += "## 2. Changes / 改动\n\n" + config.get("changes", "Design not yet implemented.") + "\n\n"
    text += "## 3. Configuration / 配置\n\n<!-- AUTO: planned configuration -->\n\n"
    text += markdown_table([{"parameter": key, "value": value} for key, value in config.items()], ["parameter", "value"])
    text += "\n## 4. Reproduction / 复现\n\n```sh\npython3 exp/remote_exp.py exp/configs/" + config["id"] + ".json\n```\n\n"
    text += "## 5. Results / 结果\n\nNot yet run.\n\n## 6. Interpretation / 解读\n\nCompare the archived estimates with parsed actual measurements after execution.\n\n"
    text += "## 7. Conclusion and next step / 结论与下一步\n\nImplement, strictly validate, then synthesize within the timeout.\n\n"
    text += "## 8. Raw files / 原始文件位置\n\nReserved immutable workspace: `workspace/exp_runs/" + config["id"] + "/`.\n"
    (archive / (config["id"] + ".md")).write_text(text)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(plan(json.loads(args.config.read_text())))


if __name__ == "__main__":
    main()
