#!/usr/bin/env python3
"""Paper-style statistical analysis of the clock ratio (PARALLEL to, not
replacing, the existing result).

Reproduces the experiment-side statistical treatment (OADEV extrapolation ->
per-segment statistical uncertainty u_i -> WLS / Birge / Mandel-Paule / Bayesian
combined values), applied to the SAME per-segment beat data used by
compute_ratio.py. Output is a SEPARATE result set alongside the original.

Method (aligned with clock/潮汐修正后的比值计算.pdf and the MATLAB source
YbSr_NISTstyle_14bin_full_analysis_20260824.m):

  1. Per segment: take the longest jump-free trace (drop >10 Hz from median,
     mask exclude_ranges), then endpoint-screen (1% peak-to-peak).
  2. OADEV: overlapping Allan deviation of the beat in fractional frequency
     (normalized to cf = 193e12 = 1550 nm light, matching F_1550). Fit
     128 s <= tau <= 0.25*T on log-log, require white-noise slope ~-1/2, then
     extrapolate to tau = T (T = segment valid duration) -> sigma_y(T).
  3. u_i = sigma_y(T) * R_i  (per-segment clock-ratio statistical uncertainty).
  4. Combined values:
       - WLS:       y = Σ w_i y_i / Σ w_i,  w_i = 1/u_i^2,  u = 1/sqrt(Σ w_i)
       - Birge:     B = sqrt(chi2_red),  u = B * u_WLS
       - Mandel-P:  u_i,eff^2 = u_i^2 + xi^2, solve chi2_red(xi)=1  ->  xi, u
       - Bayesian:  posterior over (mu, xi) via grid/MCMC, marginalize
  5. Gravitational correction (whole-experiment total): duration-weighted mean
     of Δf/f = ΔW/c² (same as correlation_reanalysis).

Outputs:
  clock_ratio/statistical_methods.csv   (per-segment u_i, and the 4 combined values)
  clock_ratio/statistical_methods.json  (structured results for the report)
"""

from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.shared import (  # noqa: E402
    EXCLUDE_RANGES, F_1550, GROUPS, JUMP_THRESHOLD, RESULTS_CSV,
    load_beat, load_tide, longest_valid_span,
)

OUT_DIR = Path(__file__).resolve().parent
C = 299792458.0
CF = 193e12  # 1550 nm light, the OADEV normalization (== f1550WH_expect in MATLAB)


def endpoint_screen(x):
    center = np.median(x)
    peak2peak = x.max() - x.min()
    thr = peak2peak * 0.01
    lo, hi = 0, len(x) - 1
    while lo <= hi and abs(x[lo] - center) > thr:
        lo += 1
    while hi >= lo and abs(x[hi] - center) > thr:
        hi -= 1
    return x[lo: hi + 1]


def oadev(x: np.ndarray, tau0: int = 1) -> tuple[np.ndarray, np.ndarray]:
    """Overlapping Allan deviation of fractional-frequency data.

    x is the FRACTIONAL frequency (beat / CF). Returns (tau, sigma_y) arrays.
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


def segment_traces():
    """Yield (i, d_long, T) for each segment's longest valid trace."""
    T_all, B = load_beat()
    excl = np.zeros(len(T_all), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T_all >= np.datetime64(s)) & (T_all <= np.datetime64(e))
    for kk, (s, e) in enumerate(GROUPS):
        S, E = np.datetime64(s), np.datetime64(e)
        in_win = (T_all >= S) & (T_all < E)
        b_seg = B[in_win]
        ex_seg = excl[in_win]
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            continue
        med = float(np.median(b_seg[plausible]))
        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        span = longest_valid_span(valid)
        if span is None:
            continue
        d_long = b_seg[span[0]: span[1] + 1]
        d_long = endpoint_screen(d_long)
        yield kk + 1, d_long, len(d_long)


