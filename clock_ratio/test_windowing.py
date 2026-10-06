from __future__ import annotations

import numpy as np
import pytest

from clock.segment_analysis.batch_analysis import triangular_window
from clock_ratio.windowing import fit_demeaned_amplitude, triangular_average


SCHEMES = ("historical-triangular", "numpy-bartlett")


def test_triangular_average_constant_signal_is_unchanged() -> None:
    x = np.full(3600, 7.5)
    got = triangular_average(x, width=1200, stride=600, scheme="historical-triangular")
    assert np.allclose(got, 7.5, rtol=0, atol=1e-14)


def test_triangular_average_historical_matches_explicit_dot_product_with_nonzero_endpoint() -> None:
    x = np.array([1.0, 0.0, 0.0, 0.0])
    k = np.arange(4, dtype=float)
    w = 1.0 - np.abs(2 * k - 3.0) / 5.0
    expected = np.array([np.dot(x[:4], w) / w.sum()])
    got = triangular_average(x, width=4, stride=4, scheme="historical-triangular")
    assert np.allclose(got, expected, rtol=0, atol=1e-14)
    assert got[0] > 0.0


def test_triangular_average_numpy_bartlett_matches_explicit_dot_product() -> None:
    x = np.arange(2400, dtype=float)
    w = np.bartlett(1200)
    expected = np.array([np.dot(x[i:i + 1200], w) / w.sum() for i in (0, 600, 1200)])
    got = triangular_average(x, width=1200, stride=600, scheme="numpy-bartlett")
    assert np.allclose(got, expected)


def test_window_schemes_differ_on_endpoint_impulse() -> None:
    x = np.array([1.0, 0.0, 0.0, 0.0])
    historical = triangular_average(x, width=4, stride=4, scheme="historical-triangular")
    bartlett = triangular_average(x, width=4, stride=4, scheme="numpy-bartlett")
    assert historical[0] == pytest.approx(1.0 / 6.0, abs=1e-14)
    assert bartlett[0] == pytest.approx(0.0, abs=1e-14)
    assert historical[0] != pytest.approx(bartlett[0], abs=1e-14)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_fit_recovers_known_negative_response_for_each_scheme(scheme: str) -> None:
    tide = np.sin(np.linspace(0, 20 * np.pi, 24_000))
    beat = -0.6 * tide
    overlap_b = triangular_average(beat, width=1200, stride=600, scheme=scheme)
    overlap_t = triangular_average(tide, width=1200, stride=600, scheme=scheme)
    independent_b = triangular_average(beat, width=1200, stride=1200, scheme=scheme)
    independent_t = triangular_average(tide, width=1200, stride=1200, scheme=scheme)

    fit = fit_demeaned_amplitude(overlap_b, overlap_t, independent_b, independent_t)

    assert fit.amplitude == pytest.approx(-0.6, abs=1e-12)
    assert fit.n_point_estimate > fit.n_inference


def test_batch_triangular_window_preserves_head_historical_baseline() -> None:
    x = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    got = triangular_window(x, 4, 4)
    expected = np.array([1.0 / 6.0, 0.0])
    assert np.allclose(got, expected, rtol=0, atol=1e-14)
