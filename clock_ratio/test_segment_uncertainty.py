"""Contracts for gap-safe segment statistical uncertainty (true overlapping ADEV).

The estimator must split runs at every gap and duplicate timestamp, fit only
inside the prespecified tau window, and never fall back to the longest
available tau when the fit is underdetermined.  The combination wiring is
exercised on synthetic segments only; no real clock data is read.
"""
from __future__ import annotations

from decimal import Decimal

import numpy as np
import pytest

from clock.sample_selection import AnalysisError, SelectedSegment, SelectionDiagnostics
from clock.shared import F_1550
from clock_ratio.segment_uncertainty import StabilityFitConfig, estimate_segment_uncertainty
from clock_ratio.statistical_methods import analyze_raw_statistics
from clock_ratio.statistical_models import SegmentEstimate, combine_estimates

# White-frequency-noise Allan slope is -1/2; the ruling fixes this acceptance band.
WHITE_BAND = (-0.65, -0.35)

# Fixed seeds whose 4096-sample white-noise fits land inside WHITE_BAND.
ESTABLISHED_WHITE_SEEDS = {1: 901, 2: 902, 3: 904}


def seconds(count: int) -> np.ndarray:
    return np.datetime64("2026-01-01T00:00:00") + np.arange(count).astype("timedelta64[s]")


def test_estimator_never_crosses_gap_or_duplicate():
    times = np.array([
        "2026-01-01T00:00:00", "2026-01-01T00:00:01",
        "2026-01-01T00:00:01", "2026-01-01T00:00:05",
        "2026-01-01T00:00:06",
    ], dtype="datetime64[s]")
    y = np.array([0.0, 1.0, 2.0, 3.0, 4.0]) * 1e-18
    result = estimate_segment_uncertainty(times, y, StabilityFitConfig(fit_min_s=1))
    assert result.n_valid == 5
    assert result.n_runs == 3


def test_white_frequency_noise_when_series_is_long() -> None:
    # Given a long i.i.d. white-frequency-noise series (fixed seed).
    rng = np.random.default_rng(20261006)
    y = rng.normal(0.0, 1e-15, 100_000)

    # When the gap-safe estimator fits the log-log stability curve.
    result = estimate_segment_uncertainty(seconds(len(y)), y, StabilityFitConfig())

    # Then the fitted slope lands in the white-noise band and the extrapolation
    # is established and finite.
    assert result.fit_slope is not None
    assert WHITE_BAND[0] <= result.fit_slope <= WHITE_BAND[1]
    assert result.fit_intercept is not None
    assert result.u_fractional is not None
    assert result.u_fractional > 0.0
    assert result.status == "established"
    assert len(result.taus_s) == len(result.sigma_y)


def test_short_series_when_fewer_than_three_fit_points() -> None:
    # Given data whose longest run leaves fewer than three taus in the window.
    rng = np.random.default_rng(20261009)
    y = rng.normal(0.0, 1e-15, 600)

    # When the estimator runs with the default 128 s fit minimum.
    result = estimate_segment_uncertainty(seconds(len(y)), y, StabilityFitConfig())

    # Then it refuses to extrapolate: no longest-tau fallback, no fit, no u.
    assert result.taus_s  # taus were evaluated ...
    assert result.u_fractional is None
    assert result.fit_slope is None
    assert result.fit_intercept is None
    assert result.status == "supported-with-limitations"


def flicker_series(count: int, seed: int) -> np.ndarray:
    """1/f noise from a white series scaled by 1/sqrt(f) in the Fourier domain."""
    white = np.random.default_rng(seed).normal(0.0, 1e-15, count)
    frequencies = np.fft.rfftfreq(count, d=1.0)
    scaling = np.zeros_like(frequencies)
    scaling[1:] = 1.0 / np.sqrt(frequencies[1:])
    return np.fft.irfft(np.fft.rfft(white) * scaling, count)


