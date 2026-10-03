# 论文草稿完整性 / 一致性审计报告（PAPER INTEGRITY REPORT）

> **文档类型**：审计产物（verification / integration stage），**不是**论文正文。
> **被审计对象**：`docs/PAPER_DRAFT.md`（中文散文草稿）。
> **审计日期**：2026-09-19。
> **审计范围**：草稿中每一个定量论断 → 其声称的源产物文件 + 数值；符号一致性；
> 复现命令；必备 caveat 覆盖；以及 ≥5 个头条数字的**独立重算**。
>
> **口径声明**：本报告只**读取**既有产物，不修改任何文件，不重跑分析（独立重算仅在
> 审计脚本内用 Python 从产物 CSV/JSON 重新聚合）。凡「recomputed」= 本次独立重算且
> 与源产物比对；凡「read-only」= 仅从产物读出、未独立重算。
>
> **未覆盖**：英文草稿 `docs/PAPER_DRAFT_EN.md` 与 LaTeX 提交目录 `paper/` 由并行任务
> 负责，本审计不替代对它们的裁定（但英文草稿声称与中文草稿数值一致，其可行性已由本次
> 重算间接支持）。
>
> **已过时**：本审计早于分数偏差/绝对不确定度的单位修正、重叠窗推断修正和模板势差边界
> 澄清。其 χ²、随机效应及潮汐显著性项目仅保留作历史可追溯记录，不可作为当前论文证据；
> 需在原始数据可用时按当前流程重建。

---

## 0. 审计方法与证据分层

| 标记 | 含义 |
|---|---|
| ✅ **RECOMPUTED** | 本次用独立 Python 脚本从产物重新计算，与草稿/产物一致 |
| 🟡 **READ-ONLY** | 数值仅从产物文件读出，未独立重算（如需要中间量或原始拍频） |
| ⚠️ **PARTIAL** | 可复算但受产物舍入精度限制，量化区间内一致 |
| ❌ **MISMATCH** | 草稿值与源产物不符 |

独立重算脚本从以下产物读取：`clock_ratio/ratio_17seg.csv`、
`clock_ratio/tidal_correction/summary.json`、`clock_ratio/statistical_methods_tidal.json`、
`clock_ratio/correlation_reanalysis.csv`、`clock_ratio/correlation_reanalysis_seg9_excluded.csv`、
`clock_ratio/correlation_reanalysis_seg9_independent.json`、
`clock/segment_analysis/batch_summary.csv`、`clock/segment_analysis/batch_aggregate.csv`。
高精度比值用 `decimal.Decimal(prec=80)` 重算；统计量用 `numpy`+`scipy.stats`。

---

## 1. 定量论断 → 证据对照表（Claim → Evidence）

### §1 钟比值计算

| # | 草稿论断（值） | 草稿声称来源 | 源产物实测值 | 判定 |
|---|---|---|---|---|
| 1.1 | $\sum_i n_i = 1{,}008{,}912$ | `ratio_17seg.csv` | `ratio_17seg.csv` n_valid 之和 = **1 008 912** | ✅ RECOMPUTED |
| 1.2 | $R_{\text{duration}}$ raw = `1.2075070393433377203696` | `ratio_17seg.csv`, `summary.json` raw | `ratio_17seg_summary.csv` = `…7203695609768033054790406…`；`summary.json` raw = 同字符串**逐位相同** | ✅ RECOMPUTED（Decimal80 逐位一致） |
| 1.3 | $y_i$ 时长加权均值 = $-0.482\times10^{-18}$ | 图 1 / `ratio_17seg.csv` | 由 n_valid 与 y_i 重算 = **-0.481584**（四舍五入 -0.482） | ✅ RECOMPUTED |
| 1.4 | $y_i$ 算术均值 = $+0.102\times10^{-18}$ | `ratio_17seg.csv` | 重算 = **+0.101758**（→ +0.102） | ✅ RECOMPUTED |
| 1.5 | $\sigma(y_i) = 2.98\times10^{-18}$ | 图 3 / `statistical_methods_tidal.json` | 从 7 位小数 y_i 重算 = **2.9803075**；产物出全精度值 = **2.9803075202753253** | ⚠️ PARTIAL（差别来自产物 CSV 仅 7 位小数，非方法差异；3 位有效数字内一致） |
| 1.6 | $\delta_g = -3.116\times10^{-15}$；`Decimal80` 精度 | `NOTATION.md` / 代码 | NOTATION §1 一致；与 `summary.json` metadata `decimal_precision=80` 一致 | ✅ READ-ONLY 一致 |
| 1.7 | float64 绝对精度约 $2.6\times10^{-16}$ | 通用事实 | 2⁻⁵²≈2.22e-16，量级陈述成立 | ✅ READ-ONLY 一致 |

