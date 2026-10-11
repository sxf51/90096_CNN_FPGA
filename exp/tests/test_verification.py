#!/usr/bin/env python3
"""Prevent inherited pre-route reports from becoming implementation evidence."""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_exp import archive_verification_reports, parse_verification, prepare_serial_implementation
from run_exp import ROOT


class VerificationTests(unittest.TestCase):
    def test_serial_retry_preserves_template_and_relocates_generated_flow(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work,template,archive = root/"F89",root/"F81",root/"archive"
            generated = template/"hls/impl/verilog"
            generated.mkdir(parents=True)
            original = "source ./settings.tcl\nset path "+str(template)+"/source\nhls_vivado_reports_setup $report_options\n"
            (generated/"run_vivado.tcl").write_text(original)
            (generated/"project.runs").mkdir()
            (generated/"project.runs/old.log").write_text("Old failed project")
            (generated/"settings.tcl").write_text("set parent "+str(template)+"\n")
            (generated/"extraction.tcl").write_text("proc hls_vivado_reports_setup {args} {}\n")
            (template/"hls/impl/ip").mkdir()
            (template/"hls/impl/ip/component.xml").write_text("<component/>\n")
            hook = root/"hook.tcl"
            hook.write_text("set_param synth.maxThreads 1\n")
            cwd,records,_ = prepare_serial_implementation(work,template,archive,hook)
            self.assertEqual((generated/"run_vivado.tcl").read_text(),original)
            self.assertIn("STEPS.SYNTH_DESIGN.TCL.PRE",(cwd/"run_vivado.tcl").read_text())
            self.assertIn(str(work),(cwd/"settings.tcl").read_text())
            self.assertNotIn(str(template),(cwd/"run_vivado.tcl").read_text())
            self.assertFalse((cwd/"project.runs").exists())
            self.assertTrue((work/"hls/impl/ip/component.xml").is_file())
            self.assertEqual(len(records),4)
            from run_exp import write_json
            write_json(archive/"config.json",{"implementation_files":records,"implementation_work_root":str(work)})
            fresh,replay = root/"F101",root/"F100"
            (fresh/"hls/impl/ip").mkdir(parents=True)
            (fresh/"hls/impl/ip/component.xml").write_text("<fresh_component/>\n")
            replay_cwd,_,_ = prepare_serial_implementation(replay,fresh,root/"replay_archive",hook,archive)
            self.assertEqual((replay/"hls/impl/ip/component.xml").read_text(),"<fresh_component/>\n")
            self.assertEqual((replay_cwd/"run_vivado.tcl").read_text().count("STEPS.SYNTH_DESIGN.TCL.PRE"),1)
            self.assertNotIn(str(work),(replay_cwd/"run_vivado.tcl").read_text())

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
