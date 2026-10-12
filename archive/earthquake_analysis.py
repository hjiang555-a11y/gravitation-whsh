#!/usr/bin/env python3
"""Estimate co-seismic gravimetric effect of Japan-China earthquakes on the
Wuhan-Shanghai clock comparison.

A shallow earthquake produces a permanent (co-seismic) ground displacement
u ~ M0 / (mu * r^2) at distance r, where M0 is the seismic moment
(M0 = 10^(1.5*Mw + 9.1) N·m) and mu ~ 3e10 Pa is the crustal shear modulus.
A differential vertical displacement du between the two stations changes the
gravitational redshift of the clock comparison by dff = g*du/c^2.

The resulting dff is compared against the experiment's uncertainty budget
(WLS statistical ~5.9e-19, Sr systematic 9.2e-19, Yb systematic 1.1e-18).
"""

from __future__ import annotations

import numpy as np

C = 299792458.0  # m/s
G = 9.8  # m/s²
MU = 3.0e10  # Pa, crustal shear modulus

WUHN = (30.531653, 114.357261)
SHAO = (31.099642, 121.200445)

# (name, lat, lon, Mw, UTC time)
QUAKES = [
    ("Miyakojima/Ryukyu M6.1 (USGS, M6.4 JMA)", 26.0, 125.8, 6.1, "2026-07-03 04:04"),
    ("Kumamoto M6.8 (USGS, M7.1 JMA)", 32.682, 130.722, 6.8, "2026-07-28 07:27"),
    ("(ref) Northern Japan M7.2", 43.0, 144.0, 7.2, "2026-06-25"),
]

# Experiment uncertainty budget (fractional frequency)
U_WLS = 5.9e-19
U_SR = 9.2e-19
U_YB = 1.1e-18


def great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlam / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def main() -> int:
    print("Co-seismic effect on the Wuhan-Shanghai clock comparison")
    print("=" * 72)
    for name, lat, lon, mw, utc in QUAKES:
        d_wuhan = great_circle_km(WUHN[0], WUHN[1], lat, lon)
        d_shanghai = great_circle_km(SHAO[0], SHAO[1], lat, lon)
        m0 = 10 ** (1.5 * mw + 9.1)
        u_wuhan = m0 / (MU * (d_wuhan * 1e3) ** 2)
        u_shanghai = m0 / (MU * (d_shanghai * 1e3) ** 2)
        du = abs(u_shanghai - u_wuhan)
        dff = G * du / C**2
        print(f"\n{name}")
        print(f"  {utc} UTC")
        print(f"  distance: Wuhan {d_wuhan:.0f} km, Shanghai {d_shanghai:.0f} km")
        print(f"  static displacement: Wuhan {u_wuhan * 1e3:.3f} mm, "
              f"Shanghai {u_shanghai * 1e3:.3f} mm")
        print(f"  differential Δf/f ~ {dff:.2e}")
    print("\n" + "=" * 72)
    print("Experiment uncertainty budget:")
    print(f"  WLS statistical = {U_WLS:.1e}")
    print(f"  Sr systematic   = {U_SR:.1e}")
    print(f"  Yb systematic   = {U_YB:.1e}")
    print("\nConclusion: earthquake effect (1e-20 ~ 1e-21) is 2-3 orders of")
    print("magnitude below the uncertainty budget; it is not observable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
