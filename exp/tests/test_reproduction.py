#!/usr/bin/env python3
"""Replay must restore archived configuration and reject corrupt/reserved inputs."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import reproduce_exp


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.folder = self.root / "experiments/P01_parent"
        (self.folder / "source").mkdir(parents=True)
        (self.root / "exp/configs").mkdir(parents=True)
        self.kernel = self.folder / "source/kernel.cpp"
        self.kernel.write_text("int frozen_kernel;\n")
        self.base = {"id": "P01", "name": "parent", "clock": 4, "T": 1, "scope": "PE",
                     "design": "designs/live", "defines": {"EXP_BITS": 8},
                     "tb_files": ["exp/tb/check.cpp"], "estimates": {}}
        hashes = {"kernel.cpp": hashlib.sha256(self.kernel.read_bytes()).hexdigest()}
        (self.folder / "config.json").write_text(json.dumps({"source_sha256": hashes}))
        (self.folder / "plan.json").write_text(json.dumps({"configuration": self.base}))
        (self.folder / "metrics.json").write_text(json.dumps({"git_commit": "abc123", "DSP": 1,
            "BRAM18K": 0, "URAM": 0, "LUT": 132, "FF": 86, "latency_cycles": 61}))
        (self.root / "exp/configs/P01.json").write_text(json.dumps({"defines": {"EXP_BITS": 16}}))
        self.patch = patch.object(reproduce_exp, "ROOT", self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.temp.cleanup()

    def test_frozen_plan_wins_over_live_configuration(self):
        config, source = reproduce_exp.make_config("P01", "P100")
        self.assertEqual(config["defines"], {"EXP_BITS": 8})
        self.assertEqual(config["estimates"]["latency_cycles"], 61)
        self.assertEqual(config["design"], "designs/reproduce_P100")
        self.assertEqual(source, self.folder / "source")
        self.assertEqual(config["tb_files"], ["exp/tb/replay_P100/root/exp/tb/check.cpp"])
        self.assertFalse((self.root / config["design"]).exists())

    def test_verification_replay_freezes_and_checks_its_independent_testbench(self):
        self.base.update(operation="cosim", verify_parent="P02",
                         verification_testbench="exp/tb/reload.cpp", reload_params=True)
        (self.folder / "plan.json").write_text(json.dumps({"configuration": self.base}))
        tb = self.folder / "testbench/reload.cpp"
        tb.parent.mkdir()
        tb.write_text("frozen verification\n")
        observed = {"testbench_sha256": {"reload.cpp": hashlib.sha256(tb.read_bytes()).hexdigest()}}
        (self.folder / "config.json").write_text(json.dumps(observed))
        config, source = reproduce_exp.make_config("P01", "P100")
        self.assertIsNone(source)
        self.assertEqual(config["verification_testbench_parent_archive"], "experiments/P01_parent")
        self.assertEqual(config["verification_testbench_manifest"], observed["testbench_sha256"])
        tb.write_text("modified\n")
        with self.assertRaisesRegex(ValueError, "testbench changed"):
            reproduce_exp.make_config("P01", "P100")

    def test_corrupt_archived_source_is_rejected(self):
        self.kernel.write_text("int changed_kernel;\n")
        with self.assertRaisesRegex(ValueError, "snapshot missing or changed"):
            reproduce_exp.make_config("P01", "P100")

    def test_reserved_replay_id_is_rejected(self):
        (self.root / "exp/configs/P100.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "already reserved"):
            reproduce_exp.make_config("P01", "P100")

    def test_replaying_a_replay_preserves_original_testbench_without_nesting(self):
        self.base.update(frozen_testbench_root="exp/tb/replay_P00/root",
                         tb_files=["exp/tb/replay_P00/root/exp/tb/check.cpp"])
        (self.folder / "plan.json").write_text(json.dumps({"configuration": self.base}))
        observed = json.loads((self.folder / "config.json").read_text())
        observed["frozen_source_commit"] = "original456"
        (self.folder / "config.json").write_text(json.dumps(observed))
        config, _ = reproduce_exp.make_config("P01", "P100")
        self.assertEqual(config["frozen_source_commit"], "original456")
        self.assertEqual(config["tb_files"], ["exp/tb/replay_P100/root/exp/tb/check.cpp"])


if __name__ == "__main__":
    unittest.main()
