"""Build a provenance ledger for ratio-analysis parameters."""
from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import typer

from clock import shared
from clock.data_provenance import ParameterEvidence
from clock_ratio.evidence import EvidenceStatus

app = typer.Typer(add_completion=False)
COMPONENT_NAMES = ("a_rou", "a_AC", "a_SM", "a_air", "a_BBR")
INHERITED_GROUPS = (15, 16, 17)
INHERITED_FROM_GROUP = 12
PARAMS_DEFAULT = Path("clock/params.json")
OUTPUT_FILENAMES = ("parameter_ledger.csv", "parameter_conflicts.json")
LEVELLING_SOURCE = Path("docs/superpowers/specs/2026-10-06-clock-comparison-audit-paper-design.md")


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


def _load_params(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _record(name: str, group: int | None, value: str | None, *, unit: str, source_path: str,
            inherited_from_group: int | None, status: EvidenceStatus, note: str) -> ParameterEvidence:
    return ParameterEvidence(
        name=name,
        group=group,
        value=Decimal(value) if value is not None else None,
        unit=unit,
        source_path=source_path,
        inherited_from_group=inherited_from_group,
        status=status,
        note=note,
    )


def _segment_record(name: str, group: int, value: str, source_path: str) -> ParameterEvidence:
    inherited_from_group = INHERITED_FROM_GROUP if group in INHERITED_GROUPS else None
    if group in INHERITED_GROUPS:
        status = EvidenceStatus.pending_verification
        note = "Inherited from group 12 in clock.shared; not stored independently in params.json."
    elif group == 9 and name == "a_SM":
        status = EvidenceStatus.pending_verification
        note = "Group 9 a_SM is explicitly called out in repository docs for manual verification."
    else:
        status = EvidenceStatus.established
        note = "Loaded directly from params.json and used by executable analysis code."
    return _record(
        name,
        group,
        value,
        unit="fractional",
        source_path=source_path,
        inherited_from_group=inherited_from_group,
        status=status,
        note=note,
    )


def _levelling_records() -> tuple[ParameterEvidence, ...]:
    source_path = LEVELLING_SOURCE.as_posix()
    return (
        _record(
            "levelling_raw_observations",
            None,
            None,
            unit="missing-source",
            source_path=source_path,
            inherited_from_group=None,
            status=EvidenceStatus.external_unverified,
            note="Repository docs treat levelling documents as external read-only sources, but no raw observations are present here.",
        ),
        _record(
            "levelling_reduction_process",
            None,
            None,
            unit="missing-source",
            source_path=source_path,
            inherited_from_group=None,
            status=EvidenceStatus.external_unverified,
            note="Repository docs explicitly state that the levelling reduction is not yet reproducible from code in this repo.",
        ),
        _record(
            "levelling_uncertainty_propagation",
            None,
            None,
            unit="missing-source",
            source_path=source_path,
            inherited_from_group=None,
            status=EvidenceStatus.external_unverified,
            note="Repository docs require levelling uncertainty propagation evidence, but no executable source is present here.",
        ),
    )



def build_parameter_records(params_path: Path) -> tuple[ParameterEvidence, ...]:
    params = _load_params(params_path)
    source_path = params_path.as_posix()
    shift = params["shift_a"]
    records: list[ParameterEvidence] = []

    for group in range(1, 18):
        source_index = INHERITED_FROM_GROUP - 1 if group in INHERITED_GROUPS else group - 1
        components: dict[str, Decimal] = {}
        component_records: list[ParameterEvidence] = []
        for name in COMPONENT_NAMES:
            value = shift[name][source_index]
            component = _segment_record(name, group, value, source_path)
            records.append(component)
            component_records.append(component)
            components[name] = component.value
        total = sum(components.values(), Decimal(0))
        inherited = group in INHERITED_GROUPS
        derived_pending = any(component.status is not EvidenceStatus.established for component in component_records)
        records.append(
            ParameterEvidence(
                name="shift_a",
                group=group,
                value=total,
                unit="fractional",
                source_path=source_path,
                inherited_from_group=INHERITED_FROM_GROUP if inherited else None,
                status=(EvidenceStatus.pending_verification if derived_pending else EvidenceStatus.established),
                note=(
                    "Inherited total shift_a from group 12 because groups 15-17 have no separate executable source."
                    if inherited
                    else "Derived from params.json components; pending because at least one constituent still needs verification."
                    if derived_pending
                    else "Sum of executable shift_a components from params.json."
                ),
            )
        )

    records.append(
        _record(
            "DELTA_G",
            None,
            params["ratio_constants"]["DELTA_G"],
            unit="fractional",
            source_path=source_path,
            inherited_from_group=None,
            status=EvidenceStatus.pending_verification,
            note="Static gravitational correction is executable, but its levelling provenance is not closed inside this repository.",
        )
    )
    records.extend(_levelling_records())
    return tuple(records)


def validate_output_dir(output_dir: Path, params_path: Path) -> Path:
    target = output_dir.resolve()
    params_resolved = params_path.resolve()

    if target.is_relative_to(shared.DATA_DIR):
        raise ValueError(f"protected raw-data directory: {target}")

    protected_roots = _protected_repo_roots()
    allowed_output_roots = tuple(repo_root / "results" / "audit-v1" for repo_root in protected_roots)
    if not any(target.is_relative_to(allowed_root) for allowed_root in allowed_output_roots):
        for repo_root in protected_roots:
            if target.is_relative_to(repo_root):
                raise ValueError(f"protected repository source/legacy output directory: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"output directory is not a directory: {target}")

    for filename in OUTPUT_FILENAMES:
        path = target / filename
        if path.resolve(strict=False) == params_resolved:
            raise ValueError(f"output filename collides with params input: {path}")
        if path.is_symlink():
            raise ValueError(f"output filename is a symlink: {path}")
        if path.exists() and (not path.is_file() or path.stat().st_nlink > 1):
            raise ValueError(f"output filename is not an independent regular file: {path}")
    return target



def _serialize_record(record: ParameterEvidence) -> dict[str, Any]:
    payload = asdict(record)
    payload["value"] = None if record.value is None else str(record.value)
    payload["status"] = record.status.value
    return payload


def _write_csv(path: Path, records: tuple[ParameterEvidence, ...]) -> None:
    fieldnames = [
        "name",
        "group",
        "value",
        "unit",
        "source_path",
        "inherited_from_group",
        "status",
        "note",
    ]
    with NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent) as temp:
        writer = csv.DictWriter(temp, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(_serialize_record(record))
        temp_path = Path(temp.name)
    temp_path.replace(path)


def _write_json(path: Path, payload: Any) -> None:
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as temp:
        json.dump(payload, temp, ensure_ascii=False, indent=2)
        temp.write("\n")
        temp_path = Path(temp.name)
    temp_path.replace(path)


@app.command()
def main(
    output_dir: Path = typer.Option(..., exists=False, file_okay=False, dir_okay=True),
    params_path: Path = typer.Option(PARAMS_DEFAULT, exists=True, dir_okay=False),
) -> None:
    try:
        target = validate_output_dir(output_dir, params_path)
        target.mkdir(parents=True, exist_ok=True)
        records = build_parameter_records(params_path)
        ledger_path = target / "parameter_ledger.csv"
        conflicts_path = target / "parameter_conflicts.json"
        _write_csv(ledger_path, records)
        conflicts = [_serialize_record(record) for record in records if record.status is not EvidenceStatus.established]
        _write_json(conflicts_path, conflicts)
    except (OSError, ValueError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error


if __name__ == "__main__":
    app()
