# Nature 论文：摘要与框架（光钟网络的多用途定位）

> **定位**：突出宣称「光钟网络是一件通用的精密仪器」——同时服务
> ① 计量科学（SI 秒定义）、② 地球引力势探测（计时水准 / 相对论大地测量）、
> ③ 高精度时空坐标参考体系的建立（作为其基本「节点对」）。
>
> 本文档给出：Nature 风格 **abstract**（英文 + 中文）+ **论文框架**（分节逻辑 + 图表清单）。
>
> **诚实边界**（据专家评审）：本文实验为 **2 节点、1 条基线、~20% 占空比**，
> 因此「**建立**时空坐标参考体系」是**过度声称**——只能作为**展望**（"a step toward" /
> "prototype node pair"），**不能**作标题或摘要主张。数据支持的最强真实陈述见 §1。

---

## 0. 事实清单（全部经库内核实）

| 量 | 值 | 来源 |
|---|---|---|
| 基线 | 武汉（Yb, IAPMST/CAS）—上海（Sr, USTC），约 **700 km** 现网光纤 | 本库计算 |
| 两处机构、两种钟 | 不同机构 + 不同钟种 | — |
| 数据 | **58 天**，17 无跳点段，**1 008 912** 个 1 秒样本 = **280 h**（占空比 ~20%）| `summary.json` |
| Yb/Sr 比值 | `1.207 507 039 343 337 7215(23)`（潮汐修正后贝叶斯中心）| 实验方 PDF §5.4 |
| **贝叶斯统计不确定度** | **`0.75 × 10⁻¹⁸`**（仅钟统计噪声、不含钟评估）| 实验方 PDF §5.4 |
| vs NIST–JILA（Aeppli 2026）| `…7230(37)`，偏差 **−1.5 × 10⁻¹⁸** | 实验方 PDF §5.6 |
| vs 欧洲网络（Pizzocaro 2026）| `…718(32)`，偏差 **+3.5 × 10⁻¹⁸** | 实验方 PDF §5.6 |
| 三方符合度 | **≤ ~5 × 10⁻¹⁸** | 本库计算 |
| 站点重力势差 | `ΔW = +280.05 m²/s²`（`Δh = +28.6 m`），由水准测量 | `delta_g` 反推 |
| 潮汐调制检出 | **6.4σ**；14/17 同号；Stouffer `\|z\| = 5.87` | `batch_aggregate.csv` |
| 约化卡方 | `5.42 → 3.70`（−32%），**段 9 主导**（剔除段 9 后反号）| `statistical_methods_tidal.json` |

---

## 1. 定位与诚实评估（写给作者看的决策依据）

### 「时空坐标参考体系」是否可声称？——**否，属过度声称**

真正的相对论坐标参考体系（如 ITRS/ITRF、TCG/TCB）需要：**≥3 个站点 + 大地测量联测 +
约定的相对论参考系 + 连续运行 + 闭合一致性检验**。本实验是 **2 站、1 基线、1 次水准联测、
20% 占空比**——它是「一条基线」，**不是**一个「体系」。故：

- ❌ 不可写成「establish a space-time reference frame」
- ✅ 可写「**a prototype node pair / the elementary link of a future chronometric network**」，
  且**仅置于 Discussion / outlook**。

### 数据支持的**最强真实陈述**（用作摘要核心）

> 一个**跨机构、跨钟种、约 700 km** 的城际光钟网络，在 **58 天**内维持 `10⁻¹⁸` 量级的
> 统计比对，**独立重现**了 Yb/Sr 比值（与两个国际独立测定在 **≤5×10⁻¹⁸** 内一致，
> 满足 SI 秒重定义关切的水准），并**对潮汐引力红移调制展现出 ~6.4σ 的敏感度**。

三条通道的支持度评级：

| 用户想突出的通道 | 支持度 | 诚实措辞 |
|---|---|---|
| ① SI 秒定义 / 计量 | ✅ **支持** | 独立、跨机构的重现；回应 Aeppli「需要不同实验室反复比对」的号召。**不可**称「最精确」（Aeppli 更精确且含系统项）|
| ② 地球引力势探测 | ⚠️ **部分支持（能力，非测量）** | 常数 `ΔW` 是**引用的**（水准），非钟测；潮汐是**检出调制**。写「**sensitivity to** the tidal redshift」，不写「measured Earth's gravity」|
| ③ 时空坐标参考体系 | ❌ **过度声称** | 只能作展望：「a step toward / prototype node pair」|

### 候选标题排序

