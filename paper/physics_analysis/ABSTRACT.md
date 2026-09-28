# Abstract（中英双语，按用户定稿框架润色）

> 本文件按用户提供的摘要框架撰写：**比对不同机构研制、不同种类光钟的高准确度频率比**，
> 定位到秒定义路线图。
>
> **占位符 `XX` 已按库内产物与实验方 PDF 填充**，全部数值见文末溯源表。英文为投稿语言。
>
> **机构口径**：库内未记录机构名称；按用户提供——武汉 Yb 光钟为**精测院**
> （中国科学院精密测量科学与技术创新研究院，APM/CAS，武汉），上海 Sr 光钟为
> **中国科学技术大学**（USTC，上海）。

---

## English version

High-accuracy comparison of different-species optical clocks built at different
institutions is a core requirement for redefining the SI second on an optical
transition. Many clocks now report self-evaluated uncertainties below
`2 × 10⁻¹⁸`, yet frequency-ratio measurements between clocks with uncertainties
better than `5 × 10⁻¹⁸` remain rare — only a single NIST–JILA Sr/Yb comparison
has reached this level, and repeated ratio determinations still disagree
substantially. Here we report a ratio measurement using an optical-clock network
that links a Yb optical clock of the Innovation Academy for Precision
Measurement Science and Technology (Wuhan) to a Sr optical clock of the
University of Science and Technology of China (Shanghai) through a `~690 km`
installed-fibre network. From 17 segments of data spanning 58 days, and after
correcting for the tidal gravitational redshift, a Bayesian combination of the
per-segment scatter gives `Yb/Sr = 1.207 507 039 343 337 7215(23)`. This value
differs from the NIST–JILA value by `−1.5 × 10⁻¹⁸` and from the European-network
value by `+3.5 × 10⁻¹⁸`. The ratio also carries a geophysical signal: a
cross-segment analysis resolves the tidal gravitational-redshift modulation at
`6.4σ`, with an amplitude about half that of the reference tidal model.
Correcting this tidal modulation markedly improves the inter-segment consistency
of all 17 groups, reducing the reduced chi-square from `5.42` to `3.70` (`−32%`),
identifying the effect as a significant term in the ratio. The experiment shows that an
inter-city, different-species optical-clock network delivers both
redefinition-grade comparisons and a sensor of the time-varying gravitational
potential, capable of measuring geopotential differences at the millimetre
level.

**Keywords:** optical lattice clock; Yb/Sr frequency ratio; fibre-link clock
comparison; SI second redefinition; gravitational redshift; tidal potential

---

## 中文版

比较机构研制的不同种类的光钟的高准确度比对，是以光学跃迁重定义国际单位制「秒」的核心
要求：许多台光钟自评估不确定度已优于 `2 × 10⁻¹⁸`，但满足不确定度优于 `5 × 10⁻¹⁸` 的钟
频率比值测量仅有 NIST–JILA 的 Sr/Yb 比值测量 1 次，且多次测量的比值还大幅度不相符。本文
报道了以网光纤连接的**精测院 Yb 光钟（武汉）**与**中国科学技术大学 Sr 光钟（上海）**构建
的光钟网络所进行的光钟比值测量实验。历时 `58` 天的 17 段测量数据，在扣除潮汐引力红移后，
用**贝叶斯方法**合并段间散布，定出 `Yb/Sr = 1.207 507 039 343 337 7215(23)`；该值与
NIST–JILA 值相差 `−1.5 × 10⁻¹⁸`、与欧洲网络值相差 `+3.5 × 10⁻¹⁸`。该比值还携带地球
物理信号：跨段分析在 `6.4σ` 水平上分辨出潮汐引力红移调制，幅度约为参考潮汐模型的一半。
扣除潮汐调制后，17 个段之间的内部一致性显著改善，约化卡方由 `5.42` 降至 `3.70`（`−32%`），
说明该效应是影响比值的显著项。本实验表明跨城、异种光钟网络技术既给出可支撑重定义的比对，
又成为一种探测时变重力势的传感器，可在**毫米量级**测量引力势差。

