# Overleaf upload package (segment-9 excluded) — Wuhan–Shanghai Yb/Sr optical-clock comparison

This folder is ready to upload to Overleaf as-is.  It is the **16-segment
(segment 9 excluded)** variant of the manuscript; the 17-segment version is
in `paper/overleaf/`.

## Contents

```
main.tex      # the manuscript (16 segments; figure paths flattened to figs/)
refs.bib      # bibliography (26 entries)
figs/         # manuscript figures (raster PNG)
  1.png       # Fig. 1  experimental setup (Wuhan Yb - Shanghai Sr fibre link)
  2.png       # Fig. 2  segment stability and the 16 per-segment ratios
  3.png       # Fig. 3  tidal influence and its correlation
  4.png       # Fig. 4  comparison with previous Yb/Sr determinations
  figS2_correlation.png     # Methods: segment-mean y_i vs tidal shift (16 segments)
  figS3_stability_long.png  # Methods: spliced concatenated stability, long tau
```

## How to upload

1. Download this folder (or the zip `paper/overleaf-seg9-upload.zip`).
2. On Overleaf: **New Project → Upload Project**, then drop the zip.
3. Set the main document to `main.tex` (Overleaf usually detects it).
4. Compiler: **pdfLaTeX** (default).

## Build

No special packages are required. The preamble loads `siunitx` only if it
exists and otherwise defines fallbacks, so it compiles on any TeX Live.
Citations use `natbib` in `[super,sort&compress]` mode with the `unsrtnat`
style (Nature-style superscript numbers, ordered by appearance).

```
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Segment-9-excluded specifics

- 16 uninterrupted segments (segment 9 removed): retained total 986 416 s.
- Headline ratio 1.207 507 039 343 337 720 1(29); Bayesian statistical term
  0.88e-18; segment-to-segment scatter sigma(y_i) = 2.58e-18; segment-mean
  correlation r = +0.429 (p = 0.098).
- Fixed-scenario reduced chi-square: raw 3.91, theory 4.11, empirical 4.26.
- Numbers come from `clock_ratio/statistical_methods_tidal_seg9_excluded.json`
  and `clock_ratio/correlation_reanalysis_seg9_independent.json`.

## Notes

- The figures are the same raster PNGs as the 17-segment package,
  de-interlaced so pdfTeX embeds them without the large-interlaced-PNG
  memory warning.
- All bibliography entries are cited and resolve; no undefined references.
- Placeholders still needing author input are marked in `main.tex` with
  `% PLACEHOLDER:` (Author contributions, Competing interests,
  Acknowledgements).
