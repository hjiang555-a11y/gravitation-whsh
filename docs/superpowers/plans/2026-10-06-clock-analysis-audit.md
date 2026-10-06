# Clock Comparison Analysis Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可复现、可交叉验证且 fail-fast 的武汉—上海光钟比对权威分析链，闭合样本账本，验证潮汐影响，生成 16 段临时主结果、17 段及 leave-one-out 敏感性结果和分析审计报告。

**Architecture:** 将现有脚本中重复的数据选择、比值反演、潮汐窗口和统计逻辑拆为小型纯函数模块，并用 characterization tests 保持受控迁移。所有分析先写入 staging 目录，通过强类型 manifest、哈希和一致性检查后原子提升为 verified 结果；分析报告只读 manifest，不再读取散落产物或硬编码数字。

**Tech Stack:** Python 3.12、uv、NumPy、SciPy、Pydantic 2、Typer、Matplotlib、pytest、Decimal 80 位精度、JSON/CSV、Git。

**Spec:** `docs/superpowers/specs/2026-10-06-clock-comparison-audit-paper-design.md`

## Global Constraints

- 当前只执行阶段一分析审计；不得修改 `paper/`、论文图、论文正文或 Supplementary Information。
- 原始拍频、专业潮汐 Excel、实验方 DOCX/PDF 和水准文档均为只读输入。
- 第 9 段不得删除或隐藏；参数确认前不进入临时主估计，16 段为临时主结果，17 段为敏感性结果。
- 保留现有 1200 s 三角窗、600 s 步长方法作为基准；先验证实现，再依据测试证据修改。
- 现有无法复现的实验方结果标记为 `external-unverified` 或 `pending-verification`，不得猜测补值。
- 所有关键数字至少由现有实现与结构独立的核验实现交叉计算。
- 论文、历史稿和 `archive/` 仅可只读，不参与阶段一结果生成。
- 新分析入口必须 fail-fast；失败运行不得覆盖最后一次 verified 结果。
- 每项任务使用 TDD：失败测试、最小实现、通过测试、提交。
- 只提交本任务列出的文件；不得提交两份未跟踪 DOCX 或原始私有数据。

---

## File Structure

### 新增文件

- `pyproject.toml`：Python 版本、运行依赖、测试依赖和 pytest 配置。
- `uv.lock`：由 uv 生成的可复现依赖锁。
- `clock_ratio/ratio_model.py`：唯一的 Decimal 高精度频率比值反演。
- `clock/sample_selection.py`：统一样本选择、端点裁剪和逐段诊断。
- `clock/data_provenance.py`：输入文件哈希、来源元数据和时间轴质量模型。
- `clock/build_sample_ledger.py`：生成逐段样本账本和时间质量报告的 CLI。
- `clock/build_parameter_ledger.py`：生成逐段频移、继承关系、静态势差和证据状态账本。
- `clock_ratio/tide_conversion.py`：专业潮汐 Excel→规范 CSV 的纯转换与比较逻辑。
- `clock_ratio/windowing.py`：三角窗投影和幅度拟合的统一实现。
- `clock_ratio/statistical_models.py`：类型化固定效应、Birge、Mandel–Paule 和 Bayesian 网格组合。
- `clock_ratio/segment_uncertainty.py`：gap-safe OADEV 和段级统计不确定度。
- `clock_ratio/statistical_scenarios.py`：raw/theory/empirical、16/17 段和 leave-one-out 纯分析。
- `clock_ratio/evidence.py`：跨分析模块共享的证据状态枚举。
- `clock_ratio/uncertainty_budget.py`：区分 correction、standard uncertainty 与 covariance 的可审计预算。
- `clock_ratio/result_manifest.py`：权威 manifest schema、哈希、一致性检查和原子写入。
- `clock_ratio/build_result_manifest.py`：从一次成功 staging run 构建 manifest 的 CLI。
- `clock_ratio/verify_result_manifest.py`：独立验证 manifest 与文件哈希的 CLI。
- `clock_ratio/audit_report.py`：只读 manifest 的分析审计报告生成器。
- `clock_ratio/test_sample_selection.py`：统一样本选择和边界测试。
- `clock_ratio/test_data_provenance.py`：哈希、时间质量和账本测试。
- `clock_ratio/test_tide_conversion.py`：潮汐列、方向、单位和转换测试。
- `clock_ratio/test_windowing.py`：三角窗和合成响应恢复测试。
- `clock_ratio/test_segment_uncertainty.py`：gap-safe OADEV、噪声斜率和限制状态测试。
- `clock_ratio/test_statistical_scenarios.py`：16/17 段、排除和 leave-one-out 测试。
- `clock_ratio/test_uncertainty_budget.py`：预算分量、相关矩阵、冲突状态和总量门测试。
- `clock_ratio/test_result_manifest.py`：schema、哈希、membership 和原子写入测试。
- `clock_ratio/test_audit_report.py`：manifest-only 报告和禁止硬编码测试。

### 修改文件

- `clock/shared.py`：拆出单文件加载与稳定时间排序，保留公共 API。
- `clock_ratio/compute_ratio.py`：改用共享选择和 ratio model，写出真实裁剪后边界。
- `clock_ratio/tidal_analysis.py`：复用共享选择与 ratio model，保留兼容导出。
- `clock/segment_analysis/batch_analysis.py`：复用统一样本和统一窗口函数。
- `clock_ratio/tidal_stability.py`：仅调整类型导入，算法作为回归基线。
- `clock_ratio/tidal_correction.py`：适配共享选择与 staging 输出。
- `clock_ratio/statistical_combination.py`：保留旧 array API，转发到类型化核心。
- `clock_ratio/statistical_methods.py`：改用真实 gap-safe 段不确定度和纯分析接口。
- `clock_ratio/statistical_methods_tidal.py`：改用统一场景分析。
- `clock_ratio/statistical_methods_tidal_seg9.py`：改为通用排除/LOO CLI 兼容层。
- `run_all.py`：新增 audit 模式、Step 类型、staging 和原子 promote。
- `clock_ratio/test_tidal_analysis.py`：迁移后的兼容和真实数据 characterization tests。
- `clock_ratio/test_tidal_outputs.py`：真实数据边界、staging 和结果回归。
- `clock_ratio/test_tidal_report.py`：audit fail-fast 与 legacy 隔离测试。
- `clock_ratio/test_statistical_combination.py`：输入验证、数值快照和缩放不变性测试。
- `docs/WORKFLOW.md`：阶段一权威命令、质量门和 legacy 隔离。
- `README.md`：最小复现入口和结果状态说明。

---

### Task 1: 固定环境与现有结果基线

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Modify: `clock_ratio/test_tidal_outputs.py:185-200`
- Modify: `clock_ratio/test_statistical_combination.py:1-45`

**Interfaces:**
- Consumes: 当前 Python 3.12 脚本和既有测试模块。
- Produces: `uv sync --extra test` 可安装环境；受版本控制的现有 17 段 characterization baseline。

- [ ] **Step 1: 写环境声明**

创建：

```toml
[project]
name = "gravitation-whsh"
version = "0.1.0"
description = "Reproducible Wuhan-Shanghai optical-clock comparison analysis"
requires-python = ">=3.12,<3.13"
dependencies = [
  "numpy>=2.0,<3",
  "scipy>=1.14,<2",
  "matplotlib>=3.9,<4",
  "pydantic>=2.10,<3",
  "typer>=0.15,<1",
]

[project.optional-dependencies]
test = ["pytest>=8.3,<9"]
weather = ["meteostat>=1.6,<2"]

[tool.pytest.ini_options]
testpaths = ["clock_ratio"]
python_files = ["test_*.py"]
addopts = "-ra"
```

- [ ] **Step 2: 生成锁文件并验证依赖**

Run:

```bash
uv lock
uv sync --extra test
uv pip check
```

Expected: 三条命令退出码均为 0，`uv.lock` 被创建。

- [ ] **Step 3: 扩展真实数据 characterization test**

在 `test_tidal_outputs.py` 的 `RUN_CLOCK_DATA_TESTS` 测试中锁定当前可复现事实，不锁定已知错误的旧时间边界：

```python
from clock.shared import load_beat
from clock_ratio.tidal_analysis import SelectionPlan, select_segments

EXPECTED_GROUPS = tuple(range(1, 18))
EXPECTED_TOTAL_VALID = 1_008_912

@pytest.mark.skipif(os.getenv("RUN_CLOCK_DATA_TESTS") != "1", reason="requires private raw data")
def test_real_data_characterization():
    segments = select_segments(*load_beat(), SelectionPlan())
    assert tuple(s.group for s in segments) == EXPECTED_GROUPS
    assert sum(len(s.beat) for s in segments) == EXPECTED_TOTAL_VALID
    assert all(s.times.shape == s.beat.shape for s in segments)
    assert all(s.times[0] <= s.times[-1] for s in segments)
```

