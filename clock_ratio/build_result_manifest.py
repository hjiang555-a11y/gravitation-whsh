#!/usr/bin/env python3
"""Build the authoritative analysis manifest from the audit staging directory.

Reads the strong-schema staging artifacts (sample ledger, time quality,
parameter ledger/conflicts, tide conversion diff, 16/17-segment scenarios),
re-hashes every input/parameter/product, promotes the raw scenarios plus the
leave-one-out sweep into the typed manifest, and fails fast (ManifestError)
when any authoritative input is missing or internally inconsistent.
"""
from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
import typer
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from clock import shared  # noqa: E402
from clock.data_provenance import TimestampQuality, timestamp_quality_status  # noqa: E402
from clock_ratio.evidence import EvidenceStatus  # noqa: E402
from clock_ratio.result_manifest import (  # noqa: E402
    BudgetComponentModel,
    CombinationManifest,
    LeaveOneOutManifest,
    ManifestError,
    ProvenanceRecord,
    ResultManifest,
    StatisticalScenarioManifest,
    TideMethodManifest,
    UncertaintyBudgetModel,
    _sha256_file,
    reconcile_manifest,
    write_manifest_atomic,
)
from clock_ratio.uncertainty_budget import (  # noqa: E402
    build_phase_one_components,
    combine_uncertainty_budget,
)

REPO = Path(__file__).resolve().parents[1]
_PACKAGE_NAMES = ("numpy", "scipy", "matplotlib", "pydantic", "typer")
_REQUIRED_STAGING_FILES = (
    "sample_ledger.csv",
    "time_quality.json",
    "parameter_ledger.csv",
    "parameter_conflicts.json",
    "tide-conversion/professional_tidal_delta_30s.csv",
    "tide-conversion/professional_tidal_delta_30s.diff.json",
    "statistical_methods_tidal.json",
    "statistical_methods_tidal_seg9_excluded.json",
)


def collect_git_info(repo: Path) -> tuple[str, bool]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise ManifestError(f"cannot collect git info: {error}") from error
    return commit, bool(status.strip())


def collect_environment() -> tuple[str, dict[str, str]]:
    packages = {}
    for name in _PACKAGE_NAMES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "unknown"
    return platform.python_version(), packages


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ManifestError(f"cannot read staging file {path.name}: {error}") from error


def _provenance_from_disk(path: Path, relative_path: str) -> ProvenanceRecord:
    stat = path.stat()
    return ProvenanceRecord(
        relative_path=relative_path,
        sha256=_sha256_file(path),
        size_bytes=stat.st_size,
        mtime_utc=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        provider=None,
        command=(),
        distributable=None,
        status=EvidenceStatus.established,
    )


def _mapping(document: Mapping[str, object], key: str, *, source: str) -> Mapping[str, object]:
    value = document.get(key)
    if not isinstance(value, Mapping):
        raise ManifestError(f"{source}: missing {key!r} block")
    return value


def _scenario_from_payload(
    payload: Mapping[str, object], *, source: str
) -> StatisticalScenarioManifest:
    try:
        rows = payload["per_segment"]
        if not isinstance(rows, list) or not rows:
            raise ManifestError(f"{source}: per_segment must be a non-empty list")
        if not all(isinstance(row, Mapping) for row in rows):
            raise ManifestError(f"{source}: malformed per_segment row")
        for row in rows:
            if "status" not in row:
                raise ManifestError(
                    f"{source}: per-segment row missing per-segment status; regenerate staging"
                )
        reference = Decimal(str(payload["R_seg1"]))
        groups = tuple(int(row["group"]) for row in rows)
        n_valid = tuple(
            int(row["n_valid"] if "n_valid" in row else row["T_s"]) for row in rows
        )
        ratios = tuple(
            _reconstructed_ratio(reference, float(row["y_i_1e18"])) for row in rows
        )
        statuses = tuple(EvidenceStatus(str(row["status"])) for row in rows)
        combination = CombinationManifest(
            R_seg1=str(payload["R_seg1"]),
            R_wls=str(payload["R_wls"]),
            R_mp=str(payload["R_mp"]),
            R_bayes=str(payload["R_bayes"]),
            y_wls_precision_1e18=float(payload["y_wls_precision_1e18"]),
            u_wls=float(payload["u_wls"]),
            chi2=float(payload["chi2"]),
            dof=int(payload["dof"]),
            chi2_red=float(payload["chi2_red"]),
            p_chi2=float(payload["p_chi2"]),
            birge_ratio=float(payload["birge_ratio"]),
            u_birge=float(payload["u_birge"]),
            xi_mp=float(payload["xi_mp"]),
            u_mp=float(payload["u_mp"]),
            mu_bayes=float(payload["mu_bayes"]),
            u_stat_bayes=float(payload["u_stat_bayes"]),
            xi_bayes=float(payload["xi_bayes"]),
        )
    except ManifestError:
        raise
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        raise ManifestError(f"{source}: malformed scenario payload: {error}") from error

    total = sum(n_valid)
    if total == 0:
        raise ManifestError(f"{source}: scenario has zero retained samples")
    with localcontext() as context:
        context.prec = 80
        duration = sum(
            (Decimal(n) * ratio for ratio, n in zip(ratios, n_valid)), Decimal(0)
        ) / Decimal(total)
    return StatisticalScenarioManifest(
        scenario="raw",
        coefficient=str(payload["coefficient"]),
        included_groups=groups,
        excluded_groups=() if 9 in groups else (9,),
        n_segments=len(rows),
        total_samples=total,
        duration_weighted_ratio=str(duration),
        segment_ratios=tuple(str(ratio) for ratio in ratios),
        segment_n_valid=n_valid,
        segment_statuses=statuses,
        combination=combination,
    )


