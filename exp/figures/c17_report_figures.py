#!/usr/bin/env python3
"""Generate the C17 report figures (SVG) from archived experiment data.

Usage:
    python3 exp/figures/c17_report_figures.py [--out docs/figures/C17]

Data sources (all under experiments/):
    C17_t4_fifo/reports/*_csynth.rpt        HLS loop depth, per-module estimates
    C20_ws_cosim_C17/profiling/*.csv        RTL FIFO / process counters (two frames)
    C14_ws_cosim_C13/profiling/channels.csv depth-2 window FIFO control
    C22_ws_impl_C17/physical_hierarchy_routed.csv  routed per-module resources
Code-derived constants come from plain/C17_srcnn_plain.cpp and are cited inline.

No third-party dependencies; the SVG is written by hand.
"""
from __future__ import annotations

import argparse
import csv
import html
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXP = os.path.join(ROOT, "experiments")

FONT = "Helvetica Neue, Helvetica, Arial, sans-serif"
MONO = "SF Mono, Menlo, Consolas, monospace"

C_BLUE = "#2f6db3"
C_ORANGE = "#d9822b"
C_GREEN = "#3a9d5d"
C_RED = "#c84b4b"
C_GREY = "#8a8f98"
C_LIGHT = "#eef1f5"
C_TEXT = "#1f2328"
C_SUB = "#5b6470"
LAYER_COLOR = {"conv1": C_BLUE, "conv2": C_ORANGE, "conv3": C_GREEN}
NO_TITLE = False          # set by --no-title: omit the figure title and crop the space it used
TITLE_BAND = 62           # pixels occupied by title + subtitle


# --------------------------------------------------------------------------
# tiny SVG helper
# --------------------------------------------------------------------------
class Svg:
    def __init__(self, width: int, height: int, title: str):
        self.w, self.h = width, height
        self.parts: list[str] = []
        self.parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="{FONT}" font-size="13" fill="{C_TEXT}">'
        )
        self.parts.append(f"<title>{html.escape(title)}</title>")
        self.parts.append(
            "<defs>"
            '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{C_SUB}"/></marker>'
            '<pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="6" stroke="{C_RED}" stroke-width="2" opacity="0.55"/></pattern>'
            "</defs>"
        )
        self.parts.append(f'<rect width="{width}" height="{height}" fill="white"/>')

    def text(self, x, y, s, size=13, anchor="start", weight="normal", color=C_TEXT, mono=False, rotate=None, opacity=1.0):
        fam = MONO if mono else FONT
        tr = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" '
            f'fill="{color}" font-family="{fam}" opacity="{opacity}"{tr}>{html.escape(str(s))}</text>'
        )

    def rect(self, x, y, w, h, fill=C_LIGHT, stroke=C_SUB, sw=1, rx=3, opacity=1.0, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}" opacity="{opacity}"{d}/>'
        )

    def line(self, x1, y1, x2, y2, stroke=C_SUB, sw=1, dash=None, arrow=False, opacity=1.0):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        a = ' marker-end="url(#arrow)"' if arrow else ""
        self.parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
            f'stroke-width="{sw}" opacity="{opacity}"{d}{a}/>'
        )

    def path(self, d, stroke=C_SUB, sw=1.2, fill="none", arrow=False, dash=None):
        a = ' marker-end="url(#arrow)"' if arrow else ""
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{sw}" fill="{fill}"{a}{ds}/>')

    def title(self, s, sub=None):
        if NO_TITLE:
            return
        self.text(24, 30, s, size=18, weight="bold")
        if sub:
            self.text(24, 50, sub, size=12, color=C_SUB)

    def footer(self, s):
        self.text(24, self.h - 12, s, size=10.5, color=C_SUB)

    def save(self, path):
        if NO_TITLE:
            h = self.h - TITLE_BAND
            self.parts[0] = (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h}" '
                f'viewBox="0 {TITLE_BAND} {self.w} {h}" font-family="{FONT}" font-size="13" fill="{C_TEXT}">'
            )
        self.parts.append("</svg>")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.parts))


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(n):
    return f"{int(round(n)):,}"


