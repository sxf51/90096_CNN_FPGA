#!/usr/bin/env python3
"""Prevent inherited pre-route reports from becoming implementation evidence."""
import sys
import json
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_exp import archive_verification_reports, parse_verification, prepare_serial_implementation, vivado_diagnostic_excerpt, diagnostic_parent, package_only_config, check_template_rtl, prepare_packaged_driver, check_image_validation, prepare_verification_testbench, reload_measurement
from run_exp import ROOT
from unittest.mock import patch
import hashlib
import verify_exp


class VerificationTests(unittest.TestCase):
    def test_changed_parameter_override_preserves_design_and_binary_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tb = root / "exp/tb/reload.cpp"
            tb.parent.mkdir(parents=True)
            tb.write_text("int main() { return 0; }\n")
            original = ("syn.file=/frozen/srcnn.cpp\nsyn.cflags=-DEXP_T=16\n"
                        "tb.cflags=-DEXP_T=16 -DEXP_FRAMES=2\n"
                        "tb.file=/old/validate.cpp\ntb.file=/old/golden.cpp\n"
                        "tb.file=/old/fixed_reference.bin\ntb.file=/old/test/set5\n")
            config = {"operation": "cosim", "reload_params": True,
                      "verification_testbench": "exp/tb/reload.cpp"}
            work, archive = root / "work", root / "archive"
            with patch.object(verify_exp, "ROOT", root):
                text = prepare_verification_testbench(original, config, work, archive)
            self.assertIn("syn.file=/frozen/srcnn.cpp", text)
            self.assertIn("syn.cflags=-DEXP_T=16", text)
            self.assertIn("tb.cflags=-DEXP_T=16 -DEXP_FRAMES=2", text)
            self.assertIn("tb.file=/old/fixed_reference.bin", text)
            self.assertIn("tb.file=/old/test/set5", text)
            self.assertNotIn("tb.file=/old/validate.cpp", text)
            self.assertNotIn("tb.file=/old/golden.cpp", text)
            self.assertEqual(config["testbench_sha256"],
                             {"reload.cpp": hashlib.sha256(tb.read_bytes()).hexdigest()})
            self.assertEqual((archive / "testbench/reload.cpp").read_bytes(), tb.read_bytes())
            with self.assertRaisesRegex(RuntimeError, "independent testbench"):
                prepare_verification_testbench(original, {"reload_params": True}, work, archive)

    def test_reload_replay_checks_frozen_testbench_not_live_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            frozen = root / "experiments/F93_parent/testbench/reload.cpp"
            frozen.parent.mkdir(parents=True)
            frozen.write_text("frozen\n")
            config = {"operation": "cosim", "verification_testbench": "exp/tb/reload.cpp",
                      "verification_testbench_parent_archive": "experiments/F93_parent",
                      "verification_testbench_manifest": {"reload.cpp": hashlib.sha256(frozen.read_bytes()).hexdigest()}}
            with patch.object(verify_exp, "ROOT", root):
                prepare_verification_testbench("tb.file=/old/validate.cpp\n", config, root / "work", root / "archive")
                frozen.write_text("changed\n")
                with self.assertRaisesRegex(RuntimeError, "testbench changed"):
                    prepare_verification_testbench("", config, root / "work2", root / "archive2")

    def test_reload_acceptance_requires_two_exact_checks_and_original_border(self):
        parent = {"border_mse": 0.00001661846957728205}
        result = {"csim_pass": True, "bit_exact": True, "reload_pass": True,
                  "frame_count": 2, "reload_expected": .40625, "border_mse": parent["border_mse"]}
        with tempfile.TemporaryDirectory() as temp:
            log = Path(temp) / "cosim.log"
            marker = "EXP_METRICS " + json.dumps(result) + "\n"
            log.write_text(marker)
            with self.assertRaisesRegex(RuntimeError, "Missing C and RTL"):
                reload_measurement(log, parent)
            log.write_text(marker + marker)
            self.assertEqual(reload_measurement(log, parent), result)
            for changes in ({"reload_pass": False}, {"border_mse": 0},
                            {"frame_count": 1}, {"bit_exact": False}, {"reload_expected": .4}):
                log.write_text(marker + "EXP_METRICS " + json.dumps({**result, **changes}) + "\n")
                with self.assertRaisesRegex(RuntimeError, "exact frame/border/reload"):
                    reload_measurement(log, parent)

    def test_all_image_evidence_requires_candidate_source_and_arithmetic_flags(self):
        parent = {"source_sha256": {"srcnn.cpp": "frozen"}, "fixed": True,
                  "precision": "w10a10acc23", "defines": {"EXP_T": 8, "EXP_FRAMES": 2}}
        full = {**parent, "defines": {"EXP_T": 8, "EXP_FRAMES": 1, "EXP_SET14": 1},
                "validation": {"csim_pass": True, "bit_exact": True, "image_count": 13,
                               "delta_psnr": -.07}}
        check_image_validation(parent, full)
        with self.assertRaisesRegex(RuntimeError, "source differs"):
            check_image_validation(parent, {**full, "source_sha256": {"srcnn.cpp": "other"}})
        with self.assertRaisesRegex(RuntimeError, "arithmetic flags differ"):
            check_image_validation(parent, {**full, "defines": {"EXP_T": 16}})
        with self.assertRaisesRegex(RuntimeError, "all-supplied-image"):
            check_image_validation(parent, {**full, "validation": {**full["validation"], "image_count": 12}})

    def test_recorded_f25_full_image_validation_matches_frozen_candidate(self):
        parent = json.loads((ROOT / "experiments/F25_nested_weight_loader_T16_2p5ns/config.json").read_text())
        full = json.loads((ROOT / "experiments/F80_final_all_supplied_F25/config.json").read_text())
        check_image_validation(parent, full)

    def test_driver_boilerplate_preserves_new_ip_and_replay_uses_archived_scripts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template, work, archive = root/"F89", root/"F97", root/"archive"
            generated = template/"hls/impl/verilog"
            generated.mkdir(parents=True)
            original = ("set has_synth true\nset has_impl 1\n"
                        "dict set report_options hls_project F81\n"
                        "dict set report_options funcmodules {old_function}\n"
                        "dict set report_options bindmodules {old_bind}\n"
                        "hls_vivado_reports_setup $report_options\n")
            (generated/"run_vivado.tcl").write_text(original)
            (generated/"settings.tcl").write_text("set top_module srcnn\nset language verilog\nset device xck26\nset package -sfvc784\nset speed -2LV-c\nset clock ap_clk\n")
            (generated/"extraction.tcl").write_text("# report procedures\n")
            (generated/"srcnn.xdc").write_text("create_clock -name ap_clk -period 2.500 [get_ports ap_clk]\n")
            stale_ip = template/"hls/impl/ip/stale.v"
            stale_ip.parent.mkdir(parents=True)
            stale_ip.write_text("module stale; endmodule\n")
            component = '<component xmlns="test"><vendor>xilinx.com</vendor><library>hls</library><name>srcnn</name><version>1.0</version></component>'
            for destination in (work, root/"F101"):
                (destination/"hls/impl/ip").mkdir(parents=True)
                (destination/"hls/impl/ip/component.xml").write_text(component)
                rtl = destination/"hls/syn/verilog"
                rtl.mkdir(parents=True)
                for name in ("srcnn", "srcnn_local_engine", "srcnn_mul"):
                    (rtl/(name+".v")).write_text("module "+name+"; endmodule\n")
            parent = {"parsed_modules": [{"module": "local_engine"}]}
            records = prepare_packaged_driver(work, template, archive, parent, "F97")
            self.assertEqual((work/"hls/impl/ip/component.xml").read_text(), component)
            self.assertFalse((work/"hls/impl/ip/stale.v").exists())
            driver = (work/"hls/impl/verilog/run_vivado.tcl").read_text()
            self.assertIn("hls_project F97", driver)
            self.assertIn("funcmodules {srcnn_local_engine}", driver)
            self.assertIn("bindmodules {srcnn_mul}", driver)
            self.assertNotIn("old_function", driver)
            self.assertEqual((generated/"run_vivado.tcl").read_text(), original)
            (archive/"config.json").write_text(json.dumps({
                "implementation_driver_template_work_root": str(template),
                "implementation_driver_template_files": records}))
            (generated/"run_vivado.tcl").write_text("changed original template\n")
            prepare_packaged_driver(root/"F101", template, root/"replay", parent, "F101", archive)
            self.assertIn("hls_project F101", (root/"F101/hls/impl/verilog/run_vivado.tcl").read_text())
            self.assertEqual((root/"F101/hls/impl/ip/component.xml").read_text(), component)

    def test_same_interface_different_rtl_template_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            parent, template = root/"F25", root/"W17"
            for work in (parent, template):
                rtl = work/"hls/syn/verilog"
                rtl.mkdir(parents=True)
                (rtl/"srcnn.v").write_text("module srcnn; endmodule\n")
                (rtl/"weights.dat").write_text("01\n")
            result = check_template_rtl(parent, template)
            self.assertEqual(result["files_checked"], 2)
            self.assertTrue(result["template_matches_parent"])
            (template/"hls/syn/verilog/weights.dat").write_text("02\n")
            with self.assertRaisesRegex(RuntimeError, "differs from the frozen parent"):
                check_template_rtl(parent, template)
            with self.assertRaisesRegex(RuntimeError, "RTL is missing"):
                check_template_rtl(parent, root/"missing")

    def test_package_only_config_removes_all_vivado_operations(self):
        with tempfile.TemporaryDirectory() as temp:
            cfg, target = Path(temp)/"hls.cfg", Path(temp)/"package.cfg"
            original = "part=xck26-sfvc784-2LV-c\n[hls]\nsyn.top=srcnn\nvivado.flow=impl\nvivado.flow=syn\n"
            cfg.write_text(original)
            package_only_config(cfg, target)
            self.assertEqual(cfg.read_text(), original)
            self.assertEqual(target.read_text().count("vivado.flow="), 1)
            self.assertIn("vivado.flow=none", target.read_text())

    def test_fresh_package_driver_enables_serial_impl_without_replacing_ip(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work, archive = root/"F94", root/"archive"
            generated = work/"hls/impl/verilog"
            generated.mkdir(parents=True)
            (generated/"run_vivado.tcl").write_text("set has_synth false\nset has_impl 0\nhls_vivado_reports_setup $report_options\n")
            (generated/"settings.tcl").write_text("set clock ap_clk\n")
            (generated/"extraction.tcl").write_text("# reports\n")
            ip = work/"hls/impl/ip/srcnn.v"
            ip.parent.mkdir(parents=True)
            ip.write_text("module srcnn; endmodule\n")
            before = ip.read_bytes()
            hook = root/"hook.tcl"
            hook.write_text("set_param synth.maxThreads 1\n")
            cwd, records, _ = prepare_serial_implementation(work, work, archive, hook, enable_impl=True)
            self.assertEqual(ip.read_bytes(), before)
            self.assertIn("set has_impl 1", (cwd/"run_vivado.tcl").read_text())
            self.assertIn("set has_synth true", (cwd/"run_vivado.tcl").read_text())
            self.assertIn("STEPS.SYNTH_DESIGN.TCL.PRE", (cwd/"run_vivado.tcl").read_text())
            self.assertEqual(len(records), 4)

    def test_diagnostic_route_requires_opt_in_exact_quality_and_csim(self):
        config = {"operation":"impl", "diagnostic_infeasible_parent":True}
        parent = {"csim_pass":True, "status":"infeasible", "bit_exact":True, "delta_psnr":-.07}
        self.assertTrue(diagnostic_parent(config,parent))
        self.assertFalse(diagnostic_parent({"operation":"impl"},parent))
        self.assertFalse(diagnostic_parent({**config,"operation":"cosim"},parent))
        for changes in ({"csim_pass":False}, {"status":"fail"}, {"bit_exact":False}, {"delta_psnr":-.11}, {"delta_psnr":None}):
            self.assertFalse(diagnostic_parent(config,{**parent,**changes}))

    def test_bounded_route_threads_keep_synthesis_serial_and_parent_immutable(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            work, template, archive = root/"W22", root/"F98", root/"archive"
            generated = template/"hls/impl/verilog"
            generated.mkdir(parents=True)
            original = "hls_vivado_reports_setup $report_options\n"
            (generated/"run_vivado.tcl").write_text(original)
            (generated/"settings.tcl").write_text("set clock ap_clk\n")
            (generated/"extraction.tcl").write_text("# reports\n")
            ip = template/"hls/impl/ip/srcnn.v"
            ip.parent.mkdir(parents=True)
            ip.write_text("module srcnn; endmodule\n")
            hook = root/"hook.tcl"
            hook.write_text("set_param general.maxThreads 1\nset_param synth.maxThreads 1\n")
            cwd, records, _ = prepare_serial_implementation(work, template, archive, hook, implementation_threads=4)
            self.assertEqual((generated/"run_vivado.tcl").read_text(), original)
            self.assertEqual((work/"hls/impl/ip/srcnn.v").read_bytes(), ip.read_bytes())
            self.assertIn("STEPS.OPT_DESIGN.TCL.PRE", (cwd/"run_vivado.tcl").read_text())
            self.assertIn("set_param general.maxThreads 4", (cwd/"bounded_implementation.tcl").read_text())
            self.assertIn("set_param synth.maxThreads 1", (cwd/"bounded_implementation.tcl").read_text())
            self.assertIn("set_param general.maxThreads 1", (cwd/"serial_synthesis.tcl").read_text())
            self.assertTrue(any(record["kind"] == "implementation_thread_hook" for record in records))
            replay, replay_archive = root/"replay", root/"replay_archive"
            fresh, _, _ = prepare_serial_implementation(replay, work, replay_archive, hook, implementation_threads=2)
            self.assertEqual((fresh/"run_vivado.tcl").read_text().count("STEPS.OPT_DESIGN.TCL.PRE"), 1)
            self.assertIn("general.maxThreads 2", (fresh/"bounded_implementation.tcl").read_text())
            serial, _, _ = prepare_serial_implementation(root/"serial", work, root/"serial_archive", hook)
            self.assertNotIn("STEPS.OPT_DESIGN.TCL.PRE", (serial/"run_vivado.tcl").read_text())
            with self.assertRaises(ValueError):
                prepare_serial_implementation(root/"bad", template, root/"bad_archive", hook, implementation_threads=12)

    def test_diagnostic_excerpt_keeps_thread_and_failure_evidence_in_log_middle(self):
        middle = ("INFO: [Synth 8-7079] Multithreading enabled using a maximum of 7 processes.\n"
                  "EXP_VIVADO_THREADS general=1 synth=1\n"
                  "EXP_VIVADO_IMPL_THREADS general=4 synth=1\n"
                  "ERROR: synthesis failed\n")
        raw = "session header\n"+"ordinary elaboration line\n"*300+middle+"ordinary mapping line\n"*300+"run ended\n"
        excerpt = vivado_diagnostic_excerpt(raw)
        self.assertIn("session header",excerpt)
        self.assertIn(middle,excerpt)
        self.assertIn("run ended",excerpt)
        self.assertLess(len(excerpt),len(raw))

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

    def test_relaxed_implementation_changes_clock_constraints_and_keeps_rtl(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template, work, archive = root/"F89", root/"F92", root/"archive"
            generated = template/"hls/impl/verilog"
            generated.mkdir(parents=True)
            (generated/"run_vivado.tcl").write_text('set target_clk_period_ns "2.500"\nhls_vivado_reports_setup $report_options\n')
            (generated/"settings.tcl").write_text("set clock ap_clk\n")
            (generated/"extraction.tcl").write_text("# extraction\n")
            (generated/"srcnn.xdc").write_text("create_clock -name ap_clk -period 2.500 -waveform {0.000 1.250} [get_ports ap_clk]\n")
            (template/"hls/impl/ip").mkdir()
            (template/"hls/impl/ip/srcnn.v").write_text("module srcnn; endmodule\n")
            (template/"hls/impl/ip/constraints").mkdir()
            (template/"hls/impl/ip/constraints/srcnn_ooc.xdc").write_text("create_clock -name ap_clk -period 2.500 [get_ports ap_clk]\n")
            hook = root/"hook.tcl"
            hook.write_text("set_param synth.maxThreads 1\n")
            cwd, records, _ = prepare_serial_implementation(work,template,archive,hook,implementation_clock_ns=5)
            self.assertIn('set target_clk_period_ns "5.000"', (cwd/"run_vivado.tcl").read_text())
            self.assertIn("-period 5.000 -waveform {0.000 2.500}", (cwd/"srcnn.xdc").read_text())
            self.assertIn("-period 2.500", (generated/"srcnn.xdc").read_text())
            self.assertEqual((work/"hls/impl/ip/srcnn.v").read_bytes(), (template/"hls/impl/ip/srcnn.v").read_bytes())
            self.assertIn("-period 5.000", (work/"hls/impl/ip/constraints/srcnn_ooc.xdc").read_text())
            self.assertEqual(len(records),6)

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
