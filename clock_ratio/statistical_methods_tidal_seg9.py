#!/usr/bin/env python3
"""Segment-9 exclusion sensitivity check for the tidal-corrected statistical
methods — an ADDITIVE result that does NOT replace or modify any existing
output.

Segment 9 is flagged anomalous (METHODOLOGY §8.2/§8.3): its Sr systematic
shift `shift_a = -8.13e-17` sits between the 7-month value (~-1.72e-16) and the
8-month value (~+7.9e-18), and its source comment asks whether that is real or a
placeholder, making y_9 ~ +6.4e-18 (raw) an outlier. This script answers "what
do the combined values and the tidal-correction story become if segment 9 is
dropped", by DECODING the ALREADY-COMPUTED per-segment facts stored in
`statistical_methods_tidal.json` into the typed scenario layer and re-combining
them there (segment-1 baseline preserved; no re-selection, no re-correction).
It never re-runs tidal_correction.py or statistical_methods.py and never
rewrites their artifacts.  The full leave-one-out sweep over all 17 groups is
recomputed from the same fact layer.

Outputs (new, separate):
  statistical_methods_tidal_seg9_excluded.json
"""
from __future__ import annotations

import json
import sys
from collections.abc import Mapping
from decimal import Decimal, localcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.sample_selection import AnalysisError  # noqa: E402
from clock_ratio.segment_uncertainty import SegmentUncertainty  # noqa: E402
from clock_ratio.statistical_methods_tidal import scenario_document  # noqa: E402
from clock_ratio.statistical_scenarios import (  # noqa: E402
    SCENARIO_KEYS,
    ScenarioSegmentResult,
    StatisticalScenarioResult,
    _build_scenario_result,
    build_synthesis,
    exclude_groups,
    leave_one_out,
    render_synthesis,
)
from clock_ratio.tidal_analysis import SCENARIOS  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
SOURCE_JSON = OUT_DIR / "statistical_methods_tidal.json"
JSON_PATH = OUT_DIR / "statistical_methods_tidal_seg9_excluded.json"
EXCLUDED_GROUP = 9
SCENARIO_BY_KEY = {scenario.key: scenario for scenario in SCENARIOS}


def decode_scenario(key: str, payload: Mapping[str, object]) -> StatisticalScenarioResult:
    """Decode one stored scenario block into the typed fact layer.

    Accepts both schema generations: rows without ``n_valid`` fall back to
    ``T_s`` (the retained-sample count in the legacy artifact).  The per-segment
    ratio is reconstructed as ``R_seg1 * (1 + y_i)`` in an 80-digit Decimal
    context; the fractional uncertainty is decoded from the stored ``u_i``.
    Diagnostic-only fields the artifact never carried (runs, tau grid, fit)
    stay empty and the uncertainty is flagged ``supported-with-limitations``.
    """
    scenario = SCENARIO_BY_KEY.get(key)
    if scenario is None:
        raise AnalysisError(f"unknown scenario key: {key!r}")
    try:
        reference = Decimal(str(payload["R_seg1"]))
        rows = payload["per_segment"]
    except (KeyError, TypeError) as error:
        raise AnalysisError(f"{key}: malformed scenario block: {error}") from error
    if not isinstance(rows, list) or not rows:
        raise AnalysisError(f"{key}: per_segment must be a non-empty list")
    facts: list[ScenarioSegmentResult] = []
    for row in rows:
        try:
            group = int(row["group"])
            n_valid = int(row.get("n_valid", row["T_s"]))
            y_i = float(row["y_i_1e18"])
            u_i = Decimal(str(row["u_i"]))
        except (KeyError, TypeError, ValueError) as error:
            raise AnalysisError(f"{key}: malformed per_segment row: {error}") from error
        with localcontext() as context:
            context.prec = 80
            ratio = reference * (Decimal(1) + Decimal(repr(y_i)) * Decimal("1e-18"))
            u_fractional = float(u_i / ratio)
        uncertainty = SegmentUncertainty(
            group=group, n_valid=n_valid, n_runs=0, taus_s=(), sigma_y=(),
            fit_slope=None, fit_intercept=None, u_fractional=u_fractional,
            status="supported-with-limitations",
        )
        facts.append(ScenarioSegmentResult(
            group=group, ratio=ratio, deviation=y_i * 1e-18,
            uncertainty=uncertainty, n_valid=n_valid,
        ))
    return _build_scenario_result(
        key, float(scenario.coefficient), tuple(facts), (), reference)


