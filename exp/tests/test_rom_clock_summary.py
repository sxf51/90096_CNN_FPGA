import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import summarize_rom_clock


class RomClockSummaryTests(unittest.TestCase):
    def test_failed_cycle_gate_cannot_supply_accepted_route_frame_time(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for exp_id, status in (("F43", "fail"), ("F44", "cosim_complete")):
                archive = root / "experiments" / (exp_id + "_probe")
                archive.mkdir(parents=True)
                (archive / "config.json").write_text(json.dumps({
                    "id": exp_id, "operation": "cosim", "verify_parent": "W21",
                    "verification": {"rtl_latency_max": 558758}}))
                (archive / "metrics.json").write_text(json.dumps({"status": status}))
            with patch.object(summarize_rom_clock, "ROOT", root):
                self.assertEqual(summarize_rom_clock.completed_rtl_matches("W21"), [("F44", 558758)])

    def test_unlaunched_plan_does_not_inherit_paper_measurements(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "experiments/W23_clock"
            archive.mkdir(parents=True)
            (archive / "plan.json").write_text(json.dumps({"configuration": {
                "id": "W23", "operation": "impl", "verify_parent": "W21",
                "estimates": {"DSP": 644, "latency_cycles": 558758}}}))
            with patch.object(summarize_rom_clock, "ROOT", root):
                record, = summarize_rom_clock.pending_experiments({
                    "experiment_ids": ["W23"], "waiting_for_memory": ["W23"]})
            self.assertEqual(record["status"], "unlaunched_memory")
            self.assertEqual(record["md_path"], "W23_clock/W23.md")
            self.assertNotIn("DSP", record)
            self.assertNotIn("rtl_cycles", record)

    def test_failed_prerequisite_plan_has_no_result_or_running_status(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "experiments/W30_clock"
            archive.mkdir(parents=True)
            (archive / "plan.json").write_text(json.dumps({"configuration": {
                "id": "W30", "operation": "impl", "verify_parent": "W27"}}))
            with patch.object(summarize_rom_clock, "ROOT", root):
                record, = summarize_rom_clock.pending_experiments({
                    "experiment_ids": ["W30"], "unlaunched_ids": ["W30"],
                    "skipped_plans": {"W30": {"prerequisite": "W28", "reason": "W28 cycle gate failed"}}})
            self.assertEqual(record["status"], "not_run_condition_failed")
            self.assertEqual(record["condition"], "W28 cycle gate failed")
            self.assertNotIn("rtl_cycles", record)


if __name__ == "__main__":
    unittest.main()
