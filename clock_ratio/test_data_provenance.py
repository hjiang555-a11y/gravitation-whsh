from __future__ import annotations

from pathlib import Path

import numpy as np

from clock.build_parameter_ledger import build_parameter_records
from clock.data_provenance import inspect_timestamp_labels, sha256_file
from clock.shared import load_beat
from clock_ratio.evidence import EvidenceStatus


FIXTURE_COLUMNS = [
    "1",
    "10000000.0",
    "13000000.0",
    "825749.0",
    "26000000.0",
    "10000000.0",
    "10000000.0",
    "9999995.0",
    "33623141.0",
]


def write_beat_fixture(tmp_path: Path, labels: list[str]) -> Path:
    rows = [
        "#PC time          S              1:FXE_B1              2:FXE_B2              3:FXE_B3              4:FXE_B4              5:FXE_B5              6:FXE_B6              7:FXE_B7              8:FXE_B8"
    ]
    for label in labels:
        date_part, time_part = label.split()
        year, month, day = (int(part) for part in date_part.split("-"))
        rows.append(
            f"{year % 100:02d}{month:02d}{day:02d} {time_part} " + "  ".join(FIXTURE_COLUMNS)
        )
    path = tmp_path / "Freq_B_2_fixture.txt"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_timestamp_quality_reports_duplicates_gaps_and_reversal(tmp_path: Path) -> None:
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



def test_sha256_changes_when_input_changes(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("a", encoding="utf-8")
    first = sha256_file(path)
    path.write_text("b", encoding="utf-8")
    assert sha256_file(path) != first



def test_parameter_ledger_flags_sensitive_and_inherited_groups() -> None:
    records = build_parameter_records(Path("clock/params.json"))
    seg9 = next(r for r in records if r.group == 9 and r.name == "a_SM")
    assert seg9.status is EvidenceStatus.pending_verification
    inherited = [r for r in records if r.group in (15, 16, 17) and r.name == "shift_a"]
    assert {r.inherited_from_group for r in inherited} == {12}
    assert all(r.status is EvidenceStatus.pending_verification for r in inherited)



def test_load_beat_preserves_file_order_for_duplicate_timestamps(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    files = [data_dir / name for name in ("Freq_B_2_260629_a.txt", "Freq_B_2_260629_b.txt", "Freq_B_2_260629_c.txt")]
    for path in files:
        path.write_text("fixture\n", encoding="utf-8")

    base = np.datetime64("2026-06-29T10:00:00")
    payloads = {
        files[0].name: (base + np.array([0, 1, 2]).astype("timedelta64[s]"), np.array([10.0, 11.0, 12.0])),
        files[1].name: (base + np.array([0, 1, 2]).astype("timedelta64[s]"), np.array([20.0, 21.0, 22.0])),
        files[2].name: (base + np.array([0, 1]).astype("timedelta64[s]"), np.array([30.0, 31.0])),
    }

    monkeypatch.setattr("clock.shared.DATA_DIR", data_dir)
    monkeypatch.setattr("clock.shared.load_beat_file", lambda path: payloads[path.name])

    times, beat = load_beat()

    np.testing.assert_array_equal(
        times,
        base + np.array([0, 0, 0, 1, 1, 1, 2, 2]).astype("timedelta64[s]"),
    )
    np.testing.assert_array_equal(beat, np.array([10.0, 20.0, 30.0, 11.0, 21.0, 31.0, 12.0, 22.0]))
