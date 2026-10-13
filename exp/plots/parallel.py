#!/usr/bin/env python3
"""Plot measured two-job task intervals from CSV evidence only."""
import csv
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[2]
with (ROOT / "experiments/parallel_jobs.csv").open(newline="") as stream:
    jobs = list(csv.DictReader(stream))
if jobs:
    origin = min(float(row["start_epoch"]) for row in jobs)
    colors = {"cosim": "#287e8e", "impl": "#b65352", "csynth": "#668b3c",
              "csynth_t4": "#668b3c", "csim": "#777777"}
    fig, ax = plt.subplots(figsize=(11, max(4, len(jobs)*.42)), layout="constrained")
    for index, row in enumerate(jobs):
        ax.barh(index, float(row["operation_seconds"])/60,
                left=(float(row["start_epoch"])-origin)/60,
                color=colors[row["kind"]], height=.65,
                hatch="//" if row["exit_code"] != "0" else None)
    ax.set_yticks(range(len(jobs)), [row["id"]+" / "+row["phase"] for row in jobs])
    ax.invert_yaxis()
    policy_line = ax.axvline((float(jobs[0]["policy_change_epoch"])-origin)/60, color="#777777",
                            linestyle="--", label="Two-job policy activated")
    started = datetime.fromtimestamp(origin, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    ax.set(xlabel="Elapsed time since "+started+" (min)", ylabel="Experiment / tool phase",
           title="Measured task overlap after two-job authorization")
    ax.legend(handles=[policy_line, *[Patch(facecolor=colors[kind], label=kind)
                                     for kind in sorted({row["kind"] for row in jobs})],
                       Patch(facecolor="#dddddd", hatch="//", label="Nonzero tool exit")])
    fig.savefig(ROOT / "experiments/figs/parallel_timeline.png", dpi=180)
    plt.close(fig)
