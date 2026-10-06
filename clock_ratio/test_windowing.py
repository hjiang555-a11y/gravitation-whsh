from __future__ import annotations

import numpy as np
import pytest

from clock_ratio.windowing import fit_demeaned_amplitude, triangular_average


def test_triangular_average_constant_signal_is_unchanged() -> None:
    x = np.full(3600, 7.5)
    got = triangular_average(x, width=1200, stride=600)
    assert np.allclose(got, 7.5, rtol=0, atol=1e-14)


def test_triangular_average_matches_explicit_dot_product() -> None:
    x = np.arange(2400, dtype=float)
    w = np.bartlett(1200)
    expected = np.array([np.dot(x[i:i + 1200], w) / w.sum() for i in (0, 600, 1200)])
    got = triangular_average(x, width=1200, stride=600)
    assert np.allclose(got, expected)


def test_fit_recovers_known_negative_response() -> None:
    tide = np.sin(np.linspace(0, 20 * np.pi, 24_000))
    beat = -0.6 * tide
    overlap_b = triangular_average(beat, width=1200, stride=600)
    overlap_t = triangular_average(tide, width=1200, stride=600)
    independent_b = triangular_average(beat, width=1200, stride=1200)
    independent_t = triangular_average(tide, width=1200, stride=1200)

    fit = fit_demeaned_amplitude(overlap_b, overlap_t, independent_b, independent_t)

    assert fit.amplitude == pytest.approx(-0.6, abs=1e-12)
    assert fit.n_point_estimate > fit.n_inference
