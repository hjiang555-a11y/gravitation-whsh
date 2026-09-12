"""Stability, output confinement and CLI contracts for the additive analysis."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from typer.testing import CliRunner

from clock import shared

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "clock_ratio" / "tidal_correction.py"


def test_help_when_invoked_from_other_directory(tmp_path: Path) -> None:
    # Given an installed interpreter and a different working directory.
    # When the real script's public help surface is invoked.
    result = subprocess.run([sys.executable, str(SCRIPT), "--help"], cwd=tmp_path,
                            capture_output=True, text=True, check=False)
    # Then help succeeds without reading data or writing results.
    assert result.returncode == 0, result.stderr
    assert "--output-dir" in result.stdout
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("tau", [1, 2, 3, 7, 16])
def test_oadev_when_all_overlapping_starts_are_counted(tau: int) -> None:
    from clock_ratio.tidal_stability import oadev
    # Given deterministic data, including a large removable numeric offset.
    x = 1e6 + np.sin(np.arange(67)) + np.arange(67) / 10
    times = np.datetime64("2026-01-01") + np.arange(len(x)).astype("timedelta64[s]")
    expected = np.array([x[i + tau:i + 2 * tau].mean() - x[i:i + tau].mean()
                         for i in range(len(x) - 2 * tau + 1)])
    # When every overlapping pair is evaluated.
    point, = oadev(times, x, (tau,))
    # Then pair count and Allan deviation match an independent explicit loop.
    assert point.n_pairs == len(x) - 2 * tau + 1
    assert point.sigma_y == pytest.approx(np.sqrt(np.mean(expected**2) / 2), rel=1e-9)


@pytest.mark.parametrize("slope", [0.0, 2e-18])
def test_oadev_when_input_is_constant_or_linear(slope: float) -> None:
    from clock_ratio.tidal_stability import oadev
    # Given constant or linear fractional frequency.
    times = np.datetime64("2026-01-01") + np.arange(50).astype("timedelta64[s]")
    x = 1e-14 + slope * np.arange(50)
    # When arbitrary integer taus are requested, including one without pairs.
    points = oadev(times, x, (1, 3, 8, 26))
    # Then no trend is subtracted, and insufficient data is explicit.
    for point in points[:-1]:
        assert point.sigma_y == pytest.approx(abs(slope) * point.tau_s / np.sqrt(2), abs=1e-29)
    assert points[-1].n_pairs == 0
    assert points[-1].sigma_y is None


@pytest.mark.parametrize("seconds", [[0, 1, 2, 3, 20, 21, 22, 23],
                                     [0, 1, 2, 3, 3, 4, 5, 6]])
def test_oadev_when_gaps_or_duplicates_split_runs(seconds: list[int]) -> None:
    from clock_ratio.tidal_stability import oadev
    # Given two four-sample runs separated by a gap or duplicate, with a jump.
    times = np.datetime64("2026-01-01") + np.array(seconds).astype("timedelta64[s]")
    x = np.array([0., 1., 2., 3., 100., 102., 104., 106.])
    # When tau=2 averages are pooled within this segment.
    point, = oadev(times, x, (2,))
    # Then there is one pair per run, no cross-boundary pair.
    assert point.n_pairs == 2
    assert point.sigma_y == pytest.approx(np.sqrt((2**2 + 4**2) / 4))


def test_tau_grid_when_longest_run_limits_requested_taus() -> None:
    from clock_ratio.tidal_stability import tau_grid
    # Given runs with lengths allowing non-dyadic prespecified taus.
    # When building the common grid.
    grid = tau_grid(28800)
    # Then include dyadic seconds and the four fixed taus, capped at one quarter.
    assert grid == tuple(sorted({2**i for i in range(13)} | {600, 1200, 3600, 7200}))
    assert tau_grid(3) == ()


@pytest.mark.parametrize("tau", [0, -1, 1.5])
def test_oadev_when_tau_is_invalid(tau: int | float) -> None:
    from clock_ratio.tidal_stability import oadev
    # Given a malformed external tau request.
    times = np.datetime64("2026-01-01") + np.arange(8).astype("timedelta64[s]")
    # When the typed boundary receives it, then reject instead of rounding.
    with pytest.raises(ValueError, match="positive integer"):
        oadev(times, np.zeros(8), (tau,))


def synthetic_loaders(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace only file loaders; exercise all real selection and computations."""
    from clock_ratio import tidal_correction as cli
    times = np.concatenate([np.datetime64(start) + np.arange(128).astype("timedelta64[s]")
                            for start, _ in shared.GROUPS])
    beat = np.full(len(times), 33_000_000., dtype=np.float64)
    utc = times - shared.UTC_OFFSET
    first = utc.min().astype("datetime64[s]").astype(np.int64) // 30 * 30
    last = (utc.max().astype("datetime64[s]").astype(np.int64) // 30 + 1) * 30
    tide_t = np.arange(first, last + 1, 30).astype("datetime64[s]")
    tide_w = np.linspace(-0.1, 0.2, len(tide_t))
    def beat_loader() -> tuple[NDArray[np.datetime64], NDArray[np.float64]]:
        return times, beat
    def tide_loader() -> tuple[NDArray[np.datetime64], NDArray[np.float64]]:
        return tide_t, tide_w
    monkeypatch.setattr(cli.shared, "load_beat", beat_loader)
    monkeypatch.setattr(cli.shared, "load_tide", tide_loader)


def test_cli_when_synthetic_data_writes_only_new_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from clock_ratio.tidal_correction import app
    # Given deterministic synthetic sources and an independent destination.
    synthetic_loaders(monkeypatch)
    output = tmp_path / "isolated"
    # When running the actual CLI command with the real pipeline.
    result = CliRunner().invoke(app, ["--output-dir", str(output)])
    # Then there are exactly 51 scenario rows and only the three new files.
    assert result.exit_code == 0, result.output
    assert {p.name for p in output.iterdir()} == {"ratio_scenarios.csv", "stability.csv", "summary.json"}
    with (output / "ratio_scenarios.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 51
    assert {row["scenario"]: row["coefficient"] for row in rows} == {"raw": "0", "theory": "-1", "empirical": "-0.54"}
    summary = json.loads((output / "summary.json").read_text(),
                         parse_constant=lambda token: pytest.fail(f"Nonfinite JSON number: {token}"))
    for key in ("raw", "theory", "empirical"):
        selected = [row for row in rows if row["scenario"] == key]
        total = sum(int(row["n_valid"]) for row in selected)
        expected = sum((Decimal(row["R"]) * int(row["n_valid"]) for row in selected), Decimal(0)) / total
        assert summary["scenarios"][key]["R_duration"] == str(expected)
        assert summary["scenarios"][key]["total_samples"] == total
        assert summary["scenarios"][key]["nsegments"] == 17
    assert Decimal(summary["scenarios"]["raw"]["delta_R"]) == Decimal(0)
    assert summary["metadata"]["decimal_precision"] == 80
    with (output / "stability.csv").open() as stream:
        stability = list(csv.DictReader(stream))
    assert stability and all(row["sigma_factor_vs_raw"] == "" for row in stability)
    raw_grid = [(row["group"], row["tau_s"], row["n_pairs"]) for row in stability if row["scenario"] == "raw"]
    for key in ("theory", "empirical"):
        assert [(row["group"], row["tau_s"], row["n_pairs"]) for row in stability if row["scenario"] == key] == raw_grid


@pytest.mark.parametrize("relative", [".", "clock_ratio", "clock", "results", "clock/data", "clock/data/new", "results/new"])
def test_cli_when_legacy_destination_is_requested(relative: str) -> None:
    from clock_ratio.tidal_correction import app
    # Given a protected source or legacy destination.
    # When requesting output there, then fail before loading any raw data.
    result = CliRunner().invoke(app, ["--output-dir", str(ROOT / relative)])
    assert result.exit_code != 0
    assert "protected" in result.output


def test_cli_when_raw_files_are_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from clock_ratio.tidal_correction import app
    # Given an empty raw input directory.
    monkeypatch.setattr(shared, "DATA_DIR", tmp_path / "missing")
    # When running, then expose a clear input error and create no output.
    result = CliRunner().invoke(app, ["--output-dir", str(tmp_path / "out")])
    assert result.exit_code != 0
    assert "raw beat data" in result.output
    assert not (tmp_path / "out").exists()


def test_writer_when_filename_is_a_symlink(tmp_path: Path) -> None:
    from clock_ratio.tidal_correction import validate_output_dir
    # Given an output filename pointing at an unrelated artifact.
    victim = tmp_path / "original.csv"
    victim.write_text("unchanged")
    out = tmp_path / "out"
    out.mkdir()
    (out / "ratio_scenarios.csv").symlink_to(victim)
    # When validating the destination, then refuse the indirection.
    with pytest.raises(ValueError, match="symlink"):
        validate_output_dir(out)
    assert victim.read_text() == "unchanged"


@pytest.mark.skipif(os.environ.get("RUN_CLOCK_DATA_TESTS") != "1", reason="parent opt-in: load real beat files once")
def test_baseline_when_real_data_matches_legacy_csv() -> None:
    from clock_ratio.tidal_analysis import SCENARIOS, analyze_segment, select_segments
    # Given the unchanged legacy inputs and published 17 segment ratios.
    times, beat = shared.load_beat()
    with (ROOT / "clock_ratio" / "ratio_17seg.csv").open() as stream:
        expected = list(csv.DictReader(stream))
    # When selecting the raw baseline once, without running any legacy generator.
    segments = select_segments(times, beat)
    # Then every Decimal ratio, membership count and endpoint trim is identical.
    assert len(segments) == len(expected) == 17
    for segment, row in zip(segments, expected, strict=True):
        raw = analyze_segment(segment, np.zeros(len(segment.beat)), SCENARIOS[0])
        assert raw.ratio == Decimal(row["YbSr_R"])
        assert len(segment.beat) == int(row["n_valid"])
        assert (segment.rem_start, segment.rem_end) == (int(row["rem_start"]), int(row["rem_end"]))
