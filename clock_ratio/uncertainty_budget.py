"""Auditable uncertainty budget for the Wuhan–Shanghai clock comparison.

The budget keeps corrections and standard uncertainties as distinct fields and
never emits a final total while any required component lacks closed evidence.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal

import numpy as np

from clock_ratio.evidence import EvidenceStatus

CovarianceModel = tuple[tuple[float, ...], ...]

_SYMMETRY_ATOL = 1e-12
_DIAGONAL_ATOL = 1e-12
_PSD_MIN_EIGENVALUE = -1e-10


@dataclass(frozen=True, slots=True)
class BudgetComponent:
    name: str
    correction: Decimal | None
    standard_uncertainty: Decimal | None
    source: str
    status: EvidenceStatus
    required: bool


@dataclass(frozen=True, slots=True)
class UncertaintyBudget:
    components: tuple[BudgetComponent, ...]
    correlation: CovarianceModel
    known_quadrature: Decimal
    total_standard_uncertainty: Decimal | None
    status: EvidenceStatus


def _validate_components(components: Sequence[BudgetComponent]) -> None:
    names = [component.name for component in components]
    if len(set(names)) != len(names):
        raise ValueError("component names must be unique")

    for component in components:
        uncertainty = component.standard_uncertainty
        if uncertainty is not None and (
            not uncertainty.is_finite() or uncertainty < 0
        ):
            raise ValueError(
                f"component {component.name!r} has an invalid standard uncertainty"
            )


def _validate_correlation(
    correlation: CovarianceModel | np.ndarray, count: int
) -> np.ndarray:
    matrix = np.asarray(correlation, dtype=float)
    if matrix.size == 0 and count == 0:
        return matrix.reshape(0, 0)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
        raise ValueError("correlation matrix must be square")
    if matrix.shape[0] != count:
        raise ValueError(
            "correlation matrix dimension must match the component count"
        )
    if not np.all(np.isfinite(matrix)):
        raise ValueError("correlation matrix entries must be finite")
    if not np.allclose(matrix, matrix.T, rtol=0, atol=_SYMMETRY_ATOL):
        raise ValueError("correlation matrix must be symmetric")
    if not np.allclose(
        np.diag(matrix), 1.0, rtol=0, atol=_DIAGONAL_ATOL
    ):
        raise ValueError("correlation matrix diagonal must be all 1.0")

    symmetrized = (matrix + matrix.T) / 2.0
    if matrix.size > 0:
        min_eigenvalue = float(np.min(np.linalg.eigvalsh(symmetrized)))
        if min_eigenvalue < _PSD_MIN_EIGENVALUE:
            raise ValueError("correlation matrix must be positive semidefinite")
    return matrix


def _known_quadrature(
    components: Sequence[BudgetComponent], matrix: np.ndarray
) -> Decimal:
    known = [
        (index, component.standard_uncertainty)
        for index, component in enumerate(components)
        if component.standard_uncertainty is not None
    ]
    if not known:
        return Decimal("0")

    indices = [index for index, _ in known]
    uncertainties = np.array(
        [float(uncertainty) for _, uncertainty in known], dtype=float
    )
    sub_matrix = matrix[np.ix_(indices, indices)]
    variance = float(uncertainties @ sub_matrix @ uncertainties)
    return Decimal(str(float(np.sqrt(variance))))


def combine_uncertainty_budget(
    components: Sequence[BudgetComponent],
    correlation: CovarianceModel | np.ndarray,
) -> UncertaintyBudget:
    """Combine known components into an auditable uncertainty budget.

    Raises ValueError for duplicate names, invalid uncertainties, or an
    invalid correlation matrix. The final total is withheld (None) while any
    required component is not established or has no standard uncertainty.
    """
    _validate_components(components)
    matrix = _validate_correlation(correlation, len(components))
    known_quadrature = _known_quadrature(components, matrix)

    can_finalize = all(
        component.status is EvidenceStatus.established
        and component.standard_uncertainty is not None
        for component in components
        if component.required
    )
    total = known_quadrature if can_finalize else None

    if total is None:
        status = EvidenceStatus.pending_verification
    elif all(
        component.status is EvidenceStatus.established for component in components
    ):
        status = EvidenceStatus.established
    else:
        status = EvidenceStatus.supported_with_limitations

    canonical: CovarianceModel = tuple(
        tuple(float(value) for value in row) for row in matrix
    )
    return UncertaintyBudget(
        components=tuple(components),
        correlation=canonical,
        known_quadrature=known_quadrature,
        total_standard_uncertainty=total,
        status=status,
    )


def build_phase_one_components(
    statistical_uncertainty: Decimal | None = None,
    statistical_status: EvidenceStatus | None = None,
) -> tuple[BudgetComponent, ...]:
    """Phase-one budget inputs: no component gets invented closed evidence.

    ``statistical_status`` overrides the legacy derived status for the
    ``statistical`` component when provided; ``None`` preserves the current
    behavior (established iff an uncertainty is supplied).
    """
    if statistical_status is None:
        statistical_status = (
            EvidenceStatus.established
            if statistical_uncertainty is not None
            else EvidenceStatus.pending_verification
        )
    return (
        BudgetComponent(
            name="statistical",
            correction=None,
            standard_uncertainty=statistical_uncertainty,
            source="gap-safe scenario analysis (16-segment provisional primary)",
            status=statistical_status,
            required=True,
        ),
        BudgetComponent(
            name="sr-systematic",
            correction=None,
            standard_uncertainty=None,
            source=(
                "params.json shift_a components (a_rou, a_AC, a_SM, a_air, "
                "a_BBR); no closed uncertainty record exists yet"
            ),
            status=EvidenceStatus.pending_verification,
            required=True,
        ),
        BudgetComponent(
            name="static-potential",
            correction=None,
            standard_uncertainty=None,
            source=(
                "levelling documents for the Wuhan-Shanghai geopotential "
                "difference; no closed uncertainty record extracted yet"
            ),
            status=EvidenceStatus.external_unverified,
            required=True,
        ),
        BudgetComponent(
            name="yb-systematic",
            correction=None,
            standard_uncertainty=None,
            source=(
                "conflicting evidence unresolved: internal 1.1e-18 vs "
                "published 1.3e-18"
            ),
            status=EvidenceStatus.pending_verification,
            required=True,
        ),
        BudgetComponent(
            name="link",
            correction=None,
            standard_uncertainty=None,
            source="1550 nm fibre link; no executable uncertainty evidence",
            status=EvidenceStatus.pending_verification,
            required=True,
        ),
        BudgetComponent(
            name="comb",
            correction=None,
            standard_uncertainty=None,
            source="optical frequency comb; no executable uncertainty evidence",
            status=EvidenceStatus.pending_verification,
            required=True,
        ),
        BudgetComponent(
            name="tidal-residual",
            correction=None,
            standard_uncertainty=None,
            source="tidal residual model; no executable uncertainty evidence",
            status=EvidenceStatus.pending_verification,
            required=True,
        ),
    )
