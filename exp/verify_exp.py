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
from contextlib import nullcontext
import xml.etree.ElementTree as ET
from run_exp import (ROOT, FIELDS, archive_logs, append_log, check_protected,
                     ensure_results_schema, invoke, lock, markdown_table, number,
                     prepare_run_directory, utc, write_json)
from compact_archive import compact
from archive_cosim_profiles import archive_profiles, profile_results
from host_memory import MemoryMonitor
from route_gates import evaluate_route, parse_route_status


def archive_verification_reports(work, archive, operation):
    records = []
    report_kind = "impl" if operation == "impl" else "sim"
    paths = sorted(path for path in work.rglob("*") if path.is_file() and
                   path.suffix in {".rpt", ".xml"} and
                   {"report", "reports"}.intersection(path.parts) and report_kind in path.parts)
    for path in paths:
        if operation == "impl" and not path.stem.endswith(("timing_routed", "utilization_routed", "status_routed")):
            continue
        dest = archive / "reports" / report_kind / path.name
        if path.resolve() == dest.resolve():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        previous = next((record for record in records if record["archived_file"] == str(dest.relative_to(archive))), None)
        if previous:
            if previous["sha256"] != digest:
                raise RuntimeError("Conflicting verification report basenames: "+path.name)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        records.append({"raw_file":str(path.relative_to(work)),
                        "archived_file":str(dest.relative_to(archive)),"sha256":digest})
    return records


