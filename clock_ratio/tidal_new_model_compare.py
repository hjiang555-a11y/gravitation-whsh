#!/usr/bin/env python3
"""Comparison analysis with the NEW tidal model (European public model).

The new model arrives as `results/comp_shanghai-wuhan-beijintime.csv`:
Beijing-time 90-s grid, `tide_tot` already in fractional-frequency units
(df/f), direction Shanghai-Wuhan (verified: corr with the old professional
series = +0.876 in the Wuhan-Shanghai convention, so the sign matches the
template convention h = F_1550 * dW/c^2 used by the analysis chain).

This script is a PARALLEL diagnostic -- it does NOT replace or modify any
existing artifact. It reuses the frozen raw selection and the scenario
machinery (analyze_scenarios), feeding a duck-typed grid that serves the
new model on the Beijing-time axis (no UTC conversion needed: beat
timestamps are Beijing time, and the new series is natively Beijing time).

Outputs (diagnostic, not part of the audit layer):
  clock_ratio/tidal_new_model_compare.json   (per-scenario combined values)
  clock_ratio/tidal_new_model_compare.md     (comparison vs the old model)
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
from clock_ratio.tidal_analysis import SCENARIOS  # noqa: E402

NEW_TIDE_CSV = Path(__file__).resolve().parents[1] / "results" / "comp_shanghai-wuhan-beijintime.csv"
OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "tidal_new_model_compare.json"
MD_PATH = OUT_DIR / "tidal_new_model_compare.md"
EXCLUDED_GROUP = 9  # match the frozen seg9-excluded primary (16 segments)


@dataclass(frozen=True, slots=True)
class NewTideGrid:
    """Beijing-time 90-s grid of fractional tidal shifts (df/f, WUH-SHA).

    Duck-types ``TideGrid.beat_at``: queries arrive as Beijing timestamps
    (the beat axis) and are answered on the native Beijing-time grid.
    """

    times: TimeArray
    dff: FloatArray

    def __post_init__(self) -> None:
        if (self.times.ndim != 1 or self.dff.ndim != 1
                or len(self.times) != len(self.dff) or len(self.times) < 2):
            raise AnalysisError("new tide grid needs at least two aligned 1-D samples")
        if np.isnat(self.times).any() or not np.isfinite(self.dff).all():
            raise AnalysisError("new tide timestamps and values must be finite")
        seconds = self.times.astype("datetime64[s]").astype(np.int64)
        if np.any(np.diff(self.times) <= np.timedelta64(0, "s")):
            raise AnalysisError("new tide grid must be sorted and unique")

    def beat_at(self, beijing_times: TimeArray) -> FloatArray:
        """Interpolate the fractional tidal shift; h = dff * F_1550."""
        if beijing_times.ndim != 1 or np.isnat(beijing_times).any():
            raise AnalysisError("tide queries must be finite 1-D Beijing timestamps")
        if np.any(beijing_times < self.times[0]) or np.any(beijing_times > self.times[-1]):
            raise AnalysisError("tide query outside coverage; clamping/extrapolation forbidden")
        right = np.searchsorted(self.times, beijing_times, side="left")
        interior = self.times[right] != beijing_times
        hi = right[interior]
        if np.any(self.times[hi] - self.times[hi - 1] != np.timedelta64(90, "s")):
            raise AnalysisError("tide interpolation across a missing >90-second interval")
        origin = self.times[0]
        query_s = (beijing_times - origin) / np.timedelta64(1, "s")
        grid_s = (self.times - origin) / np.timedelta64(1, "s")
        return np.interp(query_s, grid_s, self.dff) * s.F_1550


def load_new_tide() -> NewTideGrid:
    rows = list(csv.DictReader(open(NEW_TIDE_CSV)))
    times = np.array(
        [datetime.strptime(r["timestamp_bjt"], "%Y%m%d%H%M%S") for r in rows],
        dtype="datetime64[s]",
    )
    dff = np.array([float(r["tide_tot"]) for r in rows])
    return NewTideGrid(times, dff)


def render_document(results: dict, grid: NewTideGrid) -> dict:
    scenario_blocks = {}
    for key in ("raw", "theory", "empirical"):
        res = results[key]
        comb = res.combination
        scenario_blocks[key] = {
            "coefficient": res.coefficient,
            "n_segments": len(res.included_groups),
            "R_wls": str(res.duration_weighted_ratio) if False else None,
            "combination": {
                "y_wls": comb.y_wls,
                "u_wls": comb.u_wls,
                "chi2": comb.chi2,
                "chi2_red": comb.chi2_red,
                "p_chi2": comb.p_chi2,
                "birge_ratio": comb.birge_ratio,
                "u_birge": comb.u_birge,
                "xi_mp": comb.xi_mp,
                "u_mp": comb.u_mp,
                "mu_bayes": comb.mu_bayes,
                "u_stat_bayes": comb.u_stat_bayes,
                "xi_bayes": comb.xi_bayes,
                "reference_ratio": str(comb.reference_ratio),
            },
        }
    return {
        "metadata": {
            "source": str(NEW_TIDE_CSV.name),
            "n_rows": len(grid.times),
            "grid_s": 90,
            "time_base": "Beijing time (UTC+8), native to the beat axis",
            "unit": "fractional frequency df/f (Wuhan-Shanghai)",
            "note": "diagnostic comparison; the professional 30-s series remains authoritative",
        },
        "scenarios": scenario_blocks,
    }


def compare_with_old() -> None:
    """Load the frozen old-model seg9-excluded JSON and print a comparison."""
    old_path = Path(__file__).resolve().parents[1] / "results" / "audit-v1" / "verified" / "statistical_methods_tidal_seg9_excluded.json"
    old = json.loads(old_path.read_text())["synthesis"]["goodness_of_fit"]
    new = json.loads(JSON_PATH.read_text())["scenarios"]
    print("\n=== old (professional 30s) vs new (European 90s) ===")
    print(f"{'scenario':<10} {'old chi2_red':>13} {'new chi2_red':>13}")
    for key in ("raw", "theory", "empirical"):
        print(f"{key:<10} {old[key]['chi2_red']:13.3f} {new[key]['combination']['chi2_red']:13.3f}")


def main() -> int:
    try:
        times, beat = s.load_beat()
    except (OSError, ValueError) as error:
        raise AnalysisError(f"raw beat data could not be loaded: {error}") from error
    segments = select_segments(times, beat)
    grid = load_new_tide()

    results = analyze_scenarios(segments, grid, StabilityFitConfig())
    # Match the frozen primary: 16 segments, segment 9 excluded.
    results = {key: exclude_groups(res, frozenset({EXCLUDED_GROUP}))
               for key, res in results.items()}
    document = render_document(results, grid)
    JSON_PATH.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")

    for key in ("raw", "theory", "empirical"):
        comb = document["scenarios"][key]["combination"]
        print(f"\n[{key}] A={results[key].coefficient}")
        print(f"  chi2_red = {comb['chi2_red']:.3f}  birge = {comb['birge_ratio']:.3f}")
        print(f"  xi_mp = {comb['xi_mp']:.3e}  xi_bayes = {comb['xi_bayes']:.3e}")
        print(f"  u_stat_bayes = {comb['u_stat_bayes']:.3e}  u_wls = {comb['u_wls']:.3e}")
        print(f"  mu_bayes = {comb['mu_bayes']:.3e} (fractional dev)")

    compare_with_old()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
