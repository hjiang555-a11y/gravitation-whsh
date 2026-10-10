# paper/rev2 候选稿审阅：篇幅与投稿格式对照

**日期**：2026-10-09（更新，含本轮审阅变更） · **对象**：`paper/rev2/`（16 段口径重建候选稿；`main.pdf` 12 页含附录）

## 0. 本轮（2026-10-09）审阅变更（已实施）

1. **题名**：按指定改为 `An intercity Sr/Yb optical clock comparison at the 2.1×10⁻¹⁸
   uncertainty over a 1 350 km fiber link`；以宏 `\uTotalShort`（=2.1，由预算合成值导出）
   与 `\fibreKm`（=1 350）呈现，仍随管线生成。
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
5. **摘要段**（按指定文本替换，2026-10-09）：改为指定摘要；数字仍全部由宏管线呈现
   （含新增 `selfEvalBound`=2×10⁻¹⁸ 宏，来源见 `generated/numbers_manifest.json`）；
   PDF 渲染已逐句核对；摘要词数 153 → 177 → 185（仍 ≤200）。
6. **作者修订合并 + 参考文献补充（2026-10-09 第二轮）**：合并作者 zip
   （`overleaf_rev2_upload__hj.zip`）的 title/abstract/introduction；补 4 条参考文献
   （`heavner2014nistf2`、`weyers2018ptbcsf`、`shen2021satellite`、`caldwell2023geo`）、
   作者已加的 `vishwakarma2026interspeciesclockcomparison5` 保留；新增宏
   `refPtbTransportableU`（4.3×10⁻¹⁸）并宏化 abstract/intro 手写数字（2/7.7/3.2/4.3×10⁻¹⁸）；
   全文拼写统一为美式（intercity / fiber / stabilized / analyzed / leveling / center）。
7. **首句引文补强（2026-10-09 第三轮，按指示）**：Introduction 首句扩为——
   ytterbium（NIST/JILA `mcgrew2018geodesy`、武汉 `zhu2026yb`）与
   strontium（JILA `aeppli2024sr`、USTC `jia2026sr`、NTSC `lu2025ntsc`）晶格钟，
   Al$^+$（NIST `marshall2025alplus`、PTB `dawel2026ptbalplus`）、
   Lu$^+$（`arnold2026lu`，隶属 **NUS 新加坡量子技术中心**）、
   Ca$^+$（`zhang2026ca`）离子钟；离子 ≥2、原子 ≥2，
   全部自评估系统不确定度**严格 <2×10⁻¹⁸**。核查结论：**PTB 可用**（Al⁺ 1.6×10⁻¹⁸）；
   **NPL 暂不引**（已发表最佳 Yb⁺(E3) 2.2×10⁻¹⁸ > 2×10⁻¹⁸，Tofful 2024）；
   **NIST Al⁺ 已更新**为最新 5.5×10⁻¹⁹（Marshall et al., PRL 135, 033201 (2025)，
   取代 2019 年 9.4×10⁻¹⁹）。bib 38 → 42 条。
   （NTSC SrII 精确值为 1.96×10⁻¹⁸，其标题取整为"2×10⁻¹⁸"；按精确值仍严格低于阈值。）

8. **作者第二版合并 + 新 Overleaf 包（2026-10-09 第四轮，按指示）**：以作者第二版 zip 为基础
   ——题名改 `... Yb/Sr ...`、摘要末句 "optical clocks"；Introduction 逻辑梳理与表达润色
   （体系现状/网络验证动机/已实现链路与战役/星基前景 → 秒定义 I.2.b 要求与当前差距 →
   应用动机与"本地两次验证" → 本文工作与结果）；"used as sensors for dark matter" 句补引
   BACON-2021 比值测量 Nature 论文（`beloy2021bacon`，与 `derevianko2014topological`、
   `wcislo2018global` 并引）。生成新包 `paper/overleaf-rev2-v2/` +
   `overleaf-rev2-v2-upload.zip`；**原包 `paper/overleaf-rev2/` 保持不动**
   （`sync_overleaf.sh` 已指向新包）。正文合计 1,564 词（62.6%）。

