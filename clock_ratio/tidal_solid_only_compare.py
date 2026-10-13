#!/usr/bin/env python3
"""Solid-tide-only comparison analysis (diagnostic; does not modify the paper).

Three tide sources are compared on the same 16-segment (segment-9 excluded)
machinery:

  1. OLD total (professional 30-s UTC, solid+ocean loading, m2/s2) -- the
     authoritative template of the paper;
  2. OLD solid-only (professional 30-s UTC, H column of the source workbook,
     solid tide displacement difference only, converted with g=9.794);
  3. NEW solid-only (European public model, DE421 + Love numbers, 90-s
     Beijing-time grid, fractional df/f units, `solid` column of
     results/comp_shanghai-wuhan-beijintime.csv).

For each source we run the raw/theory/empirical scenario combination and the
per-segment correlation of y_i vs the segment-mean tidal shift.

Outputs (diagnostic only):
  clock_ratio/tidal_solid_only_compare.json
"""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared as s  # noqa: E402
from clock.sample_selection import AnalysisError, FloatArray, TimeArray, select_segments  # noqa: E402
from clock_ratio.segment_uncertainty import StabilityFitConfig  # noqa: E402
from clock_ratio.statistical_scenarios import analyze_scenarios, exclude_groups  # noqa: E402
from clock_ratio.tidal_analysis import SCENARIOS, TideGrid  # noqa: E402

OLD_CSV = Path(__file__).resolve().parents[1] / "results" / "professional_tidal_delta_30s.csv"
OLD_SOLID_CSV = Path(__file__).resolve().parents[1] / "results" / "solid_tide_old_30s_utc.csv"
NEW_CSV = Path(__file__).resolve().parents[1] / "results" / "comp_shanghai-wuhan-beijintime.csv"
OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "tidal_solid_only_compare.json"
EXCLUDED_GROUP = 9


@dataclass(frozen=True, slots=True)
class FracGrid:
    """Beijing-time grid of fractional tidal shifts (df/f) in the WUH-SHA
    direction; duck-types TideGrid.beat_at."""

    times: TimeArray
    dff: FloatArray

    def __post_init__(self) -> None:
        if (self.times.ndim != 1 or self.dff.ndim != 1
                or len(self.times) != len(self.dff) or len(self.times) < 2):
            raise AnalysisError("grid needs at least two aligned 1-D samples")
        if np.isnat(self.times).any() or not np.isfinite(self.dff).all():
            raise AnalysisError("grid timestamps and values must be finite")

    def beat_at(self, beijing_times: TimeArray) -> FloatArray:
        if beijing_times.ndim != 1 or np.isnat(beijing_times).any():
            raise AnalysisError("tide queries must be finite 1-D Beijing timestamps")
        if np.any(beijing_times < self.times[0]) or np.any(beijing_times > self.times[-1]):
            raise AnalysisError("tide query outside coverage")
        right = np.searchsorted(self.times, beijing_times, side="left")
        interior = self.times[right] != beijing_times
        hi = right[interior]
        origin = self.times[0]
        query_s = (beijing_times - origin) / np.timedelta64(1, "s")
        grid_s = (self.times - origin) / np.timedelta64(1, "s")
        return np.interp(query_s, grid_s, self.dff) * s.F_1550


def load_old_solid() -> TideGrid:
    """Old-model solid-tide-only: UTC 30-s, m2/s2 -> dW."""
    rows = list(csv.DictReader(open(OLD_SOLID_CSV)))
    t = np.array([r["timestamp_utc"].replace("Z", "") for r in rows], dtype="datetime64[s]")
    v = np.array([float(r["solid_tidal_delta_m2_s2_surface"]) for r in rows])
    return TideGrid(t, v)


def load_new_solid() -> FracGrid:
    """New-model solid column: BJ 90-s, fractional df/f."""
    rows = list(csv.DictReader(open(NEW_CSV)))
    t = np.array([datetime.strptime(r["timestamp_bjt"], "%Y%m%d%H%M%S") for r in rows],
                 dtype="datetime64[s]")
    v = np.array([float(r["solid"]) for r in rows])
    return FracGrid(t, v)


