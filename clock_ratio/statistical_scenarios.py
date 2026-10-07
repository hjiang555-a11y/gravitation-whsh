"""Unified raw/tidal statistical scenarios over one per-segment fact layer.

The three fixed-response scenarios (raw/theory/empirical) share the same
selection and ratio inversion; only the corrected beat and its per-segment
uncertainty differ.  Exclusions (segment 9, leave-one-out) recompute the
combination and the duration-weighted center from the existing facts, never
from pre-generated JSON.  The synthesis renderer preserves the legacy JSON
document schema consumed by ``make_report.py`` and ``make_paper_figures.py``.

Units follow the raw pipeline: ``y_i = R_i / R_1 - 1`` (fractional, segment-1
baseline) and ``u_i = u_frac * R_i`` (absolute ratio).
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from statistics import stdev
from typing import Final, Literal

import numpy as np

from clock.sample_selection import AnalysisError, SelectedSegment
from clock.shared import F_1550
from clock_ratio.segment_uncertainty import (
    SegmentUncertainty,
    StabilityFitConfig,
    estimate_segment_uncertainty,
)
from clock_ratio.statistical_models import (
    CombinationResult,
    SegmentEstimate,
    combine_estimates,
)
from clock_ratio.tidal_analysis import SCENARIOS, Scenario, TideGrid, analyze_segment

ScenarioKey = Literal["raw", "theory", "empirical"]

SCENARIO_KEYS: Final[tuple[str, ...]] = tuple(scenario.key for scenario in SCENARIOS)
EXPERIMENT_WLS_REFERENCE: Final = Decimal("1.2075070393433377213")
SYNTHESIS_METHODS: Final[tuple[tuple[str, str], ...]] = (
    ("R_wls", "y_wls"),
    ("R_mp", "y_mp"),
    ("R_bayes", "mu_bayes"),
)


@dataclass(frozen=True, slots=True)
class ScenarioSegmentResult:
    group: int
    ratio: Decimal
    deviation: float
    uncertainty: SegmentUncertainty
    n_valid: int


@dataclass(frozen=True, slots=True)
class StatisticalScenarioResult:
    scenario: ScenarioKey
    coefficient: float
    included_groups: tuple[int, ...]
    excluded_groups: tuple[int, ...]
    segments: tuple[ScenarioSegmentResult, ...]
    combination: CombinationResult
    duration_weighted_ratio: Decimal
    total_samples: int


@dataclass(frozen=True, slots=True)
class MethodCenter:
    ratio: Decimal
    deviation_vs_experiment_wls_1e18: float


@dataclass(frozen=True, slots=True)
class ScenarioGoodnessOfFit:
    chi2_red: float
    birge_ratio: float
    xi_mp: float
    xi_bayes: float
    u_wls: float


@dataclass(frozen=True, slots=True)
class ScenarioLongTermStability:
    y_i_std_1e18: float
    improvement_vs_raw_pct: float


@dataclass(frozen=True, slots=True)
class StatisticalSynthesis:
    reference_experiment_wls: Decimal
    methods: Mapping[str, Mapping[str, MethodCenter]]
    goodness_of_fit: Mapping[str, ScenarioGoodnessOfFit]
    long_term_stability: Mapping[str, ScenarioLongTermStability]


def u_absolute(fact: ScenarioSegmentResult) -> float:
    """u_i = u_frac * R_i (absolute ratio); ambient Decimal context, same as
    ``analyze_raw_statistics`` so the raw path stays bit-identical."""
    u_fractional = fact.uncertainty.u_fractional
    if u_fractional is None:
        raise AnalysisError(f"segment {fact.group}: u_fractional is undefined")
    return float(Decimal(repr(u_fractional)) * fact.ratio)


def _deviation(ratio: Decimal, reference: Decimal) -> float:
    return float(ratio / reference - Decimal(1))


def y_i_1e18(fact: ScenarioSegmentResult, reference: Decimal) -> float:
    """Legacy rendering fidelity: the x1e18 conversion happens in Decimal.

    A private 80-digit context keeps the value independent of the ambient
    context so renderer and synthesis agree bit for bit.
    """
    with localcontext() as context:
        context.prec = 80
        return float((fact.ratio / reference - Decimal(1)) * Decimal("1e18"))


def _duration_weighted(facts: Sequence[ScenarioSegmentResult]) -> tuple[Decimal, int]:
    with localcontext() as context:
        context.prec = 80
        total = sum(fact.n_valid for fact in facts)
        if total <= 0:
            raise AnalysisError("duration weighting requires positive total samples")
        ratio = sum((Decimal(fact.n_valid) * fact.ratio for fact in facts), Decimal(0)) / total
    return ratio, total


def _validate_facts(
    facts: Sequence[ScenarioSegmentResult], reference: Decimal | None,
) -> None:
    groups = [fact.group for fact in facts]
    if len(set(groups)) != len(groups):
        raise AnalysisError("segment groups must be unique per scenario")
    if reference is None and 1 not in groups:
        raise AnalysisError("segment-1 ratio is required as the y_i baseline")
    for fact in facts:
        if fact.uncertainty.u_fractional is None:
            raise AnalysisError(f"segment {fact.group}: u_fractional is undefined")
        if not math.isfinite(fact.deviation):
            raise AnalysisError(f"segment {fact.group}: deviation must be finite")
        absolute = u_absolute(fact)
        if not math.isfinite(absolute) or absolute <= 0:
            raise AnalysisError(
                f"segment {fact.group}: absolute uncertainty must be finite and positive")
        if not fact.ratio.is_finite() or fact.ratio <= 0:
            raise AnalysisError(f"segment {fact.group}: ratio must be finite and positive")


def _build_scenario_result(
    scenario: str,
    coefficient: float,
    facts: Sequence[ScenarioSegmentResult],
    excluded_groups: tuple[int, ...],
    reference_ratio: Decimal | None,
) -> StatisticalScenarioResult:
    items = tuple(facts)
    _validate_facts(items, reference_ratio)
    if reference_ratio is None:
        reference_ratio = next(fact.ratio for fact in items if fact.group == 1)
    if len(items) < 2:
        raise AnalysisError("scenario combination requires at least two segment estimates")
    estimates = [
        SegmentEstimate(
            group=fact.group,
            ratio=fact.ratio,
            deviation=fact.deviation,
            u_absolute=u_absolute(fact),
        )
        for fact in items
    ]
    combination = combine_estimates(estimates, reference_ratio)
    duration_ratio, total = _duration_weighted(items)
    return StatisticalScenarioResult(
        scenario=scenario,
        coefficient=coefficient,
        included_groups=tuple(fact.group for fact in items),
        excluded_groups=excluded_groups,
        segments=items,
        combination=combination,
        duration_weighted_ratio=duration_ratio,
        total_samples=total,
    )


def analyze_scenario(
    segments: Sequence[SelectedSegment],
    tide: TideGrid,
    scenario: Scenario,
    config: StabilityFitConfig = StabilityFitConfig(),
) -> StatisticalScenarioResult:
    """One fixed-response scenario over the shared selected segments.

    The raw scenario skips tide interpolation entirely (``h`` is zeros and the
    corrected beat is the raw beat), matching ``analyze_raw_statistics`` bit for
    bit; theory/empirical interpolate the template on the actual retained times.
    """
    items = tuple(segments)
    groups = [segment.group for segment in items]
    if len(set(groups)) != len(groups):
        raise AnalysisError("segment groups must be unique per scenario")
    collected: list[tuple[int, Decimal, SegmentUncertainty, int]] = []
    for segment in items:
        if scenario.coefficient == 0:
            h = np.zeros(len(segment.beat))
            b_corr = segment.beat
        else:
            h = tide.beat_at(segment.times)
            b_corr = segment.beat - float(scenario.coefficient) * h
        segment_result = analyze_segment(segment, h, scenario)
        fractional = (b_corr - b_corr.mean()) / F_1550
        fit = estimate_segment_uncertainty(segment.times, fractional, config)
        if fit.u_fractional is None:
            raise AnalysisError(
                f"segment {segment.group}: fewer than three usable OADEV fit points")
        fit = replace(fit, group=segment.group)
        collected.append((segment.group, segment_result.ratio, fit, len(segment.beat)))

    reference = next((ratio for group, ratio, _, _ in collected if group == 1), None)
    if reference is None:
        raise AnalysisError("segment-1 ratio is required as the y_i baseline")
    facts = tuple(
        ScenarioSegmentResult(
            group=group,
            ratio=ratio,
            deviation=_deviation(ratio, reference),
            uncertainty=fit,
            n_valid=n_valid,
        )
        for group, ratio, fit, n_valid in collected
    )
    return _build_scenario_result(
        scenario.key, float(scenario.coefficient), facts, (), reference)


def analyze_scenarios(
    segments: Sequence[SelectedSegment],
    tide: TideGrid,
    config: StabilityFitConfig = StabilityFitConfig(),
) -> dict[str, StatisticalScenarioResult]:
    return {
        scenario.key: analyze_scenario(segments, tide, scenario, config)
        for scenario in SCENARIOS
    }


def exclude_groups(
    result: StatisticalScenarioResult, groups: frozenset[int] | set[int],
) -> StatisticalScenarioResult:
    """Rebuild the combination and duration center without the given groups.

    The reference ratio (segment-1 baseline) is preserved from the source
    result, so excluding the empty set reproduces the full result exactly.
    """
    group_set = frozenset(groups)
    present = {fact.group for fact in result.segments}
    unknown = group_set - present
    if unknown:
        raise AnalysisError(f"cannot exclude absent segment groups: {sorted(unknown)}")
    kept = tuple(fact for fact in result.segments if fact.group not in group_set)
    if len(kept) < 2:
        raise AnalysisError("exclusion would leave fewer than two segment estimates")
    excluded = tuple(sorted(set(result.excluded_groups) | group_set))
    return _build_scenario_result(
        result.scenario, result.coefficient, kept, excluded,
        result.combination.reference_ratio,
    )


def leave_one_out(
    result: StatisticalScenarioResult,
) -> dict[int, StatisticalScenarioResult]:
    return {
        group: exclude_groups(result, frozenset({group}))
        for group in sorted(fact.group for fact in result.segments)
    }


def build_synthesis(
    results: Mapping[str, StatisticalScenarioResult],
) -> StatisticalSynthesis:
    for key in SCENARIO_KEYS:
        if key not in results:
            raise AnalysisError(f"synthesis requires the {key!r} scenario")
    with localcontext() as context:
        context.prec = 80
        reference = EXPERIMENT_WLS_REFERENCE
        methods: dict[str, dict[str, MethodCenter]] = {}
        for method, field_name in SYNTHESIS_METHODS:
            per_scenario: dict[str, MethodCenter] = {}
            for key in SCENARIO_KEYS:
                combination = results[key].combination
                ratio = combination.reference_ratio * (
                    Decimal(1) + Decimal(repr(getattr(combination, field_name))))
                per_scenario[key] = MethodCenter(
                    ratio=ratio,
                    deviation_vs_experiment_wls_1e18=float(
                        (ratio - reference) * Decimal("1e18")),
                )
            methods[method] = per_scenario
        goodness = {
            key: ScenarioGoodnessOfFit(
                chi2_red=results[key].combination.chi2_red,
                birge_ratio=results[key].combination.birge_ratio,
                xi_mp=results[key].combination.xi_mp,
                xi_bayes=results[key].combination.xi_bayes,
                u_wls=results[key].combination.u_wls,
            )
            for key in SCENARIO_KEYS
        }
        stds = {
            key: stdev([
                y_i_1e18(fact, results[key].combination.reference_ratio)
                for fact in results[key].segments
            ])
            for key in SCENARIO_KEYS
        }
        raw_std = stds["raw"]
        stability = {
            key: ScenarioLongTermStability(
                y_i_std_1e18=stds[key],
                improvement_vs_raw_pct=100.0 * (1.0 - stds[key] / raw_std),
            )
            for key in SCENARIO_KEYS
        }
    return StatisticalSynthesis(reference, methods, goodness, stability)


def render_synthesis(synthesis: StatisticalSynthesis) -> dict:
    """Wire conversion to the legacy JSON ``synthesis`` schema."""
    return {
        "reference_experiment_wls": str(synthesis.reference_experiment_wls),
        "methods": {
            method: {
                key: {
                    "R": str(center.ratio),
                    "deviation_vs_experiment_wls_1e18": center.deviation_vs_experiment_wls_1e18,
                }
                for key, center in per_scenario.items()
            }
            for method, per_scenario in synthesis.methods.items()
        },
        "goodness_of_fit": {
            key: {
                "chi2_red": goodness.chi2_red,
                "birge_ratio": goodness.birge_ratio,
                "xi_mp": goodness.xi_mp,
                "xi_bayes": goodness.xi_bayes,
                "u_wls": goodness.u_wls,
            }
            for key, goodness in synthesis.goodness_of_fit.items()
        },
        "long_term_stability": {
            key: {
                "y_i_std_1e18": stability.y_i_std_1e18,
                "improvement_vs_raw_pct": stability.improvement_vs_raw_pct,
            }
            for key, stability in synthesis.long_term_stability.items()
        },
    }
