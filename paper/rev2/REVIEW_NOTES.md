# paper/rev2 候选稿审阅：篇幅与投稿格式对照

**日期**：2026-10-11（含历轮审阅变更） · **对象**：`paper/rev2/`（16 段口径重建候选稿；`main.pdf` 12 页含附录）

## 0. 历轮审阅变更（已实施）

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
   `overleaf-rev2-v2-upload.zip`；**原包已归档至 `archive/overleaf-rev2/`**
   （`sync_overleaf.sh` 已指向新包）。正文合计 1,564 词（62.6%）。

9. **Results §2.1 重写与二次修订（2026-10-10 第五轮，按指示）**：结合实验情况扼要介绍网络组成，
   不展开链路技术细节——两台晶格钟（武汉 Yb `zhu2026yb` 1.3×10⁻¹⁸、上海 Sr `jia2026sr`
   0.92×10⁻¹⁸，均为宏）；700 km 站距、1350 km 单程/2700 km 环回相稳光纤链路
   （**商用光纤网络、非独占使用**），载波为 ITU-T 100 GHz DWDM C34 信道
   （1550.12 nm / 193.4 THz）、由上海发往武汉；链路为
   参考文献 [15]（`chen2026dissemination`）的延长，同款级联光纤噪声消除技术（一句带过）。
   频率控制与比对方法：两端光梳自参考并锁相到本钟信号，其余频率由两钟跃迁经固定二倍关系
   导出（698/1397、578/1156 nm），全系统独立频率源只有两钟；记录量为环外拍频（逐秒采样、
   `F_1550` 归一化），光纤环回全程环外监测；附录指向改为 'see Methods'。
   **推迟（暂不做）**：Methods §4.1 与附录 A 合并、统一频率关系与计算
   （含两端重复频率不同、为非准确分频值的说明；具体值见本地笔记）。
   Results 318 → 461 词；正文合计 1,707 词（68.3%）。

10. **段落挪移（2026-10-10 第六轮，按指示）**：§2.1 第三段（战役数据记录：\nDays 天、\nStages
    阶段、1 008 912 s、17 段；分析用 16 段/986 416 s）移至 §2.2 Clock-ratio determination
    开头（figure 之前）——从数据记录开始叙述更符合逻辑。字数不变（同文件内挪移）。
    **待办（暂缓）**：② 比值测量技术点需讲清楚。

11. **F_1550 表述更正 + 水准测量句（2026-10-10 第七轮，按指示）**：§2.1 第二段——拍频
    归一化改为 "normalizing to the carrier frequency $F_{1550}$ (1550.12 nm)"（F_1550 即
    1550.12 nm 载波本身，不再是单独量）；按指示补入水准测量句 "The geopotential difference …
    was measured by spirit leveling to be ΔW = 280.042 ± 0.085 m² s⁻² (see Methods)"（值/不
    确定度走宏 `\dWVal`/`\dWUnc`）。Methods 未新增占位——"Leveling determination of the
    geopotential difference" 小节本已存在。Results 461 → 482 词；正文合计 1,728 词（69.1%）。

12. **§2.2 Clock-ratio determination 重写（2026-10-10 第八轮，按指示）**：参考 refs [17]
    （Pizzocaro 欧洲网络）与 [30]（Aeppli NIST–JILA）的写法——以**贝叶斯随机效应**为
    主要结果（超散布参数边缘化）；同时给出其他统计结果（χ²_red = 4.017、15 dof、p = 2.3×10⁻⁷、
    Birge ratio = 2.004、模型受限段 5/16 列出组号、Mandel–Paule 交叉核对 \RmpHead）；
    **不再报告 WLS 结果**（正文无 WLS 字样，方法/附录保留语境）。新增引用：
    `birge1932errors`（Phys. Rev. 40, 207 (1932)）、`mandel1970interlaboratory`
    （Anal. Chem. 42, 1194 (1970)），bib 42 → 44 条。Results 482 → 472 词；
    正文合计 1,718 词（68.7%）。

13. **统计模型内联 + §2.2 定稿（2026-10-10 第九轮，按指示）**：按"Method 仅指
    Clock-ratio determination and statistical model 小节、不拓展范围；暂不考虑附录"执行。
    Methods 该小节：删除旧"四种估计量（含 WLS）+ 附录 C 指向"段，改为自包含统计模型段——
    随机效应观测模型 $R_i \sim \mathcal{N}(\mu, u_i^2 + \xi^2)$（引 Birge 1932 /
    Mandel–Paule 1970）、贝叶斯随机效应为**主结果**（$\mu$ 与 $\log\xi$ 平坦先验、
    $\log\xi$ 网格数值边缘化、后验均值 ± 后验标准差）、Mandel–Paule 交叉核对
    （$\chi^2_{\rm red}(\xi) = 1$）。Results §2.2 统计句定稿："two random-effect
    estimators agree…"，补 $u_{\rm MP}$=0.788、$\xi_{\rm MP}$=2.50、$\xi_{\rm Bayes}$=2.83
    （×10⁻¹⁸），统计不确定度改报到 3 位（`\uStatE`=0.885）。两处美式拼写统一
    （marginalized）。附录 A–E 当时未动（按指示；其中 §C 仍有一处英式拼写
    "marginalised"，待附录定位确定后再统一）。主文无 WLS 字样（附录保留方法语境）。
    词数：Results 486、Methods 687、正文合计 1,732 词（69.3%）；全文引用 34 条（bib 44 条）。

