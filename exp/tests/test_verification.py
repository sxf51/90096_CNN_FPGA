#!/usr/bin/env python3
"""Prevent inherited pre-route reports from becoming implementation evidence."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_exp import archive_verification_reports, parse_verification
from run_exp import ROOT


class VerificationTests(unittest.TestCase):
    def test_archived_vivado_2026_route(self):
        reports = ROOT / "experiments/E070_first_feasible_implementation/reports/impl"
        values, _ = parse_verification(reports, "impl")
        self.assertEqual(values["impl_DSP"], 270)
        self.assertEqual(values["impl_BRAM36"], 31)
        self.assertEqual(values["impl_LUT"], 20454)
        self.assertEqual(values["impl_FF"], 33844)
        self.assertAlmostEqual(values["impl_WNS_ns"], -1.277)

    def test_routed_sources_are_copied_outside_generated_hdl_directories(self):
        with tempfile.TemporaryDirectory() as temp:
            work,archive = Path(temp)/"work",Path(temp)/"archive"
            report = work/"hls/impl/verilog/report"
            report.mkdir(parents=True)
            (report/"srcnn_utilization_routed.rpt").write_text("| DSPs | 502 |\n")
            (report/"srcnn_timing_routed.rpt").write_text("WNS(ns) TNS(ns)\n----- -----\n-0.321 -12.3\n")
            (report/"srcnn_utilization_synth.rpt").write_text("| DSPs | 999 |\n")
            records = archive_verification_reports(work,archive,"impl")
            self.assertEqual(len(records),2)
            self.assertTrue(all(record["archived_file"].startswith("reports/impl/") for record in records))
            self.assertTrue(all("verilog" not in record["archived_file"] for record in records))
            values,_ = parse_verification(archive,"impl")
            self.assertEqual(values["impl_DSP"],502)
            self.assertEqual(values["impl_WNS_ns"],-.321)

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

    def test_two_transaction_rtl_cycles_are_separate_from_csynth(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            synthesis = work / "hls/syn/report"
            simulation = work / "hls/sim/report"
            synthesis.mkdir(parents=True)
            simulation.mkdir(parents=True)
            (synthesis / "srcnn_csynth.rpt").write_text("| Verilog | Pass | 1 | 1 | 1 | 1 | 1 | 1 |\n")
            (simulation / "srcnn_cosim.rpt").write_text(
                "| Verilog | Pass | 2083800 | 2083900 | 2084000 | 2083901 | 2084001 | 2084101 |\n")
            values, _ = parse_verification(work,"cosim")
            self.assertEqual(values["rtl_status"],"Pass")
            self.assertEqual(values["rtl_latency_max"],2084000)
            self.assertEqual(values["rtl_interval_max"],2084101)


if __name__ == "__main__":
    unittest.main()
