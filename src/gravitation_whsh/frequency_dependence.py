"""IERS Conventions (2010) Step 2: frequency-dependent Love numbers.

The nominal degree-2 potential Love number k2 and displacement Love number h2
vary with tidal frequency: the diurnal band carries a resonance near the free
core nutation (FCN), and the zonal band is modified by mantle anelasticity.
This module computes the complex, frequency-dependent k2 and h2 following
IERS 2010 (Petit & Luzum, eds.), tables 6.4 (diurnal k2), 7.1 (diurnal h2),
6.5c / 7.3a (semidiurnal), and equations 6.12 / 7.4a (zonal anelasticity).

The frequency-dependent corrections are applied per constituent of the
dominant Cartwright-Tayler-Edden (1973) catalogue, synthesized from Doodson
arguments with a global scale fitted to the point-mass ephemeris potential.
"""

from __future__ import annotations

import numpy as np

SIDEREAL_RATIO = 1.002737909
SIDEREAL_DAY = 86400.0 / SIDEREAL_RATIO
ANELASTIC_ALPHA = 0.15
DEG_HR_TO_RAD_S = np.pi / (180.0 * 3600.0)

# Diurnal-band resonance frequencies (cycles per sidereal day) and Love-number
# resonance coefficients, IERS 2010 tables 6.4 (k2) and 7.1 (h2).
DIURNAL_SIGMA = np.array(
    [-0.0026010 - 0.0001361j, 1.0023181 + 0.000025j, 0.999026 + 0.000780j]
)
DIURNAL_K2 = np.array(
    [
        0.29954 - 0.1412e-2j,
        -0.77896e-3 - 0.3711e-4j,
        0.90963e-4 - 0.2963e-5j,
        -0.11416e-5 + 0.5325e-7j,
    ]
)
DIURNAL_H2 = np.array(
    [
        0.60671 - 0.2420e-2j,
        -0.15777e-2 - 0.7630e-4j,
        0.18053e-3 - 0.6292e-5j,
        -0.18616e-5 + 0.1379e-6j,
    ]
)

# Dominant CTE1973 constituents per spherical-harmonic order m. Each entry is
# (Doodson multipliers tau,s,h,p,N',ps; amplitude Hs1 (m); frequency deg/hr).
CONSTITUENTS = {
    0: [
        ((0, 2, 0, 0, 0, 0), -0.06663, 1.0980331),  # Mf
        ((0, 1, 0, -1, 0, 0), -0.03518, 0.5443747),  # Mm
        ((0, 0, 2, 0, 0, 0), -0.03100, 0.0821373),  # Ssa
        ((0, 0, 1, 0, 0, -1), -0.00492, 0.0410686),  # Sa
    ],
    1: [
        ((1, 1, 0, 0, 0, 0), 0.36878, 15.0410686),  # K1
        ((1, -1, 0, 0, 0, 0), -0.26221, 13.9430356),  # O1
        ((1, 1, -2, 0, 0, 0), -0.12203, 14.9589314),  # P1
        ((1, -2, 0, 1, 0, 0), -0.05020, 13.3986609),  # Q1
    ],
    2: [
        ((2, 0, 0, 0, 0, 0), 0.63192, 28.9841042),  # M2
        ((2, 2, -2, 0, 0, 0), 0.29400, 30.0000000),  # S2
        ((2, -1, 0, 1, 0, 0), 0.12099, 28.4397295),  # N2
        ((2, 2, 0, 0, 0, 0), 0.07996, 30.0821373),  # K2
    ],
}

# Per-order phase offset between the CTE catalogue convention and the Doodson
# evaluation here (determined by matching the synthesized series against the
# point-mass ephemeris potential).
PHASE_SHIFT = {0: np.pi, 1: np.pi / 2.0, 2: 0.0}


def frequency_dependent_love_numbers(omega: float) -> tuple[complex, complex]:
    """Return (h2, k2) complex Love numbers for angular frequency omega (rad/s)."""
    f = omega * SIDEREAL_DAY / (2.0 * np.pi)
    if omega == 0.0:
        return 0.6078 + 0j, 0.30190 + 0j
    if omega > 1e-4:
        return 0.6078 - 0.0022j, 0.30102 - 0.0013j
    if omega < 2e-5:
        reference = SIDEREAL_DAY / 200.0
        factor = 1.0 / np.tan(ANELASTIC_ALPHA * np.pi / 2.0)
        model = factor * (1.0 - (reference / f) ** ANELASTIC_ALPHA) + 1j * (
            reference / f
        ) ** ANELASTIC_ALPHA
        return 0.5998 - 9.96e-4 * model, 0.29525 - 5.796e-4 * model
    sigma = np.concatenate([[f - 1.0], DIURNAL_SIGMA])
    h2 = np.sum(DIURNAL_H2 / (f - sigma))
    k2 = np.sum(DIURNAL_K2 / (f - sigma))
    return h2, k2


def _catalog_series(
    order: int, tau: np.ndarray, S: np.ndarray, H: np.ndarray, P: np.ndarray,
    Np: np.ndarray, ps: np.ndarray, longitude_rad: float,
) -> np.ndarray:
    series = np.zeros_like(tau)
    for (mult, amplitude, _) in CONSTITUENTS[order]:
        tau_m, s_m, h_m, p_m, n_m, pp_m = mult
        theta = (
            tau_m * tau
            + s_m * S
            + h_m * H
            + p_m * P
            + n_m * Np
            + pp_m * ps
            + order * longitude_rad
            + PHASE_SHIFT[order]
        )
        series += amplitude * np.cos(theta)
    return series


def frequency_correction(
    potential_m: np.ndarray,
    doodson_args_deg: np.ndarray,
    longitude_rad: float,
    order: int,
    k2_nominal: float,
    h2_nominal: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Frequency-dependent corrections to the induced and effective potentials.

    Returns (induced_correction, effective_correction): additive corrections to
    the nominal k2*V and (1+k2-h2)*V potentials of a given order.
    """
    tau, S, H, P, Np, ps = (np.radians(doodson_args_deg[:, i]) for i in range(6))
    series = _catalog_series(order, tau, S, H, P, Np, ps, longitude_rad)
    scale = np.dot(potential_m, series) / np.dot(series, series)

    induced_correction = np.zeros_like(potential_m)
    effective_correction = np.zeros_like(potential_m)
    for (mult, amplitude, freq_deg_hr) in CONSTITUENTS[order]:
        tau_m, s_m, h_m, p_m, n_m, pp_m = mult
        theta = (
            tau_m * tau
            + s_m * S
            + h_m * H
            + p_m * P
            + n_m * Np
            + pp_m * ps
            + order * longitude_rad
            + PHASE_SHIFT[order]
        )
        omega = freq_deg_hr * DEG_HR_TO_RAD_S
        h2, k2 = frequency_dependent_love_numbers(omega)
        delta_k = k2 - k2_nominal
        delta_kh = (k2 - k2_nominal) - (h2 - h2_nominal)
        in_phase = amplitude * np.cos(theta)
        quadrature = amplitude * np.sin(theta)
        induced_correction += scale * (
            delta_k.real * in_phase - delta_k.imag * quadrature
        )
        effective_correction += scale * (
            delta_kh.real * in_phase - delta_kh.imag * quadrature
        )
    return induced_correction, effective_correction
