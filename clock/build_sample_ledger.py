"""Build the authoritative per-segment retained-sample ledger."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import typer

from clock import shared
from clock.data_provenance import FileDigest, TimestampQuality, describe_file, inspect_timestamp_labels
from clock.sample_selection import DEFAULT_SELECTION_PLAN, SelectedSegment, select_segments

app = typer.Typer(add_completion=False)
OUTPUT_FILENAMES = ("sample_ledger.csv", "time_quality.json")
RAW_PATTERNS = ("Freq_B_2_2606*.txt", "Freq_B_2_2607*.txt", "Freq_B_2_2608*.txt")
EXTERNAL_REPORTED_TOTALS = (
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
)


def configured_data_dir() -> Path:
    override = os.getenv("CLOCK_DATA_DIR")
    return Path(override).resolve() if override else shared.DATA_DIR.resolve()


def list_raw_beat_files(data_dir: Path | None = None) -> tuple[Path, ...]:
    base = (data_dir or configured_data_dir()).resolve()
    files: list[Path] = []
    for pattern in RAW_PATTERNS:
        files.extend(sorted(base.glob(pattern)))
    return tuple(files)


def load_selected_segments() -> tuple[SelectedSegment, ...]:
    """Load the shared retained segments used by all clock-ratio callers."""
    return select_segments(*shared.load_beat(), DEFAULT_SELECTION_PLAN)


def computed_total_final(segments: tuple[SelectedSegment, ...]) -> int:
    return sum(segment.diagnostics.n_final for segment in segments)


def build_sample_ledger_rows(segments: tuple[SelectedSegment, ...]) -> tuple[dict[str, str | int], ...]:
    rows: list[dict[str, str | int]] = []
    for segment in segments:
        diagnostics = segment.diagnostics
        rows.append({
            "group": segment.group,
            "n_window": diagnostics.n_window,
            "n_excluded": diagnostics.n_excluded,
            "n_plausible": diagnostics.n_plausible,
            "n_jump_valid": diagnostics.n_jump_valid,
            "n_longest_span": diagnostics.n_longest_span,
            "n_removed_start": diagnostics.n_removed_start,
            "n_removed_end": diagnostics.n_removed_end,
            "n_final": diagnostics.n_final,
            "source_span_start": diagnostics.source_span_start,
            "source_span_stop": diagnostics.source_span_stop,
            "retained_start_beijing": str(segment.times[0]),
            "retained_end_beijing": str(segment.times[-1]),
        })
    return tuple(rows)


def _serialize_digest(digest: FileDigest) -> dict[str, Any]:
    return {
        "relative_path": digest.relative_path,
        "sha256": digest.sha256,
        "size_bytes": digest.size_bytes,
        "mtime_utc": digest.mtime_utc.isoformat(),
    }


def _serialize_quality(quality: TimestampQuality) -> dict[str, Any]:
    return {
        "n_rows": quality.n_rows,
        "n_parse_errors": quality.n_parse_errors,
        "n_duplicates": quality.n_duplicates,
        "n_reversals": quality.n_reversals,
        "n_gaps": quality.n_gaps,
        "max_gap_s": quality.max_gap_s,
        "max_abs_jitter_s": quality.max_abs_jitter_s,
        "first_label_utc8": quality.first_label_utc8.isoformat(),
        "last_label_utc8": quality.last_label_utc8.isoformat(),
    }


def build_time_quality_report(raw_files: tuple[Path, ...], segments: tuple[SelectedSegment, ...]) -> dict[str, Any]:
    base_dir = configured_data_dir()
    return {
        "computed_total_final": computed_total_final(segments),
        "computed_total_status": "established",
        "computed_total_note": "Current executable sample ledger total from shared select_segments(); reconciliation-only external totals are recorded separately and never used in computations.",
        "external_reported_totals": list(EXTERNAL_REPORTED_TOTALS),
        "files": [
            {
                "digest": _serialize_digest(describe_file(path, base_dir=base_dir)),
                "timestamp_quality": _serialize_quality(inspect_timestamp_labels(path)),
            }
            for path in raw_files
        ]
    }


def validate_output_dir(output_dir: Path) -> Path:
    target = output_dir.resolve()
    if target.is_relative_to(shared.DATA_DIR):
        raise ValueError(f"protected raw-data directory: {target}")
    allowed_root = shared.REPO_ROOT / "results" / "audit-v1"
    if target.is_relative_to(shared.REPO_ROOT) and not target.is_relative_to(allowed_root):
        raise ValueError(f"protected repository source/legacy output directory: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"output directory is not a directory: {target}")
    for filename in OUTPUT_FILENAMES:
        path = target / filename
        if path.is_symlink():
            raise ValueError(f"output filename is a symlink: {path}")
        if path.exists() and (not path.is_file() or path.stat().st_nlink > 1):
            raise ValueError(f"output filename is not an independent regular file: {path}")
    return target


def _write_csv_atomic(path: Path, rows: tuple[dict[str, str | int], ...]) -> None:
    fieldnames = [
        "group", "n_window", "n_excluded", "n_plausible", "n_jump_valid", "n_longest_span",
        "n_removed_start", "n_removed_end", "n_final", "source_span_start", "source_span_stop",
        "retained_start_beijing", "retained_end_beijing",
    ]
    with NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent) as temp:
        writer = csv.DictWriter(temp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        temp_path = Path(temp.name)
    temp_path.replace(path)


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as temp:
        json.dump(payload, temp, ensure_ascii=False, indent=2)
        temp.write("\n")
        temp_path = Path(temp.name)
    temp_path.replace(path)


@app.command()
def main(output_dir: Path = typer.Option(..., exists=False, file_okay=False, dir_okay=True)) -> None:
    try:
        target = validate_output_dir(output_dir)
        data_dir = configured_data_dir()
        raw_files = list_raw_beat_files(data_dir)
        if not raw_files:
            raise ValueError(f"no raw beat data files found in {data_dir}")
        original_data_dir = shared.DATA_DIR
        shared.DATA_DIR = data_dir
        try:
            segments = load_selected_segments()
        finally:
            shared.DATA_DIR = original_data_dir
        rows = build_sample_ledger_rows(segments)
        report = build_time_quality_report(raw_files, segments)
        target.mkdir(parents=True, exist_ok=True)
        _write_csv_atomic(target / OUTPUT_FILENAMES[0], rows)
        _write_json_atomic(target / OUTPUT_FILENAMES[1], report)
    except (OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote {len(rows)} segment ledger rows and time quality to {target}")


if __name__ == "__main__":
    app()
