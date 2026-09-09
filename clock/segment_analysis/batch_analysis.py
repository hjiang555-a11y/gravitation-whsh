#!/usr/bin/env python3
"""Batch tidal-gravitational-redshift analysis over all jump-free segments.

Replicates the MATLAB processing convention (YbSr_NISTstyle_14bin_full_analysis):
- The acquisition PC records "PC time, time zone local" (Beijing, UTC+8), but
  the per-sample timestamps carry ±1 s label jitter (dt=0 and dt=2 occur in
  equal numbers, so the net drift is 0). The MATLAB code IGNORES the file
  timestamps and rebuilds a uniform 1-s axis from a start anchor. We do the
  same: each file's axis is  first_stamp + arange(n) seconds.
- Manual exclude_ranges are masked to NaN (as in the MATLAB code).
- Points deviating >10 Hz from the median are dropped (jump removal).
- Within the remaining valid, 1-s continuous data, the LONGEST continuous run
  is kept (the "jump-free" trace the MATLAB code uses).
- A 1200-s triangular (Bartlett) window with 600-s stride integrates BOTH the
  beat AND the tidal prediction through the SAME window, so the two are projected
  onto a common time/scale grid (fair correlation; the tidal template is not
  point-sampled at window centres while the beat is window-averaged).
- The tidal prediction is the expert "综合差" (ΔW/c², UTC) interpolated to the
  1-s grid (Beijing -> UTC, −8 h) and converted to beat Hz via COEF.
- The amplitude A in  beat = A * tide + noise  is fitted (A=+1 means the tidal
  redshift appears at full expected amplitude).

Outputs: batch_summary.csv, batch_forest.png, batch_shared_axis.png.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

CLOCK_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = CLOCK_DIR / "data" / "环外数据（第八列数据）"
# Tidal template = the EXPERT-provided full tidal "综合差" (solid + ocean), on a
# 30-s grid (2026-06-20 .. 09-10 UTC). This is the authoritative sequence the
# professional supplied directly (results/professional_tidal_delta_30s.csv), NOT
# the mixed "project solid + expert ocean" series in wuhan_shanghai_*.csv.
RESULTS_CSV = (
    Path(__file__).resolve().parents[2]
    / "results"
    / "professional_tidal_delta_30s.csv"
)
TIDAL_COLUMN = "total_tidal_delta_m2_s2_surface"
OUT_DIR = Path(__file__).resolve().parent

C = 299792458.0
COEF = 4.282082163269648e-15  # beat[Hz] -> Δf/f
UTC_OFFSET = np.timedelta64(8, "h")  # Beijing -> UTC

WINDOW = 1200  # triangular window full width (s)
STRIDE = 600   # one point every 600 s (50% overlap)
JUMP_THRESHOLD = 10.0  # Hz

# 17 experimental sessions (Beijing time, UTC+8) — tables of
# clock/潮汐修正后的比值计算.pdf (the 17-jump-free-segment revision).
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

# Manual exclusion windows (Beijing time), copied from the MATLAB exclude_ranges.
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


def first_stamp(path: Path) -> np.datetime64:
    """Parse the first data line's timestamp into a datetime64[s] (Beijing time)."""
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


def load_all_beat() -> tuple[np.ndarray, np.ndarray]:
    """Uniform 1-s axis from each file's first stamp + row index (ignores jitter)."""
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


def longest_valid_span(valid: np.ndarray) -> tuple[int, int] | None:
    """Return (start, stop) inclusive indices of the longest run of True."""
    if not valid.any():
        return None
    padded = np.concatenate([[False], valid, [False]])
    diff = np.diff(padded.astype(int))
    starts = np.where(diff == 1)[0]
    stops = np.where(diff == -1)[0]  # exclusive (index after last True)
    lengths = stops - starts
    i = int(np.argmax(lengths))
    return int(starts[i]), int(stops[i] - 1)


