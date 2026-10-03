#!/usr/bin/env python3
"""Publication-oriented figure set pairing the three paper paragraphs
(clock-ratio determination, tidal-redshift detection, tidal correction).

All numbers are read from this repository's own artifacts; nothing is
recomputed or hard-coded except axis framing.

Outputs (additive; nothing existing is overwritten):
  paper_figs/fig1_ratio_segments.{png,pdf}     per-segment R_i and deviation y_i
  paper_figs/fig2_tidal_detection.{png,pdf}    per-segment amplitude A_i (detection)
  paper_figs/fig3_correction.{png,pdf}         long-term stability sigma(y_i) + chi2_red
  paper_figs/fig4_methods_summary.{png,pdf}    four-method centers vs experiment WLS / NIST

Typography: journal-submission style — serif family with STIX mathtext,
vector PDF (fonttype 42 / TrueType-embedded), thin frames, no chartjunk.
PNG kept at dpi=300 next to each PDF.
"""
from __future__ import annotations

import csv
import json
import sys
from decimal import Decimal, localcontext
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared as s  # noqa: E402

OUT = Path(__file__).resolve().parent / "paper_figs"
RATIO_CSV = Path(__file__).resolve().parent / "ratio_17seg.csv"
BATCH_CSV = Path(__file__).resolve().parent.parent / "clock" / "segment_analysis" / "batch_summary.csv"
BATCH_AGG = Path(__file__).resolve().parent.parent / "clock" / "segment_analysis" / "batch_aggregate.csv"
CORR_CSV = Path(__file__).resolve().parent / "correlation_reanalysis.csv"
TIDAL_JSON = Path(__file__).resolve().parent / "statistical_methods_tidal.json"

WLS_REF = Decimal("1.2075070393433377213")
NIST_REF = Decimal("1.2075070393433377230")
A_FIT = -0.539699
U_A = 0.084254

# Publication palette (colorblind-safe, muted for print)
C_NEG = "#1f4e9c"
C_POS = "#2ca02c"
C_NEG2 = "#b22222"
C_GREY = "#8a8a8a"
C_INK = "#111111"

FIG_NAMES = ("fig1_ratio_segments", "fig2_tidal_detection",
             "fig3_correction", "fig4_methods_summary")


