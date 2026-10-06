from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats

from clock.sample_selection import FloatArray


@dataclass(frozen=True, slots=True)
class AmplitudeFit:
    amplitude: float
    uncertainty: float
    pearson_r: float
    pearson_p: float
    n_point_estimate: int
    n_inference: int


def triangular_average(x: FloatArray, *, width: int, stride: int) -> FloatArray:
    if x.ndim != 1 or width < 2 or stride < 1 or x.size < width:
        raise ValueError("invalid triangular window request")
    if not np.isfinite(x).all():
        raise ValueError("triangular averaging requires finite samples")

    weights = np.bartlett(width)
    denominator = float(weights.sum())
    starts = range(0, x.size - width + 1, stride)
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
