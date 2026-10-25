#!/usr/bin/env python3
"""Convert the Notion export of the SRCNN report page to LaTeX section files.

Usage: notion2tex.py <notion-page.md> <output-dir>

The input is the text returned by the Notion MCP "fetch" tool (Notion-flavoured
Markdown with HTML-style tags).  The output is one .tex file per top-level
heading under <output-dir>/sections/.  The generated files are a starting
point; the committed .tex files may have been edited by hand afterwards.
"""
import re
import sys
import pathlib

SRC = sys.argv[1]
OUT = pathlib.Path(sys.argv[2])
(OUT / "sections").mkdir(parents=True, exist_ok=True)

raw = open(SRC, encoding="utf-8").read()
body = raw.split("<content>", 1)[1].split("</content>", 1)[0]
body = body.replace("\xa0", " ")
lines = body.split("\n")

# ---------------------------------------------------------------- figures
# Notion image order -> local file name and width option
FIGURES = [
    ("fig01-experiment-loop.pdf", r"width=0.9\figw"),
    ("fig02-evolution-overview.png", r"width=\linewidth,height=0.95\figh,keepaspectratio"),
    ("fig03-top-level-structure.png", r"width=0.72\linewidth,height=0.48\textheight,keepaspectratio"),
    ("fig04-dataflow-backpressure.pdf", r"width=\linewidth"),
    ("fig05-dsp48e2.png", r"width=0.8\figw"),
    ("fig06-conv3-window-engine.pdf", r"width=\linewidth"),
    ("fig07-block-design-hp0.png", r"width=\figw"),
    ("fig08-block-design-cycle-monitor.png", r"width=\figw"),
    ("fig09-block-design-hp1.png", r"width=\figw"),
    ("fig10-block-design-axi-stats.png", r"width=\figw"),
    ("fig11-butterfly.png", r"width=\figw"),
]
fig_index = 0

# ---------------------------------------------------------------- tables
# column spec per table number (main text).  'X' columns use tabularx.
# C{w} = centred paragraph column.
TABLE_SPEC = {
    1: dict(cols="lX"),
    2: dict(cols="l p{3.4cm} X"),
    3: dict(cols="l X R{0.9cm} R{1.3cm} X R{1.4cm} R{1.6cm} R{1.0cm}", size="scriptsize"),
    5: dict(cols="c C{1.15cm} C{1.25cm} C{1.15cm} C{1.25cm} C{1.15cm} C{1.3cm} C{1.4cm} C{1.5cm} X", size="footnotesize"),
    7: dict(cols="X R{1.6cm} R{1.5cm} L{2.2cm} L{2.6cm} L{2.0cm}", size="footnotesize"),
    9: dict(cols="L{5.2cm} X", size="footnotesize", paths=True),
    10: dict(cols="l l X"),
    12: dict(cols="L{4.6cm} L{3.1cm} X", size="footnotesize"),
    15: dict(cols="l r r r R{2.3cm} R{1.9cm}"),
    19: dict(cols="l l X"),
    21: dict(cols="L{2.1cm} L{3.4cm} L{2.0cm} X L{2.0cm}", size="footnotesize"),
    22: dict(cols="r L{3.0cm} X L{2.3cm} R{1.3cm} L{1.7cm}", size="footnotesize"),
}
APPENDIX_TABLE_SPEC = {
    3: dict(cols="L{2.7cm} L{4.6cm} X"),
    8: dict(cols="L{4.4cm} R{2.3cm} R{1.7cm} R{1.7cm} R{1.7cm}"),
}

# ---------------------------------------------------------------- inline
SUP = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
       "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "⁻": "-"}
UNI = {
    "×": r"$\times$", "→": r"$\rightarrow$", "↔": r"$\leftrightarrow$",
    "−": r"$-$", "·": r"$\cdot$", "–": "--", "—": "---",
    "ᵀ": r"\textsuperscript{T}", "½": r"\textonehalf{}", "¼": r"\textonequarter{}",
    "≈": r"$\approx$", "μ": r"\textmu{}", "≤": r"$\le$", "≥": r"$\ge$",
    "§": r"\S{}", "±": r"$\pm$", "…": r"\ldots{}", "÷": r"$\div$",
    "∞": r"$\infty$", "Δ": r"$\Delta$", "⊙": r"$\odot$", "💡": "",
}


