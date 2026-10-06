from __future__ import annotations

from decimal import Decimal
import csv
import json

import numpy as np
import pytest

from clock import shared as s
from clock.sample_selection import (
    DEFAULT_SELECTION_PLAN,
    EndpointScreen,
    SelectedSegment,
    SelectionDiagnostics,
    SelectionPlan,
    endpoint_screen_indices,
    select_segments,
)


def selection_fixture() -> tuple[np.ndarray, np.ndarray, SelectionPlan]:
    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = 33_000_000.0 + np.array([2.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0, 2.0])
    plan = SelectionPlan(
        groups=((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),),
        shifts=(s.SHIFT_A[0],),
        exclusions=(),
    )
    return times, beat, plan


def test_default_selection_plan_uses_shared_shift_a() -> None:
    assert DEFAULT_SELECTION_PLAN.shifts == tuple(s.SHIFT_A)


def test_endpoint_screen_indices_trim_times_and_values_identically() -> None:
    beat = np.array([101.0, 100.0, 100.0, 100.0, 101.0])
    times = np.datetime64("2026-01-01T00:00:00") + np.arange(5).astype("timedelta64[s]")

    screen = endpoint_screen_indices(beat)

    assert screen == EndpointScreen(start=1, stop=4, removed_start=1, removed_end=1)
    assert np.array_equal(times[screen.start:screen.stop], times[1:4])
    assert np.array_equal(beat[screen.start:screen.stop], beat[1:4])


def test_endpoint_screen_indices_preserves_input_array() -> None:
    beat = np.array([101.0, 100.0, 100.0, 100.0, 101.0])
    original = beat.copy()

    screen = endpoint_screen_indices(beat)

    assert screen.start == 1
    np.testing.assert_array_equal(beat, original)


@pytest.mark.parametrize("shape", [(0,), (1, 0)])
def test_endpoint_screen_indices_rejects_empty_or_non_1d_input(shape: tuple[int, ...]) -> None:
    beat = np.empty(shape, dtype=np.float64)

    with pytest.raises(ValueError, match="non-empty 1-D"):
        endpoint_screen_indices(beat)


def test_endpoint_screen_indices_keeps_flat_array() -> None:
    beat = np.full(4, 33_000_000.0)

    assert endpoint_screen_indices(beat) == EndpointScreen(0, 4, 0, 0)


def test_select_segments_records_diagnostics_and_trims_in_sync() -> None:
    times, beat, plan = selection_fixture()

    segment, = select_segments(times, beat, plan)

    np.testing.assert_array_equal(segment.times, times[1:-1])
    np.testing.assert_array_equal(segment.beat, beat[1:-1])
    assert segment.raw_mean == pytest.approx(float(beat[1:-1].mean()))
    assert segment.m_dec == Decimal("33000000.0")
    assert segment.diagnostics == SelectionDiagnostics(
        n_window=9,
        n_excluded=0,
        n_plausible=9,
        n_jump_valid=9,
        n_longest_span=9,
        n_removed_start=1,
        n_removed_end=1,
        n_final=7,
        source_span_start=0,
        source_span_stop=9,
    )
    assert segment.times.flags.writeable is False
    assert segment.beat.flags.writeable is False


def test_select_segments_treats_exclusions_as_inclusive_and_group_end_as_exclusive() -> None:
    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = np.full(9, 33_000_000.0)
    beat[0], beat[8] = np.nan, 9e10
    plan = SelectionPlan(
        groups=((str(times[0]), str(times[8])),),
        shifts=(s.SHIFT_A[0],),
        exclusions=((str(times[0]), str(times[1])),),
    )

    segment, = select_segments(times, beat, plan)

    np.testing.assert_array_equal(segment.times, times[2:8])
    np.testing.assert_array_equal(segment.beat, beat[2:8])
    assert segment.diagnostics.n_window == 8
    assert segment.diagnostics.n_excluded == 2
    assert segment.diagnostics.n_final == 6


def test_select_segments_keeps_longest_index_span_even_with_time_gap() -> None:
    times, beat, plan = selection_fixture()
    times[5:] += np.timedelta64(20, "s")
    plan = SelectionPlan(groups=((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),),
                         shifts=plan.shifts,
                         exclusions=plan.exclusions)

    segment, = select_segments(times, beat, plan)

    np.testing.assert_array_equal(segment.times, times[1:-1])
    np.testing.assert_array_equal(segment.beat, beat[1:-1])
    assert segment.diagnostics.source_span_start == 0
    assert segment.diagnostics.source_span_stop == 9


