# Two simple accelerator examples

These examples are independent. You can run and visualize either one without
running the other:

1. [WarpX: watch a plasma wake](wakefield.ipynb).
2. [ImpactX: compare beams through HTU](htu_transport.ipynb).

## Registered participants: use your Slack link

Registered participants will receive a link in Slack that opens the AWS-hosted
JupyterLab session directly. Open it; no local installation is needed. If you
registered but cannot find your link, ask the organizers in Slack.

Browse to `warpx-tutorials/episodes/files/llnl-hpc-2026/htu/` and open
`wakefield.ipynb` (select **WarpX GPU**) or `htu_transport.ipynb` (select
**WarpX CPU**). In the hosted wakefield notebook use `warpx_executable = None`.
The files are already on the instance. If you do not have access, use Docker
or Conda below.

## Alternative A: run Docker yourself

The image includes WarpX, ImpactX, the notebooks and analysis tools.

To run the image yourself:

```bash
docker pull ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
docker run --rm -p 127.0.0.1:3000:3000 ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
```

Open <http://localhost:3000/lab>, launch a **Terminal**, and go to:

```bash
cd ~/warpx-tutorials/episodes/files/llnl-hpc-2026/htu
```

The files described below are already there -- no download needed. See the
[tutorial container README](../../../../containers/tutorial/README.md) for
GPU access and other image details.

## Alternative B: running locally with Conda

Use this instead of the Docker image if you want to run the tutorial on
your own machine outside of the provided container, e.g. on a laptop with
no Docker available, or on a cluster where you'd rather use your own Conda
installation.

### Download the complete tutorial folder

Keeping the complete `htu/` directory together is easier than downloading
the files individually, since each exercise expects its scripts, inputs,
and notebooks to remain alongside each other.

With Git installed, download the tutorial folder using sparse checkout.
This preserves its directory structure without downloading the other lessons'
contents; files in parent directories are also included. No packaging script
is needed.

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/BLAST-WarpX/warpx-tutorials.git
cd warpx-tutorials
git sparse-checkout set episodes/files/llnl-hpc-2026/htu
cd episodes/files/llnl-hpc-2026/htu
```

### Create the Conda environment

Run these commands from this directory:

```bash
conda env create --file environment_setup.yml
conda activate llnlhpc26-warpx-tutorial
```

If the environment already exists, update it instead:

```bash
conda env update --name llnlhpc26-warpx-tutorial \
  --file environment_setup.yml --prune
