"""Utilities for the Xsuite--WarpX multi-superperiod tutorial.

The coupling is intentionally restricted to a head-on, single-rank WarpX
collision. Keeping that restriction explicit is safer than silently applying
an incomplete crossing-angle or distributed particle-ID transformation.
"""

from __future__ import annotations

import csv
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from openpmd_api import (
    Access_Type,
    Dataset,
    Mesh_Record_Component,
    Series,
    Unit_Dimension,
)
from openpmd_viewer import OpenPMDTimeSeries
from scipy.constants import c, elementary_charge, m_e
import xtrack as xt


SCALAR = Mesh_Record_Component.SCALAR
BOUNDARY_FOLDERS = (
    "particles_out/particles_at_xlo",
    "particles_out/particles_at_xhi",
    "particles_out/particles_at_ylo",
    "particles_out/particles_at_yhi",
    "particles_out/particles_at_zlo",
    "particles_out/particles_at_zhi",
)

MOMENT_COLUMNS = (
    "iteration",
    "n_returned",
    "n_alive",
    "x_mean",
    "px_mean",
    "y_mean",
    "py_mean",
    "zeta_mean",
    "delta_mean",
    "x_std",
    "px_std",
    "y_std",
    "py_std",
    "zeta_std",
    "delta_std",
    "x_px_cov",
    "y_py_cov",
    "zeta_delta_cov",
    "emit_x",
    "emit_y",
    "emit_zeta",
)

HANDOFF_COLUMNS = (
    "iteration",
    "beam",
    "n_sent",
    "n_returned",
    "id_mapping",
    "input_momentum_roundtrip_max",
    "input_position_roundtrip_max_m",
    "zeta_mean_before_m",
    "zeta_mean_after_m",
    "zeta_std_before_m",
    "zeta_std_after_m",
    "delta_mean_before",
    "delta_mean_after",
    "delta_std_before",
    "delta_std_after",
    "emit_zeta_before_m",
    "emit_zeta_after_m",
    "mean_delta_change",
    "rms_zeta_change_m",
)


def as_numpy(array) -> np.ndarray:
    """Copy an Xsuite CPU or GPU array to a NumPy array."""

    if hasattr(array, "get"):
        return np.asarray(array.get())
    return np.asarray(array)


def covariance_emittance(q: np.ndarray, p: np.ndarray) -> float:
    """Return sqrt(det(cov(q,p))) using population moments."""

    var_q = np.var(q)
    var_p = np.var(p)
    cov_qp = np.mean((q - np.mean(q)) * (p - np.mean(p)))
    return float(np.sqrt(max(var_q * var_p - cov_qp**2, 0.0)))


def particle_statistics(particles, iteration: int, n_returned: int) -> dict[str, float]:
    """Calculate centroid, rms, covariance, and emittance diagnostics."""

    state = as_numpy(particles.state)
    alive = state == 1
    if not np.any(alive):
        raise RuntimeError("No live Xsuite particles remain")

    values = {
        name: as_numpy(getattr(particles, name))[alive]
        for name in ("x", "px", "y", "py", "zeta", "delta")
    }

    result: dict[str, float] = {
        "iteration": iteration,
        "n_returned": n_returned,
        "n_alive": int(np.count_nonzero(alive)),
    }
    for name, array in values.items():
        result[f"{name}_mean"] = float(np.mean(array))
        result[f"{name}_std"] = float(np.std(array))

    result["x_px_cov"] = float(np.cov(values["x"], values["px"], ddof=0)[0, 1])
    result["y_py_cov"] = float(np.cov(values["y"], values["py"], ddof=0)[0, 1])
    result["zeta_delta_cov"] = float(
        np.cov(values["zeta"], values["delta"], ddof=0)[0, 1]
    )
    result["emit_x"] = covariance_emittance(values["x"], values["px"])
    result["emit_y"] = covariance_emittance(values["y"], values["py"])
    result["emit_zeta"] = covariance_emittance(values["zeta"], values["delta"])
    return result


