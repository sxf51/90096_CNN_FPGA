import csv
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archive_cosim_profiles import CHANNEL_FIELDS, PROCESS_FIELDS, archive_profiles, counter_prefix, profile_results


class ProfileTests(unittest.TestCase):
    def test_channel_prefix_preserves_measured_counters_without_reading_trace(self):
        text = io.StringIO("3\n1904526\n242\n2136450\n512\nevent history must not be parsed\n")
        _, row = counter_prefix(text, CHANNEL_FIELDS)
        self.assertEqual(row["write_block_cycles"],1904526)
        self.assertEqual(row["peak_depth"],512)
        self.assertEqual(text.readline(),"event history must not be parsed\n")

    def test_unavailable_sentinel_is_not_zero_and_truncated_prefix_fails(self):
        _, row = counter_prefix(io.StringIO("4294967295\n"*12),PROCESS_FIELDS)
        self.assertIsNone(row["process_interval_max_cycles"])
        with self.assertRaises(ValueError):
            counter_prefix(io.StringIO("3\n"),CHANNEL_FIELDS)

    def test_zip_archive_keeps_source_prefixes_and_distinguishes_invocation_interval(self):
        with tempfile.TemporaryDirectory() as temp:
            work,archive = Path(temp)/"work",Path(temp)/"archive"
            db = work/"hls/.autopilot/db"
            for folder in ("channel_depth_info","process_stalling_info"):
                (db/folder).mkdir(parents=True,exist_ok=True)
            (db/"channel_info.csv").write_text("region,raw_U,depth1.csv,chan_status1.csv\n")
            (db/"process_info.csv").write_text("region,engine1_U0,stalling1.csv,status1.csv\n")
            with zipfile.ZipFile(db/"channel_depth_info/channel.zip","w") as zipped:
                zipped.writestr("chan_status1.csv","3\n1904526\n242\n2136450\n512\n")
            with zipfile.ZipFile(db/"process_stalling_info/process.zip","w") as zipped:
                zipped.writestr("status1.csv","0\n2136450\n1068212\n1068212\n1068212\n1068181\n1068181\n1068181\n0\n0\n0\n0\nignored,event;history\n")
            files = archive_profiles(work,archive)
            self.assertTrue(all((archive/record["archived_file"]).is_file() for record in files))
            source = archive/"profiling/raw/status1.csv"
            self.assertEqual(len(source.read_text().splitlines()),12)
            with (archive/"profiling/processes.csv").open(newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["process_interval_max_cycles"],"1068212")
            self.assertIn("not inner-loop II",profile_results(archive))


if __name__ == "__main__":
    unittest.main()
