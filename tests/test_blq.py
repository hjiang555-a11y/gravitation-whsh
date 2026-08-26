from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

import numpy as np

from gravitation_whsh.blq import (
    BlqStation,
    astronomical_arguments,
    radial_displacement,
    read_blq,
)


class BlqTests(unittest.TestCase):
    def test_reads_station_record(self):
        rows = "\n".join(" ".join(str(column + row) for column in range(11)) for row in range(6))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stations.blq"
            path.write_text(f"$$ test\nWUHN\n{rows}\n", encoding="utf-8")
            station = read_blq(path)["WUHN"]

        self.assertEqual(station.amplitudes_m.shape, (3, 11))
        self.assertEqual(station.phases_deg.shape, (3, 11))
        self.assertEqual(station.radial_amplitudes_m[10], 10.0)

    def test_rejects_non_blq_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.blq"
            path.write_text("not a BLQ file\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No valid"):
                read_blq(path)

    def test_zero_amplitudes_produce_zero_displacement(self):
        station = BlqStation("ZERO", np.zeros((3, 11)), np.zeros((3, 11)))
        values = radial_displacement(
            station,
            [
                datetime(2026, 6, 20, tzinfo=timezone.utc),
                datetime(2026, 6, 21, tzinfo=timezone.utc),
            ],
        )
        np.testing.assert_array_equal(values, np.zeros(2))

    def test_astronomical_arguments_are_bounded(self):
        values = astronomical_arguments([datetime(2026, 6, 20, tzinfo=timezone.utc)])
        self.assertEqual(values.shape, (1, 6))
        self.assertTrue(np.all((values >= 0.0) & (values < 360.0)))

    def test_diurnal_tide_includes_doodson_warburg_phase(self):
        epoch = datetime(2026, 6, 20, tzinfo=timezone.utc)
        amplitudes = np.zeros((3, 11))
        amplitudes[0, 4] = 1.0
        station = BlqStation("K1", amplitudes, np.zeros((3, 11)))
        arguments = astronomical_arguments([epoch])
        k1_argument = float(arguments[0] @ np.asarray([1, 1, 0, 0, 0, 0]))
        expected = np.cos(np.deg2rad(k1_argument + 90.0))
        self.assertAlmostEqual(float(radial_displacement(station, [epoch])[0]), expected)


if __name__ == "__main__":
    unittest.main()
