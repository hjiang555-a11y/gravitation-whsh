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
- **新增情景与实验参数分开** —— `tidal_analysis.py` 的 `SCENARIOS` 固定 A=0、−1、−0.54，
  是本次指定的比较情景，不是新拟合值，也不改写 `params.json` 中的实验常数。

## 2. 运行入口：独立潮汐比较与全库重建

以下命令均在仓库根目录、已有运行环境中执行。只需查看选项、不启动分析时：

```bash
python run_all.py --help
```

### 2.1 只运行新增潮汐分析（保留旧产物时推荐）

```bash
python run_all.py --tidal-only
```

该模式**只按顺序运行两个脚本**：

1. [tidal_correction.py](../clock_ratio/tidal_correction.py)：从原始拍频与潮汐数据计算
   raw（A=0）、theory（A=−1）、empirical（A=−0.54）的钟比值及段内稳定度。
2. [make_tidal_report.py](../clock_ratio/make_tidal_report.py)：读取新生成的 CSV/JSON，生成独立报告。

**任一步失败立即停止并非零退出**；分析失败后不继续用旧的新增产物生成报告。
这个入口不运行旧分析和旧报告生成器，只重建 `clock_ratio/tidal_correction/` 下的独立产物，
因此要保留历史文件时应选它，而非无参数的全流程入口。直接运行以下两脚本得到相同流程；
使用 `&&` 保留失败即停止的行为：

```bash
python clock_ratio/tidal_correction.py && python clock_ratio/make_tidal_report.py
```

只重建独立报告、不重新分析或修改源 CSV/JSON：

```bash
python clock_ratio/make_tidal_report.py
```

| 独立产物 | 内容 |
|---|---|
| [REPORT.md](../clock_ratio/tidal_correction/REPORT.md) | 三情景中心值、逐组比值、共同 τ 的描述性 OADEV 比较及限制 |
| [ratio_scenarios.csv](../clock_ratio/tidal_correction/ratio_scenarios.csv) | 逐组全精度比值、绝对/分数变化、实际裁剪后时间边界、有效样本数及样本标准差 |
| [stability.csv](../clock_ratio/tidal_correction/stability.csv) | 各组各情景的 τ、重叠对数 n_pairs、OADEV 及 corrected/raw 倍数 |
| [summary.json](../clock_ratio/tidal_correction/summary.json) | 全精度 Decimal 时长加权中心与变化量、处理约定及限制；数值真源 |

