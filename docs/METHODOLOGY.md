# 计算方法说明（METHODOLOGY）

> 本文件**无歧义地**记录本库每一项分析的计算方法：精确定义、公式、输入、归一化
> 基准、权重。本文件是「计算方法」的权威说明，代码实现以 `clock/`、`clock_ratio/`
> 下的脚本为准。符号定义见 [docs/NOTATION.md](NOTATION.md)。

---

## 0. 数据与预处理

### 0.1 输入数据

| 数据 | 来源 | 时区 | 采样 |
|---|---|---|---|
| 拍频 beat | `clock/data/环外数据（第八列数据）/Freq_B_2_*.txt`，第 11 列（FXE_B8） | 北京时间（UTC+8） | 1 s |
| 潮汐综合差 ΔW | `results/professional_tidal_delta_30s.csv`，列 `total_tidal_delta_m2_s2_surface` | UTC | 30 s |

方向约定：`ΔW = W(WUHN) − W(SHAO)`（武汉 − 上海）。比对前拍频窗口 **−8 h** 对齐到 UTC。

### 0.2 有效段遴选（每段独立；冻结旧实现）

1. **窗口与去扣除**：段窗口为 `[start,end)`，屏蔽 `exclude_ranges` 的含两端区间（`clock/params.json`，北京时）。
2. **去跳点**：先取未扣除且 `3e7 < beat < 4e7` Hz 的合理点；以这些点的段内中位数为中心，保留偏差严格小于 `JUMP_THRESHOLD = 10 Hz` 的点。
3. **取最长有效索引段**：`longest_valid_span(valid)` 只按布尔掩码中相邻索引取最长有效段，**不检查时间戳是否每步相差 1 s**。
4. **端点筛选**：使用该索引段的原始中位数与峰峰值；起/终点距中位数 > 峰峰值 × 1% 则删去，向内逐点判断。

结果：每段得到 `d_long`（有效拍频序列）与 `n_valid = len(d_long)`（有效点数）。

> **描述更正，不改变历史代码/结果**：本节原称「0 时间断点的最长 1-s 连续段」，
> 与 `compute_ratio.py` 实际索引段规则不符。新增分析冻结这套原始选择，修正后不重新筛选；
> 全局中位数、扣除区间及端点裁剪也不变。保留样本即使有时间间断仍参与钟比值均值，
> 但新增 OADEV 在每个非 1 s 时间步（含重复时间戳）断开，见 §9。

---

## 1. 逐段钟比值 R_i（`compute_ratio.py`）

### 1.1 全局中位数 m

```
m = median( beat 中 (3e7, 4e7) Hz 区间内、去扣除后的值 )
```

### 1.2 Dr 公式（拍频 → Sr/Yb 比值偏移）

```
mean_dm  = to_dec(float(mean(d_long))) − to_dec(m)  # 拍频偏差 [Hz]；旧实现的求值顺序
coef1397 = (1 + shift_a_i) / 2                       # Sr 端修正
coef1156 = (1 + b_Yb) / 2                            # Yb 端修正，b_Yb = −1.7e-18
den      = coef1397 / N1397 × (N1550 + 7/25 + 1/25)
Dr       = coef1156 / N1156 × (mean_dm / fref / div20) / den
```

### 1.3 钟比值

```
NN   = N1550_WH + 26/20 + m / fref / div20
NN2  = N1550 + 8/25
ratio_base = coef1156 / N1156 × NN / (coef1397 / N1397 × NN2)
SrYb_raw   = ratio_base + Dr
YbSr_raw   = 1 / SrYb_raw
R_i        = YbSr_raw × (1 + delta_g)               # delta_g = −3.116e-15（静态引力修正）
```

**归一化基准**：`fref × div20 = 200 MHz = f_rep`。比值公式使用 Decimal 80 位
（镜像 MATLAB `vpa(...,80)`）；原始拍频均值和中位数先由 float64 求出，再经 `repr` 转
Decimal。后续高精度计算不能恢复这一步已损失的原始均值量化精度。

**R_i 的含义**：第 i 段的 Yb/Sr 频率比，**含**静态引力修正 delta_g、Sr/Yb 系统频移修正（shift_a、b_Yb），**不含**时变潮汐修正。

