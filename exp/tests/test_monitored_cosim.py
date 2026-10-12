"""Check simulation-only instrumentation and the cumulative cosimulation limit."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitored_cosim import install_monitor, run_monitored


class MonitoredCosimTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.work = self.root / "work"
        self.archive = self.root / "archive"
        self.sim = self.work / "hls/sim/verilog"
        self.sim.mkdir(parents=True)
        self.archive.mkdir()
        self.harness = self.sim / "srcnn_reload.autotb.v"
        names = ("AESL_start AESL_start_p1 AESL_ready_p1 AESL_done ap_clk ap_rst_n "
                 "parameters_ARVALID parameters_ARREADY parameters_ARLEN parameters_ARSIZE "
                 "parameters_RVALID parameters_RREADY parameters_AWVALID parameters_AWREADY "
                 "parameters_WVALID parameters_WREADY").split()
        self.original = ("module generated_harness;\nparameter AUTOTB_TRANSACTION_NUM = 4;\n" +
                         "\n".join("wire " + name + ";" for name in names) + "\nendmodule\n")
        self.harness.write_text(self.original)
        self.rtl = self.work / "hls/syn/verilog/srcnn_reload.v"
        self.rtl.parent.mkdir(parents=True)
        self.rtl.write_text("module srcnn_reload; endmodule\n")
        self.cfg = self.work / "hls_config.cfg"
        self.cfg.write_text("[hls]\nsyn.top=srcnn_reload\n")

    def test_only_generated_harness_changes_and_hashes_are_archived(self):
        rtl = self.rtl.read_bytes()
        record = install_monitor(self.work, self.archive)
        observed = self.harness.read_bytes()
        self.assertNotEqual(observed, self.original.encode())
        self.assertEqual(self.rtl.read_bytes(), rtl)
        self.assertEqual(record["original_sha256"], hashlib.sha256(self.original.encode()).hexdigest())
        self.assertEqual(record["instrumented_sha256"], hashlib.sha256(observed).hexdigest())
        self.assertEqual(json.loads((self.archive / "parameter_axi_monitor/manifest.json").read_text()), record)
        with self.assertRaises(RuntimeError):
            install_monitor(self.work, self.archive)
        self.assertEqual(self.harness.read_bytes(), observed)

    def test_wrong_count_or_missing_bus_signal_is_rejected_before_editing(self):
        for invalid in (self.original.replace("NUM = 4", "NUM = 3"),
                        self.original.replace("wire parameters_RVALID;", "")):
            with self.subTest(harness=invalid):
                self.harness.write_text(invalid)
                with self.assertRaises(RuntimeError):
                    install_monitor(self.work, self.archive)
                self.assertEqual(self.harness.read_text(), invalid)
        self.assertFalse((self.archive / "parameter_axi_monitor").exists())

    def test_setup_failure_never_launches_simulation_or_changes_harness(self):
        calls = []

        def invoke(args, cwd, log, remaining, phase):
            calls.append(phase)
            log.write_text("setup failed\n")
            return 1, 7

        self.assertEqual(run_monitored({}, self.work, self.archive, 100, invoke), (1, 7))
        self.assertEqual(calls, ["cosim_setup"])
        self.assertEqual(self.harness.read_text(), self.original)
        self.assertEqual((self.work / "cosim.console.log").read_text(), "setup failed\n")

    def test_generated_driver_uses_remaining_limit_and_keeps_both_logs(self):
        calls = []
        config = {}
        base = self.cfg.read_bytes()
        rtl = self.rtl.read_bytes()

        def invoke(args, cwd, log, remaining, phase):
            calls.append((args, remaining, phase))
            log.write_text(phase + " evidence\n")
            return (0, 23) if phase == "cosim_setup" else (124, 77)

        self.assertEqual(run_monitored(config, self.work, self.archive, 100, invoke), (124, 100))
        self.assertEqual([(limit, phase) for _, limit, phase in calls],
                         [(100, "cosim_setup"), (77, "cosim_execute")])
        self.assertIn("--cosim", calls[0][0])
        self.assertIn("--tcl", calls[1][0])
        driver = (self.archive / "cosim_execute.tcl").read_text()
        self.assertIn("source run_sim.tcl", driver)
        self.assertEqual((self.work / "cosim.console.log").read_text(),
                         "cosim_setup evidence\ncosim_execute evidence\n")
        self.assertTrue(config["parameter_axi_monitor"]["instrumented_sha256"])
        self.assertEqual(self.cfg.read_bytes(), base)
        self.assertEqual(self.rtl.read_bytes(), rtl)

    def test_exhausted_setup_budget_does_not_start_another_tool(self):
        calls = []

        def invoke(args, cwd, log, remaining, phase):
            calls.append(phase)
            log.write_text("setup completed\n")
            return 0, 100

        self.assertEqual(run_monitored({}, self.work, self.archive, 100, invoke), (124, 100))
        self.assertEqual(calls, ["cosim_setup"])
        self.assertFalse((self.work / "cosim_execute.console.log").exists())
        self.assertEqual((self.work / "cosim.console.log").read_text(), "setup completed\n")


if __name__ == "__main__":
    unittest.main()