def test_callers_share_identical_selected_segments(monkeypatch: pytest.MonkeyPatch) -> None:
    from clock.segment_analysis import batch_analysis
    from clock_ratio import compute_ratio, tidal_correction

    times = np.datetime64("2026-01-01T08:00:00") + np.arange(9).astype("timedelta64[s]")
    beat = np.full(9, 33_000_000.0)
    plan = SelectionPlan(
        groups=((str(times[0]), str(times[-1] + np.timedelta64(1, "s"))),),
        shifts=(s.SHIFT_A[0],),
        exclusions=(),
    )

    def loader() -> tuple[np.ndarray, np.ndarray]:
        return times, beat

    monkeypatch.setattr(compute_ratio, "load_beat", loader)
    monkeypatch.setattr(batch_analysis, "load_beat", loader)
    monkeypatch.setattr(tidal_correction.shared, "load_beat", loader)
    monkeypatch.setattr(compute_ratio, "DEFAULT_SELECTION_PLAN", plan)
    monkeypatch.setattr(batch_analysis, "DEFAULT_SELECTION_PLAN", plan)
    monkeypatch.setattr(tidal_correction, "DEFAULT_SELECTION_PLAN", plan)

    ratio_segments = compute_ratio.load_selected_segments()
    batch_segments = batch_analysis.load_selected_segments()
    tidal_segments = tidal_correction.load_selected_segments()

    assert tuple(segment.group for segment in ratio_segments) == (1,)
    for actual in (batch_segments, tidal_segments):
        for expected_segment, actual_segment in zip(ratio_segments, actual, strict=True):
            assert actual_segment.group == expected_segment.group
            assert len(actual_segment.beat) == len(expected_segment.beat)
            np.testing.assert_array_equal(actual_segment.times, expected_segment.times)
            np.testing.assert_array_equal(actual_segment.beat, expected_segment.beat)


def test_build_sample_ledger_rejects_output_dir_matching_clock_data_override(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from typer.testing import CliRunner

    from clock import build_sample_ledger

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    monkeypatch.setenv("CLOCK_DATA_DIR", str(raw_dir))

    result = CliRunner().invoke(build_sample_ledger.app, ["--output-dir", str(raw_dir)])

    assert result.exit_code != 0
    assert "protected raw-data directory" in result.output



def test_build_sample_ledger_cli_writes_diagnostics_and_time_quality(
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from typer.testing import CliRunner

    from clock import build_sample_ledger

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_file = raw_dir / "Freq_B_2_260601_demo.txt"
    raw_file.write_text(
        "# demo\n"
        "260601 080000 0 0 0 0 0 0 0 0 33000000\n"
        "260601 080001 0 0 0 0 0 0 0 0 33000001\n"
        "260601 080002 0 0 0 0 0 0 0 0 33000002\n",
        encoding="utf-8",
    )
    retained_times = np.array(["2026-06-01T08:00:01", "2026-06-01T08:00:02"], dtype="datetime64[s]")
    retained_beat = np.array([33_000_000.0, 33_000_001.0])
    retained_times.setflags(write=False)
    retained_beat.setflags(write=False)
    diagnostics = SelectionDiagnostics(
        n_window=3,
        n_excluded=0,
        n_plausible=3,
        n_jump_valid=3,
        n_longest_span=3,
        n_removed_start=1,
        n_removed_end=0,
        n_final=2,
        source_span_start=0,
        source_span_stop=3,
    )
    segment = SelectedSegment(
        group=1,
        times=retained_times,
        beat=retained_beat,
        m_dec=Decimal("33000000"),
        shift_a=s.SHIFT_A[0],
        raw_mean=float(retained_beat.mean()),
        rem_start=1,
        rem_end=0,
        diagnostics=diagnostics,
    )

    monkeypatch.setattr(build_sample_ledger.shared, "DATA_DIR", raw_dir)
    monkeypatch.setattr(build_sample_ledger.shared, "load_beat", lambda: (retained_times, retained_beat))
    monkeypatch.setattr(build_sample_ledger, "select_segments", lambda times, beat, plan=DEFAULT_SELECTION_PLAN: (segment,))

    output_dir = tmp_path / "out"
    result = CliRunner().invoke(build_sample_ledger.app, ["--output-dir", str(output_dir)])

    assert result.exit_code == 0, result.output
    with (output_dir / "sample_ledger.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [{
        "group": "1",
        "n_window": "3",
        "n_excluded": "0",
        "n_plausible": "3",
        "n_jump_valid": "3",
        "n_longest_span": "3",
        "n_removed_start": "1",
        "n_removed_end": "0",
        "n_final": "2",
        "source_span_start": "0",
        "source_span_stop": "3",
        "retained_start_beijing": "2026-06-01T08:00:01",
        "retained_end_beijing": "2026-06-01T08:00:02",
    }]
    payload = json.loads((output_dir / "time_quality.json").read_text(encoding="utf-8"))
    assert payload["computed_total_final"] == 2
    assert payload["computed_total_status"] == "established"
    assert payload["external_reported_totals"] == [
        {
            "value": 1009022,
            "status": "pending-verification",
            "source_path": "archive/CONCLUSION_17.md",
            "note": "Historical trimmed-total claim retained for reconciliation only; no authoritative per-segment allocation exists in the current analysis code.",
        },
        {
            "value": 1009204,
            "status": "pending-verification",
            "source_path": "paper/main.tex",
            "note": "Historical manuscript count retained for reconciliation only; no authoritative per-segment allocation exists in the current analysis code.",
        },
    ]
    assert len(payload["files"]) == 1
    entry = payload["files"][0]
    assert entry["digest"]["relative_path"] == raw_file.name
    assert entry["digest"]["sha256"]
    assert entry["timestamp_quality"]["n_rows"] == 3
    assert entry["timestamp_quality"]["n_parse_errors"] == 0
