"""Reject incomplete or mislabeled reload-switch evidence before ranking."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reload_switch_evidence import check_c_sequence, check_c_validation, check_rtl_metrics, parse_transactions
from monitored_cosim import measured_axi


class ReloadSwitchTests(unittest.TestCase):
    def sequence(self):
        return dict(csim_pass=True, bit_exact=True, reload_switch_pass=True, load_flags=[1, 0, 1, 0],
                    frame_count=4, reuse_pass=True, reload_pass=True, retained_latest_pass=True,
                    reload_expected=104/256, border_mse=.000016)

    def test_sequence_rejects_legacy_or_missing_latest_retention(self):
        self.assertEqual(check_c_sequence(self.sequence()), self.sequence())
        for changes in ({"frame_count": 2}, {"load_flags": [1, 1, 1, 1]},
                        {"retained_latest_pass": False}, {"reload_expected": .4}):
            with self.assertRaises(RuntimeError):
                check_c_sequence({**self.sequence(), **changes})

    def test_fresh_process_gate_requires_first_flag_zero(self):
        result = {**self.sequence(), "frame_count": 1, "load_flags": [0], "cold_start_pass": True}
        check_c_sequence(result, cold=True)
        with self.assertRaises(RuntimeError):
            check_c_sequence({**result, "load_flags": [1]}, cold=True)

    def test_quality_requires_all13_images_and_exact_load_sequence(self):
        names = "baboon barbara bridge coastguard face flowers foreman lenna man monarch pepper ppt3 zebra".split()
        text = "\n".join("EXP_RELOAD_IMAGE " + name + " load=" + str(int(i == 0))
                         for i, name in enumerate(names))
        result = dict(csim_pass=True, bit_exact=True, reload_switch_quality_pass=True,
                      image_count=13, parameter_reuse_images=12, delta_psnr=-.0759)
        check_c_validation(result, "quality", text)
        for bad_text in (text.replace("load=0", "load=1"), text.rsplit("\n", 1)[0]):
            with self.assertRaises(RuntimeError):
                check_c_validation(result, "quality", bad_text)
        with self.assertRaises(RuntimeError):
            check_c_validation({**result, "delta_psnr": -.1001}, "quality", text)

    def test_both_c_and_rtl_must_pass_with_frozen_border(self):
        marker = "EXP_METRICS " + json.dumps(self.sequence()) + "\n"
        parent = {"border_mse": self.sequence()["border_mse"]}
        check_rtl_metrics(marker + marker, parent)
        for text in (marker, marker + marker + marker,
                     "EXP_METRICS " + json.dumps({**self.sequence(), "bit_exact": False}) + "\n" + marker):
            with self.assertRaises(RuntimeError):
                check_rtl_metrics(text, parent)
        with self.assertRaises(RuntimeError):
            check_rtl_metrics(marker + marker, {"border_mse": 0})

    def test_transaction_cycles_cannot_hide_slow_reuse_or_missing_calls(self):
        text = ("transaction 0: 300000 300029\ntransaction 1: 295000 295029\n"
                "transaction 2: 300000 300029\ntransaction 3: 295000 x\n")
        rows = parse_transactions(text)
        self.assertEqual(rows[1]["latency_cycles"], 295000)
        self.assertIsNone(rows[-1]["interval_cycles"])
        for bad in (text.replace("295000", "300001"), text.replace("transaction 3", "transaction 2"),
                    text.rsplit("transaction 3", 1)[0]):
            with self.assertRaises(RuntimeError):
                parse_transactions(bad)

    def test_zero_handshakes_cannot_hide_read_attempts_on_skipped_call(self):
        rows = []
        for i, load in enumerate((1, 0, 1, 0)):
            rows.append(dict(transaction=i, load_params=load, ar_requests=load*64, r_beats=load*8129,
                             aw_requests=0, w_beats=0, ar_valid_cycles=load*64, r_valid_cycles=load*8129,
                             aw_valid_cycles=0, w_valid_cycles=0, read_bytes=load*32516))
        measured_axi(rows)
        for key in ("ar_requests", "r_beats", "ar_valid_cycles", "r_valid_cycles", "read_bytes"):
            bad = [dict(row) for row in rows]
            bad[1][key] = 1
            with self.assertRaises(RuntimeError):
                measured_axi(bad)
        with self.assertRaises(RuntimeError):
            measured_axi(rows[:-1])


if __name__ == "__main__":
    unittest.main()
