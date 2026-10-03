"""Unit-consistent statistical combination for per-segment clock ratios."""
from __future__ import annotations

import numpy as np
from scipy import stats


def _validate_inputs(
    deviations: np.ndarray, uncertainties: np.ndarray, reference_ratio: float,
) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(deviations, dtype=float)
    u_absolute = np.asarray(uncertainties, dtype=float)
    if (y.ndim != 1 or u_absolute.ndim != 1 or len(y) != len(u_absolute)
            or len(y) < 2):
        raise ValueError("deviations and uncertainties must be aligned 1-D arrays with at least two rows")
    if (not np.isfinite(y).all() or not np.isfinite(u_absolute).all()
            or np.any(u_absolute <= 0) or not np.isfinite(reference_ratio)
            or reference_ratio <= 0):
        raise ValueError("inputs and reference_ratio must be finite, with positive uncertainties")
    return y, u_absolute / reference_ratio


def _mandel_paule(deviations: np.ndarray, uncertainties: np.ndarray) -> tuple[float, float, float]:
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
    deviations: np.ndarray, uncertainties: np.ndarray,
) -> tuple[float, float, float]:
    """Marginalize a Jeffreys-prior excess scatter on a uniform log-xi grid.

    The density is integrated with respect to log(xi).  The 1/xi Jeffreys
    prior and the dxi Jacobian therefore cancel; adding another 1/xi weight
    would double-count the prior.
    """
    scale = max(float(np.max(uncertainties)), float(np.ptp(deviations)), 1e-20)
    xi_grid = np.geomspace(max(scale * 1e-6, np.finfo(float).tiny), scale * 1e3, 401)
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

    log_posterior = np.asarray(log_posterior)
    log_posterior -= log_posterior.max()
    quadrature = np.ones(len(xi_grid))
    quadrature[[0, -1]] = 0.5
    posterior = np.exp(log_posterior) * quadrature
    posterior /= posterior.sum()
    means_array = np.asarray(means)
    variances_array = np.asarray(variances)
    mean = float(np.sum(posterior * means_array))
    variance = float(np.sum(posterior * (variances_array + (means_array - mean) ** 2)))
    return mean, float(np.sqrt(variance)), float(np.sum(posterior * xi_grid))


def combine(
    deviations: np.ndarray, uncertainties: np.ndarray, reference_ratio: float,
) -> dict[str, float]:
    """Combine fractional deviations with absolute-ratio uncertainties.

    ``deviations`` are relative to ``reference_ratio``.  The uncertainties are
    first converted to that same fractional unit for every fit and chi-square;
    uncertainty and excess-scatter outputs are converted back to absolute-ratio
    units for the persisted report schema.
    """
    yy, u = _validate_inputs(deviations, uncertainties, reference_ratio)
    weights = 1.0 / u**2
    y_wls = float(np.sum(weights * yy) / np.sum(weights))
    u_wls = float(1.0 / np.sqrt(np.sum(weights)))
    dof = len(yy) - 1
    chi2 = float(np.sum((yy - y_wls) ** 2 / u**2))
    chi2_red = chi2 / dof
    birge = float(np.sqrt(chi2_red))
    xi_mp, y_mp, u_mp = _mandel_paule(yy, u)
    mu_bayes, u_stat_bayes, xi_bayes = _bayesian_random_effects(yy, u)
    return {
        "y_wls": y_wls,
        "u_wls": u_wls * reference_ratio,
        "chi2": chi2,
        "dof": dof,
        "chi2_red": chi2_red,
        "p_chi2": float(stats.chi2.sf(chi2, dof)),
        "birge_ratio": birge,
        "u_birge": birge * u_wls * reference_ratio,
        "xi_mp": xi_mp * reference_ratio,
        "y_mp": y_mp,
        "u_mp": u_mp * reference_ratio,
        "mu_bayes": mu_bayes,
        "u_stat_bayes": u_stat_bayes * reference_ratio,
        "xi_bayes": xi_bayes * reference_ratio,
    }
