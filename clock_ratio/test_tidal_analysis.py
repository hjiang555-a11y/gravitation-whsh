"""Scientific regression contracts; no legacy generators are executed."""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, localcontext

import numpy as np
import pytest
from numpy.typing import NDArray

from clock import shared as s
from clock_ratio.compute_ratio import full_ratio
from clock_ratio.tidal_analysis import (
    SCENARIOS, Scenario, SelectionPlan, TideGrid, analyze_segment, select_segments,
)


def selection_fixture() -> tuple[NDArray[np.datetime64], NDArray[np.float64], SelectionPlan]:
    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = 33_000_000. + np.array([2., 0., -1., 0., 1., 0., -1., 0., 2.])
    plan = SelectionPlan(((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),),
                         (s.SHIFT_A[0],), ())
    return times, beat, plan


def test_selection_when_raw_endpoints_are_trimmed() -> None:
    # Given raw endpoints that fail the legacy 1% peak-to-peak screen.
    times, beat, plan = selection_fixture()
    # When selecting before applying a large tide correction.
    segment, = select_segments(times, beat, plan)
    result = analyze_segment(segment, np.arange(7.) * 100., SCENARIOS[1])
    # Then actual retained bounds match data, and correction cannot re-screen.
    assert (segment.rem_start, segment.rem_end) == (1, 1)
    np.testing.assert_array_equal(segment.times, times[1:-1])
    np.testing.assert_array_equal(segment.beat, beat[1:-1])
    assert len(result.fluctuations) == 7
    assert segment.times.flags.writeable is False
    assert segment.beat.flags.writeable is False


def test_raw_when_baseline_uses_legacy_float_mean_and_decimal_inversion() -> None:
    # Given a selected segment whose raw mean carries binary float rounding.
    segment, = select_segments(*selection_fixture())
    expected = full_ratio(s.to_dec(float(segment.beat.mean())) - segment.m_dec,
                          segment.shift_a, segment.m_dec)
    # When A=0 is evaluated under an unrelated caller precision.
    with localcontext() as context:
        context.prec = 28
        raw = analyze_segment(segment, np.full(len(segment.beat), 1e-9), SCENARIOS[0])
    # Then the exact old Decimal80 ratio is preserved, not a float ratio.
    assert raw.ratio == expected
    assert raw.delta_r == Decimal(0)
    assert raw.mean_dm_corrected == s.to_dec(float(segment.beat.mean())) - segment.m_dec


def test_correction_when_negative_response_removes_modeled_tide() -> None:
    # Given b=carrier+A*h+noise, with exactly representable synthetic h.
    segment, = select_segments(*selection_fixture())
    h = -(segment.beat - 33_000_000.) + 0.25
    # When the fixed negative coefficient is removed without demeaning h.
    result = analyze_segment(segment, h, SCENARIOS[1])
    # Then all residual noise vanishes but the nonzero mean correction remains.
    assert result.beat_std_hz == 0.0
    assert result.fractional_std == 0.0
    expected_dm = s.to_dec(segment.raw_mean) - segment.m_dec + s.to_dec(float(h.mean()))
    assert result.mean_dm_corrected == expected_dm
    assert result.ratio == full_ratio(expected_dm, segment.shift_a, segment.m_dec)
    assert result.ratio != result.raw_ratio


def test_empirical_when_small_mean_correction_scales_by_point54() -> None:
    # Given a correction far below the float ULP of the 33 MHz carrier.
    segment, = select_segments(*selection_fixture())
    h = np.full(len(segment.beat), 1e-9)
    # When evaluating both prespecified, exact Decimal coefficients.
    theory = analyze_segment(segment, h, SCENARIOS[1])
    empirical = analyze_segment(segment, h, SCENARIOS[2])
    # Then mean correction scales exactly, and ratio correction to first order.
    assert empirical.mean_dm_corrected - empirical.mean_dm_raw == Decimal("0.54") * (theory.mean_dm_corrected - theory.mean_dm_raw)
    assert float(empirical.delta_r / theory.delta_r) == pytest.approx(0.54, rel=1e-15)
    assert theory.delta_r != 0
    assert float(theory.ratio) == float(theory.raw_ratio)
    assert (str(SCENARIOS[1].coefficient), str(SCENARIOS[2].coefficient)) == ("-1", "-0.54")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_fluctuations_when_compared_with_full_decimal_identity(scenario: Scenario) -> None:
    # Given tiny fractional variations relative to the SAME raw segment R0.
    segment, = select_segments(*selection_fixture())
    h = np.linspace(-0.002, 0.003, len(segment.beat))
    residual = (segment.beat - segment.raw_mean) - float(scenario.coefficient) * h
    raw_dm = s.to_dec(segment.raw_mean) - segment.m_dec
    r0 = full_ratio(raw_dm, segment.shift_a, segment.m_dec)
    expected = np.array([float(full_ratio(raw_dm + s.to_dec(float(e)), segment.shift_a,
                                         segment.m_dec) / r0 - 1) for e in residual])
    # When the cancellation-free expression evaluates the nonlinear inversion.
    result = analyze_segment(segment, h, scenario)
    # Then it agrees with full Decimal, not rounded COEF or beat/F1550.
    np.testing.assert_allclose(result.fluctuations, expected, rtol=3e-15, atol=1e-32)
    assert result.fractional_std == pytest.approx(float(expected.std(ddof=1)), rel=3e-15)


