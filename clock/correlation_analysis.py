#!/usr/bin/env python3
"""Correlation analysis: clock-comparison result vs tidal gravitational-redshift shift.

The 14 per-session clock-comparison values y_i = R_i/R_ref - 1 (in 1e-18)
are APPROXIMATE, digitized from the scatter plot in clock/atomic-clock-comp.pdf
("Yb/Sr: 14 longest continuous runs"). The tidal shifts are exact (computed by
clock_tidal_shift.py).

Pearson r is invariant under affine rescaling, so the correlation computed from
pixel coordinates is exact even though the absolute y_i values are approximate.
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

# Digitized per-session clock-comparison values y_i (×1e-18), approximate.
# Source: scatter plot "Yb/Sr: 14 longest continuous runs", img-008.
Y_I = np.array(
    [
        -0.07, -3.41, 1.86, -4.63, -3.31, -1.24, 5.26, 1.49,
        6.26, -0.81, 2.26, 0.63, -3.17, 1.95,
    ]
)


def load_tidal() -> np.ndarray:
    rows = list(csv.DictReader(open(TIDAL_CSV)))
    return np.array([float(r["frequency_shift_dff"]) for r in rows]) * 1e18


def main() -> int:
    tidal = load_tidal()
    assert len(tidal) == len(Y_I) == 14

    r, p_r = stats.pearsonr(Y_I, tidal)
    rho, p_rho = stats.spearmanr(Y_I, tidal)

    # Ordinary least-squares regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(tidal, Y_I)

    print("=== Correlation: clock-comparison y_i vs tidal shift ===")
    print(f"Pearson  r = {r:+.4f}   p = {p_r:.4f}")
    print(f"Spearman ρ = {rho:+.4f}   p = {p_rho:.4f}")
    print(f"OLS slope = {slope:+.4f}  intercept = {intercept:+.4f}")
    print(f"R² = {r**2:.4f}")
    print(f"n = 14")
    print()
    print("y_i (×1e-18, approximate):", np.round(Y_I, 2))
    print("tidal (×1e-18, exact):   ", np.round(tidal, 2))

    # Scatter plot
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(tidal, Y_I, color="#0969da", s=50, zorder=3)
    for i in range(14):
        ax.annotate(
            f"{i+1}", (tidal[i], Y_I[i]), textcoords="offset points",
            xytext=(5, 5), fontsize=8, color="#555555",
        )
    xs = np.linspace(tidal.min() - 0.3, tidal.max() + 0.3, 50)
    ax.plot(xs, slope * xs + intercept, "r--", lw=1.2,
            label=f"OLS fit (r={r:+.3f}, p={p_r:.3f})")
    ax.axhline(0.0, color="gray", lw=0.8, ls=":")
    ax.axvline(0.0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Tidal clock-comparison shift Δf/f (×10⁻¹⁸)")
    ax.set_ylabel("Clock-comparison y_i = R_i/R_ref − 1 (×10⁻¹⁸)")
    ax.set_title(
        "Correlation: measured Yb/Sr ratio deviation vs tidal redshift shift",
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
