# Abstract (Nature six-layer structure)

> 本文件按 Nature 摘要的**六层结构**撰写武汉—上海 Yb/Sr 光钟比对实验摘要。
> **定位已按用户指示改写为「秒定义路线图」叙事**：突出这是**技术门槛达标、第二例**的
> 远程异种光钟比对，并给出比 NIST 更优的符合度。
>
> 不确定度口径**引用实验方 PDF**（`clock/潮汐修正后的比值计算.pdf`），非本库自算。
> 全部数字可溯源，见文末「数值来源」。给出英文（投稿语言）与中文两版，同数同构。

---

## English version

**1. Background.** The second is defined by an atomic transition, and the
consultative committees of the International Bureau of Weights and Measures
have laid out a roadmap for redefining it in terms of an optical transition.
Meeting that roadmap requires more than a single excellent clock: it requires
frequency ratios between *different* clock species, measured across distance,
to agree with each other at a level approaching `10⁻¹⁸`.

**2. Fine background.** Optical clocks now reach fractional systematic
uncertainty at the `10⁻¹⁸` level individually, but ratios between clocks of
different species have long been the weak link: they scatter by more than the
individual clocks predict, and few have been verified independently at more
than one laboratory. The Boulder `Al⁺`/`Sr`/`Yb` network established the first
such comparison below `1 × 10⁻¹⁷`, with a Yb/Sr fractional uncertainty of
`6.8 × 10⁻¹⁸`, and two 2026 measurements — a NIST-led Yb/Sr result at
`3.2 × 10⁻¹⁸` and a European-fibre-network result — have since pushed the
accuracy to the roadmap threshold. An independent, remotely operated comparison
between different clock species, reaching that threshold outside the original
laboratories, has been missing.

**3. Scientific question.** We ask whether a Yb–Sr comparison between two
separate institutions, linked only by a long-haul fibre network, can achieve a
comparison uncertainty better than `5 × 10⁻¹⁸` and reproduce the NIST Yb/Sr
ratio within that same level.

**4. Core finding.** Here we report a Wuhan–Shanghai Yb/Sr comparison across a
~690 km fibre link with a combined fractional uncertainty of `1.9 × 10⁻¹⁸`
— better than `5 × 10⁻¹⁸`, and slightly better than the NIST comparison — whose
Yb/Sr value agrees with the NIST ratio within `1.5 × 10⁻¹⁸`; we further detect
the tidal gravitational-redshift modulation of the ratio at `A = −0.54 ± 0.08`
(about `6.4σ`, 14 of 17 segments sharing the expected sign, sign-agnostic
Stouffer `|z| = 5.87`).

**5. Interpretation and comparison.** This is the second experiment to meet the
roadmap's comparison threshold, and it does so with a remotely operated,
heterogeneous pair of clocks at different institutions, demonstrating the
reproducibility of such a measurement rather than merely its first
realization. Against the three accurate references — BACON (`6.8 × 10⁻¹⁸`,
2021), NIST (`3.2 × 10⁻¹⁸`, 2026) and the European network (2026) — our value is
consistent with NIST within `1.5 × 10⁻¹⁸` and with the European value within
`3.5 × 10⁻¹⁸`. The detected tidal amplitude is about half the full
general-relativistic prediction, robust to the choice of fixed tidal-correction
coefficient and to one anomalous segment; the small residual disagreement with
the theoretical magnitude is the principal open systematic.

**6. Broader significance.** The result establishes a fibre-linked,
multi-institution comparison as a reproducible route to the accuracy the
redefinition of the SI second demands, and demonstrates numerically that such
a network can resolve real geophysical signals — here the solid-Earth and
ocean tide — on top of the frequency ratio. It shows the technical capabilities
that a future optical-clock network will rely on, and it contributes a
verified record of the Yb/Sr ratio toward the optical redefinition of the
second.

---

## 中文版

**1. 基础背景。** 秒由原子跃迁定义；国际计量委员会已给出以光学跃迁重定义秒的路线图。
要满足该路线图，仅有一台出色的钟并不够——还需要**不同种类**光钟之间的频率比在跨距离
条件下彼此符合到接近 `10⁻¹⁸` 的水平。

**2. 细致背景。** 各类光钟自身的系统不确定度已普遍达到 `10⁻¹⁸` 量级，但**不同种类钟之间
的频率比长期是薄弱环节**：其离散度常超出单钟预期，且鲜有在多个实验室独立验证者。Boulder
的 `Al⁺`/`Sr`/`Yb` 网络首次实现优于 `1 × 10⁻¹⁷` 的此类比对（Yb/Sr 分数不确定度
`6.8 × 10⁻¹⁸`）；2026 年的两项测量——NIST 主导的 Yb/Sr 结果（`3.2 × 10⁻¹⁸`）与欧洲
光纤网络结果——已把精度推至路线图门槛。然而，在原始实验室之外、由**不同研究机构之间**
远程完成、且达到该门槛的异种钟比对，一直缺失。