@pytest.mark.parametrize("series", ["random_walk", "flicker"])
def test_colored_noise_when_slope_leaves_white_band(series: str) -> None:
    # Given coloured data far from white frequency noise.
    if series == "random_walk":
        y = np.cumsum(np.random.default_rng(20261007).normal(0.0, 1e-15, 100_000))
    else:
        y = flicker_series(100_000, 20261008)

    # When the estimator fits the stability curve.
    result = estimate_segment_uncertainty(seconds(len(y)), y, StabilityFitConfig())

    # Then the model is flagged: computed but outside the white-noise band.
    assert result.fit_slope is not None
    assert not (WHITE_BAND[0] <= result.fit_slope <= WHITE_BAND[1])
    assert result.u_fractional is not None
    assert result.status == "supported-with-limitations"


def synthetic_segment(group: int, count: int, seed: int) -> SelectedSegment:
    rng = np.random.default_rng(seed)
    times = seconds(count)
    # 33 MHz carrier +/- ~0.2 Hz, i.e. fractional frequency ~1e-15.
    beat = 33_000_000.0 + rng.normal(0.0, 0.2, count)
    diagnostics = SelectionDiagnostics(
        n_window=count, n_excluded=0, n_plausible=count, n_jump_valid=count,
        n_longest_span=count, n_removed_start=0, n_removed_end=0, n_final=count,
        source_span_start=0, source_span_stop=count,
    )
    return SelectedSegment(
        group=group, times=times, beat=beat, m_dec=Decimal("33623140.92"),
        shift_a=Decimal(0), raw_mean=float(beat.mean()), rem_start=0, rem_end=0,
        diagnostics=diagnostics,
    )


def test_analyze_raw_statistics_when_segments_are_white_noise() -> None:
    # Given three synthetic white-noise segments and their clock ratios.
    config = StabilityFitConfig()
    segments = tuple(
        synthetic_segment(group, 4096, seed=ESTABLISHED_WHITE_SEEDS[group]) for group in (1, 2, 3))
    ratios = {
        1: Decimal("1.2075070393433377200"),
        2: Decimal("1.2075070393433377210"),
        3: Decimal("1.2075070393433377195"),
    }

    # When the pure analysis builds y_i / u_i and combines.
    results, combined = analyze_raw_statistics(segments, ratios, config)

    # Then the estimator stays group-agnostic (the analysis layer attaches the
    # group) and demeaning/normalization matches a manual estimator call.
    assert [result.group for result in results] == [1, 2, 3]
    for segment, result in zip(segments, results, strict=True):
        assert result.status == "established"
        assert result.u_fractional is not None
        fractional = (segment.beat - segment.beat.mean()) / F_1550
        manual = estimate_segment_uncertainty(segment.times, fractional, config)
        assert manual.group is None
        assert result.u_fractional == manual.u_fractional

    # And the units follow the documented convention: y_i = R_g/R_1 - 1
    # (fractional), u_i = u_frac * R_g (absolute ratio), reference R_1.
    expected_estimates = [
        SegmentEstimate(
            group=segment.group,
            ratio=ratios[segment.group],
            deviation=float(ratios[segment.group] / ratios[1] - Decimal(1)),
            u_absolute=float(Decimal(repr(result.u_fractional)) * ratios[segment.group]),
        )
        for segment, result in zip(segments, results, strict=True)
    ]
    expected = combine_estimates(expected_estimates, ratios[1])
    assert combined.reference_ratio == ratios[1]
    assert combined.y_wls == pytest.approx(expected.y_wls, rel=1e-12)
    assert combined.u_wls == pytest.approx(expected.u_wls, rel=1e-12)
    assert combined.chi2 == pytest.approx(expected.chi2, rel=1e-12)
    assert combined.xi_mp == pytest.approx(expected.xi_mp, rel=1e-12)
    assert combined.mu_bayes == pytest.approx(expected.mu_bayes, rel=1e-12)


def test_analyze_raw_statistics_when_a_segment_uncertainty_is_undefined() -> None:
    # Given one well-fitted segment and one too short to fit.
    config = StabilityFitConfig()
    good = synthetic_segment(1, 4096, seed=901)
    short = synthetic_segment(2, 300, seed=902)
    ratios = {1: Decimal("1.20750703934333772"), 2: Decimal("1.20750703934333771")}

    # When the pure analysis runs.
    # Then it fails fast instead of silently dropping the segment.
    with pytest.raises(AnalysisError, match="segment 2"):
        analyze_raw_statistics((good, short), ratios, config)