def compact_summary(result: StatisticalScenarioResult) -> dict:
    """Small per-group digest for the leave-one-out section."""
    combination = result.combination
    with localcontext() as context:
        context.prec = 80
        reference = combination.reference_ratio
        return {
            "R_wls": str(reference * (Decimal(1) + Decimal(repr(combination.y_wls)))),
            "R_mp": str(reference * (Decimal(1) + Decimal(repr(combination.y_mp)))),
            "R_bayes": str(reference * (Decimal(1) + Decimal(repr(combination.mu_bayes)))),
            "chi2_red": combination.chi2_red,
            "u_wls": combination.u_wls,
        }


def reduced_block(result: StatisticalScenarioResult, coefficient: Decimal) -> dict:
    """Legacy scenario block for the 16-segment result (adds membership keys)."""
    block = scenario_document(result, coefficient)
    block["n_segments"] = len(result.included_groups)
    block["excluded_group"] = EXCLUDED_GROUP
    return block


def main() -> int:
    try:
        source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise AnalysisError(f"cannot read {SOURCE_JSON.name}: {error}") from error
    if not isinstance(source, dict):
        raise AnalysisError(f"{SOURCE_JSON.name}: document must be an object")
    scenarios = source.get("scenarios")
    if not isinstance(scenarios, dict):
        raise AnalysisError(f"{SOURCE_JSON.name}: missing scenarios block")
    missing = [key for key in SCENARIO_KEYS if key not in scenarios]
    if missing:
        raise AnalysisError(f"{SOURCE_JSON.name}: missing scenarios {missing}")

    decoded = {key: decode_scenario(key, scenarios[key]) for key in SCENARIO_KEYS}
    reduced = {
        key: exclude_groups(decoded[key], frozenset({EXCLUDED_GROUP}))
        for key in SCENARIO_KEYS
    }

    document = {
        "scenarios": {
            key: reduced_block(reduced[key], SCENARIO_BY_KEY[key].coefficient)
            for key in SCENARIO_KEYS
        },
        "synthesis": render_synthesis(build_synthesis(reduced)),
        "leave_one_out": {
            key: {
                str(group): compact_summary(result)
                for group, result in leave_one_out(decoded[key]).items()
            }
            for key in SCENARIO_KEYS
        },
        "metadata": {
            "decimal_precision": 80,
            "source": SOURCE_JSON.name,
            "excluded_group": EXCLUDED_GROUP,
            "exclusion_reason": "segment 9 shift_a anomalous (-8.13e-17 between the 7-month ~-1.72e-16 and 8-month ~+7.9e-18), y_9 a raw outlier; see METHODOLOGY §8",
            "method": "decoded the stored per-segment facts and re-combined them via the typed scenario layer (segment-1 baseline preserved); the leave-one-out sweep was recomputed from the same facts; no re-selection, no re-correction",
            "baseline": "R_seg1 from the same scenario as in statistical_methods_tidal.json",
            "note": "ADDITIVE sensitivity check; does not replace the 17-segment results",
        },
    }

    JSON_PATH.write_text(json.dumps(document, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    for key in SCENARIO_KEYS:
        sc = document["scenarios"][key]
        print(f"\n[{key}] A={sc['coefficient']}  (n={sc['n_segments']}, seg{EXCLUDED_GROUP} dropped)")
        print(f"  WLS   R={sc['R_wls'][:26]}  u={sc['u_wls']:.3e}  chi2_red={sc['chi2_red']:.3f}")
        print(f"  M-P   R={sc['R_mp'][:26]}  xi={sc['xi_mp']:.3e}")
        print(f"  Bayes R={sc['R_bayes'][:26]}  xi={sc['xi_bayes']:.3e}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)