14. **作者第三版合并 + 精简（2026-10-11 第十轮）**：合并 `overleaf_rev2_v2_upload__hj.zip`
    （作者删除非重要信息）——abstract 删"数据量"句（"Based on …hours…days"，改为 "The Yb/Sr
    frequency ratio is determined as …"）；Results §2.1 引文位置调整（移至 IAPMST~/USTC~
    之后）；§2.2 战役句压缩（58 天 / 274 有效小时 / 16 段，不再区分"记录 17 段 / 分析
    16 段"）；Methods 删 "Observation campaign and per-segment data" 小节、
    "Leveling determination" 前移至首节、"see below"→"see above"。融合时另去除摘要句中
    多余 `~`（`as ~\Rheadline`）。宏 `\nStages`/`\nSegAll`/`\nSamples`/`\nSamplesAll`/
    `\nHoursAll`/`\nSegNine` 随文字删除变为未引用（宏超集允许，管线仍全量生成）。
    词数：摘要 174、Results 474、Methods 612、正文合计 1,709（68.4%）。

15. **§2.3 时变红移不确定性 + Discussion 演进/潮汐/展望 + Conclusion（2026-10-12 第十一轮，
    按指示）**：
    - §2.3 新增一段：时变引力红移的来源（固体潮、海潮、大气/水文/非潮汐海洋负荷，
      引 `agnew2015tides`、`voigt2016timevariable`、`denker2018geodetic`）；潮汐模板修正
      后 χ²_red 从 \tidalChiRaw 升到 \tidalChiTheory/\tidalChiEmp（修正反而恶化拟合，
      即模型与数据不符），故按**误差项**处理、不修正中心值；误差项量级取模板修正引发的
      中心位移 \tidalShiftEmpE×10⁻¹⁸（≈0.53，圆整为 \uTidalE=0.5）。2.2 以前内容未动。
    - Methods「Uncertainty budget」与附录「Budget details」/「统计模型」同步补敏感性
      数字与出处（冻结 seg9 JSON：synthesis.goodness_of_fit / methods.R_bayes）。
    - Discussion 新增 (a) 比值结果演进段：Akamatsu 2014 首次 Yb/Sr（`akamatsu2014ybsr`）
      → Nemitz 2016 5×10⁻¹⁷（`nemitz2016ybsr`）→ BACON ≤8×10⁻¹⁸（`beloy2021bacon`）→
      欧洲网络 7.7×10⁻¹⁸ → 同园区 3.2×10⁻¹⁸ → 本文 2.1×10⁻¹⁸，体现比较的重要性与趋同；
      (b) 简单潮汐 fit 说明段（段均值对段均潮汐势拟合斜率依赖窗口；模板修正残留更大；
      10⁻¹⁸ 级修正超出本论文范围，留待后续）；(c) outlook 段改写为光纤+卫星/自由空间
      混合全球光钟网络展望。
    - 新增 **Conclusion** 节（main.tex `\section{Conclusion}` + `sections/conclusion.tex`）。
    - 新宏 6 个：`tidalChiRaw/tidalChiTheory/tidalChiEmp/tidalShiftEmpE`（冻结 seg9 JSON）、
      `baconE`、`nemitzU`（文献，均经 Crossref 验证）；bib 44 → 48 条。
16. **整体评估与结构优化（2026-10-12 第十二轮，按指示；Nature 评审视角）**：
    - **Methods 框架补齐、废除附录 A–E**：附录五节（频率链与比值反演 / 数据处理与段定义 /
      统计合并模型 / 水准归算 / 预算细节）全部并入 Methods，删除 `appendix.tex` 与
      main.tex 的 `\appendix`。Methods 现按逻辑顺序组织：① 水准归算 → ② 实验装置与频率
      传递（含频率链公式与 δ_g 反演）→ ③ 数据处理与段定义（`tab:segments` 迁入）→
      ④ 钟比值与统计模型（WLS/Birge/Mandel–Paule/贝叶斯自包含）→ ⑤ 不确定度预算（含潮汐
      敏感性）。消除了统计模型三处重复（原 Results/Methods/附录各一遍）。
    - **Discussion 与 Conclusion 去重**：Discussion 保留论证版（对照/演进/引力势与潮汐
      处理/运行属性/局限/展望）；Conclusion 收敛为简报式总结（首次跨城达标 + 三者趋同 +
      瓶颈转移 + 网络愿景），不再复述全文数字。
    - **逻辑修复**：删除 Discussion 中"段均值对潮汐势拟合斜率依赖拟合窗口"句——该表述是
      17 段检出叙事残留，16 段口径无对应数字支持，且与"模板修正恶化拟合"的敏感性证据
      重复；现仅保留后者（有 χ²_red 数据支撑）。
    - **bib 清理**：移除 9 条孤儿条目；bib 48 → 39 条 = 正文引用数，零孤儿。
    - 渲染：12 页（含 Methods），无 undefined 引用；正文（摘要+引言+结果+讨论+结论）
      ≈2,300 词。

