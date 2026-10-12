import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_rom_clock import inventory


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


if __name__ == "__main__":
    unittest.main()
