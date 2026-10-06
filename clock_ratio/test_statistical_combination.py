"""Regression contracts for unit-consistent clock-ratio combination."""
from __future__ import annotations

from decimal import Decimal

import numpy as np
import pytest

from clock_ratio.statistical_combination import combine
from clock_ratio.statistical_models import (
    CombinationConfig,
    CombinationResult,
    SegmentEstimate,
    combine_estimates,
)

REFERENCE_RATIO = 1.2075070393433377


def test_chi2_when_deviations_are_fractional_and_uncertainties_are_absolute() -> None:
    reference = REFERENCE_RATIO
    y = np.array([-4.0, 0.0, 5.0]) * 1e-18
    u_absolute = np.array([1.0, 2.0, 1.5]) * 1e-18
    result = combine(y, u_absolute, reference)

    u_fractional = u_absolute / reference
    weights = 1.0 / u_fractional**2
    expected_mean = np.sum(weights * y) / np.sum(weights)
    expected_chi2 = np.sum((y - expected_mean) ** 2 / u_fractional**2)

    assert result["y_wls"] == pytest.approx(expected_mean)
    assert result["chi2"] == pytest.approx(expected_chi2)
    assert result["u_wls"] == pytest.approx(1.0 / np.sqrt(np.sum(weights)) * reference)


def test_mandel_paule_when_initial_bracket_is_too_small() -> None:
    reference = 1.2
    y = np.array([-1.0, 1.0]) * 1e-15
    u_absolute = np.full(2, 1e-18)
    result = combine(y, u_absolute, reference)

    assert result["xi_mp"] > 1e-16
    assert result["chi2"] / (1 + (result["xi_mp"] / reference / (u_absolute[0] / reference)) ** 2) == pytest.approx(1.0, rel=1e-10)


def test_bayesian_combination_is_finite_after_log_space_marginalization() -> None:
    result = combine(
        np.array([-2.0, 0.5, 3.0]) * 1e-18,
        np.array([1.0, 1.2, 0.9]) * 1e-18,
        REFERENCE_RATIO,
    )

    for field in ("mu_bayes", "u_stat_bayes", "xi_bayes"):
        assert np.isfinite(result[field])
    assert result["u_stat_bayes"] > 0


SNAPSHOT_REFERENCE = Decimal("1.2075")
SNAPSHOT_DEVIATIONS = (0.0, 1.0e-18, -0.5e-18, 2.0e-18)
SNAPSHOT_UNCERTAINTIES = (1.0e-18, 1.2e-18, 0.9e-18, 1.1e-18)


def _snapshot_estimates() -> tuple[SegmentEstimate, ...]:
    return tuple(
        SegmentEstimate(group, SNAPSHOT_REFERENCE, y, u)
        for group, (y, u) in enumerate(
            zip(SNAPSHOT_DEVIATIONS, SNAPSHOT_UNCERTAINTIES, strict=True), start=1)
    )


@pytest.mark.parametrize("bad_u", [0.0, -1.0, np.nan, np.inf])
def test_combine_rejects_invalid_uncertainty(bad_u):
    estimates = [
        SegmentEstimate(1, Decimal("1.2"), 0.0, 1e-18),
        SegmentEstimate(2, Decimal("1.2"), 1e-18, bad_u),
    ]
    with pytest.raises(ValueError):
        combine_estimates(estimates, Decimal("1.2"))


def test_combination_snapshot():
    result = combine_estimates(_snapshot_estimates(), SNAPSHOT_REFERENCE)

    assert isinstance(result, CombinationResult)
    assert result.n == 4
    assert result.dof == 3
    # abs=0.0: at 1e-19 scale the default 1e-12 absolute tolerance would make
    # these guards vacuous (they would also accept 0.0).
    assert result.y_wls == pytest.approx(4.606769046858974e-19, rel=1e-12, abs=0.0)
    assert result.chi2_red == pytest.approx(1.7068376113910986, rel=1e-12)
    assert result.u_stat_bayes == pytest.approx(6.372514260551814e-19, rel=1e-12, abs=0.0)
    assert result.xi_bayes == pytest.approx(2.4323182678604663e-19, rel=1e-12, abs=0.0)