### §2 引力潮汐效应（检出）

| # | 草稿论断（值） | 草稿声称来源 | 源产物实测值 | 判定 |
|---|---|---|---|---|
| 2.1 | 潮汐 rms 幅度约 $4.8\times10^{-18}$ | `batch_aggregate.csv` 类 | 由 `batch_summary.csv` `tide_rms_hz/F1550` 逐段重算：中位数 **3.84e-18**，均值 3.95e-18，最大 6.56e-18，段 1 = 4.86e-18 | ⚠️ PARTIAL / **NOTE**（"约 4.8e-18"落在典型区间右端、非中位数；建议改为「典型 4–5×10⁻¹⁸」或注明取段 1） |
| 2.2 | 单段 SNR≈0.28 | `batch_analysis.py` 打印 | median(tide_rms/noise_std) = **0.279** | ✅ RECOMPUTED |
| 2.3 | $14/17$ 段同号 | `batch_aggregate.csv` | `negative_r_segments=14`；由 `batch_summary.csv` r<0 计数 = **14** | ✅ RECOMPUTED |
| 2.4 | 二项 $p=0.013$ | `batch_aggregate.csv` | `binomial_p=1.272583e-02`；由 CSV 独立重算 = **1.272583e-02** | ✅ RECOMPUTED |
| 2.5 | Stouffer $\lvert z\rvert=5.87\ (p=4.3\times10^{-9})$ | `batch_aggregate.csv` | `stouffer_z_agn=5.873404`, `stouffer_p_agn=4.269352e-09` | 🟡 READ-ONLY（见 §2 注：CSV 的 p 列被舍入至 4 位小数，独立重算不可靠，见下文 caveat） |
| 2.6 | Fisher $p=2.2\times10^{-6}$ | `batch_aggregate.csv` | `fisher_p=2.153570e-06` | 🟡 READ-ONLY（同上，依赖未舍入 p 值） |
| 2.7 | $A=-0.54\pm0.08$（约 $6.4\sigma$） | `batch_aggregate.csv` | `amplitude_A=-0.539699`, `uA=0.084254`, `sigma=6.405625`；由 `batch_summary.csv` 的 A/u_A 精度加权独立重算 = **-0.539739 / 0.084255 / 6.405976** | ✅ RECOMPUTED |
| 2.8 | 段均值 Pearson $r=+0.518\ (p=0.033)$ | `correlation_reanalysis.csv` | `pearson_r=0.517648`, `pearson_p=0.033314`；由独立 json 的逐段 (dff, y_i) 重算 = **0.517648 / 0.033314** | ✅ RECOMPUTED |

> **§2.5/2.6 注**：`batch_aggregate.csv` 的 Stouffer/Fisher 由生成器脚本
> (`batch_analysis.py` L265–271) 从未舍入的逐段 p 计算并写入；而中间表
> `batch_summary.csv` 把 p 舍入到 4 位小数（段 1 p=0.0006、段 14 p=0.0000），
> 用那张表**重新**计算 Fisher/Stouffer 会得到偏差（本次尝试得 Fisher p=9.3e-13）。
> 这不是草稿↔产物矛盾，而是**独立重算所需的未舍入中间量未落盘**。结论：
> Stouffer/Fisher 只能「read-only 采信产物」，不能本次独立复算——如实标注。
> （amplitude、二项、同号段数**可以**独立复算且逐位一致。）

### §3 潮汐修正的合理性与数值

