import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rtl_acceptance import accepted_cosim, acceptance_basis, LOWER_BOUND_FAILURE


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


if __name__ == "__main__":
    unittest.main()
