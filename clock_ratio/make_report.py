#!/usr/bin/env python3
"""Auto-generate the authoritative experiment report (EXPERIMENT_REPORT.md).

Reads the CSVs produced by the analysis pipeline and renders a complete Markdown
report with all headline numbers, tables, and figure references. Run after
run_all.py (or after the analysis steps) to refresh the report from data.

Outputs: clock_ratio/EXPERIMENT_REPORT.md
"""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
CLOCK_DIR = OUT_DIR.parent / "clock"

RATIO_CSV = OUT_DIR / "ratio_17seg.csv"
RATIO_SUMMARY = OUT_DIR / "ratio_17seg_summary.csv"
TIDE_CSV = CLOCK_DIR / "clock_tidal_shift.csv"
BATCH_CSV = CLOCK_DIR / "segment_analysis" / "batch_summary.csv"
AGG_CSV = CLOCK_DIR / "segment_analysis" / "batch_aggregate.csv"
CORR_CSV = OUT_DIR / "correlation_reanalysis.csv"


def _table(rows: list[dict], path: Path) -> list[dict]:
    return list(csv.DictReader(open(path)))


def _metric(rows: list[dict], name: str) -> str:
    for r in rows:
        if r["metric"] == name:
            return r["value"]
    raise KeyError(name)


def _fmt_e18(x: float) -> str:
    return f"{x:+.3f}"


