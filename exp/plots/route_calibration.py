#!/usr/bin/env python3
"""Plot physical/HLS calibration ratios from archived CSV measurements only."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parents[2]
rows = list(csv.DictReader((root / "experiments/route_calibration.csv").open(newline="")))
rows = [row for row in rows if row["route_LUT"] not in {"", "None"}]
fig, ax = plt.subplots(figsize=(12, 6), layout="constrained")
metrics = ["DSP", "LUT", "FF", "BRAM18K"]
width = 0.8/max(1, len(rows))
for i, row in enumerate(rows):
    ratios = [float(row["route_to_HLS_"+metric]) for metric in metrics]
    locations = [j-0.4+width*(i+0.5) for j in range(len(metrics))]
    bars = ax.bar(locations, ratios, width=width, label=row["id"])
    for bar, value in zip(bars, ratios):
        ax.annotate(row["id"]+"\n"+f"{value:.2f}", (bar.get_x()+bar.get_width()/2, value), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8)
ax.axhline(1, linestyle="--", color="#666666", label="HLS prediction")
ax.set_xticks(range(len(metrics)), metrics)
ax.set_ylabel("Routed resource / HLS estimate (ratio)")
ax.set_xlabel("Resource")
ax.set_title("HLS resource calibration against routed designs")
ax.set_ylim(0, max([1]+[float(row["route_to_HLS_"+metric]) for row in rows for metric in metrics])*1.4)
ax.legend()
fig.savefig(root / "experiments/figs/route_calibration.png", dpi=180)
plt.close(fig)
