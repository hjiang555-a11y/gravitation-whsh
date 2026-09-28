# physics_analysis — 物理模型探测能力调研

本目录调研**武汉—上海 Yb/Sr 光钟比对实验**对暗物质及其它超出标准模型（BSM）物理的探测能力。
模板论文为 [../3104.pdf](../3104.pdf)（BACON Collaboration, *Nature* **591**, 564 (2021)）。

> **性质声明**：本目录产出的是**调研报告 + 量级估算（illustrative）**，**不是**新的物理
> 约束。库内逐段统计不确定度 `u_i` 已知不可靠（OADEV 外推低估 30–40%），观测占空比仅
> ~20%。所有定量数字**不可作为排除线引用**。详见 [REPORT.md](REPORT.md) §6。

## 文件

| 文件 | 用途 |
|---|---|
| [`REPORT.md`](REPORT.md) | **主报告**（中文）：实验装置、BSM 文献综述、灵敏度矩阵、量级估算、局限、后续建议 |
| [`sensitivity_estimate.py`](sensitivity_estimate.py) | 量级估算脚本；读库内已有产物，无需原始拍频 |
| [`sensitivity_estimates.csv`](sensitivity_estimates.csv) | 逐段 `h_0` 与 `δ_R` 表（脚本输出）|
| [`sensitivity_summary.json`](sensitivity_summary.json) | 合并 `δ_R`、`d_e`、`Λ_γ` 汇总（脚本输出）|
| [`refs.bib`](refs.bib) | 参考文献（含核验标记；未核验项已标注）|

## 核心结论（速览）

1. **能探**：精细结构常数 `α` / 光子耦合 `d_e`（`ΔK_α^{Yb/Sr} = |0.31−0.06| = 0.25`）、
   引力红移 / GR / LPI。
2. **不能探**：`m_e` / `μ`（Yb/Sr 为纯光学-光学比值，`ΔK_μ = 0`）。
3. **已实现**：潮汐引力红移 **6.4σ** 检出（库内结果，见
   [../../clock_ratio/EXPERIMENT_REPORT.md](../../clock_ratio/EXPERIMENT_REPORT.md)）。
4. **量级估算**：`δ_R ≈ 8.8×10⁻¹⁹`；`d_e ~ 6×10⁻¹⁰`（低质量端）至 `6×10⁻⁴`（高质量端），
   均为 illustrative。

## 复现

```bash
# 从仓库根目录运行
python paper/physics_analysis/sensitivity_estimate.py
```

输出 `sensitivity_estimates.csv` 与 `sensitivity_summary.json`。

**输入**（均为库内已核验产物）：

- [`clock_ratio/statistical_methods_tidal.json`](../../clock_ratio/statistical_methods_tidal.json)
  — 逐段 `T_s` 与 fractional `u_frac`（OADEV 外推的 `σ_y(T)`）
- [`clock_ratio/ratio_17seg.csv`](../../clock_ratio/ratio_17seg.csv) — 逐段 `n_valid` 与时间戳

**物理常数与公式**：见 `sensitivity_estimate.py` 顶部注释；文献出处见 [refs.bib](refs.bib)
与 [REPORT.md](REPORT.md) §2。

## 方法要点（避免误用）

- 白频噪声系数：`h_0 = 2 σ_y²(T_i) · T_i`（**不是** `σ_y·√T_i`）。
- 相干正弦幅度探测限：`δ_R ≈ √(2 h_0 / T_eff)`，`T_eff` 用**总有效时间** `T_valid`
  （非墙钟跨度）。
- BACON 光耦合转换：`d_e = 4.2×10³⁰ · δ_R · m_φ / ΔK`（`m_φ` 单位 eV，
  `ρ_DM = 0.4 GeV/cm³`，随机振幅重标 3.0）。
- dilaton 耦合：`Λ_γ = M_Pl / (√(4π) d_e)`。
- BACON 搜索频段：`1/(20 T_max) < f < 1/100 s`。

## 相关目录

- [../main.tex](../main.tex) — 英文投稿稿（潮汐引力红移分析）
- [../../docs/NOTATION.md](../../docs/NOTATION.md) — 全库符号表
- [../../docs/METHODOLOGY.md](../../docs/METHODOLOGY.md) — 计算方法（含 `u_i` 不可靠的论证）
