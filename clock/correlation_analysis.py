#!/usr/bin/env python3
"""Correlation: 17-segment clock-ratio deviation y_i vs session tidal shift.

Plots the 17 jump-free segments as 17 points:
  x = session tidal redshift shift Δf/f (×1e-18), the segment-mean ΔW/c² from
      the professional 30-s 综合差;
  y = clock-ratio deviation y_i = R_i/R_ref − 1 (×1e-18), from
      clock_ratio/compute_ratio.py.

Both y_i and Δf/f are dimensionless quantities normalized to 1 — the tidal
effect on the clock — so this correlation is physically well-posed (unlike the
earlier "amplitude ratio A vs Δf/f", which paired a within-segment fit slope
with a between-segment mean and is physically incoherent).
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

CLOCK_DIR = Path(__file__).resolve().parent
TIDAL_CSV = CLOCK_DIR / "clock_tidal_shift.csv"
RATIO_CSV = CLOCK_DIR.parent / "clock_ratio" / "ratio_17seg.csv"


def load() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = list(csv.DictReader(open(RATIO_CSV)))
    y_i = np.array([float(r["y_i_1e18"]) for r in rows])   # ×1e-18, dimensionless
    n_valid = np.array([int(r["n_valid"]) for r in rows])  # seconds
    tr = list(csv.DictReader(open(TIDAL_CSV)))
    dff = np.array([float(r["frequency_shift_dff"]) for r in tr]) * 1e18
    return y_i, dff, n_valid


def main() -> int:
    y_i, dff, n_valid = load()
    n = len(y_i)

    r, p_r = stats.pearsonr(y_i, dff)
    rho, p_rho = stats.spearmanr(y_i, dff)
    slope, intercept, r_value, p_value, std_err = stats.linregress(dff, y_i)

    print("=== Correlation: clock-ratio deviation y_i vs session tidal shift (17 segments) ===")
    print(f"Pearson  r = {r:+.4f}   p = {p_r:.4f}")
    print(f"Spearman ρ = {rho:+.4f}   p = {p_rho:.4f}")
    print(f"OLS slope = {slope:+.4f}  intercept = {intercept:+.4f}")
    print(f"R² = {r**2:.4f}")
    print(f"n = {n}")
    print()
    print("y_i :", np.round(y_i, 2))
    print("dff:", np.round(dff, 2))

    fig, ax = plt.subplots(figsize=(8, 6))
    neg = y_i < 0
    ax.scatter(dff[neg], y_i[neg], color="#d62728", s=55, zorder=3,
               label="y_i<0")
    ax.scatter(dff[~neg], y_i[~neg], color="#2ca02c", s=55, zorder=3,
               label="y_i>0")
    for i in range(n):
        ax.annotate(
            f"{i+1}", (dff[i], y_i[i]), textcoords="offset points",
            xytext=(5, 5), fontsize=8, color="#555555",
        )
    xs = np.linspace(dff.min() - 0.3, dff.max() + 0.3, 50)
    ax.plot(xs, slope * xs + intercept, "k--", lw=1.2,
            label=f"OLS fit (r={r:+.3f}, p={p_r:.3f})")
    ax.axhline(0.0, color="gray", lw=0.8, ls=":")
    ax.axvline(0.0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Session tidal redshift shift Δf/f (×10⁻¹⁸)")
    ax.set_ylabel("Clock-ratio deviation y_i = R_i/R_ref − 1 (×10⁻¹⁸)")
    ax.set_title(
        "Correlation: clock-ratio deviation y_i vs session tidal shift (17 segments)",
        fontweight="bold",
    )
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(CLOCK_DIR / "correlation.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    print(f"\nWrote {CLOCK_DIR / 'correlation.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
