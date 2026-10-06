"""Auditable conversion of professional tide workbook rows into an executable CSV."""
from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal

import typer
from openpyxl import load_workbook

from clock import shared


CONVERTED_FILENAME = "professional_tidal_delta_30s.csv"
DIFF_FILENAME = "professional_tidal_delta_30s.diff.json"
OUTPUT_FILENAMES = (CONVERTED_FILENAME, DIFF_FILENAME)
EXPECTED_HEADERS = {
    "B1": "固体潮",
    "B2": "CAS",
    "C2": "SHA",
    "E1": "海潮",
    "E2": "CAS",
    "F2": "SHA",
    "H2": "CAS-SHA",
}
COMBINED_HEADER_PREFIX = "综合差"
STEP_TOLERANCE_MM = Decimal("1e-9")
DEFAULT_WORKBOOK = Path("clock") / "武汉-上海潮汐结果（0620-0910）-30秒间隔数据.xlsx"
DEFAULT_COMPARE = Path("results") / CONVERTED_FILENAME
app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@dataclass(frozen=True, slots=True)
class TideConversionConfig:
    gravity_m_s2: Decimal
    direction: Literal["CAS-minus-SHA"]
    timezone: Literal["UTC"]
    source_column: str = "综合差"
    expected_step_s: int = 30


DEFAULT_CONFIG = TideConversionConfig(
    gravity_m_s2=Decimal("9.794"),
    direction="CAS-minus-SHA",
    timezone="UTC",
)


@dataclass(frozen=True, slots=True)
class ConvertedRow:
    timestamp_utc: str
    total_tidal_delta_m2_s2_surface: Decimal


class ConversionError(ValueError):
    """User-facing validation errors for workbook conversion and comparison."""


def _main_checkout_root() -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(shared.REPO_ROOT), "rev-parse", "--git-common-dir"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    common_dir = Path(result.stdout.strip())
    if not common_dir.is_absolute():
        common_dir = (shared.REPO_ROOT / common_dir).resolve()
    else:
        common_dir = common_dir.resolve()
    return common_dir.parent


def _protected_repo_roots() -> tuple[Path, ...]:
    roots = {shared.REPO_ROOT.resolve()}
    main_root = _main_checkout_root()
    if main_root is not None:
        roots.add(main_root.resolve())
    return tuple(sorted(roots))


def _resolve_cli_path(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    candidate = (Path.cwd() / path).resolve()
    if candidate.exists():
        return candidate
    for root in _protected_repo_roots():
        repo_candidate = (root / path).resolve()
        if repo_candidate.exists():
            return repo_candidate
    return candidate


def _decimal_to_str(value: Decimal) -> str:
    return format(value.normalize(), "f")


def _write_csv_atomic(path: Path, rows: tuple[ConvertedRow, ...]) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent) as temp:
        writer = csv.DictWriter(temp, fieldnames=["timestamp_utc", "total_tidal_delta_m2_s2_surface"])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "timestamp_utc": row.timestamp_utc,
                "total_tidal_delta_m2_s2_surface": _decimal_to_str(row.total_tidal_delta_m2_s2_surface),
            })
        temp_path = Path(temp.name)
    temp_path.replace(path)


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as temp:
        json.dump(payload, temp, ensure_ascii=False, indent=2)
        temp.write("\n")
        temp_path = Path(temp.name)
    temp_path.replace(path)


def _parse_workbook_timestamp(raw: object) -> str:
    if raw is None:
        raise ConversionError("missing timestamp in workbook")
    if isinstance(raw, datetime):
        moment = raw
    else:
        text = str(raw).strip()
        if text.endswith(".0"):
            text = text[:-2]
        try:
            moment = datetime.strptime(text, "%Y%m%d%H%M%S")
        except ValueError as error:
            raise ConversionError(f"invalid workbook timestamp: {raw}") from error
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_decimal(raw: object, *, label: str) -> Decimal:
    if raw is None or str(raw).strip() == "":
        raise ConversionError(f"missing numeric value for {label}")
    return Decimal(str(raw))


def _validate_headers(sheet, config: TideConversionConfig) -> None:
    for cell, expected_prefix in EXPECTED_HEADERS.items():
        value = sheet[cell].value
        if value is None or not str(value).startswith(expected_prefix):
            raise ConversionError(f"unexpected workbook header at {cell}: {value!r}")
    combined = sheet["J1"].value
    if combined is None or not str(combined).startswith(config.source_column):
        raise ConversionError(f"unexpected workbook header at J1: {combined!r}")


