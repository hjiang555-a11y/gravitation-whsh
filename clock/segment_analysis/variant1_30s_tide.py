#!/usr/bin/env python3
"""Variant 1: tidal data kept on its native 30-s grid (no 1-s interpolation).

Same 17-segment pipeline as batch_analysis.py, EXCEPT the tidal data is NOT
interpolated onto the beat's 1-s grid. Instead:
  - the beat is integrated with the original 1200-s triangular window (1200
    1-s samples per window, 600-s stride);
  - the tidal data is integrated on its NATIVE 30-s grid with the same 1200-s
    window expressed as 40 samples, 600-s stride as 20 samples;
  - the two series share the same window centres, so amplitude/correlation is
    still a fair comparison.

This isolates the effect of tidal integration granularity: original uses
linear interpolation of the 30-s tide onto 1-s; this variant uses the 30-s
grid directly.

Outputs (independent of batch_summary.csv):
  variant1_30s_tide_summary.csv, variant1_30s_tide_forest.png
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from clock.shared import (  # noqa: E402
    C, COEF, F_1550, EXCLUDE_RANGES, GROUPS, JUMP_THRESHOLD, TIDAL_COLUMN,
    UTC_OFFSET, load_beat, load_tide, longest_valid_span,
)

OUT_DIR = Path(__file__).resolve().parent

WINDOW = 1200  # s
STRIDE = 600   # s
TIDE_GRID = 30  # native tidal sampling (s)


def triangular(x, n_window, n_stride):
    k = np.arange(n_window)
    tri = 1.0 - np.abs(2 * k - (n_window - 1)) / (n_window + 1)
    tri = tri / tri.sum()
    if len(x) < n_window:
        return np.array([])
    n_out = (len(x) - n_window) // n_stride + 1
    out = np.empty(n_out)
    for i in range(n_out):
        s = i * n_stride
        out[i] = float(np.dot(tri, x[s : s + n_window]))
    return out


def fit_amplitude(beat, tide):
    b = beat - beat.mean()
    t = tide - tide.mean()
    A = float(np.dot(t, b) / np.dot(t, t))
    resid = b - A * t
    dof = len(b) - 1
    sigma2 = float(np.dot(resid, resid) / dof)
    u_A = float(np.sqrt(sigma2 / np.dot(t, t)))
    r = float(np.corrcoef(beat, tide)[0, 1])
    p = float(stats.pearsonr(beat, tide).pvalue)
    return {"A": A, "u_A": u_A, "r": r, "p": p, "n": len(beat)}


def main():
    T, B = load_beat()
    t_tide, tot = load_tide()
    t_tide_sec = (t_tide - np.datetime64("1970-01-01")).astype(int)

    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))

    # tidal grid: 30-s native, in seconds since epoch (UTC)
    results = []
    for idx, (s, e) in enumerate(GROUPS, 1):
        S = np.datetime64(s)
        E = np.datetime64(e)
        in_win = (T >= S) & (T < E)
        t_seg = T[in_win]
        b_seg = B[in_win]
        ex_seg = excl[in_win]
        if len(b_seg) == 0:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue
        med = np.median(b_seg[plausible])
        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        span = longest_valid_span(valid)
        if span is None:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue
        t_run = t_seg[span[0] : span[1] + 1]
        b_run = b_seg[span[0] : span[1] + 1]

        # Beat: 1-s triangular, 1200-s window / 600-s stride (as original).
        beat_norm = b_run - b_run.mean()
        beat_tri = triangular(beat_norm, WINDOW, STRIDE)
        if len(beat_tri) < 5:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue

        # Tidal: NATIVE 30-s grid (no 1-s interpolation). Same 1200-s window /
        # 600-s stride expressed in 30-s samples: 40 / 20.
        t_run_s = (t_run - np.datetime64("1970-01-01")).astype(int)
        # align to the 30-s grid covering the run (UTC)
        t_utc_s = t_run_s - 8 * 3600
        lo = t_utc_s[0] - (t_utc_s[0] % TIDE_GRID)
        hi = t_utc_s[-1]
        grid = np.arange(lo, hi + 1, TIDE_GRID)
        tide_grid = np.interp(grid, t_tide_sec, tot) / C**2 * F_1550
        tide_tri = triangular(tide_grid - tide_grid.mean(),
                              WINDOW // TIDE_GRID, STRIDE // TIDE_GRID)
        tide_tri = tide_tri[: len(beat_tri)]

        fit = fit_amplitude(beat_tri, tide_tri)
        results.append({
            "group": idx,
            "t_start": str(t_run[0]),
            "t_end": str(t_run[-1]),
            "hours": len(t_run) / 3600,
            "n_pts": len(beat_tri),
            "A": fit["A"],
            "u_A": fit["u_A"],
            "r": fit["r"],
            "p": fit["p"],
        })

    csv_path = OUT_DIR / "variant1_30s_tide_summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "t_start_beijing", "t_end_beijing", "hours",
                    "n_pts", "A", "u_A", "A_over_uA", "r", "p"])
        for r in results:
            if np.isnan(r["A"]):
                w.writerow([r["group"], "", "", "", "", "", "", "", "", ""])
            else:
                w.writerow([r["group"], r["t_start"], r["t_end"],
                            f"{r['hours']:.3f}", r["n_pts"],
                            f"{r['A']:.4f}", f"{r['u_A']:.4f}",
                            f"{r['A']/r['u_A']:.2f}", f"{r['r']:.4f}",
                            f"{r['p']:.4f}"])

    valid = [r for r in results if not np.isnan(r["A"])]
    if valid:
        fig, ax = plt.subplots(figsize=(10, 5))
        gs = np.array([r["group"] for r in valid], dtype=float)
        A = np.array([r["A"] for r in valid])
        uA = np.array([r["u_A"] for r in valid])
        ax.errorbar(gs, A, yerr=uA, fmt="o", ms=6, lw=1.2, capsize=4,
                    color="#d62728", zorder=3)
        ax.axhline(0.0, color="gray", lw=0.8, ls=":")
        ax.axhline(1.0, color="#2ca02c", lw=1.0, ls="--", label="A = +1")
        ax.set_xlabel("Segment index")
        ax.set_ylabel("Amplitude A")
        ax.set_title("Variant 1: tidal on native 30-s grid (no 1-s interp)",
                     fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT_DIR / "variant1_30s_tide_forest.png", dpi=150,
                    bbox_inches="tight")
        plt.close(fig)

    _rs = np.array([r["r"] for r in valid])
    _ps = np.array([r["p"] for r in valid])
    _As = np.array([r["A"] for r in valid])
    _uAs = np.array([r["u_A"] for r in valid])
    neg = int((_rs < 0).sum())
    peps = np.clip(_ps, 1e-14, None)
    z_agn = np.sum(stats.norm.ppf(1 - peps / 2)) / np.sqrt(len(_rs))
    chi2 = -2 * np.sum(np.log(peps))
    fisher_p = stats.chi2.sf(chi2, 2 * len(_rs))
    w = 1.0 / _uAs**2
    Abar = float(np.sum(_As * w) / np.sum(w))
    uAbar = float(1.0 / np.sqrt(np.sum(w)))
    print("\n=== Variant 1 (tidal on native 30-s grid, no 1-s interp) ===")
    print(f"negative r segments: {neg}/{len(_rs)} (binomial p="
          f"{stats.binomtest(neg, len(_rs), 0.5).pvalue:.4f})")
    print(f"Stouffer |z| = {z_agn:.2f} (p = {2*stats.norm.cdf(-z_agn):.2e})")
    print(f"Fisher chi2 = {chi2:.1f} (df={2*len(_rs)}) p = {fisher_p:.2e}")
    print(f"amplitude A (1/uA^2) = {Abar:+.4f} +/- {uAbar:.4f} "
          f"({abs(Abar)/uAbar:.2f} sigma)")
    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'variant1_30s_tide_forest.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
