#!/usr/bin/env python3
"""Generate the report figures with datetime x-axes.

Reads results/professional_tidal_delta_30s.csv (the authoritative full tidal
"综合差" data) and writes report/fig1_timeseries_7d.png, report/fig2_spectrum.png,
report/fig3_full_68d.png and report/fig4_frequency_shift.png.
Time-domain x-axes are real datetimes formatted as ``YYYY-MM-DD HH:MM`` (UTC).
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "professional_tidal_delta_30s.csv"
)
OUT_DIR = Path(__file__).resolve().parent

TIDAL_COLUMN = "total_tidal_delta_m2_s2_surface"

C = 299792458.0  # speed of light (m/s)

# Dominant tidal constituents (frequency in Hz) for the spectrum annotations.
TIDES = {
    "M2": 1.405189e-4,
    "S2": 1.454441e-4,
    "N2": 1.378797e-4,
    "K1": 7.292116e-5,
    "O1": 6.759774e-5,
    "P1": 7.252295e-5,
}


def load() -> tuple[np.ndarray, np.ndarray]:
    rows = list(csv.DictReader(open(CSV_PATH)))
    timestamps = np.array(
        [r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]"
    )
    total = np.array([float(r[TIDAL_COLUMN]) for r in rows])
    return timestamps, total


def _style_time_axis(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")


def fig1(timestamps: np.ndarray, total: np.ndarray) -> None:
    mask = timestamps < timestamps[0] + np.timedelta64(7, "D")
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(timestamps[mask], total[mask], lw=0.4, color="#0969da")
    ax.set_ylabel("m²/s²")
    ax.set_title(
        "SHAO − WUHN full tidal difference (first 7 days)", fontweight="bold"
    )
    ax.grid(alpha=0.25)
    _style_time_axis(ax)
    ax.set_xlabel("Time (UTC)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig1_timeseries_7d.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig2(total: np.ndarray) -> None:
    dt = 30.0  # seconds, 30-second sampling

    def psd(y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        y = y - y.mean()
        window = np.hanning(len(y))
        power = np.abs(np.fft.rfft(y * window)) ** 2
        freq = np.fft.rfftfreq(len(y), d=dt)
        return freq, power

    fig, ax = plt.subplots(figsize=(10, 4.5))
    freq, power = psd(total)
    sel = freq < 5e-4
    ax.semilogy(freq[sel], power[sel], lw=0.8, label="total tidal difference", color="#d62728")
    for name, freq_tide in TIDES.items():
        ax.axvline(freq_tide, color="gray", ls=":", lw=0.6, alpha=0.5)
        ax.text(
            freq_tide, ax.get_ylim()[1] * 0.5, name, fontsize=7, rotation=90,
            va="top", color="gray",
        )
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (a.u.)")
    ax.set_title(
        "Spectrum of SHAO − WUHN full tidal difference", fontweight="bold"
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig2_spectrum.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig3(timestamps: np.ndarray, total: np.ndarray) -> None:
    days = len(total) // 2880  # 30-s samples per day
    daily = total[: days * 2880].reshape(days, 2880)
    day_starts = timestamps[: days * 2880 : 2880]

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(timestamps, total, lw=0.1, color="#0969da", alpha=0.7)
    ax.fill_between(
        day_starts, daily.min(axis=1), daily.max(axis=1),
        alpha=0.25, color="#0969da", label="daily min–max",
        step="mid",
    )
    ax.plot(day_starts, daily.mean(axis=1), lw=1.2, color="#d62728", label="daily mean")
    _style_time_axis(ax)
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("m²/s²")
    ax.set_title(
        "Full tidal difference — 83 days", fontweight="bold"
    )
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig3_full_68d.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig4(timestamps: np.ndarray, total: np.ndarray) -> None:
    frequency_shift = total / C**2  # Δf/f = ΔW/c² (dimensionless)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(timestamps, frequency_shift, lw=0.2, color="#0969da", alpha=0.8)
    _style_time_axis(ax)
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Δf / f")
    ax.set_title(
        "Clock frequency shift from tidal geopotential difference "
        "(general relativity, Δf/f = ΔW/c²)",
        fontweight="bold",
    )
    ax.grid(alpha=0.25)
    ax.ticklabel_format(style="sci", axis="y", scilimits=(-2, 2))
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig4_frequency_shift.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig5(timestamps: np.ndarray, total: np.ndarray) -> None:
    frequency_shift = total / C**2  # Δf/f (dimensionless)
    clock_offset = np.cumsum(frequency_shift) * 30.0  # Δτ = ∫(Δf/f)dt, seconds
    clock_offset_ps = clock_offset * 1e12  # picoseconds

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(timestamps, clock_offset_ps, lw=0.3, color="#0969da")
    _style_time_axis(ax)
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Clock offset Δτ (ps)")
    ax.set_title(
        "Clock offset from tidal geopotential difference "
        "(general relativity, Δτ = ∫ΔW/c² dt)",
        fontweight="bold",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig5_clock_offset.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    timestamps, total = load()
    fig1(timestamps, total)
    fig2(total)
    fig3(timestamps, total)
    fig4(timestamps, total)
    fig5(timestamps, total)
    print(
        "Wrote fig1_timeseries_7d.png, fig2_spectrum.png, "
        "fig3_full_68d.png, fig4_frequency_shift.png, fig5_clock_offset.png"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