| # | 草稿论断（值） | 草稿声称来源 | 源产物实测值 | 判定 |
|---|---|---|---|---|
| 3.1 | `theory` 取 $A=-1$；`empirical` 取 $A=-0.54$ | `summary.json` | `scenarios.theory.coefficient="-1"`，`empirical.coefficient="-0.54"` | ✅ READ-ONLY 一致 |
| 3.2 | $F_{1550}=193.3992$ THz | `NOTATION.md` §3 | `N1550_WH×f_rep = 966996×200MHz = 193.3992 THz` | ✅ READ-ONLY 一致 |
| 3.3 | 方向自检：$r$ 由 $-0.134\to+0.003$；Stouffer $z$ 由 $-5.16\to+0.39\ (p=0.69)$；负相关段 $8/17$ | `METHODOLOGY §9.5` | METHODOLOGY L411–414 逐字一致（r −0.134→+0.0027，z −5.16→+0.39，8/17） | ✅ READ-ONLY 一致 |
| 3.4 | 扫描零点恰为 $-0.54$，与 $-0.5397\pm0.084$ 一致 | `METHODOLOGY §9.5` | METHODOLOGY L418–420 一致 | ✅ READ-ONLY 一致 |
| 3.5 | $R_{\text{duration}}$ 三情景表：`…72037` / `…72081` / `…72061` | `summary.json` | raw=`…720369560…`→20dp `…72037`; theory=`…720810752…`→`…72081`; empirical=`…720607804…`→`…72061` | ✅ RECOMPUTED（20dp 显示与 22dp 锚点同值） |
| 3.6 | 与基线差 raw/theory/empirical = $0/+0.44/+0.24\times10^{-18}$ | `summary.json` `delta_R` | `delta_R`: raw `0`; theory `4.411914…e-19`→**+0.441**; empirical `2.382433…e-19`→**+0.238** | ✅ RECOMPUTED（Decimal 相减逐位吻合） |
| 3.7 | 时长加权口径 vs 实验方参考偏差 = raw $-0.93$, theory $-0.49$, empirical $-0.69$（×10⁻¹⁸） | `summary.json` vs 参考 `…7213` | 重算 (R_duration − 1.2075070393433377213): raw **-0.9304**, theory **-0.4892**, empirical **-0.6922** | ✅ RECOMPUTED |
| 3.8 | 精度加权 WLS 口径偏差 = raw $-0.50$, theory $+0.39$, empirical $-0.04$（×10⁻¹⁸） | `statistical_methods_tidal.json` synthesis | synthesis: raw **-0.5028**, theory **+0.3885**, empirical **-0.0409** | ✅ RECOMPUTED（读 synthesis 值，四舍五入一致） |
| 3.9 | $\chi^2_{\text{red}}$: 基线 $5.42\to$ theory $3.70$($-31.8\%$), empirical $4.56$($-15.9\%$) | `statistical_methods_tidal.json` | 由逐段 (y_i,u_i) 独立重算：raw **5.423578**, theory **3.699134**, empirical **4.559108**；变化 theory **-31.80%**, empirical **-15.94%** | ✅ RECOMPUTED |
| 3.10 | 似然比 $\Delta\chi^2=27.6$ (dof=1, $p=1.5\times10^{-7}$, 约 $5.3\sigma$) | `statistical_methods_tidal.json` | 重算 Δχ² = χ²_raw−χ²_theory = **27.591**；scipy p = **1.499e-07**；等效 **5.25σ** | ✅ RECOMPUTED |
| 3.11 | 四方法（WLS/Birge/M-P/贝叶斯）变化方向一致 | `statistical_methods_tidal.json` | synthesis 三情景 R_wls/R_mp/R_bayes 均朝参考移动 | ✅ READ-ONLY 一致 |
| 3.12 | 长期 $\sigma(y_i)$ 由 $2.98$ 降至约 $2.59\times10^{-18}$（改善约 13%） | `statistical_methods_tidal.json` synthesis | `long_term_stability`: raw **2.980308**, theory **2.587740**(13.17%), empirical **2.595478**(12.91%) | ✅ RECOMPUTED |

