---
title: 'Set Up a Simulation from Scratch'
teaching: 20
exercises: 15
---

:::::::::::::::::::::::::::::::::::::: questions 

How do you go from "I want to simulate X" to a working WarpX input file?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Navigate the WarpX repository to find relevant examples.
Adapt an existing input file to your physics problem.
Iterate on simulation parameters to observe the expected physics.

::::::::::::::::::::::::::::::::::::::::::::::::

## Introduction

Most simulations don't start from a blank page.
In practice, a physicist starting a new simulation will look for the closest existing example,
adapt it to their problem, run it, look at the results, and iterate.
This episode walks through that process step by step,
using the **two-stream instability** as the target physics.

Rather than handing you a ready-made input file,
we will start from a different example altogether -- a uniform plasma --
and modify it until we observe the instability.
Along the way, we'll make mistakes, debug them, and learn from the process.

::: callout
This episode is complementary to the [two-stream instability tutorial](a-two-stream-instability.Rmd),
which gives you a polished input file with exercises on parameter selection.
Here we focus on the **workflow**: how to find, adapt, and iterate.
:::


## Step 1: What do we want to simulate?

Before touching any code, clarify the physics.
We want to simulate the **two-stream instability**:
two populations of electrons streaming through each other with opposite drift velocities,
in a periodic box with a neutralizing background.
The expected result is exponential growth of electrostatic perturbations
and the formation of vortex structures ("cat eyes") in phase space.

What do we need?

- A periodic box with a uniform plasma (electrons)
- Two counter-streaming populations with a relative drift velocity
- Diagnostics to look at the phase space $(z, u_z)$

## Step 2: Browse the WarpX examples

