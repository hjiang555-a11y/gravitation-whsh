# 武汉—上海远程光钟比对：潮汐引力红移分析

武汉（WUHN）与上海（SHAO）两地光钟（Yb/Sr）经 1550 nm 光纤链路远程比对，
分析潮汐引力红移效应（广义相对论 `Δf/f = ΔW/c²`）是否可被检出，并重建
逐段 Yb/Sr 钟比值。

> **任务路由（先读）**：本库文件较多，每次任务只需其中一小片；改论文、改数值、
> 跑分析各「只读什么 / 改哪里 / 如何验证」见 [AGENTS.md](AGENTS.md)。

> **整个实验的 Yb/Sr 值（本库重建，时长加权中心值）**：**1.207 507 039 343 337 7204**
> （= 17 段按有效时长加权的中心值 R_duration = `1.20750703934333772036956097…`，
> 含静态引力修正 delta_g、未做潮汐修正）。
>
> **参考值（引用出处，供对比）**：
> - NIST：`1.2075070393433377230(37)`（Aeppli et al., Phys. Rev. Lett. 137, 033201 (2026)）
> - 欧洲网络：`1.207507039343337718(32)`（Pizzocaro et al., Phys. Rev. Research 8, 033250 (2026)）
> - 实验方 17 段 WLS：`1.2075070393433377213(23)`（`clock/潮汐修正后的比值计算.pdf`，含潮汐逐点修正）

## 符号表

> 完整符号定义见 [docs/NOTATION.md](docs/NOTATION.md)。这里列出最常用的：

| 符号 | 含义 |
|---|---|
| `ΔW` | 两站重力势差 = `W(WUHN) − W(SHAO)`（武汉−上海）|
| `Δf/f` | 相对频率偏移（×10⁻¹⁸）|
| `R_i` | 第 i 段钟比值（= 该段 Yb/Sr 频率比）|
| `R_seg1` | **第 1 段**的钟比值 R_1，仅作 y_i 的相对基准（**不是**整个实验值）|
| `R_duration` | **整个实验的 Yb/Sr 值** = 17 段按有效时长加权的中心值 `Σ(n_valid_i·R_i)/Σn_valid_i` |
| `R_wls` | 精度加权 WLS 中心值（权重 = 1/u_i²，最优无偏估计）|
| `y_i` | 段钟比值偏差 = `R_i/R_seg1 − 1`（×10⁻¹⁸）|
| `A` | 拍频响应系数：历史段内拟合用去均值波形；新增修正固定 A=−1 或 −0.54，`b_corr=b_raw−A·h`（见独立结果）|
| `COEF` | 拍频→Sr/Yb 比值偏移系数（Dr 公式）|
| `F_1550` | 1550 nm 传递光频（拍频归一化基准，193.40 THz）|
| `N1156/N1397/N1550/N1550_WH` | 光梳计数（Yb/Sr/上海1550/武汉1550）|

> **关键区分（三者不可混）**：`R_seg1`（段1，y_i 基准）、`R_duration`（时长加权
> 整个实验值）、`R_wls`（精度加权）是三个不同量。数值不同（差 ~0.4×10⁻¹⁸）是
> 不同权重的真实结果，非 bug。

> **关键易错点**：潮汐拍频模板必须归一化到 `F_1550`（1550 nm 光频），
> 而非 `COEF`（隐含 `1/COEF = 233.53 THz`，多 Yb/Sr ≈ 1.2075 倍）。
> 修正后幅度比 A ≈ −0.54（旧值 −0.45 系此错误所致）。

## 关键参数计算方法

> 每个核心参数的计算公式与输入来源。完整实现见 `clock_ratio/compute_ratio.py`
> 与 `clock/shared.py`；数值存放在 `clock/params.json`（高精度小数存字符串）。

### 1. 拍频偏差 `mean_dm`

```text
mean_dm = to_dec(float(mean(d_long))) − m_dec       [Hz，旧实现的求值顺序]
   d_long = 该段最长有效索引段（去跳点 + 去扣除 + 端点筛选后；未保证时间连续）
   m_dec  = 全局可用拍频中位数转 Decimal（~33 623 140.92 Hz）
```

### 2. Sr 系统频移修正 `shift_a`（五分量合成）