17. **u_i 计算口径变更：取最后可算点，不外推（2026-10-13 第十三轮，按指示）**：
    - `clock_ratio/segment_uncertainty.py`：u_i 从「128 s≤τ≤T/4 log-log 拟合外推到 T」
      改为「取 tau_grid 最后一个可算 OADEV 点」`u_i = R_i·σ_y(τ_max)`；log-log 斜率
      保留为白频诊断（带外标记 lim. 但 u_i 照常报告）。TDD：3 个新测试先行失败
      （含 pytest.approx rel=0 陷阱——绝对容差 1e-12 使 2.7e-18 vs 8.6e-18 误判相等，
      改用精确 ==）。
    - **重跑 audit**：新 verified 运行 `ac725aaba8ec744b`（旧 `15725f5246e87af5` 保留）。
      16 段主结果：χ²_red 4.017 → **0.412**（p=0.98）、Birge 2.004 → 0.642、
      ξ_Bayes 2.83 → **0.14**×10⁻¹⁸、u_stat 0.885 → 1.139×10⁻¹⁸、
      u_total 2.118 → **2.236**×10⁻¹⁸、R_bayes 尾数 …720.4 → …720.1(22)。
      NIST 差 −2.44 → **−2.87**×10⁻¹⁸；欧洲网络差 +1.66 → **+2.13**×10⁻¹⁸。
      潮汐敏感性：raw χ² 0.41 → theory 0.57 / empirical 0.54（仍恶化）；
      tidalShiftEmpE 0.53 → 0.85（取整后 uTidalE=0.5 依据仍在）。
    - 论文正文更新：Results §2.2 改为「段间一致（χ²_red=0.41）」叙事；图2 图注改
      「last computable point」；Methods 统计段重写；Discussion 局限段同步。
    - docs/METHODOLOGY §2.2 记裁定（外推低估 ~30–40% 为历史记录）；§8/§10.1 同步。
    - 验证：pytest 231 passed（含数据套件）；manifest verify OK；check.sh OK
      （u_total 范围断言 2.0–2.3 仍通过）。

18. **图2 三子图表述对齐 Aeppli 2026 + 三估计量对照表（2026-10-13 第十四轮，按指示）**：
    - 图2（用户提供的 fig2_ratio，三子图：a 段级分数不稳定度+梳齿/光纤环外诊断、
      b/c 逐战役比值偏差）caption 改写为 Aeppli 2026 Fig. 2 风格——白频模型
      `σ_y(τ)=σ_0/sqrt(τ/s)`、统计不确定度取最后可算点、逐战役数据点表述。
    - §2.2 新增 **Table 1：三估计量对照**（WLS / Mandel–Paule / Bayesian random
      effect，21 位小数 Yb/Sr + u），Bayes 尾数 720.134 > WLS/MP 720.130 且
      u_Bayes=1.139×10⁻¹⁸ 最大，故以 Bayes 为宣称结果——正文同步给出理由
      （"carries the largest standard uncertainty"）。
    - 新宏 6 个（`RwlsHeadT/RmpHeadT/RbayesHeadT` 21 位分组版、
      `RwlsRawT/RmpRawT/RbayesRawT` siunitx S 列无分组版）。
    - **LaTeX 修复两处**：① 宏名不能以数字结尾（`\RwlsHead21` 被解析为
      `\RwlsHead`+`21`，报 already defined）→ 改字母后缀 T；
      ② T1 字体下 `\,`/`\thinspace` 在 tabular 内被吞（PDF 字形错排成 …720 121）
      → 表格改用 siunitx `S[table-format=1.21]` 列 + 无分组数字宏，由
      `group-digits=all` 渲染分组；正文行内数字宏改文本模式（免 \ensuremath）。
    - 验证：main.log 零 undefined；PDF 文本提取表格数字 …720 130/130/134 正确。

19. **括号不确定度改为贝叶斯统计不确定度（2026-10-13 第十五轮，按指示）**：
    `\RheadlineUnc` 原为总不确定度两位数字（2.24→22），改为贝叶斯统计不确定度
    `u_stat_bayes=1.139×10⁻¹⁸` 的两位有效数字（→11），与 headline 中心值的来源
    估计量一致；`numbers.json` payload `unc_digits` 同步。PDF 现为
    `1.207 507 039 343 337 720 1(11)`，正文旁注
    "statistical uncertainty of 1.139×10⁻¹⁸ and a total standard
    uncertainty of 2.2×10⁻¹⁸"（三位与括号两位均为同一量的舍入）。

