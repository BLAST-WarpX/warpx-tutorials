#!/usr/bin/env python3
"""ImpactX input: follow one example electron beam through fixed HTU magnets.

Run twice with --energy-MeV 100 and --energy-MeV 20, in separate output
folders. Open ../htu_transport.ipynb to run both cases and analyze the results.
All source and magnet settings are in this file. No plotting runs here.
"""
import argparse
from pathlib import Path
import os
import numpy as np
from scipy.constants import c, e, m_e

MASS_MEV = m_e * c**2 / e / 1e6

def make_bunch(energy_MeV, count=5000, seed=2026):
    """Same sampled geometry/angles and relative energy spread in both cases.

    An illustrative Gaussian source, not a measured or matched HTU bunch.
    Coordinates are already at fixed s in ImpactX conventions.
    """
    if not np.isfinite(energy_MeV) or energy_MeV <= 0 or count < 2:
        raise ValueError("Energy must be positive and finite; count must be >= 2.")
    rng = np.random.default_rng(seed)
    samples = rng.normal(size=(6, count))
    samples -= samples.mean(axis=1, keepdims=True)
    gamma0 = 1 + energy_MeV / MASS_MEV
    bg0 = np.sqrt(gamma0**2 - 1)
    gamma = 1 + energy_MeV * (1 + 0.01 * samples[5]) / MASS_MEV
    if np.any(gamma <= 1):
        raise ValueError("Sampled kinetic energy must be positive.")
    bg = np.sqrt(gamma**2 - 1)
    # Choose actual slopes, then normalize momenta by reference beta*gamma.
    xp, yp = 2e-3 * samples[3], 2e-3 * samples[4]
    pz = bg / np.sqrt(1 + xp**2 + yp**2)
    return dict(dx=2e-6*samples[0], dy=2e-6*samples[1],
                dt=3e-6*samples[2], dpx=xp*pz/bg0, dpy=yp*pz/bg0,
                dpt=-(gamma-gamma0)/bg0, w=np.full(count, 80e-12/e/count),
                qm_eev=-1/(MASS_MEV*1e6), ref_kin_energy_MeV=energy_MeV,
                bunch_charge_C=80e-12, source="synthetic Gaussian; independent of WarpX")


# Reference kinetic energy used for magnetic rigidity in this beamline, in eV.
REFERENCE_ENERGY_EV = 100e6

ELECTRON_MASS_MEV = m_e * c**2 / e / 1e6  # 0.510998950 MeV


