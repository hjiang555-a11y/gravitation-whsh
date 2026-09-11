#!/usr/bin/env python3
"""17-segment clock-ratio (Yb/Sr) computation from the beat frequency.

Uses ONLY the valid (jump-free) data of each segment: drop points deviating
>10 Hz from the median, mask manual exclude_ranges, then keep the LONGEST
1-s continuous run (same as batch_analysis.py and the MATLAB convention).

Replicates the MATLAB per-bin ratio formula (YbSr_NISTstyle_14bin, lines
2234-2256):

    mean_dm_long = mean(d_long - m)                 # beat deviation [Hz]
    coef1397_k   = (1 + shift_a_k)/2
    den_k        = coef1397_k / N1397 * (N1550 + 7/25 + 1/25)
    Dr_long      = coef1156/N1156 * (mean_dm_long / fref / div20) / den_k
    ratio_base_k = coef1156/N1156 * NN / (coef1397_k/N1397 * NN2)
    SrYb_raw     = ratio_base_k + Dr_long
    YbSr_raw     = 1 / SrYb_raw
    R_bin_YbSr   = YbSr_raw * (1 + delta_g)

Outputs: clock_ratio/ratio_17seg.csv, clock_ratio/ratio_17seg_summary.csv
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.shared import (  # noqa: E402
    COEF1156, DELTA_G, DIV20, EXCLUDE_RANGES, FREF, GROUPS,
    JUMP_THRESHOLD, N1156, N1397, N1550, N1550_WH, SHIFT_A,
    D_7_25, D_1_25, load_beat, longest_valid_span, to_dec,
)

# The ratio R ~ 1.2 and the segment-to-segment differences are ~1-5e-18; kept in
# decimal 80-digit arithmetic (set in clock.shared) to match MATLAB's vpa(...,80).
getcontext().prec = 80

OUT_DIR = Path(__file__).resolve().parent


def endpoint_screen(x):
    """Trim both ends of a jump-free run per the PDF rule.

    A point is dropped when its distance from the run's centre exceeds 1% of
    the run's peak-to-peak; the check then continues to the next/previous
    point. Returns (trimmed_x, n_removed_start, n_removed_end).
    """
    center = np.median(x)
    peak2peak = x.max() - x.min()
    thr = peak2peak * 0.01

    lo, hi = 0, len(x) - 1
    n_start = 0
    while lo <= hi and abs(x[lo] - center) > thr:
        lo += 1
        n_start += 1
    n_end = 0
    while hi >= lo and abs(x[hi] - center) > thr:
        hi -= 1
        n_end += 1
    return x[lo: hi + 1], n_start, n_end


def full_ratio(mean_dm_dec, shift_dec, m_dec):
    coef1397 = (Decimal(1) + shift_dec) / Decimal(2)
    den = coef1397 / N1397 * (N1550 + D_7_25 + D_1_25)
    dr = COEF1156 / N1156 * (mean_dm_dec / FREF / DIV20) / den
    NN = N1550_WH + Decimal(26) / Decimal(20) + m_dec / FREF / DIV20
    NN2 = N1550 + Decimal(8) / Decimal(25)
    ratio_base = COEF1156 / N1156 * NN / (coef1397 / N1397 * NN2)
    sryb_raw = ratio_base + dr
    ybsr_raw = Decimal(1) / sryb_raw
    return ybsr_raw * (Decimal(1) + DELTA_G)


def main():
    T, B = load_beat()

    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))

    # global median m (as MATLAB line 434)
    data_clean = B.copy()
    data_clean[excl] = np.nan
    pl = (data_clean > 3e7) & (data_clean < 4e7)
    m = float(np.nanmedian(data_clean[pl]))
    m_dec = to_dec(m)

    results = []
    for kk, (s, e) in enumerate(GROUPS):
        S = np.datetime64(s)
        E = np.datetime64(e)
        in_win = (T >= S) & (T < E)
        t_seg = T[in_win]
        b_seg = B[in_win]
        ex_seg = excl[in_win]

        if len(b_seg) == 0:
            results.append({"group": kk + 1, "R": None, "R_str": "nan"})
            continue
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            results.append({"group": kk + 1, "R": None, "R_str": "nan"})
            continue
        med = float(np.median(b_seg[plausible]))
        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        span = longest_valid_span(valid)
        if span is None:
            results.append({"group": kk + 1, "R": None, "R_str": "nan"})
            continue
        d_long = b_seg[span[0]: span[1] + 1]

        d_long, rem_start, rem_end = endpoint_screen(d_long)
        if len(d_long) == 0:
            results.append({"group": kk + 1, "R": None, "R_str": "nan"})
            continue

        mean_dm = float(d_long.mean() - m)
        shift_k = SHIFT_A[kk]
        mean_dm_dec = to_dec(d_long.mean()) - m_dec
        shift_dec = to_dec(shift_k)
        R = full_ratio(mean_dm_dec, shift_dec, m_dec)

        results.append({
            "group": kk + 1,
            "t_start": str(t_seg[span[0]]),
            "t_end": str(t_seg[span[1]]),
            "n_valid": len(d_long),
            "rem_start": rem_start,
            "rem_end": rem_end,
            "mean_dm_hz": mean_dm,
            "shift_a": shift_k,
            "R": R,
            "R_str": str(R),
        })

    valid_R = [r["R"] for r in results if r["R"] is not None]
    R_ref = valid_R[0]
    y_i = [(r["R"] / R_ref - Decimal(1)) * Decimal("1e18")
           if r["R"] is not None else None for r in results]

    # Whole-experiment value (distinct from R_ref = segment 1): the 17-segment
    # duration-weighted mean, R_wls = Σ(n_valid_i · R_i) / Σ n_valid_i.
    ns = [Decimal(r["n_valid"]) for r in results if r["R"] is not None]
    total_n = sum(ns)
    R_wls = sum((n_i * r["R"]) for n_i, r in
                ((Decimal(r["n_valid"]), r) for r in results if r["R"] is not None)) / total_n
    y_wls = (R_wls / R_ref - Decimal(1)) * Decimal("1e18")

    csv_path = OUT_DIR / "ratio_17seg.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "group", "t_start_beijing", "t_end_beijing", "n_valid",
            "rem_start", "rem_end", "mean_dm_hz", "shift_a", "YbSr_R", "y_i_1e18",
        ])
        for i, r in enumerate(results):
            if r["R"] is None:
                w.writerow([r["group"], "", "", "", "", "", "", "", "", ""])
            else:
                w.writerow([
                    r["group"], r["t_start"], r["t_end"], r["n_valid"],
                    r["rem_start"], r["rem_end"],
                    f"{r['mean_dm_hz']:.6f}", f"{r['shift_a']:.6e}",
                    r["R_str"], format(y_i[i], ".7f"),
                ])

    print(f"{'组':>3} {'有效点':>7} {'削起/终':>9} {'mean_dm[Hz]':>13} {'shift_a':>12} "
          f"{'Yb/Sr R':>24} {'y_i(×1e-18)':>12}")
    for i, r in enumerate(results):
        if r["R"] is None:
            print(f"{r['group']:>3} (无数据)")
        else:
            print(f"{r['group']:>3} {r['n_valid']:>7} "
                  f"{r['rem_start']},{r['rem_end']:>2} {r['mean_dm_hz']:>+13.4f} "
                  f"{r['shift_a']:>+12.3e} {r['R_str'][:24]:>24} {y_i[i]:>+12.5f}")

    summary_path = OUT_DIR / "ratio_17seg_summary.csv"
    with summary_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["field", "value"])
        w.writerow(["R_ref_segment1", str(R_ref)])
        w.writerow(["R_wls_17seg_weighted", str(R_wls)])
        w.writerow(["y_wls_1e18", format(y_wls, ".7f")])
        w.writerow(["NIST_reference", "1.2075070393433377230"])
        w.writerow(["WLS_experiment", "1.2075070393433377213"])
        w.writerow(["note", "R_ref is segment 1 (y_i baseline only); R_wls is the 17-segment duration-weighted experiment value; endpoint screening (1% peak-to-peak) applied; decimal 80-digit arithmetic"])

    print(f"\nWrote {csv_path}")
    print(f"Wrote {summary_path}")
    print(f"R_ref (段1，仅作 y_i 基准) = {R_ref}")
    print(f"R_wls (17段时长加权，整个实验值) = {R_wls}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
