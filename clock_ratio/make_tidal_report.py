#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2", "typer"]
# ///
# How to run (existing environment; no installs needed):
#   python clock_ratio/make_tidal_report.py [--input-dir /independent/artifacts]
"""Render only tidal_correction/REPORT.md from validated existing CSV/JSON files."""
from __future__ import annotations

import sys
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from pathlib import Path
from typing import Annotated, Final

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock_ratio.tidal_report_data import (
    SCENARIOS, ReportData, ReportError, read_report,
)

DEFAULT_INPUT: Final = Path(__file__).resolve().parent / "tidal_correction"
app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)

METHODS: Final = """## 1. 方法与解释边界

- 三个情景使用完全相同的原始保留样本与 n_valid 权重。沿用原始数据的段窗口、扣除区间、跳点筛选、最长有效段及两端筛选；修正后不重新筛选。实际保留起止时间见 ratio_scenarios.csv，不能用旧报告的窗口端点代替。
- 原始北京时间减 8 小时得到 UTC（time offset = minus8）。30 s 潮汐网格线性插值到保留样本；不外推、不钳位，也不跨越缺失的潮汐网格间隔。
- ΔW = W(武汉) − W(上海)，单位 m²/s²。未去均值的拍频模板为 h = F_1550·ΔW/c²；使用 1550 nm 传递光频，而非 1/COEF。mean_dff = mean(h)/F_1550 是潮汐 ΔW/c²，不等于完整钟比值归一化后的变化。
- A 是响应系数：b_raw = noise + A·h；修正为 **b_corr = b_raw − A·h**。负系数意味着加回对应倍数的未去均值模板，不是减去正模板。raw 的 A=0；theory 的 A=−1；empirical 的 A=−0.54，均为固定情景，本次不重新拟合。
- **附加假设**：A=−0.54 来自历史去均值波形幅度的情景转用；把该幅度用于未去均值模板的 DC（均值）部分，是额外假设，并非波形拟合已经验证的结论。历史文档的硬件符号尚未解决；这里固定负号是用户指定的约定，不是新验证的硬件极性。
- 均值沿用旧基线的 float64 原始拍频均值，经 repr 转 Decimal；潮汐均值同样转换。以 Decimal80 计算 mean_dm_corr = mean_raw_dec − m_dec − A·mean_h_dec，再经完整 full_ratio 公式（包含静态引力项及原有系统频移项）反演 R。不是先给约 33 MHz 的 float64 拍频加微小修正再求均值，也不是瞬时 R 的平均；Decimal 不恢复已损失的原始均值量化精度。
- 稳定度使用相同的 raw 段比值 R0 作为三情景参考，按完整比值映射构造 y = −q/(1+q)，q = (K/S0)·[(b−mean_raw)−A·h]，S0=(1+DELTA_G)/R0；K 的完整定义见 summary.json。OADEV 是该无量纲 y 的稳定度，不是 ΔR 的不确定度。
- 新 OADEV 对每个连续 1 s 原始数据片段，使用全部重叠相邻 m 点均值差，起点 i=0,…,N_run−2m，σ_y = sqrt[Σ_runs Σ_i (ȳ_(i+m)−ȳ_i)²/(2·n_pairs)]。不跨间断、不跨组拼接；重复时间戳也断开。仅为前缀和做数值中心化，不去趋势、不对潮汐去均值；n_pairs 是重叠对数，不是独立自由度。
- τ 网格为二进制秒数并加入 600、1200、3600、7200 s，上限为各段最长连续原始片段长度的 1/4。三情景网格相同；超出上限的长 τ 记 **—**，绝不填零。raw OADEV 为零或不可用时，倍数也记 **—**。
- **没有传播系数、潮汐模型或系统项的不确定度**；未构造 SEM、未进行 WLS 合并、未给出误差棒或显著性检验。OADEV/样本标准差不是 SEM。倍数小于 1 只描述此固定情景下 OADEV 数值较低，不证明统计显著，也不证明准确度提高。
- 历史 [statistical_methods.oadev](../statistical_methods.py) 虽名为 oadev，实际使用不重叠块均值及其相邻差；该实现与旧输出保持不变。本报告不把旧算法数值与新 OADEV 作直接“改善”比较，所有 corrected/raw 倍数均来自同一新算法。
"""