```text
shift_a_i = a_rou_i + a_AC_i + a_SM_i + a_air_i + a_BBR_i
   a_rou  = 光晶格 AC-Stark 频移（~−3.5~−1.5×10⁻¹⁹）
   a_AC   = 交流斯塔克频移（+7.444e-18 第一轮 / +8.929e-18 第二轮）
   a_SM   = 二阶塞曼频移（~−1.78e-16 第一轮 / −8.925e-17 段9 / 0 段10-14）
   a_air  = 空气折射率修正（−6.7e-19）
   a_BBR  = 黑体辐射频移（0）
   （第 15/16/17 段沿用段 12-14 的常数 shift_a）
```

### 3. 拍频→Sr/Yb 比值偏移系数 `COEF`（Dr 公式）

```text
Dr      = coef1156/N1156 × (mean_dm / fref / div20) / den
den     = coef1397_i/N1397 × (N1550 + 7/25 + 1/25)
coef1397_i = (1 + shift_a_i)/2
coef1156   = (1 + b_Yb)/2,    b_Yb = 5.3e-18 − 7e-18 = −1.7e-18

COEF = 4.282082163269648e-15   （beat[Hz] → Sr/Yb 比值偏移，无量纲）
```

`fref × div20 = 200 MHz` 为光梳重复率 `f_rep`。自洽性：
`N1156 × f_rep = 259.15 THz`（Yb 1156.8 nm）、
`N1550_WH × f_rep = 193.40 THz`（1550.1 nm 武汉传递链路）。

### 4. 1550 nm 传递光频 `F_1550`（拍频归一化基准）

```text
F_1550 = N1550_WH × f_rep = 966996 × 200 MHz = 193.3992 THz
```

> **注意**：`1/COEF = 233.53 THz ≠ F_1550`。`COEF` 是「拍频→比值偏移」
> 系数、隐含 Yb/Sr≈1.2075 倍；潮汐拍频模板必须归一化到 `F_1550`：
> `tide_beat = (ΔW/c²) × F_1550`（不是 `÷ COEF`）。

### 5. 逐段钟比值 `R_i`

```text
ratio_base_i = coef1156/N1156 × NN / (coef1397_i/N1397 × NN2)
NN  = N1550_WH + 26/20 + m/fref/div20
NN2 = N1550 + 8/25

SrYb_raw_i = ratio_base_i + Dr_i
YbSr_raw_i = 1 / SrYb_raw_i
R_i        = YbSr_raw_i × (1 + delta_g)      delta_g = −3.116e-15（静态引力修正）
```

### 6. 钟比值偏差 `y_i` 与幅度比 `A`

```text
y_i = R_i / R_seg1 − 1            （段级钟比值偏差，归一化到 1 的无量纲）
A   = Σ(tide·beat) / Σ(tide²)    （段内拟合 beat = A·tide + noise 的斜率，去均值后）
```

`y_i` 与段潮汐频移 `Δf/f = ΔW/c²` 同是「归一化到 1 的无量纲量」，是物理上正确
的段级相关配对。`A` 是段内诊断量（A=+1 表完整理论幅度），与 `y_i` 不可互相替代。

## 数据来源

- **潮汐**：专业人士提供的 30 秒间隔「综合差」（固体潮+海潮），
  `results/professional_tidal_delta_30s.csv`（UTC，方向武汉−上海，ΔW = g·mm/1000）。
- **潮汐（新增输入，仅登记）**：`results/comp_shanghai-wuhan-beijintime.csv`
  （新一代潮汐模型输出、较既有模型更新；2026-06-20–09-10 北京时、90 s 网格；文件原样
  保留、未接入现有流程；**用途：交叉核对（不替换），后实施**；登记与列定义见
  [clock/PROFESSIONAL_TIDAL_DATA.md](clock/PROFESSIONAL_TIDAL_DATA.md) §7）。
- **实验**：1550 nm 环外拍频（FXE_B8，第 8 列数据），`clock/data/环外数据（第八列数据）/`
  （已 `.gitignore`）。17 段无跳点窗口见 `clock/shared.py` 的 `GROUPS`（北京时 UTC+8）。

## 标准流程（后续扩展按此结构）

