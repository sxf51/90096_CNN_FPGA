#!/usr/bin/env python3
"""Keep archived tool failures and resource violations visible in summaries."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_arch import failure_reason
from run_exp import ROOT


class ArchitectureAnalysisTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
