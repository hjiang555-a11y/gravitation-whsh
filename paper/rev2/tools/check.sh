#!/usr/bin/env bash
# One-shot verification for paper/rev2: numbers audit, build, reference check.
# Compiles the two documents: main.tex and supplementary.tex.
# Usage: tools/check.sh    (run from anywhere)
set -euo pipefail
cd "$(dirname "$0")/.."

python3 tools/build_numbers.py --check

if command -v latexmk >/dev/null 2>&1; then
  for doc in main supplementary; do
    latexmk -pdf -interaction=nonstopmode -halt-on-error "$doc.tex" >/dev/null 2>&1 || {
      echo "FAIL: latexmk build failed for $doc; see $doc.log" >&2; exit 1; }
  done
else
  for doc in main supplementary; do
    pdflatex -interaction=nonstopmode "$doc.tex" >/dev/null 2>&1
    pdflatex -interaction=nonstopmode "$doc.tex" >/dev/null 2>&1
  done
fi

for doc in main supplementary; do
  if grep -qE 'undefined|\?\?' "$doc.log"; then
    echo "FAIL: undefined references found in $doc.log" >&2
    exit 1
  fi
done
echo "PDF: main $(pdfinfo main.pdf | awk '/^Pages/{print $2}') pages, $(stat -c%s main.pdf) bytes; supplementary $(pdfinfo supplementary.pdf | awk '/^Pages/{print $2}')p"
echo "OK"