conda activate llnlhpc26-warpx-tutorial
```

The environment installs WarpX and ImpactX from Conda Forge, together with
the Python packages needed by the simulations. This tutorial has been
tested with WarpX 26.09 and ImpactX 26.09. To inspect the installed
versions, run:

```bash
conda list warpx
conda list impactx
```

Deactivate the environment when finished:

```bash
conda deactivate
```

To remove it completely:

```bash
conda env remove --name llnlhpc26-warpx-tutorial
```

## Example 1: a small wakefield in WarpX

Open **[wakefield.ipynb](wakefield.ipynb)** from this folder. Run the cells to
simulate a short laser pulse in plasma, then view a slice of electron density,
the longitudinal electric field, and the electron energy spectrum. Change the
snapshot number to follow the wake as it moves, or view three density frames
side by side. The default is a reduced 3D
teaching model; it is not intended to generate an HTU-quality 100 MeV bunch.

From a terminal, in `htu/lwfa_warpx/`, the equivalent commands are:

```bash
python run_lwfa_warpx.py
python plot_wakefield.py diags/diag1 --evolution --output wake-evolution.png
python plot_wakefield.py diags/diag1 --iteration 800 --output wake-snapshot.png
```

Run these commands in the GPU Python environment (`source
/opt/venv-gpu/bin/activate` in the container). With a native GPU build, you can
instead run `warpx.3d lwfa_warpx_input.txt` using your executable's path.
The plots are saved as `wake-evolution.png` and `wake-snapshot.png`. The notebook creates a fresh output
folder per run. Standalone runs use `diags/`; keep old results separately.

Try changing `a0`, or set `n_up = n_down` to remove the density drop. Compare
the wake and spectrum at the same stage of propagation.

### Wakefield parameters and limitations

The laser and plasma target are deliberately smaller than those in HTU so
we can visualize a wake on a modest GPU. These settings are teaching choices,
not a reproduction of the experimental beam.

| Setting | Default |
| --- | --- |
| Laser wavelength | 0.8 µm |
| Laser strength `a0` (dimensionless) | 3 |
| Laser field waist (radius at 1/e of peak field) | 3 µm |
| Pulse duration (intensity full width at half maximum) | 6 fs |
| Laser focus | z = 10 µm |
| Electron density before/after the drop | 4 × 10^19 / 2 × 10^19 cm^-3 |
| Entrance / density drop / exit | 0–3 / 20–22 / 50–55 µm |
| Moving simulation box | 16 × 16 × 20 µm |
| Grid cells | 32 × 32 × 512 |
| Cell spacing | 0.5 × 0.5 × 0.0390625 µm |
| Time step / total steps | approximately 0.129 fs / 1,836 |
| Simulated particles | one per cell per species; electrons and stationary He2+ ions |
| Saved output | every 200 steps and at the end |

The density changes linearly across each ramp. The plasma starts fully
ionized and electrically neutral, with two electrons per helium ion. The
ions stay fixed. Absorbing boundaries let outgoing waves and particles
leave the box. These are simplifying assumptions, and the grid has not been
refined to establish numerical convergence: use this run to explore the
wake, not to predict experimental beam quality. High-energy electrons do
not necessarily form a compact accelerated bunch.

The notebook shows a central slice at y = 0 and the energy distribution of
all electrons in the moving box. White contours mark the laser's electric
field magnitude |Ey|. A snapshot during propagation is more useful than
the last snapshot, when the moving box has passed the plasma target.

A full run took **8 min 25 s** on an RTX A2000 8 GB laptop GPU. Observed
process GPU memory was **1,140 MiB**, a snapshot rather than a peak-memory
measurement. The 1 GiB initial GPU allocation can grow; it is not a memory
limit. Runtime and memory use may differ on other machines.

For the real HTU experiment and its use of a density drop to trap electrons,
see [Barber et al. (2025)](https://doi.org/10.1103/vh62-gz1p) and
[Kohrell et al. (2026)](https://doi.org/10.1103/z2d3-bhyt).

## Example 2: different beams in the same HTU magnets

Open **[htu_transport.ipynb](htu_transport.ipynb)**. This runs ImpactX using
independent synthetic Gaussian beams at 100 MeV and 20 MeV and plots successive
beam-density maps, surviving charge and horizontal/vertical beam size. It needs no WarpX data and runs on CPU.

There are two teaching files: [input_impactx.py](beamline_impactx/input_impactx.py)
contains the source, magnets and simulation; [htu_transport.ipynb](htu_transport.ipynb)
runs the cases and contains the analysis and plotting code. Change
`energies_MeV` in the notebook to try a different pair. It saves
`beam_density.png`, `comparison.png` and `summary.json` in its new run folder.

To run a single case from `htu/` without the notebook:

```bash
python beamline_impactx/input_impactx.py --energy-MeV 100 --output runs/100MeV
```

Use a new output folder for each run.

The beams have the same sampled positions and angles, 1% rms relative energy
spread, approximately 2 µm rms size and 2 mrad rms divergence, 3 µm rms
`c*delta_t`, and 80 pC charge. These are illustrative assumptions, not a
measured or matched source. The magnet settings remain fixed. Space charge
is off. Known PMQ and undulator focusing-magnet bore radii are modeled; other
beam-pipe apertures are unspecified.

A falling charge curve shows **modeled aperture losses**. A dotted line marks
where coordinates become nonfinite: the tracking approximation has broken
down, so the plot stops and final transmission is reported as `null`. Do not
interpret numerical failure as evidence that every particle hit a real wall.

## Optional coupling

In a larger study, WarpX can generate a bunch for ImpactX. The two examples
above deliberately do not depend on that handoff. To experiment with coupling:

1. Inspect the WarpX phase space and spectrum. Choose an isolated,
   forward-going bunch after it has exited the plasma; a high-energy tail
   alone does not establish a usable bunch. The converter uses an energy
   cut, not a full trapped-bunch classifier.
2. Convert that snapshot. From `htu/`, for standalone WarpX output:

   ```bash
   python coupling/warpx_to_beamline_impactx.py \
     lwfa_warpx/diags/diag1 warpx_bunch.npz --energy-cut-MeV 20
   ```

   Replace the diagnostic path for a notebook run. The final snapshot is
   selected by default; `--iteration` selects another. Choose the cut from
   the observed bunch, not simply to force a nonempty selection. The tiny
   teaching simulation may have no electrons above this example's 20 MeV
   cut; the converter then correctly stops.
3. Track the converted bunch in its own output directory:

   ```bash
   python beamline_impactx/input_impactx.py --bunch warpx_bunch.npz --output coupled_test
   ```

The converter preserves particle weights, chooses a charge-weighted reference
energy, and changes WarpX's fixed-time lab coordinates to ImpactX's fixed-s
reference-relative coordinates. It does not change the magnet settings.
A low-energy bunch in magnets set for 100 MeV can be lost or leave the valid
tracking regime, as in the independent transport example. Meaningful coupling
requires a resolved source, an appropriate bunch selection, and optics matched
to its energy, emittance and Twiss parameters. It is an extension, not required
for either beginner exercise.
