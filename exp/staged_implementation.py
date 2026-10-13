"""Release the synthesis design before launching Vivado implementation."""
import hashlib
from pathlib import Path
import shutil


def split_driver(text):
    project = "create_project $vivado_proj_name $vivado_proj_dir -part $target_device -force\n"
    implementation = "if { $has_impl } {\n  # launch run impl\n"
    if text.count(project) != 1 or text.count(implementation) != 1:
        raise RuntimeError("Cannot split an unfamiliar generated Vivado driver")
    header, setup = text.split(project)
    synthesis, route = setup.split(implementation)
    if (synthesis.count("hls_vivado_reports_synth synth_1 $report_options") != 1
            or synthesis.count("wait_on_run synth_1") != 1
            or route.count("wait_on_run impl_1") != 1
            or route.count("hls_vivado_reports_impl impl_1 $report_options") != 1
            or "launch_runs impl_1" in synthesis or "reset_run" in route
            or "launch_runs synth_1" in route):
        raise RuntimeError("Generated flow lacks a complete, isolated synthesis/implementation boundary")
    synth_script = (header + project + synthesis
                    + '\nputs "EXP_STAGED_SYNTH_REPORT_DONE"\nclose_design\nclose_project\nexit\n')
    route_script = (header
                    + '\nopen_project [file normalize ${vivado_proj_dir}/${vivado_proj_name}.xpr]\n'
                    + 'if { [get_property PROGRESS [get_runs synth_1]] ne "100%" } {\n'
                    + '  error "Staged implementation requires completed synthesis"\n}\n'
                    + 'set_param general.maxThreads 1\nset_param synth.maxThreads 1\n'
                    + 'puts "EXP_STAGED_PROJECT_REOPENED"\n'
                    + implementation + route + '\nclose_design\nclose_project\nexit\n')
    return synth_script, route_script


def prepare_staged_driver(work, archive, cwd):
    original = (cwd / "run_vivado.tcl").read_text()
    contents = split_driver(original)
    records = []
    for name, text in zip(("run_synthesis.tcl", "run_implementation.tcl"), contents):
        path = cwd / name
        if path.exists():
            raise RuntimeError("Staged driver already exists: " + str(path))
        path.write_text(text)
        dest = archive / "implementation" / name
        shutil.copyfile(path, dest)
        records.append({"kind": "staged_driver", "archived_file": str(dest.relative_to(archive)),
                        "raw_file": str(path.relative_to(work)),
                        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()})
    return records


def run_staged_implementation(config, cwd, work, timeout, invoke_phase):
    elapsed = 0
    phases = []
    config["implementation_phases"] = phases
    for phase, driver, log in (("impl_synth", "run_synthesis.tcl", "impl_synth.console.log"),
                               ("impl_route", "run_implementation.tcl", "impl.console.log")):
        remaining = timeout - elapsed
        if remaining <= 0:
            return 124, elapsed
        args = ["vivado", "-mode", "batch", "-source", driver, "-notrace", "-nojournal"]
        record = {"phase": phase, "driver": driver, "timeout_seconds": remaining,
                  "logfile": str(Path(log))}
        phases.append(record)
        code, seconds = invoke_phase(args, cwd, work / log, remaining, phase)
        record.update(exit_code=code, seconds=seconds)
        elapsed += seconds
        if code:
            return code, elapsed
    return 0, elapsed
