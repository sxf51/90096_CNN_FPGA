#!/usr/bin/env python3
"""Plot the ROM/clock/FIFO/T4 workstream using derived CSV files only."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
FIGS = ROOT/"experiments/figs"
FIGS.mkdir(parents=True, exist_ok=True)


def rows(name):
    with (ROOT/"experiments"/name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def present(value):
    return value not in {"", "None", "unknown"}


comparison = rows("rom_clock_comparison.csv")
designs = [row for row in comparison if row["operation"] == "csim/csynth" and present(row["HLS_DSP"])]
fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
colors = {"W": "#287e8e", "F": "#b65352", "C": "#668b3c"}
for series, color in colors.items():
    group = [row for row in designs if row["series"] == series]
    if group:
        ax.scatter([float(row["HLS_DSP"]) for row in group],
                   [float(row["HLS_latency_ms_est"]) for row in group], color=color, label=series, s=48)
for index, row in enumerate(designs):
    ax.annotate(row["id"]+" T"+row["T"], (float(row["HLS_DSP"]), float(row["HLS_latency_ms_est"])),
                xytext=(5, 5+12*(index%3)), textcoords="offset points", fontsize=8)
ax.set(xlabel="HLS estimated DSP count", ylabel="HLS latency estimate (ms)",
       title="ROM, clock and FIFO controls: HLS screening only")
if designs:
    ax.legend(title="Series")
fig.savefig(FIGS/"rom_clock_pareto.png", dpi=180)
plt.close(fig)

parts = rows("rom_clock_dsp.csv")
fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
bottom = [0.0]*len(parts)
for field, color in (("Conv1_DSP", "#287e8e"), ("Conv2_DSP", "#b65352"),
                     ("Conv3_DSP", "#668b3c"), ("other_DSP", "#797979")):
    values = [float(row[field]) for row in parts]
    ax.bar(range(len(parts)), values, bottom=bottom, label=field.removesuffix("_DSP"), color=color)
    bottom = [first+second for first, second in zip(bottom, values)]
ax.set_xticks(range(len(parts)), [row["id"] for row in parts])
ax.set(xlabel="Experiment ID", ylabel="HLS estimated DSP count", title="DSP composition of independent mainline controls")
ax.legend()
fig.savefig(FIGS/"rom_clock_dsp.png", dpi=180)
plt.close(fig)

estimates = rows("rom_clock_estimates.csv")
for metric, unit in (("DSP", "DSP count"), ("latency_cycles", "cycles")):
    points = [row for row in estimates if row["metric"] == metric and present(row["estimate"]) and present(row["actual"])]
    fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
    for domain, color in (("HLS", "#287e8e"), ("RTL", "#b65352"), ("routed", "#668b3c")):
        group = [row for row in points if row["actual_domain"] == domain]
        if group:
            ax.scatter([float(row["estimate"]) for row in group], [float(row["actual"]) for row in group],
                       color=color, label=domain)
    for index, row in enumerate(points):
        ax.annotate(row["id"], (float(row["estimate"]), float(row["actual"])),
                    xytext=(5, 5+10*(index%3)), textcoords="offset points", fontsize=8)
    extent = max([1]+[float(row[key]) for row in points for key in ("estimate", "actual")])*1.12
    ax.plot([0, extent], [0, extent], linestyle="--", color="#777777", label="Estimate = actual")
    ax.set(xlabel="Paper estimate ("+unit+")", ylabel="Reported actual ("+unit+")",
           title="Paper estimate versus actual: "+metric)
    if metric == "latency_cycles":
        ax.set_title("Cycle estimates versus HLS lower bounds and measured RTL")
    ax.legend()
    fig.savefig(FIGS/("rom_clock_estimate_"+metric+".png"), dpi=180)
    plt.close(fig)

measured = [row for row in comparison if row["operation"] == "cosim" and present(row["rtl_cycles"])]
fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
if measured:
    ax.bar(range(len(measured)), [float(row["rtl_cycles"]) for row in measured], color="#287e8e", label="Two-frame RTL maximum latency")
    ax.set_xticks(range(len(measured)), [row["id"]+" / "+row["parent"] for row in measured])
ax.axhline(558758, linestyle="--", color="#b65352", label="F97 / W21 baseline")
ax.set(xlabel="Verification experiment / hardware parent", ylabel="Measured latency (cycles)",
       title="Finite-FIFO frame latency: changed input or parameters")
ax.legend()
fig.savefig(FIGS/"rom_clock_rtl_cycles.png", dpi=180)
plt.close(fig)
