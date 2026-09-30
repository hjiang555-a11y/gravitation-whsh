#!/usr/bin/env python3
"""Concatenated-stability assessment of the tidal impact on the Yb/Sr ratio.

Answers: over the WHOLE experiment (all 17 valid segments joined into one
series), how does the ratio-measurement stability behave when the tidal
gravitational redshift is (i) left in (raw), (ii) removed at the full
theoretical amplitude (A=-1, "theory"), and (iii) removed at the fitted
empirical amplitude (A=-0.54, "empirical")?

Method (reuses the frozen raw selection and the paper-style OADEV):
  1. select_segments  -> the 17 frozen segments (identical to every other
     artifact; raw data alone decide membership).
  2. For each scenario (A=0 / -1 / -0.54), apply  b_corr = b_raw - A*h  with
     h = F_1550 * deltaW(t) / c^2 interpolated onto each segment's timestamps,
     and take the per-second ratio fluctuation series  y(t) = -q/(1+q)
     produced by analyze_segment (the same series used for the per-segment
     OADEV; it is the fractional deviation of the measured ratio).
  3. CONCATENATE the 17 segments' (times, y) into a single long array and run
     ONE overlapping Allan deviation. Gaps between segments break the Allan
     pairs automatically (oadev breaks at every non-1-second step), so this is
     a gap-safe concatenated stability, not a spliced fake-continuous series.
  4. Report sigma_y(tau) for the three scenarios on the SAME tau grid, plus the
     scenario/raw sigma ratio.

  5. Also report the PER-SEGMENT-POOLED curve (pair-count weighted mean Allan
     variance across the same 17 segments, from the existing per-segment
     stability.csv) so the concatenated curve can be checked for consistency:
     the two must agree wherever the same segments contribute, and the
     concatenated curve extends to longer tau because it is not truncated to a
     single segment's run//4.

This is an independent result set; it does not modify any existing artifact.
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
    SCENARIOS, AnalysisError, TideGrid, analyze_segment, select_segments,
)
from clock_ratio.tidal_stability import (  # noqa: E402
    continuous_runs, oadev, tau_grid,
)

OUT_DIR = Path(__file__).resolve().parent
CSV_PATH = OUT_DIR / "concatenated_stability.csv"
MD_PATH = OUT_DIR / "concatenated_stability.md"
FIG_PNG = OUT_DIR / "concatenated_stability.png"
FIG_PDF = OUT_DIR / "concatenated_stability.pdf"
SEG_STABILITY_CSV = OUT_DIR / "tidal_correction" / "stability.csv"


def concatenate(results_by_scenario: dict[str, list]) -> dict[str, tuple]:
    """Join each scenario's 17 segment series into one (times, y) array.

    Segments are appended in time order (select_segments yields them in GROUPS
    order, which is chronological). The large real-world gaps remain in the
    time array, so oadev() opens a new continuous run at every gap.
    """
    out: dict[str, tuple] = {}
    for key, results in results_by_scenario.items():
        times = np.concatenate([r.segment.times for r in results])
        y = np.concatenate([r.fluctuations for r in results])
        out[key] = (times, y)
    return out


def pooled_per_segment(path: Path) -> dict[str, dict[int, tuple[int, float]]]:
    """Pair-count weighted pool of the per-segment OADEV (existing artifact).

    Returns scenario -> tau_s -> (n_pairs, sigma_y), where sigma_y is the pooled
    Allan deviation: sigma^2 = sum_runs(2*sigma_run^2*n_run) / sum_runs(2*n_run).
    This uses the SAME oadev output already in the per-segment stability.csv, so
    it is directly comparable to the concatenated curve wherever the same
    segments contribute. The per-segment file caps tau at each segment's
    run//4, so at large tau fewer segments contribute than in the concatenated
    curve (which pools every within-run pair of every segment).
    """
    acc: dict[str, dict[int, list[float]]] = {}
    if not path.exists():
        return {}
    for row in csv.DictReader(path.open(encoding="utf-8")):
        sigma = row["sigma_y"]
        if sigma in ("", "None"):
            continue
        scenario, tau, n_pairs = row["scenario"], int(row["tau_s"]), int(row["n_pairs"])
        slot = acc.setdefault(scenario, {}).setdefault(tau, [0.0, 0])
        slot[0] += 2.0 * float(sigma) ** 2 * n_pairs
        slot[1] += n_pairs
    return {
        scenario: {
            tau: (int(pair_sum), (sum_squares / (2.0 * pair_sum)) ** 0.5)
            for tau, (sum_squares, pair_sum) in taus.items()
            if pair_sum
        }
        for scenario, taus in acc.items()
    }



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

    # Per-scenario per-segment results, then concatenate.
    results_by_scenario: dict[str, list] = {sc.key: [] for sc in SCENARIOS}
    for segment in segments:
        template = tide.beat_at(segment.times)
        for scenario in SCENARIOS:
            results_by_scenario[scenario.key].append(
                analyze_segment(segment, template, scenario))

    series = concatenate(results_by_scenario)

    # One tau grid for all scenarios, from the LONGEST single continuous run
    # (oadev caps tau at run//4 internally via the caller's grid choice; we use
    # the longest run across scenarios, which is identical here).
    longest = max(
        stop - start
        for times_sc, _ in series.values()
        for start, stop in continuous_runs(times_sc)
    )
    taus = tau_grid(longest)
    curves: dict[str, tuple] = {
        key: oadev(series[key][0], series[key][1], taus)
        for key in ("raw", "theory", "empirical")
    }
    raw_sigma = {p.tau_s: p.sigma_y for p in curves["raw"]}
    pooled = pooled_per_segment(SEG_STABILITY_CSV)

    coef = {sc.key: str(sc.coefficient) for sc in SCENARIOS}
    with CSV_PATH.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["scenario", "coefficient", "tau_s", "n_pairs",
                         "sigma_y", "sigma_ratio_vs_raw",
                         "pooled_n_pairs", "pooled_sigma_y", "concat_vs_pooled"])
        for key in ("raw", "theory", "empirical"):
            for point in curves[key]:
                raw = raw_sigma.get(point.tau_s)
                ratio = (point.sigma_y / raw
                         if raw and point.sigma_y is not None and raw > 0 else "")
                pooled_point = pooled.get(key, {}).get(point.tau_s)
                if pooled_point and point.sigma_y is not None:
                    p_np, p_sig = pooled_point
                    rel = point.sigma_y / p_sig
                else:
                    p_np, p_sig, rel = "", "", ""
                writer.writerow([
                    key, coef[key], point.tau_s, point.n_pairs,
                    "" if point.sigma_y is None else f"{point.sigma_y:.6e}",
                    "" if ratio == "" else f"{ratio:.6f}",
                    p_np, "" if p_sig == "" else f"{p_sig:.6e}",
                    "" if rel == "" else f"{rel:.6f}",
                ])

    # ---- Markdown report
    total = sum(len(r.segment.beat) for r in results_by_scenario["raw"])
    lines: list[str] = []
    lines.append("# Concatenated-stability assessment of the tidal impact\n")
    lines.append(
        f"All **{total:,}** valid one-second samples from the 17 segments are "
        "joined into a single series; one gap-safe overlapping Allan deviation "
        "is computed per scenario. Real inter-segment gaps break the Allan "
        "pairs (never spliced).\n")
    lines.append(
        "The `pooled` column is the pair-count weighted pool of the existing "
        "per-segment OADEV ([tidal_correction/stability.csv](tidal_correction/stability.csv)). "
        "It agrees with the concatenated curve wherever the same segments "
        "contribute; the concatenated curve extends to longer tau because it is "
        "not truncated to a single segment's run//4.\n")
    lines.append("## sigma_y(tau)  [concat | pooled per-segment]\n")
    lines.append("| tau [s] | raw | theory (A=-1) | empirical (A=-0.54) | "
                 "theory/raw | empirical/raw |")
    lines.append("|---|---|---|---|---|---|")
    for i, tau in enumerate(taus):
        p_raw, p_th, p_em = curves["raw"][i], curves["theory"][i], curves["empirical"][i]
        def f(p, key):
            concat = "—" if p.sigma_y is None else f"{p.sigma_y:.3e}"
            pooled_pt = pooled.get(key, {}).get(tau)
            pool = f" / {pooled_pt[1]:.3e}" if pooled_pt else ""
            return concat + pool
        def r(p, base):
            if p.sigma_y is None or base is None or base == 0:
                return "—"
            return f"{p.sigma_y / base:.4f}"
        lines.append(f"| {tau} | {f(p_raw, 'raw')} | {f(p_th, 'theory')} | "
                     f"{f(p_em, 'empirical')} | "
                     f"{r(p_th, p_raw.sigma_y)} | {r(p_em, p_raw.sigma_y)} |")
    lines.append("")
    last = len(taus) - 1
    lines.append("## Summary at the longest common tau\n")
    lines.append(f"- tau = {taus[last]} s: raw = {curves['raw'][last].sigma_y:.3e}, "
                 f"theory = {curves['theory'][last].sigma_y:.3e}, "
                 f"empirical = {curves['empirical'][last].sigma_y:.3e}")
    lines.append("\n> A ratio > 1 means the tidal correction LEFT MORE scatter than "
                 "the raw data at that tau (i.e. the correction over-corrected there); "
                 "< 1 means the correction reduced the scatter.")
    lines.append("\n> Method: `b_corr = b_raw - A*h`, `h = F_1550*deltaW/c^2`, "
                 "`y(t) = -q/(1+q)` (fractional ratio deviation). "
                 "Gap-safe: pairs never cross a non-1 s step. "
                 "OADEV is not SEM and no uncertainty is propagated.\n")
    lines.append(f"\n![Concatenated stability]({FIG_PNG.name})\n")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    write_figure(taus, curves, pooled)

    print(f"concatenated samples: {total:,} over {len(segments)} segments")
    print(f"longest continuous run: {longest} s -> tau up to {taus[-1]} s")
    print(f"wrote {CSV_PATH.name}, {MD_PATH.name}, {FIG_PNG.name}, {FIG_PDF.name}")
    for key in ("raw", "theory", "empirical"):
        p = curves[key][-1]
        print(f"  {key:10s} sigma_y({taus[-1]}s) = "
              f"{'N/A' if p.sigma_y is None else f'{p.sigma_y:.4e}'}")
    return 0


def write_figure(taus, curves, pooled) -> None:
    """Three scenario lines (raw / theory / empirical), concatenated AND pooled."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    labels = {"raw": "raw (A=0)", "theory": "theory (A=-1)",
              "empirical": "empirical (A=-0.54)"}
    colors = {"raw": "#8a8a8a", "theory": "#1f4e9c", "empirical": "#b22222"}
    markers = {"raw": "o", "theory": "s", "empirical": "^"}

    fig, ax = plt.subplots(figsize=(6.9, 3.6))
    for key in ("raw", "theory", "empirical"):
        y_concat = [p.sigma_y for p in curves[key]]
        ax.loglog(taus, y_concat, color=colors[key], marker=markers[key],
                  ms=3.2, lw=1.2, label=f"{labels[key]} — concatenated")
        pooled_taus = sorted(tau for tau in pooled.get(key, {}) if tau in taus)
        if pooled_taus:
            y_pooled = [pooled[key][tau][1] for tau in pooled_taus]
            ax.loglog(pooled_taus, y_pooled, color=colors[key], ls="none",
                      marker="x", ms=4.0, mew=0.9,
                      label=f"{labels[key]} — pooled per-segment")
    ax.set_xlabel(r"$\tau$ [s]")
    ax.set_ylabel(r"$\sigma_y(\tau)$  (concatenated Yb/Sr ratio)")
    ax.set_title("Tidal impact on ratio stability: raw vs theory vs empirical",
                 fontsize=9.5)
    ax.grid(True, which="both", alpha=0.18, lw=0.4)
    ax.legend(frameon=False, fontsize=7.5, ncol=2)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    fig.savefig(FIG_PNG, dpi=300, bbox_inches="tight")
    fig.savefig(FIG_PDF)
    plt.close(fig)


if __name__ == "__main__":
    raise SystemExit(main())