- [ ] **Step 4: 运行现有快速测试并记录基线**

Run:

```bash
uv run pytest -q \
  clock_ratio/test_statistical_combination.py \
  clock_ratio/test_tidal_analysis.py \
  clock_ratio/test_tidal_outputs.py \
  clock_ratio/test_tidal_report.py
```

Expected: PASS。若任何现有测试失败，停止后续任务并在提交信息前记录失败，不修改测试来掩盖失败。

- [ ] **Step 5: 运行真实数据基线**

Run:

```bash
RUN_CLOCK_DATA_TESTS=1 uv run pytest -q \
  clock_ratio/test_tidal_analysis.py \
  clock_ratio/test_tidal_outputs.py
```

Expected: PASS，总样本数为 1,008,912。

- [ ] **Step 6: 提交环境与基线**

```bash
git add pyproject.toml uv.lock clock_ratio/test_tidal_outputs.py clock_ratio/test_statistical_combination.py
git commit -m "test: establish reproducible analysis baseline"
```

---

### Task 2: 抽离高精度比值模型

**Files:**
- Create: `clock_ratio/ratio_model.py`
- Modify: `clock_ratio/compute_ratio.py:32-78`
- Modify: `clock_ratio/tidal_analysis.py:15-16,162-194`
- Modify: `clock_ratio/test_tidal_analysis.py:41-100`

**Interfaces:**
- Consumes: `clock.shared` 中的 `Decimal` 常量 `COEF_DEC`、`DELTA_G_DEC`、`R_NIST_DEC`。
- Produces: `full_ratio(mean_dm: Decimal, shift_a: Decimal, global_median: Decimal) -> Decimal`。

- [ ] **Step 1: 先把 Decimal 测试改为新接口**

```python
from clock_ratio.ratio_model import full_ratio


def test_full_ratio_preserves_decimal_precision():
    value = full_ratio(
        Decimal("35123456.789012345678"),
        Decimal("-1.25e-16"),
        Decimal("35120000.123456789012"),
    )
    assert value == Decimal(
        "1.2075068107011621015629815674298061716812946748966460855865936187804241395717995"
    )
```

- [ ] **Step 2: 运行测试确认模块不存在**

Run: `uv run pytest clock_ratio/test_tidal_analysis.py::test_full_ratio_preserves_decimal_precision -v`

Expected: FAIL with `ModuleNotFoundError: clock_ratio.ratio_model`。

- [ ] **Step 3: 创建唯一高精度实现**

```python
from decimal import Decimal

from clock.shared import (
    COEF1156,
    D_1_25,
    D_7_25,
    DELTA_G,
    DIV20,
    FREF,
    N1156,
    N1397,
    N1550,
    N1550_WH,
)


def full_ratio(mean_dm: Decimal, shift_a: Decimal, global_median: Decimal) -> Decimal:
    coef1397 = (Decimal(1) + shift_a) / Decimal(2)
    denominator = coef1397 / N1397 * (N1550 + D_7_25 + D_1_25)
    delta_ratio = COEF1156 / N1156 * (mean_dm / FREF / DIV20) / denominator
    numerator = N1550_WH + Decimal(26) / Decimal(20) + global_median / FREF / DIV20
    denominator_base = N1550 + Decimal(8) / Decimal(25)
    ratio_base = COEF1156 / N1156 * numerator / (coef1397 / N1397 * denominator_base)
    sr_yb_raw = ratio_base + delta_ratio
    return (Decimal(1) / sr_yb_raw) * (Decimal(1) + DELTA_G)
```

该实现逐项对应当前 `compute_ratio.py:69-78`，本任务只搬移代码，不改变物理公式。

- [ ] **Step 4: 将两个调用者改为导入新模块**

删除 `compute_ratio.py` 的本地 `full_ratio` 实现；`compute_ratio.py` 和 `tidal_analysis.py` 均使用：

```python
from clock_ratio.ratio_model import full_ratio
```

- [ ] **Step 5: 运行 Decimal 与潮汐测试**

Run:

```bash
uv run pytest -q clock_ratio/test_tidal_analysis.py
```

Expected: PASS，固定响应和反演测试数值不变。

- [ ] **Step 6: 提交**

```bash
git add clock_ratio/ratio_model.py clock_ratio/compute_ratio.py clock_ratio/tidal_analysis.py clock_ratio/test_tidal_analysis.py
git commit -m "refactor: centralize precision ratio inversion"
```

---

### Task 3: 建立统一样本选择与诊断模型

**Files:**
- Create: `clock/sample_selection.py`
- Create: `clock_ratio/test_sample_selection.py`
- Modify: `clock_ratio/tidal_analysis.py:18-89`
- Modify: `clock_ratio/test_tidal_analysis.py:18-38,103-145`

**Interfaces:**
- Consumes: `clock.shared.GROUPS`、`SHIFT_A`、`EXCLUDE_RANGES`、`JUMP_THRESHOLD`、`longest_valid_span`。
- Produces: `SelectionPlan`、`SelectionDiagnostics`、`SelectedSegment`、`EndpointScreen`、`endpoint_screen_indices()`、`select_segments()`、`DEFAULT_SELECTION_PLAN`。

- [ ] **Step 1: 写端点同步裁剪失败测试**

```python
def test_endpoint_screen_indices_trim_times_and_values_identically():
    beat = np.array([101.0, 100.0, 100.0, 100.0, 101.0])
    times = np.datetime64("2026-01-01T00:00:00") + np.arange(5).astype("timedelta64[s]")
    screen = endpoint_screen_indices(beat)
    assert np.array_equal(times[screen.start:screen.stop], times[1:4])
    assert np.array_equal(beat[screen.start:screen.stop], beat[1:4])
    assert (screen.removed_start, screen.removed_end) == (1, 1)
```

同时加入：输入不变性、空数组、全平坦数组、排除区间边界和含时间缺口的选择测试。

- [ ] **Step 2: 运行新测试确认失败**

Run: `uv run pytest clock_ratio/test_sample_selection.py -v`

Expected: FAIL with missing module or symbol。

- [ ] **Step 3: 创建不可变类型**

```python
FloatArray = NDArray[np.float64]
TimeArray = NDArray[np.datetime64]
Windows = tuple[tuple[str, str], ...]

@dataclass(frozen=True, slots=True)
class EndpointScreen:
    start: int
    stop: int
    removed_start: int
    removed_end: int

@dataclass(frozen=True, slots=True)
class SelectionDiagnostics:
    n_window: int
    n_excluded: int
    n_plausible: int
    n_jump_valid: int
    n_longest_span: int
    n_removed_start: int
    n_removed_end: int
    n_final: int
    source_span_start: int
    source_span_stop: int

@dataclass(frozen=True, slots=True)
class SelectionPlan:
    groups: Windows
    shifts: tuple[Decimal, ...]
    exclusions: Windows
    plausible_low_hz: float = 3e7
    plausible_high_hz: float = 4e7
    jump_threshold_hz: float = 10.0

@dataclass(frozen=True, slots=True)
class SelectedSegment:
    group: int
    times: TimeArray
    beat: FloatArray
    m_dec: Decimal
    shift_a: Decimal
    raw_mean: float
    rem_start: int
    rem_end: int
    diagnostics: SelectionDiagnostics

DEFAULT_SELECTION_PLAN = SelectionPlan(
    groups=tuple(GROUPS),
    shifts=tuple(SHIFT_A),
    exclusions=tuple(EXCLUDE_RANGES),
)
```

- [ ] **Step 4: 实现索引式端点裁剪和选择**

```python
def endpoint_screen_indices(x: FloatArray) -> EndpointScreen:
    if x.ndim != 1 or x.size == 0:
        raise ValueError("endpoint screening requires a non-empty 1-D array")
    threshold = 0.01 * float(np.ptp(x))
    if threshold == 0.0:
        return EndpointScreen(0, x.size, 0, 0)
    center = float(np.median(x))
    keep = np.abs(x - center) <= threshold
    valid = np.flatnonzero(keep)
    if valid.size == 0:
        raise ValueError("endpoint screening removed every sample")
    start = int(valid[0])
    stop = int(valid[-1]) + 1
    return EndpointScreen(start, stop, start, x.size - stop)
```

`select_segments()` 逐字保持当前 `tidal_analysis.select_segments` 的范围、跳点、最长索引段和 1% 端点语义，但同时记录每一步计数，并用同一 `screen.start:screen.stop` 裁剪时间和值。