def test_combination_snapshot_matches_hand_computed_wls():
    result = combine_estimates(_snapshot_estimates(), SNAPSHOT_REFERENCE)
    deviations = np.asarray(SNAPSHOT_DEVIATIONS)
    u_fractional = np.asarray(SNAPSHOT_UNCERTAINTIES) / float(SNAPSHOT_REFERENCE)
    weights = 1.0 / u_fractional**2
    hand_mean = float(np.sum(weights * deviations) / np.sum(weights))

    assert result.y_wls == pytest.approx(hand_mean, rel=1e-12, abs=0.0)
    assert result.chi2 == pytest.approx(
        float(np.sum((deviations - hand_mean) ** 2 / u_fractional**2)), rel=1e-12)
    assert result.birge_ratio == pytest.approx(np.sqrt(result.chi2 / result.dof), rel=1e-12)


def test_combination_is_invariant_under_common_rescaling():
    factor = 4.0
    reference = SNAPSHOT_REFERENCE
    base = combine_estimates(_snapshot_estimates(), reference)
    scaled = combine_estimates(
        tuple(
            SegmentEstimate(est.group, est.ratio, est.deviation * factor,
                            est.u_absolute * factor)
            for est in _snapshot_estimates()
        ),
        reference,
    )

    assert scaled.chi2 == pytest.approx(base.chi2, rel=1e-12)
    assert scaled.chi2_red == pytest.approx(base.chi2_red, rel=1e-12)
    assert scaled.birge_ratio == pytest.approx(base.birge_ratio, rel=1e-12)
    for field in ("y_wls", "u_wls", "xi_mp", "y_mp", "u_mp", "mu_bayes",
                  "u_stat_bayes", "xi_bayes"):
        assert getattr(scaled, field) == pytest.approx(
            getattr(base, field) * factor, rel=1e-12, abs=0.0)


def test_combination_records_default_bayesian_grid_when_converged():
    result = combine_estimates(_snapshot_estimates(), SNAPSHOT_REFERENCE)

    assert result.bayes_log_span_used == CombinationConfig().bayes_log_span
    assert max(result.bayes_edge_mass) <= 0.01


def test_combination_expands_bayesian_grid_until_edges_converge():
    estimates = tuple(
        SegmentEstimate(group, Decimal("1.2"), 0.0, 1.0e-18)
        for group in range(1, 18)
    )
    default_span = CombinationConfig().bayes_log_span
    result = combine_estimates(estimates, Decimal("1.2"))

    # The low-side mass starts just above 1%, so exactly one low-side
    # expansion (x10 outward) must converge the grid.
    assert result.bayes_log_span_used[0] == pytest.approx(default_span[0] / 10.0, rel=1e-12)
    assert result.bayes_log_span_used[1] == pytest.approx(default_span[1], rel=1e-12)
    assert max(result.bayes_edge_mass) <= 0.01
    assert np.isfinite(result.u_stat_bayes) and result.u_stat_bayes > 0


def test_combination_rejects_unconverged_bayesian_grid():
    uncertainties = (1.0e-3,) + (1.0e-18,) * 16
    estimates = tuple(
        SegmentEstimate(group, Decimal("1.2"), 0.0, u)
        for group, u in enumerate(uncertainties, start=1)
    )
    with pytest.raises(ValueError, match="unconverged"):
        combine_estimates(estimates, Decimal("1.2"))


def test_combination_rejects_duplicate_groups():
    estimates = [
        SegmentEstimate(1, Decimal("1.2"), 0.0, 1e-18),
        SegmentEstimate(1, Decimal("1.2"), 1e-18, 1e-18),
    ]
    with pytest.raises(ValueError):
        combine_estimates(estimates, Decimal("1.2"))


def test_combination_rejects_single_segment():
    with pytest.raises(ValueError):
        combine_estimates([SegmentEstimate(1, Decimal("1.2"), 0.0, 1e-18)], Decimal("1.2"))


@pytest.mark.parametrize("bad_y", [np.nan, np.inf, -np.inf])
def test_combination_rejects_non_finite_deviation(bad_y):
    estimates = [
        SegmentEstimate(1, Decimal("1.2"), 0.0, 1e-18),
        SegmentEstimate(2, Decimal("1.2"), bad_y, 1e-18),
    ]
    with pytest.raises(ValueError):
        combine_estimates(estimates, Decimal("1.2"))


@pytest.mark.parametrize(
    "bad_reference",
    [Decimal("0"), Decimal("-1.2"), Decimal("NaN"), Decimal("Infinity")],
)
def test_combination_rejects_non_positive_reference(bad_reference):
    with pytest.raises(ValueError):
        combine_estimates(_snapshot_estimates(), bad_reference)