def uni(s):
    s = re.sub("[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+",
               lambda m: r"\textsuperscript{" + "".join(SUP[c] for c in m.group(0)) + "}", s)
    for k, v in UNI.items():
        s = s.replace(k, v)
    return s


def unescape_notion(s):
    return re.sub(r"\\([_<>~^*\\#\[\]()`])", r"\1", s)


def esc(s):
    s = s.replace("\\", "\x00BS\x00")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
                 ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")]:
        s = s.replace(a, b)
    return s.replace("\x00BS\x00", r"\textbackslash{}")


MODE = {"appendix": False, "bib": False}


def label_prefix():
    return "A" if MODE["appendix"] else ""


def xrefs(s):
    """Replace 'Figure 3', 'Table 12', 'Listing 1', 'Section 6.2' by \\ref."""
    p = label_prefix()
    kinds = {"Figure": "fig", "Table": "tab", "Listing": "lst"}

    def one(m):
        return f"{m.group(1)}~\\ref{{{kinds[m.group(1)]}:{p}{m.group(2)}}}"

    def two(m):
        k = kinds[m.group(1)[:-1]]
        return f"{m.group(1)}~\\ref{{{k}:{p}{m.group(2)}}} {m.group(3)} \\ref{{{k}:{p}{m.group(4)}}}"

    s = re.sub(r"\b(Figures|Tables|Listings) (\d+) (and|to) (\d+)\b", two, s)
    s = re.sub(r"\b(Figure|Table|Listing) (\d+)\b", one, s)
    s = re.sub(r"\bSections (\d+(?:\.\d+)?) (and|to) (\d+(?:\.\d+)?)\b",
               lambda m: f"Sections~\\ref{{sec:{m.group(1)}}} {m.group(2)} \\ref{{sec:{m.group(3)}}}", s)
    s = re.sub(r"\bSection (\d+(?:\.\d+)?)\b", lambda m: f"Section~\\ref{{sec:{m.group(1)}}}", s)
    return s


def text_segment(s):
    s = unescape_notion(s)
    s = re.sub(r'"([^"\n]*)"', r"``\1''", s)
    s = esc(s)
    s = uni(s)
    s = xrefs(s)
    return s


def code_span(s):
    s = unescape_notion(s)
    s = esc(s)
    s = uni(s)
    if "/" in s:  # path: allow line breaks after separators
        s = s.replace("/", "/\\allowbreak{}").replace("\\_", "\\_\\allowbreak{}")
    return r"\texttt{" + s + "}"


def inline(s, strip_tags=False):
    ph = []

    def keep(x):
        ph.append(x)
        return "\x01%d\x01" % (len(ph) - 1)

    s = re.sub(r"<code>(.*?)</code>", lambda m: keep(code_span(m.group(1))), s)
    s = re.sub(r"\\\[(\d+(?:,\s*\d+)*)\\\]",
               lambda m: keep(r"\cite{" + ",".join("ref" + x.strip() for x in m.group(1).split(",")) + "}"), s)

    def link(m):
        text, url = m.group(1), m.group(2)
        if url.startswith("http://AGENTS.md"):
            return keep(inline(text, strip_tags))
        if unescape_notion(re.sub(r"</?[bi]>", "", text)).strip() == url:
            return keep(r"\url{" + url + "}")
        return keep(r"\href{" + url + "}{" + inline(text, strip_tags) + "}")

    s = re.sub(r"\[([^\]]*)\]\(([^)]*)\)", link, s)
    if strip_tags:
        s = re.sub(r"</?[bi]>", "", s)
    parts = re.split(r"(<b>|</b>|<i>|</i>|<br />)", s)
    out = []
    depth = []
    for p in parts:
        if p == "<b>":
            out.append(r"\textbf{"); depth.append("b")
        elif p == "<i>":
            out.append(r"\emph{"); depth.append("i")
        elif p in ("</b>", "</i>"):
            if depth:
                depth.pop(); out.append("}")
        elif p == "<br />":
            out.append(r"\\")
        else:
            out.append(text_segment(p))
    out.extend("}" * len(depth))
    s = "".join(out)
    s = re.sub("\x01(\\d+)\x01", lambda m: ph[int(m.group(1))], s)
    # tidy empty emphasis left by Notion's formatting
    s = s.replace(r"\emph{}", "").replace(r"\textbf{}", "")
    return s


