#!/usr/bin/env python3
"""Variant 2: 30-second triangular-integration correlation analysis.

Same jump-free-segment pipeline as batch_analysis.py, EXCEPT both the beat and
the tidal data are aggregated onto the SAME 30-second grid (the native grid of
the professional tidal 综合差) before a 1200-s triangular window / 600-s stride
integration. In the original batch_analysis.py the tidal data is interpolated
onto the beat's 1-s grid; here the beat is down-sampled onto the 30-s grid so
both share the same time points at the TIDAL data's native scale.

Outputs (independent of batch_summary.csv):
  variant30s_summary.csv, variant30s_forest.png
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
    C, F_1550, EXCLUDE_RANGES, GROUPS, JUMP_THRESHOLD, TIDAL_COLUMN,
    UTC_OFFSET, load_beat, load_tide, longest_valid_span,
)

OUT_DIR = Path(__file__).resolve().parent

WINDOW = 1200  # triangular window full width (s)
STRIDE = 600   # one point every 600 s (50% overlap)
GRID = 30  # seconds: aggregate beat onto the tidal 30-s grid


def triangular_30s(x, window_s, stride_s):
    """Triangular (Bartlett) integration on a 30-s grid.

    window_s/stride_s are in seconds; the number of samples per window is
    window_s//GRID.
    """
    w = window_s // GRID
    st = stride_s // GRID
    k = np.arange(w)
    tri = 1.0 - np.abs(2 * k - (w - 1)) / (w + 1)
    tri = tri / tri.sum()
    if len(x) < w:
        return np.array([])
    n_out = (len(x) - w) // st + 1
    out = np.empty(n_out)
    for i in range(n_out):
        s = i * st
        out[i] = float(np.dot(tri, x[s : s + w]))
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


def tidal_on_30s(t_stamps_utc, t_tide, tot):
    """Sample the tidal data onto the given UTC 30-s grid timestamps."""
    t_sec = (t_tide - np.datetime64("1970-01-01")).astype(int)
    s_sec = (t_stamps_utc - np.datetime64("1970-01-01")).astype(int)
    dw = np.interp(s_sec, t_sec, tot)
    return dw / C**2 * F_1550


def main():
    T, B = load_beat()
    t_tide, tot = load_tide()

    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))

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

        # Aggregate the beats onto a uniform 30-s grid by MEAN (not decimation):
        # averaging 30 consecutive 1-s samples lowers white noise by ~sqrt(30)
        # while preserving the tidal component, matching the 30-s native grid of
        # the professional tidal data.
        n = len(b_run)
        n30 = n // GRID
        b = b_run[: n30 * GRID].reshape(n30, GRID).mean(axis=1)
        t = t_run[GRID // 2 :: GRID][:n30]

        beat_norm = b - b.mean()
        beat_tri = triangular_30s(beat_norm, WINDOW, STRIDE)
        if len(beat_tri) < 5:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue

        tide_30 = tidal_on_30s(t - UTC_OFFSET, t_tide, tot)
        tide_tri = triangular_30s(tide_30 - tide_30.mean(), WINDOW, STRIDE)
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

    csv_path = OUT_DIR / "variant30s_summary.csv"
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
        ax.set_ylabel("Amplitude A (30-s grid)")
        ax.set_title("Variant 2: 30-s triangular integration, 17 segments",
                     fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT_DIR / "variant30s_forest.png", dpi=150,
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
    print("\n=== Variant 2 (30-s triangular integration) ===")
    print(f"negative r segments: {neg}/{len(_rs)} (binomial p="
          f"{stats.binomtest(neg, len(_rs), 0.5).pvalue:.4f})")
    print(f"Stouffer |z| = {z_agn:.2f} (p = {2*stats.norm.cdf(-z_agn):.2e})")
    print(f"Fisher chi2 = {chi2:.1f} (df={2*len(_rs)}) p = {fisher_p:.2e}")
    print(f"amplitude A (1/uA^2) = {Abar:+.4f} +/- {uAbar:.4f} "
          f"({abs(Abar)/uAbar:.2f} sigma)")
    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'variant30s_forest.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
