# 分析审计报告（ANALYSIS_AUDIT）

本文件仅由通过验证的结果清单（manifest）生成；渲染前调用 `reconcile_manifest` 再次对账全部内部一致性规则。

- 清单模式版本（schema_version）：1.0
- 生成提交（git_commit）：`cb76614fb9d884d10448a11656ae3dab90ac2169`；工作区脏标记（dirty）：否
- Python：3.12.3
- 关键依赖（按包名排序）：`matplotlib` 3.11.2、`numpy` 2.5.3、`pydantic` 2.13.5、`scipy` 1.18.1、`typer` 0.27.2

## 1. 输入与来源状态

### 输入

| 相对路径 | sha256[0:16] | 大小（字节） | 状态 |
|---|---|---|---|
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260627_1.txt` | `742ba484024f5b4b` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260628_1.txt` | `656cc828870d6708` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260629_1.txt` | `f5781a875d696395` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260630_1.txt` | `1b44d3e5f62eb075` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260701_1.txt` | `adea83a264561072` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260702_1.txt` | `4f71b44d5ce973fd` | 17020800 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260703_1.txt` | `1b7409d1f0772df5` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260704_1.txt` | `648e39b7ae0219ac` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260705_1.txt` | `a5c804e1019d5804` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260706_1.txt` | `dd9261023c835c9d` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260707_1.txt` | `372ac52315bb7018` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260806_1.txt` | `c41c450d3d419030` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260807_1.txt` | `8a9cff27081bd39e` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260808_1.txt` | `dd79d8de913b1240` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260809_1.txt` | `53e2619d5eb8ee18` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260810_1.txt` | `151899e5eb416ff3` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260811_1.txt` | `00d37c725f62645a` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260812_1.txt` | `d8c3dca345653c23` | 51749764 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260820_1.txt` | `c8db7509261bcdb8` | 6088321 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260821_1.txt` | `5c2cbb0911bcf6ab` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260822_1.txt` | `d8cb9fb2337983e1` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260823_1.txt` | `1c704e83f8a3dc90` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260824_1.txt` | `040178413975add6` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260825_1.txt` | `f78e68d6f459fbde` | 17021422 | `established` |
| `../../../clock/data/环外数据（第八列数据）/Freq_B_2_260826_1.txt` | `9f796c4abdf716a8` | 17021422 | `established` |

### 参数

| 相对路径 | sha256[0:16] | 大小（字节） | 状态 |
|---|---|---|---|
| `clock/params.json` | `a2a05ef7ed0c3b7d` | 3321 | `established` |

### 产物

| 相对路径 | sha256[0:16] | 状态 |
|---|---|---|
| `sample_ledger.csv` | `9f7f5de0afb65763` | `established` |
| `time_quality.json` | `8aeb201d52115ef9` | `established` |
| `parameter_ledger.csv` | `ad5ad1d6d2a72786` | `established` |
| `parameter_conflicts.json` | `1d5a854a88ee5568` | `established` |
| `tide-conversion/professional_tidal_delta_30s.csv` | `f280e43c15ee768e` | `established` |
| `tide-conversion/professional_tidal_delta_30s.diff.json` | `728f35c50627d8e1` | `established` |
| `statistical_methods_tidal.json` | `acca6afefc156b50` | `established` |
| `statistical_methods_tidal_seg9_excluded.json` | `0308aee20f03e6a5` | `established` |

## 2. 样本账本与时间质量

- `sample_ledger.csv` 完整 sha256：`9f7f5de0afb65763514ef5540a9f5224eb9847627bc3845b3badddba08a5d03c`
- `time_quality.json` 完整 sha256：`8aeb201d52115ef91d6e258c8565ae3fe0a05d6e90328adbaefff83c3470e972`
- 16 段：n_segments = 16，total_samples = 986416；等式 `total_samples == Σ segment_n_valid`：成立
- 17 段：n_segments = 17，total_samples = 1008912；等式 `total_samples == Σ segment_n_valid`：成立

时间质量的内部细节（label 与均匀时间轴之间的差异量化、外部总数对账）位于已哈希的 `time_quality.json` 内；本报告不复述其中的数值。

## 3. 第 9 段隔离

- 16 段临时主结果：`excluded_groups` = (9,)，即排除第 9 段：成立。
- 17 段敏感性结果：`included_groups` 含第 9 段：成立；`excluded_groups` = ()。
- Leave-one-out：排除第 9 段的条目存在：成立。

## 4. 16 段临时主结果

- 情景：`raw`；响应系数：`0`；段数：16
- 包含段：1、2、3、4、5、6、7、8、10、11、12、13、14、15、16、17
- 排除段：9
- 时长加权比值（duration_weighted_ratio）：`1.2075070393433377201798925422298889411271180924277187417854518806996414723312918`
- 总样本（total_samples）：986416；等式 `total_samples == Σ segment_n_valid`：成立

