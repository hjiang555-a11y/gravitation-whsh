#!/usr/bin/env python3
"""Compute tidal clock-comparison shifts for the experimental sessions.

Reads the session time windows (from clock/潮汐修正后的比值计算.pdf, 17 segments),
averages the tidal geopotential difference ΔW over each session, and converts
it to the fractional frequency shift Δf/f = ΔW/c² induced by the tidal
gravitational redshift (general relativity).

Writes clock/clock_tidal_shift.csv and clock/clock_tidal_shift.png
(datetime x-axis).
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

# Expert-provided full tidal "综合差" (solid + ocean), 30-s grid (UTC).
RESULTS_CSV = (
    Path(__file__).resolve().parents[1]
    / "results"
    / "professional_tidal_delta_30s.csv"
)
TIDAL_COLUMN = "total_tidal_delta_m2_s2_surface"
OUT_DIR = Path(__file__).resolve().parent

C = 299792458.0  # speed of light (m/s)

# Table 1 of the PDF lists session times in Beijing time (UTC+8), matching the
# acquisition PCs ("PC time, time zone local"). The tidal CSV is UTC, so the
# session windows are shifted back 8 h before masking. (China has no DST.)
UTC_OFFSET = np.timedelta64(8, "h")

# 17 experimental sessions (start, end), Beijing time (UTC+8), 2026 — tables of
# clock/潮汐修正后的比值计算.pdf (17-jump-free-segment revision).
GROUPS = [
    ("2026-06-29 10:06:28", "2026-06-30 04:59:59"),
    ("2026-06-30 12:00:00", "2026-06-30 20:11:31"),
    ("2026-07-01 15:58:41", "2026-07-02 03:53:40"),
    ("2026-07-02 17:34:22", "2026-07-03 07:51:26"),
    ("2026-07-03 17:34:22", "2026-07-03 23:00:00"),
    ("2026-07-04 19:30:46", "2026-07-05 10:00:00"),
    ("2026-07-05 13:00:00", "2026-07-06 00:00:00"),
    ("2026-07-06 21:45:16", "2026-07-07 09:52:03"),
    ("2026-08-07 15:15:00", "2026-08-07 21:30:00"),
    ("2026-08-07 22:15:00", "2026-08-08 14:20:59"),
    ("2026-08-09 00:00:00", "2026-08-10 09:57:21"),
    ("2026-08-10 12:47:06", "2026-08-11 00:00:00"),
    ("2026-08-11 05:30:00", "2026-08-13 00:00:00"),
    ("2026-08-13 18:56:58", "2026-08-15 14:00:41"),
    ("2026-08-21 00:40:03", "2026-08-21 16:40:56"),
    ("2026-08-21 23:20:01", "2026-08-23 16:20:51"),
    ("2026-08-25 15:09:41", "2026-08-26 09:29:54"),
]


def load_series() -> tuple[np.ndarray, np.ndarray]:
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    timestamps = np.array(
        [r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]"
    )
    total = np.array([float(r[TIDAL_COLUMN]) for r in rows])
    return timestamps, total


def main() -> int:
    timestamps, total = load_series()

    records = []
    for index, (start, end) in enumerate(GROUPS, 1):
        start_beijing = np.datetime64(start)
        end_beijing = np.datetime64(end)
        # 潮汐 CSV 是 UTC，把北京时窗口减 8h 对齐到 UTC 后再取潮汐均值。
        s_utc = start_beijing - UTC_OFFSET
        e_utc = end_beijing - UTC_OFFSET
        mask = (timestamps >= s_utc) & (timestamps <= e_utc)
        count = int(mask.sum())
        mean_w = float(total[mask].mean())
        frequency_shift = mean_w / C**2  # Δf/f (dimensionless)
        mid = int((int(start_beijing.astype("int64")) + int(end_beijing.astype("int64"))) // 2)
        midpoint = np.datetime64(mid, "s")
        records.append(
            {
                "session": index,
                "start": str(start_beijing).replace("T", " "),
                "end": str(end_beijing).replace("T", " "),
                "midpoint": midpoint,
                "count_minutes": count,
                "mean_delta_w_m2_s2": mean_w,
                "frequency_shift": frequency_shift,
            }
        )

    # Write CSV（时间统一按北京时间 UTC+8 呈现）
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / "clock_tidal_shift.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "session",
                "start_beijing_utc8",
                "end_beijing_utc8",
                "midpoint_beijing_utc8",
                "count_minutes",
                "mean_delta_w_m2_s2",
                "frequency_shift_dff",
            ]
        )
        for r in records:
            writer.writerow(
                [
                    r["session"],
                    r["start"],
                    r["end"],
                    np.datetime_as_string(r["midpoint"], unit="s"),
                    r["count_minutes"],
                    f"{r['mean_delta_w_m2_s2']:.9f}",
                    f"{r['frequency_shift']:.12e}",
                ]
            )

    midpoints = np.array([r["midpoint"] for r in records])
    frequency_shift = np.array([r["frequency_shift"] for r in records]) * 1e18

    # x 轴用等间距段索引，避免 7月→8月 约 31 天空档把前后段挤在两端、
    # 使序号标注重叠。每段中点日期用「月-日」短格式标作刻度，避免 17 个
    # 完整日期标签（YYYY-MM-DD）在横轴上挤成一团。
    seg_index = np.arange(1, len(records) + 1, dtype=float)
    xtick_dates = [str(m)[5:10] for m in midpoints]

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.axhline(0.0, color="gray", lw=0.8, ls="--")
    ax.plot(seg_index, frequency_shift, "o-", color="#0969da", ms=6, lw=1.4)
    for i in range(len(seg_index)):
        ax.annotate(
            f"{i + 1}", (seg_index[i], frequency_shift[i]),
            textcoords="offset points", xytext=(0, 9),
            ha="center", fontsize=8, color="#d62728", fontweight="bold",
        )
    ax.set_xticks(seg_index)
    ax.set_xticklabels(xtick_dates, rotation=45, ha="right", fontsize=8)
    ax.set_xlabel("Segment midpoint date (Beijing, UTC+8)")
    ax.set_ylabel("Tidal clock-comparison shift  Δf/f  (×10⁻¹⁸)")
    ax.set_title(
        "Tidal gravitational-redshift shift of the Yb/Sr clock comparison "
        f"per session ({len(records)} sessions)",
        fontweight="bold",
    )
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "clock_tidal_shift.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'clock_tidal_shift.png'}")
    print()
    print(f"{'session':>7} {'midpoint':>17} {'Δf/f ×1e18':>12}")
    for r in records:
        print(
            f"{r['session']:>7} "
            f"{np.datetime_as_string(r['midpoint'], unit='D'):>17} "
            f"{r['frequency_shift'] * 1e18:>+12.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
