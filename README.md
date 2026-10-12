# 武汉—上海远程光钟比对：潮汐引力红移分析

武汉（WUHN）与上海（SHAO）两地光钟（Yb/Sr）经 1550 nm 光纤链路远程比对，
分析潮汐引力红移效应（广义相对论 `Δf/f = ΔW/c²`），并重建逐段 Yb/Sr 钟比值。

> **任务路由（先读）**：本库文件较多，每次任务只需其中一小片；改论文、改数值、
> 跑分析各「只读什么 / 改哪里 / 如何验证」见 [AGENTS.md](AGENTS.md)。

## 主结果与口径

- **权威数值**只认 `results/audit-v1/verified/manifest.json` 及其派生的
  `ANALYSIS_AUDIT.md`（勿从本文件引用运行数值）。
- **临时（provisional）主结果**：16 段口径（第 9 段因参数待外部确认而隔离）；
  17 段与 leave-one-out 为敏感性结果。专业潮汐输入的物理模型来源仍待外部确认。
- **论文口径**（当前候选稿 `paper/rev2/`，16 段）：潮汐不再作为「检出」叙事，
  仅作为误差项进入不确定度预算；主贡献为跨城、跨种、达秒定义变更不确定度要求的
  远程 Yb/Sr 比值测量。稿件内所有数字由 `paper/rev2/tools/build_numbers.py` 从
  冻结审计清单生成（无手写数值）。
- 阶段一结论、裁定与外部待确认项汇总见 [docs/audit/PHASE1_SUMMARY.md](docs/audit/PHASE1_SUMMARY.md)。

**参考值（外部文献，供对比）**：
- NIST：`1.2075070393433377230(37)`（Aeppli et al., Phys. Rev. Lett. 137, 033201 (2026)）
- 欧洲网络：`1.207507039343337718(32)`（Pizzocaro et al., Phys. Rev. Research 8, 033250 (2026)）

## 数据来源

- **潮汐**：专业人士提供的 30 秒间隔「综合差」（固体潮+海潮），
  `results/professional_tidal_delta_30s.csv`（UTC，方向武汉−上海，ΔW = g·mm/1000）。
- **潮汐（新增输入，仅登记）**：`results/comp_shanghai-wuhan-beijintime.csv`
  （新一代潮汐模型输出、较既有模型更新；2026-06-20–09-10 北京时、90 s 网格；文件原样
  保留、未接入现有流程；**用途：交叉核对（不替换），后实施**；登记与列定义见
  [clock/PROFESSIONAL_TIDAL_DATA.md](clock/PROFESSIONAL_TIDAL_DATA.md) §7）。
- **实验**：1550 nm 环外拍频（FXE_B8，第 8 列数据），`clock/data/环外数据（第八列数据）/`
  （已 `.gitignore`）。段窗口见 `clock/shared.py` 的 `GROUPS`（北京时 UTC+8）。

## 复现

**阶段一权威入口（audit，优先）**：

```bash
uv sync --extra test
uv run pytest -q
RUN_CLOCK_DATA_TESTS=1 uv run pytest -q
uv run python run_all.py --mode audit --output-dir results/audit-v1
uv run python -m clock_ratio.verify_result_manifest results/audit-v1/verified/manifest.json
uv run python -m clock_ratio.audit_report --manifest results/audit-v1/verified/manifest.json
```

审计模式为 fail-fast，先写入 `results/audit-v1/staging`，经独立清单验证后再提升为不可变历史
并原子切换 `verified` 符号链接。

**重建论文候选稿（paper/rev2）**：

```bash
cd paper/rev2
./tools/check.sh                      # 一键：数字管线校验 + 编译 + 未定义引用检查
uv run --project ../.. python tools/build_numbers.py  # （可选）重新生成数字宏
uv run --project ../.. python tools/make_figures.py   # （可选）重新生成 3 图
```

**历史/附加分析（legacy 链）**：`python run_all.py`（全流程，含 17 段历史检出、
变体、拼接稳定度、独立潮汐报告）；`--tidal-only` 只跑独立潮汐分析与报告。
完整说明见 [docs/WORKFLOW.md](docs/WORKFLOW.md)。

## 目录导航

| 路径 | 内容 |
|---|---|
| `AGENTS.md` | **任务路由（先读）**：每个任务只读哪片、改哪里、如何验证 |
| `paper/rev2/` | **当前论文候选稿**（16 段口径、潮汐为误差项；数字由宏管线生成；`main.pdf` 已入库）|
| `paper/overleaf-rev2-v2/` + zip | 当前 Overleaf 包（由 `rev2/tools/sync_overleaf.sh` 同步）|
| `paper/main.tex` 等 | **历史稿**（17 段潮汐检出叙事；冻结只读）|
| `results/audit-v1/` | 阶段一权威结果层（`verified/manifest.json` 为唯一真源）|
| `docs/audit/PHASE1_SUMMARY.md` | 阶段一结论/裁定/外部待确认总入口 |
| `docs/WORKFLOW.md` | 总流程文档（怎么跑、实验条件变了改哪）|
| `docs/METHODOLOGY.md` | 计算方法说明（精确定义、公式、归一化基准、存疑项）|
| `docs/NOTATION.md` | 符号与术语表 |
| `docs/ERROR_CHECKLIST.md` | 错误清单 + 检查项目（工作纪律）|
| `clock/`、`clock_ratio/` | 分析实现（含 229 个测试；运行说明见 WORKFLOW）|
| `clock_ratio/EXPERIMENT_REPORT.md` | 历史链总报告（钟比值+潮汐+相关性+拼接稳定度）|
| `clock/PROFESSIONAL_TIDAL_DATA.md` | 专业潮汐数据说明（含新增输入登记 §7）|
| `archive/` | 历史/冻结材料（旧 17 段检出叙事、温度分析、旧 Overleaf 快照、diffs、阶段一计划等）|

> 原始实验数据与 MATLAB 处理程序位于 `clock/data/`，已由 `.gitignore` 排除；
> 用户上传素材（`docs/raw/`、`paper/*.docx`、部分 ref PDF）本地保留、不入库。
