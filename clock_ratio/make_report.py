#!/usr/bin/env python3
"""Auto-generate the authoritative experiment report (EXPERIMENT_REPORT.md).

Reads the CSVs produced by the analysis pipeline and renders a complete Markdown
report with all headline numbers, tables, and figure references. Run after
run_all.py (or after the analysis steps) to refresh the report from data.

Outputs: clock_ratio/EXPERIMENT_REPORT.md
"""

from __future__ import annotations

import csv
import json
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
CORR_TW_CSV = OUT_DIR / "correlation_reanalysis_timeweighted.csv"
STAT_JSON = OUT_DIR / "statistical_methods.json"


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
    corr_tw = _table([], CORR_TW_CSV)
    stat = json.load(open(STAT_JSON)) if STAT_JSON.exists() else None

    # headline numbers: segment-1 baseline vs duration-weighted experiment value
    ratio_sum_map = {r["field"]: r["value"] for r in ratio_sum}
    R_seg1 = ratio_sum_map["R_seg1"]
    R_duration = ratio_sum_map["R_duration"]
    y_duration = float(ratio_sum_map["y_duration_1e18"])
    R_seg1_dec = Decimal(R_seg1)
    R_duration_dec = Decimal(R_duration)
    R_duration_18 = str(R_duration_dec)[:23]  # 23 chars ≈ 21 decimal digits, enough to resolve +.2f (0.01e-18) diffs
    NIST = Decimal(ratio_sum_map["NIST_reference"])
    WLS = "1.2075070393433377213"
    d_dur_nist = (R_duration_dec - NIST) * Decimal("1e18")
    d_dur_wls = (R_duration_dec - Decimal(WLS)) * Decimal("1e18")

    agg = {r["metric"]: r["value"] for r in agg}
    corr = {r["metric"]: r["value"] for r in corr}
    corr_tw = {r["metric"]: r["value"] for r in corr_tw}

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

    tw_r = float(corr_tw["weighted_pearson_r"])
    tw_r_p = float(corr_tw["weighted_pearson_p"])
    tw_rho = float(corr_tw["weighted_spearman_rho"])
    tw_rho_p = float(corr_tw["weighted_spearman_p"])
    tw_neff = float(corr_tw["n_eff"])
    tw_slope = float(corr_tw["wls_slope"])
    tw_slope_se = float(corr_tw["wls_slope_se"])

    L = []
    L.append("# 武汉—上海光钟比对实验报告")
    L.append("")
    L.append("> **导航**：本报告的时长加权钟比值保留未做潮汐修正的旧基线；raw / theory / empirical 的独立潮汐修正比较见新[报告](tidal_correction/REPORT.md)。")
    L.append("")
    L.append("> **Yb/Sr 钟比值计算 · 潮汐修正 · 相关性分析**（自动生成）")
    L.append(">")
    L.append(f"> **整个实验的 Yb/Sr 值（时长加权中心值）**：**{R_duration_18}**"
             f"（R_duration = `{R_duration}`）。")
    L.append(f"> 与 NIST 参考 `{ratio_sum_map['NIST_reference']}(37)` 差 {d_dur_nist:+.3f}×10⁻¹⁸，")
    L.append(f"> 与实验方 WLS `{WLS}(23)` 差 {d_dur_wls:+.3f}×10⁻¹⁸。")
    L.append(f"> （注：R_seg1 = 段 1 的值 `{R_seg1}`，仅作 y_i 相对基准，非整个实验值。）")
    L.append(">")
    L.append(f"> 数据时间跨度：{ratio[0]['t_start_beijing'][:16]} 至 "
             f"{ratio[-1]['t_end_beijing'][:16]}（北京时间 UTC+8），共 {n} 段无跳点数据，")
    L.append(f"> 总有效时长 {total_s:,} s ≈ {total_s/3600:.2f} h。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 摘要")
    L.append("")
    L.append(f"1. **整个实验的钟比值（时长加权中心值）**：R_duration = `{R_duration_18}`，与 NIST "
             f"`{ratio_sum_map['NIST_reference']}(37)` 差 {d_dur_nist:+.2f}×10⁻¹⁸，与实验方 WLS "
             f"`{WLS}(23)` 差 {d_dur_wls:+.2f}×10⁻¹⁸。逐段 y_i ∈ [{y_min:.1f}, {y_max:.1f}]×10⁻¹⁸。")
    L.append(f"2. **段内分析跨段合并（核心检出）**：{neg}/17 段同号，符号无关 Stouffer "
             f"|z| = **{zagn:.2f}**（p = {p_agn:.1e}），幅度比 **A = {A:+.2f}±{uA:.2f}**"
             f"（{abs(A)/uA:.1f}σ），潮汐以正确方向、约一半幅度被检出。")
    L.append(f"3. **段均值相关**：y_i 与会话潮汐频移 Δf/f 正相关，段等权重 Pearson r = "
             f"**{pear_r:+.3f}**（p = {pear_p:.3f}），Spearman ρ = {rho:+.3f}（p = {rho_p:.3f}）；"
             f"时间等权重（时长加权）Pearson r = {tw_r:+.3f}（p = {tw_r_p:.3f}，n_eff = {tw_neff:.1f}）。")
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
    L.append("会话潮汐引力红移频移 Δf/f（专业综合差 → ΔW/c²）：")
    L.append("")
    L.append("![会话潮汐引力红移频移](../clock/clock_tidal_shift.png)")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 2. 钟比值计算结果")
    L.append("")
    L.append(f"整个实验的 Yb/Sr 值（17 段时长加权中心值）：R_duration = `{R_duration}`")
    L.append("")
    L.append(f"第 1 段钟比值（仅作 y_i 相对基准）：R_seg1 = `{R_seg1}`")
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
    L.append("![逐段幅度比 A 森林图](../clock/segment_analysis/batch_forest.png)")
    L.append("")
    L.append("![逐段拍频 vs 潮汐共享轴](../clock/segment_analysis/batch_shared_axis.png)")
    L.append("")
    L.append(f"**跨段合并**：{neg}/17 段同号（二项 p={float(agg['binomial_p']):.4f}），")
    L.append(f"符号无关 Stouffer |z|={zagn:.2f}（p={p_agn:.1e}），"
             f"幅度比 A = {A:+.2f}±{uA:.2f}（{abs(A)/uA:.1f}σ）。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 4. 段均值相关性分析")
    L.append("")
    L.append("### 4.1 单段等权重（每段权重相同）")
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
    L.append("### 4.2 时间等权重（每秒有效数据权重相同，权重 = 段有效时长）")
    L.append("")
    L.append("> 原始逐秒数据不在库内，以各段有效时长 n_valid 作为简单时间权重"
             "（w_i = n_valid_i / Σn_valid），相关性 p 值用 Kish 有效样本量 "
             "n_eff = (Σw)²/Σw² 折算。")
    L.append("")
    L.append("![钟比值偏差 vs 会话潮汐频移（时间等权重）](correlation_reanalysis_timeweighted.png)")
    L.append("")
    L.append("| 统计量 | 数值 |")
    L.append("|---|---|")
    L.append(f"| 时长加权 Pearson r | {tw_r:+.3f}（p = {tw_r_p:.3f}，n_eff = {tw_neff:.1f}） |")
    L.append(f"| 时长加权 Spearman ρ | {tw_rho:+.3f}（p = {tw_rho_p:.3f}） |")
    L.append(f"| WLS 斜率 | {tw_slope:+.3f} ± {tw_slope_se:.3f} |")
    L.append("")
    L.append("> 时间等权重后长段（如段 13、16）权重上升，相关性从段等权重的 "
             f"r = {pear_r:+.3f}（p = {pear_p:.3f}）降为 r = {tw_r:+.3f}"
             f"（p = {tw_r_p:.3f}），不再显著——正相关主要由较短段贡献。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 5. 结论")
    L.append("")
    L.append("| 维度 | 结果 |")
    L.append("|---|---|")
    L.append(f"| 整个实验 Yb/Sr 值 | R_duration = {R_duration_18}，与实验方 WLS 差 {d_dur_wls:+.2f}×10⁻¹⁸ |")
    L.append(f"| 段内跨段合并 | {neg}/17 同号，Stouffer \\|z\\|={zagn:.2f}（p={p_agn:.1e}），A={A:+.2f}±{uA:.2f} |")
    L.append(f"| 段均值相关性 | 段等权重 Pearson r = {pear_r:+.3f}（p={pear_p:.3f}）；"
             f"时间等权重 r = {tw_r:+.3f}（p={tw_r_p:.3f}） |")
    L.append(f"| 整体修正量 | Δf/f = {w_mean_dff:+.3f}×10⁻¹⁸ |")
    L.append("")
    L.append("> 详细方法见 [docs/WORKFLOW.md](../docs/WORKFLOW.md)、"
             "[docs/NOTATION.md](../docs/NOTATION.md)。")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## 附录：单段诊断与变体分析")
    L.append("")
    L.append("### 单段诊断（段 13 / 段 6）")
    L.append("")
    L.append("![段 13 多 τ 相关 + lag sweep](../clock/segment13_correlation.png)")
    L.append("")
    L.append("![段 13 三角窗拟合共享轴](../clock/segment_analysis/segment13_shared_axis.png)")
    L.append("")
    L.append("![段 6 三角窗拟合共享轴](../clock/segment_analysis/segment6_shared_axis.png)")
    L.append("")
    L.append("### 变体分析（积分尺度稳健性）")
    L.append("")
    L.append("![变体 1（潮汐 30s 原生）森林图](../clock/segment_analysis/variant1_30s_tide_forest.png)")
    L.append("")
    L.append("![变体 2（30s 均值聚合）森林图](../clock/segment_analysis/variant30s_forest.png)")
    L.append("")

    # ---- parallel paper-method results (OADEV + WLS/Birge/MP/Bayesian) ----
    if stat is not None:
        L.append("---")
        L.append("")
        L.append("## 6. 论文统计分析方法（并列结果，非替代）")
        L.append("")
        L.append("按实验方 PDF 的统计处理（每段 OADEV 外推 → 统计不确定度 u_i → "
                 "WLS / Birge / M-P / 贝叶斯四种方法合并），作用于与 `compute_ratio.py` "
                 "相同的逐段拍频数据。**与前述时间等权重结果并列，不替代。**")
        L.append("")
        L.append(f"每段 OADEV 外推得到的统计不确定度 u_i 与四种合并结果（"
                 f"`statistical_methods.json`）。**钟比值与对应的引力（潮汐）修正量"
                 f"逐方法配对**：")
        L.append("")
        L.append("| 方法 | Yb/Sr 中心值 | 统计不确定度 u | 引力（潮汐）修正量 Δf/f |")
        L.append("|---|---|---|---|")
        L.append(f"| WLS（1/u_i²） | {stat['R_wls'][:23]} | {stat['u_wls']:.3e} | {stat['grav_wls']:+.3e} |")
        L.append(f"| Birge（B={stat['birge_ratio']:.3f}，1/u_i²） | {stat['R_wls'][:23]} | {stat['u_birge']:.3e} | {stat['grav_birge']:+.3e} |")
        L.append(f"| Mandel-Paule（ξ={stat['xi_mp']:.3e}，1/(u_i²+ξ²)） | {stat['R_mp'][:23]} | {stat['u_mp']:.3e} | {stat['grav_mp']:+.3e} |")
        L.append(f"| 贝叶斯（ξ={stat['xi_bayes']:.3e}） | {stat['R_bayes'][:23]} | {stat['u_stat_bayes']:.3e} | {stat['grav_bayes']:+.3e} |")
        L.append("")
        L.append(f"WLS 拟合度：χ² = {stat['chi2']:.2f}（dof={stat['dof']}，"
                 f"χ²_red = {stat['chi2_red']:.2f}，p = {stat['p_chi2']:.2e}）。")
        L.append("")
        L.append("> **口径说明（经过独立对抗审查）**：本套每段统计不确定度 u_i 由 OADEV 外推"
                 "得到（拍频归一化到 1550 nm 光频，128s≤τ≤T/4 拟合斜率外推到 Teff）。"
                 "审查结论：拍频数据在 τ≳4096 s 出现低频平台（真实的 flicker 频率噪声地板，"
                 "来自时钟/链路，**不是潮汐**——潮汐应在 τ≈2–4e4 s 表现为幅度 ~1e-17 的"
                 "凸起，远小于 u_i 且 τ 特征不符）。该 flicker 地板使白噪声斜率外推对"
                 "**所有段系统性低估 u_i 约 30–40%**（而非「短段偏高、长段偏低」），这会把"
                 " χ²_red 推高到 ~3.5–4。但 χ²_red≈5.4 的**剩余部分**来自个别段的 u_i 本身"
                 "不可靠（尤其段 5、6、16，u_i 极差约 18 倍，远超白噪声+flicker 应有的"
                 "≤2.8 倍），需逐段复核原始数据与 OADEV 曲线，而非外推偏移。故本并列"
                 "结果的 u_i 与四种合并值在当前 OADEV 外推下**不可靠**，仅作方法演示，"
                 "待正确估计 u_i 后重算。")
        L.append("")

    out = OUT_DIR / "EXPERIMENT_REPORT.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
