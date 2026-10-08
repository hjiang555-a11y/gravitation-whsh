# Paper draft: Wuhan-Shanghai optical-clock comparison

LaTeX submission draft for the tidal gravitational-redshift analysis of
the Wuhan (Yb) - Shanghai (Sr) optical-clock comparison.

## Version status (milestone)

- **v0.3 (2026-10-01, commit `da5b2e4`)** — stable working version.
  Nature Article structure, main text compressed to 13 pages.
- **Rebuilt candidate (2026-10-08)** — `rev2/` is a rebuild on the frozen
  phase-one audit result layer (16-segment primary membership; the
  time-varying-redshift term is carried as an uncertainty item only).
  `main.tex` in this directory is kept unchanged as the historical draft.
  Length-vs-Nature review: `rev2/REVIEW_NOTES.md`.
- **Structure** — Results: 2.1 Network and observation campaign →
  2.2 Theoretical tidal influence → 2.3 Tidal gravitational-redshift
  detection → 2.4 Clock-ratio determination. Discussion:
  3.1 Attempted tidal compensation → 3.2 Clock-comparison synthesis.
- **Open items** — authors and affiliations remain provisional. The tidal
  template response is an effect estimate only: its covariance-aware
  significance and the interpretation of the supplied height-equivalent
  tide series remain to be confirmed.

## Files

| File | Purpose |
|---|---|
| `main.tex` | Full article: abstract, introduction, results, discussion, methods, back matter, references. |
| `refs.bib` | BibTeX entries (26 references; see below). |
| `overleaf/` + `overleaf-upload.zip` | Self-contained Overleaf upload (main.tex with `figs/` paths, refs.bib, figures). |
| `overleaf-rev2/` + `overleaf-rev2-upload.zip` | Overleaf upload for the rebuilt candidate (`rev2/`; sections/, generated/, vector-PDF figs). |
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
  `graphicx`, `booktabs`, `geometry`, `natbib`, `hyperref`.
- `siunitx` is **optional**. The preamble loads it only if present
  (`\IfFileExists{siunitx.sty}`); otherwise it defines `\SI` and `\num`
  fallbacks. This TeX Live 2023 (Debian) install does **not** ship
  `siunitx`, and the document compiles without it.

## Figures

The manuscript embeds six local PNG figures:

```
figs/1.png
figs/2.png
figs/3.png
figs/4.png
figs/figS2_correlation.png
figs/figS3_stability_long.png
```

The source uses paths relative to `paper/`. The four publication-oriented
figures are generated in `clock_ratio/paper_figs/`; the manuscript copies
used for submission live under `paper/figs/`. Regenerate those source
artifacts before refreshing their manuscript copies.

## Verified vs placeholder

### Verified (traceable to repository artifacts)

Every numeric claim in `main.tex` carries a `% src: <file>` comment
naming the artifact it was read from. The anchor numbers were taken from:

- `clock_ratio/tidal_correction/summary.json` - the three
  `R_duration` values and the `delta_R` differences.
- `clock_ratio/statistical_methods_tidal.json` - regenerated WLS/Birge/M-P/
  Bayesian centres, `chi2_red`, Birge ratios and long-term stability.
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
- Regenerate all WLS, random-effects and `chi2_red` values after the
  unit-consistent statistical correction.
- The historical windowed amplitude estimate is about `A=-0.54`; inferential
  values must be regenerated from non-overlapping windows and are not a
  covariance-aware detection claim.
- Segment-9 excluded correlation: `r=+0.429` (`p=0.098`) vs full
  `+0.518` (`p=0.033`); independent re-derivation max rel diff `= 0`

### Completed (was placeholder, now verified)

- **Bibliography** in `refs.bib`. The two reference-value entries are
  verified against the publisher / arXiv records:
  - `aeppli2026nist` - Aeppli et al., *Atomic Clock Frequency Ratios with
    Fractional Uncertainty ≤ 3.2×10⁻¹⁸*, Phys. Rev. Lett. **137**, 033201
    (2026), DOI `10.1103/g865-9mk1`, arXiv:2512.21428. Reports the
    NIST Yb/Sr value `1.2075070393433377230(37)`.
  - `pizzocaro2026european` - Pizzocaro et al., *International Optical
    Clock Comparison Using the European Optical Fiber Network*,
    Phys. Rev. Research **8**, 033250 (2026), DOI `10.1103/l4bh-ryxs`,
    arXiv:2604.27963. Reports the European-network Yb/Sr value
    `1.207507039343337718(32)`.
  The five unused generic placeholder entries were removed.
- **Author** in `main.tex` - `Haifeng Jiang` (from the repository git
  history). A `% TODO` remains for optional co-authors/affiliations.
- **Repository URL, DOI, and licence** in the Data availability section -
  URL `https://github.com/hjiang555-a11y/gravitation-whsh`, licence
  Apache-2.0 (`LICENSE` file at repository root). No DOI is minted.
- **Figure files** - the four vector PDFs exist and are embedded
  (`% TODO: verify figure path` comments removed).

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
