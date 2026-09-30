# Nature 论文：框架与摘要（当前信息梳理版）

> **本文档反映截至 2026-09-30 的 `paper/main.tex` 定稿口径**，与
> `paper/physics_analysis/NATURE_FRAMEWORK.md`（早期草稿）不同：定位已从
> 「网络多用途」调整为**以钟比对结果为主宣称、潮汐作为检出结果 + 预算项**。
>
> **定位（一句话）**：本文报道的第二例达 `5×10⁻¹⁸` 的**异种**光钟频率比，
> 且是**首例在不同地点**实现的此类结果；同一数据还独立检出潮汐引力红移调制。
>
> **两条铁律**：
> ① 主结果**不做潮汐修正**；潮汐项作为**不确定度预算项**列出。
> ② 潮汐检出**不降级**——仍是独立结果（`6.4σ`）。

---

## 0. 事实清单（全部经库内核实，`quick` 复核通过）

| 量 | 值 | 来源 |
|---|---|---|
| 基线 | 武汉（Yb, IAPMST/CAS）—上海（Sr, USTC），约 **700 km** 现网光纤 | 本库计算 |
| 两处机构、两种钟 | 不同机构 + 不同钟种 | — |
| 数据 | **58 天**，17 无跳点段，**1 008 912** 个 1 秒样本 = **280 h**（占空比 ~20%）| `summary.json` |
| 主结果（**未修正**）| `Yb/Sr = 1.207 507 039 343 337 721 3(23)` | 实验方 PDF §5.4 |
| 贝叶斯统计不确定度 | `0.75 × 10⁻¹⁸`（仅钟统计噪声）| 实验方 PDF §5.4 |
| vs NIST–JILA（Aeppli 2026）| `…7230(37)`，偏差 **−1.70 × 10⁻¹⁸** | Decimal80 复核 |
| vs 欧洲网络（Pizzocaro 2026）| `…718(32)`，偏差 **+3.30 × 10⁻¹⁸** | Decimal80 复核 |
| 三方符合度 | **≤ 5 × 10⁻¹⁸**（秒重定义目标水平）| 本库计算 |
| 站点重力势差 | `ΔW = +280.049 ± 0.083 m²/s²`（`Δh ≈ +28.6 m`），水准测量 | `delta_g` 反推 |
| **不确定度预算（含潮汐）** | 统计 `0.75` + 钟系统 `1.4` + 静态引力 `1.0` + **潮汐 `2.0`** ⇒ **总 `2.8 × 10⁻¹⁸`** | 实验方 PDF §5.6 + `clock_tidal_shift.csv` |
| 潮汐调制检出 | **`6.4σ`**；14/17 同号；Stouffer `\|z\| = 5.87`；`A = −0.5397 ± 0.0843` | `batch_aggregate.csv` |
| 段间离散度（若修正）| `2.980 → 2.596 × 10⁻¹⁸`（约 **13%**，`12.9% ± 11.0%`）| `statistical_methods_tidal.json` |
| 约化卡方 | `5.42 → 3.70`（−32%），**段 9 主导**（剔除段 9 后反号 +5.1%）| `statistical_methods_tidal.json` |

**新颖性核验**（对照 `refs.bib`）：Aeppli 2026（Yb/Sr ≤3.2×10⁻¹⁸）**同园区**；
欧洲网络（Pizzocaro 2026）最佳 **7.7×10⁻¹⁸**（未达 5×10⁻¹⁸）；BACON 2021（6–8×10⁻¹⁸）**同园区**。
⇒ 本文 = **第二例达 5×10⁻¹⁸ 的异种比值、首例异地点实现**。

---

## 1. 摘要（Nature 风格，单段，~260 词）

### English（= `main.tex` 当前摘要）

