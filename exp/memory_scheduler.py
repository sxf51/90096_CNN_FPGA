"""Linux HLS task admission with persisted reservations and measured memory."""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import signal
import threading
import time
import uuid

GIB_KIB = 1024 * 1024
BUDGETS = {"impl": 12.5, "cosim": 7.5, "csynth": 2.5, "csynth_t4": 4.0, "csim": 1.0}


def admission_reason(tasks, kind, available_gib, budgets=None, parallel=False,
                     total_gib=13.0, floor_gib=2.0):
    budgets = budgets or BUDGETS
    if kind not in budgets:
        raise ValueError("Unknown memory task class: " + kind)
    reserved = sum(task["budget_gib"] for task in tasks)
    if reserved + budgets[kind] > total_gib:
        return "registered reservations exceed total memory budget"
    if available_gib - budgets[kind] < floor_gib:
        return "MemAvailable minus reservation is below the available-memory floor"
    hardware = [task["kind"] for task in tasks if task["kind"] != "csim"]
    if not parallel and hardware and kind != "csim":
        return "hardware concurrency has not been validated or was disabled after OOM"
    if ("impl" in hardware and kind != "csim") or (kind == "impl" and hardware):
        return "implementation may overlap only C simulation"
    if kind == "cosim" and "cosim" in hardware:
        return "one cosimulation at a time"
    synth_count = sum(item in {"csynth", "csynth_t4"} for item in hardware)
    cap = 2 if "cosim" in hardware or kind == "cosim" else 4
    if synth_count + (kind in {"csynth", "csynth_t4"}) > cap:
        return "synthesis concurrency cap reached"
    return None


