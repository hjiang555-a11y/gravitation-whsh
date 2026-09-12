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
| `A` | 段内幅度比（`beat = A·tide + noise`，A=+1 表示完整理论幅度）|
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
mean_dm = mean(d_long − m)          [Hz]
   d_long = 该段最长无跳点段（去跳点 + 去扣除 + 端点筛选后）
   m      = 全段拍频中位数（~33 623 140.92 Hz）
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
3. **段均值相关**：y_i 与会话潮汐频移 Δf/f 正相关，Pearson r = +0.518（p=0.033）。

> **结论说明**：以上结论为本库根据实验数据的计算结果（computed），
> 而非经过独立实验室间对比验证的结果（verified）。具体数值来源详见
> [docs/METHODOLOGY.md](docs/METHODOLOGY.md) 与
> [clock_ratio/EXPERIMENT_REPORT.md](clock_ratio/EXPERIMENT_REPORT.md)。

## 复现

**一键分析 + 出报告**（推荐）：

```bash
python run_all.py   # 跑完全部分析步骤 + 自动刷新 EXPERIMENT_REPORT.md
```

或分步运行：

```bash
python clock_ratio/compute_ratio.py              # 17 段钟比值（含端点筛选）
python clock/segment_analysis/batch_analysis.py  # 段内拟合 + 跨段合并（核心）
python clock_ratio/correlation_reanalysis.py     # 段均值相关 + 加权均值 + 修正量
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
