#!/usr/bin/env python3
"""17-segment cross-segment correlation: the 17 per-segment points.

Treats each of the 17 jump-free segments as one point. For each segment we have:
  - session tidal shift (Δf/f, ×1e-18): the segment-mean tidal gravitational
    redshift expected from the professional 综合差;
  - amplitude ratio A: the fitted beat = A·tide amplitude;
  - correlation r, p: segment-level correlation;
  - hours / n_pts: segment duration.

This script reports the pairwise correlations among these 17-point vectors:
  1. A  vs  session tidal shift   (does a larger tidal mean imply a larger fit?)
  2. r  vs  session tidal shift
  3. A  vs  r                     (internal consistency)
  4. A  vs  hours / n_pts         (duration dependence)

Outputs: segment17_correlation.md
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy import stats

OUT_DIR = Path(__file__).resolve().parent


def load():
    rows = list(csv.DictReader(open(OUT_DIR / "batch_summary.csv")))
    A = np.array([float(r["A"]) for r in rows])
    uA = np.array([float(r["u_A"]) for r in rows])
    r = np.array([float(r["r"]) for r in rows])
    p = np.array([float(r["p"]) for r in rows])
    hours = np.array([float(r["hours"]) for r in rows])
    n_pts = np.array([int(r["n_pts"]) for r in rows])
    tr = list(csv.DictReader(open(OUT_DIR.parent / "clock_tidal_shift.csv")))
    dff = np.array([float(x["frequency_shift_dff"]) for x in tr]) * 1e18
    return A, uA, r, p, hours, n_pts, dff


def pearson(x, y):
    return stats.pearsonr(x, y)


def spear(x, y):
    return stats.spearmanr(x, y)


def main():
    A, uA, r, p, hours, n_pts, dff = load()
    n = len(A)

    lines = []
    lines.append("# 17 段相关性分析（17 个点彼此间的相关）")
    lines.append("")
    lines.append("每个无跳点段作为一个点，考察以下 17 点向量之间的相关性：")
    lines.append("- 会话潮汐频差 Δf/f（×1e-18）：该段潮汐引力红移的段均值（专业综合差 → ΔW/c²）")
    lines.append("- 幅度比 A：段内拍频 = A·潮汐 的最小二乘幅度")
    lines.append("- 段相关系数 r、p：段内相关性")
    lines.append("- 段时长 hours、积分点数 n_pts")
    lines.append("")
    lines.append("## 1. 17 点两两相关矩阵（Pearson r，括号 p 值）")
    lines.append("")

    vec = {"会话潮汐频差Δf/f": dff, "幅度A": A, "相关系数r": r,
           "时长hours": hours, "积分点数": n_pts, "A不确定度u_A": uA}
    keys = list(vec.keys())
    lines.append("| | " + " | ".join(k for k in keys) + " |")
    lines.append("|---|" + "|".join("---:" for _ in keys) + "|")
    for ki in keys:
        row = [ki]
        for kj in keys:
            if ki == kj:
                row.append("1")
            else:
                rr, pp = pearson(vec[ki], vec[kj])
                row.append(f"{rr:+.3f} ({pp:.3f})")
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")
    lines.append("## 2. 关键单对相关（详细）")
    lines.append("")
    pairs = [
        ("幅度A vs 会话潮汐频差", A, dff),
        ("相关系数r vs 会话潮汐频差", r, dff),
        ("幅度A vs 相关系数r", A, r),
        ("幅度A vs 时长", A, hours),
        ("幅度A vs 积分点数", A, n_pts),
    ]
    for name, x, y in pairs:
        rr, pp = pearson(x, y)
        rho, prho = spear(x, y)
        lines.append(f"- **{name}**：Pearson r = {rr:+.3f}（p={pp:.3f}），"
                     f" Spearman ρ = {rho:+.3f}（p={prho:.3f}）")

    # 会话潮汐频差 vs A 的 OLS
    slope, intercept, rv, pv, se = stats.linregress(dff, A)
    lines.append("")
    lines.append("## 3. 幅度 A ~ 会话潮汐频差 的线性回归")
    lines.append("")
    lines.append(f"最小二乘：A = {slope:+.3f} × (会话潮汐频差) {intercept:+.3f}，"
                 f" r={rv:+.3f}，p={pv:.3f}，std_err={se:.3f}")
    # 精度加权回归 (1/uA^2)
    w = 1.0 / uA**2
    wbar = np.sum(w * dff) / np.sum(w)
    slope_w = np.sum(w * (dff - wbar) * A) / np.sum(w * (dff - wbar) ** 2)
    lines.append(f"精度加权(1/u_A²)回归斜率 = {slope_w:+.3f}")
    lines.append("")
    lines.append("""> 注：会话潮汐频差的正负反映该段潮汐段均值的符号；幅度 A 的正负反映
> 段内拍频随潮汐起伏的方向。两者符号一致（同为负段多）说明段内拟合方向与会话
> 段均值方向一致。""")

    out = OUT_DIR / "segment17_correlation.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