def _publication_style() -> None:
    """Set journal-grade rcParams: serif, STIX math, thin frames, embedded fonts."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman",
                       "Nimbus Roman", "Liberation Serif"],
        "mathtext.fontset": "stix",
        "font.size": 9,
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.5,
        "ytick.minor.width": 0.5,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.size": 1.6,
        "ytick.minor.size": 1.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "figure.dpi": 300,
    })


def SAVE(fig: plt.Figure, name: str) -> tuple[Path, Path]:
    """Write both a 300-dpi PNG and a vector PDF for one figure."""
    png = OUT / f"{name}.png"
    pdf = OUT / f"{name}.pdf"
    fig.savefig(png, dpi=300)
    fig.savefig(pdf)
    return png, pdf


def _load_ratio():
    rows = list(csv.DictReader(open(RATIO_CSV)))
    y = np.array([float(r["y_i_1e18"]) for r in rows])
    n = np.array([int(r["n_valid"]) for r in rows])
    return y, n


def _load_batch():
    rows = list(csv.DictReader(open(BATCH_CSV)))
    A = np.array([float(r["A"]) for r in rows])
    uA = np.array([float(r["u_A"]) for r in rows])
    g = np.array([int(r["group"]) for r in rows])
    return g, A, uA


def ratio_offset_1e18(value: str | Decimal, reference: Decimal) -> float:
    """Subtract near-unity ratios before converting their E-18 difference to float."""
    with localcontext() as context:
        context.prec = 80
        return float((Decimal(value) - reference) * Decimal("1e18"))


def fig1_ratio():
    y, n = _load_ratio()
    seg = np.arange(1, len(y) + 1)
    w = n / n.sum()
    mean_w = float(np.sum(w * y))
    fig, ax = plt.subplots(figsize=(6.9, 3.1))
    colors = np.where(y >= 0, C_POS, C_NEG2)
    ax.bar(seg, y, color=colors, edgecolor=C_INK, linewidth=0.3, width=0.72)
    ax.axhline(0, color=C_GREY, lw=0.6, zorder=1)
    ax.axhline(mean_w, color=C_NEG, lw=0.9, ls="--", zorder=2,
               label=f"duration-weighted mean $= {mean_w:+.3f}$")
    ax.set_xticks(seg)
    ax.set_xlabel("segment index $i$")
    ax.set_ylabel(r"$y_i = R_i/R_{\rm seg1}-1$  ($\times 10^{-18}$)")
    ax.set_title("(a) Per-segment Yb/Sr clock-ratio deviation")
    ax.legend(loc="lower right", frameon=False, handlelength=1.6)
    ax.grid(alpha=0.18, axis="y", lw=0.4)
    ax.tick_params(which="both", direction="out")
    fig.tight_layout()
    SAVE(fig, "fig1_ratio_segments")
    plt.close(fig)


def fig2_detection():
    g, A, uA = _load_batch()
    fig, ax = plt.subplots(figsize=(6.9, 3.1))
    ax.errorbar(g, A, yerr=uA, fmt="o", ms=3.6, lw=0.7, capsize=1.8,
                elinewidth=0.7, color=C_INK, ecolor=C_GREY, zorder=3)
    ax.axhline(0.0, color=C_GREY, lw=0.6, ls=":", zorder=1)
    ax.axhline(1.0, color=C_NEG2, lw=0.9, ls="--", zorder=2,
               label="full theoretical ($A=+1$)")
    ax.axhline(A_FIT, color=C_NEG, lw=0.9, zorder=2,
               label=(f"combined $A={A_FIT:+.2f}\\pm{U_A:.2f}$ "
                      r"(6.4$\,\sigma$)"))
    ax.set_xticks(g)
    ax.set_xlabel("segment index $i$")
    ax.set_ylabel(r"tidal amplitude ratio $A_i$")
    ax.set_title(r"(b) Per-segment tidal-redshift amplitude (1200-s triangular fit)")
    ax.legend(loc="upper right", frameon=False, handlelength=1.8)
    ax.grid(alpha=0.18, axis="y", lw=0.4)
    ax.tick_params(which="both", direction="out")
    fig.tight_layout()
    SAVE(fig, "fig2_tidal_detection")
    plt.close(fig)


def fig3_correction():
    d = json.load(open(TIDAL_JSON))
    sc = d["synthesis"]["long_term_stability"]
    keys = ("raw", "theory", "empirical")
    labels = ["raw\n$A=0$", "theory\n$A=-1$", "empirical\n$A=-0.54$"]
    std = [sc[k]["y_i_std_1e18"] for k in keys]
    chi2r = [d["scenarios"][k]["chi2_red"] for k in keys]

    fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.1))
    x = np.arange(3)
    bar_colors = [C_GREY, C_NEG, C_POS]

    axes[0].bar(x, std, color=bar_colors, edgecolor=C_INK, linewidth=0.3, width=0.6)
    for xi, v in zip(x, std):
        axes[0].annotate(f"{v:.3f}", (xi, v), textcoords="offset points",
                         xytext=(0, 2.5), ha="center", fontsize=7.5)
    axes[0].set_xticks(x); axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylim(0, max(std) * 1.18)
    axes[0].set_ylabel(r"inter-segment $\sigma(y_i)$  ($\times 10^{-18}$)")
    axes[0].set_title("(c) Long-term stability")
    axes[0].grid(alpha=0.18, axis="y", lw=0.4)
    axes[0].tick_params(which="both", direction="out")

    axes[1].bar(x, chi2r, color=bar_colors, edgecolor=C_INK, linewidth=0.3, width=0.6)
    for xi, v in zip(x, chi2r):
        axes[1].annotate(f"{v:.2f}", (xi, v), textcoords="offset points",
                         xytext=(0, 2.5), ha="center", fontsize=7.5)
    axes[1].set_ylim(0, max(chi2r) * 1.18)
    axes[1].axhline(1.0, color=C_INK, lw=0.7, ls="--",
                    label=r"$\chi^2_{\rm red}=1$")
    axes[1].set_xticks(x); axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel(r"$\chi^2_{\rm red}$ (dof = 16)")
    axes[1].set_title("(d) Inter-segment consistency")
    axes[1].legend(frameon=False, handlelength=1.6, loc="upper right")
    axes[1].grid(alpha=0.18, axis="y", lw=0.4)
    axes[1].tick_params(which="both", direction="out")

    fig.tight_layout()
    SAVE(fig, "fig3_correction")
    plt.close(fig)


def fig4_methods():
    d = json.load(open(TIDAL_JSON))
    sc = d["scenarios"]
    keys = ("raw", "theory", "empirical")
    methods = ("R_wls", "R_mp", "R_bayes")
    mlabels = ["WLS", "Mandel–Paule", "Bayesian"]
    fig, ax = plt.subplots(figsize=(6.9, 3.1))
    width = 0.26
    x = np.arange(len(methods))
    colors = {"raw": C_GREY, "theory": C_NEG, "empirical": C_POS}
    for j, k in enumerate(keys):
        dev = [ratio_offset_1e18(sc[k][m], WLS_REF) for m in methods]
        ax.bar(x + (j - 1) * width, dev, width, label=k, color=colors[k],
               edgecolor=C_INK, linewidth=0.3)
    ax.axhline(0, color=C_INK, lw=0.6)
    nist_dev = ratio_offset_1e18(NIST_REF, WLS_REF)
    ax.axhline(nist_dev, color=C_NEG2, lw=0.9, ls="--",
               label=f"NIST ref ({nist_dev:+.2f})")
    ax.set_xticks(x); ax.set_xticklabels(mlabels)
    ax.set_ylabel(r"$R_{\rm method} - R_{\rm exp,WLS}$  ($\times 10^{-18}$)")
    ax.set_title("(e) Tidal-corrected combined centers by statistical method")
    ax.legend(frameon=False, handlelength=1.6, ncol=2, loc="best")
    ax.grid(alpha=0.18, axis="y", lw=0.4)
    ax.tick_params(which="both", direction="out")
    fig.tight_layout()
    SAVE(fig, "fig4_methods_summary")
    plt.close(fig)


def main() -> int:
    _publication_style()
    OUT.mkdir(exist_ok=True)
    fig1_ratio(); fig2_detection(); fig3_correction(); fig4_methods()
    for name in FIG_NAMES:
        for ext in ("png", "pdf"):
            print(f"Wrote {OUT / (name + '.' + ext)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