# --------------------------------------------------------------------------
# Figure 1: fold timing of the three engines
# --------------------------------------------------------------------------
def fig1_fold_timing(out):
    # From plain/C17_srcnn_plain.cpp (continuous_*_fold loops) and
    # C17_t4_fifo/reports/*_fold_csynth.rpt (iteration latency = pipeline depth).
    engines = [
        dict(key="conv1", name="conv1 - Winograd F(2x2, 3x3)", loop="continuous_wino_fold",
             steps=16, read="read 1 transformed window (9 x 16 x 12 bit)", unit="output channel oc", per_step=4,
             dsp="4 lanes x 9 sub-blocks x 16 taps = 576 DSP (12 b x 14 b)",
             write="write 1 tile: 2x2 pixels x 64 channels", iters="128 x 128 x 16 = 262,144", depth=8,
             shift="tile is a shift register: shifts left by 4 channels per cycle, channels 0..63 in order after 16 cycles"),
        dict(key="conv2", name="conv2 - 1x1, packed weights", loop="continuous_c2_fold",
             steps=4, read="read 1 pixel (64 channels x 10 bit)", unit="output channel oc", per_step=8,
             dsp="4 lanes x 64 ic = 256 DSP, each DSP computes 2 output channels (27 b x 10 b)",
             write="write 1 pixel: 32 channels", iters="255 x 255 x 4 = 260,100", depth=11,
             shift="result is a shift register: shifts left by 8 channels per cycle, channels 0..31 in order after 4 cycles"),
        dict(key="conv3", name="conv3 - 5x5, accumulated over 4 cycles", loop="continuous_c3_fold",
             steps=4, read="read 1 window (5x5 x 32 channels, two halves of 400 x 10 bit)", unit="input channel ic", per_step=8,
             dsp="8 ic x 25 taps = 200 DSP (10 b x 10 b), then a 256-input, 8-level adder tree",
             write="write 1 pixel: 1 channel, no ReLU", iters="255 x 255 x 4 = 260,100", depth=13,
             shift="sum register: starts from the bias at step 0, then adds this cycle's 200 products"),
    ]
    W, H = 1180, 795
    s = Svg(W, H, "C17: fold timing of the three convolution engines")
    s.title("Figure 1 - Fold timing of the three convolution engines (T = 4)", "One PIPELINE II=1 loop per engine; DSP 576 + 256 + 200 = 1,032")
    x0, panel_h, top = 24, 235, 75
    for i, e in enumerate(engines):
        y = top + i * panel_h
        col = LAYER_COLOR[e["key"]]
        s.rect(x0, y, W - 2 * x0, panel_h - 18, fill="white", stroke="#d7dbe0", rx=6)
        s.text(x0 + 14, y + 24, e["name"], size=15, weight="bold", color=col)
        s.text(x0 + 14, y + 42, f"loop {e['loop']}", size=11, color=C_SUB, mono=True)
        tx, ty, tw, th = x0 + 150, y + 72, 760, 54
        steps = e["steps"]
        bw = tw / steps
        s.text(tx - 8, ty + th / 2 + 4, "step", size=11, color=C_SUB, anchor="end")
        for k in range(steps):
            bx = tx + k * bw
            s.rect(bx, ty, bw - 2, th, fill=col, stroke="none", opacity=0.14 + 0.5 * (k + 1) / steps, rx=2)
            s.text(bx + bw / 2 - 1, ty + 16, str(k), size=11, anchor="middle", color=C_TEXT)
            lo, hi = k * e["per_step"], (k + 1) * e["per_step"] - 1
            label = f"{lo}-{hi}" if (steps <= 8 or k % 2 == 0) else ""
            s.text(bx + bw / 2 - 1, ty + 40, label, size=10, anchor="middle", color=C_TEXT, mono=True)
        s.text(tx + tw + 8, ty + th / 2 + 4, e["unit"], size=10.5, color=C_SUB)
        s.line(tx + bw / 2, ty - 26, tx + bw / 2, ty - 2, stroke=C_BLUE, sw=1.5, arrow=True)
        s.text(tx + bw / 2 + 8, ty - 20, f"step 0: {e['read']}", size=11, color=C_BLUE)
        s.line(tx + tw - bw / 2, ty + th + 2, tx + tw - bw / 2, ty + th + 26, stroke=C_GREEN, sw=1.5, arrow=True)
        s.text(tx + tw - bw / 2 - 8, ty + th + 22, f"step {steps - 1}: {e['write']}", size=11, anchor="end", color=C_GREEN)
        lx = x0 + 14
        vx = x0 + 130
        s.text(lx, y + 165, "Per cycle:", size=11.5, weight="bold")
        s.text(vx, y + 165, e["dsp"], size=11.5)
        s.text(lx, y + 185, "Registers:", size=11.5, weight="bold")
        s.text(vx, y + 185, e["shift"], size=11.5)
        s.text(lx, y + 207, "Iterations:", size=11.5, weight="bold")
        s.text(vx, y + 207, f"{e['iters']}, II = 1", size=11.5, mono=True)
        s.text(x0 + 470, y + 207, "Pipeline depth:", size=11.5, weight="bold")
        s.text(x0 + 580, y + 207, f"{e['depth']} cycles (HLS iteration latency)", size=11.5, mono=True)
    s.footer("plain/C17_srcnn_plain.cpp; experiments/C17_t4_fifo/reports/*_fold_csynth.rpt")
    s.save(os.path.join(out, "fig1_fold_timing.svg"))


# --------------------------------------------------------------------------
# Figure 2: workload / DSP / cycle balance
# --------------------------------------------------------------------------
def fig2_balance(out):
    conv1_direct = 255 * 255 * 81 * 64          # direct 9x9, 64 output channels
    conv1_wino = 128 * 128 * 9 * 16 * 64        # 16384 windows x 9 sub-blocks x 16 taps x 64 oc
    conv2 = 255 * 255 * 64 * 32
    conv3 = 255 * 255 * 25 * 32
    # Measured fold-loop latency per frame from C20 C/RTL co-simulation
    # (experiments/C20_ws_cosim_C17/profiling/processes.csv, process_latency_avg_cycles of the
    # continuous_*_fold pipeline modules).
    measured = {"conv1": 262507, "conv2": 260877, "conv3": 261885}
    layers = [
        ("conv1", conv1_wino, 576, 262144, 576),
        ("conv2", conv2, 256, 260100, 512),   # packing: 2 products per DSP per cycle
        ("conv3", conv3, 200, 260100, 200),
    ]
    W, H = 1100, 560
    s = Svg(W, H, "C17: workload, DSP and cycle balance across layers")
    s.title("Figure 2 - Multiplications per frame, DSP allocation and measured fold-loop cycles per layer",
            "design cycles = multiplications / multiplications per cycle; measured cycles from C20 C/RTL co-simulation")
    panels = [
        ("Multiplications per frame (millions)", [(k, m / 1e6) for k, m, *_ in layers], "{:.1f} M"),
        ("DSP count", [(k, d) for k, _, d, *_ in layers], "{:.0f}"),
        ("Fold-loop cycles per frame, C20 measured (thousands)", [(k, measured[k] / 1e3) for k, *_ in layers], "{:.1f} k"),
    ]
    px0, py0, pw, ph = 40, 90, 320, 300
    for pi, (ptitle, vals, f) in enumerate(panels):
        x = px0 + pi * (pw + 30)
        s.rect(x, py0, pw, ph, fill="white", stroke="#d7dbe0", rx=6)
        s.text(x + 12, py0 + 22, ptitle, size=12.5 if pi == 2 else 13, weight="bold")
        vmax = max(v for _, v in vals)
        if pi == 0:
            vmax = max(vmax, conv1_direct / 1e6)
        bw, gap = 62, 34
        base = py0 + ph - 40
        scale = (ph - 110) / vmax
        for bi, (k, v) in enumerate(vals):
            bx = x + 40 + bi * (bw + gap)
            bh = v * scale
            ghost = pi == 0 and k == "conv1"
            if ghost:
                gh = conv1_direct / 1e6 * scale
                s.rect(bx, base - gh, bw, gh, fill="none", stroke=LAYER_COLOR[k], dash="4,3", rx=2)
                s.text(bx + bw / 2, base - gh - 6, f"direct 9x9: {conv1_direct/1e6:.0f} M", size=10, anchor="middle", color=C_SUB)
            s.rect(bx, base - bh, bw, bh, fill=LAYER_COLOR[k], stroke="none", rx=2)
            s.text(bx + bw / 2, base - bh + 16 if ghost else base - bh - 6, f.format(v), size=11.5, anchor="middle",
                   weight="bold", color="white" if ghost else C_TEXT)
            s.text(bx + bw / 2, base + 16, k, size=12, anchor="middle")
        s.line(x + 30, base, x + pw - 20, base, stroke=C_SUB)
        if pi == 2:
            # design bound 4 x 255 x 255 as a reference line
            yb = base - 260100 / 1e3 * scale
            s.line(x + 30, yb, x + pw - 20, yb, stroke=C_RED, sw=1.2, dash="5,3")
            s.text(x + pw - 20, yb - 5, "design bound 4 x 255 x 255 = 260.1 k", size=10, anchor="end", color=C_RED)
        if pi == 1:
            s.text(x + 12, py0 + ph - 8, "conv2's 256 DSPs compute 512 products per cycle (packing)", size=10.5, color=C_SUB)
        if pi == 0:
            s.text(x + 12, py0 + ph - 8, "Winograd cuts conv1 multiplications by 2.23x", size=10.5, color=C_SUB)
    ty = py0 + ph + 30
    s.text(40, ty, "Check: design cycles = multiplications / multiplications per cycle; measured = C20 fold-loop latency", size=12.5, weight="bold")
    cols = ["layer", "mults / frame", "mults / cycle", "design cycles", "C20 measured", "excess", "DSP share"]
    xs = [40, 110, 290, 420, 560, 690, 790]
    for cx, c in zip(xs, cols):
        s.text(cx, ty + 22, c, size=11, color=C_SUB)
    for ri, (k, m, d, c, per) in enumerate(layers):
        yy = ty + 42 + ri * 18
        mv = measured[k]
        row = [k, fmt(m), f"{per}", fmt(m / per), fmt(mv), f"+{100*(mv/c-1):.2f}%", f"{d}/1032 = {100*d/1032:.0f}%"]
        for cx, v in zip(xs, row):
            s.text(cx, yy, v, size=11, mono=True, color=LAYER_COLOR[k] if cx == 40 else C_TEXT)
    s.footer("plain/C17_srcnn_plain.cpp; experiments/C20_ws_cosim_C17/profiling/processes.csv (continuous_*_fold latency)")
    s.save(os.path.join(out, "fig2_balance.svg"))


