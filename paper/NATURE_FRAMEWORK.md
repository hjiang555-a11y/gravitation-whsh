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

## 1. 摘要（Nature 规范：单段、无引用、无公式，~182 词）

> **Nature 摘要纪律**：单一连续段落；无小标题；**无引用命令**；**无 display 公式**
> （数值内联）；~150–200 词；五段式流：背景 → 缺口 → 本文做法 → 发现 → 意义。
> **语言纪律**：首句直陈要求、不作冗长定语堆叠；避免"Highly consistent…with demonstrated
> statistical reliability"式的绕口长句。
>
> **三处刻意保留**：
> ① **不强调"未做修正"**——潮汐项直接表述为"carried as an uncertainty item"，不写
>    "without a tidal correction"（作者指示：无需强调）。
> ② **总不确定度占位 `X×10⁻¹⁸`**——部分不确定度项（如 tide model、附加系统项）仍在评估，
>    会影响总值，故暂不填数字，待定稿再补（勿以 2.8 替代）。
> ③ **仅与 NIST–JILA 比对**——欧洲网络统计不确定度过大，不作一致性主张；改用
>    "To our knowledge this is the first cross-species frequency ratio at the 5×10⁻¹⁸
>    level measured between clocks at different locations"（主宣称）。

### English（= `main.tex` 当前摘要）

Redefining the SI second requires frequency ratios of optical clocks measured independently by different laboratories, and agreeing to within 5×10⁻¹⁸. Many optical clocks report self-evaluated uncertainties meeting this level, but such claims still await independent verification, and no comparison between clocks in different cities has reached this level. Here we compare an IAPMST ytterbium clock in Wuhan with a USTC strontium clock in Shanghai, about 700 km apart, through a 1350 km fibre link, and measure the Yb/Sr frequency ratio from 58 days (280 h) of coherent operation. Treating the tidal gravitational-redshift term as an uncertainty item, we find a Bayesian statistical uncertainty of 0.75×10⁻¹⁸ and a total uncertainty of X×10⁻¹⁸, giving 1.207 507 039 343 337 721 3(23), whose central value differs from the latest NIST–JILA result by less than 5×10⁻¹⁸. To our knowledge this is the first cross-species frequency ratio at the 5×10⁻¹⁸ level measured between clocks at different locations. On the same data the tidal redshift modulation is resolved at 6.4σ; removing it would lower the reduced chi-square from 5.42 to 3.70 (32%). An inter-city, cross-species clock network thus both supports the redefinition of the SI second and senses the time-varying gravitational potential at the centimetre level.

*（~180 words；五段式：背景 → 缺口 → 做法 → 发现 → 意义）*

### 中文版

重新定义国际单位制「秒」，需要由不同实验室独立测量、并在 5×10⁻¹⁸ 以内相符的光钟频率比。许多光钟**自评估**不确定度已达该水平，但这些声明仍有待独立验证；且尚无位于不同城市的钟之间的比对达到该水平。本文比较相距约 700 公里的中科院精密测量院（IAPMST，武汉）镱钟与中科大（USTC，上海）锶钟，两者经 1350 公里光纤链路连接，基于 58 天（280 小时）相干运行数据测定其 Yb/Sr 频率比。将潮汐引力红移项作为不确定度项，得到贝叶斯统计不确定度 0.75×10⁻¹⁸、总不确定度 `X×10⁻¹⁸`（占位），比值为 1.207 507 039 343 337 721 3(23)，与最新 NIST–JILA 结果在 10⁻¹⁸ 量级相符。同一数据在 6.4σ 显著度分辨出潮汐红移调制；若将其扣除，约化卡方由 5.42 降至 3.70（降幅 32%）。跨城、跨种光钟网络由此既支撑秒重定义，又以厘米级精度感知时变引力势。

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

## 3. 论文框架（`main.tex`，Nature Article 版：Introduction + Results + Discussion + Methods）

> **组织原则（Nature Article）**：知识点保留在正文（Results/Discussion），仅**程序性细节**下沉到
> Methods。故主结果（比值、不确定度预算、潮汐检出、潮汐效应、三方对比）**一律留在正文**，
> 不下沉；只有推导配方（反演方程、四法合并、水准、潮汐拟合、统计模型）在 Methods。
> 主文 ~1700 词（Introduction + Results + Discussion），Methods 另计。

