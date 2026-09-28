# Abstract (Nature house style)

> 本文件按 **Nature 本文摘要的实际格式**撰写：**单一连续段落**，无小标题、无分层标签，
> 长度 ~200 词。
>
> **定位（两支柱 / two-pillar）**：
> ① **比值测量**作为计量学主干——异种、跨城、光纤链路的光钟频率比，与当今最精确的两个
>    测定值一致；
> ② **潮汐引力红移**作为科学亮点——跨段组合在比值的时间依赖中分辨出潮汐调制。
>
> **措辞纪律**（经专家评审）：不称 "intercontinental"（武汉—上海为**同城际/跨城
> inter-city**，约 690 km）；不称 "the second experiment"/"roadmap threshold"（无法确证
> 且非硬性阈值）；不称 "most precise"（自报 `u=1.9×10⁻¹⁸` 与「NIST/欧洲最精确」自相
> 矛盾，且该 `u` 未含潮汐模型项、link/comb 项记为 0）。
>
> 不确定度口径**引用实验方 PDF**（`clock/潮汐修正后的比值计算.pdf`）。数字溯源见文末。

---

## Abstract

Comparing clocks of different species across distance is the outstanding
requirement for redefining the SI second on an optical transition: single
optical clocks already reach `10⁻¹⁸` accuracy, but inter-species frequency
ratios verified at more than one institution remain scarce. Here we link a
ytterbium optical lattice clock in Wuhan to a strontium optical lattice clock
in Shanghai through a `690 km` installed-fibre network and operate them as a
single comparison. From `1 008 912` one-second samples across 17 jump-free
segments, and after point-by-point correction of the tidal gravitational
redshift, a Bayesian combination of the per-segment scatter gives
`Yb/Sr = 1.207 507 039 343 337 7215(23)`, differing from the NIST and
European-network values by `−1.5 × 10⁻¹⁸` and `+3.5 × 10⁻¹⁸`; the three
determinations, obtained with independent clocks, links and continents, agree
within `5 × 10⁻¹⁸`. The same ratio carries a geophysical signal: a cross-segment
analysis detects the tidal gravitational-redshift modulation at `6.4σ`
(`14` of `17` segments sharing the expected sign; Stouffer `z = 5.87`, Fisher
`p = 2.2 × 10⁻⁶`), with an amplitude about half that of the reference tidal
model. Inter-city, heterogeneous clock networks thus deliver both
redefinition-grade comparisons and a sensor of the time-varying geopotential.

**Keywords:** optical lattice clock; Yb/Sr frequency ratio; fibre-link clock
comparison; SI second redefinition; gravitational redshift; tidal potential

---

## 中文版（Nature 风格单段）

跨距离比较不同种类的光钟，是以光学跃迁重定义国际单位制「秒」的核心要求：单台光钟已达
`10⁻¹⁸` 精度，但在多个机构验证过的异种钟频率比依然稀缺。本文以 `690 km` 现网光纤连接
武汉 Yb 光晶格钟与上海 Sr 光晶格钟，将其作为一个比对系统运行。从跨 17 段无跳点窗口的
`1 008 912` 个 1 秒样本出发，在**逐点扣除潮汐引力红移**后，用**贝叶斯方法**合并段间散布，
定出 `Yb/Sr = 1.207 507 039 343 337 7215(23)`，与 NIST 值相差 `−1.5 × 10⁻¹⁸`、与欧洲
网络值相差 `+3.5 × 10⁻¹⁸`；三个由独立光钟、独立链路、不同大陆得到的测定值在
`5 × 10⁻¹⁸` 内一致。该比值还携带地球物理信号：跨段分析在 **`6.4σ`** 水平上分辨出潮汐引力
红移调制（17 段中 14 段同号；Stouffer `z = 5.87`，Fisher `p = 2.2 × 10⁻⁶`），幅度约为
参考潮汐模型的一半。跨城、异种光钟网络由此既给出可支撑重定义的比对，又成为一种探测
时变重力势的传感器。

**关键词：** 光晶格钟；Yb/Sr 频率比；光纤链路钟比对；秒定义重定义；引力红移；潮汐势

---

## 数值来源

| 数字 | 来源 |
|---|---|
| Yb/Sr = `1.207 507 039 343 337 7215(23)`（**潮汐修正后贝叶斯**结果；WLS `…7213(23)`、M-P `…7214(23)` 为同批数据的其他合并法）| **实验方** `clock/潮汐修正后的比值计算.pdf`（标题：潮汐修正、起止点修正后结果）§5.2–5.4 |
| 合成不确定度 `u = 1.902×10⁻¹⁸`（stat `7.50×10⁻¹⁹` ⊕ clock sys `1.43×10⁻¹⁸` ⊕ static geopotential `1.0×10⁻¹⁸`；**tide model 项未计入**、link/comb 项记为 0）| 实验方 PDF §5.6（`current combined u = 1.902321e-18`）|
| 与 NIST 符合 `−1.5×10⁻¹⁸`；与欧洲符合 `+3.5×10⁻¹⁸`；三者互相符合 `5×10⁻¹⁸` | 本库计算（实验方中心值 vs 参考值；NIST−欧洲 = 5.0×10⁻¹⁸）|
| NIST 参考 `…7230(37)`（`3.1×10⁻¹⁸`）；欧洲网络 `…718(32)` | 实验方 PDF §5.6 引用（Aeppli 2026, PRL 137, 033201；Pizzocaro 2026, PRR 8, 033250）|
| 欧洲网络基准值（供对比）：7 台钟 / 4 机构，比值不确定度 `7.7×10⁻¹⁸–6.1×10⁻¹⁷` | Pizzocaro 2026 摘要（arXiv:2604.27963）|
| BACON 2021 Yb/Sr `6.8×10⁻¹⁸` | `paper/3104.pdf`（Beloy et al., Nature 591, 564 (2021)）|
| 17 段、`1 008 912` 样本 | `clock_ratio/tidal_correction/summary.json`（`total_samples`）|
| 潮汐 `A = −0.5397 ± 0.0843`，`6.4σ`，14/17 同号，Stouffer `5.873404`，Fisher `2.15×10⁻⁶` | `clock/segment_analysis/batch_aggregate.csv` |
| 基线 ≈690 km | 本库计算（`REPORT.md` §2.6 与附录 D）|

> **口径与措辞声明（重要）**：
> 1. 比值中心值、比对不确定度与参考值符合度**引用实验方 PDF**（非本库自算）。
> 2. 该 PDF 标注 **tide model 不确定度未计入**（`NaN`，待模型不确定度），且 link/comb
>    项记为 0；故 `1.9×10⁻¹⁸` 为**未含潮汐模型项**的估计，不能据此声明「最精确」。
> 3. 本库逐段 `u_i` 被独立审查判定不可靠（OADEV 外推低估 30–40%），故本库不据此单独
>    声明比对不确定度。详见 [`REPORT.md`](REPORT.md) §6。
> 4. 摘要只声称**一致性**（在 `5×10⁻¹⁸` 内）与**探测**（潮汐 `6.4σ`），**不**声称刷新
>    精度纪录、不声称「达到重定义阈值」、不声称「第二例」。
> 5. 潮汐幅度约为参考模型的一半——这是**开放系统项**，摘要如实标注，未解释为与 GR 的
>    偏差或符合。
