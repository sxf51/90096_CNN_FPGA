import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_route import setup_paths
from run_exp import ROOT


class RoutedPathTests(unittest.TestCase):
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
