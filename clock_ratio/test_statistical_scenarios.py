"""Contracts for the unified raw/tidal scenario layer (synthetic data only).

One per-segment fact layer feeds raw/theory/empirical; exclusions and the
leave-one-out sweep recompute combinations from those facts, never from
pre-generated JSON.  Raw must reproduce ``analyze_raw_statistics`` field for
field; the renderer must preserve the legacy JSON document schema exactly.
"""
from __future__ import annotations

from dataclasses import fields, replace
from decimal import Decimal, localcontext
from statistics import stdev

import numpy as np
import pytest

from clock.sample_selection import AnalysisError, SelectedSegment, SelectionDiagnostics
from clock_ratio.segment_uncertainty import StabilityFitConfig
from clock_ratio.statistical_methods import analyze_raw_statistics
from clock_ratio.statistical_models import CombinationResult
from clock_ratio.statistical_scenarios import (
    ScenarioSegmentResult,
    StatisticalScenarioResult,
    _build_scenario_result,
    analyze_scenario,
    analyze_scenarios,
    build_synthesis,
    exclude_groups,
    leave_one_out,
    render_synthesis,
    u_absolute,
    y_i_1e18,
)
from clock_ratio.tidal_analysis import SCENARIOS, TideGrid, analyze_segment

BASE = np.datetime64("2026-01-01T00:00:00")
GROUP_STEP_S = 10_000
COUNT = 4096
CONFIG = StabilityFitConfig()


def _times(group: int, count: int) -> np.ndarray:
    start = BASE + np.timedelta64((group - 1) * GROUP_STEP_S, "s")
    return start + np.arange(count).astype("timedelta64[s]")


def synthetic_segment(group: int, count: int = COUNT) -> SelectedSegment:
    rng = np.random.default_rng(1000 + group)
    times = _times(group, count)
    beat = 33_000_000.0 + rng.normal(0.0, 0.2, count)
    diagnostics = SelectionDiagnostics(
        n_window=count, n_excluded=0, n_plausible=count, n_jump_valid=count,
        n_longest_span=count, n_removed_start=0, n_removed_end=0, n_final=count,
        source_span_start=0, source_span_stop=count,
    )
    return SelectedSegment(
        group=group, times=times, beat=beat, m_dec=Decimal("33623140.92"),
        shift_a=Decimal(0), raw_mean=float(beat.mean()), rem_start=0, rem_end=0,
        diagnostics=diagnostics,
    )


def synthetic_tide(segments: tuple[SelectedSegment, ...]) -> TideGrid:
    first = segments[0].times[0] - np.timedelta64(8, "h")
    last = segments[-1].times[-1] - np.timedelta64(8, "h")
    span_s = int((last - first) / np.timedelta64(1, "s"))
    offsets = np.arange(0, span_s + 60, 30)
    ticks = first + offsets.astype("timedelta64[s]")
    return TideGrid(ticks, 3000.0 * np.sin(2.0 * np.pi * offsets / 86400.0))


SEGMENTS = tuple(synthetic_segment(group) for group in range(1, 18))
TIDE = synthetic_tide(SEGMENTS)


@pytest.fixture(scope="module")
def scenario_results() -> dict[str, StatisticalScenarioResult]:
    return analyze_scenarios(SEGMENTS, TIDE, CONFIG)


@pytest.fixture(scope="module")
def full_result(scenario_results: dict[str, StatisticalScenarioResult]) -> StatisticalScenarioResult:
    return scenario_results["raw"]


def test_excluding_group_9_produces_declared_primary_16(full_result: StatisticalScenarioResult) -> None:
    primary = exclude_groups(full_result, frozenset({9}))
    assert primary.included_groups == tuple(g for g in range(1, 18) if g != 9)
    assert primary.excluded_groups == (9,)
    assert primary.combination.n == 16


def test_leave_one_out_covers_each_group_once(full_result: StatisticalScenarioResult) -> None:
    results = leave_one_out(full_result)
    assert set(results) == set(range(1, 18))
    assert all(len(r.included_groups) == 16 for r in results.values())


def test_leave_one_out_excludes_each_group_alone(full_result: StatisticalScenarioResult) -> None:
    results = leave_one_out(full_result)
    for group, result in results.items():
        assert result.excluded_groups == (group,)
        assert group not in result.included_groups
        assert len(result.included_groups) == 16


def test_raw_scenario_matches_analyze_raw_statistics_field_by_field(
    scenario_results: dict[str, StatisticalScenarioResult],
) -> None:
    # Given the same segments, the raw scenario and the raw-only entry point.
    ratios = {
        segment.group: analyze_segment(segment, np.zeros(len(segment.beat)), SCENARIOS[0]).ratio
        for segment in SEGMENTS
    }

    # When both run.
    raw_results, raw_combined = analyze_raw_statistics(SEGMENTS, ratios, CONFIG)
    raw_scenario = scenario_results["raw"]

    # Then ratios never round-trip through float and every fact matches.
    assert raw_scenario.scenario == "raw"
    assert raw_scenario.coefficient == 0.0
    assert raw_scenario.combination.reference_ratio == ratios[1]
    assert raw_scenario.included_groups == tuple(range(1, 18))
    assert raw_scenario.total_samples == sum(len(segment.beat) for segment in SEGMENTS)
    for fact, fit in zip(raw_scenario.segments, raw_results, strict=True):
        assert fact.uncertainty == fit
        assert fact.deviation == float(ratios[fact.group] / ratios[1] - Decimal(1))
        assert u_absolute(fact) == float(Decimal(repr(fit.u_fractional)) * ratios[fact.group])

    # And the combination is bit-identical field by field.
    for field in fields(CombinationResult):
        assert getattr(raw_scenario.combination, field.name) == getattr(raw_combined, field.name)


