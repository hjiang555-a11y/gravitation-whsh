#!/usr/bin/env bash
# One-shot verification for paper/rev2: numbers audit, build, reference check.
# Usage: tools/check.sh    (run from anywhere)
set -euo pipefail
cd "$(dirname "$0")/.."

python3 tools/build_numbers.py --check

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex >/dev/null 2>&1 || {
    echo "FAIL: latexmk build failed; see main.log" >&2; exit 1; }
else
  pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
  bibtex main >/dev/null 2>&1
  pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
  pdflatex -interaction=nonstopmode main.tex >/dev/null 2>&1
fi

if grep -qE 'undefined|\?\?' main.log; then
  echo "FAIL: undefined references found in main.log" >&2
  exit 1
fi
echo "PDF: $(pdfinfo main.pdf | awk '/^Pages/{print $2}') pages, $(stat -c%s main.pdf) bytes"
echo "OK"
