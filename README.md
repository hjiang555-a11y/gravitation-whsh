# 武汉—上海远程光钟比对：潮汐引力红移分析

武汉（WUHN）与上海（SHAO）两地光钟（Yb/Sr）经 1550 nm 光纤链路远程比对，
分析潮汐引力红移效应（广义相对论 `Δf/f = ΔW/c²`）是否可被检出，并重建
逐段 Yb/Sr 钟比值。

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
clock/segment_analysis/batch_analysis.py → 段内 1200-s 拟合 + 跨段合并（核心检出）
clock/clock_tidal_shift.py            → 会话潮汐频移
clock_ratio/EXPERIMENT_REPORT.md      → 总权威报告
```

## 主要结论

1. **钟比值（整个实验值，时长加权中心值）**：R_duration = `1.207507039343337720370…`，
   与 NIST 参考 `1.2075070393433377230(37)` 差 −2.63×10⁻¹⁸，与实验方
   WLS `1.2075070393433377213(23)` 差 −0.93×10⁻¹⁸。（注：R_seg1 = 段 1 的值，仅作
   y_i 基准，非整个实验值。）
2. **潮汐检出（核心）**：段内 1200-s 窗拟合单段不显著，但跨段累加显著——
   14/17 段同号，符号无关 Stouffer |z|=5.87（p≈4.3e-9），幅度比
   **A = −0.54±0.08**（6.4σ），潮汐以正确方向、约一半幅度被检出。
3. **段均值相关**：y_i 与会话潮汐频移 Δf/f 正相关，单段等权重 Pearson r = +0.518
   （p=0.033）；时间等权重（权重=段有效时长）r = +0.372（p=0.226，n_eff≈12.4），
   不再显著——正相关主要由较短段贡献。

> **结论说明**：以上结论为本库根据实验数据的计算结果（computed），
> 而非经过独立实验室间对比验证的结果（verified）。具体数值来源详见
> [docs/METHODOLOGY.md](docs/METHODOLOGY.md) 与
> [clock_ratio/EXPERIMENT_REPORT.md](clock_ratio/EXPERIMENT_REPORT.md)。

## 新增：固定响应系数的潮汐修正比较（独立结果）

保留上方未做潮汐修正的历史主结果；下表是**先修正拍频、再计算钟比值**的新增情景，
不替代旧结果或其统计分析。三个情景均使用相同的 **17 组、1,008,912 个保留样本**，
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

## 复现

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
| `clock_ratio/EXPERIMENT_REPORT.md` | **总权威报告**（钟比值+潮汐+相关性）|
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
