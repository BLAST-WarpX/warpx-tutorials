# LLNL HPC Innovation Center 2026: HTU-inspired WarpX and ImpactX tutorial

This directory contains the files for a three-part accelerator-physics
tutorial combining WarpX and ImpactX:

1. `two_stream_instability/`: a quick 1D two-stream instability warm-up with
   WarpX, used to get everyone to a working simulate-then-analyze pipeline
   before the heavier exercises below;
2. `htu/lwfa_warpx/`: a small, visual 3D wakefield demonstration; and
3. `htu/beamline_impactx/`: independent synthetic beams transported through
   HTU magnets to show energy sensitivity and possible losses/model breakdown.

The WarpX and ImpactX exercises are separate. Coupling is an optional extension.

The complete lesson and explanations are in
[`episodes/llnl-hpc-2026.Rmd`](../../llnl-hpc-2026.Rmd) and on the
[WarpX tutorials website](https://blast-warpx.github.io/warpx-tutorials/).

# Usage

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
cd ~/warpx-tutorials/episodes/files/llnl-hpc-2026
```

The files described below are already there -- no download needed. See the
[tutorial container README](../../../containers/tutorial/README.md) for
GPU access and other image details.

## Alternative B: running locally with Conda

Use this instead of the Docker image if you want to run the tutorial on
your own machine outside of the provided container, e.g. on a laptop with
no Docker available, or on a cluster where you'd rather use your own Conda
installation.

### Download the complete tutorial folder

Keeping the complete `llnl-hpc-2026/` directory together is easier than
downloading the files individually, since each exercise expects its
scripts, inputs, and notebooks to remain alongside each other.

With Git installed, download the tutorial folder using sparse checkout.
This preserves its directory structure without downloading the other lessons'
contents; files in parent directories are also included. No packaging script
is needed.

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/BLAST-WarpX/warpx-tutorials.git
cd warpx-tutorials
git sparse-checkout set episodes/files/llnl-hpc-2026
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

## Tutorial 1: two-stream instability warm-up

```bash
cd two_stream_instability
python run_two_stream_instability.py
jupyter lab two_stream_instability_plots.ipynb
cd ..
```

This runs a cheap 1D WarpX simulation of two counter-streaming electron
populations, a classic kinetic instability that saturates in seconds on a
laptop. Unlike the two exercises below, all its physical and numerical
parameters are fixed rather than chosen by you -- the point here is just to
confirm the simulate-then-analyze pipeline (WarpX, Python, Jupyter) works
before moving on to the heavier LWFA and beamline stages. The simulation
writes its diagnostics under `two_stream_instability/diags/`.

## Two independent examples

Open [wakefield.ipynb](htu/wakefield.ipynb) to run WarpX and visualize the wake.
Open [htu_transport.ipynb](htu/htu_transport.ipynb) to compare independent
100 MeV and 20 MeV synthetic beams in fixed HTU magnets with ImpactX.

See the [short instructions](htu/README.md) for both examples and the
[optional coupling section](htu/README.md#optional-coupling) for the converter.
