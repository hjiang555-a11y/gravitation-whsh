#!/usr/bin/env python3
"""ADEV of the Yb/Sr ratio for three concatenated series, on one figure.

The user asked for the (overlapping) Allan deviation of the Yb/Sr ratio, with
three curves on a single plot:

  1. "17 段选取后的有效数据"        -> the RAW valid data (tidal response A = 0)
  2. "潮汐修正的有效数据"           -> the tidal-CORRECTED valid data (A = -0.54,
                                       the historical empirical response coefficient)
  3. "对应的潮汐修正数据连接成一个
      长数据系列"                   -> the tidal-correction series itself,
                                       i.e. (-A) * h / F_1550  (the fractional
                                       template that is SUBTRACTED from the raw
                                       series), concatenated end-to-end

All three series are built per segment through the SAME selection pipeline that
produces the published results (clock_ratio.tidal_analysis), then concatenated
into one long series each. ADEV is computed with the repo's gap-safe estimator
(clock_ratio.tidal_stability.oadev): every non-1-second step (including repeated
timestamps and the inter-segment joins) BREAKS the series, so no averaging
window ever crosses a gap.

Units: fractional frequency (dimensionless); plotted as x 1e-18.

Outputs (paper/physics_analysis/):
  - adev_three_series.png / .pdf   the figure
  - adev_three_series.csv          tau, sigma_y for the three series

Run:  python paper/physics_analysis/adev_three_series.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from clock import shared as s                                    # noqa: E402
from clock_ratio.tidal_analysis import (                          # noqa: E402
    SCENARIOS, TideGrid, analyze_segment, select_segments,
)
from clock_ratio.tidal_stability import continuous_runs, oadev, tau_grid  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
EMPIRICAL = SCENARIOS[2]   # Scenario("empirical", Decimal("-0.54"))
RAW = SCENARIOS[0]         # Scenario("raw", Decimal("0"))

# tau grid for the pooled (long-series) curves: dyadic seconds + fixed taus,
# capped at longest_run//4, identical to the repo convention.
FIXED_TAUS = (600, 1200, 3600, 7200)


def pooled_tau_grid(times: np.ndarray) -> tuple[int, ...]:
    longest = max(stop - start for start, stop in continuous_runs(times))
    return tau_grid(longest)


def build_series() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (times, raw_y, corrected_y, tide_y) concatenated over 17 segments."""
    beat_t, beat_b = s.load_beat()
    segments = select_segments(beat_t, beat_b)
    tide_t, tide_w = s.load_tide()
    grid = TideGrid(tide_t, tide_w)

    all_t, all_raw, all_corr, all_tide = [], [], [], []
    coef = float(EMPIRICAL.coefficient)   # -0.54
    for seg in segments:
        h = grid.beat_at(seg.times)                       # Hz, undemeaned template
        raw = analyze_segment(seg, h, RAW).fluctuations    # y = -q/(1+q)
        corr = analyze_segment(seg, h, EMPIRICAL).fluctuations
        tide_frac = (-coef) * h / s.F_1550                 # the subtracted correction
        all_t.append(seg.times)
        all_raw.append(np.asarray(raw, dtype=float))
        all_corr.append(np.asarray(corr, dtype=float))
        all_tide.append(np.asarray(tide_frac, dtype=float))
    return (np.concatenate(all_t), np.concatenate(all_raw),
            np.concatenate(all_corr), np.concatenate(all_tide))


def main() -> int:
    times, y_raw, y_corr, y_tide = build_series()
    taus = pooled_tau_grid(times)

    curves: dict[str, np.ndarray] = {}
    for label, y in (("raw", y_raw), ("corrected", y_corr), ("tide", y_tide)):
        pts = {p.tau_s: p.sigma_y for p in oadev(times, y, taus)}
        curves[label] = np.array([np.nan if pts.get(t) is None else pts[t]
                                  for t in taus], dtype=float)

    tau_arr = np.array(taus, dtype=float)

    # --- CSV ---------------------------------------------------------------
    csv_path = OUT_DIR / "adev_three_series.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tau_s", "sigma_y_raw", "sigma_y_corrected", "sigma_y_tide"])
        for i, t in enumerate(taus):
            w.writerow([t, f"{curves['raw'][i]:.6e}", f"{curves['corrected'][i]:.6e}",
                        f"{curves['tide'][i]:.6e}"])

    # --- figure ------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "stix",
                         "axes.linewidth": 0.8})
    fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=300)

    styles = {
        "raw":       dict(color="#1f4e79", marker="o", ms=3.2, lw=1.3,
                          label="17 segments, raw valid data"),
        "corrected": dict(color="#c0504d", marker="s", ms=3.0, lw=1.3,
                          label="tidal-corrected valid data (A = -0.54)"),
        "tide":      dict(color="#4f8a3d", marker="^", ms=3.2, lw=1.3,
                          label="tidal-correction series, $-A\\,h/F_{1550}$"),
    }
    for key in ("raw", "corrected", "tide"):
        ax.loglog(tau_arr, curves[key] * 1e18, **styles[key])

    ax.set_xlabel(r"Averaging time $\tau$ (s)")
    ax.set_ylabel(r"Overlapping Allan deviation $\sigma_y(\tau)$  ($10^{-18}$)")
    ax.grid(True, which="both", ls=":", lw=0.5, alpha=0.6)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    fig.tight_layout()
    png, pdf = OUT_DIR / "adev_three_series.png", OUT_DIR / "adev_three_series.pdf"
    fig.savefig(png)
    fig.savefig(pdf)

    # --- console -----------------------------------------------------------
    print("=== ADEV of the Yb/Sr ratio: three concatenated series ===")
    print(f"segments=17  retained samples={len(times)}  "
          f"runs={len(continuous_runs(times))}")
    print(f"tau grid: {taus[0]} .. {taus[-1]} s ({len(taus)} points)")
    print()
    print(" tau(s)   sigma_raw     sigma_corr    sigma_tide    (x1e-18)")
    for i, t in enumerate(taus):
        print(f"{t:>7}  {curves['raw'][i]*1e18:>11.3f}  {curves['corrected'][i]*1e18:>11.3f}"
              f"  {curves['tide'][i]*1e18:>11.3f}")
    print()
    print(f"wrote {png.name}, {pdf.name}, {csv_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
