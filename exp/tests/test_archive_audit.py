#!/usr/bin/env python3
"""First-run and replay testbenches must retain their recorded Git provenance."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import close_arch


class ArchiveAuditTests(unittest.TestCase):
    def recorded(self, folder):
        return json.loads((close_arch.ROOT / "experiments" / folder / "metrics.json").read_text())

    def test_original_reload_verification_matches_recorded_source(self):
        rows = [self.recorded(folder) for folder in
                ("F93_ws_reload_cosim_F28", "F97_ws_cosim_W21")]
        records = close_arch.audit_archives(rows)
        self.assertEqual([record["id"] for record in records], ["F93", "F97"])
        self.assertTrue(all(record["archived_testbench_files_checked"] == 1 for record in records))

    def test_git_content_mismatch_is_rejected_even_with_valid_archive_hash(self):
        row = self.recorded("F93_ws_reload_cosim_F28")
        with patch.object(close_arch.subprocess, "check_output", return_value=b"different source\n"):
            with self.assertRaisesRegex(RuntimeError, "differs from recorded Git source"):
                close_arch.audit_archives([row])

    def test_replay_prefers_frozen_commit_over_new_run_commit(self):
        row = self.recorded("F93_ws_reload_cosim_F28")
        loads, show = json.loads, close_arch.subprocess.check_output
        frozen = "e8c2b3c29dbe4ed7806c682df1648ccbaeaca1ac"

        def replay(text):
            record = loads(text)
            if "verification_testbench" in record:
                record.update(frozen_source_commit=frozen, source_commit="new-run-commit")
            return record

        with patch.object(close_arch.json, "loads", side_effect=replay):
            with patch.object(close_arch.subprocess, "check_output", wraps=show) as command:
                close_arch.audit_archives([row])
                command.assert_called_once_with(
                    ["git", "show", frozen+":exp/tb/validate_reload.cpp"], cwd=close_arch.ROOT)

    def test_missing_commit_is_rejected(self):
        row = self.recorded("F93_ws_reload_cosim_F28")
        loads = json.loads

        def missing(text):
            record = loads(text)
            if "verification_testbench" in record:
                record.pop("source_commit", None)
            return record

        with patch.object(close_arch.json, "loads", side_effect=missing):
            with self.assertRaisesRegex(RuntimeError, "Missing testbench source commit"):
                close_arch.audit_archives([row])


if __name__ == "__main__":
    unittest.main()
