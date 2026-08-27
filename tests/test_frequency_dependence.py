import unittest

import numpy as np

from gravitation_whsh.frequency_dependence import frequency_dependent_love_numbers


class FrequencyDependenceTests(unittest.TestCase):
    def test_semidiurnal_band_uses_nominal_values(self):
        # M2 frequency (rad/s) lies in the semidiurnal band (> 1e-4).
        h2, k2 = frequency_dependent_love_numbers(1.4051890e-4)
        self.assertAlmostEqual(h2.real, 0.6078, places=12)
        self.assertAlmostEqual(h2.imag, -0.0022, places=12)
        self.assertAlmostEqual(k2.real, 0.30102, places=12)
        self.assertAlmostEqual(k2.imag, -0.0013, places=12)

    def test_diurnal_k1_resonance(self):
        # K1 sits near the FCN resonance: k2 drops well below the nominal 0.29830.
        h2, k2 = frequency_dependent_love_numbers(7.2921158e-5)
        self.assertAlmostEqual(k2.real, 0.258800415826, places=9)
        self.assertAlmostEqual(k2.imag, -0.000286283320, places=9)
        self.assertAlmostEqual(h2.real, 0.526062945528, places=9)

    def test_zonal_band_anelasticity(self):
        # Mf frequency (rad/s) lies in the long-period band (< 2e-5).
        h2, k2 = frequency_dependent_love_numbers(5.3234147e-7)
        self.assertAlmostEqual(k2.real, 0.305379287661, places=9)
        self.assertAlmostEqual(k2.imag, -0.003011426812, places=9)

    def test_permanent_tide_returns_nominal(self):
        h2, k2 = frequency_dependent_love_numbers(0.0)
        self.assertAlmostEqual(h2.real, 0.6078, places=12)
        self.assertAlmostEqual(k2.real, 0.30190, places=12)

    def test_semidiurnal_real_part_matches_nominal(self):
        # The semidiurnal band real parts equal the nominal values: the
        # frequency-dependent correction is purely out-of-phase (anelastic).
        h2, k2 = frequency_dependent_love_numbers(1.4051890e-4)
        self.assertAlmostEqual(k2.real, 0.30102, places=12)
        self.assertAlmostEqual(h2.real, 0.6078, places=12)
        self.assertNotEqual(k2.imag, 0.0)
        self.assertNotEqual(h2.imag, 0.0)

    def test_frequency_correction_is_linear_in_input(self):
        from gravitation_whsh.frequency_dependence import frequency_correction

        rng = np.random.default_rng(0)
        potential = rng.normal(size=720)
        args = rng.normal(size=(720, 6)) * 100.0
        d1_induced, d1_effective = frequency_correction(
            potential, args, longitude_rad=1.0, order=2,
            k2_nominal=0.30102, h2_nominal=0.6078,
        )
        d2_induced, d2_effective = frequency_correction(
            2.0 * potential, args, longitude_rad=1.0, order=2,
            k2_nominal=0.30102, h2_nominal=0.6078,
        )
        np.testing.assert_allclose(d2_induced, 2.0 * d1_induced)
        np.testing.assert_allclose(d2_effective, 2.0 * d1_effective)


if __name__ == "__main__":
    unittest.main()
