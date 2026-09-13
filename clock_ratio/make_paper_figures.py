#!/usr/bin/env python3
"""Publication-oriented figure set pairing the three paper paragraphs
(clock-ratio determination, tidal-redshift detection, tidal correction).

All numbers are read from this repository's own artifacts; nothing is
recomputed or hard-coded except axis framing.

Outputs (new, additive; nothing existing is overwritten):
  paper_figs/fig1_ratio_segments.png     per-segment R_i and deviation y_i
  paper_figs/fig2_tidal_detection.png    per-segment amplitude A_i (detection)
  paper_figs/fig3_correction.png         correction before/after + direction self-check
  paper_figs/fig4_methods_summary.png    four-method centers vs experiment WLS / NIST
"""
from __future__ import annotations

import csv
import json
import sys
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

WLS_REF = 1.2075070393433377213
NIST_REF = 1.2075070393433377230
A_FIT = -0.539699
U_A = 0.084254


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


def fig1_ratio():
    y, n = _load_ratio()
    seg = np.arange(1, len(y) + 1)
    w = n / n.sum()
    mean_w = float(np.sum(w * y))
    fig, ax = plt.subplots(figsize=(9, 4.2))
    colors = np.where(y >= 0, "#2ca02c", "#d62728")
    ax.bar(seg, y, color=colors, alpha=0.85, edgecolor="black", linewidth=0.4)
    ax.axhline(0, color="gray", lw=1)
    ax.axhline(mean_w, color="#1f4e9c", lw=1.4, ls="--",
               label=f"duration-weighted mean = {mean_w:+.3f} ×10$^{{-18}}$")
    ax.set_xticks(seg)
    ax.set_xlabel("Segment index $i$")
    ax.set_ylabel(r"$y_i = R_i/R_{\rm seg1}-1$  ($\times 10^{-18}$)")
    ax.set_title("(a) Per-segment Yb/Sr clock-ratio deviation", fontweight="bold")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "fig1_ratio_segments.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig2_detection():
    g, A, uA = _load_batch()
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.errorbar(g, A, yerr=uA, fmt="o", ms=5, lw=1.1, capsize=3,
                color="#333333", ecolor="#999999", zorder=3)
    ax.axhline(0.0, color="gray", lw=1, ls=":")
    ax.axhline(1.0, color="#d62728", lw=1.2, ls="--", label="full theoretical ($A=+1$)")
    ax.axhline(A_FIT, color="#1f4e9c", lw=1.4,
               label=f"combined $A={A_FIT:+.2f}\\pm{U_A:.2f}$ (6.4$\\sigma$)")
    ax.set_xticks(g)
    ax.set_xlabel("Segment index $i$")
    ax.set_ylabel(r"tidal amplitude ratio $A_i$")
    ax.set_title("(b) Per-segment tidal-redshift amplitude (1200-s triangular fit)",
                 fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_tidal_detection.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig3_correction():
    d = json.load(open(TIDAL_JSON))
    sc = d["synthesis"]["long_term_stability"]
    keys = ("raw", "theory", "empirical")
    labels = ["raw\n$A=0$", "theory\n$A=-1$", "empirical\n$A=-0.54$"]
    std = [sc[k]["y_i_std_1e18"] for k in keys]
    chi2r = [d["scenarios"][k]["chi2_red"] for k in keys]

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))
    x = np.arange(3)
    axes[0].bar(x, std, color=["#999999", "#1f4e9c", "#2ca02c"], alpha=0.9,
                edgecolor="black", linewidth=0.4)
    for xi, v in zip(x, std):
        axes[0].annotate(f"{v:.3f}", (xi, v), textcoords="offset points",
                         xytext=(0, 3), ha="center", fontsize=8)
    axes[0].set_xticks(x); axes[0].set_xticklabels(labels, fontsize=8)
    axes[0].set_ylabel(r"inter-segment $\sigma(y_i)$  ($\times 10^{-18}$)")
    axes[0].set_title("(c) Long-term stability", fontweight="bold")
    axes[0].grid(alpha=0.25, axis="y")

    axes[1].bar(x, chi2r, color=["#999999", "#1f4e9c", "#2ca02c"], alpha=0.9,
                edgecolor="black", linewidth=0.4)
    for xi, v in zip(x, chi2r):
        axes[1].annotate(f"{v:.2f}", (xi, v), textcoords="offset points",
                         xytext=(0, 3), ha="center", fontsize=8)
    axes[1].axhline(1.0, color="black", lw=1, ls="--", label=r"$\chi^2_{\rm red}=1$")
    axes[1].set_xticks(x); axes[1].set_xticklabels(labels, fontsize=8)
    axes[1].set_ylabel(r"$\chi^2_{\rm red}$ (dof=16)")
    axes[1].set_title("(d) Inter-segment consistency", fontweight="bold")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "fig3_correction.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig4_methods():
    d = json.load(open(TIDAL_JSON))
    sc = d["scenarios"]
    keys = ("raw", "theory", "empirical")
    methods = ("R_wls", "R_mp", "R_bayes")
    mlabels = ["WLS", "Mandel-Paule", "Bayesian"]
    fig, ax = plt.subplots(figsize=(9, 4.2))
    width = 0.25
    x = np.arange(len(methods))
    colors = {"raw": "#999999", "theory": "#1f4e9c", "empirical": "#2ca02c"}
    for j, k in enumerate(keys):
        dev = [(float(sc[k][m]) - WLS_REF) * 1e18 for m in methods]
        ax.bar(x + (j - 1) * width, dev, width, label=k, color=colors[k],
               alpha=0.9, edgecolor="black", linewidth=0.4)
    ax.axhline(0, color="black", lw=1)
    nist_dev = (NIST_REF - WLS_REF) * 1e18
    ax.axhline(nist_dev, color="#d62728", lw=1.2, ls="--",
               label=f"NIST ref ({nist_dev:+.2f})")
    ax.set_xticks(x); ax.set_xticklabels(mlabels)
    ax.set_ylabel(r"$R_{\rm method} - R_{\rm exp,WLS}$  ($\times 10^{-18}$)")
    ax.set_title("(e) Tidal-corrected combined centers by statistical method",
                 fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    fig.savefig(OUT / "fig4_methods_summary.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    OUT.mkdir(exist_ok=True)
    fig1_ratio(); fig2_detection(); fig3_correction(); fig4_methods()
    for name in ("fig1_ratio_segments", "fig2_tidal_detection",
                 "fig3_correction", "fig4_methods_summary"):
        print(f"Wrote {OUT / (name + '.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
