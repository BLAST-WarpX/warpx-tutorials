"""Read the self-injected electron bunch out of the WarpX openPMD output."""

import numpy as np
from openpmd_viewer import OpenPMDTimeSeries
from scipy.constants import c, e, m_e

ELECTRON_MASS_MEV = m_e * c**2 / e / 1e6  # 0.510998950 MeV


def read_electrons(diags_dir="diags/diag1", iteration=None):
    """Return the electron species phase space at one iteration.

    Parameters
    ----------
    diags_dir : str
        Path to the WarpX openPMD series directory.
    iteration : int or None
        Which iteration to read. Defaults to the last one written.

    Returns
    -------
    x, y, z : arrays, position in m
    ux, uy, uz : arrays, proper velocity (gamma*beta, dimensionless)
    w : array, macroparticle weight (real electrons represented)
    kinetic_energy_MeV : array
    """
    ts = OpenPMDTimeSeries(diags_dir)
    it = ts.iterations[-1] if iteration is None else iteration

    x, y, z, ux, uy, uz, w = ts.get_particle(
        ["x", "y", "z", "ux", "uy", "uz", "w"], species="electrons", iteration=it
    )
    gamma = np.sqrt(1.0 + ux**2 + uy**2 + uz**2)
    kinetic_energy_MeV = (gamma - 1.0) * ELECTRON_MASS_MEV

    return x, y, z, ux, uy, uz, w, kinetic_energy_MeV
