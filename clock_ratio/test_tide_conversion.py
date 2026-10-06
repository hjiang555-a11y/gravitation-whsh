"""Executable audit coverage for professional tide conversion."""
from __future__ import annotations

import csv
import os
from decimal import Decimal
from pathlib import Path

import pytest
from typer.testing import CliRunner

from clock import shared
from clock_ratio.tide_conversion import (
    CONVERTED_FILENAME,
    DIFF_FILENAME,
    TideConversionConfig,
    app,
    compare_tide_csv,
    convert_height_mm_to_potential,
    convert_workbook,
    validate_output_dir,
)


ROOT = Path(__file__).resolve().parents[1]


def write_demo_workbook(path: Path) -> None:
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

    rows = [
        ("20260620000000", Decimal("10.0"), Decimal("9.0"), Decimal("-2.0"), Decimal("1.0"), Decimal("-2.0")),
        ("20260620000030", Decimal("5.5"), Decimal("5.0"), Decimal("-1.0"), Decimal("0.5"), Decimal("-1.0")),
        ("20260620000100", Decimal("3.0"), Decimal("6.0"), Decimal("0.0"), Decimal("2.0"), Decimal("-5.0")),
    ]
    for row_index, (stamp, solid_cas, solid_sha, ocean_cas, ocean_sha, combined) in enumerate(rows, start=3):
        sheet[f"A{row_index}"] = stamp
        sheet[f"B{row_index}"] = float(solid_cas)
        sheet[f"C{row_index}"] = float(solid_sha)
        sheet[f"E{row_index}"] = float(ocean_cas)
        sheet[f"F{row_index}"] = float(ocean_sha)
        sheet[f"H{row_index}"] = float(solid_cas - solid_sha)
        sheet[f"I{row_index}"] = float(ocean_cas - ocean_sha)
        sheet[f"J{row_index}"] = float(combined)

    workbook.save(path)


def test_height_difference_conversion_preserves_direction() -> None:
    config = TideConversionConfig(
        gravity_m_s2=Decimal("9.794"),
        direction="CAS-minus-SHA",
        timezone="UTC",
    )

    assert convert_height_mm_to_potential(Decimal("1"), config) == Decimal("0.009794")
    assert convert_height_mm_to_potential(Decimal("-1"), config) == Decimal("-0.009794")


def test_convert_workbook_writes_expected_utc_grid_from_comprehensive_difference_column(tmp_path: Path) -> None:
    workbook_path = tmp_path / "professional.xlsx"
    output_csv = tmp_path / CONVERTED_FILENAME
    write_demo_workbook(workbook_path)

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


def test_compare_tide_csv_reports_first_difference_and_max_abs_deltas(tmp_path: Path) -> None:
    converted = tmp_path / CONVERTED_FILENAME
    converted.write_text(
        "timestamp_utc,total_tidal_delta_m2_s2_surface\n"
        "2026-06-20T00:00:00Z,-0.019588\n"
        "2026-06-20T00:00:30Z,-0.009794\n",
        encoding="utf-8",
    )
    reference = tmp_path / "reference.csv"
    reference.write_text(
        "timestamp_utc,total_tidal_delta_m2_s2_surface\n"
        "2026-06-20T00:00:30Z,-0.019500\n"
        "2026-06-20T00:01:00Z,-0.009700\n",
        encoding="utf-8",
    )

    summary = compare_tide_csv(converted, reference)

    assert summary["row_count"] == 2
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


def test_validate_output_dir_rejects_protected_paths_and_input_collisions(tmp_path: Path) -> None:
    workbook_path = tmp_path / "professional.xlsx"
    reference_csv = tmp_path / "reference.csv"
    workbook_path.write_text("placeholder", encoding="utf-8")
    reference_csv.write_text("placeholder", encoding="utf-8")

    with pytest.raises(ValueError, match="protected repository source/legacy output directory"):
        validate_output_dir(ROOT / "results", workbook_path=workbook_path, compare_csv=reference_csv)

    collision_dir = tmp_path / "collision"
    collision_dir.mkdir()
    with pytest.raises(ValueError, match="collides with input"):
        validate_output_dir(collision_dir, workbook_path=workbook_path, compare_csv=collision_dir / CONVERTED_FILENAME)


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_validate_output_dir_rejects_linked_output_files(tmp_path: Path, kind: str) -> None:
    victim = tmp_path / "victim.csv"
    victim.write_text("unchanged", encoding="utf-8")
    workbook_path = tmp_path / "professional.xlsx"
    reference_csv = tmp_path / "reference.csv"
    workbook_path.write_text("workbook", encoding="utf-8")
    reference_csv.write_text("reference", encoding="utf-8")
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    target = output_dir / CONVERTED_FILENAME
    if kind == "symlink":
        target.symlink_to(victim)
    else:
        os.link(victim, target)

    with pytest.raises(ValueError, match="symlink|independent regular file"):
        validate_output_dir(output_dir, workbook_path=workbook_path, compare_csv=reference_csv)
    assert victim.read_text(encoding="utf-8") == "unchanged"


def test_cli_writes_conversion_copy_and_diff_report(tmp_path: Path) -> None:
    workbook_path = tmp_path / "professional.xlsx"
    write_demo_workbook(workbook_path)
    reference = tmp_path / "reference.csv"
    reference.write_text(
        "timestamp_utc,total_tidal_delta_m2_s2_surface\n"
        "2026-06-20T00:00:00Z,-0.019588\n"
        "2026-06-20T00:00:30Z,-0.009794\n"
        "2026-06-20T00:01:00Z,-0.048970\n",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "--input",
            str(workbook_path),
            "--compare",
            str(reference),
            "--output-dir",
            str(tmp_path / "audit"),
        ],
    )

    assert result.exit_code == 0, result.output
    assert {path.name for path in (tmp_path / "audit").iterdir()} == {CONVERTED_FILENAME, DIFF_FILENAME}
