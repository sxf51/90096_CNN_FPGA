#!/usr/bin/env python3
"""Run a unique, immutable HLS experiment and archive measured results."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from contextlib import contextmanager
from datetime import datetime, timezone
from compact_archive import compact

ROOT = Path(__file__).resolve().parents[1]
FIELDS = "id,time,stage,series,design,precision_w_a_acc,T_target,unroll_split,weight_storage,clock_target_ns,clock_est_ns,latency_cycles,interval_cycles,latency_ms_est,DSP,DSP_pct,BRAM18K,BRAM_pct,URAM,LUT,LUT_pct,FF,FF_pct,csim_pass,butterfly_mse,border_mse,bit_exact,set14_psnr,delta_psnr,ii_ok,synth_minutes,status,git_commit,md_path,notes".split(",")
ARCH_ID = r"[SGPWCF]\d{2,}"
EXPERIMENT_ID = r"(?:E\d{3,}|" + ARCH_ID + ")"
CAPACITY = {"DSP": 1248, "BRAM18K": 288, "URAM": 64, "LUT": 117120, "FF": 234240}
LIMIT = {"DSP": 1, "BRAM18K": 1, "URAM": 1, "LUT": .7, "FF": .7}


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_protected():
    manifests = [ROOT / "experiments/checksums.txt"]
    architecture_manifest = ROOT / "experiments/phase1_design_checksums.txt"
    if architecture_manifest.exists():
        manifests.append(architecture_manifest)
    for manifest in manifests:
        for line in manifest.read_text().splitlines():
            digest, name = line.split("  ", 1)
            path = ROOT / name
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError("Protected input checksum mismatch: " + name)


def ensure_results_schema(path):
    if not path.exists():
        return
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        header, rows = reader.fieldnames, list(reader)
    if header == FIELDS:
        return
    if header != [field for field in FIELDS if field != "series"]:
        raise RuntimeError("Unexpected results schema; refusing a lossy migration")
    temporary = path.with_suffix(".csv.migrating")
    with temporary.open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({**row, "series": ""} for row in rows)
    temporary.replace(path)


def plan_digest(config):
    runtime = {"source_commit", "plan_sha256", "planned_at"}
    stable = {key: value for key, value in config.items() if key not in runtime}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_plan(config, archive):
    plan_path = archive / "plan.json"
    if not plan_path.is_file() or (archive / "metrics.json").exists():
        raise RuntimeError("Archive is not an unused pre-implementation plan: " + str(archive))
    plan = json.loads(plan_path.read_text())
    if plan["config_sha256"] != plan_digest(config):
        raise RuntimeError("Configuration changed after planning; allocate a new experiment ID")
    text = (archive / (config["id"] + ".md")).read_text()
    purpose = text.split("## 1. Purpose and hypothesis / 目的与假设\n\n", 1)[1].split("\n\n## 2.", 1)[0]
    if purpose != plan["purpose_section"]:
        raise RuntimeError("Planned purpose/estimates changed; allocate a new experiment ID")
    return plan


def prepare_run_directory(config, work, archive):
    if work.exists():
        raise RuntimeError("Experiment workspace already exists; use a new ID: " + config["id"])
    if re.fullmatch(ARCH_ID, config["id"]):
        plan = check_plan(config, archive)
    else:
        plan = None
        if archive.exists():
            raise RuntimeError("Experiment archive already exists; use a new ID: " + config["id"])
        archive.mkdir(parents=True)
    work.mkdir(parents=True)
    return plan


@contextmanager
def lock(path, wait_timeout=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    while True:
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() - started >= wait_timeout:
                raise RuntimeError(f"Run lock exists: {path}; inspect its PID before recovery")
            time.sleep(2)
    try:
        os.write(fd, f"{os.getpid()} {utc()}\n".encode())
        os.close(fd)
        yield
    finally:
        path.unlink(missing_ok=True)


def command_env(args, settings):
    if os.name == "nt":
        body = 'call "' + str(settings) + '"\r\n' + subprocess.list2cmdline(args)
        return ["cmd.exe", "/d", "/s", "/c", body]
    return ["bash", "-c", "source " + shlex.quote(str(settings)) + "\nexec " + shlex.join(args)]


def invoke(args, settings, cwd, logfile, timeout):
    started = time.monotonic()
    with logfile.open("w", encoding="utf-8") as log:
        log.write("COMMAND " + json.dumps(args) + "\n")
        log.flush()
        flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
        proc = subprocess.Popen(command_env(args, settings), cwd=cwd, stdout=log,
                                stderr=subprocess.STDOUT, **flags)
        try:
            code = proc.wait(timeout=timeout)
            return code, time.monotonic() - started
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], check=False, stdout=log, stderr=log)
            else:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    pass
                # Kill descendants even when the group leader exited on SIGTERM.
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            proc.wait()
            log.write(f"\nEXP_TIMEOUT after {timeout} seconds; process tree terminated\n")
            return 124, time.monotonic() - started


def number(value):
    if value is None:
        return None
    try:
        result = float(str(value).strip().replace(",", ""))
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def parse_xml(path):
    root = ET.parse(path).getroot()
    for node in root.iter():
        node.tag = node.tag.split("}")[-1]
    metrics = {}
    specs = {
        "clock_est_ns": ".//SummaryOfTimingAnalysis/EstimatedClockPeriod",
        "latency_cycles": ".//SummaryOfOverallLatency/Worst-caseLatency",
        "interval_cycles": ".//SummaryOfOverallLatency/Interval-max",
        "DSP": ".//AreaEstimates/Resources/DSP",
        "BRAM18K": ".//AreaEstimates/Resources/BRAM_18K",
        "URAM": ".//AreaEstimates/Resources/URAM",
        "LUT": ".//AreaEstimates/Resources/LUT",
        "FF": ".//AreaEstimates/Resources/FF",
    }
    for key, query in specs.items():
        metrics[key] = number(root.findtext(query))
    loops = []
    for node in root.findall(".//SummaryOfLoopLatency/*"):
        item = {child.tag: child.text for child in node}
        item["loop"] = item.get("Name", node.tag)
        item["actual_ii"] = number(item.get("PipelineII"))
        loops.append(item)
    return metrics, loops


def markdown_table(rows, columns):
    def val(x):
        return "unknown" if x is None or x == "" else str(x).replace("|", "\\|").replace("\n", " ")
    return "| " + " | ".join(columns) + " |\n| " + " | ".join(["---"] * len(columns)) + " |\n" + "".join(
        "| " + " | ".join(val(row.get(col)) for col in columns) + " |\n" for row in rows)


def append_log(message):
    path = ROOT / "experiments/LOG.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Pending Human Decisions / 待人工决策"
    text = text.replace(marker, f"- {utc()}: {message}\n\n" + marker, 1)
    path.write_text(text, encoding="utf-8")


def generate_config(config, work):
    snapshot = work / "source"
    source = ROOT / config["design"]
    if not source.is_dir():
        raise RuntimeError("Design not found: " + str(source))
    shutil.copytree(source, snapshot, ignore=shutil.ignore_patterns("weights", "__pycache__"))
    defines = dict(config.get("defines", {}))
    defines.update(EXP_FIXED=int(config.get("fixed", False)), EXP_SET14=int(config.get("set14", False)),
                   EXP_REFERENCE=int(bool(config.get("reference"))), EXP_NUMPY_REFERENCE=int(bool(config.get("numpy_reference"))))
    defines["EXP_QUICK"] = int(config.get("quick", False))
    flags = "-std=c++14 -ffp-contract=off " + " ".join(f"-D{k}={v}" for k, v in defines.items())
    includes = (snapshot.as_posix(), (ROOT / "src").as_posix())
    if any(re.search(r"\s", path) for path in includes):
        raise RuntimeError("Vitis 2026.1 rewrites quoted absolute -I paths incorrectly; use a whitespace-free checkout")
    flags += " " + " ".join("-I" + path for path in includes)
    lines = ["part=xck26-sfvc784-2LV-c", "[hls]", "flow_target=vivado",
             f"clock={config['clock']}ns", "package.output.format=ip_catalog",
             "syn.top=" + config.get("top", "srcnn"), "csim.O=true", "syn.cflags=" + flags, "tb.cflags=" + flags]
    for path in sorted(snapshot.glob("*.cpp")):
        lines.append("syn.file=" + path.as_posix())
    for name in config.get("tb_files", ("exp/tb/validate.cpp", "exp/tb/golden.cpp", "test/tb_conv1.cpp", "test/tb_srcnn.cpp", "test/util.cpp",
                                       "src/weights", "test/set5", "test/set14")):
        lines.append("tb.file=" + (ROOT / name).as_posix())
    if config.get("reference"):
        reference = ROOT / config["reference"]
        shutil.copyfile(reference, work / "fixed_reference.bin")
        lines.append("tb.file=" + (work / "fixed_reference.bin").as_posix())
    if config.get("numpy_reference"):
        shutil.copytree(ROOT / config["numpy_reference"], work / "numpy_reference")
        lines.append("tb.file=" + (work / "numpy_reference").as_posix())
    directives = config.get("directives", [])
    if directives:
        tcl = work / "directives.tcl"
        tcl.write_text("\n".join(directives) + "\n")
        for command in directives:
            tokens = shlex.split(command)
            kind, rest = tokens[0], tokens[1:]
            if kind == "set_directive_pipeline":
                ii = rest[rest.index("-II") + 1] if "-II" in rest else "1"
                lines.append("syn.directive.pipeline=location=" + rest[-1] + " II=" + ii)
            elif kind == "set_directive_array_partition":
                options = {}
                for flag in ("-type", "-factor", "-dim"):
                    if flag in rest:
                        options[flag[1:]] = rest[rest.index(flag) + 1]
                location, variable = rest[-2:]
                lines.append("syn.directive.array_partition=location=" + location + " variable=" + variable + " " +
                             " ".join(f"{k}={v}" for k, v in options.items()))
            else:
                raise ValueError("Unsupported directive; use structured directive_entries: " + kind)
    for key, value in config.get("directive_entries", []):
        lines.append(key + "=" + value)
    for key, value in config.get("options", {}).items():
        lines.append(f"{key}={value}")
    cfg = work / "hls_config.cfg"
    cfg.write_text("\n".join(lines) + "\n")
    config["source_sha256"] = {str(p.relative_to(snapshot)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(snapshot.rglob("*")) if p.is_file()}
    config["compiler_flags"] = flags
    return cfg


def archive_logs(work, archive):
    for operation in ("csim", "csynth", "impl", "cosim", "help", "version"):
        path = work / (operation + ".console.log")
        if path.exists():
            text = path.read_text(errors="replace")
            if len(text) > 2_000_000:
                lines = text.splitlines()
                chosen = lines[:80] + [s for s in lines if re.search(r"WARNING|ERROR|EXP_|Final II|achieved|DSP|BRAM|LUT", s)] + lines[-160:]
                text = "\n".join(chosen)[-2_000_000:]
            (archive / (operation + ".log")).write_text(text)
            # Existing ignore rules exclude *.log in experiments; tracked text is identical.
            (archive / (operation + ".log.txt")).write_text(text)


def run(config):
    if config.get("operation") in {"impl", "cosim"}:
        from verify_exp import run_verification
        return run_verification(config)
    check_protected()
    exp_id, name = config["id"], config["name"]
    if not re.fullmatch(EXPERIMENT_ID, exp_id) or not re.fullmatch(r"[a-zA-Z0-9_]+", name):
        raise ValueError("Unsafe experiment ID or name")
    work = ROOT / "workspace/exp_runs" / exp_id
    archive = ROOT / "experiments" / f"{exp_id}_{name}"
    plan = prepare_run_directory(config, work, archive)
    if "source_commit" not in config:
        config["source_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    config.update(time=utc(), os=platform.platform(), cpu_count=os.cpu_count())
    settings = Path(config.get("settings", os.environ.get("VITIS_SETTINGS", "")))
    row = dict.fromkeys(FIELDS, "")
    row.update(id=exp_id, time=config["time"], stage=config["stage"],
               series=config.get("series", exp_id[0] if re.fullmatch(ARCH_ID, exp_id) else ""), design=config["design"],
               precision_w_a_acc=config.get("precision", "float32"), T_target=config.get("T", ""),
               unroll_split=config.get("unroll", ""), weight_storage=config.get("storage", "default"),
               clock_target_ns=config["clock"], git_commit=config["source_commit"],
               md_path=f"{exp_id}_{name}/{exp_id}.md", notes=config.get("notes", ""), status="fail", csim_pass=False)
    loops, modules, validation = [], [], {}
    errors = []
    try:
        if not settings.is_file():
            raise RuntimeError("Vitis settings script missing; set --settings or VITIS_SETTINGS")
        code, _ = invoke(["vitis-run", "--version"], settings, ROOT, work / "version.console.log", 120)
        if code:
            raise RuntimeError("Vitis version probe failed")
        config["tool_version"] = (work / "version.console.log").read_text().strip()
        cfg = generate_config(config, work)
        shutil.copyfile(cfg, archive / "hls_config.cfg")
        with lock(work / ".run.lock"):
            code, _ = invoke(["vitis-run", "--mode", "hls", "--csim", "--config", str(cfg), "--work_dir", str(work)],
                             settings, ROOT, work / "csim.console.log", config.get("csim_timeout", 2700))
            logs = list(work.rglob("*_csim.log")) + [work / "csim.console.log"]
            for path in logs:
                matches = re.findall(r"EXP_METRICS (\{[^\r\n]+\})", path.read_text(errors="replace"))
                if matches:
                    validation = json.loads(matches[-1])
                    break
            row.update({k: v for k, v in validation.items() if k in row and v is not None})
            config["validation"] = validation
            unknown = re.findall(r"Skipping unknown config[^\n]+", (work / "csim.console.log").read_text(errors="replace"))
            if unknown:
                row["status"] = "invalid_config"
                raise RuntimeError("Tool skipped configuration: " + "; ".join(unknown))
            if code != 0 or not validation.get("csim_pass"):
                row["csim_pass"] = False
                row["status"] = "timeout" if code == 124 else "fail"
                raise RuntimeError(f"C simulation not accepted (exit={code}); synthesis not eligible")
            if config.get("quality_reference"):
                reference_row = json.loads((ROOT / config["quality_reference"]).read_text())
                if (not validation.get("bit_exact") or not config.get("reference") or
                        reference_row["precision_w_a_acc"] != row["precision_w_a_acc"] or
                        reference_row.get("csim_pass") is not True or
                        number(reference_row.get("delta_psnr")) is None):
                    raise RuntimeError("Invalid precision provenance or failed exact comparison")
                for key in ("set14_psnr", "delta_psnr"):
                    row[key] = reference_row[key]
                config["quality_provenance"] = {"path": config["quality_reference"],
                    "method": "Same quantization and butterfly bit identity; quality measured by reference",
                    "image_count": 13}
                if number(row["delta_psnr"]) < -0.1:
                    row["status"] = "precision_fail"
                    raise RuntimeError("Inherited precision point fails the unchanged 0.1 dB gate")
            if config.get("csim_only"):
                row["status"] = "csim_pass"
            else:
                with lock(ROOT / "workspace/exp_runs/.synthesis.lock", wait_timeout=86400):
                    code, seconds = invoke(["v++", "-c", "--mode", "hls", "--config", str(cfg), "--work_dir", str(work)],
                                           settings, ROOT, work / "csynth.console.log", min(config.get("synth_timeout", 3600), 3600))
                row["synth_minutes"] = seconds / 60
                if code:
                    row["status"] = "timeout" if code == 124 else "fail"
                    raise RuntimeError(f"Synthesis failed (exit={code})")
                top = config.get("top", "srcnn")
                reports = sorted(work.rglob(top + "_csynth.xml"))
                if not reports:
                    raise RuntimeError("Missing top csynth XML report")
                metrics, loops = parse_xml(reports[-1])
                row.update({k: v for k, v in metrics.items() if v is not None})
                shutil.copyfile(reports[-1], archive / "csynth.xml")
                for rpt in sorted(work.rglob("*_csynth.rpt")):
                    if rpt.stem == top + "_csynth":
                        shutil.copyfile(rpt, archive / "csynth.rpt")
                for xml in sorted(reports[-1].parent.glob("*_csynth.xml")):
                    module, module_loops = parse_xml(xml)
                    module["module"] = xml.stem.removesuffix("_csynth")
                    modules.append(module)
                    if xml != reports[-1]:
                        for loop in module_loops:
                            loop["module"] = module["module"]
                            loops.append(loop)
                shutil.copytree(reports[-1].parent, archive / "reports",
                                ignore=shutil.ignore_patterns("*.json", "*.adb", "*.log"))
                for key, cap in CAPACITY.items():
                    if metrics.get(key) is not None and key != "URAM":
                        pct_key = "BRAM_pct" if key == "BRAM18K" else key + "_pct"
                        row[pct_key] = 100 * metrics[key] / cap
                if metrics.get("clock_est_ns") is not None and metrics.get("latency_cycles") is not None:
                    row["latency_ms_est"] = metrics["latency_cycles"] * max(config["clock"], metrics["clock_est_ns"]) / 1e6
                targets = config.get("ii_targets", {})
                for loop in loops:
                    loop["target_ii"] = next((v for k, v in targets.items() if k in loop["loop"]),
                                             1 if loop["actual_ii"] is not None else None)
                    if loop["actual_ii"] is not None:
                        loop["ii_ok"] = None if loop["target_ii"] is None else loop["actual_ii"] <= loop["target_ii"]
                compared = [loop for loop in loops if loop.get("target_ii") is not None]
                row["ii_ok"] = all(loop.get("ii_ok") is True for loop in compared) if compared else ""
                complete = (all(metrics.get(k) is not None for k in CAPACITY)
                            and number(row["latency_ms_est"]) is not None
                            and number(row["latency_ms_est"]) >= 0)
                feasible = complete and all(metrics[k] <= CAPACITY[k] * LIMIT[k] for k in CAPACITY)
                row["status"] = "pass" if feasible else "infeasible" if complete else "report_incomplete"
                if config.get("fixed") and validation.get("image_count", 0) < 14 and row["status"] == "pass":
                    row["status"] = "provisional"
                if row["ii_ok"] is False:
                    row["notes"] += "; requested II missed"
                interface_report = ((archive / "csynth.rpt").read_text()
                                    if config.get("required_axi_bundles") else "")
                missing = [bundle for bundle in config.get("required_axi_bundles", [])
                           if "m_axi_" + bundle + "_" not in interface_report]
                if missing:
                    row["status"] = "invalid_config"
                    raise RuntimeError("Required external DDR AXI bundles not generated: " + ", ".join(missing))
    except Exception as exc:
        errors.append(str(exc))
        row["notes"] += "; " + str(exc)
    finally:
        config["errors"] = errors
        config["parsed_loops"] = loops
        config["parsed_modules"] = modules
        if (work / "source").exists():
            shutil.copytree(work / "source", archive / "source", dirs_exist_ok=True)
        write_json(archive / "config.json", config)
        write_json(archive / "metrics.json", row)
        archive_logs(work, archive)
        compact(archive)
        # Reports and model output can be located beneath csim/build, version-dependent.
        for filename in ("quality.csv", "butterfly_output.bin"):
            paths = [p for p in work.rglob(filename)
                     if p.parent.name == "build" and "csim" in p.parts]
            if paths:
                shutil.copyfile(paths[-1], archive / filename)
        detail = [{"kind": "loop", **p} for p in loops] + [{"kind": "module", **p} for p in modules]
        if detail:
            columns = sorted(set().union(*(p.keys() for p in detail)))
            with (archive / "data.csv").open("w", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=columns)
                writer.writeheader()
                writer.writerows(detail)
        command = "python3 exp/run_exp.py --config exp/configs/" + exp_id + ".json"
        cfg_table = markdown_table([{"parameter": k, "value": v} for k, v in config.items()
                                   if k not in {"parsed_loops", "parsed_modules", "validation"}], ["parameter", "value"])
        result_table = markdown_table([{"metric": k, "value": row[k]} for k in FIELDS], ["metric", "value"])
        purpose = plan["purpose_section"] if plan else config.get("purpose", "See stage plan.")
        md = f"# {exp_id}: {name}\n\n## 1. Purpose and hypothesis / 目的与假设\n\n{purpose}\n\n"
        md += f"## 2. Changes / 改动\n\n{config.get('changes', 'Independent source/config snapshot.')} Source commit: `{config['source_commit']}`.\n\n"
        md += "## 3. Configuration / 配置\n\n<!-- AUTO: configuration -->\n\n" + cfg_table
        md += f"\n## 4. Reproduction / 复现\n\n```sh\n{command}\n```\n\nUse a new ID for reruns; existing run directories are immutable. Settings path is recorded in config.json.\n\n"
        md += "## 5. Results / 结果\n\n<!-- AUTO: parsed measurements; blank values are unknown -->\n\n" + result_table
        md += "\n### Pipeline loops\n\n" + (markdown_table(loops, ["loop", "target_ii", "actual_ii", "ii_ok"]) if loops else "No loop report available.\n")
        md += "\n### Module resources\n\n" + (markdown_table(modules, ["module", "DSP", "BRAM18K", "URAM", "LUT", "FF"]) if modules else "No module report available.\n")
        md += f"\n## 6. Interpretation / 解读\n\n{config.get('interpretation', 'Pending report-based interpretation.')}\n"
        if errors:
            md += "\nObserved errors: " + "; ".join(errors) + "\n"
        md += f"\n## 7. Conclusion and next step / 结论与下一步\n\n{config.get('conclusion', 'See current progress and stage summary.')}\n\n"
        md += f"## 8. Raw files / 原始文件位置\n\n`workspace/exp_runs/{exp_id}/` on `{platform.node()}`. Full console logs and source snapshot stay there; archive excerpts are in this directory. No board validation implied.\n"
        (archive / (exp_id + ".md")).write_text(md, encoding="utf-8")
        results = ROOT / "experiments/results.csv"
        with lock(ROOT / "workspace/exp_runs/.results.lock"):
            ensure_results_schema(results)
            header = not results.exists()
            with results.open("a", newline="") as out:
                writer = csv.DictWriter(out, fieldnames=FIELDS)
                if header:
                    writer.writeheader()
                writer.writerow(row)
            append_log(f"{exp_id}: {name}; status={row['status']}; latency_ms_est={row['latency_ms_est'] or 'unknown'}; " + "; ".join(errors))
        check_protected()
        print(json.dumps(row), flush=True)
    return 0 if row["status"] in {"pass", "provisional", "infeasible", "csim_pass", "report_incomplete"} else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--settings")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.settings:
        config["settings"] = args.settings
    return run(config)


if __name__ == "__main__":
    sys.exit(main())
