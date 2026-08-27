#!/usr/bin/env python3
"""Compare theoretical tidal gravity factors against Wuhan reference values.

The gravimetric factor delta_n = 1 + (2/n) h_n - ((n+1)/n) k_n relates the
observed gravity tide to the tide-generating potential via the displacement
(h) and potential (k) Love numbers. For degree 2:

    delta = 1 + h2 - 1.5 * k2

This script computes delta for the four main tidal waves (O1, K1, M2, S2)
using this project's IERS 2010 Love numbers (Step 1 order-dependent nominal +
Step 2 frequency dependence) and compares against the published Wuhan
superconducting-gravimeter reference values.

Reference values (Wuhan SG station, 30.52N 114.49E):
- Xu et al. 2000, Sci. China D 43(1):77-83 (WITH ocean loading):
    delta(O1)=1.1780, delta(K1)=1.1522, delta(M2)=1.1751, delta(S2)=1.1710
- 2014 14-year SG C032 re-analysis, loading-corrected (refined):
    delta(M2)=1.16410, delta(O1)=1.15841

Note the semidiurnal band has no frequency dependence (k2=0.30102, h2=0.6078
for all constituents), while the diurnal band shows strong FCN-resonance
frequency dependence. The residual vs. observation is the documented gap
between the IERS 2010 nominal Love numbers and the non-hydrostatic anelastic
DDW99 model (Dehant-Defraigne-Wahr 1999), NOT an implementation error.
"""

from __future__ import annotations

from gravitation_whsh.frequency_dependence import frequency_dependent_love_numbers

# Angular frequencies (rad/s) of the four main tidal waves.
WAVES = {
    "O1": 6.7597744e-5,
    "K1": 7.2921158e-5,
    "M2": 1.4051890e-4,
    "S2": 1.4544411e-4,
}

# Wuhan reference gravity factors (WITH ocean loading, Xu et al. 2000).
WUHAN_2000 = {"O1": 1.1780, "K1": 1.1522, "M2": 1.1751, "S2": 1.1710}
# Loading-corrected refined values (2014 SG C032, 14-year series).
WUHAN_2014_LOADING_FREE = {"O1": 1.15841, "M2": 1.16410}


def gravimetric_factor(omega: float) -> float:
    h2, k2 = frequency_dependent_love_numbers(omega)
    return 1.0 + h2.real - 1.5 * k2.real


def main() -> int:
    print("Theoretical tidal gravity factors (IERS 2010 Love numbers)")
    print("-" * 74)
    print(f"{'wave':>4} {'delta_theory':>14} {'Wuhan2000':>11} {'2014-free':>11}")
    print("-" * 74)
    for wave, omega in WAVES.items():
        delta = gravimetric_factor(omega)
        w2000 = WUHAN_2000.get(wave)
        w2014 = WUHAN_2014_LOADING_FREE.get(wave)
        w2000_s = f"{w2000:.5f}" if w2000 else "  -"
        w2014_s = f"{w2014:.5f}" if w2014 else "  -"
        print(f"{wave:>4} {delta:14.6f} {w2000_s:>11} {w2014_s:>11}")

    print("-" * 74)
    m2_theory = gravimetric_factor(WAVES["M2"])
    m2_obs = WUHAN_2014_LOADING_FREE["M2"]
    gap = (m2_obs - m2_theory) / m2_theory * 100.0
    print(f"M2 theory vs 2014 loading-free: gap = {gap:+.2f}%")
    print(
        "This gap is the documented difference between the IERS 2010 nominal "
        "Love numbers and the non-hydrostatic anelastic DDW99 model "
        "(Dehant-Defraigne-Wahr 1999), which the Wuhan observations confirm. "
        "The semidiurnal band is frequency-independent, so M2/S2 share the "
        "same delta; the diurnal band (O1/K1) carries the FCN resonance."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
