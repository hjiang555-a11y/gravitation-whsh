"""Frozen raw selection and fixed-response tidal clock-ratio analysis.

Only raw beat data determine membership. Decimal80 inversion follows the
unchanged legacy formula; small corrections never touch the MHz float carrier.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from typing import Final, Literal

import numpy as np
from numpy.typing import NDArray

from clock import shared as s
from clock_ratio.compute_ratio import endpoint_screen, full_ratio

FloatArray = NDArray[np.float64]
TimeArray = NDArray[np.datetime64]
Windows = tuple[tuple[str, str], ...]


class AnalysisError(ValueError):
    """A source or analysis contract failed, with a human-readable detail."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class SelectionPlan:
    groups: Windows = tuple(s.GROUPS)
    shifts: tuple[Decimal, ...] = tuple(s.SHIFT_A)
    exclusions: Windows = tuple(s.EXCLUDE_RANGES)


@dataclass(frozen=True, slots=True)
class Segment:
    group: int
    times: TimeArray
    beat: FloatArray
    m_dec: Decimal
    shift_a: Decimal
    raw_mean: float
    rem_start: int
    rem_end: int


def select_segments(times: TimeArray, beat: FloatArray,
                    plan: SelectionPlan = SelectionPlan()) -> tuple[Segment, ...]:
    """Reproduce compute_ratio.main selection, including its index-span rule."""
    if times.ndim != 1 or beat.ndim != 1 or len(times) != len(beat) or not len(beat):
        raise AnalysisError("raw beat data must be nonempty aligned 1-D arrays")
    if np.isnat(times).any() or np.any(np.diff(times) < np.timedelta64(0, "s")):
        raise AnalysisError("raw timestamps must be finite and sorted (duplicates allowed)")
    if not plan.groups or len(plan.groups) != len(plan.shifts):
        raise AnalysisError("segment windows and shifts must be nonempty and aligned")
    excluded = np.zeros(len(times), dtype=bool)
    for start, end in plan.exclusions:
        excluded |= (times >= np.datetime64(start)) & (times <= np.datetime64(end))
    clean = beat.copy()
    clean[excluded] = np.nan
    plausible_global = (clean > 3e7) & (clean < 4e7)
    if not plausible_global.any():
        raise AnalysisError("raw beat data contain no plausible unexcluded samples")
    m_dec = s.to_dec(float(np.nanmedian(clean[plausible_global])))
    segments: list[Segment] = []
    for k, (start, end) in enumerate(plan.groups):
        inside = (times >= np.datetime64(start)) & (times < np.datetime64(end))
        t_seg, b_seg = times[inside], beat[inside]
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~excluded[inside]
        if not plausible.any():
            raise AnalysisError(f"segment {k + 1}: missing or empty plausible raw data")
        median = float(np.median(b_seg[plausible]))
        valid = plausible & (np.abs(b_seg - median) < s.JUMP_THRESHOLD)
        span = s.longest_valid_span(valid)
        if span is None:
            raise AnalysisError(f"segment {k + 1}: no valid raw span")
        kept, rem_start, rem_end = endpoint_screen(b_seg[span[0]:span[1] + 1])
        if not len(kept):
            raise AnalysisError(f"segment {k + 1}: empty after raw endpoint screen")
        retained_times = t_seg[span[0] + rem_start:span[1] + 1 - rem_end].copy()
        retained_beat = kept.copy()
        retained_times.setflags(write=False)
        retained_beat.setflags(write=False)
        segments.append(Segment(k + 1, retained_times, retained_beat, m_dec,
                                plan.shifts[k], float(kept.mean()), rem_start, rem_end))
    return tuple(segments)


