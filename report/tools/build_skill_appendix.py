#!/usr/bin/env python3
"""Render the experiment-exploration skill (SKILL.md) as a LaTeX appendix.

Usage: build_skill_appendix.py <SKILL.md> <output .tex>

Strips the YAML front matter, maps the few non-ASCII symbols to LaTeX outside
code spans, runs pandoc (markdown -> latex, listings for code), and turns the
top-level heading into the appendix section.  Requires pandoc.
"""
import re
import subprocess
import sys
import tempfile
import pathlib

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])

src = re.sub(r"^---\n.*?\n---\n", "", src, count=1, flags=re.S)

UNI = {"≥": r"$\ge$", "≤": r"$\le$", "−": r"$-$", "Δ": r"$\Delta$", "★": r"$\star$",
       "×": r"$\times$", "→": r"$\rightarrow$", "—": "---", "…": "..."}


def map_text(seg):
    for k, v in UNI.items():
        seg = seg.replace(k, v)
    return seg


# apply the symbol map outside fenced blocks and inline code spans
parts = re.split(r"(```.*?```)", src, flags=re.S)
for i, p in enumerate(parts):
    if p.startswith("```"):
        continue
    sub = re.split(r"(`[^`\n]*`)", p)
    parts[i] = "".join(x if x.startswith("`") else map_text(x) for x in sub)
src = "".join(parts)

with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
    f.write(src)
    tmp = f.name
tex = subprocess.run(["pandoc", "-f", "markdown", "-t", "latex", "--listings", tmp],
                     check=True, capture_output=True, text=True).stdout

# the skill's own title becomes the appendix heading (set in main.tex)
tex = re.sub(r"\\section\{[^}]*\n?[^}]*\}\\label\{[^}]*\}\n*", "", tex, count=1)
# the skill numbers its own sections ("## 3. When ..."); LaTeX numbers them B.n, so drop the prefix
tex = re.sub(r"(\\subsection\{)\d+\.\s*", r"\1", tex)
# two-column pipe tables: give the first column 28 % instead of half
tex = re.sub(r"\\real\{0\.5000\}\}\n(\s*>\{\\raggedright\\arraybackslash\}p\{\(\\linewidth - 2\\tabcolsep\) \* )\\real\{0\.5000\}",
             r"\\real{0.28}}\n\1\\real{0.72}", tex)
# pandoc's auto labels can clash with ours; drop them
tex = re.sub(r"\\label\{[a-z0-9-]+\}", "", tex)


# relative links (templates/...) point into the skill directory: keep the text only
def strip_rel_href(s):
    res = []
    i = 0
    while True:
        j = s.find(r"\href{", i)
        if j < 0:
            res.append(s[i:]); break
        res.append(s[i:j])
        k = s.index("}", j)
        url = s[j + 6:k]
        # balanced second argument
        depth = 0; m = k + 1
        assert s[m] == "{"
        for m in range(k + 1, len(s)):
            if s[m] == "{": depth += 1
            elif s[m] == "}":
                depth -= 1
                if depth == 0: break
        text = s[k + 2:m]
        res.append(text if not url.startswith("http") else r"\href{" + url + "}{" + text + "}")
        i = m + 1
    return "".join(res)


tex = strip_rel_href(tex)
# pandoc's uncaptioned-longtable wrapper clashes with the caption package
tex = re.sub(r"\{\\def\\LTcaptype\{none\}[^\n]*\n", "", tex)
tex = tex.replace("\\end{longtable}\n}", "\\end{longtable}")
out.write_text("% Generated from SKILL.md by tools/build_skill_appendix.py; do not edit by hand.\n" + tex,
               encoding="utf-8")
print(out)
