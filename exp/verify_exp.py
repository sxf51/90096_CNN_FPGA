#!/usr/bin/env python3
"""Implementation/cosimulation on an isolated copy of an accepted HLS run."""
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from run_exp import (ROOT, FIELDS, archive_logs, append_log, check_protected,
                     ensure_results_schema, invoke, lock, markdown_table, number,
                     prepare_run_directory, utc, write_json)
from compact_archive import compact


def parse_verification(work, operation):
    detail = []
    for path in sorted(work.rglob("*.xml")):
        if "report" not in path.parts or "syn" in path.parts or path.stat().st_size > 10_000_000:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for node in root.iter():
            value = number(node.text)
            if not list(node) and value is not None:
                detail.append({"file": str(path.relative_to(work)), "metric": node.tag, "value": value})
    observed = {}
    for path in sorted(work.rglob("*.rpt")):
        if "report" not in path.parts and "reports" not in path.parts:
            continue
        if operation == "impl" and ("impl" not in path.parts or "routed" not in path.stem):
            continue
        if operation == "cosim" and "sim" not in path.parts:
            continue
        text = path.read_text(errors="replace")
        for line in text.splitlines():
            fields = [p.strip() for p in line.split("|")[1:-1]]
            if operation == "cosim" and len(fields) >= 8 and fields[0] in {"Verilog", "VHDL"}:
                observed["rtl_status"] = fields[1]
                for key, value in zip(("rtl_latency_min", "rtl_latency_avg", "rtl_latency_max",
                                       "rtl_interval_min", "rtl_interval_avg", "rtl_interval_max"), fields[2:8]):
                    observed[key] = number(value)
            elif operation == "impl" and len(fields) >= 2:
                keys = {"CLB LUTs": "impl_LUT", "Slice LUTs": "impl_LUT",
                        "CLB Registers": "impl_FF", "Slice Registers": "impl_FF",
                        "DSPs": "impl_DSP", "DSP48E2": "impl_DSP",
                        "Block RAM Tile": "impl_BRAM36", "URAM": "impl_URAM"}
                key = keys.get(fields[0].rstrip("* "))
                value = number(fields[1])
                if key and value is not None:
                    observed[key] = value
                    observed["impl_resource_report"] = str(path.relative_to(work))
        if operation == "impl":
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if "WNS(ns)" in line and "TNS(ns)" in line:
                    for candidate in lines[index + 1:index + 7]:
                        values = candidate.split()
                        if values and number(values[0]) is not None:
                            observed["impl_WNS_ns"] = number(values[0])
                            observed["impl_TNS_ns"] = number(values[1]) if len(values) > 1 else None
                            observed["impl_timing_report"] = str(path.relative_to(work))
                            break
    detail.extend({"file": "parsed_rpt", "metric": key, "value": value} for key, value in observed.items())
    return observed, detail