| 字段 | 数值 |
|---|---|
| R_seg1 | `1.2075070393433377209511392342884451167413791027221712598810109303259159213121598` |
| R_wls | `1.2075070393433377200464104337868920419305439666264194521188560456494883520088030` |
| R_mp | `1.2075070393433377205519661184561686865486879863554356316437687495815956453706540` |
| R_bayes | `1.2075070393433377205630643505541719423190803014306306585972367401019724827739822` |
| u_wls | 3.33746e-19 |
| chi2 | 60.2503 |
| dof | 15 |
| chi2_red | 4.017 |
| p_chi2 | 2.28407e-07 |
| birge_ratio | 2.00417 |
| u_birge | 6.68882e-19 |
| xi_mp | 2.49812e-18 |
| u_mp | 7.88105e-19 |
| mu_bayes | -3.21385e-19 |
| u_stat_bayes | 8.85481e-19 |
| xi_bayes | 2.8328e-18 |

该结果为阶段一临时（provisional）主结果：第 9 段因参数待确认而被隔离；待专业潮汐输入的物理模型来源外部确认后冻结。

## 5. 17 段敏感性结果

- 情景：`raw`；响应系数：`0`；段数：17
- 包含段：1、2、3、4、5、6、7、8、9、10、11、12、13、14、15、16、17
- 排除段：（无）
- 时长加权比值（duration_weighted_ratio）：`1.2075070393433377203695663475692647402466509985105627343026029475466651648186284`
- 总样本（total_samples）：1008912；等式 `total_samples == Σ segment_n_valid`：成立

| 字段 | 数值 |
|---|---|
| R_seg1 | `1.2075070393433377209511392342884451167413791027221712598810109303259159213121598` |
| R_wls | `1.2075070393433377203508308164214641935543357052536743204004013654453495112214479` |
| R_mp | `1.2075070393433377211047583193618757168764464461666254035945404733639278067032786` |
| R_bayes | `1.2075070393433377211081341623810528868922563885110506780237704388403490692156701` |
| u_wls | 3.27813e-19 |
| chi2 | 83.8637 |
| dof | 16 |
| chi2_red | 5.241 |
| p_chi2 | 3.32345e-11 |
| birge_ratio | 2.28943 |
| u_birge | 7.50505e-19 |
| xi_mp | 3.06195e-18 |
| u_mp | 8.86949e-19 |
| mu_bayes | 1.30016e-19 |
| u_stat_bayes | 9.83381e-19 |
| xi_bayes | 3.40232e-18 |

本表为敏感性检查，不替代第 4 节的临时主结果；第 9 段在内。

## 6. Leave-one-out

逐个排除一段的敏感性扫描；数值直接取自清单条目。

| 排除段 | R_wls | chi2_red | u_wls |
|---|---|---|---|
| 第 1 段 | `1.2075070393433377203128849332622190555838615214247067286247736416526990237968947` | 5.577 | 3.38015e-19 |
| 第 2 段 | `1.2075070393433377205444753458683651140284228734639402195246384339593958304344759` | 5.176 | 3.36884e-19 |
| 第 3 段 | `1.2075070393433377202933607427392966511584261721363945435839526668703960674993656` | 5.484 | 3.30926e-19 |
| 第 4 段 | `1.2075070393433377207913590331794992815921818555974629109993630992876864629465718` | 4.233 | 3.42039e-19 |
| 第 5 段 | `1.2075070393433377203578705444029445080335429721980541018097099868684377324287017` | 5.576 | 3.28145e-19 |
| 第 6 段 | `1.2075070393433377206581275542010136625773522839835339096663852284843396339279020` | 5.441 | 3.86436e-19 |
| 第 7 段 | `1.2075070393433377199538664973270215998703958824839391793931884032910927803255962` | 3.863 | 3.36959e-19 |
| 第 8 段 | `1.2075070393433377203444002245418886836203078295625952750447698009073697977779003` | 5.584 | 3.28409e-19 |
| 第 9 段 | `1.2075070393433377200464104337868920419305439666264194521188560456494883520088030` | 4.017 | 3.33746e-19 |
| 第 10 段 | `1.2075070393433377203673465232495387248953882555243314940013382245256404038879741` | 5.588 | 3.36105e-19 |
| 第 11 段 | `1.2075070393433377202977988107468402356684198653370301058144004388130995694850452` | 5.467 | 3.3012e-19 |
| 第 12 段 | `1.2075070393433377203127762487324713526675361658208902605259043204866380907846270` | 5.556 | 3.31999e-19 |
| 第 13 段 | `1.2075070393433377204334056163530995718237459109183369678295891328233997574871506` | 5.430 | 3.32104e-19 |
| 第 14 段 | `1.2075070393433377202303025169432103634315484034132665984804012066734242058191477` | 5.368 | 3.34378e-19 |
| 第 15 段 | `1.2075070393433377203370464601450260810015450383883444006540736103821019110596128` | 5.588 | 3.35283e-19 |
| 第 16 段 | `1.2075070393433377204336660037765129238026848519870695347308128373902030780843710` | 5.574 | 3.66516e-19 |
| 第 17 段 | `1.2075070393433377203586684536083279719252281121802419385746294224457932268135440` | 5.589 | 3.3048e-19 |