9. **Results §2.1 重写与二次修订（2026-10-10 第五轮，按指示）**：结合实验情况扼要介绍网络组成，
   不展开链路技术细节——两台晶格钟（武汉 Yb `zhu2026yb` 1.3×10⁻¹⁸、上海 Sr `jia2026sr`
   0.92×10⁻¹⁸，均为宏）；700 km 站距、1350 km 单程/2700 km 环回相稳光纤链路，载波为
   1550.12 nm 电信信道、由上海发往武汉；链路为参考文献 [15]（`chen2026dissemination`）的延长，
   同款级联光纤噪声消除技术（一句带过）。频率控制与比对方法：两端光梳自参考并锁相到本钟信号，
   其余频率由两钟跃迁经固定二倍关系导出（698/1397、578/1156 nm），全系统独立频率源只有两钟；
   记录量为环外拍频（逐秒采样、`F_1550` 归一化），光纤环回全程环外监测；附录指向改为
   'see Methods'。**推迟（暂不做）**：Methods §4.1 与附录 A 合并、统一频率关系与计算
   （含两端重复频率不同、为非准确分频值的说明；具体值见本地笔记）。
   Results 318 → 445 词；正文合计 1,691 词（67.6%）。

## 1. 正文篇幅 vs Nature Article 一般篇幅

**Nature 格式指南锚点**（physical sciences）：

- 印版一般**不超过 6 页**（最终由编辑裁量）；
- 典型 **6 页** Article ≈ 正文 **2,500 词**（摘要段 + 正文）+ 4 个紧凑图表项；
- 典型 **8 页** ≈ **4,300 词** + 5–6 个图表项；
- 词数不含题名、作者、致谢、参考文献；**Methods** 为在线部分，另计（指引 ≤3,000 词）。

**本稿实测**（tex 源统计；剥离 `\cite`、公式与浮动体环境）：

| 组成 | 词数 | 对照 |
|---|---:|---|
| Summary（摘要段，无引用） | 185 | 指引 ≤200 ✓ |
| 1 Introduction | 431 | |
| 2 Results | 445 | |
| 3 Discussion and outlook | 630 | |
| **正文小计（I+R+D）** | **1,506** | |
| **正文合计（摘要段 + 正文）** | **1,691** | 6 页锚点 2,500 → **−809（−32.4%）**；8 页锚点 4,300 → −2,609 |
| 主文图表项 | 3 图 + 1 表 = 4 | 6 页档标配 4 ✓ |
| Methods | 689 | 指引 ≤3,000 ✓；不计入正文页数 |
| 附录 A–E | 539 | 在线/补充材料 |

**结论**：当前正文 ≈ 典型 6 页 Article 字数的 **67.6%**；按 4 个紧凑图表项估计，印版约 **5 页**。
补 ≈700–1,000 词可达典型 6 页体量（候选位置：Results 的对照与稳健性细节；Discussion 的
应用/展望；Introduction 的动机细节），或维持紧凑短稿。

## 2. 其他投稿格式核对（顺带记录）

| 项 | 现状 | Nature 指引 | 判定 |
|---|---|---|---|
| 题名 | 99 字符（intercity 题名） | ≤75 字符（两行） | ✗ 仍超约 24，投稿前需再精简 |
| 引文数 | 全文 32（bib 42 条） | 正文 ≤50 | ✓ |
| 摘要段 | 185 词、无引用、无公式 | ≤200 | ✓ |
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
- Overleaf 包（当前）：`paper/overleaf-rev2-v2/`、`paper/overleaf-rev2-v2-upload.zip`；
  初版包 `paper/overleaf-rev2/` 保留为冻结快照
- 根 README：「篇幅与 Nature Article 对照（paper/rev2）」一节