def process_start(pid, proc_root=Path("/proc")):
    try:
        return (proc_root / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return None


def group_alive(group, proc_root=Path("/proc")):
    if not group:
        return False
    for path in proc_root.glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            if fields[0] != "Z" and int(fields[2]) == group:
                return True
        except (OSError, ValueError, IndexError):
            pass
    return False


def available_gib(proc_root=Path("/proc")):
    fields = dict(line.split(":", 1) for line in (proc_root / "meminfo").read_text().splitlines())
    return int(fields["MemAvailable"].split()[0]) / GIB_KIB


def oom_count(proc_root=Path("/proc")):
    try:
        fields = dict(line.split() for line in (proc_root / "vmstat").read_text().splitlines())
        return int(fields["oom_kill"])
    except (OSError, ValueError, KeyError):
        return None


class Scheduler:
    def __init__(self, root):
        self.directory = Path(root) / "workspace/exp_runs"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / ".memory_scheduler.json"
        self.guard = self.directory / ".memory_scheduler.guard"

    @contextmanager
    def state(self):
        with self.guard.open("a+") as guard:
            fcntl.flock(guard, fcntl.LOCK_EX)
            try:
                state = json.loads(self.path.read_text()) if self.path.exists() else {
                    "total_gib": 13.0, "floor_gib": 2.0, "budgets": BUDGETS.copy(),
                    "parallel_validated": False, "serial_after_oom": False, "tasks": {}}
                yield state
                temporary = self.path.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n")
                temporary.replace(self.path)
            finally:
                fcntl.flock(guard, fcntl.LOCK_UN)

    def acquire(self, exp_id, kind, controlled=False, wait_timeout=86400, event=None):
        if not Path("/proc/meminfo").is_file():
            raise RuntimeError("Memory admission requires Linux /proc; do not run HLS on the Mac")
        started, last_reason = time.monotonic(), None
        token = uuid.uuid4().hex
        while True:
            with self.state() as state:
                state["tasks"] = {key: task for key, task in state["tasks"].items()
                                  if process_start(task["pid"]) == task["process_start"] or
                                  group_alive(task.get("process_group"))}
                current = available_gib()
                reason = admission_reason(list(state["tasks"].values()), kind, current,
                                          state["budgets"],
                                          (state["parallel_validated"] or controlled) and
                                          not state["serial_after_oom"],
                                          state["total_gib"], state["floor_gib"])
                if reason is None:
                    state["tasks"][token] = {"id": exp_id, "kind": kind, "pid": os.getpid(),
                                              "process_start": process_start(os.getpid()),
                                              "budget_gib": state["budgets"][kind],
                                              "available_gib_at_start": current, "started": time.time()}
                    record = dict(state["tasks"][token])
            if reason is None:
                if event:
                    event({"event": "admitted", **record})
                return Lease(self, token, record)
            if reason != last_reason:
                last_reason = reason
                if event:
                    event({"event": "waiting", "reason": reason, "available_gib": current,
                           "required_available_gib": state["budgets"][kind] + state["floor_gib"]})
                print("EXP_MEMORY_WAIT", exp_id, kind, reason, f"available={current:.3f}GiB", flush=True)
            if time.monotonic() - started >= wait_timeout:
                raise RuntimeError("Memory admission timeout: " + reason)
            time.sleep(3)


class Lease:
    def __init__(self, scheduler, token, record):
        self.scheduler, self.token, self.record = scheduler, token, record
        self.group = None
        self.pressure = None
        self.stop = threading.Event()
        self.thread = None
        self.oom_before = oom_count()

    def register_process(self, pid):
        self.group = pid
        with self.scheduler.state() as state:
            state["tasks"][self.token]["process_group"] = pid

    def monitor(self):
        while not self.stop.wait(2):
            floor = 2.0
            with self.scheduler.state() as state:
                floor = state["floor_gib"]
            current = available_gib()
            if current < floor and self.group:
                self.pressure = {"available_gib": current, "floor_gib": floor}
                try:
                    os.killpg(self.group, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                if not self.stop.wait(5):
                    try:
                        os.killpg(self.group, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                return

    def __enter__(self):
        self.thread = threading.Thread(target=self.monitor, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()
        if self.pressure and self.group:
            try:
                os.killpg(self.group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.oom_after = oom_count()
        with self.scheduler.state() as state:
            state["tasks"].pop(self.token, None)
            if self.oom_before is not None and self.oom_after is not None and self.oom_after > self.oom_before:
                state["serial_after_oom"] = True
                state["parallel_validated"] = False
                old = state["budgets"][self.record["kind"]]
                state["budgets"][self.record["kind"]] = max(old + 1, old * 1.2)
                state["last_oom"] = {"id": self.record["id"], "before": self.oom_before,
                                     "after": self.oom_after, "new_budget_gib": state["budgets"][self.record["kind"]]}


def scheduled_invoke(config, archive, kind, args, settings, cwd, logfile, timeout):
    from run_exp import ROOT, invoke, utc, write_json
    from host_memory import MemoryMonitor
    scheduler = Scheduler(ROOT)
    event_path = archive / "scheduler_events.jsonl"
    def event(record):
        with event_path.open("a") as stream:
            stream.write(json.dumps({"time": utc(), **record}, sort_keys=True) + "\n")
    lease = scheduler.acquire(config["id"], kind,
                              config.get("controlled_parallel_validation", False),
                              config.get("memory_wait_timeout", 86400), event)
    destination = archive / (kind + "_host_memory.csv")
    with lease, MemoryMonitor(destination, interval=2, root_pid=os.getpid()):
        result = invoke(args, settings, cwd, logfile, timeout, on_start=lease.register_process)
    record = {**lease.record, "finished": time.time(), "oom_before": lease.oom_before,
              "oom_after": lease.oom_after, "memory_pressure": lease.pressure, "exit_code": result[0]}
    write_json(archive / (kind + "_admission.json"), record)
    event({"event": "released", **record})
    if lease.pressure:
        raise RuntimeError("Task terminated to preserve 2 GiB MemAvailable: " + json.dumps(lease.pressure))
    return result
