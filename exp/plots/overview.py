#!/usr/bin/env python3
"""Regenerate first-phase figures using archived CSV data only."""
import csv
from pathlib import Path
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIGS = ROOT / "experiments/figs"
FIGS.mkdir(parents=True, exist_ok=True)
rows = list(csv.DictReader((ROOT / "experiments/results.csv").open(newline="")))


def numeric(row, key):
    try:
        value = float(row[key])
        return value if math.isfinite(value) else None
    except (ValueError, KeyError):
        return None


network = [r for r in rows if r["design"] != "numpy_precision_scan" and
           not "micro" in r["design"] and numeric(r, "latency_ms_est") is not None and
           r["status"] not in {"invalid_config", "fail", "timeout"}]
fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
colors = {"pass": "#187c59", "provisional": "#217eb0", "infeasible": "#b8463e"}
for row in network:
    x, y = numeric(row, "DSP"), numeric(row, "latency_ms_est")
    ax.scatter(x, y, color=colors.get(row["status"], "#666666"), marker="x" if row["status"] == "infeasible" else "o")
    ax.annotate(row["id"] + " T=" + (row["T_target"] or "auto") + " " + row["precision_w_a_acc"],
                (x, y), xytext=(5, 6), textcoords="offset points", fontsize=7)
ax.set(title="SRCNN HLS estimates: latency vs DSP", xlabel="DSP48E2 (count)", ylabel="Estimated frame latency (ms)")
ax.set_yscale("log")
ax.axvline(1248, color="#555555", linestyle="--", linewidth=1)
ax.grid(alpha=.2)
ax.legend(handles=[Line2D([0], [0], marker="o", color=c, linestyle="", label=s) for s, c in colors.items()], loc="best")
fig.savefig(FIGS / "pareto.png", dpi=180)
plt.close(fig)

scan = list(csv.DictReader((ROOT / "experiments/E010_precision_scan/data.csv").open(newline="")))
widths = [8, 10, 12, 16]
matrix = np.full((4, 4), np.nan)
for row in scan:
    matrix[widths.index(int(row["w_bits"])), widths.index(int(row["a_bits"]))] = float(row["delta_psnr"])
fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
im = ax.imshow(matrix, cmap="RdYlGn", vmin=-.5, vmax=.1)
ax.set_xticks(range(4), widths)
ax.set_yticks(range(4), widths)
ax.set(title="E010: PSNR change on 13 supplied Set14 pairs", xlabel="Activation width (bits)", ylabel="Weight width (bits)")
for i in range(4):
    for j in range(4):
        ax.text(j, i, f"E010\n{matrix[i, j]:+.4f} dB", ha="center", va="center", fontsize=9,
                color="white" if matrix[i, j] < -.3 else "black")
fig.colorbar(im, ax=ax, label="Mean PSNR change relative to float (dB); gate >= -0.1")
fig.savefig(FIGS / "precision_heatmap.png", dpi=180)
plt.close(fig)

comparison = [r for r in network if str(r["stage"]) in {"0", "2", "3", "4"}]
comparison.sort(key=lambda r: numeric(r, "latency_ms_est"), reverse=True)
fig, ax = plt.subplots(figsize=(max(9, len(comparison) * .65), 6), constrained_layout=True)
for index, row in enumerate(comparison):
    color = "#c65c52" if str(row["stage"]) in {"0", "2"} else "#21808d"
    ax.bar(index, numeric(row, "latency_ms_est"), color=color, hatch="//" if row["status"] == "infeasible" else None)
ax.set_xticks(range(len(comparison)), [r["id"] for r in comparison], rotation=45, ha="right")
ax.set_yscale("log")
ax.set(title="Compiler controls vs streaming architectures (HLS estimates)", xlabel="Experiment ID", ylabel="Estimated frame latency (ms, logarithmic)")
ax.grid(axis="y", alpha=.2)
ax.legend(handles=[Line2D([0], [0], color="#c65c52", linewidth=8, label="Golden / compiler controls"),
                   Line2D([0], [0], color="#21808d", linewidth=8, label="Streaming architecture")])
fig.savefig(FIGS / "compiler_vs_architecture.png", dpi=180)
plt.close(fig)
print("Wrote", FIGS)