```
clock/params.json                     ← 中间参数文档（实验条件都改这里）
clock/shared.py                       ← 单一真源：读 params.json，提供常量/段定义/加载器
docs/NOTATION.md                      ← 符号表（全库引用）
docs/ERROR_CHECKLIST.md               ← 错误清单 + 检查项目（工作纪律）
docs/WORKFLOW.md                      ← 总流程文档（怎么跑、实验条件变了改哪）
docs/METHODOLOGY.md                   ← 计算方法说明（精确定义、公式、归一化基准、存疑项）
clock_ratio/compute_ratio.py          → 17 段钟比值（decimal 80 位 + 端点筛选）
clock_ratio/correlation_reanalysis.py → 段均值相关性 + 时长加权均值 + 修正量
clock_ratio/correlation_reanalysis_timeweighted.py → 段均值相关性（时间等权重，权重=段有效时长）
clock_ratio/correlation_reanalysis_seg9_excluded.py → 段均值相关性·剔除段9（附加，不替代）
clock_ratio/correlation_reanalysis_seg9_independent.py → 段均值相关性·剔除段9 完全独立重算（从原始拍频重做比值）
clock/segment_analysis/batch_analysis.py → 段内 1200-s 拟合 + 跨段合并（核心检出）
clock/clock_tidal_shift.py            → 会话潮汐频移
clock_ratio/EXPERIMENT_REPORT.md      → 总权威报告
```

## 主要结论

1. **钟比值（整个实验值，时长加权中心值）**：R_duration = `1.207507039343337720370…`，
   与 NIST 参考 `1.2075070393433377230(37)` 差 −2.63×10⁻¹⁸，与实验方
   WLS `1.2075070393433377213(23)` 差 −0.93×10⁻¹⁸。（注：R_seg1 = 段 1 的值，仅作
   y_i 基准，非整个实验值。）
2. **潮汐模板响应（待正式推断）**：历史 1200-s / 600-s 重叠窗拟合给出
   A≈−0.54 的点估计，但重叠窗不能作为独立样本，旧的符号无关 Stouffer p 值无有效零假设。
   当前代码改用验证插值与不重叠窗推断；完整潮汐势与时序协方差确认前，不作 σ 级检出声明。
3. **段均值相关**：y_i 与会话潮汐频移 Δf/f 正相关，单段等权重 Pearson r = +0.518
   （p=0.033）；时间等权重（权重=段有效时长）r = +0.372（p=0.226，n_eff≈12.4），
   不再显著——正相关主要由较短段贡献。

> **论文口径（重要）**：**论文主结果采用"未做潮汐修正"的比值**（潮汐项 ~5×10⁻¹⁸ rms
> 与当前不确定度同量级，属小量）；潮汐作为**效应估计**报告——历史幅度点估计 A≈−0.54，
> 以及"若修正则段间离散度降低约 **13%±11%**（jackknife）"；完整响应不确定度待以
> 不重叠窗/协方差模型重建。故上文第 1 条的
> R_duration（未修正）与第 2、3 条的潮汐统计均为论文支撑，但**修正值本身不并入主结果**。

> **结论说明**：以上结论为本库根据实验数据的计算结果（computed），
> 而非经过独立实验室间对比验证的结果（verified）。具体数值来源详见
> [docs/METHODOLOGY.md](docs/METHODOLOGY.md) 与
> [clock_ratio/EXPERIMENT_REPORT.md](clock_ratio/EXPERIMENT_REPORT.md)。

## 新增：固定响应系数的潮汐修正比较（独立结果 / 论文中作效应估计）

保留上方未做潮汐修正的历史主结果；下表是**先修正拍频、再计算钟比值**的新增情景。
**在论文口径下，这些修正值仅作潮汐效应的估计，不并入主结果**（见上方「论文口径」）；
它们不替代旧结果或其统计分析。三个情景均使用相同的 **17 组、1,008,912 个保留样本**，
权重为 `n_valid`（每样本 1 s），不是 WLS。

| 情景 | 响应系数 A | R_duration | ΔR×10¹⁸（绝对比值差） | (R/R_raw−1)×10¹⁸（分数变化） |
|---|---|---|---|---|
| raw（旧基线） | 0 | 1.2075070393433377203696 | +0.000000 | +0.000000 |
| theory（固定理论幅度） | -1 | 1.2075070393433377208108 | +0.441191 | +0.365374 |
| empirical（固定经验幅度） | -0.54 | 1.2075070393433377206078 | +0.238243 | +0.197302 |

`ΔR = R_duration,scenario − R_duration,raw` 是带符号的**绝对比值差**（不是取绝对值）；
分数变化还须除以 `R_duration,raw`，因此两列不能混用，也不等于潮汐 `mean_dff`。
R 从 [summary.json](clock_ratio/tidal_correction/summary.json) 的完整 Decimal 字符串以
`ROUND_HALF_EVEN` 舍入到小数点后 **22 位**；变化量从未舍入值计算，显示小数点后 6 位。
显示位数不代表测量准确度。

