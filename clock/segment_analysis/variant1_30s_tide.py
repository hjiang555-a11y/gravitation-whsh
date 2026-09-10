#!/usr/bin/env python3
"""Variant 1: tidal data kept on its native 30-s grid (no 1-s interpolation).

Same 17-segment pipeline as batch_analysis.py, EXCEPT the tidal data is NOT
interpolated onto the beat's 1-s grid. Instead:
  - the beat is integrated with the original 1200-s triangular window (1200
    1-s samples per window, 600-s stride);
  - the tidal data is integrated on its NATIVE 30-s grid with the same 1200-s
    window expressed as 40 samples, 600-s stride as 20 samples;
  - the two series share the same window centres, so amplitude/correlation is
    still a fair comparison.

This isolates the effect of tidal integration granularity: original uses
linear interpolation of the 30-s tide onto 1-s; this variant uses the 30-s
grid directly.

Outputs (independent of batch_summary.csv):
  variant1_30s_tide_summary.csv, variant1_30s_tide_forest.png
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

CLOCK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CLOCK_DIR / "data" / "环外数据（第八列数据）"
RESULTS_CSV = (
    Path(__file__).resolve().parents[2]
    / "results"
    / "professional_tidal_delta_30s.csv"
)
TIDAL_COLUMN = "total_tidal_delta_m2_s2_surface"
OUT_DIR = Path(__file__).resolve().parent

C = 299792458.0
COEF = 4.282082163269648e-15
UTC_OFFSET = np.timedelta64(8, "h")

WINDOW = 1200  # s
STRIDE = 600   # s
JUMP_THRESHOLD = 10.0
TIDE_GRID = 30  # native tidal sampling (s)

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


def longest_valid_span(valid):
    if not valid.any():
        return None
    padded = np.concatenate([[False], valid, [False]])
    diff = np.diff(padded.astype(int))
    starts = np.where(diff == 1)[0]
    stops = np.where(diff == -1)[0]
    i = int(np.argmax(stops - starts))
    return int(starts[i]), int(stops[i] - 1)


def triangular(x, n_window, n_stride):
    k = np.arange(n_window)
    tri = 1.0 - np.abs(2 * k - (n_window - 1)) / (n_window + 1)
    tri = tri / tri.sum()
    if len(x) < n_window:
        return np.array([])
    n_out = (len(x) - n_window) // n_stride + 1
    out = np.empty(n_out)
    for i in range(n_out):
        s = i * n_stride
        out[i] = float(np.dot(tri, x[s : s + n_window]))
    return out


def fit_amplitude(beat, tide):
    b = beat - beat.mean()
    t = tide - tide.mean()
    A = float(np.dot(t, b) / np.dot(t, t))
    resid = b - A * t
    dof = len(b) - 1
    sigma2 = float(np.dot(resid, resid) / dof)
    u_A = float(np.sqrt(sigma2 / np.dot(t, t)))
    r = float(np.corrcoef(beat, tide)[0, 1])
    p = float(stats.pearsonr(beat, tide).pvalue)
    return {"A": A, "u_A": u_A, "r": r, "p": p, "n": len(beat)}


def main():
    T, B = load_all_beat()
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    t_tide = np.array([r["timestamp_utc"].replace("Z", "") for r in rows],
                      dtype="datetime64[s]")
    tot = np.array([float(r[TIDAL_COLUMN]) for r in rows])
    t_tide_sec = (t_tide - np.datetime64("1970-01-01")).astype(int)

    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))

    # tidal grid: 30-s native, in seconds since epoch (UTC)
    results = []
    for idx, (s, e) in enumerate(GROUPS, 1):
        S = np.datetime64(s)
        E = np.datetime64(e)
        in_win = (T >= S) & (T < E)
        t_seg = T[in_win]
        b_seg = B[in_win]
        ex_seg = excl[in_win]
        if len(b_seg) == 0:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue
        med = np.median(b_seg[plausible])
        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        span = longest_valid_span(valid)
        if span is None:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue
        t_run = t_seg[span[0] : span[1] + 1]
        b_run = b_seg[span[0] : span[1] + 1]

        # Beat: 1-s triangular, 1200-s window / 600-s stride (as original).
        beat_norm = b_run - b_run.mean()
        beat_tri = triangular(beat_norm, WINDOW, STRIDE)
        if len(beat_tri) < 5:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan})
            continue

        # Tidal: NATIVE 30-s grid (no 1-s interpolation). Same 1200-s window /
        # 600-s stride expressed in 30-s samples: 40 / 20.
        t_run_s = (t_run - np.datetime64("1970-01-01")).astype(int)
        # align to the 30-s grid covering the run (UTC)
        t_utc_s = t_run_s - 8 * 3600
        lo = t_utc_s[0] - (t_utc_s[0] % TIDE_GRID)
        hi = t_utc_s[-1]
        grid = np.arange(lo, hi + 1, TIDE_GRID)
        tide_grid = np.interp(grid, t_tide_sec, tot) / C**2 / COEF
        tide_tri = triangular(tide_grid - tide_grid.mean(),
                              WINDOW // TIDE_GRID, STRIDE // TIDE_GRID)
        tide_tri = tide_tri[: len(beat_tri)]

        fit = fit_amplitude(beat_tri, tide_tri)
        results.append({
            "group": idx,
            "t_start": str(t_run[0]),
            "t_end": str(t_run[-1]),
            "hours": len(t_run) / 3600,
            "n_pts": len(beat_tri),
            "A": fit["A"],
            "u_A": fit["u_A"],
            "r": fit["r"],
            "p": fit["p"],
        })

    csv_path = OUT_DIR / "variant1_30s_tide_summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "t_start_beijing", "t_end_beijing", "hours",
                    "n_pts", "A", "u_A", "A_over_uA", "r", "p"])
        for r in results:
            if np.isnan(r["A"]):
                w.writerow([r["group"], "", "", "", "", "", "", "", "", ""])
            else:
                w.writerow([r["group"], r["t_start"], r["t_end"],
                            f"{r['hours']:.3f}", r["n_pts"],
                            f"{r['A']:.4f}", f"{r['u_A']:.4f}",
                            f"{r['A']/r['u_A']:.2f}", f"{r['r']:.4f}",
                            f"{r['p']:.4f}"])

    valid = [r for r in results if not np.isnan(r["A"])]
    if valid:
        fig, ax = plt.subplots(figsize=(10, 5))
        gs = np.array([r["group"] for r in valid], dtype=float)
        A = np.array([r["A"] for r in valid])
        uA = np.array([r["u_A"] for r in valid])
        ax.errorbar(gs, A, yerr=uA, fmt="o", ms=6, lw=1.2, capsize=4,
                    color="#d62728", zorder=3)
        ax.axhline(0.0, color="gray", lw=0.8, ls=":")
        ax.axhline(1.0, color="#2ca02c", lw=1.0, ls="--", label="A = +1")
        ax.set_xlabel("Segment index")
        ax.set_ylabel("Amplitude A")
        ax.set_title("Variant 1: tidal on native 30-s grid (no 1-s interp)",
                     fontweight="bold")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT_DIR / "variant1_30s_tide_forest.png", dpi=150,
                    bbox_inches="tight")
        plt.close(fig)

    _rs = np.array([r["r"] for r in valid])
    _ps = np.array([r["p"] for r in valid])
    _As = np.array([r["A"] for r in valid])
    _uAs = np.array([r["u_A"] for r in valid])
    neg = int((_rs < 0).sum())
    peps = np.clip(_ps, 1e-14, None)
    z_agn = np.sum(stats.norm.ppf(1 - peps / 2)) / np.sqrt(len(_rs))
    chi2 = -2 * np.sum(np.log(peps))
    fisher_p = stats.chi2.sf(chi2, 2 * len(_rs))
    w = 1.0 / _uAs**2
    Abar = float(np.sum(_As * w) / np.sum(w))
    uAbar = float(1.0 / np.sqrt(np.sum(w)))
    print("\n=== Variant 1 (tidal on native 30-s grid, no 1-s interp) ===")
    print(f"negative r segments: {neg}/{len(_rs)} (binomial p="
          f"{stats.binomtest(neg, len(_rs), 0.5).pvalue:.4f})")
    print(f"Stouffer |z| = {z_agn:.2f} (p = {2*stats.norm.cdf(-z_agn):.2e})")
    print(f"Fisher chi2 = {chi2:.1f} (df={2*len(_rs)}) p = {fisher_p:.2e}")
    print(f"amplitude A (1/uA^2) = {Abar:+.4f} +/- {uAbar:.4f} "
          f"({abs(Abar)/uAbar:.2f} sigma)")
    print(f"Wrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'variant1_30s_tide_forest.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
