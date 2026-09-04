# 武汉—上海潮汐引力势差

本项目计算 2026-06-20 00:00 至 2026-08-26 23:59（UTC）期间，武汉
`WUHN00CHN` 与上海佘山 `SHAO00CHN` 两个 IGS 站之间每分钟的潮汐引力势差：

```text
ΔW = W(SHAO) - W(WUHN)       [J/kg = m²/s²]
```

这里的“势能变化”按**单位质量的引力势变化**报告。质量为 `m` kg 的物体对应势能
变化为 `m × ΔW` J。结果只包含随时间变化的固体潮和海洋潮汐负荷项，不包含
EGM2008 静态重力场，因此不会把与潮汐无关的高程/纬度静态势差混入结果。

> **方向约定说明**：本项目数值序列经专业人士提供的 30 秒间隔潮汐数据
> （`clock/武汉-上海潮汐结果（0620-0910）-30秒间隔数据.xlsx`，UTC，“综合差”
> = 固体潮之差 + 海潮之差）交叉验证——各分量均与该专业数据的数值方向**一致**
> （相关系数 +0.6~+1.0）。该专业数据的「之差」列数值方向实为**上海−武汉**（与
> 本项目 `SHAO − WUHN` 约定一致；xlsx 表头「CAS−SHA」仅为按列公式的标签）。
> 因此应按上海−武汉方向理解差值方向，详见
> [clock/PROFESSIONAL_CORRECTION_REPORT.md](clock/PROFESSIONAL_CORRECTION_REPORT.md)。

## 数据来源与模型

