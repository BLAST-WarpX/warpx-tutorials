"""Run with: python -m unittest discover -s tests (from htu/)."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.constants import e

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "coupling"))
import warpx_to_beamline_impactx as handoff
from transformation_utilities import to_global_t_from_ref_part_t, to_t_from_s


class Series:
    iterations = np.array([10, 20])

    def __init__(self, data):
        self.data = data

    def get_particle(self, *args, **kwargs):
        return self.data


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.data = [
            np.array([1., 2., 3., 4.]) * 1e-6,
            np.array([-1., 1., 2., 3.]) * 1e-6,
            np.array([1., 2., 3., 4.]) * 1e-6,
            np.array([0.1, 0.2, 0.1, 0.0]),
            np.array([0.0, 0.1, 0.0, 0.0]),
            np.array([100., 120., -100., 0.]),
            np.array([1., 3., 2., 10.]) * 1e5,
        ]

    def convert(self, data=None, **kwargs):
        with patch.object(handoff, "OpenPMDTimeSeries", return_value=Series(self.data if data is None else data)):
            return handoff.convert("unused", **kwargs)

    def test_selection_charge_and_coordinate_round_trip(self):
        bunch = self.convert()
        self.assertEqual(bunch["n_selected"], 2)
        self.assertEqual(bunch["iteration"], 20)
        w = self.data[-1][:2]
        self.assertAlmostEqual(bunch["bunch_charge_C"] / e, w.sum())
        np.testing.assert_array_equal(bunch["w"], w)
        x, y, z, ux, uy, uz = [a[:2] for a in self.data[:-1]]
        gamma = np.sqrt(1 + ux**2 + uy**2 + uz**2)
        ref_gamma = np.average(gamma, weights=w)
        self.assertAlmostEqual(bunch["ref_kin_energy_MeV"], (ref_gamma - 1) * handoff.ELECTRON_MASS_MEV)
        ref = handoff.RefParticle(*[np.average(a, weights=w) for a in (x,y,z)],
                                  0., 0., np.sqrt(ref_gamma**2 - 1), -ref_gamma)
        fixed_t = to_t_from_s(ref, *[bunch[k] for k in ("dx","dy","dt","dpx","dpy","dpt")])
        recovered = to_global_t_from_ref_part_t(ref, *fixed_t)
        for actual, expected in zip(recovered, (x,y,z,ux,uy,uz)):
            np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_empty_snapshot(self):
        with self.assertRaisesRegex(RuntimeError, "No electrons"):
            self.convert([np.array([]) for _ in range(7)])

    def test_no_accelerated_bunch(self):
        with self.assertRaisesRegex(RuntimeError, "Highest kinetic energy"):
            self.convert(energy_cut_MeV=1000)

    def test_invalid_cut(self):
        for cut in (-1, np.nan, np.inf):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                self.convert(energy_cut_MeV=cut)

    def test_nonfinite_particles(self):
        self.data[0][0] = np.nan
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.convert()

    def test_zero_weights(self):
        self.data[-1][:] = 0
        with self.assertRaisesRegex(RuntimeError, "No forward-going"):
            self.convert()


if __name__ == "__main__":
    unittest.main()
