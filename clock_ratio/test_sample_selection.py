from __future__ import annotations

from decimal import Decimal

import numpy as np
import pytest

from clock import shared as s
from clock.sample_selection import (
    DEFAULT_SELECTION_PLAN,
    EndpointScreen,
    SelectionDiagnostics,
    SelectionPlan,
    endpoint_screen_indices,
    select_segments,
)


def selection_fixture() -> tuple[np.ndarray, np.ndarray, SelectionPlan]:
    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = 33_000_000.0 + np.array([2.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0, 2.0])
    plan = SelectionPlan(
        groups=((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),),
        shifts=(s.SHIFT_A[0],),
        exclusions=(),
    )
    return times, beat, plan


def test_default_selection_plan_uses_shared_shift_a() -> None:
    assert DEFAULT_SELECTION_PLAN.shifts == tuple(s.SHIFT_A)


def test_endpoint_screen_indices_trim_times_and_values_identically() -> None:
    beat = np.array([101.0, 100.0, 100.0, 100.0, 101.0])
    times = np.datetime64("2026-01-01T00:00:00") + np.arange(5).astype("timedelta64[s]")

    screen = endpoint_screen_indices(beat)

    assert screen == EndpointScreen(start=1, stop=4, removed_start=1, removed_end=1)
    assert np.array_equal(times[screen.start:screen.stop], times[1:4])
    assert np.array_equal(beat[screen.start:screen.stop], beat[1:4])


def test_endpoint_screen_indices_preserves_input_array() -> None:
    beat = np.array([101.0, 100.0, 100.0, 100.0, 101.0])
    original = beat.copy()

    screen = endpoint_screen_indices(beat)

    assert screen.start == 1
    np.testing.assert_array_equal(beat, original)


@pytest.mark.parametrize("shape", [(0,), (1, 0)])
def test_endpoint_screen_indices_rejects_empty_or_non_1d_input(shape: tuple[int, ...]) -> None:
    beat = np.empty(shape, dtype=np.float64)

    with pytest.raises(ValueError, match="non-empty 1-D"):
        endpoint_screen_indices(beat)


def test_endpoint_screen_indices_keeps_flat_array() -> None:
    beat = np.full(4, 33_000_000.0)

    assert endpoint_screen_indices(beat) == EndpointScreen(0, 4, 0, 0)


def test_select_segments_records_diagnostics_and_trims_in_sync() -> None:
    times, beat, plan = selection_fixture()

    segment, = select_segments(times, beat, plan)

    np.testing.assert_array_equal(segment.times, times[1:-1])
    np.testing.assert_array_equal(segment.beat, beat[1:-1])
    assert segment.raw_mean == pytest.approx(float(beat[1:-1].mean()))
    assert segment.m_dec == Decimal("33000000.0")
    assert segment.diagnostics == SelectionDiagnostics(
        n_window=9,
        n_excluded=0,
        n_plausible=9,
        n_jump_valid=9,
        n_longest_span=9,
        n_removed_start=1,
        n_removed_end=1,
        n_final=7,
        source_span_start=0,
        source_span_stop=9,
    )
    assert segment.times.flags.writeable is False
    assert segment.beat.flags.writeable is False


def test_select_segments_treats_exclusions_as_inclusive_and_group_end_as_exclusive() -> None:
    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = np.full(9, 33_000_000.0)
    beat[0], beat[8] = np.nan, 9e10
    plan = SelectionPlan(
        groups=((str(times[0]), str(times[8])),),
        shifts=(s.SHIFT_A[0],),
        exclusions=((str(times[0]), str(times[1])),),
    )

    segment, = select_segments(times, beat, plan)

    np.testing.assert_array_equal(segment.times, times[2:8])
    np.testing.assert_array_equal(segment.beat, beat[2:8])
    assert segment.diagnostics.n_window == 8
    assert segment.diagnostics.n_excluded == 2
    assert segment.diagnostics.n_final == 6


def test_select_segments_keeps_longest_index_span_even_with_time_gap() -> None:
    times, beat, plan = selection_fixture()
    times[5:] += np.timedelta64(20, "s")
    plan = SelectionPlan(groups=((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),),
                         shifts=plan.shifts,
                         exclusions=plan.exclusions)

    segment, = select_segments(times, beat, plan)

    np.testing.assert_array_equal(segment.times, times[1:-1])
    np.testing.assert_array_equal(segment.beat, beat[1:-1])
    assert segment.diagnostics.source_span_start == 0
    assert segment.diagnostics.source_span_stop == 9
