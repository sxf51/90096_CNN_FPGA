#!/usr/bin/env python3
"""Keep archived tool failures and resource violations visible in summaries."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_arch import actual_measurement, area_breakdown, failure_reason, scope
from run_exp import ROOT


class ArchitectureAnalysisTests(unittest.TestCase):
    def test_int16_area_categories_sum_to_reported_totals(self):
        for exp_id in ("P13", "P14", "P15", "P16"):
            report = next((ROOT / "experiments").glob(exp_id + "_*/csynth.rpt"))
            with self.subTest(exp_id=exp_id):
                rows = area_breakdown(report)
                self.assertEqual(rows[-1]["category"], "Total")
                for resource in ("DSP", "LUT", "FF"):
                    self.assertEqual(sum(row[resource] or 0 for row in rows[:-1]), rows[-1][resource])

    def test_boundary_exhaustion_is_a_primitive_validation(self):
        config = {"tb_files": ["exp/tb/integer_numeric.cpp"], "csim_only": True}
        self.assertEqual(scope(config, {"design": "designs/dataflow_int"}), "PE")

    def test_real_oversized_aggregate_diagnostic(self):
        reason = failure_reason({"status": "fail", "notes": "Synthesis failed (exit=1)"},
                                ROOT / "experiments/W11_fixed_tiles_T8_allcontinuous_4ns")
        self.assertIn("HLS 214-256", reason)
        self.assertIn("8000", reason)
        self.assertIn("4096", reason)

    def test_real_macro_collision_diagnostic(self):
        reason = failure_reason({"status": "fail", "notes": "C simulation failed"},
                                ROOT / "experiments/W04_winograd_conv1_T16")
        self.assertIn("F2/F3 size macros collide", reason)
        self.assertIn("ap_fixed_base.h", reason)

    def test_lut_limit_uses_unchanged_gate(self):
        reason = failure_reason({"status": "infeasible", "LUT": "101488", "DSP": "254"}, ROOT)
        self.assertEqual(reason, "LUT=101488 exceeds 81984")

    def test_cosim_resources_are_not_actual_measurements(self):
        row = {"DSP":"502", "LUT":"70449", "latency_cycles":"1048730"}
        config = {"operation":"cosim", "verification":{"rtl_latency_max":1100000}}
        self.assertEqual(actual_measurement(row,config,"latency_cycles"),1100000)
        self.assertIsNone(actual_measurement(row,config,"DSP"))
        self.assertIsNone(actual_measurement(row,config,"LUT"))

    def test_missing_rtl_report_does_not_inherit_hls_cycles(self):
        self.assertIsNone(actual_measurement({"latency_cycles":"1048730"},
                                           {"operation":"cosim"},"latency_cycles"))

    def test_implementation_resources_are_routed_and_cycles_unknown(self):
        row = {"DSP":"502", "BRAM18K":"73", "latency_cycles":"1048730"}
        config = {"operation":"impl", "verification":{"impl_DSP":480,"impl_BRAM36":40.5}}
        self.assertEqual(actual_measurement(row,config,"DSP"),480)
        self.assertEqual(actual_measurement(row,config,"BRAM18K"),81)
        self.assertIsNone(actual_measurement(row,config,"latency_cycles"))


if __name__ == "__main__":
    unittest.main()
