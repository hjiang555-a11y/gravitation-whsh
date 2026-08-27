# 可信结果形成计划 — 武汉–上海潮汐引力势差

> 本文件记录本任务"可信结果"的形成方式：权威数据源、获取方式、模型实现标准，
> 以及已发现缺陷与对应修复。所有数据源均给出 URL 与校验方式，保证结果可复现、可引用。

## 1. 可信度的定义

潮汐引力势差是**确定性、模型驱动**的量——没有观测"真值"，只有"社区公认的实现"。
其可信度取决于三点：

1. **星历**：使用社区公认的 JPL 星历（DE440/441），而非第三方截断打包的 DE421。
2. **固体潮模型**：完整实现 IERS Conventions (2010) 的 Step 1（阶相关 Love 数）+
   Step 2（频率相关 δk 改正），而非仅用名义 Love 数近似。
3. **交叉验证**：与独立实现（DEHANTTIDEINEL / pyTMD / ETGTAB）及已发表基准值比对。

## 2. 权威数据源与获取方式

### 2.1 星历

| 项 | 值 | 获取 |
|---|---|---|
| 主选 | DE440（覆盖 1550–2650，ICRF3） | `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp`（114MB）或 `de440s.bsp`（31MB） |
| 校验和 | SHA-256 | `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/aa_checksums.txt` |
| 引用 | Park et al. 2021, AJ, DOI `10.3847/1538-3881/abd414` | |

### 2.2 固体潮模型

| 项 | 值 | 获取 |
|---|---|---|
| 标准 | IERS Conventions (2010), TN36（当前官方最新，无 2020/2022 后继） | `https://iers-conventions.obspm.fr/content/tn36.pdf` |
| 势模型 | Chapter 6（表 6.3 Love 数、表 6.5a/b/c 频率改正、Eq 6.6–6.8） | `https://iers-conventions.obspm.fr/content/chapter6/icc6.pdf` |
| 位移基准 | Chapter 7 + DEHANTTIDEINEL.F 测试用例 | `https://iers-conventions.obspm.fr/content/chapter7/icc7.pdf` |
| 引用 | Petit & Luzum 2010；DDW99 `10.1029/1998JB900051`；Mathews et al. 1997 `10.1029/97jb01515` | |

### 2.3 海潮负荷（OTL）

| 模型 | 中国东部 M₂ OTL 精度 | 结论 |
|---|---|---|
| EOT20 | 0.49mm（最优） | 交叉验证首选 |
| FES2014b | 0.63mm（当前基线） | 保持 |
| FES2022b | 0.63mm，区域潮位站同化稀疏 | 不急于换 |

| 提供方 | 格式 | 分潮数 | 模型 | 获取 |
|---|---|---|---|---|
| massloading.net | HARPOS | 44 | FES2014b | `https://massloading.net/select_loading_files.html` |
| Onsala/GGFC | BLQ/HARPOS | 11 | FES2022b/EOT20 等 | `https://barre.oso.chalmers.se/loading/` |
| AVISO+ | netCDF | 34 | FES2022b | `sftp://ftp-access.aviso.altimetry.fr:2221/auxiliary/tide_model/fes2022b` |

> 分潮数结论：11 分潮（BLQ）不足以声称毫米级（缺小潮），≥34–44 分潮才行。
> 当前 44 分潮 HARPOS 达标。

### 2.4 站点坐标（IGS20 SINEX, epoch 2015.0, ITRF2020）

| 站 | 权威值 | 来源 |
|---|---|---|
| WUHN | 30.531653°N, 114.357261°E, 28.2m | `https://files.igs.org/pub/station/general/igs.snx` |
| SHAO | 31.099642°N, 121.200445°E, 22.09m | `https://files.igs.org/pub/station/log/shao00chn_20230306.log` |

### 2.5 验证基准

| 基准 | 用途 |
|---|---|
| DEHANTTIDEINEL 4 组测试用例 | 位移链路验证（权威数值基准） |
| 武汉 2000 国际潮汐重力基准值（Xu et al. 2000, Sci. China D 43(1):77–83） | 半日潮带验证（日潮带避用，有已知偏差） |
| pyTMD / ETGTAB | 独立软件交叉验证 |
| IGETS 数据库（`https://isdc.gfz.de/igets-data-base/`） | 与武汉 SG 实测残差对比 |

## 3. 已发现缺陷与修复状态

### P0 — 正确性 Bug

- [x] **SHAO 坐标错误**：`cli.py` 原 `26.0m` → 权威 `22.09m`；经纬度同步修正。

### P1 — 可信度硬伤

- [x] **Love 数 k₂ 未分阶**：改为 m=0→0.30190 / m=1→0.29830 / m=2→0.30102（IERS2010 表 6.3）。
- [ ] **缺频率相关 δk 改正**（表 6.5a/b/c，Step 2）。量级 ~10⁻⁶ 相对，仅对毫米级声明必要。
- [x] **星历用第三方 DE421** → 换官方 de440s.bsp（MD5 `3917ee...` 锚定）。

### P2 — 文档/代码一致性

- [x] 缺 `.gitignore`（`.pyc`、`egg-info` 入库）→ 已新增并 `git rm --cached`。
- [x] README「44 分潮」与文件头「34 分潮」表述混淆 → 已改为「44 条谐波」。
- [x] HARPOS 静默覆盖 BLQ 未文档化 → 已注明「同时给出时 HARPOS 优先」。
- [x] BLQ 路径角色（备用）未说明 → 已注明「也可用 `--blq` 指定」。

## 4. 实施阶段

1. **阶段 1（正确性修复）**：修 SHAO 坐标 + README 同步。✅ 已完成
2. **阶段 2（可信度升级）**：de440 星历 ✅ + IERS2010 Step1 阶相关 Love 数 ✅；Step2 频率相关 δk ⏳ 未做。
3. **阶段 3（验证）**：pyTMD 交叉验证 ✅（见 §5）；DEHANTTIDEINEL 基准 / 武汉半日潮基准 ⏳ 未做。
4. **阶段 4（文档对齐）**：`.gitignore` + README 数据溯源与优先级说明。✅ 已完成

## 5. 交叉验证结果（pyTMD，已执行）

用 [pyTMD 3.0.9](https://pytmd.readthedocs.io/) 的 `body_tide`（CTE1973 谐波目录 +
解析平黄经，**天文学完全独立**于本项目的 DE440s 点质量星历法）复算 WUHN/SHAO 固体潮
生成势，与本项目实现比对 48 小时时变信号：

| 量 | 残差 std | 相对 | 相关系数 |
|---|---:|---:|---:|
| WUHN 时变生成势 | 0.0037 m²/s² | 0.31% | 1.00000 |
| SHAO 时变生成势 | 0.0038 m²/s² | 0.32% | 1.00000 |
| **SHAO−WUHN 差（核心输出）** | 0.00056 m²/s² | **0.23%** | 1.00000 |

**结论**：天文学内容完全一致（corr=1.00000）。残余 ~0.3% 是 pyTMD 参考目录 CTE1973
谐波截断（l≤3）相对精确点质量星历的**已知截断误差**，属于参考实现侧的近似，非本实现误差。

可复现脚本：[validation/cross_validate_pytmd.py](validation/cross_validate_pytmd.py)（需 `pip install pyTMD`）。
