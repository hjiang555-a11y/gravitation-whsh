# Overleaf upload package — Wuhan–Shanghai Yb/Sr optical-clock comparison

This folder is ready to upload to Overleaf as-is.

## Contents

```
main.tex      # the manuscript (figure paths already flattened to figs/)
refs.bib      # bibliography (26 entries)
figs/         # the four figures as vector PDFs
  fig1_ratio_segments.pdf
  fig2_tidal_detection.pdf
  fig3_correction.pdf
  fig4_methods_summary.pdf
```

## How to upload

1. Download this folder (or the zip `paper/overleaf-upload.zip`).
2. On Overleaf: **New Project → Upload Project**, then drop the zip.
3. Set the main document to `main.tex` (Overleaf usually detects it).
4. Compiler: **pdfLaTeX** (default).

## Build

No special packages are required. The preamble loads `siunitx` only if it
exists and otherwise defines fallbacks, so it compiles on any TeX Live.

```
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Notes

- Figure files are the vector PDFs; PNG variants (`*.png`, 300 dpi) exist in
  `clock_ratio/paper_figs/` should you prefer raster images.
- All bibliography entries are cited and resolve; no undefined references.
- Placeholders still needing author input are marked in `main.tex` with
  `% PLACEHOLDER:` (Author contributions, Competing interests,
  Acknowledgements) and `X` for the total uncertainty in the abstract.
