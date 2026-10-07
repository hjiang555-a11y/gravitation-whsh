#!/usr/bin/env python3
"""One-command analysis pipeline for the Wuhan-Shanghai clock comparison.

Runs every analysis step in dependency order (each step reads the CSVs produced
by earlier steps), then regenerates the authoritative report. With new
experimental data (new beat files + params.json entries), running this single
script reproduces the full analysis and report.
Use --tidal-only for just the independent tidal analysis/report (fail-fast).
Use --mode audit for the transactional audit pipeline: every step writes into
results/audit-v1/staging, any failure stops the run before promote, and a fully
verified run is atomically renamed into results/audit-v1/runs/<manifest hash>
with results/audit-v1/verified pointing at it (old runs are never deleted).
Use --help to show options without starting any analysis.

Steps (all in the repo, run via subprocess so each keeps its own main):
  1. clock_ratio/compute_ratio.py          -> ratio_17seg.csv (per-segment ratio)
  2. clock/clock_tidal_shift.py            -> clock_tidal_shift.csv (tidal Δf/f)
  3. clock/segment_analysis/batch_analysis.py -> batch_summary.csv (within-seg + aggregate)
  4. clock_ratio/correlation_reanalysis.py -> correlation_reanalysis.csv (seg-mean corr)
  5. clock_ratio/correlation_reanalysis_timeweighted.py -> correlation_reanalysis_timeweighted.csv (time-weighted corr)
  6. clock/correlation_analysis.py         -> correlation.png (y_i vs Δf/f)
  7. clock_ratio/make_report_figures.py    -> ratio_segments.png (report figure)
  8. variants / single-segment diagnostics (appendix figures)
  9. clock_ratio/make_report.py            -> EXPERIMENT_REPORT.md (authoritative report)
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Final

import typer

REPO = Path(__file__).resolve().parent
app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)
TIDAL_STEPS: Final = [
    ("独立潮汐修正", REPO / "clock_ratio" / "tidal_correction.py"),
    ("独立潮汐报告", REPO / "clock_ratio" / "make_tidal_report.py"),
]

STEPS = [
    ("逐段钟比值", REPO / "clock_ratio" / "compute_ratio.py"),
    ("潮汐频移", REPO / "clock" / "clock_tidal_shift.py"),
    ("段内拟合+跨段合并", REPO / "clock" / "segment_analysis" / "batch_analysis.py"),
    ("段均值相关", REPO / "clock_ratio" / "correlation_reanalysis.py"),
    ("段均值相关（时间等权重）", REPO / "clock_ratio" / "correlation_reanalysis_timeweighted.py"),
    ("段均值相关·剔除段9(附加)", REPO / "clock_ratio" / "correlation_reanalysis_seg9_excluded.py"),
    ("段均值相关·剔除段9(完全独立重算)", REPO / "clock_ratio" / "correlation_reanalysis_seg9_independent.py"),
    ("段均值相关图", REPO / "clock" / "correlation_analysis.py"),
    ("报告插图", REPO / "clock_ratio" / "make_report_figures.py"),
    ("变体1（潮汐30s原生）", REPO / "clock" / "segment_analysis" / "variant1_30s_tide.py"),
    ("变体2（30s均值聚合）", REPO / "clock" / "segment_analysis" / "variant30s_analysis.py"),
    ("段13多τ相关", REPO / "clock" / "segment13_correlation.py"),
    ("段13三角窗", REPO / "clock" / "segment_analysis" / "segment13_triangular.py"),
    ("段6三角窗", REPO / "clock" / "segment_analysis" / "segment6_triangular.py"),
    ("论文统计方法(OADEV+WLS/Birge/M-P/贝叶斯)", REPO / "clock_ratio" / "statistical_methods.py"),
    ("论文统计方法·潮汐修正重算", REPO / "clock_ratio" / "statistical_methods_tidal.py"),
    ("段9剔除敏感性(附加)", REPO / "clock_ratio" / "statistical_methods_tidal_seg9.py"),
    ("拼接稳定度(保留真实间断)", REPO / "clock_ratio" / "concatenated_stability.py"),
    ("拼接稳定度(端到端附加视角)", REPO / "clock_ratio" / "concatenated_stability_long.py"),
    ("论文配图(附加)", REPO / "clock_ratio" / "make_paper_figures.py"),
    *TIDAL_STEPS,
    ("自动报告", REPO / "clock_ratio" / "make_report.py"),
]

STAGING: Final = REPO / "results" / "audit-v1" / "staging"


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


def _inline(code: str) -> tuple[str, ...]:
    return (sys.executable, "-c", code)


def audit_steps(staging: Path, output_dir: Path) -> list[Step]:
    staging = Path(staging)
    tide_dir = staging / "tide-conversion"
    tidal_json = staging / "statistical_methods_tidal.json"
    seg9_json = staging / "statistical_methods_tidal_seg9_excluded.json"
    ratio_code = (
        "import clock_ratio.compute_ratio as m; "
        "from pathlib import Path; "
        f"m.OUT_DIR = Path({str(staging)!r}); "
        "raise SystemExit(m.main())"
    )
    tidal_code = (
        "import clock_ratio.statistical_methods_tidal as m; "
        "from pathlib import Path; "
        f"m.JSON_PATH = Path({str(tidal_json)!r}); "
        "raise SystemExit(m.main())"
    )
    methods_code = (
        "import clock_ratio.statistical_methods as m; "
        "from pathlib import Path; "
        f"m.OUT_DIR = Path({str(staging)!r}); "
        "raise SystemExit(m.main())"
    )
    seg9_code = (
        "import clock_ratio.statistical_methods_tidal_seg9 as m; "
        "from pathlib import Path; "
        f"m.SOURCE_JSON = Path({str(tidal_json)!r}); "
        f"m.JSON_PATH = Path({str(seg9_json)!r}); "
        "raise SystemExit(m.main())"
    )
    return [
        Step(
            "样本账本",
            (sys.executable, str(REPO / "clock" / "build_sample_ledger.py"), "--output-dir", str(staging)),
            (staging / "sample_ledger.csv", staging / "time_quality.json"),
        ),
        Step(
            "参数账本",
            (sys.executable, str(REPO / "clock" / "build_parameter_ledger.py"), "--output-dir", str(staging)),
            (staging / "parameter_ledger.csv", staging / "parameter_conflicts.json"),
        ),
        Step(
            "潮汐转换比较",
            (sys.executable, str(REPO / "clock_ratio" / "tide_conversion.py"), "--output-dir", str(tide_dir), "--tolerate-mismatch"),
            (tide_dir / "professional_tidal_delta_30s.csv", tide_dir / "professional_tidal_delta_30s.diff.json"),
        ),
        Step(
            "比值",
            _inline(ratio_code),
            (staging / "ratio_17seg.csv", staging / "ratio_17seg_summary.csv"),
        ),
        Step(
            "潮汐场景",
            _inline(tidal_code),
            (tidal_json,),
        ),
        Step(
            "段不确定度",
            _inline(methods_code),
            (staging / "statistical_methods.csv", staging / "statistical_methods.json"),
        ),
        Step(
            "敏感性",
            _inline(seg9_code),
            (seg9_json,),
        ),
        Step(
            "manifest 构建",
            (sys.executable, "-m", "clock_ratio.build_result_manifest", "--staging", str(staging), "--command", "python run_all.py --mode audit"),
            (staging / "manifest.json",),
        ),
        Step(
            "manifest 验证",
            (sys.executable, "-m", "clock_ratio.verify_result_manifest", str(staging / "manifest.json")),
            (),
        ),
    ]


def select_steps(
    mode: str,
    *,
    staging_root: Path | None = None,
    output_dir: Path | None = None,
) -> list[Step]:
    """Keep legacy order by default; isolate tidal or the transactional audit lane."""
    if mode == "audit":
        staging = staging_root if staging_root is not None else STAGING
        root = output_dir if output_dir is not None else REPO / "results" / "audit-v1"
        return audit_steps(staging, root)
    if mode == "legacy":
        scripts = STEPS
    elif mode == "tidal":
        scripts = TIDAL_STEPS
    else:
        raise ValueError(f"unknown mode: {mode!r}")
    return [Step(name, (sys.executable, str(script)), ()) for name, script in scripts]


def run_steps(steps: tuple[Step, ...] | list[Step], staging_dir: Path, *, fail_fast: bool) -> RunSummary:
    completed: list[str] = []
    failed: str | None = None
    for step in steps:
        print(f"\n===== [{step.name}] =====", flush=True)
        result = subprocess.run(list(step.command), cwd=REPO)
        missing = any(not Path(out).exists() for out in step.outputs)
        if result.returncode != 0 or missing:
            print(f"  ✗ {step.name} 失败 (exit {result.returncode})", file=sys.stderr)
            if failed is None:
                failed = step.name
            if fail_fast:
                return RunSummary(False, tuple(completed), step.name, staging_dir)
        else:
            completed.append(step.name)
            print(f"  ✓ {step.name} 完成")
    return RunSummary(failed is None, tuple(completed), failed, staging_dir)


def promote_run(staging_dir: Path, *, output_dir: Path) -> Path:
    digest = hashlib.sha256((staging_dir / "manifest.json").read_bytes()).hexdigest()
    run_dir = output_dir / "runs" / digest[:16]
    if not run_dir.exists():
        run_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging_dir, run_dir)
    verified = output_dir / "verified"
    if verified.exists() and not verified.is_symlink():
        raise ValueError("verified pointer is a directory; refusing to replace")
    pointer = output_dir / "verified.tmp"
    pointer.unlink(missing_ok=True)
    pointer.symlink_to(os.path.relpath(run_dir, output_dir))
    os.replace(pointer, verified)
    return run_dir


def run_audit(output_dir: Path) -> int:
    steps = select_steps("audit", output_dir=output_dir)
    summary = run_steps(steps, STAGING, fail_fast=True)
    if not summary.success:
        print(f"审计失败，未 promote；失败步骤: {summary.failed_step}", file=sys.stderr)
        return 1
    run_dir = promote_run(STAGING, output_dir=output_dir)
    print(f"verified -> {output_dir / 'verified'}")
    print(f"run -> {run_dir}")
    return 0


def main(tidal_only: bool = False) -> int:
    mode = "tidal" if tidal_only else "legacy"
    summary = run_steps(select_steps(mode), REPO / "results", fail_fast=(mode == "tidal"))
    if not summary.success:
        print(f"\n失败步骤: {[summary.failed_step]}", file=sys.stderr)
        return 1
    report = "clock_ratio/tidal_correction/REPORT.md" if tidal_only else "clock_ratio/EXPERIMENT_REPORT.md"
    print(f"\n全部步骤完成。报告见 {report}")
    return 0


@app.command()
def cli(
    tidal_only: Annotated[bool, typer.Option("--tidal-only", help="Run only tidal analysis and its report; stop on the first failure.")] = False,
    mode: Annotated[str, typer.Option("--mode", help="legacy | tidal | audit")] = "legacy",
    output_dir: Annotated[Path, typer.Option("--output-dir", help="Audit result root (runs/ and verified).")] = REPO / "results" / "audit-v1",
) -> None:
    """Run all legacy steps plus tidal comparison, just the independent tidal lane, or the audit lane."""
    resolved = "tidal" if tidal_only else mode
    if resolved == "audit":
        raise typer.Exit(code=run_audit(output_dir))
    raise typer.Exit(code=main(resolved == "tidal"))


if __name__ == "__main__":
    app()
