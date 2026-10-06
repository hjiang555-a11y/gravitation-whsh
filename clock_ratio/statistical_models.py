"""Typed statistical-combination core for per-segment clock-ratio estimates.

All fits (WLS, Birge, Mandel-Paule, Bayesian random effects) run in fractional
units ``u_i / R_reference``; uncertainty and excess-scatter outputs are returned
in absolute-ratio units.  The Bayesian excess scatter is marginalized on a
uniform log-xi grid; the 1/xi Jeffreys prior and the dxi Jacobian cancel, so no
extra 1/xi weight is applied.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Literal, Sequence

import numpy as np
from scipy import stats

_BAYES_EDGE_BINS: Final = 3
_BAYES_EDGE_LIMIT: Final = 0.01
_BAYES_MAX_EXPANSIONS: Final = 6


@dataclass(frozen=True, slots=True)
class SegmentEstimate:
    group: int
    ratio: Decimal
    deviation: float
    u_absolute: float


@dataclass(frozen=True, slots=True)
class CombinationConfig:
    bayes_grid_points: int = 401
    bayes_log_span: tuple[float, float] = (1e-6, 1e3)
    prior: Literal["jeffreys"] = "jeffreys"


@dataclass(frozen=True, slots=True)
class CombinationResult:
    reference_ratio: Decimal
    n: int
    y_wls: float
    u_wls: float
    chi2: float
    dof: int
    chi2_red: float
    p_chi2: float
    birge_ratio: float
    u_birge: float
    xi_mp: float
    y_mp: float
    u_mp: float
    mu_bayes: float
    u_stat_bayes: float
    xi_bayes: float
    bayes_log_span_used: tuple[float, float]
    bayes_edge_mass: tuple[float, float]


def _validated_fractional_arrays(
    estimates: Sequence[SegmentEstimate], reference_ratio: Decimal,
) -> tuple[np.ndarray, np.ndarray]:
    items = tuple(estimates)
    if len(items) < 2:
        raise ValueError("combination requires at least two segment estimates")
    groups = [estimate.group for estimate in items]
    if len(set(groups)) != len(groups):
        raise ValueError("segment groups must be unique")
    if not reference_ratio.is_finite() or reference_ratio <= 0:
        raise ValueError("reference ratio must be finite and positive")
    for estimate in items:
        if not estimate.ratio.is_finite() or estimate.ratio <= 0:
            raise ValueError(f"segment {estimate.group}: ratio must be finite and positive")
        if not math.isfinite(estimate.deviation):
            raise ValueError(f"segment {estimate.group}: deviation must be finite")
        if not math.isfinite(estimate.u_absolute) or estimate.u_absolute <= 0:
            raise ValueError(
                f"segment {estimate.group}: absolute uncertainty must be finite and positive")
    deviations = np.asarray([estimate.deviation for estimate in items], dtype=float)
    uncertainties = (
        np.asarray([estimate.u_absolute for estimate in items], dtype=float)
        / float(reference_ratio)
    )
    return deviations, uncertainties


def _mandel_paule(
    deviations: np.ndarray, uncertainties: np.ndarray,
) -> tuple[float, float, float]:
    """Return (xi, weighted mean, uncertainty) in fractional-ratio units."""
    dof = len(deviations) - 1

    def reduced_chi2(xi: float) -> float:
        variance = uncertainties**2 + xi**2
        weights = 1.0 / variance
        mean = float(np.sum(weights * deviations) / np.sum(weights))
        return float(np.sum((deviations - mean) ** 2 / variance) / dof)

    if reduced_chi2(0.0) <= 1.0:
        weights = 1.0 / uncertainties**2
        return 0.0, float(np.sum(weights * deviations) / np.sum(weights)), float(1.0 / np.sqrt(np.sum(weights)))

    lo = 0.0
    hi = max(float(np.max(uncertainties)), float(np.ptp(deviations)), np.finfo(float).tiny)
    while reduced_chi2(hi) > 1.0:
        hi *= 2.0
        if not np.isfinite(hi):
            raise ValueError("could not bracket the Mandel-Paule excess-scatter root")
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if reduced_chi2(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    xi = (lo + hi) / 2.0
    weights = 1.0 / (uncertainties**2 + xi**2)
    return xi, float(np.sum(weights * deviations) / np.sum(weights)), float(1.0 / np.sqrt(np.sum(weights)))


def _bayesian_random_effects(
    deviations: np.ndarray, uncertainties: np.ndarray, config: CombinationConfig,
) -> tuple[float, float, float, tuple[float, float], tuple[float, float]]:
    """Marginalize a Jeffreys-prior excess scatter on an adaptive log-xi grid.

    Returns (posterior mean, posterior sd, posterior-mean xi, realized span
    multipliers, edge masses).  A side whose outermost-edge mass stays above
    1% widens by x10, at most ``_BAYES_MAX_EXPANSIONS`` times; failing that the
    grid is unconverged and a ValueError is raised.
    """
    span_low, span_high = config.bayes_log_span
    scale = max(float(np.max(uncertainties)), float(np.ptp(deviations)), 1e-20)
    for attempt in range(_BAYES_MAX_EXPANSIONS + 1):
        xi_grid = np.geomspace(
            max(scale * span_low, np.finfo(float).tiny),
            scale * span_high,
            config.bayes_grid_points,
        )
        means: list[float] = []
        variances: list[float] = []
        log_posterior: list[float] = []
        for xi in xi_grid:
            variance = uncertainties**2 + xi**2
            weights = 1.0 / variance
            mean = float(np.sum(weights * deviations) / np.sum(weights))
            log_likelihood_at_mean = -0.5 * np.sum(
                (deviations - mean) ** 2 / variance + np.log(2.0 * np.pi * variance))
            log_posterior.append(float(log_likelihood_at_mean
                                      + 0.5 * np.log(2.0 * np.pi / np.sum(weights))))
            means.append(mean)
            variances.append(float(1.0 / np.sum(weights)))

        log_posterior_array = np.asarray(log_posterior)
        log_posterior_array -= log_posterior_array.max()
        quadrature = np.ones(len(xi_grid))
        quadrature[[0, -1]] = 0.5
        posterior = np.exp(log_posterior_array) * quadrature
        posterior /= posterior.sum()
        edge_mass = (
            float(posterior[:_BAYES_EDGE_BINS].sum()),
            float(posterior[-_BAYES_EDGE_BINS:].sum()),
        )
        if max(edge_mass) <= _BAYES_EDGE_LIMIT:
            means_array = np.asarray(means)
            variances_array = np.asarray(variances)
            mean = float(np.sum(posterior * means_array))
            variance = float(np.sum(posterior * (variances_array + (means_array - mean) ** 2)))
            return (mean, float(np.sqrt(variance)), float(np.sum(posterior * xi_grid)),
                    (span_low, span_high), edge_mass)
        if attempt == _BAYES_MAX_EXPANSIONS:
            raise ValueError(
                f"unconverged Bayesian log-xi grid after {_BAYES_MAX_EXPANSIONS} expansions: "
                f"edge masses {edge_mass}")
        if edge_mass[0] > _BAYES_EDGE_LIMIT:
            span_low /= 10.0
        if edge_mass[1] > _BAYES_EDGE_LIMIT:
            span_high *= 10.0
    raise AssertionError("unreachable Bayesian grid state")


def combine_estimates(
    estimates: Sequence[SegmentEstimate],
    reference_ratio: Decimal,
    config: CombinationConfig | None = None,
) -> CombinationResult:
    if config is None:
        config = CombinationConfig()
    if config.prior != "jeffreys":
        raise ValueError(f"unsupported prior: {config.prior!r}")
    if config.bayes_grid_points < 2 * _BAYES_EDGE_BINS:
        raise ValueError("bayesian grid needs at least twice the edge-bin count of points")
    y, u = _validated_fractional_arrays(estimates, reference_ratio)
    reference = float(reference_ratio)

    weights = 1.0 / u**2
    y_wls = float(np.sum(weights * y) / np.sum(weights))
    u_wls = float(1.0 / np.sqrt(np.sum(weights)))
    dof = len(y) - 1
    chi2 = float(np.sum((y - y_wls) ** 2 / u**2))
    chi2_red = chi2 / dof
    birge = float(np.sqrt(chi2_red))
    xi_mp, y_mp, u_mp = _mandel_paule(y, u)
    mu_bayes, u_stat_bayes, xi_bayes, span_used, edge_mass = _bayesian_random_effects(y, u, config)
    return CombinationResult(
        reference_ratio=reference_ratio,
        n=len(y),
        y_wls=y_wls,
        u_wls=u_wls * reference,
        chi2=chi2,
        dof=dof,
        chi2_red=chi2_red,
        p_chi2=float(stats.chi2.sf(chi2, dof)),
        birge_ratio=birge,
        u_birge=birge * u_wls * reference,
        xi_mp=xi_mp * reference,
        y_mp=y_mp,
        u_mp=u_mp * reference,
        mu_bayes=mu_bayes,
        u_stat_bayes=u_stat_bayes * reference,
        xi_bayes=xi_bayes * reference,
        bayes_log_span_used=span_used,
        bayes_edge_mass=edge_mass,
    )
