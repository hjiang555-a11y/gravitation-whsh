# results/audit-v1 — 阶段一审计结果存档

阶段一（数据分析审计）的权威结果层。本目录由 audit 通道生成；数值真源是 manifest，
而非散落产物。存档提交时的结构如下。

## 结构

| 路径 | 内容 |
|---|---|
| `verified` → `runs/<hash16>` | 原子切换的符号链接，指向当前已验证（verified）运行 |
| `runs/<hash16>/manifest.json` | 权威结果清单（schema 1.1）；`<hash16>` = 本文件 SHA-256 前 16 位 |
| `runs/<hash16>/ANALYSIS_AUDIT.md` | 仅由 manifest 渲染的审计报告（源中无硬编码数值） |
| `runs/<hash16>/…` | 该次运行的账本、比值、统计与潮汐换算产物（staging 已并入） |
| `verification-<UTC>/` | Task 15 端到端验证运行（历史过程证据，非当前权威） |

本存档提交时的权威运行：`runs/15725f5246e87af5`（生成于提交 `a070eeb`，`dirty=false`）

manifest SHA-256：`15725f5246e87af5a450c8e31ccf0d0ef277d517a493ed1fb44d65a4b86564d4`

## 复现（需本地原始拍频数据与专业潮汐工作簿；二者按策略不入库）

```bash
uv sync --extra test
uv run python run_all.py --mode audit --output-dir results/audit-v1
uv run python -m clock_ratio.verify_result_manifest results/audit-v1/verified/manifest.json
uv run python -m clock_ratio.audit_report --manifest results/audit-v1/verified/manifest.json
```

## 说明

- 审计运行是 fail-fast + 事务式的：中间产物先写入固定 `staging/`，经 manifest 构建与
  独立验证后才提升为不可变 `runs/<hash16>/` 并原子切换 `verified` 符号链接；失败运行
  不产生运行目录，也从不删除既有运行。
- `manifest.json.run.json` 是该次运行的元数据（仅生成时间）；可比对载荷在
  `manifest.json` 内，不含运行时间。
- 每个运行目录的 `tide-conversion/professional_tidal_delta_30s.csv` 为专业潮汐工作簿
  换算的 30 s 序列；与 `results/professional_tidal_delta_30s.csv` 存在已知差异
  （max|Δ| = 2.02736e-5 m²/s²，见同目录 `.diff.json`），属记录的待确认外部输入，
  不是回归。
- 16 段为临时（provisional）主结果（第 9 段因参数待确认而隔离）；17 段与
  leave-one-out 为敏感性结果。
- 重新运行会产生新的 `runs/<hash16>/` 并移动 `verified` 链接（在 git 中显示为改动）；
  是否提交新运行由使用者决定。
- 历史验证运行可能由较早的 schema 生成（如 `verification-20261007T161859Z` 为 schema 1.0，
  缺少此后新增的 `segment_statuses` 字段）；当前工具对它们可能无法直接复用校验/渲染，
  以生成当时的记录为准，权威结果只认 `verified` 指向的运行。
