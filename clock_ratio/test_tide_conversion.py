"""Executable audit coverage for professional tide conversion."""
from __future__ import annotations

import csv
import json
import os
from decimal import Decimal
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from typer.testing import CliRunner

from clock_ratio import tide_conversion
from clock_ratio.tide_conversion import (
    CONVERTED_FILENAME,
    DIFF_FILENAME,
    TideConversionConfig,
    app,
    compare_tide_csv,
    convert_height_mm_to_potential,
    convert_workbook,
)


def staging_repo_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "results" / "audit-v1" / "staging").mkdir(parents=True)
    return root


def staging_output_csv(repo_root: Path, name: str = "demo") -> Path:
    return repo_root / "results" / "audit-v1" / "staging" / name / CONVERTED_FILENAME


def write_demo_workbook(path: Path, rows: list[tuple[str, Decimal, Decimal, Decimal, Decimal, Decimal]] | None = None) -> None:
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    sheet["B1"] = "固体潮（mm)"
    sheet["E1"] = "海潮（mm)"
    sheet["H1"] = "固体潮之差（mm)"
    sheet["I1"] = "海潮之差（mm)"
    sheet["J1"] = "综合差（mm)"
    sheet["B2"] = "CAS"
    sheet["C2"] = "SHA"
    sheet["E2"] = "CAS"
    sheet["F2"] = "SHA"
    sheet["H2"] = "CAS-SHA"

    data_rows = rows or [
        ("20260620000000", Decimal("10.0"), Decimal("9.0"), Decimal("-2.0"), Decimal("1.0"), Decimal("-2.0")),
        ("20260620000030", Decimal("5.5"), Decimal("5.0"), Decimal("-1.0"), Decimal("0.5"), Decimal("-1.0")),
        ("20260620000100", Decimal("3.0"), Decimal("6.0"), Decimal("0.0"), Decimal("2.0"), Decimal("-5.0")),
    ]
    for row_index, (stamp, solid_cas, solid_sha, ocean_cas, ocean_sha, combined) in enumerate(data_rows, start=3):
        sheet[f"A{row_index}"] = stamp
        sheet[f"B{row_index}"] = float(solid_cas)
        sheet[f"C{row_index}"] = float(solid_sha)
        sheet[f"E{row_index}"] = float(ocean_cas)
        sheet[f"F{row_index}"] = float(ocean_sha)
        sheet[f"H{row_index}"] = float(solid_cas - solid_sha)
        sheet[f"I{row_index}"] = float(ocean_cas - ocean_sha)
        sheet[f"J{row_index}"] = float(combined)

    workbook.save(path)


def patch_cell_text(path: Path, cell_ref: str, text: str) -> None:
    with ZipFile(path) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    sheet_xml = members["xl/worksheets/sheet1.xml"].decode("utf-8")
    marker = f'r="{cell_ref}"'
    start = sheet_xml.index(marker)
    value_start = sheet_xml.index("<v>", start) + 3
    value_end = sheet_xml.index("</v>", value_start)
    sheet_xml = sheet_xml[:value_start] + text + sheet_xml[value_end:]
    members["xl/worksheets/sheet1.xml"] = sheet_xml.encode("utf-8")
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def write_csv(path: Path, rows: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp_utc", "total_tidal_delta_m2_s2_surface"])
        writer.writerows(rows)


def test_height_difference_conversion_preserves_direction() -> None:
    config = TideConversionConfig(
        gravity_m_s2=Decimal("9.794"),
        direction="CAS-minus-SHA",
        timezone="UTC",
    )

    assert convert_height_mm_to_potential(Decimal("1"), config) == Decimal("0.009794")
    assert convert_height_mm_to_potential(Decimal("-1"), config) == Decimal("-0.009794")


def test_convert_workbook_writes_expected_utc_grid_from_comprehensive_difference_column(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = staging_repo_root(tmp_path)
    monkeypatch.setattr(tide_conversion, "_protected_repo_roots", lambda: (repo_root.resolve(),))
    workbook_path = repo_root / "clock" / "professional.xlsx"
    workbook_path.parent.mkdir(parents=True)
    write_demo_workbook(workbook_path)
    output_csv = staging_output_csv(repo_root)

    summary = convert_workbook(workbook_path, output_csv)

    with output_csv.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))

    assert rows == [
        {
            "timestamp_utc": "2026-06-20T00:00:00Z",
            "total_tidal_delta_m2_s2_surface": "-0.019588",
        },
        {
            "timestamp_utc": "2026-06-20T00:00:30Z",
            "total_tidal_delta_m2_s2_surface": "-0.009794",
        },
        {
            "timestamp_utc": "2026-06-20T00:01:00Z",
            "total_tidal_delta_m2_s2_surface": "-0.04897",
        },
    ]
    assert summary == {
        "row_count": 3,
        "first_timestamp_utc": "2026-06-20T00:00:00Z",
        "last_timestamp_utc": "2026-06-20T00:01:00Z",
        "step_seconds": 30,
        "source_column": "综合差",
    }


