"""Unified raw-sample selection for clock-ratio analyses."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

import numpy as np
from numpy.typing import NDArray

from clock.shared import EXCLUDE_RANGES, GROUPS, JUMP_THRESHOLD, SHIFT_A, longest_valid_span, to_dec

FloatArray = NDArray[np.float64]
TimeArray = NDArray[np.datetime64]
Windows = tuple[tuple[str, str], ...]


class AnalysisError(ValueError):
    """A source or analysis contract failed, with a human-readable detail."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True, slots=True)
class EndpointScreen:
    start: int
    stop: int
    removed_start: int
    removed_end: int


@dataclass(frozen=True, slots=True)
class SelectionDiagnostics:
    n_window: int
    n_excluded: int
    n_plausible: int
    n_jump_valid: int
    n_longest_span: int
    n_removed_start: int
    n_removed_end: int
    n_final: int
    source_span_start: int
    source_span_stop: int


@dataclass(frozen=True, slots=True)
class SelectionPlan:
    groups: Windows = field(default_factory=lambda: tuple(GROUPS))
    shifts: tuple[Decimal, ...] = field(default_factory=lambda: tuple(SHIFT_A))
    exclusions: Windows = field(default_factory=lambda: tuple(EXCLUDE_RANGES))
    plausible_low_hz: float = 3e7
    plausible_high_hz: float = 4e7
    jump_threshold_hz: float = JUMP_THRESHOLD


@dataclass(frozen=True, slots=True)
class SelectedSegment:
    group: int
    times: TimeArray
    beat: FloatArray
    m_dec: Decimal
    shift_a: Decimal
    raw_mean: float
    rem_start: int
    rem_end: int
    diagnostics: SelectionDiagnostics


DEFAULT_SELECTION_PLAN = SelectionPlan(
    groups=tuple(GROUPS),
    shifts=tuple(SHIFT_A),
    exclusions=tuple(EXCLUDE_RANGES),
)


def endpoint_screen_indices(x: FloatArray) -> EndpointScreen:
    if x.ndim != 1 or x.size == 0:
        raise ValueError("endpoint screening requires a non-empty 1-D array")
    threshold = 0.01 * float(np.ptp(x))
    if threshold == 0.0:
        return EndpointScreen(0, x.size, 0, 0)
    center = float(np.median(x))
    keep = np.abs(x - center) <= threshold
    valid = np.flatnonzero(keep)
    if valid.size == 0:
        raise ValueError("endpoint screening removed every sample")
    start = int(valid[0])
    stop = int(valid[-1]) + 1
    return EndpointScreen(start, stop, start, x.size - stop)


def select_segments(
    times: TimeArray,
    beat: FloatArray,
    plan: SelectionPlan = DEFAULT_SELECTION_PLAN,
) -> tuple[SelectedSegment, ...]:
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
    plausible_global = (clean > plan.plausible_low_hz) & (clean < plan.plausible_high_hz)
    if not plausible_global.any():
        raise AnalysisError("raw beat data contain no plausible unexcluded samples")
    m_dec = to_dec(float(np.nanmedian(clean[plausible_global])))

    segments: list[SelectedSegment] = []
    for k, (start, end) in enumerate(plan.groups):
        inside = (times >= np.datetime64(start)) & (times < np.datetime64(end))
        t_seg = times[inside]
        b_seg = beat[inside]
        ex_seg = excluded[inside]
        plausible = ((b_seg > plan.plausible_low_hz)
                     & (b_seg < plan.plausible_high_hz)
                     & ~ex_seg)
        if not plausible.any():
            raise AnalysisError(f"segment {k + 1}: missing or empty plausible raw data")
        median = float(np.median(b_seg[plausible]))
        valid = plausible & (np.abs(b_seg - median) < plan.jump_threshold_hz)
        span = longest_valid_span(valid)
        if span is None:
            raise AnalysisError(f"segment {k + 1}: no valid raw span")

        span_start, span_stop_inclusive = span
        source_times = t_seg[span_start:span_stop_inclusive + 1]
        source_beat = b_seg[span_start:span_stop_inclusive + 1]
        try:
            screen = endpoint_screen_indices(source_beat)
        except ValueError as error:
            raise AnalysisError(f"segment {k + 1}: empty after raw endpoint screen") from error
        retained_times = source_times[screen.start:screen.stop].copy()
        retained_beat = source_beat[screen.start:screen.stop].copy()
        if retained_beat.size == 0:
            raise AnalysisError(f"segment {k + 1}: empty after raw endpoint screen")

        retained_times.setflags(write=False)
        retained_beat.setflags(write=False)
        diagnostics = SelectionDiagnostics(
            n_window=int(b_seg.size),
            n_excluded=int(np.count_nonzero(ex_seg)),
            n_plausible=int(np.count_nonzero(plausible)),
            n_jump_valid=int(np.count_nonzero(valid)),
            n_longest_span=int(source_beat.size),
            n_removed_start=screen.removed_start,
            n_removed_end=screen.removed_end,
            n_final=int(retained_beat.size),
            source_span_start=span_start,
            source_span_stop=span_stop_inclusive + 1,
        )
        segments.append(
            SelectedSegment(
                group=k + 1,
                times=retained_times,
                beat=retained_beat,
                m_dec=m_dec,
                shift_a=plan.shifts[k],
                raw_mean=float(retained_beat.mean()),
                rem_start=screen.removed_start,
                rem_end=screen.removed_end,
                diagnostics=diagnostics,
            )
        )
    return tuple(segments)
