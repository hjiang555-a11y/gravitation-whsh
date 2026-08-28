#!/usr/bin/env python3
"""Segment 6 (jump-free) — 1200-s triangular window, one point every 600 s.

Same analysis as segment 13, applied to the jump-free segment 6 window.

Data coverage note: the official segment-6 window (Beijing 2026-07-04 19:30:46
~ 2026-07-05 10:00:00, 14.49 h) spans Freq_B_2_260704 + Freq_B_2_260705, but
Freq_B_2_260704_1.txt is not present in the repository. Only the latter half
(2026-07-04 23:59:55 ~ 2026-07-05 10:00:00, ~10 h) is available, taken from
Freq_B_2_260705_1.txt. That segment is jump-free (0 points deviate >10 Hz from
the median) and 1-s continuous.

The beat timestamps are Beijing time (UTC+8); the tidal CSV is UTC, so the 8 h
offset is removed before interpolation.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

DATA_DIR = (
    Path(__file__).resolve().parents[1] / "data" / "环外数据（第八列数据）"
)
RESULTS_CSV = (
    Path(__file__).resolve().parents[2] / "results" / "wuhan_shanghai_20260620_20260826.csv"
)
OUT_DIR = Path(__file__).resolve().parent

C = 299792458.0  # m/s
COEF = 4.282082163269648e-15  # beat[Hz] -> Δf/f (from the MATLAB Dr formula)

UTC_OFFSET = np.timedelta64(8, "h")

SEG_START = np.datetime64("2026-07-04 19:30:46")  # Beijing time
SEG_END = np.datetime64("2026-07-05 10:00:00")    # Beijing time

WINDOW = 1200  # triangular window full width (s)
STRIDE = 600   # one point every 600 s (50% overlap)


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
        stamps.append(f"{2000 + yy:04d}-{mm:02d}-{day:02d} {hh:02d}:{mi:02d}:{ss:02d}")
    return np.array(stamps, dtype="datetime64[s]"), data[:, 2]


def triangular_window(x: np.ndarray, window: int, stride: int) -> np.ndarray:
    k = np.arange(window)
    tri = 1.0 - np.abs(2 * k - (window - 1)) / (window + 1)
    tri = tri / tri.sum()
    n_out = (len(x) - window) // stride + 1
    out = np.empty(n_out)
    for i in range(n_out):
        start = i * stride
        out[i] = float(np.dot(tri, x[start : start + window]))
    return out


def tidal_prediction(t_stamps: np.ndarray) -> np.ndarray:
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    ts = np.array([r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]")
    tot = np.array([float(r["total_tidal_delta_m2_s2"]) for r in rows])
    t_sec = (ts - np.datetime64("1970-01-01")).astype(int)
    s_utc = t_stamps - UTC_OFFSET  # Beijing -> UTC
    s_sec = (s_utc - np.datetime64("1970-01-01")).astype(int)
    interp = np.interp(s_sec, t_sec, tot)
    return interp / C**2 / COEF  # beat Hz


def main() -> int:
    parts = []
    for name in ("Freq_B_2_260705_1.txt",):
        t, b = read_beat(DATA_DIR / name)
        parts.append((t, b))
    t = np.concatenate([p[0] for p in parts])
    b = np.concatenate([p[1] for p in parts])
    mask = (t >= SEG_START) & (t < SEG_END)
    t, b = t[mask], b[mask]

    print("=== Segment 6 (jump-free) tidal correlation ===")
    print(f"Official window (Beijing): {SEG_START} ~ {SEG_END}")
    print(f"Available data: {t[0]} ~ {t[-1]} ({len(b)/3600:.2f} h)")
    print(f"Missing head (no 260704 file): {((SEG_END - SEG_START).astype(int) - len(b))/3600:.2f} h")
    beat_norm = b - b.mean()
    jump = int(np.sum(np.abs(b - np.median(b)) > 10))
    print(f"Jump check (>10 Hz from median): {jump} points (none removed)")
    print(f"Raw 1-s noise std: {beat_norm.std():.4f} Hz")

    beat_tri = triangular_window(beat_norm, WINDOW, STRIDE)
    t_tri = t[WINDOW // 2 :: STRIDE][: len(beat_tri)]
    print(f"\n1200-s triangular window (600-s stride): {len(beat_tri)} points")
    print(f"Integrated beat std: {beat_tri.std():.5f} Hz")

    tide = tidal_prediction(t_tri)
    print(f"Tidal prediction (beat Hz): rms {tide.std():.3e}, peak-peak {tide.max()-tide.min():.3e}")

    A = float(np.dot(tide, beat_tri) / np.dot(tide, tide))
    resid = beat_tri - A * tide
    u_A = float(np.sqrt(np.dot(resid, resid) / (len(beat_tri) - 1) / np.dot(tide, tide)))

    beat_ff = beat_tri * COEF * 1e18
    tide_ff = tide * COEF * 1e18

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(t_tri, beat_ff, "o-", ms=4, lw=1.0, color="#0969da",
            label="measured beat (1200-s triangular, 600-s points)")
    ax.plot(t_tri, tide_ff, lw=1.6, color="#d62728",
            label="tidal prediction (A = +1)")
    ax.plot(t_tri, A * tide_ff, lw=1.4, color="#2ca02c", ls="--",
            label=f"fitted tidal (A = {A:+.2f})")
    ax.axhline(0.0, color="gray", lw=0.6, ls=":")
    ax.set_ylabel("Δf/f (×10⁻¹⁸)")
    ax.set_xlabel("Time (Beijing, UTC+8)")
    ax.set_title(
        f"Segment 6 — 1200-s triangular beat vs tidal redshift (shared axis, "
        f"A = {A:+.2f} ± {u_A:.2f})",
        fontweight="bold",
    )
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(alpha=0.25)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    fig.autofmt_xdate()

    fig.tight_layout()
    fig.savefig(OUT_DIR / "segment6_shared_axis.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nAmplitude fit: A = {A:+.3f} ± {u_A:.3f}")
    print(f"Tidal Δf/f: rms {tide_ff.std():.3f}×1e-18, peak-peak {(tide_ff.max()-tide_ff.min()):.3f}×1e-18")
    print(f"Wrote {OUT_DIR / 'segment6_shared_axis.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
