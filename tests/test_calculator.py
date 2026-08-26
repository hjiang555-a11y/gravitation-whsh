from datetime import datetime, timezone
import unittest

import numpy as np

from gravitation_whsh.calculator import _body_potential, minute_epochs


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


if __name__ == "__main__":
    unittest.main()
