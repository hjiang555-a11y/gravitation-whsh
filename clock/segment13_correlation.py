#!/usr/bin/env python3
"""Segment 13 (jump-free) tidal-gravitational-redshift correlation analysis.

Correlates the 1550 nm out-of-loop link beat frequency (FXE_B8, ~33.6 MHz) of
the Wuhan-Shanghai clock comparison against the predicted tidal gravitational
redshift of the comparison.

Key corrections over earlier scripts:

1. Time base. The acquisition PC records "PC time, time zone local" — the
   experiment runs in China (UTC+8), so the printed beat timestamps are BEIJING
   time. The tidal prediction (results/*.csv) is UTC. We therefore convert the
   beat time to UTC by subtracting 8 h before correlating. (China has no DST,
   so the offset is a constant +8.)

2. Unit conversion. The MATLAB processing defines the beat-frequency-to-clock
   fractional-frequency coefficient as

       Dr = coef1156/N1156 * (dm / fref / div20) / den,
       coef1156 = (1 + b_Yb)/2,  b_Yb = 5.3e-18,  N1156 = 1295739,
       fref = 1e7,  div20 = 20,
       den = coef1397/N1397 * (N1550 + 7/25 + 1/25),
       coef1397 = (1 + shift_a)/2,  N1397 = 858456,  N1550 = 773598,

   giving  Δf/f = COEF * beat[Hz]  with  COEF = 4.282082163269648e-15.
   Hence the tidal fractional frequency Δf/f = ΔW/c² maps to a beat deviation

       beat[Hz] = (ΔW/c²) / COEF.

3. Amplitude fit. Besides Pearson/Spearman correlation, we fit the model

       beat_i = A * tide_i + noise_i

   and report A ± u_A. The gravitational prediction is DIRECTIONAL: if the
   tidal effect is fully present at the expected amplitude, A = +1. This is a
   stronger test than "correlation is nonzero", and is insensitive to the
   overall beat noise floor.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
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
OUT_DIR = CLOCK_DIR

C = 299792458.0  # m/s
COEF = 4.282082163269648e-15  # beat[Hz] -> Δf/f  (from the MATLAB processing)
UTC_OFFSET_H = 8  # data PC local time = UTC+8 (China Standard Time)

SEG_START = np.datetime64("2026-08-11 05:30:00")  # printed (Beijing) time
SEG_END = np.datetime64("2026-08-13 00:00:00")

TAU_LIST = [60, 300, 600, 1800, 3600]
TAU_PLOT = 600


def read_beat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Read (date, time, FXE_B8) and return (datetime64[s], beat Hz)."""
    data = np.loadtxt(path, usecols=(0, 1, 10))
    date = data[:, 0].astype(int)
    time = data[:, 1]
    stamps = []
    for dd, tt in zip(date, time):
        yy, mm, day = dd // 10000, (dd // 100) % 100, dd % 100
        hh = int(tt) // 10000
        mi = (int(tt) // 100) % 100
        ss = int(tt) % 100
        stamps.append(f"{2000 + yy:04d}-{mm:02d}-{day:02d} {hh:02d}:{mi:02d}:{ss:02d}")
    return np.array(stamps, dtype="datetime64[s]"), data[:, 2]


def load_segment() -> tuple[np.ndarray, np.ndarray]:
    parts = []
    for name in ("Freq_B_2_260811_1.txt", "Freq_B_2_260812_1.txt"):
        t, b = read_beat(DATA_DIR / name)
        parts.append((t, b))
    t = np.concatenate([p[0] for p in parts])
    b = np.concatenate([p[1] for p in parts])
    mask = (t >= SEG_START) & (t < SEG_END)
    return t[mask], b[mask]


def load_tidal() -> tuple[np.ndarray, np.ndarray]:
    """Tidal total ΔW (m²/s²) on UTC datetime64[s] grid."""
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    ts = np.array([r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]")
    tot = np.array([float(r["total_tidal_delta_m2_s2"]) for r in rows])
    return ts, tot


def to_utc(t_naive: np.ndarray) -> np.ndarray:
    """Convert printed (Beijing) time to UTC by subtracting UTC_OFFSET_H hours."""
    return t_naive - np.timedelta64(UTC_OFFSET_H * 3600, "s")


def tidal_beat(t_stamps_utc: np.ndarray, t_tide: np.ndarray, tot: np.ndarray) -> np.ndarray:
    """Tidal prediction in beat Hz at the given (UTC) timestamps."""
    t_sec = (t_tide - np.datetime64("1970-01-01")).astype(int)
    s_sec = (t_stamps_utc - np.datetime64("1970-01-01")).astype(int)
    dw = np.interp(s_sec, t_sec, tot)
    return dw / C**2 / COEF


def triangular_segment(x: np.ndarray, tau: int) -> np.ndarray:
    """Non-overlapping triangular (Bartlett) weighted means, one point per tau."""
    n_seg = len(x) // tau
    x = x[: n_seg * tau]
    k = np.arange(tau)
    tri = 1.0 - np.abs(2 * k - (tau - 1)) / (tau + 1)
    tri = tri / tri.sum()
    return (x.reshape(n_seg, tau) * tri).sum(axis=1)


def amplitude_fit(beat: np.ndarray, tide: np.ndarray) -> dict[str, float]:
    """Least-squares fit beat = A * tide + noise; return A, u_A, t-stat, R²."""
    A = float(np.dot(tide, beat) / np.dot(tide, tide))
    resid = beat - A * tide
    n = len(beat)
    dof = n - 1
    sigma2 = float(np.dot(resid, resid) / dof)
    u_A = float(np.sqrt(sigma2 / np.dot(tide, tide)))
    r = float(np.corrcoef(beat, tide)[0, 1])
    return {
        "A": A,
        "u_A": u_A,
        "t_stat": A / u_A,
        "r": r,
        "R2": r * r,
        "n": n,
    }


def lag_sweep(beat_utc: np.ndarray, dm: np.ndarray, t_tide: np.ndarray, tot: np.ndarray):
    """Sweep a tidal time shift to confirm the time base; A≈1 marks the true lag."""
    tau = TAU_PLOT
    d_sm = triangular_segment(dm, tau)
    t_sm = beat_utc[tau // 2 :: tau][: len(d_sm)]
    s_base = (t_sm - np.datetime64("1970-01-01")).astype(int)
    t_sec = (t_tide - np.datetime64("1970-01-01")).astype(int)
    print("\nLag sweep (tau=600 s) — A ≈ +1 at the correct time base:")
    print(f"{'lag_h':>6} {'A':>9} {'u_A':>8} {'r':>8} {'rho':>8}")
    for lag in range(-12, 1):
        s = (t_sm + np.timedelta64(lag * 3600, "s") - np.datetime64("1970-01-01")).astype(int)
        tide = np.interp(s, t_sec, tot) / C**2 / COEF
        r = float(np.corrcoef(d_sm, tide)[0, 1])
        rho = float(stats.spearmanr(d_sm, tide).statistic)
        fit = amplitude_fit(d_sm, tide)
        print(f"{lag:+6d} {fit['A']:+9.3f} {fit['u_A']:8.3f} {r:+8.4f} {rho:+8.4f}")


def main() -> int:
    t_naive, b = load_segment()
    t_utc = to_utc(t_naive)
    dm = b - np.median(b)  # beat deviation, Hz
    t_tide, tot = load_tidal()

    print("=== Segment 13 (jump-free) tidal correlation ===")
    print(f"Window (Beijing): {SEG_START} ~ {SEG_END}")
    print(f"Window (UTC):     {t_utc[0]} ~ {t_utc[-1]}")
    print(f"Points: {len(b)} ({len(b)/3600:.2f} h)")
    jump = int(np.sum(np.abs(b - np.median(b)) > 10))
    print(f"Jump check (>10 Hz from median): {jump} points (none removed)")
    print(f"Raw 1-s noise std: {dm.std():.4f} Hz")

    # Correct-alignment tidal template on the full 1-s grid.
    tide_1s = tidal_beat(t_utc, t_tide, tot)
    print(f"Tidal template: rms {tide_1s.std():.3e} Hz, "
          f"peak-peak {(tide_1s.max()-tide_1s.min()):.3e} Hz")

    # Correlation + amplitude fit at several integration times.
    print(f"\n{'tau':>6} {'noise std (Hz)':>15} {'r':>9} {'p':>9} "
          f"{'A':>9} {'u_A':>8} {'A/u_A':>8}")
    print("-" * 72)
    rows = []
    for tau in TAU_LIST:
        d_sm = triangular_segment(dm, tau)
        t_sm = t_utc[tau // 2 :: tau][: len(d_sm)]
        tide = tidal_beat(t_sm, t_tide, tot)
        r, p = stats.pearsonr(d_sm, tide)
        rho, prho = stats.spearmanr(d_sm, tide)
        fit = amplitude_fit(d_sm, tide)
        rows.append((tau, d_sm, t_sm, tide, r, p, rho, prho, fit))
        print(f"{tau:>6d} {d_sm.std():15.5f} {r:>+9.4f} {p:9.2e} "
              f"{fit['A']:+9.3f} {fit['u_A']:8.3f} {fit['t_stat']:+8.2f}")

    # Lag sweep to confirm time base.
    lag_sweep(t_utc, dm, t_tide, tot)

    # --- Plot at tau = 600 s ---
    tau = TAU_PLOT
    d_sm = triangular_segment(dm, tau)
    t_sm = t_utc[tau // 2 :: tau][: len(d_sm)]
    tide = tidal_beat(t_sm, t_tide, tot)
    fit = amplitude_fit(d_sm, tide)

    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    # Panel 1: raw + smoothed beat.
    ax = axes[0]
    ax.plot(t_utc, dm, lw=0.15, color="#c0c0c0", label="raw (1 s)")
    ax.plot(t_sm, d_sm, lw=1.0, color="#0969da", label=f"triangular τ={tau}s")
    ax.set_ylabel("beat deviation (Hz)")
    ax.set_title("Segment 13 — 1550 nm link beat frequency (jump-free)", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    # Panel 2: decimated beat vs tidal prediction (shared axis, same units).
    ax = axes[1]
    ax.plot(t_sm, d_sm, "o-", ms=4, lw=1.0, color="#0969da", label="measured beat")
    ax.plot(t_sm, tide, lw=1.4, color="#d62728", label="tidal prediction (A=1)")
    ax.set_ylabel("beat deviation (Hz)")
    ax.set_title(
        f"600-s points vs tidal prediction (A fit = {fit['A']:+.2f} ± {fit['u_A']:.2f})",
        fontweight="bold",
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    fig.autofmt_xdate()

    # Panel 3: correlation scatter + fit.
    ax = axes[2]
    ax.scatter(tide, d_sm, s=10, color="#0969da", alpha=0.6)
    xs = np.linspace(tide.min(), tide.max(), 50)
    ax.plot(xs, fit["A"] * xs, "r--", lw=1.2,
            label=f"fit A={fit['A']:+.2f} (r={fit['r']:+.3f})")
    ax.plot(xs, xs, "g:", lw=1.0, label="A=1 (full tidal amplitude)")
    ax.set_xlabel("tidal beat shift (Hz)")
    ax.set_ylabel("measured beat deviation (Hz)")
    ax.set_title("Correlation scatter (600-s grid)", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)

    fig.tight_layout()
    out = OUT_DIR / "segment13_correlation.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
