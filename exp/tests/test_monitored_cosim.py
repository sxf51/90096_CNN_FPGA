"""Check simulation-only instrumentation and the cumulative cosimulation limit."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from monitored_cosim import archive_measurements, install_monitor, measured_result, run_monitored


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
        for name in ("run_sim.tcl", "check_sim.tcl", "dataflow_monitor_API.tcl", "run_xsim.sh"):
            (self.sim / name).write_text("# generated driver fixture\n")

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
        self.assertEqual(len(config["generated_cosim_driver"]), 4)
        for record in config["generated_cosim_driver"]:
            self.assertEqual((self.work / record["raw_file"]).read_bytes(),
                             (self.archive / record["archived_file"]).read_bytes())
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

    def test_modified_generated_postcheck_driver_cannot_report_success(self):
        def invoke(args, cwd, log, remaining, phase):
            log.write_text(phase + " completed\n")
            if phase == "cosim_execute":
                (self.sim / "check_sim.tcl").write_text("# changed validation\n")
            return 0, 1

        with self.assertRaisesRegex(RuntimeError, "driver changed"):
            run_monitored({}, self.work, self.archive, 100, invoke)
        self.assertEqual((self.archive / "simulation_driver/check_sim.tcl").read_text(),
                         "# generated driver fixture\n")

    def test_execution_metrics_are_independent_of_setup_vector_generation(self):
        install_monitor(self.work, self.archive)
        functional = dict(csim_pass=True, bit_exact=True, reload_switch_pass=True,
                          load_flags=[1, 0, 1, 0], frame_count=4, reuse_pass=True,
                          reload_pass=True, retained_latest_pass=True,
                          reload_expected=104/256, border_mse=.000016)
        marker = "EXP_METRICS " + json.dumps(functional) + "\n"
        execution = marker * 2 + "EXP_MONITORED_COSIM_DONE\n"
        (self.work / "cosim_execute.console.log").write_text(execution)
        (self.work / "cosim.console.log").write_text(marker + execution)
        (self.sim / "srcnn_reload.performance.result.transaction.xml").write_text(
            "transaction 0: 300000 300029\ntransaction 1: 295000 295029\n"
            "transaction 2: 300000 300029\ntransaction 3: 295000 x\n")
        fields = ("transaction,load_params,ar_requests,r_beats,aw_requests,w_beats,"
                  "ar_valid_cycles,r_valid_cycles,aw_valid_cycles,w_valid_cycles,read_bytes\n")
        fields += "\n".join(str(i) + "," + ("1,64,8129,0,0,64,8129,0,0,32516"
                                          if load else "0,0,0,0,0,0,0,0,0,0")
                             for i, load in enumerate((1, 0, 1, 0))) + "\n"
        (self.sim / "reload_parameter_axi.csv").write_text(fields)
        result = measured_result(self.work, self.archive, {"border_mse": functional["border_mse"]})
        self.assertTrue(result["skip_parameter_axi_zero"])
        self.assertEqual(result["rtl_latency_max"], 300000)
        self.assertEqual(result["rtl_latency_min"], 295000)
        self.assertEqual(result["rtl_frame_count"], 4)
        self.assertTrue((self.archive / "reload_transactions.csv").is_file())
        (self.work / "cosim_execute.console.log").write_text(marker + "EXP_MONITORED_COSIM_DONE\n")
        with self.assertRaisesRegex(RuntimeError, "separate C and RTL"):
            measured_result(self.work, self.archive, {"border_mse": functional["border_mse"]})

    def test_partial_observer_evidence_survives_aborted_execution(self):
        bus = self.sim / "reload_parameter_axi.csv"
        bus.write_text("transaction,load_params,read_bytes\n0,1,32516\n1,0,4\n")
        (self.work / "cosim_execute.console.log").write_text("simulation aborted\n")
        with self.assertRaisesRegex(RuntimeError, "did not complete"):
            measured_result(self.work, self.archive, {})
        records = archive_measurements(self.work, self.archive)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual((self.archive / record["archived_file"]).read_bytes(), bus.read_bytes())
        self.assertEqual(record["sha256"], hashlib.sha256(bus.read_bytes()).hexdigest())
        self.assertFalse((self.archive / "reload_transactions.csv").exists())

    def test_nonzero_skipped_read_is_rejected_but_raw_measurements_are_retained(self):
        functional = dict(csim_pass=True, bit_exact=True, reload_switch_pass=True,
                          load_flags=[1, 0, 1, 0], frame_count=4, reuse_pass=True,
                          reload_pass=True, retained_latest_pass=True,
                          reload_expected=104/256, border_mse=.000016)
        marker = "EXP_METRICS " + json.dumps(functional) + "\n"
        (self.work / "cosim_execute.console.log").write_text(marker * 2 + "EXP_MONITORED_COSIM_DONE\n")
        performance = self.sim / "srcnn_reload.performance.result.transaction.xml"
        performance.write_text("transaction 0: 300000 300029\ntransaction 1: 295000 295029\n"
                               "transaction 2: 300000 300029\ntransaction 3: 295000 x\n")
        bus = self.sim / "reload_parameter_axi.csv"
        bus.write_text("transaction,load_params,ar_requests,r_beats,aw_requests,w_beats,"
                       "ar_valid_cycles,r_valid_cycles,aw_valid_cycles,w_valid_cycles,read_bytes\n" +
                       "\n".join(str(i) + "," + ("1,8129,8129,0,0,8129,8129,0,0,32516"
                                                 if load else "0,1,1,0,0,1,1,0,0,4")
                                 for i, load in enumerate((1, 0, 1, 0))) + "\n")
        with self.assertRaisesRegex(RuntimeError, "parameter AXI traffic"):
            measured_result(self.work, self.archive, {"border_mse": functional["border_mse"]})
        folder = self.archive / "parameter_axi_monitor"
        records = json.loads((folder / "measurement_manifest.json").read_text())
        for source in (performance, bus):
            self.assertEqual((folder / source.name).read_bytes(), source.read_bytes())
            self.assertEqual(records[source.name]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse((self.archive / "reload_transactions.csv").exists())


if __name__ == "__main__":
    unittest.main()
