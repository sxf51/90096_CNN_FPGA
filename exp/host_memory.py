"""Read Linux host CPU/memory and tool RSS without process arguments."""
import argparse
import csv
from pathlib import Path
import threading
import time
from run_exp import utc


def cpu_sample(proc_root):
    result = dict.fromkeys(("logical_cpus", "cpu_total_ticks", "cpu_idle_ticks", "load1"))
    try:
        lines = (proc_root / "stat").read_text().splitlines()
        ticks = list(map(int, next(line for line in lines if line.startswith("cpu ")).split()[1:9]))
        if len(ticks) < 5:
            return result
        result.update(logical_cpus=sum(line.split()[0][3:].isdigit() for line in lines if line.startswith("cpu")),
                      cpu_total_ticks=sum(ticks), cpu_idle_ticks=ticks[3]+ticks[4])
        result["load1"] = float((proc_root / "loadavg").read_text().split()[0])
    except (OSError, ValueError, StopIteration, IndexError):
        pass
    return result


def cpu_summary(rows):
    total, idle, intervals = 0, 0, 0
    for first, last in zip(rows, rows[1:]):
        try:
            elapsed = int(last["cpu_total_ticks"])-int(first["cpu_total_ticks"])
            waiting = int(last["cpu_idle_ticks"])-int(first["cpu_idle_ticks"])
        except (KeyError, ValueError, TypeError):
            continue
        if elapsed > 0 and 0 <= waiting <= elapsed:
            total += elapsed
            idle += waiting
            intervals += 1
    loads, cores = [], []
    for row in rows:
        try:
            loads.append(float(row["load1"]))
            cores.append(int(row["logical_cpus"]))
        except (KeyError, ValueError, TypeError):
            continue
    return {"cpu_intervals": intervals, "logical_cpus": max(cores) if cores else None,
            "cpu_busy_pct": 100*(total-idle)/total if total else None,
            "mean_load1": sum(loads)/len(loads) if loads else None,
            "max_load1": max(loads) if loads else None}


def sample(proc_root=Path("/proc")):
    memory = {}
    for line in (proc_root / "meminfo").read_text().splitlines():
        fields = line.split()
        memory[fields[0].rstrip(":")] = int(fields[1])
    tools = []
    for path in proc_root.glob("[0-9]*/status"):
        try:
            fields = dict(line.split(":", 1) for line in path.read_text().splitlines() if ":" in line)
            name = fields["Name"].strip()
            if name in {"vivado", "vitis_hls", "vitis-run", "v++", "xsim", "xsimk"}:
                tools.append((path.parent.name, name, int(fields.get("VmRSS", "0").split()[0])))
        except (OSError, ValueError, KeyError):
            continue
    return {"time": utc(), "total_kib": memory["MemTotal"],
            "available_kib": memory["MemAvailable"], "swap_free_kib": memory["SwapFree"],
            "tool_count": len(tools), "tool_rss_kib": sum(item[2] for item in tools),
            "tools_pid_name_rss_kib": ";".join(":".join(map(str, item)) for item in sorted(tools)),
            **cpu_sample(proc_root)}


class MemoryMonitor:
    def __init__(self, destination, interval=15):
        self.destination = destination
        self.interval = interval
        self.stop = threading.Event()
        self.thread = None

    def __enter__(self):
        if Path("/proc/meminfo").is_file():
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
        return self

    def run(self):
        with self.destination.open("w", newline="") as stream:
            writer = None
            while True:
                try:
                    row = sample()
                    if writer is None:
                        writer = csv.DictWriter(stream, fieldnames=list(row))
                        writer.writeheader()
                    writer.writerow(row)
                    stream.flush()
                except OSError:
                    pass
                if self.stop.wait(self.interval):
                    return

    def __exit__(self, *args):
        self.stop.set()
        if self.thread:
            self.thread.join()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    if args.samples < 2 or args.interval <= 0:
        parser.error("Require at least two samples and a positive interval")
    rows = []
    with args.output.open("x", newline="") as stream:
        writer = None
        for index in range(args.samples):
            row = sample()
            rows.append(row)
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
            writer.writerow(row)
            stream.flush()
            if index+1 < args.samples:
                time.sleep(args.interval)
    print(cpu_summary(rows), flush=True)


if __name__ == "__main__":
    main()