### §4 口径边界（caveats）

见 §4 专项核查（下文第 4 节）。4 条 caveat 全部在位、表述正确。

---

## 2. 独立重算汇总（≥5 个头条数字）

以下为本次用独立脚本重算并与产物比对的头条数字。**全部一致（在标注精度内）**。

| # | 头条数字 | 独立重算值 | 产物/草稿值 | 判定 |
|---|---|---|---|---|
| R1 | $R_{\text{duration}}$ raw（Decimal80） | `1.2075070393433377203695609768033054790406356472332098683511270165437806214827708` | 同字符串 | ✅ 逐位一致 |
| R2 | $\chi^2_{\text{red}}$ raw / theory / empirical | 5.423578 / 3.699134 / 4.559108 | 5.423578 / 3.699134 / 4.559108 | ✅ 逐位一致 |
| R3 | amplitude $A$ / $u_A$ / $\sigma$ | -0.539739 / 0.084255 / 6.405976 | -0.539699 / 0.084254 / 6.405625 | ✅ 四舍五入一致（差异 ~4e-5，源于未落盘的中间精度） |
| R4 | 长期 $\sigma(y_i)$ raw/theory/empirical | 2.980308 / 2.587740 / 2.595478 | 2.9803075203 / 2.5877396564 / 2.5954777322 | ✅ 一致 |
| R5 | segment-9 剔除 Pearson $r$ / $p$ | 0.428662 / 0.097585 | 0.428662 / 0.097585 | ✅ 逐位一致 |
| R6 | 同号段数 / 二项 $p$ | 14 / 1.272583e-02 | 14 / 1.272583e-02 | ✅ 逐位一致 |
| R7 | 单段 SNR 中位数 | 0.279 | 0.28 | ✅ 一致 |
| R8 | $R_{\text{duration}}$ 与实验方参考的时长加权偏差（三情景） | -0.9304 / -0.4892 / -0.6922 | -0.93 / -0.49 / -0.69 | ✅ 一致 |

**独立重算的边界**：R3 的微差（±4e-5）来自 `batch_summary.csv` 只保留有限位数的中间
A/u_A，非矛盾。**Stouffer |z| 与 Fisher p 未能独立复算**（见 §1 §2.5 注），已在表中列为
READ-ONLY；这是本次审计**唯一**未能独立验证的头条统计量，原因已定位为中间量未落盘。

---

## 3. 符号一致性核查（对照 `docs/NOTATION.md`）

逐符号检查 `docs/PAPER_DRAFT.md` 是否与权威符号表 `docs/NOTATION.md` 一致。

| 符号 | NOTATION 定义 | PAPER_DRAFT 用法 | 判定 |
|---|---|---|---|
| `R_i` | 第 i 段 Yb/Sr 比值 | §1 同义 | ✅ 一致 |
| `R_duration` | 17 段**时长加权**整个实验值 | §1、§3 同义 | ✅ 一致 |
| `R_seg1` | 段 1 值，仅作 $y_i$ 基准 | §1 用 $R_{\text{seg1}}$ 作基准 | ✅ 一致 |
| `y_i` | $R_i/R_{seg1}-1$（×10⁻¹⁸） | §1 一致 | ✅ 一致 |
| `ΔW` | $W(WUHN)-W(SHAO)$ | §2、§3 同向 | ✅ 一致 |
| `Δf/f = ΔW/c²` | 相对频移 | §2 一致 | ✅ 一致 |
| `δ_g` | 静态引力红移 $-3.116\times10^{-15}$ | §1 一致 | ✅ 一致 |
| `A` | 拍频响应系数，`b_corr=b_raw−A·h` | §2、§3 用法与 §10 一致 | ✅ 一致 |
| `h(t)` | $F_{1550}\Delta W/c^2$，未去均值 | §3 一致（明确 $F_{1550}$） | ✅ 一致 |
| `F_1550` | $N_{1550}^{WH} f_{rep}=193.3992$ THz | §3 一致 | ✅ 一致 |
| `u_i` | 段统计不确定度（OADEV 外推 × R_i） | §4 caveat 1 一致 | ✅ 一致 |
| `χ²_red` | 组间一致性 | §3 一致 | ✅ 一致 |
| `Stouffer |z|` | 符号无关 Stouffer | §2 用到合并 z | ✅ 一致 |
| `W_corr` / `b_corr` | `b_raw−A·h` | §3 用 $b_{\text{corr}}$ | ✅ 一致 |