20. **表述对齐 Pizzocaro 2026 + WLS 解释 + Methods 精简（2026-10-13 第十六轮，
    按指示）**：
    - 借鉴 Pizzocaro 2026（PRR 8, 033250）的 Birge/每日 bin 数据组合表述——
      §2.2 以 χ²_red、Birge ratio、p 值叙述段间一致性，再用随机效应模型合并；
    - WLS 在正文与表注中一句话解释（inverse-variance weights w_i=1/u_i²）；
    - Methods 统计段精简：只展开 Bayesian random-effect 主模型（先验、边缘化、
      40-decade log ξ 网格）；WLS、Birge、Mandel–Paule 仅引用文献与数值
      （birge1932errors / mandel1970interlaboratory），不再逐一推导；
    - 括号不确定度定位句改为 "the parenthesized uncertainty is the Bayesian
      statistical uncertainty"。

21. **统计量入表、正文更简练（2026-10-13 第十七轮，按指示）**：
    Table 1 增加 ξ（共同超额散布）列，WLS 行以 --- 占位；χ²_red、dof、p、
    Birge ratio 移入表注；正文 §2.2 不再逐项报这些统计量，仅以
    "as quantified by the combination statistics in Table 1" 一句概括，
    段 2/6/7/12/16 模型受限组的表述保留在正文。Methods 交叉核对句不变。

22. **§2.2 表述再精简（2026-10-13 第十八轮，按指示）**：
    - 删 "jump-point removal and endpoint screening"——实际数据无挑点
      （样本账本：1,009,200 样本仅 3 剔除 + 249 端点裁剪），Methods 的
      数据处理段同步删除 10 Hz 跳点与 1% 端点筛选细节，只保留"最长无跳段"；
    - 段 2/6/7/12/16 模型受限组号与斜率细节从正文删除，正文仅一句
      "(see Methods for the model-limited segments)"，细节在 Methods 与
      逐段表（tab:segments 的 lim. 标记）；
    - "The total standard uncertainty is 2.2×10⁻¹⁸" 句从 §2.2 末尾移入
      §2.3 首段（本就属于预算节）。

23. **§2.2 去括号 + §2.3 重写为完整预算叙述（2026-10-13 第十九轮，按指示）**：
    - §2.2 headline 公式去括号：`Yb/Sr = 1.207…7201`（无不确定度后缀），
      旁注只给统计不确定度 1.139×10⁻¹⁸；abstract 同步去括号。
    - §2.3 重写为四段预算叙述：① 总括（统计之外还有哪些系统贡献）；
      ② 逐项数值+来源（Sr 0.92×10⁻¹⁸ 引 jia2026sr、Yb 1.3×10⁻¹⁸ 引 zhu2026yb、
      静态势 u(ΔW)/c²=0.946×10⁻¹⁸ 换算说明、链路/梳齿各 0.1×10⁻¹⁸ 上限）；
      ③ 动态引力：潮汐模板使 χ²_red 0.41→0.57/0.54（模型与数据不符）→ 按
      不确定度处理，估计法=固定幅度模板重组合的 Bayesian 中心位移
      0.85×10⁻¹⁸（库内 `statistical_methods_tidal_seg9_excluded.json`
      empirical−raw 差值，tidal_e18 0.5→**0.85**，run_checks 总不确定度
      断言窗 2.0–2.3 → **2.2–2.5**）；④ 合成总不确定度 2.3×10⁻¹⁸ 并给出
      括号值 `Yb/Sr = 1.207…7201(28)`——括号为**绝对**不确定度：分数
      总不确定度 × 比值本身（2.34×10⁻¹⁸ × 1.2075 ≈ 2.8×10⁻¹⁸），
      `\RheadlineUnc` 由 `u_total×R` 生成（末两位小数单位 10⁻¹⁹）。

24. **链路/梳齿表述改频率参考设定 + ETideLoad4.5 介绍（2026-10-13 第二十轮，
    按指示）**：
    - "The fiber link and the frequency combs each contribute below 1×10⁻¹⁹,
      carried at 0.1×10⁻¹⁸ and 0.1×10⁻¹⁸" 改为 "The frequency conversion
      stages each contribute 0.1×10⁻¹⁸ and 0.1×10⁻¹⁸ from the
      frequency-reference settings of the frequency transfer"（来源于频率变换的
      频率参考设定）；
    - 动态引力段开头新增潮汐数据来源介绍：公开软件 ETideLoad4.5（章传银，
      地球潮汐/负荷效应与形变监测计算，实现 IERS Conventions (2010) 的
      地球物理模型与数值标准），新增 bib 两条：`zhang2026etideload`
      （官网 URL）、`iers2010conventions`（IERS Technical Note 36）。

