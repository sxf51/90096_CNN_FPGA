"""Completed SSH jobs must import once and preserve planned evidence."""
import contextlib
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import remote_exp
import run_exp


class RemoteRecoveryTests(unittest.TestCase):
    def fixture(self, root):
        archive = root / "experiments/P99_recovery"
        archive.mkdir(parents=True)
        (root / "experiments/LOG.md").write_text("## Pending Human Decisions / 待人工决策\n")
        config = {"id": "P99", "name": "recovery", "clock": 4}
        purpose = "Frozen exact pair hypothesis."
        run_exp.write_json(archive / "plan.json", {
            "config_sha256": run_exp.plan_digest(config), "purpose_section": purpose})
        (archive / "P99.md").write_text(
            "## 1. Purpose and hypothesis / 目的与假设\n\n" + purpose + "\n\n## 2. Changes\n")
        metrics = dict.fromkeys(run_exp.FIELDS, "")
        metrics.update(id="P99", md_path="P99_recovery/P99.md", status="pass",
                       csim_pass=True, bit_exact=True, DSP=2.0, clock_est_ns=None)
        run_exp.write_json(archive / "metrics.json", metrics)
        return config, archive, metrics

    def test_already_collected_job_preserves_local_enrichment_without_transfer(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, archive, _ = self.fixture(root)
            config_path = root / "P99.json"
            run_exp.write_json(config_path, config)
            enrichment = archive / "profiling/local_evidence.csv"
            enrichment.parent.mkdir()
            enrichment.write_text("name,peak_depth\nfifo,16\n")
            with patch.object(remote_exp, "ROOT", root), patch.object(run_exp, "ROOT", root), \
                    patch.object(remote_exp, "check_protected"), \
                    patch.object(remote_exp.subprocess, "run") as invoked, \
                    patch.object(sys, "argv", ["remote_exp.py", str(config_path), "--collect-only"]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(remote_exp.main(), 0)
            self.assertEqual(enrichment.read_text(), "name,peak_depth\nfifo,16\n")
            self.assertTrue(invoked.called)
            self.assertTrue(all(call.args[0][0] not in {"ssh", "scp", "rsync"}
                                for call in invoked.call_args_list))

    def test_repeat_collection_preserves_one_row_including_unknowns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, archive, metrics = self.fixture(root)
            with patch.object(remote_exp, "ROOT", root), patch.object(run_exp, "ROOT", root), \
                    contextlib.redirect_stdout(io.StringIO()):
                remote_exp.record_archive(config, archive)
                remote_exp.record_archive(config, archive)
            with (root / "experiments/results.csv").open(newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["DSP"], "2.0")
            self.assertEqual(rows[0]["clock_est_ns"], "")
            self.assertEqual((root / "experiments/LOG.md").read_text().count("P99:"), 1)

    def test_conflicting_metrics_do_not_replace_or_duplicate_existing_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, archive, metrics = self.fixture(root)
            with patch.object(remote_exp, "ROOT", root), patch.object(run_exp, "ROOT", root):
                remote_exp.record_archive(config, archive)
                original = (root / "experiments/results.csv").read_bytes()
                metrics["DSP"] = 1.0
                run_exp.write_json(archive / "metrics.json", metrics)
                with self.assertRaisesRegex(RuntimeError, "conflicts"):
                    remote_exp.record_archive(config, archive)
            self.assertEqual((root / "experiments/results.csv").read_bytes(), original)

    def test_changed_paper_configuration_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, archive, _ = self.fixture(root)
            with patch.object(remote_exp, "ROOT", root), patch.object(run_exp, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "planned configuration"):
                    remote_exp.record_archive({**config, "clock": 3}, archive)
            self.assertFalse((root / "experiments/results.csv").exists())

    def test_wrong_archive_identity_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config, archive, metrics = self.fixture(root)
            metrics["id"] = "P98"
            run_exp.write_json(archive / "metrics.json", metrics)
            with patch.object(remote_exp, "ROOT", root), patch.object(run_exp, "ROOT", root):
                with self.assertRaisesRegex(RuntimeError, "archive identity"):
                    remote_exp.record_archive(config, archive)
            self.assertFalse((root / "experiments/results.csv").exists())


if __name__ == "__main__":
    unittest.main()