def format_ratio(value: Decimal) -> str:
    """Round the original Decimal to 22 fractional digits, never via float/slicing."""
    with localcontext() as context:
        context.prec = 80
        return format(value.quantize(Decimal("1e-22"), rounding=ROUND_HALF_EVEN), ".22f")


def stability_table(data: ReportData, tau: int) -> str:
    """Include every group, explicitly marking unavailable long-tau entries."""
    points = {(row.scenario, row.group): row for row in data.stability if row.tau_s == tau}
    lines = [f"### τ = {tau} s", "", "| 组 | raw σ_y | theory σ_y | empirical σ_y | theory/raw | empirical/raw |", "|---|---|---|---|---|---|"]
    for group in data.groups:
        triplet = [points.get((name, group)) for name in SCENARIOS]
        sigma = [f"{row.sigma_y:.6e}" if row is not None and row.sigma_y is not None else "—" for row in triplet]
        factors = [f"{row.sigma_factor_vs_raw:.6f}" if row is not None and row.sigma_factor_vs_raw is not None else "—" for row in triplet[1:]]
        lines.append("| " + " | ".join([str(group), *sigma, *factors]) + " |")
    return "\n".join(lines) + "\n"


def render_report(data: ReportData) -> str:
    """Pure Chinese Markdown rendering; all result numbers originate in parsed artifacts."""
    raw = data.summary.scenarios["raw"]
    lines = [
        "# 潮汐修正独立比较报告", "",
        "> 本报告由现有三份 CSV/JSON 自动生成，只作固定系数情景比较；不替代[旧基线报告](../EXPERIMENT_REPORT.md)。科学解释及符号假设仍需研究者确认。", "",
        f"三情景均为 {raw.nsegments} 组、{raw.total_samples:,} 个保留样本，有效加权时长 {raw.duration_s:,} s（每样本 1 s；不把间断计入权重）。", "",
        METHODS,
        "## 2. 时长加权钟比值", "",
        "R_duration = Σ(n_valid_i·R_i)/Σn_valid_i；三情景使用相同权重，不是 WLS。", "",
        "R 统一直接从 Decimal 按 ROUND_HALF_EVEN 舍入到小数点后 22 位；不是字符串截断，也不表示 22 位测量准确度。全精度中心值见 [summary.json](summary.json)，逐组全精度值见 [ratio_scenarios.csv](ratio_scenarios.csv)。", "",
        "**绝对比值差** ΔR = R − R_raw（带符号，非取绝对值）；表中列为 delta_R×10¹⁸。**分数变化** delta_fractional_1e18 = (R/R_raw − 1)×10¹⁸。两者分母不同，不可混用，也不是 mean_dff_1e18。", "",
        "| 情景 | A | R_duration | ΔR×10¹⁸（绝对比值差） | (R/R_raw−1)×10¹⁸（分数变化） |",
        "|---|---|---|---|---|",
    ]
    with localcontext() as context:
        context.prec = 80
        for name in SCENARIOS:
            center = data.summary.scenarios[name]
            lines.append(f"| {name} | {center.coefficient} | {format_ratio(center.R_duration)} | {center.delta_R * Decimal('1e18'):+.6f} | {center.delta_fractional_1e18:+.6f} |")
    lines.extend([
        "", "## 3. 逐组比值及相对 raw 的分数变化", "",
        "后三列均为各组 (R_scenario/R_raw−1)×10¹⁸，不是相对第一组。", "",
        "| 组 | n_valid | raw R | theory R | empirical R | raw 分数变化 | theory 分数变化 | empirical 分数变化 |",
        "|---|---|---|---|---|---|---|---|",
    ])
    rows = {(row.scenario, row.group): row for row in data.ratios}
    for group in data.groups:
        triplet = [rows[(name, group)] for name in SCENARIOS]
        ratios = [format_ratio(row.R) for row in triplet]
        changes = [f"{row.delta_fractional_1e18:+.6f}" for row in triplet]
        lines.append("| " + " | ".join([str(group), str(triplet[0].n_valid), *ratios, *changes]) + " |")
    lines.extend([
        "", "## 4. 逐组 OADEV（无量纲）", "",
        "数值及 corrected/raw 倍数来自 [stability.csv](stability.csv)，比较的是相同 τ、相同保留样本。倍数保留 6 位小数；分类使用未舍入值。— 表示该 τ 不可用或倍数无定义，不表示零稳定度。", "",
        stability_table(data, 1200), stability_table(data, 7200),
        "## 5. 共同 τ 的描述性计数", "",
        "每个情景/τ 的分母仅为该 τ 上 raw 和 corrected 均可用且 raw>0 的合格组；不把未提供长 τ 的组计入分母。范围为合格组的 corrected/raw 最小值–最大值，没有跨组拟合或显著性推断。", "",
        "| τ (s) | 情景 | 合格组数 | 倍数 < 1 | 倍数 ≥ 1 | 倍数范围 |",
        "|---|---|---|---|---|---|",
    ])
    for tau in (1200, 3600, 7200):
        for name in SCENARIOS[1:]:
            factors = [row.sigma_factor_vs_raw for row in data.stability if row.tau_s == tau and row.scenario == name and row.sigma_factor_vs_raw is not None]
            lower = sum(value < 1 for value in factors)
            extent = f"{min(factors):.6f}–{max(factors):.6f}" if factors else "—"
            lines.append(f"| {tau} | {name} | {len(factors)} | {lower} | {len(factors) - lower} | {extent} |")
    lines.extend([
        "", "## 6. 来源与复现", "",
        "- 数值证据：[summary.json](summary.json)（scenarios 与处理约定）、[ratio_scenarios.csv](ratio_scenarios.csv)（逐组数据）、[stability.csv](stability.csv)（全部 τ 与 n_pairs）。",
        "- 分析代码：[tidal_correction.py](../tidal_correction.py)、[tidal_analysis.py](../tidal_analysis.py)、[tidal_stability.py](../tidal_stability.py)。",
        "- 报告代码：[make_tidal_report.py](../make_tidal_report.py)、[tidal_report_data.py](../tidal_report_data.py)；旧硬件符号讨论：[SIGN_COEFFICIENT_ANALYSIS.md](../../clock/SIGN_COEFFICIENT_ANALYSIS.md)。", "",
        "在仓库根目录仅重建本报告（不重算分析、不修改源 CSV/JSON 或旧报告）：", "",
        "```bash", "python clock_ratio/make_tidal_report.py", "```", "",
        "需要重新分析原始数据并生成本报告时：", "",
        "```bash", "python run_all.py --tidal-only", "```", "",
        "读取器先检查三情景、组数、权重、Decimal 中心/变化量以及 OADEV 网格/倍数的一致性；源文件缺失或冲突则非零退出，不生成混合报告。tidal-only 模式在任一步失败时停止，避免随后用旧结果生成报告。三个源文件没有共同运行 ID/内容指纹，因此一致性检查不是对原始测量数据或同次运行来源的独立认证。", "",
    ])
    return "\n".join(lines)


@app.command()
def main(input_dir: Annotated[Path, typer.Option(help="Directory containing all three tidal artifacts.")] = DEFAULT_INPUT) -> None:
    """Generate the independent report only; never execute analysis or legacy reporting."""
    try:
        text = render_report(read_report(input_dir))
        target = input_dir / "REPORT.md"
        if target.is_symlink() or (target.exists() and (not target.is_file() or target.stat().st_nlink > 1)):
            raise ReportError(f"report destination must be an independent regular file: {target}")
        target.write_text(text, encoding="utf-8")
    except (ReportError, OSError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote {target}")


if __name__ == "__main__":
    app()
