"""Compatibility wrapper: the statistical-combination core now lives in
``clock_ratio.statistical_models``; this module preserves the historical
``combine()`` dict interface and its field names for existing callers.
"""
from __future__ import annotations

from decimal import Decimal

import numpy as np

from clock_ratio.statistical_models import SegmentEstimate, combine_estimates


def combine(
    deviations: np.ndarray, uncertainties: np.ndarray, reference_ratio: float,
) -> dict[str, float]:
    """Combine fractional deviations with absolute-ratio uncertainties.

    ``deviations`` are relative to ``reference_ratio``.  The uncertainties are
    first converted to that same fractional unit for every fit and chi-square;
    uncertainty and excess-scatter outputs are converted back to absolute-ratio
    units for the persisted report schema.
    """
    y = np.asarray(deviations, dtype=float)
    u_absolute = np.asarray(uncertainties, dtype=float)
    if (y.ndim != 1 or u_absolute.ndim != 1 or len(y) != len(u_absolute)
            or len(y) < 2):
        raise ValueError("deviations and uncertainties must be aligned 1-D arrays with at least two rows")
    ratio = Decimal(repr(float(reference_ratio)))
    estimates = [
        SegmentEstimate(group=index + 1, ratio=ratio,
                        deviation=float(y[index]), u_absolute=float(u_absolute[index]))
        for index in range(len(y))
    ]
    result = combine_estimates(estimates, ratio)
    return {
        "y_wls": result.y_wls,
        "u_wls": result.u_wls,
        "chi2": result.chi2,
        "dof": result.dof,
        "chi2_red": result.chi2_red,
        "p_chi2": result.p_chi2,
        "birge_ratio": result.birge_ratio,
        "u_birge": result.u_birge,
        "xi_mp": result.xi_mp,
        "y_mp": result.y_mp,
        "u_mp": result.u_mp,
        "mu_bayes": result.mu_bayes,
        "u_stat_bayes": result.u_stat_bayes,
        "xi_bayes": result.xi_bayes,
    }