def prepare_serial_implementation(work, template_work, archive, hook_path, template_archive=None,
                                  implementation_clock_ns=None, enable_impl=False, implementation_threads=1,
                                  implementation_strategy=None):
    if type(implementation_threads) is not int or implementation_threads not in {1, 2, 4}:
        raise ValueError("Implementation thread limit must be 1, 2 or 4; synthesis remains single-threaded")
    target = work / "hls/impl"
    if work.resolve() != template_work.resolve():
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(template_work / "hls/impl", target,
                        ignore=shutil.ignore_patterns("project.*", ".Xil", "*.log", "*.jou",
                                                     "*.pb", "report", "*.zip", "*.dcp"))
    old_root = str(template_work)
    if template_archive:
        frozen = json.loads((template_archive / "config.json").read_text())
        old_root = frozen["implementation_work_root"]
        for record in frozen["implementation_files"]:
            source = template_archive / record["archived_file"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != record["sha256"]:
                raise RuntimeError("Frozen implementation script changed: "+str(source))
            destination = work / record["raw_file"] if record.get("raw_file") else target / "verilog" / source.name
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,destination)
    driver = target / "verilog/run_vivado.tcl"
    original = driver.read_text()
    new_root = str(work)
    for path in target.rglob("*"):
        if path.is_file() and path.suffix in {".tcl", ".sh", ".xml", ".xdc"}:
            text = path.read_text()
            if old_root in text:
                path.write_text(text.replace(old_root,new_root))
    text = driver.read_text()
    if enable_impl:
        text, count = re.subn(r"^set has_impl [01]$", "set has_impl 1", text, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError("Cannot enable implementation in the generated package driver")
        text, count = re.subn(r"^set has_synth (?:true|false)$", "set has_synth true", text, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError("Cannot enable synthesis reports in the generated package driver")
    marker = "hls_vivado_reports_setup $report_options"
    if text.count(marker) != 1:
        raise RuntimeError("Unexpected generated Vivado driver; cannot install serial hook")
    local_hook = target / "verilog/serial_synthesis.tcl"
    shutil.copyfile(hook_path,local_hook)
    injection = ("set_param general.maxThreads 1\nset_param synth.maxThreads 1\n"
                 "foreach exp_run [get_runs -filter {IS_SYNTHESIS == 1}] {\n"
                 "  set_property STEPS.SYNTH_DESIGN.TCL.PRE [file normalize ./serial_synthesis.tcl] $exp_run\n"
                 "}\n")
    driver.write_text(text if "STEPS.SYNTH_DESIGN.TCL.PRE" in text else text.replace(marker,injection+marker))
    thread_files = []
    text = re.sub(r"# EXP_IMPLEMENTATION_THREADS_BEGIN\n.*?# EXP_IMPLEMENTATION_THREADS_END\n",
                  "", driver.read_text(), flags=re.DOTALL)
    if implementation_threads != 1:
        route_hook = driver.parent / "bounded_implementation.tcl"
        route_hook.write_text(f"set_param general.maxThreads {implementation_threads}\nset_param synth.maxThreads 1\n"
                              'puts "EXP_VIVADO_IMPL_THREADS general=[get_param general.maxThreads] synth=[get_param synth.maxThreads]"\n')
        block = ("# EXP_IMPLEMENTATION_THREADS_BEGIN\nsource ./bounded_implementation.tcl\n"
                 "foreach exp_impl_run [get_runs -filter {IS_IMPLEMENTATION == 1}] {\n"
                 "  set_property STEPS.OPT_DESIGN.TCL.PRE [file normalize ./bounded_implementation.tcl] $exp_impl_run\n"
                 "}\n# EXP_IMPLEMENTATION_THREADS_END\n")
        text = text.replace(marker, block+marker)
        thread_files.append(("implementation_thread_hook", route_hook))
    text = re.sub(r"# EXP_IMPLEMENTATION_STRATEGY_BEGIN\n.*?# EXP_IMPLEMENTATION_STRATEGY_END\n",
                  "", text, flags=re.DOTALL)
    if implementation_strategy:
        if implementation_strategy != "Performance_Explore":
            raise ValueError("Only the independently probed Performance_Explore strategy is allowed")
        strategy_hook = driver.parent / "implementation_strategy.tcl"
        strategy_hook.write_text(
            'foreach exp_impl_run [get_runs -filter {IS_IMPLEMENTATION == 1}] {\n'
            '  set_property strategy Performance_Explore $exp_impl_run\n'
            '  set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true $exp_impl_run\n'
            '  puts "EXP_VIVADO_STRATEGY run=$exp_impl_run strategy=[get_property STRATEGY $exp_impl_run] '
            'post_route_phys_opt=[get_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED $exp_impl_run]"\n'
            '}\n')
        text = text.replace(marker, '# EXP_IMPLEMENTATION_STRATEGY_BEGIN\nsource ./implementation_strategy.tcl\n'
                            '# EXP_IMPLEMENTATION_STRATEGY_END\n' + marker)
        thread_files.append(("implementation_strategy_hook", strategy_hook))
    driver.write_text(text)
    constraints = []
    if implementation_clock_ns is not None:
        period = number(implementation_clock_ns)
        if period is None or period <= 0:
            raise RuntimeError("Implementation clock must be a positive period")
        updated, count = re.subn(r'^set target_clk_period_ns "[\d.]+"$',
                                 f'set target_clk_period_ns "{period:.3f}"', driver.read_text(), flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError("Cannot locate the generated implementation clock")
        driver.write_text(updated)
        xdc_files = sorted(driver.parent.glob("*.xdc")) + sorted((target / "ip/constraints").glob("*.xdc"))
        for path in xdc_files:
            original_constraint = path.read_text()
            updated, count = re.subn(
                r'^create_clock -name ap_clk -period [\d.]+(?: -waveform \{[\d.]+ [\d.]+\})? \[get_ports ap_clk\]$',
                f'create_clock -name ap_clk -period {period:.3f} -waveform {{0.000 {period/2:.3f}}} [get_ports ap_clk]',
                original_constraint, flags=re.MULTILINE)
            if count:
                if count != 1:
                    raise RuntimeError("Ambiguous ap_clk implementation constraints")
                path.write_text(updated)
                constraints.append(path)
        if sum(path.parent == driver.parent for path in constraints) != 1:
            raise RuntimeError("Require exactly one top-level generated ap_clk XDC constraint")
    records = []
    for label,path in (("driver",driver),("thread_hook",local_hook),
                       *thread_files,
                       ("settings",driver.parent / "settings.tcl"),
                       ("report_extraction",driver.parent / "extraction.tcl"),
                       *(("implementation_constraint", path) for path in constraints)):
        if not path.is_file():
            raise RuntimeError("Generated-flow dependency missing: "+str(path))
        dest = archive / "implementation" / path.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,dest)
        records.append({"kind":label,"archived_file":str(dest.relative_to(archive)),
                        "raw_file":str(path.relative_to(work)),
                        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest()})
    return driver.parent, records, hashlib.sha256(original.encode()).hexdigest()


def package_only_config(cfg, target):
    text = cfg.read_text()
    text = re.sub(r"^vivado\.flow=.*\n?", "", text, flags=re.MULTILINE)
    target.write_text(text.rstrip()+"\nvivado.flow=none\n")
    return target


def rtl_manifest(work):
    source = work / "hls/syn/verilog"
    hashes = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source.rglob("*") if path.is_file() and path.suffix in {".v", ".sv", ".dat", ".mem", ".hex"}}
    if not any(name.endswith((".v", ".sv")) for name in hashes):
        raise RuntimeError("Frozen parent RTL is missing: "+str(source))
    return hashes


def check_template_rtl(parent_work, template_work):
    parent, template = rtl_manifest(parent_work), rtl_manifest(template_work)
    if parent != template:
        raise RuntimeError("Implementation template RTL differs from the frozen parent; package this parent independently")
    digest = hashlib.sha256(json.dumps(parent, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"files_checked": len(parent), "manifest_sha256": digest, "template_matches_parent": True}


def prepare_packaged_driver(work, template_work, archive, parent_config, exp_id, template_archive=None):
    target = work / "hls/impl/verilog"
    if (target / "run_vivado.tcl").is_file():
        return []
    component = work / "hls/impl/ip/component.xml"
    if not component.is_file():
        raise RuntimeError("Independent candidate IP package is missing")
    fields = {node.tag.rsplit("}", 1)[-1]: node.text for node in ET.parse(component).getroot()}
    if tuple(fields.get(key) for key in ("vendor", "library", "name", "version")) != ("xilinx.com", "hls", "srcnn", "1.0"):
        raise RuntimeError("Packaged candidate VLNV does not match this generated SRCNN flow")
    template = template_work / "hls/impl/verilog"
    old_root = str(template_work)
    if template_archive:
        frozen = json.loads((template_archive / "config.json").read_text())
        old_root = frozen["implementation_driver_template_work_root"]
        files = [(template_archive / record["archived_file"], record["sha256"])
                 for record in frozen["implementation_driver_template_files"]]
    else:
        paths = [template / name for name in ("run_vivado.tcl", "settings.tcl", "extraction.tcl")]
        paths += sorted(template.glob("*.xdc"))
        files = [(path, hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
    if not any(path.suffix == ".xdc" for path, _ in files):
        raise RuntimeError("Generated driver template has no top-level clock constraint")
    records = []
    target.mkdir(parents=True, exist_ok=True)
    for path, digest in files:
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError("Generated driver template archive changed")
        dest = archive / "driver_template" / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        records.append({"archived_file": str(dest.relative_to(archive)), "sha256": digest})
        (target / path.name).write_text(path.read_text().replace(old_root, str(work)))
    settings = (target / "settings.tcl").read_text()
    for key, value in (("top_module", "srcnn"), ("language", "verilog"), ("device", "xck26"),
                       ("package", "-sfvc784"), ("speed", "-2LV-c"), ("clock", "ap_clk")):
        if not re.search(r"^set "+key+" "+re.escape(value)+"$", settings, re.MULTILINE):
            raise RuntimeError("Generated flow template has incompatible "+key)
    available = {path.stem for path in (work / "hls/syn/verilog").glob("*.v")}
    if "srcnn" not in available or any(not re.fullmatch(r"[A-Za-z_]\w*", name) for name in available):
        raise RuntimeError("Cannot determine candidate RTL modules for generated reports")
    functions = sorted({"srcnn_"+item["module"] for item in parent_config.get("parsed_modules", [])} & available)
    bindings = sorted(available-set(functions)-{"srcnn"})
    driver = target / "run_vivado.tcl"
    text = driver.read_text()
    for key, value in (("funcmodules", "{"+" ".join(functions)+"}"),
                       ("bindmodules", "{"+" ".join(bindings)+"}"), ("hls_project", exp_id)):
        text, count = re.subn(r"^dict set report_options "+key+r" .*?$",
                              "dict set report_options "+key+" "+value, text, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError("Cannot replace generated report option "+key)
    driver.write_text(text)
    return records


def vivado_diagnostic_excerpt(text):
    lines = text.splitlines()
    useful = lines[:60] + [line for line in lines if re.search(
        r"EXP_VIVADO_(?:IMPL_)?THREADS|Synth 8-707\d|ERROR:|CRITICAL WARNING:|Killed|terminate|Memory \(MB\)|Finished.*Optimization",line)] + lines[-100:]
    return "\n".join(useful)+"\n"


def archive_verification_diagnostics(work,archive):
    records = []
    for path in sorted(work.glob("hls/impl/*/project.runs/*/runme.log")):
        dest = archive / "diagnostics" / (path.parent.name+".txt")
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(vivado_diagnostic_excerpt(path.read_text(errors="replace")))
        records.append({"raw_file":str(path.relative_to(work)),"archived_file":str(dest.relative_to(archive)),
                        "raw_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                        "sha256":hashlib.sha256(dest.read_bytes()).hexdigest(),"excerpt":True})
    return records


def parse_verification(work, operation):
    detail = []
    for path in sorted(work.rglob("*.xml")):
        if not {"report", "reports"}.intersection(path.parts) or "syn" in path.parts or path.stat().st_size > 10_000_000:
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
            observed.update(parse_route_status(text))
            lines = text.splitlines()
            for index, line in enumerate(lines):
                if "WNS(ns)" in line and "TNS(ns)" in line:
                    for candidate in lines[index + 1:index + 7]:
                        values = candidate.split()
                        if values and number(values[0]) is not None:
                            observed["impl_WNS_ns"] = number(values[0])
                            observed["impl_TNS_ns"] = number(values[1]) if len(values) > 1 else None
                            if len(values) >= 6 and "WHS(ns)" in line:
                                observed["impl_WHS_ns"] = number(values[4])
                                observed["impl_THS_ns"] = number(values[5])
                            if len(values) >= 10 and "TPWS(ns)" in line:
                                observed["impl_TPWS_ns"] = number(values[9])
                            observed["impl_timing_report"] = str(path.relative_to(work))
                            break
    if operation == "impl":
        logfile = work / "impl.console.log"
        if logfile.exists():
            observed.update(parse_route_status(logfile.read_text(errors="replace")))
        observed = evaluate_route(observed)
    detail.extend({"file": "parsed_rpt", "metric": key, "value": value} for key, value in observed.items())
    return observed, detail


def diagnostic_parent(config, parent):
    return (config["operation"] == "impl" and config.get("diagnostic_infeasible_parent") is True and
            parent.get("csim_pass") is True and parent["status"] == "infeasible" and
            parent.get("bit_exact") is True and number(parent.get("delta_psnr")) is not None and
            number(parent["delta_psnr"]) >= -.1)


def screened_parent(config, parent, parent_config):
    return (config.get("resource_policy") == "routed" and parent_config.get("hls_screen_pass") is True and
            parent.get("csim_pass") is True and parent.get("bit_exact") is True and
            parent.get("status") in {"pass", "provisional", "infeasible"} and
            number(parent.get("delta_psnr")) is not None and number(parent["delta_psnr"]) >= -.1)


def check_image_validation(parent_config, validation_config):
    validation = validation_config.get("validation", {})
    delta = number(validation.get("delta_psnr"))
    if (validation.get("csim_pass") is not True or validation.get("bit_exact") is not True or
            validation.get("image_count") != 13 or delta is None or delta < -.1):
        raise RuntimeError("Selected candidate failed mandatory all-supplied-image validation")
    hashes = parent_config.get("source_sha256", {})
    if not hashes or validation_config.get("source_sha256") != hashes:
        raise RuntimeError("Full-image validation source differs from the frozen candidate")
    tb_only = {"EXP_FRAMES", "EXP_SET14", "EXP_QUICK", "EXP_REFERENCE", "EXP_NUMPY_REFERENCE"}
    flags = lambda cfg: {key: value for key, value in cfg.get("defines", {}).items() if key not in tb_only}
    if (flags(parent_config) != flags(validation_config) or
            any(parent_config.get(key) != validation_config.get(key) for key in ("fixed", "precision"))):
        raise RuntimeError("Full-image validation arithmetic flags differ from the frozen candidate")


def prepare_verification_testbench(text, config, work, archive):
    if not config.get("verification_testbench"):
        if config.get("reload_params"):
            raise RuntimeError("Changed-parameter verification requires an independent testbench")
        return text
    if config["operation"] != "cosim":
        raise RuntimeError("Verification testbench override requires cosimulation")
    replay = config.get("verification_testbench_parent_archive")
    source = ROOT / config["verification_testbench"]
    if replay:
        source = ROOT / replay / "testbench" / source.name
        expected = config.get("verification_testbench_manifest", {}).get(source.name)
        if not expected or hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            raise RuntimeError("Frozen verification testbench changed or lacks its manifest")
    elif not str(Path(config["verification_testbench"])).startswith("exp/tb/"):
        raise RuntimeError("New verification testbenches must be under exp/tb")
    target = work / "testbench" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    dest = archive / "testbench" / source.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    config["testbench_sha256"] = {source.name: hashlib.sha256(dest.read_bytes()).hexdigest()}
    # Keep binary inputs and design flags; only the verification translation units change.
    lines = [line for line in text.splitlines() if not (
        line.startswith("tb.file=") and Path(line.split("=", 1)[1]).suffix.lower() in
        {".c", ".cc", ".cpp", ".cxx"})]
    lines.append("tb.file=" + target.as_posix())
    return "\n".join(lines) + "\n"


def reload_measurement(logfile, parent):
    matches = re.findall(r"EXP_METRICS (\{[^\r\n]+\})", logfile.read_text(errors="replace"))
    if len(matches) < 2:
        raise RuntimeError("Missing C and RTL changed-parameter testbench checks")
    result = json.loads(matches[-1])
    if (result.get("csim_pass") is not True or result.get("bit_exact") is not True or
            result.get("reload_pass") is not True or result.get("frame_count") != 2 or
            result.get("reload_expected") != 104 / 256 or
            result.get("border_mse") != number(parent.get("border_mse"))):
        raise RuntimeError("Changed-parameter testbench failed exact frame/border/reload gates")
    return result


def rom_measurement(logfile, parent):
    matches = re.findall(r"EXP_METRICS (\{[^\r\n]+\})", logfile.read_text(errors="replace"))
    if len(matches) < 2:
        raise RuntimeError("Missing C and RTL ROM changed-input checks")
    for match in matches:
        result = json.loads(match)
        if (result.get("csim_pass") is not True or result.get("bit_exact") is not True or
                result.get("same_weights_changed_input") is not True or
                result.get("changed_input_pass") is not True or result.get("frame_count") != 2 or
                result.get("border_mse") != number(parent.get("border_mse"))):
            raise RuntimeError("ROM changed-input testbench failed exact frame/border gates")
    return json.loads(matches[-1])


def run_verification(config):
    check_protected()
    exp_id, name, operation = config["id"], config["name"], config["operation"]
    if not re.fullmatch(r"(?:E\d{3,}|[SGPWCF]\d{2,})", exp_id) or not re.fullmatch(r"[a-zA-Z0-9_]+", name):
        raise ValueError("Unsafe verification ID/name")
    parent = next((ROOT / "experiments").glob(config["verify_parent"] + "_*"))
    parent_config = json.loads((parent / "config.json").read_text())
    parent_row = json.loads((parent / "metrics.json").read_text())
    diagnostic = diagnostic_parent(config, parent_row)
    if parent_row.get("csim_pass") is not True or (parent_row["status"] not in {"pass", "provisional"} and
            not diagnostic and not screened_parent(config, parent_row, parent_config)):
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
        cfg_text = prepare_verification_testbench(cfg_text, config, work, archive)
        cfg_text = re.sub(r"^(tb\.cflags=)(.*)$", lambda match: match[1] +
                          re.sub(r"(?:^|\s)-DEXP_FRAMES=\d+", "", match[2]) + " -DEXP_FRAMES=2",
                          cfg_text, flags=re.MULTILINE)
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
    if diagnostic:
        row["notes"] += "; diagnostic only: parent remains HLS-resource-infeasible and cannot enter accepted rankings"
    observed, detail, errors = {}, [], []
    impl_cwd = None
    package_serial = config.get("implementation_backend") == "serial_packaged_flow"
    if package_serial and operation != "impl":
        raise RuntimeError("Serial packaged flow is only valid for implementation")
    settings = Path(config.get("settings", parent_config["settings"]))
    try:
        if operation == "cosim":
            config["verification_rtl_check"] = check_template_rtl(source_work, work)
        if config.get("implementation_backend") == "serial_generated_flow":
            if operation != "impl":
                raise RuntimeError("Serial generated flow is only valid for implementation")
            template = ROOT / "workspace/exp_runs" / config["implementation_template"]
            config["implementation_rtl_check"] = check_template_rtl(source_work, template)
            template_archive = ROOT / config["implementation_template_archive"] if config.get("implementation_template_archive") else None
            impl_cwd, records, original_digest = prepare_serial_implementation(
                work,template,archive,ROOT / config["verification_hook"],template_archive,
                config.get("implementation_clock_ns"),
                implementation_threads=config.get("implementation_threads", 1),
                implementation_strategy=config.get("implementation_strategy"))
            config["implementation_files"] = records
            config["original_generated_driver_sha256"] = original_digest
            config["implementation_work_root"] = str(work)
        if config.get("validation_parent"):
            full = next((ROOT / "experiments").glob(config["validation_parent"] + "_*/config.json"))
            try:
                check_image_validation(parent_config, json.loads(full.read_text()))
            except RuntimeError:
                row["status"] = "precision_fail"
                raise
        timeout = 21600 if operation == "cosim" else config.get("timeout", 10800)
        legacy_slot = (nullcontext() if config.get("memory_scheduler") else
                       lock(ROOT / "workspace/exp_runs/.synthesis.lock", wait_timeout=86400))
        with lock(work / ".run.lock"), legacy_slot:
            if package_serial:
                package_cfg = package_only_config(cfg, work / "package_config.cfg")
                shutil.copyfile(package_cfg, archive / "package_config.cfg")
                with MemoryMonitor(archive / "package_host_memory.csv"):
                    package_code, package_seconds = invoke(
                        ["vitis-run", "--mode", "hls", "--package", "--config", str(package_cfg), "--work_dir", str(work)],
                        settings, ROOT, work / "package.console.log", 600)
                config["package_minutes"] = package_seconds / 60
                if package_code:
                    raise RuntimeError(f"Package-only export failed (exit={package_code})")
                config["implementation_rtl_check"] = check_template_rtl(source_work, work)
                template_work = ROOT / "workspace/exp_runs" / config.get("implementation_driver_template", "F89")
                template_archive = ROOT / config["implementation_driver_archive"] if config.get("implementation_driver_archive") else None
                config["implementation_driver_template_files"] = prepare_packaged_driver(
                    work, template_work, archive, parent_config, exp_id, template_archive)
                if config["implementation_driver_template_files"]:
                    config["implementation_driver_template_work_root"] = str(template_work)
                impl_cwd, records, original_digest = prepare_serial_implementation(
                    work, work, archive, ROOT / config["verification_hook"],
                    implementation_clock_ns=config.get("implementation_clock_ns", config["clock"]), enable_impl=True,
                    implementation_threads=config.get("implementation_threads", 1),
                    implementation_strategy=config.get("implementation_strategy"))
                config["implementation_files"] = records
                config["original_generated_driver_sha256"] = original_digest
                config["implementation_work_root"] = str(work)
            if impl_cwd:
                args = ["vivado","-mode","batch","-source","run_vivado.tcl","-notrace","-nojournal"]
                cwd = impl_cwd
            else:
                args = ["vitis-run", "--mode", "hls", "--" + operation,
                        "--config", str(cfg), "--work_dir", str(work)]
                cwd = ROOT
            with MemoryMonitor(archive / "host_memory.csv"):
                if config.get("memory_scheduler"):
                    from memory_scheduler import scheduled_invoke
                    code, seconds = scheduled_invoke(config, archive, operation, args, settings, cwd,
                                                     work / (operation + ".console.log"), timeout)
                else:
                    code, seconds = invoke(args,settings,cwd,work / (operation + ".console.log"),timeout)
        config["operation_minutes"] = seconds / 60
        observed, detail = parse_verification(work, operation)
        if operation == "cosim":
            config["verification_rtl_check_after"] = check_template_rtl(source_work, work)
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
        if operation == "cosim" and config.get("reload_params"):
            config["reload_validation"] = reload_measurement(work / "cosim.console.log", parent_row)
            observed["changed_params_bit_exact"] = True
        if operation == "cosim" and config.get("same_weights_changed_input"):
            config["rom_validation"] = rom_measurement(work / "cosim.console.log", parent_row)
            observed["same_weights_changed_input_bit_exact"] = True
        if operation == "cosim" and config.get("rtl_max_cycles") is not None:
            if observed["rtl_latency_max"] > config["rtl_max_cycles"]:
                raise RuntimeError("Measured RTL cycles exceed the preplanned acceptance bound")
        row["status"] = operation + "_complete"
        if operation == "impl":
            if not config.get("resource_policy") == "routed":
                observed["timing_met"] = observed["impl_WNS_ns"] >= 0
            observed["impl_target_clock_ns"] = float(config.get("implementation_clock_ns", config["clock"]))
            observed["impl_clock_ns_est"] = observed["impl_target_clock_ns"] - observed["impl_WNS_ns"]
            row["route_feasible"] = observed.get("route_feasible")
        if operation == "cosim":
            actual = observed.get("rtl_latency_max")
            estimate = number(parent_row.get("latency_cycles"))
            if actual is not None and estimate:
                observed["cycle_deviation_pct"] = 100 * (actual / estimate - 1)
        config["verification"] = observed
        detail.extend({"file": "derived", "metric": key, "value": value}
                      for key, value in observed.items()
                      if key in {"cycle_deviation_pct", "timing_met", "impl_clock_ns_est", "route_feasible"})
    except Exception as exc:
        errors.append(str(exc))
        row["notes"] += "; " + str(exc)
    finally:
        archive_logs(work, archive)
        config["verification_reports"] = archive_verification_reports(work,archive,operation)
        config["verification_diagnostics"] = archive_verification_diagnostics(work,archive)
        if operation == "cosim" and observed.get("rtl_status") == "Pass":
            try:
                config["verification_profiles"] = archive_profiles(work,archive)
            except Exception as exc:
                config["profiling_archive_error"] = str(exc)
                row["notes"] += "; profiling archive unavailable: "+str(exc)
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
        md += f"## 2. Changes / 改动\n\nIndependent workspace copy of `{parent_row['id']}`, source commit `{parent_row['git_commit']}`. Cosimulation requests two complete frames to check state reset and transaction interval."
        if config.get("reload_params"):
            md += " The second frame uses changed runtime weights/biases and constant0.5 input, requiring exact104/256 at every output; the first frame retains E017 butterfly and border checks. Independent testbench source is frozen in testbench/ at verification commit `" + config["source_commit"] + "`."
        if config.get("same_weights_changed_input"):
            md += " Both frames use the same compile-time ROM weights; the second input changes from butterfly to lenna. "
            md += "Every output bit matches the independent w10a10 reference. There is no runtime parameter port, so changed-parameter verification is inapplicable."
        md += "\n\n"
        md += "## 3. Configuration / 配置\n\n" + markdown_table([{"parameter": k, "value": v} for k, v in config.items() if k not in {"parent_config", "parent_metrics"}], ["parameter", "value"])
        md += f"\n## 4. Reproduction / 复现\n\n```sh\npython3 exp/reproduce_exp.py {exp_id} --run\n```\n\nThis rebuilds a fresh frozen parent before verification; see [reproduction guide](../REPRODUCE.md). Original reserved invocation:\n\n```sh\npython3 exp/run_exp.py --config exp/configs/{exp_id}.json\n```\n\nNo parent directory is overwritten.\n\n"
        md += "## 5. Results / 结果\n\n" + markdown_table([{"metric": k, "value": v} for k, v in observed.items()], ["metric", "value"])
        md += "\nHLS prediction and precision provenance:\n\n" + markdown_table([row], ["latency_cycles", "latency_ms_est", "DSP", "BRAM18K", "LUT", "FF", "csim_pass", "bit_exact", "delta_psnr", "status"])
        md += "\nParent loop II and per-module resources are in the linked parent archive; verification resources are distinct from csynth.\n"
        md += "\nArchived verification source reports (neutral paths preserve Git tracking):\n\n"
        md += markdown_table(config["verification_reports"],["raw_file","archived_file","sha256"])
        md += profile_results(archive)
        if config.get("implementation_files"):
            md += "\nIndependent generated-flow retry files:\n\n"
            md += markdown_table(config["implementation_files"],["kind","archived_file","sha256"])
        if config["verification_diagnostics"]:
            md += "\nVivado subrun diagnostic excerpts:\n\n"
            md += markdown_table(config["verification_diagnostics"],["raw_file","archived_file","raw_sha256","sha256","excerpt"])
        default = "Actual verification results are parsed from reports in data.csv. Implementation completion alone does not prove timing closure or board operation."
        if config.get("required_image_count") == 13:
            default += " The complete course-provided Set14 set contains 13 images under docs/0005."
        else:
            default += " Supplied-image precision remains provisional until comic is available."
        md += "\n## 6. Interpretation / 解读\n\n" + ("; ".join(errors) if errors else default) + "\n"
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
