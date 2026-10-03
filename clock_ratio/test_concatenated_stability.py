"""Regression contracts for end-to-end spliced stability."""
from __future__ import annotations

import numpy as np
import pytest

from clock_ratio.concatenated_stability_long import spliced_oadev


def test_spliced_oadev_when_exactly_one_overlapping_pair_exists() -> None:
    values = np.array([0.0, 1.0, 2.0, 3.0])
    point, = spliced_oadev(values, (2,))

    assert point["n_pairs"] == 1
    assert point["sigma_y"] == pytest.approx(np.sqrt(2.0))
