#!/usr/bin/env python3
"""Paper-style statistical analysis of the clock ratio (PARALLEL to, not
replacing, the existing result).

Reproduces the experiment-side statistical treatment (OADEV extrapolation ->
per-segment statistical uncertainty u_i -> WLS / Birge / Mandel-Paule / Bayesian
combined values), applied to the SAME per-segment beat data used by
compute_ratio.py. Output is a SEPARATE result set alongside the original.

Method (aligned with clock/潮汐修正后的比值计算.pdf and the MATLAB source
YbSr_NISTstyle_14bin_full_analysis_20260824.m):

  1. Per segment: shared gap-aware selection (select_segments: longest
     jump-free span, endpoint-screen 1% peak-to-peak).
  2. Gap-safe OADEV: TRUE overlapping Allan deviation of the beat fractional
     frequency (normalized to F_1550 = N1550_WH·f_rep = 193.3992 THz), computed
     by clock_ratio.segment_uncertainty inside the prespecified window
     128 s <= tau <= 0.25*T with T = longest gap-free run, fit to
     log sigma_y = a + b·log tau and extrapolated to tau = T. Underdetermined
     fits and non-white slopes are flagged; the longest tau is never reused.
  3. u_i = sigma_y(T) * R_i  (per-segment clock-ratio statistical uncertainty).
  4. Combined values via the typed core: WLS / Birge / Mandel-Paule / Bayesian.
  5. Gravitational correction (whole-experiment total): per-method weighted mean
     of Δf/f = ΔW/c² (same as correlation_reanalysis).

The historical block-mean estimator is preserved as `legacy_block_deviation`
(alias `oadev` for statistical_methods_tidal.py) for comparison; it is NOT
true OADEV and its numeric difference from the new estimator is an algorithm
change, not a physics signal.

Outputs:
  clock_ratio/statistical_methods.csv   (per-segment u_i, and the 4 combined values)
  clock_ratio/statistical_methods.json  (structured results for the report)
"""

from __future__ import annotations

import csv
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.sample_selection import (  # noqa: E402
    DEFAULT_SELECTION_PLAN, AnalysisError, SelectedSegment, select_segments,
)
from clock.shared import F_1550, GROUPS, load_beat, load_tide  # noqa: E402
from clock_ratio.segment_uncertainty import (  # noqa: E402
    SegmentUncertainty, StabilityFitConfig, estimate_segment_uncertainty,
)
from clock_ratio.statistical_models import (  # noqa: E402
    CombinationResult, SegmentEstimate, combine_estimates,
)
from clock_ratio.tidal_stability import continuous_runs  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent
C = 299792458.0


