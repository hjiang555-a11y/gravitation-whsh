#!/usr/bin/env python3
"""FULLY INDEPENDENT segment-9-excluded clock-ratio / tidal correlation.

Unlike `correlation_reanalysis_seg9_excluded.py` (which drops row 9 from the
already-computed `ratio_17seg.csv`), this script re-runs the ENTIRE ratio
pipeline from the raw beat files: re-selects each segment's longest valid span,
applies the endpoint screen, computes mean_dm, and inverts the full Dr formula in
Decimal80 — exactly mirroring `compute_ratio.py` — then correlates the resulting
per-segment y_i against the session tidal shift, with segment 9 removed.

Nothing existing is read as a shortcut and nothing existing is written: the
17-segment products (`ratio_17seg.csv`, `correlation_reanalysis.csv`, ...) are
untouched. This is an independent cross-check of the "drop segment 9" result.

Outputs (new, separate):
  correlation_reanalysis_seg9_independent.csv
  correlation_reanalysis_seg9_independent.json
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal, getcontext
from pathlib import Path

import numpy as np
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock.shared import (  # noqa: E402
    COEF1156, DELTA_G, DIV20, EXCLUDE_RANGES, FREF, GROUPS,
    JUMP_THRESHOLD, N1156, N1397, N1550, N1550_WH, SHIFT_A,
    D_7_25, D_1_25, load_beat, longest_valid_span, to_dec,
)
from clock_ratio.compute_ratio import endpoint_screen, full_ratio  # noqa: E402

getcontext().prec = 80
OUT_DIR = Path(__file__).resolve().parent
EXCLUDED_GROUP = 9


def recompute_ratios() -> list[dict]:
    """Re-derive per-segment R_i from raw beat, mirroring compute_ratio.main."""
    T, B = load_beat()
    excl = np.zeros(len(T), dtype=bool)
    for s, e in EXCLUDE_RANGES:
        excl |= (T >= np.datetime64(s)) & (T <= np.datetime64(e))
    clean = B.copy()
    clean[excl] = np.nan
    pl = (clean > 3e7) & (clean < 4e7)
    m = float(np.nanmedian(clean[pl]))
    m_dec = to_dec(m)

    rows: list[dict] = []
    for kk, (s, e) in enumerate(GROUPS):
        S, E = np.datetime64(s), np.datetime64(e)
        in_win = (T >= S) & (T < E)
        t_seg, b_seg, ex_seg = T[in_win], B[in_win], excl[in_win]
        plausible = (b_seg > 3e7) & (b_seg < 4e7) & ~ex_seg
        if not plausible.any():
            continue
        med = float(np.median(b_seg[plausible]))
        valid = plausible & (np.abs(b_seg - med) < JUMP_THRESHOLD)
        span = longest_valid_span(valid)
        if span is None:
            continue
        d_long = b_seg[span[0]: span[1] + 1]
        d_long, rem_start, rem_end = endpoint_screen(d_long)
        if len(d_long) == 0:
            continue
        shift_dec = to_dec(SHIFT_A[kk])
        mean_dm_dec = to_dec(d_long.mean()) - m_dec
        R = full_ratio(mean_dm_dec, shift_dec, m_dec)
        rows.append({
            "group": kk + 1,
            "n_valid": len(d_long),
            "t_start": str(t_seg[span[0]]),
            "t_end": str(t_seg[span[1]]),
            "R": R,
        })
    return rows


def load_tide() -> dict[int, float]:
    t = list(csv.DictReader(open(OUT_DIR.parent / "clock" / "clock_tidal_shift.csv")))
    return {int(x["session"]): float(x["frequency_shift_dff"]) * 1e18 for x in t}


def weighted_mean(x, w):
    return float(np.sum(w * x) / np.sum(w))


def main() -> int:
    rows = recompute_ratios()
    if len(rows) != 17:
        raise SystemExit(f"expected 17 segments from raw beat, got {len(rows)}")
    dff_map = load_tide()

    R_ref = rows[0]["R"]                       # segment-1 baseline (as compute_ratio)
    for r in rows:
        r["y_i"] = float((r["R"] / R_ref - Decimal(1)) * Decimal("1e18"))
        r["dff"] = dff_map[r["group"]]

    keep = [r for r in rows if r["group"] != EXCLUDED_GROUP]
    y = np.array([r["y_i"] for r in keep])
    dff = np.array([r["dff"] for r in keep])
    n = np.array([r["n_valid"] for r in keep])
    w = n / n.sum()

    r_eq, p_eq = stats.pearsonr(y, dff)
    rho, p_rho = stats.spearmanr(y, dff)
    slope, intercept, _rv, _pv, _se = stats.linregress(dff, y)
    mean_y_w = weighted_mean(y, w)
    mean_dff_w = weighted_mean(dff, w)

    # cross-check the raw re-derivation against the stored 17-segment ratios
    stored = {int(x["group"]): Decimal(x["YbSr_R"])
              for x in csv.DictReader(open(OUT_DIR / "ratio_17seg.csv"))}
    max_rel = max(abs(float(r["R"] / stored[r["group"]] - 1)) for r in rows)

    result = {
        "excluded_group": EXCLUDED_GROUP,
        "n_segments": len(keep),
        "method": "fully independent: ratios re-derived from raw beat via compute_ratio pipeline",
        "pearson_r": r_eq,
        "pearson_p": p_eq,
        "spearman_rho": rho,
        "spearman_p": p_rho,
        "ols_slope": slope,
        "ols_intercept": intercept,
        "weighted_mean_yi_1e18": mean_y_w,
        "weighted_mean_dff_1e18": mean_dff_w,
        "raw_rederivation_max_rel_diff_vs_ratio_17seg": max_rel,
        "per_segment": [{"group": r["group"], "n_valid": r["n_valid"],
                         "y_i_1e18": r["y_i"], "dff_1e18": r["dff"],
                         "R": str(r["R"])} for r in rows],
    }

    (OUT_DIR / "correlation_reanalysis_seg9_independent.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8")
    with (OUT_DIR / "correlation_reanalysis_seg9_independent.csv").open("w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["metric", "value"])
        for k in ("excluded_group", "n_segments", "pearson_r", "pearson_p",
                  "spearman_rho", "spearman_p", "ols_slope", "ols_intercept",
                  "weighted_mean_yi_1e18", "weighted_mean_dff_1e18",
                  "raw_rederivation_max_rel_diff_vs_ratio_17seg"):
            wr.writerow([k, result[k]])

    print(f"=== fully independent, segment {EXCLUDED_GROUP} excluded ({len(keep)} segments) ===")
    print(f"Raw re-derivation vs ratio_17seg.csv: max rel diff = {max_rel:.2e}")
    print(f"Pearson  r = {r_eq:+.4f}  p = {p_eq:.4f}")
    print(f"Spearman ρ = {rho:+.4f}  p = {p_rho:.4f}")
    print(f"y_i weighted mean = {mean_y_w:+.5f} ×1e-18")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
