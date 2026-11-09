import os
import re
import warnings

import numpy as np
from openpmd_viewer import OpenPMDTimeSeries
from scipy.constants import c, e, m_e
from scipy.integrate import quad, trapezoid


def extract_macroparticles(species_list, sim_folder=".", diags_name="diags", step=-1):
    """
    Read WarpX coordinates located at 'sim_folder' in 'diags_name'
    corresponding to simulation timestep 'step'.
    """
    x_list = []
    y_list = []
    z_list = []
    w_list = []
    ux_list = []
    uy_list = []
    uz_list = []

    if step==-1:
        folder_list = [
            diags_name+'/particles_in',
            diags_name+'/particles_out/particles_at_xlo',
            diags_name+'/particles_out/particles_at_xhi',
            diags_name+'/particles_out/particles_at_ylo',
            diags_name+'/particles_out/particles_at_yhi',
            diags_name+'/particles_out/particles_at_zlo',
            diags_name+'/particles_out/particles_at_zhi',
            ]
    else:
        folder_list = [ diags_name+'/particles_in', ]
    # Loop through the files that contain particles collected at the edges and in the box
    for folder_name in folder_list:
        read_dir = os.path.join(sim_folder, folder_name)
        if os.path.isdir(read_dir):
            series = OpenPMDTimeSeries(read_dir)
            time = series.t[step]
            iteration = series.iterations[step]
            dt =  series.t[-1] / series.iterations[-1]

            for species in species_list:
                x, y, z, ux, uy, uz, w = series.get_particle( ['x', 'y', 'z', 'ux', 'uy', 'uz', 'w'], iteration=iteration, species=species )

                if ("particles_at" in folder_name):
                    it_scrape, = series.get_particle( ['stepScraped', ], iteration=iteration, species=species )
                    t_scrape = it_scrape * dt

                    momentum_squared = ux**2 + uy**2 + uz**2
                    if "pho" in species:
                        momentum_magnitude = np.sqrt(momentum_squared)
                        vx = c * ux / momentum_magnitude
                        vy = c * uy / momentum_magnitude
                        vz = c * uz / momentum_magnitude
                    else:
                        gamma = np.sqrt(1.0 + momentum_squared / (m_e * c) ** 2)
                        vx = ux / (gamma * m_e)
                        vy = uy / (gamma * m_e)
                        vz = uz / (gamma * m_e)

                    time_since_scrape = time - t_scrape
                    x = x + vx * time_since_scrape
                    y = y + vy * time_since_scrape
                    z = z + vz * time_since_scrape

                # convert from SI [kg m s-1] to [eV/c]
                conversion_factor = c/e

                x_list=np.append(x_list, x)
                y_list=np.append(y_list, y)
                z_list=np.append(z_list, z)
                w_list=np.append(w_list, w)
                ux_list=np.append(ux_list, ux * conversion_factor)
                uy_list=np.append(uy_list, uy * conversion_factor)
                uz_list=np.append(uz_list, uz * conversion_factor)

    # x y z [m], ux, uy, uz [eV/c], w=weight (no dimension)
    return np.asarray(x_list), np.asarray(y_list), np.asarray(z_list), np.asarray(ux_list), np.asarray(uy_list), np.asarray(uz_list), np.asarray(w_list)

def get_Ecom(filename):
    """
    Return 1 numpy array:
    - the center-of-mass energy (in eV)
    """
    with open(filename) as f:
        # First line: header, contains the energies
        line = f.readline()
        Ecom = np.array( list(map( float, re.findall('=(.*?)\\(', line) )) )
    return Ecom

def get_dL_dEcom(filename):
    """
    Return the cumulative differential luminosity and its energy integral.

    Returns:
    - the center-of-mass energy [eV]
    - differential luminosity [m^-2 eV^-1]
    - luminosity integrated over center-of-mass energy [m^-2]
    """
    Ecom = get_Ecom(filename)  # eV
    # ``ndmin=2`` also handles a diagnostic containing only its final row.
    values = np.loadtxt(filename, ndmin=2)[-1, 2:]
    if values.size == Ecom.size + 1:
        # Current WarpX appends the total luminosity after the differential
        # energy bins. Keep it out of the plotted spectrum.
        dL_dEcom = values[:-1]  # m^-2 eV^-1
        Ltot = values[-1]  # m^-2
    elif values.size == Ecom.size:
        # Compatibility with older output that omitted the total column.
        warnings.warn(
            "DifferentialLuminosity has no final total-luminosity column; "
            "integrating the energy bins. Check the WarpX version.",
            RuntimeWarning,
            stacklevel=2,
        )
        dL_dEcom = values
        Ltot = trapezoid(dL_dEcom, Ecom)
    else:
        raise ValueError(
            "Unexpected DifferentialLuminosity layout: "
            f"found {values.size} values for {Ecom.size} energy bins"
        )

    return Ecom, dL_dEcom, Ltot


