import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from host_memory import cpu_sample, cpu_summary, sample


class MemorySampleTests(unittest.TestCase):
    def test_reads_host_and_tool_rss_without_command_lines(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "meminfo").write_text("MemTotal: 15000 kB\nMemAvailable: 9000 kB\nSwapFree: 0 kB\n")
            for pid, name, rss in (("2", "vivado", 2000), ("3", "vivado", 1500), ("4", "other", 1000)):
                path = root / pid
                path.mkdir()
                (path / "status").write_text(f"Name:\t{name}\nVmRSS:\t{rss} kB\n")
            row = sample(root)
            self.assertEqual(row["available_kib"], 9000)
            self.assertEqual(row["tool_count"], 2)
            self.assertEqual(row["tool_rss_kib"], 3500)
            self.assertEqual(row["tools_pid_name_rss_kib"], "2:vivado:2000;3:vivado:1500")
            self.assertIsNone(row["cpu_total_ticks"])

    def test_cpu_totals_do_not_double_count_guest_time(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "stat").write_text("cpu 100 20 30 400 50 4 6 1 9 2\ncpu0 1 2 3 4 5\ncpu1 1 2 3 4 5\nctxt 45\n")
            (root / "loadavg").write_text("1.25 1.0 0.5 2/55 12\n")
            row = cpu_sample(root)
            self.assertEqual(row["logical_cpus"], 2)
            self.assertEqual(row["cpu_total_ticks"], 611)
            self.assertEqual(row["cpu_idle_ticks"], 450)
            self.assertEqual(row["load1"], 1.25)

    def test_utilization_is_weighted_by_elapsed_cpu_ticks(self):
        rows = [{"cpu_total_ticks": total, "cpu_idle_ticks": idle, "logical_cpus": 12, "load1": 1.5}
                for total, idle in ((100, 80), (200, 140), (400, 240))]
        summary = cpu_summary(rows)
        self.assertAlmostEqual(summary["cpu_busy_pct"], 100*140/300)
        self.assertEqual(summary["cpu_intervals"], 2)
        self.assertEqual(summary["logical_cpus"], 12)
        self.assertEqual(summary["mean_load1"], 1.5)
        self.assertIsNone(cpu_summary([{}, {}])["cpu_busy_pct"])
        self.assertIsNone(cpu_summary(list(reversed(rows)))["cpu_busy_pct"])


if __name__ == "__main__":
    unittest.main()
