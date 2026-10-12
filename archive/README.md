# archive 归档说明

> 本目录存放**历史/冻结/已过时**的材料（旧分析文档、旧论文包、阶段一计划等）。
> 保留是为了可追溯，但其中的结论**可能基于旧的 14 段数据、旧的幅度比 A≈−0.45、
> 旧的 COEF 归一化，或已废弃的 17 段潮汐检出叙事**，不作为当前权威结果。

## 当前权威文档

| 文档 | 说明 |
|---|---|
| `results/audit-v1/verified/manifest.json` | **权威数值真源**（阶段一审计；16 段临时主结果） |
| `paper/rev2/` | **当前论文候选稿**（16 段口径、潮汐为误差项；数字宏管线） |
| `clock_ratio/EXPERIMENT_REPORT.md` | 历史链总报告：钟比值 + 潮汐修正 + 段内/段均值相关性 |
| `docs/NOTATION.md` | 符号与术语表（COEF/F_1550 等符号的定义） |
| `clock/shared.py` | 代码单一真源（常量、段定义、数据加载） |

## 本目录归档内容与过时原因

| 材料 | 归档原因 |
|---|---|
| `ANALYSIS.md` | 与 EXPERIMENT_REPORT/FINAL_REPORT 重叠；含 14 段旧表述 |
| `FINAL_REPORT.md` | 与 EXPERIMENT_REPORT 重叠 |
| `CONCLUSION_17.md` | 段信息/钟比值已并入 EXPERIMENT_REPORT |
| `CORRELATION_REPORT.md` | 相关性结论已并入 EXPERIMENT_REPORT |
| `INVESTIGATION_NOTES.md` | 14 段时代的调研求证过程 |
| `PDF_METHODOLOGY_REVIEW.md` | 基于旧 14 段版 PDF（atomic-clock-comp.pdf）方法论证 |
| `PROJECT_REPORT.md` | 17 段「潮汐检出」叙事综合报告；与 rev2 16 段口径矛盾，2026-10 移入 |
| `temperature/` | 环外第二列数据 + 气温分析；分析链已切换第八列，零活跃引用 |
| `earthquake_analysis.{py,md}` | 地震效应粗估；零引用、无产物 |
| `segment17_correlation.{py,md}` | 17 点两两相关；run_all 已移除该步 |
| `physics_analysis/` | 早期 BSM/暗物质探测能力调研；框架被根目录 NATURE_FRAMEWORK.md 取代 |
| `overleaf-rev2/` + `overleaf-rev2-upload.zip` | rev2 旧 Overleaf 快照（被 `paper/overleaf-rev2-v2/` 取代） |
| `diffs/` | 针对冻结历史稿（main.tex / seg9 变体）的 latexdiff 产物，可再生成 |
| `superpowers/` | 阶段一审计的实施计划与设计规格（已验收完成） |

## 重要：旧幅度比 A ≈ −0.45 已被修正

归档文档（及其时代的所有报告）里的幅度比 **A ≈ −0.45** 是基于**错误的潮汐
拍频归一化**（`tide_beat = ΔW/c²/COEF`，隐含 233.53 THz）。正确归一化是
**1550 nm 传递光 `F_1550 = 193.40 THz`**，即 `tide_beat = (ΔW/c²) × F_1550`。

修正后幅度比 **A ≈ −0.54**（三种方法一致：原方法 −0.540、变体1 −0.538、
变体2 −0.539）。详见 `docs/NOTATION.md` 的 COEF/F_1550 说明。

> 另注：`PROJECT_REPORT.md` 与旧草稿（已删除的 `docs/PAPER_DRAFT*.md`）的
> 「潮汐检出 5.87σ / 6.4σ 已成立」叙事与当前 16 段口径（潮汐仅作不确定度项）
> 直接矛盾，引用时须以上方权威文档为准。
