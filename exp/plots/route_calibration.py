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
metrics = ["DSP", "LUT", "FF", "BRAM18K"]
fig, axes = plt.subplots(1, 4, figsize=(15, max(6, 0.42*len(rows)+2)),
                         sharey=True, layout="constrained")
limit = max([1]+[float(row["route_to_HLS_"+metric]) for row in rows for metric in metrics])*1.35
for ax, metric in zip(axes, metrics):
    ratios = [float(row["route_to_HLS_"+metric]) for row in rows]
    bars = ax.barh(range(len(rows)), ratios, color="#34798a", label="Routed / HLS")
    for bar, row, value in zip(bars, rows, ratios):
        ax.annotate(row["id"]+f" {value:.2f}",
                    (value, bar.get_y()+bar.get_height()/2),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=8,
                    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.5})
    ax.axvline(1, linestyle="--", color="#666666", label="HLS prediction")
    ax.set_xlim(0, limit)
    ax.set_title(metric)
    ax.set_xlabel("Routed / HLS (ratio)")
axes[0].set_yticks(range(len(rows)), [row["id"] for row in rows])
axes[0].set_ylabel("Experiment ID")
axes[0].invert_yaxis()
fig.suptitle("HLS resource calibration against routed designs")
fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=2)
fig.savefig(root / "experiments/figs/route_calibration.png", dpi=180)
plt.close(fig)
