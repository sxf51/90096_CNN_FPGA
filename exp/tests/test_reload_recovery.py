"""Failed-run recovery retains diagnostic evidence without changing acceptance."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import recover_reload_evidence as recovery
from rtl_acceptance import accepted_cosim


class ReloadRecoveryTests(unittest.TestCase):
    def fixture(self, root):
        archive = root / "experiments/C27_failed"
        archive.mkdir(parents=True)
        (root / "experiments/LOG.md").write_text("## Pending Human Decisions / 待人工决策\n")
        rtl = dict(files_checked=2, manifest_sha256="frozen", template_matches_parent=True)
        config = dict(id="C27", name="failed", verify_parent="C23", operation="cosim",
                      reload_switch_validation=True, parameter_axi_monitor=True,
                      verification_rtl_check=rtl, parent_metrics={"border_mse": .001},
                      verification={})
        (archive / "config.json").write_text(json.dumps(config))
        (archive / "metrics.json").write_text(json.dumps({"status": "fail"}))
        (archive / "C27.md").write_text("## 5. Results / 结果\n\nOriginal fail.\n\n## 6. Interpretation / 解读\n\nKeep fail.\n")
        return archive, rtl

    def test_active_run_is_rejected_without_collecting_or_changing_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, _ = self.fixture(root)
            original = (archive / "config.json").read_bytes()
            with patch.object(recovery, "ROOT", root), patch.object(recovery, "check_protected"), \
                    patch.object(recovery, "archived", return_value=archive), \
                    patch.object(recovery, "inspect_remote", return_value={"active_pids": [123], "complete": False}), \
                    patch.object(recovery.subprocess, "run") as transfer, \
                    patch.object(sys, "argv", ["recover_reload_evidence.py", "C27"]):
                with self.assertRaisesRegex(RuntimeError, "Wait for the remote run"):
                    recovery.main()
            transfer.assert_not_called()
            self.assertEqual((archive / "config.json").read_bytes(), original)

    def test_complete_failed_run_retains_exact_outputs_and_nonzero_axi_separately(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive, rtl = self.fixture(root)
            source = root / "raw"
            source.mkdir()
            performance = source / "srcnn_reload.performance.result.transaction.xml"
            performance.write_text("transaction 0: 300000 300029\ntransaction 1: 295000 295029\n"
                                   "transaction 2: 300000 300029\ntransaction 3: 295000 x\n")
            bus = source / "reload_parameter_axi.csv"
            bus.write_text("transaction,load_params,ar_requests,r_beats,aw_requests,w_beats,"
                           "ar_valid_cycles,r_valid_cycles,aw_valid_cycles,w_valid_cycles,read_bytes\n"
                           "0,1,8129,8129,0,0,8129,8129,0,0,32516\n1,0,1,1,0,0,1,1,0,0,4\n"
                           "2,1,8129,8129,0,0,8129,8129,0,0,32516\n3,0,1,1,0,0,1,1,0,0,4\n")
            functional = dict(csim_pass=True, bit_exact=True, reload_switch_pass=True,
                              load_flags=[1, 0, 1, 0], frame_count=4, reuse_pass=True,
                              reload_pass=True, retained_latest_pass=True,
                              reload_expected=104/256, border_mse=.001)
            log = source / "cosim_execute.console.log"
            log.write_text(("EXP_METRICS " + json.dumps(functional) + "\n") * 2)
            files = [{"raw_file": ("" if path == log else "hls/sim/verilog/") + path.name,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                     for path in (performance, bus, log)]
            def transfer(command, **kwargs):
                shutil.copyfile(source / command[-2].rsplit("/", 1)[-1], command[-1])
            original = (archive / "metrics.json").read_bytes()
            with patch.object(recovery, "ROOT", root), patch.object(recovery, "check_protected"), \
                    patch.object(recovery, "archived", return_value=archive), \
                    patch.object(recovery, "append_log"), \
                    patch.object(recovery, "inspect_remote", return_value={"active_pids": [], "complete": True}), \
                    patch.object(recovery.subprocess, "check_output", return_value=json.dumps({"rtl_check_after": rtl, "files": files})), \
                    patch.object(recovery.subprocess, "run", side_effect=transfer), \
                    patch.object(sys, "argv", ["recover_reload_evidence.py", "C27"]), \
                    contextlib.redirect_stdout(io.StringIO()):
                recovery.main()
            config = json.loads((archive / "config.json").read_text())
            diagnostic = json.loads((archive / "parameter_axi_monitor/failed_evidence.json").read_text())
            self.assertEqual((archive / "metrics.json").read_bytes(), original)
            self.assertFalse(diagnostic["accepted"])
            self.assertTrue(diagnostic["functional_postcheck"]["bit_exact"])
            self.assertEqual(diagnostic["transactions"][1]["read_bytes"], 4)
            self.assertFalse(accepted_cosim({"status": "fail"}, config))
            self.assertEqual(config["verification"], {})
            self.assertEqual(config["verification_rtl_check_after"], rtl)
            self.assertIn("Raw failed-run diagnostics", (archive / "C27.md").read_text())
            self.assertIn("| 1 | 0 | 295000 | 295029 | 1 | 1 |", (archive / "C27.md").read_text())
            for record in config["verification_diagnostics"]:
                self.assertEqual(hashlib.sha256((archive / record["archived_file"]).read_bytes()).hexdigest(), record["sha256"])


if __name__ == "__main__":
    unittest.main()