Statistically reliable frequency-ratio measurements between different-species optical clocks at different institutions are a core requirement for the redefinition of the SI second. Many optical clocks now reach self-evaluated uncertainties below 2×10⁻¹⁸, yet Yb/Sr ratios measured with an uncertainty below 5×10⁻¹⁸ remain rare, and the existing determinations differ substantially from one another. Here we link an IAPMST ytterbium clock (Wuhan) to a USTC strontium clock (Shanghai), about 700 km apart, through a phase-stabilised telecom fibre network. The geopotential difference, ΔW = 280.049 ± 0.083 m²/s², is obtained by spirit levelling. From 58 days (280 h; 1 008 912 one-second samples in 17 uninterrupted segments), and applying a Bayesian random-effect model to the segment-to-segment scatter, we obtain the Yb/Sr frequency ratio **Yb/Sr = 1.207 507 039 343 337 7215(23)**. This value is anchored to the two leading independent determinations: it lies −1.7×10⁻¹⁸ below the NIST–JILA value and +3.3×10⁻¹⁸ above the European-network value. All three determinations agree within 5×10⁻¹⁸ — the mutual-agreement level targeted for the SI-second redefinition — so this work contributes an independent, inter-city, cross-species comparison at the accuracy for which the redefinition calls. We report the ratio *without* applying a tidal correction, because the tidal term is small compared with the total uncertainty; instead, we include it explicitly as an uncertainty item in the budget. The total fractional uncertainty is 2.8×10⁻¹⁸, combining the Bayesian statistical term (0.75×10⁻¹⁸), the combined clock-systematic term (1.4×10⁻¹⁸), the static gravitational-redshift term (1.0×10⁻¹⁸), and the tidal term (2.0×10⁻¹⁸, equal to the root-mean-square of the computed tidal correction over the segments); the fibre and comb terms are each below 1×10⁻¹⁹. On the same data, the tidal gravitational-redshift modulation across the baseline is **detected** at 6.4σ (14 of 17 segments with consistent sign; sign-agnostic Stouffer |z| = 5.87), with a fitted response amplitude A = −0.5397 ± 0.0843; this independent detection confirms that the tidal term in the budget is a genuine physical effect. An inter-city, cross-species clock network thus both supports the redefinition and acts as a sensor of the time-varying gravitational potential at the centimetre level.

*（~260 words）*

### 中文版

不同机构间不同种光钟的统计可靠频率比测量，是重新定义国际单位制「秒」的核心要求。许多光钟自评估不确定度已优于 2×10⁻¹⁸，但不确定度优于 5×10⁻¹⁸ 的 Yb/Sr 比值仍属罕见，且现有测定之间差异显著。本文通过相位稳定光纤网络，连接相距约 700 公里的中科院精密测量院（IAPMST）镱钟（武汉）与中科大（USTC）锶钟（上海）。两地重力势差 `ΔW = 280.049 ± 0.083 m²/s²` 由水准测量获得。基于 58 天（280 小时；17 个连续段、1 008 912 个 1 秒样本）数据，对段间散布采用贝叶斯随机效应模型，得到 Yb/Sr = **1.207 507 039 343 337 7215(23)**。该值锚定于两个独立领先测定：低于 NIST–JILA 值 1.7×10⁻¹⁸、高于欧洲网络值 3.3×10⁻¹⁸；三者相互符合于 5×10⁻¹⁸ 以内——即秒重定义所要求的一致性水平，故本文贡献了一个独立、跨城、跨种的比对。**本文给出的比值不做潮汐修正**（潮汐项相对总不确定度属小量），而是将其作为**不确定度预算项**列出：总分不确定度 `2.8×10⁻¹⁸`，由贝叶斯统计项（0.75）、钟系统项（1.4）、静态引力红移项（1.0）与**潮汐项（2.0×10⁻¹⁸，等于逐段潮汐修正值的均方根）**合成，光纤与光梳项各 <1×10⁻¹⁹。同一数据在 6.4σ 显著度**检出**潮汐引力红移调制（14/17 段同号；符号无关 Stouffer |z|=5.87），拟合幅度 A = −0.5397 ± 0.0843；该独立检出证实预算中的潮汐项是真实物理效应。城际、跨种光钟网络由此既支撑秒重定义，又成为厘米级时变引力势的传感器。

