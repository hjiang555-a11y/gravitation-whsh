# 武汉—上海远程光钟比对：潮汐引力红移分析

武汉（WUHN）与上海（SHAO）两地光钟（Yb/Sr）经 1550 nm 光纤链路远程比对，
分析潮汐引力红移效应（广义相对论 `Δf/f = ΔW/c²`）是否可被检出，并重建
逐段 Yb/Sr 钟比值。

> **权威钟比值**：Yb/Sr = **1.207 507 039 343 337 721**
> （R_ref = `1.20750703934333772095107679839…`）。

## 符号表

> 完整符号定义见 [docs/NOTATION.md](docs/NOTATION.md)。这里列出最常用的：

| 符号 | 含义 |
|---|---|
| `ΔW` | 两站重力势差 = `W(WUHN) − W(SHAO)`（武汉−上海）|
| `Δf/f` | 相对频率偏移（×10⁻¹⁸）|
| `R_i` / `R_ref` | 第 i 段钟比值 / 参考钟比值（= R_1）|
| `y_i` | 段钟比值偏差 = `R_i/R_ref − 1` |
| `A` | 段内幅度比（`beat = A·tide + noise`，A=+1 表示完整理论幅度）|
| `COEF` | 拍频→Sr/Yb 比值偏移系数（Dr 公式）|
| `F_1550` | 1550 nm 传递光频（拍频归一化基准，193.40 THz）|
| `N1156/N1397/N1550/N1550_WH` | 光梳计数（Yb/Sr/上海1550/武汉1550）|

> **关键易错点**：潮汐拍频模板必须归一化到 `F_1550`（1550 nm 光频），
> 而非 `COEF`（隐含 `1/COEF = 233.53 THz`，多 Yb/Sr ≈ 1.2075 倍）。
> 修正后幅度比 A ≈ −0.54（旧值 −0.45 系此错误所致）。

## 数据来源

- **潮汐**：专业人士提供的 30 秒间隔「综合差」（固体潮+海潮），
  `results/professional_tidal_delta_30s.csv`（UTC，方向武汉−上海，ΔW = g·mm/1000）。
- **实验**：1550 nm 环外拍频（FXE_B8，第 8 列数据），`clock/data/环外数据（第八列数据）/`
  （已 `.gitignore`）。17 段无跳点窗口见 `clock/shared.py` 的 `GROUPS`（北京时 UTC+8）。

## 标准流程（后续扩展按此结构）

```
clock/params.json                     ← 中间参数文档（实验条件都改这里）
clock/shared.py                       ← 单一真源：读 params.json，提供常量/段定义/加载器
docs/NOTATION.md                      ← 符号表（全库引用）
docs/ERROR_CHECKLIST.md               ← 错误清单 + 检查项目（工作纪律）
docs/WORKFLOW.md                      ← 总流程文档（怎么跑、实验条件变了改哪）
clock_ratio/compute_ratio.py          → 17 段钟比值（decimal 80 位 + 端点筛选）
clock_ratio/correlation_reanalysis.py → 段均值相关性 + 时长加权均值 + 修正量
clock/segment_analysis/batch_analysis.py → 段内 1200-s 拟合 + 跨段合并（核心检出）
clock/clock_tidal_shift.py            → 会话潮汐频移
clock_ratio/EXPERIMENT_REPORT.md      → 总权威报告
```

## 主要结论

1. **钟比值**：R_ref = `1.207507039343337720951…`（≈…721），与实验方 WLS
   `1.2075070393433377213(23)` 差 −0.35×10⁻¹⁸。
2. **潮汐检出（核心）**：段内 1200-s 窗拟合单段不显著，但跨段累加显著——
   14/17 段同号，符号无关 Stouffer |z|=5.87（p≈4.3e-9），幅度比
   **A = −0.54±0.08**（6.4σ），潮汐以正确方向、约一半幅度被检出。
3. **段均值相关**：y_i 与会话潮汐频移 Δf/f 正相关，Pearson r = +0.518（p=0.033）。

## 复现

```bash
python clock_ratio/compute_ratio.py              # 17 段钟比值（含端点筛选）
python clock/segment_analysis/batch_analysis.py  # 段内拟合 + 跨段合并（核心）
python clock_ratio/correlation_reanalysis.py     # 段均值相关 + 加权均值 + 修正量
python clock/clock_tidal_shift.py                # 会话潮汐频移
```

## 目录导航

| 路径 | 内容 |
|---|---|
| `clock_ratio/EXPERIMENT_REPORT.md` | **总权威报告**（钟比值+潮汐+相关性）|
| `docs/WORKFLOW.md` | 总流程文档（怎么跑、实验条件变了改哪）|
| `docs/NOTATION.md` | 符号与术语表 |
| `docs/ERROR_CHECKLIST.md` | 错误清单 + 检查项目（工作纪律）|
| `clock/params.json` + `clock/PARAMS.md` | 中间参数文档 + 字段说明 |
| `clock/shared.py` | 代码单一真源（读 params.json）|
| `clock/SEGMENT_17_SUMMARY.md` | 17 段起止时间表 |
| `clock/PROFESSIONAL_TIDAL_DATA.md` | 专业潮汐数据说明 |
| `clock/SIGN_COEFFICIENT_ANALYSIS.md` | 频率链符号与系数提取 |
| `clock/segment_analysis/` | 段内分析 + 变体 + 17 点相关性 |
| `clock/temperature/` | 环外信号与温度分析 |
| `archive/` | 历史/重叠/过时文档（含旧 14 段、旧 A≈−0.45）|

> 原始实验数据与 MATLAB 处理程序位于 `clock/data/`，已由 `.gitignore` 排除。
