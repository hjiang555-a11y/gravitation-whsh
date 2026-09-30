#!/usr/bin/env python3
"""Spliced concatenated stability for both compensation signs.

The 17 valid segments are SPLICED end-to-end with their inter-segment gaps
removed, giving one continuous 1,008,912-sample record. A single standard
overlapping Allan deviation then runs on that record, so tau can reach the
full spliced length instead of being capped by the longest single run.

  1. select_segments -> the 17 frozen segments (raw data alone decide
     membership, identical to every other artifact).
  2. Build the per-second ratio fluctuation series y(t) = -q/(1+q) for each
     scenario via analyze_segment. analyse_segment applies
     b_corr = b_raw - coefficient*h, so the coefficient sign selects the
     compensation direction:
       raw            A=0      (no correction)
       theory         A=-1     (full-amplitude correction)
       empirical      A=-0.54  (fitted-amplitude correction)
       pos_theory     A=+1     (full-amplitude, OPPOSITE sign)
       pos_empirical  A=+0.54  (fitted-amplitude, OPPOSITE sign)
       correction     the removed term itself, h/F_1550
  3. SPLICE: concatenate the 17 segment series back-to-back, dropping the
     wall-clock gaps entirely (t = 0,1,2,... over the spliced record).
  4. Run one OADEV on the spliced record for every series.

The pos_* series exist to show that the opposite compensation direction
leaves MORE scatter, i.e. the chosen (negative) sign is the one that
removes the tide.

Because the gaps are removed, the spliced record is treated as if the
segments were contiguous; a tau longer than one raw segment is now
computable but mixes different campaigns. n_pairs is reported so the record
length behind each point is explicit.

Independent result set; modifies no existing artifact.
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared as s  # noqa: E402
from clock_ratio.tidal_analysis import (  # noqa: E402
    SCENARIOS, AnalysisError, Scenario, TideGrid, analyze_segment, select_segments,
)

OUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUT_DIR / "concatenated_stability_long.csv"
MD_PATH = OUT_DIR / "concatenated_stability_long.md"
FIG_PNG = OUT_DIR / "concatenated_stability_long.png"
FIG_PDF = OUT_DIR / "concatenated_stability_long.pdf"

TAU_START_S = 100
TAUS_S = (128, 256, 512, 600, 1024, 1200, 2048,
          3600, 4096, 7200, 8192, 16384, 21600, 32768, 43200, 65536, 86400,
          100000, 131072, 172800, 200000, 262144, 345600, 400000)


def aligned_axis(segment_times: list[np.ndarray]) -> np.ndarray:
    """Place each segment end-to-end on one continuous 1-s clock.

    Starts at the first segment's timestamp and appends each segment back-to-back
    so the gaps between real segments are removed. Every step is exactly 1 s, so
    tau on this axis is pure data time, not wall-clock time.
    """
    origin = segment_times[0][0]
    blocks, offset = [], 0
    for times in segment_times:
        blocks.append(origin + np.timedelta64(offset, "s")
                      + np.arange(len(times)) * np.timedelta64(1, "s"))
        offset += len(times)
    return np.concatenate(blocks)


def spliced_oadev(y: np.ndarray, taus_s) -> list[dict]:
    """Overlapping Allan deviation on one continuous spliced record.

    The record has no gaps (t = 0,1,...,N-1). For lag m (tau = m seconds),
    every start i=0..N-2m contributes an adjacent m-averaged difference.

    The 1-sigma uncertainty on sigma_y uses the chi-square estimate with
    equivalent degrees of freedom for overlapping Allan deviation
    (Riley & Howe):  Edf = (3*(N-1)/(2*m) - 1) * (2/3), clipped to >= 1;
    u_sigma = sigma_y / sqrt(2 * Edf).
    """
    n = len(y)
    centered = y - y[0]
    centered = centered - centered.mean()
    prefix = np.concatenate(([0.0], np.cumsum(centered)))
    points = []
    for tau in taus_s:
        m = int(tau)
        n_pairs = n - 2 * m
        if n_pairs <= 0:
            points.append({"tau_s": m, "n_pairs": 0, "sigma_y": None, "u_sigma": None})
            continue
        difference = (prefix[2 * m:] - 2 * prefix[m:-m] + prefix[:-2 * m]) / m
        sigma = float(np.sqrt(np.dot(difference, difference) / (2.0 * n_pairs)))
        edf = max(1.0, (3.0 * (n - 1) / (2.0 * m) - 1.0) * (2.0 / 3.0))
        u_sigma = sigma / np.sqrt(2.0 * edf)
        points.append({"tau_s": m, "n_pairs": int(n_pairs), "sigma_y": sigma,
                       "u_sigma": float(u_sigma)})
    return points


def main() -> int:
    try:
        times, beat = s.load_beat()
    except (OSError, ValueError) as error:
        raise AnalysisError(f"raw beat data could not be loaded: {error}") from error
    segments = select_segments(times, beat)
    try:
        tide = TideGrid(*s.load_tide())
    except (OSError, ValueError, KeyError) as error:
        raise AnalysisError(f"tide data could not be loaded: {error}") from error

    scenario_by_key = {sc.key: sc for sc in SCENARIOS}
    opposite = {
        "pos_theory": Scenario("pos_theory", Decimal("1")),
        "pos_empirical": Scenario("pos_empirical", Decimal("0.54")),
    }
    results: dict[str, list] = {k: [] for k in
                                ("raw", "theory", "empirical", "pos_theory",
                                 "pos_empirical")}
    for segment in segments:
        h = tide.beat_at(segment.times)
        results["raw"].append(analyze_segment(segment, h, scenario_by_key["raw"]))
        results["theory"].append(analyze_segment(segment, h, scenario_by_key["theory"]))
        results["empirical"].append(analyze_segment(segment, h, scenario_by_key["empirical"]))
        results["pos_theory"].append(analyze_segment(segment, h, opposite["pos_theory"]))
        results["pos_empirical"].append(analyze_segment(segment, h, opposite["pos_empirical"]))

    segment_times = [r.segment.times for r in results["raw"]]
    aligned_times = aligned_axis(segment_times)
    span_days = float((segment_times[-1][-1] - segment_times[0][0])
                      / np.timedelta64(1, "D"))
    h_frac_all = np.concatenate([tide.beat_at(seg.times) / s.F_1550 for seg in segments])
    series = {
        key: np.concatenate([r.fluctuations for r in results[key]])
        for key in ("raw", "theory", "empirical", "pos_theory", "pos_empirical")
    }
    series["correction"] = h_frac_all
    n_total = len(series["raw"])
    if not np.all(np.diff(aligned_times) == np.timedelta64(1, "s")):
        raise AnalysisError("aligned axis is not a monotone 1-second clock")
    taus = [t for t in TAUS_S if TAU_START_S <= t < n_total // 2]
    curves = {key: spliced_oadev(series[key], taus) for key in series}

    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["series", "tau_s", "tau_days", "n_pairs", "sigma_y", "u_sigma"])
        for key in ("raw", "theory", "empirical", "pos_theory", "pos_empirical",
                    "correction"):
            for point in curves[key]:
                writer.writerow([
                    key, point["tau_s"], f"{point['tau_s'] / 86400:.6f}",
                    point["n_pairs"],
                    "" if point["sigma_y"] is None else f"{point['sigma_y']:.6e}",
                    "" if point["u_sigma"] is None else f"{point['u_sigma']:.6e}",
                ])

    lines = [
        "# Spliced concatenated stability (both compensation signs)\n",
        f"17 segments placed end-to-end on one continuous 1-s clock; the "
        f"wall-clock gaps are removed. The aligned record spans "
        f"**{n_total:,}** s ({n_total / 86400:.3f} d of pure data time) versus "
        f"{span_days:.2f} d of real elapsed time. One OADEV per series over the "
        f"aligned axis, starting at tau = {TAU_START_S} s.\n",
        "| tau [s] | tau [d] | raw (A=0) | theory (A=-1) | empirical (A=-0.54) "
        "| pos_theory (A=+1) | pos_empirical (A=+0.54) | correction h/F1550 "
        "| n_pairs |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, tau in enumerate(taus):
        p_raw, p_th, p_em = curves["raw"][i], curves["theory"][i], curves["empirical"][i]
        p_pt, p_pe = curves["pos_theory"][i], curves["pos_empirical"][i]
        p_cor = curves["correction"][i]
        def f(p):
            if p["sigma_y"] is None:
                return "—"
            return f"{p['sigma_y']:.3e} ± {p['u_sigma']:.1e}"
        lines.append(
            f"| {tau} | {tau / 86400:.3f} | {f(p_raw)} | {f(p_th)} | {f(p_em)} "
            f"| {f(p_pt)} | {f(p_pe)} | {f(p_cor)} | {p_raw['n_pairs']} |")
    lines.append(
        "\n> `u_sigma` is the 1-sigma EDF (Riley & Howe) uncertainty on sigma_y. "
        "Gaps are removed, so the record is treated as contiguous; a tau longer "
        "than one raw segment is computable but mixes different campaigns, and "
        "`n_pairs` records the adjacent m-averaged differences behind each "
        "point.\n")
    lines.append(f"\n![Spliced stability]({FIG_PNG.name})\n")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    write_figure(taus, curves)

    print(f"aligned axis: {aligned_times[0]} .. {aligned_times[-1]} "
          f"({n_total:,} samples, 1-s steps)")
    print(f"pure data span {n_total / 86400:.3f} d vs real elapsed {span_days:.2f} d; "
          f"tau up to {taus[-1]} s ({taus[-1] / 86400:.3f} d)")
    for key in ("raw", "theory", "empirical", "pos_theory", "pos_empirical",
                "correction"):
        p = curves[key][-1]
        sigma = "N/A" if p["sigma_y"] is None else f"{p['sigma_y']:.4e}"
        print(f"  {key:13s} sigma_y({p['tau_s']}s) = {sigma}  (n_pairs={p['n_pairs']})")
    print(f"wrote {CSV_PATH.name}, {MD_PATH.name}")
    return 0


def write_figure(taus, curves) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    meta = {
        "raw": ("raw (A=0)", "#8a8a8a", "o", "-"),
        "theory": ("theory (A=-1)", "#1f4e9c", "s", "-"),
        "empirical": ("empirical (A=-0.54)", "#2ca02c", "D", "--"),
        "pos_theory": ("pos_theory (A=+1)", "#1f4e9c", "s", ":"),
        "pos_empirical": ("pos_empirical (A=+0.54)", "#2ca02c", "D", ":"),
        "correction": ("correction h/F1550 (A=-1)", "#b22222", "^", "-"),
    }
    fig, ax = plt.subplots(figsize=(6.9, 3.6))
    for key in ("raw", "theory", "empirical", "pos_theory", "pos_empirical",
                "correction"):
        label, color, marker, linestyle = meta[key]
        pts = [p for p in curves[key] if p["sigma_y"] is not None]
        xs = [p["tau_s"] for p in pts]
        ys = [p["sigma_y"] for p in pts]
        es = [p["u_sigma"] for p in pts]
        ax.errorbar(xs, ys, yerr=es, color=color, marker=marker, ms=4.0,
                    lw=1.2, linestyle=linestyle, elinewidth=0.8, capsize=1.8,
                    label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\tau$ [s]")
    ax.set_ylabel(r"$\sigma_y(\tau)$")
    ax.set_title("Spliced concatenated ratio stability (gaps removed)",
                 fontsize=9.5)
    ax.grid(True, which="both", alpha=0.18, lw=0.4)
    ax.legend(frameon=False, fontsize=8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.savefig(FIG_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(FIG_PDF)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
