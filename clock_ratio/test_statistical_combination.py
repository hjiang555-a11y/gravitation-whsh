"""Regression contracts for unit-consistent clock-ratio combination."""
from __future__ import annotations

import numpy as np
import pytest

from clock_ratio.statistical_combination import combine


def test_chi2_when_deviations_are_fractional_and_uncertainties_are_absolute() -> None:
    reference = 1.2075070393433377
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
        1.2075070393433377,
    )

    for field in ("mu_bayes", "u_stat_bayes", "xi_bayes"):
        assert np.isfinite(result[field])
    assert result["u_stat_bayes"] > 0
