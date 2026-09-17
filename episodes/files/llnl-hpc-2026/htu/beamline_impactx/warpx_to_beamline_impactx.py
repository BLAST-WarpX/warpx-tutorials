#!/usr/bin/env python3
"""Convert the WarpX LWFA output (lwfa_warpx) into an ImpactX bunch (beamline_impactx).

WarpX and ImpactX cannot run in the same Python process (each calls its own
AMReX/MPI init), so this script is a separate, in-between step: it reads the
self-injected electron bunch from the WarpX openPMD diagnostics, picks out
the accelerated population with an energy cut, and writes the particle
coordinates ImpactX needs (already transformed from WarpX's lab-frame,
fixed-time convention to ImpactX's reference-relative, fixed-s convention)
to a small ``.npz`` file that ``run_beamline_impactx.py`` loads directly.

WarpX's ``momentum/x,y,z`` openPMD records are true SI momentum (mass *
gamma * velocity), but ``openpmd_viewer``'s ``ux,uy,uz`` convenience
quantities are that momentum normalized by ``m_e * c`` -- i.e. proper
velocity, gamma*beta. ImpactX's reference-relative momenta (``px,py,pz``)
use the exact same normalization (by the reference particle's mass), so for
an electron bunch handed to an electron reference particle no unit
conversion is needed here at all: WarpX's ``ux,uy,uz`` plug directly into
the coordinate-transform utilities ImpactX ships for exactly this purpose.
"""

import argparse

import numpy as np
from openpmd_viewer import OpenPMDTimeSeries
from scipy.constants import e

from htu_lattice import ELECTRON_MASS_MEV
from transformation_utilities import to_ref_part_t_from_global_t, to_s_from_t


class RefParticle:
    """Minimal stand-in for ImpactX's reference particle, for use with the
    transform utilities before an ``ImpactX()`` simulation object exists."""

    def __init__(self, x, y, z, px, py, pz, pt):
        self.x = x
        self.y = y
        self.z = z
        self.px = px
        self.py = py
        self.pz = pz
        self.pt = pt


def convert(diags_dir, energy_cut_MeV=20.0, iteration=None):
    """Read the WarpX electron bunch and return ImpactX-ready coordinates.

    Parameters
    ----------
    diags_dir : str
        Path to the WarpX ``diag1`` openPMD series directory (lwfa_warpx's
        ``diags/diag1``).
    energy_cut_MeV : float
        Kinetic energy threshold, in MeV, used to separate the self-injected
        accelerated bunch from the cold background plasma electrons.
    iteration : int or None
        Which openPMD iteration to read. Defaults to the last one written.

    Returns
    -------
    dict with keys ``dx, dy, dt, dpx, dpy, dpt, w, qm_eev, ref_kin_energy_MeV``
    -- everything ``run_beamline_impactx.py`` needs to build the ImpactX bunch.
    """
    ts = OpenPMDTimeSeries(diags_dir)
    it = ts.iterations[-1] if iteration is None else iteration

    x, y, z, ux, uy, uz, w = ts.get_particle(
        ["x", "y", "z", "ux", "uy", "uz", "w"], species="electrons", iteration=it
    )

    gamma = np.sqrt(1.0 + ux**2 + uy**2 + uz**2)
    kinetic_energy_MeV = (gamma - 1.0) * ELECTRON_MASS_MEV
    mask = kinetic_energy_MeV > energy_cut_MeV
    n_selected = int(mask.sum())
    if n_selected == 0:
        raise RuntimeError(
            f"No electrons found above the {energy_cut_MeV} MeV energy cut "
            f"at iteration {it}. Highest kinetic energy present: "
            f"{kinetic_energy_MeV.max():.3f} MeV."
        )

    x, y, z, ux, uy, uz, w = (
        x[mask],
        y[mask],
        z[mask],
        ux[mask],
        uy[mask],
        uz[mask],
        w[mask],
    )

    # Reference particle: mean position/momentum of the selected bunch, at
    # this fixed lab-frame time, moving purely along z.
    ref_x = x.mean()
    ref_y = y.mean()
    ref_z = z.mean()
    ref_gamma = gamma[mask].mean()
    ref_pz = np.sqrt(ref_gamma**2 - 1.0)
    ref_kin_energy_MeV = (ref_gamma - 1.0) * ELECTRON_MASS_MEV
    ref_pt = -ref_gamma
    ref = RefParticle(x=ref_x, y=ref_y, z=ref_z, px=0.0, py=0.0, pz=ref_pz, pt=ref_pt)

    dx, dy, dz, dpx, dpy, dpz = to_ref_part_t_from_global_t(ref, x, y, z, ux, uy, uz)
    dx, dy, dt, dpx, dpy, dpt = to_s_from_t(ref, dx, dy, dz, dpx, dpy, dpz)

    qm_eev = -1.0 / ELECTRON_MASS_MEV / 1e6  # electron charge/mass, in e/eV

    bunch_charge_C = w.sum() * e

    return dict(
        dx=dx,
        dy=dy,
        dt=dt,
        dpx=dpx,
        dpy=dpy,
        dpt=dpt,
        w=w,
        qm_eev=qm_eev,
        ref_kin_energy_MeV=ref_kin_energy_MeV,
        bunch_charge_C=bunch_charge_C,
        n_selected=n_selected,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("diags_dir", help="WarpX openPMD series directory (e.g. ../lwfa_warpx/diags/diag1)")
    parser.add_argument("output_npz", help="Output .npz file for run_beamline_impactx.py")
    parser.add_argument(
        "--energy-cut-MeV",
        type=float,
        default=20.0,
        help="Kinetic energy threshold used to isolate the accelerated bunch (default: 20 MeV)",
    )
    args = parser.parse_args()

    result = convert(args.diags_dir, energy_cut_MeV=args.energy_cut_MeV)
    np.savez(args.output_npz, **result)

    print(f"Selected {result['n_selected']} macroparticles above {args.energy_cut_MeV} MeV")
    print(f"Reference kinetic energy: {result['ref_kin_energy_MeV']:.3f} MeV")
    print(f"Bunch charge: {result['bunch_charge_C'] * 1e12:.3f} pC")
    print(f"Wrote {args.output_npz}")


if __name__ == "__main__":
    main()
