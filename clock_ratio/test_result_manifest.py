"""Task 13 tests: authoritative analysis manifest (schemas, hashes, atomic write)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from clock_ratio.build_result_manifest import build_manifest
from clock_ratio.evidence import EvidenceStatus
from clock_ratio.result_manifest import (
    BudgetComponentModel,
    CombinationManifest,
    LeaveOneOutManifest,
    ManifestError,
    ProvenanceRecord,
    ResultManifest,
    StatisticalScenarioManifest,
    TideMethodManifest,
    UncertaintyBudgetModel,
    read_manifest,
    reconcile_manifest,
    verify_input_hashes,
    verify_manifest,
    verify_product_hashes,
    write_manifest_atomic,
)

REPO = Path(__file__).resolve().parents[1]
_EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)
_REFERENCE = Decimal("1.20750703934333772037")

_PRODUCT_FILENAMES = (
    "sample_ledger.csv",
    "time_quality.json",
    "parameter_ledger.csv",
    "parameter_conflicts.json",
    "tide-conversion/professional_tidal_delta_30s.csv",
    "tide-conversion/professional_tidal_delta_30s.diff.json",
    "statistical_methods_tidal.json",
    "statistical_methods_tidal_seg9_excluded.json",
)


def _provenance(relative_path: str, sha256: str, *, size_bytes: int = 0) -> ProvenanceRecord:
    return ProvenanceRecord(
        relative_path=relative_path,
        sha256=sha256,
        size_bytes=size_bytes,
        mtime_utc=_EPOCH,
        provider=None,
        command=(),
        distributable=None,
        status=EvidenceStatus.established,
    )


def _make_budget() -> UncertaintyBudgetModel:
    names = (
        "statistical",
        "clock_systematic",
        "tide_model",
        "gravity_potential",
        "link_noise",
        "reference_uncertainty",
        "collisional",
    )
    components = tuple(
        BudgetComponentModel(
            name=name,
            correction=None,
            standard_uncertainty="3.7e-19" if index == 0 else None,
            source="phase-one budget",
            status=EvidenceStatus.established if index == 0 else EvidenceStatus.pending_verification,
            required=True,
        )
        for index, name in enumerate(names)
    )
    size = len(components)
    return UncertaintyBudgetModel(
        components=components,
        correlation=tuple(
            tuple(1.0 if row == column else 0.0 for column in range(size)) for row in range(size)
        ),
        known_quadrature="1.5e-18",
        total_standard_uncertainty=None,
        status=EvidenceStatus.pending_verification,
    )


def _make_scenario(groups: tuple[int, ...], *, scenario: str = "raw") -> StatisticalScenarioManifest:
    with localcontext() as ctx:
        ctx.prec = 80
        ratios = tuple(
            _REFERENCE * (Decimal(1) + Decimal(repr(0.1 * group)) * Decimal("1e-18"))
            for group in groups
        )
        n_valid = tuple(1000 + group for group in groups)
        total = Decimal(sum(n_valid))
        duration = sum((Decimal(n) * ratio for ratio, n in zip(ratios, n_valid)), Decimal(0)) / total
        combination = CombinationManifest(
            R_seg1=str(_REFERENCE),
            R_wls=str(_REFERENCE + Decimal("1e-22")),
            R_mp=str(_REFERENCE + Decimal("2e-22")),
            R_bayes=str(_REFERENCE + Decimal("3e-22")),
            y_wls_precision_1e18=0.0,
            u_wls=1.0e-18,
            chi2=float(len(groups)),
            dof=len(groups) - 1,
            chi2_red=1.0,
            p_chi2=0.5,
            birge_ratio=1.0,
            u_birge=1.0e-18,
            xi_mp=0.0,
            u_mp=1.0e-18,
            mu_bayes=0.0,
            u_stat_bayes=3.7e-19,
            xi_bayes=0.0,
        )
    return StatisticalScenarioManifest(
        scenario=scenario,
        coefficient="0",
        included_groups=groups,
        excluded_groups=() if 9 in groups else (9,),
        n_segments=len(groups),
        total_samples=sum(n_valid),
        duration_weighted_ratio=str(duration),
        segment_ratios=tuple(str(ratio) for ratio in ratios),
        segment_n_valid=n_valid,
        segment_statuses=tuple(EvidenceStatus.established for _ in groups),
        combination=combination,
    )


def make_valid_manifest(**overrides: object) -> ResultManifest:
    """Internally consistent in-memory manifest, sufficient for reconcile-only tests."""
    products = tuple(
        _provenance(relative_path, format(index, "064x"))
        for index, relative_path in enumerate(_PRODUCT_FILENAMES, start=1)
    )
    manifest = ResultManifest(
        git_commit="deadbeef",
        dirty=False,
        python="3.12.0",
        packages={"numpy": "2.0.0", "scipy": "1.14.0"},
        inputs=(_provenance("input.csv", "0" * 64),),
        parameters=_provenance("clock/params.json", "c" * 64),
        products=products,
        parameter_ledger_sha256=format(3, "064x"),
        sample_ledger_sha256=format(1, "064x"),
        primary_16=_make_scenario(tuple(group for group in range(1, 18) if group != 9)),
        sensitivity_17=_make_scenario(tuple(range(1, 18))),
        leave_one_out={
            group: LeaveOneOutManifest(
                excluded_group=group,
                R_wls="1.20750703934333772038",
                R_mp="1.20750703934333772039",
                R_bayes="1.20750703934333772040",
                chi2_red=1.0,
                u_wls=1.0e-18,
            )
            for group in range(1, 18)
        },
        tide_method=TideMethodManifest(
            source_column="delta_w",
            direction="WUHN-SHAO",
            timezone="UTC",
            expected_step_s=30,
            gravity_m_s2="9.7946",
            converted_row_count=2,
            reference_row_count=2,
            common_prefix_row_count=2,
            max_abs_time_diff_s=0.0,
            max_abs_value_diff="0.0",
            first_inconsistent_row_number=None,
            first_inconsistent_value_diff=None,
            status=EvidenceStatus.pending_verification,
        ),
        uncertainty_budget=_make_budget(),
        commands=("uv run python -m clock_ratio.build_result_manifest",),
    )
    if overrides:
        manifest = manifest.model_copy(update=overrides)
    return manifest


def _scenario_payload(groups: tuple[int, ...], *, reference: str) -> dict[str, object]:
    return {
        "per_segment": [
            {
                "group": group,
                "T_s": 1200.0,
                "u_frac": 1.0e-16,
                "u_i": 1.0e-16,
                "y_i_1e18": 0.1 * group,
                "n_valid": 1000 + group,
                "status": "established",
                "fit_slope": -0.5,
            }
            for group in groups
        ],
        "coefficient": "0",
        "R_seg1": reference,
        "R_wls": reference,
        "R_mp": reference,
        "R_bayes": reference,
        "y_wls_precision_1e18": 0.0,
        "u_wls": 1.0e-18,
        "chi2": float(len(groups)),
        "dof": len(groups) - 1,
        "chi2_red": 1.0,
        "p_chi2": 0.5,
        "birge_ratio": 1.0,
        "u_birge": 1.0e-18,
        "xi_mp": 0.0,
        "u_mp": 1.0e-18,
        "mu_bayes": 0.0,
        "u_stat_bayes": 3.7e-19,
        "xi_bayes": 0.0,
    }


def _leave_one_out_payload() -> dict[str, dict[str, object]]:
    return {
        str(group): {
            "R_wls": "1.20750703934333772038",
            "R_mp": "1.20750703934333772039",
            "R_bayes": "1.20750703934333772040",
            "chi2_red": 1.0,
            "u_wls": 1.0e-18,
        }
        for group in range(1, 18)
    }


def _write_synthetic_staging(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Build a hermetic synthetic staging tree; returns (staging, root, data_dir)."""
    root = tmp_path
    staging = root / "staging"
    data_dir = root / "data"
    (staging / "tide-conversion").mkdir(parents=True)
    data_dir.mkdir()
    (root / "clock").mkdir()

    raw_bytes = b"raw-bytes"
    (data_dir / "Freq_fake.txt").write_bytes(raw_bytes)
    (root / "clock" / "params.json").write_text('{"synthetic": true}', encoding="utf-8")

    digest = {
        "relative_path": "Freq_fake.txt",
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "size_bytes": len(raw_bytes),
        "mtime_utc": "2026-01-01T00:00:00+00:00",
    }
    (staging / "time_quality.json").write_text(
        json.dumps(
            {
                "computed_total_final": 100,
                "files": [
                    {
                        "digest": digest,
                        "timestamp_quality": {
                            "n_rows": 100,
                            "n_parse_errors": 0,
                            "n_duplicates": 0,
                            "n_reversals": 0,
                            "n_gaps": 0,
                            "max_gap_s": 1.0,
                            "max_abs_jitter_s": 0.0,
                            "first_label_utc8": "2026-01-01T00:00:00+08:00",
                            "last_label_utc8": "2026-01-01T00:01:39+08:00",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (staging / "sample_ledger.csv").write_text(
        "group,n_final\n" + "\n".join(f"{group},{1000 + group}" for group in range(1, 18)) + "\n",
        encoding="utf-8",
    )
    (staging / "parameter_ledger.csv").write_text("name,group,value\nfake,1,1.0\n", encoding="utf-8")
    (staging / "parameter_conflicts.json").write_text("[]", encoding="utf-8")
    (staging / "tide-conversion" / "professional_tidal_delta_30s.csv").write_text(
        "timestamp_utc,delta_w\n2026-01-01T00:00:00Z,0.0\n", encoding="utf-8"
    )
    diff_payload = {
        "config": {
            "gravity_m_s2": "9.7946",
            "direction": "WUHN-SHAO",
            "timezone": "UTC",
            "source_column": "delta_w",
            "expected_step_s": 30,
        },
        "input_workbook": "workbook.xlsx",
        "reference_csv": "reference.csv",
        "conversion_summary": {
            "row_count": 2,
            "first_timestamp_utc": "2026-01-01T00:00:00+00:00",
            "last_timestamp_utc": "2026-01-01T00:00:30+00:00",
            "step_seconds": 30,
            "source_column": "delta_w",
        },
        "comparison_summary": {
            "converted_row_count": 2,
            "reference_row_count": 2,
            "common_prefix_row_count": 2,
            "first_timestamp_utc": "2026-01-01T00:00:00+00:00",
            "last_timestamp_utc": "2026-01-01T00:00:30+00:00",
            "max_abs_time_diff_s": 0.0,
            "max_abs_value_diff": 0.0,
            "first_inconsistent_row": None,
            "first_extra_converted_row": None,
            "first_extra_reference_row": None,
        },
    }
    (staging / "tide-conversion" / "professional_tidal_delta_30s.diff.json").write_text(
        json.dumps(diff_payload, indent=2), encoding="utf-8"
    )

    reference = str(_REFERENCE)
    seg16 = tuple(group for group in range(1, 18) if group != 9)
    seg17 = tuple(range(1, 18))
    (staging / "statistical_methods_tidal.json").write_text(
        json.dumps({"scenarios": {"raw": _scenario_payload(seg17, reference=reference)}}, indent=2),
        encoding="utf-8",
    )
    (staging / "statistical_methods_tidal_seg9_excluded.json").write_text(
        json.dumps(
            {
                "scenarios": {"raw": _scenario_payload(seg16, reference=reference)},
                "leave_one_out": {"raw": _leave_one_out_payload()},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return staging, root, data_dir


def test_manifest_rejects_duplicate_or_wrong_membership() -> None:
    manifest = make_valid_manifest()
    wrong = manifest.primary_16.model_copy(update={"included_groups": tuple(range(1, 17))})
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"primary_16": wrong}))
    duplicate = manifest.primary_16.model_copy(
        update={"included_groups": (1, *range(1, 9), *range(10, 18))}
    )
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"primary_16": duplicate}))


def test_manifest_detects_tampered_input(tmp_path: Path) -> None:
    valid_manifest = make_valid_manifest()
    (tmp_path / "input.csv").write_text("changed", encoding="utf-8")
    with pytest.raises(ManifestError, match="sha256"):
        verify_input_hashes(valid_manifest, root=tmp_path)


def test_manifest_roundtrip_and_deterministic_serialization(tmp_path: Path) -> None:
    manifest = make_valid_manifest()
    serialized = manifest.model_dump_json(indent=2)
    assert serialized == ResultManifest.model_validate_json(serialized).model_dump_json(indent=2)
    target = tmp_path / "manifest.json"
    write_manifest_atomic(manifest, target)
    first_bytes = target.read_bytes()
    write_manifest_atomic(manifest, target)
    assert target.read_bytes() == first_bytes
    assert read_manifest(target) == manifest


def test_atomic_write_preserves_old_manifest_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "manifest.json"
    target.write_text('{"old": true}', encoding="utf-8")

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("replace failed")

    monkeypatch.setattr("clock_ratio.result_manifest.os.replace", boom)
    with pytest.raises(RuntimeError):
        write_manifest_atomic(make_valid_manifest(), target)
    assert target.read_text(encoding="utf-8") == '{"old": true}'
    assert list(tmp_path.glob("*.tmp")) == []


def test_reconcile_rejects_leave_one_out_membership() -> None:
    manifest = make_valid_manifest()
    missing = {key: value for key, value in manifest.leave_one_out.items() if key != 9}
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"leave_one_out": missing}))
    wrong = dict(manifest.leave_one_out)
    wrong[9] = wrong[9].model_copy(update={"excluded_group": 10})
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"leave_one_out": wrong}))