25. **Discussion/Conclusion/Methods 整体改写（2026-10-13 第二十一轮，按指示；
    Nature 评审视角）**：
    - Discussion：删除与 §2.3 重复的潮汐处理段（原 ¶4 "The treatment of
      the time-varying term illustrates this point" 整段并入 ¶3 引力势段，
      保留一句 future-work 指向）；首段删去"瓶颈论证"尾部（与 ¶2 演进段
      重复的 campus 对比）；limitations 段"model-limited slope diagnostics"
      措辞微调。结构现为：对照与达标 → 比值演进/趋同 → 引力势与潮汐边界
      → 运行属性 → 局限 → 展望。
    - Conclusion：重写为简报式四句（结果/首次跨城达标+三者趋同/剩余局限/
      网络愿景），与 Discussion 首段及 abstract 去重。
    - Methods：不确定度预算节补齐**潮汐模板构造**（ETideLoad4.5 30 s
      固体潮+海潮负荷位移差 → g·Δh 势差 → h=F_1550·ΔW/c² 拍频模板），
      解决 §2.3 "supplied tide series" 无来源的问题；链路/梳齿条目表述
      同步为 frequency-conversion stages；删除已不用的
      `\uSubsystemBound` 引用（宏保留）。
    - Results §2.2：图2a 的正文描述段与 caption 重复，合并为一段
      （正文一句概括 + 指向 caption 细节）。
    - 词数：正文（摘要+引言+结果+讨论+结论）≈2,244；Methods ≈997。

26. **水准测量段重写（2026-10-13 第二十二轮，按指示；素材：用户上传
    "国内外水准测量标准.zip"）**：
    - Methods「Leveling determination」按最新实验记录重写：1113 km 一等水准
      联测、数字水准仪+条码因瓦标尺、视距 ≤30 m、6–8 km 分段往返观测现场检核、
      沿线重力同步观测；ΔW = 280.042 ± 0.085 m²/s²；M_Δ = 0.255 mm/km
      满足中（GB/T 12897-2006 表1：一等 M_Δ≤0.45）/美（FGCC 1984：一等 I 类
      0.5 mm/√km）/德（AdV FA-PN 2022：0.4 mm）/捷（ČÚZK 2015：I 级网
      m₀=0.40 mm/km）最高等级强制规定（四国限值已从上传 PDF 原文核实）。
    - 新增独立检核段：GNSS PPP 椭球高 + 局部水准垂向偏移 + EGM2008 大地水准面
      模型 → ΔW = 280.60 ± 2.558 m²/s²，两法在不确定度内一致，构成双重检核。
    - 新宏 `\dWAlt`/`\dWAltUnc`（280.60/2.558）；新 bib 4 条
      （gb12897/fgcc1984/advfapn2022/cuzk2015）。

27. **Conclusion 末两句正面化（2026-10-13 第二十三轮，按指示）**：
    末两句改为正面展望——"两站点构成工作节点对，**奠定网络拓展的基础**：
    未来通过更多光钟节点接入陆地光纤骨干、以卫星与自由空间链路跨洲互联，
    扩展为全球光钟网络；该网络将提供秒定义重定义所需的可验证计量基础设施，
    并支撑厘米级时变测地与分布式新物理搜寻"——与 Introduction 首段的
    "verifiable metrological infrastructure / future global optical clock
    network"及第三段（chronometric leveling、dark-matter sensing）呼应。

28. **Discussion 引力势/潮汐段逻辑链改写（2026-10-13 第二十四轮，按指示；
    仅改此段）**：潮汐影响在本精度已可观（"already appreciable"）→ 更大
    尺度（洲际/洲间基线）时变红移成为主导系统项之一（引 denker2018geodetic）
    → 网络因此成为"地球探测仪器"：大基线钟比对直接感知时变重力位，
    为潮汐与负荷模型提供独立检验与校准手段（呼应 chronometric geodesy）
    → 反过来，认识了潮汐后可以修正时变项而非保守计入，扩大光钟比对的
    精度适用范围（双向闭环）。末句保留未来工作指向。段落其余部分
    （首段对照、演进、运行属性、局限、展望）未动。

29. **Methods 小节合并与潮汐节独立（2026-10-13 第二十五轮，按指示）**：
    - 「Clock-ratio determination and statistical model」与「Uncertainty
      budget」内容高度重复（统计项、系统项两处都讲），合并为
      **「Clock-ratio determination, statistical model and uncertainty
      budget」**：逐段 u_i 与随机效应模型 → 交叉核对（WLS/M-P/Birge）→
      预算系统项（Sr/Yb/静态势/频率转换）。删除"excess scatter absorbs
      the tidal term"过渡句。
    - 潮汐内容独立成节 **「Tidal template and time-varying redshift」**：
      ① 模板量值确定（ETideLoad4.5 30 s 固体潮+海潮负荷位移差 →
      g·Δh → h=F_1550·ΔW/c²）；② fit 情况（固定理论幅度 A=−1 与历史幅度
      A=−0.54 两情景重组合，χ²_red 0.41→0.57/0.54 恶化 → 模型与数据不符 →
      不作修正、中心位移 0.85×10⁻¹⁸ 作为不确定度项；A=−0.54 的历史来源
      （同战役早期分析的去均值拍频波形幅度）在文中交代）。

