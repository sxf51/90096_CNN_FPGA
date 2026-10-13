import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prepare_board_handoff import register_map, validate_handoff
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
        for impl_id, rtl_id, parent in (("C18", "C14", "C13"), ("F98", "F97", "W21"),
                                       ("C22", "C20", "C17")):
            impl = archived(impl_id)
            rtl = archived(rtl_id)
            self.assertEqual(validate_handoff(
                json.loads((impl/"config.json").read_text()), archive_route_evidence(impl),
                json.loads((rtl/"config.json").read_text()), json.loads((rtl/"metrics.json").read_text())),
                (parent, 5))

    def test_generated_legacy_pointer_maps_still_have_eight_arguments(self):
        root = Path(__file__).resolve().parents[2]
        for impl_id in ("C18", "C22", "F98"):
            header = root / "experiments/board_handoff" / impl_id / "xsrcnn_hw.h"
            registers = register_map(header.read_text(), "srcnn")
            self.assertEqual(len(registers), 8)
            self.assertTrue(all(item["pointer_bits"] == 64 for item in registers))

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


class ReloadBoardHandoffTests(unittest.TestCase):
    def evidence(self):
        transactions = []
        for index, load in enumerate((1, 0, 1, 0)):
            transactions.append(dict(transaction=index, load_params=load,
                                     latency_cycles=300000 if load else 295000,
                                     interval_cycles=300029 if index < 3 else None,
                                     ar_requests=load * 64, r_beats=load * 8129, aw_requests=0, w_beats=0,
                                     ar_valid_cycles=load * 64, r_valid_cycles=load * 8129,
                                     aw_valid_cycles=0, w_valid_cycles=0, read_bytes=load * 32516))
        return (
            dict(operation="impl", verify_parent="C23", verification=dict(impl_target_clock_ns=5),
                 parent_config=dict(top="srcnn_reload")),
            dict(route_feasible=True),
            dict(operation="cosim", verify_parent="C23", reload_switch_validation=True,
                 verification=dict(rtl_status="Pass", rtl_latency_max=300000, rtl_interval_max=300029,
                                   reload_switch_bit_exact=True, skip_parameter_axi_zero=True,
                                   rtl_frame_count=4, reload_switch_transactions=transactions,
                                   functional_validation=dict(csim_pass=True, bit_exact=True,
                                                              reload_switch_pass=True, load_flags=[1, 0, 1, 0],
                                                              frame_count=4, reuse_pass=True, reload_pass=True,
                                                              retained_latest_pass=True, reload_expected=104/256))),
            dict(status="cosim_complete"),
        )

    def test_reload_top_requires_its_independent_four_call_proof(self):
        self.assertEqual(validate_handoff(*self.evidence()), ("C23", 5))
        for key, value in (("reload_switch_bit_exact", False), ("skip_parameter_axi_zero", False),
                           ("rtl_frame_count", 2), ("functional_validation", {})):
            evidence = copy.deepcopy(self.evidence())
            evidence[2]["verification"][key] = value
            with self.assertRaises(RuntimeError):
                validate_handoff(*evidence)

    def test_skipped_axi_activity_rejects_handoff_even_with_pass_flags(self):
        evidence = self.evidence()
        evidence[2]["verification"]["reload_switch_transactions"][1]["r_valid_cycles"] = 1
        with self.assertRaises(RuntimeError):
            validate_handoff(*evidence)

    def test_legacy_two_frame_proof_cannot_validate_the_reload_interface(self):
        config, route, rtl, metrics = BoardHandoffTests().evidence()
        config["parent_config"]["top"] = "srcnn_reload"
        with self.assertRaises(RuntimeError):
            validate_handoff(config, route, rtl, metrics)

    def test_generated_scalar_register_is_distinct_from_pointer_arguments(self):
        names = ["in_r", "out_r", "weights1", "biases1", "weights2", "biases2", "weights3", "biases3"]
        header = "\n".join("#define XSRCNN_RELOAD_CONTROL_ADDR_" + name.upper() +
                           "_DATA 0x" + format(16 + index * 12, "x") for index, name in enumerate(names))
        header += "\n#define XSRCNN_RELOAD_CONTROL_ADDR_LOAD_PARAMS_DATA 0x70\n"
        header += "#define XSRCNN_RELOAD_CONTROL_BITS_LOAD_PARAMS_DATA 1\n"
        registers = register_map(header, "srcnn_reload")
        self.assertEqual(registers[-1], dict(argument="load_params", offset="0x70", pointer_bits=None, scalar_bits=1))
        for invalid in (header.replace("_DATA 1\n", "_DATA 32\n"),
                        header.replace("WEIGHTS3_DATA", "OTHER_DATA")):
            with self.assertRaises(RuntimeError):
                register_map(invalid, "srcnn_reload")


if __name__ == "__main__":
    unittest.main()
