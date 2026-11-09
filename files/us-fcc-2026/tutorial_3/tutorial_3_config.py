"""Parameters for the simplified FCC-ee ttbar multi-superperiod model."""

from __future__ import annotations

import numpy as np


def get_beam_parameters() -> dict[str, float]:
    """Return a fresh dictionary so callers can safely modify its values."""

    params = {
        "circumference": 90_658.816,  # m
        "n_ip": 4,
        "mass0_eV": 0.511e6,
        "p0c_eV": 182.5e9,
        "bunch_intensity": 1.55e11,
        # Deliberately round teaching beam, not the nominal flat FCC-ee beam.
        "gemitt_x": 1.59e-9,  # m
        "gemitt_y": 1.59e-9,  # m
        "beta_x": 1.0,  # m
        "beta_y": 1.0,  # m
        # Beamstrahlung-broadened values retained from the original example.
        # They are not an equilibrium of the tutorial's undamped arc model.
        "sigma_z": 2.17e-3,  # m
        "sigma_delta": 1.92e-3,
        # Full-ring tunes. Qy is intentionally made equal to Qx.
        "qx_full": 398.148,
        "qy_full": 398.148,
        "qs_full": 0.091,
        # The handoff currently supports head-on collisions only.
        "half_crossing_angle": 0.0,
    }

    params["beta_gamma0"] = params["p0c_eV"] / params["mass0_eV"]
    params["gamma0"] = np.sqrt(1.0 + params["beta_gamma0"] ** 2)
    params["beta0"] = params["beta_gamma0"] / params["gamma0"]

    params["sigma_x"] = np.sqrt(params["gemitt_x"] * params["beta_x"])
    params["sigma_px"] = np.sqrt(params["gemitt_x"] / params["beta_x"])
    params["sigma_y"] = np.sqrt(params["gemitt_y"] * params["beta_y"])
    params["sigma_py"] = np.sqrt(params["gemitt_y"] / params["beta_y"])
    params["beta_s"] = params["sigma_z"] / params["sigma_delta"]

    params["qx"] = np.mod(params["qx_full"] / params["n_ip"], 1.0)
    params["qy"] = np.mod(params["qy_full"] / params["n_ip"], 1.0)
    params["qs"] = params["qs_full"] / params["n_ip"]
    return params
