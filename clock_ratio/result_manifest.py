"""Authoritative analysis manifest: schemas, reconciliation, hashing, atomic write.

The manifest is the single machine-checkable record of what the audit consumed
and what it produced: relative paths plus SHA-256 for inputs, parameters, and
staging products; typed scenario numbers for the provisional 16-segment primary,
the 17-segment sensitivity, the leave-one-out sweep, the tide conversion, and
the uncertainty budget. `reconcile_manifest` cross-checks internal
consistency; the `verify_*` functions re-hash files on disk.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from clock_ratio.evidence import EvidenceStatus


class ManifestError(ValueError):
    """Raised when a manifest cannot be read, reconciled, or verified."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LEAVE_ONE_OUT_GROUPS = frozenset(range(1, 18))
_PRIMARY_GROUPS = _LEAVE_ONE_OUT_GROUPS - {9}
_COMBINATION_FLOAT_FIELDS = (
    "y_wls_precision_1e18",
    "u_wls",
    "chi2",
    "chi2_red",
    "p_chi2",
    "birge_ratio",
    "u_birge",
    "xi_mp",
    "u_mp",
    "mu_bayes",
    "u_stat_bayes",
    "xi_bayes",
)


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    relative_path: str
    sha256: str
    size_bytes: int
    mtime_utc: datetime
    provider: str | None
    command: tuple[str, ...]
    distributable: bool | None
    status: EvidenceStatus


class CombinationManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    R_seg1: str
    R_wls: str
    R_mp: str
    R_bayes: str
    y_wls_precision_1e18: float
    u_wls: float
    chi2: float
    dof: int
    chi2_red: float
    p_chi2: float
    birge_ratio: float
    u_birge: float
    xi_mp: float
    u_mp: float
    mu_bayes: float
    u_stat_bayes: float
    xi_bayes: float


class StatisticalScenarioManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    scenario: Literal["raw", "theory", "empirical"]
    coefficient: str
    included_groups: tuple[int, ...]
    excluded_groups: tuple[int, ...]
    n_segments: int
    total_samples: int
    duration_weighted_ratio: str
    segment_ratios: tuple[str, ...]
    segment_n_valid: tuple[int, ...]
    segment_statuses: tuple[EvidenceStatus, ...]
    combination: CombinationManifest


class LeaveOneOutManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    excluded_group: int
    R_wls: str
    R_mp: str
    R_bayes: str
    chi2_red: float
    u_wls: float


class TideMethodManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_column: str
    direction: str
    timezone: str
    expected_step_s: int
    gravity_m_s2: str
    converted_row_count: int
    reference_row_count: int
    common_prefix_row_count: int
    max_abs_time_diff_s: float
    max_abs_value_diff: str
    first_inconsistent_row_number: int | None
    first_inconsistent_value_diff: str | None
    status: EvidenceStatus


class BudgetComponentModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    correction: str | None
    standard_uncertainty: str | None
    source: str
    status: EvidenceStatus
    required: bool


class UncertaintyBudgetModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    components: tuple[BudgetComponentModel, ...]
    correlation: tuple[tuple[float, ...], ...]
    known_quadrature: str
    total_standard_uncertainty: str | None
    status: EvidenceStatus


class ResultManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal["1.0", "1.1"] = "1.1"
    git_commit: str
    dirty: bool
    python: str
    packages: dict[str, str]
    inputs: tuple[ProvenanceRecord, ...]
    parameters: ProvenanceRecord
    products: tuple[ProvenanceRecord, ...]
    parameter_ledger_sha256: str
    sample_ledger_sha256: str
    primary_16: StatisticalScenarioManifest
    sensitivity_17: StatisticalScenarioManifest
    leave_one_out: dict[int, LeaveOneOutManifest]
    tide_method: TideMethodManifest
    uncertainty_budget: UncertaintyBudgetModel
    commands: tuple[str, ...]


def read_manifest(path: Path) -> ResultManifest:
    try:
        payload = json.loads(Path(path).read_bytes())
        return ResultManifest.model_validate(payload)
    except (OSError, ValueError) as error:
        raise ManifestError(f"cannot read manifest {path}: {error}") from error


def _check_group_membership(
    scenario: StatisticalScenarioManifest,
    *,
    expected: frozenset[int],
    excluded: tuple[int, ...],
    label: str,
) -> None:
    groups = scenario.included_groups
    if groups != tuple(sorted(set(groups))):
        raise ManifestError(f"rule 3/4: {label} included_groups must be sorted and duplicate-free")
    if set(groups) != set(expected):
        raise ManifestError(f"rule 3/4: {label} included_groups do not match the expected membership")
    if scenario.excluded_groups != excluded:
        raise ManifestError(f"rule 3/4: {label} excluded_groups do not match the expected exclusion")


