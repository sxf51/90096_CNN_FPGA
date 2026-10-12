import sys
import json
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from memory_scheduler import admission_reason, Scheduler, BUDGETS, scheduled_invoke
from host_memory import process_tree_rss


def task(kind):
    return {"kind": kind, "budget_gib": BUDGETS[kind]}


class AdmissionTests(unittest.TestCase):
    def test_one_heavy_policy_refuses_both_heavy_pairings(self):
        for active in ("impl", "cosim"):
            for requested in ("impl", "cosim"):
                self.assertIn("one-heavy", admission_reason([task(active)], requested, 30,
                                                             one_heavy=True))
        self.assertIsNone(admission_reason([], "impl", 13.4, {**BUDGETS, "impl": 15},
                                          one_heavy=True, floor_gib=.5))

    def test_one_heavy_policy_allows_only_light_jobs_with_actual_headroom(self):
        self.assertIsNone(admission_reason([task("cosim")], "csynth", 6, one_heavy=True))
        self.assertIn("below2GiB", admission_reason([task("cosim")], "csynth", 4,
                                                   one_heavy=True))
        self.assertIn("reservations", admission_reason([task("impl")], "csim", 5,
                                                       one_heavy=True))
        self.assertIn("light-task cap", admission_reason([task("csim")]*3, "csim", 12,
                                                         one_heavy=True))

    def test_explicit_two_job_policy_bypasses_predicted_reservations(self):
        self.assertIsNone(admission_reason([task("cosim")], "cosim", 6.5,
                                          parallel=True, floor_gib=.5, user_two_jobs=True))
        self.assertIsNone(admission_reason([], "impl", 13.4,
                                          parallel=True, floor_gib=.5, user_two_jobs=True))
        self.assertIn("cap", admission_reason([task("cosim"), task("cosim")], "cosim", 3,
                                              parallel=True, floor_gib=.5, user_two_jobs=True))
        self.assertIn("actual MemAvailable", admission_reason([], "cosim", .4,
                                                             floor_gib=.5, user_two_jobs=True))
        self.assertIn("disabled after OOM", admission_reason([task("cosim")], "cosim", 6.5,
                                                            floor_gib=.5, user_two_jobs=True))

    def test_package_and_implementation_share_budget_but_keep_separate_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root/"archive"
            archive.mkdir()
            config = {"id": "W29"}
            with (patch("run_exp.ROOT", root),
                  patch("memory_scheduler.Path.is_file", return_value=True),
                  patch("memory_scheduler.available_gib", return_value=15),
                  patch("memory_scheduler.process_start", return_value="task"),
                  patch("memory_scheduler.oom_count", return_value=0),
                  patch("host_memory.MemoryMonitor", side_effect=lambda *a, **k: nullcontext()) as monitor,
                  patch("run_exp.invoke", return_value=(0, 1))):
                scheduled_invoke(config, archive, "impl", ["vitis-run", "--package"],
                                 root/"settings", root, root/"package.log", 600, telemetry_name="package")
                original = (archive/"package_admission.json").read_bytes()
                scheduled_invoke(config, archive, "impl", ["vivado"],
                                 root/"settings", root, root/"impl.log", 10800)
                scheduled_invoke(config, archive, "impl", ["vivado", "-source", "report_setup_paths.tcl"],
                                 root/"settings", root, root/"paths.log", 1800, telemetry_name="setup_paths")
            package = json.loads(original)
            implementation = json.loads((archive/"impl_admission.json").read_text())
            paths = json.loads((archive/"setup_paths_admission.json").read_text())
            self.assertEqual(package["kind"], "impl")
            self.assertEqual(package["budget_gib"], BUDGETS["impl"])
            self.assertEqual(package["phase"], "package")
            self.assertEqual(implementation["phase"], "impl")
            self.assertEqual(paths["kind"], "impl")
            self.assertEqual(paths["phase"], "setup_paths")
            self.assertEqual((archive/"package_admission.json").read_bytes(), original)
            self.assertEqual([call.args[0].name for call in monitor.call_args_list],
                             ["package_host_memory.csv", "impl_host_memory.csv", "setup_paths_host_memory.csv"])
            self.assertEqual(json.loads(Scheduler(root).path.read_text())["tasks"], {})

    def test_controlled_three_job_trial_fits(self):
        tasks = [task("csynth"), task("csynth")]
        self.assertIsNone(admission_reason(tasks, "csim", 8, parallel=True))
        self.assertIsNone(admission_reason([task("csim"), task("csynth")], "csynth", 8, parallel=True))

    def test_implementation_floor_is_strict_even_on_an_idle_host(self):
        self.assertIn("MemAvailable", admission_reason([], "impl", 13.438, parallel=True))
        self.assertIsNone(admission_reason([], "impl", 14.5, parallel=True))
        self.assertIn("reservations", admission_reason([task("impl")], "csim", 15, parallel=True))

    def test_implementation_does_not_overlap_hardware(self):
        small = {**BUDGETS, "impl": 5}
        self.assertIn("only C", admission_reason([task("csynth")], "impl", 20, small, parallel=True))
        self.assertIn("only C", admission_reason([{"kind": "impl", "budget_gib": 5}], "cosim", 20, small, parallel=True))

    def test_cosim_allows_only_two_syntheses(self):
        tasks = [task("cosim"), task("csynth")]
        self.assertIsNone(admission_reason(tasks, "csynth", 8, parallel=True))
        tasks.append(task("csynth"))
        self.assertIsNotNone(admission_reason(tasks, "csynth", 8, parallel=True))

    def test_unvalidated_or_oom_mode_serializes_hardware(self):
        self.assertIn("not been validated", admission_reason([task("csynth")], "csynth", 12))
        self.assertIsNone(admission_reason([task("csynth")], "csim", 12))

    def test_four_synthesis_cap_and_total_budget_are_independent(self):
        small = {**BUDGETS, "csynth": 1}
        self.assertIn("cap", admission_reason([{"kind": "csynth", "budget_gib": 1}] * 4,
                                               "csynth", 12, small, parallel=True))
        self.assertIn("reservations", admission_reason([task("csynth_t4")] * 3,
                                                        "csynth", 12, parallel=True))

    def test_state_persists_and_failed_mutation_does_not_replace_it(self):
        with tempfile.TemporaryDirectory() as temp:
            scheduler = Scheduler(temp)
            with scheduler.state() as state:
                state["parallel_validated"] = True
            original = scheduler.path.read_bytes()
            with self.assertRaises(RuntimeError):
                with scheduler.state() as state:
                    state["parallel_validated"] = False
                    raise RuntimeError("aborted update")
            self.assertEqual(scheduler.path.read_bytes(), original)
            with scheduler.state() as state:
                self.assertTrue(state["parallel_validated"])

    def test_csim_rss_includes_compiler_and_excludes_other_task(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for pid, parent, rss in ((1, 0, 100), (2, 1, 200), (3, 2, 300), (4, 0, 1000)):
                path = root / str(pid)
                path.mkdir()
                (path / "status").write_text(f"PPid: {parent}\nVmRSS: {rss} kB\n")
            self.assertEqual(process_tree_rss(1, root), 600)


if __name__ == "__main__":
    unittest.main()
