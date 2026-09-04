from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import numpy as np

from gravitation_whsh.calculator import (
    _body_potential,
    load_professional_ocean,
    minute_epochs,
)


class CalculatorTests(unittest.TestCase):
    def test_inclusive_minute_epochs(self):
        start = datetime(2026, 6, 20, tzinfo=timezone.utc)
        end = datetime(2026, 8, 26, 23, 59, tzinfo=timezone.utc)
        epochs = minute_epochs(start, end)
        self.assertEqual(len(epochs), 97_920)
        self.assertEqual(epochs[0], start)
        self.assertEqual(epochs[-1], end)

    def test_rejects_non_minute_boundary(self):
        with self.assertRaisesRegex(ValueError, "whole minutes"):
            minute_epochs(
                datetime(2026, 1, 1, 0, 0, 1),
                datetime(2026, 1, 1, 0, 1),
            )

    def test_degree_two_body_potential_geometry(self):
        station = np.asarray([[2.0], [0.0], [0.0]])
        body = np.asarray([[10.0], [0.0], [0.0]])
        aligned = _body_potential(station, body, gm=100.0, degree=2)
        self.assertAlmostEqual(float(aligned[0]), 0.4)

        perpendicular_body = np.asarray([[0.0], [10.0], [0.0]])
        perpendicular = _body_potential(station, perpendicular_body, gm=100.0, degree=2)
        self.assertAlmostEqual(float(perpendicular[0]), -0.2)

    def test_load_professional_ocean_preserves_sign_and_epochs(self):
        # The professional ocean-loading ΔW series is authoritative and must be
        # consumed as-is (no sign flip): its values are already Shanghai-minus-Wuhan
        # (SHAO − WUHN), matching the solid-tide convention. This test locks that
        # sign and the epoch-parsing behaviour against regression.
        content = (
            "timestamp_utc,ocean_loading_delta_m2_s2\n"
            "2026-06-20T00:00:00Z,-0.167949027\n"
            "2026-06-20T00:00:30Z,-0.168959770\n"
            "2026-06-20T00:01:00Z,-0.169966595\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prof_ocean.csv"
            path.write_text(content, encoding="utf-8")
            epochs, delta_w = load_professional_ocean(path)

        self.assertEqual(len(epochs), 3)
        self.assertEqual(len(delta_w), 3)
        expected_t0 = datetime(2026, 6, 20, tzinfo=timezone.utc).timestamp()
        self.assertAlmostEqual(float(epochs[0]), expected_t0)
        self.assertAlmostEqual(float(epochs[2] - epochs[0]), 60.0)
        # Sign is preserved verbatim (authoritative SHAO − WUHN convention).
        np.testing.assert_allclose(
            delta_w, [-0.167949027, -0.168959770, -0.169966595]
        )

    def test_load_professional_ocean_handles_tz_naive_iso(self):
        # A "+00:00" (or bare) UTC suffix parses to the same epoch as "Z".
        content = (
            "timestamp_utc,ocean_loading_delta_m2_s2\n"
            "2026-06-20T00:00:00+00:00,-0.1\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prof_ocean.csv"
            path.write_text(content, encoding="utf-8")
            epochs, delta_w = load_professional_ocean(path)
        expected = datetime(2026, 6, 20, tzinfo=timezone.utc).timestamp()
        self.assertAlmostEqual(float(epochs[0]), expected)
        self.assertAlmostEqual(float(delta_w[0]), -0.1)


if __name__ == "__main__":
    unittest.main()
