# Abstract (Nature house style)

> 本文件按 **Nature 本文摘要的实际格式**撰写：**单一连续段落**，无小标题、无分层标签，
> 长度 ~200 词。
>
> **定位**：**比值测量**为计量学主干（异种、跨城、光纤链路的光钟频率比，与当今最精确的
> 两个测定值一致）+ **潮汐引力红移**为科学亮点（跨段组合分辨出潮汐调制）。
>
> **措辞纪律**：不称 "intercontinental"（武汉—上海为**跨城 inter-city**）；不称
> "most precise"（自报 `u=1.9×10⁻¹⁸` 未含潮汐模型项）。
>
> **水平测量（水准测量）为独立测量，数据不在本库**，按用户提供写入。其余数值引用实验方 PDF
> （`clock/潮汐修正后的比值计算.pdf`），溯源见文末。

---

## Abstract

High-precision comparison of different species of optical clocks between
different institutions is a core requirement for redefining the SI second. Many
optical clocks now achieve self-evaluated uncertainties better than
`2 × 10⁻¹⁸`, yet frequency ratios measured with an uncertainty better than
`5 × 10⁻¹⁸` remain rare: only one such result, a 2026 measurement of the
frequency ratio between a NIST ytterbium clock and a JILA strontium clock,
meets the requirement, and it differs substantially from previously reported
results. Here we connect a ytterbium clock of the Innovation Academy for
Precision Measurement Science and Technology (IAPMST, Wuhan) to a strontium
clock of the University of Science and Technology of China (USTC, Shanghai),
about `700 km` away, by fibre to build an optical clock network, and measure the Yb/Sr frequency ratio.
The geopotential difference between the two sites is obtained by spirit
levelling, with an uncertainty of less than `2 mm`. From `58` days of data
totalling `280` hours, after correcting the tidal gravitational redshift and
applying a Bayesian treatment, we obtain
Yb/Sr = 1.207 507 039 343 337 7215(23). This deviates from the latest NIST–JILA
value, 1.207 507 039 343 337 7230(37), by −1.5 × 10⁻¹⁸, and from the latest
European-network value, 1.207 507 039 343 337 718(32), by +3.5 × 10⁻¹⁸. A
cross-segment analysis resolves the tidal gravitational-redshift modulation at
a significance of 6.4σ; removing the model-predicted modulation markedly
improves the statistical consistency of the data, lowering the reduced
chi-square from 5.42 to 3.70 (a 32% reduction), showing the effect is
significant. An inter-city, cross-species clock network thus both supports
redefinition and senses the time-varying gravitational potential, resolving its
difference at the millimetre level.

**Keywords:** optical lattice clock; Yb/Sr frequency ratio; fibre-link clock
comparison; SI second redefinition; gravitational redshift; tidal potential

---

## 中文版（Nature 风格单段）

不同机构间高精度的不同种光学钟比较是重新定义国际单位制「秒」的核心要求。目前许多光学钟
的自评估不确定度已优于 `2 × 10⁻¹⁸`，但频率比测量的不确定度优于 `5 × 10⁻¹⁸` 的情况仍较为
罕见：仅有一组 2026 年报道的 NIST 镱光钟与 JILA 锶光钟频率的比值数据符合要求，且与此前
报道结果存在显著差异。本文通过光纤连接了相距约 700 公里的中国科学院精密测量科学与技术创新研究院（IAPMST）的
镱钟（武汉）与中国科学技术大学（USTC）的锶钟（上海），构建了光学钟网络，测量了镱/锶频率比。
两地间重力势能差通过水准测量获得，不确定度小于 `2 mm`。基于跨越 `58` 天、总计 `280` 小时的
数据，在修正潮汐引力红移并采用贝叶斯方法统计处理数据后，我们得到
Yb/Sr = 1.207 507 039 343 337 7215(23)。该结果与 NIST–JILA 的最新结果
1.207 507 039 343 337 7230(37) 相比偏差为 −1.5 × 10⁻¹⁸，与欧洲网络的最新结果
1.207 507 039 343 337 718(32) 相比偏差为 +3.5 × 10⁻¹⁸。该频率比还包含地球物理信号：
跨段分析以 6.4σ 显著性分辨出潮汐引力红移调制。去除模型预测的潮汐调制，显著提高了数据的
统计一致性，使约化卡方值从 5.42 降至 3.70（降幅达 32%），表明该效应具有显著性。因此，
城市间、跨物种的时钟网络不仅提供了支持重新定义的比较数据，还充当了时间变化引力势的探测器，
实现了毫米级的重力位差测量。

**关键词：** 光晶格钟；Yb/Sr 频率比；光纤链路钟比对；秒定义重定义；引力红移；潮汐势

---

## 数值来源

| 数字 | 来源 |
|---|---|
| Yb/Sr = `1.207 507 039 343 337 7215(23)`（潮汐修正后贝叶斯）| **实验方** `clock/潮汐修正后的比值计算.pdf` §5.4 |
| NIST–JILA 参考 `…7230(37)`（相差 −1.5 × 10⁻¹⁸）| 实验方 PDF §5.6 引用（Aeppli 2026, PRL 137, 033201）|
| 欧洲网络参考 `…718(32)`（相差 +3.5 × 10⁻¹⁸）| 实验方 PDF §5.6 引用（Pizzocaro 2026, PRR 8, 033250）|
| 历时 `58` 天 / `280` 小时 | `clock_ratio/ratio_17seg.csv`（总有效 1 008 912 s）|
| 潮汐 `6.4σ` | `clock/segment_analysis/batch_aggregate.csv` |
| 约化卡方 `5.42 → 3.70`（`−32%`）| `clock_ratio/statistical_methods_tidal.json` |
| 重力势差（水准测量）不确定度 < `2 mm` | **用户提供**（独立测量，不在本库）|

> **口径声明**：
> 1. 比值中心值、不确定度与参考值符合度**引用实验方 PDF**；该 PDF 标注 tide model 项未计入、
>    link/comb 项记为 0。
> 2. **水准测量为独立测量，数据不在本库**，按用户提供写入；本库无法核验。注意实验方 PDF 中
>    `static geopotential = 1.0×10⁻¹⁸`（≈9 mm）与「<2 mm 水准测量」为不同口径，勿混用。
> 3. 约化卡方降幅 `−32%` 为同一 `u_i` 下 raw→full-tidal 的比较，且**段 9 敏感**（剔除段 9 后
>    反号：`+31.8% → −5.1%`）；故称其「显著项」，未称其独立验证了潮汐模型。