def get_lattice(emq_currents=(0.683822195172598, -0.882403221217054, 1.085116293768873)):
    """Return the list of ImpactX lattice elements for the HTU beamline.

    Parameters
    ----------
    emq_currents : tuple of 3 floats
        Currents in the EMQ1H, EMQ2V, and EMQ3H electromagnet quadrupoles, in amps.
    """
    TCPhosphor = screen("TCPhosphor")
    ChicaneSlit = screen("ChicaneSlit")
    DCPhosphor = screen("DCPhosphor")
    Phosphor1 = screen("Phosphor1")
    Aline1 = screen("UC_ALineEbeam1")
    Aline2 = screen("UC_ALineEBeam2")
    Aline3 = screen("UC_ALineEBeam3")
    VisaEBeam1 = screen("UC_VisaEBeam1")
    VisaEBeam2 = screen("UC_VisaEBeam2")
    VisaEBeam3 = screen("UC_VisaEBeam3")
    VisaEBeam4 = screen("UC_VisaEBeam4")
    VisaEBeam5 = screen("UC_VisaEBeam5")
    VisaEBeam6 = screen("UC_VisaEBeam6")
    VisaEBeam7 = screen("UC_VisaEBeam7")
    VisaEBeam8 = screen("UC_VisaEBeam8")

    # Permanent-magnet quadrupole (PMQ) triplet just after the gas jet.
    SrcToPMQ1 = drift("SrcToPMQ1", 0.052)
    PMQ1V = quadrupole("PMQ1V", L=0.02903, bore_radius=0.006, B=-1.242)
    PMQ2H = quadrupole("PMQ2H", L=0.02890, bore_radius=0.006, B=1.242)
    PMQ3V = quadrupole("PMQ3V", L=0.016321, bore_radius=0.006, B=-1.107)

    L1 = drift("L1", 0.029035)
    L2 = drift("L2", 0.0473895)

    PMQTrip = [PMQ1V, L1, PMQ2H, L2, PMQ3V]

    PMQTripToTCPhos = drift("PMQTripToTCPhos", 0.2158)
    TCPhosToChicane = drift("TCPhosToChicane", 0.42)

    # Steering kickers: kept in the lattice at zero field, as placeholders
    # for where a real orbit correction would be applied.
    S1 = kicker("S1", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0)
    S2 = kicker("S2", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0)
    S3 = kicker("S3", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0)
    S4 = kicker("S4", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0)

    # Magnetic bunch-compression chicane.
    BEND1 = dipole("BEND1", 0.175, r56=200.0, bend=1)
    BEND2 = dipole("BEND2", 0.175, r56=200.0, bend=2)
    BEND3 = dipole("BEND3", 0.175, r56=200.0, bend=3)
    BEND4 = dipole("BEND4", 0.175, r56=200.0, bend=4)

    L12 = drift("L12", 0.125)
    L23 = drift("L23", 0.15)

    Chicane = [BEND1, L12, BEND2, L23, ChicaneSlit, L23, BEND3, L12, BEND4]

    DriftToDCPhos = drift("DriftToDCPhos", 0.27)
    DriftToEMQTrip = drift("DriftToEMQTrip", 0.405)
    EMQ1H = quadrupole("EMQ1H", L=0.1408, current=emq_currents[0], design="EMQD-113-394")
    EMQL1 = drift("EMQL1", 0.112735)
    EMQ2V = quadrupole("EMQ2V", L=0.28141, current=emq_currents[1], design="EMQD-113-949")
    EMQL2 = drift("EMQL2", 0.112735)
    EMQ3H = quadrupole("EMQ3H", L=0.1409, current=emq_currents[2], design="EMQD-113-394")

    EMQTriplet = [EMQ1H, EMQL1, EMQ2V, EMQL2, EMQ3H]

    DriftToPhos1 = drift("DriftToPhos1", 0.084325)
    DriftToSpec = drift("DriftToSpec", 0.28)
    MagSpec = dipole("MagSpec", 0.4826, angle=0.0)

    DriftToAline1 = drift("DriftToAline1", 0.4009)
    DriftToAline2 = drift("DriftToAline2", 0.3825)
    DriftToAline3 = drift("DriftToAline3", 0.4191)

    DriftToUndulator = drift("DriftToUndulator", 0.2945)

    Aline = [DriftToAline1, Aline1, DriftToAline2, Aline2, DriftToAline3, Aline3, DriftToUndulator]

    VS1 = kicker("VS1", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS2 = kicker("VS2", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS3 = kicker("VS3", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS4 = kicker("VS4", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS5 = kicker("VS5", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS6 = kicker("VS6", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS7 = kicker("VS7", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)
    VS8 = kicker("VS8", 0.0, 0.0, max_integrated_field=1970e-6 * 0.5, max_current=5.0)

    VD = drift("VD", 0.018)

    VQ1 = quadrupole("VQ1", L=0.0504, bore_radius=0.004, B=0.132)
    VQ2 = quadrupole("VQ2", L=0.0504, bore_radius=0.004, B=-0.132)
    FODOCell1 = [VQ1, VQ1, VD, VQ2, VQ2, VD]
    UndulatorSegment1 = [*FODOCell1, VS1, VisaEBeam1, *FODOCell1, *FODOCell1, VS2, VisaEBeam2, *FODOCell1]

    VQ3 = quadrupole("VQ3", L=0.0504, bore_radius=0.004, B=0.132)
    VQ4 = quadrupole("VQ4", L=0.0504, bore_radius=0.004, B=-0.132)
    FODOCell2 = [VQ3, VQ3, VD, VQ4, VQ4, VD]
    UndulatorSegment2 = [*FODOCell2, VS3, VisaEBeam3, *FODOCell2, *FODOCell2, VS4, VisaEBeam4, *FODOCell2]

    VQ5 = quadrupole("VQ5", L=0.0504, bore_radius=0.004, B=0.132)
    VQ6 = quadrupole("VQ6", L=0.0504, bore_radius=0.004, B=-0.132)
    FODOCell3 = [VQ5, VQ5, VD, VQ6, VQ6, VD]
    UndulatorSegment3 = [*FODOCell3, VS5, VisaEBeam5, *FODOCell3, *FODOCell3, VS6, VisaEBeam6, *FODOCell3]

    VQ7 = quadrupole("VQ7", L=0.0504, bore_radius=0.004, B=0.132)
    VQ8 = quadrupole("VQ8", L=0.0504, bore_radius=0.004, B=-0.132)
    FODOCell4 = [VQ7, VQ7, VD, VQ8, VQ8, VD]
    UndulatorSegment4 = [*FODOCell4, VS7, VisaEBeam7, *FODOCell4, *FODOCell4, VS8, VisaEBeam8, *FODOCell4]

    B0 = [
        SrcToPMQ1, *PMQTrip, PMQTripToTCPhos, TCPhosphor, TCPhosToChicane,
        S1, *Chicane, S2, DriftToDCPhos, DCPhosphor, DriftToEMQTrip,
        *EMQTriplet, S3, DriftToPhos1, Phosphor1, DriftToSpec, MagSpec,
        S4, *Aline,
    ]
    Undulator = UndulatorSegment1 + UndulatorSegment2 + UndulatorSegment3 + UndulatorSegment4

    return B0 + Undulator


def screen(name):
    """A beam-monitor placed at the location of an HTU diagnostic screen."""
    return elements.BeamMonitor(name=name, backend="h5")


def peakfield_to_Bgradient(bore_radius, B):
    """Convert a peak field in T (at the given bore radius) to a field gradient in T/m."""
    return B / bore_radius


def current_to_Bgradient(current, design):
    """Convert an EMQ current in A to a field gradient in T/m, for a given EMQ design."""
    if design == "EMQD-113-394":
        # From "LBM6_03 Calibration" in EMQD-113-394 Testing Report-FINAL.pdf
        return 2.9217 * current + 0.0965  # T/m
    elif design == "EMQD-113-949":
        # From "LBM6_03 Calibration" in EMQD-113-949 Testing Report-FINAL.pdf
        return 2.9318 * current + 0.0077  # T/m
    else:
        raise ValueError(f"Unsupported design: {design}")


def get_rigidity(reference_energy_eV):
    """Return the magnetic rigidity, in T-m, for a reference kinetic energy in eV."""
    gamma = 1.0 + reference_energy_eV / (ELECTRON_MASS_MEV * 1e6)
    beta = (1 - 1 / gamma**2) ** 0.5
    return m_e * gamma * beta * c / e


def quadrupole(name, L, k1=None, current=None, design=None, bore_radius=None, B=None, reference_energy_eV=REFERENCE_ENERGY_EV):
    """Define an ImpactX chromatic quadrupole element from either (bore_radius, B) or (current, design)."""
    if k1 is None and current is None:
        Bgradient = peakfield_to_Bgradient(bore_radius, B)
    elif k1 is None:
        Bgradient = current_to_Bgradient(current, design)
    # Apply known bore radii at each slice. EMQ bores are unspecified here.
    aperture = bore_radius if bore_radius is not None else 0.0
    return elements.ChrQuad(name=name, ds=L, k=-Bgradient, unit=1,
                            aperture_x=aperture, aperture_y=aperture, nslice=20)


def drift(name, L):
    """Define an ImpactX exact drift element."""
    return elements.ExactDrift(name=name, ds=L, nslice=10)


def current_to_integrated_field(current, max_current, max_integrated_field):
    return current * max_integrated_field / max_current


def kicker(name, current_h, current_v, max_current, max_integrated_field, reference_energy_eV=REFERENCE_ENERGY_EV):
    """Define an ImpactX kicker element from horizontal/vertical steering currents."""
    integrated_field_h = current_to_integrated_field(current_h, max_current, max_integrated_field)
    integrated_field_v = current_to_integrated_field(current_v, max_current, max_integrated_field)
    return elements.Kicker(name=name, xkick=integrated_field_h, ykick=integrated_field_v, unit="T-m")


def chicane_r56_to_field(r56, L, reference_energy_eV):
    """Return the dipole field, in T, for a chicane r56 setting in microns."""
    angle_rad = 0.001438389904456 * r56**0.5
    return -1.0 * get_rigidity(reference_energy_eV) * angle_rad / L


def Bfield_to_angle(Bfield, L, reference_energy_eV):
    """Return the bend angle, in radians, for a dipole field in T."""
    return -1.0 * Bfield * L / get_rigidity(reference_energy_eV)


def dipole(name, L, angle=None, r56=None, bend=None, reference_energy_eV=REFERENCE_ENERGY_EV):
    """Define an ImpactX exact sector-bend dipole element."""
    if angle is None:
        Bfield = chicane_r56_to_field(r56, L, reference_energy_eV)
        angle = Bfield_to_angle(Bfield, L, reference_energy_eV)
    else:
        Bfield = 0.0
    if bend == 1 or bend == 4:
        Bfield = -Bfield
        angle = -angle
    import math

    angle_deg = angle * 180.0 / math.pi
    return elements.ExactSbend(name=name, ds=L, phi=angle_deg, B=Bfield, nslice=10)


def track(bunch):
    from impactx import ImpactX
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--energy-MeV', type=float, default=100.)
    parser.add_argument('--particles', type=int, default=5000)
    parser.add_argument('--output', type=Path, default=Path('impactx-output'),
                        help='New output folder; must not already exist')
    parser.add_argument('--bunch', type=Path,
                        help='Optional converted WarpX NPZ; replaces the synthetic source')
    args = parser.parse_args()
    bunch = (dict(np.load(args.bunch)) if args.bunch else
             make_bunch(args.energy_MeV, args.particles))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(output)
    # Import ImpactX only when running, so source settings can be inspected alone.
    global elements
    from impactx import elements
    track(bunch)
    print(f'Results: {output}')


if __name__ == '__main__':
    main()
