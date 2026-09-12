#!/usr/bin/env python3
"""Paper-style statistical methods (WLS / Birge / Mandel-Paule / Bayesian) applied
to TIDAL-CORRECTED data, as a parallel result set that does NOT replace the raw
baseline in `statistical_methods.py`.

The three fixed-coefficient scenarios (raw A=0, theory A=-1, empirical A=-0.54,
identical to `tidal_correction.py`) are each propagated through the FULL
paper-style pipeline:

  1. Per segment: freeze the raw selection (windows, exclusions, jump filter,
     longest index span, endpoint screen) via `tidal_analysis.select_segments`.
  2. Corrected beat:  b_corr = b_raw - A*h,  h = F_1550 * dW/c^2 (undemeaned
     tidal template, interpolated from the 30-s grid).
  3. OADEV -> statistical uncertainty u_i:  overlapping Allan deviation of the
     CORRECTED beat fractional frequency, extrapolated 128s<=tau<=T/4 -> T
     (reusing `statistical_methods.oadev` / `extrapolate_u` so raw and corrected
     u_i are computed identically except for the applied template).
  4. Per-scenario ratio R_i,scenario and deviation y_i,scenario = R_i/R_seg1 - 1
     (same segment-1 baseline convention as the raw pipeline).
  5. Combine with WLS / Birge / M-P / Bayesian (same formulas as the raw case).

Outputs (independent, all under clock_ratio/):
  statistical_methods_tidal.json   (per-scenario combined values + metadata)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared as s  # noqa: E402
from clock_ratio.statistical_methods import extrapolate_u, oadev  # noqa: E402
from clock_ratio.tidal_analysis import (  # noqa: E402
    SCENARIOS, AnalysisError, Segment, TideGrid, analyze_segment, select_segments,
)

OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "statistical_methods_tidal.json"


def corrected_beat(segment: Segment, h: np.ndarray, coefficient: Decimal) -> np.ndarray:
    """b_corr = b_raw - A*h for a fixed response coefficient (A < 0 adds template)."""
    return segment.beat - float(coefficient) * h


def combine(yy: np.ndarray, u: np.ndarray) -> dict[str, float]:
    """WLS / Birge / Mandel-Paule / Bayesian on (y_i, u_i). Same math as statistical_methods."""
    w = 1.0 / u**2
    y_wls = float(np.sum(w * yy) / np.sum(w))
    u_wls = float(1.0 / np.sqrt(np.sum(w)))

    dof = len(yy) - 1
    chi2 = float(np.sum(((yy - y_wls) / u) ** 2))
    chi2_red = chi2 / dof
    p_chi2 = float(stats.chi2.sf(chi2, dof))
    birge = float(np.sqrt(chi2_red))
    u_birge = birge * u_wls

    def chi2_red_mp(xi: float) -> float:
        v = u**2 + xi**2
        ww = 1.0 / v
        yw = float(np.sum(ww * yy) / np.sum(ww))
        return float(np.sum(((yy - yw) / np.sqrt(v)) ** 2) / dof)

    lo, hi = 0.0, 1e-16
    for _ in range(200):
        mid = (lo + hi) / 2
        if chi2_red_mp(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    xi_mp = (lo + hi) / 2
    v = u**2 + xi_mp**2
    ww = 1.0 / v
    y_mp = float(np.sum(ww * yy) / np.sum(ww))
    u_mp = float(1.0 / np.sqrt(np.sum(ww)))

    xi_grid = np.geomspace(1e-20, 1e-16, 200)
    logpost = []
    for xi in xi_grid:
        var = u**2 + xi**2
        num = np.sum(yy / var)
        den = np.sum(1.0 / var)
        mu_hat = num / den
        logL = -0.5 * np.sum((yy - mu_hat) ** 2 / var + np.log(2 * np.pi * var))
        logpost.append(logL - np.log(xi))
    logpost = np.array(logpost) - np.array(logpost).max()
    post = np.exp(logpost)
    post /= post.sum()

    mu_samples = []
    for xi, p in zip(xi_grid, post):
        var = u**2 + xi**2
        mhat = np.sum(yy / var) / np.sum(1.0 / var)
        s2 = 1.0 / np.sum(1.0 / var)
        mu_samples.append((mhat, s2, p))
    mu_post_mean = float(np.sum([p * m for m, _s2, p in mu_samples]))
    mu_post_var = float(np.sum([p * (s2 + (m - mu_post_mean) ** 2) for m, s2, p in mu_samples]))
    mu_post_sd = float(np.sqrt(mu_post_var))
    xi_post_mean = float(np.sum(xi_grid * post))

    return {
        "y_wls": y_wls,
        "u_wls": u_wls,
        "chi2": chi2,
        "dof": dof,
        "chi2_red": chi2_red,
        "p_chi2": p_chi2,
        "birge_ratio": birge,
        "u_birge": u_birge,
        "xi_mp": xi_mp,
        "y_mp": y_mp,
        "u_mp": u_mp,
        "mu_bayes": mu_post_mean,
        "u_stat_bayes": mu_post_sd,
        "xi_bayes": xi_post_mean,
    }


def scenario_result(segments: tuple[Segment, ...], tide: TideGrid,
                    scenario, corrected_ratios: dict[int, Decimal]) -> dict:
    """Run the full paper-style pipeline for one fixed-coefficient scenario."""
    rows: list[dict] = []
    R_seg1 = corrected_ratios[1]
    for seg in segments:
        h = tide.beat_at(seg.times) if scenario.coefficient != 0 else np.zeros(len(seg.beat))
        b_corr = corrected_beat(seg, h, scenario.coefficient)
        frac = (b_corr - b_corr.mean()) / s.F_1550
        tau, sig = oadev(frac)
        sig_T = extrapolate_u(tau, sig, len(b_corr)) if len(tau) else np.nan
        Rg = corrected_ratios[seg.group]
        y_i = float((Rg / R_seg1 - Decimal(1)) * Decimal("1e18"))
        rows.append({
            "group": seg.group,
            "T_s": len(seg.beat),
            "u_frac": float(sig_T),
            "u_i": float(Decimal(repr(sig_T)) * Rg),
            "y_i_1e18": y_i,
        })

    u = np.array([r["u_i"] for r in rows])
    yy = np.array([r["y_i_1e18"] for r in rows]) * 1e-18
    comb = combine(yy, u)

    with localcontext() as ctx:
        ctx.prec = 80
        R0 = corrected_ratios[1]
        y_wls_d = Decimal(repr(comb["y_wls"]))
        y_mp_d = Decimal(repr(comb["y_mp"]))
        mu_d = Decimal(repr(comb["mu_bayes"]))
        return {
            "coefficient": str(scenario.coefficient),
            "R_seg1": str(R0),
            "R_wls": str(R0 * (Decimal(1) + y_wls_d)),
            "R_mp": str(R0 * (Decimal(1) + y_mp_d)),
            "R_bayes": str(R0 * (Decimal(1) + mu_d)),
            "y_wls_precision_1e18": comb["y_wls"] * 1e18,
            **{k: comb[k] for k in ("u_wls", "chi2", "dof", "chi2_red", "p_chi2",
                                    "birge_ratio", "u_birge", "xi_mp", "u_mp",
                                    "mu_bayes", "u_stat_bayes", "xi_bayes")},
            "per_segment": rows,
        }


def main() -> int:
    try:
        times, beat = s.load_beat()
    except (OSError, ValueError) as error:
        raise AnalysisError(f"raw beat data could not be loaded: {error}") from error
    segments = select_segments(times, beat)
    try:
        tide = TideGrid(*s.load_tide())
    except (OSError, ValueError, KeyError) as error:
        raise AnalysisError(f"tide data could not be loaded: {error}") from error

    # Corrected per-segment ratios: reuse analyze_segment so the ratio path is
    # bit-identical to tidal_correction.py for each scenario (incl. raw).
    corrected_ratios: dict[str, dict[int, Decimal]] = {}
    for scenario in SCENARIOS:
        corrected_ratios[scenario.key] = {}
        for seg in segments:
            h = tide.beat_at(seg.times) if scenario.coefficient != 0 else np.zeros(len(seg.beat))
            res = analyze_segment(seg, h, scenario)
            corrected_ratios[scenario.key][seg.group] = res.ratio

    document = {
        "scenarios": {},
        "metadata": {
            "decimal_precision": 80,
            "selection": "frozen raw selection via tidal_analysis.select_segments (identical retained samples across scenarios)",
            "oadev": "overlapping Allan deviation on corrected beat, extrapolated 128s<=tau<=T/4 -> T, same as statistical_methods.py",
            "y_i_baseline": "R_i_scenario / R_seg1_scenario - 1 (segment-1 ratio of the SAME scenario), x1e18",
            "u_i": "sigma_y(T) * R_i_scenario, absolute ratio uncertainty, NOT SEM",
            "note": "raw baseline (A=0) reproduces statistical_methods.py up to identical selection/arith; theory/empirical are the new corrected runs.",
        },
    }
    for scenario in SCENARIOS:
        document["scenarios"][scenario.key] = scenario_result(
            segments, tide, scenario, corrected_ratios[scenario.key])

    JSON_PATH.write_text(json.dumps(document, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    for key, sc in document["scenarios"].items():
        print(f"\n[{key}] A={sc['coefficient']}")
        print(f"  R_seg1 = {sc['R_seg1'][:26]}")
        print(f"  WLS    R={sc['R_wls'][:26]}  u={sc['u_wls']:.3e}  chi2_red={sc['chi2_red']:.3f}")
        print(f"  Birge  B={sc['birge_ratio']:.3f}  u={sc['u_birge']:.3e}")
        print(f"  M-P    R={sc['R_mp'][:26]}  xi={sc['xi_mp']:.3e}  u={sc['u_mp']:.3e}")
        print(f"  Bayes  R={sc['R_bayes'][:26]}  xi={sc['xi_bayes']:.3e}  u={sc['u_stat_bayes']:.3e}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)
