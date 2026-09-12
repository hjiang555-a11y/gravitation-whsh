"""Narrow parsed artifact contract for the independent tidal report (no analysis I/O)."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal, DecimalException, localcontext
from math import isclose
from pathlib import Path
from typing import Annotated, Final, Literal, assert_never

from pydantic import BaseModel, ConfigDict, Field, ValidationError

Scenario = Literal["raw", "theory", "empirical"]
SCENARIOS: Final[tuple[Scenario, ...]] = ("raw", "theory", "empirical")
COEFFICIENTS: Final = dict(zip(SCENARIOS, map(Decimal, ("0", "-1", "-0.54")), strict=True))
PositiveInt = Annotated[int, Field(gt=0)]
NonnegativeFloat = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class ReportError(ValueError):
    """An incomplete or inconsistent artifact set must not produce a report."""
    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class Center(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)
    coefficient: Decimal
    R_duration: Annotated[Decimal, Field(gt=0)]
    total_samples: PositiveInt
    nsegments: PositiveInt
    duration_s: PositiveInt
    delta_R: Decimal
    delta_fractional_1e18: Decimal


class Metadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    decimal_precision: Literal[80]


class Summary(BaseModel):
    model_config = ConfigDict(frozen=True)
    scenarios: dict[Scenario, Center]
    metadata: Metadata


class RatioRow(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)
    scenario: Scenario
    coefficient: Decimal
    group: PositiveInt
    n_valid: PositiveInt
    duration_s: PositiveInt
    t_start_beijing: datetime
    t_end_beijing: datetime
    t_start_utc: datetime
    t_end_utc: datetime
    n_continuous_runs: PositiveInt
    longest_run_s: PositiveInt
    R: Annotated[Decimal, Field(gt=0)]
    delta_R: Decimal
    delta_fractional_1e18: Decimal


class StabilityRow(BaseModel):
    model_config = ConfigDict(frozen=True, allow_inf_nan=False)
    scenario: Scenario
    coefficient: Decimal
    group: PositiveInt
    tau_s: PositiveInt
    n_pairs: Annotated[int, Field(ge=0)]
    sigma_y: NonnegativeFloat | None
    sigma_factor_vs_raw: NonnegativeFloat | None


@dataclass(frozen=True, slots=True)
class ReportData:
    summary: Summary
    ratios: tuple[RatioRow, ...]
    stability: tuple[StabilityRow, ...]

    @property
    def groups(self) -> tuple[int, ...]:
        return tuple(sorted(row.group for row in self.ratios if row.scenario == "raw"))


def check_changes(center: Center | RatioRow, reference: Decimal) -> None:
    """Check Decimal deltas at the source's 80-digit arithmetic precision."""
    match center:
        case Center(R_duration=ratio):
            pass
        case RatioRow(R=ratio):
            pass
        case unreachable:
            assert_never(unreachable)
    if center.delta_R != ratio - reference or center.delta_fractional_1e18 != (ratio / reference - 1) * Decimal("1e18"):
        raise ReportError("ratio/delta_R/delta_fractional_1e18 mismatch")


def read_report(directory: Path) -> ReportData:
    """Read all three artifacts, then reconcile their numeric and sampling contracts."""
    try:
        summary = Summary.model_validate_json((directory / "summary.json").read_text(encoding="utf-8"))
        with (directory / "ratio_scenarios.csv").open(newline="", encoding="utf-8") as stream:
            ratios = tuple(RatioRow.model_validate(row) for row in csv.DictReader(stream))
        with (directory / "stability.csv").open(newline="", encoding="utf-8") as stream:
            stability = tuple(StabilityRow.model_validate({key: value or None for key, value in row.items()}) for row in csv.DictReader(stream))
        data = ReportData(summary, ratios, stability)
        with localcontext() as context:
            context.prec = summary.metadata.decimal_precision
            reconcile(data)
        return data
    except (OSError, UnicodeError, csv.Error, ValidationError, DecimalException) as error:
        raise ReportError(f"cannot read a consistent tidal artifact set: {error}") from error