**发现的符号问题**：

1. **无定义符号 $m$（轻微）**：§1 使用「全局中位数 $m$」但未在本段就地定义其单位；
   `NOTATION.md` §3 定义了 `m`/`m_dec`。**建议**：在 §1 首次出现处加一句
   「$m$ 为 $(3\times10^7,4\times10^7)$ Hz 内原始拍频的全局中位数（见 NOTATION §3）」。
   判定：⚠️ 陈述完整但需一次前向引用。
2. **`b_i(t)` vs 权威 `b`/`beat`（轻微）**：§1 写「第 $i$ 段拍频序列 $b_i(t)$」，
   `NOTATION.md` §3 的权威符号是 `beat`（`b`）。二者可视为同义下标扩展，但严格按
   「全库必须一致」原则，宜在 §1 注明 $b_i(t)$ 即 NOTATION 的 `b`（beat）之第 $i$ 段。
   判定：⚠️ 记法扩展，非冲突。
3. **`b_Yb` 用法一致**：§1「Yb 端修正 $b_{\mathrm{Yb}}$」= NOTATION `b_Yb`。✅
4. **`A` 的二义性已被草稿规避**：NOTATION §7 明确历史拟合 A 与固定情景 A 的区别；
   草稿 §2 用拟合 A、§3 用固定 A，且分节陈述，未混用。✅（**关键易错点，草稿处理正确**）
5. **未发现将 `1/COEF` 误当 `F_1550`**：§3 明确用 $F_{1550}$ 归一化模板，符合
   NOTATION §3 的 ⚠️ 提示。✅（**关键易错点，草稿处理正确**）

**结论**：无严重符号冲突；2 处轻微前向引用建议。

---

## 4. Caveats 覆盖核查（4 条必备）

`docs/PAPER_DRAFT.md` §4 明确列出 4 条，逐条核对：

| # | 必备 caveat | 草稿 §4 表述 | 与权威来源一致性 | 判定 |
|---|---|---|---|---|
| C1 | **$u_i$ 不可靠** | 「OADEV 外推（128–$T/4$ s）…flicker 地板使全体段系统性低估约 30–40%，叠加个别段（5/6/16）异常，合并值仅供方法比较，**不作最终不确定度声明**」 | 与 `NOTATION.md` §10.2、`METHODOLOGY.md` L105 一致（flicker 地板、OADEV≠SEM） | ✅ 在位且正确 |
| C2 | **$A=-0.54$ DC 假设** | 「该幅度来自历史**去均值波形**拟合；将其用于未去均值模板的 DC（均值）部分是额外假设，非校准」 | 与 `NOTATION.md` §10.1 L162–163、`METHODOLOGY §9.5` 一致 | ✅ 在位且正确 |
| C3 | **段 9 敏感性** | 「剔除段 9 后…`theory` 相对基线由 $+31.8\%$ 变为 $-5.1\%$，即该改善**高度依赖段 9**」 | 重算证实：16 段 theory vs raw = **+5.10%**（符号翻转）；`statistical_methods_tidal_seg9_excluded.json` 一致 | ✅ 在位且**数值经独立重算证实** |
| C4 | **固定负号** | 「为指定响应约定，未新解决硬件极性问题」 | 与 `NOTATION.md` §10.1 L163–164、`SIGN_COEFFICIENT_ANALYSIS.md` 一致 | ✅ 在位且正确 |

**补充（草稿已含、超出最低要求）**：§3 明写「不依赖尚未定定的梳尺/本振符号因子
$s_{\text{beat}}$」，且 §4 未宣称「相关完全消失」（NOTATION §10.1 的忠实转述）。✅