- [ ] **Step 5: 在 tidal_analysis 中兼容导出**

```python
from clock.sample_selection import (
    DEFAULT_SELECTION_PLAN,
    SelectionPlan,
    SelectedSegment as Segment,
    select_segments,
)
```

删除本地重复 dataclass 和实现，但保持下游 `from tidal_analysis import Segment` 可用。

- [ ] **Step 6: 跑选择和潮汐回归**

Run:

```bash
uv run pytest -q \
  clock_ratio/test_sample_selection.py \
  clock_ratio/test_tidal_analysis.py \
  clock_ratio/test_tidal_outputs.py
```

Expected: PASS。

- [ ] **Step 7: 运行真实数据 membership 回归**

Run: `RUN_CLOCK_DATA_TESTS=1 uv run pytest -q clock_ratio/test_tidal_outputs.py::test_real_data_characterization`

Expected: 17 段、总样本 1,008,912，与任务 1 一致。

- [ ] **Step 8: 提交**

```bash
git add clock/sample_selection.py clock_ratio/test_sample_selection.py clock_ratio/tidal_analysis.py clock_ratio/test_tidal_analysis.py
git commit -m "refactor: unify segment sample selection"
```

---

### Task 4: 审计原始时间轴与输入 provenance

**Files:**
- Create: `clock_ratio/evidence.py`
- Create: `clock/data_provenance.py`
- Create: `clock/build_parameter_ledger.py`
- Create: `clock_ratio/test_data_provenance.py`
- Modify: `clock/shared.py:111-147`

**Interfaces:**
- Consumes: 原始拍频文件路径和当前 `first_stamp()` 规则。
- Produces: `FileDigest`、`TimestampQuality`、`ParameterEvidence`、`load_beat_file()`、`inspect_timestamp_labels()`、`sha256_file()`、`parameter_ledger.csv`、`parameter_conflicts.json`。

- [ ] **Step 1: 写时间质量测试**

构造带亚秒抖动、重复、倒序和缺口的临时文件：

```python
def test_timestamp_quality_reports_duplicates_gaps_and_reversal(tmp_path):
    path = write_beat_fixture(
        tmp_path,
        [
            "2026-06-29 10:00:00.10",
            "2026-06-29 10:00:01.05",
            "2026-06-29 10:00:01.05",
            "2026-06-29 10:00:00.95",
            "2026-06-29 10:00:03.00",
        ],
    )
    quality = inspect_timestamp_labels(path)
    assert quality.n_rows == 5
    assert quality.n_duplicates == 1
    assert quality.n_reversals == 1
    assert quality.n_gaps == 1
    assert quality.max_abs_jitter_s > 0
```

- [ ] **Step 2: 写哈希稳定性测试**

```python
def test_sha256_changes_when_input_changes(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("a", encoding="utf-8")
    first = sha256_file(path)
    path.write_text("b", encoding="utf-8")
    assert sha256_file(path) != first


def test_parameter_ledger_flags_sensitive_and_inherited_groups():
    records = build_parameter_records(Path("clock/params.json"))
    seg9 = next(r for r in records if r.group == 9 and r.name == "a_SM")
    assert seg9.status is EvidenceStatus.pending_verification
    inherited = [r for r in records if r.group in (15, 16, 17) and r.name == "shift_a"]
    assert {r.inherited_from_group for r in inherited} == {12}
    assert all(r.status is EvidenceStatus.pending_verification for r in inherited)
```

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_data_provenance.py -v`

Expected: FAIL with missing symbols。

- [ ] **Step 4: 创建类型和纯函数**

```python
class EvidenceStatus(str, Enum):
    established = "established"
    supported_with_limitations = "supported-with-limitations"
    pending_verification = "pending-verification"
    external_unverified = "external-unverified"

@dataclass(frozen=True, slots=True)
class FileDigest:
    relative_path: str
    sha256: str
    size_bytes: int
    mtime_utc: datetime

@dataclass(frozen=True, slots=True)
class ParameterEvidence:
    name: str
    group: int | None
    value: Decimal
    unit: str
    source_path: str
    inherited_from_group: int | None
    status: EvidenceStatus
    note: str

@dataclass(frozen=True, slots=True)
class TimestampQuality:
    n_rows: int
    n_parse_errors: int
    n_duplicates: int
    n_reversals: int
    n_gaps: int
    max_gap_s: float
    max_abs_jitter_s: float
    first_label_utc8: datetime
    last_label_utc8: datetime
```

`EvidenceStatus` 写入 `clock_ratio/evidence.py`，其他类型写入 `clock/data_provenance.py`。`inspect_timestamp_labels()` 只读逐行标签并计算 `np.diff`；1 s 之外的正差记为 gap，零差记 duplicate，负差记 reversal，`abs(diff-1)` 的最大值记 jitter。解析失败计数后必须使该文件状态为限制状态，不静默跳过。

`build_parameter_records()` 从 `params.json` 逐项写出 17 段 `shift_a` 及分量、静态 `DELTA_G` 和水准值来源；第 9 段 `a_SM`、第 15–17 段继承值及所有只有文档声明而无可执行来源的项标记为 pending。CLI 同时写 `parameter_ledger.csv` 和只包含冲突/缺口的 `parameter_conflicts.json`。

- [ ] **Step 5: 拆分 shared 单文件加载**

```python
def uniform_file_axis(first: np.datetime64, count: int) -> TimeArray:
    if count < 0:
        raise ValueError("count must be non-negative")
    return first + np.arange(count).astype("timedelta64[s]")


def load_beat_file(path: Path) -> tuple[TimeArray, FloatArray]:
    beat = np.loadtxt(path, comments="#", usecols=(10,), ndmin=1)
    return uniform_file_axis(first_stamp(path), beat.size), beat.astype(float)
```

`load_beat()` 只负责发现文件、拼接并使用 `np.argsort(times, kind="stable")` 稳定排序。

- [ ] **Step 6: 运行单元和真实数据加载测试**

Run:

```bash
uv run pytest -q clock_ratio/test_data_provenance.py clock_ratio/test_tidal_analysis.py
RUN_CLOCK_DATA_TESTS=1 uv run pytest -q clock_ratio/test_tidal_outputs.py::test_real_data_characterization
uv run python -m clock.build_parameter_ledger --output-dir results/audit-v1/staging
```

Expected: PASS，总样本 membership 不变；生成的 parameter ledger 明确标记第 9 段和第 15–17 段，而不修改 `params.json`。

- [ ] **Step 7: 提交**

```bash
git add clock_ratio/evidence.py clock/data_provenance.py clock/build_parameter_ledger.py clock/shared.py clock_ratio/test_data_provenance.py
git commit -m "feat: audit inputs timestamps and parameters"
```

---

### Task 5: 生成逐段样本账本并迁移三个调用者

**Files:**
- Create: `clock/build_sample_ledger.py`
- Modify: `clock_ratio/compute_ratio.py:32-193`
- Modify: `clock/segment_analysis/batch_analysis.py:42-192`
- Modify: `clock_ratio/tidal_correction.py:22-25,185-203`
- Modify: `clock_ratio/test_sample_selection.py`
- Modify: `clock_ratio/test_tidal_outputs.py:185-200`

**Interfaces:**
- Consumes: `select_segments()`、`SelectionDiagnostics`、`inspect_timestamp_labels()`。
- Produces: `results/audit-v1/sample_ledger.csv`、`time_quality.json`；三个分析入口使用完全相同的 `SelectedSegment`。

- [ ] **Step 1: 写真实边界和调用者一致性测试**

```python
@pytest.mark.skipif(os.getenv("RUN_CLOCK_DATA_TESTS") != "1", reason="requires private raw data")
def test_ratio_bounds_equal_actual_retained_bounds():
    segments = select_segments(*load_beat(), DEFAULT_SELECTION_PLAN)
    rows = compute_ratio_rows(segments)
    for segment, row in zip(segments, rows, strict=True):
        assert row.t_start == str(segment.times[0])
        assert row.t_end == str(segment.times[-1])
        assert row.n_valid == len(segment.beat)
```

在测试文件中加入结构独立的 MATLAB 公式核验器，不调用 `ratio_model.full_ratio()`：

```python
def reference_ratio_from_comb_chain(mean_dm, shift_a, global_median):
    sr_multiplier = (Decimal(1) + shift_a) / Decimal(2)
    measured_delta = (
        COEF1156 / N1156
        * (mean_dm / FREF / DIV20)
        / (sr_multiplier / N1397 * (N1550 + Decimal(8) / Decimal(25)))
    )
    numerator_count = N1550_WH + Decimal(26) / Decimal(20) + global_median / FREF / DIV20
    baseline_sr_yb = (
        COEF1156 / N1156 * numerator_count
        / (sr_multiplier / N1397 * (N1550 + Decimal(8) / Decimal(25)))
    )
    return Decimal(1) / (baseline_sr_yb + measured_delta) * (Decimal(1) + DELTA_G)