def scenario_summary(results: dict) -> dict:
    out = {}
    for key in ("raw", "theory", "empirical"):
        comb = results[key].combination
        out[key] = {
            "chi2_red": comb.chi2_red,
            "birge_ratio": comb.birge_ratio,
            "xi_bayes": comb.xi_bayes,
            "u_stat_bayes": comb.u_stat_bayes,
            "mu_bayes": comb.mu_bayes,
        }
    # Center shifts in ABSOLUTE ratio units (x1e18), matching the paper
    # convention: R = reference_ratio * (1 + mu_bayes) with the scenario's
    # own segment-1 ratio as reference.
    for key in ("theory", "empirical"):
        r_raw = results["raw"].combination.reference_ratio * (
            Decimal(1) + Decimal(repr(results["raw"].combination.mu_bayes)))
        r_k = results[key].combination.reference_ratio * (
            Decimal(1) + Decimal(repr(results[key].combination.mu_bayes)))
        out[key]["center_shift_e18"] = float((r_k - r_raw) * Decimal("1e18"))
    return out


def segment_correlation(segments, grid) -> dict:
    """y_i (from scenario raw facts) vs segment-mean tidal dff."""
    from clock_ratio.statistical_scenarios import y_i_1e18
    results_raw = analyze_scenarios(segments, grid, StabilityFitConfig())["raw"]
    ref = results_raw.combination.reference_ratio
    y = np.array([y_i_1e18(f, ref) for f in results_raw.segments])
    nv = np.array([f.n_valid for f in results_raw.segments], dtype=float)
    w = nv / nv.sum()
    dff = np.array([float(grid.beat_at(seg.times).mean() / s.F_1550) for seg in segments]) * 1e18
    mask = np.array([seg.group != EXCLUDED_GROUP for seg in segments])
    from scipy import stats
    r_all, p_all = stats.pearsonr(y, dff)
    r_16, p_16 = stats.pearsonr(y[mask], dff[mask])
    def wp(x, yy, ww):
        mx = np.sum(ww*x)/np.sum(ww); my = np.sum(ww*yy)/np.sum(ww)
        return np.sum(ww*(x-mx)*(yy-my))/np.sqrt(np.sum(ww*(x-mx)**2)*np.sum(ww*(yy-my)**2))
    return {
        "pearson_17": {"r": float(r_all), "p": float(p_all)},
        "pearson_16": {"r": float(r_16), "p": float(p_16)},
        "timeweighted_17": {"r": float(wp(y, dff, w))},
        "timeweighted_16": {"r": float(wp(y[mask], dff[mask], w[mask]))},
        "seg_mean_dff_e18": [float(x) for x in dff],
        "y_i_e18": [float(x) for x in y],
        "groups": [seg.group for seg in segments],
    }


def main() -> int:
    try:
        times, beat = s.load_beat()
    except (OSError, ValueError) as error:
        raise AnalysisError(f"raw beat data could not be loaded: {error}") from error
    segments = select_segments(times, beat)

    document = {"metadata": {
        "note": "solid-tide-only diagnostic; paper unaffected",
        "excluded_group": EXCLUDED_GROUP,
    }, "sources": {}}

    sources = [
        ("old_total", TideGrid(*s.load_tide())),
        ("old_solid", load_old_solid()),
        ("new_solid", load_new_solid()),
    ]
    for name, grid in sources:
        results = analyze_scenarios(segments, grid, StabilityFitConfig())
        results = {k: exclude_groups(v, frozenset({EXCLUDED_GROUP}))
                   for k, v in results.items()}
        document["sources"][name] = {
            "scenarios": scenario_summary(results),
            "correlation": segment_correlation(segments, grid),
        }
        print(f"\n=== {name} ===")
        ss = document["sources"][name]["scenarios"]
        for key in ("raw", "theory", "empirical"):
            print(f"  {key:<10} chi2_red={ss[key]['chi2_red']:.3f} "
                  f"xi_bayes={ss[key]['xi_bayes']:.3e} shift={ss[key].get('center_shift_e18', 0):+.3f}")
        cor = document["sources"][name]["correlation"]
        print(f"  corr 17seg r={cor['pearson_17']['r']:+.3f} p={cor['pearson_17']['p']:.3f} | "
              f"16seg r={cor['pearson_16']['r']:+.3f} p={cor['pearson_16']['p']:.3f}")

    JSON_PATH.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {JSON_PATH}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
