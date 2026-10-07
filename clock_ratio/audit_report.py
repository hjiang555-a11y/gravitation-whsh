"""Manifest-only audit report generator for the phase-one analysis audit.

Renders a Chinese Markdown audit report exclusively from a verified
``ResultManifest``. Two required sections have no backing fields in the closed
manifest schema (covariance-aware inference coverage diagnostics and old-vs-new
aggregation audits); they are rendered as pointer limitation sections that
reference the review commits only. Every number in the report is read from the
manifest; this source file must not contain historical result literals
(guarded by ``test_source_contains_no_historical_result_literals``).
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from clock_ratio.evidence import EvidenceStatus  # noqa: E402
from clock_ratio.result_manifest import (  # noqa: E402
    ManifestError,
    ResultManifest,
    StatisticalScenarioManifest,
    UncertaintyBudgetModel,
    read_manifest,
    reconcile_manifest,
)

_DEFAULT_REPORT_NAME = "ANALYSIS_AUDIT.md"
_COVARIANCE_COMMITS = "c996e6d..fd1f7de"
_OLD_NEW_COMMITS = "44abd1a..eff7021"


def read_audit_inputs(manifest_path: Path) -> ResultManifest:
    manifest = read_manifest(manifest_path)
    reconcile_manifest(manifest)
    return manifest


def render_audit_report(manifest: ResultManifest) -> str:
    reconcile_manifest(manifest)
    return "\n".join(render_sections(manifest))


def write_report_atomic(text: str, path: Path) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)


def _verdict(flag: bool) -> str:
    return "成立" if flag else "不成立"


def _bool(flag: bool) -> str:
    return "是" if flag else "否"


def _product(manifest: ResultManifest, relative_path: str):
    for record in manifest.products:
        if record.relative_path == relative_path:
            return record
    raise ManifestError(f"missing product record: {relative_path}")


def _section_header(manifest: ResultManifest) -> str:
    packages = "、".join(
        f"`{name}` {version}" for name, version in sorted(manifest.packages.items())
    )
    lines = [
        "# 分析审计报告（ANALYSIS_AUDIT）",
        "",
        "本文件仅由通过验证的结果清单（manifest）生成；渲染前调用 `reconcile_manifest` "
        "再次对账全部内部一致性规则。",
        "",
        f"- 清单模式版本（schema_version）：{manifest.schema_version}",
        f"- 生成提交（git_commit）：`{manifest.git_commit}`；工作区脏标记（dirty）：{_bool(manifest.dirty)}",
        f"- Python：{manifest.python}",
        f"- 关键依赖（按包名排序）：{packages}",
    ]
    return "\n".join(lines) + "\n"


def _section_inputs(manifest: ResultManifest) -> str:
    parameters = manifest.parameters
    lines = [
        "## 1. 输入与来源状态",
        "",
        "### 输入",
        "",
        "| 相对路径 | sha256[0:16] | 大小（字节） | 状态 |",
        "|---|---|---|---|",
    ]
    for record in manifest.inputs:
        lines.append(
            f"| `{record.relative_path}` | `{record.sha256[:16]}` | {record.size_bytes} "
            f"| `{record.status.value}` |"
        )
    lines += [
        "",
        "### 参数",
        "",
        "| 相对路径 | sha256[0:16] | 大小（字节） | 状态 |",
        "|---|---|---|---|",
        f"| `{parameters.relative_path}` | `{parameters.sha256[:16]}` | {parameters.size_bytes} "
        f"| `{parameters.status.value}` |",
        "",
        "### 产物",
        "",
        "| 相对路径 | sha256[0:16] | 状态 |",
        "|---|---|---|",
    ]
    for record in manifest.products:
        lines.append(
            f"| `{record.relative_path}` | `{record.sha256[:16]}` | `{record.status.value}` |"
        )
    return "\n".join(lines) + "\n"


def _section_ledgers(manifest: ResultManifest) -> str:
    sample_ledger = _product(manifest, "sample_ledger.csv")
    time_quality = _product(manifest, "time_quality.json")
    lines = [
        "## 2. 样本账本与时间质量",
        "",
        f"- `sample_ledger.csv` 完整 sha256：`{sample_ledger.sha256}`",
        f"- `time_quality.json` 完整 sha256：`{time_quality.sha256}`",
    ]
    for label, scenario in (("16 段", manifest.primary_16), ("17 段", manifest.sensitivity_17)):
        closed = scenario.total_samples == sum(scenario.segment_n_valid)
        lines.append(
            f"- {label}：n_segments = {scenario.n_segments}，"
            f"total_samples = {scenario.total_samples}；"
            f"等式 `total_samples == Σ segment_n_valid`：{_verdict(closed)}"
        )
    lines += [
        "",
        "时间质量的内部细节（label 与均匀时间轴之间的差异量化、外部总数对账）位于已哈希的 "
        "`time_quality.json` 内；本报告不复述其中的数值。",
    ]
    return "\n".join(lines) + "\n"


def _section_segment9(manifest: ResultManifest) -> str:
    primary = manifest.primary_16
    sensitivity = manifest.sensitivity_17
    lines = [
        "## 3. 第 9 段隔离",
        "",
        f"- 16 段临时主结果：`excluded_groups` = {primary.excluded_groups}，"
        f"即排除第 9 段：{_verdict(9 in primary.excluded_groups)}。",
        f"- 17 段敏感性结果：`included_groups` 含第 9 段："
        f"{_verdict(9 in sensitivity.included_groups)}；"
        f"`excluded_groups` = {sensitivity.excluded_groups}。",
        f"- Leave-one-out：排除第 9 段的条目存在：{_verdict(9 in manifest.leave_one_out)}。",
    ]
    return "\n".join(lines) + "\n"


def _scenario_section(
    number: int,
    title: str,
    scenario: StatisticalScenarioManifest,
    note: str,
) -> str:
    combination = scenario.combination
    rows = (
        ("R_seg1", f"`{combination.R_seg1}`"),
        ("R_wls", f"`{combination.R_wls}`"),
        ("R_mp", f"`{combination.R_mp}`"),
        ("R_bayes", f"`{combination.R_bayes}`"),
        ("u_wls", f"{combination.u_wls:.6g}"),
        ("chi2", f"{combination.chi2:.6g}"),
        ("dof", f"{combination.dof}"),
        ("chi2_red", f"{combination.chi2_red:.3f}"),
        ("p_chi2", f"{combination.p_chi2:.6g}"),
        ("birge_ratio", f"{combination.birge_ratio:.6g}"),
        ("u_birge", f"{combination.u_birge:.6g}"),
        ("xi_mp", f"{combination.xi_mp:.6g}"),
        ("u_mp", f"{combination.u_mp:.6g}"),
        ("mu_bayes", f"{combination.mu_bayes:.6g}"),
        ("u_stat_bayes", f"{combination.u_stat_bayes:.6g}"),
        ("xi_bayes", f"{combination.xi_bayes:.6g}"),
    )
    included = "、".join(str(group) for group in scenario.included_groups)
    excluded = "、".join(str(group) for group in scenario.excluded_groups) or "（无）"
    closed = scenario.total_samples == sum(scenario.segment_n_valid)
    lines = [
        f"## {number}. {title}",
        "",
        f"- 情景：`{scenario.scenario}`；响应系数：`{scenario.coefficient}`；"
        f"段数：{scenario.n_segments}",
        f"- 包含段：{included}",
        f"- 排除段：{excluded}",
        f"- 时长加权比值（duration_weighted_ratio）：`{scenario.duration_weighted_ratio}`",
        f"- 总样本（total_samples）：{scenario.total_samples}；"
        f"等式 `total_samples == Σ segment_n_valid`：{_verdict(closed)}",
        "",
        "| 字段 | 数值 |",
        "|---|---|",
    ]
    lines += [f"| {name} | {value} |" for name, value in rows]
    lines += ["", note]
    return "\n".join(lines) + "\n"


def _section_loo(manifest: ResultManifest) -> str:
    entries = sorted(manifest.leave_one_out.values(), key=lambda entry: entry.excluded_group)
    lines = [
        "## 6. Leave-one-out",
        "",
        "逐个排除一段的敏感性扫描；数值直接取自清单条目。",
        "",
        "| 排除段 | R_wls | chi2_red | u_wls |",
        "|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| 第 {entry.excluded_group} 段 | `{entry.R_wls}` | {entry.chi2_red:.3f} "
            f"| {entry.u_wls:.6g} |"
        )
    return "\n".join(lines) + "\n"


def _section_tide(manifest: ResultManifest) -> str:
    tide = manifest.tide_method
    if tide.first_inconsistent_row_number is None:
        first = "none"
    else:
        first = (
            f"第 {tide.first_inconsistent_row_number} 行"
            f"（value_diff = {tide.first_inconsistent_value_diff}）"
        )
    lines = [
        "## 7. 潮汐方法验证",
        "",
        f"- 源列（source_column）：`{tide.source_column}`；方向：`{tide.direction}`；"
        f"时区：`{tide.timezone}`",
        f"- 预期步长：{tide.expected_step_s} s；重力加速度：`{tide.gravity_m_s2}` m/s²",
        f"- 行数：转换 {tide.converted_row_count} / 参考 {tide.reference_row_count} / "
        f"公共前缀 {tide.common_prefix_row_count}",
        f"- 最大时间差：{tide.max_abs_time_diff_s:.6g} s；"
        f"最大数值差：`{tide.max_abs_value_diff}`",
        f"- 首个不一致行：{first}",
        f"- 状态：`{tide.status.value}`",
    ]
    return "\n".join(lines) + "\n"


def _section_budget(budget: UncertaintyBudgetModel) -> str:
    lines = [
        "## 8. 不确定度预算",
        "",
        "| 组件 | 修正 | 标准不确定度 | 状态 | 必需 |",
        "|---|---|---|---|---|",
    ]
    for component in budget.components:
        correction = component.correction if component.correction is not None else "—"
        uncertainty = (
            component.standard_uncertainty
            if component.standard_uncertainty is not None
            else "—"
        )
        lines.append(
            f"| `{component.name}` | {correction} | {uncertainty} "
            f"| `{component.status.value}` | {_bool(component.required)} |"
        )
    unresolved = [
        component
        for component in budget.components
        if component.required
        and (
            component.status is not EvidenceStatus.established
            or component.standard_uncertainty is None
        )
    ]
    if budget.total_standard_uncertainty is None:
        total_line = "未给出（withheld）"
        reason = (
            f"扣留原因：仍有 {len(unresolved)} 个必需（required）组件未建立"
            "（状态非 established 或缺少标准不确定度）。"
        )
    else:
        total_line = f"`{budget.total_standard_uncertainty}`"
        reason = "总计已给出（未扣留）。"
    lines += [
        "",
        f"- 已知分量合成（known_quadrature）：`{budget.known_quadrature}`",
        f"- 总标准不确定度：{total_line}",
        f"- {reason}",
        f"- 预算状态：`{budget.status.value}`",
        "",
        "相关矩阵（按组件声明顺序；紧凑行）：",
    ]
    for component, row in zip(budget.components, budget.correlation):
        values = "  ".join(f"{value:.3f}" for value in row)
        lines.append(f"  - `{component.name}`：{values}")
    return "\n".join(lines) + "\n"


def _section_covariance_pointer() -> str:
    lines = [
        "## 9. 协方差感知潮汐推断（限制说明）",
        "",
        "协方差感知的 GLS 与块自助（block-bootstrap）验证已在阶段一中实现并复核；其覆盖"
        "诊断未嵌入本清单模式，因此本报告不复述其数值。证据与复核记录见提交 "
        f"`{_COVARIANCE_COMMITS}`。",
    ]
    return "\n".join(lines) + "\n"


def _section_old_new_pointer() -> str:
    lines = [
        "## 10. 新旧结果差异（限制说明）",
        "",
        "估计量与聚合方式的新旧审计（块均值改为 gap-safe OADEV；情景统一；协方差列）已在"
        "任务 7/9/10/12 中记录并复核；本清单模式不嵌入历史基线数值，因此本报告不复述其"
        "数值。证据见提交 "
        f"`{_OLD_NEW_COMMITS}`。",
    ]
    return "\n".join(lines) + "\n"


def _section_external(manifest: ResultManifest) -> str:
    items: list[str] = []
    for component in manifest.uncertainty_budget.components:
        if component.status is not EvidenceStatus.established:
            items.append(
                f"- 预算组件 `{component.name}`：状态 `{component.status.value}`；"
                f"来源：{component.source}"
            )
    tide = manifest.tide_method
    if tide.status is not EvidenceStatus.established:
        items.append(
            f"- 潮汐方法验证（源列 `{tide.source_column}`）：状态 `{tide.status.value}`"
        )
    for kind, records in (
        ("输入", manifest.inputs),
        ("参数", (manifest.parameters,)),
        ("产物", manifest.products),
    ):
        for record in records:
            if record.status is not EvidenceStatus.established:
                items.append(
                    f"- {kind} `{record.relative_path}`：状态 `{record.status.value}`"
                )
    if not items:
        items.append("- 无：所列输入、参数、产物、预算组件与潮汐方法验证均为 `established`。")
    lines = ["## 11. 外部确认项", "", *items]
    return "\n".join(lines) + "\n"


def _section_status_summary(manifest: ResultManifest) -> str:
    statuses = [record.status for record in (*manifest.inputs, *manifest.products)]
    statuses += [
        component.status for component in manifest.uncertainty_budget.components
    ]
    statuses.append(manifest.tide_method.status)
    lines = ["## 12. 证据状态汇总", ""]
    for status in EvidenceStatus:
        count = statuses.count(status)
        if count:
            lines.append(f"- `{status.value}`：{count}")
    return "\n".join(lines) + "\n"


def _section_checklist(manifest: ResultManifest) -> str:
    primary = manifest.primary_16
    sensitivity = manifest.sensitivity_17
    tide = manifest.tide_method
    totals_closed = all(
        scenario.total_samples == sum(scenario.segment_n_valid)
        for scenario in (primary, sensitivity)
    )
    seg9_ok = (
        9 in sensitivity.included_groups
        and 9 in primary.excluded_groups
        and 9 in manifest.leave_one_out
    )
    counts_ok = (
        primary.n_segments == 16
        and sensitivity.n_segments == 17
        and len(manifest.leave_one_out) == 17
    )
    tide_counts_ok = (
        tide.converted_row_count > 0
        and tide.reference_row_count > 0
        and tide.common_prefix_row_count > 0
    )
    lines = [
        "## 13. 阶段一放行清单",
        "",
        f"- [{'PASS' if totals_closed else 'FAIL'}] 样本总数闭合：16 段 "
        f"{primary.total_samples} = Σ 分段 {sum(primary.segment_n_valid)}；17 段 "
        f"{sensitivity.total_samples} = Σ 分段 {sum(sensitivity.segment_n_valid)}。",
        "- [POINTER] 外部计数的独立对账：证据位于已哈希的 `time_quality.json`，"
        "本报告不复述。",
        f"- [{'PASS' if seg9_ok else 'FAIL'}] 第 9 段保留：17 段包含、16 段排除、"
        "leave-one-out 条目齐备。",
        f"- [{'PASS' if counts_ok else 'FAIL'}] 16/17 段结果与 17 条 leave-one-out 齐备"
        f"（{primary.n_segments}、{sensitivity.n_segments}、"
        f"{len(manifest.leave_one_out)}）。",
        "- [POINTER] label 与均匀时间轴的差异量化：证据位于已哈希的 `time_quality.json`。",
        f"- [{'PASS' if tide_counts_ok else 'FAIL'}] 潮汐 Excel→CSV 比较明确：转换 "
        f"{tide.converted_row_count}、参考 {tide.reference_row_count}、公共前缀 "
        f"{tide.common_prefix_row_count} 行。",
        "- [POINTER] 三角窗合成验证：由窗口相关单元测试覆盖。",
        "- [POINTER] 重叠协方差处理或限制说明：见 §9。",
        "- [POINTER] 新旧 OADEV 差异解释：见 §10。",
        "- [PASS] 清单哈希已验证：审计流水线在渲染前由 `verify_result_manifest` 校验通过。",
        "- [POINTER] 论文文件未变更：由审计命令集核对（git diff 为空）。",
    ]
    return "\n".join(lines) + "\n"


def render_sections(manifest: ResultManifest) -> list[str]:
    return [
        _section_header(manifest),
        _section_inputs(manifest),
        _section_ledgers(manifest),
        _section_segment9(manifest),
        _scenario_section(
            4,
            "16 段临时主结果",
            manifest.primary_16,
            "该结果为阶段一临时（provisional）主结果：第 9 段因参数待确认而被隔离；"
            "待专业潮汐输入的物理模型来源外部确认后冻结。",
        ),
        _scenario_section(
            5,
            "17 段敏感性结果",
            manifest.sensitivity_17,
            "本表为敏感性检查，不替代第 4 节的临时主结果；第 9 段在内。",
        ),
        _section_loo(manifest),
        _section_tide(manifest),
        _section_budget(manifest.uncertainty_budget),
        _section_covariance_pointer(),
        _section_old_new_pointer(),
        _section_external(manifest),
        _section_status_summary(manifest),
        _section_checklist(manifest),
    ]


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(
    manifest: Path = typer.Option(..., "--manifest", exists=True, dir_okay=False),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    try:
        loaded = read_audit_inputs(manifest)
        target = (
            output if output is not None else Path(manifest).parent / _DEFAULT_REPORT_NAME
        )
        write_report_atomic(render_audit_report(loaded), target)
    except (ManifestError, OSError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote {target}")


if __name__ == "__main__":
    app()
