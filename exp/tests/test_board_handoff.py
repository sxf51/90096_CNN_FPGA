import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_board_handoff import validate_handoff
from reproduce_exp import archived
from route_gates import archive_route_evidence


class BoardHandoffTests(unittest.TestCase):
    def evidence(self):
        return (
            {"operation": "impl", "verify_parent": "C13",
             "verification": {"impl_target_clock_ns": 5}, "parent_config": {"top": "srcnn"}},
            {"route_feasible": True},
            {"operation": "cosim", "verify_parent": "C13", "reload_params": True,
             "reload_validation": {"frame_count": 2, "reload_pass": True, "bit_exact": True},
             "verification": {"rtl_status": "Pass", "changed_params_bit_exact": True,
                              "rtl_latency_max": 300632, "rtl_interval_max": 300661}},
            {"status": "cosim_complete"},
        )

    def test_matching_closed_changed_parameter_evidence(self):
        self.assertEqual(validate_handoff(*self.evidence()), ("C13", 5))

    def test_completed_c18_and_legacy_f98_provenance(self):
        for impl_id, rtl_id, parent in (("C18", "C14", "C13"), ("F98", "F97", "W21")):
            impl = archived(impl_id)
            rtl = archived(rtl_id)
            self.assertEqual(validate_handoff(
                json.loads((impl/"config.json").read_text()), archive_route_evidence(impl),
                json.loads((rtl/"config.json").read_text()), json.loads((rtl/"metrics.json").read_text())),
                (parent, 5))

    def test_missing_or_failed_physical_acceptance(self):
        for route in ({}, {"route_feasible": False}, {"route_feasible": None}):
            config, _, rtl, metrics = self.evidence()
            with self.assertRaises(RuntimeError):
                validate_handoff(config, route, rtl, metrics)

    def test_other_parent_or_rom_cannot_inherit_runtime_handoff(self):
        for index, key, value in ((0, "parent_config", {"top": "srcnn_rom"}),
                                  (2, "verify_parent", "W21")):
            evidence = list(self.evidence())
            evidence[index][key] = value
            with self.assertRaises(RuntimeError):
                validate_handoff(*evidence)

    def test_unverified_reload_or_incomplete_transactions(self):
        for change in ({"reload_params": False}, {"reload_validation": {"frame_count": 1}},
                       {"verification": {"rtl_status": "Pass", "changed_params_bit_exact": False}}):
            config, route, rtl, metrics = self.evidence()
            rtl.update(change)
            with self.assertRaises(RuntimeError):
                validate_handoff(config, route, rtl, metrics)

    def test_cycle_data_must_be_complete_positive_integers(self):
        for key in ("rtl_latency_max", "rtl_interval_max"):
            for value in (None, 0, -1, 300632.5):
                evidence = copy.deepcopy(self.evidence())
                evidence[2]["verification"][key] = value
                with self.assertRaises(RuntimeError):
                    validate_handoff(*evidence)


if __name__ == "__main__":
    unittest.main()