### 1.4 参考基准与整个实验值

```
R_seg1     = R_1                                   # 第 1 段钟比值，仅作 y_i 基准
y_i        = R_i / R_seg1 − 1（×10⁻¹⁸）            # 段级相对偏差
R_duration = Σ(n_valid_i · R_i) / Σ n_valid_i      # 时长加权中心值（权重 = 有效时长）
```

---

## 2. 历史 Allan 稳定度与统计不确定度 u_i（`statistical_methods.py`）

### 2.1 历史 `oadev` 名称与实际算法

```
frac = (d_long − mean(d_long)) / F_1550            # 拍频 → 分数频率（demean）
F_1550 = N1550_WH × f_rep = 193 399 200 000 000 Hz = 193.3992 THz
```

历史函数虽名为 `oadev`，实际将 frac 分成长度 m 的**不重叠块均值**，再对相邻块
作差，τ = 1, 2, 4, 8, …（2 的幂），条件为 3m ≤ N。它不是逐样本移动起点、使用
全部重叠窗口的 OADEV。旧代码、输出字段名及结果原样保留；下文历史「OADEV」表述
均指该历史实现。新增真正重叠算法见 §9.4，不能把两种算法的数值差称为潮汐修正效果。

### 2.2 外推到段时长 T

```
拟合区间：128 s ≤ τ ≤ T/4
log(σ_y) = a + b·log(τ) 线性拟合
σ_y(T) = exp(a + b·log(T))                          # 外推到 T
```

> ⚠️ **已知存疑（已经过独立对抗审查）**：拍频数据在 τ ≳ 4096 s 后出现低频平台
> （真实的 flicker 频率噪声地板，来自时钟/链路，**不是潮汐**——潮汐应在
> τ≈2–4×10⁴ s 表现为幅度 ~1e-17 的凸起，τ 特征与幅度都不符）。该 flicker 地板使
> 白噪声斜率外推对**所有段系统性低估 u_i 约 30–40%**（而非「短段偏高、长段偏低」），
> 把 χ²_red 推高到 ~3.5–4。但 χ²_red≈5.4 的剩余部分来自**个别段 u_i 本身不可靠**
> （u_i 极差约 18 倍，远超白噪声+flicker 应有的 ≤2.8 倍），需逐段复核原始数据与
> OADEV 曲线。当前 u_i 与四种合并值**不可靠**，仅作方法演示。

### 2.3 每段统计不确定度 u_i

```
u_i = σ_y(T) × R_i                                  # 绝对钟比值不确定度
```

---

## 3. 四种统计合并方法（`statistical_methods.py`）

输入：`y_i`（×10⁻¹⁸）、`u_i`（绝对钟比值不确定度，17 段）。

### 3.1 WLS（精度加权最小二乘）

```
w_i   = 1 / u_i²
y_wls = Σ w_i y_i / Σ w_i
u_wls = 1 / sqrt(Σ w_i)
```

### 3.2 Birge ratio（比例膨胀不确定度）

```
χ²      = Σ (y_i − y_wls)² / u_i²
χ²_red  = χ² / (N−1)
B       = sqrt(χ²_red)
u_birge = B · u_wls
```

### 3.3 Mandel–Paule（加噪声地板 ξ）

```
u_i,eff² = u_i² + ξ²
ξ 由 χ²_red(ξ) = 1 迭代求出（二分 200 次）
y_mp = Σ w_i y_i / Σ w_i，w_i = 1/(u_i²+ξ²)
u_mp = 1 / sqrt(Σ 1/(u_i²+ξ²))
```

### 3.4 贝叶斯（μ、ξ 两参数网格后验）

```
ξ 在 log 网格 1e-20 ~ 1e-16 上 200 点
似然：y_i ~ Normal(μ, u_i²+ξ²)，Jeffreys 先验 p(ξ)∝1/ξ
μ 后验均值 μ_post = Σ p_k · m_k（m_k 为给定 ξ_k 的加权均值）
μ 后验标准差 u_stat_bayes = sqrt(Σ p_k (s_k² + (m_k−μ_post)²))
R_bayes = R_seg1 × (1 + μ_post)
```