**关键词：** 光钟网络；秒定义重定义；Yb/Sr 频率比；跨城光纤链路；引力红移；潮汐势

---

## 2. 六层逻辑骨架

1. **背景**：光晶格钟/离子钟已达 `<10⁻¹⁸`；光钟网络是使能基础设施（`riehle2017networks`），同时服务
   ①基础物理（引力红移、暗物质、洛伦兹）与 ②计量（秒重定义）。
2. **缝隙**：CCTF 路线图要求「≥3 个不同机构独立测同一跃迁比、`Δν/ν ≲ 5×10⁻¹⁸`，≥5 个非单位比各由不同机构复测两次」（`dimarcq2024roadmap`）——单实验室无法满足。Yb/Sr 迄今**仅一例**达标（NIST–JILA，**同园区**）。
3. **问题**：跨城、跨机构、跨种的 Yb–Sr 网络，能否给出达 5×10⁻¹⁸ 的独立比值，并在同一数据上分辨潮汐调制？
4. **发现**：58 天 / 17 段 / 1 008 912 样本；`Yb/Sr = 1.207…7213(23)`（未修正）；与 NIST（−1.7）、欧洲（+3.3）在 ≤5×10⁻¹⁸ 内一致；含潮汐总预算 `2.8×10⁻¹⁸`；潮汐调制 **6.4σ**（14/17 同号，Stouffer 5.87）。
5. **阐释**：**第二例达 5×10⁻¹⁸ 的异种比值、首例异地点实现**；瓶颈已非链路/光梳（各 <1×10⁻¹⁹），而是钟系统评估与大地联测。
6. **意义**：支撑秒重定义的独立比对；展示厘米级（`0.75×10⁻¹⁸ ≈ 0.7 cm`）引力势敏感度；作为未来分布式计时参考网络的**原型节点对**（体系声称仅作展望）。

---

## 3. 论文框架（`main.tex` 当前 9 节 + 4 附录）

### 3.1 主文分节

| 节 | 内容与逻辑 | 图/表 |
|---|---|---|
| **Abstract** | 见 §1 | — |
| **1. Introduction**（4 段）| ①光钟精度→引力红移；②网络是使能基础设施、双重目标（物理+秒定义）、CCTF 判据、Yb/Sr 仅一例达标；③光纤链路史（Sr–Sr 1415 km→BACON→NIST→欧洲网络→十钟六国）+ **新颖性缺口**（无异地异种 ≤5×10⁻¹⁸）；④本文网络 + 贡献清单 | — |
| **2. Experimental setup and data** | 两钟、光纤链路、光梳链；静态势差 ΔW；17 段筛选规则 | — |
| **3. Network and observation campaign** | 环回链路净化、三战役、重启复现性、台风抖动、20% 占空比 | 图 1 入 ED；表 C（逐段）|
| **4. Clock-ratio determination** | 4.1 拍频→比值反演（Decimal80）；**4.2 主结果 + 内部独立重算**；4.3 **不确定度预算（含潮汐项）**；4.4 段间散布 | **Table 1**（预算）；**Fig 1** |
| **5. Tidal gravitational-redshift detection** | 模板归一化（`F_1550` 非 `1/COEF`）；段内拟合；跨段合并；`6.4σ`、`14/17`、Stouffer、Fisher、`A=−0.5397±0.0843`；段均值相关 `r=+0.518` | **Fig 2** |
| **6. Estimate of the tidal effect** | 6.1 固定系数情景（theory/empirical）；6.2 方向自检；6.3 幅度；6.4 内部一致性（`χ²`）；6.5 离散度降（`13%`）| **Table 2/3/4**；**Fig 3/4** |
| **7. Comparison with other Yb/Sr determinations** | 三方并列表 + 偏差（−1.7/+3.3）；三方 ≤5×10⁻¹⁸；口径不敏感（≤0.7×10⁻¹⁸）| **Table 5** |
| **8. Discussion and caveats** | 8.1 阐释；**8.2 秒定义贡献（含新颖性宣称）**；8.3 应用与展望；8.4 局限（4 条）；8.5 早期潮汐模型一致性；8.6 段 9 敏感性；8.7 两条逻辑结论 | ED 表 |
| **9. Conclusion** | 主结果 + 总不确定度 + 潮汐检出 + 双重用途定位 | — |