def _reconstructed_ratio(reference: Decimal, y_i: float) -> Decimal:
    with localcontext() as context:
        context.prec = 80
        return reference * (Decimal(1) + Decimal(repr(y_i)) * Decimal("1e-18"))


def _leave_one_out_manifest(
    block: Mapping[str, object], *, source: str
) -> dict[int, LeaveOneOutManifest]:
    try:
        return {
            int(key): LeaveOneOutManifest(
                excluded_group=int(key),
                R_wls=str(value["R_wls"]),
                R_mp=str(value["R_mp"]),
                R_bayes=str(value["R_bayes"]),
                chi2_red=float(value["chi2_red"]),
                u_wls=float(value["u_wls"]),
            )
            for key, value in block.items()
        }
    except (KeyError, TypeError, ArithmeticError, ValidationError) as error:
        raise ManifestError(f"{source}: malformed leave_one_out block: {error}") from error


def _tide_method_manifest(diff_document: Mapping[str, object]) -> TideMethodManifest:
    source = "professional_tidal_delta_30s.diff.json"
    try:
        config = _mapping(diff_document, "config", source=source)
        comparison = _mapping(diff_document, "comparison_summary", source=source)
        first = comparison.get("first_inconsistent_row")
        if first is not None and not isinstance(first, Mapping):
            raise ManifestError(f"{source}: malformed first_inconsistent_row")
        return TideMethodManifest(
            source_column=str(config["source_column"]),
            direction=str(config["direction"]),
            timezone=str(config["timezone"]),
            expected_step_s=int(config["expected_step_s"]),
            gravity_m_s2=str(config["gravity_m_s2"]),
            converted_row_count=int(comparison["converted_row_count"]),
            reference_row_count=int(comparison["reference_row_count"]),
            common_prefix_row_count=int(comparison["common_prefix_row_count"]),
            max_abs_time_diff_s=float(comparison["max_abs_time_diff_s"]),
            max_abs_value_diff=str(comparison["max_abs_value_diff"]),
            first_inconsistent_row_number=int(first["row_number"]) if first is not None else None,
            first_inconsistent_value_diff=str(first["value_diff"]) if first is not None else None,
            status=EvidenceStatus.pending_verification,
        )
    except ManifestError:
        raise
    except (KeyError, TypeError, ValueError) as error:
        raise ManifestError(f"{source}: malformed diff report: {error}") from error


def _uncertainty_budget_model(
    statistical_uncertainty: Decimal,
    statistical_status: EvidenceStatus | None = None,
) -> UncertaintyBudgetModel:
    components = build_phase_one_components(
        statistical_uncertainty=statistical_uncertainty,
        statistical_status=statistical_status,
    )
    try:
        budget = combine_uncertainty_budget(components, np.eye(len(components)))
    except ValueError as error:
        raise ManifestError(f"cannot combine uncertainty budget: {error}") from error
    return UncertaintyBudgetModel(
        components=tuple(
            BudgetComponentModel(
                name=component.name,
                correction=str(component.correction) if component.correction is not None else None,
                standard_uncertainty=(
                    str(component.standard_uncertainty)
                    if component.standard_uncertainty is not None
                    else None
                ),
                source=component.source,
                status=component.status,
                required=component.required,
            )
            for component in budget.components
        ),
        correlation=budget.correlation,
        known_quadrature=str(budget.known_quadrature),
        total_standard_uncertainty=(
            str(budget.total_standard_uncertainty)
            if budget.total_standard_uncertainty is not None
            else None
        ),
        status=budget.status,
    )


