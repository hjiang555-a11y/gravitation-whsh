# 阶段一审计总结（PHASE1_SUMMARY）

**状态：** 阶段一（实验数据分析审计）已完成并通过用户验收（2026-10-08）。
**日期：** 2026-10-08
**分支：** `worktree-clock-analysis-audit`；审计提交范围 `61329ad..f9a3339`（33 个提交），本归档提交为其收尾（均已推送 origin）
**记录说明：** 过程工作区 `.superpowers/sdd/2026-10-06-clock-analysis-audit/` 已按用户要求
删除；本文档、`results/audit-v1/` 与 git 历史为现存记录。审计期内的评审 diff 均可由上述
提交范围经 `git diff` 重建。

## 1. 权威结果层

- **权威清单：** `results/audit-v1/verified/manifest.json`（`verified` → `runs/15725f5246e87af5`）
  - SHA-256：`15725f5246e87af5a450c8e31ccf0d0ef277d517a493ed1fb44d65a4b86564d4`
  - schema 1.1；生成提交 `a070eeb`；`dirty=false`；`verify_result_manifest` 通过
- **审计报告（仅由清单渲染）：** `results/audit-v1/verified/ANALYSIS_AUDIT.md`
- **运行存档说明：** `results/audit-v1/README.md`

### 结果（raw 情景，未做潮汐修正；数值截断显示）

| 口径 | n | 样本 | R_wls | R_mp | R_bayes | u_wls | χ²_red |
|---|---|---|---|---|---|---|---|
| 16 段（隔离第 9 段，临时主结果） | 16 | 986,416 | 1.2075070393433377200464 | 1.2075070393433377205519 | 1.2075070393433377205630 | 3.3375e-19 | 4.017 |
| 17 段（敏感性） | 17 | 1,008,912 | 1.2075070393433377203508 | 1.2075070393433377211047 | 1.2075070393433377211081 | 3.2781e-19 | 5.241 |

- LOO：17 项完整生成（同一逐段事实层重算，不读预生成 JSON）。
- 模型受限段（Allan 斜率超出白频带、拟合状态 `supported-with-limitations`）：16 段中
  5 段（组 2、6、7、12、16）；17 段中 6 段（另含组 9）。已在审计报告中显式公开。
- 第 9 段：隔离于临时主结果，保留在 17 段敏感性与 LOO 中（未删除、未隐藏）。

### 过程结论

- 潮汐 Excel→CSV：239,040 / 239,040 行；max|Δ| = 2.02736e-5 m²/s²（状态
  `pending-verification`；已知差异，非回归）。
- 不确定度预算：已知分量合成 8.854811496434007E-19；最终总量 withheld（required 分量未全部
  established，状态 `pending-verification`）；Yb 冲突（1.1e-18 vs 1.3e-18）记录未决。
- 协方差感知潮汐推断校准（200 种子）：GLS 覆盖率 0.920（通过 [0.90, 0.99] 门）；
  moving-block bootstrap 0.895（记为诊断）；朴素 OLS 0.750。未调参、未挑选、未 xfail。

## 2. 验证与审查

- 质量门：快速套件 `225 passed, 4 skipped`；`RUN_CLOCK_DATA_TESTS=1` `229 passed`；
  audit E2E（staging → manifest → verify → report → promote）全绿。
- 逐任务独立审查（规格符合 + 质量）；最终全分支审查（`61329ad..cb76614`）结论
  "With fixes"（1 Important + 6 Minor + 1 建议）→ 单一修复波次（`437a237`、`a070eeb`）
  → 限定范围复审：全部发现闭环、无新增 Critical/Important。
- 独立复核要点：manifest reconcile 规则实际绑定（成员/求和/时长重算/哈希/预算一致性）；
  哈希复验通过；promoted 主结果由 staged 逐段事实独立复算一致（R_wls 至 27 位、
  χ² 至 ~1e-15）；`paper/`、`archive/` 相对计划起点零改动。

## 3. 执行期间的关键决策（Rulings）

1. **环境与依赖**：uv + pyproject 锁定环境；Excel 解析固定 `openpyxl>=3.1,<4`；
   未声明环境缺少 pytest 不视为基线失败（Task 1 环境即首个有效基线）。
2. **统计主结果口径**：仓库可复现的 Bayesian 随机效应为中心值主结果（用户指示）；
   WLS / Birge / Mandel–Paule / 固定效应保留为诊断与敏感性；"可复现主结果"不含实验方
   外部 MCMC。
3. **窗口基线**：历史非零端点三角窗权重保留为批处理基线；`np.bartlett(1200)` 作为独立
   敏感性方案（切换需受控基准更新）。
4. **段不确定度政策**：<3 个可用拟合点 → `u=None` 且 fail-fast（拒绝静默回退最长 τ）；
   ≥3 → 计算；斜率 ∈ [−0.65, −0.35] 才 `established`，否则带旗标纳入（模型受限段不被
   静默阻塞）。
5. **外推时长**：T = 最长连续 run（gap-safe，非保留样本数）；拟合窗 `128 s ≤ τ ≤ 0.25T`；
   τ 取 `tau_grid`。