- **符号与顺序**：`h = F_1550·ΔW/c²`，`ΔW = W(武汉)−W(上海)`；h **不去均值**。
  A 是 `b_raw = noise + A·h` 中的响应系数，修正为 `b_corr = b_raw − A·h`，
  即 A=−1 加回 h、A=−0.54 加回 0.54h；本次不重新拟合 A。
- **同样本比较**：冻结原始筛选、全局中位数、最长有效索引段及两端裁剪；
  对实际保留的北京时间戳减 8 h 后插值 30 s 潮汐，不外推、不钳位、不跨缺失插值区间。
  潮汐均值修正在 Decimal80 的小拍频偏差中完成，再经完整 `full_ratio` 反演；
  保留 `DELTA_G`、`shift_a`，不向 MHz 浮点载波或数量级为 1 的浮点比值直接叠加微小量。
  旧原始 float64 均值的量化误差仍然继承，并非平均瞬时比值。
- **段内稳定度**：三情景以同一 raw 段比值为参考，使用完整比值映射及全部重叠窗口的 OADEV；
  每个非 1 s 时间步（含重复时间戳）均断开，不跨组拼接。保留旧索引段中的间断样本归属，
  不等于让 OADEV 跨间断。τ=1200 s 时 theory/empirical 分别有 **7/17、10/17** 组 OADEV 较低；
  τ=3600 s 为 **13/17、13/17**；τ=7200 s 为 **6/15、10/15**。
  分母仅计该 τ 可比较的组；不是所有段都改善，也不是显著性或准确度结论。