def run_verification(config):
    check_protected()
    exp_id, name, operation = config["id"], config["name"], config["operation"]
    if not re.fullmatch(r"(?:E\d{3,}|[SGPWCF]\d{2,})", exp_id) or not re.fullmatch(r"[a-zA-Z0-9_]+", name):
        raise ValueError("Unsafe verification ID/name")
    parent = next((ROOT / "experiments").glob(config["verify_parent"] + "_*"))
    parent_config = json.loads((parent / "config.json").read_text())
    parent_row = json.loads((parent / "metrics.json").read_text())
    if parent_row.get("csim_pass") is not True or parent_row["status"] not in {"pass", "provisional"}:
        raise RuntimeError("Verification parent is not numerically and resource accepted")
    work = ROOT / "workspace/exp_runs" / exp_id
    archive = ROOT / "experiments" / (exp_id + "_" + name)
    plan = prepare_run_directory(config, work, archive)
    source_work = ROOT / "workspace/exp_runs" / parent_row["id"]
    shutil.copytree(source_work, work, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("*.console.log", "*.zip", "*.wdb", ".run.lock"))
    cfg = work / "hls_config.cfg"
    cfg_text = cfg.read_text().replace(str(source_work), str(work))
    if operation == "cosim":
        cfg_text = cfg_text.replace("tb.cflags=", "tb.cflags=-DEXP_FRAMES=2 ")
        cfg_text += "cosim.rtl=verilog\ncosim.trace_level=none\ncosim.enable_dataflow_profiling=true\n"
    else:
        cfg_text += "vivado.flow=impl\n"
    cfg.write_text(cfg_text)
    shutil.copyfile(cfg, archive / "hls_config.cfg")
    config.update(time=utc(), parent_config=parent_config, parent_metrics=parent_row,
                  source_commit=config.get("source_commit", parent_row["git_commit"]),
                  precision=parent_config.get("precision"), T=parent_config.get("T"),
                  tool_version=parent_config.get("tool_version"))
    for filename, digest in parent_config.get("source_sha256", {}).items():
        if hashlib.sha256((work / "source" / filename).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Frozen parent source mismatch: " + filename)
    row = {k: parent_row.get(k, "") for k in FIELDS}
    row.update(id=exp_id, time=config["time"], stage=config.get("stage", 6),
               series=config.get("series", exp_id[0] if not exp_id.startswith("E") else ""),
               md_path=archive.name + "/" + exp_id + ".md", git_commit=config["source_commit"],
               status="fail", notes=f"{operation} of {parent_row['id']}; HLS estimates inherited, real measurements in data.csv")
    observed, detail, errors = {}, [], []
    settings = Path(config.get("settings", parent_config["settings"]))
    try:
        if config.get("validation_parent"):
            full = next((ROOT / "experiments").glob(config["validation_parent"] + "_*/config.json"))
            validation = json.loads(full.read_text()).get("validation", {})
            delta = number(validation.get("delta_psnr"))
            if (validation.get("csim_pass") is not True or validation.get("bit_exact") is not True or
                    validation.get("image_count") != 13 or delta is None or delta < -.1):
                row["status"] = "precision_fail"
                raise RuntimeError("Selected candidate failed mandatory all-supplied-image validation")
        timeout = 21600 if operation == "cosim" else config.get("timeout", 10800)
        with lock(work / ".run.lock"), lock(ROOT / "workspace/exp_runs/.synthesis.lock", wait_timeout=86400):
            code, seconds = invoke(["vitis-run", "--mode", "hls", "--" + operation,
                                    "--config", str(cfg), "--work_dir", str(work)],
                                   settings, ROOT, work / (operation + ".console.log"), timeout)
        config["operation_minutes"] = seconds / 60
        observed, detail = parse_verification(work, operation)
        if code:
            row["status"] = "timeout" if code == 124 else "fail"
            raise RuntimeError(f"{operation} failed (exit={code})")
        if operation == "impl" and any(observed.get(k) is None for k in
                ("impl_WNS_ns", "impl_DSP", "impl_LUT", "impl_FF")):
            row["status"] = "report_incomplete"
            raise RuntimeError("Missing routed timing/resource evidence; packaging is not implementation")
        if operation == "cosim" and observed.get("rtl_status") != "Pass":
            raise RuntimeError("No passing RTL cosimulation report")
        if operation == "cosim" and any(observed.get(key) is None for key in
                ("rtl_latency_min", "rtl_latency_max", "rtl_interval_min", "rtl_interval_max")):
            row["status"] = "report_incomplete"
            raise RuntimeError("Missing numeric RTL latency/interval evidence for two transactions")
        row["status"] = operation + "_complete"
        if operation == "impl":
            observed["timing_met"] = observed["impl_WNS_ns"] >= 0
            observed["impl_clock_ns_est"] = float(config["clock"]) - observed["impl_WNS_ns"]
        if operation == "cosim":
            actual = observed.get("rtl_latency_max")
            estimate = number(parent_row.get("latency_cycles"))
            if actual is not None and estimate:
                observed["cycle_deviation_pct"] = 100 * (actual / estimate - 1)
        config["verification"] = observed
        detail.extend({"file": "derived", "metric": key, "value": value}
                      for key, value in observed.items()
                      if key in {"cycle_deviation_pct", "timing_met", "impl_clock_ns_est"})
    except Exception as exc:
        errors.append(str(exc))
        row["notes"] += "; " + str(exc)
    finally:
        archive_logs(work, archive)
        config["errors"] = errors
        config["verification"] = observed
        write_json(archive / "config.json", config)
        write_json(archive / "metrics.json", row)
        write_json(archive / "verification.json", observed)
        with (archive / "data.csv").open("w", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=["file", "metric", "value"])
            writer.writeheader()
            writer.writerows(detail)
        for path in work.rglob("*.rpt"):
            if ("report" in path.parts or "reports" in path.parts) and ("impl" in path.parts or "sim" in path.parts):
                dest = archive / "reports" / path.relative_to(work)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
        for path in work.rglob("*.xml"):
            if ("report" in path.parts or "reports" in path.parts) and ("impl" in path.parts or "sim" in path.parts):
                dest = archive / "reports" / path.relative_to(work)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
        md = f"# {exp_id}: {name}\n\n## 1. Purpose and hypothesis / 目的与假设\n\n"
        md += (plan["purpose_section"] if plan else config.get("purpose", f"Validate {parent_row['id']} with {operation} using frozen source.")) + "\n\n"
        md += f"## 2. Changes / 改动\n\nIndependent workspace copy of `{parent_row['id']}`, source commit `{parent_row['git_commit']}`. Cosimulation requests two complete frames to check state reset and transaction interval.\n\n"
        md += "## 3. Configuration / 配置\n\n" + markdown_table([{"parameter": k, "value": v} for k, v in config.items() if k not in {"parent_config", "parent_metrics"}], ["parameter", "value"])
        md += f"\n## 4. Reproduction / 复现\n\n```sh\npython3 exp/run_exp.py --config exp/configs/{exp_id}.json\n```\n\nFrozen parent workspace must exist; no parent directory is overwritten.\n\n"
        md += "## 5. Results / 结果\n\n" + markdown_table([{"metric": k, "value": v} for k, v in observed.items()], ["metric", "value"])
        md += "\nHLS prediction and precision provenance:\n\n" + markdown_table([row], ["latency_cycles", "latency_ms_est", "DSP", "BRAM18K", "LUT", "FF", "csim_pass", "bit_exact", "delta_psnr", "status"])
        md += "\nParent loop II and per-module resources are in the linked parent archive; verification resources are distinct from csynth.\n"
        md += "\n## 6. Interpretation / 解读\n\n" + ("; ".join(errors) if errors else "Actual verification results are parsed from reports in data.csv. Implementation completion alone does not prove timing closure or board operation. Supplied-image precision remains provisional until comic is available.") + "\n"
        md += "\n## 7. Conclusion and next step / 结论与下一步\n\nCompare implementation slack/resources and RTL cycles with HLS estimates. No board result is inferred.\n\n"
        md += f"## 8. Raw files / 原始文件位置\n\n`workspace/exp_runs/{exp_id}/`; parent [{parent_row['id']}](../{parent_row['md_path']}).\n"
        (archive / (exp_id + ".md")).write_text(md)
        results = ROOT / "experiments/results.csv"
        with lock(ROOT / "workspace/exp_runs/.results.lock"):
            ensure_results_schema(results)
            with results.open("a", newline="") as out:
                csv.DictWriter(out, fieldnames=FIELDS).writerow(row)
            append_log(f"{exp_id}: {operation} of {parent_row['id']}; status={row['status']}; " + "; ".join(errors))
        check_protected()
        print(json.dumps(row), flush=True)
    return 0 if row["status"] == operation + "_complete" else 1


if __name__ == "__main__":
    run_verification(json.loads(Path(sys.argv[1]).read_text()))