def build_arc_lines(context, beam: dict[str, float]):
    """Build one independent linear superperiod map for each beam."""

    def make_line():
        arc = xt.LineSegmentMap(
            _context=context,
            qx=beam["qx"],
            qy=beam["qy"],
            longitudinal_mode="linear_fixed_qs",
            qs=beam["qs"],
            betx=[beam["beta_x"], beam["beta_x"]],
            bety=[beam["beta_y"], beam["beta_y"]],
            alfx=[0.0, 0.0],
            alfy=[0.0, 0.0],
            bets=beam["beta_s"],
        )
        line = xt.Line(elements=[arc])
        line.build_tracker(_context=context)
        return line

    return make_line(), make_line()


def _beam_frame_signs(beam_number: int) -> tuple[float, float, float]:
    """Signs mapping local (x,y,s) components into the common lab frame."""

    if beam_number == 1:
        return 1.0, 1.0, 1.0
    if beam_number == 2:
        return -1.0, 1.0, -1.0
    raise ValueError("beam_number must be 1 or 2")


def xsuite_to_warpx(
    particles,
    beam_number: int,
    beam: dict[str, float],
    focal_distance: float,
) -> tuple[dict[str, np.ndarray], dict[str, float]]:
    """Convert Xsuite IP coordinates into one common WarpX lab frame.

    Xsuite stores px=Px/P0 and delta=(P-P0)/P0. The geometric slope is
    therefore px/ps, not px, where ps/P0 is obtained from the full momentum
    magnitude. This distinction matters once radiation changes delta.
    """

    if beam["half_crossing_angle"] != 0.0:
        raise NotImplementedError(
            "Tutorial 3 currently implements only a head-on collision. "
            "A crossing angle requires a complete position, momentum, and time transform."
        )

    order = np.argsort(as_numpy(particles.particle_id).astype(np.int64))
    x = as_numpy(particles.x)[order]
    px = as_numpy(particles.px)[order]
    y = as_numpy(particles.y)[order]
    py = as_numpy(particles.py)[order]
    zeta = as_numpy(particles.zeta)[order]
    delta = as_numpy(particles.delta)[order]
    weight = as_numpy(particles.weight)[order]
    particle_id = as_numpy(particles.particle_id)[order].astype(np.int64)

    momentum_sq = (1.0 + delta) ** 2
    transverse_sq = px**2 + py**2
    if np.any(momentum_sq <= transverse_sq):
        raise ValueError("A particle has no real longitudinal momentum")

    ps_over_p0 = np.sqrt(momentum_sq - transverse_sq)
    slope_x = px / ps_over_p0
    slope_y = py / ps_over_p0
    beta_gamma0 = beam["beta_gamma0"]

    ux_local = beta_gamma0 * px
    uy_local = beta_gamma0 * py
    us_local = beta_gamma0 * ps_over_p0
    gamma_local = np.sqrt(1.0 + ux_local**2 + uy_local**2 + us_local**2)

    # Xsuite coordinates are specified when each particle crosses the IP
    # plane, whereas WarpX needs a simultaneous lab-frame snapshot. At
    # t=-f/(beta0*c), propagate each particle from its own crossing time with
    # its own longitudinal velocity c*us/gamma.
    z_local = (
        (zeta - focal_distance)
        * us_local
        / (gamma_local * beam["beta0"])
    )
    x_local = x + z_local * slope_x
    y_local = y + z_local * slope_y

    sx, sy, ss = _beam_frame_signs(beam_number)
    arrays = {
        "x": sx * x_local,
        "y": sy * y_local,
        "z": ss * z_local,
        "ux": sx * ux_local,
        "uy": sy * uy_local,
        "uz": ss * us_local,
        "w": weight,
        "id": particle_id,
    }

    # An algebraic round trip catches sign, normalization, and slope mistakes
    # before WarpX is launched.
    px_rt = ux_local / beta_gamma0
    py_rt = uy_local / beta_gamma0
    delta_rt = np.sqrt(ux_local**2 + uy_local**2 + us_local**2) / beta_gamma0 - 1.0
    x_rt = x_local - z_local * (ux_local / us_local)
    y_rt = y_local - z_local * (uy_local / us_local)
    zeta_rt = (
        beam["beta0"] * gamma_local / us_local * z_local + focal_distance
    )
    checks = {
        "momentum_roundtrip_max": float(
            max(
                np.max(np.abs(px_rt - px)),
                np.max(np.abs(py_rt - py)),
                np.max(np.abs(delta_rt - delta)),
            )
        ),
        "position_roundtrip_max_m": float(
            max(
                np.max(np.abs(x_rt - x)),
                np.max(np.abs(y_rt - y)),
                np.max(np.abs(zeta_rt - zeta)),
            )
        ),
    }
    return arrays, checks