1. **（推荐）** *An inter-city optical clock network for precision metrology and relativistic geodesy*
2. *Inter-city Yb–Sr clocks with SI-second-level agreement reveal the tidal gravitational redshift*（若潮汐经误差膨胀后仍 ≥5σ）
3. *A 700-km two-species optical clock network*（计量主导；稳妥但相对 Aeppli 增量）
4. *Tidal gravitational-redshift modulation across an inter-city clock network*（地球探测主导；最新颖但最脆）
5. **（避免）** *Towards a continental space-time coordinate frame*（过度声称）

### 谁领衔？——**网络能力领衔**，比值作验证，潮汐作地球探测「延伸」

- 比值单独作标题：相对 Aeppli 2026 属增量（更精确且含系统项）→ 更适合 PRL。
- 潮汐单独作标题：数据脆弱（段 9 主导）→ 风险高。
- **网络能力（首例跨城、跨机构、跨钟种、持续数周、达 SI 相关水准 + 具引潮敏感度）** 才是 Nature 独特点。

---

## 2. Abstract（Nature 风格，单段，~197 词）

### English version

Optical lattice clocks reach fractional uncertainties below `10⁻¹⁸`, opening the prospect of a redefined SI second and of clock-based geodesy, but both goals require repeated comparisons of distant clocks by different laboratories. Here we demonstrate an inter-city optical clock network that links a Yb lattice clock in Wuhan and a Sr lattice clock in Shanghai — different species at different institutions, about `700 km` apart — through a phase-stabilized telecom fibre. Over `58` days, 17 uninterrupted segments yield `1 008 912` one-second samples (`280` h). After point-by-point tidal-redshift and endpoint corrections and a Bayesian combination of the segment scatter, the Yb/Sr frequency ratio is `1.207 507 039 343 337 7215(23)`, with a statistical uncertainty of `0.75 × 10⁻¹⁸`, consistent within `5 × 10⁻¹⁸` with independent determinations from NIST/JILA and the European fibre network — the accuracy level targeted for the SI-second redefinition. A cross-segment analysis further detects the tidal gravitational-redshift modulation across the baseline at `6.4σ` (14 of 17 segments with consistent sign; Stouffer `|z| = 5.87`), reducing the reduced chi-square from `5.42` to `3.70`. Inter-city clock networks thus emerge as dual-purpose instruments for frequency metrology and relativistic geodesy, and as a prototype node pair for a future chronometric reference frame.

*（~197 words）*

### 中文版

光晶格钟已达 `10⁻¹⁸` 以下的分数不确定度，为「秒」的重定义与基于光钟的大地测量打开了前景；但二者都要求不同实验室对相距遥远的钟进行**反复比对**。本文演示了一个**城际光钟网络**，将武汉的 Yb 光晶格钟与上海的 Sr 光晶格钟——**不同钟种、不同机构、相距约 700 公里**——经相位稳定光纤链路连接。在 `58` 天中，17 个连续无跳点段给出 `1 008 912` 个 1 秒样本（`280` 小时）。经逐点潮汐红移修正与端点修正，并用贝叶斯方法合并段间散布后，Yb/Sr 频率比为 `1.207 507 039 343 337 7215(23)`，统计不确定度 `0.75 × 10⁻¹⁸`，与 NIST/JILA 及欧洲光纤网络的独立测定在 `5 × 10⁻¹⁸` 以内一致——即秒重定义所关切的水准。跨段分析进一步在 `6.4σ` 显著度上检出该基线上的潮汐引力红移调制（17 段中 14 段同号；Stouffer `|z| = 5.87`），使约化卡方由 `5.42` 降至 `3.70`。城际光钟网络由此成为兼具**频率计量**与**相对论大地测量**双重用途的仪器，并可作为未来计时坐标参考体系的**原型节点对**。

**关键词：** 光钟网络；秒定义重定义；相对论大地测量；引力红移；潮汐；时空参考体系

---

## 3. 六层逻辑骨架

1. **背景（Background）**：光晶格钟已达 `<10⁻¹⁸`；两大应用都需要跨实验室比对——SI 秒重定义（独立比值 ≤5×10⁻¹⁸）与相对论大地测量（`1 cm ≈ 1.1×10⁻¹⁸`）。光纤链路使之成为可能。
2. **缝隙（Gap）**：迄今演示或是**单园区**多钟种（BACON）、或是**同种**跨城链路、或区域网络；**尚无「两机构 + 两城 + 两钟种」的持续数周、既有 SI 相关比值一致性、又对时变引力敏感的**网络。Aeppli 2026 明确呼吁「不同实验室的反复比对」。
3. **问题（Question）**：约 700 km 现网光纤的 Yb–Sr 网络，能否在数周内给出计量级频率一致性，并分辨潮汐引力红移调制？
4. **发现（Finding）**：58 天 / 17 段 / 1 008 912 样本；比值 `1.207…7215(23)`，统计 `0.75×10⁻¹⁸`；与 NIST、欧洲在 ≤5×10⁻¹⁸ 内一致（偏差 −1.5、+3.5×10⁻¹⁸）；潮汐调制 6.4σ（14/17 同号，Stouffer 5.87；χ² 5.42→3.70），并如实标注其脆弱性。
5. **阐释（Interpretation）**：跨机构异种网络在计量上可靠（独立重现），在引力上敏感（潮汐红移）；统计地板 `0.75×10⁻¹⁸ ≈ 0.7 cm` 高度当量，系统项与大地联测成为当前瓶颈。
6. **意义（Significance）**：支撑 SI 秒定义的独立验证；通往计时水准/大地测量的路径；作为未来**分布式相对论参考网络**的原型节点对（体系声称仅作展望）。

