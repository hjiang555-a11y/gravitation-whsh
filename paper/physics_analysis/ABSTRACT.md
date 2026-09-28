# Abstract（中英双语）

> **占位符填充说明**：`xx 天` → `58`；`NIST-JILA 值XXX` → `1.207 507 039 343 337 7230(37)`；
> `欧洲XXX-XXX 值XXX`（即欧洲网络值）→ `1.207 507 039 343 337 718(32)`。
> 中文正文仅填充 `XX`，未改动其余文字。英文版为对应翻译并润色。数值溯源见文末。

---

## 中文版

比较机构研制的不同种类的光钟的高准确度比对，是以光学跃迁重定义国际单位制「秒」的核心要求：许多台光钟自评估的不确定度已优于 `2 × 10⁻¹⁸`，但满足不确定度优于 `5 × 10⁻¹⁸` 的钟频率比值测量仅有 NIST-JILA 的比值测量仅有 1 次，而且测量结果之间存在大幅差异。本文报道了以网光纤连接的 IAPMST Yb 光钟（武汉）与 USTC Sr 光钟（上海）构建的光钟网络进行的光钟比值测量实验。历时 `58` 天的 17 段测量数据，在扣除潮汐引力红移后，用贝叶斯方法合并段间散布，定出 Yb/Sr = 1.207 507 039 343 337 7215(23)；该值与 NIST-JILA 值 `1.207 507 039 343 337 7230(37)` 相差 −1.5 × 10⁻¹⁸、与欧洲网络值 `1.207 507 039 343 337 718(32)` 相差 +3.5 × 10⁻¹⁸。该比值还携带地球物理信号：跨段分析在 6.4σ 水平上分辨出潮汐引力红移调制，幅度约为参考潮汐模型的一半。扣除潮汐调制后，17 个段之间的内部一致性显著改善，约化卡方由 5.42 降至 3.70（−32%），说明该效应是影响比值的显著项。本实验表明跨城、异种光钟网络技术既给出可支撑重定义的比对，又成为一种探测时变重力势的传感器，可在毫米量级测量引力势差。

**关键词：** 光晶格钟；Yb/Sr 频率比；光纤链路钟比对；秒定义重定义；引力红移；潮汐势

---

## English version

High-accuracy comparison of different-species optical clocks built at different
institutions is a core requirement for redefining the SI second in terms of an
optical transition. Many clocks now achieve self-evaluated uncertainties better
than `2 × 10⁻¹⁸`, yet frequency-ratio measurements between clocks that reach an
uncertainty better than `5 × 10⁻¹⁸` remain rare: only one such NIST–JILA ratio
measurement exists, and the reported results differ substantially from one
another. Here we report a frequency-ratio measurement performed with an optical
clock network that links the IAPMST Yb optical clock (Wuhan) to the USTC Sr
optical clock (Shanghai) through an installed fibre network. From 17 segments of
data spanning `58` days, after correcting for the tidal gravitational redshift,
a Bayesian combination of the inter-segment scatter yields
Yb/Sr = 1.207 507 039 343 337 7215(23). This value differs from the NIST–JILA
value of `1.207 507 039 343 337 7230(37)` by −1.5 × 10⁻¹⁸ and from the European
network value of `1.207 507 039 343 337 718(32)` by +3.5 × 10⁻¹⁸. The ratio also
carries a geophysical signal: a cross-segment analysis resolves the tidal
gravitational-redshift modulation at the 6.4σ level, with an amplitude about
half that of the reference tidal model. After removing this tidal modulation,
the internal consistency among the 17 segments improves markedly, with the
reduced chi-square dropping from 5.42 to 3.70 (−32%), identifying the effect as
a significant term affecting the ratio. This experiment shows that an inter-city,
different-species optical clock network delivers both comparisons able to
support redefinition and a sensor of the time-varying gravitational potential,
capable of measuring geopotential differences at the millimetre level.

**Keywords:** optical lattice clock; Yb/Sr frequency ratio; fibre-link clock
comparison; SI second redefinition; gravitational redshift; tidal potential

---

## 数值溯源

| 数字 | 值 | 来源 |
|---|---|---|
| 历时 | `58` 天（观测跨度）| `clock_ratio/ratio_17seg.csv` 首末时间戳 |
| 段数 / 样本 | `17` 段，`1 008 912` 个 1 秒样本 | `clock_ratio/tidal_correction/summary.json` |
| Yb/Sr | `1.207 507 039 343 337 7215(23)` | 实验方 `clock/潮汐修正后的比值计算.pdf` §5.4 |
| NIST-JILA 参考 | `1.207 507 039 343 337 7230(37)`（相差 −1.5 × 10⁻¹⁸）| 实验方 PDF §5.6 引用（Aeppli 2026, PRL 137, 033201）|
| 欧洲网络参考 | `1.207 507 039 343 337 718(32)`（相差 +3.5 × 10⁻¹⁸）| 实验方 PDF §5.6 引用（Pizzocaro 2026, PRR 8, 033250）|
| 潮汐检出 | `6.4σ`，幅度约为参考模型一半 | `clock/segment_analysis/batch_aggregate.csv` |
| 约化卡方 | `5.42 → 3.70`（`−32%`）| `clock_ratio/statistical_methods_tidal.json`（n_segments=17, dof=16）|

> **口径声明**：比值中心值、不确定度与参考值符合度**引用实验方 PDF**（非本库自算）；该 PDF
> 标注 tide model 不确定度未计入、link/comb 项记为 0。约化卡方降幅为同一 `u_i` 下
> raw→full-tidal 的比较，且**段 9 敏感**（剔除段 9 后反号：`+31.8% → −5.1%`），故称其为
> 「影响比值的显著项」，未称其独立验证了潮汐模型。