def test_excluding_the_empty_set_reproduces_the_full_result(full_result: StatisticalScenarioResult) -> None:
    rebuilt = exclude_groups(full_result, frozenset())
    assert rebuilt.combination == full_result.combination
    assert rebuilt.duration_weighted_ratio == full_result.duration_weighted_ratio
    assert rebuilt.total_samples == full_result.total_samples
    assert rebuilt.included_groups == full_result.included_groups
    assert rebuilt.excluded_groups == ()


def test_duplicate_groups_are_rejected() -> None:
    with pytest.raises(AnalysisError, match="unique"):
        analyze_scenario((SEGMENTS[0], SEGMENTS[0]), TIDE, SCENARIOS[0])


def test_missing_segment_one_baseline_is_rejected() -> None:
    with pytest.raises(AnalysisError, match="segment-1"):
        analyze_scenario(SEGMENTS[1:3], TIDE, SCENARIOS[0])


def test_short_segment_with_undefined_uncertainty_is_rejected() -> None:
    short = synthetic_segment(2, count=600)
    with pytest.raises(AnalysisError, match="segment 2"):
        analyze_scenario((SEGMENTS[0], short), TIDE, SCENARIOS[0])


def test_excluding_an_absent_group_is_rejected(full_result: StatisticalScenarioResult) -> None:
    with pytest.raises(AnalysisError, match="absent"):
        exclude_groups(full_result, frozenset({99}))


def test_tampered_facts_are_rejected_on_rebuild(full_result: StatisticalScenarioResult) -> None:
    bad_deviation = replace(full_result.segments[0], deviation=float("nan"))
    with pytest.raises(AnalysisError, match="deviation"):
        _build_scenario_result(
            full_result.scenario, full_result.coefficient,
            (bad_deviation, *full_result.segments[1:]), (), None)
    bad_uncertainty = replace(full_result.segments[0].uncertainty, u_fractional=None)
    bad_fact = replace(full_result.segments[0], uncertainty=bad_uncertainty)
    with pytest.raises(AnalysisError, match="u_fractional"):
        _build_scenario_result(
            full_result.scenario, full_result.coefficient,
            (bad_fact, *full_result.segments[1:]), (), None)


def test_synthesis_renderer_preserves_legacy_schema(
    scenario_results: dict[str, StatisticalScenarioResult],
) -> None:
    document = render_synthesis(build_synthesis(scenario_results))
    assert set(document) == {"reference_experiment_wls", "methods", "goodness_of_fit", "long_term_stability"}
    assert document["reference_experiment_wls"] == "1.2075070393433377213"
    assert set(document["methods"]) == {"R_wls", "R_mp", "R_bayes"}
    for per_scenario in document["methods"].values():
        assert set(per_scenario) == {"raw", "theory", "empirical"}
        for entry in per_scenario.values():
            assert set(entry) == {"R", "deviation_vs_experiment_wls_1e18"}
            assert isinstance(entry["R"], str)
            assert isinstance(entry["deviation_vs_experiment_wls_1e18"], float)
    for key in ("raw", "theory", "empirical"):
        assert set(document["goodness_of_fit"][key]) == {"chi2_red", "birge_ratio", "xi_mp", "xi_bayes", "u_wls"}
        assert set(document["long_term_stability"][key]) == {"y_i_std_1e18", "improvement_vs_raw_pct"}
    assert document["long_term_stability"]["raw"]["improvement_vs_raw_pct"] == 0.0


def test_synthesis_values_follow_the_documented_arithmetic(
    scenario_results: dict[str, StatisticalScenarioResult],
) -> None:
    document = render_synthesis(build_synthesis(scenario_results))
    raw = scenario_results["raw"]
    with localcontext() as context:
        context.prec = 80
        reference = raw.combination.reference_ratio
        for method, field_name in (("R_wls", "y_wls"), ("R_mp", "y_mp"), ("R_bayes", "mu_bayes")):
            ratio = reference * (Decimal(1) + Decimal(repr(getattr(raw.combination, field_name))))
            entry = document["methods"][method]["raw"]
            assert entry["R"] == str(ratio)
            expected = float((ratio - Decimal("1.2075070393433377213")) * Decimal("1e18"))
            assert entry["deviation_vs_experiment_wls_1e18"] == expected
    std = stdev([y_i_1e18(fact, reference) for fact in raw.segments])
    assert document["long_term_stability"]["raw"]["y_i_std_1e18"] == std
