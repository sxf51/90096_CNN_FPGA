#!/usr/bin/env python3
"""Plot the ROM/clock/FIFO/T4 workstream using derived CSV files only."""
import csv
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.text import Text

ROOT = Path(__file__).resolve().parents[2]
FIGS = ROOT/"experiments/figs"
FIGS.mkdir(parents=True, exist_ok=True)


def rows(name):
    with (ROOT/"experiments"/name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def present(value):
    return value not in {"", "None", "unknown"}


def annotate_groups(ax, points, x_key, y_key, include_t=False, outside=False):
    grouped = {}
    for row in points:
        coordinate = (float(row[x_key]), float(row[y_key]))
        label = row["id"] + (" T" + row["T"] if include_t else "")
        grouped.setdefault(coordinate, []).append(label)
    if outside:
        ordered = sorted(grouped.items(), key=lambda item: (-item[0][1], item[0][0]))
        for index, (coordinate, labels) in enumerate(ordered):
            ax.annotate(textwrap.fill(", ".join(labels), width=27), coordinate,
                        xytext=(1.04, .94-.88*index/max(1, len(ordered)-1)),
                        textcoords="axes fraction", ha="left", va="center", fontsize=8,
                        annotation_clip=False,
                        arrowprops={"arrowstyle": "-", "color": "#777777", "linewidth": .5})
        return
    ax.figure.canvas.draw()
    renderer = ax.figure.canvas.get_renderer()
    occupied = [ax.get_legend().get_window_extent(renderer)] if ax.get_legend() else []
    for coordinate, labels in grouped.items():
        annotation = ax.annotate(textwrap.fill(", ".join(labels), width=27), coordinate,
                                 xytext=(6, 8), textcoords="offset points", fontsize=8,
                                 arrowprops={"arrowstyle": "-", "color": "#777777", "linewidth": .5})
        for distance in range(20):
            offsets = ((6, 8 + 22*distance), (6, -14 - 22*distance),
                       (-6, 8 + 22*distance), (-6, -14 - 22*distance))
            for offset in offsets:
                annotation.set_position(offset)
                annotation.set_ha("left" if offset[0] > 0 else "right")
                annotation.update_positions(renderer)
                box = Text.get_window_extent(annotation, renderer).expanded(1.06, 1.12)
                if (ax.bbox.contains(box.x0, box.y0) and ax.bbox.contains(box.x1, box.y1) and
                        not any(box.overlaps(previous) for previous in occupied)):
                    break
            else:
                continue
            break
        occupied.append(box)


comparison = rows("rom_clock_comparison.csv")
designs = [row for row in comparison if row["operation"] == "csim/csynth" and present(row["HLS_DSP"])]
fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
colors = {"W": "#287e8e", "F": "#b65352", "C": "#668b3c"}
for series, color in colors.items():
    group = [row for row in designs if row["series"] == series]
    if group:
        ax.scatter([float(row["HLS_DSP"]) for row in group],
                   [float(row["HLS_latency_ms_est"]) for row in group], color=color, label=series, s=48)
if designs:
    dsp = [float(row["HLS_DSP"]) for row in designs]
    ax.set_xlim(min(dsp)*.94, max(dsp)*1.08)
    ax.margins(y=.35)
ax.set(xlabel="HLS estimated DSP count", ylabel="HLS latency estimate (ms)",
       title="ROM, clock and FIFO controls: HLS screening only")
if designs:
    ax.legend(title="Series")
annotate_groups(ax, designs, "HLS_DSP", "HLS_latency_ms_est", include_t=True)
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
    fig, ax = plt.subplots(figsize=(10, 6), layout="constrained")
    for domain, color in (("HLS", "#287e8e"), ("RTL", "#b65352"), ("routed", "#668b3c")):
        group = [row for row in points if row["actual_domain"] == domain]
        if group:
            ax.scatter([float(row["estimate"]) for row in group], [float(row["actual"]) for row in group],
                       color=color, label=domain)
    extent = max([1]+[float(row[key]) for row in points for key in ("estimate", "actual")])*1.12
    ax.plot([0, extent], [0, extent], linestyle="--", color="#777777", label="Estimate = actual")
    ax.set(xlabel="Paper estimate ("+unit+")", ylabel="Reported actual ("+unit+")",
           title="Paper estimate versus actual: "+metric)
    if metric == "latency_cycles":
        ax.set_title("Cycle estimates versus HLS lower bounds and measured RTL")
    ax.legend()
    annotate_groups(ax, points, "estimate", "actual", outside=True)
    fig.savefig(FIGS/("rom_clock_estimate_"+metric+".png"), dpi=180)
    plt.close(fig)

measured = [row for row in comparison if row["operation"] == "cosim" and present(row["rtl_cycles"])]
fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
if measured:
    bars = ax.bar(range(len(measured)), [float(row["rtl_cycles"]) for row in measured],
                  color=["#287e8e" if row["status"] == "cosim_complete" else "#b65352" for row in measured],
                  label="Two-frame RTL maximum latency (red: rejected verification)")
    ax.bar_label(bars, labels=[format(int(float(row["rtl_cycles"])), ",") for row in measured], fontsize=8, padding=3)
    ax.margins(y=.12)
    ax.set_xticks(range(len(measured)), [row["id"]+" / "+row["parent"] for row in measured])
baseline = next((row for row in measured if row["id"] == "F97"), None)
if baseline:
    ax.axhline(float(baseline["rtl_cycles"]), linestyle="--", color="#b65352", label="F97 / W21 baseline")
goal = next((row for row in comparison if row.get("wsD_goal_met") in {"True", "False"} and present(row["rtl_2pct_limit_cycles"])), None)
if goal:
    ax.axhline(float(goal["rtl_2pct_limit_cycles"]), linestyle=":", color="#668b3c", label="WS-D: HLS +2% goal")
ax.set(xlabel="Verification experiment / hardware parent", ylabel="Measured latency (cycles)",
       title="Finite-FIFO frame latency: changed input or parameters")
ax.tick_params(axis="x", labelrotation=25)
ax.legend()
fig.savefig(FIGS/"rom_clock_rtl_cycles.png", dpi=180)
plt.close(fig)
