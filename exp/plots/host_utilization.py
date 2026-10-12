#!/usr/bin/env python3
"""Compare archived CPU occupancy and memory headroom using CSV files only."""
import csv
from pathlib import Path
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "exp"))
from host_memory import cpu_summary

records = []
for path in sorted((root / "experiments").glob("*_*/host_memory_summary.csv")):
    for row in csv.DictReader(path.open(newline="")):
        records.append({**row, "id": path.parent.name.split("_", 1)[0], "scope": "full operation"})
for path in sorted((root / "experiments").glob("*_*/host_utilization_baseline.csv")):
    samples = list(csv.DictReader(path.open(newline="")))
    if samples:
        records.append({**cpu_summary(samples), "id": path.parent.name.split("_", 1)[0],
                        "implementation_threads": 1, "scope": "30 s snapshot",
                        "min_available_GiB": min(float(row["available_kib"]) for row in samples)/1048576})
if not records:
    raise RuntimeError("No archived host telemetry CSV files")

fig, axes = plt.subplots(1, 2, figsize=(12, 5), layout="constrained")
for axis, metric, ylabel, title in zip(axes, ("cpu_busy_pct", "min_available_GiB"),
                                      ("All logical CPUs busy (%)", "Minimum available memory (GiB)"),
                                      ("Observed remote CPU utilization", "Observed host memory headroom")):
    available = [row for row in records if row.get(metric) not in ("", None, "None")]
    for index, row in enumerate(available):
        parallel = int(row.get("implementation_threads") or 1) > 1
        color = "#008f7a" if parallel else "#c56745"
        value = float(row[metric])
        axis.bar(index, value, color=color)
        axis.annotate(row["id"]+f"\n{value:.2f}", (index, value), xytext=(0, 4),
                      textcoords="offset points", ha="center", fontsize=8)
    axis.set_xticks(range(len(available)), [row["id"]+"\n"+(
        "full\noperation" if row["scope"] == "full operation" else "30 s\nsnapshot")
        for row in available], fontsize=8)
    axis.set_xlabel("Experiment and measurement scope")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.set_ylim(0, 100 if metric == "cpu_busy_pct" else max(float(row[metric]) for row in available)*1.3)
    axis.legend(handles=[Patch(facecolor="#c56745", label="Implementation limit: 1 thread"),
                         Patch(facecolor="#008f7a", label="Implementation limit: >1 thread")], fontsize=8)
fig.savefig(root / "experiments/figs/host_utilization.png", dpi=180)
plt.close(fig)
