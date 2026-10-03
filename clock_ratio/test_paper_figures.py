"""Precision contracts for publication-figure source values."""
from __future__ import annotations

from decimal import Decimal

import pytest

from clock_ratio.make_paper_figures import NIST_REF, WLS_REF, ratio_offset_1e18


def test_ratio_offsets_when_near_unity_values_differ_at_e18() -> None:
    assert ratio_offset_1e18("1.207507039343337720797", WLS_REF) == pytest.approx(-0.503)
    assert ratio_offset_1e18(NIST_REF, WLS_REF) == pytest.approx(1.7)
    assert ratio_offset_1e18(Decimal("1.2075070393433377213"), WLS_REF) == 0.0