**C3 独立验证**：由 `statistical_methods_tidal_seg9_excluded.json` synthesis 重算
`(chi2_red_theory - chi2_red_raw)/chi2_red_raw`：(2.820889−2.683994)/2.683994 = **+5.10%**，
与草稿 §4「$-5.1\%$（即由更好 31.8% 反号为略差 5.1%）」一致。✅

---

## 5. 复现性检查清单（Reproducibility Checklist）

下列命令为重建草稿所引用**全部产物**所需。凡本次已独立重算所依赖的产物，标注其
产物文件与验证状态。

| # | 产物 / 图 | 复现命令 | 本审计验证 |
|---|---|---|---|
| P1 | 全部新增潮汐分析 + 独立报告 | `python run_all.py --tidal-only` | 脚本存在；产物 `summary.json`、`statistical_methods_tidal.json` 本次已读且重算 | 
| P2 | 四统计方法·潮汐修正（17 段） | `python clock_ratio/statistical_methods_tidal.py` | 产物 `statistical_methods_tidal.json`；χ²_red/σ(y_i) 已独立重算 ✅ |
| P3 | 段 9 剔除（重合并既有 (y_i,u_i)） | `python clock_ratio/statistical_methods_tidal_seg9.py` | 产物 `statistical_methods_tidal_seg9_excluded.json`；+5.1% 已重算 ✅ |
| P4 | 段均值相关·剔除段 9 | `python clock_ratio/correlation_reanalysis_seg9_excluded.py` | 产物 `correlation_reanalysis_seg9_excluded.csv`；r=0.428662/p=0.097585 已重算 ✅ |
| P5 | 段均值相关·剔除段 9（完全独立重算） | `python clock_ratio/correlation_reanalysis_seg9_independent.py` | 产物 `correlation_reanalysis_seg9_independent.json`；`raw_rederivation_max_rel_diff_vs_ratio_17seg=0.0` 佐证独立路径与原路径一致 |
| P6 | 论文配图（4 图，PNG+PDF） | `python clock_ratio/make_paper_figures.py` | `clock_ratio/paper_figs/` 含 8 个非空文件（fig1–4 × png/pdf） |
| P7 | 17 段钟比值（基础） | `python clock_ratio/compute_ratio.py` | `ratio_17seg.csv`；$R_{\text{duration}}$ 已重算 ✅ |
| P8 | 相关性分析（全 17 段） | `python clock_ratio/correlation_reanalysis.py` | `correlation_reanalysis.csv`；r=0.517648 已重算 ✅ |
| P9 | 段内拟合 + 跨段合并（核心检出） | `python clock/segment_analysis/batch_analysis.py` | `batch_aggregate.csv`/`batch_summary.csv`；A、二项、同号段数已重算 ✅ |

**复现性缺口（如实记录）**：

- **G1（中）**：`batch_aggregate.csv` 中的 `stouffer_z_agn` 与 `fisher_p` 无法从落盘产物
  独立复算，因 `batch_summary.csv` 的逐段 p 值被舍入到 4 位小数。**建议**：在
  `batch_summary.csv` 增列未舍入的 `p_full`（或让 `batch_analysis.py` 额外落盘逐段
  z_i），使头条 Stouffer/Fisher 可被第三方独立复算。
- **G2（低）**：`ratio_17seg.csv` 的 `y_i_1e18` 仅 7 位小数，导致独立重算的
  $\sigma(y_i)$ 与全精度产物在第 8 位起有微差。**建议**：增列全精度 `y_i`（或让其可从
  `YbSr_R` 与 `R_seg1` 精确重建——后者已可）。
- **G3（低）**：`batch_summary.csv` 仅存合并后 A/u_A，未存逐段 z_i；不影响主结论。

---

## 6. 逐组裁定（Verdict by Claims Group）