def test_convert_workbook_reads_cached_decimal_text_without_binary_tail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = staging_repo_root(tmp_path)
    monkeypatch.setattr(tide_conversion, "_protected_repo_roots", lambda: (repo_root.resolve(),))
    workbook_path = repo_root / "clock" / "precision.xlsx"
    workbook_path.parent.mkdir(parents=True)
    write_demo_workbook(
        workbook_path,
        rows=[("20260620000000", Decimal("0.0"), Decimal("30.0"), Decimal("0.4219"), Decimal("2.0"), Decimal("-31.5781"))],
    )
    patch_cell_text(workbook_path, "J3", "-31.5781000000000001")
    output_csv = staging_output_csv(repo_root, name="precision")

    convert_workbook(workbook_path, output_csv)

    with output_csv.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows == [{
        "timestamp_utc": "2026-06-20T00:00:00Z",
        "total_tidal_delta_m2_s2_surface": "-0.3092759114000000009794",
    }]


def test_convert_workbook_rejects_non_staging_and_colliding_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = staging_repo_root(tmp_path)
    monkeypatch.setattr(tide_conversion, "_protected_repo_roots", lambda: (repo_root.resolve(),))
    workbook_path = repo_root / "clock" / "professional.xlsx"
    workbook_path.parent.mkdir(parents=True)
    write_demo_workbook(workbook_path)

    with pytest.raises(ValueError, match="staging"):
        convert_workbook(workbook_path, repo_root / "results" / "audit-v1" / CONVERTED_FILENAME)
    with pytest.raises(ValueError, match="collides with protected input"):
        convert_workbook(workbook_path, workbook_path)


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_convert_workbook_rejects_linked_output_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    repo_root = staging_repo_root(tmp_path)
    monkeypatch.setattr(tide_conversion, "_protected_repo_roots", lambda: (repo_root.resolve(),))
    workbook_path = repo_root / "clock" / "professional.xlsx"
    workbook_path.parent.mkdir(parents=True)
    write_demo_workbook(workbook_path)
    victim = tmp_path / "victim.csv"
    victim.write_text("unchanged", encoding="utf-8")
    output_csv = staging_output_csv(repo_root, name="linked")
    output_csv.parent.mkdir(parents=True)
    if kind == "symlink":
        output_csv.symlink_to(victim)
    else:
        os.link(victim, output_csv)

    with pytest.raises(ValueError, match="symlink|independent regular file"):
        convert_workbook(workbook_path, output_csv)
    assert victim.read_text(encoding="utf-8") == "unchanged"


def test_compare_tide_csv_reports_first_difference_and_max_abs_deltas(tmp_path: Path) -> None:
    converted = tmp_path / CONVERTED_FILENAME
    write_csv(
        converted,
        [
            ("2026-06-20T00:00:00Z", "-0.019588"),
            ("2026-06-20T00:00:30Z", "-0.009794"),
        ],
    )
    reference = tmp_path / "reference.csv"
    write_csv(
        reference,
        [
            ("2026-06-20T00:00:30Z", "-0.019500"),
            ("2026-06-20T00:01:00Z", "-0.009700"),
        ],
    )

    summary = compare_tide_csv(converted, reference)

    assert summary["converted_row_count"] == 2
    assert summary["reference_row_count"] == 2
    assert summary["common_prefix_row_count"] == 2
    assert summary["first_timestamp_utc"] == "2026-06-20T00:00:00Z"
    assert summary["last_timestamp_utc"] == "2026-06-20T00:00:30Z"
    assert summary["max_abs_time_diff_s"] == 30
    assert summary["max_abs_value_diff"] == "0.000094"
    assert summary["first_inconsistent_row"] == {
        "row_number": 1,
        "converted_timestamp_utc": "2026-06-20T00:00:00Z",
        "reference_timestamp_utc": "2026-06-20T00:00:30Z",
        "converted_value": "-0.019588",
        "reference_value": "-0.0195",
        "time_diff_s": 30,
        "value_diff": "-0.000088",
    }
    assert summary["first_extra_converted_row"] is None
    assert summary["first_extra_reference_row"] is None


