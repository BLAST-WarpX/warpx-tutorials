#!/usr/bin/env python3
"""Plotting helpers for the laser wakefield accelerator notebook."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from openpmd_viewer import OpenPMDTimeSeries
from scipy.constants import c, e, m_e


# WarpX analysis
def plot_snapshot(diags, iteration=None):
    reduced_dir = Path(diags).parent / 'reducedfiles'
    energy_histories = {}
    for name in ('ParticleEnergy', 'FieldEnergy'):
        path = reduced_dir / f'{name}.txt'
        if not path.is_file():
            raise FileNotFoundError(
                f'{path} not found. Rerun the simulation with the energy reduced diagnostics enabled.'
            )
        # Columns: step, time (s), total energy (J), then diagnostic-specific values.
        energy_histories[name] = np.loadtxt(path, usecols=(1, 2), ndmin=2)
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
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    axes = axes.ravel()
    im = axes[0].imshow(-density/e/1e25, origin='lower', extent=extent, aspect='auto',
                        cmap='viridis', vmin=0)
    fig.colorbar(im, ax=axes[0], label=r'$n_e$ ($10^{25}$ m$^{-3}$)')
    # The laser is y polarized; show its transverse field as white contours.
    peak = np.max(np.abs(ey))
    if peak > 0:
        axes[0].contour(info.z*1e6, info.x*1e6, np.abs(ey), levels=[0.3*peak,0.7*peak],
                        colors='white', linewidths=0.5)
    axes[0].set(title='Electron density; white: |Ey|', xlabel='z (µm)', ylabel='x (µm)')
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
    for name, label in (('ParticleEnergy', 'Particle kinetic energy'),
                        ('FieldEnergy', 'Electromagnetic field energy')):
        history = energy_histories[name]
        axes[3].plot(history[:, 0]*1e15, history[:, 1]*1e3, label=label)
    snapshot_time = float(ts.t[np.flatnonzero(ts.iterations == iteration)[0]])
    axes[3].axvline(snapshot_time*1e15, color='0.5', linestyle='--', label='Snapshot time')
    axes[3].set(xlabel='Time (fs)', ylabel='Energy (mJ)', title='Energy in the moving box')
    axes[3].legend()
    axes[3].grid(alpha=0.3)
    fig.suptitle(f'WarpX snapshot: step {iteration}')
    return fig


def plot_density_evolution(diags, iterations=None):
    """Three density slices on one color scale, following the moving window."""
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


if __name__ == '__main__':
    plot_wakefield_main()