# --------------------------------------------------------------------------
# Figure 3: dataflow graph with FIFO depth/width and measured backpressure
# --------------------------------------------------------------------------
def fig3_dataflow(out):
    ch = {r["name"]: r for r in read_csv(os.path.join(EXP, "C20_ws_cosim_C17", "profiling", "channels.csv"))}
    pr = {r["name"]: r for r in read_csv(os.path.join(EXP, "C20_ws_cosim_C17", "profiling", "processes.csv")) if r["kind"] == "process"}
    c14 = {r["name"]: r for r in read_csv(os.path.join(EXP, "C14_ws_cosim_C13", "profiling", "channels.csv"))}

    chain = [
        ("read_input", "read_input_U0", "io"),
        ("online_pad1", "online_pad_ap_int_10_4_U0", "pad"),
        ("wino_windows", "wino_windows_U0", "win"),
        ("wino_engine\n576 DSP", "wino_engine_U0", "mac"),
        ("distribute_tiles", "distribute_tiles_U0", "misc"),
        ("reorder_rows", "reorder_rows_U0", "misc"),
        ("conv2_stream\n256 DSP", "conv2_stream_U0", "mac"),
        ("online_pad3", "online_pad_pixel2_2_U0", "pad"),
        ("windows3", "windows3_U0", "win"),
        ("engine3\n200 DSP", "engine3_U0", "mac"),
        ("write_output", "write_output_U0", "io"),
    ]
    # depth/width from #pragma HLS STREAM and struct sizes in plain/C17_srcnn_plain.cpp
    fifos = [
        ("raw_U", "raw", 512, 10),
        ("padded1_U", "padded1", 16, 10),
        ("windows_U", "windows", 32, 9 * 16 * 12),
        ("tiles_U", "tiles", 2, 4 * 64 * 10),
        ("top_U/bottom_U", "top / bottom", 512, 64 * 10),
        ("features_U", "features", 4, 64 * 10),
        ("features2_U", "features2", 4, 32 * 10),
        ("padded3_U", "padded3", 16, 32 * 10),
        ("windows0_U/windows1_U", "windows0 / windows1", 2, 400 * 10),
        ("result_U", "result", 16, 10),
    ]
    W, H = 1300, 740
    s = Svg(W, H, "C17: dataflow and FIFO backpressure")
    s.title("Figure 3 - dataflow_region: processes, FIFOs (depth x width) and measured blocking (C20, two RTL frames)",
            "W / R = share of cycles the FIFO blocked a write / a read.  stall = share of cycles the process waited.")
    nw, nh = 122, 54
    gap = 90
    rows = [chain[:6], chain[6:]]
    pos = {}
    y_rows = [125, 335]
    for ri, row in enumerate(rows):
        for ci, node in enumerate(row):
            pos[node[1]] = (50 + ci * (nw + gap), y_rows[ri])

    def stall_pct(name):
        return float(pr[name]["stall_pct"]) if name in pr else None

    kind_fill = {"io": "#f3f4f6", "pad": "#f3f4f6", "win": "#eaf1fb", "mac": "#fff1e3", "misc": "#f3f4f6"}
    for label, name, kind in chain:
        x, y = pos[name]
        s.rect(x, y, nw, nh, fill=kind_fill[kind], stroke=C_ORANGE if kind == "mac" else "#c9ced6", sw=2 if kind == "mac" else 1, rx=6)
        lines = label.split("\n")
        s.text(x + nw / 2, y + 19, lines[0], size=11.5, anchor="middle", weight="bold", mono=True)
        if len(lines) > 1:
            s.text(x + nw / 2, y + 33, lines[1], size=10.5, anchor="middle", color=C_ORANGE)
        sp = stall_pct(name)
        if sp is not None:
            s.text(x + nw / 2, y + nh - 6, f"stall {sp:.1f}%", size=10, anchor="middle",
                   color=C_RED if sp > 50 else C_GREEN, weight="bold" if sp < 10 else "normal")

    def block_color(p):
        if p >= 50:
            return C_RED
        if p >= 5:
            return C_ORANGE
        return C_GREEN

    for i, (cname, label, depth, width) in enumerate(fifos):
        a, b = chain[i][1], chain[i + 1][1]
        (ax, ay), (bx, by) = pos[a], pos[b]
        names = cname.split("/")
        wb = max(float(ch[n]["write_block_pct"]) for n in names)
        rb = max(float(ch[n]["read_block_pct"]) for n in names)
        col = block_color(max(wb, rb))
        if ay == by:
            x1, x2 = ax + nw, bx
            s.line(x1, ay + nh / 2, x2 - 2, by + nh / 2, stroke=col, sw=2.5, arrow=True)
            mx = (x1 + x2) / 2
            s.text(mx, ay + nh / 2 - 19, label, size=10, anchor="middle", mono=True, weight="bold")
            s.text(mx, ay + nh / 2 - 7, f"{depth} x {width} b", size=9.5, anchor="middle", color=C_SUB)
            s.text(mx, ay + nh / 2 + 17, f"W {wb:.0f}%  R {rb:.0f}%", size=10, anchor="middle", color=col, weight="bold")
        else:
            x1, y1 = ax + nw / 2, ay + nh
            x2, y2 = bx + nw / 2, by
            midy = (y1 + y2) / 2
            s.path(f"M {x1} {y1} L {x1} {midy} L {x2} {midy} L {x2} {y2 - 2}", stroke=col, sw=2.5, arrow=True)
            s.text(min(x1, x2) + 60, midy - 8, f"{label}   {depth} x {width} b   W {wb:.0f}%  R {rb:.0f}%", size=10.5, anchor="start", mono=True, weight="bold")

    # parameter side-stream (dashed), routed as a bus below the second row
    px, py = 50, 530
    s.rect(px, py, nw, nh, fill="#f3f4f6", stroke="#c9ced6", rx=6)
    s.text(px + nw / 2, py + 19, "read_params", size=11.5, anchor="middle", weight="bold", mono=True)
    s.text(px + nw / 2, py + 33, "AXI, transform, 3 outputs", size=9.5, anchor="middle", color=C_SUB)
    s.text(px + nw / 2, py + nh - 6, f"stall {stall_pct('read_params_U0'):.1f}%", size=10, anchor="middle", color=C_GREEN, weight="bold")
    busy = py + nh / 2
    right_x = pos["write_output_U0"][0] + nw + 24   # free column right of the second row
    s.line(px + nw, busy, right_x, busy, stroke=C_GREY, sw=1.2, dash="5,4")

    def param_label(x, y_bottom, text):
        s.text(x - 5, y_bottom - 40, text, size=9.5, color=C_SUB, mono=True, rotate=-90)

    # params2 -> conv2_stream and params3 -> engine3 are straight up from the bus
    for pname, target, depth, width in (("params2_U", "conv2_stream_U0", 16, 10), ("params3_U", "engine3_U0", 16, 10)):
        tx_, ty_ = pos[target]
        rb = float(ch[pname]["read_block_pct"])
        cx = tx_ + nw / 2
        s.line(cx, busy, cx, ty_ + nh + 2, stroke=C_GREY, sw=1.2, dash="5,4", arrow=True)
        param_label(cx, busy, f"{pname[:-2]} {depth}x{width}b R {rb:.1f}%")
    # params1 -> wino_engine goes around the right end, between the two rows, then up
    tx_, ty_ = pos["wino_engine_U0"]
    rb = float(ch["params1_U"]["read_block_pct"])
    cx = tx_ + nw / 2
    mid_y = pos["conv2_stream_U0"][1] - 32
    s.path(f"M {right_x} {busy} L {right_x} {mid_y} L {cx} {mid_y} L {cx} {ty_ + nh + 2}", stroke=C_GREY, sw=1.2, dash="5,4", arrow=True)
    param_label(right_x, busy, f"params1 4x{16*14}b R {rb:.1f}%")

    # colour key (one line)
    kx, ky = 300, 590
    for i, (c, t) in enumerate(((C_RED, ">= 50%"), (C_ORANGE, "5-50%"), (C_GREEN, "< 5%"))):
        s.line(kx + i * 110, ky - 4, kx + i * 110 + 24, ky - 4, stroke=c, sw=3)
        s.text(kx + i * 110 + 30, ky, t, size=11, color=C_SUB)

    # the one change: windows FIFO depth 2 -> 32
    c14_rb = int(c14["windows_U"]["read_block_cycles"])
    c17_rb = int(ch["windows_U"]["read_block_cycles"])
    ix, iy, iw, ih = 300, 608, 950, 92
    s.rect(ix, iy, iw, ih, fill="#fbfbfc", stroke="#d7dbe0", rx=6)
    s.text(ix + 14, iy + 22, "windows FIFO depth 2 -> 32  (C13/C14 -> C17/C20)", size=12.5, weight="bold")
    cols = ["", "depth", "read-block cycles", "wino fold cycles", "frame cycles", "frame @ 5 ns"]
    xs = [ix + 14, ix + 150, ix + 260, ix + 450, ix + 640, ix + 800]
    for cx, c in zip(xs, cols):
        s.text(cx, iy + 44, c, size=10.5, color=C_SUB)
    rows_ = [("depth 2", "2", fmt(c14_rb), "291,234", "300,632", "1.503 ms"),
             ("depth 32", "32", fmt(c17_rb), "262,507", "273,023", "1.365 ms")]
    for ri, row in enumerate(rows_):
        for cx, v in zip(xs, row):
            s.text(cx, iy + 64 + ri * 18, v, size=11.5, mono=True, weight="bold" if ri == 1 else "normal")
    s.footer("experiments/C20_ws_cosim_C17/profiling, C14_ws_cosim_C13/profiling, plain/C17_srcnn_plain.cpp")
    s.save(os.path.join(out, "fig3_dataflow_backpressure.svg"))