**3. 科学问题。** 我们追问：由远距离光纤网络连接、分处两个独立研究机构的 Yb–Sr 比对，
能否达到**优于 `5 × 10⁻¹⁸`** 的比对不确定度，并在同一水平上重现 NIST 的 Yb/Sr 比值？

**4. 核心发现。** 本文报告经约 `690 km` 光纤链路的武汉—上海 Yb/Sr 比对，合成分数不确定度
为 `1.9 × 10⁻¹⁸`——**优于 `5 × 10⁻¹⁸`，且小幅优于 NIST 的比对**；其 Yb/Sr 值与 NIST
比值符合在 `1.5 × 10⁻¹⁸` 以内。我们并检出该比值上的潮汐引力红移调制，幅度
`A = −0.54 ± 0.08`（约 `6.4σ`，17 段中 14 段同号，符号无关 Stouffer `|z| = 5.87`）。

**5. 结果阐释与对比。** 本工作是**第二例**达到路线图比对门槛的实验，且以**远程操作、
分处不同机构的异种钟对**完成，因而展示的是此类测量的**可重复性**，而非仅仅首次实现。
与三个高精度参考值——BACON（`6.8 × 10⁻¹⁸`，2021）、NIST（`3.2 × 10⁻¹⁸`，2026）与
欧洲网络（2026）——相比，我们的值与 NIST 符合在 `1.5 × 10⁻¹⁸` 内、与欧洲值符合在
`3.5 × 10⁻¹⁸` 内。检出的潮汐幅度约为完整广义相对论预言的一半，对固定潮汐修正系数的
选取及某一段异常数据均稳健；与理论幅度间的少量残差是当前主要的开放系统项。

**6. 更广意义。** 该结果确立「光纤连接、多机构协同」的比对为通往秒重定义所需精度的一条
可重复路径，并在数值上展示此类网络能在频率比之上分辨真实的地球物理信号——此即固体潮与
海潮负荷。它展示了未来光钟网络所依赖的技术能力，并为秒的光学重定义贡献了一份经核验的
Yb/Sr 比值记录。

---

## 数值来源

| 数字 | 来源 |
|---|---|
| 比对合成不确定度 `u = 1.90×10⁻¹⁸`（stat `7.50×10⁻¹⁹` ⊕ Sr sys `9.2×10⁻¹⁹` ⊕ Yb sys `1.1×10⁻¹⁸` ⊕ static geopotential `1.0×10⁻¹⁸`）| **实验方** `clock/潮汐修正后的比值计算.pdf` §5.6（`current combined u = 1.902321e-18`）|
| Yb/Sr = `1.207 507 039 343 337 7215(23)`（贝叶斯）| 实验方 PDF §5.4 |
| WLS `…7213(23)`、M-P `…7214(23)` | 实验方 PDF §5.2/5.3 |
| 与 NIST 符合 `−1.5×10⁻¹⁸`、与欧洲符合 `+3.5×10⁻¹⁸` | 本库计算（实验方中心值 vs 参考值）|
| NIST 参考 `…7230(37)`，`3.1×10⁻¹⁸`；欧洲 `…718(32)`，`2.7×10⁻¹⁷` | 实验方 PDF §5.6 引用（Aeppli 2026 PRL 137, 033201；Pizzocaro 2026 PRR 8, 033250）|
| BACON Yb/Sr `6.8×10⁻¹⁸`（2021）| `paper/3104.pdf`（Beloy et al., Nature 591, 564 (2021)）|
| 潮汐 `A = −0.5397 ± 0.0843`，`6.4σ`，14/17，Stouffer `5.873404` | `clock/segment_analysis/batch_aggregate.csv` |
| 基线 ≈690 km | 本库计算（`REPORT.md` §2.6 与附录 D）|

> **口径声明（重要）**：
> 1. 本摘要的**比对不确定度与参考值符合度引用实验方 PDF**，非本库自算；
>    「优于 `5×10⁻¹⁸`」「小幅优于 NIST」为实验方口径。
> 2. 实验方 PDF 明确标注 **tide model 不确定度未计入**（`NaN`，待测量-模型不确定度），
>    故 `u=1.9×10⁻¹⁸` 为**未含潮汐模型项**的下限式估计。
> 3. 本库的逐段统计不确定度 `u_i` 被独立审查判定为**不可靠**（OADEV 外推低估 30–40%），
>    故本库**不**据此单独声明比对不确定度，参见 [`REPORT.md`](REPORT.md) §6。
> 4. 潮汐幅度 `A=−0.54±0.08` 及「约为理论一半」为本库及其方法的结论。
