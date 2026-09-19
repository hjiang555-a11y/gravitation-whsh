# Paper draft: Wuhan-Shanghai optical-clock comparison

LaTeX submission draft for the tidal gravitational-redshift analysis of
the Wuhan (Yb) - Shanghai (Sr) optical-clock comparison.

## Files

| File | Purpose |
|---|---|
| `main.tex` | Full article: abstract, introduction, setup, methods, detection, correction, caveats, conclusion, data availability, references. |
| `refs.bib` | BibTeX entries. **All entries are placeholders** (see below). |
| `README.md` | This file. |

## How to compile

Standard four-pass build (two `pdflatex` passes around `bibtex` so that
cross-references and the bibliography resolve):

```bash
cd paper
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

The output is `main.pdf`. A single `pdflatex main.tex` pass also exits 0
and produces a PDF, but the bibliography and some cross-references will
show as `?` until `bibtex` and the second `pdflatex` pass run.

### Preamble notes

- Class: plain `article` (11pt, a4paper). No `revtex4-2` dependency.
- Required packages: `fontenc`, `inputenc`, `amsmath`, `amssymb`,
  `graphicx`, `booktabs`, `geometry`, `hyperref`.
- `siunitx` is **optional**. The preamble loads it only if present
  (`\IfFileExists{siunitx.sty}`); otherwise it defines `\SI` and `\num`
  fallbacks. This TeX Live 2023 (Debian) install does **not** ship
  `siunitx`, and the document compiles without it.

## Figures

The four figures are `\includegraphics` placeholders pointing at PDF
files that do **not** exist yet:

```
../clock_ratio/paper_figs/fig1_ratio_segments.pdf
../clock_ratio/paper_figs/fig2_tidal_detection.pdf
../clock_ratio/paper_figs/fig3_correction.pdf
../clock_ratio/paper_figs/fig4_methods_summary.pdf
```

Only the PNG versions exist in the repository
(`clock_ratio/paper_figs/figN_*.png`). To build with figures, either:

1. convert the PNGs to PDF, e.g.
   `for f in ../clock_ratio/paper_figs/fig*.png; do convert "$f" "${f%.png}.pdf"; done`
   (requires ImageMagick), or
2. edit the four `\includegraphics` lines in `main.tex` to use `.png`.

Without the figure files, `pdflatex` still exits 0 but prints
`LaTeX Warning: File ... not found` and leaves the figure boxes empty.
Each `\includegraphics` line carries a `% TODO: verify figure path`
comment with the PNG fallback.

## Verified vs placeholder

### Verified (traceable to repository artifacts)

Every numeric claim in `main.tex` carries a `% src: <file>` comment
naming the artifact it was read from. The anchor numbers were taken from:

- `clock_ratio/tidal_correction/summary.json` - the three
  `R_duration` values and the `delta_R` differences.
- `clock_ratio/statistical_methods_tidal.json` - WLS/Birge/M-P/Bayesian
  centres, `chi2_red`, Birge ratios, long-term stability.
- `clock_ratio/statistical_methods_tidal_seg9_excluded.json` -
  segment-9-excluded sensitivity.
- `clock/segment_analysis/batch_aggregate.csv` - detection statistics
  (14/17 sign, Stouffer, Fisher, amplitude `A`).
- `clock_ratio/correlation_reanalysis.csv` - segment-mean Pearson
  correlation.
- `clock_ratio/correlation_reanalysis_seg9_independent.json` -
  independent re-derivation and segment-9-excluded correlation.

The verified anchor values are:

- `R_duration(raw) = 1.2075070393433377203696`
- `R_duration(theory) = 1.2075070393433377208108` (`+0.441e-18`)
- `R_duration(empirical) = 1.2075070393433377206078` (`+0.238e-18`)
- WLS deviations vs `1.2075070393433377213`: raw `-0.503e-18`,
  theory `+0.389e-18`, empirical `-0.041e-18`
- `chi2_red`: `5.424 / 3.699 / 4.559`
- Detection: `14/17` same sign (`p=0.013`), Stouffer `|z|=5.87`
  (`p=4.3e-9`), Fisher `p=2.2e-6`, `A=-0.5397 +/- 0.0843` (`6.4 sigma`)
- Long-term `sigma(y_i)`: `2.980 / 2.588 / 2.596 x 1e-18`
- Segment-9 excluded correlation: `r=+0.429` (`p=0.098`) vs full
  `+0.518` (`p=0.033`); independent re-derivation max rel diff `= 0`

### Placeholder (needs verification before submission)

- **All bibliography entries** in `refs.bib`. Each carries a
  `% TODO: verify citation` comment. The NIST and European-network
  entries have plausible metadata but the authors, volume, article
  number, year, and DOI have **not** been checked against the publisher
  record. The remaining entries are generic placeholders that must be
  replaced with real references.
- **Author list and affiliations** in `main.tex` (`% TODO: verify`).
- **Repository URL, DOI, and licence** in the Data availability section
  (`% TODO: verify`).
- **Figure files** (PDF paths do not exist; see above).

## Caveats carried into the paper

The Discussion section states the four limitations explicitly, matching
`docs/METHODOLOGY.md`:

1. The per-segment uncertainties `u_i` are unreliable (OADEV
   extrapolation underestimates by ~30-40%, plus anomalous segments
   5/6/16); combined values are for method comparison only.
2. The `A=-0.54` amplitude comes from a demeaned waveform; applying it
   to the DC part of the undemeaned template is an extra assumption.
3. The `chi2_red` improvement depends strongly on segment 9; excluding
   it reverses the theory-versus-raw comparison.
4. The negative sign is a specified convention, not a new resolution of
   the hardware-polarity question.

## Source draft

This LaTeX draft is derived from `docs/PAPER_DRAFT.md` (Chinese prose
draft) and the repository numeric artifacts. `docs/PAPER_DRAFT.md` is
**not** modified by this directory.
