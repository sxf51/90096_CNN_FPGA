#!/usr/bin/env python3
"""Prevent inherited pre-route reports from becoming implementation evidence."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_exp import parse_verification
from run_exp import ROOT


class VerificationTests(unittest.TestCase):
    def test_archived_vivado_2026_route(self):
        reports = ROOT / "experiments/E070_first_feasible_implementation/reports"
        values, _ = parse_verification(reports, "impl")
        self.assertEqual(values["impl_DSP"], 270)
        self.assertEqual(values["impl_BRAM36"], 31)
        self.assertEqual(values["impl_LUT"], 20454)
        self.assertEqual(values["impl_FF"], 33844)
        self.assertAlmostEqual(values["impl_WNS_ns"], -1.277)

    def test_synth_report_cannot_override_route(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            report = work / "hls/impl/verilog/report"
            report.mkdir(parents=True)
            (report / "srcnn_utilization_synth.rpt").write_text("| DSPs | 999 |\n| CLB LUTs | 99999 |\n")
            (report / "srcnn_timing_synth.rpt").write_text("WNS(ns) TNS(ns)\n----- -----\n9.999 0\n")
            (report / "srcnn_utilization_routed.rpt").write_text("| DSPs | 251 |\n| CLB LUTs | 41000 |\n")
            (report / "srcnn_timing_routed.rpt").write_text("WNS(ns) TNS(ns)\n----- -----\n-0.321 -12.3\n")
            values, _ = parse_verification(work, "impl")
            self.assertEqual(values["impl_DSP"], 251)
            self.assertEqual(values["impl_LUT"], 41000)
            self.assertEqual(values["impl_WNS_ns"], -.321)
            self.assertTrue(values["impl_timing_report"].endswith("_routed.rpt"))

    def test_synthesis_alone_has_no_implementation_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            report = work / "hls/impl/verilog/report"
            report.mkdir(parents=True)
            (report / "srcnn_utilization_synth.rpt").write_text("| DSPs | 251 |\n")
            values, _ = parse_verification(work, "impl")
            self.assertNotIn("impl_DSP", values)
            self.assertNotIn("impl_WNS_ns", values)


if __name__ == "__main__":
    unittest.main()
