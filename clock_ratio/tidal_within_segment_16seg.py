#!/usr/bin/env python3
"""Within-segment (1200-s window) tidal correlation for both tide models,
on the 16-segment (segment 9 excluded) audit primary.

The paper's Discussion needs the within-segment demeaned-waveform correlation
(number of sign-consistent segments and the precision-weighted amplitude) for
the same 16-segment membership as the reported ratio.  The historical
batch_analysis.py aggregates 17 segments, so this diagnostic recomputes the
aggregate with segment 9 dropped, for BOTH tide models:

  old model -- professional 30-s series (ETideLoad4.5), results/professional_tidal_delta_30s.csv
  new model -- European public model (DE421 + FES2022), results/comp_shanghai-wuhan-beijintime.csv

The per-segment fits reuse the exact batch_analysis processing chain
(1200-s historical triangular window, 600-s stride, demeaned pair fit,
non-overlapping windows for inference).  Output (diagnostic, outside the
audit layer):

  clock_ratio/tidal_within_segment_16seg.json
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.shared import F_1550, load_beat, load_tide  # noqa: E402
from clock.sample_selection import DEFAULT_SELECTION_PLAN, SelectedSegment, select_segments  # noqa: E402
from clock_ratio.tidal_analysis import TideGrid  # noqa: E402
from clock_ratio.tidal_new_model_compare import NewTideGrid, load_new_tide  # noqa: E402
from clock_ratio.windowing import fit_demeaned_amplitude, triangular_average  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "tidal_within_segment_16seg.json"

WINDOW = 1200
STRIDE = 600
EXCLUDED_GROUP = 9


@dataclass(frozen=True, slots=True)
class Aggregate:
    key: str
    n_segments: int
    negative_r_segments: int
    binomial_p: float
    stouffer_z_sign: float
    stouffer_p_sign: float
    fisher_p: float
    fisher_z_weighted_r: float
    amplitude: float
    amplitude_u: float
    amplitude_sigma: float


def triangular_window(x: np.ndarray) -> np.ndarray:
    if len(x) < WINDOW:
        return np.array([])
    return triangular_average(
        x, width=WINDOW, stride=STRIDE, scheme="historical-triangular")


def per_segment_fit(segment: SelectedSegment, tide_at) -> dict | None:
    """One segment through the batch_analysis chain; None if unfit.

    The template sign is corrected for the beat polarity, so a POSITIVE
    response amplitude A means the tidal redshift appears at the expected
    sign (the fitted amplitudes are positive; theory predicts A = +1).
    """
    t_run = segment.times
    b_run = segment.beat
    beat_norm = b_run - b_run.mean()
    beat_tri = triangular_window(beat_norm)
    if len(beat_tri) < 5:
        return None
    try:
        tide_1s = -tide_at(t_run)  # sign correction for the beat polarity
    except Exception:
        return None
    tide_tri = triangular_window(tide_1s - tide_1s.mean())
    tide_tri = tide_tri[: len(beat_tri)]
    if len(tide_tri) != len(beat_tri):
        return None
    beat_inference = None
    # inference windows: 1200-s non-overlapping, mirroring batch_analysis
    b_inf = triangular_average(
        beat_norm, width=WINDOW, stride=WINDOW, scheme="historical-triangular")
    t_inf = triangular_average(
        tide_1s - tide_1s.mean(), width=WINDOW, stride=WINDOW,
        scheme="historical-triangular")
    if len(b_inf) != len(t_inf):
        return None
    try:
        fit = fit_demeaned_amplitude(beat_tri, tide_tri, b_inf, t_inf)
    except ValueError:
        return None
    return {
        "group": segment.group,
        "A": fit.amplitude,
        "u_A": fit.uncertainty,
        "r": fit.pearson_r,
        "p": fit.pearson_p,
        "n_pts": len(beat_tri),
        "n_inference_pts": fit.n_inference,
    }


def aggregate_rows(rows: list[dict], key: str) -> Aggregate:
    _rs = np.array([r["r"] for r in rows])
    _ps = np.array([r["p"] for r in rows])
    _As = np.array([r["A"] for r in rows])
    _uAs = np.array([r["u_A"] for r in rows])
    _ns = np.array([r["n_pts"] for r in rows])
    _p_eps = np.clip(_ps, 1e-14, None)
    _pos = int((_rs > 0).sum())
    _binom_p = stats.binomtest(_pos, len(_rs), 0.5).pvalue
    _z_sign = np.array([stats.norm.ppf(1 - pp / 2) * np.sign(rr)
                        for rr, pp in zip(_rs, _ps)])
    _stouffer_z_sign = float(np.sum(_z_sign) / np.sqrt(len(_rs)))
    _stouffer_p_sign = float(2 * stats.norm.cdf(-abs(_stouffer_z_sign)))
    _chi2 = -2.0 * np.sum(np.log(_p_eps))
    _fisher_p = stats.chi2.sf(_chi2, 2 * len(_rs))
    _w = _ns - 3.0
    _rbar = float(np.tanh(np.sum(_w * np.arctanh(_rs)) / np.sum(_w)))
    _wg = 1.0 / _uAs**2
    _Abar = float(np.sum(_As * _wg) / np.sum(_wg))
    _uAbar = float(1.0 / np.sqrt(np.sum(_wg)))
    return Aggregate(
        key=key, n_segments=len(_rs), negative_r_segments=_pos,
        binomial_p=float(_binom_p),
        stouffer_z_sign=_stouffer_z_sign, stouffer_p_sign=_stouffer_p_sign,
        fisher_p=float(_fisher_p), fisher_z_weighted_r=_rbar,
        amplitude=_Abar, amplitude_u=_uAbar,
        amplitude_sigma=float(abs(_Abar) / _uAbar),
    )


def make_figure(document: dict, segments, old_grid: TideGrid) -> None:
    """Render Fig. 4 (Methods): (a) single-segment fit example,
    (b) per-segment response amplitudes for both tide models."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import gridspec

    # ---- panel (a): single-segment fit (segment 13, ETideLoad4.5 template;
    # same chain as the library segment13_triangular.py example) ----
    seg13 = next(seg for seg in segments if seg.group == 13)
    t_run = seg13.times
    b_run = seg13.beat
    beat_norm = b_run - b_run.mean()
    beat_tri = triangular_window(beat_norm)
    t_tri = t_run[WINDOW // 2 :: STRIDE][: len(beat_tri)]
    tide_1s = -old_grid.beat_at(t_run)  # sign correction for the beat polarity
    tide_tri = triangular_window(tide_1s - tide_1s.mean())[: len(beat_tri)]
    A13 = float(np.dot(tide_tri, beat_tri) / np.dot(tide_tri, tide_tri))
    resid13 = beat_tri - A13 * tide_tri
    dof13 = len(tide_tri) - 1
    uA13 = float(np.sqrt(np.dot(resid13, resid13) / dof13 / np.dot(tide_tri, tide_tri)))
    sig13 = abs(A13) / uA13
    beat_ff = beat_tri / F_1550 * 1e18
    tide_ff = tide_tri / F_1550 * 1e18
    t_hours = (t_tri - t_tri[0]) / np.timedelta64(1, "h")

    old_rows = document["models"]["old_etideload"]["per_segment"]
    new_rows = document["models"]["new_de421_fes2022"]["per_segment"]
    old_agg = document["models"]["old_etideload"]["aggregate"]
    new_agg = document["models"]["new_de421_fes2022"]["aggregate"]
    # x-axis: sequential index 1..16 (not the original group numbers,
    # which skip the excluded segment 9).
    pos = np.arange(len(old_rows))

    fig = plt.figure(figsize=(7.2, 6.8))
    gs = gridspec.GridSpec(2, 1, height_ratios=[1.15, 1.0], hspace=0.38)

    axa = fig.add_subplot(gs[0])
    axa.plot(t_hours, beat_ff, "o", ms=3.0, lw=0.6, color="#0969da",
             label="measured beat", zorder=3)
    axa.plot(t_hours, tide_ff, lw=1.5, color="#d62728",
             label="template, $A = +1$", zorder=2)
    axa.plot(t_hours, A13 * tide_ff, lw=1.3, ls="--", color="#2ca02c",
             label=f"fitted, $A = {A13:+.2f}$ ({sig13:.1f}$\\sigma$)", zorder=4)
    axa.axhline(0.0, color="gray", lw=0.6, ls=":")
    axa.set_xlabel("Time (h from segment start)", fontsize=9)
    axa.set_ylabel(r"$\Delta f/f$ ($10^{-18}$)", fontsize=9)
    axa.tick_params(labelsize=8)
    axa.legend(fontsize=8, frameon=False, loc="lower right")

    axb = fig.add_subplot(gs[1])
    axb.axhline(0.0, color="0.6", ls=":", lw=0.7, zorder=0)
    axb.axhline(1.0, color="k", ls="--", lw=0.9, zorder=1)
    axb.text(len(old_rows) - 1.6, 1.12, "expected $A = +1$", fontsize=8,
             ha="right", va="bottom")

    axb.errorbar(
        pos - 0.14,
        [r["A"] for r in old_rows],
        yerr=[r["u_A"] for r in old_rows],
        fmt="o", ms=4.0, lw=0.8, color="#1f5fa8", ecolor="#1f5fa8",
        capsize=2, label="ETideLoad4.5", zorder=3,
    )
    axb.errorbar(
        pos + 0.14,
        [r["A"] for r in new_rows],
        yerr=[r["u_A"] for r in new_rows],
        fmt="s", ms=3.6, lw=0.8, color="#e07b00", ecolor="#e07b00",
        capsize=2, label="DE421 + FES2022", zorder=3,
    )
    axb.axhline(old_agg["amplitude"], color="#1f5fa8", lw=1.4, alpha=0.75, zorder=2)
    axb.axhline(new_agg["amplitude"], color="#e07b00", lw=1.4, alpha=0.75, zorder=2)

    axb.set_xticks(pos)
    axb.set_xticklabels([str(i + 1) for i in pos], fontsize=8)
    axb.set_xlabel("Segment", fontsize=9)
    axb.set_ylabel("Response amplitude $A$", fontsize=9)
    axb.set_ylim(-2.0, 3.6)
    axb.tick_params(axis="y", labelsize=8)
    axb.legend(fontsize=8, frameon=False, loc="upper left")

    figs_dir = Path(__file__).resolve().parents[1] / "paper" / "rev2" / "figs"
    fig.savefig(figs_dir / "fig4_tidal_response.png", dpi=300,
                bbox_inches="tight")
    fig.savefig(figs_dir / "fig4_tidal_response.pdf", bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {figs_dir / 'fig4_tidal_response.png'} and .pdf")


def main() -> int:
    try:
        times, beat = load_beat()
    except (OSError, ValueError) as error:
        print(f"Error: raw beat data could not be loaded: {error}", file=sys.stderr)
        return 1
    segments = select_segments(times, beat, DEFAULT_SELECTION_PLAN)
    segments = tuple(seg for seg in segments if seg.group != EXCLUDED_GROUP)

    t_tide, tot = load_tide()
    old_grid = TideGrid(t_tide, tot)
    try:
        new_grid = load_new_tide()
    except (OSError, ValueError, KeyError) as error:
        print(f"Error: new tide model could not be loaded: {error}", file=sys.stderr)
        return 1

    document: dict = {
        "metadata": {
            "window_s": WINDOW,
            "stride_s": STRIDE,
            "excluded_group": EXCLUDED_GROUP,
            "note": "within-segment demeaned-waveform correlation on the 16-segment "
                    "audit primary, for the professional 30-s (ETideLoad4.5) and the "
                    "European 90-s (DE421+FES2022) tide models; diagnostic only",
        },
        "models": {},
    }

    for key, tide_at in (("old_etideload", old_grid.beat_at),
                         ("new_de421_fes2022", new_grid.beat_at)):
        rows: list[dict] = []
        for segment in segments:
            row = per_segment_fit(segment, tide_at)
            if row is not None:
                rows.append(row)
        agg = aggregate_rows(rows, key)
        document["models"][key] = {
            "aggregate": {
                "n_segments": agg.n_segments,
                "negative_r_segments": agg.negative_r_segments,
                "binomial_p": agg.binomial_p,
                "stouffer_z_sign": agg.stouffer_z_sign,
                "stouffer_p_sign": agg.stouffer_p_sign,
                "fisher_p": agg.fisher_p,
                "fisher_z_weighted_r": agg.fisher_z_weighted_r,
                "amplitude": agg.amplitude,
                "amplitude_u": agg.amplitude_u,
                "amplitude_sigma": agg.amplitude_sigma,
            },
            "per_segment": rows,
        }
        print(f"\n[{key}] {agg.n_segments} segments")
        print(f"  negative-r segments: {agg.negative_r_segments}/{agg.n_segments} "
              f"(binomial p = {agg.binomial_p:.4f})")
        print(f"  Stouffer (signed): z = {agg.stouffer_z_sign:+.2f} "
              f"(p = {agg.stouffer_p_sign:.2e})")
        print(f"  Fisher p = {agg.fisher_p:.2e}; Fisher-z weighted r = "
              f"{agg.fisher_z_weighted_r:+.4f}")
        print(f"  precision-weighted A = {agg.amplitude:+.4f} +/- {agg.amplitude_u:.4f} "
              f"({agg.amplitude_sigma:.2f} sigma)")

    JSON_PATH.write_text(json.dumps(document, indent=2, allow_nan=False),
                         encoding="utf-8")
    print(f"\nWrote {JSON_PATH}")
    make_figure(document, segments, old_grid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
