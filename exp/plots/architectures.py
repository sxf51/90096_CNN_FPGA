#!/usr/bin/env python3
"""Regenerate all architecture plots from derived CSV evidence only."""
import csv
import math
import textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from adjustText import adjust_text
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIGS = ROOT / "experiments/figs"
FIGS.mkdir(exist_ok=True)
COLORS = {"S":"#4e79a7","G":"#59a14f","P":"#e15759","W":"#b07aa1","C":"#f28e2b","F":"#76b7b2","E":"#888888"}
PRECISION_LABELS = {"w10a10acc23": "w10 a10",
                    "w10_8_10a10acc23_21_23": "w10/8/10 a10"}
np.random.seed(1011)


def read(name):
    return list(csv.DictReader((ROOT / "experiments" / name).open(newline="")))


def num(row,key):
    try:
        value = float(row[key])
        return value if math.isfinite(value) else None
    except (KeyError,ValueError,TypeError):
        return None


def save(fig,name):
    fig.savefig(FIGS / name,dpi=180)
    plt.close(fig)


rows = read("architecture_data.csv")
frames = [row for row in rows if row["scope"] == "frame" and not row["operation"] and
          num(row,"latency_ms_est") is not None and num(row,"DSP") is not None and
          row["status"] in {"pass","provisional","infeasible"} and
          (row["series"] or row["id"] in {"E043","E057","E060"})]
fig,ax = plt.subplots(figsize=(16,11),constrained_layout=True)
labels,grouped = [],{}
for row in frames:
    grouped.setdefault((num(row,"DSP"),num(row,"latency_ms_est"),row["series"] or "E",
                        row["status"] == "infeasible",row["T_target"],
                        row["precision_w_a_acc"]),[]).append(row)
for (dsp,latency,series,bad,t,precision),points in grouped.items():
    ax.scatter(dsp,latency,color=COLORS[series],marker="x" if bad else "o",s=42)
    ids = textwrap.fill(", ".join(p["id"] for p in points),width=23)
    labels.append(ax.text(dsp,latency,ids+f" T={t}\n"+
                          PRECISION_LABELS.get(precision,precision),fontsize=8))
ax.set(title="SRCNN architecture exploration: HLS estimates",xlabel="DSP48E2 (count)",ylabel="Estimated frame latency (ms)")
ax.set_yscale("log")
ax.axvline(1248,color="#444444",linestyle="--",linewidth=1)
ax.grid(alpha=.2)
legend = ax.legend(handles=[Line2D([0],[0],marker="o",color=color,linestyle="",label=series+" series") for series,color in COLORS.items()]+
                   [Line2D([0],[0],marker="x",color="#444444",linestyle="",label="Resource infeasible")],fontsize=8)
fig.canvas.draw()
fig.set_layout_engine("none")
adjust_text(labels,objects=[legend],ax=ax,iter_lim=1500,expand=(1.3,1.5),
            force_text=(.3,.5),force_pull=(.004,.004),
            arrowprops={"arrowstyle":"-","color":"#888888","lw":.5})
save(fig,"architecture_pareto.png")

compositions = read("dsp_composition.csv")
representatives = {"G01","G02","G03","S05","P10","W08","W14","W15","W16","C04","C05","C06","C07","C10","C11","F09","F10","F11","F12","F13","F14","F15","E043"}
ranked = sorted((row for row in rows if row["eligible_provisional"] == "True" and
                 num(row,"latency_ms_est") is not None),key=lambda row:num(row,"latency_ms_est"))
representatives.update(row["id"] for row in ranked[:3])
parts = [row for row in compositions if row["id"] in representatives]
fig,ax = plt.subplots(figsize=(max(10,len(parts)*.8),6),constrained_layout=True)
x,bottom = np.arange(len(parts)),np.zeros(len(parts))
for key,color in (("Conv1_DSP","#4e79a7"),("Conv2_DSP","#f28e2b"),("Conv3_DSP","#59a14f"),("other_DSP","#888888")):
    values = np.array([num(row,key) for row in parts])
    ax.bar(x,values,bottom=bottom,label=key.replace("_DSP",""),color=color)
    bottom += values
ax.set_xticks(x,[row["id"] for row in parts],rotation=45,ha="right")
ax.axhline(1248,color="#555555",linestyle="--",label="K26 DSP capacity")
ax.set(title="Measured DSP composition by network layer",xlabel="Representative experiment ID",ylabel="DSP48E2 (count)")
ax.legend()
ax.grid(axis="y",alpha=.2)
save(fig,"architecture_dsp_layers.png")

