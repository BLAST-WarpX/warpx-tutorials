# LLNL HPC Innovation Center 2026: WarpX and ImpactX tutorial

This directory provides a three-part accelerator-physics
tutorial combining WarpX and ImpactX:

1. `two_stream_instability/`: a quick 1D two-stream instability warm-up with
   WarpX, used to get everyone to a working simulate-then-analyze pipeline
   before the heavier exercises below;
2. `htu/lwfa_warpx/`: a small, visual 3D wakefield demonstration; and
3. `htu/beamline_impactx/htu_transport.ipynb`: the upstream 100 MeV total-energy HTU beam
   with an optional beam-energy experiment.

The WarpX and ImpactX exercises are separate. Their helper modules are `htu/lwfa_warpx/warpx_helpers.py` for WarpX plots and `htu/beamline_impactx/impactx_helpers.py` for ImpactX analysis. The ImpactX notebook defines and runs the simulation directly in its kernel.

The complete lesson and explanations are in
[`episodes/llnl-hpc-2026.Rmd`](../../llnl-hpc-2026.Rmd) and on the
[WarpX tutorials website](https://blast-warpx.github.io/warpx-tutorials/).

# Usage

After choosing a setup option below, run `bash startup.sh` from this directory
before starting the exercises. See [Prepare the exercise files](#prepare-the-exercise-files).

## Registered participants: use your Slack link

Registered participants will receive a link in Slack that opens the AWS-hosted
JupyterLab session directly. Open it; no local installation is needed.
In a terminal, go to `~/warpx-tutorials/episodes/files/llnl-hpc-2026`,
then follow **Prepare the exercise files** below.

## Alternative A: run Docker yourself

The image includes WarpX, ImpactX, the notebooks and analysis tools.

To run the image yourself:

```bash
docker pull ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
docker run --rm -p 127.0.0.1:3000:3000 ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
```

Open <http://localhost:3000/lab>, launch a **Terminal**, and go to:

```bash
cd ~/warpx-tutorials/episodes/files/llnl-hpc-2026
```

The source materials are already there. Run `bash startup.sh` before the
exercises; no download is needed. See the
[tutorial container README](../../../containers/tutorial/README.md) for
GPU access and other image details.

## Alternative B: running locally with Conda

Use this instead of the Docker image if you want to run the tutorial on
your own machine outside of the provided container, e.g. on a laptop with
no Docker available, or on a cluster where you'd rather use your own Conda
installation.

### Download the complete tutorial folder

Keep `llnl-hpc-2026/`, `laser-wakefield/`, and `beam-transport/` together
under `episodes/files/`. The startup script copies the shared example
materials into the workshop folders.

With Git installed, download the tutorial folder using sparse checkout.
This preserves its directory structure without downloading unnecessary materials.

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/BLAST-WarpX/warpx-tutorials.git
cd warpx-tutorials
git sparse-checkout set episodes/files/llnl-hpc-2026 \
  episodes/files/laser-wakefield episodes/files/beam-transport
cd episodes/files/llnl-hpc-2026
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

## Prepare the exercise files

Before starting any exercise, run from `llnl-hpc-2026/`:

```bash
bash startup.sh
```

The script copies the wakefield notebook, input, driver, and helper from
`../laser-wakefield/` into `htu/lwfa_warpx/`, and the beam-transport notebook
and helper from `../beam-transport/` into `htu/beamline_impactx/`.
It does not copy figures or simulation results.

**If a destination already exists, the script does nothing to it.** Rerunning
fills in missing files only; it never refreshes existing copies or overwrites
your edits. Missing source files produce an error before copying begins.
The script also works when invoked by its path from another directory.

## Tutorial 1: two-stream instability warm-up

```bash
cd two_stream_instability
python run_two_stream_instability.py
jupyter lab two_stream_instability_plots.ipynb
cd ..
```

This runs a cheap 1D WarpX simulation of two counter-streaming electron
populations, a classic kinetic instability that saturates in seconds on a
laptop. The simulation writes its diagnostics under `two_stream_instability/diags/`.

## Two independent examples

Run WarpX in a terminal, then open `htu/lwfa_warpx/wakefield.ipynb` to visualize the wake.
Open `htu/beamline_impactx/htu_transport.ipynb` to run
the nominal HTU beam and explore off-energy transport with ImpactX.

The [lesson](../../llnl-hpc-2026.Rmd) explains both examples. Each notebook uses its helper module
in its own folder. The ImpactX notebook runs the simulation directly; no generated script is needed.