def test_reconcile_rejects_duration_weighted_mismatch() -> None:
    manifest = make_valid_manifest()
    broken = manifest.primary_16.model_copy(update={"duration_weighted_ratio": "1.2"})
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"primary_16": broken}))


def test_reconcile_rejects_nonfinite_float() -> None:
    manifest = make_valid_manifest()
    combination = manifest.primary_16.combination.model_copy(update={"chi2_red": float("nan")})
    broken = manifest.primary_16.model_copy(update={"combination": combination})
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"primary_16": broken}))


def test_reconcile_rejects_segment_statuses_length_mismatch() -> None:
    manifest = make_valid_manifest()
    broken = manifest.primary_16.model_copy(
        update={"segment_statuses": manifest.primary_16.segment_statuses[:-1]}
    )
    with pytest.raises(ManifestError, match="rule 5"):
        reconcile_manifest(manifest.model_copy(update={"primary_16": broken}))


def test_reconcile_rejects_nonfinite_segment_ratio() -> None:
    manifest = make_valid_manifest()
    ratios = (*manifest.primary_16.segment_ratios[:-1], "Infinity")
    broken = manifest.primary_16.model_copy(update={"segment_ratios": ratios})
    with pytest.raises(ManifestError, match="rule 5"):
        reconcile_manifest(manifest.model_copy(update={"primary_16": broken}))


