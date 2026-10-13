import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_rom_clock import reload_transactions, rtl_excess


class RomClockAnalysisTests(unittest.TestCase):
    def test_two_percent_goal_does_not_round_fractional_limit_up(self):
        accepted = rtl_excess(525237, 535741)
        rejected = rtl_excess(525237, 535742)
        self.assertEqual(accepted["rtl_2pct_limit_cycles"], 535741)
        self.assertTrue(accepted["rtl_within_2pct"])
        self.assertFalse(rejected["rtl_within_2pct"])
        self.assertGreater(rejected["rtl_hls_excess_pct"], 2)

    def test_unknown_rtl_cannot_establish_fifo_goal(self):
        result = rtl_excess(525237, None)
        self.assertIsNone(result["rtl_within_2pct"])
        self.assertIsNone(result["rtl_hls_excess_cycles"])

    def test_invalid_cycle_measurement_is_rejected(self):
        for hls, rtl in ((0, 558758), (525237, 0), (525237.5, 558758)):
            with self.assertRaises(ValueError):
                rtl_excess(hls, rtl)


class ReloadTransactionAnalysisTests(unittest.TestCase):
    def setUp(self):
        transactions = []
        for index, load in enumerate((1, 0, 1, 0)):
            transactions.append(dict(transaction=index, load_params=load,
                                     latency_cycles=300000 if load else 295000,
                                     interval_cycles=300029 if load else 295029 if index < 3 else None,
                                     ar_requests=load * 64, r_beats=load * 8129, aw_requests=0, w_beats=0,
                                     ar_valid_cycles=load * 64, r_valid_cycles=load * 8129,
                                     aw_valid_cycles=0, w_valid_cycles=0, read_bytes=load * 32516))
        self.row = dict(id="C26", status="cosim_complete", md_path="C26_rtl/C26.md")
        self.config = dict(operation="cosim", verify_parent="C23", reload_switch_validation=True,
                           verification=dict(rtl_status="Pass", reload_switch_bit_exact=True,
                                             skip_parameter_axi_zero=True, reload_switch_transactions=transactions))
        self.route = dict(id="C27", operation="impl", parent="C23", rtl_source="C26",
                          route_feasible=True, route_clock_ns=5, md_path="C27_route/C27.md")

    def result(self, route=None):
        return reload_transactions([(None, self.row, self.config)], [] if route is None else [route])

    def test_four_calls_remain_separate_without_an_inferred_clock(self):
        rows = self.result()
        self.assertEqual([row["case"] for row in rows], ["first_load", "reuse", "reload", "retain"])
        self.assertEqual([row["read_bytes"] for row in rows], [32516, 0, 32516, 0])
        self.assertTrue(all(row["ip_frame_ms"] is None and row["implementation_id"] is None for row in rows))

    def test_only_a_matching_successful_route_can_provide_milliseconds(self):
        rows = self.result(self.route)
        self.assertEqual([row["ip_frame_ms"] for row in rows], [1.5, 1.475, 1.5, 1.475])
        self.assertTrue(all(row["id"] == "C27" and row["rtl_source"] == "C26" for row in rows))
        for mismatch in ({"parent": "C13"}, {"rtl_source": "C14"}, {"route_feasible": False}):
            with self.subTest(mismatch=mismatch):
                rows = self.result({**self.route, **mismatch})
                self.assertTrue(all(row["ip_frame_ms"] is None for row in rows))

    def test_failed_rtl_cannot_enter_reuse_timings(self):
        self.row["status"] = "fail"
        self.assertEqual(self.result(self.route), [])

    def test_zero_axi_claim_cannot_hide_actual_read_valid_cycles(self):
        self.config["verification"]["reload_switch_transactions"][1]["ar_valid_cycles"] = 1
        with self.assertRaises(RuntimeError):
            self.result(self.route)

    def test_missing_exact_or_axi_proof_cannot_enter_summary(self):
        for key in ("reload_switch_bit_exact", "skip_parameter_axi_zero"):
            measured = self.config["verification"]
            measured[key] = False
            with self.assertRaises(RuntimeError):
                self.result(self.route)
            measured[key] = True


if __name__ == "__main__":
    unittest.main()
