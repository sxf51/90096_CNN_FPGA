import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from staged_implementation import prepare_staged_driver, run_staged_implementation, split_driver
from run_exp import ROOT


DRIVER = '''source stub.tcl
set vivado_proj_name project
set vivado_proj_dir .
set target_device xck26
set has_impl 1
set report_options {}
create_project $vivado_proj_name $vivado_proj_dir -part $target_device -force
reset_run synth_1
launch_runs synth_1
wait_on_run synth_1
hls_vivado_reports_synth synth_1 $report_options
if { $has_impl } {
  # launch run impl
  launch_runs impl_1
  wait_on_run impl_1
  hls_vivado_reports_impl impl_1 $report_options
}
hls_vivado_reports_finalize $report_options
'''


class StagedImplementationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("tclsh"), "Tcl interpreter unavailable")
    def test_two_processes_restore_project_without_restarting_synthesis(self):
        stub = '''proc record {text} {
  set out [open calls.txt a]
  puts $out $text
  close $out
}
proc create_project {args} { record CREATE }
proc reset_run {args} { record RESET }
proc launch_runs {run} { record "LAUNCH $run" }
proc wait_on_run {run} { record "WAIT $run" }
proc hls_vivado_reports_synth {args} {
  record SYNTH_REPORT
  set out [open project.xpr w]
  puts $out 100%
  close $out
}
proc open_project {path} {
  record REOPEN
  set in [open $path r]
  set ::progress [string trim [read $in]]
  close $in
}
proc get_runs {run} { return $run }
proc get_property {property run} { return $::progress }
proc set_param {args} {}
proc hls_vivado_reports_impl {args} { record ROUTE_REPORT }
proc hls_vivado_reports_finalize {args} { record FINAL_REPORT }
proc close_design {} { record CLOSE_DESIGN }
proc close_project {} { record CLOSE_PROJECT }
'''
        with tempfile.TemporaryDirectory() as temp:
            cwd = Path(temp)
            (cwd / "stub.tcl").write_text(stub)
            synth, route = split_driver(DRIVER)
            for name, content in (("synth.tcl", synth), ("route.tcl", route)):
                (cwd / name).write_text(content)
                subprocess.run(["tclsh", name], cwd=cwd, check=True, capture_output=True)
            self.assertEqual((cwd / "calls.txt").read_text().splitlines(),
                             ["CREATE", "RESET", "LAUNCH synth_1", "WAIT synth_1", "SYNTH_REPORT",
                              "CLOSE_DESIGN", "CLOSE_PROJECT", "REOPEN", "LAUNCH impl_1", "WAIT impl_1",
                              "ROUTE_REPORT", "FINAL_REPORT", "CLOSE_DESIGN", "CLOSE_PROJECT"])
            (cwd / "project.xpr").write_text("99%\n")
            failed = subprocess.run(["tclsh", "route.tcl"], cwd=cwd, capture_output=True, text=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("requires completed synthesis", failed.stderr)

    def test_actual_archived_driver_retains_clock_constraints_and_route_steps(self):
        archive = ROOT / "experiments/C15_ws_impl_C13/implementation/run_vivado.tcl"
        original = archive.read_text()
        synth, route = split_driver(original)
        self.assertIn('set target_clk_period_ns "5.000"', synth)
        self.assertIn('set target_clk_period_ns "5.000"', route)
        self.assertNotIn("launch_runs impl_1", synth)
        self.assertNotIn("create_project", route)
        self.assertNotIn("reset_run", route)
        self.assertNotIn("launch_runs synth_1", route)
        boundary = "if { $has_impl } {\n  # launch run impl\n"
        self.assertIn(boundary + original.split(boundary)[1], route)

    def test_unrecognized_or_ambiguous_driver_is_rejected(self):
        for content in (DRIVER + DRIVER, DRIVER.replace("wait_on_run synth_1", ""),
                        DRIVER.replace("hls_vivado_reports_impl impl_1 $report_options", "")):
            with self.assertRaises(RuntimeError):
                split_driver(content)

    def test_driver_archival_keeps_original_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp) / "work"
            cwd, archive = work / "hls/impl/verilog", Path(temp) / "archive"
            cwd.mkdir(parents=True)
            (archive / "implementation").mkdir(parents=True)
            driver = cwd / "run_vivado.tcl"
            driver.write_text(DRIVER)
            records = prepare_staged_driver(work, archive, cwd)
            self.assertEqual(driver.read_text(), DRIVER)
            for record in records:
                self.assertEqual(hashlib.sha256((archive / record["archived_file"]).read_bytes()).hexdigest(),
                                 record["sha256"])
            with self.assertRaisesRegex(RuntimeError, "already exists"):
                prepare_staged_driver(work, archive, cwd)

    def test_cumulative_timeout_and_failure_propagation(self):
        invoke = Mock(side_effect=[(0, 8000), (124, 2800)])
        config = {}
        self.assertEqual(run_staged_implementation(config, Path("cwd"), Path("work"), 10800, invoke),
                         (124, 10800))
        self.assertEqual([call.args[3] for call in invoke.call_args_list], [10800, 2800])
        self.assertEqual([phase["phase"] for phase in config["implementation_phases"]],
                         ["impl_synth", "impl_route"])
        failed = Mock(return_value=(1, 20))
        self.assertEqual(run_staged_implementation({}, Path("cwd"), Path("work"), 10800, failed), (1, 20))
        self.assertEqual(failed.call_count, 1)
        expired = Mock(return_value=(0, 10800))
        self.assertEqual(run_staged_implementation({}, Path("cwd"), Path("work"), 10800, expired), (124, 10800))
        self.assertEqual(expired.call_count, 1)


if __name__ == "__main__":
    unittest.main()