```

对 17 个真实段逐一断言两种实现的 Decimal 差值小于 `1e-75`。另加 synthetic test，断言 batch lane 和 tidal lane 接收相同 group、时间、beat 和样本数。

- [ ] **Step 2: 运行目标测试确认旧边界失败**

Run: `RUN_CLOCK_DATA_TESTS=1 uv run pytest clock_ratio/test_tidal_outputs.py -k ratio_bounds -v`

Expected: FAIL，指出旧 `ratio_17seg.csv` 使用裁剪前边界。

- [ ] **Step 3: 将 compute_ratio 改为纯行构建 + CLI 写出**

增加：

```python
@dataclass(frozen=True, slots=True)
class RatioRow:
    group: int
    ratio: Decimal
    n_valid: int
    t_start: str
    t_end: str
    rem_start: int
    rem_end: int


def compute_ratio_rows(segments: Sequence[SelectedSegment]) -> tuple[RatioRow, ...]:
    return tuple(
        RatioRow(
            group=s.group,
            ratio=full_ratio(to_dec(float(np.mean(s.beat))) - s.m_dec, s.shift_a, s.m_dec),
            n_valid=len(s.beat),
            t_start=str(s.times[0]),
            t_end=str(s.times[-1]),
            rem_start=s.rem_start,
            rem_end=s.rem_end,
        )
        for s in segments
    )
```

现有 CSV schema 保持；仅 `t_start/t_end` 改为真实裁剪后边界。

- [ ] **Step 4: 迁移 batch_analysis**

删除 102–147 的重复选择代码，改为：

```python
times, beat = load_beat()
segments = select_segments(times, beat, DEFAULT_SELECTION_PLAN)
for segment in segments:
    d_long = segment.beat
    t_long = segment.times
    diagnostics = segment.diagnostics
    # 现有窗口、拟合和输出逻辑从这里继续
```

本任务不修改窗口和拟合公式。

- [ ] **Step 5: 实现账本 CLI**

`build_sample_ledger.py` 写 CSV 字段：

```text
group,n_window,n_excluded,n_plausible,n_jump_valid,n_longest_span,
n_removed_start,n_removed_end,n_final,source_span_start,source_span_stop,
retained_start_beijing,retained_end_beijing
```

写入临时文件后 `Path.replace()` 原子替换目标。`time_quality.json` 保存每个输入文件的 `TimestampQuality` 和 `FileDigest`。

- [ ] **Step 6: 运行迁移测试**

Run:

```bash
uv run pytest -q \
  clock_ratio/test_sample_selection.py \
  clock_ratio/test_tidal_analysis.py \
  clock_ratio/test_tidal_outputs.py
RUN_CLOCK_DATA_TESTS=1 uv run pytest -q \
  clock_ratio/test_tidal_outputs.py
```

Expected: 所有比值和样本数不变；旧 ratio CSV 的边界字段按真实裁剪后时刻受控变化。

- [ ] **Step 7: 生成账本并验证三种总数解释入口存在**

Run:

```bash
uv run python -m clock.build_sample_ledger --output-dir results/audit-v1/staging
```

Expected: CSV 的 `n_final` 总和为 1,008,912；报告同时给出当前代码口径，外部 1,009,022 和 1,009,204 作为待对账记录，不伪造逐段分配。

- [ ] **Step 8: 提交**

```bash
git add clock/build_sample_ledger.py clock_ratio/compute_ratio.py clock/segment_analysis/batch_analysis.py clock_ratio/tidal_correction.py clock_ratio/test_sample_selection.py clock_ratio/test_tidal_outputs.py
git commit -m "feat: build authoritative segment sample ledger"
```

---

### Task 6: 建立可执行潮汐转换与输入核验

**Files:**
- Create: `clock_ratio/tide_conversion.py`
- Create: `clock_ratio/test_tide_conversion.py`
- Modify: `clock/PROFESSIONAL_TIDAL_DATA.md`

**Interfaces:**
- Consumes: 专业潮汐 Excel、现有 `results/professional_tidal_delta_30s.csv`。
- Produces: `TideConversionConfig`、`convert_height_mm_to_potential()`、`convert_workbook()`、`compare_tide_csv()`。

- [ ] **Step 1: 写单位、方向和时间测试**

```python
def test_height_difference_conversion_preserves_direction():
    config = TideConversionConfig(
        gravity_m_s2=Decimal("9.794"),
        direction="CAS-minus-SHA",
        timezone="UTC",
    )
    assert convert_height_mm_to_potential(Decimal("1"), config) == Decimal("0.009794")
    assert convert_height_mm_to_potential(Decimal("-1"), config) == Decimal("-0.009794")
```

再构造最小 workbook fixture，验证 B/C/E/F 与“综合差”列选择、30 s 间隔、UTC 首末点和无重复。

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_tide_conversion.py -v`

Expected: FAIL with missing module。

- [ ] **Step 3: 创建显式配置**

```python
@dataclass(frozen=True, slots=True)
class TideConversionConfig:
    gravity_m_s2: Decimal
    direction: Literal["CAS-minus-SHA"]
    timezone: Literal["UTC"]
    source_column: str = "综合差"
    expected_step_s: int = 30


def convert_height_mm_to_potential(value_mm: Decimal, config: TideConversionConfig) -> Decimal:
    return value_mm * config.gravity_m_s2 / Decimal(1000)
```

使用 `openpyxl` 读取 Excel；在 `pyproject.toml` 运行依赖中加入 `openpyxl>=3.1,<4`，随后执行 `uv lock` 更新 `uv.lock`。

- [ ] **Step 4: 实现逐行转换和比较**

`convert_workbook()` 输出固定列 `timestamp_utc,total_tidal_delta_m2_s2_surface`。`compare_tide_csv()` 返回：行数、时间范围、最大绝对时间偏差、最大绝对数值差、首个不一致行；任何时间重复或非 30 s 步长立即失败。

- [ ] **Step 5: 对真实 Excel 与当前 CSV 运行只读比较**

Run:

```bash
uv run python -m clock_ratio.tide_conversion \
  --input "clock/武汉-上海潮汐结果（0620-0910）-30秒间隔数据.xlsx" \
  --compare results/professional_tidal_delta_30s.csv \
  --output-dir results/audit-v1/staging/tide-conversion
```

Expected: 生成转换副本和差异 JSON，不覆盖当前 Git 跟踪 CSV。若不逐点一致，停止并将首个差异作为审计发现。

- [ ] **Step 6: 更新数据说明**

文档必须使用“由专业提供综合高度差和 `g=9.794 m/s²` 派生的等效势差模板”，并列出尚缺的模型、版本、坐标、参考框架和 EOP/IERS 信息；不将其称为已验证完整潮汐位势。

- [ ] **Step 7: 测试并提交**

```bash
uv run pytest -q clock_ratio/test_tide_conversion.py
git add pyproject.toml uv.lock clock_ratio/tide_conversion.py clock_ratio/test_tide_conversion.py clock/PROFESSIONAL_TIDAL_DATA.md
git commit -m "feat: make professional tide conversion auditable"
```

---

### Task 7: 统一三角窗投影并验证潮汐响应恢复

**Files:**
- Create: `clock_ratio/windowing.py`
- Create: `clock_ratio/test_windowing.py`
- Modify: `clock/segment_analysis/batch_analysis.py:54-99,148-192`

**Interfaces:**
- Consumes: 1 s beat、逐秒潮汐模板、1200 s width 和 600 s stride。
- Produces: `triangular_average()`、`AmplitudeFit`、`fit_demeaned_amplitude()`。

- [ ] **Step 1: 写窗口定义测试**

```python
def test_triangular_average_constant_signal_is_unchanged():
    x = np.full(3600, 7.5)
    got = triangular_average(x, width=1200, stride=600)
    assert np.allclose(got, 7.5, rtol=0, atol=1e-14)


def test_triangular_average_matches_explicit_dot_product():
    x = np.arange(2400, dtype=float)
    w = np.bartlett(1200)
    expected = np.array([np.dot(x[i:i+1200], w) / w.sum() for i in (0, 600, 1200)])
    assert np.allclose(triangular_average(x, width=1200, stride=600), expected)
```

- [ ] **Step 2: 写已知响应与符号测试**