各方法中心值 = `R_seg1 × (1 + 对应 y)`，用 Decimal 保留全精度（避免 float64 吞 E-18 级差异）。

---

## 4. 引力（潮汐）修正量（逐方法权重）

每段潮汐频移 `dff_i = ΔW_i / c²`（ΔW_i 为该段潮汐综合差均值）。

```
grav_method = Σ w_i · dff_i / Σ w_i
```

其中 w_i 为**对应方法的权重**：

| 方法 | 权重 w_i |
|---|---|
| WLS / Birge | `1/u_i²` |
| Mandel–Paule | `1/(u_i²+ξ_mp²)` |
| 贝叶斯 | `1/(u_i²+ξ_bayes²)` |

> **关键一致性**：钟比值的合并权重与引力潮汐修正的合并权重**必须相同**（同方法同权重），不能用时长权重混用。

---

## 5. 段内相关性分析（`batch_analysis.py`）

### 5.1 潮汐拍频模板

```
tide_beat = (ΔW/c²) × F_1550                         # 归一化到 1550 nm 光频
```

> **不是** `(ΔW/c²) / COEF`。COEF 是「拍频→比值偏移」系数（隐含 1/COEF=233.53 THz），
> 多 Yb/Sr≈1.2075 倍；潮汐模板必须归一化到 F_1550=193.40 THz。

### 5.2 幅度拟合

拍频与潮汐模板同过 1200-s 三角窗（600-s 步长），去均值后拟合：

```
beat = A · tide + noise
A    = Σ(tide·beat) / Σ(tide²)
u_A  = sqrt(σ²_res / Σ(tide²))
r    = corr(beat, tide)
```

### 5.3 跨段合并

- 符号一致性：负相关段数，二项检验
- Stouffer（符号无关 |z|）：合并各段双侧 p 值
- Fisher：χ² = −2Σ ln p
- Fisher-z 加权 r：权重 = n_pts − 3
- 精度加权 A：权重 = 1/u_A²

---

## 6. 段均值相关性（`correlation_reanalysis.py` / `correlation_analysis.py`）

```
y_i（段级钟比值偏差）↔ dff_i（段级潮汐频移 ΔW_i/c²）
Pearson r, Spearman ρ：不加权（17 点）
加权 Pearson r：权重 = n_valid
整体均值：y_i 时长加权均值 = Σ(n_valid_i·y_i)/Σn_valid_i
整体潮汐修正：Σ(n_valid_i·dff_i)/Σn_valid_i
```

> **物理量一致性**：y_i 与 dff 都是「归一化到 1 的无量纲量（潮汐对钟的影响）」，
> 是物理正确的段级配对。幅度比 A 是段内拟合斜率，与段级 dff 物理量不对应，仅作诊断。

### 6.1 时间等权重版本（`correlation_reanalysis_timeweighted.py`）

上面 Pearson/Spearman/OLS 是**单段等权重**（17 段每段一票）。时间等权重版本让
**每秒有效数据权重相同**——原始逐秒数据不在库内，用各段有效时长 n_valid 作简单
时间权重：

```
w_i = n_valid_i / Σn_valid
加权 Pearson r、加权 Spearman ρ（秩上的加权 Pearson）
p 值：Kish 有效样本量 n_eff = (Σw)²/Σw²，t = r·√((n_eff−2)/(1−r²))
WLS 拟合：y_i = slope·dff + intercept（权重 w_i，SE 按 n_eff 自由度）
```

输出：`clock_ratio/correlation_reanalysis_timeweighted.csv` / `.png`
（CSV 同时给出单段等权重 Pearson r 作对照）。

---

## 7. 归一化基准总表（全库统一）

| 量 | 基准 | 值 | 用途 |
|---|---|---|---|
| `F_1550` | N1550_WH × f_rep | 193 399 200 000 000 Hz（193.3992 THz） | 拍频归一化（潮汐模板、OADEV frac） |
| `f_rep` | fref × div20 | 200 MHz | 光梳重复率 |
| `COEF` | Dr 公式系数 | 4.282082163269648e-15 | 拍频→Sr/Yb 比值偏移（**非**光频） |
| `delta_g` | 静态引力红移 | −3.116e-15 | 钟比值静态修正 |
| `c` | 光速 | 299 792 458 m/s | ΔW/c² 换算 |

