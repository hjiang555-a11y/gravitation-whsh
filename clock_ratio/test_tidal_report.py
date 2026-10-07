"""Regression contracts for the independent report; never run legacy analyses."""
from __future__ import annotations

import csv
import hashlib
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
    "correlation_reanalysis.py", "correlation_reanalysis_timeweighted.py",
    "correlation_reanalysis_seg9_excluded.py",
    "correlation_reanalysis_seg9_independent.py",
    "correlation_analysis.py", "make_report_figures.py",
    "variant1_30s_tide.py", "variant30s_analysis.py", "segment13_correlation.py",
    "segment13_triangular.py", "segment6_triangular.py",
    "statistical_methods.py",
    "statistical_methods_tidal.py", "statistical_methods_tidal_seg9.py",
    "concatenated_stability.py", "concatenated_stability_long.py",
    "make_paper_figures.py",
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


def test_step_selection_when_mode_changes() -> None:
    import run_all
    # Given a mode, When selecting, Then preserve legacy order and keep audit steps separate.
    tidal = ["tidal_correction.py", "make_tidal_report.py"]
    assert [Path(step.command[1]).name for step in run_all.select_steps("tidal")] == tidal
    legacy = [Path(step.command[1]).name for step in run_all.select_steps("legacy")]
    assert legacy == [*LEGACY[:-1], *tidal, LEGACY[-1]]
    assert all(step.outputs == () for step in run_all.select_steps("legacy"))


def test_select_steps_audit_order() -> None:
    import run_all
    # Given audit mode, When selecting, Then the nine executable steps keep their fixed order.
    names = [step.name for step in run_all.select_steps("audit")]
    assert names == [
        "样本账本", "参数账本", "潮汐转换比较", "比值", "潮汐场景",
        "段不确定度", "敏感性", "manifest 构建", "manifest 验证",
    ]


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


def test_seg9_exclusion_when_combined_values_are_reduced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import clock_ratio.statistical_methods_tidal_seg9 as seg9
    # Given the actual per-segment source, When re-combining without segment 9,
    # Then every scenario has 16 segments and the source file is untouched.
    source = REPO / "clock_ratio" / "statistical_methods_tidal.json"
    before = source.read_text()
    import json
    out = tmp_path / "statistical_methods_tidal_seg9_excluded.json"
    monkeypatch.setattr(seg9, "JSON_PATH", out)
    assert seg9.main() == 0
    document = json.loads(out.read_text())
    assert set(document["scenarios"]) == {"raw", "theory", "empirical"}
    for scenario in document["scenarios"].values():
        assert scenario["n_segments"] == 16
        assert scenario["excluded_group"] == 9
        assert all(row["group"] != 9 for row in scenario["per_segment"])
    assert source.read_text() == before


def test_seg9_correlation_when_original_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import clock_ratio.correlation_reanalysis_seg9_excluded as corr
    import csv
    # Given the full 17-segment correlation outputs, When re-running with
    # segment 9 excluded, Then 16 segments are used and the originals are intact.
    orig_csv = REPO / "clock_ratio" / "correlation_reanalysis.csv"
    before = orig_csv.read_text()
    monkeypatch.setattr(corr, "OUT_DIR", tmp_path)
    assert corr.main() == 0
    reduced = dict(csv.reader(open(tmp_path / "correlation_reanalysis_seg9_excluded.csv")))
    assert reduced["excluded_group"] == "9"
    assert reduced["n_segments"] == "16"
    assert float(reduced["pearson_r"]) == pytest.approx(0.428662, abs=1e-5)
    assert float(reduced["pearson_p"]) > 0.05
    assert (tmp_path / "correlation_reanalysis_seg9_excluded.png").exists()
    assert orig_csv.read_text() == before


@pytest.mark.skipif(os.environ.get("RUN_CLOCK_DATA_TESTS") != "1", reason="parent opt-in: load real beat files once")
def test_seg9_independent_when_recomputes_from_raw_and_matches() -> None:
    from clock_ratio.correlation_reanalysis_seg9_independent import main as indep_main
    import csv
    import json
    # Given the raw beat data, When re-deriving ratios and excluding segment 9,
    # Then the raw re-derivation matches the stored ratios and existing products
    # stay untouched.
    ratio_csv = REPO / "clock_ratio" / "ratio_17seg.csv"
    orig_corr = REPO / "clock_ratio" / "correlation_reanalysis.csv"
    ratio_before, corr_before = ratio_csv.read_text(), orig_corr.read_text()
    assert indep_main() == 0
    document = json.loads((REPO / "clock_ratio" / "correlation_reanalysis_seg9_independent.json").read_text())
    assert document["n_segments"] == 16
    assert document["excluded_group"] == 9
    # Pre-declared cross-check tolerance: the tracked CSV was generated in an
    # earlier float64 environment; last-bit reduction-order drift of the beat
    # mean bounds exact reproduction at ~1e-22. 1e-21 is ~20x the observed
    # ~5.2e-23 drift and still five orders below any selection/formula change.
    assert abs(document["raw_rederivation_max_rel_diff_vs_ratio_17seg"]) <= 1e-21
    assert document["pearson_r"] == pytest.approx(0.428662, abs=1e-5)
    row = dict(csv.reader(open(REPO / "clock_ratio" / "correlation_reanalysis_seg9_independent.csv")))
    assert row["n_segments"] == "16"
    assert ratio_csv.read_text() == ratio_before
    assert orig_corr.read_text() == corr_before


