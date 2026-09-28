# Abstract (Nature house style)

> 本文件按 **Nature 本文摘要的实际格式**撰写：**单一连续段落**，无小标题、无分层标签，
> 长度 ~200 词。
>
> **定位**：**比值测量本身是本文最大成果**——以秒定义路线图所需精度完成的远程异种光钟
> 频率比测量；潮汐引力红移为**次要发现**。
> 不确定度口径**引用实验方 PDF**（`clock/潮汐修正后的比值计算.pdf`）。数字溯源见文末。

---

## Abstract

Redefining the SI second in terms of an optical transition requires frequency
ratios between clocks of different species, measured across distance, to agree
at the `10⁻¹⁸` level; individual optical clocks already reach this accuracy, but
such inter-species ratios remain the limiting step and few have been verified
at more than one institution. Here we report the most accurate Yb/Sr frequency
ratio so far obtained through a remote, two-institution fibre-link comparison,
by linking a Yb optical clock in Wuhan to a Sr optical clock in Shanghai over a
`~690 km` fibre network. After correcting each one-second sample for the tidal
gravitational-redshift modulation of the geopotential difference, and combining
`1 008 912` retained samples across 17 segments with a Bayesian analysis of the
per-segment scatter, we obtain
`Yb/Sr = 1.207 507 039 343 337 7215(23)`, with a combined fractional uncertainty
of `1.9 × 10⁻¹⁸` — below `5 × 10⁻¹⁸` and marginally better than the NIST
comparison. The value agrees with the NIST reference
within `1.5 × 10⁻¹⁸` and with the European-network value within `3.5 × 10⁻¹⁸`,
establishing reproducibility of the ratio across independent laboratories and
clock species. We further resolve the tidal gravitational-redshift modulation of
the ratio at `A = −0.54 ± 0.08` (about `6.4σ`, 14 of 17 segments sharing the
expected sign), showing that a fibre-linked clock network recovers real
geophysical signals on top of the ratio. This is the second experiment to meet
the roadmap's comparison threshold, and it does so with remotely operated clocks
at two institutions, contributing a verified Yb/Sr record toward the optical
redefinition of the second.

**Keywords:** optical lattice clock; Yb/Sr frequency ratio; fibre-link clock
comparison; SI second redefinition; optical clock network; tidal gravitational
redshift

---

## 中文版（Nature 风格单段）

用光学跃迁重定义国际单位制「秒」，要求不同种类光钟之间的频率比在跨距离条件下符合到
`10⁻¹⁸` 水平；单台光钟已达到该精度，但异种钟比值仍是限制环节，且少有在多个机构独立验证者。
本文报告迄今最精确的 Yb/Sr 频率比之一——通过远程、跨两机构的比对取得：以约 `690 km`
光纤网络连接武汉 Yb 光钟与上海 Sr 光钟。在**逐点扣除潮汐引力红移调制**后，对跨 17 段、
`1 008 912` 个 1 秒样本以**贝叶斯方法**合并段间散布，定出
`Yb/Sr = 1.207 507 039 343 337 7215(23)`，合成分数不确定度 `1.9 × 10⁻¹⁸`——低于
`5 × 10⁻¹⁸`，并小幅优于 NIST 的比对。该值与 NIST 参考值符合在 `1.5 × 10⁻¹⁸` 以内、
与欧洲网络值符合在 `3.5 × 10⁻¹⁸` 以内，确立了该比值在独立实验室与不同钟种间的可重复性。
我们并分辨出该比值上的潮汐引力红移调制，幅度 `A = −0.54 ± 0.08`（约 `6.4σ`，17 段中
14 段同号），表明光纤连接的光钟网络能在比值之上复原真实的地球物理信号。这是第二例达到
路线图比对门槛的实验，且以分处两机构的远程操作光钟完成，为秒的光学重定义贡献了一份经核验的
Yb/Sr 记录。

**关键词：** 光晶格钟；Yb/Sr 频率比；光纤链路钟比对；秒定义重定义；光钟网络；潮汐引力红移

---

## 数值来源

| 数字 | 来源 |
|---|---|
| Yb/Sr = `1.207 507 039 343 337 7215(23)`（**潮汐修正后贝叶斯**结果；WLS `…7213(23)`、M-P `…7214(23)` 为同批数据的其他合并法）| **实验方** `clock/潮汐修正后的比值计算.pdf`（标题：潮汐修正、起止点修正后结果）§5.2–5.4 |
| 合成不确定度 `u = 1.902×10⁻¹⁸`（stat `7.50×10⁻¹⁹` ⊕ clock sys `1.43×10⁻¹⁸` ⊕ static geopotential `1.0×10⁻¹⁸`）| 实验方 PDF §5.6（`current combined u = 1.902321e-18`）|
| 与 NIST 符合 `−1.5×10⁻¹⁸`；与欧洲符合 `+3.5×10⁻¹⁸` | 本库计算（实验方中心值 vs 参考值）|
| NIST 参考 `…7230(37)`（3.1×10⁻¹⁸）；欧洲 `…718(32)` | 实验方 PDF §5.6 引用（Aeppli 2026 PRL 137, 033201；Pizzocaro 2026 PRR 8, 033250）|
| 17 段、`1 008 912` 样本 | `clock_ratio/tidal_correction/summary.json`（`total_samples`）|
| 潮汐 `A = −0.5397 ± 0.0843`，`6.4σ`，14/17 | `clock/segment_analysis/batch_aggregate.csv` |
| 基线 ≈690 km | 本库计算（`REPORT.md` §2.6 与附录 D）|

> **口径声明**：比值中心值、比对不确定度与参考值符合度**引用实验方 PDF**（非本库自算）；
> 该 PDF 标注 **tide model 项未计入**，故 `1.9×10⁻¹⁸` 为未含潮汐模型的估计。本库逐段 `u_i`
> 被独立审查判定不可靠，故本库不据此单独声明比对不确定度。详见 [`REPORT.md`](REPORT.md) §6。
