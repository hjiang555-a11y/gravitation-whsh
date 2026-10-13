#!/usr/bin/env python3
"""Figure generator for the rebuilt manuscript (paper/rev2).

Reads only generated/numbers.json (written by build_numbers.py) and writes
figs/fig2_campaign, figs/fig3_compare as PNG (300 dpi) and PDF. No numeric
literal that appears in the manuscript is typed here; every plotted value
comes from the generated payload.

fig1_network is a hand-supplied figure (user-provided PNG, 2026-10-13) and
is intentionally not regenerated here.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TOOLS = Path(__file__).resolve().parent
REV2 = TOOLS.parent
FIGS = REV2 / "figs"
PAYLOAD = REV2 / "generated" / "numbers.json"

STAGE_COLORS = {1: "#0969da", 2: "#d62728", 3: "#2ca02c"}
STAGE_LABELS = {1: "Stage 1", 2: "Stage 2", 3: "Stage 3"}


def _load() -> dict:
    with PAYLOAD.open(encoding="utf-8") as fh:
        return json.load(fh)


def _save(fig, name: str) -> None:
    png = FIGS / f"{name}.png"
    pdf = FIGS / f"{name}.pdf"
    fig.savefig(png, dpi=300)
    fig.savefig(pdf)
    plt.close(fig)
    print(f"Wrote {png.name}, {pdf.name}")


def fig_network() -> None:
    """Hand-supplied figure: see module docstring. Kept as a no-op so that
    old invocations do not overwrite the user-provided fig1_network.png."""
    print("fig1_network.png is user-supplied; skipping regeneration")


def fig_campaign() -> None:
    payload = _load()
    segments = payload["segments"]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.9, 4.0),
                                   gridspec_kw={"height_ratios": [1, 2]})

    max_n = max(seg["n_valid"] for seg in segments)
    x_lo = min(seg["group"] for seg in segments) - 0.6
    x_hi = max(seg["group"] for seg in segments) + 0.6
    for seg in segments:
        color = STAGE_COLORS[seg["stage"]]
        width = 0.8 * np.sqrt(seg["n_valid"] / max_n)
        ax1.barh(0, width, left=seg["group"] - width / 2, color=color,
                 height=0.6, alpha=0.85)
    ax1.set_yticks([])
    ax1.set_xlim(x_lo, x_hi)
    ax1.set_xlabel("Recorded segment index")
    ax1.set_title("(a) Campaign stages", fontsize=10, loc="left")
    handles = [plt.Rectangle((0, 0), 1, 1, color=STAGE_COLORS[s])
               for s in sorted(STAGE_COLORS)]
    ax1.legend(handles, [STAGE_LABELS[s] for s in sorted(STAGE_COLORS)],
               fontsize=8, ncol=3, loc="upper right", frameon=False)

    groups = [seg["group"] for seg in segments]
    y = [seg["y_i_1e18"] for seg in segments]
    u = [seg["u_frac_1e18"] for seg in segments]
    colors = [STAGE_COLORS[seg["stage"]] for seg in segments]
    ax2.errorbar(groups, y, yerr=u, fmt="none", ecolor="#57606a", lw=1.0,
                 capsize=2.5, zorder=2)
    ax2.scatter(groups, y, c=colors, s=32, zorder=3)
    ax2.axhline(0.0, color="#24292f", lw=0.8, ls="--")
    ax2.set_xlabel("Segment index")
    ax2.set_ylabel(r"$y_i$ ($10^{-18}$)")
    ax2.set_title("(b) Per-segment ratio deviations", fontsize=10, loc="left")
    ax2.grid(alpha=0.25)
    ax2.set_xlim(x_lo, x_hi)
    fig.tight_layout()
    _save(fig, "fig2_campaign")


def fig_compare() -> None:
    payload = _load()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.9, 3.0))

    comps = payload["comparisons"]
    names = [c["name"] for c in comps]
    deltas = [c["delta_e18"] for c in comps]
    errs = [c["u_e18"] for c in comps]
    colors = ["#0969da", "#d62728", "#2ca02c"]
    ypos = np.arange(len(comps))[::-1]
    ax1.errorbar(deltas, ypos, xerr=errs, fmt="o", ms=6, lw=1.4, capsize=3,
                 color="#24292f", zorder=2)
    for x, yv, c in zip(deltas, ypos, colors):
        ax1.plot([x], [yv], marker="o", ms=6, color=c, zorder=3)
    ax1.axvline(0.0, color="#57606a", lw=0.8, ls=":")
    ax1.set_yticks(ypos)
    ax1.set_yticklabels(names, fontsize=8.5)
    ax1.set_xlabel(r"Difference from this work ($10^{-18}$)")
    ax1.set_title("(a) Comparison with published ratios", fontsize=10, loc="left")
    ax1.grid(alpha=0.25, axis="x")

    budget = payload["budget"]
    names = [b["name"] for b in budget]
    vals = [b["e18"] for b in budget]
    ax2.barh(np.arange(len(budget))[::-1], vals, color="#0969da", alpha=0.85)
    total = payload["headline"]["u_total_e18"]
    ax2.axvline(total, color="#d62728", lw=1.2, ls="--",
                label=f"total = {total:.2f}")
    ax2.set_yticks(np.arange(len(budget))[::-1])
    ax2.set_yticklabels(names, fontsize=8.5)
    ax2.set_xlabel(r"Contribution ($10^{-18}$)")
    ax2.set_title("(b) Uncertainty budget", fontsize=10, loc="left")
    ax2.legend(fontsize=8, frameon=False, loc="lower right")
    ax2.grid(alpha=0.25, axis="x")
    fig.tight_layout()
    _save(fig, "fig3_compare")


def main() -> int:
    FIGS.mkdir(parents=True, exist_ok=True)
    fig_network()
    fig_campaign()
    fig_compare()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