def _check_scenario(scenario: StatisticalScenarioManifest, *, label: str) -> None:
    if not (
        scenario.n_segments
        == len(scenario.included_groups)
        == len(scenario.segment_ratios)
        == len(scenario.segment_n_valid)
        == len(scenario.segment_statuses)
    ):
        raise ManifestError(f"rule 5: {label} segment counts are inconsistent")
    if scenario.total_samples != sum(scenario.segment_n_valid):
        raise ManifestError(f"rule 5: {label} total_samples does not match the segment sum")
    if any(count < 0 for count in scenario.segment_n_valid):
        raise ManifestError(f"rule 5: {label} has a negative segment_n_valid entry")
    total = sum(scenario.segment_n_valid)
    if total == 0:
        raise ManifestError(f"rule 5: {label} has zero total retained samples")
    try:
        parsed_ratios = tuple(Decimal(ratio) for ratio in scenario.segment_ratios)
    except (ArithmeticError, ValueError) as error:
        raise ManifestError(f"rule 5: {label} segment values are not Decimal-parsable: {error}") from error
    if not all(ratio.is_finite() for ratio in parsed_ratios):
        raise ManifestError(f"rule 5: {label} has a non-finite segment ratio")
    try:
        with localcontext() as context:
            context.prec = 80
            recomputed = sum(
                (
                    Decimal(n) * ratio
                    for ratio, n in zip(parsed_ratios, scenario.segment_n_valid)
                ),
                Decimal(0),
            ) / Decimal(total)
    except (ArithmeticError, ValueError) as error:
        raise ManifestError(f"rule 5: {label} segment values are not Decimal-parsable: {error}") from error
    if not recomputed.is_finite():
        raise ManifestError(f"rule 5: {label} recomputed duration is not finite")
    if str(recomputed) != scenario.duration_weighted_ratio:
        raise ManifestError(
            f"rule 5: {label} duration_weighted_ratio does not match the segment recomputation"
        )


def _finite_decimal(value: str | None, *, label: str) -> Decimal | None:
    if value is None:
        return None
    try:
        parsed = Decimal(value)
    except (ArithmeticError, ValueError) as error:
        raise ManifestError(f"rule 8: {label} is not a Decimal: {error}") from error
    if not parsed.is_finite():
        raise ManifestError(f"rule 8: {label} is not finite")
    return parsed


