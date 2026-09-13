# 论文段落草稿：钟比值计算、引力潮汐效应与潮汐修正

> 本文件是**论文散文草稿**，不是分析产物。所有数值均可溯源到本库已核验的产物；
> 每个数值后标注来源文件。公式为 LaTeX 就绪格式。配图见
> [`clock_ratio/paper_figs/`](../clock_ratio/paper_figs/)，由图脚本
> [make_paper_figures.py](../clock_ratio/make_paper_figures.py) 生成（不覆盖任何旧图）。

---

## §1 钟比值计算（Methods: clock-ratio determination）

> **配图**：图 1（[fig1_ratio_segments.png](../clock_ratio/paper_figs/fig1_ratio_segments.png)），
> 逐段 $R_i$ 的偏差 $y_i$。

武汉—上海两地光钟（Yb/Sr）经 1550 nm 光纤链路远程比对。记第 $i$ 段最长无跳点拍频序列为
$b_i(t)$、全局中位数 $m$，则段内拍频偏差为

$$\overline{\delta b}_i \;=\; \overline{b_i} - m .$$

Sr 端系统频移修正 $a_i$ 与 Yb 端修正 $b_{\mathrm{Yb}}$ 合成 Dr 系数后，第 $i$ 段 Yb/Sr
比值由完整反演给出

$$R_i \;=\; \bigl[\,\mathrm{ratio\_base}_i + \mathrm{Dr}_i\,\bigr]^{-1}\times(1+\delta_g),
\qquad \delta_g=-3.116\times10^{-15},$$

全程以 80 位十进制精度（`Decimal80`，镜像 MATLAB `vpa(...,80)`）计算，避免 $10^{-18}$
量级差异被双精度舍入破坏（float64 绝对精度约 $2.6\times10^{-16}$）。整个实验的时长加权
中心值为

$$R_{\text{duration}} \;=\; \frac{\sum_i n_i R_i}{\sum_i n_i},
\qquad \sum_i n_i = 1{,}008{,}912,$$

得基线中心 $R_{\text{duration}} = 1.207\,507\,039\,343\,337\,720\,369\,6$（未做潮汐修正）。

> *数值来源*：`clock_ratio/ratio_17seg.csv`、`clock_ratio/tidal_correction/summary.json`
> （raw 情景）。图 1 显示 17 段偏差 $y_i=R_i/R_{\text{seg1}}-1$ 的时长加权均值为
> $-0.482\times10^{-18}$（算术均值 $+0.102\times10^{-18}$），段间散布
> $\sigma(y_i)=2.98\times10^{-18}$。

---

## §2 引力潮汐效应（Results: tidal gravitational-redshift detection）

> **配图**：图 2（[fig2_tidal_detection.png](../clock_ratio/paper_figs/fig2_tidal_detection.png)），
> 逐段潮汐幅度拟合 $A_i$。

潮汐（固体潮 + 海潮负荷）改变两站重力势差
$\Delta W(t)=W_{\text{WUHN}}(t)-W_{\text{SHAO}}(t)$，经广义相对论引力红移在比对频率中
留下

$$\frac{\Delta f}{f} \;=\; \frac{\Delta W(t)}{c^{2}},$$

其 rms 幅度约 $4.8\times10^{-18}$。段内 1200-s 三角窗投影后单段信噪比仅
$\mathrm{SNR}\approx0.28$，故 17 段中单段均不显著（图 2）；但跨段合并后符号一致性显著：

$$14/17\ \text{段同号}\ (p=0.013),\qquad
\text{Stouffer }|z|=5.87\ (p=4.3\times10^{-9}),\qquad
\text{Fisher }p=2.2\times10^{-6}.$$

拟合幅度 $A=-0.54\pm0.08$（距零约 $6.4\sigma$）：潮汐信号以**正确的方向、约理论
幅度一半**的强度被检出。段均值层面，$y_i$ 与会话潮汐频移 $\Delta f/f$ 正相关，
Pearson $r=+0.518\ (p=0.033)$。

> *数值来源*：`clock/segment_analysis/batch_aggregate.csv`、
> `clock_ratio/correlation_reanalysis.csv`。

---

## §3 潮汐修正的合理性与数值（Tidal correction: validity and magnitude）

> **配图**：图 3（[fig3_correction.png](../clock_ratio/paper_figs/fig3_correction.png)）
> 长期稳定度与组间一致性；图 4
> （[fig4_methods_summary.png](../clock_ratio/paper_figs/fig4_methods_summary.png)）
> 四方法中心值。

潮汐修正的依据是**修正后残差应与潮汐模板不再系统相关**。本文采用固定响应系数的两个
情景，而非重新拟合：

$$b_{\text{corr}}(t)=b_{\text{raw}}(t)-A\,h(t),\qquad
h(t)=F_{1550}\,\frac{\Delta W(t)}{c^{2}},\qquad
F_{1550}=N_{1550}^{\text{WH}}f_{\text{rep}}=193.3992\ \text{THz},$$

