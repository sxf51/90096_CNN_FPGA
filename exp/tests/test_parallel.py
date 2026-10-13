import sys
from datetime import datetime, timezone
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyze_parallel import overlap


def task(exp_id, start, finish, times, rss):
    return {"admission": {"id": exp_id, "kind": "cosim", "started": start, "finished": finish},
            "samples": [{"time": datetime.fromtimestamp(time, timezone.utc).isoformat(),
                         "task_tree_rss_kib": rss, "available_kib": 1048576} for time in times]}


class ParallelEvidenceTests(unittest.TestCase):
    def test_queued_or_sequential_tasks_are_not_counted_as_overlap(self):
        self.assertIsNone(overlap(task("F43", 0, 10, [5], 100), task("F46", 10, 20, [15], 200)))

    def test_peak_pairs_use_only_temporally_aligned_samples_inside_overlap(self):
        first = task("F43", 0, 20, [0, 5, 10, 15, 20], 1048576)
        first["samples"][0]["task_tree_rss_kib"] = 100*1048576
        second = task("F46", 8, 18, [9, 14], 2*1048576)
        result = overlap(first, second)
        self.assertEqual(result["overlap_seconds"], 10)
        self.assertEqual(result["aligned_samples"], 2)
        self.assertEqual(result["peak_combined_process_tree_rss_GiB"], 3)
        self.assertEqual(result["minimum_available_GiB"], 1)

    def test_unaligned_samples_cannot_fabricate_combined_rss(self):
        result = overlap(task("F43", 0, 30, [1], 100), task("F46", 0, 30, [20], 200))
        self.assertEqual(result["overlap_seconds"], 30)
        self.assertEqual(result["aligned_samples"], 0)
        self.assertIsNone(result["peak_combined_process_tree_rss_GiB"])


if __name__ == "__main__":
    unittest.main()