# --------------------------------------------------------------------------
# Figure 4: per-process activity within one frame (Gantt-like)
# --------------------------------------------------------------------------
def fig4_gantt(out):
    pr = {r["name"]: r for r in read_csv(os.path.join(EXP, "C20_ws_cosim_C17", "profiling", "processes.csv")) if r["kind"] == "process"}
    order = [
        ("read_input", "read_input_U0", "io"),
        ("read_params", "read_params_U0", "io"),
        ("online_pad1", "online_pad_ap_int_10_4_U0", "pad"),
        ("wino_windows", "wino_windows_U0", "win"),
        ("wino_engine", "wino_engine_U0", "mac"),
        ("distribute_tiles", "distribute_tiles_U0", "misc"),
        ("reorder_rows", "reorder_rows_U0", "misc"),
        ("conv2_stream", "conv2_stream_U0", "mac"),
        ("online_pad3", "online_pad_pixel2_2_U0", "pad"),
        ("windows3", "windows3_U0", "win"),
        ("engine3", "engine3_U0", "mac"),
        ("write_output", "write_output_U0", "io"),
    ]
    rtl_lat, hls_lat, c14_lat = 273023, 263090, 300632
    W, H = 1200, 580
    s = Svg(W, H, "C17: per-process activity within one frame")
    s.title("Figure 4 - Activity of each process within one 273,052-cycle frame (C20 RTL co-simulation, df_process_monitor)",
            "bar = process latency from frame start; hatched = share of cycles waiting on a FIFO")
    gx, gy, gw, rowh = 190, 95, 780, 32
    xmax = 310000
    sc = gw / xmax
    for t in range(0, xmax + 1, 50000):
        x = gx + t * sc
        s.line(x, gy - 6, x, gy + rowh * len(order), stroke="#e3e6ea")
        s.text(x, gy - 10, f"{t//1000}k", size=10, anchor="middle", color=C_SUB)
    s.text(gx + gw, gy - 26, "cycles", size=10.5, anchor="end", color=C_SUB)
    col_lat = gx + gw + 14
    col_wait = gx + gw + 90
    s.text(col_lat, gy - 10, "latency", size=10, color=C_SUB)
    s.text(col_wait, gy - 10, "waiting", size=10, color=C_SUB)
    kind_col = {"io": C_GREY, "pad": "#9db7d9", "win": "#6f97c9", "mac": C_ORANGE, "misc": "#b9bec6"}
    for i, (label, name, kind) in enumerate(order):
        r = pr[name]
        lat = float(r["process_latency_max_cycles"])
        stall_f = (float(r["read_stall_cycles"]) + float(r["write_stall_cycles"])) / 2.0  # counters span two frames
        y = gy + i * rowh + 5
        s.text(gx - 10, y + 15, label, size=11.5, anchor="end", mono=True, weight="bold" if kind == "mac" else "normal")
        s.rect(gx, y, lat * sc, rowh - 10, fill=kind_col[kind], stroke="none", rx=2)
        if stall_f > 0:
            s.rect(gx, y, min(stall_f, lat) * sc, rowh - 10, fill="url(#hatch)", stroke="none", rx=2)
        s.text(col_lat, y + 15, fmt(lat), size=10.5, mono=True)
        s.text(col_wait, y + 15, f"{100*stall_f/lat:.0f}%", size=10.5, color=C_RED if stall_f / lat > 0.5 else C_SUB, mono=True)
    ybot = gy + rowh * len(order) + 4
    refs = ((hls_lat, f"HLS estimate {fmt(hls_lat)}", C_BLUE, "5,4", 0),
            (rtl_lat, f"RTL measured {fmt(rtl_lat)}", C_GREEN, None, 1),
            (c14_lat, f"C14 (FIFO depth 2) {fmt(c14_lat)}", C_RED, "5,4", 2))
    for val, lab, col, dash, k in refs:
        x = gx + val * sc
        s.line(x, gy - 4, x, ybot + 4 + k * 16, stroke=col, sw=1.5, dash=dash)
        s.text(x, ybot + 16 + k * 16, lab, size=10.5, anchor="start" if k == 2 else "end", color=col, weight="bold")
    s.footer("experiments/C20_ws_cosim_C17/profiling/processes.csv; C14_ws_cosim_C13/verification.json")
    s.save(os.path.join(out, "fig4_process_gantt.svg"))


