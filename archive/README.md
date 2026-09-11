# archive 归档说明

> 本目录存放**历史/重叠/已过时**的分析文档。这些文档保留是为了可追溯，
> 但其中的结论**可能基于旧的 14 段数据、旧的幅度比 A≈−0.45、或旧的 COEF
> 归一化**，不作为当前权威结果。

## 当前权威文档

| 文档 | 说明 |
|---|---|
| `clock_ratio/EXPERIMENT_REPORT.md` | **总权威报告**：钟比值 + 潮汐修正 + 段内/段均值相关性 |
| `docs/NOTATION.md` | 符号与术语表（COEF/F_1550 等符号的定义） |
| `README.md` | 导航入口 + 符号表 |
| `clock/shared.py` | 代码单一真源（常量、17 段定义、数据加载） |

## 本目录归档内容与过时原因

| 文档 | 归档原因 |
|---|---|
| `ANALYSIS.md` | 与 EXPERIMENT_REPORT/FINAL_REPORT 重叠；含 14 段旧表述 |
| `FINAL_REPORT.md` | 与 EXPERIMENT_REPORT 重叠 |
| `CONCLUSION_17.md` | 段信息/钟比值已并入 EXPERIMENT_REPORT |
| `CORRELATION_REPORT.md` | 相关性结论已并入 EXPERIMENT_REPORT |
| `INVESTIGATION_NOTES.md` | 14 段时代的调研求证过程 |
| `PDF_METHODOLOGY_REVIEW.md` | 基于旧 14 段版 PDF（atomic-clock-comp.pdf）方法论证 |

## 重要：旧幅度比 A ≈ −0.45 已被修正

归档文档（及其时代的所有报告）里的幅度比 **A ≈ −0.45** 是基于**错误的潮汐
拍频归一化**（`tide_beat = ΔW/c²/COEF`，隐含 233.53 THz）。正确归一化是
**1550 nm 传递光 `F_1550 = 193.40 THz`**，即 `tide_beat = (ΔW/c²) × F_1550`。

修正后幅度比 **A ≈ −0.54**（三种方法一致：原方法 −0.540、变体1 −0.538、
变体2 −0.539）。详见 `docs/NOTATION.md` 的 COEF/F_1550 说明。