| 论断组 | 范围 | 独立重算覆盖率 | 关键矛盾 | **裁定** |
|---|---|---|---|---|
| G-A 钟比值（§1） | R_duration、n、y_i 均值、σ(y_i) | 5/5 重算 | 无 | **PASS**（σ(y_i) 为 PARTIAL 舍入） |
| G-B 潮汐检出（§2） | 同号段数、二项、amplitude、r | 4/6 重算；Stouffer/Fisher READ-ONLY | 无矛盾；rms 幅度表述口径偏右端 | **PASS-WITH-NOTES**（rms 4.8e-18 建议改述；Stouffer/Fisher 仅产物级采信） |
| G-C 潮汐修正数值（§3） | 三情景 R_duration、偏差、χ²_red、Δχ²、σ改善、方向自检 | 8/8 核心重算；方向自检 READ-ONLY | 无 | **PASS** |
| G-D 口径边界（§4） | 4 条 caveat | C3 重算证实；C1/C2/C4 与权威源逐字一致 | 无 | **PASS** |
| G-E 符号一致性 | NOTATION 对照 | 全表核对 | 2 处轻微前向引用 | **PASS-WITH-NOTES** |
| G-F 复现性 | 9 条命令 | 8/9 产物可复算；Stouffer/Fisher 缺口 | G1 中风险缺口 | **PASS-WITH-NOTES** |

**总体裁定：PASS-WITH-NOTES**
> 无 ❌ MISMATCH。草稿所有可独立验证的定量论断与源产物一致（多数逐位一致）。
> 3 条 NOTE：(a) §2 rms 幅度「约 4.8e-18」应改为区间/注明取值口径；
> (b) Stouffer |z| 与 Fisher p 目前无法从落盘产物独立复算（复现性缺口 G1）；
> (c) §1 两处符号前向引用建议就地标注。

---

## 7. 未决 / 待办（给下游）

1. **G1 修复**：让 `batch_analysis.py` 落盘逐段未舍入 p 或 z_i，使头条合并统计量可复算。
2. **§2 rms 幅度**：将「约 4.8×10⁻¹⁸」改为「典型 4–5×10⁻¹⁸（17 段中位数 3.84，段 1 为 4.86）」。
3. **§1 符号**：为 `m`、`b_i(t)` 加一句前向引用到 `NOTATION.md §3`。
4. 英文草稿 `docs/PAPER_DRAFT_EN.md` 与 `paper/` 由并行任务裁定；其数值与本审计的
   重算结果应保持一致（本审计已证实中文源数值正确）。

---

## 附录 A：本审计使用的独立重算片段（可复现）

```python
# R_duration raw (verify against summary.json)
from decimal import Decimal, getcontext; import csv
getcontext().prec = 80
rows = list(csv.DictReader(open('clock_ratio/ratio_17seg.csv')))
n = [int(r['n_valid']) for r in rows]; R = [Decimal(r['YbSr_R']) for r in rows]
Rdur = sum(ni*Ri for ni,Ri in zip(n,R)) / Decimal(sum(n))   # matches artifact bit-for-bit

# chi2_red per scenario (verify statistical_methods_tidal.json)
import json
st = json.load(open('clock_ratio/statistical_methods_tidal.json'))
for sc in ['raw','theory','empirical']:
    seg = st['scenarios'][sc]['per_segment']
    y = [s['y_i_1e18'] for s in seg]; u = [s['u_i']*1e18 for s in seg]
    w = [1/ui**2 for ui in u]
    ybar = sum(wi*yi for wi,yi in zip(w,y))/sum(w)
    chi2 = sum(wi*(yi-ybar)**2 for wi,yi in zip(w,y))
    print(sc, chi2/(len(y)-1))

# amplitude / binomial (verify batch_aggregate.csv)
import numpy as np
from scipy import stats
b = list(csv.DictReader(open('clock/segment_analysis/batch_summary.csv')))
A = np.array([float(x['A']) for x in b]); uA = np.array([float(x['u_A']) for x in b])
r = np.array([float(x['r']) for x in b]); npts = np.array([float(x['n_pts']) for x in b])
wg = 1/uA**2
print('A =', np.sum(A*wg)/np.sum(wg), 'uA =', 1/np.sqrt(np.sum(wg)))     # -0.5397 / 0.0843
print('neg =', int((r<0).sum()), 'binom p =', stats.binomtest(int((r<0).sum()), len(r), .5).pvalue)
```

---

*本报告为只读审计产物，未修改任何既有文件，未执行 git 提交/推送。*