def test_compare_tide_csv_reports_row_count_mismatches_without_raising(tmp_path: Path) -> None:
    converted = tmp_path / CONVERTED_FILENAME
    write_csv(converted, [("2026-06-20T00:00:00Z", "-0.019588")])
    reference = tmp_path / "reference.csv"
    write_csv(
        reference,
        [
            ("2026-06-20T00:00:00Z", "-0.019588"),
            ("2026-06-20T00:00:30Z", "-0.009794"),
        ],
    )

    summary = compare_tide_csv(converted, reference)

    assert summary["converted_row_count"] == 1
    assert summary["reference_row_count"] == 2
    assert summary["common_prefix_row_count"] == 1
    assert summary["first_extra_converted_row"] is None
    assert summary["first_extra_reference_row"] == {
        "row_number": 2,
        "reference_timestamp_utc": "2026-06-20T00:00:30Z",
        "reference_value": "-0.009794",
    }


def test_cli_writes_diff_report_before_exiting_on_row_count_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = staging_repo_root(tmp_path)
    monkeypatch.setattr(tide_conversion, "_protected_repo_roots", lambda: (repo_root.resolve(),))
    workbook_path = repo_root / "clock" / "professional.xlsx"
    workbook_path.parent.mkdir(parents=True)
    write_demo_workbook(workbook_path)
    reference = repo_root / "results" / "professional_tidal_delta_30s.csv"
    write_csv(
        reference,
        [
            ("2026-06-20T00:00:00Z", "-0.019588"),
            ("2026-06-20T00:00:30Z", "-0.009794"),
        ],
    )
    output_dir = repo_root / "results" / "audit-v1" / "staging" / "cli"

    result = CliRunner().invoke(
        app,
        [
            "--input",
            str(workbook_path),
            "--compare",
            str(reference),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code != 0
    assert {path.name for path in output_dir.iterdir()} == {CONVERTED_FILENAME, DIFF_FILENAME}
    payload = json.loads((output_dir / DIFF_FILENAME).read_text(encoding="utf-8"))
    assert payload["comparison_summary"]["converted_row_count"] == 3
    assert payload["comparison_summary"]["reference_row_count"] == 2
    assert payload["comparison_summary"]["first_extra_converted_row"] == {
        "row_number": 3,
        "converted_timestamp_utc": "2026-06-20T00:01:00Z",
        "converted_value": "-0.04897",
    }


def test_cli_when_tolerate_mismatch_records_and_exits_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = staging_repo_root(tmp_path)
    monkeypatch.setattr(tide_conversion, "_protected_repo_roots", lambda: (repo_root.resolve(),))
    workbook_path = repo_root / "clock" / "professional.xlsx"
    workbook_path.parent.mkdir(parents=True)
    write_demo_workbook(workbook_path)
    reference = repo_root / "results" / "professional_tidal_delta_30s.csv"
    write_csv(
        reference,
        [
            ("2026-06-20T00:00:00Z", "-0.019588"),
            ("2026-06-20T00:00:30Z", "-0.009794"),
        ],
    )
    base_args = ["--input", str(workbook_path), "--compare", str(reference)]

    tolerated_dir = repo_root / "results" / "audit-v1" / "staging" / "tolerate"
    tolerated = CliRunner().invoke(app, [*base_args, "--output-dir", str(tolerated_dir), "--tolerate-mismatch"])
    assert tolerated.exit_code == 0
    assert {path.name for path in tolerated_dir.iterdir()} == {CONVERTED_FILENAME, DIFF_FILENAME}

    strict_dir = repo_root / "results" / "audit-v1" / "staging" / "strict"
    strict = CliRunner().invoke(app, [*base_args, "--output-dir", str(strict_dir)])
    assert strict.exit_code != 0
