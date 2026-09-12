"""Regression contracts for the independent report; never run legacy analyses."""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from pathlib import Path
from typing import Final

import pytest

REPO: Final = Path(__file__).resolve().parents[1]
SOURCE: Final = REPO / "clock_ratio" / "tidal_correction"
SCRIPT: Final = REPO / "clock_ratio" / "make_tidal_report.py"
ARTIFACTS: Final = ("summary.json", "ratio_scenarios.csv", "stability.csv")
SCENARIOS: Final = ("raw", "theory", "empirical")
LEGACY: Final = (
    "compute_ratio.py", "clock_tidal_shift.py", "batch_analysis.py",
    "correlation_reanalysis.py", "correlation_analysis.py", "make_report_figures.py",
    "variant1_30s_tide.py", "variant30s_analysis.py", "segment13_correlation.py",
    "segment13_triangular.py", "segment6_triangular.py", "statistical_methods.py",
    "make_report.py",
)


@pytest.fixture
def artifact_copy(tmp_path: Path) -> Path:
    for name in ARTIFACTS:
        shutil.copyfile(SOURCE / name, tmp_path / name)
    return tmp_path


@pytest.mark.parametrize("value,expected", [
    ("1.207507039343337720369560976803305479", "1.2075070393433377203696"),
    ("1.207507039343337720810752422497709680", "1.2075070393433377208108"),
    ("1.207507039343337720607804357478283747", "1.2075070393433377206078"),
    ("1.00000000000000000000005", "1.0000000000000000000000"),
    ("1.00000000000000000000015", "1.0000000000000000000002"),
])
def test_ratio_rounding_when_decimal_context_is_small(value: str, expected: str) -> None:
    from clock_ratio.make_tidal_report import format_ratio
    # Given a small ambient precision, When formatting, Then round rather than truncate.
    with localcontext() as context:
        context.prec = 6
        assert format_ratio(Decimal(value)) == expected


def test_tables_when_reading_actual_sources() -> None:
    from clock_ratio.make_tidal_report import read_report, render_report
    # Given the authoritative files, When rendering, Then every numeric row is derived.
    data = read_report(SOURCE)
    text = render_report(data)
    document = json.loads((SOURCE / "summary.json").read_text())
    with localcontext() as context:
        context.prec = 80
        for name in SCENARIOS:
            row = document["scenarios"][name]
            assert data.summary.scenarios[name].R_duration == Decimal(row["R_duration"])
            rounded = Decimal(row["R_duration"]).quantize(Decimal("1e-22"), rounding=ROUND_HALF_EVEN)
            delta = Decimal(row["delta_R"]) * Decimal("1e18")
            fractional = Decimal(row["delta_fractional_1e18"])
            assert f"| {name} | {row['coefficient']} | {rounded:.22f} | {delta:+.6f} | {fractional:+.6f} |" in text
        with (SOURCE / "ratio_scenarios.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        groups = sorted({int(row["group"]) for row in rows})
        for group in groups:
            triplet = [next(row for row in rows if int(row["group"]) == group and row["scenario"] == name) for name in SCENARIOS]
            ratios = [f"{Decimal(row['R']):.22f}" for row in triplet]
            changes = [f"{Decimal(row['delta_fractional_1e18']):+.6f}" for row in triplet]
            assert "| " + " | ".join([str(group), triplet[0]["n_valid"], *ratios, *changes]) + " |" in text


@pytest.mark.parametrize("tau", [1200, 3600, 7200])
def test_stability_when_tau_has_only_eligible_segments(tau: int) -> None:
    from clock_ratio.make_tidal_report import read_report, render_report
    # Given actual stability CSV, When rendering, Then counts/ranges use available factors only.
    with (SOURCE / "stability.csv").open() as stream:
        rows = [row for row in csv.DictReader(stream) if int(row["tau_s"]) == tau]
    text = render_report(read_report(SOURCE))
    for name in SCENARIOS[1:]:
        factors = [float(row["sigma_factor_vs_raw"]) for row in rows if row["scenario"] == name and row["sigma_factor_vs_raw"]]
        lower = sum(factor < 1 for factor in factors)
        assert f"| {tau} | {name} | {len(factors)} | {lower} | {len(factors) - lower} | {min(factors):.6f}–{max(factors):.6f} |" in text
    if tau in (1200, 7200):
        table = text.split(f"### τ = {tau} s", 1)[1].split("\n##", 1)[0]
        for group in range(1, 18):
            triplet = [next((row for row in rows if int(row["group"]) == group and row["scenario"] == name), None) for name in SCENARIOS]
            sigma = [f"{float(row['sigma_y']):.6e}" if row and row["sigma_y"] else "—" for row in triplet]
            factors = [f"{float(row['sigma_factor_vs_raw']):.6f}" if row and row["sigma_factor_vs_raw"] else "—" for row in triplet[1:]]
            assert "| " + " | ".join([str(group), *sigma, *factors]) + " |" in table


@pytest.mark.parametrize("filename,old,new", [
    ("summary.json", '"nsegments": 17', '"nsegments": 16'),
    ("summary.json", '"total_samples": 1008912', '"total_samples": 1008911'),
    ("summary.json", "1.207507039343337720810752", "1.207507039343337720910752"),
    ("summary.json", '"theory":', '"unknown":'),
    ("ratio_scenarios.csv", "theory,-1,1,68009,", "theory,-1,1,68008,"),
    ("ratio_scenarios.csv", "theory,-1,1,", "theory,-1,99,"),
    ("ratio_scenarios.csv", "0.8080575717789768", "0.9080575717789768"),
    ("stability.csv", "theory,-1,1,1200,65610", "theory,-1,1,1200,65609"),
    ("stability.csv", "0.9988643767034399", "0.5"),
    ("stability.csv", "1.2393277760855727e-17", "NaN"),
])
def test_rejects_inconsistent_sources_when_one_artifact_changes(artifact_copy: Path, filename: str, old: str, new: str) -> None:
    from clock_ratio.make_tidal_report import ReportError, read_report
    # Given a stale/malformed artifact, When reading, Then fail before any report rendering.
    path = artifact_copy / filename
    original = path.read_text()
    assert old in original
    path.write_text(original.replace(old, new, 1))
    with pytest.raises(ReportError):
        read_report(artifact_copy)


@pytest.mark.parametrize("filename", ARTIFACTS)
def test_cli_preserves_report_when_source_missing(artifact_copy: Path, filename: str) -> None:
    # Given an old report and a missing source, When CLI runs, Then exit nonzero without overwriting.
    (artifact_copy / filename).unlink()
    report = artifact_copy / "REPORT.md"
    report.write_text("previous report")
    result = subprocess.run([sys.executable, str(SCRIPT), "--input-dir", str(artifact_copy)], capture_output=True, text=True)
    assert result.returncode != 0
    assert report.read_text() == "previous report"


@pytest.mark.parametrize("script", [SCRIPT, REPO / "run_all.py"])
@pytest.mark.parametrize("argument,status", [("--help", 0), ("--invalid-option", 2)])
def test_cli_when_help_or_invalid_args(script: Path, argument: str, status: int, tmp_path: Path) -> None:
    # Given a sandbox pipeline copy, When parsing CLI options, Then no analysis is executed.
    sandbox = tmp_path / script.name
    shutil.copyfile(script, sandbox)
    result = subprocess.run([sys.executable, str(sandbox), argument], capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(REPO)})
    assert result.returncode == status
    assert "=====" not in result.stdout
    assert "Usage" in result.stdout + result.stderr