---

## 8. 已知存疑项（待解决）

1. **OADEV 外推低估 u_i（flicker 地板所致）+ 个别段 u_i 不可靠**（§2.2）——外推对全体段系统性低估 ~30–40%（推高 χ²_red 到 ~3.5–4），叠加个别段（段 5/6/16）u_i 异常（极差 18 倍，超出任何统一噪声模型），合起来 χ²_red≈5.4、Birge≈2.3，与实验方（1.70/1.30）不同。需逐段复核原始数据与 OADEV 曲线，改用 MDEV 或限制外推区间后重算 u_i。
2. **段 9 的 a_SM = −8.925e-17** 与段 10–14 的 a_SM=0 跳变——MATLAB 源码自注「请确认是真实值还是占位符」，本库原样保留未改。
3. **段 9 的 shift_a 异常**导致 y_9 ≈ +6.4×10⁻¹⁸ 偏大。

---

## 9. 新增：固定响应系数的潮汐修正与段内稳定度

这是与历史结果并列的独立情景分析，不替代 §1–8。实现见
[tidal_analysis.py](../clock_ratio/tidal_analysis.py)、
[tidal_stability.py](../clock_ratio/tidal_stability.py) 与
[tidal_correction.py](../clock_ratio/tidal_correction.py)。数值来源为
[summary.json](../clock_ratio/tidal_correction/summary.json)、
[ratio_scenarios.csv](../clock_ratio/tidal_correction/ratio_scenarios.csv)、
[stability.csv](../clock_ratio/tidal_correction/stability.csv)；汇总见独立
[REPORT.md](../clock_ratio/tidal_correction/REPORT.md)。

### 9.1 固定响应、未去均值模板与时间对齐

```text
ΔW(t) = W(武汉,t) − W(上海,t)                       [m²/s²]
h(t) = F_1550 · ΔW(t)/c²                            [Hz，未去均值]
b_raw(t) = noise(t) + A · h(t)                      # A 是响应系数，不是直接相加的修正系数
b_corr(t) = b_raw(t) − A · h(t)
raw: A=0；theory: A=−1；empirical: A=−0.54           # 固定 Decimal 常数，本次不拟合
```

因此 theory 加回 h，empirical 加回 0.54h；不能再给 h 预加负号而重复反号。
冻结 §0.2 的原始样本选择、全局中位数及两端裁剪，对**实际保留**的拍频时间戳
执行北京时间减 8 h 得 UTC；不使用旧 CSV 中未反映端点裁剪的起止时间代替。
潮汐网格须有限、递增、无重复且位于 UTC 30 s 刻度，线性插值到这些实际时间戳。
查询超出覆盖范围、或所需插值两端不是相邻 30 s 刻度时报错；不外推、不端点钳位、
不跨缺失潮汐区间插值。命中现有网格点可直接取值。

### 9.2 先在小拍频均值偏差上修正，再反演

```text
mean_raw_dec = to_dec(float(mean(b_kept)))           # 继承旧 float64 均值，以 repr 转换
mean_h_dec   = to_dec(float(mean(h)))
mean_dm_raw  = mean_raw_dec − m_dec
mean_dm_corr = mean_dm_raw − A · mean_h_dec          # Decimal80
R_i,A = full_ratio(mean_dm_corr, shift_a_i, m_dec)   # 完整 Dr + 反演 + 静态修正
```

h 的均值包含 DC 部分，不做去均值或重新拟合。`DELTA_G`、`shift_a` 以及完整 Dr 常数
均保持原值。这是**先平均修正后的线性拍频，再反演**，不是平均逐点瞬时 R。
不在约 33 MHz 的 float64 拍频上先叠加微小潮汐再求均值，也不向数量级为 1 的
float64 比值直接叠加微小修正。Decimal80 保留后续小量运算，但不恢复原始浮点均值的量化精度。

三情景用相同 `n_valid_i` 权重计算 `R_duration,A = Σ(n_valid_i·R_i,A)/Σn_valid_i`。
当前均为 **17 组、1,008,912 个样本**；`duration_s = n_valid×1 s`，不是含时间间断的
`elapsed_span_s = last−first+1 s`。全精度中心及差值以 summary.json 为准，展示 R 时
直接从 Decimal 按 `ROUND_HALF_EVEN` 舍入至小数点后 22 位，不先转 float 或截断字符串。

