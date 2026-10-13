import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_weight_loading import loader_measurement
from run_exp import ROOT


class LoaderAnalysisTests(unittest.TestCase):
    def test_streamed_loader_clock_miss_is_not_ws2_acceptance(self):
        baseline = json.loads((ROOT / "experiments/F25_nested_weight_loader_T16_2p5ns/metrics.json").read_text())
        archive = ROOT / "experiments/F27_local_streamed_params_T16"
        row, warnings = loader_measurement(archive, baseline)
        self.assertEqual(row["outside_LUT"], 3170)
        self.assertEqual(warnings, [])
        self.assertTrue(row["outside_gate"])
        self.assertTrue(row["cycles_gate"])
        self.assertFalse(row["clock_gate"])
        self.assertFalse(row["ws2_all_gates"])

    def test_new_loader_requires_warning_free_ownership(self):
        baseline = {"latency_cycles": 1056904, "clock_est_ns": 2.377, "border_mse": 0.01}
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            row = {"id": "F28", "status": "provisional", "csim_pass": True, "bit_exact": True,
                   "LUT": 50000, "latency_cycles": 1050000, "clock_est_ns": 2.377, "border_mse": 0.01}
            config = {"require_weight_predecessor_free": True,
                      "parsed_modules": [{"module": "dataflow_region", "LUT": 47000}],
                      "parsed_loops": [{"loop": name, "actual_ii": 1}
                                       for name in ("c1_fold", "c2_fold", "c3_fold")]}
            (archive / "metrics.json").write_text(json.dumps(row))
            (archive / "config.json").write_text(json.dumps(config))
            log = archive / "csynth.log.txt"
            log.write_text("WARNING: [HLS 200-1449] direct parameter access\n")
            result, _ = loader_measurement(archive, baseline)
            self.assertFalse(result["ws2_all_gates"])
            log.write_text("completed\n")
            result, _ = loader_measurement(archive, baseline)
            self.assertTrue(result["ws2_all_gates"])

    def test_winograd_conv1_fold_uses_its_actual_reported_label(self):
        baseline = json.loads((ROOT / "experiments/F25_nested_weight_loader_T16_2p5ns/metrics.json").read_text())
        archive = ROOT / "experiments/W17_narrow_raw_banks_T8"
        row, _ = loader_measurement(archive, baseline)
        self.assertTrue(row["fold_II1"])
        self.assertFalse(row["ws2_all_gates"])

    def test_archived_baseline_attribution_and_warning_gate(self):
        archive = ROOT / "experiments/F25_nested_weight_loader_T16_2p5ns"
        baseline = json.loads((archive / "metrics.json").read_text())
        row, warnings = loader_measurement(archive, baseline)
        self.assertEqual(row["dataflow_LUT"], 37682)
        self.assertEqual(row["outside_LUT"], 32294)
        self.assertEqual(row["top_multiplexer_LUT"], 14134)
        self.assertEqual(len(warnings), 5)
        self.assertTrue(row["fold_II1"])
        self.assertFalse(row["outside_gate"])
        self.assertFalse(row["ws2_all_gates"])

    def test_failed_run_does_not_turn_absent_reports_into_zero_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            row = {"id":"F27", "status":"fail", "csim_pass":False, "bit_exact":False,
                   "LUT":None, "latency_cycles":None, "clock_est_ns":None, "border_mse":None}
            (archive / "metrics.json").write_text(json.dumps(row))
            (archive / "config.json").write_text("{}")
            values, warnings = loader_measurement(archive, {"latency_cycles":1056904,"clock_est_ns":2.377,"border_mse":0.01})
            self.assertIsNone(values["outside_LUT"])
            self.assertIsNone(values["weight_predecessor_warnings"])
            self.assertFalse(values["ws2_all_gates"])
            self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
