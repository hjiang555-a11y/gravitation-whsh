#!/usr/bin/env python3
"""17-segment clock-ratio (Yb/Sr) computation from the retained beat samples."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Sequence

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.shared import load_beat, to_dec  # noqa: E402
from clock.sample_selection import DEFAULT_SELECTION_PLAN, SelectedSegment, select_segments  # noqa: E402
from clock_ratio.ratio_model import full_ratio  # noqa: E402

# The ratio R ~ 1.2 and the segment-to-segment differences are ~1-5e-18; kept in
# decimal 80-digit arithmetic (set in clock.shared) to match MATLAB's vpa(...,80).
getcontext().prec = 80

OUT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True, slots=True)
class RatioRow:
    group: int
    ratio: Decimal
    n_valid: int
    t_start: str
    t_end: str
    rem_start: int
    rem_end: int


def load_selected_segments() -> tuple[SelectedSegment, ...]:
    """Load the shared retained segments used by all clock-ratio callers."""
    return select_segments(*load_beat(), DEFAULT_SELECTION_PLAN)


def compute_ratio_rows(segments: Sequence[SelectedSegment]) -> tuple[RatioRow, ...]:
    return tuple(
        RatioRow(
            group=segment.group,
            ratio=full_ratio(to_dec(float(np.mean(segment.beat))) - segment.m_dec,
                             segment.shift_a,
                             segment.m_dec),
            n_valid=len(segment.beat),
            t_start=str(segment.times[0]),
            t_end=str(segment.times[-1]),
            rem_start=segment.rem_start,
            rem_end=segment.rem_end,
        )
        for segment in segments
    )


def main() -> int:
    segments = load_selected_segments()
    rows = compute_ratio_rows(segments)

    valid_r = [row.ratio for row in rows]
    r_ref = valid_r[0]
    y_i = [(row.ratio / r_ref - Decimal(1)) * Decimal("1e18") for row in rows]

    total_n = sum(Decimal(row.n_valid) for row in rows)
    r_wls = sum(Decimal(row.n_valid) * row.ratio for row in rows) / total_n
    y_wls = (r_wls / r_ref - Decimal(1)) * Decimal("1e18")

    csv_path = OUT_DIR / "ratio_17seg.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "group", "t_start_beijing", "t_end_beijing", "n_valid",
            "rem_start", "rem_end", "mean_dm_hz", "shift_a", "YbSr_R", "y_i_1e18",
        ])
        for segment, row, y_value in zip(segments, rows, y_i, strict=True):
            mean_dm = float(np.mean(segment.beat)) - float(segment.m_dec)
            writer.writerow([
                row.group,
                row.t_start,
                row.t_end,
                row.n_valid,
                row.rem_start,
                row.rem_end,
                f"{mean_dm:.6f}",
                f"{float(segment.shift_a):.6e}",
                str(row.ratio),
                format(y_value, ".7f"),
            ])

    print(f"{'组':>3} {'有效点':>7} {'削起/终':>9} {'mean_dm[Hz]':>13} {'shift_a':>12} "
          f"{'Yb/Sr R':>24} {'y_i(×1e-18)':>12}")
    for segment, row, y_value in zip(segments, rows, y_i, strict=True):
        mean_dm = float(np.mean(segment.beat)) - float(segment.m_dec)
        print(f"{row.group:>3} {row.n_valid:>7} "
              f"{row.rem_start},{row.rem_end:>2} {mean_dm:+13.4f} "
              f"{float(segment.shift_a):>+12.3e} {str(row.ratio)[:24]:>24} {y_value:>+12.5f}")

    summary_path = OUT_DIR / "ratio_17seg_summary.csv"
    with summary_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["field", "value"])
        writer.writerow(["R_seg1", str(r_ref)])
        writer.writerow(["R_duration", str(r_wls)])
        writer.writerow(["y_duration_1e18", format(y_wls, ".7f")])
        writer.writerow(["NIST_reference", "1.2075070393433377230"])
        writer.writerow(["WLS_experiment", "1.2075070393433377213"])
        writer.writerow(["note", "R_seg1 = segment-1 ratio (y_i baseline only); R_duration = 17-segment duration-weighted center; endpoint screening (1% peak-to-peak) applied; decimal 80-digit arithmetic"])

    print(f"\nWrote {csv_path}")
    print(f"Wrote {summary_path}")
    print(f"R_seg1 (段1，仅作 y_i 基准) = {r_ref}")
    print(f"R_duration (17段时长加权中心值) = {r_wls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
