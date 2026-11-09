"""Define the HTU beamline lattice for ImpactX.

This is a trimmed port of the HTU lattice used for LBNL BELLA Center's
Hundred Terawatt Undulator (HTU) beamline modeling. It keeps only the
``impactx`` element definitions (drifts, quadrupoles, dipoles, and
beam-monitor screens at the same locations as the real diagnostics), and
drops experiment-specific pieces that don't matter for this tutorial:
steering-magnet currents (kickers ``S1``-``S4`` and ``VS1``-``VS8`` are
kept in the lattice but hardcoded to zero current, since we have no
control-system settings to plug in), and the screen image
calibration/misalignment logic that requires an experiment configuration
file.
"""

from scipy.constants import c, e, m_e

from impactx import elements

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
    return elements.ChrQuad(name=name, ds=L, k=-Bgradient, unit=1, nslice=20)


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
