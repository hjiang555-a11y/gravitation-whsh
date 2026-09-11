# 分析流程文档（WORKFLOW）

> 本文件说明**如何运行本库的完整分析流程**，以及**实验条件改变时改哪里**。
> 目标：后续新增实验数据，只需改参数文档、放数据文件、跑一条命令，即可
> 产出完整分析报告。

## 1. 整体架构（模块化分层）

```
数据文件（原始拍频）          clock/data/环外数据（第八列数据）/Freq_B_2_*.txt
潮汐数据（专业综合差）        results/professional_tidal_delta_30s.csv
        │
        ▼
参数文档（唯一改参数的地方）  clock/params.json  +  clock/PARAMS.md（字段说明）
        │
        ▼
代码单一真源                  clock/shared.py（读 params.json，提供常量/段定义/加载器）
        │
        ├──► 全库分析链（自动，见 §2）
        │
        └──► 单段诊断脚本（手动选段，见 §4）
```

**核心原则**：
- **参数不放代码里** —— 所有实验相关参数在 `clock/params.json`。
- **代码不重复参数** —— 任何脚本要段窗口/常数，一律 `from clock.shared import ...`。
- **物理量定义统一** —— 符号定义见 [docs/NOTATION.md](NOTATION.md)，错误教训见
  [docs/ERROR_CHECKLIST.md](ERROR_CHECKLIST.md)。

## 2. 全库分析链（一键运行）

按顺序运行（后面的脚本读前面的 CSV 产物）：

```bash
# 1. 逐段钟比值（decimal 80 位 + 端点筛选）
python clock_ratio/compute_ratio.py
#   输出: clock_ratio/ratio_17seg.csv, ratio_17seg_summary.csv

# 2. 会话潮汐频移（专业综合差 → ΔW/c²）
python clock/clock_tidal_shift.py
#   输出: clock/clock_tidal_shift.csv, .png

# 3. 段内 1200-s 拟合 + 跨段合并（核心检出）
python clock/segment_analysis/batch_analysis.py
#   输出: clock/segment_analysis/batch_summary.csv, batch_forest.png, batch_shared_axis.png

# 4. 段均值相关性 + 时长加权均值 + 整体修正量
python clock_ratio/correlation_reanalysis.py
#   输出: clock_ratio/correlation_reanalysis.csv, .png

# 5. 段均值相关（y_i vs Δf/f，物理量一致的版本）
python clock/correlation_analysis.py
#   输出: clock/correlation.png

# 6. 报告插图
python clock_ratio/make_report_figures.py
#   输出: clock_ratio/ratio_segments.png
```

运行完成后，重点看：
- `clock_ratio/ratio_17seg.csv` —— 逐段钟比值 R_i 和偏差 y_i
- `clock/segment_analysis/batch_summary.csv` —— 逐段幅度比 A、跨段合并统计
- 权威结论汇总在 [clock_ratio/EXPERIMENT_REPORT.md](../clock_ratio/EXPERIMENT_REPORT.md)

## 3. 实验条件改变时改哪里

| 变化 | 改哪里 | 不用动 |
|---|---|---|
| **新增/修改数据段窗口** | `clock/params.json` 的 `segments.groups`（加/改 `[开始,结束]`） | 代码 |
| **新增/修改扣除区间** | `clock/params.json` 的 `segments.exclude_ranges` | 代码 |
| **钟比值常数变化**（N 值、DELTA_G 等） | `clock/params.json` 的 `ratio_constants` | 代码 |
| **Sr 系统频移分量变化**（shift_a 五分量） | `clock/params.json` 的 `shift_a` | 代码 |
| **新增拍频数据文件** | 放到 `clock/data/环外数据（第八列数据）/`，命名 `Freq_B_2_*.txt` | 代码 |
| **潮汐数据更新** | 覆盖 `results/professional_tidal_delta_30s.csv` | 代码 |

> 重要：`params.json` 里**高精度小数必须存字符串**（如 `"-3.116e-15"`），否则
> `json.load` 转 float64 会丢 E-18 精度。详见 [clock/PARAMS.md](../clock/PARAMS.md)。

## 4. 单段诊断脚本（手动选段）

这些脚本对**某一段**做深入分析（多 τ 相关、lag sweep、幅度拟合）。段号已参数化
（从 `shared.GROUPS[段号-1]` 取窗口），如需改分析的段，改脚本里的段索引即可：

```bash
# 段 13 多 τ 相关 + lag sweep（段索引 12）
python clock/segment13_correlation.py

# 段 13 三角窗拟合（段索引 12）
python clock/segment_analysis/segment13_triangular.py

# 段 6 三角窗拟合（段索引 5）
python clock/segment_analysis/segment6_triangular.py
```

> 注意：这些脚本的段窗口是「按段号」从 `shared.GROUPS` 取的单一真源值，不是
> 硬编码时间戳。改分析的段号需改脚本里的 `GROUPS[索引]`，窗口自动跟随 params.json。

## 5. 变体分析（积分尺度稳健性检验）

```bash
python clock/segment_analysis/variant1_30s_tide.py   # 潮汐 30s 原生网格
python clock/segment_analysis/variant30s_analysis.py # 拍频 30s 均值聚合
python clock/segment_analysis/segment17_correlation.py # 17 点两两相关
```

## 6. 诊断清单（运行前自检）

每次运行前，对照 [docs/ERROR_CHECKLIST.md](ERROR_CHECKLIST.md) 的六类错误自检，
尤其：

- [ ] 高精度小数是否走 Decimal（未用 float 直接算 E-18 量）
- [ ] 潮汐归一化用 `F_1550`（不是 `COEF`）
- [ ] 相关性配对物理量一致（`y_i ↔ Δf/f`，不是 `A ↔ Δf/f`）
- [ ] 参数只在 `params.json`，未散落硬编码

## 7. 相关文档

| 文档 | 说明 |
|---|---|
| [docs/NOTATION.md](NOTATION.md) | 符号与术语表 |
| [docs/ERROR_CHECKLIST.md](ERROR_CHECKLIST.md) | 错误清单 + 检查项目 |
| [clock/PARAMS.md](../clock/PARAMS.md) | 参数文档字段说明 |
| [clock_ratio/EXPERIMENT_REPORT.md](../clock_ratio/EXPERIMENT_REPORT.md) | 总权威报告 |
