from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import stats

from clock.sample_selection import FloatArray
from clock_ratio.tidal_stability import continuous_runs


WindowScheme = Literal["historical-triangular", "numpy-bartlett"]


@dataclass(frozen=True, slots=True)
class AmplitudeFit:
    amplitude: float
    uncertainty: float
    pearson_r: float
    pearson_p: float
    n_point_estimate: int
    n_inference: int


def triangular_weights(width: int, *, scheme: WindowScheme) -> FloatArray:
    if width < 2:
        raise ValueError("triangular window width must be at least 2")
    if scheme == "historical-triangular":
        k = np.arange(width, dtype=float)
        return 1.0 - np.abs(2 * k - (width - 1)) / (width + 1)
    if scheme == "numpy-bartlett":
        return np.bartlett(width)
    raise ValueError(f"unknown triangular window scheme: {scheme}")


def triangular_average(
    x: FloatArray,
    *,
    width: int,
    stride: int,
    scheme: WindowScheme = "historical-triangular",
) -> FloatArray:
    if x.ndim != 1 or width < 2 or stride < 1 or x.size < width:
        raise ValueError("invalid triangular window request")
    if not np.isfinite(x).all():
        raise ValueError("triangular averaging requires finite samples")

    weights = triangular_weights(width, scheme=scheme)
    starts = range(0, x.size - width + 1, stride)
    if scheme == "historical-triangular":
        # Historical order: normalize first, then np.dot with the normalized
        # weights as the FIRST operand (bit-for-bit 44abd1a compatibility).
        normalized = weights / weights.sum()
        return np.array([float(np.dot(normalized, x[s:s + width])) for s in starts])
    denominator = float(weights.sum())
    return np.array([np.dot(x[s:s + width], weights) / denominator for s in starts], dtype=float)


def fit_demeaned_amplitude(
    beat: FloatArray,
    tide: FloatArray,
    inference_beat: FloatArray,
    inference_tide: FloatArray,
) -> AmplitudeFit:
    if (beat.ndim != 1 or tide.ndim != 1 or inference_beat.ndim != 1 or inference_tide.ndim != 1
            or beat.size != tide.size or inference_beat.size != inference_tide.size):
        raise ValueError("fit inputs must be aligned 1-D arrays")
    if (not np.isfinite(beat).all() or not np.isfinite(tide).all()
            or not np.isfinite(inference_beat).all() or not np.isfinite(inference_tide).all()):
        raise ValueError("fit inputs must be finite")

    b = beat - beat.mean()
    t = tide - tide.mean()
    tt = float(np.dot(t, t))
    if tt == 0.0:
        raise ValueError("point-estimate tide windows must vary")
    amplitude = float(np.dot(t, b) / tt)

    bi = inference_beat - inference_beat.mean()
    ti = inference_tide - inference_tide.mean()
    titi = float(np.dot(ti, ti))
    if len(bi) < 3 or titi == 0.0:
        raise ValueError("at least three non-overlapping, nonconstant windows are required for inference")

    inference_amplitude = float(np.dot(ti, bi) / titi)
    resid = bi - inference_amplitude * ti
    dof = len(bi) - 2
    sigma2 = float(np.dot(resid, resid) / dof)
    uncertainty = float(np.sqrt(sigma2 / titi))
    pearson_r = float(np.corrcoef(inference_beat, inference_tide)[0, 1])
    pearson_p = float(stats.pearsonr(inference_beat, inference_tide).pvalue)
    return AmplitudeFit(
        amplitude=amplitude,
        uncertainty=uncertainty,
        pearson_r=pearson_r,
        pearson_p=pearson_p,
        n_point_estimate=len(beat),
        n_inference=len(inference_beat),
    )


@dataclass(frozen=True, slots=True)
class CovarianceAwareFit:
    amplitude: float
    standard_error: float
    ci_low: float
    ci_high: float
    method: Literal["gls", "block-bootstrap"]
    n_windows: int
    effective_n: float


def ar1_precision_matrix(n: int, rho: float) -> FloatArray:
    """Stationary AR(1) precision matrix (tridiagonal, endpoint diagonals 1)."""
    if n < 1:
        raise ValueError("precision matrix needs at least one sample")
    if not -1.0 < rho < 1.0:
        raise ValueError("AR(1) coefficient must lie in (-1, 1)")
    diag = np.full(n, 1.0 + rho * rho)
    diag[0] = 1.0
    diag[-1] = 1.0
    matrix = np.diag(diag)
    if n > 1:
        off = np.full(n - 1, -rho)
        matrix += np.diag(off, 1) + np.diag(off, -1)
    return matrix