```python
def test_fit_recovers_known_negative_response():
    tide = np.sin(np.linspace(0, 20 * np.pi, 24_000))
    beat = -0.6 * tide
    overlap_b = triangular_average(beat, width=1200, stride=600)
    overlap_t = triangular_average(tide, width=1200, stride=600)
    independent_b = triangular_average(beat, width=1200, stride=1200)
    independent_t = triangular_average(tide, width=1200, stride=1200)
    fit = fit_demeaned_amplitude(overlap_b, overlap_t, independent_b, independent_t)
    assert fit.amplitude == pytest.approx(-0.6, abs=1e-12)
    assert fit.n_point_estimate > fit.n_inference
```

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_windowing.py -v`

Expected: FAIL with missing module。

- [ ] **Step 4: 实现统一窗口函数**

```python
def triangular_average(x: FloatArray, *, width: int, stride: int) -> FloatArray:
    if x.ndim != 1 or width < 2 or stride < 1 or x.size < width:
        raise ValueError("invalid triangular window request")
    weights = np.bartlett(width)
    denominator = float(weights.sum())
    starts = range(0, x.size - width + 1, stride)
    return np.array([np.dot(x[s:s + width], weights) / denominator for s in starts])
```

`fit_demeaned_amplitude()` 继续使用重叠窗做点估计、1200 s 不重叠窗做当前基准推断，并返回具名 dataclass：

```python
@dataclass(frozen=True, slots=True)
class AmplitudeFit:
    amplitude: float
    uncertainty: float
    pearson_r: float
    pearson_p: float
    n_point_estimate: int
    n_inference: int
```

- [ ] **Step 5: 迁移 batch_analysis，不改变基准结果**

`triangular_window()` 和 `fit_amplitude()` 改为兼容 wrapper 或直接调用新模块。先保持输出 CSV schema 与 1200/600 数值不变。

- [ ] **Step 6: 跑合成测试和真实结果回归**

Run:

```bash
uv run pytest -q clock_ratio/test_windowing.py clock_ratio/test_tidal_analysis.py
uv run python clock/segment_analysis/batch_analysis.py
```

Expected: 合成响应恢复；真实 `batch_summary.csv` 和 `batch_aggregate.csv` 除格式化差异外与迁移前一致。保存机器 diff 供后续审计，不手工覆盖差异。

- [ ] **Step 7: 提交**

```bash
git add clock_ratio/windowing.py clock_ratio/test_windowing.py clock/segment_analysis/batch_analysis.py
git commit -m "refactor: verify shared tidal window projection"
```

---

### Task 8: 建立类型化统计组合核心

**Files:**
- Create: `clock_ratio/statistical_models.py`
- Modify: `clock_ratio/statistical_combination.py:1-127`
- Modify: `clock_ratio/test_statistical_combination.py`

**Interfaces:**
- Consumes: 每段 group、Decimal ratio、fractional deviation 和 absolute uncertainty。
- Produces: `SegmentEstimate`、`CombinationConfig`、`CombinationResult`、`combine_estimates()`；旧 `combine()` 为兼容 wrapper。

- [ ] **Step 1: 写非法输入和数值快照测试**

```python
@pytest.mark.parametrize("bad_u", [0.0, -1.0, np.nan, np.inf])
def test_combine_rejects_invalid_uncertainty(bad_u):
    estimates = [
        SegmentEstimate(1, Decimal("1.2"), 0.0, 1e-18),
        SegmentEstimate(2, Decimal("1.2"), 1e-18, bad_u),
    ]
    with pytest.raises(ValueError):
        combine_estimates(estimates, Decimal("1.2"))


def test_combination_snapshot():
    deviations = (0.0, 1.0e-18, -0.5e-18, 2.0e-18)
    uncertainties = (1.0e-18, 1.2e-18, 0.9e-18, 1.1e-18)
    estimates = tuple(
        SegmentEstimate(i + 1, Decimal("1.2075"), y, u)
        for i, (y, u) in enumerate(zip(deviations, uncertainties, strict=True))
    )
    result = combine_estimates(estimates, Decimal("1.2075"))
    assert result.n == 4
    assert result.dof == 3
    assert result.y_wls == pytest.approx(4.606769046858974e-19, rel=1e-12)
    assert result.chi2_red == pytest.approx(1.7068376113910986, rel=1e-12)
    assert result.u_stat_bayes == pytest.approx(6.372514260551814e-19, rel=1e-12)
    assert result.xi_bayes == pytest.approx(2.4323182678604663e-19, rel=1e-12)
```

这些字面量由当前已通过的旧实现对固定小数据集计算；评审时同时保留手算 WLS 断言，不得从被测函数动态生成 expected。

- [ ] **Step 2: 写缩放不变性测试**

对 deviations 和 uncertainties 同比例缩放，断言 `chi2_red`、Birge ratio 不变，中心和不确定度按比例缩放。

- [ ] **Step 3: 运行测试确认新接口失败**

Run: `uv run pytest clock_ratio/test_statistical_combination.py -v`

Expected: FAIL with missing `statistical_models`。

- [ ] **Step 4: 创建类型化模型和验证**

```python
@dataclass(frozen=True, slots=True)
class SegmentEstimate:
    group: int
    ratio: Decimal
    deviation: float
    u_absolute: float

@dataclass(frozen=True, slots=True)
class CombinationConfig:
    bayes_grid_points: int = 401
    bayes_log_span: tuple[float, float] = (1e-6, 1e3)
    prior: Literal["jeffreys"] = "jeffreys"

@dataclass(frozen=True, slots=True)
class CombinationResult:
    reference_ratio: Decimal
    n: int
    y_wls: float
    u_wls: float
    chi2: float
    dof: int
    chi2_red: float
    p_chi2: float
    birge_ratio: float
    u_birge: float
    xi_mp: float
    y_mp: float
    u_mp: float
    mu_bayes: float
    u_stat_bayes: float
    xi_bayes: float
    bayes_log_span_used: tuple[float, float]
    bayes_edge_mass: tuple[float, float]
```

拒绝重复 group、少于 2 段、非有限 deviation、非正 uncertainty 和非正 reference ratio。Bayesian 网格检查首尾各 3 个 bin 的后验质量；任一侧超过 1% 时把对应 log-xi 边界扩大 10 倍并重算，最多扩展 6 次，仍不收敛才抛出 `ValueError`。结果对象同时记录最终网格边界和边界质量，不能只检查 finite。

- [ ] **Step 5: 将旧 combine 改为薄兼容层**

旧接口构造 `SegmentEstimate`，调用新核心，再返回字段名与现有 JSON 兼容的 dict。保持当前 `statistical_methods_tidal.json` 数值基线。

- [ ] **Step 6: 运行统计测试**

Run: `uv run pytest -q clock_ratio/test_statistical_combination.py`

Expected: PASS，旧单位一致性测试继续通过。

- [ ] **Step 7: 提交**

```bash
git add clock_ratio/statistical_models.py clock_ratio/statistical_combination.py clock_ratio/test_statistical_combination.py
git commit -m "refactor: type statistical combination models"
```

---

### Task 9: 用 gap-safe OADEV 建立段级统计不确定度

**Files:**
- Create: `clock_ratio/segment_uncertainty.py`
- Create: `clock_ratio/test_segment_uncertainty.py`
- Modify: `clock_ratio/tidal_stability.py:11`
- Modify: `clock_ratio/statistical_methods.py:54-128`

**Interfaces:**
- Consumes: `SelectedSegment.times`、fractional frequency、`tidal_stability.oadev()`。
- Produces: `StabilityFitConfig`、`SegmentUncertainty`、`estimate_segment_uncertainty()`。

- [ ] **Step 1: 写 gap 和 duplicate 不跨越测试**

```python
def test_estimator_never_crosses_gap_or_duplicate():
    times = np.array([
        "2026-01-01T00:00:00", "2026-01-01T00:00:01",
        "2026-01-01T00:00:01", "2026-01-01T00:00:05",
        "2026-01-01T00:00:06",
    ], dtype="datetime64[s]")
    y = np.array([0.0, 1.0, 2.0, 3.0, 4.0]) * 1e-18
    result = estimate_segment_uncertainty(times, y, StabilityFitConfig(fit_min_s=1))
    assert result.n_valid == 5
    assert result.n_runs == 3
```

- [ ] **Step 2: 写白频噪声斜率测试**

使用固定 RNG seed 生成足够长的 white-frequency-noise，断言拟合斜率落在 `[-0.65,-0.35]`；短数据和明显 flicker 数据返回 `supported-with-limitations`，不静默使用最长 τ。

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_segment_uncertainty.py -v`

Expected: FAIL with missing module。

- [ ] **Step 4: 创建配置和结果类型**