def test_cli_generates_reproducible_report_when_sources_valid(artifact_copy: Path) -> None:
    from clock_ratio.make_tidal_report import read_report, render_report
    # Given actual sources in isolation, When CLI runs, Then bytes match pure rendering.
    result = subprocess.run([sys.executable, str(SCRIPT), "--input-dir", str(artifact_copy)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert (artifact_copy / "REPORT.md").read_text() == render_report(read_report(artifact_copy))


@pytest.mark.parametrize("tidal_only", [True, False])
def test_step_selection_when_tidal_mode_changes(tidal_only: bool) -> None:
    import run_all
    # Given mode, When selecting, Then preserve legacy order and place new steps before old report.
    names = [path.name for _, path in run_all.select_steps(tidal_only)]
    tidal = ["tidal_correction.py", "make_tidal_report.py"]
    assert names == (tidal if tidal_only else [*LEGACY[:-1], *tidal, LEGACY[-1]])


@pytest.mark.parametrize("fail_index", [None, 0, 1])
def test_tidal_cli_when_subprocess_fails_stops_before_stale_report(tmp_path: Path, fail_index: int | None) -> None:
    # Given sandbox scripts with deterministic exit status, When tidal-only runs, Then fail fast.
    shutil.copyfile(REPO / "run_all.py", tmp_path / "run_all.py")
    lane = tmp_path / "clock_ratio"
    lane.mkdir()
    names = ["tidal_correction.py", "make_tidal_report.py"]
    for index, name in enumerate(names):
        (lane / name).write_text("from pathlib import Path\nwith Path('calls').open('a') as stream:\n    stream.write(" + repr(name + "\n") + ")\nraise SystemExit(" + str(7 if fail_index == index else 0) + ")\n")
    result = subprocess.run([sys.executable, str(tmp_path / "run_all.py"), "--tidal-only"], capture_output=True, text=True)
    assert result.returncode == (0 if fail_index is None else 1)
    assert (tmp_path / "calls").read_text().splitlines() == names[:1 if fail_index == 0 else 2]


def test_default_continues_when_legacy_step_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    import run_all
    calls: list[str] = []
    # Given a failed legacy subprocess, When the default loop runs, Then keep its continuation semantics.
    def record(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        calls.append(Path(command[1]).name)
        return subprocess.CompletedProcess(command, 1 if len(calls) == 1 else 0)
    monkeypatch.setattr(run_all.subprocess, "run", record)
    status = run_all.main()
    assert status == 1
    assert calls == [*LEGACY[:-1], "tidal_correction.py", "make_tidal_report.py", LEGACY[-1]]


def test_navigation_when_baseline_report_is_preserved() -> None:
    # Given both old report and its generator, When reading, Then use the identical persistent note.
    note = "> **导航**：本报告的时长加权钟比值保留未做潮汐修正的旧基线；raw / theory / empirical 的独立潮汐修正比较见新[报告](tidal_correction/REPORT.md)。"
    assert note in (REPO / "clock_ratio" / "EXPERIMENT_REPORT.md").read_text()
    assert note in (REPO / "clock_ratio" / "make_report.py").read_text()
