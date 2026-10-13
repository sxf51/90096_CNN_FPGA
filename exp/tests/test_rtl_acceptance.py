import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rtl_acceptance import accepted_cosim, acceptance_basis, check_transaction_cycle_limits, LOWER_BOUND_FAILURE


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.row = {"status": "fail"}
        self.config = {"operation": "cosim", "errors": [LOWER_BOUND_FAILURE],
                       "reload_params": True, "rtl_max_cycles": 564345,
                       "verification": {"rtl_status": "Pass", "rtl_latency_max": 549438,
                                        "changed_params_bit_exact": True},
                       "acceptance_override": {"authorized_by": "user", "max_cycles": 564345,
                                               "policy": "upper_latency_bound_only",
                                               "decision_reference": "docs/0005 section6.2"}}

    def test_only_explicit_user_revision_accepts_faster_complete_rtl(self):
        self.assertTrue(accepted_cosim(self.row, self.config))
        self.assertEqual(acceptance_basis(self.row, self.config), "user_authorized_upper_only")
        config = copy.deepcopy(self.config)
        config.pop("acceptance_override")
        self.assertFalse(accepted_cosim(self.row, config))
        self.assertEqual(self.row["status"], "fail")

    def test_revision_cannot_hide_numerical_host_or_upper_bound_failures(self):
        for section, key, value in (("verification", "changed_params_bit_exact", False),
                                    ("verification", "rtl_status", "Fail"),
                                    ("verification", "rtl_latency_max", 564346),
                                    ("acceptance_override", "max_cycles", 600000),
                                    ("acceptance_override", "authorized_by", "agent")):
            config = copy.deepcopy(self.config)
            config[section][key] = value
            self.assertFalse(accepted_cosim(self.row, config))
        config = copy.deepcopy(self.config)
        config["errors"] = ["impl failed (exit=137)"]
        self.assertFalse(accepted_cosim(self.row, config))

    def test_per_call_bound_catches_reuse_regression_hidden_by_loaded_max(self):
        config = {"reload_switch_validation": True, "rtl_transaction_max_cycles": [303000, 298960, 303000, 298960]}
        measured = {"reload_switch_transactions": [
            {"transaction": i, "load_params": load, "latency_cycles": 300000}
            for i, load in enumerate((1, 0, 1, 0))]}
        with self.assertRaisesRegex(RuntimeError, "transaction 1"):
            check_transaction_cycle_limits(config, measured)
        for row in measured["reload_switch_transactions"]:
            row["latency_cycles"] = config["rtl_transaction_max_cycles"][row["transaction"]]
        check_transaction_cycle_limits(config, measured)
        for row in measured["reload_switch_transactions"]:
            row["latency_cycles"] = 200000
        check_transaction_cycle_limits(config, measured)

    def test_per_call_bound_rejects_missing_reordered_or_invalid_measurements(self):
        config = {"reload_switch_validation": True, "rtl_transaction_max_cycles": [101] * 4}
        calls = [{"transaction": i, "load_params": load, "latency_cycles": 100}
                 for i, load in enumerate((1, 0, 1, 0))]
        for rows in (calls[:3], list(reversed(calls)), [*calls[:3], {**calls[3], "latency_cycles": 0}],
                     [*calls[:3], {**calls[3], "latency_cycles": 100.0}]):
            with self.assertRaises(RuntimeError):
                check_transaction_cycle_limits(config, {"reload_switch_transactions": rows})
        for limits in ([101] * 3, [True] * 4, [0] * 4):
            with self.assertRaises(RuntimeError):
                check_transaction_cycle_limits({**config, "rtl_transaction_max_cycles": limits},
                                               {"reload_switch_transactions": calls})


if __name__ == "__main__":
    unittest.main()