---

## 4. 论文框架（Nature Article，正文 ~4000 词 + Methods）

### 4.1 主文分节

| 节 | 内容与逻辑 | 图/表 |
|---|---|---|
| **Abstract** | 见 §2 | — |
| **1. Introduction**（3 段）| ① 光钟精度 → SI 秒定义（需 ≥3 个独立比值 ≤5×10⁻¹⁸）与相对论大地测量（`1 cm≈10⁻¹⁸`）；② 光纤链路使跨城比对可行——既有工作（单园区 BACON；跨城同种；欧洲网络；可搬运钟 Grotti/Takamoto）；③ **缝隙**：尚无分布式、多机构、多钟种、持续运行的 SI 级网络 + 时变引力敏感度；本文：武汉 Yb ↔ 上海 Sr，约 700 km，两项结果（比值；潮汐），路线图 | — |
| **2. Results A — 网络与观测活动** | 系统描述（两钟、光纤链路、光梳链）；链路稳定度；在线率；数据筛选；两钟稳定度。58 天 / 17 段 / 1 008 912 样本；占空比 | **Fig 1**（网络示意 + 活动概览）；表入 ED |
| **3. Results B — Yb/Sr 比值** | 处理流程；修正（逐点潮汐、端点）；贝叶斯段合并；结果 `1.207…7215(23)`，统计 `0.75×10⁻¹⁸`；与 Aeppli（−1.5×10⁻¹⁸）、Pizzocaro（+3.5×10⁻¹⁸）对比；三方 ≤5×10⁻¹⁸；站点势差 `ΔW=+280.05 m²/s²`（水准，28.6 m）与该一致性所检验的内容；**完整不确定度预算**（明列未含项：钟评估、潮汐模型、link/comb 置零 → 标注为统计下界）| **Fig 2**；**Table 1** |
| **4. Results C — 潮汐信号** | 方法（跨段组合；相位/幅度拟合）；结果 6.4σ、14/17 同号、Stouffer z；χ² 5.42→3.70；**稳健性**（段 9 主导、剔除后反号；OADEV 低估 30–40% 后的膨胀误差显著性）；结论措辞：**能力/敏感度**，非确定性测量 | **Fig 3**；**Fig 4 / ED** |
| **5. Discussion**（~4 段）| ① 阐释：跨机构异种网络达 SI 相关一致性；首例跨城网络对潮汐红移的敏感度；`0.75×10⁻¹⁸ ≈ 0.7 cm` 统计地板与 ~5 cm 跨实验室一致性；瓶颈转为系统项 + 大地联测。② 应用：SI 秒定义验证；计时水准大地测量；**时空/相对论参考体系（仅作展望：需 ≥3 节点、闭合、连续、约定参考系）**。③ 局限：潮汐脆弱性、逐段不确定度、未含项；何种数据能解决。④ 展望：网络扩容、链路/光梳改进、联合大地联测 | — |
| **6. Methods** | 钟与运行；光纤链路；光梳链；数据流程与去跳点；端点修正；潮汐模型与逐点修正；贝叶斯合并；跨段统计（Stouffer、符号检验、jackknife）；不确定度预算；水准与 `ΔW` | ED 表 |
| **7. Back matter** | Data/Code availability、致谢、作者贡献（CRediT）、利益冲突 | — |

### 4.2 图表清单

- **Fig 1 — 网络与活动**：(a) 武汉—上海 ~700 km 现网光纤路线图；(b) 实验示意（Yb@APMST 武汉 / Sr@USTC 上海，链路、光梳）；(c) 58 天内各段在线情况；(d) 链路稳定度 / OADEV。
- **Fig 2 — 比值结果**：逐段比值偏差与误差棒；合并值；与 Aeppli、Pizzocaro 对比（点 + 误差棒 + 带）。
- **Fig 3 — 潮汐分析**：(a) 残差 vs 潮汐相位/模型；(b) 幅度拟合；(c) 修正前后 χ²；(d) 逐段符号 / Stouffer。
- **Fig 4 — 稳健性**：jackknife / 留一法（高亮段 9）、显著性 vs 误差膨胀（OADEV 修正）、敏感度投影。
- **Table 1** — 比值结果与不确定度（本文 / NIST / 欧洲）。
- **Extended Data**：ED1 系统预算表（Yb/Sr 钟评估、引力/水准、link、comb、统计、潮汐模型）；ED2 逐段表；ED3 链路/光梳表征；ED4 潮汐模型对比与敏感度投影；ED5 钟评估汇总。

