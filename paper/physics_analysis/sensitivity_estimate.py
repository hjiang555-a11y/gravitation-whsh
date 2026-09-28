#!/usr/bin/env python3
"""Illustrative BSM sensitivity estimates for the Wuhan-Shanghai Yb/Sr comparison.

Turns the *existing* repository stability artifacts into order-of-magnitude
("illustrative") sensitivity estimates for physics beyond the Standard Model,
following the analysis template of the BACON collaboration
(Beloy et al., Nature 591, 564 (2021)) - the reference paper `paper/3104.pdf`.

WHAT IT COMPUTES
----------------
1. A per-segment white-frequency-noise (WFM) coefficient h_0 from the published
   per-segment fractional stability sigma_y(T_i):

       h_0 = 2 * sigma_y(T_i)^2 * T_i          [fractional^2 * s]

2. The combined fractional-amplitude reach delta_R of a coherent sinusoidal
   search over the total *valid* observing time T_valid:

       delta_R_reach ~ sqrt(2 * h_0 / T_valid)  ~ sqrt(2) * sigma_y(T_valid)

   This is the standard WFM result: the 1-sigma sensitivity to a coherent
   sinusoidal modulation is set by the clock stability at the total averaging
   time (scaled by the quadrature-convention factor sqrt(2)). It is FLAT in the
   oscillation frequency f for WFM. See REPORT.md for the derivation and its
   limitations.

3. From delta_R, the ultralight-bosonic-dark-matter photon coupling d_e via the
   BACON conversion (Nature 591, 564 (2021), "Dark-matter constraints"):

       d_e = 4.2e30 * delta_R * m_phi / DeltaK          (m_phi in eV)

   with DeltaK = |K_Yb - K_Sr| = 0.25 for the Yb/Sr ratio.

4. The dilaton coupling Lambda_gamma = M_Pl / (sqrt(4 pi) d_e) [GeV].

BACON SEARCH BAND (Nature 591, 564 (2021)):
    1/(20 T_max) < omega_C/2pi < 1/100 s
i.e. the LOWER Compton-frequency cutoff is 1/(20 T_max) (T_max = span between
first and last measurements), and the upper cutoff is 1/100 s (100-s servo
cutoff). This script uses that band.

INPUTS (read from the repository; no raw beat file needed)
----------------------------------------------------------
- clock_ratio/statistical_methods_tidal.json  -> per-segment T_s and u_frac
- clock_ratio/ratio_17seg.csv                 -> n_valid per segment, timestamps

RESULT FILES
------------
- paper/physics_analysis/sensitivity_estimates.csv  (per-segment table)
- paper/physics_analysis/sensitivity_summary.json   (combined + coupling values)

CAVEATS (MANDATORY - see REPORT.md)
-----------------------------------
The per-segment u_i are *known to be unreliable* (OADEV extrapolation
underestimates by ~30-40%; anomalous segments 5/6/16). The observation window is
fragmented (duty cycle ~20%, long dead-time gaps) and the noise is not strictly
white FM. Everything here is an ORDER-OF-MAGNITUDE estimate for method
illustration ONLY - it is NOT a constraint statement and must not be quoted as
one.

Run:  python paper/physics_analysis/sensitivity_estimate.py
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Physical constants (BACON template; see paper/3104.pdf, "Dark-matter
# constraints" section and Safronova et al., Rev. Mod. Phys. 90, 025008 (2018))
# --------------------------------------------------------------------------
HBAR_EV_S = 6.582119569e-16  # reduced Planck constant [eV s]
M_PLANCK_GEV = 1.220910e19   # Planck mass [GeV]
V_DM_OVER_C = 1.0e-3         # local DM virial velocity / c (standard assumption)

# Relativistic alpha-sensitivity coefficients nu ∝ alpha^K (Safronova RMP 2018).
K_YB = 0.31
K_SR = 0.06
DELTA_K_ALPHA = abs(K_YB - K_SR)          # = 0.25 for the Yb/Sr ratio

# BACON d_e conversion + stochastic rescaling.
D_E_PREFACTOR = 4.2e30        # eV^-1, dimensionless d_e when m_phi in eV
STOCHASTIC_RESCALE = 3.0      # uniform rescaling for Rayleigh-distributed DM amp.
RHO_DM_GEV_CM3 = 0.4          # local DM density assumed by BACON

# BACON search band: 1/(20 T_max) < f < 1/100 s.
F_MAX_HZ = 1.0 / 100.0        # upper Compton frequency (100-s servo cutoff)

REPO_ROOT = Path(__file__).resolve().parents[2]
STAT_JSON = REPO_ROOT / "clock_ratio" / "statistical_methods_tidal.json"
RATIO_CSV = REPO_ROOT / "clock_ratio" / "ratio_17seg.csv"
OUT_DIR = Path(__file__).resolve().parent


def load_per_segment() -> list[dict]:
    """Per-segment T_s, fractional sigma_y(T) and n_valid from repo artifacts."""
    stat = json.loads(STAT_JSON.read_text())
    per_seg = stat["scenarios"]["raw"]["per_segment"]

    nvalid: dict[int, int] = {}
    with open(RATIO_CSV) as f:
        for row in csv.DictReader(f):
            nvalid[int(row["group"])] = int(row["n_valid"])

    rows = []
    for entry in per_seg:
        g = int(entry["group"])
        rows.append({
            "group": g,
            "T_s": int(entry["T_s"]),
            "n_valid": nvalid.get(g, int(entry["T_s"])),
            "sigma_y_T": float(entry["u_frac"]),   # fractional sigma_y(T)
        })
    return rows


def h0_from_segment(sigma_y_T: float, t_s: float) -> float:
    """White-FM coefficient h_0 = 2 sigma_y(T)^2 T  [fractional^2 s].

    For white frequency noise sigma_y^2(tau) = h_0 / (2 tau); inverting gives
    h_0 = 2 sigma_y^2(T) T. Consistent for any averaging time T in the WFM
    regime (the point of the WFM model).
    """
    return 2.0 * sigma_y_T ** 2 * t_s


def delta_R_reach_from_h0(h0: float, t_eff_s: float) -> float:
    """Amplitude reach of a coherent sinusoid: sqrt(2 h_0 / T_eff).

    Equivalent to sqrt(2) * sigma_y(T_eff) for WFM. The sqrt(2) is the
    quadrature-convention factor; the order-of-magnitude result is ~= sigma_y(T).
    """
    if t_eff_s <= 0:
        return float("nan")
    return math.sqrt(2.0 * h0 / t_eff_s)


def d_e_from_amplitude(delta_R: float, m_phi_ev: float) -> float:
    """BACON photon-coupling conversion d_e = 4.2e30 * dR * m_phi / DeltaK."""
    return D_E_PREFACTOR * delta_R * m_phi_ev / DELTA_K_ALPHA


def lambda_gamma_gev(d_e: float) -> float:
    """Dilaton coupling Lambda_gamma = M_Pl / (sqrt(4 pi) d_e) [GeV]."""
    if d_e == 0:
        return float("inf")
    return M_PLANCK_GEV / (math.sqrt(4 * math.pi) * d_e)


def main() -> int:
    rows = load_per_segment()
    total_T = sum(r["n_valid"] for r in rows)   # total valid time T_valid

    # Observation span (wall clock) from first/last retained sample timestamps.
    t_first = t_last = None
    with open(RATIO_CSV) as f:
        for row in csv.DictReader(f):
            if t_first is None:
                t_first = row["t_start_beijing"]
            t_last = row["t_end_beijing"]
    fmt = "%Y-%m-%dT%H:%M:%S"
    span_s = (datetime.strptime(t_last, fmt)
              - datetime.strptime(t_first, fmt)).total_seconds()

    # BACON band: f_min = 1/(20 T_max), f_max = 1/100 s.
    f_min = 1.0 / (20.0 * span_s)
    m_min_ev = 2 * math.pi * f_min * HBAR_EV_S
    m_max_ev = 2 * math.pi * F_MAX_HZ * HBAR_EV_S

    # --- per-segment h_0 and reach ---------------------------------------
    out_rows = []
    for r in rows:
        h0 = h0_from_segment(r["sigma_y_T"], r["T_s"])
        # individual-segment reach over that segment's own time
        dR_seg = delta_R_reach_from_h0(h0, r["T_s"])
        out_rows.append({**r, "h0": h0, "delta_R_reach": dR_seg})

    # --- combined reach ---------------------------------------------------
    # Option A (primary): combine the per-segment h_0 (mean), then evaluate the
    # reach at the total valid time T_valid. Standard WFM treatment when the
    # noise is (approximately) white across segments.
    h0_bar = sum(r["h0"] for r in out_rows) / len(out_rows)
    delta_R_comb = delta_R_reach_from_h0(h0_bar, total_T)

    # Option B (cross-check): inverse-variance combination of per-segment
    # reaches (treats each segment as an independent estimate of the same
    # amplitude) - typically slightly more optimistic.
    wsum = sum(1.0 / r["delta_R_reach"] ** 2 for r in out_rows
               if r["delta_R_reach"] > 0)
    delta_R_iv = 1.0 / math.sqrt(wsum) if wsum > 0 else float("nan")

    # --- coherence-time context ------------------------------------------
    # tau_c ~ 2 pi hbar / (m v^2), v ~ 1e-3 c (standard virial assumption).
    def tau_c(m_ev: float) -> float:
        return 2 * math.pi * HBAR_EV_S / (m_ev * V_DM_OVER_C ** 2)

    tau_c_at_mmin = tau_c(m_min_ev)
    tau_c_at_mmax = tau_c(m_max_ev)

    # Coupling values at band edges.
    def couplings(dR: float) -> dict:
        de_lo = d_e_from_amplitude(dR, m_min_ev)   # low mass -> smallest d_e
        de_hi = d_e_from_amplitude(dR, m_max_ev)   # high mass -> largest d_e
        return {
            "delta_R_reach": dR,
            "d_e_at_m_min_eV": de_lo,
            "d_e_at_m_max_eV": de_hi,
            "d_e_scaled_rayleigh_at_m_min_eV": de_lo * STOCHASTIC_RESCALE,
            "lambda_gamma_gev_at_m_min": lambda_gamma_gev(de_lo),
        }

    summary = {
        "description": (
            "ILLUSTRATIVE order-of-magnitude BSM sensitivity for the "
            "Wuhan-Shanghai Yb/Sr comparison. NOT a constraint statement."
        ),
        "inputs": {
            "stat_json": str(STAT_JSON.relative_to(REPO_ROOT)),
            "ratio_csv": str(RATIO_CSV.relative_to(REPO_ROOT)),
            "n_segments": len(rows),
            "total_valid_s": total_T,
            "observation_span_s": span_s,
            "duty_cycle": total_T / span_s,
        },
        "constants": {
            "K_Yb": K_YB,
            "K_Sr": K_SR,
            "DeltaK_alpha": DELTA_K_ALPHA,
            "d_e_prefactor_eV_inv": D_E_PREFACTOR,
            "stochastic_rescale": STOCHASTIC_RESCALE,
            "rho_dm_GeV_cm3": RHO_DM_GEV_CM3,
            "v_dm_over_c": V_DM_OVER_C,
        },
        "mass_band_eV": {
            "f_min_Hz": f_min,
            "f_max_Hz": F_MAX_HZ,
            "m_phi_min_eV": m_min_ev,
            "m_phi_max_eV": m_max_ev,
            "coherence_time_at_m_min_s": tau_c_at_mmin,
            "coherence_time_at_m_max_s": tau_c_at_mmax,
        },
        "h0_mean_fractional2_s": h0_bar,
        "combined_h0": couplings(delta_R_comb),
        "combined_inverse_variance": couplings(delta_R_iv),
    }

    # --- write outputs ---------------------------------------------------
    csv_path = OUT_DIR / "sensitivity_estimates.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "T_s", "n_valid", "sigma_y_T",
                    "h0_fractional2_s", "delta_R_reach_segment"])
        for r in out_rows:
            w.writerow([
                r["group"], r["T_s"], r["n_valid"],
                f"{r['sigma_y_T']:.6e}",
                f"{r['h0']:.6e}",
                f"{r['delta_R_reach']:.6e}",
            ])

    json_path = OUT_DIR / "sensitivity_summary.json"
    json_path.write_text(json.dumps(summary, indent=2) + "\n")

    # --- console report --------------------------------------------------
    print("=== Wuhan-Shanghai Yb/Sr - illustrative BSM sensitivity ===")
    print(f"segments={len(rows)}  T_valid={total_T} s  span={span_s:.0f} s  "
          f"duty={total_T/span_s*100:.1f}%")
    print(f"DeltaK_alpha(Yb/Sr) = |{K_YB} - {K_SR}| = {DELTA_K_ALPHA}")
    print(f"BACON band: f = {f_min:.3e} .. {F_MAX_HZ:.3e} Hz")
    print(f"            m_phi = {m_min_ev:.3e} .. {m_max_ev:.3e} eV")
    print(f"coherence time at band edges: {tau_c_at_mmin:.2e} s .. "
          f"{tau_c_at_mmax:.2e} s")
    print()
    print("per-segment (sigma_y(T) -> h_0 -> delta_R over its own T):")
    for r in out_rows:
        print(f"  seg {r['group']:>2}: T={r['T_s']:>7}s  "
              f"sigma_y(T)={r['sigma_y_T']:.3e}  h0={r['h0']:.3e}  "
              f"dR={r['delta_R_reach']:.3e}")
    print()
    print(f"mean h_0 = {h0_bar:.3e}")
    print(f"combined reach delta_R (h_0 mean @ T_valid) = {delta_R_comb:.3e}")
    print(f"combined reach delta_R (inverse-variance)    = {delta_R_iv:.3e}")
    print()
    c = summary["combined_h0"]
    print(f"combined  d_e(m_min) = {c['d_e_at_m_min_eV']:.3e}  "
          f"(x{STOCHASTIC_RESCALE:g} Rayleigh -> "
          f"{c['d_e_scaled_rayleigh_at_m_min_eV']:.3e})")
    print(f"combined  d_e(m_max) = {c['d_e_at_m_max_eV']:.3e}")
    print(f"combined  Lambda_gamma(m_min) = "
          f"{c['lambda_gamma_gev_at_m_min']:.3e} GeV")
    print()
    print(f"wrote {csv_path.name}, {json_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