## 7. 潮汐方法验证

- 源列（source_column）：`综合差`；方向：`CAS-minus-SHA`；时区：`UTC`
- 预期步长：30 s；重力加速度：`9.794` m/s²
- 行数：转换 239040 / 参考 239040 / 公共前缀 239040
- 最大时间差：0 s；最大数值差：`0.0000202736`
- 首个不一致行：第 1 行（value_diff = -0.000005889399999931442）
- 状态：`pending-verification`

## 8. 不确定度预算

| 组件 | 修正 | 标准不确定度 | 状态 | 必需 |
|---|---|---|---|---|
| `statistical` | — | 8.854811496434007E-19 | `established` | 是 |
| `sr-systematic` | — | — | `pending-verification` | 是 |
| `static-potential` | — | — | `external-unverified` | 是 |
| `yb-systematic` | — | — | `pending-verification` | 是 |
| `link` | — | — | `pending-verification` | 是 |
| `comb` | — | — | `pending-verification` | 是 |
| `tidal-residual` | — | — | `pending-verification` | 是 |

- 已知分量合成（known_quadrature）：`8.854811496434007E-19`
- 总标准不确定度：未给出（withheld）
- 扣留原因：仍有 6 个必需（required）组件未建立（状态非 established 或缺少标准不确定度）。
- 预算状态：`pending-verification`

相关矩阵（按组件声明顺序；紧凑行）：
  - `statistical`：1.000  0.000  0.000  0.000  0.000  0.000  0.000
  - `sr-systematic`：0.000  1.000  0.000  0.000  0.000  0.000  0.000
  - `static-potential`：0.000  0.000  1.000  0.000  0.000  0.000  0.000
  - `yb-systematic`：0.000  0.000  0.000  1.000  0.000  0.000  0.000
  - `link`：0.000  0.000  0.000  0.000  1.000  0.000  0.000
  - `comb`：0.000  0.000  0.000  0.000  0.000  1.000  0.000
  - `tidal-residual`：0.000  0.000  0.000  0.000  0.000  0.000  1.000

## 9. 协方差感知潮汐推断（限制说明）

协方差感知的 GLS 与块自助（block-bootstrap）验证已在阶段一中实现并复核；其覆盖诊断未嵌入本清单模式，因此本报告不复述其数值。证据与复核记录见提交 `c996e6d..fd1f7de`。

## 10. 新旧结果差异（限制说明）

估计量与聚合方式的新旧审计（块均值改为 gap-safe OADEV；情景统一；协方差列）已在任务 7/9/10/12 中记录并复核；本清单模式不嵌入历史基线数值，因此本报告不复述其数值。证据见提交 `44abd1a..eff7021`。

## 11. 外部确认项

- 预算组件 `sr-systematic`：状态 `pending-verification`；来源：params.json shift_a components (a_rou, a_AC, a_SM, a_air, a_BBR); no closed uncertainty record exists yet
- 预算组件 `static-potential`：状态 `external-unverified`；来源：levelling documents for the Wuhan-Shanghai geopotential difference; no closed uncertainty record extracted yet
- 预算组件 `yb-systematic`：状态 `pending-verification`；来源：conflicting evidence unresolved: internal 1.1e-18 vs published 1.3e-18
- 预算组件 `link`：状态 `pending-verification`；来源：1550 nm fibre link; no executable uncertainty evidence
- 预算组件 `comb`：状态 `pending-verification`；来源：optical frequency comb; no executable uncertainty evidence
- 预算组件 `tidal-residual`：状态 `pending-verification`；来源：tidal residual model; no executable uncertainty evidence
- 潮汐方法验证（源列 `综合差`）：状态 `pending-verification`

## 12. 证据状态汇总

- `established`：34
- `pending-verification`：6
- `external-unverified`：1

## 13. 阶段一放行清单

- [PASS] 样本总数闭合：16 段 986416 = Σ 分段 986416；17 段 1008912 = Σ 分段 1008912。
- [POINTER] 外部计数的独立对账：证据位于已哈希的 `time_quality.json`，本报告不复述。
- [PASS] 第 9 段保留：17 段包含、16 段排除、leave-one-out 条目齐备。
- [PASS] 16/17 段结果与 17 条 leave-one-out 齐备（16、17、17）。
- [POINTER] label 与均匀时间轴的差异量化：证据位于已哈希的 `time_quality.json`。
- [PASS] 潮汐 Excel→CSV 比较明确：转换 239040、参考 239040、公共前缀 239040 行。
- [POINTER] 三角窗合成验证：由窗口相关单元测试覆盖。
- [POINTER] 重叠协方差处理或限制说明：见 §9。
- [POINTER] 新旧 OADEV 差异解释：见 §10。
- [PASS] 清单哈希已验证：审计流水线在渲染前由 `verify_result_manifest` 校验通过。
- [POINTER] 论文文件未变更：由审计命令集核对（git diff 为空）。
