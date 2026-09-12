#!/usr/bin/env python3
"""One-command analysis pipeline for the Wuhan-Shanghai clock comparison.

Runs every analysis step in dependency order (each step reads the CSVs produced
by earlier steps), then regenerates the authoritative report. With new
experimental data (new beat files + params.json entries), running this single
script reproduces the full analysis and report.
Use --tidal-only for just the independent tidal analysis/report (fail-fast).
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

import subprocess
import sys
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
    ("段均值相关图", REPO / "clock" / "correlation_analysis.py"),
    ("报告插图", REPO / "clock_ratio" / "make_report_figures.py"),
    ("变体1（潮汐30s原生）", REPO / "clock" / "segment_analysis" / "variant1_30s_tide.py"),
    ("变体2（30s均值聚合）", REPO / "clock" / "segment_analysis" / "variant30s_analysis.py"),
    ("段13多τ相关", REPO / "clock" / "segment13_correlation.py"),
    ("段13三角窗", REPO / "clock" / "segment_analysis" / "segment13_triangular.py"),
    ("段6三角窗", REPO / "clock" / "segment_analysis" / "segment6_triangular.py"),
    ("论文统计方法(OADEV+WLS/Birge/M-P/贝叶斯)", REPO / "clock_ratio" / "statistical_methods.py"),
    *TIDAL_STEPS,
    ("自动报告", REPO / "clock_ratio" / "make_report.py"),
]


def select_steps(tidal_only: bool) -> list[tuple[str, Path]]:
    """Keep legacy order by default; isolate the two additive steps when requested."""
    return list(TIDAL_STEPS if tidal_only else STEPS)


def main(tidal_only: bool = False) -> int:
    failed: list[str] = []
    for name, script in select_steps(tidal_only):
        print(f"\n===== [{name}] {script.name} =====", flush=True)
        r = subprocess.run([sys.executable, str(script)], cwd=REPO)
        if r.returncode != 0:
            print(f"  ✗ {name} 失败 (exit {r.returncode})", file=sys.stderr)
            failed.append(name)
            if tidal_only:
                return 1
        else:
            print(f"  ✓ {name} 完成")
    if failed:
        print(f"\n失败步骤: {failed}", file=sys.stderr)
        return 1
    report = "clock_ratio/tidal_correction/REPORT.md" if tidal_only else "clock_ratio/EXPERIMENT_REPORT.md"
    print(f"\n全部步骤完成。报告见 {report}")
    return 0


@app.command()
def cli(tidal_only: Annotated[bool, typer.Option("--tidal-only", help="Run only tidal analysis and its report; stop on the first failure.")] = False) -> None:
    """Run all legacy steps plus tidal comparison, or just the independent tidal lane."""
    raise typer.Exit(code=main(tidal_only))


if __name__ == "__main__":
    app()
