import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from route_gates import evaluate_route, archive_route_evidence, parse_route_status
from run_exp import ROOT


class RouteGateTests(unittest.TestCase):
    def baseline(self):
        return {"impl_WNS_ns": .1, "impl_TNS_ns": 0, "impl_WHS_ns": .03,
                "impl_unrouted_nets": 0, "impl_LUT": 81984, "impl_FF": 163968,
                "impl_DSP": 1248, "impl_BRAM36": 144, "impl_URAM": 64}

    def test_equal_caps_pass_and_dsp_risk_is_visible(self):
        result = evaluate_route(self.baseline())
        self.assertTrue(result["route_feasible"])
        self.assertTrue(result["route_dsp_over_90pct"])
        self.assertEqual(result["impl_BRAM18K"], 288)

    def test_hold_or_unrouted_or_resource_failure_cannot_pass_with_positive_wns(self):
        for change in ({"impl_WHS_ns": -.001}, {"impl_unrouted_nets": 1}, {"impl_partial_nets": 1},
                       {"impl_TNS_ns": -1}, {"impl_LUT": 81985}, {"impl_FF": 163969},
                       {"impl_DSP": 1249}, {"impl_BRAM36": 144.5}, {"impl_URAM": 65}):
            self.assertFalse(evaluate_route({**self.baseline(), **change})["route_feasible"])

    def test_missing_evidence_is_unknown(self):
        for key in self.baseline():
            fields = self.baseline()
            fields.pop(key)
            self.assertIsNone(evaluate_route(fields)["route_feasible"])

    def test_uses_final_route_status_not_initial_unrouted_count(self):
        text = "Number of Unrouted Nets = 126796\nNumber of Unrouted Nets = 0\n"
        self.assertEqual(parse_route_status(text)["impl_unrouted_nets"], 0)

    def test_existing_w22_route_is_evaluated_without_changing_its_archive(self):
        archive = ROOT / "experiments/W22_ws_clock_4p95_W21"
        before = (archive / "metrics.json").read_bytes()
        result = archive_route_evidence(archive)
        self.assertTrue(result["route_feasible"])
        self.assertEqual(result["impl_WHS_ns"], .032)
        self.assertEqual(result["impl_BRAM18K"], 109)
        self.assertEqual((archive / "metrics.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
