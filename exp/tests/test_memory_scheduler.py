import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from memory_scheduler import admission_reason, Scheduler, BUDGETS
from host_memory import process_tree_rss


def task(kind):
    return {"kind": kind, "budget_gib": BUDGETS[kind]}


class AdmissionTests(unittest.TestCase):
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