def main() -> int:
    ratio = _table([], RATIO_CSV)
    ratio_sum = _table([], RATIO_SUMMARY)
    tide = _table([], TIDE_CSV)
    batch = _table([], BATCH_CSV)
    agg = _table([], AGG_CSV)
    corr = _table([], CORR_CSV)

    # headlin numbers
    R_ref = ratio[0]["YbSr_R"]
    R_ref_dec = Decimal(R_ref)
    R_ref_18 = str(R_ref_dec)[:20]  # ~1.20750703934333772
    WLS = "1.2075070393433377213"
    d_ref = (R_ref_dec - Decimal(WLS)) * Decimal("1e18")

    agg = {r["metric"]: r["value"] for r in agg}
    corr = {r["metric"]: r["value"] for r in corr}

    n = len(ratio)
    y_i = [float(r["y_i_1e18"]) for r in ratio]
    y_min, y_max = min(y_i), max(y_i)
    n_valid = [int(r["n_valid"]) for r in ratio]
    total_s = sum(n_valid)

    A = float(agg["amplitude_A"])
    uA = float(agg["amplitude_uA"])
    zagn = float(agg["stouffer_z_agn"])
    p_agn = float(agg["stouffer_p_agn"])
    neg = int(agg["negative_r_segments"])

    pear_r = float(corr["pearson_r"])
    pear_p = float(corr["pearson_p"])
    rho = float(corr["spearman_rho"])
    rho_p = float(corr["spearman_p"])
    w_mean_yi = float(corr["weighted_mean_yi_1e18"])
    w_mean_dff = float(corr["weighted_mean_dff_1e18"])

    L = []
    L.append("# 武汉—上海光钟比对实验报告")
    L.append("")
    L.append("> **Yb/Sr 钟比值计算 · 潮汐修正 · 相关性分析**（自动生成）")
    L.append(">")
    L.append(f"> **钟比值结果（本报告）**：Yb/Sr = **{R_ref_18}**")
    L.append(f"> （R_ref = `{R_ref}`；与实验方 WLS 差 {d_ref:+.3f}×10⁻¹⁸）。")
    L.append(">")
    L.append(f"> 数据时间跨度：{ratio[0]['t_start_beijing'][:16]} 至 "
             f"{ratio[-1]['t_end_beijing'][:16]}（北京时间 UTC+8），共 {n} 段无跳点数据，")
    L.append(f"> 总有效时长 {total_s:,} s ≈ {total_s/3600:.2f} h。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 摘要")
    L.append("")
    L.append(f"1. **钟比值**：R_ref = `{R_ref_18}`，与实验方 WLS `{WLS}(23)` 差 "
             f"**{d_ref:+.2f}×10⁻¹⁸**。逐段 y_i ∈ [{y_min:.1f}, {y_max:.1f}]×10⁻¹⁸。")
    L.append(f"2. **段内分析跨段合并（核心检出）**：{neg}/17 段同号，符号无关 Stouffer "
             f"|z| = **{zagn:.2f}**（p = {p_agn:.1e}），幅度比 **A = {A:+.2f}±{uA:.2f}**"
             f"（{abs(A)/uA:.1f}σ），潮汐以正确方向、约一半幅度被检出。")
    L.append(f"3. **段均值相关**：y_i 与会话潮汐频移 Δf/f 正相关，Pearson r = "
             f"**{pear_r:+.3f}**（p = {pear_p:.3f}），Spearman ρ = {rho:+.3f}（p = {rho_p:.3f}）。")
    L.append(f"4. **整体均值与修正量**：y_i 时长加权均值 = **{w_mean_yi:+.3f}×10⁻¹⁸**，"
             f"整体潮汐修正量（时长加权 Δf/f）= **{w_mean_dff:+.3f}×10⁻¹⁸**。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 1. 数据与方法")
    L.append("")
    L.append("17 段无跳点数据段（北京时 UTC+8，含端点筛选）：")
    L.append("")
    L.append("| 段 | 开始 | 结束 | 有效点数 n | 段 | 开始 | 结束 | 有效点数 n |")
    L.append("|---|---|---|---|---|---|---|---|")
    half = (n + 1) // 2
    for i in range(half):
        j = i + half
        left = ratio[i]
        if j < n:
            right = ratio[j]
            L.append(f"| {left['group']} | {left['t_start_beijing'][5:16]} | "
                     f"{left['t_end_beijing'][5:16]} | {left['n_valid']} | "
                     f"{right['group']} | {right['t_start_beijing'][5:16]} | "
                     f"{right['t_end_beijing'][5:16]} | {right['n_valid']} |")
        else:
            L.append(f"| {left['group']} | {left['t_start_beijing'][5:16]} | "
                     f"{left['t_end_beijing'][5:16]} | {left['n_valid']} | | | | |")
    L.append("")
    L.append("> 参数（段窗口、扣除区间、常数、shift_a 分量）在 `clock/params.json`，")
    L.append("> 说明见 `clock/PARAMS.md`。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 2. 钟比值计算结果")
    L.append("")
    L.append(f"R_ref（段 1 Yb/Sr）= `{R_ref}`")
    L.append("")
    L.append("![17 段钟比值偏差](ratio_segments.png)")
    L.append("")
    L.append("| 段 | y_i (×10⁻¹⁸) | 段 | y_i (×10⁻¹⁸) |")
    L.append("|---|---|---|---|")
    for i in range(half):
        j = i + half
        left = ratio[i]
        if j < n:
            right = ratio[j]
            L.append(f"| {left['group']} | {_fmt_e18(float(left['y_i_1e18']))} | "
                     f"{right['group']} | {_fmt_e18(float(right['y_i_1e18']))} |")
        else:
            L.append(f"| {left['group']} | {_fmt_e18(float(left['y_i_1e18']))} | | |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 3. 段内相关性分析（1200-s 窗拟合）")
    L.append("")
    L.append("逐段幅度比 A（`beat = A·tide + noise`）：")
    L.append("")
    L.append("| 组 | 时长 h | A | u_A | r | p |")
    L.append("|---|---|---|---|---|---|")
    for r in batch:
        L.append(f"| {r['group']} | {float(r['hours']):.1f} | {float(r['A']):+.2f} | "
                 f"{float(r['u_A']):.2f} | {float(r['r']):+.3f} | {float(r['p']):.3f} |")
    L.append("")
    L.append(f"**跨段合并**：{neg}/17 段同号（二项 p={float(agg['binomial_p']):.4f}），")
    L.append(f"符号无关 Stouffer |z|={zagn:.2f}（p={p_agn:.1e}），"
             f"幅度比 A = {A:+.2f}±{uA:.2f}（{abs(A)/uA:.1f}σ）。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 4. 段均值相关性分析")
    L.append("")
    L.append("![钟比值偏差 vs 会话潮汐频移](correlation_reanalysis.png)")
    L.append("")
    L.append("| 统计量 | 数值 |")
    L.append("|---|---|")
    L.append(f"| Pearson r | {pear_r:+.3f}（p = {pear_p:.3f}） |")
    L.append(f"| Spearman ρ | {rho:+.3f}（p = {rho_p:.3f}） |")
    L.append(f"| y_i 时长加权均值 | {w_mean_yi:+.3f}×10⁻¹⁸ |")
    L.append(f"| 整体潮汐修正量 Δf/f | {w_mean_dff:+.3f}×10⁻¹⁸ |")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 5. 结论")
    L.append("")
    L.append("| 维度 | 结果 |")
    L.append("|---|---|")
    L.append(f"| 钟比值中心值 | R_ref = {R_ref_18}，与实验方 WLS 差 {d_ref:+.2f}×10⁻¹⁸ |")
    L.append(f"| 段内跨段合并 | {neg}/17 同号，Stouffer \\|z\\|={zagn:.2f}（p={p_agn:.1e}），A={A:+.2f}±{uA:.2f} |")
    L.append(f"| 段均值相关性 | Pearson r = {pear_r:+.3f}（p={pear_p:.3f}） |")
    L.append(f"| 整体修正量 | Δf/f = {w_mean_dff:+.3f}×10⁻¹⁸ |")
    L.append("")
    L.append("> 详细方法见 [docs/WORKFLOW.md](../docs/WORKFLOW.md)、"
             "[docs/NOTATION.md](../docs/NOTATION.md)。")
    L.append("")

    out = OUT_DIR / "EXPERIMENT_REPORT.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
