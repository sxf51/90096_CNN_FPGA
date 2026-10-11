import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_route import setup_paths, hierarchy
from archive_setup_paths import archive_complete, register_report
from run_exp import ROOT


class RoutedPathTests(unittest.TestCase):
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