# ---------------------------------------------------------------- blocks
chunks = []          # list of (file_key, text)
file_key = ["00-front"]
sec_counter = [0, 0, 0, 0]
last_level = 0
pending_table = None   # (number, caption)


def emit(s):
    chunks.append((file_key[0], s))


def slug(s):
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:40]


def heading(level, text):
    global last_level
    text = re.sub(r"</?b>", "", text).strip()
    if text == "归档一下":
        MODE["appendix"] = True
        sec_counter[:] = [0, 0, 0, 0]
        text = "Archived material"
    if text == "References":
        MODE["bib"] = True
        file_key[0] = "08-references"
        emit("\\phantomsection\\addcontentsline{toc}{section}{References}")
        return
    level = min(level, last_level + 1)
    last_level = level
    sec_counter[level - 1] += 1
    for k in range(level, 4):
        sec_counter[k] = 0
    num = ".".join(str(x) for x in sec_counter[:level])
    cmd = ["section", "subsection", "subsubsection", "paragraph"][level - 1]
    if level == 1:
        file_key[0] = f"{sec_counter[0]:02d}-{slug(text)}" if not MODE["appendix"] else "A1-archive"
    lab = ("app:" if MODE["appendix"] else "sec:") + num
    title = inline(text, strip_tags=True)
    if cmd == "paragraph":
        emit(f"\\{cmd}{{{title}}}")
    else:
        emit(f"\\{cmd}{{{title}}}\\label{{{lab}}}")


def figure(src_index, caption_text):
    fname, opt = FIGURES[src_index]
    m = re.match(r"\s*Figure (\d+)\.\s*(.*)", caption_text, re.S)
    num, cap = (m.group(1), m.group(2)) if m else (None, caption_text)
    cap = inline(cap.strip(), strip_tags=True)
    lab = f"fig:{label_prefix()}{num}" if num else f"fig:{fname}"
    emit("\\begin{figure}[!htbp]\n\\centering\n"
         f"\\includegraphics[{opt}]{{figures/{fname}}}\n"
         f"\\caption{{{cap}}}\n\\label{{{lab}}}\n\\end{{figure}}")


def is_numeric(cell):
    return re.fullmatch(r"[\d,.\s%+−\-–/]*", re.sub(r"</?b>", "", cell)) is not None


def table(rows, header):
    global pending_table
    num, cap = pending_table if pending_table else (None, "")
    pending_table = None
    spec = (APPENDIX_TABLE_SPEC if MODE["appendix"] else TABLE_SPEC).get(int(num) if num else -1, {})
    ncol = max(len(r) for r in rows)
    rows = [r + [""] * (ncol - len(r)) for r in rows]
    cols = spec.get("cols")
    if not cols:
        cols = ""
        for c in range(ncol):
            body_cells = [r[c] for r in rows[1:]] if header else [r[c] for r in rows]
            cols += "r" if c > 0 and all(is_numeric(x) for x in body_cells) else "l"
    cols = cols.replace(" ", "")
    use_x = "X" in cols
    cols = cols.replace("X", "Y")  # Y = ragged-right X column (defined in main.tex)
    size = spec.get("size", "footnotesize")
    env = "tabularx" if use_x else "tabular"
    begin = f"\\begin{{{env}}}{{\\linewidth}}{{{cols}}}" if use_x else f"\\begin{{{env}}}{{{cols}}}"
    out = []
    if spec.get("landscape"):
        out.append("\\begin{landscape}")
    out.append("\\begin{table}[!htbp]\n\\centering\n\\" + size)
    if cap:
        out.append(f"\\caption{{{inline(cap, strip_tags=True)}}}\n\\label{{tab:{label_prefix()}{num}}}")
    out.append(begin + "\n\\toprule")
    for i, r in enumerate(rows):
        cells = []
        for c in r:
            c = c.strip()
            if i == 0 and header:
                c = re.sub(r"</?b>", "", c)
            cell = inline(c)
            if spec.get("paths"):
                cell = re.sub(r"\\texttt\{([^{}]*)\}", lambda m: "\\path{" + m.group(1)
                              .replace("\\allowbreak{}", "").replace("\\_", "_").replace("\\%", "%")
                              .replace("\\#", "#") + "}", cell)
            cells.append(cell)
        out.append(" & ".join(cells) + r" \\")
        if i == 0 and header:
            out.append("\\midrule")
    out.append("\\bottomrule\n\\end{" + env + "}\n\\end{table}")
    if spec.get("landscape"):
        out.append("\\end{landscape}")
    emit("\n".join(out))


