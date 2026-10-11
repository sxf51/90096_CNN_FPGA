"""Read Linux host memory and tool RSS without collecting process arguments."""
import csv
from pathlib import Path
import threading
from run_exp import utc


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
            "tools_pid_name_rss_kib": ";".join(":".join(map(str, item)) for item in sorted(tools))}


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
