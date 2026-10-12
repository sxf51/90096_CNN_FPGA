import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audit_rom_clock
from audit_rom_clock import audit_pending, inventory


class RomClockAuditTests(unittest.TestCase):
    def test_measured_and_queued_and_unlaunched_are_separate(self):
        state = {"experiment_ids": ["W24", "W25", "W23"], "waiting_for_memory": ["W23"],
                 "session_jobs": {"1": ["W25"]}}
        self.assertEqual(inventory(state, [{"id": "W24"}]), (["W24"], ["W23", "W25"]))

    def test_unexplained_missing_result_is_not_silently_omitted(self):
        with self.assertRaisesRegex(RuntimeError, "no recovery state"):
            inventory({"experiment_ids": ["W24", "W25"]}, [{"id": "W24"}])

    def test_completed_memory_wait_and_duplicate_results_fail(self):
        with self.assertRaisesRegex(RuntimeError, "still listed"):
            inventory({"experiment_ids": ["W24"], "waiting_for_memory": ["W24"]}, [{"id": "W24"}])
        with self.assertRaisesRegex(RuntimeError, "Duplicate"):
            inventory({"experiment_ids": ["W24"]}, [{"id": "W24"}, {"id": "W24"}])

    def test_skipped_condition_remains_unmeasured_and_must_be_inactive(self):
        state = {"experiment_ids": ["W28", "W30"], "skipped_plans": {
            "W30": {"prerequisite": "W28", "reason": "Cycle gate failed"}}}
        self.assertEqual(inventory(state, [{"id": "W28"}]), (["W28"], ["W30"]))
        for change, rows in (({"session_jobs": {"1": ["W30"]}}, [{"id": "W28"}]),
                             ({}, [{"id": "W28"}, {"id": "W30"}])):
            with self.assertRaisesRegex(RuntimeError, "unmeasured and inactive"):
                inventory({**state, **change}, rows)

    def test_skip_audit_requires_failed_prerequisite_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "exp/configs").mkdir(parents=True)
            archive = root / "experiments/W30_clock"
            archive.mkdir(parents=True)
            config = {"id": "W30", "operation": "impl"}
            encoded = json.dumps({"config_sha256": "digest", "configuration": config}).encode()
            (archive / "plan.json").write_bytes(encoded)
            (root / "exp/configs/W30.json").write_text(json.dumps(config))
            prerequisite = root / "experiments/W28_cosim"
            prerequisite.mkdir()
            (prerequisite / "metrics.json").write_text(json.dumps({"status": "cosim_complete"}))
            state = {"planned_conditions": {"W30": "W28 must pass"}, "skipped_plans": {
                "W30": {"prerequisite": "W28", "reason": "Cycle gate failed"}}}
            with patch.object(audit_rom_clock, "ROOT", root), \
                    patch.object(audit_rom_clock, "plan_digest", return_value="digest"), \
                    patch.object(audit_rom_clock.subprocess, "check_output", return_value=encoded):
                with self.assertRaisesRegex(RuntimeError, "failed prerequisite evidence"):
                    audit_pending(state, ["W30"])
                (prerequisite / "metrics.json").write_text(json.dumps({"status": "fail"}))
                record, = audit_pending(state, ["W30"])
                self.assertTrue(record["not_run_condition_failed"])
                self.assertFalse(record["has_measured_result"])
                self.assertEqual(len(record["prerequisite_metrics_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
