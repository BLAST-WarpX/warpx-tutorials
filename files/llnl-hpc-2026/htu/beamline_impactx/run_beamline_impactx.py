#!/usr/bin/env python3
"""Propagate the WarpX-generated LWFA bunch through the HTU beamline.

Loads the electron bunch converted by ``warpx_to_beamline_impactx.py`` and tracks it
through the full HTU lattice (PMQ triplet, chicane, EMQ triplet,
spectrometer, and the four undulator FODO segments) defined in
``htu_lattice.py``.
"""

import argparse

import numpy as np

from htu_lattice import ELECTRON_MASS_MEV, get_lattice
from impactx import ImpactX, elements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "bunch_npz",
        nargs="?",
        default="warpx_bunch.npz",
        help="Bunch file written by warpx_to_beamline_impactx.py (default: warpx_bunch.npz)",
    )
    args = parser.parse_args()

    bunch = np.load(args.bunch_npz)

    sim = ImpactX()
    sim.particle_shape = 2
    sim.space_charge = False
    sim.slice_step_diagnostics = True
    sim.init_grids()

    ref = sim.particle_container().ref_particle()
    ref.set_charge_qe(-1.0).set_mass_MeV(ELECTRON_MASS_MEV).set_kin_energy_MeV(
        float(bunch["ref_kin_energy_MeV"])
    )

    pc = sim.particle_container()
    pc.add_n_particles(
        bunch["dx"],
        bunch["dy"],
        bunch["dt"],
        bunch["dpx"],
        bunch["dpy"],
        bunch["dpt"],
        float(bunch["qm_eev"]),
        w=bunch["w"],
    )

    monitor = elements.BeamMonitor("monitor", backend="h5")
    sim.lattice.extend([monitor, *get_lattice(), monitor])

    sim.track_particles()
    sim.finalize()


if __name__ == "__main__":
    main()
