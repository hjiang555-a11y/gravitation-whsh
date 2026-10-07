"""Covariance-aware tidal inference: unit and coverage tests (Task 12).

Synthetic AR(1) beat/tide series with known response ``A = -0.6`` exercise the
GLS and block-bootstrap estimators added to ``clock_ratio.windowing``.
"""

import numpy as np
import pytest
from scipy import stats
from scipy.signal import lfilter

from clock_ratio.windowing import (
    _ar1_quadratic_form,
    ar1_precision_matrix,
    block_bootstrap_amplitude,
    fit_gls_amplitude,
)


def synthetic_ar1_response(seed: int):
    """3 runs x 12000 s with 100-s gaps; AR(1) rho=0.5 sigma=0.02; sine tide; A=-0.6."""
    rng = np.random.default_rng(seed)
    beats, tides = [], []
    for _ in range(3):
        idx = np.arange(12000)
        tide = np.sin(2.0 * np.pi * idx / 2400.0)
        eta = rng.normal(0.0, 0.02, 12000)
        e = lfilter([1.0], [1.0, -0.5], eta)
        beats.append(-0.6 * tide + e)
        tides.append(tide)
    start = np.datetime64("2026-01-01T00:00:00")
    parts = [start + np.timedelta64(r * (12000 + 100), "s")
             + np.arange(12000).astype("timedelta64[s]") for r in range(3)]
    return np.concatenate(parts), np.concatenate(beats), np.concatenate(tides)


def naive_ols_ci(times, beat, tide):
    """Pooled per-run demeaned iid OLS with t CI (the naive comparator)."""
    from clock_ratio.tidal_stability import continuous_runs
    t_all, b_all = [], []
    for start, stop in continuous_runs(times):
        t = tide[start:stop] - tide[start:stop].mean()
        b = beat[start:stop] - beat[start:stop].mean()
        t_all.append(t)
        b_all.append(b)
    T = np.concatenate(t_all)
    B = np.concatenate(b_all)
    amplitude = float(np.dot(T, B) / np.dot(T, T))
    resid = B - amplitude * T
    n = len(B)
    se = float(np.sqrt(np.dot(resid, resid) / (n - 2) / np.dot(T, T)))
    quantile = float(stats.t.ppf(0.975, n - 2))
    return amplitude - quantile * se, amplitude + quantile * se


def test_gls_uses_nonoverlap_units_not_overlap_count():
    rng = np.random.default_rng(11)
    idx = np.arange(2400)
    times = np.datetime64("2026-01-01T00:00:00") + idx.astype("timedelta64[s]")
    tide = np.sin(2.0 * np.pi * idx / 2400.0)
    eta = rng.normal(0.0, 0.02, 2400)
    e = lfilter([1.0], [1.0, -0.5], eta)
    beat = -0.6 * tide + e

    overlap_points = (2400 - 1200) // 600 + 1
    assert overlap_points == 3

    fit = fit_gls_amplitude(times, beat, tide, block_size=1200)
    assert fit.method == "gls"
    assert fit.n_windows == 2
    assert fit.n_windows != overlap_points
    assert fit.ci_low < fit.amplitude < fit.ci_high


def test_ar1_precision_matrix_is_symmetric_positive_definite():
    for rho in (-0.9, 0.0, 0.9):
        for n in (1, 2, 5):
            matrix = ar1_precision_matrix(n, rho)
            assert matrix.shape == (n, n)
            assert np.array_equal(matrix, matrix.T)
            assert np.linalg.eigvalsh(matrix).min() > 0

    rng = np.random.default_rng(123)
    u = rng.normal(size=5)
    v = rng.normal(size=5)
    rho = 0.4
    matrix = ar1_precision_matrix(5, rho)
    assert np.isclose(float(u @ (matrix @ v)), _ar1_quadratic_form(u, v, rho), rtol=1e-12)


def test_block_bootstrap_is_deterministic_and_ordered():
    times, beat, tide = synthetic_ar1_response(seed=1000)
    first = block_bootstrap_amplitude(times, beat, tide, block_size=1200, n_resamples=50, seed=7)
    second = block_bootstrap_amplitude(times, beat, tide, block_size=1200, n_resamples=50, seed=7)
    assert first == second
    assert first.ci_low <= first.ci_high


def test_block_bootstrap_blocks_never_cross_runs():
    rng = np.random.default_rng(777)
    beats, tides = [], []
    for run in range(2):
        idx = np.arange(1200)
        tide = np.sin(2.0 * np.pi * idx / 2400.0 + 0.3 * run)
        eta = rng.normal(0.0, 0.01, 1200)
        e = lfilter([1.0], [1.0, -0.5], eta)
        beats.append(-0.6 * tide + e)
        tides.append(tide)
    start = np.datetime64("2026-01-01T00:00:00")
    parts = [start + np.timedelta64(run * (1200 + 60), "s")
             + np.arange(1200).astype("timedelta64[s]") for run in range(2)]
    times = np.concatenate(parts)
    beat = np.concatenate(beats)
    tide = np.concatenate(tides)

    fit = block_bootstrap_amplitude(times, beat, tide, block_size=1200, n_resamples=50, seed=3)
    assert fit.standard_error == 0.0
    assert fit.ci_low == fit.ci_high


def test_gls_and_bootstrap_reject_bad_inputs():
    times, beat, tide = synthetic_ar1_response(seed=5)

    empty_times = np.array([], dtype="datetime64[s]")
    empty = np.array([])
    with pytest.raises(ValueError):
        fit_gls_amplitude(empty_times, empty, empty)
    with pytest.raises(ValueError):
        block_bootstrap_amplitude(empty_times, empty, empty, block_size=1200, n_resamples=10, seed=0)

    bad_beat = beat.copy()
    bad_beat[0] = np.nan
    with pytest.raises(ValueError):
        fit_gls_amplitude(times, bad_beat, tide)
    with pytest.raises(ValueError):
        block_bootstrap_amplitude(times, bad_beat, tide, n_resamples=10, seed=0)

    with pytest.raises(ValueError):
        fit_gls_amplitude(times, beat, np.ones_like(tide))
    with pytest.raises(ValueError):
        block_bootstrap_amplitude(times, beat, np.ones_like(tide), n_resamples=10, seed=0)

    with pytest.raises(ValueError):
        fit_gls_amplitude(times, beat, tide, block_size=0)
    with pytest.raises(ValueError):
        block_bootstrap_amplitude(times, beat, tide, block_size=0, n_resamples=10, seed=0)
    with pytest.raises(ValueError):
        block_bootstrap_amplitude(times, beat, tide, block_size=1200, n_resamples=0, seed=0)


@pytest.mark.slow
def test_covariance_aware_coverage_for_ar1_noise():
    gls_covered = bootstrap_covered = naive_covered = 0
    for index in range(200):
        times, beat, tide = synthetic_ar1_response(seed=1000 + index)
        gls = fit_gls_amplitude(times, beat, tide, block_size=1200)
        bootstrap = block_bootstrap_amplitude(
            times, beat, tide, block_size=1200, n_resamples=500, seed=index)
        low, high = naive_ols_ci(times, beat, tide)
        gls_covered += gls.ci_low <= -0.6 <= gls.ci_high
        bootstrap_covered += bootstrap.ci_low <= -0.6 <= bootstrap.ci_high
        naive_covered += low <= -0.6 <= high
    assert 0.90 <= gls_covered / 200 <= 0.99
    assert gls_covered >= naive_covered
    assert bootstrap_covered >= naive_covered
