#!/usr/bin/env python3
"""Checks for numerical gating, missing report values and directive serialization."""
import contextlib
import hashlib
import io
import json
import shutil
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_exp


class RunnerTests(unittest.TestCase):
    def test_actual_report(self):
        report = run_exp.ROOT / "experiments/E020_auto_default_10ns/csynth.xml"
        metrics, loops = run_exp.parse_xml(report)
        self.assertEqual(metrics["latency_cycles"], 1960113853)
        self.assertEqual(metrics["BRAM18K"], 11064)
        module = run_exp.ROOT / "experiments/E020_auto_default_10ns/reports/srcnn_Pipeline_g_01_oc_g_02_y_g_03_x_csynth.xml"
        _, loops = run_exp.parse_xml(module)
        self.assertEqual(loops[0]["actual_ii"], 32)

    def test_missing_report_is_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "unknown.xml"
            path.write_text("<profile><AreaEstimates><Resources><DSP>?</DSP></Resources></AreaEstimates></profile>")
            metrics, _ = run_exp.parse_xml(path)
            self.assertIsNone(metrics["DSP"])
            self.assertIsNone(metrics["URAM"])
            self.assertIsNone(metrics["latency_cycles"])

    def fixture(self, root):
        (root / "src").mkdir()
        (root / "src/design.cpp").write_text("void srcnn() {}\n")
        (root / "experiments").mkdir()
        (root / "experiments/LOG.md").write_text("## Events\n\n## Pending Human Decisions / 待人工决策\n")
        digest = hashlib.sha256((root / "src/design.cpp").read_bytes()).hexdigest()
        (root / "experiments/checksums.txt").write_text(digest + "  src/design.cpp\n")
        settings = root / "settings.sh"
        settings.write_text(":\n")
        return {"id": "E999", "name": "runner_fixture", "stage": "test", "design": "src", "clock": 10,
                "settings": str(settings), "source_commit": "fixture", "tb_files": []}

    def test_exit_zero_does_not_override_failed_metrics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.fixture(root)
            calls = []
            def fake_invoke(args, settings, cwd, logfile, timeout):
                calls.append(args[0])
                logfile.write_text("version fixture\n" if "--version" in args else 'EXP_METRICS {"csim_pass":false}\n')
                return 0, .01
            with patch.object(run_exp, "ROOT", root), patch.object(run_exp, "invoke", fake_invoke), contextlib.redirect_stdout(io.StringIO()):
                code = run_exp.run(config)
            self.assertEqual(code, 1)
            self.assertNotIn("v++", calls)
            metrics = json.loads((root / "experiments/E999_runner_fixture/metrics.json").read_text())
            self.assertFalse(metrics["csim_pass"])
            self.assertEqual(metrics["status"], "fail")

    def test_supported_repeatable_directives(self):
        with tempfile.TemporaryDirectory(prefix="hls_config_") as temp:
            root = Path(temp)
            config = self.fixture(root)
            config["directives"] = ["set_directive_pipeline -II 1 srcnn/pixels",
                                    "set_directive_pipeline -II 2 srcnn/taps",
                                    "set_directive_array_partition -type cyclic -factor 4 -dim 1 srcnn weights"]
            work = root / "work"
            work.mkdir()
            with patch.object(run_exp, "ROOT", root):
                path = run_exp.generate_config(config, work)
            text = path.read_text()
            self.assertNotIn("syn.directive=", text)
            self.assertIn("syn.directive.pipeline=location=srcnn/pixels II=1", text)
            self.assertIn("syn.directive.pipeline=location=srcnn/taps II=2", text)
            self.assertIn("syn.directive.array_partition=location=srcnn variable=weights", text)
            self.assertIn(" -I" + str(work / "source"), text)
            self.assertNotIn(' -I"', text)

    def test_combinational_zero_latency_is_complete(self):
        actual = run_exp.ROOT / "experiments/E052_mul16_constant_unroll/csynth.xml"
        self.assertEqual(run_exp.parse_xml(actual)[0]["latency_cycles"], 0)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self.fixture(root)
            def fake_invoke(args, settings, cwd, logfile, timeout):
                if args[0] == "v++":
                    work = Path(args[args.index("--work_dir") + 1])
                    report = work / "hls/syn/report"
                    report.mkdir(parents=True)
                    shutil.copyfile(actual, report / "srcnn_csynth.xml")
                    logfile.write_text("Synthesis completed\n")
                else:
                    logfile.write_text("version fixture\n" if "--version" in args else
                                       'EXP_METRICS {"csim_pass":true,"bit_exact":true}\n')
                return 0, .01
            with patch.object(run_exp, "ROOT", root), patch.object(run_exp, "invoke", fake_invoke), contextlib.redirect_stdout(io.StringIO()):
                code = run_exp.run(config)
            self.assertEqual(code, 0)
            row = json.loads((root / "experiments/E999_runner_fixture/metrics.json").read_text())
            self.assertEqual(row["status"], "pass")
            self.assertEqual(row["latency_ms_est"], 0)
            self.assertEqual(row["DSP"], 60)


if __name__ == "__main__":
    unittest.main()