- **方向自检**：历史上以「修正后潮汐相关性减弱」支持 −0.54 作为固定情景的方向约定。
  去均值波形的自检不校准未去均值模板的 DC 部分，也不替代硬件极性或完整势差的确认。详见
  [方法 §9.5](docs/METHODOLOGY.md#95-方向自检−054-修正后潮汐相关性消失)。
- **解释边界**：把历史去均值波形的 −0.54 幅度用于未去均值模板的 DC（均值）部分，
  是额外假设，不是校准；固定负号是用户指定情景，未新解决
  [硬件极性问题](clock/SIGN_COEFFICIENT_ANALYSIS.md)。未传播系数、潮汐模型或系统项不确定度，
  OADEV 与样本标准差不是 SEM；没有新增 WLS 或总不确定度。

完整结果见独立 [REPORT.md](clock_ratio/tidal_correction/REPORT.md)，逐组钟比值见
[ratio_scenarios.csv](clock_ratio/tidal_correction/ratio_scenarios.csv)，全部 τ 与重叠对数见
[stability.csv](clock_ratio/tidal_correction/stability.csv)。实现：
[tidal_analysis.py](clock_ratio/tidal_analysis.py)、[tidal_stability.py](clock_ratio/tidal_stability.py)、
[tidal_correction.py](clock_ratio/tidal_correction.py)；公式细节见
[方法 §9](docs/METHODOLOGY.md#9-新增固定响应系数的潮汐修正与段内稳定度)。
旧 `statistical_methods.oadev` 实际使用不重叠块均值；旧代码和结果保留，
不能把旧算法与新 OADEV 的数值差当作潮汐效应。

**四种统计方法（WLS/Birge/M-P/贝叶斯）的潮汐修正重算**：`statistical_methods_tidal.py`
用与上述相同的固定系数情景（raw/theory/empirical）在修正后拍频上重跑 §6 节的那套
OADEV→u_i→WLS/Birge/M-P/贝叶斯合并，结果写入
[statistical_methods_tidal.json](clock_ratio/statistical_methods_tidal.json) 并纳入
[EXPERIMENT_REPORT.md](clock_ratio/EXPERIMENT_REPORT.md) 第 7 节（并列、不替代）。
历史 χ²_red 混合了分数偏差与绝对不确定度，必须以当前代码重建后再引用；段间散布的
**约 13% 情景变化**仍只作描述性比较。OADEV 外推仍系统低估 u_i，合并值仅供方法比较。详见
[方法 §10](docs/METHODOLOGY.md#10-新增潮汐修正后重算四种统计方法statistical_methods_tidalpy)。

**段 9 剔除敏感性（附加）**：`statistical_methods_tidal_seg9.py` 把异常段 9
（`shift_a` 介于两轮之间、y_9 偏大）剔除后重新合并已有逐段 (y_i, u_i)，写入
[statistical_methods_tidal_seg9_excluded.json](clock_ratio/statistical_methods_tidal_seg9_excluded.json)
并纳入报告 §8。**这是附加结果，17 段主结果不被替换。**关键发现：剔除段 9 后，
潮汐补偿「降低 χ²_red」的效应大幅减弱甚至反号（theory 相对 raw 的 χ²_red 由 17 段的
「更好 31.8%」变为 16 段的「略差 5.1%」），且 WLS / Mandel–Paule / 贝叶斯三种中心值
下移（WLS、Mandel–Paule 约 −0.65 ~ −0.70×10⁻¹⁸，贝叶斯约 −0.91×10⁻¹⁸），
说明 §7 的 χ²_red 改善**高度依赖段 9**。
详见 [方法 §11](docs/METHODOLOGY.md#11-段-9-剔除敏感性检查statistical_methods_tidal_seg9py附加)。

**拼接序列稳定度（附加，频域视角）**：§7.2 的「长期稳定度」用的是 17 段**段均值**的
样本标准差 σ(y_i)（离散度，只看段间常数偏移）。本节补一个频域视角：把全部 1,008,912 个
1 s 样本接成一条序列，跑重叠 Allan 偏差 σ_y(τ)，看潮汐修正在各平均时间 τ 上的作用。
两个量测**不同频段**，不矛盾（解释见报告 §9.3）。

- **gap-safe 版**（`concatenated_stability.py` → `concatenated_stability.{md,csv}`）：段间真实
  空档保持为断点（不跨 gap 拼接），拼接后恰为 **17 个连续 run**；与既有逐段池化曲线在
  τ≤4096 s **逐位一致**（比值 1.0000），大 τ 才因参与段选择不同而分离。
- **拼接版**（`concatenated_stability_long.py` → `concatenated_stability_long.{md,csv,png,pdf}`）：
  17 段**端到端相接**（空档移除）成一条连续 1 s 记录（对齐轴跨度 **11.677 d** 纯数据时间，
  实际历时 57.97 d），τ 可达 **4.63 d**；每点带 **EDF（Riley & Howe）1σ 误差棒**，
  τ 从 **128 s** 起。log-log 图含三条补偿线（raw/theory/empirical）+ 修正项。

**要点**：短 τ（≤~512 s）三线重合（潮汐是慢信号）；在长 τ=400000 s 处
`empirical (A=−0.54)` 为 8.14e-19、raw 为 8.36e-19，而 `theory (A=−1)` 为
8.71e-19（该点 A=−1 过扣）。**反号证伪**：临时画入的 A=+1 / A=+0.54 在所有长 τ 处显著高于
raw（4.63 d：1.09e-18 / 9.48e-19），证明负号才是抵消方向。**离散度降（A=−1 13.17%、
A=−0.54 12.91%）与 A=−1 的长 τ 不稳定度升都是真实的**：前者对幅度不敏感、后者敏感。
数值见 [EXPERIMENT_REPORT.md](clock_ratio/EXPERIMENT_REPORT.md) §9。**这是独立结果，
不替换 §7 的任何数值；拼接版 τ 长于单段会混合不同测量战役，`n_pairs` 逐点列出。**

## 篇幅与 Nature Article 对照（paper/rev2）

> 已按 2026-10-09 审阅意见调整：题名与摘要按指定文本更新；作者修订版（title→Introduction）
> 合并、参考文献补 5 条（NIST-F2 / PTB CSF / 卫星链路 3 条）、首句补离子/原子光钟引文（+4 条，
> 全部 <2×10⁻¹⁸：PTB Al⁺ 1.6×10⁻¹⁸、NIST Al⁺ 更新 5.5×10⁻¹⁹；NPL 最佳 2.2×10⁻¹⁸ 超线未引）、
> 全文拼写统一美式；原 Results §2.3 并入独立章节 "Discussion and outlook"，原 §2.4（段 9 敏感性）
> 移除、论文不再解释其不采用原因；作者第二版合并：题名改 Yb/Sr、Introduction 逻辑梳理与润色、
> 暗物质句补引 BACON-2021（beloy2021bacon）；新 Overleaf 包 overleaf-rev2-v2 已生成（原包保留）；
> Results §2.1 重写并二次精简（网络组成/频率控制/比对方法；链路细节从简；
> 商用网络非独占使用；载波记作 ITU-T 100 GHz DWDM C34 信道）；
> §2.1 战役段挪至 §2.2 开头（从数据记录起叙述）；§2.2 以贝叶斯随机效应为主结果重写
> （Mandel–Paule 为交叉核对，不提 WLS；新增 Birge 1932 / Mandel–Paule 1970 引文）；
> Methods「Clock-ratio determination and statistical model」小节改为自包含统计模型段
> （贝叶斯主结果 + Mandel–Paule 交叉核对；不再指向附录），§2.2 统计句定稿
> （补 u_MP / ξ 值；统计不确定度 3 位有效数字）。
> 详细对照与复算口径见 [paper/rev2/REVIEW_NOTES.md](paper/rev2/REVIEW_NOTES.md)。

Nature 格式指南锚点：物理论文一般 ≤6 印页；典型 6 页 ≈ 正文 2,500 词（摘要段+正文）+ 4 个
紧凑图表项；Methods 在线部分另计（≤3,000 词）。

| 项 | 本稿 | 锚点 | 差 |
|---|---:|---:|---:|
| Summary（摘要段） | 185 词 | ≤200 | ✓ |
| 正文（摘要段 + Introduction + Results + Discussion and outlook） | **1,732 词** | 2,500（典型 6 页） | **−768（−30.7%）** |
| 主文图表项 | 3 图 + 1 表 = 4 | 4（典型 6 页） | ✓ |
| Methods | 687 词（不计正文） | ≤3,000 | ✓ |
| 题名 | 99 字符 | ≤75（两行） | 超 ~24 |

**结论**：正文约为典型 6 页 Article 的 69.3%，估计印版 5 页；补 ≈770 词可达典型
6 页体量（候选位置见审阅文档），或维持紧凑短稿。

## 复现

**阶段一审计状态（临时）**：当前阶段一临时（provisional）主结果是 16 段结果——第 9 段因参数
待确认而被隔离；17 段与 leave-one-out 结果为敏感性检查；专业潮汐输入的物理模型来源仍需外部
确认。权威数值以 `results/audit-v1/verified/manifest.json` 及其生成的 `ANALYSIS_AUDIT.md`
为准（本节不写入任何运行数值）。阶段一结论、验证与关键裁定汇总见
[docs/audit/PHASE1_SUMMARY.md](docs/audit/PHASE1_SUMMARY.md)。

**阶段一权威入口（audit）**：

```bash
uv sync --extra test
uv run pytest -q
RUN_CLOCK_DATA_TESTS=1 uv run pytest -q
uv run python run_all.py --mode audit --output-dir results/audit-v1
uv run python -m clock_ratio.verify_result_manifest results/audit-v1/verified/manifest.json
uv run python -m clock_ratio.audit_report --manifest results/audit-v1/verified/manifest.json
```

审计模式为 fail-fast，先写入 `results/audit-v1/staging`，经独立清单验证后再提升为不可变历史
并原子切换 `verified` 符号链接；分析审计报告仅从已验证的清单生成。

**重建论文候选稿（paper/rev2，2026-10-08）**：基于冻结的 16 段审计结果层重建的
Nature 风格候选稿；原稿 `paper/main.tex` 原样保留、不参与重建。潮汐分析不再作为检出叙事，
潮汐影响仅作为误差项进入不确定度预算；主贡献为跨城、跨种、达秒定义变更不确定度要求的
远程 Yb/Sr 比值测量。稿件内所有数字由管线从冻结清单生成（无手写数值）：

```bash
cd paper/rev2
uv run --project ../.. python tools/build_numbers.py       # 生成数字宏（读取冻结清单）
uv run --project ../.. python tools/build_numbers.py --check  # 审计：宏覆盖与一致性
uv run --project ../.. python tools/make_figures.py        # 生成 3 图（PNG300/PDF）
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

编译产物 `paper/rev2/main.pdf` 已入库，便于直接查看。数字来源逐条见
`paper/rev2/generated/numbers_manifest.json`。**Overleaf 上传包（当前）**：
[paper/overleaf-rev2-v2/](paper/overleaf-rev2-v2/)（自包含目录）与
[paper/overleaf-rev2-v2-upload.zip](paper/overleaf-rev2-v2-upload.zip)（直接上传 zip）；
初版包 [paper/overleaf-rev2/](paper/overleaf-rev2/) 保留为冻结快照。以下历史命令保留原样。

**只重建新增潮汐分析与独立报告**（希望保留旧产物时推荐）：

```bash
python run_all.py --tidal-only
python run_all.py --help   # 仅显示选项，不启动分析
```

`--tidal-only` 只顺序运行 `tidal_correction.py`、`make_tidal_report.py`，任一步失败立即停止。
同样的独立流程可直接运行：

```bash
python clock_ratio/tidal_correction.py && python clock_ratio/make_tidal_report.py
```

**全流程重建**（会像历史流程一样重新生成旧分析产物，并加入上述新增两步）：

```bash
python run_all.py
```

旧分析的部分分步命令（完整顺序见 WORKFLOW）：

```bash
python clock_ratio/compute_ratio.py              # 17 段钟比值（含端点筛选）
python clock/segment_analysis/batch_analysis.py  # 段内拟合 + 跨段合并（核心）
python clock_ratio/correlation_reanalysis.py     # 段均值相关 + 加权均值 + 修正量
python clock_ratio/correlation_reanalysis_timeweighted.py  # 段均值相关（时间等权重）
python clock/clock_tidal_shift.py                # 会话潮汐频移
python clock_ratio/make_report.py                # 自动生成权威报告
```

> 完整流程说明见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。

## 目录导航

| 路径 | 内容 |
|---|---|
| `AGENTS.md` | **任务路由（先读）**：每个任务只读哪片、改哪里、如何验证 |
| `clock_ratio/EXPERIMENT_REPORT.md` | **总权威报告**（钟比值+潮汐+相关性+拼接稳定度 §9）|
| `clock_ratio/concatenated_stability.py` + `.md/.csv` | gap-safe 拼接稳定度（A=0/−1/−0.54，不跨 gap）|
| `clock_ratio/concatenated_stability_long.py` + `.md/.csv/.png/.pdf` | 拼接版长 τ 稳定度（段端到端相接，τ≤4.63 d，带 EDF 误差棒，log-log 图）|
| `paper/main.tex` + `paper/refs.bib` | **LaTeX 投稿稿**（英文，Nature 网络框架；`cd paper && pdflatex main.tex && bibtex main && pdflatex main.tex` ×2）|
| `paper/rev2/` | **重建候选稿**（16 段口径、潮汐为误差项；数字由 `tools/build_numbers.py` 从冻结清单生成；`main.pdf` 已入库）|
| `docs/PAPER_DRAFT.md` | 论文段落草稿（中文，配 4 图）|
| `docs/PAPER_DRAFT_EN.md` | 论文段落草稿（英文，与中文稿同数同构）|
| `docs/PAPER_INTEGRITY_REPORT.md` | 论文草稿完整性/一致性审计（claim→证据，PASS-WITH-NOTES）|
| `clock_ratio/paper_figs/` | 论文配图（4 图 × PNG300dpi + 矢量 PDF）|
| `docs/audit/` | 阶段一审计总结（PHASE1_SUMMARY.md）与新旧对照证据存档 |
| `docs/WORKFLOW.md` | 总流程文档（怎么跑、实验条件变了改哪）|
| `docs/METHODOLOGY.md` | 计算方法说明（精确定义、公式、归一化基准、存疑项）|
| `docs/NOTATION.md` | 符号与术语表 |
| `docs/ERROR_CHECKLIST.md` | 错误清单 + 检查项目（工作纪律）|
| `clock/params.json` + `clock/PARAMS.md` | 中间参数文档 + 字段说明 |
| `clock/shared.py` | 代码单一真源（读 params.json）|
| `clock/params.json` | 17 段窗口、扣除区间、钟比值常数、shift_a 分量 |
| `clock/PROFESSIONAL_TIDAL_DATA.md` | 专业潮汐数据说明 |
| `clock/SIGN_COEFFICIENT_ANALYSIS.md` | 频率链符号与系数提取 |
| `clock/segment_analysis/` | 段内分析 + 变体 + 17 点相关性 |
| `clock/temperature/` | 环外信号与温度分析 |
| `archive/` | 历史/重叠/过时文档（含旧 14 段、旧 A≈−0.45）|

> 原始实验数据与 MATLAB 处理程序位于 `clock/data/`，已由 `.gitignore` 排除。