**关键词：** 光晶格钟；Yb/Sr 频率比；光纤链路钟比对；秒定义重定义；引力红移；潮汐势

---

## 数值溯源（XX 填充依据）

| 占位符 / 数字 | 值 | 来源 |
|---|---|---|
| 历时 `xx` 天 | `58` 天（观测跨度；有效 11.68 天，占空比 20.1%）| `clock_ratio/ratio_17seg.csv` 首末时间戳 |
| 段数 | `17` 段，`1 008 912` 个 1 秒样本 | `clock_ratio/tidal_correction/summary.json` |
| Yb/Sr | `1.207 507 039 343 337 7215(23)`（**潮汐修正后贝叶斯**）| **实验方** `clock/潮汐修正后的比值计算.pdf` §5.4 |
| 与 NIST–JILA 相差 | `−1.5 × 10⁻¹⁸` | 本库计算（实验方中心值 vs NIST `…7230(37)`）|
| 与欧洲网络相差 | `+3.5 × 10⁻¹⁸` | 本库计算（vs Pizzocaro 2026 `…718(32)`）|
| 潮汐检出 | `6.4σ`；`A = −0.5397 ± 0.0843`；14/17 同号 | `clock/segment_analysis/batch_aggregate.csv` |
| 约化卡方 | `5.423 → 3.699`（`−31.8%`）| `clock_ratio/statistical_methods_tidal.json` |
| 基线 | `~690 km`（大圆 687 km）| 本库计算（`REPORT.md` §2.6）|
| 毫米量级引力势差 | 合并 `u = 1.9 × 10⁻¹⁸` ↔ `ΔW = 0.171 m²/s²` ↔ `~17 mm`；贝叶斯统计项 `7.5 × 10⁻¹⁹` ↔ `~7 mm`；WLS 统计项 `4.8 × 10⁻¹⁹` ↔ `~4 mm` | `1×10⁻¹⁸ ↔ ~1 cm`（McGrew 2018）；本库换算 |

> **口径与措辞声明（重要，须随文携带）**：
> 1. **机构名称**（精测院 / 中国科学技术大学）为**用户提供**，库内无记录；投稿前请以实验方
>    正式署名为准。
> 2. **「仅有 NIST–JILA 的 Sr/Yb 1 次」** 为秒定义路线图口径下的表述：BACON（NIST+JILA，
>    2021）Yb/Sr 为 `6.8 × 10⁻¹⁸`，NIST（Aeppli 2026）Yb/Sr 为 `3.1 × 10⁻¹⁸`（`≤3.2 × 10⁻¹⁸`），
>    欧洲网络（Pizzocaro 2026，7 台钟 / 4 机构）比值不确定度 `7.7 × 10⁻¹⁸–6.1 × 10⁻¹⁷`。
>    本摘要沿用用户对「满足优于 `5 × 10⁻¹⁸` 者仅 1 次」的界定。
> 3. **比对不确定度 `1.9 × 10⁻¹⁸`** 引用实验方 PDF；该 PDF 标注 **tide model 项未计入**
>    （`NaN`），link/comb 项记为 0。故不据此声称「最精确」。
> 4. **约化卡方 `−32%`** 为同一 `u_i` 下 raw→full-tidal 的比较（本库重算），且**段 9 敏感**
>    （剔除段 9 后反号：`+31.8% → −5.1%`）；故称「改善内部一致性、是显著项」，**不**称其
>    独立验证了潮汐模型。
> 5. **毫米量级**为**统计精度**口径（WLS 统计项 `4.8 × 10⁻¹⁹` ↔ `~4 mm`，贝叶斯统计项
>    `7.5 × 10⁻¹⁹` ↔ `~7 mm`）；合并时钟系统项后 `1.9 × 10⁻¹⁸` 对应 `~17 mm`。措辞宜写
>    「毫米量级」并保留该换算来源，勿将 `(23)` 记法误读为 `2.3 × 10⁻¹⁸`。
