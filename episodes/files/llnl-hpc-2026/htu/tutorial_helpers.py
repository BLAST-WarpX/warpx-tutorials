#!/usr/bin/env python3
"""Shared helpers for the LLNL WarpX and ImpactX notebooks.

Learner entry points: wakefield.ipynb and htu_transport.ipynb.
The HTU lattice and source are adapted from ImpactX revision
74988bd3fb752b336d745e76f2c640e334f2ecd1, examples/htu_beamline.
https://github.com/BLAST-ImpactX/impactx/tree/74988bd3fb752b336d745e76f2c640e334f2ecd1/examples/htu_beamline
Lattice maps and parameters are retained; imports are local to their functions.
The source uses seeded NumPy Gaussian samples with sample means removed.
Upstream driver authors: Axel Huebl and Chad Mitchell.

The upstream copyright notice, conditions and disclaimer follow:
"""
# ImpactX Copyright (c) 2022, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of
# any required approvals from the U.S. Dept. of Energy). All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# (1) Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# (2) Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# (3) Neither the name of the University of California, Lawrence Berkeley
# National Laboratory, U.S. Dept. of Energy nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
#
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# You are under no obligation whatsoever to provide any bug fixes, patches,
# or upgrades to the features, functionality or performance of the source
# code ("Enhancements") to anyone; however, if you choose to make your
# Enhancements available either publicly, or directly to Lawrence Berkeley
# National Laboratory, without imposing a separate written license agreement
# for such Enhancements, then you hereby grant the following license: a
# non-exclusive, royalty-free perpetual license to install, use, modify,
# prepare derivative works, incorporate into other computer software,
# distribute, and sublicense such enhancements or derivative works thereof,
# in binary and source code form.

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import matplotlib.pyplot as plt
import numpy as np
import openpmd_api as io
from scipy.constants import c, e, m_e

HTU = Path(__file__).resolve().parent


# WarpX analysis
def plot_snapshot(diags, iteration=None):
    import matplotlib.pyplot as plt
    from openpmd_viewer import OpenPMDTimeSeries
    ts = OpenPMDTimeSeries(str(diags))
    # The final frame is in vacuum: choose a frame inside the target by default.
    if iteration is None:
        iteration = int(ts.iterations[len(ts.iterations)//2])
    density, info = ts.get_field('rho_electrons', iteration=iteration, slice_across='y')
    ez, _ = ts.get_field('E', coord='z', iteration=iteration, slice_across='y')
    ey, _ = ts.get_field('E', coord='y', iteration=iteration, slice_across='y')
    # Arrange both images as x rows and z columns, independent of storage order.
    order = [next(k for k,v in info.axes.items() if v == axis) for axis in ('x','z')]
    density, ez, ey = [np.transpose(a, order) for a in (density, ez, ey)]
    extent = [info.z[0]*1e6, info.z[-1]*1e6, info.x[0]*1e6, info.x[-1]*1e6]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4), constrained_layout=True)
    im = axes[0].imshow(-density/e/1e25, origin='lower', extent=extent, aspect='auto',
                        cmap='viridis', vmin=0)
    fig.colorbar(im, ax=axes[0], label=r'$n_e$ ($10^{25}$ m$^{-3}$)')
    # The laser is y polarized; show its transverse field as white contours.
    peak = np.max(np.abs(ey))
    if peak > 0:
        axes[0].contour(info.z*1e6, info.x*1e6, np.abs(ey), levels=[0.3*peak,0.7*peak],
                        colors='white', linewidths=0.5)
    axes[0].set(title='Electron density; white: laser field', xlabel='z (µm)', ylabel='x (µm)')
    scale = max(float(np.max(np.abs(ez)))/1e9, 1e-10)
    im = axes[1].imshow(ez/1e9, origin='lower', extent=extent, aspect='auto',
                        cmap='RdBu_r', vmin=-scale, vmax=scale)
    fig.colorbar(im, ax=axes[1], label=r'$E_z$ (GV/m)')
    axes[1].set(title='Longitudinal wakefield', xlabel='z (µm)', ylabel='x (µm)')
    ux,uy,uz,w = ts.get_particle(['ux','uy','uz','w'], species='electrons', iteration=iteration)
    energy = (np.sqrt(1+ux**2+uy**2+uz**2)-1)*m_e*c*c/e/1e6
    axes[2].hist(energy, bins=80, weights=w*e*1e12, histtype='step')
    axes[2].set(xlabel='Electron kinetic energy (MeV)', ylabel='Charge per bin (pC)',
                title='All electrons in the moving box')
    axes[2].set_yscale('log')
    fig.suptitle(f'WarpX snapshot: step {iteration}')
    return fig


def plot_wakefield_main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('diags', nargs='?', default='diags/diag1')
    parser.add_argument('--iteration', type=int)
    parser.add_argument('--output', type=Path, default=Path('wakefield.png'))
    parser.add_argument('--evolution', action='store_true', help='Plot three density snapshots')
    args=parser.parse_args(argv)
    fig=plot_density_evolution(args.diags) if args.evolution else plot_snapshot(args.diags,args.iteration)
    fig.savefig(args.output,dpi=150)
    print(args.output.resolve())