def html_table(block):
    header = 'header-row="true"' in block[0]
    text = "\n".join(block)
    rows = []
    for tr in re.findall(r"<tr>(.*?)</tr>", text, re.S):
        cells = [" ".join(x.strip() for x in td.strip().split("\n")) for td in re.findall(r"<td>(.*?)</td>", tr, re.S)]
        rows.append(cells)
    table(rows, header)


def pipe_table(block):
    rows = []
    for ln in block:
        if re.fullmatch(r"\|[\s\-|:]*\|", ln.strip()):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        rows.append(cells)
    table(rows, True)


def listing(lang, code):
    opts = []
    if code and re.match(r"Listing (\d+)\.", code[0]):
        m = re.match(r"Listing (\d+)\.\s*(.*)", code[0])
        opts.append(f"caption={{{inline(m.group(2))}}}")
        opts.append(f"label={{lst:{m.group(1)}}}")
        code = code[1:]
        while code and not code[0].strip():
            code = code[1:]
    if lang in ("c++", "cpp", "c"):
        opts.append("language=C++")
    else:
        opts.append("language={}")
    emit("\\begin{lstlisting}[" + ",".join(opts) + "]\n" + "\n".join(code) + "\n\\end{lstlisting}")


para = []


def flush_para():
    if para:
        emit(inline(" ".join(x.strip() for x in para)))
        para.clear()


list_items = []
list_kind = None


def flush_list():
    global list_kind
    if list_items and MODE["bib"] and list_kind == "ol":
        emit("\\begin{thebibliography}{%d}\n" % len(list_items)
             + "\n".join("\\bibitem{ref%d} %s" % (k + 1, inline(x)) for k, x in enumerate(list_items))
             + "\n\\end{thebibliography}")
        list_items.clear()
    elif list_items:
        env = "enumerate" if list_kind == "ol" else "itemize"
        emit(f"\\begin{{{env}}}\n" + "\n".join("\\item " + inline(x) for x in list_items) + f"\n\\end{{{env}}}")
        list_items.clear()
    list_kind = None


def flush():
    flush_para()
    flush_list()


