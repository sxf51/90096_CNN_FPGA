#!/usr/bin/env bash
# Build report/main.pdf.  Uses tectonic when available, otherwise latexmk.
set -euo pipefail
cd "$(dirname "$0")"
if command -v tectonic >/dev/null 2>&1; then
    tectonic --keep-logs main.tex
elif command -v latexmk >/dev/null 2>&1; then
    latexmk -xelatex -interaction=nonstopmode main.tex
else
    echo "neither tectonic nor latexmk found" >&2
    exit 1
fi
echo "built $(pwd)/main.pdf"
