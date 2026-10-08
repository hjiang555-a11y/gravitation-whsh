#!/usr/bin/env python3
"""Two-tier numbers pipeline for the rebuilt manuscript (paper/rev2).

Tier 1 -- the frozen, audited analysis layer:
    results/audit-v1/verified/manifest.json                      (schema 1.1)
    results/audit-v1/verified/statistical_methods_tidal_seg9_excluded.json
        (per-segment u_i / status diagnostics, frozen with the verified run)

Tier 2 -- curated constants adopted for the manuscript, each with an explicit
    provenance tag (collaboration values, published literature, or the
    user-confirmed scale of the time-varying-redshift error term).

Outputs (all under paper/rev2/generated/):
    numbers.tex            -- LaTeX macros; every number in the manuscript
    numbers_manifest.json  -- macro -> {value, source} mapping
    numbers.json           -- machine-readable payload for the figure tools
    segment_table.tex      -- per-segment table for the appendix

Usage:
    python tools/build_numbers.py          # regenerate the four outputs
    python tools/build_numbers.py --check  # validate only; writes nothing

Overrides (test hooks): --manifest PATH, --seg9 PATH.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REV2 = TOOLS.parent
ROOT = REV2.parent.parent
GENERATED = REV2 / "generated"

DEFAULT_MANIFEST = ROOT / "results" / "audit-v1" / "verified" / "manifest.json"
DEFAULT_SEG9 = (
    ROOT / "results" / "audit-v1" / "verified"
    / "statistical_methods_tidal_seg9_excluded.json"
)

C_LIGHT = 299792458.0  # m s^-1, exact

# ---------------------------------------------------------------------------
# Tier-2 curated constants: id -> (value, provenance)
# ---------------------------------------------------------------------------
CURATED: dict[str, tuple[str, str]] = {
    "sr_syst_e18": (
        "0.92",
        "curated: USTC Sr1 systematic uncertainty 9.2e-19 (Jia et al. 2026, "
        "Metrologia 63, 025002), adopted as 0.92e-18",
    ),
    "yb_syst_e18": (
        "1.3",
        "curated (user-confirmed): Wuhan Yb lattice-clock published systematic "
        "uncertainty 1.3e-18 (Zhu et al., arXiv:2606.10514); resolves the "
        "internal 1.1e-18 vs published 1.3e-18 conflict in favour of the "
        "published evaluation",
    ),
    "link_e18": (
        "0.1",
        "curated upper bound: experiment-side budget lists the fibre transfer "
        "as < 1e-19 (experiment materials; .omo/drafts/experiment-facts.md); "
        "adopted as 0.1e-18",
    ),
    "comb_e18": (
        "0.1",
        "curated upper bound: experiment-side budget lists the comb transfer "
        "as < 1e-19 (experiment materials; .omo/drafts/experiment-facts.md); "
        "adopted as 0.1e-18",
    ),
    "tidal_e18": (
        "0.5",
        "mandate (user-confirmed 0.5e-18): data-driven scale of the "
        "time-varying redshift term carried as an uncertainty item; consistent "
        "with the frozen 16-segment empirical-scenario centre shift (5.30e-19) "
        "in results/audit-v1/verified/statistical_methods_tidal_seg9_excluded.json",
    ),
    "delta_w": (
        "280.042",
        "curated: levelled geopotential difference 280.042 m^2/s^2 "
        "(experiment-side levelling report); the alternative record "
        "280.049 m^2/s^2 is carried as an external pending item",
    ),
    "delta_w_unc": (
        "0.085",
        "curated: levelling uncertainty +/- 0.085 m^2/s^2 "
        "(experiment-side levelling report)",
    ),
    "ref_nist": (
        "1.2075070393433377230",
        "literature: Aeppli et al. 2026, Phys. Rev. Lett. 137, 033201 "
        "(arXiv:2512.21428)",
    ),
    "ref_nist_u_digits": (
        "37",
        "literature: Aeppli et al. 2026 (as above), quoted uncertainty digits",
    ),
    "ref_eu": (
        "1.207507039343337718",
        "literature: Pizzocaro et al. 2026, Phys. Rev. Research 8, 033250 "
        "(arXiv:2604.27963)",
    ),
    "ref_eu_u_digits": (
        "32",
        "literature: Pizzocaro et al. 2026 (as above), quoted uncertainty digits",
    ),
    "fibre_km": ("1350", "experiment materials (link documentation): single-pass fibre length"),
    "round_trip_km": ("2700", "experiment materials (link documentation): loop-back round-trip length"),
    "site_km": ("700", "experiment materials (link documentation): separation of the two sites"),
    "level_km": ("1113", "experiment-side levelling report: levelling line length"),
    "campaign_days": ("58", "experiment materials: 2026-06-29 to 2026-08-26 campaign span"),
    "n_stages": ("3", "experiment materials: number of measurement stages"),
    "same_campus_best_e18": (
        "3.2",
        "literature: Aeppli et al. 2026 (PRL 137, 033201): best same-campus "
        "(NIST-JILA, 3.6 km link) cross-species ratio uncertainty, as quoted",
    ),
    "same_campus_km": (
        "3.6",
        "literature: Aeppli et al. 2026 (as above): phase-stabilised fibre "
        "link length of the NIST-JILA campus comparison",
    ),
    "eu_best_e18": (
        "7.7",
        "literature: Pizzocaro et al. 2026 (Phys. Rev. Research 8, 033250; "
        "arXiv:2604.27963): best ratio in the European fibre network campaign",
    ),
    "vlbi_km": (
        "9000",
        "literature: Pizzocaro et al. 2021 (Nature Physics 17, 223-227): "
        "VLBI comparison of two optical clocks separated by about 9000 km",
    ),
    "lisdat_km": (
        "1415",
        "literature: Lisdat et al. 2016 (Nature Communications 7, 12443): "
        "Paris-Braunschweig Sr-Sr comparison over 1415 km of telecom fibre",
    ),
    "f_rep_mhz": ("200", "clock/params.json (FREF=1e7, DIV20=20): comb repetition rate, MHz"),
    "f_1550_thz": (
        "193.3992",
        "clock/params.json: N1550_WH x f_rep = 966996 x 200 MHz; the 1550 nm "
        "transfer frequency used to convert the beat to fractional units",
    ),
    "delta_g": (
        "-3.116\\times10^{-15}",
        "clock/params.json DELTA_G = -3.116e-15: static gravitational-redshift "
        "correction applied in the ratio inversion",
    ),
    "ref_threshold": (
        "5\\times10^{-18}",
        "literature: Dimarcq et al. 2024 (Metrologia 61, 012001), mandatory "
        "criterion I.2: required agreement level of frequency-ratio comparisons",
    ),
    "lisdat_u_e17": (
        "5\\times10^{-17}",
        "literature: Lisdat et al. 2016 (Nature Communications 7, 12443): "
        "reported Sr-Sr ratio uncertainty over 1415 km of fibre",
    ),
    "eu_n_clocks": ("7", "literature: Pizzocaro et al. 2026: number of optical clocks in the European fibre-network campaign"),
    "eu_n_institutes": ("4", "literature: Pizzocaro et al. 2026: number of participating institutes"),
    "lindvall_n_clocks": ("10", "literature: Lindvall et al. 2025 (Optica 12, 843): number of optical clocks in coordinated comparisons"),
    "lindvall_n_countries": ("6", "literature: Lindvall et al. 2025: number of countries"),
    "lindvall_n_ratios": ("38", "literature: Lindvall et al. 2025: number of optical frequency ratios reported"),
    "schioppo_km": ("2\\,220", "literature: Schioppo et al. 2022 (Nature Communications 13, 212): metrological fibre link network length"),
    "chen_km": ("2\\,067", "literature: Chen et al. 2026 (Light: Science & Applications 15, 276): field-deployed fibre link length"),
    "claim_date": ("October 2026", "the claim date of the first-report statement; user-confirmed timing"),
}

# Measurement-stage assignment by recorded segment group (experiment materials).
STAGES: dict[int, int] = {
    **{g: 1 for g in range(1, 9)},
    **{g: 2 for g in range(9, 15)},
    **{g: 3 for g in range(15, 18)},
}


def _load(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _chunks(text: str, from_right: bool) -> list[str]:
    out: list[str] = []
    if from_right:
        while len(text) > 3:
            out.insert(0, text[-3:])
            text = text[:-3]
        if text:
            out.insert(0, text)
    else:
        while len(text) > 3:
            out.append(text[:3])
            text = text[3:]
        if text:
            out.append(text)
    return out


def latex_groups(num_str: str) -> str:
    """Digit-group a decimal string with LaTeX thin spaces (1.207\\,507\\,...)."""
    sign = ""
    text = num_str
    if text.startswith("-"):
        sign, text = "-", text[1:]
    if "." in text:
        int_part, frac = text.split(".")
        return sign + r"\,".join(_chunks(int_part, True)) + "." + r"\,".join(_chunks(frac, False))
    return sign + r"\,".join(_chunks(text, True))


def round_str(x: str, places: int) -> str:
    q = Decimal(1).scaleb(-places)
    return str(Decimal(x).quantize(q, rounding=ROUND_HALF_EVEN))


def sci_latex(value: float) -> str:
    mant, exp = f"{value:.1e}".split("e")
    return rf"{mant}\times10^{{{int(exp)}}}"


def build(macros: list[tuple[str, str, str]]) -> dict:
    """Compute the full macro table, payload and per-segment rows."""
    manifest = _load(MANIFEST_PATH)
    seg9 = _load(SEG9_PATH)

    primary = manifest["primary_16"]
    sensitivity = manifest["sensitivity_17"]
    comb = primary["combination"]

    def add(name: str, value: str, source: str) -> None:
        macros.append((name, value, source))

    tier1 = "manifest:primary_16.combination"
    add("Rheadline", latex_groups(round_str(comb["R_bayes"], 19)),
        f"{tier1}.R_bayes rounded to 19 decimals")
    add("RbayesFull", comb["R_bayes"], f"{tier1}.R_bayes (full precision)")
    add("RwlsFull", comb["R_wls"], f"{tier1}.R_wls (full precision)")
    add("RmpFull", comb["R_mp"], f"{tier1}.R_mp (full precision)")
    add("RwlsHead", latex_groups(round_str(comb["R_wls"], 19)),
        f"{tier1}.R_wls rounded to 19 decimals")
    add("RmpHead", latex_groups(round_str(comb["R_mp"], 19)),
        f"{tier1}.R_mp rounded to 19 decimals")

    u_stat_e18 = comb["u_stat_bayes"] * 1e18
    add("uStatE", f"{u_stat_e18:.3f}", f"{tier1}.u_stat_bayes")
    add("uStatShort", f"{u_stat_e18:.2f}", f"{tier1}.u_stat_bayes (2 significant figures)")
    add("uWlsE", f"{comb['u_wls'] * 1e18:.3f}", f"{tier1}.u_wls")
    add("uMpE", f"{comb['u_mp'] * 1e18:.3f}", f"{tier1}.u_mp")
    add("uBirgeE", f"{comb['u_birge'] * 1e18:.3f}", f"{tier1}.u_birge")
    add("chiSq", f"{comb['chi2']:.2f}", f"{tier1}.chi2")
    add("chiRed", f"{comb['chi2_red']:.3f}", f"{tier1}.chi2_red")
    add("dofV", str(int(comb["dof"])), f"{tier1}.dof")
    add("pChi", sci_latex(comb["p_chi2"]), f"{tier1}.p_chi2")
    add("birgeRatio", f"{comb['birge_ratio']:.3f}", f"{tier1}.birge_ratio")
    add("xiMpE", f"{comb['xi_mp'] * 1e18:.2f}", f"{tier1}.xi_mp")
    add("xiBayesE", f"{comb['xi_bayes'] * 1e18:.2f}", f"{tier1}.xi_bayes")
    add("muBayesE", f"{comb['mu_bayes'] * 1e18:.3f}", f"{tier1}.mu_bayes")

    add("nSeg", str(len(primary["included_groups"])), "manifest:primary_16.included_groups")
    add("nSegAll", str(len(sensitivity["included_groups"])), "manifest:sensitivity_17.included_groups")
    add("nSamples", latex_groups(str(primary["total_samples"])), "manifest:primary_16.total_samples")
    add("nSamplesAll", latex_groups(str(sensitivity["total_samples"])), "manifest:sensitivity_17.total_samples")
    add("nHours", str(round(primary["total_samples"] / 3600)), "derived: total_samples / 3600")
    add("nHoursAll", str(round(sensitivity["total_samples"] / 3600)), "derived: sensitivity total_samples / 3600")

    limited = [
        g for g, status in zip(primary["included_groups"], primary["segment_statuses"])
        if status != "established"
    ]
    add("nModelLimited", str(len(limited)),
        "manifest:primary_16.segment_statuses (non-established)")
    add("modelLimitedGroups", r",\ ".join(str(g) for g in limited),
        "manifest:primary_16 (groups with non-established fit status)")

    # Curated constants.
    add("uSrE", CURATED["sr_syst_e18"][0], CURATED["sr_syst_e18"][1])
    add("uYbE", CURATED["yb_syst_e18"][0], CURATED["yb_syst_e18"][1])
    add("uLinkE", CURATED["link_e18"][0], CURATED["link_e18"][1])
    add("uCombE", CURATED["comb_e18"][0], CURATED["comb_e18"][1])
    add("uTidalE", CURATED["tidal_e18"][0], CURATED["tidal_e18"][1])
    add("dWVal", CURATED["delta_w"][0], CURATED["delta_w"][1])
    add("dWUnc", CURATED["delta_w_unc"][0], CURATED["delta_w_unc"][1])
    add("refNistV", latex_groups(CURATED["ref_nist"][0]), CURATED["ref_nist"][1])
    add("refNistU", CURATED["ref_nist_u_digits"][0], CURATED["ref_nist_u_digits"][1])
    add("refEuV", latex_groups(CURATED["ref_eu"][0]), CURATED["ref_eu"][1])
    add("refEuU", CURATED["ref_eu_u_digits"][0], CURATED["ref_eu_u_digits"][1])
    add("fibreKm", latex_groups(CURATED["fibre_km"][0]), CURATED["fibre_km"][1])
    add("roundKm", latex_groups(CURATED["round_trip_km"][0]), CURATED["round_trip_km"][1])
    add("siteKm", latex_groups(CURATED["site_km"][0]), CURATED["site_km"][1])
    add("levelKm", latex_groups(CURATED["level_km"][0]), CURATED["level_km"][1])
    add("nDays", CURATED["campaign_days"][0], CURATED["campaign_days"][1])
    add("nStages", CURATED["n_stages"][0], CURATED["n_stages"][1])
    add("refSameCampusU", CURATED["same_campus_best_e18"][0] + r"\times10^{-18}",
        CURATED["same_campus_best_e18"][1])
    add("refSameCampusKm", CURATED["same_campus_km"][0], CURATED["same_campus_km"][1])
    add("refEuBestU", CURATED["eu_best_e18"][0] + r"\times10^{-18}",
        CURATED["eu_best_e18"][1])
    add("refVlbiKm", latex_groups(CURATED["vlbi_km"][0]), CURATED["vlbi_km"][1])
    add("refLisdatKm", latex_groups(CURATED["lisdat_km"][0]), CURATED["lisdat_km"][1])
    add("fRepMHz", CURATED["f_rep_mhz"][0], CURATED["f_rep_mhz"][1])
    add("fFifteenTHz", CURATED["f_1550_thz"][0], CURATED["f_1550_thz"][1])
    add("deltaGV", CURATED["delta_g"][0], CURATED["delta_g"][1])
    add("refThreshold", CURATED["ref_threshold"][0], CURATED["ref_threshold"][1])
    add("refLisdatU", CURATED["lisdat_u_e17"][0], CURATED["lisdat_u_e17"][1])
    add("euNClocks", CURATED["eu_n_clocks"][0], CURATED["eu_n_clocks"][1])
    add("euNInstitutes", CURATED["eu_n_institutes"][0], CURATED["eu_n_institutes"][1])
    add("lindvallNClocks", CURATED["lindvall_n_clocks"][0], CURATED["lindvall_n_clocks"][1])
    add("lindvallNCountries", CURATED["lindvall_n_countries"][0], CURATED["lindvall_n_countries"][1])
    add("lindvallNRatios", CURATED["lindvall_n_ratios"][0], CURATED["lindvall_n_ratios"][1])
    add("schioppoKm", CURATED["schioppo_km"][0], CURATED["schioppo_km"][1])
    add("chenKm", CURATED["chen_km"][0], CURATED["chen_km"][1])
    add("claimDate", CURATED["claim_date"][0], CURATED["claim_date"][1])

    # Derived: static-potential uncertainty from the levelled dW uncertainty.
    u_static_e18 = float(CURATED["delta_w_unc"][0]) / C_LIGHT**2 * 1e18
    add("uStaticE", f"{u_static_e18:.3f}",
        "derived: curated delta_w_unc / c^2")

    # Derived: total standard uncertainty (quadrature of the budget).
    budget_values = {
        "statistical": u_stat_e18,
        "sr": float(CURATED["sr_syst_e18"][0]),
        "yb": float(CURATED["yb_syst_e18"][0]),
        "static": u_static_e18,
        "link": float(CURATED["link_e18"][0]),
        "comb": float(CURATED["comb_e18"][0]),
        "tidal": float(CURATED["tidal_e18"][0]),
    }
    u_total_e18 = math.sqrt(sum(v * v for v in budget_values.values()))
    add("uTotalE", f"{u_total_e18:.2f}",
        "derived: quadrature of the budget components (this pipeline)")
    add("uTotalShort", f"{u_total_e18:.1f}",
        "derived: quadrature of the budget components, 2 significant figures")

    unc_digits = f"{u_total_e18:.1f}".replace(".", "")
    add("RheadlineUnc", unc_digits,
        "derived: total standard uncertainty to two significant figures")

    # Derived: differences from the reference values.
    r_bayes = Decimal(comb["R_bayes"])
    d_nist = float((r_bayes - Decimal(CURATED["ref_nist"][0])) * Decimal("1e18"))
    d_eu = float((r_bayes - Decimal(CURATED["ref_eu"][0])) * Decimal("1e18"))
    add("dVsNistE", f"{d_nist:+.2f}" + r"\times10^{-18}",
        "derived: R_bayes minus the NIST-JILA reference, in 1e-18")
    add("dVsEuE", f"{d_eu:+.2f}" + r"\times10^{-18}",
        "derived: R_bayes minus the European-network reference, in 1e-18")

    # Per-segment cross-check: manifest segment_ratios vs frozen seg9 JSON.
    groups = list(primary["included_groups"])
    ratios = [Decimal(s) for s in primary["segment_ratios"]]
    nvals = list(primary["segment_n_valid"])
    statuses = list(primary["segment_statuses"])
    base = ratios[0]
    seg_rows = {row["group"]: row for row in seg9["scenarios"]["raw"]["per_segment"]}
    if set(seg_rows) != set(groups):
        raise SystemExit("ERROR: frozen seg9 JSON groups do not match the manifest membership")

    segments = []
    max_diff = 0.0
    for group, ratio, n_valid, status in zip(groups, ratios, nvals, statuses):
        y_manifest = float((ratio / base - Decimal(1)) * Decimal("1e18"))
        row = seg_rows[group]
        max_diff = max(max_diff, abs(y_manifest - float(row["y_i_1e18"])))
        segments.append({
            "group": group,
            "stage": STAGES.get(group, 0),
            "y_i_1e18": y_manifest,
            "u_frac_1e18": float(row["u_frac"]) * 1e18,
            "n_valid": int(n_valid),
            "status": status,
        })

    payload = {
        "headline": {
            "R_full": comb["R_bayes"],
            "R_19dp": round_str(comb["R_bayes"], 19),
            "unc_digits": unc_digits,
            "u_total_e18": u_total_e18,
            "u_stat_e18": u_stat_e18,
        },
        "segments": segments,
        "budget": [
            {"name": "Statistical", "e18": u_stat_e18, "source": f"{tier1}.u_stat_bayes"},
            {"name": "Sr systematics", "e18": budget_values["sr"], "source": "curated:sr_syst_e18"},
            {"name": "Yb systematics", "e18": budget_values["yb"], "source": "curated:yb_syst_e18"},
            {"name": "Static potential", "e18": u_static_e18, "source": "derived:curated delta_w_unc / c^2"},
            {"name": "Fibre link", "e18": budget_values["link"], "source": "curated:link_e18"},
            {"name": "Frequency comb", "e18": budget_values["comb"], "source": "curated:comb_e18"},
            {"name": "Time-varying redshift", "e18": budget_values["tidal"], "source": "curated:tidal_e18"},
        ],
        "comparisons": [
            {"name": "This work", "delta_e18": 0.0, "u_e18": u_total_e18},
            {"name": "NIST-JILA", "delta_e18": d_nist, "u_e18": float(CURATED["ref_nist_u_digits"][0]) / 10.0},
            {"name": "European network", "delta_e18": d_eu, "u_e18": float(CURATED["ref_eu_u_digits"][0]) / 10.0},
        ],
        "meta": {
            "n_segments": len(groups),
            "n_segments_all": len(sensitivity["included_groups"]),
            "model_limited_groups": limited,
            "max_manifest_vs_frozen_y_diff_e18": max_diff,
        },
    }
    return payload


def render_tex(macros: list[tuple[str, str, str]]) -> str:
    lines = [
        "% Generated by tools/build_numbers.py -- do not edit by hand.",
        "% Provenance for every macro: generated/numbers_manifest.json.",
        "",
    ]
    for name, value, _ in macros:
        lines.append(rf"\newcommand{{\{name}}}{{\ensuremath{{{value}}}}}")
    return "\n".join(lines) + "\n"


def render_segment_table(segments: list[dict]) -> str:
    lines = [
        "% Generated by tools/build_numbers.py -- do not edit by hand.",
        r"\begin{tabular}{rrrrl}",
        r"\toprule",
        r"Group & $n_{\rm valid}$ & $y_i$ ($10^{-18}$) & $u_i$ ($10^{-18}$) & Fit \\",
        r"\midrule",
    ]
    for seg in segments:
        fit = "est." if seg["status"] == "established" else "lim."
        lines.append(
            f"{seg['group']} & {seg['n_valid']:,} & {seg['y_i_1e18']:+.2f} & "
            f"{seg['u_frac_1e18']:.3f} & {fit} \\\\".replace(",", r"\,")
        )
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    return "\n".join(lines)


def run_checks(
    macros: list[tuple[str, str, str]],
    payload: dict,
    *,
    compare_existing: bool,
) -> list[str]:
    errs: list[str] = []
    names = [name for name, _, _ in macros]
    if len(set(names)) != len(names):
        errs.append("duplicate macro names")
    for name, value, source in macros:
        if not value:
            errs.append(f"macro {name}: empty value")
        if not source:
            errs.append(f"macro {name}: missing source")
    meta = payload["meta"]
    if meta["n_segments"] != 16:
        errs.append(f"primary membership has {meta['n_segments']} segments, expected 16")
    if meta["n_segments_all"] != 17:
        errs.append(f"sensitivity membership has {meta['n_segments_all']} segments, expected 17")
    if 9 in {seg["group"] for seg in payload["segments"]}:
        errs.append("segment 9 must not be in the primary membership")
    if meta["max_manifest_vs_frozen_y_diff_e18"] > 1e-6:
        errs.append(
            "manifest segment ratios disagree with the frozen per-segment y_i "
            f"by {meta['max_manifest_vs_frozen_y_diff_e18']:.3e}"
        )
    if not 2.0 <= payload["headline"]["u_total_e18"] <= 2.3:
        errs.append("total standard uncertainty outside the reviewed range")
    if compare_existing and NUMBERS_TEX.exists():
        present = set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", NUMBERS_TEX.read_text(encoding="utf-8")))
        expected = set(names)
        if present != expected:
            errs.append(
                "numbers.tex macro set differs from the pipeline: "
                f"missing={sorted(expected - present)} extra={sorted(present - expected)}"
            )
    return errs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate only; write nothing")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="frozen manifest path (test hook)")
    parser.add_argument("--seg9", type=Path, default=DEFAULT_SEG9, help="frozen seg9 JSON path (test hook)")
    args = parser.parse_args()

    global MANIFEST_PATH, SEG9_PATH, NUMBERS_TEX
    MANIFEST_PATH, SEG9_PATH = args.manifest, args.seg9
    NUMBERS_TEX = GENERATED / "numbers.tex"

    for path, label in ((MANIFEST_PATH, "frozen manifest"), (SEG9_PATH, "frozen seg9 JSON")):
        if not path.is_file():
            print(f"ERROR: {label} not found at {path}; run the audit pipeline first", file=sys.stderr)
            return 1

    macros: list[tuple[str, str, str]] = []
    payload = build(macros)
    # Structural checks first; the numbers.tex comparison runs after the write
    # (build mode) or against the existing file (check mode).
    errs = run_checks(macros, payload, compare_existing=False)
    if errs:
        for err in errs:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    if args.check:
        errs = run_checks(macros, payload, compare_existing=True)
        if errs:
            for err in errs:
                print(f"ERROR: {err}", file=sys.stderr)
            return 1
        print(
            f"OK: {len(macros)} macros (all sourced); "
            f"u_total={payload['headline']['u_total_e18']:.3f}e-18; "
            f"max |manifest-frozen y| diff="
            f"{payload['meta']['max_manifest_vs_frozen_y_diff_e18']:.2e} (e-18 units)"
        )
        return 0

    GENERATED.mkdir(parents=True, exist_ok=True)
    NUMBERS_TEX.write_text(render_tex(macros), encoding="utf-8")
    manifest_map = {
        "generated_by": "paper/rev2/tools/build_numbers.py",
        "macros": {name: {"value": value, "source": source} for name, value, source in macros},
    }
    (GENERATED / "numbers_manifest.json").write_text(
        json.dumps(manifest_map, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (GENERATED / "numbers.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (GENERATED / "segment_table.tex").write_text(
        render_segment_table(payload["segments"]), encoding="utf-8")
    print(
        f"Wrote {len(macros)} macros to {NUMBERS_TEX}, numbers_manifest.json, "
        f"numbers.json, segment_table.tex"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