i = 0
n = len(lines)
while i < n:
    ln = lines[i]
    st = ln.strip()
    # --- skip / structural tags
    if st.startswith("<callout"):
        while not lines[i].strip().startswith("</callout>"):
            i += 1
        i += 1
        continue
    if st.startswith("<table-of-contents") or st in ("<p>", "</p>", "<p />"):
        flush(); i += 1; continue
    if st == "":
        flush(); i += 1; continue
    # --- code fence
    if st.startswith("```"):
        flush()
        lang = st[3:].strip().lower()
        code = []
        i += 1
        while not lines[i].strip().startswith("```"):
            code.append(lines[i]); i += 1
        listing(lang, code)
        i += 1
        continue
    # --- display math
    if st == "$$":
        flush()
        math = []
        i += 1
        while lines[i].strip() != "$$":
            math.append(lines[i]); i += 1
        emit("\\begin{equation}\n" + "\n".join(math) + "\n\\end{equation}")
        i += 1
        continue
    # --- headings
    m = re.match(r"^(#{1,4}) (.*)$", ln)
    if m:
        flush(); heading(len(m.group(1)), m.group(2)); i += 1; continue
    if st == "<h3>":
        flush()
        txt = []
        i += 1
        while lines[i].strip() != "</h3>":
            txt.append(lines[i].strip()); i += 1
        heading(3, " ".join(txt).rstrip(". "))
        i += 1
        continue
    # --- image
    m = re.match(r'^<image source="([^"]+)"\s*(/?)>', st)
    if m:
        flush()
        idx = fig_index; fig_index += 1
        if m.group(2) == "/":
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            cap = ""
            if j < n and re.match(r"^<i>Figure \d+\.", lines[j].strip()):
                cap = re.sub(r"</?i>", "", lines[j].strip())
                i = j
            figure(idx, cap)
            i += 1
        else:
            cap = []
            i += 1
            while not lines[i].strip().startswith("</image>"):
                cap.append(lines[i].strip()); i += 1
            figure(idx, " ".join(cap))
            i += 1
        continue
    # --- table caption
    m = re.match(r"^<i>Table (\d+)\.\s*(.*)</i>\s*$", st) or re.match(r"^<b>Table (\d+)\.</b>\s*(.*)$", st)
    if m:
        flush(); pending_table = (m.group(1), m.group(2)); i += 1; continue
    # --- html table
    if st.startswith("<table"):
        flush()
        block = []
        while not lines[i].strip().startswith("</table>"):
            block.append(lines[i]); i += 1
        html_table(block)
        i += 1
        continue
    # --- pipe table
    if st.startswith("|"):
        flush()
        block = []
        while i < n and lines[i].strip().startswith("|"):
            block.append(lines[i]); i += 1
        pipe_table(block)
        continue
    # --- bookmark
    m = re.match(r'^<bookmark source="([^"]+)"', st)
    if m:
        flush(); emit("\\noindent\\url{" + m.group(1) + "}"); i += 1; continue
    # --- blockquote
    if st.startswith("> "):
        flush(); emit("\\begin{quote}\n" + inline(st[2:]) + "\n\\end{quote}"); i += 1; continue
    # --- lists
    if st.startswith("- "):
        flush_para()
        if list_kind != "ul":
            flush_list(); list_kind = "ul"
        list_items.append(st[2:]); i += 1; continue
    m = re.match(r"^\d+\. (.*)$", st)
    if m:
        flush_para()
        if list_kind != "ol":
            flush_list(); list_kind = "ol"
        list_items.append(m.group(1)); i += 1; continue
    # --- plain paragraph text
    flush_list()
    para.append(ln)
    i += 1
flush()

# ---------------------------------------------------------------- write
files = {}
for key, text in chunks:
    files.setdefault(key, []).append(text)


