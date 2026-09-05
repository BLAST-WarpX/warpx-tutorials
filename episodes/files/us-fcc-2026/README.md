# US-FCC 2026 WarpX and ImpactX tutorials

This directory contains the files for three exercises combining WarpX,
ImpactX, Xsuite, and MAD-X:

1. a single FCC-ee bunch crossing with WarpX;
2. a linear-optics comparison with ImpactX, Xsuite, and MAD-X; and
3. a multi-turn Xsuite simulation coupled to WarpX collisions.

The complete lesson and explanations are in
[`episodes/us-fcc-2026.Rmd`](../../us-fcc-2026.Rmd) and on the
[WarpX tutorials website](https://blast-warpx.github.io/warpx-tutorials/).

## Download the complete tutorial folder

Keeping the complete `us-fcc-2026/` directory is easier than downloading the
files individually because each exercise expects its scripts, inputs, and
notebooks to remain together.

The simplest option is to download the
[repository ZIP archive](https://github.com/BLAST-WarpX/warpx-tutorials/archive/refs/heads/main.zip),
unpack it, and open:

```text
warpx-tutorials-main/episodes/files/us-fcc-2026/
```

Git users can download only this directory with sparse checkout:

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/BLAST-WarpX/warpx-tutorials.git
cd warpx-tutorials
git sparse-checkout set episodes/files/us-fcc-2026
cd episodes/files/us-fcc-2026
```

## Create the Conda environment

Run these commands from this directory:

```bash
conda env create --file environment_setup.yml
conda activate usfcc26-warpx-tutorial
```

If the environment already exists, update it instead:

```bash
conda env update --name usfcc26-warpx-tutorial \
  --file environment_setup.yml --prune
conda activate usfcc26-warpx-tutorial
```

The environment installs WarpX and ImpactX from Conda Forge, together with
the Python packages needed by the simulations and notebooks. These exercises
have been tested with WarpX 26.09 and ImpactX 26.09. To inspect the installed
versions, run:

```bash
conda list warpx
conda list impactx
```

## Tutorial 1: one WarpX bunch crossing

```bash
cd tutorial_1
warpx.3d tutorial_1_input.txt
jupyter lab tutorial_1_plots.ipynb
cd ..
```

The simulation writes its diagnostics under `tutorial_1/diags/`. Run the
notebook after the WarpX command finishes.

## Tutorial 2: linear-optics comparison

```bash
cd tutorial_2
python fcc_impactx.py
jupyter lab tutorial_2_plots.ipynb
cd ..
```

The Python script runs the ImpactX envelope calculation. The notebook then
compares the result with Xsuite and MAD-X using the common `fccee_z.madx`
lattice. The first notebook run creates `fccee_p_ring.json`; later runs reuse
this cached Xsuite line.

## Tutorial 3: multi-turn Xsuite--WarpX coupling

First, a quick one-collision smoke test:

```bash
cd tutorial_3
python exec_tutorial_3.py --macroparticles 1000 --iterations 1
```

The standard comparison uses an arc-only reference and a classical WarpX
collision run:

```bash
python exec_tutorial_3.py \
  --no-warpx --macroparticles 10000 --iterations 256
python exec_tutorial_3.py \
  --macroparticles 10000 --iterations 20
```

Beamstrahlung can be enabled in a separate run:

```bash
python exec_tutorial_3.py \
  --macroparticles 10000 --iterations 20 --beamstrahlung
```

Analyze whichever runs are available with:

```bash
jupyter lab tutorial_3_plots.ipynb
```

Use `python exec_tutorial_3.py --help` to see the device, launcher, output,
and diagnostics options. The default coupling is intentionally single-rank.

## Finish

Deactivate the environment when finished:

```bash
conda deactivate
```

To remove it completely:

```bash
conda env remove --name usfcc26-warpx-tutorial
```
