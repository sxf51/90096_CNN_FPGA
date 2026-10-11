import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from host_memory import sample


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


if __name__ == "__main__":
    unittest.main()
