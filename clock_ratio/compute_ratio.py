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
from pathlib import Path

import numpy as np

CLOCK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CLOCK_DIR / "clock" / "data" / "环外数据（第八列数据）"
OUT_DIR = Path(__file__).resolve().parent

C = 299792458.0
N1156 = 1295739
N1397 = 858456
N1550 = 773598
N1550_WH = 966996
FREF = 1e7
DIV20 = 20
B_YB = (5.3e-18) - (7e-18)  # -1.7e-18
DELTA_G = -3.116e-15
JUMP_THRESHOLD = 10.0

COEF1156 = (1.0 + B_YB) / 2.0

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


def clock_ratio(mean_dm, shift_a):
    coef1397 = (1.0 + shift_a) / 2.0
    den = coef1397 / N1397 * (N1550 + 7.0 / 25.0 + 1.0 / 25.0)
    dr = COEF1156 / N1156 * (mean_dm / FREF / DIV20) / den
    return dr


def main():
    T, B = load_all_beat()

    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))

    # global median m (as MATLAB line 434)
    data_clean = B.copy()
    data_clean[excl] = np.nan
    pl = (data_clean > 3e7) & (data_clean < 4e7)
    m = np.nanmedian(data_clean[pl])

    NN = N1550_WH + 26.0 / 20.0 + m / FREF / DIV20
    NN2 = N1550 + 8.0 / 25.0

    results = []
    for kk, (s, e) in enumerate(GROUPS):
        S = np.datetime64(s)
        E = np.datetime64(e)
        in_win = (T >= S) & (T < E)
        t_seg = T[in_win]
        b_seg = B[in_win]
        ex_seg = excl[in_win]

        if len(b_seg) == 0:
            results.append({"group": kk + 1, "R": np.nan})
            continue
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            results.append({"group": kk + 1, "R": np.nan})
            continue
        med = np.median(b_seg[plausible])
        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        span = longest_valid_span(valid)
        if span is None:
            results.append({"group": kk + 1, "R": np.nan})
            continue
        d_long = b_seg[span[0]: span[1] + 1]

        mean_dm = d_long.mean() - m
        shift_k = SHIFT_A[kk]
        coef1397 = (1.0 + shift_k) / 2.0
        den = coef1397 / N1397 * (N1550 + 7.0 / 25.0 + 1.0 / 25.0)
        dr = COEF1156 / N1156 * (mean_dm / FREF / DIV20) / den
        ratio_base = COEF1156 / N1156 * NN / (coef1397 / N1397 * NN2)
        sryb_raw = ratio_base + dr
        ybsr_raw = 1.0 / sryb_raw
        R = ybsr_raw * (1.0 + DELTA_G)

        results.append({
            "group": kk + 1,
            "t_start": str(t_seg[span[0]]),
            "t_end": str(t_seg[span[1]]),
            "n_valid": len(d_long),
            "mean_dm_hz": mean_dm,
            "dr": dr,
            "shift_a": shift_k,
            "R": R,
        })

    R_arr = np.array([r["R"] for r in results])
    ok = ~np.isnan(R_arr)
    R_ref = R_arr[ok][0]
    y_i = (R_arr / R_ref - 1.0) * 1e18

    csv_path = OUT_DIR / "ratio_17seg.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "group", "t_start_beijing", "t_end_beijing", "n_valid",
            "mean_dm_hz", "shift_a", "YbSr_R", "y_i_1e18",
        ])
        for i, r in enumerate(results):
            if np.isnan(r["R"]):
                w.writerow([r["group"], "", "", "", "", "", "", ""])
            else:
                w.writerow([
                    r["group"], r["t_start"], r["t_end"], r["n_valid"],
                    f"{r['mean_dm_hz']:.6f}", f"{r['shift_a']:.6e}",
                    f"{r['R']:.20f}", f"{y_i[i]:.6f}",
                ])

    print(f"{'组':>3} {'有效点':>7} {'mean_dm[Hz]':>13} {'shift_a':>12} "
          f"{'Yb/Sr R':>24} {'y_i(×1e-18)':>12}")
    for i, r in enumerate(results):
        if np.isnan(r["R"]):
            print(f"{r['group']:>3} (无数据)")
        else:
            print(f"{r['group']:>3} {r['n_valid']:>7} {r['mean_dm_hz']:>+13.4f} "
                  f"{r['shift_a']:>+12.3e} {r['R']:>24.18f} {y_i[i]:>+12.4f}")

    # summary CSV: R_ref, per-segment y_i, and the 14-segment cross-check against
    # the experiment's low-precision y_i (reference only, not used in the ratio).
    summary_path = OUT_DIR / "ratio_17seg_summary.csv"
    with summary_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["field", "value"])
        w.writerow(["R_ref", f"{R_ref:.20f}"])
        w.writerow(["WLS_YbSr_experiment", "1.2075070393433377213"])
        w.writerow(["note", "segment 9 y_i ~ -222e-18 due to a_SM=-8.925e-17 (MATLAB-source flagged placeholder)"])

    print(f"\nWrote {csv_path}")
    print(f"Wrote {summary_path}")
    print(f"R_ref (段1 Yb/Sr) = {R_ref:.20f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
