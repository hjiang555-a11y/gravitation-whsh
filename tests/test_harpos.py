from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import numpy as np
from skyfield.api import Loader

from gravitation_whsh.harpos import (
    J2000_TT,
    HarposStation,
    radial_displacement,
    read_harpos,
)


class HarposTests(unittest.TestCase):
    def _station(self, phase=0.0, freq=1.0, accel=0.0, cos=1.0, sin=0.0):
        return HarposStation(
            name="TEST",
            phases_rad=np.asarray([phase]),
            freqs_rad_s=np.asarray([freq]),
            accels_rad_s2=np.asarray([accel]),
            up_cos=np.asarray([cos]),
            up_sin=np.asarray([sin]),
        )

    def test_reads_minimal_harpos_file(self):
        content = "\n".join(
            (
                "HARPOS  Format version of 2005.03.28",
                "H  M2         2.169437D+00   1.405189027044D-04   1.240D-23",
                "S  SHAO      -2831733.3570  4675666.0060  3275369.4810   30.9297 121.2004   22.1",
                "D  M2        SHAO       -0.00552  0.00281 -0.00484   -0.00583 -0.00027  0.00004",
                "HARPOS  Format version of 2005.03.28",
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "station.harpos"
            path.write_text(content, encoding="utf-8")
            stations = read_harpos(path)

        self.assertIn("SHAO", stations)
        station = stations["SHAO"]
        self.assertEqual(station.up_cos.shape, (1,))
        self.assertAlmostEqual(station.up_cos[0], -0.00552)
        self.assertAlmostEqual(station.up_sin[0], -0.00583)
        # D-exponent phase must survive parsing
        self.assertAlmostEqual(station.phases_rad[0], 2.169437)

    def test_rejects_non_harpos_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.harpos"
            path.write_text("not a HARPOS file\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No valid"):
                read_harpos(path)

    def test_zero_amplitudes_produce_zero_displacement(self):
        station = HarposStation(
            name="ZERO",
            phases_rad=np.zeros(1),
            freqs_rad_s=np.ones(1),
            accels_rad_s2=np.zeros(1),
            up_cos=np.zeros(1),
            up_sin=np.zeros(1),
        )
        loader = Loader(tempfile.gettempdir())
        values = radial_displacement(
            station, [datetime(2026, 6, 20, tzinfo=timezone.utc)], loader.timescale()
        )
        np.testing.assert_array_equal(values, np.zeros(1))

    def test_single_cosine_harmonic(self):
        # At t = J2000.0 (TT), a single cosine harmonic with phase 0 is cos(0)=1.
        station = self._station(phase=0.0, freq=1.0, cos=2.5, sin=0.0)
        loader = Loader(tempfile.gettempdir())
        # J2000.0 TT = 2000-01-01 12:00 TT = 2000-01-01 11:58:55.816 UTC
        epoch = datetime(2000, 1, 1, 11, 58, 55, 816000, tzinfo=timezone.utc)
        values = radial_displacement(station, [epoch], loader.timescale())
        self.assertAlmostEqual(float(values[0]), 2.5, places=5)


if __name__ == "__main__":
    unittest.main()