def fixups(key, s):
    """Edits that the Notion markup cannot express; applied after conversion."""
    if key.startswith("01-"):
        # the page says "Figure 1 shows the network" but carries no network figure;
        # the figure supplied separately (figures/fig00-network.png) is inserted here
        s = s.replace("Figure~\\ref{fig:1} shows the network", "Figure~\\ref{fig:network} shows the network")
        anchor = "the intermediate data never has to leave the device."
        assert anchor in s
        s = s.replace(anchor, anchor + "\n\n"
            "\\begin{figure}[!htbp]\n\\centering\n"
            "\\includegraphics[width=0.78\\figw]{figures/fig00-network.png}\n"
            "\\caption{The SRCNN network as implemented: Conv1 (9$\\times$9, 1$\\rightarrow$64 channels, ReLU), "
            "Conv2 (1$\\times$1, 64$\\rightarrow$32, ReLU) and Conv3 (5$\\times$5, 32$\\rightarrow$1, linear) on a "
            "255$\\times$255 single-channel input. Per output pixel each layer is a matrix--vector product with "
            "5,184, 2,048 and 800 multiply-accumulates; over the 65,025 pixels of a frame that is 337.1 M, 133.2 M "
            "and 52.0 M, 522 million in all.}\n\\label{fig:network}\n\\end{figure}", 1)
    if key.startswith("04-"):
        # the two Notion sub-pages with the sources are appendices in the PDF
        s = re.sub(r"<page url=``[^']*''> Original Code </page>\n\n<page url=``[^']*''> Readable version code </page>\n",
                   lambda m: "The readable version is reproduced in Appendix~\\ref{app:code-readable}; the original "
                   "source is \\path{designs/winograd_t4_windows32_v1/srcnn.cpp} in the project repository.\n", s)
        # the explanation of Table 3 carries broken italic/bold runs on the Notion page
        s = re.sub(r"\\emph\{Iterations per frame\(\}C/RTL co-simulation\\emph\{\) is measured after Vitis \}.*?\(stall\\_pct\)\.\}",
                   lambda m: "\\emph{Iterations per frame (C/RTL co-simulation)} is measured after Vitis C/RTL co-simulation: "
                   "from the latency of the process within one frame (\\texttt{process\\_latency\\_avg\\_cycles}, up to "
                   "273,052 cycles) we subtract \\texttt{read\\_stall\\_cycles} and \\texttt{write\\_stall\\_cycles}, which "
                   "gives the number of cycles in which the stage was actually processing data. \\emph{Stall Percent} is the "
                   "share of the frame in which the process waited on a FIFO (\\texttt{stall\\_pct}).", s, flags=re.S)
        s = s.replace("Iterations per frame(design)", "Iterations per frame (design)")
        s = s.replace("Iterations per frame(C/RTL co-simulation)", "Iterations per frame (C/RTL co-simulation)")
    # references dropped at the authors' request (2026-10-26): 4 FSRCNN, 9 Amidi cheatsheet,
    # 14 Claude Code / Codex software entry, 17 Xilinx INT8 white paper, 19 Zynq UltraScale+ TRM.  thebibliography
    # renumbers the rest and \\cite follows.
    s = s.replace("Its successor FSRCNN \\cite{ref4} moves the upscaling into the network and is the variant most FPGA "
                  "work targets; we keep the original because it is the algorithm set for the project. ", "")
    s = s.replace("\\cite{ref8,ref9}", "\\cite{ref8}")
    s = s.replace(" \\cite{ref14}", "")
    s = s.replace(" \\cite{ref17}", "")
    s = s.replace("\\cite{ref19,ref20}", "\\cite{ref20}")
    if key.startswith("08-"):
        s = re.sub(r"\\bibitem\{ref(4|9|14|17|19)\} [^\n]*\n", "", s)
    if key.startswith("05-"):
        # the Notion bookmark becomes a footnote on the sentence it supports
        s = re.sub(r"QoS mechanisms\.\n\n\\noindent\\url\{([^}]*)\}",
                   lambda m: "QoS mechanisms.\\footnote{AMD Xilinx wiki, \\emph{Traffic Shaping of HP Ports on Zynq "
                             "UltraScale+}: \\url{" + m.group(1).replace("%", "\\%") + "}}", s)
    if key.startswith("06-"):
        # the page refers to a "Listing 2" that it never shows; insert the loader it describes
        s = s.replace("The parameter loaders have the same structure.",
                      "The parameter loaders have the same structure.\n\n"
                      "\\begin{lstlisting}[language=C++,caption={The input loader of C22 (\\texttt{read\\_input} in the "
                      "original source): one pipelined loop that reads a word from DDR, encodes it and writes it to the "
                      "stream in the same iteration.},label={lst:2}]\n"
                      "static void read_input(ftmap_t in[N0][H][W], hls::stream<input> &stream) {\n"
                      "    read_pixels: for (int i = 0; i < H * W; ++i) {\n"
                      "#pragma HLS PIPELINE II=1\n"
                      "        stream.write(encode_input(in[0][i / W][i % W]));\n"
                      "    }\n"
                      "}\n"
                      "\\end{lstlisting}", 1)
    return s


for key, parts in files.items():
    path = OUT / "sections" / f"{key}.tex"
    with open(path, "w", encoding="utf-8") as f:
        f.write("% Generated from the Notion page by tools/notion2tex.py (see report/README.md).\n")
        f.write(fixups(key, "\n\n".join(parts)) + "\n")
    print(path)