30. **两潮汐模型不一致入论文（2026-10-13 第二十六轮，按指示）**：
    - §2.3 正文（简练）：ETideLoad4.5 模板修正使 χ²_red 0.41→0.57/0.54；
      第二个独立模型（DE421 星历+Love 数的固体潮 + FES2022 海潮负荷，
      90 s 北京时网格）同样恶化拟合（χ²_red=0.50）但中心位移**方向相反**
      （0.21×10⁻¹⁸ vs 0.85×10⁻¹⁸）；两独立模型符号分歧=模板不完备的直接
      证据 → 按不确定度处理，取**较大者** 0.85×10⁻¹⁸。
    - Methods（详细）：主模型（ETideLoad4.5、A=−1/−0.54 两情景、位移
      0.85）→ 交叉核对模型（DE421 固体潮 + FES2022 负荷、90 s 网格、
      历史幅度 χ²_red=0.50、反向位移 0.21）→ 处理逻辑（不修正、较大位移
      作不确定度项）→ 正交合成总不确定度 2.3×10⁻¹⁸。
    - 新宏 `\tidalShiftAltE`(0.21)/`\tidalChiAlt`(0.50)，从已提交的
      `clock_ratio/tidal_new_model_compare.json` 生成；`tidal_e18`
      provenance 改为"两模型位移的较大者"。总不确定度 2.3 与括号 (28)
      不变。

31. **全文结构与表述润色（2026-10-13 第二十七轮，按指示；Nature 顶级期刊
    目标，superpowers + paper-writing/scientific-writing 流程）**：
    - **摘要**：headline 值恢复括号 `1.207 507 039 343 337 720 1(28)`
      （`\Rheadline(\RheadlineUnc)`），总不确定度 2.3×10⁻¹⁸ 与 (28) 一致。
    - **渲染修复**：`\claimDate` 原为 \ensuremath 包裹（数学模式吞空格，
      PDF 显示 "October2026"）；build_numbers.py 的纯文本正则扩展为
      数字+thinspace+字母+空格，日期类宏改文本模式渲染，现为
      "as of October 2026"。
    - **拼写/语法**：§2.1 "An ytterbium" → "A ytterbium"。
    - **标点**：Discussion 展望段三重 em-dash 包裹句改为括号
      （Nature 每页 ≤2 个 em-dash 的约束下更稳妥）。
    - **全文一致性核对**：95 宏管线校验通过；(28) 出现 2 处（摘要+§2.3）
      且与总不确定度 2.3 一致；(11) 仅出现在参考文献页码（Anal. Chem.
      42(11)）；引文 45 条零缺失零孤儿；句子长度分布合理（均值 25–39 词，
      无 45+ 词长句）；无 AI 典型用语（delve/crucial/it is important 等）。

32. **固体潮相关性结论写入论文（2026-10-13 第二十八轮，按指示）**：
    - §2.3 正文加一句：段均值相关在全潮 r=+0.52，仅固体潮降至 r=+0.31
      （"locating the dominant coupling in the ocean-tide loading term"）；
    - Methods 潮汐节补固体潮分解句（全潮 r 0.52 → 固体潮 0.31，主导耦合
      在海潮负荷项）；
    - 新宏 `\tidalCorrTotal`(0.52)/`\tidalCorrSolid`(0.31)，从已提交的
      `clock_ratio/tidal_solid_only_compare.json` 生成（97 宏）。

33. **重力位差"外部保留项"歧义消除（2026-10-13 第二十九轮，按审稿提示）**：
    Discussion 局限段原有"an alternative value exists in the experiment
    records and is carried as an external item pending reconciliation"——
    与 Methods 的 GNSS+EGM2008 检核（280.60±2.558，与水准值一致）矛盾，
    且 280.049 m²/s² 为旧记录（历史遗留，仅存于冻结的 NATURE_FRAMEWORK.md）。
    修改：局限段改为"水准值已由独立 GNSS+大地水准面模型校准交叉核实、
    在不确定度内一致（Methods）"；"pending reconciliation"仅保留给潮汐
    序列来源与样本总数口径；      `delta_w` provenance 同步更新为双检核口径。

34. **模型受限段归因说明（2026-10-13 第三十轮，按审稿提示）**：
    审稿人问 5 个模型受限段是否有共性物理条件变化。调研（斜率分布、段时长、
    时段、战役、温度/锁分记录）：受限段与正常段无干净分离——斜率连续分布
    （−0.43 至 −0.79），受限段（−0.67~−0.79）只是越过 −0.65 界限的陡端；
    其 u_frac 反而更低（更接近白频）；无单一战役/天气/温度归因
    （温度与锁定频移 |r|<0.05）。结论：正常现象，不值得强调。
    Methods「Data processing」加一句："These five lie at the steep end of a
    continuous slope distribution, just beyond the acceptance bound, and show
    no common campaign, weather or laboratory condition that distinguishes
    them from the remaining segments."

35. **§2.2 交叉引用修正 + Discussion 三处内容补充（2026-10-13 第三十一轮，
    按指示）**：
    - §2.2 "see Methods for the model-limited segments" 指向不存在的小节，
      改为"The five segments flagged as model-limited in the per-segment
      table (Methods) are retained with their measured uncertainties."
    - Discussion 演进段补双向反馈句（比对互相验证 + 结果反馈到各实验室的
      方法评估与误差改进）；"three latest, independently obtained values"。
    - 新增钟能力对比段：最终不确定度与 NIST–JILA 相当且略小，虽然分布式
      系统带来链路/光梳/大地测量附加不确定度；补偿因素是 274 小时连续
      记录远长于典型单园区窗口，而更长的连续平均是缩小统计不确定度的
      直接途径；记录无跳点本身是链路跳变抑制与监测控制的技术成果
      （段内几乎无剔除样本）。
    - 运行属性段补钟复现性保障：比对前刻意关机重启测试重启复现性 +
      实验室环境严格调控，使"钟能回到同一频率"本身成为被测属性；
      三阶段段均值无系统偏移（−0.53/+0.29/−0.64×10⁻¹⁸）。
    - 正文 2,612 词（6 页锚点 +4%），结构未动。

