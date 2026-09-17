# LLNL HPC Innovation Center 2026: HTU-inspired WarpX and ImpactX tutorial

This directory contains the files for a three-part accelerator-physics
tutorial combining WarpX and ImpactX:

1. `two_stream_instability/`: a quick 1D two-stream instability warm-up with
   WarpX, used to get everyone to a working simulate-then-analyze pipeline
   before the heavier exercises below;
2. `htu/lwfa_warpx/`: a laser-wakefield accelerated (LWFA) electron bunch,
   self-injected at a plasma density downramp, simulated with WarpX; and
3. `htu/beamline_impactx/`: that same bunch propagated through the real
   downstream beamline of LBNL BELLA Center's Hundred Terawatt Undulator
   (HTU) -- a permanent-magnet quadrupole triplet, a bunch-compression
   chicane, an electromagnet quadrupole triplet, a spectrometer, and four
   undulator FODO segments -- simulated with ImpactX.

The complete lesson and explanations are in
[`episodes/llnl-hpc-2026.Rmd`](../../../llnl-hpc-2026.Rmd) and on the
[WarpX tutorials website](https://blast-warpx.github.io/warpx-tutorials/).

The LWFA and ImpactX stages use raw AMReX/ImpactX-style input rather than
PICMI: the WarpX stage is a plain input file loaded from Python with
`pywarpx.warpx.load_inputs_file(...)`, and the ImpactX stage builds its
lattice directly from `impactx.elements`. The two-stream warm-up uses the
same raw-input-from-Python pattern as the LWFA stage.

## Option A: the tutorial Docker image (recommended)

The tutorial is run live from a pre-built Docker image that already has
WarpX, ImpactX, and every Python package this lesson needs, served as a
browser-based JupyterLab session. This is how the tutorial is presented at
the LLNL HPC Innovation Center session, typically from an AWS instance
someone else has already started for you -- in that case, skip straight to
opening the URL you were given and go to
[Tutorial 1](#tutorial-1-two-stream-instability-warm-up) below.

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
[tutorial container README](../../../../containers/tutorial/README.md) for
GPU access and other image details.

## Option B: running locally with Conda

Use this instead of the Docker image if you want to run the tutorial on
your own machine outside of the provided container, e.g. on a laptop with
no Docker available, or on a cluster where you'd rather use your own Conda
installation.

### Download the complete tutorial folder

Keeping the complete `llnl-hpc-2026/` directory together is easier than
downloading the files individually, since each exercise expects its
scripts, inputs, and notebooks to remain alongside each other.

The simplest option is to download the
[repository ZIP archive](https://github.com/BLAST-WarpX/warpx-tutorials/archive/refs/heads/main.zip),
unpack it, and open:

```text
warpx-tutorials-main/episodes/files/llnl-hpc-2026/
```

Git users can download only this directory with sparse checkout:

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

## Tutorial 2: LWFA stage with WarpX

```bash
cd htu/lwfa_warpx
python run_lwfa_warpx.py
cd ../..
```

This runs a 3D WarpX simulation of a short laser pulse driving a plasma
wake. A density downramp partway through the plasma triggers self-injection
of a quasi-monoenergetic electron bunch, which is then accelerated over the
following lower-density plateau. The parameters here are tutorial-scale
(coarse mesh, higher plasma density than the real HTU target for a shorter
dephasing length) so the run completes in a few minutes on a laptop, while
still reaching the same qualitative regime as the real beamline: a
self-injected bunch of several tens of MeV. The simulation writes its
diagnostics under `htu/lwfa_warpx/diags/`.

## Tutorial 3: HTU beamline with ImpactX

WarpX and ImpactX each initialize their own AMReX/MPI state and cannot run
in the same Python process, so the handoff between them goes through a
small converter script and an intermediate file.

```bash
cd htu/beamline_impactx
python warpx_to_beamline_impactx.py ../lwfa_warpx/diags/diag1 warpx_bunch.npz
python run_beamline_impactx.py warpx_bunch.npz
cd ../..
```

`warpx_to_beamline_impactx.py` reads the WarpX output, isolates the
accelerated bunch from the cold background plasma with an energy cut, and
transforms its coordinates from WarpX's lab-frame convention to the
reference-relative convention ImpactX expects. `run_beamline_impactx.py`
then tracks that bunch through `htu_lattice.py`, a trimmed definition of the
full real HTU beamline (PMQ triplet, chicane, EMQ triplet, spectrometer, and
four undulator FODO segments), with `BeamMonitor` diagnostics at the same
locations as HTU's real screens. Steering-magnet kickers are present in the
lattice but held at zero current, since there is no control-system setting
to plug in for a generic tutorial. ImpactX's reduced beam diagnostics are
written under `htu/beamline_impactx/diags/`.

## Analyze the LWFA and beamline results

Open `htu_plots.ipynb` in JupyterLab, from the `htu` directory:

```bash
cd htu
jupyter lab htu_plots.ipynb
```