def luminosity_per_bx_hourglass(
    bunch_intensity,
    sigma_x,
    sigma_y,
    sigma_z,
    phi,
    beta_x_star,
    beta_y_star,
    epsabs=0.0,
    epsrel=1.0e-10,
):
    """Return luminosity per bunch crossing, including the hourglass effect.

    This evaluates the longitudinal overlap of two identical Gaussian bunches.
    The transverse beam sizes evolve around the interaction-point waist as
    ``sigma(s) = sigma_star * sqrt(1 + (s / beta_star)**2)``. The crossing
    angle ``phi`` is the half crossing angle.

    Parameters are in SI units (meters and radians); the returned luminosity
    per bunch crossing is in ``m^-2``.
    """
    positive_parameters = {
        "bunch_intensity": bunch_intensity,
        "sigma_x": sigma_x,
        "sigma_y": sigma_y,
        "sigma_z": sigma_z,
        "beta_x_star": beta_x_star,
        "beta_y_star": beta_y_star,
    }
    for name, value in positive_parameters.items():
        if value <= 0.0:
            raise ValueError(f"{name} must be positive, got {value!r}")

    def integrand(s):
        sigma_x_s = sigma_x * np.sqrt(1.0 + (s / beta_x_star) ** 2)
        sigma_y_s = sigma_y * np.sqrt(1.0 + (s / beta_y_star) ** 2)
        longitudinal_overlap = np.exp(-(s / sigma_z) ** 2)
        crossing_angle_reduction = np.exp(-((phi * s) / sigma_x_s) ** 2)
        return longitudinal_overlap * crossing_angle_reduction / (
            sigma_x_s * sigma_y_s
        )

    overlap_integral, _ = quad(
        integrand,
        -np.inf,
        np.inf,
        epsabs=epsabs,
        epsrel=epsrel,
        limit=200,
    )
    normalization = 4.0 * np.pi * np.sqrt(np.pi) * sigma_z
    return bunch_intensity**2 * overlap_integral / normalization


def integrand_qed(y, beam_energy, electron_mass):
    """Return the radiative-Bhabha cross-section integrand.

    ``y`` is the emitted photon's fractional beam energy. ``beam_energy`` and
    ``electron_mass`` must use the same energy unit; the tutorial uses GeV.
    This expression neglects the beam-size effect.
    """
    if not 0.0 < y < 1.0:
        raise ValueError(f"y must lie strictly between 0 and 1, got {y!r}")
    if beam_energy <= 0.0 or electron_mass <= 0.0:
        raise ValueError("beam_energy and electron_mass must be positive")

    photon_spectrum = (4.0 / 3.0 + y**2 - 4.0 * y / 3.0) / y
    logarithmic_factor = (
        2.0 * np.log(4.0 * beam_energy**2 / electron_mass**2)
        + 2.0 * np.log((1.0 - y) / y)
        - 1.0
    )
    return photon_spectrum * logarithmic_factor


def beam_lifetime(
    cross_section,
    luminosity_per_bx,
    bunch_population,
    n_interaction_points,
    revolution_frequency,
    n_bunches=1,
):
    """Return the beam lifetime in hours.

    ``cross_section * luminosity_per_bx`` must be dimensionless. For example,
    use a cross section in mbarn with luminosity converted to mbarn^-1 per
    bunch crossing, as done in the tutorial notebook.
    """
    positive_parameters = {
        "cross_section": cross_section,
        "luminosity_per_bx": luminosity_per_bx,
        "bunch_population": bunch_population,
        "n_interaction_points": n_interaction_points,
        "revolution_frequency": revolution_frequency,
        "n_bunches": n_bunches,
    }
    for name, value in positive_parameters.items():
        if value <= 0.0:
            raise ValueError(f"{name} must be positive, got {value!r}")

    loss_rate = (
        cross_section
        * luminosity_per_bx
        * n_interaction_points
        * revolution_frequency
        * n_bunches
    )
    return bunch_population / loss_rate / 3600.0
