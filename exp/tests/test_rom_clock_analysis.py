import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_rom_clock import rtl_excess


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


if __name__ == "__main__":
    unittest.main()
