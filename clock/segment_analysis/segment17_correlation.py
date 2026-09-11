#!/usr/bin/env python3
"""17-segment cross-segment correlation: the 17 per-segment points.

Treats each of the 17 jump-free segments as one point. For each segment we have:
  - session tidal shift (Δf/f, ×1e-18): the segment-mean tidal gravitational
    redshift expected from the professional 综合差;
  - clock-ratio deviation y_i = R_i/R_ref − 1 (×1e-18): the physically-primary
    segment-level quantity (dimensionless, normalized to 1, the tidal effect on
    the clock);
  - amplitude ratio A: the fitted beat = A·tide amplitude (a dimensionless
    within-segment fit slope — diagnostic, NOT interchangeable with y_i);
  - correlation r, p: segment-level correlation;
  - hours / n_pts: segment duration.

The physically-coherent segment-level correlation is y_i vs Δf/f (both are
dimensionless quantities normalized to 1). A vs Δf/f is physically incoherent
(A is a within-segment fit slope, Δf/f is a between-segment mean) and is kept
only as a diagnostic. Outputs: segment17_correlation.md
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
    ratio_rows = list(csv.DictReader(
        open(Path(__file__).resolve().parents[2] / "clock_ratio" / "ratio_17seg.csv")))
    y_i = np.array([float(rr["y_i_1e18"]) for rr in ratio_rows])
    return A, uA, r, p, hours, n_pts, dff, y_i


def pearson(x, y):
    return stats.pearsonr(x, y)


def spear(x, y):
    return stats.spearmanr(x, y)


def main():
    A, uA, r, p, hours, n_pts, dff, y_i = load()
    n = len(A)

    lines = []
    lines.append("# 17 段相关性分析（17 个点彼此间的相关）")
    lines.append("")
    lines.append("每个无跳点段作为一个点，考察以下 17 点向量之间的相关性：")
    lines.append("- 会话潮汐频差 Δf/f（×1e-18）：该段潮汐引力红移的段均值（专业综合差 → ΔW/c²）")
    lines.append("- 钟比值偏差 y_i（×1e-18）：R_i/R_ref − 1，**物理主要段级量**（无量纲、归一化到 1）")
    lines.append("- 幅度比 A：段内拍频 = A·潮汐 的最小二乘幅度（诊断量，与 y_i 不可互相替代）")
    lines.append("- 段相关系数 r、p：段内相关性")
    lines.append("- 段时长 hours、积分点数 n_pts")
    lines.append("")
    lines.append("> 物理量对应说明：**y_i 与 Δf/f 是物理上正确的段级配对**（两者都是归一化到 1 的")
    lines.append("> 无量纲量，表征潮汐对钟的影响）。A 与 Δf/f 物理量不对应（A 是段内拟合斜率、")
    lines.append("> Δf/f 是段间均值），其相关仅作诊断参考。")
    lines.append("")
    lines.append("## 1. 17 点两两相关矩阵（Pearson r，括号 p 值）")
    lines.append("")

    vec = {"会话潮汐频差Δf/f": dff, "钟比值偏差y_i": y_i, "幅度A": A,
           "相关系数r": r, "时长hours": hours, "积分点数": n_pts, "A不确定度u_A": uA}
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
        ("钟比值偏差y_i vs 会话潮汐频差", y_i, dff),
        ("幅度A vs 会话潮汐频差", A, dff),
        ("相关系数r vs 会话潮汐频差", r, dff),
        ("钟比值偏差y_i vs 幅度A", y_i, A),
        ("幅度A vs 相关系数r", A, r),
        ("幅度A vs 时长", A, hours),
        ("幅度A vs 积分点数", A, n_pts),
    ]
    for name, x, y in pairs:
        rr, pp = pearson(x, y)
        rho, prho = spear(x, y)
        lines.append(f"- **{name}**：Pearson r = {rr:+.3f}（p={pp:.3f}），"
                     f" Spearman ρ = {rho:+.3f}（p={prho:.3f}）")

    # 会话潮汐频差 vs y_i 的 OLS（物理正确的段级回归）
    slope, intercept, rv, pv, se = stats.linregress(dff, y_i)
    lines.append("")
    lines.append("## 3. 钟比值偏差 y_i ~ 会话潮汐频差 的线性回归（物理正确）")
    lines.append("")
    lines.append(f"最小二乘：y_i = {slope:+.3f} × (会话潮汐频差) {intercept:+.3f}，"
                 f" r={rv:+.3f}，p={pv:.3f}，std_err={se:.3f}")
    lines.append("")
    lines.append("""> 注：这是物理上正确的段级回归——y_i 与 Δf/f 都是归一化到 1 的无量纲量，
> 表征潮汐对钟的影响；斜率物理上应趋近 1（若钟无其他漂移）。""")

    out = OUT_DIR / "segment17_correlation.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
