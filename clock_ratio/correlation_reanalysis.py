#!/usr/bin/env python3
"""Re-correlation analysis on the newest high-precision 17-segment clock ratios.

Uses the decimal-computed per-segment ratio deviations y_i = R_i/R_ref - 1
(from clock_ratio/ratio_17seg.csv) and correlates them against the session
tidal redshift shift Δf/f = ΔW/c² (from clock/clock_tidal_shift.csv).

Reports:
  1. overall correlation  — Pearson / Spearman / time-weighted Pearson of
     (y_i, Δf/f) across all 17 segments;
  2. time-weighted grand mean of y_i (weight = segment valid-test duration);
  3. overall tidal correction — the duration-weighted mean of Δf/f, i.e. the
     tidal gravitational-redshift term that should be removed from the ratio.

Outputs: clock_ratio/correlation_reanalysis.csv and .png
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


def weighted_pearson(x, y, w):
    mx = weighted_mean(x, w)
    my = weighted_mean(y, w)
    cov = np.sum(w * (x - mx) * (y - my))
    vx = np.sum(w * (x - mx) ** 2)
    vy = np.sum(w * (y - my) ** 2)
    return cov / np.sqrt(vx * vy)


def main() -> int:
    y_i, dff, n_valid = load()
    w = n_valid / n_valid.sum()

    r, p_r = stats.pearsonr(y_i, dff)
    rho, p_rho = stats.spearmanr(y_i, dff)
    r_w = weighted_pearson(y_i, dff, w)
    slope, intercept, rv, pv, se = stats.linregress(dff, y_i)

    mean_y_w = weighted_mean(y_i, w)
    mean_dff_w = weighted_mean(dff, w)
    mean_y_arith = float(y_i.mean())
    mean_dff_arith = float(dff.mean())

    print("=== Re-correlation: newest 17-segment clock ratio vs tidal shift ===")
    print(f"Pearson  r = {r:+.4f}  p = {p_r:.4f}")
    print(f"Spearman ρ = {rho:+.4f}  p = {p_rho:.4f}")
    print(f"time-weighted Pearson r = {r_w:+.4f}")
    print(f"OLS: y_i = {slope:+.4f}·Δf/f {intercept:+.4f}  (r={rv:+.4f}, p={pv:.4f})")
    print()
    print("=== time-weighted grand mean (×1e-18) ===")
    print(f"y_i  weighted mean  = {mean_y_w:+.5f}")
    print(f"y_i  arithmetic mean= {mean_y_arith:+.5f}")
    print()
    print("=== overall tidal correction (×1e-18) ===")
    print(f"Δf/f weighted mean  = {mean_dff_w:+.5f}")
    print(f"Δf/f arithmetic mean= {mean_dff_arith:+.5f}")
    print(f"total test time     = {n_valid.sum():.0f} s = {n_valid.sum()/3600:.2f} h")

    # CSV
    csv_path = OUT_DIR / "correlation_reanalysis.csv"
    with csv_path.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["metric", "value"])
        wr.writerow(["pearson_r", f"{r:.6f}"])
        wr.writerow(["pearson_p", f"{p_r:.6f}"])
        wr.writerow(["spearman_rho", f"{rho:.6f}"])
        wr.writerow(["spearman_p", f"{p_rho:.6f}"])
        wr.writerow(["weighted_pearson_r", f"{r_w:.6f}"])
        wr.writerow(["ols_slope", f"{slope:.6f}"])
        wr.writerow(["ols_intercept", f"{intercept:.6f}"])
        wr.writerow(["weighted_mean_yi_1e18", f"{mean_y_w:.6f}"])
        wr.writerow(["arith_mean_yi_1e18", f"{mean_y_arith:.6f}"])
        wr.writerow(["weighted_mean_dff_1e18", f"{mean_dff_w:.6f}"])
        wr.writerow(["arith_mean_dff_1e18", f"{mean_dff_arith:.6f}"])
        wr.writerow(["total_test_time_s", f"{n_valid.sum():.0f}"])

    # plot
    fig, ax = plt.subplots(figsize=(8, 6))
    sizes = 40 + 240 * w / w.max()
    sc = ax.scatter(dff, y_i, s=sizes, c=np.arange(17), cmap="viridis",
                    zorder=3, edgecolors="black", linewidths=0.4)
    for i in range(17):
        ax.annotate(f"{i+1}", (dff[i], y_i[i]),
                    textcoords="offset points", xytext=(5, 5),
                    fontsize=7, color="#444444")
    xs = np.linspace(dff.min() - 0.6, dff.max() + 0.6, 50)
    ax.plot(xs, slope * xs + intercept, "k--", lw=1.2,
            label=f"OLS (r={r:+.3f}, p={p_r:.3f})")
    ax.axhline(0, color="gray", lw=0.8, ls=":")
    ax.axvline(0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Session tidal redshift shift Δf/f (×10⁻¹⁸)")
    ax.set_ylabel("Clock-ratio deviation y_i = R_i/R_ref − 1 (×10⁻¹⁸)")
    ax.set_title(
        "17-segment clock ratio vs tidal shift (newest decimal ratios)",
        fontweight="bold",
    )
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "correlation_reanalysis.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    print(f"\nWrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'correlation_reanalysis.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