def plot_density_evolution(diags, iterations=None):
    """Three density slices on one color scale, following the moving window."""
    import matplotlib.pyplot as plt
    from openpmd_viewer import OpenPMDTimeSeries
    ts = OpenPMDTimeSeries(str(diags))
    if iterations is None:
        indices = [round((len(ts.iterations)-1)*fraction) for fraction in (0.2,0.4,0.6)]
        iterations = [int(ts.iterations[i]) for i in indices]
    fig, axes = plt.subplots(1, len(iterations), figsize=(12,3.8),
                             constrained_layout=True, squeeze=False)
    for ax, iteration in zip(axes[0], iterations):
        rho, info = ts.get_field('rho_electrons', iteration=iteration, slice_across='y')
        order = [next(k for k,v in info.axes.items() if v == axis) for axis in ('x','z')]
        ne = -np.transpose(rho, order)/e/1e25
        t = float(ts.t[np.flatnonzero(ts.iterations == iteration)[0]])
        # xi=z-ct follows the simulation window, so every panel has the same axes.
        xi = (info.z-c*t)*1e6
        im = ax.imshow(ne, origin='lower', aspect='equal', cmap='magma', vmin=0, vmax=8,
                        extent=[xi[0],xi[-1],info.x[0]*1e6,info.x[-1]*1e6])
        ax.set(title=f'Step {iteration} · {t*1e15:.0f} fs',
               xlabel=r'$z-ct$ (µm)', ylabel='x (µm)')
        ax.tick_params(labelsize=9)
    fig.colorbar(im, ax=list(axes[0]), label=r'Electron density ($10^{25}$ m$^{-3}$)',
                 shrink=0.8, extend='max')
    fig.suptitle('A laser-driven wake evolving through the plasma', fontsize=15)
    return fig



# ImpactX source and execution
MASS_MEV = m_e * c**2 / e / 1e6
REFERENCE_TOTAL_ENERGY_MEV = 100.0
BUNCH_CHARGE_C = 25e-12


def make_bunch(total_energy_MeV=100.0, count=10000, seed=2026):
    """Sample the upstream Gaussian Twiss distribution at fixed s.

    beta_x = beta_y = 2 mm, normalized emittance = 1.5 micrometers,
    sigma_t = 1 micrometer, sigma_pt = 0.025, and all alpha = 0.
    Off-energy cases shift mean_pt while keeping the same reference and
    sampled second moments, as in upstream run_impactx_offenergy1.py.
    """
    if (not np.isfinite(total_energy_MeV) or total_energy_MeV <= MASS_MEV
            or count < 2):
        raise ValueError("Total energy must exceed rest energy; count must be >= 2.")
    rng = np.random.default_rng(seed)
    samples = rng.normal(size=(6, count))
    samples -= samples.mean(axis=1, keepdims=True)
    gamma0 = REFERENCE_TOTAL_ENERGY_MEV / MASS_MEV
    bg0 = np.sqrt(gamma0**2 - 1)
    emittance = 1.5e-6 / bg0
    mean_pt = -(total_energy_MeV - REFERENCE_TOTAL_ENERGY_MEV) / MASS_MEV / bg0
    dpx = np.sqrt(emittance / 0.002) * samples[3]
    dpy = np.sqrt(emittance / 0.002) * samples[4]
    dpt = 0.025 * samples[5] + mean_pt
    gamma = gamma0 - bg0 * dpt
    if np.any(gamma <= 1) or np.any(gamma**2 - 1 <= bg0**2 * (dpx**2 + dpy**2)):
        raise ValueError("Sampled particles must have physical forward momenta.")
    return dict(
        dx=np.sqrt(0.002 * emittance) * samples[0],
        dy=np.sqrt(0.002 * emittance) * samples[1], dt=1e-6 * samples[2],
        dpx=dpx, dpy=dpy, dpt=dpt,
        w=np.full(count, BUNCH_CHARGE_C / e / count),
        qm_eev=-1 / (MASS_MEV * 1e6),
        ref_kin_energy_MeV=REFERENCE_TOTAL_ENERGY_MEV - MASS_MEV,
        bunch_charge_C=BUNCH_CHARGE_C,
        source="HTU Gaussian Twiss source; independent of WarpX",
    )