---

## 5. 专家指出的最大审稿风险与预防

**最大反对意见**：*标题超出了不确定度预算——`0.75×10⁻¹⁸` 仅为统计（link、comb、潮汐模型、钟评估均未含）；而 6.4σ 潮汐信号由单个段（段 9）主导，剔除后消失，且逐段误差被低估 30–40%。*

**预防**：
1. **两层声称**：已确立（跨城一致性 ≤5×10⁻¹⁸）vs 暂定（潮汐敏感度）。
2. **主文给出完整不确定度预算**（不埋入附录）；比值的**总不确定度**单独引用。
3. **稳健性**：jackknife、留一、符号检验、Stouffer；按 OADEV 定标膨胀逐段误差（~1.3–1.4×）后报告显著度；若 <5σ，措辞改为 "evidence for"，全文（含标题）一致下调。
4. **强调 ≤5×10⁻¹⁸ 的符合度**——这一结论对上述问题稳健。
5. **避免强词**：不写 "measurement of Earth's tides"、不写 "mm"、不写 "coordinate frame"。
6. 比值符合度作为**可证伪的**标题主张，潮汐作为**敏感度**。

**次要反对意见**：*相对 Aeppli 2026 属增量，潮汐脆弱，且非最长基线记录（Schioppo 2220 km），Beloy 已演示网络运行。*
预防：强调**独立重现**的必要性、**分布式多机构**运行、以及**大地测量能力**；淡化「记录」字眼。

---

## 6. 内部一致性警示（提交前必须处理）

1. **`(23)` 与 `0.75×10⁻¹⁸` 的记法冲突**：本文核实——实验方 PDF 中 WLS/MP/贝叶斯三种方法的**统计 u 各不相同**（`4.76`、`6.5`、`7.5 × 10⁻¹⁹`），但**给出的数值标签一律为 `(23)`**；而 Aeppli 2026 的 `(37)` 与其 `3.1×10⁻¹⁸` 分数不确定度**自洽**（`37×10⁻¹⁹ = 3.7×10⁻¹⁸ ≈ 1.2×3.1×10⁻¹⁸`）。据此推断：本实验的 `(23)` **不是** `0.75×10⁻¹⁸` 那一个统计不确定度的标准记法，而是**数值串的显示精度标签**（≈`1.9×10⁻¹⁸` 分数）。**摘要中两者必须分别标注来源**（本文已如此处理：比值给 `(23)` 标签，统计另给 `0.75×10⁻¹⁸`）。提交前建议向实验方确认二者口径。
2. **「首例」主张**：使用 "first inter-city tidal signal" 前须对照 Lisdat 2016 及后续跨城网络潮汐工作核实；未核实则用 "to our knowledge" 或改为 "a demonstration"。**本摘要草稿刻意未写 "first"**。
3. **段 9 敏感性**：提交前完成「膨胀误差 + 留一」分析；若显著度 <5σ，全文动词（含标题）由 "detect" 改为 "find evidence for"。

---

## 7. 安全换算（仅用于框架性表述）

| 换算 | 值 |
|---|---|
| `ΔW/c²` | `3.12 × 10⁻¹⁵` |
| `1 cm` 当量 | `1.09 × 10⁻¹⁸` |
| `0.75 × 10⁻¹⁸` 当量 | `≈ 0.7 cm` 高度 |
| `≤5 × 10⁻¹⁸` 当量 | `≈ 4.6 cm`（~5 cm）|
| `280 h / 58 d` | `20.1%` 占空比 |

---

## 8. 参考文献（已收入 `refs.bib`）

`beloy2021bacon`（BACON, Nature 591, 564）· `aeppli2026nist`（PRL 137, 033201）·
`arnold2026lu`（Nature 2026, ¹⁷⁶Lu⁺）· `zhang2026ca`（PRL 136, 053202, ⁴⁰Ca⁺）·
`pizzocaro2026european`（PRR 8, 033250）· `schioppo2022cavities`（2220 km 链路）·
`grotti2018geodesy`（可搬运钟大地测量）· `takamoto2020redshift`（GR 检验）·
`mcgrew2018geodesy`（`1 cm ↔ 10⁻¹⁸`）· `delva2017sr`、`sanner2019lorentz`（相对论检验）。