计算逻辑见 [tidal_analysis.py](../clock_ratio/tidal_analysis.py) 与
[tidal_stability.py](../clock_ratio/tidal_stability.py)，方法见 [METHODOLOGY §9](METHODOLOGY.md#9-新增固定响应系数的潮汐修正与段内稳定度)。
三情景冻结原始样本及权重，不重新筛选或拟合 A；负响应对应加回未去均值模板，
不是修改 `DELTA_G` 或 `shift_a`。完整比值反演前做潮汐修正，段内 OADEV 另按真实时间间断分开。

有本地原始钟数据时，相关测试命令为（这里列出复核入口，不代表本次文档编辑已执行测试）：

```bash
RUN_CLOCK_DATA_TESTS=1 python -m pytest -q clock_ratio/test_tidal_analysis.py clock_ratio/test_tidal_outputs.py clock_ratio/test_tidal_report.py
```

### 2.2 全库分析链（会重新生成历史产物）

```bash
python run_all.py
```

默认入口仍运行**所有旧步骤，加上新增两步**，并像历史流程一样重新生成旧分析、图及
`EXPERIMENT_REPORT.md`。新增比较是独立结果，不意味着默认全流程不写旧文件。
默认模式也保留历史的错误收集行为：某步失败仍继续后续步骤，最后汇总并非零退出；
不要把 `--tidal-only` 的 fail-fast 保证套到默认模式。

当前 [run_all.py](../run_all.py) 的执行顺序如下：

```bash
# 1. 逐段钟比值（Decimal80 反演 + 原始端点筛选）
python clock_ratio/compute_ratio.py
#   输出: clock_ratio/ratio_17seg.csv, ratio_17seg_summary.csv

# 2. 会话潮汐频移（专业综合差 → ΔW/c²）
python clock/clock_tidal_shift.py
#   输出: clock/clock_tidal_shift.csv, .png

# 3. 段内 1200-s 拟合 + 跨段合并（历史检出分析）
python clock/segment_analysis/batch_analysis.py
#   输出: batch_summary.csv, batch_aggregate.csv, batch_forest.png, batch_shared_axis.png

# 4–6. 历史相关性及报告插图
python clock_ratio/correlation_reanalysis.py
#   输出: clock_ratio/correlation_reanalysis.csv, .png

# 4b. 段均值相关性（时间等权重：权重 = 段有效时长 n_valid）
python clock_ratio/correlation_reanalysis_timeweighted.py
#   输出: clock_ratio/correlation_reanalysis_timeweighted.csv, .png

# 5. 段均值相关（y_i vs Δf/f，物理量一致的版本）
python clock/correlation_analysis.py
python clock_ratio/make_report_figures.py

# 7–11. 历史变体及单段诊断（默认流程也运行）
python clock/segment_analysis/variant1_30s_tide.py
python clock/segment_analysis/variant30s_analysis.py
python clock/segment13_correlation.py
python clock/segment_analysis/segment13_triangular.py
python clock/segment_analysis/segment6_triangular.py

# 12. 历史 Allan 稳定度及统计合并（oadev 名称的算法注释见 METHODOLOGY §2）
python clock_ratio/statistical_methods.py

# 12b. 潮汐修正后重算四种统计方法（raw/theory/empirical，见 METHODOLOGY §10）
python clock_ratio/statistical_methods_tidal.py

# 13–14. 独立潮汐比较及独立报告
python clock_ratio/tidal_correction.py
python clock_ratio/make_tidal_report.py

# 15. 自动生成旧分析总报告
python clock_ratio/make_report.py
#   输出: clock_ratio/EXPERIMENT_REPORT.md
```

运行完成后，历史钟比值与相关性结果仍见
[EXPERIMENT_REPORT.md](../clock_ratio/EXPERIMENT_REPORT.md)，
新增固定响应情景见 [tidal_correction/REPORT.md](../clock_ratio/tidal_correction/REPORT.md)。
两份报告由各自生成器读取产物自动生成，不手改生成报告。

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

每次运行前，对照 [docs/ERROR_CHECKLIST.md](ERROR_CHECKLIST.md) 的六类历史错误及新增潮汐专项检查，
尤其：

- [ ] 高精度小数是否走 Decimal（未用 float 直接算 E-18 比值差）
- [ ] 潮汐归一化用 `F_1550`（不是 `COEF`）
- [ ] 相关性配对物理量一致（`y_i ↔ Δf/f`，不是 `A ↔ Δf/f`）
- [ ] 实验参数仍来自 `params.json`；固定 A 情景与实验常数分开
- [ ] 要保留旧产物时选择 `--tidal-only`，不误跑默认全流程
- [ ] 实际裁剪后时间戳减 8 h；潮汐覆盖及插值区间有效，不外推或跨缺失区间
- [ ] 三情景保留样本与权重相同；OADEV 不跨间断，且不与历史块均值算法混比
- [ ] 分开报告 `delta_R×10¹⁸` 与 `delta_fractional_1e18`，不把 OADEV 当 SEM 或总不确定度

## 7. 相关文档

| 文档 | 说明 |
|---|---|
| [docs/NOTATION.md](NOTATION.md) | 符号与术语表 |
| [docs/ERROR_CHECKLIST.md](ERROR_CHECKLIST.md) | 错误清单 + 检查项目 |
| [clock/PARAMS.md](../clock/PARAMS.md) | 参数文档字段说明 |
| [clock_ratio/EXPERIMENT_REPORT.md](../clock_ratio/EXPERIMENT_REPORT.md) | 总权威报告 |