def legacy_block_deviation(x: np.ndarray, tau0: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Legacy block-mean deviation of fractional-frequency data (NOT true OADEV).

    x is the FRACTIONAL frequency (beat / F_1550). Returns (tau, sigma_y) arrays.
    Uses non-overlapping block means and the differences of consecutive windows;
    retained only for the historical comparison and the tidal caller.
    """
    x = np.asarray(x, dtype=float)
    out_tau, out_sig = [], []
    n = len(x)
    m = 1
    while 3 * m <= n:
        # non-overlapping means of length m
        nseg = n // m
        ymeans = x[: nseg * m].reshape(nseg, m).mean(axis=1)
        # overlapping first differences at stride m (Allan variance with tau=m)
        # overlapping pairs: consecutive window means
        tau_sec = m * tau0
        # overlapping Allan variance using all available differences
        if nseg >= 2:
            d = np.diff(ymeans)
            sig2 = np.sum(d ** 2) / (2.0 * (len(d)))
            out_tau.append(tau_sec)
            out_sig.append(np.sqrt(sig2))
        m *= 2
    return np.array(out_tau), np.array(out_sig)


# Compatibility alias: clock_ratio.statistical_methods_tidal.py imports `oadev`
# from here (Task 10 migrates that caller). This block-mean estimator is NOT
# true overlapping Allan deviation; the audit result uses segment_uncertainty.
oadev = legacy_block_deviation


def extrapolate_u(tau, sig, T):
    """Fit log(sigma) = a + b*log(tau) over 128s<=tau<=T/4, extrapolate to T."""
    mask = (tau >= 128) & (tau <= max(128, T / 4)) & (sig > 0)
    if mask.sum() < 2:
        # fall back to the longest available tau
        i = np.argmax(tau)
        return sig[i]
    lt = np.log(tau[mask])
    ls = np.log(sig[mask])
    b, a = np.polyfit(lt, ls, 1)
    # white frequency noise -> b = -1/2; extrapolate
    lT = np.log(T)
    return float(np.exp(a + b * lT))


def analyze_raw_statistics(
    segments: Sequence[SelectedSegment],
    ratios: Mapping[int, Decimal],
    config: StabilityFitConfig,
) -> tuple[tuple[SegmentUncertainty, ...], CombinationResult]:
    """Pure per-segment gap-safe fit and combination; no file I/O.

    y_i = R_g / R_1 - 1 (fractional, segment-1 baseline) and u_i = u_frac * R_g
    (absolute ratio). A segment without a defined u_fractional aborts the whole
    analysis -- fail-fast, never a silent exclusion.
    """
    if 1 not in ratios:
        raise AnalysisError("segment-1 ratio is required as the y_i baseline")
    reference = ratios[1]
    results: list[SegmentUncertainty] = []
    estimates: list[SegmentEstimate] = []
    for segment in segments:
        if segment.group not in ratios:
            raise AnalysisError(f"segment {segment.group}: missing clock ratio")
        fractional = (segment.beat - segment.beat.mean()) / F_1550
        fit = estimate_segment_uncertainty(segment.times, fractional, config)
        if fit.u_fractional is None:
            raise AnalysisError(
                f"segment {segment.group}: fewer than three usable OADEV fit "
                "points; refusing a silent longest-tau fallback")
        fit = replace(fit, group=segment.group)
        ratio = ratios[segment.group]
        results.append(fit)
        estimates.append(SegmentEstimate(
            group=segment.group,
            ratio=ratio,
            deviation=float(ratio / reference - Decimal(1)),
            u_absolute=float(Decimal(repr(fit.u_fractional)) * ratio),
        ))
    return tuple(results), combine_estimates(estimates, reference)


def main() -> int:
    # ---- per-segment gap-safe OADEV -> u_i ----
    times, beat = load_beat()
    segments = select_segments(times, beat, DEFAULT_SELECTION_PLAN)

    # load R_i (clock ratio): u_frac -> u_i = u_frac * R_i, y_i = R_i/R_1 - 1
    ratio_rows = list(csv.DictReader(open(OUT_DIR / "ratio_17seg.csv")))
    R = {int(r["group"]): Decimal(r["YbSr_R"]) for r in ratio_rows}
    R0 = R[1]  # segment-1 ratio (Decimal), as the y_i baseline reference

    results, combined = analyze_raw_statistics(segments, R, StabilityFitConfig())

    rows = []
    for segment, result in zip(segments, results, strict=True):
        longest_run = max((stop - start for start, stop in continuous_runs(segment.times)),
                          default=0)
        u_i = float(Decimal(repr(result.u_fractional)) * R[segment.group])
        rows.append({"group": segment.group, "T_s": longest_run,
                     "u_frac": result.u_fractional, "u_i": u_i})

    u_wls = combined.u_wls
    chi2 = combined.chi2
    dof = combined.dof
    chi2_red = combined.chi2_red
    p_chi2 = combined.p_chi2
    birge = combined.birge_ratio
    u_birge = combined.u_birge
    xi_mp = combined.xi_mp
    y_mp = combined.y_mp
    u_mp = combined.u_mp
    mu_post_mean = combined.mu_bayes
    mu_post_sd = combined.u_stat_bayes
    xi_post_mean = combined.xi_bayes

    # ---- Gravitational (tidal) correction, per-method weights ----
    # The tidal correction of each segment is Δf/f = ΔW_i/c² (from
    # clock_tidal_shift.csv). Its whole-experiment total must use the SAME
    # per-segment weights as the corresponding ratio-combination method, NOT a
    # duration weight.
    t_tide, tot = load_tide()
    dff = {}
    for kk, (s, e) in enumerate(GROUPS, 1):
        S = np.datetime64(s) - np.timedelta64(8, "h")  # Beijing -> UTC
        E = np.datetime64(e) - np.timedelta64(8, "h")
        m = (t_tide >= S) & (t_tide <= E)
        if m.sum():
            dff[kk] = float(tot[m].mean()) / C ** 2
    dff_arr = np.array([dff[g] for g in sorted(dff)])

    def weighted(m, w_i):
        return float(np.sum(w_i * dff_arr) / np.sum(w_i))

    u_arr = np.array([r["u_i"] for r in rows])
    w_wls = 1.0 / u_arr ** 2                      # WLS / Birge share these weights
    w_mp = 1.0 / (u_arr ** 2 + xi_mp ** 2)         # M-P effective weights
    w_bay = 1.0 / (u_arr ** 2 + xi_post_mean ** 2) # Bayesian (posterior-mean xi)

    grav_wls = weighted(-1, w_wls)
    grav_birge = grav_wls       # Birge center uses the same 1/u² weights
    grav_mp = weighted(-1, w_mp)
    grav_bayes = weighted(-1, w_bay)

    # ---- assemble outputs ----
    # Precision-weighted (1/u_i²) WLS center; distinct from the duration-weighted
    # (n_valid) center in compute_ratio.py — the two weightings answer different
    # questions and must not be conflated.
    # R[1] is Decimal; reconstruct each center as R0 × (1 + y) in Decimal so the
    # e-19-level y does NOT get swallowed by float64 (error-1 discipline).
    y_wls_d = Decimal(repr(float(combined.y_wls)))
    y_mp_d = Decimal(repr(float(y_mp)))
    mu_d = Decimal(repr(float(mu_post_mean)))
    result = {
        "R_wls": str(R0 * (Decimal(1) + y_wls_d)),
        "u_wls": float(u_wls),
        "chi2": float(chi2),
        "dof": int(dof),
        "chi2_red": float(chi2_red),
        "p_chi2": float(p_chi2),
        "birge_ratio": float(birge),
        "u_birge": float(u_birge),
        "xi_mp": float(xi_mp),
        "R_mp": str(R0 * (Decimal(1) + y_mp_d)),
        "u_mp": float(u_mp),
        "mu_bayes": float(mu_post_mean),
        "u_stat_bayes": float(mu_post_sd),
        "xi_bayes": float(xi_post_mean),
        "R_bayes": str(R0 * (Decimal(1) + mu_d)),
        "grav_wls": grav_wls,
        "grav_birge": grav_birge,
        "grav_mp": grav_mp,
        "grav_bayes": grav_bayes,
        "y_wls_precision_1e18": float(combined.y_wls * 1e18),
    }

    # ---- write CSV ----
    csv_path = OUT_DIR / "statistical_methods.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "T_s", "OADEV_frac_T", "u_i_ratio"])
        for r in rows:
            w.writerow([r["group"], r["T_s"], f"{r['u_frac']:.6e}", f"{r['u_i']:.6e}"])
        w.writerow([])
        w.writerow(["method", "value"])
        for k, v in result.items():
            w.writerow([k, f"{v}"])

    json_path = OUT_DIR / "statistical_methods.json"
    with json_path.open("w") as f:
        json.dump(result, f, indent=2)

    print("=== per-segment OADEV -> u_i ===")
    for r in rows:
        print(f"  seg {r['group']:>2}: T={r['T_s']:>6}s  sigma_y(T)={r['u_frac']:.3e}  u_i={r['u_i']:.3e}")
    print("\n=== combined values ===")
    print(f"WLS      : R = {result['R_wls'][:22]}  u = {result['u_wls']:.3e}")
    print(f"  chi2 = {chi2:.3f} (dof={dof}, chi2_red={chi2_red:.3f}, p={p_chi2:.3f})")
    print(f"Birge    : ratio = {birge:.3f}  u = {u_birge:.3e}")
    print(f"Mandel-P : xi = {xi_mp:.3e}  u = {u_mp:.3e}  R = {result['R_mp'][:22]}")
    print(f"Bayesian : mu = {mu_post_mean:.3e}  u = {mu_post_sd:.3e}  xi = {xi_post_mean:.3e}")
    print(f"          R = {result['R_bayes'][:22]}")
    print(f"\ngravitational (tidal) correction, per-method weights:")
    print(f"  WLS   : {grav_wls:.6e}")
    print(f"  Birge : {grav_birge:.6e}  (same 1/u² weights as WLS)")
    print(f"  M-P   : {grav_mp:.6e}")
    print(f"  Bayes : {grav_bayes:.6e}")
    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