def reconcile_manifest(manifest: ResultManifest) -> None:
    """Cross-check internal consistency; raise ManifestError naming the failed rule."""
    # Rule 1: identity, inputs presence, unique product paths.
    if not manifest.git_commit:
        raise ManifestError("rule 1: git_commit must be non-empty")
    if not manifest.inputs:
        raise ManifestError("rule 1: inputs must be non-empty")
    product_paths = [record.relative_path for record in manifest.products]
    if len(set(product_paths)) != len(product_paths):
        raise ManifestError("rule 1: duplicate relative_path within products")

    # Rule 2: provenance record shape.
    provenance = (*manifest.inputs, manifest.parameters, *manifest.products)
    for record in provenance:
        if not record.relative_path:
            raise ManifestError("rule 2: provenance record has an empty relative_path")
        if not _SHA256_RE.fullmatch(record.sha256):
            raise ManifestError(
                f"rule 2: {record.relative_path!r} sha256 must be 64 lowercase hex chars"
            )
        if record.size_bytes < 0:
            raise ManifestError(f"rule 2: {record.relative_path!r} has a negative size_bytes")

    # Rules 3-4: membership.
    _check_group_membership(
        manifest.primary_16, expected=_PRIMARY_GROUPS, excluded=(9,), label="primary_16"
    )
    _check_group_membership(
        manifest.sensitivity_17, expected=_LEAVE_ONE_OUT_GROUPS, excluded=(), label="sensitivity_17"
    )

    # Rule 5: segment bookkeeping and duration-weighted recomputation.
    _check_scenario(manifest.primary_16, label="primary_16")
    _check_scenario(manifest.sensitivity_17, label="sensitivity_17")

    # Rule 6: finite floats.
    for label, scenario in (("primary_16", manifest.primary_16), ("sensitivity_17", manifest.sensitivity_17)):
        for name in _COMBINATION_FLOAT_FIELDS:
            if not math.isfinite(getattr(scenario.combination, name)):
                raise ManifestError(f"rule 6: {label} combination.{name} is not finite")
    for key, entry in manifest.leave_one_out.items():
        if not math.isfinite(entry.chi2_red) or not math.isfinite(entry.u_wls):
            raise ManifestError(f"rule 6: leave_one_out[{key}] has a non-finite float")
    if not math.isfinite(manifest.tide_method.max_abs_time_diff_s):
        raise ManifestError("rule 6: tide_method.max_abs_time_diff_s is not finite")

    # Rule 7: leave-one-out membership.
    if set(manifest.leave_one_out) != set(_LEAVE_ONE_OUT_GROUPS):
        raise ManifestError("rule 7: leave_one_out keys must be exactly the groups 1..17")
    for key, entry in manifest.leave_one_out.items():
        if entry.excluded_group != key:
            raise ManifestError(f"rule 7: leave_one_out[{key}] excludes group {entry.excluded_group}")

    # Rule 8: uncertainty budget decimals and consistency.
    budget = manifest.uncertainty_budget
    correlation = budget.correlation
    n_components = len(budget.components)
    if len(correlation) != n_components or any(
        len(row) != n_components for row in correlation
    ):
        raise ManifestError(
            "rule 8: correlation matrix must be square and match the component count"
        )
    if any(not math.isfinite(value) for row in correlation for value in row):
        raise ManifestError("rule 8: correlation matrix entries must be finite")
    if any(abs(correlation[index][index] - 1.0) > 1e-12 for index in range(n_components)):
        raise ManifestError("rule 8: correlation matrix diagonal entries must be 1.0")
    for component in budget.components:
        _finite_decimal(component.correction, label=f"component {component.name!r} correction")
        _finite_decimal(
            component.standard_uncertainty,
            label=f"component {component.name!r} standard_uncertainty",
        )
    _finite_decimal(budget.known_quadrature, label="known_quadrature")
    _finite_decimal(budget.total_standard_uncertainty, label="total_standard_uncertainty")

    unsatisfied = [
        component
        for component in budget.components
        if component.required
        and (component.status is not EvidenceStatus.established or component.standard_uncertainty is None)
    ]
    if unsatisfied and budget.total_standard_uncertainty is not None:
        raise ManifestError(
            "rule 8: total_standard_uncertainty present while a required component lacks "
            "established uncertainty"
        )
    if all(component.status is EvidenceStatus.established for component in budget.components):
        if budget.total_standard_uncertainty is None:
            raise ManifestError(
                "rule 8: every component is established but total_standard_uncertainty is None"
            )
    if (
        budget.total_standard_uncertainty is not None
        and budget.total_standard_uncertainty != budget.known_quadrature
    ):
        raise ManifestError("rule 8: total_standard_uncertainty does not equal known_quadrature")

    # Rule 9: tide counts.
    tide = manifest.tide_method
    if tide.converted_row_count < 0 or tide.reference_row_count < 0 or tide.common_prefix_row_count < 0:
        raise ManifestError("rule 9: tide row counts must be non-negative")
    if tide.common_prefix_row_count > min(tide.converted_row_count, tide.reference_row_count):
        raise ManifestError("rule 9: common_prefix_row_count exceeds the compared row counts")

    # Rule 10: ledger digest fields must resolve to exactly one product record.
    for field_value, filename in (
        (manifest.parameter_ledger_sha256, "parameter_ledger.csv"),
        (manifest.sample_ledger_sha256, "sample_ledger.csv"),
    ):
        matches = [record for record in manifest.products if record.relative_path == filename]
        if len(matches) != 1 or matches[0].sha256 != field_value:
            raise ManifestError(
                f"rule 10: {filename} sha256 does not match a unique product record"
            )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _check_hashes(records: tuple[ProvenanceRecord, ...], base: Path, *, kind: str) -> None:
    for record in records:
        target = Path(base) / record.relative_path
        if not target.is_file() or _sha256_file(target) != record.sha256:
            raise ManifestError(f"sha256 mismatch or missing {kind}: {record.relative_path}")


def verify_input_hashes(manifest: ResultManifest, root: Path) -> None:
    _check_hashes(manifest.inputs, root, kind="input")


def verify_parameter_hash(manifest: ResultManifest, root: Path) -> None:
    _check_hashes((manifest.parameters,), root, kind="parameter")


def verify_product_hashes(manifest: ResultManifest, base_dir: Path) -> None:
    _check_hashes(manifest.products, base_dir, kind="product")


def verify_manifest(manifest: ResultManifest, *, root: Path, base_dir: Path) -> None:
    reconcile_manifest(manifest)
    verify_input_hashes(manifest, root)
    verify_parameter_hash(manifest, root)
    verify_product_hashes(manifest, base_dir)


def write_manifest_atomic(manifest: ResultManifest, path: Path) -> None:
    """Write deterministic bytes; never leave a partial manifest behind."""
    payload = manifest.model_dump_json(indent=2).encode("utf-8") + b"\n"
    path = Path(path)
    temp = path.with_name(path.name + ".tmp")
    try:
        with open(temp, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except BaseException:
        try:
            temp.unlink(missing_ok=True)
        finally:
            raise