estimates = read("estimate_actual.csv")
for metric,unit,name in (("DSP","DSP48E2 (count)","estimate_actual_dsp.png"),
                         ("latency_cycles","Frame/kernel latency (cycles)","estimate_actual_cycles.png")):
    points = [row for row in estimates if row["metric"] == metric and num(row,"estimate") is not None and
              num(row,"actual") is not None and num(row,"estimate") >= 0 and num(row,"actual") >= 0]
    fig,axes = plt.subplots(1,2,figsize=(17,8),width_ratios=(2,1),constrained_layout=True)
    annotations = []
    for ax,is_pe in zip(axes,(False,True)):
        subset = [row for row in points if (row["scope"] == "PE") == is_pe]
        texts, grouped = [], {}
        for row in subset:
            paper,actual = num(row,"estimate"),num(row,"actual")
            ax.scatter(paper,actual,color=COLORS[row["series"]],marker="s" if is_pe else "^" if row["scope"] == "layer" else "o",s=35)
            grouped.setdefault((paper,actual,row["series"],row["scope"]),[]).append(row["id"])
        for (paper,actual,_,_),ids in grouped.items():
            texts.append(ax.text(paper,actual,",".join(ids),fontsize=7))
        if subset:
            high = max(max(num(r,"estimate"),num(r,"actual")) for r in subset)*1.4
            includes_zero = any(num(r,"estimate") == 0 or num(r,"actual") == 0 for r in subset)
            positives = [num(r,key) for r in subset for key in ("estimate","actual") if num(r,key) > 0]
            low = min(positives)*.7 if positives else 1
            high = max(high,low*2)
            axis = np.geomspace(low,high,100)
            if includes_zero:
                axis = np.concatenate(([0],axis))
            ax.plot(axis,axis,color="#555555",label="Estimate = actual")
            ax.fill_between(axis,axis*.8,axis*1.2,color="#cccccc",alpha=.3,label="20% band")
            ax.set_xscale("symlog" if includes_zero else "log",**({"linthresh":1} if includes_zero else {}))
            ax.set_yscale("symlog" if includes_zero else "log",**({"linthresh":1} if includes_zero else {}))
        ax.set(title="Processing elements" if is_pe else "Full frames and layers",
               xlabel="Paper estimate: "+unit,ylabel="Parsed actual: "+unit)
        ax.grid(alpha=.2)
        annotations.append((ax,texts))
    handles,_ = axes[0].get_legend_handles_labels()
    handles += [Line2D([0],[0],marker="o",color=COLORS[series],linestyle="",label=series+" series")
                for series in sorted({row["series"] for row in points})]
    handles += [Line2D([0],[0],marker=marker,color="#444444",linestyle="",label=label)
                for marker,label in (("s","PE"),("^","Layer"),("o","Frame"))]
    fig.legend(handles=handles,fontsize=8,ncol=6,loc="outside lower center")
    fig.suptitle(f"Paper estimates vs measured {metric}")
    fig.canvas.draw()
    fig.set_layout_engine("none")
    for ax,texts in annotations:
        adjust_text(texts,ax=ax,iter_lim=1000,expand=(1.2,1.3),force_text=(.3,.5),
                    arrowprops={"arrowstyle":"-","color":"#888888","lw":.4})
    save(fig,name)

g = [row for row in rows if row["id"] in {"G01","G02","G03"}]
fig,axes = plt.subplots(1,3,figsize=(13,5),constrained_layout=True)
for ax,metric in zip(axes,("BRAM18K","LUT","FF")):
    x = np.arange(len(g))
    values = [num(row,metric) or 0 for row in g]
    ax.bar(x,values,color=["#4e79a7","#f28e2b","#59a14f"][:len(g)])
    ax.set_xticks(x,[row["id"]+"\n"+label for row,label in zip(g,("Gather","Scatter + pad","Scatter + edge"))],fontsize=8)
    ax.set(title=metric,xlabel="T32/10ns experiment",ylabel=metric+" (count)")
    for index,value in enumerate(values):
        ax.annotate(f"{value:g}",(index,value),xytext=(0,3),textcoords="offset points",ha="center",fontsize=8)
    ax.grid(axis="y",alpha=.2)
fig.suptitle("Conv3 organization: full-network HLS resources, exact w10a10")
fig.legend(handles=[Line2D([0],[0],color=color,linewidth=8,label=label) for color,label in
                    (("#4e79a7","G01 gather"),("#f28e2b","G02 explicit-pad scatter"),("#59a14f","G03 merged-edge scatter"))],loc="outside lower center",ncol=3)
save(fig,"conv3_resources.png")
kernel = read("conv3_comparison.csv")
fig,axes = plt.subplots(1,3,figsize=(13,5),constrained_layout=True)
for ax,metric in zip(axes,("BRAM18K","LUT","FF")):
    x = np.arange(len(kernel))
    core = np.array([num(row,"kernel_"+metric) or 0 for row in kernel])
    padding = np.array([num(row,"padding_"+metric) or 0 for row in kernel])
    ax.bar(x,core,label="Conv3 core",color="#4e79a7")
    ax.bar(x,padding,bottom=core,label="External pad stage",color="#f28e2b")
    ax.set_xticks(x,[row["id"]+"\n"+row["variant"] for row in kernel],fontsize=8)
    ax.set(title=metric,xlabel="T32/10ns experiment",ylabel=metric+" (count)")
    ax.grid(axis="y",alpha=.2)
axes[0].legend()
fig.suptitle("Conv3 core and explicit padding resources (FIFO costs separate)")
save(fig,"conv3_core_resources.png")
print("Wrote architecture figures to",FIGS)