37. **对抗性评审 + 修复（2026-10-14 第三十三轮，superpowers +
    academic-paper-reviewer 五视角）**：
    - [修] 总不确定度呈现统一为 2.34×10⁻¹⁸（正文/摘要/结论/引言改用
      `\uTotalE` 两位有效数字；标题保留 `\uTotalShort`=2.3 简洁形式），
      消除与 Table 2（2.34）的不一致；
    - [修] 图2 caption "(b) Per-campaign" → "Per-segment"（与正文
      "one data point per segment" 一致）；
    - [修] §2.3 显式指向 Methods Table 4（`\ref{tab:tidal}`），让第二
      模型位移 0.21×10⁻¹⁸ 可核对；
    - 评审意见全文见 `paper/rev2/REVIEW_ADVERSARIAL.md`（含供作者决策的
      4 项：first 论断防御性、摘要双重让步句、Methods 残余重复、标题长度）。

38. **标题与摘要精简（2026-10-14 第三十四轮，按指示）**：
    - 标题改为 "Intercity Yb/Sr optical clock comparison at
      2.3×10⁻¹⁸"（53 字符，≤75 达标；原 99 字符）。
    - 摘要 181 → 166 词：删双重让步句（"although several optical
      clocks have reported..."），"In this study" → "Here"，末句
      "Furthermore, together with..." 并入前句（"and together with
      the NIST–JILA result it satisfies..."）；`\selfEvalBound` 宏仍由
      Introduction 使用，非孤儿。
    - 评审意见 4 作者裁定不改（不确定度要求 <5×10⁻¹⁸，无争议）。

39. **外部评审意见采纳（2026-10-14 第三十五轮；PRL/Metrologia 路线）**：
    审稿意见全文（期刊建议 PRL + Metrologia、路线图判据口径、(28)vs(23)、
    表1/表3 对齐、水准系统误差、潮汐统计定义、Yb arXiv 状态等）见本轮对话记录。
    - **路线图判据修正（采纳，最关键）**：I.2.b 原文要求"至少五组非整数
      频率比、每组由不同机构测两次"（Dimarcq 2024 原文核实）。摘要改为
      "provides the second independent measurement of the Yb/Sr ratio by a
      different institute, as required by criterion I.2.b for this pair of
      transitions"（不再声称满足整个 I.2.b）；删 "confirming the validity
      of uncertainty assessments for both clocks"；"margin of statistical
      error" → "combined standard uncertainty"。Introduction 判据段补
      "at least five non-unit ratios ... each ratio at least twice"；
      末段 "completes the class" → "demonstrates ... the class"。
      Discussion 局限段同步：Yb/Sr 的两次独立测量已满足，I.2.b 还差
      另外四组比值。
    - **表3 补 R₁ 与段9说明**：caption 加 "with R1 = 1.207 507 039 343 337
      721 0"（新宏 `\RsegOne` 从 manifest segment_ratios[0] 生成）+ "segment
      9 is excluded (see text)"。
    - **核验审稿人第 2 条指控**：用冻结清单逐段 u_i 逆方差加权复算
      u_wls = 1.128×10⁻¹⁸，与表 1 完全一致；χ²=6.18 同时自洽。
      审稿人算的 0.93×10⁻¹⁸ 为口径错误，不修改。
    - 用户裁定：第 1 条 (28)→(23) 不改（归一化处理正确）；第 6 条
      光纤/梳齿细节放补充材料；其余（水准系统误差、潮汐均方根、频率链
      显式公式、重启数据、作者信息）留待投稿准备轮处理。

36. **PTB 多离子钟引用 + 已发表条目去 arXiv note（2026-10-13 第三十二轮，
    按指示）**：
    - Introduction 首句加多离子钟：Filzinger et al. 2026（PTB，
      arXiv:2603.23446，5.3×10⁻¹⁹，最多 10 个 Sr 离子）——Crossref 无正式
      发表记录，按预印本格式入库（`filzinger2026multiion`，与
      dawel2026ptbalplus 同款）。
    - 已正式发表条目移除 arXiv note 5 条：aeppli2026nist（PRL 137）、
      pizzocaro2026european（PRR 8）、beloy2021bacon（Nature 591）、
      mcgrew2018geodesy（Nature 564）、dimarcq2024roadmap（Metrologia 61）；
      zhu2026yb 仍为预印本，保留 note。bib 45 → 46 条，零缺失零孤儿。