def warpx_to_xsuite(
    arrays: dict[str, np.ndarray],
    beam_number: int,
    beam: dict[str, float],
    focal_distance: float,
) -> dict[str, np.ndarray]:
    """Convert final-time WarpX coordinates back to Xsuite IP coordinates."""

    sx, sy, ss = _beam_frame_signs(beam_number)
    x_local = sx * arrays["x"]
    y_local = sy * arrays["y"]
    z_local = ss * arrays["z"]
    ux_local = sx * arrays["ux"]
    uy_local = sy * arrays["uy"]
    us_local = ss * arrays["uz"]

    if np.any(us_local <= 0.0):
        raise RuntimeError("At least one primary particle reversed longitudinal direction")

    slope_x = ux_local / us_local
    slope_y = uy_local / us_local
    beta_gamma0 = beam["beta_gamma0"]

    # Convert the simultaneous snapshot at t=+f/(beta0*c) back to the time at
    # which each particle crosses the IP plane.
    gamma_local = np.sqrt(1.0 + ux_local**2 + uy_local**2 + us_local**2)
    zeta = (
        beam["beta0"] * gamma_local / us_local * z_local - focal_distance
    )
    x_ip = x_local - z_local * slope_x
    y_ip = y_local - z_local * slope_y

    return {
        "x": x_ip,
        "px": ux_local / beta_gamma0,
        "y": y_ip,
        "py": uy_local / beta_gamma0,
        "zeta": zeta,
        # delta is defined by total momentum, not by its longitudinal component.
        "delta": np.sqrt(ux_local**2 + uy_local**2 + us_local**2)
        / beta_gamma0
        - 1.0,
        "id": arrays["id"].astype(np.int64),
    }


