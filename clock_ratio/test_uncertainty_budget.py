"""Tests for the auditable uncertainty budget (Task 11)."""
from __future__ import annotations

from decimal import Decimal

import numpy as np
import pytest

from clock_ratio.evidence import EvidenceStatus
from clock_ratio.uncertainty_budget import (
    BudgetComponent,
    build_phase_one_components,
    combine_uncertainty_budget,
)


def established_component(name: str, value: str) -> BudgetComponent:
    return BudgetComponent(
        name=name,
        correction=None,
        standard_uncertainty=Decimal(value),
        source="test fixture",
        status=EvidenceStatus.established,
        required=True,
    )


def pending_component(name: str, *, required: bool) -> BudgetComponent:
    return BudgetComponent(
        name=name,
        correction=None,
        standard_uncertainty=None,
        source="test fixture",
        status=EvidenceStatus.pending_verification,
        required=required,
    )


def test_budget_preserves_correction_and_uncertainty_as_distinct_fields():
    # Given: a component carrying both a correction and a standard uncertainty.
    component = BudgetComponent(
        name="sr-systematic",
        correction=Decimal("-2.3e-18"),
        standard_uncertainty=Decimal("9.2e-19"),
        source="params.json + experimental record",
        status=EvidenceStatus.established,
        required=True,
    )

    # When: the dataclass stores both fields.

    # Then: correction and uncertainty remain distinct, unmodified values.
    assert component.correction == Decimal("-2.3e-18")
    assert component.standard_uncertainty == Decimal("9.2e-19")


def test_correlated_budget_uses_covariance_matrix():
    # Given: two established components with 0.5 correlation.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, 0.5], [0.5, 1.0]])

    # When: the budget is combined.
    result = combine_uncertainty_budget(components, correlation)

    # Then: the total is sqrt(u^T C u) with the covariance cross term.
    expected = Decimal(str(np.sqrt(1.0 + 4.0 + 2.0))) * Decimal("1e-18")
    assert float(result.total_standard_uncertainty) == pytest.approx(
        float(expected), rel=1e-15
    )
    # And: the canonical tuple-of-tuples correlation is stored.
    assert result.correlation == ((1.0, 0.5), (0.5, 1.0))


def test_required_pending_component_blocks_final_total():
    # Given: a pending required component alongside an established one.
    components = (
        established_component("statistical", "7.5e-19"),
        pending_component("yb-systematic", required=True),
    )

    # When: the budget is combined.
    result = combine_uncertainty_budget(components, np.eye(2))

    # Then: no final total is emitted, but the known quadrature is present.
    assert result.total_standard_uncertainty is None
    assert result.known_quadrature is not None
    assert result.status is EvidenceStatus.pending_verification


def test_total_equals_known_quadrature_when_all_required_are_established():
    # Given: two established required components with 0.5 correlation.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, 0.5], [0.5, 1.0]])

    # When: the budget is combined.
    result = combine_uncertainty_budget(components, correlation)

    # Then: the total equals the known quadrature and the status is established.
    assert result.total_standard_uncertainty == result.known_quadrature
    assert result.status is EvidenceStatus.established


def test_zero_uncertainty_is_accepted_as_non_negative():
    # Given: two established components with exactly zero uncertainty.
    components = (
        established_component("a", "0"),
        established_component("b", "0"),
    )

    # When: the budget is combined.
    result = combine_uncertainty_budget(components, np.eye(2))

    # Then: zero is a valid non-negative uncertainty.
    assert result.total_standard_uncertainty == Decimal("0")


def test_duplicate_component_names_rejected():
    # Given: two components sharing the same name.
    components = (
        established_component("a", "1e-18"),
        established_component("a", "2e-18"),
    )

    # When/Then: combination rejects duplicate names.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, np.eye(2))


def test_negative_uncertainty_rejected():
    # Given: a component with a negative standard uncertainty.
    components = (
        established_component("a", "-1e-18"),
        established_component("b", "2e-18"),
    )

    # When/Then: combination rejects it.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, np.eye(2))


def test_nan_uncertainty_rejected():
    # Given: a component with a non-finite (NaN) standard uncertainty.
    components = (
        established_component("a", "NaN"),
        established_component("b", "2e-18"),
    )

    # When/Then: combination rejects it.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, np.eye(2))


def test_non_finite_correlation_rejected():
    # Given: a correlation matrix containing infinity.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, np.inf], [np.inf, 1.0]])

    # When/Then: combination rejects a non-finite matrix.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, correlation)


def test_non_square_correlation_rejected():
    # Given: a non-square correlation matrix.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    # When/Then: combination rejects it.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, correlation)


def test_dimension_mismatch_rejected():
    # Given: a matrix whose dimension differs from the component count.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )

    # When/Then: combination rejects the dimension mismatch.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, np.eye(3))


def test_asymmetric_correlation_rejected():
    # Given: an asymmetric correlation matrix.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, 0.5], [0.2, 1.0]])

    # When/Then: combination rejects non-symmetry.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, correlation)


def test_diagonal_not_one_rejected():
    # Given: a matrix whose diagonal is not all 1.0.
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.1, 0.0], [0.0, 1.0]])

    # When/Then: combination rejects it.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, correlation)


def test_negative_eigenvalue_rejected():
    # Given: a symmetric matrix that is not positive semidefinite
    # ([[1, 2], [2, 1]] has eigenvalues -1 and 3).
    components = (
        established_component("a", "1e-18"),
        established_component("b", "2e-18"),
    )
    correlation = np.array([[1.0, 2.0], [2.0, 1.0]])

    # When/Then: combination rejects the non-PSD matrix.
    with pytest.raises(ValueError):
        combine_uncertainty_budget(components, correlation)


def test_phase_one_components_keep_yb_pending_with_conflict():
    # Given: phase-one components with a statistical input.
    components = build_phase_one_components(Decimal("7.5e-19"))

    # When: the Yb systematic component is located.
    yb = next(c for c in components if c.name == "yb-systematic")

    # Then: it stays pending, required, without a closed uncertainty,
    # recording both conflicting numbers.
    assert yb.status is EvidenceStatus.pending_verification
    assert yb.required is True
    assert yb.standard_uncertainty is None
    assert "1.1e-18" in yb.source
    assert "1.3e-18" in yb.source

    # And: the statistical component is established when the argument is given.
    statistical = next(c for c in components if c.name == "statistical")
    assert statistical.status is EvidenceStatus.established
    assert statistical.standard_uncertainty == Decimal("7.5e-19")


def test_phase_one_budget_blocks_final_total():
    # Given: the phase-one input factory with a statistical uncertainty.
    components = build_phase_one_components(Decimal("7.5e-19"))

    # When: the budget is combined with the identity correlation.
    assert len(components) == 7
    result = combine_uncertainty_budget(components, np.eye(7))

    # Then: the final total is blocked and the known quadrature is reported.
    assert result.total_standard_uncertainty is None
    assert float(result.known_quadrature) == pytest.approx(7.5e-19, rel=1e-15)
    assert result.status is EvidenceStatus.pending_verification
