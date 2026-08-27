#!/usr/bin/env python3
"""Generate the report figures with datetime x-axes.

Reads results/wuhan_shanghai_20260620_20260826.csv and writes
report/fig1_timeseries_7d.png, report/fig2_spectrum.png and
report/fig3_full_68d.png. Time-domain x-axes are real datetimes formatted
as ``YYYY-MM-DD HH:MM`` (UTC).
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

CSV_PATH = Path(__file__).resolve().parents[1] / "results" / "wuhan_shanghai_20260620_20260826.csv"
OUT_DIR = Path(__file__).resolve().parent

# Dominant tidal constituents (frequency in Hz) for the spectrum annotations.
TIDES = {
    "M2": 1.405189e-4,
    "S2": 1.454441e-4,
    "N2": 1.378797e-4,
    "K1": 7.292116e-5,
    "O1": 6.759774e-5,
    "P1": 7.252295e-5,
}


def load() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    rows = list(csv.DictReader(open(CSV_PATH)))
    timestamps = np.array(
        [r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]"
    )
    columns = (
        "tide_generating_delta_m2_s2",
        "solid_induced_delta_m2_s2",
        "solid_effective_delta_m2_s2",
        "ocean_loading_delta_m2_s2",
        "total_tidal_delta_m2_s2",
    )
    data = {c: np.array([float(r[c]) for r in rows]) for c in columns}
    return timestamps, data


def _style_time_axis(ax):
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")


def fig1(timestamps: np.ndarray, data: dict[str, np.ndarray]) -> None:
    mask = timestamps < timestamps[0] + np.timedelta64(7, "D")
    panels = (
        ("tide_generating_delta_m2_s2", "Tide-generating potential difference"),
        ("solid_induced_delta_m2_s2", "Solid induced potential (k·V)"),
        ("solid_effective_delta_m2_s2", "Solid effective potential ((1+k-h)·V)"),
        ("ocean_loading_delta_m2_s2", "Ocean-loading potential (-γ·δh)"),
        ("total_tidal_delta_m2_s2", "Total tidal potential difference"),
    )
    fig, axes = plt.subplots(5, 1, figsize=(10, 9), sharex=True)
    for ax, (column, label) in zip(axes, panels):
        ax.plot(timestamps[mask], data[column][mask], lw=0.4, color="#0969da")
        ax.set_ylabel("m²/s²")
        ax.set_title(label, loc="left", fontsize=9)
        ax.grid(alpha=0.25)
    _style_time_axis(axes[-1])
    axes[-1].set_xlabel("Time (UTC)")
    axes[0].set_title(
        "SHAO − WUHN tidal geopotential difference (first 7 days)", fontweight="bold"
    )
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig1_timeseries_7d.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig2(data: dict[str, np.ndarray]) -> None:
    dt = 60.0  # seconds, 1-minute sampling

    def psd(y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        y = y - y.mean()
        window = np.hanning(len(y))
        power = np.abs(np.fft.rfft(y * window)) ** 2
        freq = np.fft.rfftfreq(len(y), d=dt)
        return freq, power

    fig, ax = plt.subplots(figsize=(10, 4.5))
    series = (
        ("tide_generating_delta_m2_s2", "generating", "#888888"),
        ("solid_effective_delta_m2_s2", "solid effective", "#0969da"),
        ("ocean_loading_delta_m2_s2", "ocean loading", "#e07b00"),
        ("total_tidal_delta_m2_s2", "total", "#d62728"),
    )
    for column, label, color in series:
        freq, power = psd(data[column])
        sel = freq < 5e-4
        ax.semilogy(freq[sel], power[sel], lw=0.8, label=label, color=color, alpha=0.9)
    for name, freq in TIDES.items():
        ax.axvline(freq, color="gray", ls=":", lw=0.6, alpha=0.5)
        ax.text(
            freq, ax.get_ylim()[1] * 0.5, name, fontsize=7, rotation=90,
            va="top", color="gray",
        )
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Power (a.u.)")
    ax.set_title("Spectrum of SHAO − WUHN tidal geopotential difference", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, which="both")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig2_spectrum.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def fig3(timestamps: np.ndarray, data: dict[str, np.ndarray]) -> None:
    total = data["total_tidal_delta_m2_s2"]
    days = len(total) // 1440
    daily = total[: days * 1440].reshape(days, 1440)
    day_starts = timestamps[: days * 1440 : 1440]

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.plot(timestamps, total, lw=0.1, color="#0969da", alpha=0.7)
    ax.fill_between(
        day_starts, daily.min(axis=1), daily.max(axis=1),
        alpha=0.25, color="#0969da", label="daily min–max",
        step="mid",
    )
    ax.plot(
        day_starts, daily.mean(axis=1), lw=1.2, color="#d62728", label="daily mean"
    )
    _style_time_axis(ax)
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("m²/s²")
    ax.set_title("Total tidal potential difference — full 68 days", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "fig3_full_68d.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    timestamps, data = load()
    fig1(timestamps, data)
    fig2(data)
    fig3(timestamps, data)
    print("Wrote fig1_timeseries_7d.png, fig2_spectrum.png, fig3_full_68d.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
