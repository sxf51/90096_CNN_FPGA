#!/usr/bin/env python3
"""Plot measured load/reuse transactions using the archived CSV only."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]


def main():
    with (ROOT / "experiments/reload_switch_measurements.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        print("No measured reload-switch transactions; no figure generated")
        return
    cases = ("first_load", "reuse", "reload", "retain")
    labels = ("First load", "Reuse", "Reload", "Retain latest")
    colors = ("#287e8e", "#668b3c", "#b65352", "#797979")
    ids = list(dict.fromkeys(row["id"] for row in rows))
    indexed = {(row["id"], row["case"]): row for row in rows}
    closed = all(row["ip_frame_ms"] not in {"", "None", "unknown"} for row in rows)
    metric = "ip_frame_ms" if closed else "latency_cycles"
    unit = "Verified IP time (ms)" if closed else "Measured RTL latency (cycles)"
    fig, axes = plt.subplots(1, 2, figsize=(max(10, len(ids) * 2), 5), layout="constrained")
    for index, (case, label, color) in enumerate(zip(cases, labels, colors)):
        group = [indexed[(exp_id, case)] for exp_id in ids]
        positions = [x + (index - 1.5) * .2 for x in range(len(ids))]
        for axis, key in zip(axes, (metric, "read_bytes")):
            bars = axis.bar(positions, [float(row[key]) for row in group], width=.19,
                            label=label, color=color)
            axis.bar_label(bars, fmt="%.3f" if key == "ip_frame_ms" else "%g",
                           fontsize=8, padding=3, rotation=90)
    for axis in axes:
        axis.set_xticks(range(len(ids)), [exp_id + " / " + indexed[(exp_id, cases[0])]["rtl_source"]
                                         if exp_id != indexed[(exp_id, cases[0])]["rtl_source"] else exp_id
                                         for exp_id in ids])
        axis.set_xlabel("Experiment ID / RTL verification")
        axis.margins(y=.28)
    axes[0].set(title="Initial loading and retained-parameter calls", ylabel=unit)
    axes[1].set(title="Observed parameter AXI read payload", ylabel="Read requests (bytes)")
    fig.suptitle("SRCNN parameter reload switch: four independently checked transactions")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=4, fontsize=8)
    fig.savefig(ROOT / "experiments/figs/reload_switch_transactions.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