def prepare_run(argv=None):
    """Read command-line settings, create a fresh output folder and sample the beam."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--total-energy-MeV', type=float, default=100.,
                        help='Mean total energy, including rest energy (default: 100 MeV)')
    parser.add_argument('--chicane-r56-um', type=float, default=200.,
                        help='Chicane control setting in micrometers; use 0 for off-energy scans')
    parser.add_argument('--particles', type=int, default=10000)
    parser.add_argument('--output', type=Path, default=Path('impactx-output'),
                        help='New output folder; must not already exist')
    args = parser.parse_args(argv)
    bunch = make_bunch(args.total_energy_MeV, args.particles)
    if not np.isfinite(args.chicane_r56_um) or args.chicane_r56_um < 0:
        parser.error('--chicane-r56-um must be finite and nonnegative')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.chdir(output)
    return bunch, args.chicane_r56_um

def track(bunch, chicane_r56=200.0):
    from impactx import ImpactX, elements
    sim = ImpactX()
    sim.particle_shape = 2
    sim.space_charge = False  # Independent particles: no collective fields.
    sim.slice_step_diagnostics = True
    sim.init_grids()

    ref = sim.particle_container().ref_particle()
    ref.set_charge_qe(-1.0).set_mass_MeV(MASS_MEV).set_kin_energy_MeV(
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

    # Bookend the upstream magnets with entrance and exit snapshots.
    monitor = elements.BeamMonitor("monitor", backend="h5")
    sim.lattice.extend([monitor, *get_lattice("impactx", chicane_r56=chicane_r56), monitor])

    sim.track_particles()
    sim.finalize()



# ImpactX notebook analysis
COLORS = ("#087e8b", "#d1495b", "#7656a5", "#dd8b16")


def run_beams(particles=10000, energies=(100,), chicane_r56_um=200.):
    """Time complete processes with two requested CPU threads; retain logs."""
    (HTU / "runs").mkdir(exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="transport-", dir=HTU / "runs"))
    performance = []
    for energy in energies:
        case = run / f"{energy:g}MeV"
        log_path = run / f"{energy:g}MeV.log"
        started = time.perf_counter()
        with log_path.open("w") as log:
            result = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "impactx",
                 "--particles", str(particles), "--total-energy-MeV", str(energy),
                 "--chicane-r56-um", str(chicane_r56_um), "--output", str(case)],
                env=dict(os.environ, OMP_NUM_THREADS="2"), stdout=log,
                stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f"ImpactX failed. Read {log_path}")
        elapsed = time.perf_counter() - started
        size = sum(p.stat().st_size for p in case.rglob("*") if p.is_file()) / 2**20
        performance.append(dict(particles=particles, total_energy_MeV=energy,
            chicane_r56_um=chicane_r56_um, requested_cpu_threads=2,
            elapsed_seconds=elapsed, output_MiB=size))
        print(f"{energy:g} MeV | {particles:,} particles | {elapsed:.2f} s | {size:.1f} MiB")
    (run / "performance.json").write_text(json.dumps(performance, indent=2)+"\n")
    print(f"Results: {run}")
    return run


def measurements(run):
    return json.loads((Path(run) / "performance.json").read_text())


def analyze(case):
    files = sorted((case / "diags").glob("reduced_beam_characteristics.*"))
    if not files:
        raise RuntimeError(f"No beam diagnostics in {case}")
    data = np.genfromtxt(files[0], names=True)
    data = np.atleast_1d(data)
    # Beam moments can be undefined after all particles are lost. Never call
    # nonfinite moments a measurement of loss; use the charge diagnostic.
    charge = np.abs(data["charge_C"])
    if not np.all(np.isfinite(charge)):
        raise RuntimeError(f"Nonfinite charge diagnostic in {case}")
    if charge[0] <= 0:
        raise RuntimeError(f"No initial beam charge in {case}")
    fraction = charge / charge[0]
    active = fraction > 0
    finite = np.isfinite(data["sigma_x"]) & np.isfinite(data["sigma_y"])
    bad = np.flatnonzero(active & ~finite)
    stop = int(bad[0]) if len(bad) else len(data)
    # Once the tracking map is invalid, its remaining-particle count is not
    # a trustworthy transmission prediction. Plot only the valid prefix.
    summary = dict(
        final_transmission=(None if len(bad) else float(fraction[-1])),
        first_nonfinite_s_m=(float(data["s"][stop]) if len(bad) else None),
        last_valid_transmission=float(fraction[max(0, stop - 1)]),
        max_rms_size_m=float(
            max(
                np.max(data["sigma_x"][:stop][(active & finite)[:stop]], initial=0),
                np.max(data["sigma_y"][:stop][(active & finite)[:stop]], initial=0),
            )
        ),
    )
    data = data[:stop]
    fraction = fraction[:stop]
    return data, fraction, summary




def screens(case):
    """Read all saved transverse snapshots in beamline order, including exit."""
    _, _, summary = analyze(case)
    cutoff = summary['first_nonfinite_s_m']
    result = []
    for path in sorted((case / 'diags/openPMD').glob('*.h5')):
        series = io.Series(str(path), io.Access.read_only)
        try:
            for iteration in series.iterations:
                beam = series.iterations[iteration].particles['beam']
                s = float(beam.get_attribute('s_ref'))
                if cutoff is not None and s >= cutoff:
                    continue
                frame = beam.to_df()
                values = frame[['position_x', 'position_y', 'weighting']].to_numpy()
                if not np.all(np.isfinite(values)):
                    raise ValueError(f'Invalid tracking at {path.name}; no snapshot shown.')
                name = path.stem
                if name == 'monitor':
                    name = 'Source' if iteration == min(series.iterations) else 'Exit'
                result.append(dict(name=name, s=s, values=values))
        finally:
            series.close()
    return sorted(result, key=lambda item: item['s'])


def histogram(values, limit=None):
    """Full-beam charge map: no percentile cuts or discarded halo particles."""
    if not np.all(np.isfinite(values)):
        raise ValueError('Cannot histogram nonfinite particle coordinates or weights.')
    xy = values[:, :2] * 1e3  # mm throughout; viewer formats small scales as µm.
    if limit is None:
        limit = max(np.max(np.abs(xy), initial=0) * 1.03, 1e-6)
    hist, _, _ = np.histogram2d(*xy.T, bins=48,
        range=[[-limit, limit]] * 2, weights=values[:, 2] * e * 1e12)
    return hist.T, float(limit)


def beam_explorer(run):
    """Create a standalone, offline slider/play viewer and a static contact sheet."""
    import html
    from IPython.display import IFrame
    cases = []
    for record in measurements(run):
        energy = record['total_energy_MeV']
        case = Path(run) / f'{energy:g}MeV'
        snapshots = screens(case)
        _, _, summary = analyze(case)
        if not snapshots:
            raise RuntimeError(f'No valid saved screens in {case}')
        common = max(histogram(snap['values'])[1] for snap in snapshots)
        frames = []
        for snap in snapshots:
            hist, limit = histogram(snap['values'])
            fixed, _ = histogram(snap['values'], common)
            frames.append(dict(name=snap['name'], s=snap['s'], limit=limit,
                hist=hist.tolist(), fixed=fixed.tolist(),
                charge=float(snap['values'][:, 2].sum()*e*1e12)))
        cases.append(dict(energy=energy, frames=frames, common=common,
            invalid_at=summary['first_nonfinite_s_m']))
    positive = [v for case in cases for frame in case['frames']
                for mode in ('hist', 'fixed') for row in frame[mode] for v in row if v > 0]
    low, high = (min(positive), max(positive)) if positive else (.001, 1.)
    high = max(high, low*10)
    palette = (plt.get_cmap('magma')(np.linspace(0, 1, 256))[:, :3]*255).astype(int).tolist()
    payload = dict(cases=cases, low=low, high=high, palette=palette)
    template = BEAM_EXPLORER_HTML
    document = template.replace('__BEAM_DATA__', json.dumps(payload, allow_nan=False))
    (Path(run)/'beam_explorer.html').write_text(document)
    return IFrame('about:blank', width='100%', height=660, extras=[
        'title="HTU beam explorer"', 'sandbox="allow-scripts"',
        'srcdoc="'+html.escape(document, quote=True)+'"'])



def lattice_layout(chicane_r56_um=200.):
    """Use the tracking lattice's element lengths, including zero-length screens."""
    layout = []
    position = 0.
    for element in get_lattice('impactx', chicane_r56=chicane_r56_um):
        length = float(element.ds)
        layout.append(dict(name=element.name, kind=type(element).__name__,
                           start=position, length=length))
        position += length
    return layout


