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
        records.append({**row, "id": path.parent.name.split("_", 1)[0],
                        "scope": row.get("measurement_scope", "full operation")})
for path in sorted((root / "experiments").glob("*_*/host_utilization_baseline.csv")):
    samples = list(csv.DictReader(path.open(newline="")))
    if samples:
        records.append({**cpu_summary(samples), "id": path.parent.name.split("_", 1)[0],
                        "implementation_threads": 1, "scope": "30 s snapshot",
                        "min_available_GiB": min(float(row["available_kib"]) for row in samples)/1048576})
if not records:
    raise RuntimeError("No archived host telemetry CSV files")

fig, axes = plt.subplots(1, 2, figsize=(max(14, 0.85*len(records)), 6), layout="constrained")
scope_codes = {"full operation": "all", "synthesis and implementation stages": "S+R",
               "30 s snapshot": "30s"}
for axis, metric, ylabel, title in zip(axes, ("cpu_busy_pct", "min_available_GiB"),
                                      ("All logical CPUs busy (%)", "Minimum available memory (GiB)"),
                                      ("Observed remote CPU utilization", "Observed host memory headroom")):
    available = [row for row in records if row.get(metric) not in ("", None, "None")]
    for index, row in enumerate(available):
        observed = row.get("observed_implementation_thread_limit")
        color = ("#888888" if observed in ("", None, "None") else
                 "#008f7a" if int(observed) > 1 else "#c56745")
        value = float(row[metric])
        axis.bar(index, value, color=color)
        axis.annotate(f"{value:.2f}", (index, value), xytext=(0, 4),
                      textcoords="offset points", ha="center", fontsize=8)
    axis.set_xticks(range(len(available)),
                   [row["id"]+" ["+scope_codes[row["scope"]]+"]" for row in available],
                   fontsize=8, rotation=45, ha="right")
    axis.set_xlabel("Experiment [measurement scope]")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.set_ylim(0, 100 if metric == "cpu_busy_pct" else max(float(row[metric]) for row in available)*1.3)
    axis.legend(handles=[Patch(facecolor="#c56745", label="Observed limit: 1 thread"),
                         Patch(facecolor="#008f7a", label="Observed limit: >1 thread"),
                         Patch(facecolor="#888888", label="Thread limit: unknown")], fontsize=8)
fig.supxlabel("Scope: all = full operation; S+R = synthesis and routing stages; 30s = 30-second snapshot",
              fontsize=9)
fig.savefig(root / "experiments/figs/host_utilization.png", dpi=180)
plt.close(fig)