* 日月星历：NASA/JPL `DE440s` 星历（Park et al. 2021, DOI
  `10.3847/1538-3881/abd414`），由仓库内置的 `data/de440s.bsp` 提供（MD5
  `3917ee56769db332790c751e2168843d`，可在
  [JPL NAIF](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/) 核对），
  并由 [Skyfield](https://rhodesmill.org/skyfield/) 读取。
* 固体潮：在地固系中按球谐加法定理将二、三阶潮汐生成势展开，采用 IERS
  Conventions (2010) 表 6.3 的**阶相关** Love 数（k₂ 分 m=0/1/2：
  `0.30190`/`0.29830`/`0.30102`；k₃=`0.093`），并对主导分潮叠加表 6.4/6.5c/7.1
  与式 6.12/7.4a 的**频率相关** Love 数改正（Step 2，含日潮 FCN 共振与长周期
  滞弹性）。输出同时给出潮汐生成势、地球诱导势，以及地表随形点的有效势
  `(1 + kₙ - hₙ)Vₙ`。见 [CREDIBILITY_PLAN.md](CREDIBILITY_PLAN.md)。
* 海潮负荷：默认读取 [International Mass Loading Service](https://massloading.net/)
  预计算的站点海潮负荷位移（HARPOS 格式，FES2014b 模型，44 条谐波）。程序重建
  径向位移时间序列，并以一阶关系 `δW = -γ δh` 转换为站点随形势变化。
  也可用 `--blq` 指定 [Onsala Ocean Tide Loading Provider](https://barre.oso.chalmers.se/loading/)
  生成的 BLQ 系数（11 个主分潮）；同时给出 `--harpos` 与 `--blq` 时 HARPOS 优先。
  完整结果推荐用 `--professional-ocean` 指定专业提供的权威海潮负荷序列（30 秒
  网格，覆盖 HARPOS/BLQ），详见 `PROFESSIONAL_CORRECTION_REPORT.md`。
* 站点坐标：IGS20 框架（epoch 2015.0，ITRF2020），取自
  [IGS 站点日志](https://files.igs.org/pub/station/log/) 与
  [igs.snx](https://files.igs.org/pub/station/general/igs.snx)。

海潮负荷位移由 massloading.net 基于 FES2014b 潮汐模型预计算；未包含大气负荷、
极潮和静态重力场。结果适合研究潮汐变化趋势，不应替代毫米级大地测量产品。

## 安装

需要 Python 3.11 或更高版本：

```bash
python -m pip install -e .
```

## 获取海潮负荷数据

仓库已内置两个站的 FES2014b 海潮负荷系数
（`data/wuhn_shao_fes2014b.harpos`，HARPOS 格式，来自
[International Mass Loading Service](https://massloading.net/)，44 个分潮）。

也可从 Onsala 服务获取 BLQ 系数：选择同一个海潮模型（推荐 FES2014b），提交以下
坐标，并将两个站的结果合并保存为一个 BLQ 文件：

| 站点 | 纬度 | 经度 | 椭球高 |
|---|---:|---:|---:|
| WUHN | 30.531653°N | 114.357261°E | 28.2 m |
| SHAO | 31.099642°N | 121.200445°E | 22.09 m |

Onsala 服务要求通过电子邮件交付结果，因此内置的 HARPOS 文件取自可公开下载的
massloading.net 预计算数据集。

## 计算

```bash
# 权威海潮负荷（推荐）：用专业提供的 30 秒海潮之差序列替换 HARPOS
gravitation-whsh \
  --professional-ocean data/professional_ocean_loading_30s.csv \
  --output results/wuhan_shanghai_20260620_20260826.csv \
  --plot results/wuhan_shanghai_20260620_20260826.svg

# 或不含专业数据、纯模型计算：
gravitation-whsh \
  --harpos data/wuhn_shao_fes2014b.harpos \
  --output results/wuhan_shanghai_20260620_20260826.csv \
  --plot results/wuhan_shanghai_20260620_20260826.svg
```

海潮负荷项有三个来源，优先级从高到低：
`--professional-ocean`（专业权威序列，覆盖海潮负荷）> `--harpos` > `--blq`。
HARPOS FES2014b 的海潮负荷幅度相对专业数据偏低约 3.9 倍（SHAO M₂ ~8 mm vs
专业 ~30 mm），故完整结果推荐用 `--professional-ocean`。

仓库内置 `data/de440s.bsp`，默认即可完全离线运行；也可用
`--ephemeris /path/to/de440.bsp` 指定完整版 JPL 星历。日期范围按两个日期都
完整包含，共 68 天、97,920 个分钟历元。
程序同时生成 SVG 折线图；横轴为日期与时刻（`YYYY-MM-DD` / `HH:MM`，UTC），纵轴为
`SHAO − WUHN` 潮汐重力势差（m²/s²）。CSV 的 `elapsed_minutes` 列仍给出从起始时刻
算起的分钟数，便于与时间轴对应。

CSV 的关键列：

* `solid_effective_delta_m2_s2`：固体潮有效势差；
* `ocean_loading_delta_m2_s2`：海潮负荷随形势差；
* `total_tidal_delta_m2_s2`：上述两项之和；
* `energy_change_per_kg_j`：与总潮汐势差相同，明确表示每千克的焦耳数。

若只需验证固体潮流程，可显式使用 `--allow-no-ocean`；此时海潮列为空，不能称为
完整结果。

## 验证

```bash
python -m unittest discover -s tests -v
```

## 光钟比对潮汐分析

潮汐引力势差 ΔW 通过广义相对论引力红移（`Δf/f = ΔW/c²`）影响武汉—上海两地
光钟（Yb/Sr）比对的频率差。`clock/` 目录记录了把理论潮汐势差与实测 1550 nm
环外链路拍频（FXE_B8）及 `atomic-clock-comp.pdf` 的 14 组实验记录比对的分析，
完整报告见 [clock/ANALYSIS.md](clock/ANALYSIS.md)。

关键结果：

- **时区与系数修正**：拍频时间戳为北京时间（UTC+8），潮汐 CSV 为 UTC，比对前
  须 `−8 h` 对齐；拍频→钟频分差的换算系数 `COEF = 4.282082163269648e-15`（由
  MATLAB `Dr` 公式推导），而非早期脚本误用的 `×F_BEAT`。另发现时间戳 ±1 s 抖动
  （数据本质为均匀 1-s 采样），已按 MATLAB 约定重建均匀时间轴。
- **14 段无跳点批量分析**：14 段全部有数据（已修复漏加载 6 月 `2606*.txt` 后
  组 1–5 恢复），逐段 1200-s 三角窗 + 幅度拟合。单段大多不显著，但 **12/14 段
  相关系数为负，跨段合并后显著负相关**（Stouffer |z| = 6.33，p = 2.5e-10，
  加权 r ≈ −0.17，A = −0.52±0.08/6.8σ）。
- **关键发现**：这一致负向最可能是潮汐模板符号方向相反所致；若方向取反
  （`−ΔW/c²`），则潮汐引力红移以**正确方向、部分幅度**被检出。确认需 Yb/Sr 钟
  部署站点与拍频符号约定。
- **信号被链路噪声淹没**：潮汐信号（Δf/f rms ~4.8e-18）比 1200-s 积分后的链路
  噪声（~1.7e-17）小约 3.6 倍，故单段必然不显著，仅跨段合并能累加出符号趋势。
- **14 组会话均值相关性**：Pearson r = +0.472（p = 0.088），方向为正、较旧模板
  提升但仍不显著（y_i 为 PDF 散点图数字化近似值）。

```bash
python clock/clock_tidal_shift.py            # 14 组会话平均潮汐频差
python clock/correlation_analysis.py         # 14 组会话相关性（y_i 数字化）
python clock/segment_analysis/batch_analysis.py   # 14 段批量分析（核心）
python clock/segment13_correlation.py        # 第 13 组多 τ 相关 + 幅度拟合
```

> 原始实验数据与 MATLAB 处理程序位于 `clock/data/`，已由 `.gitignore` 排除，
> 不上传 GitHub。

## 专业数据交叉验证

专业人士提供了 30 秒间隔的武汉—上海潮汐结果（2026-06-20 ~ 09-10），并对本项目
结果做了差异评估。对比结论见
[clock/PROFESSIONAL_CORRECTION_REPORT.md](clock/PROFESSIONAL_CORRECTION_REPORT.md)：

- **固体潮**：波形完全一致（r=1.0000），幅度差 ~5.2% 来自本项目采用的 IERS 2010
  阶相关 + 频率相关 Love 数改正（比专业数据用的名义 h₂/k₂ 更完整，非错误）。
- **海潮负荷**：波形一致（r≈+0.78）但幅度偏低约 3.9 倍——本项目 HARPOS FES2014b
  的 SHAO 海潮负荷 M₂ 仅 ~8 mm，专业数据约 30 mm。已用专业权威序列替换并固化
  （`--professional-ocean`），见
  [clock/PROFESSIONAL_CORRECTION_REPORT.md](clock/PROFESSIONAL_CORRECTION_REPORT.md)。
- 专业数据换算序列已存为 `data/professional_ocean_loading_30s.csv`（海潮之差）与
  `results/professional_tidal_delta_30s.csv`（综合差），供下游钟比对分析复用。

## 参考资料

1. Petit, G. & Luzum, B. (eds.), *IERS Conventions (2010)*, TN 36,
   Chapters 5 and 7.
2. Farrell, W. E. (1972), Deformation of the Earth by surface loads,
   *Reviews of Geophysics*, 10(3), 761–797.
3. Scherneck, H.-G. (1991), A parametrized solid earth tide model and ocean
   loading, *Geophysical Journal International*, 106(3), 677–694.
