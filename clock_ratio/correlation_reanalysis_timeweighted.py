#!/usr/bin/env python3
"""Time-weighted (duration-weighted) segment-mean correlation analysis.

Companion to correlation_reanalysis.py, which treats every segment with equal
weight. Here every *second* of valid test time gets equal weight instead: since
the raw per-second data are not kept in this repo, each segment i is weighted
by its valid-test duration n_valid_i (from clock_ratio/ratio_17seg.csv) as a
simple proxy — w_i = n_valid_i / Σ n_valid.

Reports (all duration-weighted):
  1. weighted Pearson r of (y_i, Δf/f) with a p-value from the effective
     sample size n_eff = (Σw)²/Σw² (Kish), t = r·sqrt((n_eff−2)/(1−r²));
  2. weighted Spearman ρ (weighted Pearson of the ranks, same p approach);
  3. weighted least-squares (WLS) fit y_i = slope·Δf/f + intercept;
  4. duration-weighted means of y_i and Δf/f (grand mean / tidal correction).

Equal-weight Pearson r is included in the CSV for direct comparison.

Outputs: clock_ratio/correlation_reanalysis_timeweighted.csv and .png
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

RATIO_CSV = Path(__file__).resolve().parent / "ratio_17seg.csv"
TIDE_CSV = Path(__file__).resolve().parents[1] / "clock" / "clock_tidal_shift.csv"
OUT_DIR = Path(__file__).resolve().parent


def load():
    ratio = list(csv.DictReader(open(RATIO_CSV)))
    y_i = np.array([float(r["y_i_1e18"]) for r in ratio])        # ×1e-18
    n_valid = np.array([int(r["n_valid"]) for r in ratio])       # seconds
    tide = list(csv.DictReader(open(TIDE_CSV)))
    dff = np.array([float(r["frequency_shift_dff"]) for r in tide]) * 1e18
    return y_i, dff, n_valid


def weighted_mean(x, w):
    return float(np.sum(w * x) / np.sum(w))


def effective_n(w):
    """Kish effective sample size (Σw)²/Σw² for weighted correlation tests."""
    return float(np.sum(w) ** 2 / np.sum(w ** 2))


def weighted_pearson(x, y, w):
    mx = weighted_mean(x, w)
    my = weighted_mean(y, w)
    cov = np.sum(w * (x - mx) * (y - my))
    vx = np.sum(w * (x - mx) ** 2)
    vy = np.sum(w * (y - my) ** 2)
    return float(cov / np.sqrt(vx * vy))


def weighted_corr_pvalue(r, n_eff):
    """Two-sided p for a weighted correlation via the effective sample size."""
    dof = n_eff - 2.0
    if dof <= 0 or abs(r) >= 1.0:
        return float("nan")
    t = r * np.sqrt(dof / (1.0 - r * r))
    return float(2.0 * stats.t.sf(abs(t), dof))


def wls_fit(x, y, w):
    """Weighted least squares y = slope·x + intercept; SE via n_eff dof."""
    mx = weighted_mean(x, w)
    my = weighted_mean(y, w)
    sxx = np.sum(w * (x - mx) ** 2)
    sxy = np.sum(w * (x - mx) * (y - my))
    slope = float(sxy / sxx)
    intercept = float(my - slope * mx)
    resid = y - (slope * x + intercept)
    n_eff = effective_n(w)
    dof = n_eff - 2.0
    s2 = float(np.sum(w * resid ** 2) / np.sum(w) * n_eff / dof)
    slope_se = float(np.sqrt(s2 * np.sum(w) / (n_eff * sxx)))
    return slope, intercept, slope_se


def main() -> int:
    y_i, dff, n_valid = load()
    w = n_valid / n_valid.sum()
    n_eff = effective_n(w)

    r_w = weighted_pearson(y_i, dff, w)
    p_r_w = weighted_corr_pvalue(r_w, n_eff)
    rho_w = weighted_pearson(stats.rankdata(y_i), stats.rankdata(dff), w)
    p_rho_w = weighted_corr_pvalue(rho_w, n_eff)
    slope, intercept, slope_se = wls_fit(dff, y_i, w)

    r_eq, p_r_eq = stats.pearsonr(y_i, dff)          # equal-weight reference
    slope_eq, intercept_eq, *_ = stats.linregress(dff, y_i)

    mean_y_w = weighted_mean(y_i, w)
    mean_dff_w = weighted_mean(dff, w)

    print("=== Time-weighted re-correlation: 17-segment clock ratio vs tidal shift ===")
    print(f"weights: w_i = n_valid_i / Σn_valid  (n_eff = {n_eff:.2f} of 17)")
    print(f"weighted Pearson  r = {r_w:+.4f}  p = {p_r_w:.4f}")
    print(f"weighted Spearman ρ = {rho_w:+.4f}  p = {p_rho_w:.4f}")
    print(f"WLS: y_i = {slope:+.4f}·Δf/f {intercept:+.4f}  (slope SE = {slope_se:.4f})")
    print(f"[equal-weight reference: Pearson r = {r_eq:+.4f}, p = {p_r_eq:.4f}]")
    print()
    print("=== duration-weighted grand mean (×1e-18) ===")
    print(f"y_i  weighted mean  = {mean_y_w:+.5f}")
    print(f"Δf/f weighted mean  = {mean_dff_w:+.5f}  (overall tidal correction)")
    print(f"total test time     = {n_valid.sum():.0f} s = {n_valid.sum()/3600:.2f} h")

    # CSV
    csv_path = OUT_DIR / "correlation_reanalysis_timeweighted.csv"
    with csv_path.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["metric", "value"])
        wr.writerow(["weighted_pearson_r", f"{r_w:.6f}"])
        wr.writerow(["weighted_pearson_p", f"{p_r_w:.6f}"])
        wr.writerow(["weighted_spearman_rho", f"{rho_w:.6f}"])
        wr.writerow(["weighted_spearman_p", f"{p_rho_w:.6f}"])
        wr.writerow(["n_eff", f"{n_eff:.6f}"])
        wr.writerow(["wls_slope", f"{slope:.6f}"])
        wr.writerow(["wls_slope_se", f"{slope_se:.6f}"])
        wr.writerow(["wls_intercept", f"{intercept:.6f}"])
        wr.writerow(["equalweight_pearson_r", f"{r_eq:.6f}"])
        wr.writerow(["equalweight_pearson_p", f"{p_r_eq:.6f}"])
        wr.writerow(["weighted_mean_yi_1e18", f"{mean_y_w:.6f}"])
        wr.writerow(["weighted_mean_dff_1e18", f"{mean_dff_w:.6f}"])
        wr.writerow(["total_test_time_s", f"{n_valid.sum():.0f}"])

    # plot
    fig, ax = plt.subplots(figsize=(8, 6))
    sizes = 40 + 240 * w / w.max()
    ax.scatter(dff, y_i, s=sizes, c=np.arange(len(y_i)), cmap="viridis",
               zorder=3, edgecolors="black", linewidths=0.4)
    for i in range(len(y_i)):
        ax.annotate(f"{i+1}", (dff[i], y_i[i]),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=7, color="#444444")
    xs = np.linspace(dff.min() - 0.6, dff.max() + 0.6, 50)
    ax.plot(xs, slope * xs + intercept, "k--", lw=1.4,
            label=f"WLS time-weighted (r={r_w:+.3f}, p={p_r_w:.3f})")
    ax.plot(xs, slope_eq * xs + intercept_eq, color="gray", ls=":", lw=1.2,
            label=f"OLS equal-weight (r={r_eq:+.3f}, p={p_r_eq:.3f})")
    ax.axhline(0, color="gray", lw=0.8, ls=":")
    ax.axvline(0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Session tidal redshift shift Δf/f (×10⁻¹⁸)")
    ax.set_ylabel("Clock-ratio deviation y_i = R_i/R_ref − 1 (×10⁻¹⁸)")
    ax.set_title(
        "17-segment clock ratio vs tidal shift — time-weighted (w = duration)",
        fontweight="bold",
    )
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "correlation_reanalysis_timeweighted.png",
                dpi=160, bbox_inches="tight")
    plt.close(fig)

    print(f"\nWrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'correlation_reanalysis_timeweighted.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
