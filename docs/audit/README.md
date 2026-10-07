# 阶段一审计：新旧对照文本存档（docs/audit/）

本目录保存阶段一审计工作区（`.superpowers/sdd/2026-10-06-clock-analysis-audit/`）中
任务 7/9/10/12 的新旧结果对照记录（内容原样复制，未做修改）。审计工作区不再保留这些
证据后，仍可在此查阅；`clock_ratio/audit_report.py` §9/§10 的指针同步引用本目录。

| 文件 | 比较内容 | 提交范围 | 用途 |
|---|---|---|---|
| `task-07-window-baseline-vs-current.txt` | 冻结的 44abd1a 历史三角窗基线脚本 vs 修复后当前脚本（CSV 无差异、PNG 哈希一致） | 44abd1a → 6ec394c/a4200c0 | 证明窗口迁移后批处理基线与历史实现逐位一致 |
| `task-07-batch-tracked-vs-rerun.txt` | Task 7 之前的跟踪批处理产物 vs 修复后脚本重跑（逐字段 diff） | Task 7 修复前产物 → 修复后重跑 | 记录跟踪产物陈旧差异；**该差异反映 Task 7 前跟踪产物未随窗口修复更新，不是回归** |
| `task-07-batch-head-vs-current.txt` | 捕获时 HEAD 基线 vs 修复后当前脚本（逐字段 diff） | 6f6b637 → 6ec394c | 轮次修复过程中的批处理差异对照，后续由 a4200c0 归零 |
| `task-09-stats-old-vs-new.txt` | 旧块均值 `oadev`（`git show b130276:...`）vs 新 gap-safe OADEV（当前 worktree） | b130276 → d63d8c6 | 估计量变更的逐段 u_i / 合并值差异审计 |
| `task-10-scenarios-old-vs-new.txt` | 旧代码（d63d8c6）vs 统一情景层 `statistical_scenarios`（211986e） | d63d8c6 → 211986e | 情景 JSON 键集与 16 段合并值一致性审计 |
| `task-12-covariance-old-vs-new.txt` | 冻结 `c996e6d` 的 `batch_analysis.py` vs 追加协方差列的新实现 | c996e6d → fd1f7de | 协方差列追加不改变既有列/行/PNG 的审计 |

说明：

- 所有对照均在审计工作区内以冻结副本 / `git show <rev>:<path>` 方式运行，
  不重写任何跟踪产物；跟踪产物如有再生成，均已恢复且从未提交。
- `task-07-batch-tracked-vs-rerun.txt` 中的「before」为 Task 7 修复前生成的跟踪产物，
  「after」为 Task 7 修复后脚本的重跑输出；两者差异属产物陈旧，**不是数值回归**。
- 本目录文件仅作文本证据存档，不参与审计流水线；权威数值仍以
  `results/audit-v1/verified/manifest.json` 及其生成的 `ANALYSIS_AUDIT.md` 为准。