### 3.1 正文分节（Main text）

| 节 | 内容与逻辑 | 图/表 |
|---|---|---|
| **Abstract** | 见 §1 | — |
| **Introduction**（无编号）| ①光钟精度→引力红移；②网络是使能基础设施、双重目标（物理+秒定义）、CCTF 判据、Yb/Sr 仅一例达标；③光纤链路史（Sr–Sr 1415 km→BACON→NIST→欧洲网络→十钟六国）+ **新颖性缺口**（无异地异种 ≤5×10⁻¹⁸）；④本文网络 + 贡献清单 | — |
| **Results** | 见下 5 个子节 | Fig 1–4；Table 1–5 |
| ├ 2.1 Network and observation campaign | 两钟两城、光纤链路（环回净化）、光梳链；17 段筛选；三战役、重启复现性、台风抖动、20% 占空比 | 逐段表入 Methods |
| ├ 2.2 Clock-ratio determination | **主结果（未修正）+ 内部重算**；**不确定度预算（含潮汐项，总值 provisional）**；段间散布 | **Table 1**（预算）；**Fig 1** |
| ├ 2.3 Tidal gravitational-redshift detection | 模板归一化（`F_1550` 非 `1/COEF`）；段内拟合；跨段合并；`6.4σ`、`14/17`、Stouffer、Fisher、`A=−0.5397±0.0843`；段均值相关 `r=+0.518` | **Fig 2** |
| ├ 2.4 Estimate of the tidal effect | 固定系数情景（theory/empirical）；方向自检；幅度；内部一致性（`χ²`）；离散度降（`13%`）| **Table 2/3/4**；**Fig 3/4** |
| └ 2.5 Comparison with other Yb/Sr determinations | 并列表 + 偏差（NIST −1.7；欧洲 +3.3，注明其统计不确定度更大，不作一致性主张）；口径不敏感（≤0.7×10⁻¹⁸）| **Table 5** |
| **Discussion** | 阐释；秒定义贡献（含新颖性宣称）；应用与展望；局限；早期潮汐模型一致性；两条逻辑结论；**Conclusion 折为末段** | ED 表 |

### 3.2 Methods（程序性细节）

| 小节 | 内容 |
|---|---|
| **Experimental setup and frequency transfer** | 频率关系式 + AOM 表 |
| **Beat-to-ratio inversion** | 拍频→比值反演方程（Decimal80）|
| **Statistical combination methods** | WLS/Birge/Mandel–Paule/贝叶斯四法 |
| **Levelling determination of the geopotential difference** | 1113 km 一等水准 + 五部分位差表 |
| **Tidal analysis** | 模板归一化、1200-s 拟合、固定系数情景配方 |
| **Per-segment data** | 17 段 `n_i` 表（合计 1 008 912）|
| **Statistical model details** | 观测模型、贝叶斯后验、MCMC、Gelman–Rubin `R̂=1.000` |

### 3.3 图表清单

- **Fig 1** — 逐段钟比偏差 `y_i` + 时长加权均值（`−0.482×10⁻¹⁸`）。
- **Fig 2** — 逐段潮汐幅度 `A_i` + 合并值 `A=−0.54±0.08`。
- **Fig 3** — 长期稳定度 `σ(y_i)` 与 `χ²_red`（三情景）。
- **Fig 4** — 四方法中心值 vs 实验方 WLS / NIST 参考。
- **Table 1** — 不确定度项（**含潮汐项**）。
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

## 6. 参考文献（`paper/refs.bib`，20 篇，全部被引且解析）

`aeppli2026nist` · `pizzocaro2026european` · `beloy2021bacon` · `arnold2026lu` ·
`zhang2026ca` · `grotti2018geodesy` · `mcgrew2018geodesy` · `takamoto2020redshift` ·
`schioppo2022cavities` · `dimarcq2024roadmap` · `riehle2017networks` ·
`riehle2015redefinition` · `lisdat2016network` · `lindvall2025coordinated` ·
`derevianko2014topological` · `wcislo2018global` · `sanner2019lorentz` ·
`laurent2015aces` · `kolkowitz2016gw` · `roberts2017domain`
