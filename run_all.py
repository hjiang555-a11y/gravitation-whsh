#!/usr/bin/env python3
"""One-command analysis pipeline for the Wuhan-Shanghai clock comparison.

Runs every analysis step in dependency order (each step reads the CSVs produced
by earlier steps), then regenerates the authoritative report. With new
experimental data (new beat files + params.json entries), running this single
script reproduces the full analysis and report.

Steps (all in the repo, run via subprocess so each keeps its own main):
  1. clock_ratio/compute_ratio.py          -> ratio_17seg.csv (per-segment ratio)
  2. clock/clock_tidal_shift.py            -> clock_tidal_shift.csv (tidal Δf/f)
  3. clock/segment_analysis/batch_analysis.py -> batch_summary.csv (within-seg + aggregate)
  4. clock_ratio/correlation_reanalysis.py -> correlation_reanalysis.csv (seg-mean corr)
  5. clock/correlation_analysis.py         -> correlation.png (y_i vs Δf/f)
  6. clock_ratio/make_report_figures.py    -> ratio_segments.png (report figure)
  7. clock_ratio/make_report.py            -> EXPERIMENT_REPORT.md (authoritative report)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent

STEPS = [
    ("逐段钟比值", REPO / "clock_ratio" / "compute_ratio.py"),
    ("潮汐频移", REPO / "clock" / "clock_tidal_shift.py"),
    ("段内拟合+跨段合并", REPO / "clock" / "segment_analysis" / "batch_analysis.py"),
    ("段均值相关", REPO / "clock_ratio" / "correlation_reanalysis.py"),
    ("段均值相关图", REPO / "clock" / "correlation_analysis.py"),
    ("报告插图", REPO / "clock_ratio" / "make_report_figures.py"),
    ("自动报告", REPO / "clock_ratio" / "make_report.py"),
]


def main() -> int:
    failed = []
    for name, script in STEPS:
        print(f"\n===== [{name}] {script.name} =====", flush=True)
        r = subprocess.run([sys.executable, str(script)], cwd=REPO)
        if r.returncode != 0:
            print(f"  ✗ {name} 失败 (exit {r.returncode})", file=sys.stderr)
            failed.append(name)
        else:
            print(f"  ✓ {name} 完成")
    if failed:
        print(f"\n失败步骤: {failed}", file=sys.stderr)
        return 1
    print("\n全部步骤完成。报告见 clock_ratio/EXPERIMENT_REPORT.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