def triangular_window(x: np.ndarray, window: int, stride: int) -> np.ndarray:
    k = np.arange(window)
    tri = 1.0 - np.abs(2 * k - (window - 1)) / (window + 1)
    tri = tri / tri.sum()
    if len(x) < window:
        return np.array([])
    n_out = (len(x) - window) // stride + 1
    out = np.empty(n_out)
    for i in range(n_out):
        start = i * stride
        out[i] = float(np.dot(tri, x[start : start + window]))
    return out


def tidal_beat(t_stamps_utc: np.ndarray, t_tide: np.ndarray, tot: np.ndarray) -> np.ndarray:
    t_sec = (t_tide - np.datetime64("1970-01-01")).astype(int)
    s_sec = (t_stamps_utc - np.datetime64("1970-01-01")).astype(int)
    dw = np.interp(s_sec, t_sec, tot)
    return dw / C**2 / COEF  # beat Hz


def fit_amplitude(beat: np.ndarray, tide: np.ndarray) -> dict[str, float]:
    # Demean BOTH: the beat is already mean-subtracted, and the tidal template
    # carries a non-zero session-mean (DC) that must be excluded too. Fitting
    # the demeaned pair is equivalent to fitting beat = A*tide + intercept, and
    # yields A = r * sigma_beat / sigma_tide (sign consistent with r).
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