def build_manifest(
    staging_dir: Path,
    *,
    root: Path,
    data_dir: Path,
    git_commit: str,
    dirty: bool,
    commands: tuple[str, ...] = (),
) -> ResultManifest:
    staging_dir = Path(staging_dir)
    root = Path(root)
    for name in _REQUIRED_STAGING_FILES:
        if not (staging_dir / name).is_file():
            raise ManifestError(f"missing required staging file: {name}")

    # Products: one provenance record per required staging file, in declared order.
    products = tuple(
        _provenance_from_disk(staging_dir / name, name) for name in _REQUIRED_STAGING_FILES
    )

    # Inputs: raw-file digests recorded by the time-quality report.
    time_quality = _load_json(staging_dir / "time_quality.json")
    if not isinstance(time_quality, Mapping):
        raise ManifestError("time_quality.json: document must be an object")
    entries = time_quality.get("files")
    if not isinstance(entries, list) or not entries:
        raise ManifestError("time_quality.json: missing files list")
    try:
        inputs = tuple(
            ProvenanceRecord(
                relative_path=Path(
                    os.path.relpath(Path(data_dir) / entry["digest"]["relative_path"], root)
                ).as_posix(),
                sha256=entry["digest"]["sha256"],
                size_bytes=int(entry["digest"]["size_bytes"]),
                mtime_utc=entry["digest"]["mtime_utc"],
                provider=None,
                command=(),
                distributable=None,
                status=timestamp_quality_status(
                    TimestampQuality(**entry["timestamp_quality"])
                ),
            )
            for entry in entries
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ManifestError(f"time_quality.json: malformed file digest: {error}") from error

    parameters_path = root / "clock" / "params.json"
    if not parameters_path.is_file():
        raise ManifestError("missing required parameter file: clock/params.json")
    parameters = _provenance_from_disk(parameters_path, "clock/params.json")

    # Scenarios: promote the raw blocks; 16-segment primary + 17-segment sensitivity.
    seg9_document = _load_json(staging_dir / "statistical_methods_tidal_seg9_excluded.json")
    tidal_document = _load_json(staging_dir / "statistical_methods_tidal.json")
    if not isinstance(seg9_document, Mapping) or not isinstance(tidal_document, Mapping):
        raise ManifestError("statistical scenario documents must be JSON objects")
    primary_16 = _scenario_from_payload(
        _mapping(_mapping(seg9_document, "scenarios", source="seg9"), "raw", source="seg9"),
        source="statistical_methods_tidal_seg9_excluded.json",
    )
    sensitivity_17 = _scenario_from_payload(
        _mapping(_mapping(tidal_document, "scenarios", source="tidal"), "raw", source="tidal"),
        source="statistical_methods_tidal.json",
    )
    leave_one_out = _leave_one_out_manifest(
        _mapping(
            _mapping(seg9_document, "leave_one_out", source="seg9"), "raw", source="seg9"
        ),
        source="statistical_methods_tidal_seg9_excluded.json",
    )

    diff_document = _load_json(staging_dir / "tide-conversion" / "professional_tidal_delta_30s.diff.json")
    if not isinstance(diff_document, Mapping):
        raise ManifestError("professional_tidal_delta_30s.diff.json: document must be an object")
    tide_method = _tide_method_manifest(diff_document)

    # Budget: propagate the worst per-segment model status of the primary
    # scenario (any non-established segment flags the statistical component).
    worst_status = (
        EvidenceStatus.supported_with_limitations
        if any(status is not EvidenceStatus.established for status in primary_16.segment_statuses)
        else EvidenceStatus.established
    )
    uncertainty_budget = _uncertainty_budget_model(
        Decimal(str(primary_16.combination.u_stat_bayes)),
        statistical_status=worst_status,
    )

    product_sha256 = {record.relative_path: record.sha256 for record in products}
    python, packages = collect_environment()
    manifest = ResultManifest(
        git_commit=git_commit,
        dirty=dirty,
        python=python,
        packages=packages,
        inputs=inputs,
        parameters=parameters,
        products=products,
        parameter_ledger_sha256=product_sha256["parameter_ledger.csv"],
        sample_ledger_sha256=product_sha256["sample_ledger.csv"],
        primary_16=primary_16,
        sensitivity_17=sensitivity_17,
        leave_one_out=leave_one_out,
        tide_method=tide_method,
        uncertainty_budget=uncertainty_budget,
        commands=tuple(commands),
    )
    reconcile_manifest(manifest)
    return manifest


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(
    staging: Path = typer.Option(..., exists=True, file_okay=False),
    output: Path | None = typer.Option(None),
    command: list[str] = typer.Option(()),
    git_commit: str | None = typer.Option(None),
    dirty: bool | None = typer.Option(None),
) -> None:
    try:
        resolved_commit, resolved_dirty = collect_git_info(REPO)
        manifest = build_manifest(
            staging,
            root=REPO,
            data_dir=shared.DATA_DIR,
            git_commit=git_commit if git_commit is not None else resolved_commit,
            dirty=dirty if dirty is not None else resolved_dirty,
            commands=tuple(command),
        )
        target = output if output is not None else staging / "manifest.json"
        write_manifest_atomic(manifest, target)
        sidecar = target.with_name(target.name + ".run.json")
        sidecar.write_text(
            json.dumps({"generated_at_utc": datetime.now(timezone.utc).isoformat()}) + "\n",
            encoding="utf-8",
        )
    except (ManifestError, OSError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote {target}")


if __name__ == "__main__":
    app()