# --------------------------------------------------------------------------
# Figure 5: fixed-point bit-width flow
# --------------------------------------------------------------------------
def fig5_bitwidth(out):
    W, H = 1360, 520
    s = Svg(W, H, "C17: fixed-point bit widths through the three layers")
    s.title("Figure 5 - Fixed-point widths and fraction bits through the three layers (ap_int; stored integer = real value x 2^frac)",
            "round half to even, saturate to [-512, 511]; 13 Set14 images: mean delta-PSNR -0.076 dB vs float golden")

    def chain(y, color, name, boxes, note):
        s.text(24, y - 14, name, size=14, weight="bold", color=color)
        x = 24
        bw, gap = 112, 58
        for i, (w, frac, label, op) in enumerate(boxes):
            s.rect(x, y, bw, 58, fill="white", stroke=color, sw=1.5, rx=6)
            s.text(x + bw / 2, y + 20, w, size=12.5, anchor="middle", weight="bold", mono=True)
            s.text(x + bw / 2, y + 36, frac, size=10.5, anchor="middle", color=C_SUB)
            s.text(x + bw / 2, y + 51, label, size=9.5, anchor="middle")
            if i < len(boxes) - 1:
                s.line(x + bw + 2, y + 33, x + bw + gap - 2, y + 33, stroke=color, sw=1.5, arrow=True)
                s.text(x + bw + gap / 2, y + 24, op, size=9, anchor="middle", color=color)
            x += bw + gap
        pass

    chain(85, C_BLUE, "conv1 - Winograd path", [
        ("ap_int<10>", "8 frac bits", "input pixel", "B^T d B"),
        ("ap_int<12>", "8 frac bits", "transformed input 4x4", "x weight"),
        ("ap_int<14>", "9+2 frac bits", "transformed weight x4", "mul"),
        ("ap_int<26>", "19 frac bits", "product (DSP)", "sum 9 blocks"),
        ("ap_int<34>", "19 frac bits", "accumulated m[16]", "A^T m A"),
        ("ap_int<34>", "19 frac bits", "output transform 2x2", ">>2, trunc"),
        ("ap_int<23>", "17 frac bits", "+ bias1 (x256)", "ReLU, round"),
        ("ap_int<10>", "8 frac bits", "conv1 output", ""),
    ], "The weight-transform matrix G is doubled to stay integer, so weights are scaled by 4 and the output transform is shifted right by 2. quantize_conv1 drops 9 fraction bits (round half to even) and saturates to [-512, 511].")

    chain(225, C_ORANGE, "conv2 - packed multiply path (one DSP computes two output channels)", [
        ("ap_int<8> x2", "7 frac bits", "two channel weights", "w0*2^18 + w1"),
        ("ap_int<27>", "packed word", "packed_weights", "x pixel"),
        ("ap_int<10>", "8 frac bits", "conv1 output pixel", "mul"),
        ("ap_int<37>", "15 frac bits", "product (DSP)", "split hi/lo 18"),
        ("ap_int<23> x2", "15 frac bits", "two channel products", "64-input tree"),
        ("ap_int<23>", "15 frac bits", "+ bias2 (x256)", "trunc 21"),
        ("ap_int<21>", "15 frac bits", "before ReLU", "round"),
        ("ap_int<10>", "7 frac bits", "conv2 output", ""),
    ], "The low 18 bits are read as a signed value; a negative low half adds 1 to the high half. Truncating to 21 bits relies on the range asserted in C simulation (21-bit signed). quantize_conv2 drops 8 fraction bits.")

    chain(365, C_GREEN, "conv3 - direct 5x5 convolution, accumulated over 4 cycles", [
        ("ap_int<10>", "7 frac bits", "conv2 output pixel", "x weight"),
        ("ap_int<10>", "9 frac bits", "conv3 weight", "mul"),
        ("ap_int<20>", "16 frac bits", "product (DSP)", "256-input tree"),
        ("ap_int<23>", "16 frac bits", "sum of this cycle's 200", "+ sum"),
        ("ap_int<23>", "16 frac bits", "4-cycle accumulate (+bias3 x128)", "round"),
        ("ap_int<10>", "8 frac bits", "final output (no ReLU)", ""),
    ], ["Every adder-tree level is a fabric adder with one register stage (BIND_OP impl=fabric latency=1): 64 inputs = 6 levels, 256 inputs = 8 levels, which is the main source of the pipeline depths 11 / 13.",
        "decode rebuilds the IEEE float bits directly, so the 10-bit integer converts back to float exactly."])
    s.footer("plain/C17_srcnn_plain.cpp")
    s.save(os.path.join(out, "fig5_bitwidth_flow.svg"))