def main() -> int:
    T, B = load_all_beat()
    rows = list(csv.DictReader(open(RESULTS_CSV)))
    t_tide = np.array([r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]")
    tot = np.array([float(r[TIDAL_COLUMN]) for r in rows])

    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))

    results = []
    print(f"{'g':>2} {'最长段起(北京)':<18} {'时长h':>6} {'跳点':>5} "
          f"{'积分点':>6} {'A':>8} {'u_A':>7} {'A/u_A':>7} {'r':>7} {'p':>8}")
    print("-" * 92)

    for idx, (s, e) in enumerate(GROUPS, 1):
        S = np.datetime64(s)
        E = np.datetime64(e)
        in_win = (T >= S) & (T < E)
        t_seg = T[in_win]
        b_seg = B[in_win]
        ex_seg = excl[in_win]

        if len(b_seg) == 0:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan, "note": "无数据"})
            print(f"{idx:>2} {'(无数据)':<18} {'—':>6}")
            continue

        # robust median over physically plausible beat values (excludes saturation)
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            results.append({"group": idx, "A": np.nan, "u_A": np.nan, "note": "无有效值"})
            print(f"{idx:>2} {'(无有效值)':<18} {'—':>6}")
            continue
        med = np.median(b_seg[plausible])

        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        n_jump = int(plausible.sum()) - int(valid.sum())

        span = longest_valid_span(valid)
        if span is None:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan, "note": "无连续段"})
            print(f"{idx:>2} {'(无连续段)':<18} {'—':>6}")
            continue
        t_run = t_seg[span[0] : span[1] + 1]
        b_run = b_seg[span[0] : span[1] + 1]

        beat_norm = b_run - b_run.mean()
        beat_tri = triangular_window(beat_norm, WINDOW, STRIDE)
        if len(beat_tri) < 5:
            results.append({"group": idx, "A": np.nan, "u_A": np.nan, "note": "过短"})
            print(f"{idx:>2} {str(t_run[0])[5:16]:<18} {len(b_run)/3600:>6.2f} "
                  f"{n_jump:>5} {'(过短)':>8}")
            continue

        # Tidal template projected through the SAME 1200-s triangular window as
        # the beat: build the 1-s tidal series over the same run, then integrate
        # with triangular_window so the tidal "measurement" shares the beat's
        # windowing (fair amplitude/r comparison, not centre-point sampling).
        tide_1s = tidal_beat(t_run - UTC_OFFSET, t_tide, tot)
        tide_tri = triangular_window(tide_1s - tide_1s.mean(), WINDOW, STRIDE)
        tide_tri = tide_tri[: len(beat_tri)]
        t_tri = t_run[WINDOW // 2 :: STRIDE][: len(beat_tri)]
        tide = tide_tri
        fit = fit_amplitude(beat_tri, tide)

        results.append({
            "group": idx,
            "t_start": str(t_run[0]),
            "t_end": str(t_run[-1]),
            "hours": len(b_run) / 3600,
            "n_jump": n_jump,
            "n_pts": len(beat_tri),
            "A": fit["A"],
            "u_A": fit["u_A"],
            "r": fit["r"],
            "p": fit["p"],
            "tide_rms": float(tide.std()),
            "noise_std": float(beat_tri.std()),
            "beat_tri": beat_tri,
            "t_tri": t_tri,
            "tide": tide,
        })

        print(f"{idx:>2} {str(t_run[0])[5:16]:<18} {len(b_run)/3600:>6.2f} {n_jump:>5} "
              f"{len(beat_tri):>6} {fit['A']:>+8.2f} {fit['u_A']:>7.2f} "
              f"{fit['A']/fit['u_A']:>+7.2f} {fit['r']:>+7.3f} {fit['p']:>8.3f}")

    # ---- summary CSV ----
    csv_path = OUT_DIR / "batch_summary.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "group", "t_start_beijing", "t_end_beijing", "hours",
            "n_jump", "n_pts", "A", "u_A", "A_over_uA", "r", "p",
            "tide_rms_hz", "noise_std_hz",
        ])
        for r in results:
            if np.isnan(r["A"]):
                w.writerow([r["group"], "", "", "", "", "", "", "", "", "", "", "", ""])
            else:
                w.writerow([
                    r["group"], r["t_start"], r["t_end"], f"{r['hours']:.3f}",
                    r["n_jump"], r["n_pts"],
                    f"{r['A']:.4f}", f"{r['u_A']:.4f}", f"{r['A']/r['u_A']:.2f}",
                    f"{r['r']:.4f}", f"{r['p']:.4f}",
                    f"{r['tide_rms']:.3e}", f"{r['noise_std']:.3e}",
                ])

    # ---- forest plot ----
    valid = [r for r in results if not np.isnan(r["A"])]
    if valid:
        fig, ax = plt.subplots(figsize=(10, 5))
        gs = np.array([r["group"] for r in valid], dtype=float)
        A = np.array([r["A"] for r in valid])
        uA = np.array([r["u_A"] for r in valid])
        ax.errorbar(gs, A, yerr=uA, fmt="o", ms=6, lw=1.2, capsize=4,
                    color="#0969da", zorder=3)
        ax.axhline(0.0, color="gray", lw=0.8, ls=":")
        ax.axhline(1.0, color="#d62728", lw=1.0, ls="--", label="A = +1 (full tidal)")
        ax.set_xlabel("Segment index")
        ax.set_ylabel("Amplitude fit A")
        ax.set_title(f"Tidal amplitude fit A ± u_A across {len(valid)} segments", fontweight="bold")
        ax.set_xticks(gs)
        ax.set_xticklabels([f"{int(g)}" for g in gs])
        ax.legend(fontsize=9)
        ax.grid(alpha=0.25)
        fig.tight_layout()
        fig.savefig(OUT_DIR / "batch_forest.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    # ---- combined shared-axis figure ----
    n_plot = len(valid)
    if n_plot:
        cols = 3
        rows = int(np.ceil(n_plot / cols))
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 6, rows * 3),
                                 sharex=False, squeeze=False)
        for ax, r in zip(axes.flat, valid):
            beat_ff = r["beat_tri"] * COEF * 1e18
            tide_ff = r["tide"] * COEF * 1e18
            t = r["t_tri"]
            ax.plot(t, beat_ff, "o-", ms=2, lw=0.8, color="#0969da", label="beat")
            ax.plot(t, tide_ff, lw=1.4, color="#d62728", label="tidal (A=+1)")
            ax.plot(t, r["A"] * tide_ff, lw=1.0, color="#2ca02c", ls="--",
                    label=f"fit A={r['A']:+.2f}")
            ax.axhline(0.0, color="gray", lw=0.5, ls=":")
            ax.set_title(f"Segment {r['group']} (A={r['A']:+.2f}±{r['u_A']:.2f})",
                         fontsize=9, fontweight="bold")
            ax.tick_params(labelsize=7)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
            ax.grid(alpha=0.2)
        for ax in axes.flat[n_plot:]:
            ax.set_visible(False)
        fig.suptitle("1200-s triangular beat vs tidal redshift (Δf/f ×10⁻¹⁸), all segments",
                     fontweight="bold")
        fig.text(0.5, 0.01, "Time (Beijing, UTC+8)", ha="center", fontsize=9)
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        fig.savefig(OUT_DIR / "batch_shared_axis.png", dpi=150, bbox_inches="tight")
        plt.close(fig)

    print(f"\nWrote {csv_path}")
    print(f"Wrote {OUT_DIR / 'batch_forest.png'}")
    print(f"Wrote {OUT_DIR / 'batch_shared_axis.png'}")

    # ---- cross-segment aggregation (reproducible headline statistics) ----
    # Combine the per-segment results into the sign-agnostic significance
    # figures cited throughout the reports: negative-segment count + binomial
    # test, Stouffer / Fisher combined p-values, Fisher-z weighted mean r, and
    # precision-weighted amplitude ratio A.
    _ok = [r for r in results if "r" in r and not np.isnan(r["r"])]
    _rs = np.array([r["r"] for r in _ok])
    _ps = np.array([r["p"] for r in _ok])
    _As = np.array([r["A"] for r in _ok])
    _uAs = np.array([r["u_A"] for r in _ok])
    _ns = np.array([r["n_pts"] for r in _ok])
    _p_eps = np.clip(_ps, 1e-14, None)  # guard log(0) for Fisher
    _neg = int((_rs < 0).sum())
    _binom_p = stats.binomtest(_neg, len(_rs), 0.5).pvalue
    _z_sign = np.array([stats.norm.ppf(1 - pp / 2) * np.sign(rr)
                        for rr, pp in zip(_rs, _ps)])
    # Sign-agnostic Stouffer: combine the two-sided |z| scores of each segment
    # (z_i = ppf(1 - p_i/2), always positive), summed and renormed by 1/sqrt(n).
    _z_agn = np.sum(stats.norm.ppf(1 - _ps / 2)) / np.sqrt(len(_rs))
    _chi2 = -2.0 * np.sum(np.log(_p_eps))
    _fisher_p = stats.chi2.sf(_chi2, 2 * len(_rs))
    _w = _ns - 3.0
    _rbar = float(np.tanh(np.sum(_w * np.arctanh(_rs)) / np.sum(_w)))
    _wg = 1.0 / _uAs**2
    _Abar = float(np.sum(_As * _wg) / np.sum(_wg))
    _uAbar = float(1.0 / np.sqrt(np.sum(_wg)))
    print(f"\n=== cross-segment aggregation ({len(_rs)} segments) ===")
    print(f"negative r segments : {_neg}/{len(_rs)}  (binomial two-sided p = {_binom_p:.4f})")
    print(f"Stouffer (sign)     : z = {np.sum(_z_sign)/np.sqrt(len(_rs)):+.2f}  "
          f"(p = {2*stats.norm.cdf(-abs(np.sum(_z_sign)/np.sqrt(len(_rs)))):.2e})")
    print(f"Stouffer (|z|)      : |z| = {_z_agn:.2f}  (p = {2*stats.norm.cdf(-_z_agn):.2e})")
    print(f"Fisher              : chi2 = {_chi2:.1f} (df={2*len(_rs)})  p = {_fisher_p:.2e}")
    print(f"Fisher-z weighted r : {_rbar:+.4f}")
    print(f"amplitude A (1/uA^2) : {_Abar:+.4f} +/- {_uAbar:.4f}  ({abs(_Abar)/_uAbar:.2f} sigma)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
