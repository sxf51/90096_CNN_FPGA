#!/usr/bin/env python3
"""Plot report-derived compute/loader attribution from CSV only."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader((root / "experiments/weight_loading_comparison.csv").open(newline="")))
rows = [row for row in rows if row["dataflow_LUT"] not in {"", "None"} and row["outside_LUT"] not in {"", "None"}]
fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
x = list(range(len(rows)))
inside = [float(row["dataflow_LUT"]) for row in rows]
outside = [float(row["outside_LUT"]) for row in rows]
ax.bar(x, inside, label="Inside DATAFLOW (includes local loaders)", color="#287e8e")
ax.bar(x, outside, bottom=inside, label="Outside DATAFLOW", color="#bb534d")
for i, row in enumerate(rows):
    ax.annotate(row["id"], (i, inside[i]+outside[i]), xytext=(0, 5), textcoords="offset points", ha="center")
ax.axhline(81984, color="#666666", linestyle="--", label="HLS LUT gate: 81,984")
ax.set_xticks(x, [row["id"]+" T"+row["T_target"] for row in rows])
ax.set_ylabel("HLS estimated LUT count")
ax.set_xlabel("Experiment and cycles per pixel T")
ax.set_title("Runtime weight-loader area attribution")
ax.set_ylim(0, max([81984]+[a+b for a,b in zip(inside,outside)])*1.2)
ax.legend(loc="upper left", fontsize=8)
fig.savefig(root / "experiments/figs/weight_loading_area.png", dpi=180)
plt.close(fig)