```python
@dataclass(frozen=True, slots=True)
class StabilityFitConfig:
    tau0_s: int = 1
    fit_min_s: int = 128
    fit_max_fraction: float = 0.25
    estimator: Literal["gap_safe_oadev"] = "gap_safe_oadev"

@dataclass(frozen=True, slots=True)
class SegmentUncertainty:
    group: int | None
    n_valid: int
    n_runs: int
    taus_s: tuple[int, ...]
    sigma_y: tuple[float, ...]
    fit_slope: float | None
    fit_intercept: float | None
    u_fractional: float | None
    status: Literal["established", "supported-with-limitations", "pending-verification"]
```

- [ ] **Step 5: 实现估计规则**

调用 `tidal_stability.oadev(times, y, taus)`。拟合点必须满足 `fit_min_s <= tau <= duration*fit_max_fraction` 且至少 3 点；不足 3 点时令 `u_fractional=None` 并返回 `supported-with-limitations`，由场景组合层拒绝把该段静默纳入权威组合。保留旧 block 算法输出为 comparison 字段或审计差异，不再把它命名为 OADEV。

- [ ] **Step 6: 将 statistical_methods 的计算与 I/O 分离**

增加纯接口：

```python
def analyze_raw_statistics(
    segments: Sequence[SelectedSegment],
    ratios: Mapping[int, Decimal],
    config: StabilityFitConfig,
) -> tuple[tuple[SegmentUncertainty, ...], CombinationResult]: ...
```

`main()` 只负责加载、调用和写出兼容 CSV/JSON。

- [ ] **Step 7: 运行合成和旧结果差异测试**

Run:

```bash
uv run pytest -q \
  clock_ratio/test_segment_uncertainty.py \
  clock_ratio/test_tidal_outputs.py \
  clock_ratio/test_statistical_combination.py
```

Expected: 新 OADEV 合成测试通过；旧算法差异被显式记录，不能把预期 30–40% 变化当成回归失败直接忽略。

- [ ] **Step 8: 提交**

```bash
git add clock_ratio/segment_uncertainty.py clock_ratio/test_segment_uncertainty.py clock_ratio/tidal_stability.py clock_ratio/statistical_methods.py
git commit -m "feat: estimate gap-safe segment uncertainty"
```

---

### Task 10: 统一 raw/tidal 场景、16/17 段与 leave-one-out

**Files:**
- Create: `clock_ratio/statistical_scenarios.py`
- Create: `clock_ratio/test_statistical_scenarios.py`
- Modify: `clock_ratio/statistical_methods_tidal.py:46-200`
- Modify: `clock_ratio/statistical_methods_tidal_seg9.py:36-100`

**Interfaces:**
- Consumes: `SelectedSegment`、`TideGrid`、`Scenario`、`SegmentUncertainty`、`combine_estimates()`。
- Produces: `StatisticalScenarioResult`、`StatisticalSynthesis`、`analyze_scenario()`、`analyze_scenarios()`、`exclude_groups()`、`leave_one_out()`。

- [ ] **Step 1: 写 membership 和完整性测试**

```python
def test_excluding_group_9_produces_declared_primary_16(full_result):
    primary = exclude_groups(full_result, frozenset({9}))
    assert primary.included_groups == tuple(g for g in range(1, 18) if g != 9)
    assert primary.excluded_groups == (9,)
    assert primary.combination.n == 16


def test_leave_one_out_covers_each_group_once(full_result):
    results = leave_one_out(full_result)
    assert set(results) == set(range(1, 18))
    assert all(len(r.included_groups) == 16 for r in results.values())
```

加入重复 group、缺 ratio、缺 uncertainty、非有限值立即失败测试。

- [ ] **Step 2: 写 raw 路径一致性测试**

对同一 synthetic segments，`analyze_scenario(raw)` 与 raw-only 入口逐字段一致，Decimal ratio 不经过 float round-trip。

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_statistical_scenarios.py -v`

Expected: FAIL with missing module。

- [ ] **Step 4: 创建类型**

```python
@dataclass(frozen=True, slots=True)
class ScenarioSegmentResult:
    group: int
    ratio: Decimal
    deviation: float
    uncertainty: SegmentUncertainty
    n_valid: int

@dataclass(frozen=True, slots=True)
class StatisticalScenarioResult:
    scenario: Literal["raw", "theory", "empirical"]
    coefficient: float
    included_groups: tuple[int, ...]
    excluded_groups: tuple[int, ...]
    segments: tuple[ScenarioSegmentResult, ...]
    combination: CombinationResult
    duration_weighted_ratio: Decimal
    total_samples: int
```

- [ ] **Step 5: 实现场景与排除函数**

`analyze_scenario()` 在实际保留 `segment.times` 上调用 `TideGrid.beat_at()`；`exclude_groups()` 从已有逐段结果重算组合和时长权重；`leave_one_out()` 对每个 group 调用通用排除，不读取预先生成 JSON。

- [ ] **Step 6: 将两个旧脚本改为兼容 CLI**

`statistical_methods_tidal.py` 调用 `analyze_scenarios()`；`statistical_methods_tidal_seg9.py` 调用 `exclude_groups(...,{9})` 并同时可选写出完整 LOO。保留旧文件名，避免现有工作流断裂。

- [ ] **Step 7: 测试**

Run:

```bash
uv run pytest -q \
  clock_ratio/test_statistical_scenarios.py \
  clock_ratio/test_tidal_report.py \
  clock_ratio/test_statistical_combination.py
```

Expected: PASS；16 段、17 段和 17 个 LOO 均由同一逐段事实重算。

- [ ] **Step 8: 提交**

```bash
git add clock_ratio/statistical_scenarios.py clock_ratio/test_statistical_scenarios.py clock_ratio/statistical_methods_tidal.py clock_ratio/statistical_methods_tidal_seg9.py
git commit -m "feat: unify statistical scenarios and sensitivity"
```

---

### Task 11: 建立可审计不确定度预算

**Files:**
- Modify: `clock_ratio/evidence.py`
- Create: `clock_ratio/uncertainty_budget.py`
- Create: `clock_ratio/test_uncertainty_budget.py`

**Interfaces:**
- Consumes: 统计不确定度、Yb/Sr 系统项、链路、光梳、水准和潮汐项及其证据状态。
- Produces: `BudgetComponent`、`CovarianceModel`、`UncertaintyBudget`、`combine_uncertainty_budget()`。

- [ ] **Step 1: 写 correction 与 uncertainty 分离测试**

```python
def test_budget_preserves_correction_and_uncertainty_as_distinct_fields():
    component = BudgetComponent(
        name="sr-systematic",
        correction=Decimal("-2.3e-18"),
        standard_uncertainty=Decimal("9.2e-19"),
        source="params.json + experimental record",
        status=EvidenceStatus.established,
        required=True,
    )
    assert component.correction == Decimal("-2.3e-18")
    assert component.standard_uncertainty == Decimal("9.2e-19")
```

- [ ] **Step 2: 写相关预算和未决项门测试**

```python
def test_correlated_budget_uses_covariance_matrix():
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, 0.5], [0.5, 1.0]])
    result = combine_uncertainty_budget(components, correlation)
    expected = Decimal(str(np.sqrt(1.0 + 4.0 + 2.0))) * Decimal("1e-18")
    assert float(result.total_standard_uncertainty) == pytest.approx(float(expected), rel=1e-15)


def test_required_pending_component_blocks_final_total():
    components = (
        established_component("statistical", "7.5e-19"),
        pending_component("yb-systematic", required=True),
    )
    result = combine_uncertainty_budget(components, np.eye(2))
    assert result.total_standard_uncertainty is None
    assert result.known_quadrature is not None
    assert result.status is EvidenceStatus.pending_verification
```

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_uncertainty_budget.py -v`

Expected: FAIL with missing module。

- [ ] **Step 4: 创建预算类型**

```python
from clock_ratio.evidence import EvidenceStatus

@dataclass(frozen=True, slots=True)
class BudgetComponent:
    name: str
    correction: Decimal | None
    standard_uncertainty: Decimal | None
    source: str
    status: EvidenceStatus
    required: bool

@dataclass(frozen=True, slots=True)
class UncertaintyBudget:
    components: tuple[BudgetComponent, ...]
    correlation: tuple[tuple[float, ...], ...]
    known_quadrature: Decimal
    total_standard_uncertainty: Decimal | None
    status: EvidenceStatus
```

在 `clock_ratio/evidence.py` 中唯一地定义 `EvidenceStatus`；预算与 manifest 模块都从这里导入，禁止重复 enum。

- [ ] **Step 5: 实现预算验证和合成**

