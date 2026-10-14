# 稿件对抗性评审意见（2026-10-14；Nature 目标）

> 五视角评审（EIC / 方法 / 领域 / 交叉学科 / 魔鬼代言人）的合成结论。
> 已实施修改的标注 [已修]；其余供作者决策。

## 一、已识别并修复的问题

1. **[已修] 总不确定度呈现不一致（方法评审，MAJOR）**
   Table 2 总行显示 2.34×10⁻¹⁸，但正文/摘要/结论用 2.3×10⁻¹⁸（一位有效数字）。
   审稿人会质疑数字管线。已将正文统一为 `\uTotalE`=2.34（两位），标题保留 2.3
   简洁形式。

2. **[已修] 图2 caption 术语不一致（领域评审，MINOR）**
   "(b) Per-campaign ratio measurements" 与正文 "one data point per segment"
   的 segment/campaign 混用。已统一为 "Per-segment ratio deviations"。

3. **[已修] 第二潮汐模型的数值不可见（魔鬼代言人，MINOR）**
   §2.3 只说 "larger of the two model shifts, 0.85" 而未给出另一模型的 0.21，
   读者无法核对。已在 §2.3 显式指向 Methods Table 4（两模型并列诊断表）。

## 二、供作者决策的意见（未自动修改）

4. **"first intercity" 论断的防御性（魔鬼代言人，MAJOR）**
   论证依据：欧洲网络的最佳比值 7.7×10⁻¹⁸ 是"总不确定度"口径，本文 2.3×10⁻¹⁸
   也是总不确定度，口径可比；但审稿人可能追问：(a) 欧洲网络论文是否也声称
   "不同城市"？（其站点也在不同机构/城市）；(b) "first" 的时间断言
   （as of October 2026）在投稿后数月需要更新。
   **建议**：改为 "the first intercity, cross-species measurement to our
   knowledge"（已有）并在 claim date 保持精确；或加一句与欧洲网络口径的
   直接对比（"vs 7.7×10⁻¹⁸ in the European network"）——后者已被删除以去重，
   如审稿人挑战可恢复。

5. **摘要的双重让步句（EIC，MINOR）**
   "However, although several optical clocks have reported self-evaluated
   uncertainties below 2×10⁻¹⁸, validation of these self-assessed values
   through frequency-ratio comparisons has not yet been achieved."
   双重让步略显拖沓。建议简化：删 "although several ... 2×10⁻¹⁸" 子句，
   直接 "validation ... has not yet been achieved"（首句已给 5×10⁻¹⁸ 阈值语境）。
   注意：删后摘要首句的 "self-evaluated uncertainties below 2×10⁻¹⁸" 信息会丢，
   可考虑保留（信息密度优先）。**倾向保留**。

6. **Methods 潮汐节与 §2.3 的剩余重复（方法评审，MINOR）**
   §2.3 已精简为论证主线，Methods 承接细节；但 Methods 潮汐节文字仍较长
   （模板构造 + 两模型描述 + 固体潮分解 + Table 4）。若 Methods 字数敏感，
   可把"固体潮分解"句并入 Table 4 注。**当前可接受**。

7. **标题长度（EIC，已知项）**
   标题 99 字符，超 Nature 75 字符指引（REVIEW_NOTES 已记录）。投稿前需
   精简。候选："Intercity Yb/Sr optical clock comparison at 2.3×10⁻¹⁸"
   （约 55 字符）。

8. **摘要与 Conclusion 的 "first" 重复（领域评审，MINOR）**
   摘要、Discussion、Conclusion 三处都出现 "first intercity"。结论处可简化为
   "the first intercity ratio meeting the roadmap requirement" 已足够；
   三处保留不算错误，但 Conclusion 可进一步压缩。

## 三、评审总评

- **新颖性/意义**：跨城、跨种、达 2.34×10⁻¹⁸ 的比值测量，首次满足路线图
  要求，对秒重定义有直接贡献——Nature 级意义成立。
- **方法严谨性**：冻结审计层 + 数字宏管线 + 双潮汐模型交叉验证 + 随机效应
  统计，透明度与可复现性高于同类论文平均水平。
- **主要风险**："first" 论断的时间窗口与口径可比性；标题长度。
- **建议决定**：Minor Revision（投稿前处理 4、7 即可）。

## 四、验证记录

- check.sh：97 宏 + 14 页 PDF，无 undefined
- pytest：231 passed
- 数字一致性：2.34 出现 7 处（表+正文+摘要），(28) 括号 2 处，0.85 潮汐项 5 处
