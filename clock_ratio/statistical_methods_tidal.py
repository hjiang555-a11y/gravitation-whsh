#!/usr/bin/env python3
"""Paper-style statistical methods (WLS / Birge / Mandel-Paule / Bayesian) applied
to TIDAL-CORRECTED data, as a parallel result set that does NOT replace the raw
baseline in `statistical_methods.py`.

The three fixed-coefficient scenarios (raw A=0, theory A=-1, empirical A=-0.54,
identical to `tidal_correction.py`) are each propagated through the unified
scenario layer `clock_ratio.statistical_scenarios`:

  1. Per segment: freeze the raw selection (windows, exclusions, jump filter,
     longest index span, endpoint screen) via `tidal_analysis.select_segments`.
  2. Corrected beat:  b_corr = b_raw - A*h,  h = F_1550 * dW/c^2 (undemeaned
     tidal template, interpolated from the 30-s grid on the actual retained
     timestamps; the raw scenario skips interpolation).
  3. Per-segment uncertainty u_i: gap-safe TRUE overlapping Allan deviation of
     the CORRECTED beat fractional frequency (via `segment_uncertainty`), fitted
     over 128 s <= tau <= 0.25*T with T the longest gap-free run and
     extrapolated to tau = T; the longest-tau fallback is never reused.
  4. Per-scenario ratio R_i and deviation y_i = R_i / R_seg1 - 1 (same
     segment-1 baseline convention and Decimal80 ratio path as the raw case).
  5. Combine with WLS / Birge / M-P / Bayesian (typed core).

Outputs (independent, all under clock_ratio/):
  statistical_methods_tidal.json   (per-scenario combined values + metadata)
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared as s  # noqa: E402
from clock.sample_selection import AnalysisError, select_segments  # noqa: E402
from clock_ratio.evidence import EvidenceStatus  # noqa: E402
from clock_ratio.statistical_scenarios import (  # noqa: E402
    StatisticalScenarioResult,
    analyze_scenarios,
    build_synthesis,
    render_synthesis,
    u_absolute,
    y_i_1e18,
)
from clock_ratio.tidal_analysis import SCENARIOS, TideGrid  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
JSON_PATH = OUT_DIR / "statistical_methods_tidal.json"

SUMMARY_FIELDS = ("u_wls", "chi2", "dof", "chi2_red", "p_chi2", "birge_ratio",
                  "u_birge", "xi_mp", "u_mp", "mu_bayes", "u_stat_bayes", "xi_bayes")
SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}


def scenario_document(result: StatisticalScenarioResult, coefficient: Decimal) -> dict:
    """Render one scenario's legacy JSON block from the typed scenario result.

    The schema (and key names) matches the historical artifact so downstream
    consumers (`make_report.py`, `make_paper_figures.py`) keep working; the
    per-segment rows gain ``n_valid`` plus the model-status disclosure fields
    ``status`` (plain value string, never ``str(enum)``) and ``fit_slope``.
    """
    combination = result.combination
    with localcontext() as context:
        context.prec = 80
        reference = combination.reference_ratio
        center_wls = reference * (Decimal(1) + Decimal(repr(combination.y_wls)))
        center_mp = reference * (Decimal(1) + Decimal(repr(combination.y_mp)))
        center_bayes = reference * (Decimal(1) + Decimal(repr(combination.mu_bayes)))
    rows = [
        {
            "group": fact.group,
            "T_s": fact.n_valid,
            "u_frac": fact.uncertainty.u_fractional,
            "u_i": u_absolute(fact),
            "y_i_1e18": y_i_1e18(fact, reference),
            "n_valid": fact.n_valid,
            "status": EvidenceStatus(fact.uncertainty.status).value,
            "fit_slope": fact.uncertainty.fit_slope,
        }
        for fact in result.segments
    ]
    return {
        "coefficient": str(coefficient),
        "R_seg1": str(reference),
        "R_wls": str(center_wls),
        "R_mp": str(center_mp),
        "R_bayes": str(center_bayes),
        "y_wls_precision_1e18": combination.y_wls * 1e18,
        **{name: getattr(combination, name) for name in SUMMARY_FIELDS},
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

    results = analyze_scenarios(segments, tide)

    document = {
        "scenarios": {
            key: scenario_document(results[key], SCENARIO_BY_KEY[key].coefficient)
            for key in SCENARIO_BY_KEY
        },
        "metadata": {
            "decimal_precision": 80,
            "selection": "frozen raw selection via tidal_analysis.select_segments (identical retained samples across scenarios)",
            "oadev": "gap-safe true overlapping Allan deviation via segment_uncertainty.estimate_segment_uncertainty on the corrected beat; fit 128s<=tau<=0.25*T (T = longest gap-free run), extrapolated to tau=T; no longest-tau fallback",
            "y_i_baseline": "R_i_scenario / R_seg1_scenario - 1 (segment-1 ratio of the SAME scenario), x1e18",
            "u_i": "sigma_y(T) * R_i_scenario, absolute ratio uncertainty, NOT SEM",
            "note": "raw baseline (A=0) reproduces statistical_methods.py field-for-field (same gap-safe estimator); theory/empirical are the new corrected runs.",
        },
        "synthesis": render_synthesis(build_synthesis(results)),
    }

    JSON_PATH.write_text(json.dumps(document, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    for key in SCENARIO_BY_KEY:
        sc = document["scenarios"][key]
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