6. **兼容迁移**：旧 `oadev` / `extrapolate_u` 逐字节保留至调用方迁移；
   `endpoint_screen` / `segment_traces` 仅在 grep 证明无外部引用后移除（后由 Task 15
   修复一个被遗漏的导入方）。
7. **seg9 适配契约**：seg9 CLI 保持 `SOURCE_JSON` 输入契约；旧 schema `n_valid := T_s`；
   比值 Decimal80 重建；输出新增顶层 `leave_one_out`；既有 `scenarios` / `n_segments` /
   `excluded_group` 不变。
8. **再生成 tidal JSON**：保留全部既有键；`per_segment` 增加 `n_valid`；不确定性估计迁移至
   gap-safe 估计器；与跟踪基线的数值偏移记录在案。
9. **Task 10 拆分**：连续派发失败后拆为 10a / 10b 两个提交（评审范围不变）。
10. **raw 情景**：跳过潮汐插值以与迁移前实现逐位一致。
11. **协方差方法定义**：GLS（AR(1) 三对角精度矩阵、run 内求和）+ moving-block bootstrap
    （按连续 run 分块、不跨缺口）；`n_windows` = 非重叠单元数（非重叠点计数）；
    `effective_n` = Σ n(1−ρ)/(1+ρ)；CI 口径按方法钉定；不新增 `fit_nonoverlap_ols`。
12. **主方法与覆盖率门**：批处理主方法 = GLS；覆盖率测试为方法验证门、不可调参；
    bootstrap 低于门时保留为诊断，不 xfail、不挑选最优。
13. **批处理产物**：追加协方差列/行；既有列、行、PNG 逐位不变；跟踪产物永不在提交中
    再生成。
14. **pyproject**：注册 `slow` marker；慢测试默认运行（全套时间 +~50 s）。
15. **promote 语义**：`os.replace(staging → runs/<sha16>)` + 相对目标原子切换 `verified`
    符号链接；永不删除旧运行；已存在的真实 `verified` 目录被拒绝。
16. **E2E 流程**：先备份 staging 至 /tmp；任一命令失败即 STOP/BLOCKED、不手改 staging；
    数据套件可能再生成跟踪产物 → 事后 `git checkout --` 恢复并报告。
17. **ledger builders**：补充 `sys.path` 引导（超出任务清单 2 个文件；Task 14 对
    `tide_conversion` 的同款先例，可直接 revert）。
18. **最终修复波次**：I1 + M1–M5 + M6 + R1 一次派发；manifest schema 升 1.1
    （旧 1.0 清单不再能被新工具读取，由新 E2E 运行取代）。

## 4. 已知保留项（审查后接受，不阻塞）

1. `clock_ratio/audit_report.py` 约 468 行，超出项目 250 行指引；职责单一，拆分延后。
2. 批处理协方差聚合在"全部段拟合失败"时会输出 nan/inf（当前 17 段数据不可触发；后续可加
   空集保护）。
3. 少数接线测试为半循环（期望值经同一合并函数构造）；数值正确性由独立 comb-chain 测试与
   快照测试另行覆盖。
4. 类型表面残留：`_build_scenario_result` 参数仍为 `str`（字段已用 `ScenarioKey`）；
   解码的 `fit_slope` 未做类型校验——运行时无影响。
5. `run_audit` 对真实 `verified` 目录的拒绝发生在 staging 改名之后（阶段一单操作者场景
   接受；建议后续 pre-flight）。
6. 历史 E2E 运行中 schema 1.0 的清单不能被当前工具直接校验/渲染（已在
   `results/audit-v1/README.md` 说明；权威结果只认 `verified` 指向的运行）。

## 5. 外部待确认输入（设计 §9）

- 第 9 段 `a_SM` 的实验记录与计算依据；第 15–17 段频移参数依据；
- 实验方 MCMC 代码、输入、先验与收敛输出；
- 三种样本总数口径（1,008,912 / 1,009,022 / 1,009,204）的原始统计表；
- Yb 系统不确定度采用 1.1 或 1.3×10⁻¹⁸ 的依据；
- 本实验链路与光梳不确定度评估；水准原始观测、归算与不确定度传播；
- 专业潮汐数据的提供者、模型、版本、坐标、参考框架与生成配置；
- 作者、单位、贡献、资金、致谢与利益冲突信息；原始数据与派生潮汐序列的公开授权。

## 6. 记录索引

- 本目录：`docs/audit/`（本总结 + task-07/09/10/12 新旧对照证据）
- 权威运行与 E2E 历史：`results/audit-v1/`（含 `README.md`）
- 计划与设计：`docs/superpowers/plans/2026-10-06-clock-analysis-audit.md`、
  `docs/superpowers/specs/2026-10-06-clock-comparison-audit-paper-design.md`
- 提交范围：`61329ad..f9a3339`（33 个提交，分支 `worktree-clock-analysis-audit`）

## 7. 后续

- **阶段二（论文重建）**：按设计文档 §7，须基于本冻结结果层另行编写并获审批的实施计划后
  启动；在此之前不得修改 `paper/`。
- **外部输入补齐后**：重跑 audit 流水线，可将临时（provisional）主结果升级为最终结果，
  并发布完整不确定度预算。
