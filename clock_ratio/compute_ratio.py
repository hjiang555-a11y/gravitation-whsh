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
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np

# The ratio R ~ 1.2 and the segment-to-segment differences are ~1-5e-18, i.e. at
# the 16th-18th significant digit. float64 (eps ~2.2e-16, ~260e-18 absolute on
# R~1.2) destroys that signal, which the MATLAB source avoids via vpa(...,80).
# We mirror that with decimal arithmetic at 80 significant digits.
getcontext().prec = 80

CLOCK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CLOCK_DIR / "clock" / "data" / "环外数据（第八列数据）"
OUT_DIR = Path(__file__).resolve().parent

C = 299792458.0
JUMP_THRESHOLD = 10.0

# Ratio-formula constants, held in decimal (80-digit) arithmetic to match the
# MATLAB vpa(...,80) precision; the E-20-level segment differences survive only
# if every step of the chain stays above ~20 significant digits.
N1156 = Decimal(1295739)
N1397 = Decimal(858456)
N1550 = Decimal(773598)
N1550_WH = Decimal(966996)
FREF = Decimal("1e7")
DIV20 = Decimal(20)
B_YB = Decimal("5.3e-18") - Decimal("7e-18")  # -1.7e-18
DELTA_G = Decimal("-3.116e-15")
COEF1156 = (Decimal(1) + B_YB) / Decimal(2)
D_7_25 = Decimal(7) / Decimal(25)
D_1_25 = Decimal(1) / Decimal(25)

GROUPS = [
    ("2026-06-29 10:06:28", "2026-06-30 04:59:59"),
    ("2026-06-30 12:00:00", "2026-06-30 20:11:31"),
    ("2026-07-01 15:58:41", "2026-07-02 03:53:40"),
    ("2026-07-02 14:00:00", "2026-07-03 07:51:26"),
    ("2026-07-03 17:34:22", "2026-07-03 23:00:00"),
    ("2026-07-04 19:30:46", "2026-07-05 10:00:00"),
    ("2026-07-05 13:00:00", "2026-07-06 00:00:00"),
    ("2026-07-06 21:45:16", "2026-07-07 09:52:03"),
    ("2026-08-07 15:15:00", "2026-08-07 21:30:00"),
    ("2026-08-07 22:15:00", "2026-08-08 14:20:59"),
    ("2026-08-09 00:00:00", "2026-08-09 09:57:21"),
    ("2026-08-10 12:47:06", "2026-08-11 00:00:00"),
    ("2026-08-11 05:30:00", "2026-08-13 00:00:00"),
    ("2026-08-13 18:56:58", "2026-08-14 14:00:42"),
    ("2026-08-21 00:40:03", "2026-08-21 16:40:56"),
    ("2026-08-21 23:20:01", "2026-08-23 16:20:51"),
    ("2026-08-25 15:09:41", "2026-08-26 09:29:54"),
]
EXCLUDE_RANGES = [
    ("2026-06-30 05:00:00", "2026-06-30 12:00:00"),
    ("2026-06-30 20:30:00", "2026-07-01 14:00:00"),
    ("2026-07-02 08:00:00", "2026-07-02 14:00:00"),
    ("2026-07-03 12:00:00", "2026-07-03 16:20:00"),
    ("2026-07-03 23:00:00", "2026-07-04 01:20:00"),
    ("2026-07-05 10:00:00", "2026-07-05 13:00:00"),
    ("2026-07-06 00:00:00", "2026-07-06 20:00:00"),
    ("2026-08-07 21:30:01", "2026-08-07 22:14:59"),
    ("2026-08-08 18:00:01", "2026-08-08 23:59:59"),
    ("2026-08-10 01:00:01", "2026-08-10 11:59:59"),
    ("2026-08-11 00:00:01", "2026-08-11 05:29:59"),
    ("2026-08-13 00:00:01", "2026-08-13 03:29:59"),
]

# shift_a 14 segments = a_rou + a_AC + a_SM + a_air + a_BBR
A_ROU = [
    -2.3405897235204027e-19, -1.4762696609004877e-19, -2.447205229168124e-19,
    -2.8193721064244536e-19, -2.722072607303744e-19, -2.6646987912614174e-19,
    -2.530366977034812e-19, -2.334981365086871e-19,
    -3.532e-19, -3.532e-19, -3.532e-19, -3.422e-19, -3.422e-19, -3.422e-19,
]
A_AC = [7.44377658537123e-18] * 8 + [8.929e-18] * 6
A_SM = [
    -1.7854788394394161e-16, -1.786187875083559e-16, -1.7856555448119226e-16,
    -1.7848198533888947e-16, -1.7852307151852717e-16, -1.784782742736454e-16,
    -1.7827511036845825e-16, -1.782675356790445e-16, -8.925e-17, 0.0, 0.0, 0.0,
    0.0, 0.0,
]
A_AIR = [-6.7e-19] * 14
A_BBR = [0.0] * 14
SHIFT_A_14 = [A_ROU[i] + A_AC[i] + A_SM[i] + A_AIR[i] + A_BBR[i]
              for i in range(14)]
# 15/16/17 inherit the segment 12-14 constant shift
SHIFT_A = SHIFT_A_14 + [SHIFT_A_14[11]] * 3


def first_stamp(path):
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            tok = line.split()
            dd, tt = int(tok[0]), float(tok[1])
            yy, mm, day = dd // 10000, (dd // 100) % 100, dd % 100
            hh = int(tt) // 10000
            mi = (int(tt) // 100) % 100
            ss = int(tt) % 100
            return np.datetime64(f"{2000+yy:04d}-{mm:02d}-{day:02d} "
                                 f"{hh:02d}:{mi:02d}:{ss:02d}")


def longest_valid_span(valid):
    if not valid.any():
        return None
    padded = np.concatenate([[False], valid, [False]])
    diff = np.diff(padded.astype(int))
    starts = np.where(diff == 1)[0]
    stops = np.where(diff == -1)[0]
    i = int(np.argmax(stops - starts))
    return int(starts[i]), int(stops[i] - 1)


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


def load_all_beat():
    files = sorted(DATA_DIR.glob("Freq_B_2_2606*.txt")) + sorted(
        DATA_DIR.glob("Freq_B_2_2607*.txt")
    ) + sorted(DATA_DIR.glob("Freq_B_2_2608*.txt"))
    t_all, b_all = [], []
    for f in files:
        b = np.loadtxt(f, usecols=(10,))
        t0 = first_stamp(f)
        t = t0 + np.arange(len(b), dtype="int64").astype("timedelta64[s]")
        t_all.append(t)
        b_all.append(b)
    t = np.concatenate(t_all)
    b = np.concatenate(b_all)
    order = np.argsort(t.astype("int64"))
    return t[order], b[order]


def to_dec(x):
    return Decimal(repr(float(x)))


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
    T, B = load_all_beat()

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
        w.writerow(["R_ref", str(R_ref)])
        w.writerow(["WLS_YbSr_experiment", "1.2075070393433377213"])
        w.writerow(["note", "endpoint screening (1% peak-to-peak) applied; decimal 80-digit arithmetic"])

    print(f"\nWrote {csv_path}")
    print(f"Wrote {summary_path}")
    print(f"R_ref (段1 Yb/Sr) = {R_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