# --------------------------------------------------------------------------
# Figure 6: HLS estimate vs Vivado routed resources per module
# --------------------------------------------------------------------------
def fig6_resources(out):
    routed = {r["Instance"]: r for r in read_csv(os.path.join(EXP, "C22_ws_impl_C17", "physical_hierarchy_routed.csv"))}
    # HLS per-module estimates: experiments/C17_t4_fifo/C17.md "Module resources" (csynth.rpt)
    hls = {
        "wino_windows": (6026, 4082, 9),
        "wino_engine": (38414, 41307, 0),
        "conv2_stream": (37074, 80091, 0),
        "windows3": (6014, 17679, 36),
        "engine3": (23676, 36001, 0),
        "read_params": (6414, 3524, 0),
        "srcnn (top)": (127985, 192308, 146),
    }
    inst = {
        "wino_windows": "wino_windows_U0", "wino_engine": "wino_engine_U0", "conv2_stream": "conv2_stream_U0",
        "windows3": "windows3_U0", "engine3": "engine3_U0", "read_params": "read_params_U0", "srcnn (top)": "bd_0_wrapper",
    }
    W, H = 1180, 560
    s = Svg(W, H, "C17: HLS estimate vs Vivado routed resources")
    s.title("Figure 6 - HLS estimate vs Vivado post-route resources (C17 to C22, xck26, 5 ns)",
            "grey = HLS csynth estimate, blue = Vivado post-route")
    panels = [("LUT", 0, "Total LUTs"), ("FF", 1, "FFs"), ("BRAM18K", 2, "BRAM18K")]
    px0, py0, pw, ph = 40, 85, 355, 400
    for pi, (ptitle, hi, rcol) in enumerate(panels):
        x = px0 + pi * (pw + 25)
        s.rect(x, py0, pw, ph, fill="white", stroke="#d7dbe0", rx=6)
        s.text(x + 12, py0 + 22, ptitle, size=13, weight="bold")
        mods = list(hls.keys())
        vmax = max(max(hls[m][hi], float(routed[inst[m]][rcol])) for m in mods)
        bar_h, gap = 14, 12
        label_w = 100
        scale = (pw - label_w - 95) / vmax
        for mi, m in enumerate(mods):
            y = py0 + 40 + mi * (2 * bar_h + gap)
            hv = hls[m][hi]
            rv = float(routed[inst[m]][rcol])
            s.text(x + label_w - 6, y + bar_h + 2, m, size=10.5, anchor="end", mono=True, weight="bold" if m.startswith("srcnn") else "normal")
            s.rect(x + label_w, y, hv * scale, bar_h, fill=C_GREY, stroke="none", rx=2, opacity=0.7)
            s.rect(x + label_w, y + bar_h + 1, rv * scale, bar_h, fill=C_BLUE, stroke="none", rx=2)
            s.text(x + label_w + hv * scale + 4, y + bar_h - 3, fmt(hv), size=9.5, mono=True, color=C_SUB)
            ratio = f"  ({100*rv/hv:.0f}%)" if hv else ""
            s.text(x + label_w + rv * scale + 4, y + 2 * bar_h - 2, fmt(rv) + ratio, size=9.5, mono=True, color=C_BLUE)
        ly = py0 + ph - 22
        s.rect(x + 12, ly - 10, 14, 10, fill=C_GREY, stroke="none", opacity=0.7)
        s.text(x + 30, ly, "HLS csynth estimate", size=10.5)
        s.rect(x + 170, ly - 10, 14, 10, fill=C_BLUE, stroke="none")
        s.text(x + 188, ly, "Vivado post-route (C22)", size=10.5)
    ty = py0 + ph + 30
    top = routed["bd_0_wrapper"]
    s.text(40, ty, f"Routed: DSP 1,032 / 1,248   LUT {fmt(float(top['Total LUTs']))} / 117,120   FF {fmt(float(top['FFs']))} / 234,240   BRAM18K 109 / 288   URAM 0      5 ns: WNS +0.013 ns, WHS +0.032 ns, TNS 0", size=11.5, mono=True)
    s.footer("experiments/C17_t4_fifo/reports/csynth.rpt; experiments/C22_ws_impl_C17/physical_hierarchy_routed.csv, verification.json")
    s.save(os.path.join(out, "fig6_hls_vs_routed.svg"))