def convert_height_mm_to_potential(value_mm: Decimal, config: TideConversionConfig) -> Decimal:
    return value_mm * config.gravity_m_s2 / Decimal(1000)


def _rows_from_workbook(workbook_path: Path, config: TideConversionConfig) -> tuple[ConvertedRow, ...]:
    workbook = load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        _validate_headers(sheet, config)
        converted: list[ConvertedRow] = []
        previous_stamp: datetime | None = None
        seen_stamps: set[str] = set()
        for row_number, row in enumerate(sheet.iter_rows(min_row=3, max_col=10, values_only=True), start=3):
            if not any(value is not None and str(value).strip() != "" for value in row):
                continue
            stamp = _parse_workbook_timestamp(row[0])
            if stamp in seen_stamps:
                raise ConversionError(f"duplicate UTC timestamp at workbook row {row_number}: {stamp}")
            seen_stamps.add(stamp)
            moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
            if previous_stamp is not None:
                delta_s = int((moment - previous_stamp).total_seconds())
                if delta_s != config.expected_step_s:
                    raise ConversionError(
                        f"non-{config.expected_step_s}s step at workbook row {row_number}: {delta_s}s"
                    )
            previous_stamp = moment
            solid_delta = _parse_decimal(row[1], label=f"B{row_number}") - _parse_decimal(row[2], label=f"C{row_number}")
            ocean_delta = _parse_decimal(row[4], label=f"E{row_number}") - _parse_decimal(row[5], label=f"F{row_number}")
            combined_delta = _parse_decimal(row[9], label=f"J{row_number}")
            if abs((solid_delta + ocean_delta) - combined_delta) > STEP_TOLERANCE_MM:
                raise ConversionError(f"combined difference mismatch at workbook row {row_number}")
            converted.append(
                ConvertedRow(
                    timestamp_utc=stamp,
                    total_tidal_delta_m2_s2_surface=convert_height_mm_to_potential(combined_delta, config),
                )
            )
        if not converted:
            raise ConversionError(f"no tide rows found in workbook: {workbook_path}")
        return tuple(converted)
    finally:
        workbook.close()


def convert_workbook(
    workbook_path: Path,
    output_csv: Path,
    config: TideConversionConfig = DEFAULT_CONFIG,
) -> dict[str, object]:
    rows = _rows_from_workbook(workbook_path, config)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    _write_csv_atomic(output_csv, rows)
    return {
        "row_count": len(rows),
        "first_timestamp_utc": rows[0].timestamp_utc,
        "last_timestamp_utc": rows[-1].timestamp_utc,
        "step_seconds": config.expected_step_s,
        "source_column": config.source_column,
    }


def _load_csv_rows(path: Path, *, config: TideConversionConfig) -> tuple[ConvertedRow, ...]:
    with path.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    converted: list[ConvertedRow] = []
    previous_stamp: datetime | None = None
    seen_stamps: set[str] = set()
    for row_number, row in enumerate(rows, start=1):
        stamp = row["timestamp_utc"]
        if stamp in seen_stamps:
            raise ConversionError(f"duplicate UTC timestamp at CSV row {row_number}: {stamp}")
        seen_stamps.add(stamp)
        try:
            moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as error:
            raise ConversionError(f"invalid CSV timestamp at row {row_number}: {stamp}") from error
        if previous_stamp is not None:
            delta_s = int((moment - previous_stamp).total_seconds())
            if delta_s != config.expected_step_s:
                raise ConversionError(f"non-{config.expected_step_s}s step at CSV row {row_number}: {delta_s}s")
        previous_stamp = moment
        converted.append(
            ConvertedRow(
                timestamp_utc=stamp,
                total_tidal_delta_m2_s2_surface=Decimal(row["total_tidal_delta_m2_s2_surface"]),
            )
        )
    if not converted:
        raise ConversionError(f"no tide rows found in CSV: {path}")
    return tuple(converted)


