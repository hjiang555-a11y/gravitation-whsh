"""Build a provenance ledger for ratio-analysis parameters."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import typer

from clock.data_provenance import ParameterEvidence
from clock_ratio.evidence import EvidenceStatus

app = typer.Typer(add_completion=False)
COMPONENT_NAMES = ("a_rou", "a_AC", "a_SM", "a_air", "a_BBR")
INHERITED_GROUPS = (15, 16, 17)
INHERITED_FROM_GROUP = 12
PARAMS_DEFAULT = Path("clock/params.json")


def _load_params(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def _record(name: str, group: int | None, value: str, *, unit: str, source_path: str,
            inherited_from_group: int | None, status: EvidenceStatus, note: str) -> ParameterEvidence:
    return ParameterEvidence(
        name=name,
        group=group,
        value=Decimal(value),
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
            note="Static gravitational correction is executable, but its leveling provenance is document-only in this repository.",
        )
    )
    return tuple(records)


def _serialize_record(record: ParameterEvidence) -> dict[str, Any]:
    payload = asdict(record)
    payload["value"] = str(record.value)
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
    output_dir.mkdir(parents=True, exist_ok=True)
    records = build_parameter_records(params_path)
    ledger_path = output_dir / "parameter_ledger.csv"
    conflicts_path = output_dir / "parameter_conflicts.json"
    _write_csv(ledger_path, records)
    conflicts = [_serialize_record(record) for record in records if record.status is not EvidenceStatus.established]
    _write_json(conflicts_path, conflicts)


if __name__ == "__main__":
    app()