def reconcile(data: ReportData) -> None:
    """Reject missing/duplicate groups, mismatched weights, deltas, grids or factors."""
    summary = data.summary.scenarios
    if set(summary) != set(SCENARIOS):
        raise ReportError("summary must contain raw, theory and empirical")
    raw = {row.group: row for row in data.ratios if row.scenario == "raw"}
    if len(raw) != summary["raw"].nsegments:
        raise ReportError("raw groups disagree with summary nsegments")
    for name in SCENARIOS:
        rows = tuple(row for row in data.ratios if row.scenario == name)
        center = summary[name]
        total = sum(row.n_valid for row in rows)
        if len(rows) != len(raw) or {row.group for row in rows} != set(raw):
            raise ReportError(f"{name}: missing or duplicate ratio groups")
        if center.nsegments != len(raw) or center.total_samples != total or center.duration_s != total:
            raise ReportError(f"{name}: summary sample counts/duration disagree")
        weighted = sum((row.R * row.n_valid for row in rows), Decimal(0)) / total
        if weighted != center.R_duration or center.coefficient != COEFFICIENTS[name]:
            raise ReportError(f"{name}: summary center/coefficient disagrees with CSV")
        check_changes(center, summary["raw"].R_duration)
        for row in rows:
            baseline = raw[row.group]
            fields = ("n_valid", "duration_s", "t_start_beijing", "t_end_beijing", "t_start_utc", "t_end_utc", "n_continuous_runs", "longest_run_s")
            if any(getattr(row, field) != getattr(baseline, field) for field in fields):
                raise ReportError(f"{name}/{row.group}: retained sample metadata differs")
            if row.coefficient != COEFFICIENTS[name] or row.duration_s != row.n_valid or row.longest_run_s > row.n_valid:
                raise ReportError(f"{name}/{row.group}: coefficient/duration/run mismatch")
            if row.t_start_beijing - row.t_start_utc != timedelta(hours=8) or row.t_end_beijing - row.t_end_utc != timedelta(hours=8):
                raise ReportError(f"{name}/{row.group}: timestamps do not use minus-eight hours")
            check_changes(row, baseline.R)
    points = {(row.scenario, row.group, row.tau_s): row for row in data.stability}
    expected: set[tuple[Scenario, int, int]] = set()
    for group, row in raw.items():
        maximum = row.longest_run_s // 4
        taus = {2**i for i in range(maximum.bit_length())} | {t for t in (600, 1200, 3600, 7200) if t <= maximum}
        expected.update((name, group, tau) for name in SCENARIOS for tau in taus)
    if len(points) != len(data.stability) or set(points) != expected:
        raise ReportError("stability groups/tau grids are missing, duplicated or inconsistent with retained runs")
    for row in data.stability:
        baseline = points[("raw", row.group, row.tau_s)]
        segment = raw[row.group]
        if row.coefficient != COEFFICIENTS[row.scenario] or row.n_pairs != baseline.n_pairs:
            raise ReportError("stability coefficients or overlapping counts differ across scenarios")
        if segment.n_continuous_runs == 1 and row.n_pairs != segment.n_valid - 2 * row.tau_s + 1:
            raise ReportError("stability pair count disagrees with the retained continuous run")
        if (row.sigma_y is None) != (row.n_pairs == 0):
            raise ReportError("missing OADEV must match zero available pairs")
        factor = row.sigma_y / baseline.sigma_y if row.sigma_y is not None and baseline.sigma_y is not None and baseline.sigma_y > 0 else None
        if factor is None:
            if row.sigma_factor_vs_raw is not None:
                raise ReportError("factor must be absent when raw OADEV is zero/unavailable")
        elif row.sigma_factor_vs_raw is None or not isclose(factor, row.sigma_factor_vs_raw, rel_tol=2e-15, abs_tol=0):
            raise ReportError("stability factor disagrees with corrected/raw OADEV")
