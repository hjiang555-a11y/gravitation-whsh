#!/usr/bin/env python3
"""Segment-9 exclusion sensitivity check for the tidal-corrected statistical
methods — an ADDITIVE result that does NOT replace or modify any existing
output.

Segment 9 is flagged anomalous (METHODOLOGY §8.2/§8.3): its Sr systematic
shift `shift_a = -8.13e-17` sits between the 7-month value (~-1.72e-16) and the
8-month value (~+7.9e-18), and its source comment asks whether that is real or a
placeholder, making y_9 ~ +6.4e-18 (raw) an outlier. This script answers "what
do the combined values and the tidal-correction story become if segment 9 is
dropped", by re-reducing the ALREADY-COMPUTED per-segment (y_i, u_i) stored in
`statistical_methods_tidal.json`. It never re-runs tidal_correction.py or
statistical_methods.py and never rewrites their artifacts.

Outputs (new, separate):
  statistical_methods_tidal_seg9_excluded.json
"""
from __future__ import annotations

import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock_ratio.statistical_methods_tidal import (  # noqa: E402
    AnalysisError, build_synthesis, combine,
)

OUT_DIR = Path(__file__).resolve().parent
SOURCE_JSON = OUT_DIR / "statistical_methods_tidal.json"
JSON_PATH = OUT_DIR / "statistical_methods_tidal_seg9_excluded.json"
EXCLUDED_GROUP = 9


def scenario_result_from_rows(scenario: dict, rows: list[dict]) -> dict:
    """Re-combine preset per-segment (y_i, u_i) rows for one scenario, keeping
    the same segment-1 baseline and the same Decimal reconstruction path as
    statistical_methods_tidal.scenario_result."""
    import numpy as np
    u = np.array([r["u_i"] for r in rows])
    yy = np.array([r["y_i_1e18"] for r in rows]) * 1e-18
    comb = combine(yy, u)
    with localcontext() as ctx:
        ctx.prec = 80
        R0 = Decimal(scenario["R_seg1"])
        y_wls_d = Decimal(repr(comb["y_wls"]))
        y_mp_d = Decimal(repr(comb["y_mp"]))
        mu_d = Decimal(repr(comb["mu_bayes"]))
        return {
            "coefficient": scenario["coefficient"],
            "R_seg1": scenario["R_seg1"],
            "n_segments": len(rows),
            "excluded_group": EXCLUDED_GROUP,
            "R_wls": str(R0 * (Decimal(1) + y_wls_d)),
            "R_mp": str(R0 * (Decimal(1) + y_mp_d)),
            "R_bayes": str(R0 * (Decimal(1) + mu_d)),
            "y_wls_precision_1e18": comb["y_wls"] * 1e18,
            **{k: comb[k] for k in ("u_wls", "chi2", "dof", "chi2_red", "p_chi2",
                                    "birge_ratio", "u_birge", "xi_mp", "u_mp",
                                    "mu_bayes", "u_stat_bayes", "xi_bayes")},
            "per_segment": rows,
        }


def main() -> int:
    try:
        source = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise AnalysisError(f"cannot read {SOURCE_JSON.name}: {error}") from error

    scenarios = source["scenarios"]
    reduced: dict[str, dict] = {}
    for key, scenario in scenarios.items():
        rows = [r for r in scenario["per_segment"] if r["group"] != EXCLUDED_GROUP]
        if len(rows) != len(scenario["per_segment"]) - 1:
            raise AnalysisError(f"{key}: segment {EXCLUDED_GROUP} not present exactly once")
        reduced[key] = scenario_result_from_rows(scenario, rows)

    document = {
        "scenarios": reduced,
        "synthesis": build_synthesis(reduced),
        "metadata": {
            "decimal_precision": 80,
            "source": SOURCE_JSON.name,
            "excluded_group": EXCLUDED_GROUP,
            "exclusion_reason": "segment 9 shift_a anomalous (-8.13e-17 between the 7-month ~-1.72e-16 and 8-month ~+7.9e-18), y_9 a raw outlier; see METHODOLOGY §8",
            "method": "re-combined the existing per-segment (y_i, u_i); no re-selection, no re-correction",
            "baseline": "R_seg1 from the same scenario as in statistical_methods_tidal.json",
            "note": "ADDITIVE sensitivity check; does not replace the 17-segment results",
        },
    }
    JSON_PATH.write_text(json.dumps(document, indent=2, allow_nan=False), encoding="utf-8")
    print(f"Wrote {JSON_PATH}")
    for key, sc in reduced.items():
        print(f"\n[{key}] A={sc['coefficient']}  (n={sc['n_segments']}, seg{EXCLUDED_GROUP} dropped)")
        print(f"  WLS   R={sc['R_wls'][:26]}  u={sc['u_wls']:.3e}  chi2_red={sc['chi2_red']:.3f}")
        print(f"  M-P   R={sc['R_mp'][:26]}  xi={sc['xi_mp']:.3e}")
        print(f"  Bayes R={sc['R_bayes'][:26]}  xi={sc['xi_bayes']:.3e}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AnalysisError as e:
        print(f"Error: {e}", file=sys.stderr)
        raise SystemExit(1)
