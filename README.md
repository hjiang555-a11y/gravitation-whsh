# 武汉—上海潮汐引力势差

本项目计算 2026-06-20 00:00 至 2026-08-26 23:59（UTC）期间，武汉
`WUHN00CHN` 与上海佘山 `SHAO00CHN` 两个 IGS 站之间每分钟的潮汐引力势差：

```text
ΔW = W(SHAO) - W(WUHN)       [J/kg = m²/s²]
```

这里的“势能变化”按**单位质量的引力势变化**报告。质量为 `m` kg 的物体对应势能
变化为 `m × ΔW` J。结果只包含随时间变化的固体潮和海洋潮汐负荷项，不包含
EGM2008 静态重力场，因此不会把与潮汐无关的高程/纬度静态势差混入结果。

## 数据来源与模型

* 日月星历：NASA/JPL 公共 `DE440s` 星历，由
  [Skyfield](https://rhodesmill.org/skyfield/) 下载并读取。
* 固体潮：用 JPL 日月地心矢量计算二、三阶潮汐生成势，并采用 IERS Conventions
  (2010) 的名义 Love 数。输出同时给出潮汐生成势、地球诱导势，以及地表随形点
  的有效势 `(1 + kₙ - hₙ)Vₙ`。
* 海潮负荷：读取 [Onsala Ocean Tide Loading Provider](https://barre.oso.chalmers.se/loading/)
  生成的 BLQ 系数。程序重建 11 个主要分潮的径向位移，并以一阶关系
  `δW = -γ δh` 转换为站点随形势变化。
* 站点坐标：[IGS Network](https://network.igs.org/) 的 WUHN00CHN 与
  SHAO00CHN 坐标。

海潮部分是基于 11 个主分潮的工程近似，不是完整 342 分潮 HARDISP 卷积；未包含
大气负荷、极潮和静态重力场。BLQ 相位采用 Scherneck/Onsala 约定，当前实现未施加
分潮交点调制，适合研究潮汐变化趋势，不应替代毫米级大地测量产品。

## 安装

需要 Python 3.11 或更高版本：

```bash
python -m pip install -e .
```

## 获取 BLQ 数据

在 Onsala 服务中选择同一个海潮模型（推荐 FES2014b），提交以下坐标，并将两个站
的结果合并保存为一个 BLQ 文件：

| 站点 | 纬度 | 经度 | 椭球高 |
|---|---:|---:|---:|
| WUHN | 30.531653°N | 114.357261°E | 28.2 m |
| SHAO | 31.099370°N | 121.200250°E | 26.0 m |

服务可能要求通过电子邮件交付结果，所以仓库不伪造或内置模型系数。

## 计算

```bash
gravitation-whsh \
  --blq data/wuhn_shao.blq \
  --output results/wuhan_shanghai_20260620_20260826.csv
```

首次运行会从 JPL 下载约 32 MB 的 `de440s.bsp` 到用户缓存。若已下载，可用
`--ephemeris /path/to/de440s.bsp` 离线运行。日期范围按两个日期都完整包含，共
68 天、97,920 个分钟历元。

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

## 参考资料

1. Petit, G. & Luzum, B. (eds.), *IERS Conventions (2010)*, TN 36,
   Chapters 5 and 7.
2. Farrell, W. E. (1972), Deformation of the Earth by surface loads,
   *Reviews of Geophysics*, 10(3), 761–797.
3. Scherneck, H.-G. (1991), A parametrized solid earth tide model and ocean
   loading, *Geophysical Journal International*, 106(3), 677–694.