def plot_lattice(ax, chicane_r56_um=200.):
    """Draw a longitudinal schematic, not the bent orbit or physical apertures."""
    from matplotlib.patches import Patch, Rectangle
    from matplotlib.lines import Line2D

    layout = lattice_layout(chicane_r56_um)
    end = layout[-1]['start'] + layout[-1]['length']
    colors = {'ChrQuad': '#087e8b', 'ExactSbend': '#dd8b16',
              'Kicker': '#5d9c43', 'BeamMonitor': '#7656a5'}
    ax.plot([0, end], [0, 0], color='#a5adb8', lw=2, zorder=0)
    for element in layout:
        kind, start, length = element['kind'], element['start'], element['length']
        if kind in ('ChrQuad', 'ExactSbend'):
            ax.add_patch(Rectangle((start, -.3), length, .6,
                                  facecolor=colors[kind], edgecolor='none'))
        elif kind == 'Kicker':
            ax.plot([start, start], [-.4, .4], color=colors[kind], lw=1.5)
        elif kind == 'BeamMonitor':
            ax.plot(start, .58, marker='v', color=colors[kind], ms=4)
        elif kind != 'ExactDrift':
            raise ValueError(f'Add a lattice symbol for {kind}.')
    handles = [Patch(color=colors['ChrQuad'], label='Quadrupole'),
               Patch(color=colors['ExactSbend'], label='Bending magnet'),
               Line2D([], [], color=colors['Kicker'], marker='|', ls='', label='Steerer'),
               Line2D([], [], color=colors['BeamMonitor'], marker='v', ls='', label='Screen'),
               Line2D([], [], color='#a5adb8', label='Drift')]
    ax.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, -.38),
              ncol=5, frameon=False, fontsize=9)
    ax.set(ylim=(-.65, .9), yticks=[], xlabel='Distance along the beamline (m)')
    ax.set_title('Lattice: element lengths to scale; vertical sizes are symbolic',
                 fontsize=10, loc='left')
    ax.spines[['top', 'right', 'left']].set_visible(False)


def plot_beam_sizes(run):
    """Show focusing in both planes and screen landmarks; preserve validity checks."""
    fig, (ax, lattice_ax) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
        gridspec_kw={'height_ratios': [4, 1]}, constrained_layout=True)
    plot_lattice(lattice_ax, measurements(run)[0]['chicane_r56_um'])
    summaries = {}
    for i, record in enumerate(measurements(run)):
        energy = record['total_energy_MeV']
        case = Path(run)/f'{energy:g}MeV'
        data, fraction, summary = analyze(case)
        summaries[f'{energy:g} MeV'] = summary
        for j, plane in enumerate(('x', 'y')):
            sizes = np.where(fraction > 0, data[f'sigma_{plane}']*1e3, np.nan)
            ax.plot(data['s'], sizes, color=COLORS[(2*i+j)%len(COLORS)],
                    ls='-' if j == 0 else '--', lw=2.5, label=f'{energy:g} MeV · {plane}')
        if summary['first_nonfinite_s_m'] is not None:
            ax.axvline(summary['first_nonfinite_s_m'], color='red', ls=':')
            ax.text(.02, .05, 'Tracking invalid: curves stop at the last valid sample.',
                    transform=ax.transAxes, color='red')
        if i == 0:
            for snap in screens(case):
                if snap['name'] in ('TCPhosphor', 'ChicaneSlit', 'UC_VisaEBeam1'):
                    ax.axvline(snap['s'], color='#9aa9b5', lw=1, alpha=.5)
                    label = {'TCPhosphor':'After focusing', 'ChicaneSlit':'Mid-chicane',
                             'UC_VisaEBeam1':'Undulator screens'}[snap['name']]
                    ax.text(snap['s'], 1.02, label, transform=ax.get_xaxis_transform(),
                            fontsize=9, ha='center')
    ax.set(yscale='log', ylabel='Rms beam size (mm)', title='Focusing and expansion along HTU\n')
    ax.grid(alpha=.18); ax.legend(loc='best', ncol=2)
    (Path(run)/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
    fig.savefig(Path(run)/'beam_sizes.png', dpi=160)
    for label, summary in summaries.items():
        fraction = summary['final_transmission']
        print(f"{label}: remaining charge = {100*fraction:.1f}%" if fraction is not None
              else f'{label}: invalid tracking; transmission is not a prediction.')
    print('No apertures are modeled: remaining charge does not tell us whether a real beam fits.')
    plt.show()
    return fig


def compare_cost(baseline, larger):
    """Compare workload cost at fixed physics and thread count, not hardware speedup."""
    records = [measurements(path) for path in (baseline, larger)]
    if any(len(items) != 1 for items in records):
        raise ValueError('Use one energy per run for the particle-count comparison.')
    a, b = [items[0] for items in records]
    for key in ('total_energy_MeV', 'chicane_r56_um', 'requested_cpu_threads'):
        if a[key] != b[key]:
            raise ValueError(f'Keep {key} fixed to compare particle counts.')
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), constrained_layout=True)
    for ax, key, title in zip(axes, ('elapsed_seconds', 'output_MiB'),
                             ('Time to solution (s)', 'Data written (MiB)')):
        bars = ax.bar([f"{r['particles']:,} particles" for r in (a,b)],
                     [a[key], b[key]], color=COLORS[:2], width=.55)
        ax.bar_label(bars, fmt='%.2f', padding=4)
        ax.set(title=title, ylim=(0, max(a[key], b[key])*1.25))
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Computing cost: runtime and output size', fontsize=15)
    fig.savefig(Path(larger)/'hpc_cost.png', dpi=160)
    plt.show()
    return fig