WarpX ships with many examples in its [GitHub repository][warpx-github],
organized under [`Examples/Physics_applications/`](https://github.com/BLAST-WarpX/warpx/tree/development/Examples/Physics_applications).
The [documentation][warpx-readthedocs] also has a 
[gallery of examples](https://warpx.readthedocs.io/en/latest/usage/examples.html)
with descriptions, input files, and analysis scripts.

::::::::::::::::::::::::::::::::::::: challenge

## Find a starting point

Browse the examples in the [WarpX repository](https://github.com/BLAST-WarpX/warpx/tree/development/Examples/Physics_applications)
or the [documentation gallery](https://warpx.readthedocs.io/en/latest/usage/examples.html).
Which example is the closest to what we want?

:::::::::::::::: solution

The [`uniform_plasma`](https://github.com/BLAST-WarpX/warpx/tree/development/Examples/Physics_applications/uniform_plasma) 
example is a good starting point: 
it already has a periodic box with a uniform electron population, 
a Gaussian (thermal) momentum distribution, 
and basic diagnostics. 
We "just" need to add a drift velocity and duplicate the species.

:::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::

## Step 3: Start from the uniform plasma example

Here is the 2D uniform plasma input file, rendered directly from the 
[WarpX repository](https://github.com/BLAST-WarpX/warpx/blob/development/Examples/Physics_applications/uniform_plasma/inputs_test_2d_uniform_plasma):


``` output
#################################
####### GENERAL PARAMETERS ######
#################################
max_step = 10
amr.n_cell =  128 128
amr.max_grid_size = 64
amr.blocking_factor = 32
amr.max_level = 0
geometry.dims = 2
geometry.prob_lo = -20.e-6   -20.e-6    # physical domain
geometry.prob_hi =  20.e-6    20.e-6

#################################
####### Boundary condition ######
#################################
boundary.field_lo = periodic periodic
boundary.field_hi = periodic periodic

#################################
############ NUMERICS ###########
#################################
warpx.serialize_initial_conditions = 1
warpx.verbose = 1
warpx.cfl = 1.0
warpx.use_filter = 0

# Order of particle shape factors
algo.particle_shape = 1

#################################
############ PLASMA #############
#################################
particles.species_names = electrons

electrons.charge = -q_e
electrons.mass = m_e
electrons.injection_style = "NUniformPerCell"
electrons.num_particles_per_cell_each_dim = 2 2
electrons.profile = constant
electrons.density = 1.e25  # number of electrons per m^3
electrons.momentum_distribution_type = "gaussian"
electrons.ux_th  = 0.01 # uth the std of the (unitless) momentum
electrons.uy_th  = 0.01 # uth the std of the (unitless) momentum
electrons.uz_th  = 0.01 # uth the std of the (unitless) momentum

# Diagnostics
diagnostics.diags_names = diag1
diag1.intervals = 10
diag1.diag_type = Full
```

This simulates a single electron species in a box with thermal fluctuations. No drift, no instability.


## Step 4: Add a drift velocity

To create two counter-streaming beams, we need to:

1. **Duplicate the species**: create `ele1` and `ele2` with opposite drift velocities
2. **Add a bulk drift** to each species along one direction

Here are the key modifications.
Replace the single `electrons` species block with two species:

```
particles.species_names = ele1 ele2

ele1.species_type = electron
ele1.injection_style = "NUniformPerCell"
ele1.num_particles_per_cell_each_dim = 2 2
ele1.profile = constant
ele1.density = 1.e25
ele1.momentum_distribution_type = "gaussian"
ele1.ux_th = 0.01
ele1.uy_th = 0.01
ele1.uz_th = 0.01
ele1.uz_m = 0.1

ele2.species_type = electron
ele2.injection_style = "NUniformPerCell"
ele2.num_particles_per_cell_each_dim = 2 2
ele2.profile = constant
ele2.density = 1.e25
ele2.momentum_distribution_type = "gaussian"
ele2.ux_th = 0.01
ele2.uy_th = 0.01
ele2.uz_th = 0.01
ele2.uz_m = -0.1
```

The parameter `uz_m` sets the mean of the Gaussian distribution for the $z$-momentum (in units of $m c$),
so `+0.1` and `-0.1` give two beams drifting in opposite directions at $\beta_0 \approx 0.1$.

::::::::::::::::::::::::::::::::::::: challenge

## What parameters do we need to check?

Before running, take a look at the rest of the input file.
Are there any parameters that might need adjusting for the two-stream case?

:::::::::::::::: solution

A few things to keep in mind:

- **`max_step = 10`**: way too few timesteps to see anything happen
- **Resolution**: 128 cells may or may not be enough depending on the plasma parameters
- **Diagnostics**: the uniform plasma example uses the default `plotfile` format, but we'll want to switch to [openPMD][openpmd] so we can use [openPMD-viewer][openpmd-viewer] to grab particle data easily

We'll deal with these one at a time.

:::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::


### Define `nt` as a constant

A practical tip: define the number of timesteps as a `my_constants` variable 
at the top of the input file, 
so you can change it in one place and have everything else follow:

```
my_constants.nt = 10

max_step = nt
```

This is especially handy because you'll also want the diagnostic interval 
to scale with the total number of steps (see below).

### Switch diagnostics to openPMD

The uniform plasma example writes diagnostics in WarpX's native `plotfile` format.
This works, but it's much more convenient to use the [openPMD][openpmd] standard instead,
because then you can use the [openPMD-viewer][openpmd-viewer] Python library 
to grab particle and field data with a couple of lines of code.

Replace the diagnostics block with:

```
diagnostics.diags_names = diag1
diag1.intervals = floor(nt/2)
diag1.diag_type = Full
diag1.fields_to_plot = none
diag1.format = openpmd
```

A few things to note:

- `diag1.intervals = floor(nt/2)` writes 2 snapshots regardless of how many timesteps you run -- 
  so when you increase `nt` later, the diagnostic output adjusts automatically.
- `diag1.fields_to_plot = none` skips the field data, since we only care about the particle phase space for now.
- `diag1.format = openpmd` enables the use of [openPMD-viewer][openpmd-viewer] for analysis.


## Step 5: Run -- and nothing happens

Let's run the simulation as-is with `max_step = 10`, just to make sure the code doesn't crash.

```bash
warpx.2d my_inputs.txt
```

The simulation runs in a few seconds. 
Now open a Jupyter notebook and plot the phase space $(z, u_z)$
using [openPMD-viewer][openpmd-viewer]:

```python
from openpmd_viewer import OpenPMDTimeSeries
import matplotlib.pyplot as plt

ts = OpenPMDTimeSeries("./diags/diag1/")
z, uz = ts.get_particle(["z", "uz"], species="ele1", iteration=ts.iterations[-1])
plt.scatter(z, uz, s=0.1, alpha=0.3)
z, uz = ts.get_particle(["z", "uz"], species="ele2", iteration=ts.iterations[-1])
plt.scatter(z, uz, s=0.1, alpha=0.3)
plt.xlabel("z [m]")
plt.ylabel("uz [m_e c]")
plt.show()
```

The phase space looks like... two flat lines. Nothing is happening. 
That's probably because we only ran 10 timesteps, 
and the instability needs time to grow from noise. 

::: callout
**This is normal.**
Not seeing what you expect on the first try is part of the process.
The important thing is to understand *why* and to iterate.
:::


## Step 6: Iterate

This is where the real work (and the learning) begins.
Each iteration teaches you something about the physics and the numerics.

### Increase the number of timesteps

If you defined `my_constants.nt` as suggested earlier, just increase it: 
try `my_constants.nt = 100` or `200` or more.
Both `max_step` and the diagnostic interval will update automatically.

### Reduce the temperature

The instability is driven by the relative drift between the two beams.
If the temperature is too high, the thermal spread dominates over the drift
and the instability won't develop.
Try setting the thermal spread to zero:

```
ele1.ux_th = 0.0
ele1.uy_th = 0.0
ele1.uz_th = 0.0
```

This is a "cold beam" limit. In practice, some finite temperature is physical,
but starting cold makes it easier to see the instability develop cleanly.

### Switch to 1D

The two-stream instability is inherently a 1D phenomenon (along the drift direction).
Running in 2D or 3D adds transverse dimensions that increase the computational cost
without changing the essential physics.
Change to 1D:

```
geometry.dims = 1
amr.n_cell = 256
geometry.prob_lo = -20.e-6
geometry.prob_hi = 20.e-6
```

### Increase resolution and particles per cell

With only 2 particles per cell, the noise level is high. Try increasing to 100 or more.
Also make sure the grid is fine enough to resolve the plasma skin depth $c/\omega_{pe}$.

::::::::::::::::::::::::::::::::::::: challenge

## Put it all together

Combine all the modifications above into a single input file.
Run the simulation and plot the phase space at multiple time snapshots.
Do you see the instability developing?

:::::::::::::::: solution

You should see the two initially-flat streams begin to develop a sinusoidal
modulation, followed by the formation of vortex ("cat eye") structures
as particles get trapped in the electrostatic potential wells.
The number of timesteps needed depends on the drift velocity and density;
you may need to adjust `max_step` until you see saturation.

:::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::


## Step 7: Visualize the result

Once the instability is developing, you can produce a sequence of phase-space plots.
Loop over the diagnostic snapshots:

```python
from openpmd_viewer import OpenPMDTimeSeries
import matplotlib.pyplot as plt

ts = OpenPMDTimeSeries("./diags/diag1/")
for i in ts.iterations:
    z, uz = ts.get_particle(["z", "uz"], iteration=i)
    plt.figure()
    plt.scatter(z, uz, s=0.1, alpha=0.3)
    plt.xlabel("z [m]")
    plt.ylabel("uz [m_e c]")
    plt.title(f"iteration {i}")
    plt.savefig(f"phase_space_{i:06d}.png", dpi=150)
    plt.close()
```

From these frames you can make a video using `ffmpeg`:

```bash
ffmpeg -framerate 10 -pattern_type glob -i 'phase_space_*.png' \
       -c:v libx264 -pix_fmt yuv420p phase_space.mp4
```


## What's next?

Now that you've seen the full workflow -- from browsing examples to iterating on parameters to producing visualizations -- 
you can try the [polished two-stream instability tutorial](a-two-stream-instability.Rmd),
which provides a carefully prepared input file with exercises on choosing physical and numerical parameters,
reduced diagnostics for tracking the growth rate, and analysis notebooks.

The key takeaway is the **process**:

1. Clarify the physics you want to simulate
2. Find the closest existing example
3. Modify it step by step
4. Run, visualize, and iterate
5. Don't be discouraged when things don't work on the first try
6. Ask yourself: **is what I'm seeing physics, numerics, or both?** 
   This is one of the hardest questions in computational physics...

:::::::::::::::::::::::::::::::::::::::::: spoiler

### A note on timescales

The characteristic timescale of the two-stream instability is the inverse plasma frequency $\omega_{pe}^{-1}$,
where $\omega_{pe} = \sqrt{n_0 e^2 / (m_e \epsilon_0)}$.
The instability growth rate is of order $\omega_{pe}$,
so the simulation needs to cover many plasma periods for the instability to develop and saturate.
This is why increasing `nt` is the first thing to try when nothing seems to be happening.

::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::: keypoints 

The [WarpX examples](https://github.com/BLAST-WarpX/warpx/tree/development/Examples/Physics_applications) and the [documentation gallery](https://warpx.readthedocs.io/en/latest/usage/examples.html) are the best starting points for a new simulation.

Setting up a simulation is an iterative process: run, visualize, understand what's wrong, fix it, repeat.

When the simulation doesn't show the expected physics, check the basics first: enough timesteps? resolved scales? adequate particles per cell? temperature not too high?

The [documentation][warpx-readthedocs] parameter reference is your constant companion for understanding and modifying input files.

::::::::::::::::::::::::::::::::::::::::::::::::
