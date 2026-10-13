import signal
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from priority_waiters import pause, resume, waiting_worker


class PriorityWaiterTests(unittest.TestCase):
    def test_admitted_tool_is_never_paused(self):
        scheduler = Mock()
        state = {"tasks": {"active": {"id": "W32"}}}
        with patch("priority_waiters.os.kill") as kill:
            with self.assertRaisesRegex(RuntimeError, "already admitted"):
                waiting_worker(scheduler, state, "W32")
        kill.assert_not_called()

    def test_all_workers_are_checked_before_any_pause(self):
        scheduler = Mock()
        scheduler.state.return_value = nullcontext({"tasks": {}})
        with (patch("priority_waiters.waiting_worker", side_effect=[{"id": "F50", "pid": 1},
                                                                   RuntimeError("not waiting")]),
              patch("priority_waiters.os.kill") as kill):
            with self.assertRaisesRegex(RuntimeError, "not waiting"):
                pause(scheduler, ["F50", "F51"])
        kill.assert_not_called()

    def test_partial_pause_failure_resumes_the_checked_workers(self):
        scheduler = Mock()
        scheduler.state.return_value = nullcontext({"tasks": {}})
        records = [{"id": "F50", "pid": 1, "process_start": "first"},
                   {"id": "F51", "pid": 2, "process_start": "second"}]
        with (patch("priority_waiters.waiting_worker", side_effect=records),
              patch("priority_waiters.os.kill", side_effect=[None, ProcessLookupError()]) as kill,
              patch("priority_waiters.resume") as release):
            with self.assertRaises(ProcessLookupError):
                pause(scheduler, ["F50", "F51"])
        self.assertEqual(kill.call_args_list[0].args, (1, signal.SIGSTOP))
        release.assert_called_once_with(records)

    def test_release_does_not_signal_a_reused_pid(self):
        records = [{"pid": 1, "process_start": "old"}, {"pid": 2, "process_start": "same"}]
        with (patch("priority_waiters.process_start", side_effect=["new", "same"]),
              patch("priority_waiters.os.kill") as kill):
            resume(records)
        kill.assert_called_once_with(2, signal.SIGCONT)


if __name__ == "__main__":
    unittest.main()
