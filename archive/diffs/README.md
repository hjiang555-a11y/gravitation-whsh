# 修订对比（latexdiff）

本目录存放由 [latexdiff](https://github.com/ftilmann/latexdiff)（v1.4.0）生成的**带标记修订对比**，
供合作者/审稿人快速查看改动。`.tex` 为可编译源（红删蓝增），`.pdf` 为渲染结果。

| 文件 | 对比内容 |
|---|---|
| `main_rev_latest.{tex,pdf}` | **17 段主稿**：上一提交（`781977e` 之前）→ 当前工作区（含 siunitx `\qty` 重排、摘要 `(24)→(23)` 对齐）|
| `seg9_rev_latest.{tex,pdf}` | **16 段（剔9组）变体**：上一提交 → 当前工作区 |
| `main_vs_seg9.{tex,pdf}` | **跨变体对比**：17 段主稿 `main.tex` ↔ 16 段变体 `main_seg9_excluded.tex`（展示剔段9后的全部数值/措辞差异）|

## 重新生成

```bash
# 需要 latexdiff（CTAN 的 perl 脚本，无需安装到系统）
latexdiff <旧>.tex <新>.tex > diff.tex
pdflatex diff.tex && bibtex diff && pdflatex diff.tex && pdflatex diff.tex
```

> 注：diff 的 `.tex` 引用 `refs.bib` 与 `figs/`，编译时需与本目录的同级 `paper/` 一致，或把这两者复制到编译目录。