# Offline viewer template
BEAM_EXPLORER_HTML = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HTU beam explorer</title>
<style>
body{margin:0;background:#101627;color:#edf3fa;font:15px system-ui,sans-serif;padding:20px;box-sizing:border-box}h2{margin:0 0 5px}p{color:#bdc9db;margin:8px 0}button,select{font:inherit;padding:7px 12px;border-radius:8px;border:1px solid #75849d;background:#202d45;color:white}button{cursor:pointer}label{display:inline-block;margin:8px 16px 8px 0}input[type=range]{width:100%;accent-color:#ffc36b}canvas{max-width:100%;display:block;margin:auto} .view{display:flex;gap:24px;align-items:center;justify-content:center}.stats{max-width:260px}.badge{color:#ffd18b;font-size:24px;font-weight:bold}#route{height:8px;background:#33435c;border-radius:8px;margin:12px 0}#progress{height:100%;background:#ffc36b;border-radius:8px}.small{font-size:12px}#warning{color:#ffb9bf} @media(max-width:600px){.view{gap:8px}.stats{max-width:160px}body{padding:10px}}
</style>
<h2>HTU beam explorer</h2><p>Follow the bunch through saved HTU screens. Where does it focus, and where does it expand?</p>
<label>Beam <select id="energy" aria-label="Beam energy"></select></label>
<label><input id="fit" type="checkbox" checked> Zoom to fit each screen</label>
<div class="view"><canvas id="beam" width="390" height="360" aria-label="Transverse charge map"></canvas>
<div class="stats"><div id="name" class="badge"></div><p id="position"></p><p id="charge"></p><p id="scale"></p>
<p class="small">Color: charge per bin (pC), logarithmic scale. Bin area changes when zooming; color alone does not compare charge per unit area.</p>
<canvas id="legend" width="240" height="45" aria-label="Charge color scale"></canvas><p id="warning"></p></div></div>
<div id="route"><div id="progress"></div></div>
<label><button id="play" type="button">▶ Play screens</button> <span id="step"></span></label>
<input id="slider" aria-label="Saved screen" type="range" min="0" value="0" step="1">
<p class="small">Snapshots in beamline order, not a movie in physical time. All particles are included. No apertures or collective fields are modeled. Uncheck zoom to compare beam sizes on the same axes.</p>
<script>
const data=__BEAM_DATA__;
const $=id=>document.getElementById(id), canvas=$('beam'), ctx=canvas.getContext('2d');
let timer=null;
for(const c of data.cases){const o=document.createElement('option');o.textContent=c.energy+' MeV';$('energy').append(o);}
function color(v){if(v<=0)return '#100d22';const t=Math.max(0,Math.min(1,Math.log(v/data.low)/Math.log(data.high/data.low)));return 'rgb('+data.palette[Math.round(t*255)].join(',')+')';}
function draw(){
 const c=data.cases[$('energy').selectedIndex], i=Number($('slider').value), f=c.frames[i], fit=$('fit').checked;
 const h=fit?f.hist:f.fixed, limit=fit?f.limit:c.common;
 ctx.clearRect(0,0,390,360);const left=57,top=10,size=292;
 ctx.fillStyle='#100d22';ctx.fillRect(left,top,size,size);
 for(let y=0;y<48;y++)for(let x=0;x<48;x++){ctx.fillStyle=color(h[y][x]);ctx.fillRect(left+x*size/48,top+(47-y)*size/48,size/48+.3,size/48+.3);}
 ctx.strokeStyle='#a5b6cd';ctx.strokeRect(left,top,size,size);ctx.fillStyle='#edf3fa';ctx.font='12px system-ui';
 const unit=limit<.1?'µm':'mm', factor=limit<.1?1000:1, extent=(limit*factor).toPrecision(3);
 ctx.textAlign='center';ctx.fillText('-'+extent,left,321);ctx.fillText('0',left+size/2,321);ctx.fillText(extent,left+size,321);ctx.fillText('x ('+unit+')',left+size/2,348);
 ctx.textAlign='right';ctx.fillText(extent,left-5,18);ctx.fillText('0',left-5,top+size/2);ctx.fillText('-'+extent,left-5,top+size);
 ctx.save();ctx.translate(12,top+size/2);ctx.rotate(-Math.PI/2);ctx.textAlign='center';ctx.fillText('y ('+unit+')',0,0);ctx.restore();
 $('name').textContent=f.name;$('position').textContent='s = '+f.s.toFixed(3)+' m';$('charge').textContent=f.charge.toFixed(2)+' pC on this screen';
 $('scale').textContent=(fit?'Zoom to fit':'Fixed axes')+' · ±'+extent+' '+unit;
 $('step').textContent='Screen '+(i+1)+' / '+c.frames.length;
 $('progress').style.width=100*(f.s-c.frames[0].s)/Math.max(c.frames.at(-1).s-c.frames[0].s,1e-12)+'%';
 $('warning').textContent=c.invalid_at===null?'':'Tracking becomes invalid at s = '+c.invalid_at.toFixed(3)+' m. Later screens are excluded.';
}
function stop(){clearInterval(timer);timer=null;$('play').textContent='▶ Play screens';}
function reset(){stop();$('slider').max=data.cases[$('energy').selectedIndex].frames.length-1;$('slider').value=0;draw();}
$('energy').onchange=reset;$('fit').onchange=draw;$('slider').oninput=()=>{stop();draw();};
$('play').onclick=()=>{if(timer){stop();return;}if(Number($('slider').value)===Number($('slider').max))$('slider').value=0;$('play').textContent='⏸ Pause';draw();timer=setInterval(()=>{const next=Number($('slider').value)+1;if(next>Number($('slider').max)){stop();return;}$('slider').value=next;draw();},650);};
const legend=$('legend').getContext('2d');for(let x=0;x<240;x++){legend.fillStyle=color(data.low*Math.pow(data.high/data.low,x/239));legend.fillRect(x,0,1,16);}legend.fillStyle='#edf3fa';legend.font='12px system-ui';legend.fillText(data.low.toPrecision(2),0,34);legend.textAlign='right';legend.fillText(data.high.toPrecision(2)+' pC',240,34);
reset();
</script></html>
'''

# Upstream HTU lattice
def get_lattice(
    code,
    vs_current_x=[0] * 8,
    vs_current_y=[0] * 8,
    emq_currents=[0.683822195172598, -0.882403221217054, 1.085116293768873],
    chicane_r56=200.0,
    from_element=None,
    to_element=None,
):
    """
    Get the lattice for the HTU accelerator.

    Parameters:
        code (str):
            "impactx", ...
        vs_current_x (list of 8 elements):
            The current in the VISA horizontal steering magnets, in amps.
        vs_current_y (list of 8 elements):
            The current in the VISA vertical steering magnets, in amps.
        emq_currents (list of 3 elements):
            The current in EMQ1H, EMQ2V and EMQ3H, in amps.
        chicane_r56 (float):
            The r56 setting of the chicane, in microns. This is the parameter that is entered in the
            control system, in BELLA operations. It does not necessarily correspond to the actual R56
            of the chicane, esp. if the mean energy of the beam differs from 100 MeV.
        from_element (str):
            The name of the element to start from. If None, start from the beginning.
        to_element (str):
            The name of the element to end at. If None, end at the last element.

    Returns:
        list: The lattice for the HTU accelerator.
    """
    TCPhosphor = screen("TCPhosphor", code)
    ChicaneSlit = screen("ChicaneSlit", code)
    DCPhosphor = screen("DCPhosphor", code)
    Phosphor1 = screen("Phosphor1", code)
    Aline1 = screen(
        "UC_ALineEbeam1",
        code,
    )
    Aline2 = screen(
        "UC_ALineEBeam2",
        code,
    )
    Aline3 = screen(
        "UC_ALineEBeam3",
        code,
    )
    VisaEBeam1 = screen(
        "UC_VisaEBeam1",
        code,
    )
    VisaEBeam2 = screen(
        "UC_VisaEBeam2",
        code,
    )
    VisaEBeam3 = screen(
        "UC_VisaEBeam3",
        code,
    )
    VisaEBeam4 = screen(
        "UC_VisaEBeam4",
        code,
    )
    VisaEBeam5 = screen(
        "UC_VisaEBeam5",
        code,
    )
    VisaEBeam6 = screen(
        "UC_VisaEBeam6",
        code,
    )
    VisaEBeam7 = screen(
        "UC_VisaEBeam7",
        code,
    )
    VisaEBeam8 = screen(
        "UC_VisaEBeam8",
        code,
    )

    # Distance from the plasma source to the first PMQ, when Jetz=6.8
    # Jetz moves the jet Upstream for positive changes.  Therefore, we can
    # get ~6.8mm closer to the PMQ1, and about ~15mm further away.
    SrcToPMQ1 = drift("SrcToPMQ1", 0.052, code)
    PMQ1V = quadrupole("PMQ1V", L=0.02903, bore_radius=0.006, B=-1.242, code=code)
    PMQ2H = quadrupole("PMQ2H", L=0.02890, bore_radius=0.006, B=1.242, code=code)
    PMQ3V = quadrupole("PMQ3V", L=0.016321, bore_radius=0.006, B=-1.107, code=code)

    L1 = drift("L1", 0.029035, code)
    L2 = drift("L2", 0.0473895, code)

    PMQTrip = [PMQ1V, L1, PMQ2H, L2, PMQ3V]

    PMQTripToTCPhos = drift("PMQTripToTCPhos", 0.2158, code)
    TCPhosToChicane = drift("TCPhosToChicane", 0.42, code)

    # Integrated field (converted from G.cm to T.m) and max current from HTU_Kickers_SteeringMagnets.pdf
    # https://drive.google.com/drive/u/0/folders/1r9InjfW7-92OUpZo4xADUm6rVM5u13yt
    S1 = kicker(
        "S1", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0, code=code
    )
    S2 = kicker(
        "S2", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0, code=code
    )
    S3 = kicker(
        "S3", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0, code=code
    )
    S4 = kicker(
        "S4", 0.0, 0.0, max_integrated_field=1970e-6, max_current=5.0, code=code
    )

    # Calculation of the bending field and bend angle are now found in the dipole definitions below.
    BEND1 = dipole("BEND1", 0.175, r56=chicane_r56, bend=1, code=code)
    BEND2 = dipole("BEND2", 0.175, r56=chicane_r56, bend=2, code=code)
    BEND3 = dipole("BEND3", 0.175, r56=chicane_r56, bend=3, code=code)
    BEND4 = dipole("BEND4", 0.175, r56=chicane_r56, bend=4, code=code)

    L12 = drift("L12", 0.125, code)
    L23 = drift("L23", 0.15, code)

    Chicane = [BEND1, L12, BEND2, L23, ChicaneSlit, L23, BEND3, L12, BEND4]

    DriftToDCPhos = drift("DriftToDCPhos", 0.27, code)
    DriftToEMQTrip = drift("DriftToEMQTrip", 0.405, code)
    EMQ1H = quadrupole(
        "EMQ1H", L=0.1408, current=emq_currents[0], design="EMQD-113-394", code=code
    )
    EMQL1 = drift("EMQL1", 0.112735, code)
    EMQ2V = quadrupole(
        "EMQ2V", L=0.28141, current=emq_currents[1], design="EMQD-113-949", code=code
    )
    EMQL2 = drift("EMQL2", 0.112735, code)
    EMQ3H = quadrupole(
        "EMQ3H", L=0.1409, current=emq_currents[2], design="EMQD-113-394", code=code
    )

    EMQTriplet = [EMQ1H, EMQL1, EMQ2V, EMQL2, EMQ3H]

    DriftToPhos1 = drift("DriftToPhos1", 0.084325, code)
    DriftToSpec = drift("DriftToSpec", 0.28, code)
    MagSpec = dipole("MagSpec", 0.4826, angle=0.0, code=code)

    DriftToAline1 = drift("DriftToAline1", 0.4009, code)
    DriftToAline2 = drift("DriftToAline2", 0.3825, code)
    DriftToAline3 = drift("DriftToAline3", 0.4191, code)

    DriftToUndulator = drift("DriftToUndulator", 0.2945, code)
    # TODO: UndulatorAperture = aperture("UndulatorAperture", 0.005, 0.003, code)

    Aline = [
        DriftToAline1,
        Aline1,
        DriftToAline2,
        Aline2,
        DriftToAline3,
        Aline3,
        DriftToUndulator,
    ]

    # Integrated field (converted from G.cm to T.m) is from HTU_Kickers_SteeringMagnets.pdf
    # but scaled by 0.5 to account for lower peak field, per Sam's recommendation
    VS1 = kicker(
        "VS1",
        vs_current_x[0],
        vs_current_y[0],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS2 = kicker(
        "VS2",
        vs_current_x[1],
        vs_current_y[1],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS3 = kicker(
        "VS3",
        vs_current_x[2],
        vs_current_y[2],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS4 = kicker(
        "VS4",
        vs_current_x[3],
        vs_current_y[3],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS5 = kicker(
        "VS5",
        vs_current_x[4],
        vs_current_y[4],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS6 = kicker(
        "VS6",
        vs_current_x[5],
        vs_current_y[5],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS7 = kicker(
        "VS7",
        vs_current_x[6],
        vs_current_y[6],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )
    VS8 = kicker(
        "VS8",
        vs_current_x[7],
        vs_current_y[7],
        max_integrated_field=1970e-6 * 0.5,
        max_current=5.0,
        code=code,
    )

    VD = drift("VD", 0.018, code)

    VQ1 = quadrupole("VQ1", L=0.0504, bore_radius=0.004, B=0.132, code=code)
    VQ2 = quadrupole("VQ2", L=0.0504, bore_radius=0.004, B=-0.132, code=code)
    FODOCell1 = [VQ1, VQ1, VD, VQ2, VQ2, VD]
    UndulatorSegment1 = [
        *FODOCell1,
        VS1,
        VisaEBeam1,
        *FODOCell1,
        *FODOCell1,
        VS2,
        VisaEBeam2,
        *FODOCell1,
    ]

    VQ3 = quadrupole("VQ3", L=0.0504, bore_radius=0.004, B=0.132, code=code)
    VQ4 = quadrupole("VQ4", L=0.0504, bore_radius=0.004, B=-0.132, code=code)
    FODOCell2 = [VQ3, VQ3, VD, VQ4, VQ4, VD]
    UndulatorSegment2 = [
        *FODOCell2,
        VS3,
        VisaEBeam3,
        *FODOCell2,
        *FODOCell2,
        VS4,
        VisaEBeam4,
        *FODOCell2,
    ]

    VQ5 = quadrupole("VQ5", L=0.0504, bore_radius=0.004, B=0.132, code=code)
    VQ6 = quadrupole("VQ6", L=0.0504, bore_radius=0.004, B=-0.132, code=code)
    FODOCell3 = [VQ5, VQ5, VD, VQ6, VQ6, VD]
    UndulatorSegment3 = [
        *FODOCell3,
        VS5,
        VisaEBeam5,
        *FODOCell3,
        *FODOCell3,
        VS6,
        VisaEBeam6,
        *FODOCell3,
    ]

    VQ7 = quadrupole("VQ7", L=0.0504, bore_radius=0.004, B=0.132, code=code)
    VQ8 = quadrupole("VQ8", L=0.0504, bore_radius=0.004, B=-0.132, code=code)
    FODOCell4 = [VQ7, VQ7, VD, VQ8, VQ8, VD]
    UndulatorSegment4 = [
        *FODOCell4,
        VS7,
        VisaEBeam7,
        *FODOCell4,
        *FODOCell4,
        VS8,
        VisaEBeam8,
        *FODOCell4,
    ]

    B0 = [
        SrcToPMQ1,
        *PMQTrip,
        PMQTripToTCPhos,
        TCPhosphor,
        TCPhosToChicane,
        S1,
        *Chicane,
        S2,
        DriftToDCPhos,
        DCPhosphor,
        DriftToEMQTrip,
        *EMQTriplet,
        S3,
        DriftToPhos1,
        Phosphor1,
        DriftToSpec,
        MagSpec,
        S4,
        *Aline,
    ]
    Undulator = (
        UndulatorSegment1 + UndulatorSegment2 + UndulatorSegment3 + UndulatorSegment4
    )
    full_beamline = B0 + Undulator

    # Only return the elements between from_element and to_element
    if from_element is not None:
        element_indices = [
            i for i, elem in enumerate(full_beamline) if elem.name == from_element
        ]
        if len(element_indices) == 0:
            raise ValueError(f"Element {from_element} not found in beamline.")
        elif len(element_indices) > 1:
            raise ValueError(
                f"Multiple elements with name {from_element} found in beamline."
            )
        # Get the first index of the element
        from_index = element_indices[0]
    else:
        from_index = 0
    if to_element is not None:
        element_indices = [
            i for i, elem in enumerate(full_beamline) if elem.name == to_element
        ]
        if len(element_indices) == 0:
            raise ValueError(f"Element {to_element} not found in beamline.")
        elif len(element_indices) > 1:
            raise ValueError(
                f"Multiple elements with name {to_element} found in beamline."
            )
        # Get the first index of the element
        to_index = element_indices[0]
    else:
        to_index = len(full_beamline) - 1
    beamline = full_beamline[from_index : to_index + 1]

    return beamline


# Define a screen element
def screen(name, code):
    """
    Define a screen element.
    """
    from impactx import elements
    return elements.BeamMonitor(name=name, backend="h5")


# Define a quadrupole element
def peakfield_to_Bgradient(bore_radius, B):
    """
    Convert the peak field in T (and corresponding bore radius) to the field gradient in T/m of a quadrupole.

    Parameters:
        bore_radius (float):
            The bore radius in m.
        B (float):
            The peak field in T.
    """
    Bgradient = B / bore_radius
    return Bgradient


def current_to_Bgradient(current, design):
    """
    Convert a current in A to the field gradient in T/m of a quadrupole.

    Parameters:
        current (float):
            The current in A.
        design (str):
            Indicates which EMQ design is being used
    """
    if design == "EMQD-113-394":
        # From "LBM6_03 Calibration" in EMQD-113-394 Testing Report-FINAL.pdf
        Bgradient = 2.9217 * current + 0.0965  # T/m
    elif design == "EMQD-113-949":
        # From "LBM6_03 Calibration" in EMQD-113-949 Testing Report-FINAL.pdf
        Bgradient = 2.9318 * current + 0.0077  # T/m
    else:
        raise ValueError(f"Unsupported design: {design}")
    return Bgradient


def get_rigidity(reference_energy_eV):
    """
    Return the magnetic rigidity associated with reference_energy_eV in
    units of T-m, to be used for field strength normalization.

    Parameters:
        Bfield (float):
            The reference energy in eV.
    """
    gamma = reference_energy_eV * e / (m_e * c**2)
    beta = (1 - 1 / gamma**2) ** 0.5
    rigidity = m_e * gamma * beta * c / e
    return rigidity


def quadrupole(
    name,
    L,
    k1=None,
    current=None,
    design=None,
    bore_radius=None,
    B=None,
    code=None,
    reference_energy_eV=100e6,
):
    """
    Define a quadrupole element.

    Need to provide k1, current, or bore_radius and B.
    """
    from impactx import elements
    if k1 is None and current is None:
        Bgradient = -1.0 * peakfield_to_Bgradient(bore_radius, B)
        unit = 1
    elif k1 is None:
        Bgradient = -1.0 * current_to_Bgradient(current, design)
        unit = 1
    else:
        Bgradient = k1
        unit = 0
    return elements.ChrQuad(name=name, ds=L, k=Bgradient, unit=unit, nslice=1)


# Define a drift element
def drift(name, L, code):
    """
    Define a drift element.
    """
    from impactx import elements
    return elements.ExactDrift(name=name, ds=L, nslice=1)


# Define a kicker element
def current_to_integrated_field(current, max_current, max_integrated_field):
    integrated_field = current * max_integrated_field / max_current
    return integrated_field


def kicker(
    name,
    current_h,
    current_v,
    max_current,
    max_integrated_field,
    code,
    reference_energy_eV=100e6,
):
    """
    Define a kicker element.
    """
    from impactx import elements
    integrated_field_h = current_to_integrated_field(
        current_h, max_current, max_integrated_field
    )
    integrated_field_v = current_to_integrated_field(
        current_v, max_current, max_integrated_field
    )
    return elements.Kicker(
        name=name, xkick=integrated_field_h, ykick=integrated_field_v, unit="T-m"
    )


# Define a dipole element
def chicane_r56_to_field(r56, L, reference_energy_eV):
    """
    Return the magnetic field in T associated with the chicane setting of r56
    defined at the reference energy reference_energy_eV.

    Parameters:
        r56 (float):
            The chicane r56 at nominal energy in microns.
        L (float):
            The bend length in m.
        reference_energy_eV (float):
            The reference energy in eV.
    """

    # Polynomial fit to find the dipole angle as a function of chicane r56 (no longer used)
    # angle_rad = 0.00743627 + 6.32812981e-05*chicane_r56 -4.83395592e-08*chicane_r56**2 + 1.91504783e-11*chicane_r56**3
    # Updated r56 formula valid near r56=0
    angle_rad = 0.001438389904456 * r56**0.5
    # TODO: This angle explicitly assumes that the reference energy of the beam is 100 MeV! We should make
    # sure that this is the case. In particular, for beams with fluctuations in energy, we should keep the
    # energy of the reference particles constant.

    B = -1.0 * get_rigidity(reference_energy_eV) * angle_rad / L
    return B


def Bfield_to_angle(Bfield, L, reference_energy_eV):
    """
    Return the bend angle in radians associated with a magnetic field Bfield
    in units of T, for a bend of length L and specified energy.

    Parameters:
        Bfield (float):
            The value of the magnetic field in T.
        L (float):
            The bend length in m.
        reference_energy_eV (float):
            The reference energy in eV.
    """
    angle = -1.0 * Bfield * L / get_rigidity(reference_energy_eV)
    return angle


def dipole(
    name, L, angle=None, r56=None, bend=None, code=None, reference_energy_eV=100e6
):
    """
    Define a dipole element.
    """
    from impactx import elements
    if angle is None:
        Bfield = chicane_r56_to_field(r56, L, reference_energy_eV=100e6)
        angle = Bfield_to_angle(Bfield, L, reference_energy_eV)
    else:
        Bfield = 0.0
    if bend == 1 or bend == 4:
        Bfield = -Bfield
        angle = -angle
    angle_deg = angle * 180.0 / (3.1415926535898)
    return elements.ExactSbend(name=name, ds=L, phi=angle_deg, B=Bfield, nslice=1)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'impactx':
        bunch, chicane_r56 = prepare_run(sys.argv[2:])
        track(bunch, chicane_r56)
    elif len(sys.argv) > 1 and sys.argv[1] == 'wakefield':
        plot_wakefield_main(sys.argv[2:])
    else:
        raise SystemExit('Usage: python tutorial_helpers.py {impactx|wakefield} --help')
