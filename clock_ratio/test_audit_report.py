"""Tests for clock_ratio.audit_report — manifest-only audit report generator."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from clock_ratio import audit_report
from clock_ratio.audit_report import app, render_audit_report, write_report_atomic
from clock_ratio.result_manifest import ManifestError, write_manifest_atomic
from clock_ratio.test_result_manifest import make_valid_manifest


def replace_primary_chi2(manifest, value):
    return manifest.model_copy(
        update={
            "primary_16": manifest.primary_16.model_copy(
                update={
                    "combination": manifest.primary_16.combination.model_copy(
                        update={"chi2_red": value}
                    )
                }
            )
        }
    )


def test_report_changes_when_manifest_value_changes() -> None:
    first = render_audit_report(make_valid_manifest())
    changed = replace_primary_chi2(make_valid_manifest(), 1.234)
    second = render_audit_report(changed)
    assert first != second
    assert f"{changed.primary_16.combination.chi2_red:.3f}" in second


def test_report_requires_primary_sensitivity_and_loo() -> None:
    with pytest.raises(ManifestError):
        render_audit_report(make_valid_manifest(leave_one_out={}))


def test_source_contains_no_historical_result_literals() -> None:
    source = Path(audit_report.__file__).read_text(encoding="utf-8")
    for literal in ("5.42", "3.70", "4.56", "6.4", "31.8%"):
        assert literal not in source


def test_render_includes_membership_and_loo_rows() -> None:
    text = render_audit_report(make_valid_manifest())
    for group in range(1, 18):
        assert f"第 {group} 段" in text
    segment9_section = text.split("## 3. ", 1)[1].split("## 4.", 1)[0]
    assert "第 9 段" in segment9_section
    assert "排除" in segment9_section


def test_write_report_atomic_replaces_and_is_deterministic(tmp_path: Path) -> None:
    target = tmp_path / "ANALYSIS_AUDIT.md"
    text = render_audit_report(make_valid_manifest())
    write_report_atomic(text, target)
    assert target.read_text(encoding="utf-8") == text
    write_report_atomic(text, target)
    assert target.read_text(encoding="utf-8") == text
    assert not (tmp_path / "ANALYSIS_AUDIT.md.tmp").exists()


def test_cli_writes_default_output_next_to_manifest(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    write_manifest_atomic(make_valid_manifest(), manifest_path)
    result = CliRunner().invoke(app, ["--manifest", str(manifest_path)])
    assert result.exit_code == 0
    target = manifest_path.parent / "ANALYSIS_AUDIT.md"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == render_audit_report(make_valid_manifest())