def test_selection_when_exclusions_and_window_bounds_are_inclusive() -> None:
    # Given an excluded first/second point and an end-exclusive group boundary.
    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = np.full(9, 33_000_000.)
    beat[0], beat[8] = np.nan, 9e10
    plan = SelectionPlan(((str(times[0]), str(times[8])),), (s.SHIFT_A[0],),
                         ((str(times[0]), str(times[1])),))
    # When applying exactly the raw legacy membership rules.
    segment, = select_segments(times, beat, plan)
    # Then invalid/excluded values do not contaminate the median or samples.
    assert segment.m_dec == Decimal("33000000.0")
    np.testing.assert_array_equal(segment.times, times[2:8])


def test_selection_when_valid_rows_have_time_gaps() -> None:
    # Given a gap in timestamps, but no invalid beat rows.
    times, beat, plan = selection_fixture()
    times[5:] += np.timedelta64(20, "s")
    plan = replace(plan, groups=((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),))
    # When selecting the longest valid INDEX span, not the longest time run.
    segment, = select_segments(times, beat, plan)
    # Then ratio membership retains samples on both sides of the gap.
    assert len(segment.beat) == 7
    np.testing.assert_array_equal(segment.times, times[1:-1])


@pytest.mark.parametrize("beat", [[], [1.0] * 9, [33_000_000., 33_000_002.]])
def test_selection_when_segment_is_missing_or_empty(beat: list[float]) -> None:
    # Given absent, nonplausible, or entirely endpoint-screened raw input.
    times, _, plan = selection_fixture()
    # When selecting, then explicitly reject rather than silently omit a group.
    with pytest.raises(ValueError, match="raw|segment"):
        select_segments(times[:len(beat)], np.array(beat), plan)


def test_selection_when_later_required_group_has_no_data() -> None:
    # Given a valid group followed by a completely missing required group.
    times, beat, plan = selection_fixture()
    plan = replace(plan, groups=plan.groups + (("2026-01-02", "2026-01-03"),),
                   shifts=plan.shifts * 2)
    # When selecting all configured groups, then name the missing segment.
    with pytest.raises(ValueError, match="segment 2"):
        select_segments(times, beat, plan)


def test_tide_when_beijing_time_is_converted_to_utc_and_interpolated() -> None:
    # Given a UTC 30-second ramp with a known exact linear interpolation.
    grid = TideGrid(np.array(["2026-01-01T00:00:00", "2026-01-01T00:00:30"], dtype="datetime64[s]"),
                    np.array([0., 30.]))
    beijing = np.array(["2026-01-01T08:00:00", "2026-01-01T08:00:15", "2026-01-01T08:00:30"], dtype="datetime64[s]")
    # When supplying actual Beijing sample times.
    h = grid.beat_at(beijing)
    # Then subtract 8 hours and normalize using F1550/c^2.
    np.testing.assert_allclose(h, np.array([0., 15., 30.]) * s.F_1550 / s.C**2, rtol=1e-15)


@pytest.mark.parametrize("seconds,values", [([0, 0], [1., 2.]), ([30, 0], [1., 2.]),
                                           ([0, 30], [1., float("nan")]),
                                           ([0, 30], [1., float("inf")]),
                                           ([0, 31], [1., 2.]), ([], []), ([0], [1.])])
def test_tide_when_grid_is_invalid(seconds: list[int], values: list[float]) -> None:
    # Given an invalid, ambiguous or non-finite tide source.
    times = np.datetime64("2026-01-01") + np.array(seconds, dtype=np.int64).astype("timedelta64[s]")
    # When parsing at the boundary, then explicitly reject the source.
    with pytest.raises(ValueError, match="tide"):
        TideGrid(times, np.array(values))


@pytest.mark.parametrize("offset", [-1, 15, 59, 61])
def test_tide_when_query_is_outside_bounds_or_across_missing_point(offset: int) -> None:
    # Given a tide grid with a missing 30-second node.
    grid = TideGrid(np.array(["2026-01-01T00:00:00", "2026-01-01T00:01:00"], dtype="datetime64[s]"), np.array([0., 60.]))
    query = np.array([np.datetime64("2026-01-01T08:00:00") + np.timedelta64(offset, "s")])
    # When querying outside coverage or inside the missing interval, then fail.
    with pytest.raises(ValueError, match="tide"):
        grid.beat_at(query)


def test_tide_when_nat_timestamp_is_supplied() -> None:
    # Given a non-finite tide timestamp.
    times = np.array(["2026-01-01", "NaT"], dtype="datetime64[s]")
    # When parsing, then reject rather than convert NaT to a finite integer.
    with pytest.raises(ValueError, match="tide"):
        TideGrid(times, np.array([0., 1.]))