# --------------------------------------------------------------------------
# Figure 7: conv2 packed multiply, bit layout of one DSP product
# --------------------------------------------------------------------------
def fig7_packing(out):
    # Bit layout from plain/C17_srcnn_plain.cpp (conv2_stream): packed = w0 * 2^18 + w1,
    # product = packed * x (27 b x 10 b -> 37 b), low 18 bits read as signed, borrow repaired.
    # PE measurements: experiments/P01 (signed8 pair), P07 (exact10 residual pair), P02 (direct control).
    W, H = 1180, 760
    s = Svg(W, H, "C17: conv2 packed multiply")
    s.title("Figure 7 - conv2: one DSP48E2 multiply computes two output channels",
            "packed = w0 x 2^18 + w1 (two signed 8-bit weights); product = packed x activation; the low 18 bits hold w1 x, the rest hold w0 x")
    col = C_ORANGE
    x0, bitw = 150, 22          # bits drawn from MSB (left) to LSB (right); bit 36 at x0

    def field(y, msb, lsb, label, fill, h=34, sub=None, size=11):
        x = x0 + (36 - msb) * bitw
        w = (msb - lsb + 1) * bitw
        s.rect(x, y, w, h, fill=fill, stroke=C_SUB, sw=1, rx=3)
        s.text(x + w / 2, y + 21, label, size=size, anchor="middle", weight="bold")
        s.text(x + 2, y + h + 12, str(msb), size=9, color=C_SUB, mono=True)
        s.text(x + w - 2, y + h + 12, str(lsb), size=9, color=C_SUB, mono=True, anchor="end")
        if sub:
            s.text(x + w / 2, y + h + 26, sub, size=10, anchor="middle", color=C_SUB)

    # row 1: packed weight word (27 bits -> bits 26..0): w0 | 10-bit gap | w1
    y = 90
    s.text(24, y + 21, "packed weight", size=12, weight="bold", color=col)
    s.text(24, y + 36, "ap_int<27>", size=10.5, mono=True, color=C_SUB)
    field(y, 26, 18, "w0 (8 bit + sign)", "#fbe3cc", sub="A port, bits 26..18")
    field(y, 17, 8, "10-bit gap: all 0 if w1 >= 0, all 1 if w1 < 0", "white", sub="sign extension of w1 (it is one integer)", size=10)
    field(y, 7, 0, "w1 (8 bit)", "#fdf1e4", sub="bits 7..0")
    # row 2: activation
    y = 180
    s.text(24, y + 21, "activation", size=12, weight="bold", color=col)
    s.text(24, y + 36, "ap_int<10>", size=10.5, mono=True, color=C_SUB)
    field(y, 9, 0, "x (10 bit, >= 0 after ReLU)", "#e3ecf7", sub="B port")
    s.text(x0 + (36 - 9) * bitw - 14, y + 24, "x   (DSP48E2 27 x 18 signed multiplier: A port = packed word, B port = x)", size=11.5, color=C_SUB, anchor="end")
    # row 3: product
    y = 275
    s.text(24, y + 21, "product", size=12, weight="bold", color=col)
    s.text(24, y + 36, "ap_int<37>", size=10.5, mono=True, color=C_SUB)
    field(y, 36, 18, "high field = w0 x   (reads w0 x - 1 when w1 x < 0)", "#fbe3cc", sub="19 bits, read as signed, then + borrow")
    field(y, 17, 0, "low field = w1 x, 18-bit two's complement", "#fdf1e4", sub="8 b x 10 b needs 17 bits + sign = 18 bits, so it never reaches bit 18")
    s.path(f"M {x0 + (36 - 17) * bitw + 12} {y - 6} C {x0 + (36 - 17) * bitw + 12} {y - 30}, {x0 + (36 - 26) * bitw + 60} {y - 30}, {x0 + (36 - 26) * bitw + 60} {y - 6}",
           stroke=C_RED, sw=1.4, arrow=True)
    s.text(x0 + (36 - 22) * bitw, y - 34, "bit 17 = sign of w1 x; if 1, high field += 1 (borrow repair, fabric)", size=10.5, color=C_RED, anchor="middle")

    # worked example
    y = 370
    s.rect(24, y, 1132, 190, fill="white", stroke="#d7dbe0", rx=6)
    s.text(38, y + 22, "Worked example: w0 = 3, w1 = -5, x = 7   (expect w0 x = 21, w1 x = -35)", size=12.5, weight="bold", color=col)
    mono_x = 38
    rows = [
        ("packed = 3 x 2^18 + (-5) = 786,427", "000000010 | 1111111111 | 11111011", "fields read 2, all ones, 251: w1 = -5 has already borrowed 1 from w0"),
        ("product = 786,427 x 7 = 5,504,989", "0000000000000010100 | 111111111111011101", "high = 20, low = 262,109 unsigned"),
        ("low field as 18-bit signed", "bit 17 = 1  ->  262,109 - 2^18 = -35", "= w1 x, exact"),
        ("high field repaired", "20 + 1 = 21", "= w0 x, exact"),
        ("same with w1 = +5", "000000011 | 0000000000 | 00000101  x 7 -> high 21, low 35, bit 17 = 0", ""),
    ]
    for i, (a, b_, c) in enumerate(rows):
        yy = y + 48 + i * 26
        s.text(mono_x, yy, a, size=11)
        s.text(mono_x + 330, yy, b_, size=11, mono=True)
        if c:
            s.text(mono_x + 760, yy, c, size=10.5, color=C_SUB)
    s.text(mono_x + 330, y + 48 + 5 * 26, "no borrow, nothing to repair", size=10.5, color=C_SUB)

    # bottom: per-cycle structure and alternatives
    y = 580
    s.rect(24, y, 640, 150, fill="white", stroke="#d7dbe0", rx=6)
    s.text(38, y + 22, "Per cycle in continuous_c2_fold (II = 1, 4 cycles per pixel)", size=12.5, weight="bold", color=col)
    lines = [
        "4 lanes x 64 input channels = 256 DSPs, each producing w0 x and w1 x -> 512 products",
        "per lane: two 64-input fabric adder trees (6 levels, 1 register each) -> sum0, sum1",
        "+ bias (x 2^8), truncate to 21 bits, ReLU, round half to even, saturate -> two ap_int<10>",
        "4 cycles x 4 lanes x 2 = 32 output channels; packing done once per frame at weight load (2,192 cycles)",
    ]
    for i, t in enumerate(lines):
        s.text(38, y + 46 + i * 22, t, size=11.5)
    s.rect(690, y, 466, 150, fill="white", stroke="#d7dbe0", rx=6)
    s.text(704, y + 22, "Measured PE alternatives (4 ns target, II = 1)", size=12.5, weight="bold")
    hdr = ["variant", "DSP / pair", "LUT", "exact?"]
    rows = [
        ("direct 10 b x 10 b, two DSPs (P02)", "2", "-", "yes"),
        ("signed-8 pair, gap 18 (P01)", "1", "132", "yes (2^24)"),
        ("exact-10 residual pair (P07)", "1", "454", "yes"),
    ]
    cx = [704, 950, 1030, 1085]
    for j, h in enumerate(hdr):
        s.text(cx[j], y + 46, h, size=11, weight="bold", color=C_SUB)
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            s.text(cx[j], y + 70 + i * 22, v, size=11, mono=(j > 0))
    s.footer("plain/C17_srcnn_plain.cpp (conv2_stream); experiments/P01, P02, P07; C13/C17 csynth: conv2_stream 256 DSP")
    s.save(os.path.join(out, "fig7_conv2_packing.svg"))


