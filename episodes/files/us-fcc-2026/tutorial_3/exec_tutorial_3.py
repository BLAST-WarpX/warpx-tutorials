"""Couple a linear Xsuite superperiod map to one WarpX beam collision."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import xobjects as xo
import xpart as xp
from scipy.constants import elementary_charge

import tutorial_3_config as config
import tutorial_3_utils as utils


def parse_arguments() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description=(
            "Track two simplified FCC-ee bunches through repeated linear "
            "superperiod maps and optional WarpX beam-beam collisions."
        )
    )
    parser.add_argument("--device", choices=("cpu", "gpu"), default="cpu")
    parser.add_argument("--macroparticles", "--nm", type=int, default=10_000)
    parser.add_argument("--iterations", "--nt", type=int, default=20)
    parser.add_argument("--job-dir", type=Path, default=Path("."))
    parser.add_argument("--output", help="Output directory name inside job-dir")
    parser.add_argument(
        "--input",
        type=Path,
        default=script_dir / "tutorial_3_input.txt",
        help="WarpX input template",
    )
    parser.add_argument(
        "--run-script",
        type=Path,
        default=script_dir / "run_warpx.py",
        help="Python script that launches one rendered WarpX collision",
    )
    parser.add_argument(
        "--no-warpx",
        action="store_true",
        help="Track only the Xsuite arc to generate the reference spectrum",
    )
    parser.add_argument(
        "--beamstrahlung",
        action="store_true",
        help="Enable WarpX quantum-synchrotron photon emission",
    )
    parser.add_argument(
        "--launcher", choices=("direct", "mpirun", "srun"), default="direct"
    )
    parser.add_argument("--ranks", type=int, default=1)
    parser.add_argument(
        "--keep-diags",
        action="store_true",
        help="Archive the openPMD diagnostics from every collision",
    )
    parser.add_argument("--seed", type=int, default=2)
    return parser.parse_args()


def make_bunch(context, beam: dict[str, float], charge: int, rng, count: int):
    return xp.Particles(
        _context=context,
        q0=charge,
        p0c=beam["p0c_eV"],
        mass0=beam["mass0_eV"],
        x=beam["sigma_x"] * rng.standard_normal(count),
        px=beam["sigma_px"] * rng.standard_normal(count),
        y=beam["sigma_y"] * rng.standard_normal(count),
        py=beam["sigma_py"] * rng.standard_normal(count),
        zeta=beam["sigma_z"] * rng.standard_normal(count),
        delta=beam["sigma_delta"] * rng.standard_normal(count),
        weight=np.full(count, beam["bunch_intensity"] / count),
    )


def longitudinal_arrays_by_id(particles):
    ids = utils.as_numpy(particles.particle_id).astype(np.int64)
    order = np.argsort(ids)
    return (
        ids[order],
        utils.as_numpy(particles.zeta)[order],
        utils.as_numpy(particles.delta)[order],
    )


def handoff_row(
    iteration: int,
    beam_number: int,
    sent_ids: np.ndarray,
    before_zeta: np.ndarray,
    before_delta: np.ndarray,
    converted: dict[str, np.ndarray],
    id_mapping: str,
    checks: dict[str, float],
) -> dict:
    order = np.argsort(converted["id"])
    if not np.array_equal(converted["id"][order], sent_ids):
        raise RuntimeError("Could not align returned particles with their input IDs")
    after_zeta = converted["zeta"][order]
    after_delta = converted["delta"][order]
    return {
        "iteration": iteration,
        "beam": beam_number,
        "n_sent": len(sent_ids),
        "n_returned": len(converted["id"]),
        "id_mapping": id_mapping,
        "input_momentum_roundtrip_max": checks["momentum_roundtrip_max"],
        "input_position_roundtrip_max_m": checks["position_roundtrip_max_m"],
        "zeta_mean_before_m": np.mean(before_zeta),
        "zeta_mean_after_m": np.mean(after_zeta),
        "zeta_std_before_m": np.std(before_zeta),
        "zeta_std_after_m": np.std(after_zeta),
        "delta_mean_before": np.mean(before_delta),
        "delta_mean_after": np.mean(after_delta),
        "delta_std_before": np.std(before_delta),
        "delta_std_after": np.std(after_delta),
        "emit_zeta_before_m": utils.covariance_emittance(before_zeta, before_delta),
        "emit_zeta_after_m": utils.covariance_emittance(after_zeta, after_delta),
        "mean_delta_change": np.mean(after_delta - before_delta),
        "rms_zeta_change_m": np.sqrt(np.mean((after_zeta - before_zeta) ** 2)),
    }


def main() -> None:
    args = parse_arguments()
    if args.macroparticles < 2:
        raise ValueError("At least two macroparticles are required")
    if args.iterations < 1:
        raise ValueError("At least one superperiod iteration is required")
    if args.ranks != 1:
        raise ValueError(
            "This teaching adapter currently supports one WarpX rank because "
            "its fallback particle-ID mapping relies on input order."
        )
    if args.no_warpx and args.beamstrahlung:
        raise ValueError("--beamstrahlung requires WarpX")

    job_dir = args.job_dir.resolve()
    job_dir.mkdir(parents=True, exist_ok=True)
    if args.output is None:
        if args.no_warpx:
            output_name = "outputs_without_warpx"
        elif args.beamstrahlung:
            output_name = "outputs_with_warpx_beamstrahlung"
        else:
            output_name = "outputs_with_warpx"
    else:
        output_name = args.output
    output_dir = job_dir / output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    context = xo.ContextCupy() if args.device == "gpu" else xo.ContextCpu()
    beam = config.get_beam_parameters()
    rng = np.random.default_rng(args.seed)
    bunches = {
        1: make_bunch(context, beam, -1, rng, args.macroparticles),
        2: make_bunch(context, beam, +1, rng, args.macroparticles),
    }
    lines = dict(zip((1, 2), utils.build_arc_lines(context, beam)))

    moment_logs = {
        beam_number: utils.open_csv_log(
            output_dir / f"moments_b{beam_number}.csv", utils.MOMENT_COLUMNS
        )
        for beam_number in (1, 2)
    }
    handoff_handle = handoff_writer = None
    if not args.no_warpx:
        handoff_handle, handoff_writer = utils.open_csv_log(
            output_dir / "handoff_checks.csv", utils.HANDOFF_COLUMNS
        )

    warpx_read_dir = job_dir / "warpx_read"
    diag_dir = job_dir / "warpx_dump" / "diags"
    rendered_input = job_dir / "warpx_runtime_input.txt"
    used_inputs = job_dir / "warpx_used_inputs_tutorial_3.txt"
    focal_distance = 4.0 * beam["sigma_z"]

    print(
        f"[setup] Qsp=({beam['qx']:.6f}, {beam['qy']:.6f}, {beam['qs']:.6f}), "
        f"sigma=({beam['sigma_x']:.3e}, {beam['sigma_y']:.3e}, "
        f"{beam['sigma_z']:.3e}) m"
    )
    print(
        f"[setup] {args.iterations} superperiods = "
        f"{args.iterations / beam['n_ip']:.3f} full-ring turns"
    )
    if args.beamstrahlung:
        print(
            "[model] Beamstrahlung is enabled, but arc radiation damping, "
            "quantum excitation, and synchronous-energy compensation are omitted. "
            "This is a transient mismatch study, not an equilibrium model."
        )

    try:
        for iteration in range(1, args.iterations + 1):
            start = time.perf_counter()
            for beam_number in (1, 2):
                lines[beam_number].track(bunches[beam_number])

            n_returned = {1: 0, 2: 0}
            if not args.no_warpx:
                archive = None
                if args.keep_diags and iteration > 1:
                    archive = diag_dir.parent / f"diags_{iteration - 1:06d}"
                utils.prepare_diagnostic_directory(diag_dir, archive)

                outgoing = {}
                checks = {}
                before = {}
                for beam_number in (1, 2):
                    before[beam_number] = longitudinal_arrays_by_id(
                        bunches[beam_number]
                    )
                    outgoing[beam_number], checks[beam_number] = utils.xsuite_to_warpx(
                        bunches[beam_number], beam_number, beam, focal_distance
                    )
                    charge = -elementary_charge if beam_number == 1 else elementary_charge
                    utils.write_openpmd_species(
                        warpx_read_dir / f"beam{beam_number}.bp",
                        f"beam{beam_number}",
                        outgoing[beam_number],
                        charge,
                    )

                # A fresh seed per collision avoids an artificial turn-to-turn
                # correlation of stochastic beamstrahlung emission.
                utils.render_warpx_input(
                    args.input.resolve(),
                    rendered_input,
                    warpx_read_dir / "beam1.bp",
                    warpx_read_dir / "beam2.bp",
                    diag_dir,
                    used_inputs,
                    args.beamstrahlung,
                    random_seed=10_000 + args.seed + iteration,
                )
                utils.run_warpx(
                    args.run_script.resolve(),
                    rendered_input,
                    job_dir,
                    args.launcher,
                    args.ranks,
                )

                for beam_number in (1, 2):
                    returned = utils.read_warpx_species(
                        diag_dir, f"beam{beam_number}"
                    )
                    returned["id"], mapping = utils.map_warpx_ids(
                        returned["id"], outgoing[beam_number]["id"]
                    )
                    converted = utils.warpx_to_xsuite(
                        returned, beam_number, beam, focal_distance
                    )
                    sent_ids, before_zeta, before_delta = before[beam_number]
                    row = handoff_row(
                        iteration,
                        beam_number,
                        sent_ids,
                        before_zeta,
                        before_delta,
                        converted,
                        mapping,
                        checks[beam_number],
                    )
                    utils.write_row(
                        handoff_writer, utils.HANDOFF_COLUMNS, row
                    )
                    utils.update_xsuite_particles(bunches[beam_number], converted)
                    n_returned[beam_number] = len(converted["id"])

            for beam_number in (1, 2):
                values = utils.particle_statistics(
                    bunches[beam_number], iteration, n_returned[beam_number]
                )
                _, writer = moment_logs[beam_number]
                utils.write_row(writer, utils.MOMENT_COLUMNS, values)

            elapsed = time.perf_counter() - start
            print(
                f"[tracking] superperiod {iteration}/{args.iterations} "
                f"completed in {elapsed:.2f} s"
            )
    finally:
        for handle, _ in moment_logs.values():
            handle.close()
        if handoff_handle is not None:
            handoff_handle.close()

    print(f"[done] Results written to {output_dir}")


if __name__ == "__main__":
    main()