@dataclass(frozen=True, slots=True)
class TideGrid:
    """Validated UTC grid; missing intervals may exist but cannot be bridged."""

    times: TimeArray
    delta_w: FloatArray

    def __post_init__(self) -> None:
        if (self.times.ndim != 1 or self.delta_w.ndim != 1
                or len(self.times) != len(self.delta_w) or len(self.times) < 2):
            raise AnalysisError("tide grid needs at least two aligned 1-D samples")
        if np.isnat(self.times).any() or not np.isfinite(self.delta_w).all():
            raise AnalysisError("tide timestamps and potential must be finite")
        seconds = self.times.astype("datetime64[s]").astype(np.int64)
        if (np.any(np.diff(self.times) <= np.timedelta64(0, "s"))
                or np.any(self.times != self.times.astype("datetime64[s]"))
                or np.any(seconds % 30 != 0)):
            raise AnalysisError("tide grid must be sorted, unique and on UTC 30-second ticks")
        object.__setattr__(self, "times", self.times.copy())
        object.__setattr__(self, "delta_w", self.delta_w.copy())
        self.times.setflags(write=False)
        self.delta_w.setflags(write=False)

    def beat_at(self, beijing_times: TimeArray) -> FloatArray:
        """Interpolate W(Wuhan)-W(Shanghai), then h=F1550*deltaW/c^2."""
        if beijing_times.ndim != 1 or np.isnat(beijing_times).any():
            raise AnalysisError("tide queries must be finite 1-D Beijing timestamps")
        utc = beijing_times - s.UTC_OFFSET
        if np.any(utc < self.times[0]) or np.any(utc > self.times[-1]):
            raise AnalysisError("tide query outside coverage; clamping/extrapolation forbidden")
        right = np.searchsorted(self.times, utc, side="left")
        interior = self.times[right] != utc
        hi = right[interior]
        if np.any(self.times[hi] - self.times[hi - 1] != np.timedelta64(30, "s")):
            raise AnalysisError("tide interpolation across a missing >30-second interval")
        origin = self.times[0]
        query_s = (utc - origin) / np.timedelta64(1, "s")
        grid_s = (self.times - origin) / np.timedelta64(1, "s")
        return np.interp(query_s, grid_s, self.delta_w) * s.F_1550 / s.C**2


@dataclass(frozen=True, slots=True)
class Scenario:
    key: Literal["raw", "theory", "empirical"]
    coefficient: Decimal


SCENARIOS: Final = (
    Scenario("raw", Decimal("0")),
    Scenario("theory", Decimal("-1")),
    Scenario("empirical", Decimal("-0.54")),
)


@dataclass(frozen=True, slots=True)
class SegmentResult:
    segment: Segment
    scenario: Scenario
    mean_tide_beat_hz: float
    mean_dm_raw: Decimal
    mean_dm_corrected: Decimal
    ratio: Decimal
    raw_ratio: Decimal
    delta_r: Decimal
    delta_fractional_1e18: Decimal
    fractional_std: float | None
    beat_std_hz: float | None
    fluctuations: FloatArray


def analyze_segment(segment: Segment, h: FloatArray, scenario: Scenario) -> SegmentResult:
    """Average corrected linear beat, then invert; never average point ratios.

    For stability R0 is ALWAYS the raw segment ratio, including for corrections.
    y=R(b)/R0-1 is evaluated as -q/(1+q), avoiding float-ratio cancellation.
    """
    if h.shape != segment.beat.shape or not np.isfinite(h).all():
        raise AnalysisError("tide beat template must be finite and match retained samples")
    if not scenario.coefficient.is_finite():
        raise AnalysisError("response coefficient must be finite")
    with localcontext() as context:
        context.prec = 80
        mean_h = float(h.mean())
        mean_dm_raw = s.to_dec(segment.raw_mean) - segment.m_dec
        mean_dm_corrected = mean_dm_raw - scenario.coefficient * s.to_dec(mean_h)
        raw_ratio = full_ratio(mean_dm_raw, segment.shift_a, segment.m_dec)
        ratio = full_ratio(mean_dm_corrected, segment.shift_a, segment.m_dec)
        coef1397 = (Decimal(1) + segment.shift_a) / Decimal(2)
        den = coef1397 / s.N1397 * (s.N1550 + s.D_7_25 + s.D_1_25)
        k = (s.COEF1156 / s.N1156) / (s.FREF * s.DIV20 * den)
        s0 = (Decimal(1) + s.DELTA_G) / raw_ratio
        residual = (segment.beat - segment.raw_mean) - float(scenario.coefficient) * h
        q = float(k / s0) * residual
        if not np.isfinite(q).all() or np.any(1 + q <= 0):
            raise AnalysisError("corrected beat is outside the positive ratio domain")
        fluctuations = -q / (1 + q)
        fluctuations.setflags(write=False)
        fractional_std = float(fluctuations.std(ddof=1)) if len(h) > 1 else None
        beat_std = float(residual.std(ddof=1)) if len(h) > 1 else None
        return SegmentResult(segment, scenario, mean_h, mean_dm_raw, mean_dm_corrected,
                             ratio, raw_ratio, ratio - raw_ratio,
                             (ratio / raw_ratio - 1) * Decimal("1e18"),
                             fractional_std, beat_std, fluctuations)