# --------------------------------------------------------------------------
# Figure 8: conv3 streaming window and folded engine
# --------------------------------------------------------------------------
def fig8_conv3(out):
    # From plain/C17_srcnn_plain.cpp (windows3, engine3) and C17 csynth (engine3 fold depth 13, windows3 36 BRAM18K).
    W, H = 1180, 600
    s = Svg(W, H, "C17: conv3 window generation and folded engine")
    s.title("Figure 8 - conv3: 5x5 window from a 4-row line buffer, 200 DSPs over 4 cycles per output pixel",
            "windows3 keeps four rows of the padded 259x259x32 map; engine3 handles 8 input channels x 25 taps per cycle and accumulates over 4 cycles")
    col = C_GREEN
    # ---- left: windows3
    lx, ly = 24, 80
    s.rect(lx, ly, 520, 470, fill="white", stroke="#d7dbe0", rx=6)
    s.text(lx + 14, ly + 24, "windows3  (one padded pixel in, one window out, II = 1)", size=13, weight="bold", color=col)
    # input stream
    s.rect(lx + 14, ly + 50, 150, 40, fill="#e9f5ee", stroke=col, rx=4)
    s.text(lx + 89, ly + 67, "padded3 stream", size=11, anchor="middle", weight="bold")
    s.text(lx + 89, ly + 82, "pixel2: 32 ch x 10 b = 320 b", size=9.5, anchor="middle", color=C_SUB)
    s.line(lx + 164, ly + 70, lx + 200, ly + 70, stroke=col, sw=1.5, arrow=True)
    # line buffer
    bx, by = lx + 200, ly + 50
    for r in range(4):
        s.rect(bx, by + r * 22, 300, 20, fill="#e9f5ee", stroke=col, rx=2)
        s.text(bx + 150, by + r * 22 + 14, f"line[{r}]  259 x 32 ch x 10 b", size=10, anchor="middle", mono=True)
    s.text(bx + 150, by + 4 * 22 + 14, "4 x 82,880 b = 331,520 b -> 36 BRAM18K (ram_2p)", size=10, anchor="middle", color=C_SUB)
    # window
    wx, wy = lx + 40, ly + 190
    s.text(wx, wy - 8, "window[5][5][32]  5 x 5 x 32 x 10 b = 8,000 b in registers; shifts one column per pixel", size=10.5, color=C_SUB)
    cell = 26
    for r in range(5):
        for c in range(5):
            s.rect(wx + c * cell, wy + r * cell, cell - 2, cell - 2, fill="#cfe9d8" if c == 4 else "#e9f5ee", stroke=col, sw=0.8, rx=1)
    s.text(wx + 5 * cell + 10, wy + 2.5 * cell, "column 4 = new column: 4 rows from line[] + the new pixel", size=10)
    s.text(wx + 5 * cell + 10, wy + 2.5 * cell + 16, "line[] shifts up one row at the same address", size=10)
    # outputs
    ox, oy = lx + 40, ly + 350
    s.rect(ox, oy, 215, 44, fill="#e9f5ee", stroke=col, rx=4)
    s.text(ox + 107, oy + 18, "windows0: channels 0..15", size=11, anchor="middle", weight="bold")
    s.text(ox + 107, oy + 34, "25 taps x 16 ch x 10 b = 4,000 b, depth 2", size=9.5, anchor="middle", color=C_SUB)
    s.rect(ox + 235, oy, 215, 44, fill="#e9f5ee", stroke=col, rx=4)
    s.text(ox + 342, oy + 18, "windows1: channels 16..31", size=11, anchor="middle", weight="bold")
    s.text(ox + 342, oy + 34, "25 taps x 16 ch x 10 b = 4,000 b, depth 2", size=9.5, anchor="middle", color=C_SUB)
    s.text(ox, oy + 66, "The 8,000-bit window is split in two because Vitis HLS rejects aggregated streams wider than 4,096 bits", size=10.5, color=C_SUB)
    s.text(ox, oy + 82, "(C09 failed with 'bit-width after aggregation (8000) is larger than 4096').", size=10.5, color=C_SUB)
    s.text(lx + 14, ly + 455, "A window is emitted only for y >= 4 and x >= 4: 65,025 windows from 67,081 padded pixels.", size=10.5)

    # ---- right: engine3
    rx, ry = 570, 80
    s.rect(rx, ry, 586, 470, fill="white", stroke="#d7dbe0", rx=6)
    s.text(rx + 14, ry + 24, "engine3  (continuous_c3_fold, II = 1, 4 cycles per output pixel)", size=13, weight="bold", color=col)
    sx, sy, sw_, sh = rx + 120, ry + 50, 100, 40
    s.text(sx - 8, sy + 25, "step", size=11, color=C_SUB, anchor="end")
    for k in range(4):
        s.rect(sx + k * (sw_ + 8), sy, sw_, sh, fill=col, stroke="none", opacity=0.2 + 0.2 * k, rx=3)
        s.text(sx + k * (sw_ + 8) + sw_ / 2, sy + 16, str(k), size=11, anchor="middle")
        s.text(sx + k * (sw_ + 8) + sw_ / 2, sy + 32, f"ic {8*k}..{8*k+7}", size=10, anchor="middle", mono=True)
    s.text(sx, sy - 8, "step 0 reads both window halves", size=10, color=C_BLUE)
    s.text(sx + 3 * (sw_ + 8) + sw_, sy + sh + 14, "step 3 writes 1 output", size=10, color=C_GREEN, anchor="end")
    # datapath boxes
    dx, dy = rx + 40, ry + 130
    boxes = [
        ("8 ic x 25 taps = 200 products", "ap_int<10> x ap_int<10> -> ap_int<20>, 200 DSPs (BIND_OP impl=dsp)"),
        ("zero-pad to 256, 8-level adder tree", "fabric adders, one register per level -> ap_int<23> partial"),
        ("sum = (step 0 ? bias x 2^7 : sum) + partial", "ap_int<23>, fabric add, latency 1"),
        ("after step 3: round half to even, saturate", "drop 8 fraction bits -> ap_int<10>, no ReLU"),
    ]
    for i, (a, b) in enumerate(boxes):
        yy = dy + i * 70
        s.rect(dx, yy, 506, 52, fill="#e9f5ee", stroke=col, rx=5)
        s.text(dx + 12, yy + 21, a, size=12, weight="bold")
        s.text(dx + 12, yy + 40, b, size=10.5, color=C_SUB, mono=True)
        if i < len(boxes) - 1:
            s.line(dx + 253, yy + 52, dx + 253, yy + 70 - 2, stroke=col, sw=1.5, arrow=True)
    s.text(rx + 14, ry + 430, "Pipeline depth 13 cycles (HLS iteration latency): multiply, 8 tree levels, accumulate, quantize.", size=10.5)
    s.text(rx + 14, ry + 448, "Weights 32 x 25 x 10 b = 8,000 b in LUTRAM, partitioned 8 x 25 so all 200 taps are read in one cycle.", size=10.5)
    s.footer("plain/C17_srcnn_plain.cpp (windows3, engine3); experiments/C17_t4_fifo/reports/engine3_Pipeline_continuous_c3_fold_csynth.rpt; C22 routed: windows3 36 BRAM18K")
    s.save(os.path.join(out, "fig8_conv3_window_engine.svg"))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "figures", "C17"))
    ap.add_argument("--no-title", action="store_true", help="omit the in-figure title; use the document caption instead")
    args = ap.parse_args(argv)
    global NO_TITLE
    NO_TITLE = args.no_title
    os.makedirs(args.out, exist_ok=True)
    for fn in (fig1_fold_timing, fig2_balance, fig3_dataflow, fig4_gantt, fig5_bitwidth, fig6_resources, fig7_packing, fig8_conv3):
        fn(args.out)
        print("wrote", fn.__name__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