`combine_uncertainty_budget()` 必须验证：组件名唯一；uncertainty 非负；相关矩阵有限、对称、对角为 1、半正定且维度匹配。已知分量按 `sqrt(uᵀCu)` 合成；任一 `required=True` 分量不是 established 或其 uncertainty 为 `None` 时，最终总量为 `None`，但同时给出已知分量 quadrature。

- [ ] **Step 6: 编码当前证据冲突，不替实验方决策**

构建阶段一预算输入时：统计项来自新分析；Sr、静态势差等只在来源闭合时 established；Yb 的 `1.1e-18` 与已发表 `1.3e-18` 作为两个冲突证据记录，使 Yb 预算项保持 pending；链路、光梳、水准和潮汐残余缺可执行证据时同样保持 pending。不得输出最终 `2e-18` 总量。

- [ ] **Step 7: 测试并提交**

```bash
uv run pytest -q clock_ratio/test_uncertainty_budget.py
git add clock_ratio/evidence.py clock_ratio/uncertainty_budget.py clock_ratio/test_uncertainty_budget.py
git commit -m "feat: model auditable uncertainty budget"
```

---

### Task 12: 增加潮汐协方差感知推断验证

**Files:**
- Modify: `clock_ratio/windowing.py`
- Create: `clock_ratio/test_tidal_inference.py`
- Modify: `clock/segment_analysis/batch_analysis.py:275-323`

**Interfaces:**
- Consumes: 每段窗口化 beat/tide、段边界和固定 RNG seed。
- Produces: `CovarianceAwareFit`、`fit_gls_amplitude()`、`block_bootstrap_amplitude()`；保留基准非重叠窗结果。

- [ ] **Step 1: 写自相关覆盖率合成测试**

生成 AR(1) noise + 已知潮汐响应；固定 200 个 seed，比较 naive OLS 与候选方法的 95% CI 覆盖率。测试要求候选方法覆盖率位于 `[0.90,0.99]`，且不低于 naive 方法。

```python
def test_block_bootstrap_has_reasonable_coverage_for_ar1_noise():
    covered = 0
    for seed in range(200):
        times, beat, tide = synthetic_ar1_response(seed=seed, amplitude=-0.6)
        fit = block_bootstrap_amplitude(
            times, beat, tide, block_size=1200, n_resamples=500, seed=seed
        )
        covered += fit.ci_low <= -0.6 <= fit.ci_high
    assert 0.90 <= covered / 200 <= 0.99
```

为保持测试时间可控，可把 CI 仿真标记为 `@pytest.mark.slow`，快速测试另用 20 seed 检查确定性和区间有序性。

- [ ] **Step 2: 写重叠窗有效自由度测试**

断言正式推断使用的观测数不是重叠点总数；GLS 协方差矩阵维度和对称正定性被验证。

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_tidal_inference.py -v`

Expected: FAIL with missing functions。

- [ ] **Step 4: 实现候选推断类型**

```python
@dataclass(frozen=True, slots=True)
class CovarianceAwareFit:
    amplitude: float
    standard_error: float
    ci_low: float
    ci_high: float
    method: Literal["nonoverlap-ols", "gls", "block-bootstrap"]
    n_windows: int
    effective_n: float
```

实现至少一个通过合成覆盖率门的协方差感知方法；非重叠 1200 s 基准结果继续保留。block bootstrap 必须按连续 run 分块，不跨越时间缺口或段边界。

- [ ] **Step 5: 在 batch 聚合中并列输出方法**

保留当前 1200/600 点估计和非重叠推断字段，新增 covariance-aware CI、方法名和有效样本数。不得删除旧结果；报告新旧差异。

- [ ] **Step 6: 跑快速和慢速测试**

Run:

```bash
uv run pytest -q clock_ratio/test_tidal_inference.py -m "not slow"
uv run pytest -q clock_ratio/test_tidal_inference.py -m slow
```

Expected: 两者 PASS。若 GLS 与 bootstrap 均不满足覆盖率门，保留结果为诊断，潮汐显著性状态设为 `supported-with-limitations`，不得挑选给出最大 σ 的方法。

- [ ] **Step 7: 提交**

```bash
git add clock_ratio/windowing.py clock_ratio/test_tidal_inference.py clock/segment_analysis/batch_analysis.py
git commit -m "feat: validate covariance-aware tidal inference"
```

---

### Task 13: 建立权威结果 manifest 与哈希校验

**Files:**
- Create: `clock_ratio/result_manifest.py`
- Create: `clock_ratio/build_result_manifest.py`
- Create: `clock_ratio/verify_result_manifest.py`
- Create: `clock_ratio/test_result_manifest.py`

**Interfaces:**
- Consumes: sample ledger、time quality、潮汐转换差异、16/17/LOO 场景、统计结果、Git 和环境信息。
- Produces: `results/audit-v1/manifest.json`、`read_manifest()`、`reconcile_manifest()`、`write_manifest_atomic()`。

- [ ] **Step 1: 写 schema 和篡改测试**

```python
def test_manifest_rejects_duplicate_or_wrong_membership(valid_manifest):
    broken = valid_manifest.model_copy(
        update={"primary_16": valid_manifest.primary_16.model_copy(
            update={"included_groups": tuple(range(1, 17))}
        )}
    )
    with pytest.raises(ManifestError):
        reconcile_manifest(broken)


def test_manifest_detects_tampered_input(valid_manifest, tmp_path):
    input_path = tmp_path / "input.csv"
    input_path.write_text("changed", encoding="utf-8")
    with pytest.raises(ManifestError, match="sha256"):
        verify_input_hashes(valid_manifest, root=tmp_path)
```

- [ ] **Step 2: 写原子写入和字节稳定测试**

同一模型两次序列化字节完全一致；运行时间放在独立 run metadata，不进入可比较 scientific payload。模拟 `os.replace` 前异常时旧 manifest 保持不变。

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_result_manifest.py -v`

Expected: FAIL with missing module。

- [ ] **Step 4: 创建 Pydantic schema**

```python
from clock_ratio.evidence import EvidenceStatus

class ProvenanceRecord(BaseModel):
    relative_path: str
    sha256: str
    size_bytes: int
    mtime_utc: datetime
    provider: str | None
    command: tuple[str, ...]
    distributable: bool | None
    status: EvidenceStatus

class ResultManifest(BaseModel):
    schema_version: Literal["1.0"]
    git_commit: str
    dirty: bool
    python: str
    packages: dict[str, str]
    inputs: tuple[ProvenanceRecord, ...]
    parameters: ProvenanceRecord
    parameter_ledger_sha256: str
    sample_ledger_sha256: str
    primary_16: StatisticalScenarioManifest
    sensitivity_17: StatisticalScenarioManifest
    leave_one_out: dict[int, StatisticalScenarioManifest]
    tide_method: TideMethodManifest
    uncertainty_budget: UncertaintyBudgetModel
    commands: tuple[str, ...]
```

`StatisticalScenarioManifest` 和 `TideMethodManifest` 显式列字段，不使用 `dict[str, Any]` 存科学结果。

- [ ] **Step 5: 实现 reconcile 规则**

必须检查：

- primary groups 正好是 1–17 去掉 9；
- sensitivity groups 正好是 1–17；
- LOO key 正好是 1–17，每项只排除对应 group；
- 样本总数等于段之和；
- duration-weighted 中心按段 `n_valid` 重算一致；
- 所有 float 有限；
- pending/external 字段允许 `null`，established 必填；
- 输入、参数、账本和分析产物哈希一致。

- [ ] **Step 6: 实现 CLI 和原子写入**

`build_result_manifest` 从指定 staging 目录读取强 schema 产物；缺任何权威输入立即非零退出。`write_manifest_atomic()` 写同目录临时文件、flush、`os.fsync` 后 `os.replace`。

- [ ] **Step 7: 测试**

Run: `uv run pytest -q clock_ratio/test_result_manifest.py`

Expected: PASS。

- [ ] **Step 8: 提交**

```bash
git add clock_ratio/result_manifest.py clock_ratio/build_result_manifest.py clock_ratio/verify_result_manifest.py clock_ratio/test_result_manifest.py
git commit -m "feat: add authoritative analysis manifest"
```

---

### Task 14: 建立 audit fail-fast staging/promote 工作流

**Files:**
- Modify: `run_all.py:34-93`
- Modify: `clock_ratio/test_tidal_report.py:158-191`

**Interfaces:**
- Consumes: 各分析 CLI 和 manifest builder。
- Produces: `Step`、`RunSummary`、`select_steps(mode)`、`run_steps()`、`promote_run()`；CLI `--mode audit --output-dir results/audit-v1`。

