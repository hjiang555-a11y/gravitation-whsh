from __future__ import annotations

import numpy as np
import pytest

from clock.segment_analysis.batch_analysis import triangular_window
from clock_ratio.windowing import fit_demeaned_amplitude, triangular_average


SCHEMES = ("historical-triangular", "numpy-bartlett")


def _historical_reference(x: np.ndarray, *, width: int, stride: int) -> np.ndarray:
    """Frozen pre-migration implementation (44abd1a:clock/segment_analysis/batch_analysis.py).

    Kept inline so the bit-exactness regression does not depend on the code under test.
    """
    k = np.arange(width)
    tri = 1.0 - np.abs(2 * k - (width - 1)) / (width + 1)
    tri = tri / tri.sum()
    if len(x) < width:
        return np.array([])
    n_out = (len(x) - width) // stride + 1
    out = np.empty(n_out)
    for i in range(n_out):
        start = i * stride
        out[i] = float(np.dot(tri, x[start : start + width]))
    return out


def test_triangular_average_constant_signal_is_unchanged() -> None:
    x = np.full(3600, 7.5)
    got = triangular_average(x, width=1200, stride=600, scheme="historical-triangular")
    assert np.allclose(got, 7.5, rtol=0, atol=1e-14)


def test_triangular_average_historical_matches_reference_bit_for_bit_with_nonzero_endpoint() -> None:
    x = np.array([1.0, 0.0, 0.0, 0.0])
    expected = _historical_reference(x, width=4, stride=4)
    got = triangular_average(x, width=4, stride=4, scheme="historical-triangular")
    assert np.array_equal(got, expected)
    assert got[0] > 0.0


@pytest.mark.parametrize("stride", [600, 1200])
def test_triangular_average_historical_matches_reference_bit_for_bit(stride: int) -> None:
    # Deterministic data on which the old normalize-then-dot order and the
    # dot-then-divide order differ below 1 ulp; np.array_equal must hold.
    x = np.linspace(-3.7, 12.1, 2400)
    expected = _historical_reference(x, width=1200, stride=stride)
    got = triangular_average(x, width=1200, stride=stride, scheme="historical-triangular")
    assert np.array_equal(got, expected)


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
    expected = _historical_reference(x, width=4, stride=4)
    assert np.array_equal(got, expected)
    assert got[0] == pytest.approx(1.0 / 6.0, abs=1e-14)
