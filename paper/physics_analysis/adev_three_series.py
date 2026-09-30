#!/usr/bin/env python3
"""ADEV of the Yb/Sr ratio for three concatenated series, on one figure.

The user asked for the (overlapping) Allan deviation of the Yb/Sr ratio, with
three curves on a single plot:

  1. "17 段选取后的有效数据"        -> the RAW valid data (no correction, A = 0)
  2. "潮汐修正的有效数据"           -> the tidal-CORRECTED valid data, using the
                                       MODEL tide (A = -1, i.e. the physical
                                       deltaW/c^2 template with unit response --
                                       NOT a fitted amplitude, NOT -0.54)
  3. "对应的潮汐修正数据连接成一个
      长数据系列"                   -> the MODEL tidal data itself, i.e. the
                                       fractional template h / F_1550 = deltaW/c^2
                                       (the model series that is SUBTRACTED from
                                       the raw beat), concatenated end-to-end

The model tide is the professional 30-s "综合差" deltaW (W(WUHN)-W(SHAO)),
converted to a fractional shift via deltaW/c^2 -- with NO fitted response
coefficient. The -0.54 amplitude in the wider repo is a *fitted diagnostic*
and is deliberately NOT used here.

All three series are built per segment through the SAME selection pipeline that
produces the published results (clock_ratio.tidal_analysis), then integrated
into ONE long series each: the per-segment samples are laid end-to-end on a
single synthetic 1-second axis (the calendar dead time between segments is
ignored, as is standard for concatenated-ADEV of a clock network with dead
time). This lets the Allan windows span the segment joins, so the curves reach
daily (and longer) averaging times -- unlike a gap-safe estimator, which would
stop at the longest single segment (~10 h).

Concatenated total: 1 008 912 s = 280.25 h -> tau up to ~70 h (T/4).

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
from clock_ratio.tidal_stability import continuous_runs, oadev  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
RAW = SCENARIOS[0]         # Scenario("raw",        Decimal("0"))   -- uncorrected
MODEL = SCENARIOS[1]       # Scenario("theory",     Decimal("-1"))  -- model tide

# tau grid for the pooled (long-series) curves: dyadic seconds plus fixed taus
# (10 min, 20 min, 1 h, 2 h, 12 h, 1--3 days) capped at longest_run // 4, the
# conventional maximum for a stable OADEV estimate.
FIXED_TAUS = (600, 1200, 3600, 7200, 43200, 86400, 172800, 259200)


def pooled_tau_grid(times: np.ndarray) -> tuple[int, ...]:
    longest = max(stop - start for start, stop in continuous_runs(times))
    maximum = longest // 4
    dyadic = {2**i for i in range(maximum.bit_length())} if maximum > 0 else set()
    tagged = {t for t in (86400, 172800, 259200, maximum) if 0 < t <= maximum}
    return tuple(sorted(dyadic | {t for t in FIXED_TAUS if t <= maximum} | tagged))


def build_series() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (times, raw_y, corrected_y, tide_y) as ONE concatenated series.

    Per-segment fractional series are laid end-to-end on a single synthetic
    1-second axis (calendar gaps ignored), so Allan windows may span the joins.
    """
    beat_t, beat_b = s.load_beat()
    segments = select_segments(beat_t, beat_b)
    tide_t, tide_w = s.load_tide()
    grid = TideGrid(tide_t, tide_w)

    all_raw, all_corr, all_tide = [], [], []
    for seg in segments:
        h = grid.beat_at(seg.times)                       # Hz, undemeaned MODEL template
        raw = analyze_segment(seg, h, RAW).fluctuations    # y = -q/(1+q), uncorrected
        corr = analyze_segment(seg, h, MODEL).fluctuations  # model tide removed (A=-1)
        tide_frac = h / s.F_1550                            # the MODEL tidal data itself
        all_raw.append(np.asarray(raw, dtype=float))
        all_corr.append(np.asarray(corr, dtype=float))
        all_tide.append(np.asarray(tide_frac, dtype=float))
    y_raw = np.concatenate(all_raw)
    y_corr = np.concatenate(all_corr)
    y_tide = np.concatenate(all_tide)
    t0 = np.datetime64("2026-06-29T00:00:00")
    times = t0 + np.arange(len(y_raw), dtype="int64").astype("timedelta64[s]")
    return times, y_raw, y_corr, y_tide


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
                          label="tidal-corrected valid data (model tide, $A=-1$)"),
        "tide":      dict(color="#4f8a3d", marker="^", ms=3.2, lw=1.3,
                          label="model tidal data, $\\Delta W/c^2$"),
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
