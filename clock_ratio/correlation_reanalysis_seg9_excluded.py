#!/usr/bin/env python3
"""Segment-9-excluded correlation analysis — an ADDITIVE result that does NOT
replace or modify correlation_reanalysis.py or its outputs.

Rationale: segment 9 carries an anomalous Sr systematic shift
(`shift_a = -8.13e-17`, between the 7-month ~-1.72e-16 and the 8-month
~+7.9e-18; source comment asks whether it is real or a placeholder), so its
ratio deviation y_9 is an outlier. This script re-runs the SAME correlation
between the per-segment clock-ratio deviation y_i = R_i/R_ref - 1 and the
session tidal redshift shift Δf/f = ΔW/c², after dropping segment 9.

It reads the already-computed ratio_17seg.csv and clock_tidal_shift.csv, drops
row 9, and recomputes the equal-weight statistics (Pearson r, Spearman ρ, OLS,
means). The 17-segment originals are untouched.

Outputs (new, separate):
  correlation_reanalysis_seg9_excluded.csv
  correlation_reanalysis_seg9_excluded.png
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
EXCLUDED_GROUP = 9


def load() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ratio = list(csv.DictReader(open(RATIO_CSV)))
    g = np.array([int(r["group"]) for r in ratio])
    y_i = np.array([float(r["y_i_1e18"]) for r in ratio])
    n_valid = np.array([int(r["n_valid"]) for r in ratio])
    tide = list(csv.DictReader(open(TIDE_CSV)))
    dff = np.array([float(r["frequency_shift_dff"]) for r in tide]) * 1e18
    return g, y_i, dff, n_valid


def weighted_mean(x, w):
    return float(np.sum(w * x) / np.sum(w))


def main() -> int:
    g, y_all, dff_all, n_all = load()
    if len(g) != len(dff_all):
        raise SystemExit("ratio and tide length mismatch")
    keep = g != EXCLUDED_GROUP
    y_i, dff, n_valid = y_all[keep], dff_all[keep], n_all[keep]
    w = n_valid / n_valid.sum()

    r, p_r = stats.pearsonr(y_i, dff)
    rho, p_rho = stats.spearmanr(y_i, dff)
    slope, intercept, rv, pv, se = stats.linregress(dff, y_i)
    mean_y_w = weighted_mean(y_i, w)
    mean_dff_w = weighted_mean(dff, w)

    print(f"=== correlation with segment {EXCLUDED_GROUP} EXCLUDED ({len(y_i)} segments) ===")
    print(f"Pearson  r = {r:+.4f}  p = {p_r:.4f}")
    print(f"Spearman ρ = {rho:+.4f}  p = {p_rho:.4f}")
    print(f"OLS: y_i = {slope:+.4f}·Δf/f {intercept:+.4f}  (r={rv:+.4f}, p={pv:.4f})")
    print(f"y_i weighted mean = {mean_y_w:+.5f} ×1e-18")
    print(f"Δf/f weighted mean = {mean_dff_w:+.5f} ×1e-18")

    csv_path = OUT_DIR / "correlation_reanalysis_seg9_excluded.csv"
    with csv_path.open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["metric", "value"])
        wr.writerow(["excluded_group", EXCLUDED_GROUP])
        wr.writerow(["n_segments", len(y_i)])
        wr.writerow(["pearson_r", f"{r:.6f}"])
        wr.writerow(["pearson_p", f"{p_r:.6f}"])
        wr.writerow(["spearman_rho", f"{rho:.6f}"])
        wr.writerow(["spearman_p", f"{p_rho:.6f}"])
        wr.writerow(["ols_slope", f"{slope:.6f}"])
        wr.writerow(["ols_intercept", f"{intercept:.6f}"])
        wr.writerow(["weighted_mean_yi_1e18", f"{mean_y_w:.6f}"])
        wr.writerow(["weighted_mean_dff_1e18", f"{mean_dff_w:.6f}"])

    fig, ax = plt.subplots(figsize=(8, 6))
    sizes = 40 + 240 * w / w.max()
    ax.scatter(dff, y_i, s=sizes, c=np.arange(len(y_i)), cmap="viridis",
               zorder=3, edgecolors="black", linewidths=0.4)
    for i, gi in enumerate(g[keep]):
        ax.annotate(f"{gi}", (dff[i], y_i[i]), textcoords="offset points",
                    xytext=(5, 5), fontsize=7, color="#444444")
    xs = np.linspace(dff.min() - 0.6, dff.max() + 0.6, 50)
    ax.plot(xs, slope * xs + intercept, "k--", lw=1.2,
            label=f"OLS (r={r:+.3f}, p={p_r:.3f})")
    ax.axhline(0, color="gray", lw=0.8, ls=":")
    ax.axvline(0, color="gray", lw=0.8, ls=":")
    ax.set_xlabel("Session tidal redshift shift Δf/f (×10⁻¹⁸)")
    ax.set_ylabel("Clock-ratio deviation y_i = R_i/R_ref − 1 (×10⁻¹⁸)")
    ax.set_title(f"Clock ratio vs tidal shift — segment {EXCLUDED_GROUP} excluded",
                 fontweight="bold")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "correlation_reanalysis_seg9_excluded.png",
                dpi=160, bbox_inches="tight")
    plt.close(fig)

    print(f"\nWrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'correlation_reanalysis_seg9_excluded.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
