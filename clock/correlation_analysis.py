#!/usr/bin/env python3
"""Correlation: 17-segment amplitude ratio A vs session tidal redshift shift.

Plots the 17 jump-free segments as 17 points:
  x = session tidal redshift shift Δf/f (×1e-18), the segment-mean ΔW/c² from
      the professional 30-s 综合差;
  y = per-segment amplitude ratio A, the fitted beat = A·tide amplitude from
      batch_analysis.py (available for ALL 17 segments).

Previously this plot used the clock-ratio deviation y_i = R_i/R_ref − 1 as the
y axis, but y_i only exists for 14 segments (the experimenter's 17-segment
revision reports only aggregate Yb/Sr, not per-segment y_i for 15/16/17).
Switching the y axis to A (available for all 17) yields a complete 17-point
picture.
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
BATCH_CSV = CLOCK_DIR / "segment_analysis" / "batch_summary.csv"


def load() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rows = list(csv.DictReader(open(BATCH_CSV)))
    A = np.array([float(r["A"]) for r in rows])
    uA = np.array([float(r["u_A"]) for r in rows])
    tr = list(csv.DictReader(open(TIDAL_CSV)))
    dff = np.array([float(r["frequency_shift_dff"]) for r in tr]) * 1e18
    return A, uA, dff


def main() -> int:
    A, uA, dff = load()
    n = len(A)

    r, p_r = stats.pearsonr(A, dff)
    rho, p_rho = stats.spearmanr(A, dff)
    slope, intercept, r_value, p_value, std_err = stats.linregress(dff, A)

    print("=== Correlation: amplitude A vs session tidal shift (17 segments) ===")
    print(f"Pearson  r = {r:+.4f}   p = {p_r:.4f}")
    print(f"Spearman ρ = {rho:+.4f}   p = {p_rho:.4f}")
    print(f"OLS slope = {slope:+.4f}  intercept = {intercept:+.4f}")
    print(f"R² = {r**2:.4f}")
    print(f"n = {n}")
    print()
    print("A :", np.round(A, 2))
    print("dff:", np.round(dff, 2))

    fig, ax = plt.subplots(figsize=(8, 6))
    neg = A < 0
    ax.scatter(dff[neg], A[neg], color="#d62728", s=55, zorder=3,
               label="A<0")
    ax.scatter(dff[~neg], A[~neg], color="#2ca02c", s=55, zorder=3,
               label="A>0")
    for i in range(n):
        ax.annotate(
            f"{i+1}", (dff[i], A[i]), textcoords="offset points",
            xytext=(5, 5), fontsize=8, color="#555555",
        )
    xs = np.linspace(dff.min() - 0.3, dff.max() + 0.3, 50)
    ax.plot(xs, slope * xs + intercept, "k--", lw=1.2,
            label=f"OLS fit (r={r:+.3f}, p={p_r:.3f})")
    ax.axhline(0.0, color="gray", lw=0.8, ls=":")
    ax.axvline(0.0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Session tidal redshift shift Δf/f (×10⁻¹⁸)")
    ax.set_ylabel("Amplitude ratio A = (beat / tide)")
    ax.set_title(
        "Correlation: amplitude ratio A vs session tidal shift (17 segments)",
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
