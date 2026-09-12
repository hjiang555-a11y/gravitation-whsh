"""Gap-safe overlapping Allan deviation and sample-duration weighted centers."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, localcontext
from math import isfinite, sqrt

import numpy as np

from clock_ratio.tidal_analysis import AnalysisError, FloatArray, SegmentResult, TimeArray


@dataclass(frozen=True, slots=True)
class AllanPoint:
    tau_s: int
    n_pairs: int
    sigma_y: float | None


def continuous_runs(times: TimeArray) -> tuple[tuple[int, int], ...]:
    """Return half-open index bounds, breaking at EVERY non-1-second step."""
    if times.ndim != 1 or np.isnat(times).any():
        raise AnalysisError("stability timestamps must be finite and one-dimensional")
    if not len(times):
        return ()
    breaks = np.flatnonzero(np.diff(times) != np.timedelta64(1, "s")) + 1
    bounds = [0, *(int(i) for i in breaks), len(times)]
    return tuple(zip(bounds[:-1], bounds[1:], strict=True))


def tau_grid(longest_run: int) -> tuple[int, ...]:
    """Prespecified dyadic seconds plus fixed taus, through longest_run // 4."""
    maximum = longest_run // 4
    dyadic = {2**i for i in range(maximum.bit_length())} if maximum > 0 else set()
    return tuple(sorted(dyadic | {t for t in (600, 1200, 3600, 7200) if t <= maximum}))


def oadev(times: TimeArray, y: FloatArray, taus: Sequence[int | float]) -> tuple[AllanPoint, ...]:
    """True OADEV: adjacent m-averages for every start i=0..N-2m.

    Each continuous run is numerically centered before prefix sums. Squared
    differences and counts are pooled ONLY inside this segment. n_pairs counts
    overlapping pairs, NOT independent degrees of freedom or SEM information.
    """
    if y.ndim != 1 or y.shape != times.shape or not np.isfinite(y).all():
        raise AnalysisError("stability values must be finite and aligned with timestamps")
    if any(not isfinite(t) or t <= 0 or int(t) != t for t in taus):
        raise AnalysisError("tau must be a positive integer number of seconds")
    prefixes: list[FloatArray] = []
    for start, stop in continuous_runs(times):
        run = y[start:stop]
        centered = run - run[0]
        centered = centered - centered.mean()
        prefixes.append(np.concatenate((np.zeros(1), np.cumsum(centered, dtype=np.float64))))
    points: list[AllanPoint] = []
    for tau in taus:
        m = int(tau)
        count, sum_squares = 0, 0.0
        for prefix in prefixes:
            n_pairs = len(prefix) - 2 * m
            if n_pairs <= 0:
                continue
            # N+1 prefix entries give exactly N-2m+1 overlapping differences.
            difference = (prefix[2 * m:] - 2 * prefix[m:-m] + prefix[:-2 * m]) / m
            sum_squares += float(np.dot(difference, difference))
            count += n_pairs
        sigma = sqrt(sum_squares / (2 * count)) if count else None
        points.append(AllanPoint(m, count, sigma))
    return tuple(points)


@dataclass(frozen=True, slots=True)
class DurationSummary:
    ratio: Decimal
    total_samples: int
    nsegments: int
    delta_r: Decimal
    delta_fractional_1e18: Decimal


def duration_summary(results: Sequence[SegmentResult]) -> DurationSummary:
    """Use the same n_valid weights for a scenario and its raw reference.

    This is a duration-weighted center, never inverse-variance WLS. The sample
    duration is n_valid * 1 second even when the retained timestamps have gaps.
    """
    if not results:
        raise AnalysisError("duration summary requires at least one segment")
    scenario = results[0].scenario
    if any(result.scenario != scenario for result in results):
        raise AnalysisError("duration summary cannot mix scenarios")
    if len({result.segment.group for result in results}) != len(results):
        raise AnalysisError("duration summary cannot count duplicate segment groups")
    with localcontext() as context:
        context.prec = 80
        total = sum(len(result.segment.beat) for result in results)
        ratio = sum((Decimal(len(r.segment.beat)) * r.ratio for r in results), Decimal(0)) / total
        raw = sum((Decimal(len(r.segment.beat)) * r.raw_ratio for r in results), Decimal(0)) / total
        return DurationSummary(ratio, total, len(results), ratio - raw,
                               (ratio / raw - 1) * Decimal("1e18"))