def compare_tide_csv(
    converted_csv: Path,
    reference_csv: Path,
    config: TideConversionConfig = DEFAULT_CONFIG,
) -> dict[str, object]:
    converted_rows = _load_csv_rows(converted_csv, config=config)
    reference_rows = _load_csv_rows(reference_csv, config=config)
    max_abs_time_diff_s = 0
    max_abs_value_diff = Decimal(0)
    first_inconsistent_row: dict[str, object] | None = None
    for row_number, (converted, reference) in enumerate(zip(converted_rows, reference_rows, strict=False), start=1):
        converted_moment = datetime.strptime(converted.timestamp_utc, "%Y-%m-%dT%H:%M:%SZ")
        reference_moment = datetime.strptime(reference.timestamp_utc, "%Y-%m-%dT%H:%M:%SZ")
        time_diff_s = int((converted_moment - reference_moment).total_seconds())
        value_diff = converted.total_tidal_delta_m2_s2_surface - reference.total_tidal_delta_m2_s2_surface
        max_abs_time_diff_s = max(max_abs_time_diff_s, abs(time_diff_s))
        max_abs_value_diff = max(max_abs_value_diff, abs(value_diff))
        if first_inconsistent_row is None and (time_diff_s != 0 or value_diff != 0):
            first_inconsistent_row = {
                "row_number": row_number,
                "converted_timestamp_utc": converted.timestamp_utc,
                "reference_timestamp_utc": reference.timestamp_utc,
                "converted_value": _decimal_to_str(converted.total_tidal_delta_m2_s2_surface),
                "reference_value": _decimal_to_str(reference.total_tidal_delta_m2_s2_surface),
                "time_diff_s": abs(time_diff_s),
                "value_diff": _decimal_to_str(value_diff),
            }
    if len(converted_rows) != len(reference_rows):
        raise ConversionError(
            f"row-count mismatch: converted={len(converted_rows)} reference={len(reference_rows)}"
        )
    return {
        "row_count": len(converted_rows),
        "first_timestamp_utc": converted_rows[0].timestamp_utc,
        "last_timestamp_utc": converted_rows[-1].timestamp_utc,
        "max_abs_time_diff_s": max_abs_time_diff_s,
        "max_abs_value_diff": _decimal_to_str(max_abs_value_diff),
        "first_inconsistent_row": first_inconsistent_row,
    }


def validate_output_dir(output_dir: Path, *, workbook_path: Path, compare_csv: Path) -> Path:
    target = output_dir.resolve()
    protected_inputs = {workbook_path.resolve(), compare_csv.resolve()}
    protected_roots = _protected_repo_roots()
    allowed_roots = tuple(repo_root / "results" / "audit-v1" for repo_root in protected_roots)
    if not any(target.is_relative_to(allowed_root) for allowed_root in allowed_roots):
        for repo_root in protected_roots:
            if target.is_relative_to(repo_root):
                raise ValueError(f"protected repository source/legacy output directory: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"output directory is not a directory: {target}")
    for filename in OUTPUT_FILENAMES:
        path = target / filename
        if path.resolve(strict=False) in protected_inputs:
            raise ValueError(f"output filename collides with input: {path}")
        if path.is_symlink():
            raise ValueError(f"output filename is a symlink: {path}")
        if path.exists() and (not path.is_file() or path.stat().st_nlink > 1):
            raise ValueError(f"output filename is not an independent regular file: {path}")
    return target


@app.command()
def main(
    input: Path = typer.Option(DEFAULT_WORKBOOK, "--input", exists=False, dir_okay=False),
    compare: Path = typer.Option(DEFAULT_COMPARE, "--compare", exists=False, dir_okay=False),
    output_dir: Path = typer.Option(..., "--output-dir", exists=False, file_okay=False, dir_okay=True),
) -> None:
    try:
        input_path = _resolve_cli_path(input)
        compare_path = _resolve_cli_path(compare)
        target = validate_output_dir(output_dir, workbook_path=input_path, compare_csv=compare_path)
        target.mkdir(parents=True, exist_ok=True)
        conversion_summary = convert_workbook(input_path, target / CONVERTED_FILENAME)
        comparison_summary = compare_tide_csv(target / CONVERTED_FILENAME, compare_path)
        report = {
            "config": {
                "gravity_m_s2": _decimal_to_str(DEFAULT_CONFIG.gravity_m_s2),
                "direction": DEFAULT_CONFIG.direction,
                "timezone": DEFAULT_CONFIG.timezone,
                "source_column": DEFAULT_CONFIG.source_column,
                "expected_step_s": DEFAULT_CONFIG.expected_step_s,
            },
            "input_workbook": str(input_path),
            "reference_csv": str(compare_path),
            "conversion_summary": conversion_summary,
            "comparison_summary": comparison_summary,
        }
        _write_json_atomic(target / DIFF_FILENAME, report)
        if comparison_summary["first_inconsistent_row"] is not None:
            raise ConversionError(
                "converted workbook does not match the tracked CSV; see diff report for the first inconsistent row"
            )
    except (ConversionError, OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote converted tide CSV and diff report to {target}")


if __name__ == "__main__":
    app()
