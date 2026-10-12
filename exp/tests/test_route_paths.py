import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_route import analyze, setup_paths, hierarchy
from archive_setup_paths import archive_complete, register_report, select_checkpoint
from archive_route_progress import resources, routing_progress
from verify_exp import parse_verification
from run_exp import ROOT


class RoutedPathTests(unittest.TestCase):
    def test_final_optimized_checkpoint_is_used_instead_of_preoptimization_route(self):
        checkpoints = ["work/impl_1/bd_0_wrapper_routed.dcp",
                       "work/impl_1/bd_0_wrapper_postroute_physopt.dcp"]
        self.assertEqual(select_checkpoint(checkpoints, True), checkpoints[1])
        self.assertEqual(select_checkpoint(checkpoints), checkpoints[1])
        self.assertEqual(select_checkpoint(checkpoints[:1]), checkpoints[0])

    def test_checkpoint_selection_rejects_missing_or_ambiguous_final_state(self):
        with self.assertRaisesRegex(RuntimeError, "optimization checkpoint is missing"):
            select_checkpoint(["work/impl_1/top_routed.dcp"], True)
        with self.assertRaisesRegex(RuntimeError, "unique final"):
            select_checkpoint(["work/impl_1/top_postroute_physopt.dcp",
                               "work/impl_2/top_postroute_physopt.dcp"], True)

    def route_fixture(self, root, wns=.1, accepted_cosim=True):
        archive = root / "experiments/F01_impl"
        archive.mkdir(parents=True)
        observed = {"impl_WNS_ns": wns, "impl_TNS_ns": 0 if wns >= 0 else -1,
                    "impl_WHS_ns": .03, "impl_unrouted_nets": 0,
                    "impl_LUT": 42592, "impl_FF": 88806, "impl_DSP": 644,
                    "impl_BRAM36": 54.5, "impl_URAM": 0, "timing_met": wns >= 0}
        config = {"id": "F01", "verify_parent": "W21", "operation": "impl", "clock": 3.33,
                  "implementation_clock_ns": 4.5, "resource_policy": "routed", "verification": observed}
        (archive / "config.json").write_text(json.dumps(config))
        (archive / "metrics.json").write_text(json.dumps({"status": "impl_complete", "DSP": 644}))
        (archive / "F01.md").write_text("## 6. Interpretation\n")
        for exp_id, status, cycles in (("F02", "cosim_complete" if accepted_cosim else "fail", 558758),
                                        ("F03", "fail", 999999), ("F04", "timeout", 888888)):
            candidate = root / ("experiments/"+exp_id+"_cosim")
            candidate.mkdir()
            (candidate / "config.json").write_text(json.dumps({
                "id": exp_id, "operation": "cosim", "verify_parent": "W21",
                "verification": {"rtl_status": "Pass", "rtl_latency_max": cycles,
                                 "rtl_interval_max": cycles+29}}))
            (candidate / "metrics.json").write_text(json.dumps({"status": status}))
        return archive

    def test_failed_cycle_gate_and_timeout_do_not_override_accepted_rtl(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.route_fixture(root)
            with patch("analyze_route.ROOT", root):
                result = analyze(archive)
            self.assertEqual(result["rtl_source_id"], "F02")
            self.assertEqual(result["rtl_latency_cycles"], 558758)
            self.assertTrue(result["route_feasible"])
            self.assertAlmostEqual(result["rtl_frame_ms_at_target"], 2.514411)
            self.assertIn("independent routed gates", (archive / "F01.md").read_text())

    def test_unclosed_route_retains_cycles_but_has_no_validated_target_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.route_fixture(root, wns=-.05)
            with patch("analyze_route.ROOT", root):
                result = analyze(archive)
            self.assertFalse(result["route_feasible"])
            self.assertEqual(result["rtl_latency_cycles"], 558758)
            self.assertIsNone(result["rtl_frame_ms_at_target"])

    def test_only_failed_rtl_reports_cannot_produce_a_frame_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.route_fixture(root, accepted_cosim=False)
            with patch("analyze_route.ROOT", root):
                result = analyze(archive)
            self.assertNotIn("rtl_source_id", result)
            self.assertNotIn("rtl_frame_ms_at_target", result)

    def test_timeout_partial_resources_never_become_final_routed_results(self):
        archive = ROOT / "experiments/F89_serial_vivado_impl_F25"
        partial = resources((archive / "diagnostics/pre_route/srcnn_utilization_synth.rpt").read_text())
        self.assertEqual(partial["DSP"], 592)
        self.assertEqual(partial["LUT"], 37240)
        observed, _ = parse_verification(archive, "impl")
        self.assertNotIn("impl_WNS_ns", observed)
        self.assertNotIn("impl_LUT", observed)

    def test_intermediate_routing_keeps_missing_iteration_and_no_final_verdict(self):
        text = "INFO: Intermediate Timing Summary | WNS=-1.2 | TNS=-12.3\nPhase 5.2 Global Iteration 1\nINFO: Intermediate Timing Summary | WNS=-0.9 | TNS=-10.1\n"
        rows = routing_progress(text)
        self.assertIsNone(rows[0]["iteration"])
        self.assertEqual(rows[1]["iteration"], 1)
        self.assertTrue(all(row["final_routed_verdict"] is False for row in rows))

    def test_partial_copy_is_not_a_completed_archive_and_registration_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            script = archive / "export.tcl"
            script.write_text("# export setup paths\n")
            report = archive / "reports/impl/srcnn_setup5_routed.rpt"
            report.parent.mkdir(parents=True)
            block = "Slack (MET) : 0.5ns\n  Source: start/Q\n  Destination: finish/D\n  Path Type: Setup\n"
            report.write_text(block*5)
            config = {}
            self.assertFalse(archive_complete(archive, config, script))
            (archive / "critical_paths.csv").write_text("path,slack_ns\n")
            (archive / "setup_paths_operation.txt").write_text("CHECKPOINT_SHA256 abc\n")
            config["setup_paths_script_sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
            register_report(config, archive, report, "srcnn_setup5_routed.rpt")
            register_report(config, archive, report, "srcnn_setup5_routed.rpt")
            self.assertEqual(len(config["verification_reports"]), 1)
            self.assertTrue(archive_complete(archive, config, script))
            config["implementation_strategy"] = "Performance_Explore"
            self.assertFalse(archive_complete(archive, config, script))
            config["setup_paths_checkpoint"] = {"stage": "post_route_phys_opt"}
            self.assertTrue(archive_complete(archive, config, script))
            report.write_text(block*4)
            self.assertFalse(archive_complete(archive, config, script))

    def test_hierarchy_keeps_parent_totals_and_mixed_bram_units(self):
        text = "| Instance | Module | Total LUTs | Logic LUTs | LUTRAMs | SRLs | FFs | RAMB36 | RAMB18 | URAM | DSP Blocks |\n| top | (top) | 37240 | 31910 | 4762 | 568 | 77805 | 28 | 16 | 0 | 592 |\n| child | core | 25094 | 24194 | 736 | 164 | 67973 | 20 | 15 | 0 | 591 |\n"
        rows = hierarchy(text)
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]["BRAM18K"],72)
        self.assertEqual(rows[1]["BRAM18K"],55)
        self.assertEqual(rows[0]["DSP Blocks"],592)

    def test_real_report_keeps_setup_only_and_counts_dsp_sites(self):
        path = ROOT / "experiments/E070_first_feasible_implementation/reports/impl/srcnn_timing_routed.rpt"
        rows = setup_paths(path.read_text())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["logic_levels"], 25)
        self.assertEqual(rows[0]["DSP_sites"], 8)
        self.assertTrue(rows[0]["DSP_cascade_PCIN_PCOUT"])
        self.assertEqual(rows[0]["slack_ns"], -1.277)
        self.assertIn("c1_fold", rows[0]["source"])

    def test_limits_to_first_five_and_does_not_invent_missing_paths(self):
        block = "Slack (MET) : 0.5ns\n  Source: start/Q\n  Destination: finish/D\n  Path Type: Setup\n  Logic Levels: 3\n"
        self.assertEqual(len(setup_paths(block*8)), 5)
        self.assertEqual(setup_paths("No timing evidence"), [])


if __name__ == "__main__":
    unittest.main()