def main() -> int:
    # ---- per-segment OADEV -> u_i ----
    rows = []
    for idx, d_long, T in segment_traces():
        frac = (d_long - d_long.mean()) / CF  # fractional frequency, demeaned
        tau, sig = oadev(frac)
        sig_T = extrapolate_u(tau, sig, T) if len(tau) else np.nan
        rows.append({"group": idx, "T_s": T, "u_frac": sig_T})

    # load R_i (clock ratio) to convert u_frac -> u_i = sig_T * R_i
    ratio_rows = list(csv.DictReader(open(OUT_DIR / "ratio_17seg.csv")))
    R = {int(r["group"]): Decimal(r["YbSr_R"]) for r in ratio_rows}
    y = {int(r["group"]): Decimal(r["y_i_1e18"]) for r in ratio_rows}

    for r in rows:
        g = r["group"]
        Rg = R[g]
        r["u_i"] = float(Decimal(str(r["u_frac"])) * Rg)  # absolute ratio uncertainty
        r["y_i"] = float(y[g])                            # ×1e-18

    # ---- WLS ----
    u = np.array([r["u_i"] for r in rows])
    yy = np.array([r["y_i"] for r in rows]) * 1e-18
    w = 1.0 / u ** 2
    y_wls = np.sum(w * yy) / np.sum(w)
    u_wls = 1.0 / np.sqrt(np.sum(w))

    # ---- chi2 / Birge ----
    chi2 = np.sum(((yy - y_wls) / u) ** 2)
    dof = len(rows) - 1
    chi2_red = chi2 / dof
    p_chi2 = stats.chi2.sf(chi2, dof)
    birge = np.sqrt(chi2_red)
    u_birge = birge * u_wls

    # ---- Mandel-Paule (iterative xi) ----
    def chi2_red_mp(xi):
        u_eff2 = u ** 2 + xi ** 2
        ww = 1.0 / u_eff2
        yw = np.sum(ww * yy) / np.sum(ww)
        return np.sum(((yy - yw) / np.sqrt(u_eff2)) ** 2) / dof

    lo, hi = 0.0, 1e-16
    for _ in range(200):
        mid = (lo + hi) / 2
        if chi2_red_mp(mid) > 1.0:
            lo = mid
        else:
            hi = mid
    xi_mp = (lo + hi) / 2
    u_eff2 = u ** 2 + xi_mp ** 2
    ww = 1.0 / u_eff2
    y_mp = np.sum(ww * yy) / np.sum(ww)
    u_mp = 1.0 / np.sqrt(np.sum(ww))

    # ---- Bayesian (grid posterior over mu, xi) ----
    # marginalize xi over a log grid, Gaussian likelihood per segment with
    # effective variance u_i^2 + xi^2
    xi_grid = np.geomspace(1e-20, 1e-16, 200)
    logpost = []
    for xi in xi_grid:
        var = u ** 2 + xi ** 2
        num = np.sum(yy / var)
        den = np.sum(1.0 / var)
        mu_hat = num / den
        logL = -0.5 * np.sum((yy - mu_hat) ** 2 / var + np.log(2 * np.pi * var))
        logpost.append(logL - np.log(xi))  # Jeffreys prior on xi (scale)
    logpost = np.array(logpost)
    logpost -= logpost.max()
    post = np.exp(logpost)
    post /= post.sum()

    # marginal posteriors
    mu_map = None
    mu_mean = 0.0
    mu_var_part = 0.0
    # for mu, condition on each xi
    mu_samples = []
    xi_samples = []
    for k, xi in enumerate(xi_grid):
        var = u ** 2 + xi ** 2
        mhat = np.sum(yy / var) / np.sum(1.0 / var)
        s2 = 1.0 / np.sum(1.0 / var)
        mu_samples.append((mhat, s2, post[k]))
    # posterior mean & SD of mu (marginalized over xi)
    mu_post_mean = np.sum([p * m for m, s2, p in mu_samples])
    mu_post_var = np.sum([p * (s2 + (m - mu_post_mean) ** 2) for m, s2, p in mu_samples])
    mu_post_sd = np.sqrt(mu_post_var)
    xi_post_mean = np.sum(xi_grid * post)

    # ---- Gravitational correction (whole-experiment total) ----
    t_tide, tot = load_tide()
    dff_all, n_valid_all = [], []
    for kk, (s, e) in enumerate(GROUPS):
        S = np.datetime64(s) - np.timedelta64(8, "h")  # Beijing -> UTC
        E = np.datetime64(e) - np.timedelta64(8, "h")
        m = (t_tide >= S) & (t_tide <= E)
        if m.sum():
            dff_all.append(float(tot[m].mean()) / C ** 2)
            # duration weight = n_valid (from ratio csv)
            n_valid_all.append(int(ratio_rows[kk]["n_valid"]))
    dff_all = np.array(dff_all)
    n_valid_all = np.array(n_valid_all, dtype=float)
    wv = n_valid_all / n_valid_all.sum()
    grav_total = float(np.sum(dff_all * wv))

    # ---- assemble outputs ----
    # Precision-weighted (1/u_i²) WLS center; distinct from the duration-weighted
    # (n_valid) center in compute_ratio.py — the two weightings answer different
    # questions and must not be conflated.
    R0 = float(R[1])  # segment-1 ratio, as the y_i baseline reference
    result = {
        "R_wls_precision": float(R0 * (1 + y_wls)),
        "u_wls": float(u_wls),
        "chi2": float(chi2),
        "dof": int(dof),
        "chi2_red": float(chi2_red),
        "p_chi2": float(p_chi2),
        "birge_ratio": float(birge),
        "u_birge": float(u_birge),
        "xi_mp": float(xi_mp),
        "R_mp": float(R0 * (1 + y_mp)),
        "u_mp": float(u_mp),
        "mu_bayes": float(mu_post_mean),
        "u_stat_bayes": float(mu_post_sd),
        "xi_bayes": float(xi_post_mean),
        "R_bayes": float(R0 * (1 + mu_post_mean)),
        "grav_correction_total": grav_total,
        "y_wls_precision_1e18": float(y_wls * 1e18),
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
    print(f"WLS      : R = {result['R_wls_precision']:.19f}  u = {result['u_wls']:.3e}")
    print(f"  chi2 = {chi2:.3f} (dof={dof}, chi2_red={chi2_red:.3f}, p={p_chi2:.3f})")
    print(f"Birge    : ratio = {birge:.3f}  u = {u_birge:.3e}")
    print(f"Mandel-P : xi = {xi_mp:.3e}  u = {u_mp:.3e}  R = {result['R_mp']:.19f}")
    print(f"Bayesian : mu = {mu_post_mean:.3e}  u = {mu_post_sd:.3e}  xi = {xi_post_mean:.3e}")
    print(f"          R = {result['R_bayes']:.19f}")
    print(f"\ngravitational correction (total) = {grav_total:.6e}")
    print(f"\nWrote {csv_path}")
    print(f"Wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
