# AGENTS.md — 先读我：任务路由与阅读纪律

> 本库文档较多，但**每次任务只需要其中一小片**。先查下表定位，再只读相关文件；
> 不要通读整库、不要全库搜索。深度说明在各专项文档中，本文件只做路由。

## 阅读纪律

1. 先按下表找「任务 → 只读什么」，再打开文件；需要精确行时先 grep 定位再局部读。
2. 论文数字不在正文手改——全部由 `paper/rev2/tools/build_numbers.py` 生成宏（`generated/numbers.tex`）。
3. 权威数值只认 `results/audit-v1/verified/manifest.json` 及其派生的
   `ANALYSIS_AUDIT.md`；其它产物仅作参考。
4. 用户上传素材**本地保留、不入库**：`docs/raw/`、`paper/*.docx`、
   `paper/ref/Pizzocaro*.pdf`、`paper/ref/Vishwakarma*.pdf`；
   `results/comp_shanghai-wuhan-beijintime.csv` 为新增潮汐输入（已登记于
   `clock/PROFESSIONAL_TIDAL_DATA.md` §7，后续分析用，保持未跟踪）。
5. 历史/冻结材料只读：`paper/main.tex`、`paper/main_seg9_excluded.tex`、`archive/`、
   `results/audit-v1/`、`docs/audit/` 内的记录。

## 任务路由（读什么 / 改哪里 / 怎么验证）

| 任务 | 只读这些 | 改动位置 | 验证 |
|---|---|---|---|
| 改论文正文（abstract/intro/results/discussion/methods/appendix） | `paper/rev2/sections/<目标>.tex` + `paper/rev2/generated/numbers.tex`（查宏名） | 同左 | `paper/rev2/tools/check.sh` |
| 改论文数值/预算/对照 | `paper/rev2/tools/build_numbers.py`（CURATED 段）+ `results/audit-v1/verified/manifest.json`（只读） | `build_numbers.py` → 重生成 | `check.sh`（`--check` 逐字节比对 4 产物） |
| 改图 | `paper/rev2/tools/make_figures.py` + `paper/rev2/generated/numbers.json` | 同左 | `check.sh` |
| 同步 Overleaf 包 | — | — | `paper/rev2/tools/sync_overleaf.sh` |
| 发布（校验+同步+提交+推送） | — | — | `paper/rev2/tools/publish.sh "msg"` |
| 题名/摘要等格式记录 | `paper/rev2/REVIEW_NOTES.md` §0 | 同左 | 随 publish |
| 分析管线（重跑/扩展） | `docs/WORKFLOW.md` | `clock/`、`clock_ratio/` | `uv run pytest -q`；audit：`uv run python run_all.py --mode audit --output-dir results/audit-v1` |
| 查权威结果 | `results/audit-v1/verified/manifest.json`、`.../ANALYSIS_AUDIT.md` | 只读 | `uv run python -m clock_ratio.verify_result_manifest results/audit-v1/verified/manifest.json` |
| 阶段一历史/裁定/外部待确认 | `docs/audit/PHASE1_SUMMARY.md` | 只读 | — |
| 符号/方法/参数 | `docs/NOTATION.md`、`docs/METHODOLOGY.md`、`clock/PARAMS.md` | 按需 | — |
| 潮汐数据（含新增输入登记） | `clock/PROFESSIONAL_TIDAL_DATA.md`（§7） | 按需 | — |

## 一键命令（改论文的轻循环）

```bash
cd paper/rev2
./tools/check.sh                      # 数字管线校验 + 编译 + 未定义引用检查
./tools/sync_overleaf.sh              # 刷新 Overleaf 包与 zip
./tools/publish.sh "commit message"   # 以上全部 + git 提交 + push origin main
```

## 目录地图（一句话）

| 路径 | 一句话 |
|---|---|
| `paper/rev2/` | **当前论文候选稿**（16 段口径；数字宏管线；`main.pdf` 已入库） |
| `paper/main.tex` 等 | 历史稿（潮汐检出叙事），冻结只读 |
| `paper/overleaf-rev2/` + zip | rev2 的 Overleaf 上传包（由 `sync_overleaf.sh` 同步） |
| `results/audit-v1/verified/` | 阶段一权威结果层（manifest 为唯一真源） |
| `docs/audit/PHASE1_SUMMARY.md` | 阶段一结论/裁定/外部输入总入口 |
| `clock/`、`clock_ratio/` | 分析实现（运行说明见 `docs/WORKFLOW.md`） |
| `docs/` | 符号/方法/流程/审计等专项文档（按需读，勿通读） |
| `results/comp_shanghai-wuhan-beijintime.csv` | 新增潮汐输入（仅登记，后续分析用） |
