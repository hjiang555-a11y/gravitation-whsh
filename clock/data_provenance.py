"""Provenance helpers for raw beat files and parameter ledgers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from clock_ratio.evidence import EvidenceStatus

FloatArray = NDArray[np.float64]
TimeArray = NDArray[np.datetime64]
UTC8 = timezone(timedelta(hours=8))
UTC = timezone.utc


@dataclass(frozen=True, slots=True)
class FileDigest:
    relative_path: str
    sha256: str
    size_bytes: int
    mtime_utc: datetime


@dataclass(frozen=True, slots=True)
class ParameterEvidence:
    name: str
    group: int | None
    value: Decimal | None
    unit: str
    source_path: str
    inherited_from_group: int | None
    status: EvidenceStatus
    note: str


@dataclass(frozen=True, slots=True)
class TimestampQuality:
    n_rows: int
    n_parse_errors: int
    n_duplicates: int
    n_reversals: int
    n_gaps: int
    max_gap_s: float
    max_abs_jitter_s: float
    first_label_utc8: datetime
    last_label_utc8: datetime


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def describe_file(path: Path, *, base_dir: Path | None = None) -> FileDigest:
    resolved = path.resolve()
    base = (base_dir or Path.cwd()).resolve()
    try:
        relative = str(resolved.relative_to(base))
    except ValueError:
        relative = str(resolved)
    stat = resolved.stat()
    return FileDigest(
        relative_path=relative,
        sha256=sha256_file(resolved),
        size_bytes=stat.st_size,
        mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
    )


def _iter_data_lines(path: Path):
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            yield stripped


def _parse_timestamp_label(date_token: str, time_token: str) -> datetime:
    if "-" in date_token:
        iso_date = date_token
    else:
        yy, mm, day = int(date_token[:2]), int(date_token[2:4]), int(date_token[4:6])
        iso_date = f"{2000 + yy:04d}-{mm:02d}-{day:02d}"

    if ":" in time_token:
        stamp = datetime.fromisoformat(f"{iso_date}T{time_token}")
        return stamp.replace(tzinfo=UTC8)

    whole, dot, frac = time_token.partition(".")
    hh = int(whole) // 10000
    minute = (int(whole) // 100) % 100
    second = int(whole) % 100
    stamp = datetime.fromisoformat(f"{iso_date}T{hh:02d}:{minute:02d}:{second:02d}").replace(tzinfo=UTC8)
    if dot:
        stamp += timedelta(seconds=float(f"0.{frac}"))
    return stamp


def inspect_timestamp_labels(path: Path) -> TimestampQuality:
    labels: list[datetime] = []
    n_rows = 0
    n_parse_errors = 0
    for line in _iter_data_lines(path):
        n_rows += 1
        tokens = line.split()
        try:
            labels.append(_parse_timestamp_label(tokens[0], tokens[1]))
        except (IndexError, ValueError):
            n_parse_errors += 1
    if not labels:
        raise ValueError(f"no parseable timestamp labels in {path}")

    label_ns = np.array([label.replace(tzinfo=None) for label in labels], dtype="datetime64[ns]")
    diffs_ns = np.diff(label_ns)
    diffs_s = diffs_ns.astype("timedelta64[ns]").astype(np.int64) / 1_000_000_000
    positive = diffs_s[diffs_s > 0]
    return TimestampQuality(
        n_rows=n_rows,
        n_parse_errors=n_parse_errors,
        n_duplicates=int(np.count_nonzero(diffs_s == 0)),
        n_reversals=int(np.count_nonzero(diffs_s < 0)),
        n_gaps=int(np.count_nonzero(diffs_s > 1.0)),
        max_gap_s=float(positive.max()) if positive.size else 0.0,
        max_abs_jitter_s=float(np.max(np.abs(diffs_s - 1.0))) if diffs_s.size else 0.0,
        first_label_utc8=labels[0],
        last_label_utc8=labels[-1],
    )


def timestamp_quality_status(quality: TimestampQuality) -> EvidenceStatus:
    if quality.n_parse_errors:
        return EvidenceStatus.supported_with_limitations
    return EvidenceStatus.established


def uniform_file_axis(first: np.datetime64, count: int) -> TimeArray:
    if count < 0:
        raise ValueError("count must be non-negative")
    return first + np.arange(count).astype("timedelta64[s]")


def load_beat_file(path: Path) -> tuple[TimeArray, FloatArray]:
    from clock.shared import first_stamp

    beat = np.loadtxt(path, comments="#", usecols=(10,), ndmin=1)
    return uniform_file_axis(first_stamp(path), beat.size), beat.astype(float)