def _ar1_quadratic_form(u: FloatArray, v: FloatArray, rho: float) -> float:
    n = u.shape[0]
    diag = np.full(n, 1.0 + rho * rho)
    diag[0] = 1.0
    diag[-1] = 1.0
    value = float(np.sum(diag * u * v))
    if n > 1:
        value -= rho * (float(np.sum(u[:-1] * v[1:])) + float(np.sum(u[1:] * v[:-1])))
    return value


def _segmented_arrays(times, beat, tide):
    if (times.ndim != 1 or beat.ndim != 1 or tide.ndim != 1
            or times.shape != beat.shape or times.shape != tide.shape):
        raise ValueError("covariance-aware inference needs aligned 1-D series")
    if not (np.isfinite(beat).all() and np.isfinite(tide).all()):
        raise ValueError("covariance-aware inference needs finite samples")
    runs = continuous_runs(times)
    if not runs:
        raise ValueError("covariance-aware inference needs at least one continuous run")
    data = []
    for start, stop in runs:
        b = beat[start:stop] - float(beat[start:stop].mean())
        t = tide[start:stop] - float(tide[start:stop].mean())
        if float(np.dot(t, t)) == 0.0:
            raise ValueError("tidal template must vary inside every continuous run")
        data.append((t, b))
    return data


def _pooled_ar1_rho(data) -> float:
    num = den = 0.0
    for t, b in data:
        slope = float(np.dot(t, b) / np.dot(t, t))
        resid = b - slope * t
        num += float(np.dot(resid[:-1], resid[1:]))
        den += float(np.dot(resid, resid))
    if den == 0.0:
        return 0.0
    return float(np.clip(num / den, -0.95, 0.95))


def fit_gls_amplitude(times, beat, tide, *, block_size: int = 1200) -> CovarianceAwareFit:
    if block_size < 1:
        raise ValueError("block_size must be a positive number of samples")
    data = _segmented_arrays(times, beat, tide)
    rho = _pooled_ar1_rho(data)
    m = v = w = 0.0
    total = 0
    n_windows = 0
    effective = 0.0
    for t, b in data:
        m += _ar1_quadratic_form(t, t, rho)
        v += _ar1_quadratic_form(t, b, rho)
        w += _ar1_quadratic_form(b, b, rho)
        n = t.shape[0]
        total += n
        n_windows += n // block_size
        effective += n * (1.0 - rho) / (1.0 + rho)
    amplitude = v / m
    dof = max(total - len(data) - 1, 1)
    sigma2 = max(w - v * v / m, 0.0) / dof
    standard_error = float(np.sqrt(sigma2 / m))
    quantile = float(stats.t.ppf(0.975, max(effective - 2.0, 1.0)))
    return CovarianceAwareFit(
        amplitude=amplitude, standard_error=standard_error,
        ci_low=amplitude - quantile * standard_error,
        ci_high=amplitude + quantile * standard_error,
        method="gls", n_windows=n_windows, effective_n=effective,
    )


def block_bootstrap_amplitude(
    times, beat, tide, *, block_size: int = 1200, n_resamples: int = 500, seed: int,
) -> CovarianceAwareFit:
    if block_size < 1 or n_resamples < 1:
        raise ValueError("block_size and n_resamples must be positive")
    data = _segmented_arrays(times, beat, tide)
    num = den = 0.0
    for t, b in data:
        num += float(np.dot(t, b))
        den += float(np.dot(t, t))
    amplitude = num / den
    residuals = [(t, b - amplitude * t) for t, b in data]
    rng = np.random.default_rng(seed)
    estimates = np.empty(n_resamples)
    for k in range(n_resamples):
        num = den = 0.0
        for t, r in residuals:
            n = t.shape[0]
            length = min(block_size, n)
            nblocks = (n + length - 1) // length
            starts = rng.integers(0, n - length + 1, nblocks)
            index = (starts[:, None] + np.arange(length)[None, :]).ravel()[:n]
            rs = r[index]
            bs = amplitude * t + rs
            num += float(np.dot(t, bs))
            den += float(np.dot(t, t))
        estimates[k] = num / den
    low, high = np.percentile(estimates, [2.5, 97.5])
    standard_error = float(np.std(estimates, ddof=1)) if n_resamples > 1 else 0.0
    rho = _pooled_ar1_rho(data)
    n_windows = sum(t.shape[0] // block_size for t, _ in data)
    effective = sum(t.shape[0] * (1.0 - rho) / (1.0 + rho) for t, _ in data)
    return CovarianceAwareFit(
        amplitude=amplitude, standard_error=standard_error,
        ci_low=float(low), ci_high=float(high),
        method="block-bootstrap", n_windows=n_windows, effective_n=effective,
    )