其中 `theory` 取 $A=-1$（完全信任专业潮汐数据与相对论引力理论），`empirical` 取
$A=-0.54$（信任波形、按历史拟合幅度）。

**合理性（方向自检）** 以 $A_{\text{fix}}=-0.54$ 修正后，残差与模板的段均值相关系数由
$-0.134$ 塌缩到 $+0.003$，带符号 Stouffer $z$ 由 $-5.16$ 降至 $+0.39\ (p=0.69)$，
负相关段降为 $8/17$（随机，$p=1.000$）；扫描 $A_{\text{fix}}$ 得到的残差相关性零点
恰为 $-0.54$，与历史精度加权幅度 $-0.5397\pm0.084$ 一致。这从「修正后相关性消失」
直接确认 $A=-0.54$ 的**符号与幅度均正确**，且不依赖尚未定定的梳尺/本振符号因子
$s_{\text{beat}}$。

**数值** 修正使整个实验时长加权中心由基线 $1.207\,507\,039\,343\,337\,720\,37$ 上移：

| 情景 | $A$ | $R_{\text{duration}}$ | 与基线差（$10^{-18}$） |
|---|---|---|---|
| raw | 0 | $1.207\,507\,039\,343\,337\,720\,37$ | 0 |
| theory | $-1$ | $1.207\,507\,039\,343\,337\,720\,81$ | $+0.44$ |
| empirical | $-0.54$ | $1.207\,507\,039\,343\,337\,720\,61$ | $+0.24$ |

与实验方含潮汐逐点修正的参考 $1.207\,507\,039\,343\,337\,721\,3(23)$ 的偏差（**时长加权
口径**）由基线的 $-0.93\times10^{-18}$ 收敛到 `theory` 的 $-0.49\times10^{-18}$、
`empirical` 的 $-0.69\times10^{-18}$（两者都朝参考值方向）；若改用**精度加权 WLS 中心**
（权重 $1/u_i^2$，与实验方同口径），偏差为基线 $-0.50$、`theory` $+0.39$、`empirical$
$-0.04\times10^{-18}$，即 `empirical` 最接近参考。组间一致性以 $\chi^2_{\text{red}}$
衡量：基线 $5.42\to$ `theory` $3.70$（$-31.8\%$）、`empirical` $4.56$（$-15.9\%$）；
似然比 $\Delta\chi^2=27.6$（dof=1，$p=1.5\times10^{-7}$，约 $5.3\sigma$），说明补偿
**高度显著地**改善组间一致性。四种统计合并方法（WLS / Birge / Mandel–Paule / 贝叶斯）
给出一致的变化方向（图 4）。

> *数值来源*：`clock_ratio/tidal_correction/summary.json`、
> `clock_ratio/statistical_methods_tidal.json`；方向自检见
> [METHODOLOGY §9.5](METHODOLOGY.md)。

---

## §4 口径边界（论文必须如实写出，非缺陷而是可信度来源）

1. **$u_i$ 不可靠**：每段统计不确定度由 OADEV 外推（$128$–$T/4$ s）得到，flicker 地板
   使全体段系统性低估约 30–40%，叠加个别段（5/6/16）异常，故合并值仅供方法比较，
   **不作最终不确定度声明**。
2. **$A=-0.54$ 的 DC 假设**：该幅度来自历史**去均值波形**拟合；将其用于未去均值模板的
   DC（均值）部分是额外假设，非校准。
3. **段 9 敏感性**：剔除 `shift_a` 异常的段 9 后，潮汐补偿「降低 $\chi^2_{\text{red}}$」
   的效应大幅减弱甚至反号（`theory` 相对基线由 $+31.8\%$ 变为 $-5.1\%$），即该改善
   **高度依赖段 9**——段 9 的 `shift_a` 真实性未定前须谨慎解读。
4. **固定负号**：为指定响应约定，未新解决硬件极性问题。

---

## 图目录

| 图 | 文件 | 对应段落 | 内容 |
|---|---|---|---|
| 图 1 | `paper_figs/fig1_ratio_segments.png` | §1 | 逐段钟比值偏差 $y_i$ 与时长加权均值 |
| 图 2 | `paper_figs/fig2_tidal_detection.png` | §2 | 逐段潮汐幅度 $A_i$ 与合并值 $A=-0.54\pm0.08$ |
| 图 3 | `paper_figs/fig3_correction.png` | §3 | 长期稳定度 $\sigma(y_i)$ 与 $\chi^2_{\text{red}}$ |
| 图 4 | `paper_figs/fig4_methods_summary.png` | §3 | 四方法中心值相对实验方 WLS / NIST |

> 复现：`python clock_ratio/make_paper_figures.py`（只写入 `clock_ratio/paper_figs/`，
> 不修改任何已有产物）。