def test_reconcile_rejects_correlation_row_count_mismatch() -> None:
    manifest = make_valid_manifest()
    correlation = manifest.uncertainty_budget.correlation[:-1]
    budget = manifest.uncertainty_budget.model_copy(update={"correlation": correlation})
    with pytest.raises(ManifestError, match="rule 8"):
        reconcile_manifest(manifest.model_copy(update={"uncertainty_budget": budget}))


def test_reconcile_rejects_established_component_without_uncertainty() -> None:
    manifest = make_valid_manifest()
    components = tuple(
        component.model_copy(
            update={
                "status": EvidenceStatus.established,
                "standard_uncertainty": component.standard_uncertainty or "1e-19",
            }
        )
        for component in manifest.uncertainty_budget.components
    )
    components = (components[0].model_copy(update={"standard_uncertainty": None}),) + components[1:]
    budget = manifest.uncertainty_budget.model_copy(
        update={
            "components": components,
            "known_quadrature": "1e-18",
            "total_standard_uncertainty": "1e-18",
        }
    )
    with pytest.raises(ManifestError):
        reconcile_manifest(manifest.model_copy(update={"uncertainty_budget": budget}))


def test_verify_input_hashes_accepts_matching_file(tmp_path: Path) -> None:
    content = b"hello manifest"
    (tmp_path / "input.csv").write_bytes(content)
    record = make_valid_manifest().inputs[0].model_copy(
        update={"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}
    )
    verify_input_hashes(make_valid_manifest(inputs=(record,)), root=tmp_path)


def test_verify_product_hashes_detects_tampering(tmp_path: Path) -> None:
    staging, root, data_dir = _write_synthetic_staging(tmp_path)
    manifest = build_manifest(
        staging, root=root, data_dir=data_dir, git_commit="deadbeef", dirty=False
    )
    (staging / "sample_ledger.csv").write_text("group,n_final\n1,0\n", encoding="utf-8")
    with pytest.raises(ManifestError, match="sha256"):
        verify_product_hashes(manifest, base_dir=staging)


def test_build_manifest_from_synthetic_staging(tmp_path: Path) -> None:
    staging, root, data_dir = _write_synthetic_staging(tmp_path)
    manifest = build_manifest(
        staging, root=root, data_dir=data_dir, git_commit="deadbeef", dirty=False
    )
    reconcile_manifest(manifest)
    assert manifest.primary_16.n_segments == 16
    assert manifest.sensitivity_17.n_segments == 17
    assert set(manifest.leave_one_out) == set(range(1, 18))
    verify_manifest(manifest, root=root, base_dir=staging)
    (staging / "statistical_methods_tidal.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ManifestError, match="sha256"):
        verify_manifest(manifest, root=root, base_dir=staging)


def test_build_manifest_missing_input_fails(tmp_path: Path) -> None:
    staging = tmp_path / "empty-staging"
    staging.mkdir()
    with pytest.raises(ManifestError, match="sample_ledger.csv"):
        build_manifest(
            staging,
            root=tmp_path,
            data_dir=tmp_path / "data",
            git_commit="deadbeef",
            dirty=False,
        )


def test_verify_result_manifest_cli(tmp_path: Path) -> None:
    staging, root, data_dir = _write_synthetic_staging(tmp_path)
    manifest = build_manifest(
        staging, root=root, data_dir=data_dir, git_commit="deadbeef", dirty=False
    )
    manifest_path = staging / "manifest.json"
    write_manifest_atomic(manifest, manifest_path)
    command = [
        sys.executable,
        "-m",
        "clock_ratio.verify_result_manifest",
        str(manifest_path),
        "--root",
        str(root),
    ]
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    assert result.returncode == 0
    assert "OK" in result.stdout
    (staging / "statistical_methods_tidal_seg9_excluded.json").write_text("{}", encoding="utf-8")
    broken = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    assert broken.returncode != 0
    assert "sha256" in broken.stderr