def write_openpmd_species(
    path: Path,
    species_name: str,
    arrays: dict[str, np.ndarray],
    charge_coulomb: float,
) -> None:
    """Write one primary bunch in the format used by WarpX external_file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    series = Series(str(path), Access_Type.create)
    series.set_meshes_path("fields")
    series.set_particles_path("particles")
    species = series.iterations[0].particles[species_name]
    n_particles = len(arrays["x"])
    real_dataset = Dataset(np.dtype("float64"), extent=(n_particles,))
    id_dataset = Dataset(np.dtype("uint64"), extent=(n_particles,))

    species["mass"].reset_dataset(real_dataset)
    species["mass"][SCALAR].make_constant(m_e)
    species["mass"].unit_dimension = {Unit_Dimension.M: 1.0}
    species["mass"][SCALAR].unit_SI = 1.0
    species["charge"].reset_dataset(real_dataset)
    species["charge"][SCALAR].make_constant(charge_coulomb)
    species["charge"].unit_dimension = {
        Unit_Dimension.T: 1.0,
        Unit_Dimension.I: 1.0,
    }
    species["charge"][SCALAR].unit_SI = 1.0

    species["position"].unit_dimension = {Unit_Dimension.L: 1.0}
    species["positionOffset"].unit_dimension = {Unit_Dimension.L: 1.0}

    for component in ("x", "y", "z"):
        species["position"][component].reset_dataset(real_dataset)
        species["position"][component].store_chunk(arrays[component])
        species["position"][component].unit_SI = 1.0
        species["positionOffset"][component].reset_dataset(real_dataset)
        species["positionOffset"][component].make_constant(0.0)
        species["positionOffset"][component].unit_SI = 1.0

    species["momentum"].unit_dimension = {
        Unit_Dimension.L: 1.0,
        Unit_Dimension.M: 1.0,
        Unit_Dimension.T: -1.0,
    }
    for component in ("x", "y", "z"):
        key = f"u{component}"
        species["momentum"][component].reset_dataset(real_dataset)
        species["momentum"][component].store_chunk(arrays[key])
        species["momentum"][component].unit_SI = m_e * c

    species["weighting"].reset_dataset(real_dataset)
    species["weighting"][SCALAR].store_chunk(arrays["w"])
    species["weighting"].unit_dimension = {}
    species["weighting"][SCALAR].unit_SI = 1.0
    species["particle_id"].reset_dataset(id_dataset)
    species["particle_id"][SCALAR].store_chunk(arrays["id"].astype(np.uint64))

    # Do not write opticalDepthQSR. It is a WarpX QED runtime attribute, not
    # part of the documented external_file input, and current WarpX samples it
    # independently for each particle. If a reader ever honored a supplied
    # zero, that value would mean that the emission threshold was already met.

    series.flush()
    del series


def _read_openpmd_folder(
    folder: Path,
    species_name: str,
    propagate_scraped: bool,
) -> dict[str, np.ndarray] | None:
    if not folder.is_dir():
        return None

    time_series = OpenPMDTimeSeries(str(folder), check_all_files=False)
    if species_name not in time_series.avail_species:
        return None

    iteration = int(time_series.iterations[-1])
    final_time = float(time_series.t[-1])
    x, y, z, ux, uy, uz, weight, particle_id = time_series.get_particle(
        ["x", "y", "z", "ux", "uy", "uz", "w", "id"],
        iteration=iteration,
        species=species_name,
    )

    if propagate_scraped and len(x):
        if iteration <= 0:
            raise RuntimeError("Cannot infer the WarpX time step from iteration zero")
        step_scraped, = time_series.get_particle(
            ["stepScraped"], iteration=iteration, species=species_name
        )
        dt = final_time / iteration
        gamma = np.sqrt(1.0 + ux**2 + uy**2 + uz**2)
        remaining_time = final_time - step_scraped * dt
        x = x + c * ux / gamma * remaining_time
        y = y + c * uy / gamma * remaining_time
        z = z + c * uz / gamma * remaining_time

    return {
        "x": np.asarray(x),
        "y": np.asarray(y),
        "z": np.asarray(z),
        "ux": np.asarray(ux),
        "uy": np.asarray(uy),
        "uz": np.asarray(uz),
        "w": np.asarray(weight),
        # WarpX 26.09 IDs can exceed the signed 64-bit range.
        "id": np.asarray(particle_id, dtype=np.uint64),
    }


def read_warpx_species(diag_dir: Path, species_name: str) -> dict[str, np.ndarray]:
    """Combine final in-domain particles with all boundary-scraped particles."""

    chunks = []
    inside = _read_openpmd_folder(diag_dir / "particles_in", species_name, False)
    if inside is not None:
        chunks.append(inside)
    for relative_folder in BOUNDARY_FOLDERS:
        chunk = _read_openpmd_folder(diag_dir / relative_folder, species_name, True)
        if chunk is not None:
            chunks.append(chunk)

    if not chunks:
        raise RuntimeError(f"No WarpX output found for {species_name} in {diag_dir}")

    combined = {
        key: np.concatenate([chunk[key] for chunk in chunks])
        for key in chunks[0]
    }
    if len(np.unique(combined["id"])) != len(combined["id"]):
        raise RuntimeError(f"Duplicate WarpX particle IDs found for {species_name}")
    return combined


def map_warpx_ids(
    output_ids: np.ndarray, sent_ids: np.ndarray
) -> tuple[np.ndarray, str]:
    """Map WarpX IDs back to Xsuite IDs for this single-rank adapter.

    Some WarpX versions preserve the supplied openPMD IDs; others allocate
    AMReX IDs in input order. Since this tutorial requires every primary to be
    recovered from either the full or boundary diagnostic, rank-order mapping
    is unambiguous in the latter case.
    """

    output_ids = np.asarray(output_ids, dtype=np.uint64)
    sent_ids = np.sort(np.asarray(sent_ids, dtype=np.int64))
    if len(output_ids) != len(sent_ids):
        raise RuntimeError(
            f"Sent {len(sent_ids)} primaries but recovered {len(output_ids)}. "
            "The handoff refuses a partial update."
        )

    if np.array_equal(np.sort(output_ids), sent_ids.astype(np.uint64)):
        return output_ids.astype(np.int64), "preserved"

    order = np.argsort(output_ids)
    mapped = np.empty_like(sent_ids)
    mapped[order] = sent_ids
    return mapped, "single-rank input order"


def update_xsuite_particles(particles, converted: dict[str, np.ndarray]) -> None:
    """Update Xsuite arrays by particle ID, including delta-derived internals."""

    current_ids = as_numpy(particles.particle_id).astype(np.int64)
    order = np.argsort(current_ids)
    sorted_ids = current_ids[order]
    locations = np.searchsorted(sorted_ids, converted["id"])
    if np.any(locations == len(sorted_ids)) or not np.array_equal(
        sorted_ids[locations], converted["id"]
    ):
        raise RuntimeError("WarpX returned an ID that is absent from the Xsuite bunch")
    indices = order[locations]

    context = particles._context
    indices_context = context.nparray_to_context_array(indices)
    for name in ("x", "px", "y", "py", "zeta"):
        values = context.nparray_to_context_array(np.asarray(converted[name]))
        getattr(particles, name)[indices_context] = values

    full_delta = particles.delta.copy()
    full_delta[indices_context] = context.nparray_to_context_array(converted["delta"])
    particles.update_delta(full_delta)


def render_warpx_input(
    template_path: Path,
    rendered_path: Path,
    beam1_file: Path,
    beam2_file: Path,
    diag_dir: Path,
    used_inputs_file: Path,
    beamstrahlung: bool,
    random_seed: int,
) -> None:
    """Render paths and run switches without modifying the source template."""

    template = template_path.read_text(encoding="utf-8")
    rendered = template.format(
        BEAM1_FILE=beam1_file.resolve().as_posix(),
        BEAM2_FILE=beam2_file.resolve().as_posix(),
        DIAG_DIR=diag_dir.resolve().as_posix(),
        USED_INPUTS_FILE=used_inputs_file.resolve().as_posix(),
        BEAMSTRAHLUNG=int(beamstrahlung),
        WARPX_SEED=random_seed,
    )
    rendered_path.write_text(rendered, encoding="utf-8")


def run_warpx(
    run_script: Path,
    rendered_input: Path,
    job_dir: Path,
    launcher: str,
    ranks: int,
) -> None:
    """Run one collision and fail immediately if the child process fails."""

    base_command = [sys.executable, str(run_script.resolve()), str(rendered_input.resolve())]
    if launcher == "direct":
        if ranks != 1:
            raise ValueError("The direct launcher supports exactly one rank")
        command = base_command
    elif launcher == "mpirun":
        command = ["mpirun", "-np", str(ranks), *base_command]
    elif launcher == "srun":
        command = ["srun", "-n", str(ranks), "--cpu-bind=cores", *base_command]
    else:
        raise ValueError(f"Unknown launcher: {launcher}")

    print("[coupling]", " ".join(command))
    subprocess.run(command, cwd=job_dir, check=True)


def prepare_diagnostic_directory(diag_dir: Path, archive_dir: Path | None) -> None:
    """Remove or archive the diagnostics from the preceding collision."""

    if not diag_dir.exists():
        return
    if diag_dir.name != "diags" or diag_dir.parent.name != "warpx_dump":
        raise RuntimeError(f"Refusing to remove unexpected diagnostic path: {diag_dir}")
    if archive_dir is None:
        shutil.rmtree(diag_dir)
    else:
        archive_dir.parent.mkdir(parents=True, exist_ok=True)
        if archive_dir.exists():
            raise FileExistsError(archive_dir)
        shutil.move(str(diag_dir), str(archive_dir))


def open_csv_log(path: Path, columns: tuple[str, ...]):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("w", newline="", encoding="utf-8")
    writer = csv.DictWriter(handle, fieldnames=columns)
    writer.writeheader()
    return handle, writer


def write_row(writer: csv.DictWriter, columns: tuple[str, ...], values: dict) -> None:
    writer.writerow({column: values[column] for column in columns})


def read_moment_csv(output_dir: str | Path) -> dict[int, dict[str, np.ndarray]]:
    """Load the two moment logs used by the analysis notebook."""

    output_dir = Path(output_dir)
    result = {}
    for beam_number in (1, 2):
        data = np.genfromtxt(
            output_dir / f"moments_b{beam_number}.csv",
            delimiter=",",
            names=True,
            ndmin=1,
        )
        result[beam_number] = {name: data[name] for name in data.dtype.names}
    return result