40. **Nature 标准评估后修改（2026-10-15 第三十六轮，按指示）**：
    评估报告见本轮对话（五视角：EIC/方法/领域/交叉/魔鬼代言人；投稿目标
    Nature→PRL/Metrologia 缓降路径）。用户裁定：段 9 排除不解释（记录在库、
    参数与其他段差异大、疑似学生纪律错误无法回溯）、标题暂不改、"two orders"
    是行内共识说法不改、投稿准备项后续补、段 9 参数外部确认不可行（记录已过、
    异常即异常）。
    - [3] Conclusion I.2.b 表述：'confirming one of the required ratio
      measurements' → 'satisfying criterion I.2.b of the roadmap for this
      pair of transitions'（避免"五分之一"歧义）。
    - [2] Methods 统计段补贝叶斯 log ξ 网格收敛句（边缘质量 <1% 门）。
    - [6] Methods u_i 段 τ 网格写全：二次方秒 + 600/1200/3600/7200 s，
      上限为最长无间断 run 的 1/4。
    - [4] Introduction "only locally" 三实验：补 Vishwakarma 2026 PTB
      可搬运钟 Yb⁺/Sr（4.3×10⁻¹⁸）与 Takamoto 并列；bib 补
      `vishwakarma2026interspeciesclockcomparison5`（作者列表取自归档旧包）。
    - [8]+[新增] 段内相关性 16 段口径重算（用户要求两模型都算并对比）：
      新诊断脚本 `clock_ratio/tidal_within_segment_16seg.py`（复用
      batch_analysis 处理链：1200-s 三角窗、600-s 步长、去均值、不重叠
      推断窗；排除段 9）→ `clock_ratio/tidal_within_segment_16seg.json`。
      结果：两模型负相关段均为 12/16（二项 p=0.077）；带符号 Stouffer
      z = −3.75（旧 ETideLoad4.5）/ −4.50（新 DE421+FES2022）；
      精度加权幅度 A = −0.577±0.115（5.0σ）/ −0.873±0.152（5.8σ）——
      均显著但互不相同且都偏离预期 −1。17 段历史基线（12/17，A=−0.568）
      保持不变。
    - 新宏 3 个：`tidalNegSeg`(12)、`tidalAmpOldE`(−0.58)、`tidalAmpNewE`(−0.87)，
      来源 `tidal_within_segment_16seg.json`（102 宏）。
    - Discussion 引力势/潮汐段嵌入段内相关性阐述（两模型幅度差异+中心位移
      符号分歧→模板不完备）；"模型不完备可由更多网络比对数据修正/移除"作为
      展望句（不作为贡献）。Methods 潮汐节末段同步补同口径数字与展望。
    - 验证：pytest 227 passed, 4 skipped；数据套件 231 passed；check.sh
      102 宏 + 14 页 PDF 零 undefined；bib 44 条零缺失零孤儿。
    - 用户裁定不改：段 9 排除理由（库内有记录，无需论文解释）、标题、
      "two orders of magnitude"、投稿准备项（作者/基金/致谢/利益冲突）。

## 1. 正文篇幅 vs Nature Article 一般篇幅

**Nature 格式指南锚点**（physical sciences）：

- 印版一般**不超过 6 页**（最终由编辑裁量）；
- 典型 **6 页** Article ≈ 正文 **2,500 词**（摘要段 + 正文）+ 4 个紧凑图表项；
- 典型 **8 页** ≈ **4,300 词** + 5–6 个图表项；
- 词数不含题名、作者、致谢、参考文献；**Methods** 为在线部分，另计（指引 ≤3,000 词）。

**本稿实测**（tex 源统计；剥离 `\cite`、公式与浮动体环境）：

| 组成 | 词数 | 对照 |
|---|---:|---|
| Summary（摘要段，无引用） | 181 | 指引 ≤200 ✓ |
| 1 Introduction | 436 | |
| 2 Results | 695 | |
| 3 Discussion and outlook | 913 | |
| 4 Conclusion | 142 | |
| **正文小计（I+R+D+C）** | **2,186** | |
| **正文合计（摘要段 + 正文）** | **2,367** | 6 页锚点 2,500 → **−133（−5.3%）**；8 页锚点 4,300 → −1,933 |
| 主文图表项 | 3 图 + 1 表 = 4 | 6 页档标配 4 ✓ |
| Methods | 572 | 指引 ≤3,000 ✓；不计入正文页数 |

**结论**：当前正文 ≈ 典型 6 页 Article 字数的 **94.7%**；按 4 个紧凑图表项估计，印版约 **5–6 页**。

## 2. 其他投稿格式核对（顺带记录）

| 项 | 现状 | Nature 指引 | 判定 |
|---|---|---|---|
| 题名 | 99 字符（intercity 题名） | ≤75 字符（两行） | ✗ 仍超约 24，投稿前需再精简 |
| 引文数 | 全文 34（bib 44 条） | 正文 ≤50 | ✓ |
| 摘要段 | 174 词、无引用、无公式 | ≤200 | ✓ |
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
  初版包已归档至 `archive/overleaf-rev2/`（冻结快照）
- 根 README：「篇幅与 Nature Article 对照（paper/rev2）」一节
