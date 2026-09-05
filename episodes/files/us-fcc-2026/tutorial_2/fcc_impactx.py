"""Track a matched FCC-ee Z-pole covariance through one ring with ImpactX."""

from __future__ import annotations

from scipy.constants import c, e, m_e

from impactx import ImpactX, distribution, twiss


DO_PARTICLE_TRACKING = False
N_MACROPARTICLES = 10_000_000

P0C_EV = 45.6e9
BUNCH_POPULATION = 20.20e10

BETA_X = 90.0e-3
BETA_Y = 0.7e-3
SIGMA_X = 7_993.75e-9
SIGMA_Y = 35.20e-9
SIGMA_Z = 16.7e-3
SIGMA_DELTA = 1.34e-3


def main() -> None:
    rest_energy_eV = m_e * c**2 / e
    kinetic_energy_MeV = (
        (P0C_EV**2 + rest_energy_eV**2) ** 0.5 - rest_energy_eV
    ) / 1.0e6

    emit_x = SIGMA_X**2 / BETA_X
    emit_y = SIGMA_Y**2 / BETA_Y
    emit_t = SIGMA_Z * SIGMA_DELTA
    beta_t = SIGMA_Z / SIGMA_DELTA

    # These entrance values come from MAD-X TWISS for fccee_p_ring.
    matched = twiss(
        beta_x=9.0001558787240060e-2,
        beta_y=7.0000996200456436e-4,
        beta_t=beta_t,
        emitt_x=emit_x,
        emitt_y=emit_y,
        emitt_t=emit_t,
        alpha_x=-6.6321120158102317e-5,
        alpha_y=7.2350925246117162e-6,
        alpha_t=0.0,
    )
    matched.update(
        dispX=6.4849775346585406e-7,
        dispY=1.2169605840140507e-17,
        dispPx=3.9358998902730878e-6,
        dispPy=-2.7876031925555894e-15,
    )

    simulation = ImpactX()
    simulation.space_charge = False
    simulation.slice_step_diagnostics = True
    simulation.always_warn_immediately = True
    simulation.verbose = 2
    simulation.init_grids()

    # set_species supplies the electron mass, negative charge, and magnetic
    # anomaly.  Set the energy afterwards, following the current ImpactX API.
    reference = simulation.beam.ref
    reference.set_species("electron").set_kin_energy_MeV(kinetic_energy_MeV)

    beam = distribution.Gaussian(**matched)
    if DO_PARTICLE_TRACKING:
        total_charge_coulomb = -BUNCH_POPULATION * e
        simulation.add_particles(total_charge_coulomb, beam, N_MACROPARTICLES)
    else:
        simulation.init_envelope(reference, beam)

    simulation.lattice.load_file("fccee_z.madx", nslice=1)
    simulation.periods = 1

    try:
        if DO_PARTICLE_TRACKING:
            simulation.track_particles()
        else:
            simulation.track_envelope()
    finally:
        simulation.finalize()


if __name__ == "__main__":
    main()
