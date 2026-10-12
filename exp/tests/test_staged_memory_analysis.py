import csv
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_route import memory_summary


def telemetry(path, rss, counters):
    rows = [{"available_kib": 5*1048576, "tool_rss_kib": rss*1048576,
             "task_tree_rss_kib": rss*1048576, "cpu_total_ticks": total,
             "cpu_idle_ticks": idle, "logical_cpus": 12, "load1": 1.5}
            for total, idle in counters]
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class StagedMemoryAnalysisTests(unittest.TestCase):
    def test_stage_measurements_do_not_include_another_tasks_waiting_peak(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            telemetry(archive/"host_memory.csv", 100, [(100, 0), (5100, 0)])
            telemetry(archive/"impl_synth_host_memory.csv", 7, [(100, 80), (200, 160)])
            telemetry(archive/"impl_route_host_memory.csv", 8, [(5000, 160), (5100, 240)])
            result, phases = memory_summary(archive, {"implementation_backend": "staged_packaged_flow"})
            self.assertEqual(result["peak_process_tree_RSS_GiB"], 8)
            self.assertEqual(result["samples"], 4)
            self.assertEqual(result["cpu_busy_pct"], 20)
            self.assertEqual(result["missing_telemetry_files"], [])
            self.assertEqual([row["peak_process_tree_RSS_GiB"] for row in phases], [7, 8])
            self.assertTrue((archive/"host_memory_phases.csv").is_file())

    def test_missing_stage_is_explicit_and_does_not_use_global_samples(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            telemetry(archive/"host_memory.csv", 100, [(100, 0), (5100, 0)])
            result, phases = memory_summary(archive, {"implementation_backend": "staged_packaged_flow"})
            self.assertIsNone(result["peak_process_tree_RSS_GiB"])
            self.assertEqual(result["samples"], 0)
            self.assertEqual(len(result["missing_telemetry_files"]), 2)
            self.assertTrue(all(row["samples"] == 0 for row in phases))

    def test_existing_single_process_implementation_uses_its_own_samples(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp)
            telemetry(archive/"host_memory.csv", 100, [(100, 0), (5100, 0)])
            telemetry(archive/"impl_host_memory.csv", 12, [(100, 80), (200, 160)])
            result, phases = memory_summary(archive, {})
            self.assertEqual(result["peak_process_tree_RSS_GiB"], 12)
            self.assertEqual(result["cpu_busy_pct"], 20)
            self.assertEqual(result["telemetry_file"], "impl_host_memory.csv")
            self.assertEqual(len(phases), 1)
            self.assertNotIn("missing_telemetry_files", result)


if __name__ == "__main__":
    unittest.main()
