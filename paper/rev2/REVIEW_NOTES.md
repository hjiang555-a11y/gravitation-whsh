# paper/rev2 候选稿审阅：篇幅与投稿格式对照

**日期**：2026-10-09（更新，含本轮审阅变更） · **对象**：`paper/rev2/`（16 段口径重建候选稿；`main.pdf` 11 页含附录）

## 0. 本轮（2026-10-09）审阅变更（已实施）

1. **题名**（按指定）：
   `An inter-city Sr/Yb optical clock comparison at the 2.1×10⁻¹⁸ uncertainty over a 1 350 km fibre link`
   正文中以宏 `\uTotalShort`（=2.1，由预算合成值导出）与 `\fibreKm`（=1 350）呈现，仍随管线生成。
2. **结构**：原 Results §2.3（与其他测量的对照）并入独立章节 **Discussion and outlook**；
   该章覆盖——与 NIST/欧洲网络对照及秒定义贡献、地球引力势变化的影响、网络化运行的工程属性、
   限制与外部待确认项、未来拓展（含 VLBI 洲际路径）。
3. **移除**：原 Results §2.4（段 9 敏感性检查）整体删除；Methods/Results/Appendix 不再解释其
   不采用原因，仅保留"记录 17 段、分析 16 段"的事实陈述。
   （段 9 的完整技术记录仍保留在审计层：`results/audit-v1/`、`docs/audit/`。）
4. **工具（应"轻量化"要求）**：新增
   `tools/check.sh`（一键：数字管线校验 + 编译 + 未定义引用检查）、
   `tools/sync_overleaf.sh`（同步 Overleaf 包 + 重建 zip）与
   `tools/publish.sh "commit message"`（校验 + 同步 + 提交 + 推送，一条命令）。

## 1. 正文篇幅 vs Nature Article 一般篇幅

**Nature 格式指南锚点**（physical sciences）：

- 印版一般**不超过 6 页**（最终由编辑裁量）；
- 典型 **6 页** Article ≈ 正文 **2,500 词**（摘要段 + 正文）+ 4 个紧凑图表项；
- 典型 **8 页** ≈ **4,300 词** + 5–6 个图表项；
- 词数不含题名、作者、致谢、参考文献；**Methods** 为在线部分，另计（指引 ≤3,000 词）。

**本稿实测**（tex 源统计；剥离 `\cite`、公式与浮动体环境）：

| 组成 | 词数 | 对照 |
|---|---:|---|
| Summary（摘要段，无引用） | 153 | 指引 ≤200 ✓ |
| 1 Introduction | 409 | |
| 2 Results | 318 | |
| 3 Discussion and outlook | 630 | |
| **正文小计（I+R+D）** | **1,357** | |
| **正文合计（摘要段 + 正文）** | **1,510** | 6 页锚点 2,500 → **−990（−40%）**；8 页锚点 4,300 → −2,790 |
| 主文图表项 | 3 图 + 1 表 = 4 | 6 页档标配 4 ✓ |
| Methods | 689 | 指引 ≤3,000 ✓；不计入正文页数 |
| 附录 A–E | 538 | 在线/补充材料 |

**结论**：当前正文 ≈ 典型 6 页 Article 字数的 **60%**；按 4 个紧凑图表项估计，印版约 **4–5 页**。
补 ≈700–1,000 词可达典型 6 页体量（候选位置：Results 的对照与稳健性细节；Discussion 的
应用/展望；Introduction 的动机细节），或维持紧凑短稿。

## 2. 其他投稿格式核对（顺带记录）

| 项 | 现状 | Nature 指引 | 判定 |
|---|---|---|---|
| 题名 | 约 100 字符（按指定题名） | ≤75 字符（两行） | ✗ 仍超约 25，投稿前需再精简 |
| 引文数 | 正文 20 / 全文 22（bib 33 条） | 正文 ≤50 | ✓ |
| 摘要段 | 153 词、无引用、无公式 | ≤200 | ✓ |
| Methods 位置 | 引文之后、无编号 | 随主文文件、引文之后 | ✓ |
| 作者 | `xxxxx` 占位 | — | 待协作组提供 |

## 3. 复算口径

词数：Python 正则从 `paper/rev2/sections/*.tex` 统计——先剥离注释、`\cite*{...}`、
`$...$` / `\[...\]`、figure / table / equation 环境与命令参数，再计英文单词。
摘要段与正文的界定按 Nature 口径（题名、作者、致谢、参考文献不计入）。

## 4. 相关位置

- 稿件：`paper/rev2/main.pdf` / `paper/rev2/main.tex`
- 一键校验：`paper/rev2/tools/check.sh`；Overleaf 包同步：`paper/rev2/tools/sync_overleaf.sh`；
  一键发布：`paper/rev2/tools/publish.sh "commit message"`（校验+同步+提交+推送）
- Overleaf 包：`paper/overleaf-rev2/`、`paper/overleaf-rev2-upload.zip`
- 根 README：「篇幅与 Nature Article 对照（paper/rev2）」一节
