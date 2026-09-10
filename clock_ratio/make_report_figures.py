#!/usr/bin/env python3
"""Generate the report figures for the clock-ratio experiment report.

Figures:
  1. ratio_segments.png — 17-segment clock-ratio deviation y_i (×1e-18) vs
     segment, with the time-weighted grand mean and the segment midpoints.
  2. ratio_vs_tide.png — y_i against session tidal shift (copy of the
     correlation reanalysis figure, referenced by the report).

Both read the newest decimal-precision 17-segment ratios.
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = Path(__file__).resolve().parent
RATIO_CSV = OUT_DIR / "ratio_17seg.csv"
TIDE_CSV = OUT_DIR.parent / "clock" / "clock_tidal_shift.csv"


def load():
    rows = list(csv.DictReader(open(RATIO_CSV)))
    y_i = np.array([float(r["y_i_1e18"]) for r in rows])
    n_valid = np.array([int(r["n_valid"]) for r in rows])
    R = [Decimal(r["YbSr_R"]) for r in rows]
    starts = [r["t_start_beijing"] for r in rows]
    ends = [r["t_end_beijing"] for r in rows]
    tide = list(csv.DictReader(open(TIDE_CSV)))
    dff = np.array([float(r["frequency_shift_dff"]) for r in tide]) * 1e18
    return y_i, n_valid, R, starts, ends, dff


def midpoint_label(start, end):
    s = np.datetime64(start.replace("T", " "))
    e = np.datetime64(end.replace("T", " "))
    mid = s + (e - s) / 2
    return str(mid)[5:10]


def main() -> int:
    y_i, n_valid, R, starts, ends, dff = load()
    w = n_valid / n_valid.sum()
    mean_w = float(np.sum(w * y_i))

    # figure 1: per-segment ratio deviation
    fig, ax = plt.subplots(figsize=(12, 5.5))
    seg = np.arange(1, 18)
    colors = np.where(y_i >= 0, "#2ca02c", "#d62728")
    ax.bar(seg, y_i, color=colors, alpha=0.85, edgecolor="black", linewidth=0.4)
    ax.axhline(0, color="gray", lw=1)
    ax.axhline(mean_w, color="blue", lw=1.4, ls="--",
               label=f"time-weighted mean = {mean_w:+.3f} ×10⁻¹⁸")
    for i in range(17):
        ax.annotate(f"{y_i[i]:+.2f}", (seg[i], y_i[i]),
                    textcoords="offset points",
                    xytext=(0, 3 if y_i[i] >= 0 else -13),
                    ha="center", fontsize=7, color="#333333")
    ax.set_xticks(seg)
    labels = [midpoint_label(s, e) for s, e in zip(starts, ends)]
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Segment (midpoint date, Beijing UTC+8)")
    ax.set_ylabel("Clock-ratio deviation  y_i = R_i/R_ref − 1  (×10⁻¹⁸)")
    ax.set_title("17-segment Yb/Sr clock-ratio deviations (decimal 80-digit)",
                 fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "ratio_segments.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {OUT_DIR / 'ratio_segments.png'}")
    print(f"time-weighted grand mean = {mean_w:+.6f} ×1e-18")
    print(f"R_ref (segment 1) = {R[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