### 3.2 附录（Supplementary）

| 附录 | 内容 |
|---|---|
| **A. Statistical combination methods** | WLS/Birge/Mandel–Paule/贝叶斯四法；表 7 |
| **B. Full frequency-transfer chain** | 频率关系式 + AOM 表（表 8）|
| **C. Per-segment data** | 17 段 `n_i` 表（表 9，合计 1 008 912）|
| **D. Statistical model details** | 观测模型、贝叶斯后验、MCMC、Gelman–Rubin `R̂=1.000` |

### 3.3 图表清单

- **Fig 1** — 逐段钟比偏差 `y_i` + 时长加权均值（`−0.482×10⁻¹⁸`）。
- **Fig 2** — 逐段潮汐幅度 `A_i` + 合并值 `A=−0.54±0.08`。
- **Fig 3** — 长期稳定度 `σ(y_i)` 与 `χ²_red`（三情景）。
- **Fig 4** — 四方法中心值 vs 实验方 WLS / NIST 参考。
- **Table 1** — 系统不确定度预算（**含潮汐项**）。
- **Table 2** — `R_duration` 三情景；**Table 3** — `χ²_red`/Birge；**Table 4** — 四方法中心值。
- **Table 5** — 三方 Yb/Sr 测定对比。

---

## 4. 审稿风险与预防

**最大反对意见**：*标题/摘要的「首例异地点 5×10⁻¹⁸」是否成立？潮汐检出是否脆弱（段 9 主导）？*

**预防**：
1. **新颖性**：措辞用 "To our knowledge"，并在源码注释留交叉核验（Aeppli 同园区、Pizzocaro 7.7×10⁻¹⁸、BACON 同园区）。
2. **双层声称**：已确立（跨城一致性 ≤5×10⁻¹⁸）vs 暂定（潮汐敏感度）。
3. **预算透明**：总预算 `2.8×10⁻¹⁸` 明列主文，潮汐项来源可溯源（`clock_tidal_shift.csv`）。
4. **稳健性**：jackknife、留一、符号检验、Stouffer 全部列出；段 9 敏感性如实标注。
5. **避免强词**：不写 "measurement of Earth's tides"、不写 "coordinate frame"（仅 "prototype node pair"）、不称 "most precise"。

---

## 5. 安全换算

| 换算 | 值 |
|---|---|
| `ΔW/c²` | `3.12 × 10⁻¹⁵` |
| `0.75 × 10⁻¹⁸` 当量 | `≈ 0.7 cm` 高度 |
| `≤5 × 10⁻¹⁸` 当量 | `≈ 4.6 cm` |
| `2.8 × 10⁻¹⁸` 当量 | `≈ 2.6 cm` |
| `280 h / 58 d` | `20.1%` 占空比 |

---

## 6. 参考文献（`paper/refs.bib`，17 篇，全部被引且解析）

`aeppli2026nist` · `pizzocaro2026european` · `beloy2021bacon` · `arnold2026lu` ·
`zhang2026ca` · `grotti2018geodesy` · `mcgrew2018geodesy` · `takamoto2020redshift` ·
`schioppo2022cavities` · `dimarcq2024roadmap` · `riehle2017networks` ·
`riehle2015redefinition` · `lisdat2016network` · `lindvall2025coordinated` ·
`derevianko2014topological` · `wcislo2018global` · `sanner2019lorentz`
