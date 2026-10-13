"""Gap-safe per-segment statistical uncertainty from true overlapping ADEV.

The estimator evaluates ``sigma_y`` on the prespecified tau grid (up to a
quarter of the longest gap-free run) and adopts the **last computable point**
as the segment uncertainty: ``u = sigma_y(tau_max)`` with no log-log fit and no
extrapolation to the segment duration.  Runs never cross a gap or a duplicate
timestamp; that guarantee comes from ``tidal_stability.oadev`` /
``continuous_runs``.

The slope of ``log sigma_y`` vs ``log tau`` is still computed as a diagnostic:
when it leaves the white-frequency-noise band ``[-0.65, -0.35]`` the result is
flagged ``supported-with-limitations`` (the last-point value is still
reported).  When no computable point reaches ``fit_min_s`` the estimator
refuses to report any value instead of silently reusing a shorter tau.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from clock.sample_selection import AnalysisError, FloatArray, TimeArray
from clock_ratio.tidal_stability import continuous_runs, oadev, tau_grid

# White frequency noise has Allan slope -1/2; the acceptance band is the ruling
# from the audit plan (conservative flag outside it, never silent trust).
ESTABLISHED_SLOPE_BAND = (-0.65, -0.35)


@dataclass(frozen=True, slots=True)
class StabilityFitConfig:
    tau0_s: int = 1
    fit_min_s: int = 128
    fit_max_fraction: float = 0.25
    estimator: Literal["gap_safe_oadev"] = "gap_safe_oadev"

    def __post_init__(self) -> None:
        if self.tau0_s != 1:
            raise AnalysisError("gap-safe OADEV assumes a 1-second sample interval")
        if self.fit_min_s < 1:
            raise AnalysisError("fit_min_s must be a positive number of seconds")
        if not 0.0 < self.fit_max_fraction <= 1.0:
            raise AnalysisError("fit_max_fraction must lie in (0, 1]")


@dataclass(frozen=True, slots=True)
class SegmentUncertainty:
    group: int | None
    n_valid: int
    n_runs: int
    taus_s: tuple[int, ...]
    sigma_y: tuple[float, ...]
    fit_slope: float | None
    fit_intercept: float | None
    u_fractional: float | None
    status: Literal["established", "supported-with-limitations", "pending-verification"]


def estimate_segment_uncertainty(
    times: TimeArray, y: FloatArray, config: StabilityFitConfig,
) -> SegmentUncertainty:
    """Adopt the last computable OADEV point as the segment uncertainty.

    ``y`` is the segment's fractional frequency; each run is centered inside
    ``oadev``.  The returned ``group`` is always None -- segment identity is
    attached by the caller (``analyze_raw_statistics``).  The log-log slope is
    kept as a white-frequency-noise diagnostic only.
    """
    runs = continuous_runs(times)
    longest_run = max((stop - start for start, stop in runs), default=0)
    taus = tau_grid(longest_run)
    points = oadev(times, y, taus)
    defined = [(point.tau_s, float(point.sigma_y))
               for point in points if point.sigma_y is not None]
    taus_s = tuple(tau for tau, _ in defined)
    sigma_y = tuple(sigma for _, sigma in defined)

    if not defined or max(tau for tau, _ in defined) < config.fit_min_s:
        # Conservative fallback: no computable point at or above the minimum
        # tau -- never reuse a shorter-than-allowed point silently.
        return SegmentUncertainty(
            group=None, n_valid=len(times), n_runs=len(runs), taus_s=taus_s,
            sigma_y=sigma_y, fit_slope=None, fit_intercept=None,
            u_fractional=None, status="supported-with-limitations",
        )

    u_fractional = defined[-1][1]

    upper = config.fit_max_fraction * longest_run
    usable = [(tau, sigma) for tau, sigma in defined
              if config.fit_min_s <= tau <= upper and sigma > 0.0]
    slope = intercept = None
    if len(usable) >= 3:
        log_tau = np.log([tau for tau, _ in usable])
        log_sigma = np.log([sigma for _, sigma in usable])
        slope, intercept = (float(value) for value in np.polyfit(log_tau, log_sigma, 1))

    status: Literal["established", "supported-with-limitations"] = (
        "established"
        if slope is not None and ESTABLISHED_SLOPE_BAND[0] <= slope <= ESTABLISHED_SLOPE_BAND[1]
        else "supported-with-limitations"
    )
    return SegmentUncertainty(
        group=None, n_valid=len(times), n_runs=len(runs), taus_s=taus_s,
        sigma_y=sigma_y, fit_slope=slope, fit_intercept=intercept,
        u_fractional=float(u_fractional), status=status,
    )
