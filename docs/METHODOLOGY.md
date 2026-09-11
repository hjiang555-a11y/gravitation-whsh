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

### 0.2 有效段遴选（每段独立）

1. **去扣除**：屏蔽 `exclude_ranges`（`clock/params.json`，北京时）。
2. **去跳点**：剔除偏离段内中位数 > `JUMP_THRESHOLD = 10 Hz` 的点。
3. **取最长连续无跳点段**：段内 0 跳点、0 时间断点的最长 1-s 连续段。
4. **端点筛选**：起/终点与该段中位数距离 > 段峰峰值 × 1% 则删去，逐点判断。

结果：每段得到 `d_long`（有效拍频序列）与 `n_valid = len(d_long)`（有效点数）。

---

## 1. 逐段钟比值 R_i（`compute_ratio.py`）

### 1.1 全局中位数 m

```
m = median( beat 中 (3e7, 4e7) Hz 区间内、去扣除后的值 )
```

### 1.2 Dr 公式（拍频 → Sr/Yb 比值偏移）

```
mean_dm  = mean(d_long) − m                          # 拍频偏差 [Hz]
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

**归一化基准**：`fref × div20 = 200 MHz = f_rep`。全程 Decimal 80 位（镜像 MATLAB `vpa(...,80)`）。

**R_i 的含义**：第 i 段的 Yb/Sr 频率比，**含**静态引力修正 delta_g、Sr/Yb 系统频移修正（shift_a、b_Yb），**不含**时变潮汐修正。

### 1.4 参考基准与整个实验值

```
R_seg1     = R_1                                   # 第 1 段钟比值，仅作 y_i 基准
y_i        = R_i / R_seg1 − 1（×10⁻¹⁸）            # 段级相对偏差
R_duration = Σ(n_valid_i · R_i) / Σ n_valid_i      # 时长加权中心值（权重 = 有效时长）
```

---

## 2. OADEV 稳定度与统计不确定度 u_i（`statistical_methods.py`）

### 2.1 OADEV（重叠 Allan 方差）

```
frac = (d_long − mean(d_long)) / F_1550            # 拍频 → 分数频率（demean）
F_1550 = N1550_WH × f_rep = 193 399 200 000 000 Hz = 193.3992 THz
```

OADEV 对 frac 计算重叠 Allan 偏差，τ = 1, 2, 4, 8, …（2 的幂），直到 3m ≤ N。

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
