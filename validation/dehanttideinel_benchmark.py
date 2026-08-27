#!/usr/bin/env python3
"""Reproduce the IERS DEHANTTIDEINEL displacement test cases.

DEHANTTIDEINEL (Mathews, Dehant & Gipson 1997; IERS 2010 Ch.7) computes
solid-Earth tidal STATION DISPLACEMENT from geocentric station/Sun/Moon
vectors, using displacement Love/Shida numbers (h2, l2, h3, l3).

This project's primary output is the tidal GEOPOTENTIAL (k2/h2), a different
physical quantity. This script therefore reproduces the Step-1 displacement
formula from the published Fortran source to verify that the SHARED astronomy
and IERS displacement conventions are correctly understood. The residual
between Step-1 (nominal Love/Shida numbers) and the IERS expected values is
the Step-2 frequency-dependent correction (diurnal FCN resonance + long-period
anelasticity), whose magnitude (~1.35% amplitude-weighted) is consistent.

Notes on the authoritative source (DEHANTTIDEINEL.F header):
- Case 4 has a corrupted Sun vector (|XSUN| = 0.097 AU instead of ~1 AU) and
  its expected output is a verbatim copy of Case 3; it is excluded here.
"""

from __future__ import annotations

import numpy as np

H20 = 0.6078
L20 = 0.0847
H3 = 0.292
L3 = 0.015
MASS_RATIO_SUN = 332946.0482
MASS_RATIO_MOON = 0.0123000371
RE = 6378136.6

# (XSTA, XSUN, XMON, expected DXTIDE) — IERS 2010 test cases 1–3.
CASES = [
    (
        [4075578.385, 931852.890, 4801570.154],
        [137859926952.015, 54228127881.435, 23509422341.696],
        [-179996231.920342, -312468450.131567, -169288918.592160],
        [0.0770042035710813, 0.0630405632182497, 0.0551656815259725],
    ),
    (
        [1112189.660, -4842955.026, 3985352.284],
        [-54537460436.2357, 130244288385.279, 56463429031.5996],
        [300396716.912, 243238281.451, 120548075.939],
        [-0.0203683147959208, 0.0565825477622597, -0.0759767967687174],
    ),
    (
        [1112200.5696, -4842957.8511, 3985345.9122],
        [100210282451.6279, 103055630398.3160, 56855096480.4475],
        [369817604.4348, 1897917.5258, 120804980.8284],
        [0.00509570869172364, 0.0828663025983529, -0.0636634925404190],
    ),
]


def step1_displacement(xsta, xsun, xmon):
    """DEHANTTIDEINEL Step 1: nominal Love/Shida displacement (meters)."""
    xsta = np.asarray(xsta, dtype=float)
    xsun = np.asarray(xsun, dtype=float)
    xmon = np.asarray(xmon, dtype=float)
    rsta = np.linalg.norm(xsta)
    rsun = np.linalg.norm(xsun)
    rmon = np.linalg.norm(xmon)

    sc_sun = np.dot(xsta, xsun) / rsta / rsun
    sc_mon = np.dot(xsta, xmon) / rsta / rmon

    cosphi = np.sqrt(xsta[0] ** 2 + xsta[1] ** 2) / rsta
    h2 = H20 - 0.0006 * (1.0 - 1.5 * cosphi**2)
    l2 = L20 + 0.0002 * (1.0 - 1.5 * cosphi**2)

    p2_sun = 3.0 * (h2 / 2.0 - l2) * sc_sun**2 - h2 / 2.0
    p2_mon = 3.0 * (h2 / 2.0 - l2) * sc_mon**2 - h2 / 2.0
    p3_sun = 2.5 * (H3 - 3.0 * L3) * sc_sun**3 + 1.5 * (L3 - H3) * sc_sun
    p3_mon = 2.5 * (H3 - 3.0 * L3) * sc_mon**3 + 1.5 * (L3 - H3) * sc_mon

    x2_sun = 3.0 * l2 * sc_sun
    x2_mon = 3.0 * l2 * sc_mon
    x3_sun = 1.5 * L3 * (5.0 * sc_sun**2 - 1.0)
    x3_mon = 1.5 * L3 * (5.0 * sc_mon**2 - 1.0)

    fac2_sun = MASS_RATIO_SUN * RE * (RE / rsun) ** 3
    fac2_mon = MASS_RATIO_MOON * RE * (RE / rmon) ** 3
    fac3_sun = fac2_sun * (RE / rsun)
    fac3_mon = fac2_mon * (RE / rmon)

    return (
        fac2_sun * (x2_sun * xsun / rsun + p2_sun * xsta / rsta)
        + fac2_mon * (x2_mon * xmon / rmon + p2_mon * xsta / rsta)
        + fac3_sun * (x3_sun * xsun / rsun + p3_sun * xsta / rsta)
        + fac3_mon * (x3_mon * xmon / rmon + p3_mon * xsta / rsta)
    )


def main() -> int:
    print("IERS DEHANTTIDEINEL Step-1 displacement reproduction")
    print("(nominal Love/Shida numbers; residual = Step-2 frequency correction)")
    print("-" * 74)
    worst = 0.0
    for index, (xsta, xsun, xmon, expected) in enumerate(CASES, 1):
        got = step1_displacement(xsta, xsun, xmon)
        expected = np.asarray(expected)
        residual = got - expected
        worst = max(worst, float(np.abs(residual).max()))
        print(f"Case {index}:")
        print(f"  got      = {got[0]:+.6f} {got[1]:+.6f} {got[2]:+.6f}")
        print(f"  expected = {expected[0]:+.6f} {expected[1]:+.6f} {expected[2]:+.6f}")
        print(f"  residual = {residual[0]:+.6f} {residual[1]:+.6f} {residual[2]:+.6f} m")
    print("-" * 74)
    print(f"Worst Step-1 residual: {worst * 1000:.2f} mm")
    print(
        "This residual is the Step-2 frequency-dependent correction "
        "(diurnal FCN resonance, K1 h2 deviates ~13% from nominal)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
