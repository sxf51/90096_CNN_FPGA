#!/usr/bin/env python3
"""Plot measured full INT16 product-pair costs from archived CSV only."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[2]
source = ROOT / "experiments/int16_packing_comparison.csv"
with source.open(newline="") as handle:
    rows = [row for row in csv.DictReader(handle)
            if row["DSP"] and row["LUT"] and row["FF"]]
if not rows:
    print("No measured INT16 pair rows available")
else:
    labels = {"0":"Direct DSP", "1":"Byte limbs", "2":"Overlap + fabric", "3":"Direct mixed"}
    colors = {"0":"#4e79a7", "1":"#b07aa1", "2":"#e15759", "3":"#59a14f"}
    fig,axes = plt.subplots(1,3,figsize=(14,5),constrained_layout=True)
    for ax,metric in zip(axes,("DSP","LUT","FF")):
        values = [float(row[metric]) for row in rows]
        ax.bar(range(len(rows)),values,color=[colors[row["mode"]] for row in rows])
        ax.set_xticks(range(len(rows)),[row["id"] for row in rows])
        ax.set(title=metric,xlabel="Exact INT16 pair experiment",ylabel=metric+" (count)")
        ax.margins(y=.18)
        for index,value in enumerate(values):
            ax.annotate(f"{value:g}",(index,value),xytext=(0,4),textcoords="offset points",
                        ha="center",fontsize=9)
        ax.grid(axis="y",alpha=.2)
    fig.suptitle("Complete signed16 x signed16 product pairs: HLS resource costs")
    fig.legend(handles=[Line2D([0],[0],color=colors[row["mode"]],linewidth=8,
                               label=row["id"]+" "+labels[row["mode"]]) for row in rows],
               loc="outside lower center",ncol=4,fontsize=9)
    target = ROOT / "experiments/figs/int16_packing_resources.png"
    fig.savefig(target,dpi=180)
    plt.close(fig)
    print("Wrote",target)