```text
delta_R = R_duration,A − R_duration,raw             # 带符号的绝对比值差，非取绝对值
delta_fractional_1e18 = (R_duration,A/R_duration,raw − 1) × 10¹⁸
mean_dff = mean(h)/F_1550                            # 潮汐 ΔW/c² 的均值，不是上述比值变化
```

两种变化量须分别计算；逐组 CSV 的对应列以该组 raw 为分母，而不是第 1 组。

### 9.3 段内稳定度：所有情景共用 raw 参考

本小节省略段下标。令 `R0` 为**当前段 raw 钟比值**（不是整个实验中心，也不是固定第 1 段），
三个情景均使用该参考。完整 Dr 系数 K 随该段 `shift_a` 计算，不能用展示用的舍入 `COEF` 代替：

```text
G   = 1 + DELTA_G
S0  = G/R0
den = ((1+shift_a)/2)/N1397 · (N1550+7/25+1/25)
K   = (COEF1156/N1156)/(FREF · DIV20 · den)           [Hz⁻¹]
e(t) = (b(t) − raw_mean) − A · h(t)                 [Hz]
q(t) = (K/S0) · e(t)
y(t) = R_A(t)/R0 − 1 = −q(t)/(1+q(t))              [无量纲]
```

实现先用 Decimal 求 K/S0，再转 float 乘小残差 e，直接计算 `−q/(1+q)`，
避免先构造接近 1 的浮点比值再相减。`y(t)` 不同于历史段间 `y_i=R_i/R_seg1−1`。
输出 `fractional_std` 与 `beat_std_hz` 分别为 y 与 e 的样本标准差（`ddof=1`）。

### 9.4 真正重叠、间断安全的 OADEV

按保留的原始时间戳分出连续 1 s 片段（run）：**每个非 1 s 步长都断开**，包括重复时间戳。
间断两侧样本仍属于同一钟比值组，但 OADEV 窗口不能跨间断或跨组。
对 τ=m 秒、长度为 N_run 的每个片段，计算所有起点的相邻 m 点均值差：

```text
ȳ_run,j = (1/m) · Σ_{k=j}^{j+m−1} y_run,k
D_run,j = ȳ_run,j+m − ȳ_run,j
j = 0,…,N_run−2m                                   # 每次移动 1 个样本
n_pairs,run = max(N_run−2m+1, 0)
n_pairs = Σ_runs n_pairs,run
σ_y²(τ) = [Σ_runs Σ_j D_run,j²] / (2 · n_pairs)
```

平方差与对数仅在**同一组内部**跨 run 汇总；不是先求各 run 的 OADEV 再平均。
`n_pairs` 是重叠对数，**不是独立自由度**。前缀和前仅做数值中心化，
不去趋势，也不对潮汐模板去均值。

每段 τ 网格取 1、2、4、… 秒并加入 600、1200、3600、7200 s，
均限制在该段最长连续 raw 片段长度的 1/4 内；三情景使用同一网格。
超限 τ 不提供行；不可用 OADEV 或 raw 为零时的 corrected/raw 倍数在 CSV 留空，
报告显示「—」，不填零。比较倍数只来自此处同一算法、同一 τ、同一保留样本。

### 9.5 解释边界

- −0.54 来自历史**去均值波形**幅度，将其转用到未去均值模板的 DC（均值）部分是
  **额外假设**，不是已验证的均值校准，也不是本次重新估计的系数。
- 固定负号为用户指定的响应约定，不新解决
  [历史硬件极性问题](../clock/SIGN_COEFFICIENT_ANALYSIS.md)。
- 不传播系数、潮汐模型或系统项不确定度。OADEV/样本标准差不是 SEM，
  不据此新建 WLS、总不确定度或显著性检验，也不改变历史统计结果。
- 不声称所有段改善。报告的「OADEV 较低组数」仅描述合格组在指定 τ 下的数值比较，
  不代表统计显著或准确度提升；旧 §2 算法与本节新算法之间的差异不能解释为潮汐效应。