- [ ] **Step 1: 替换旧默认继续测试，增加事务测试**

```python
def test_audit_stops_on_first_failure_and_preserves_verified(tmp_path, monkeypatch):
    verified = tmp_path / "verified"
    verified.mkdir()
    old = verified / "manifest.json"
    old.write_text('{"old": true}', encoding="utf-8")
    summary = run_steps(failing_steps(), tmp_path / "staging", fail_fast=True)
    assert not summary.success
    assert old.read_text(encoding="utf-8") == '{"old": true}'
    assert not (tmp_path / "staging" / "manifest.json").exists()
```

再写：subprocess 返回 0 但缺声明输出时失败；全部成功后一次 promote；legacy 可 continue 但不得生成 audit manifest。

- [ ] **Step 2: 运行测试确认旧 audit 接口失败**

Run: `uv run pytest clock_ratio/test_tidal_report.py -k "audit or promote" -v`

Expected: FAIL with missing interface。

- [ ] **Step 3: 创建步骤类型**

```python
@dataclass(frozen=True, slots=True)
class Step:
    name: str
    command: tuple[str, ...]
    outputs: tuple[Path, ...]

@dataclass(frozen=True, slots=True)
class RunSummary:
    success: bool
    completed: tuple[str, ...]
    failed_step: str | None
    staging_dir: Path
```

`select_steps("audit")` 顺序固定为：样本账本、参数账本、潮汐转换比较、比值、潮汐场景、段不确定度、敏感性、不确定度预算、manifest 构建、manifest 验证。

- [ ] **Step 4: 实现 staging 和输出验证**

每个 step 通过 CLI 参数写入唯一 staging run 目录。子进程非零或缺任一声明输出立即停止。禁止 audit step 读取 verified 目录中的旧分析产物作为替代。

- [ ] **Step 5: 实现原子 promote**

成功验证 manifest 后，把 staging 重命名为带 manifest hash 的 run 目录，再原子更新 `results/audit-v1/verified` 指针或目录。不得删除旧 verified run；保留可回滚历史。

- [ ] **Step 6: 保留显式 legacy 模式**

旧默认步骤放在 `--mode legacy`；其 continue-on-error 行为可以保留，但输出不得被 manifest builder 接受。`--tidal-only` 兼容映射为显式 `tidal` 模式。

- [ ] **Step 7: 测试**

Run: `uv run pytest -q clock_ratio/test_tidal_report.py`

Expected: PASS；audit fail-fast，legacy 隔离。

- [ ] **Step 8: 提交**

```bash
git add run_all.py clock_ratio/test_tidal_report.py
git commit -m "feat: run audit pipeline transactionally"
```

---

### Task 15: 生成 manifest-only 审计报告并完成阶段一验证

**Files:**
- Create: `clock_ratio/audit_report.py`
- Create: `clock_ratio/test_audit_report.py`
- Modify: `docs/WORKFLOW.md:32-165`
- Modify: `README.md:253-286`

**Interfaces:**
- Consumes: verified `ResultManifest`。
- Produces: `results/audit-v1/verified/ANALYSIS_AUDIT.md`、阶段一复现命令和差异清单。

- [ ] **Step 1: 写报告完全由 manifest 驱动的测试**

```python
def test_report_changes_when_manifest_value_changes(valid_manifest):
    first = render_audit_report(valid_manifest)
    changed = replace_primary_chi2(valid_manifest, valid_manifest.primary_16.combination.chi2_red + 1)
    second = render_audit_report(changed)
    assert first != second
    assert format(changed.primary_16.combination.chi2_red, ".3f") in second


def test_report_requires_primary_sensitivity_and_loo(valid_manifest):
    broken = valid_manifest.model_copy(update={"leave_one_out": {}})
    with pytest.raises(ManifestError):
        render_audit_report(broken)
```

- [ ] **Step 2: 增加旧硬编码数字禁入测试**

报告模块源代码不得出现 `5.42`、`3.70`、`4.56`、`6.4`、`31.8%` 等历史结果字面量。测试读取 `audit_report.py` 源文并断言这些 token 不存在。

- [ ] **Step 3: 运行测试确认失败**

Run: `uv run pytest clock_ratio/test_audit_report.py -v`

Expected: FAIL with missing module。

- [ ] **Step 4: 实现纯渲染和原子写入**

```python
def read_audit_inputs(manifest_path: Path) -> ResultManifest:
    manifest = read_manifest(manifest_path)
    reconcile_manifest(manifest)
    return manifest


def render_audit_report(manifest: ResultManifest) -> str:
    reconcile_manifest(manifest)
    return "\n".join(render_sections(manifest))


def write_report_atomic(text: str, path: Path) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
```

报告固定包含：输入/provenance 状态、样本账本、时间质量、16 段主结果、17 段敏感性、完整 LOO、潮汐方法验证、协方差感知结果、不确定度方法、新旧结果差异、外部确认项和证据状态。

- [ ] **Step 5: 更新工作流文档**

`docs/WORKFLOW.md` 把以下命令标为阶段一权威入口：

```bash
uv sync --extra test
uv run pytest -q
RUN_CLOCK_DATA_TESTS=1 uv run pytest -q
uv run python run_all.py --mode audit --output-dir results/audit-v1
uv run python -m clock_ratio.verify_result_manifest results/audit-v1/verified/manifest.json
uv run python -m clock_ratio.audit_report --manifest results/audit-v1/verified/manifest.json
```

旧命令移动到“Legacy diagnostics”，明确不能生成权威 manifest。

- [ ] **Step 6: 更新 README 阶段状态**

README 说明：当前主结果为第 9 段隔离后的 16 段临时主结果；17 段和 LOO 是敏感性结果；专业潮汐输入的物理模型来源尚需外部确认。不得把运行过程中得到的数值手写进 README，改为链接 manifest 和审计报告。

- [ ] **Step 7: 运行全部快速测试**

Run: `uv run pytest -q`

Expected: PASS；记录测试总数和耗时。

- [ ] **Step 8: 运行全部真实数据测试**

Run: `RUN_CLOCK_DATA_TESTS=1 uv run pytest -q`

Expected: PASS；若有外部输入缺失，相关测试只能明确标记 limitation，不得把数据错误转换为 skip。

- [ ] **Step 9: 从空 staging 执行 audit pipeline**

Run:

```bash
verification_dir="results/audit-v1/verification-$(date -u +%Y%m%dT%H%M%SZ)"
uv run python run_all.py --mode audit --output-dir "$verification_dir"
uv run python -m clock_ratio.verify_result_manifest \
  "$verification_dir/verified/manifest.json"
uv run python -m clock_ratio.audit_report \
  --manifest "$verification_dir/verified/manifest.json"
```

Expected: 所有命令退出 0；verified manifest 和报告由本次 run 产生；Git 跟踪的历史结果和 `paper/` 未改变。

- [ ] **Step 10: 检查禁止修改范围**

Run:

```bash
git diff --name-only $(git merge-base HEAD main)..HEAD -- paper/ archive/
```

Expected: 无输出。

- [ ] **Step 11: 人工核验阶段一放行清单**

逐项确认并在 `ANALYSIS_AUDIT.md` 中记录：

- 1,008,912 的逐段和总数闭合；
- 1,009,022 与 1,009,204 被列为外部待对账口径；
- 第 9 段没有从数据或敏感性结果中消失；
- 16/17 段和 17 个 LOO 均存在；
- 原标签和均匀轴差异已量化；
- 潮汐 Excel→CSV 比较有明确结果；
- 三角窗已用合成信号验证；
- 正式潮汐区间处理重叠协方差或明确 limitation；
- 新旧 OADEV/不确定度差异已解释；
- 所有 manifest 哈希通过；
- 没有论文文件变化。

- [ ] **Step 12: 提交文档和报告生成器**

```bash
git add clock_ratio/audit_report.py clock_ratio/test_audit_report.py docs/WORKFLOW.md README.md
git commit -m "docs: publish reproducible analysis audit workflow"
```

- [ ] **Step 13: 请求阶段一代码审查**

使用 `superpowers:requesting-code-review` 审查相对本计划起点的全部变更，重点检查科学正确性、单位、时间、符号、数据泄露和 staging 原子性。修复确认问题后重新运行 Steps 7–10。

- [ ] **Step 14: 向用户提交阶段一验收包**

只报告经验证的：

- verified manifest 路径与哈希；
- 16 段临时主结果；
- 17 段和 LOO 敏感性；
- 潮汐方法验证结论；
- 新旧结果差异；
- 尚需实验团队确认的输入；
- 测试命令和实际通过数。

等待用户明确审核阶段一结果；在此之前不得启动论文修改计划。