def failing_steps():
    import run_all
    return (run_all.Step("failing", (sys.executable, "-c", "raise SystemExit(3)"), ()),)


def test_audit_stops_on_first_failure_and_preserves_verified(tmp_path: Path) -> None:
    import run_all
    verified = tmp_path / "verified"
    verified.mkdir()
    old = verified / "manifest.json"
    old.write_text('{"old": true}', encoding="utf-8")
    summary = run_all.run_steps(failing_steps(), tmp_path / "staging", fail_fast=True)
    assert not summary.success
    assert summary.failed_step == "failing"
    assert old.read_text(encoding="utf-8") == '{"old": true}'
    assert not (tmp_path / "staging" / "manifest.json").exists()


def test_run_steps_success_but_missing_declared_output_fails(tmp_path: Path) -> None:
    import run_all
    # Given a zero-exit step that never writes its declared output, When run, Then it fails.
    step = run_all.Step("empty", (sys.executable, "-c", "pass"), (tmp_path / "missing.csv",))
    summary = run_all.run_steps((step,), tmp_path / "staging", fail_fast=True)
    assert not summary.success
    assert summary.failed_step == "empty"


def test_run_steps_legacy_continues_and_reports_failure(tmp_path: Path) -> None:
    import run_all
    # Given a failing step followed by a passing one, When run without fail_fast, Then continue.
    first = run_all.Step("first", (sys.executable, "-c", "raise SystemExit(3)"), ())
    second = run_all.Step("second", (sys.executable, "-c", "pass"), ())
    summary = run_all.run_steps((first, second), tmp_path / "staging", fail_fast=False)
    assert summary.completed == ("second",)
    assert summary.failed_step == "first"
    assert not summary.success


def test_promote_run_is_atomic_and_keeps_history(tmp_path: Path) -> None:
    import run_all
    # Given a verified staging run, When promoted, Then the run is immutable history and
    # the verified symlink is atomically swapped, never deleting old runs.
    out = tmp_path / "out"
    staging = tmp_path / "staging"
    staging.mkdir()
    (staging / "manifest.json").write_text('{"ok": true}', encoding="utf-8")
    digest = hashlib.sha256(b'{"ok": true}').hexdigest()[:16]
    run_dir = run_all.promote_run(staging, output_dir=out)
    assert run_dir == out / "runs" / digest
    verified = out / "verified"
    assert verified.is_symlink()
    assert (verified / "manifest.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert not staging.exists()
    # identical re-promotion keeps the immutable run and leaves the pointer valid
    staging_same = tmp_path / "staging-same"
    staging_same.mkdir()
    (staging_same / "manifest.json").write_text('{"ok": true}', encoding="utf-8")
    assert run_all.promote_run(staging_same, output_dir=out) == run_dir
    assert (verified / "manifest.json").read_text(encoding="utf-8") == '{"ok": true}'
    assert run_dir.exists()
    # a different manifest swaps the pointer but keeps the first run in history
    staging_new = tmp_path / "staging-new"
    staging_new.mkdir()
    (staging_new / "manifest.json").write_text('{"ok": false}', encoding="utf-8")
    new_digest = hashlib.sha256(b'{"ok": false}').hexdigest()[:16]
    assert run_all.promote_run(staging_new, output_dir=out) == out / "runs" / new_digest
    assert (verified / "manifest.json").read_text(encoding="utf-8") == '{"ok": false}'
    assert run_dir.exists()


def test_legacy_mode_never_declares_outputs() -> None:
    import run_all
    # Given legacy/tidal compatibility modes, When selecting, Then no Step declares outputs.
    assert all(step.outputs == () for step in run_all.select_steps("legacy"))
    assert all(step.outputs == () for step in run_all.select_steps("tidal"))
