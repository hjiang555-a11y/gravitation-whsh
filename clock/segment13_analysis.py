#!/usr/bin/env python3
"""Segment 13 tidal-gravitational-redshift correlation analysis.

Reads the 1550 nm link beat frequency (FXE_B8, ~33.6 MHz) of the out-of-loop
clock comparison for segment 13 (2026-08-11 05:30 ~ 2026-08-13 00:00), applies
triangular (Bartlett) integration to suppress high-frequency noise, and
correlates against the tidal gravitational-redshift prediction.

No jump removal: segment 13 is itself jump-free (0 points deviate >10 Hz from
the median), so the data is used as-is.
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
DATA_DIR = CLOCK_DIR / "data" / "环外数据（第八列数据）"
RESULTS_CSV = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "wuhan_shanghai_20260620_20260826.csv"
)

C = 299792458.0  # m/s
# beat[Hz] -> clock fractional frequency Δf/f (from the MATLAB Dr formula).
COEF = 4.282082163269648e-15

# Beat timestamps are Beijing time (UTC+8, "PC time, time zone local"); the
# tidal CSV is UTC, so the 8 h offset is removed before interpolation.
UTC_OFFSET = np.timedelta64(8, "h")

SEGMENT_START = np.datetime64("2026-08-11 05:30:00")  # Beijing time
SEGMENT_END = np.datetime64("2026-08-13 00:00:00")    # Beijing time


def read_beat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    data = np.loadtxt(path, usecols=(0, 1, 10))
    date = data[:, 0].astype(int)
    time = data[:, 1]
    stamps = []
    for dd, tt in zip(date, time):
        yy, mm, day = dd // 10000, (dd // 100) % 100, dd % 100
        hh = int(tt) // 10000
        mi = (int(tt) // 100) % 100
        ss = int(tt) % 100
        stamps.append(f"{2000+yy:04d}-{mm:02d}-{day:02d} {hh:02d}:{mi:02d}:{ss:02d}")
    return np.array(stamps, dtype="datetime64[s]"), data[:, 2]


def load_segment() -> tuple[np.ndarray, np.ndarray]:
    parts = []
    for name in ("Freq_B_2_260811_1.txt", "Freq_B_2_260812_1.txt"):
        t, b = read_beat(DATA_DIR / name)
        parts.append((t, b))
    t = np.concatenate([p[0] for p in parts])
    b = np.concatenate([p[1] for p in parts])
    mask = (t >= SEGMENT_START) & (t < SEGMENT_END)
    return t[mask], b[mask]


def tidal_beat(t_stamps: np.ndarray) -> np.ndarray:
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    ts = np.array([r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]")
    tot = np.array([float(r["total_tidal_delta_m2_s2"]) for r in rows])
    t_sec = (ts - np.datetime64("1970-01-01")).astype(int)
    s_utc = t_stamps - UTC_OFFSET  # Beijing -> UTC
    s_sec = (s_utc - np.datetime64("1970-01-01")).astype(int)
    interp = np.interp(s_sec, t_sec, tot)
    return interp / C**2 / COEF  # Hz, beat-frequency tidal displacement


def triangular_integrate(x: np.ndarray, tau: int) -> np.ndarray:
    k = np.arange(-tau, tau + 1)
    tri = 1.0 - np.abs(k) / tau
    tri = tri / tri.sum()
    return np.convolve(x, tri, mode="same")


def decimate(x: np.ndarray, t: np.ndarray, step: int):
    return x[step // 2 :: step][: len(x) // step], t[step // 2 :: step][: len(t) // step]


def main() -> int:
    t, b = load_segment()
    dm = b - np.median(b)  # beat-frequency deviation, Hz
    tide = tidal_beat(t)

    # Jump-free check (no removal performed).
    jump_count = int(np.sum(np.abs(b - np.median(b)) > 10))
    print(f"Segment 13: {len(b)} points, {len(b)/3600:.1f} h")
    print(f"Jump check (>10 Hz): {jump_count} points (no removal)")
    print(f"Raw noise std: {dm.std():.4f} Hz")
    print(f"Tidal beat displacement: rms {tide.std():.3e} Hz, "
          f"peak-peak {tide.max()-tide.min():.3e} Hz")
    print()

    # Triangular integration at several tau, correlate at decimated grids.
    print(f"{'tau':>6s} {'noise std (Hz)':>15s} {'Pearson r':>11s} {'p':>9s} {'Spearman':>10s}")
    print("-" * 56)
    tau_list = [60, 300, 600, 1800, 3600]
    rows_out = []
    for tau in tau_list:
        sm = triangular_integrate(dm, tau)
        # decimate to independent samples every tau seconds
        d_sm, d_t = decimate(sm, t, tau)
        d_tide = tidal_beat(d_t)
        r, p = stats.pearsonr(d_sm, d_tide)
        rho, prho = stats.spearmanr(d_sm, d_tide)
        rows_out.append((tau, d_sm.std(), r, p, rho, prho, d_sm, d_t, d_tide))
        print(f"{tau:>6d} {d_sm.std():15.5f} {r:>+11.4f} {p:9.2e} {rho:>+10.4f}")

    # Plot: tau=600 s case (10-minute triangular integration)
    tau_plot = 600
    sm = triangular_integrate(dm, tau_plot)
    d_sm, d_t = decimate(sm, t, tau_plot)
    d_tide = tidal_beat(d_t)

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=False)
    # Panel 1: raw + smoothed beat
    ax = axes[0]
    ax.plot(t, dm, lw=0.15, color="#c0c0c0", label="raw (1 s)")
    ax.plot(t, sm, lw=0.5, color="#0969da", label=f"triangular τ={tau_plot}s")
    ax.set_ylabel("beat deviation (Hz)")
    ax.set_title("Segment 13 — 1550 nm link beat frequency", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    # Panel 2: decimated beat vs tidal (dual axis)
    ax = axes[1]
    ax.plot(d_t, d_sm, lw=0.8, color="#0969da", label="beat (10-min)")
    ax.set_ylabel("beat deviation (Hz)", color="#0969da")
    ax.tick_params(axis="y", labelcolor="#0969da")
    ax2 = ax.twinx()
    ax2.plot(d_t, d_tide, lw=1.2, color="#d62728", label="tidal prediction")
    ax2.set_ylabel("tidal beat shift (Hz)", color="#d62728")
    ax2.tick_params(axis="y", labelcolor="#d62728")
    ax.set_title("10-min triangular-integrated beat vs tidal prediction", fontweight="bold")
    ax.grid(alpha=0.25)
    fig.autofmt_xdate()

    # Panel 3: correlation scatter
    ax = axes[2]
    ax.scatter(d_tide, d_sm, s=8, color="#0969da", alpha=0.6)
    slope, intercept, rval, pval, _ = stats.linregress(d_tide, d_sm)
    xs = np.linspace(d_tide.min(), d_tide.max(), 50)
    ax.plot(xs, slope * xs + intercept, "r--", lw=1,
            label=f"OLS (r={rval:+.3f}, p={pval:.1e})")
    ax.set_xlabel("tidal beat shift (Hz)")
    ax.set_ylabel("beat deviation (Hz)")
    ax.set_title("Correlation scatter (10-min grid)", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    fig.tight_layout()
    fig.savefig(CLOCK_DIR / "segment13_correlation.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nWrote {CLOCK_DIR / 'segment13_correlation.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
