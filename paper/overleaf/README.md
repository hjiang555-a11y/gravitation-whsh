# Overleaf upload package — Wuhan–Shanghai Yb/Sr optical-clock comparison

This folder is ready to upload to Overleaf as-is.

## Contents

```
main.tex      # the manuscript (figure paths already flattened to figs/)
refs.bib      # bibliography (26 entries)
figs/         # manuscript figures (raster PNG)
  1.png       # Fig. 1  experimental setup (Wuhan Yb - Shanghai Sr fibre link)
  2.png       # Fig. 2  segment stability and the 17 per-segment ratios
  3.png       # Fig. 3  tidal influence and its correlation
  4.png       # Fig. 4  comparison with previous Yb/Sr determinations
  figS2_correlation.png     # Methods: segment-mean y_i vs tidal shift
  figS3_stability_long.png  # Methods: spliced concatenated stability, long tau
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

- The main-text figures are raster PNGs (`figs/1.png`--`4.png`) and the
  two Methods figures are `figs/figS2_correlation.png` and
  `figs/figS3_stability_long.png`, all de-interlaced so pdfTeX embeds them
  without the large-interlaced-PNG memory warning. Vector-PDF variants
  remain in `clock_ratio/paper_figs/`.
- All bibliography entries are cited and resolve; no undefined references.
- Placeholders still needing author input are marked in `main.tex` with
  `% PLACEHOLDER:` (Author contributions, Competing interests,
  Acknowledgements) and `X` for the total uncertainty in the abstract.
