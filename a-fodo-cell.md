---
title: 'A FODO Cell'
teaching: 10
exercises: 20
---

:::::::::::::::::::::::::::::::::::::: questions 

How to simulate a particle beam travelling through a FODO cell 🧲🛝🧲?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Learn how to setup, run, and visualize a particle 
beam simulation through a FODO (Focusing-Defocusing) cell with WarpX 🎢

::::::::::::::::::::::::::::::::::::::::::::::::

## Setup

In this example we will simulate a particle beam travelling through a FODO cell.
A **FODO cell** is a periodic focusing structure used in particle accelerators, 
consisting of alternating **F**ocusing (F) and **D**efocusing (D) quadrupole magnets, with **O** (drift) sections in between.
The FODO cell is one of the most fundamental building blocks in accelerator physics, 
providing transverse focusing to keep particle beams confined as they travel through the accelerator.
The alternating focusing and defocusing quadrupoles create a net focusing effect in both transverse planes, 
allowing the beam to be transported over long distances while maintaining its size.

### WarpX for Beam Dynamics

WarpX is a Particle-in-Cell (PIC) code that can track particles embedded in external fields. 
Two important features are:

* **Space charge effects**: 
You can turn space charge effects on or off using the appropriate input parameters. 
When enabled, WarpX solves the electromagnetic (or electrostatic) fields self-consistently from the particle distributions, 
allowing you to study how the beam's own fields affect its dynamics.

* **Arbitrary external fields**: 
WarpX allows you to define arbitrary external electromagnetic fields, 
either analytically or by loading them from files. 
This makes it possible to model complex accelerator elements like quadrupoles, dipoles, and other magnets.

::: caution

**WarpX is not necessarily the best tool for all beam dynamics simulations**. 
If space charge effects are negligible and you're primarily interested in linear beam optics, 
there are more specialized and computationally efficient tools available, such as ImpactX.

:::

### WarpX vs ImpactX

**ImpactX** is another code from the same ecosystem, the Beam, Plasma & Accelerator Simulation Toolkit ([**BLAST**][blast]), 
designed for beam dynamics. See the [ImpactX documentation][impactx] and [repository][impactx-github].
Key differences:

* **WarpX** — **t-based** (time-based): solves Maxwell/Poisson on a grid, advances particles and fields in time. Best for:
  - Strong space charge, wakefields, full EM solutions
  - Plasma–beam and other collective effects
  - When time evolution of fields matters

* **ImpactX** — **z-based** (position-based): tracks particles along the beamline through lattice elements. Best for:
  - Weak or approximated space charge
  - Optics design, linear dynamics, envelope tracking
  - Fast runs when detailed field evolution is not needed

For this tutorial we use WarpX to set up a FODO simulation with optional space charge.

::: callout
## Equivalent ImpactX Example

If you're interested in seeing how a similar FODO cell simulation can be set up using ImpactX, 
check out the [ImpactX FODO cell example with 2D space charge using envelope tracking][impactx-fodo-example]. 
This example demonstrates the envelope tracking approach.
:::


Whenever you need to prepare an input file, [this is where you want to go](https://warpx.readthedocs.io/en/latest/usage/parameters.html).

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at the input file


``` output
####################
### MY CONSTANTS ###
####################
# BEAM
my_constants.mass          = m_p                              # kg
my_constants.current       = 0.5                              # A
my_constants.energy        = 6.7e6 * q_e                      # J 
my_constants.velocity      = sqrt(2 * energy / mass)          # m/s 
my_constants.gamma         = energy / (mass * clight**2) + 1. # - 
my_constants.beta          = velocity / clight                # - 
my_constants.beta_x        = 0.737881                         # m 
my_constants.beta_y        = 0.737881                         # m 
my_constants.beta_t        = 0.25                             # m
my_constants.alpha_x       = +2.4685083                       # -
my_constants.alpha_y       = -2.4685083                       # -
my_constants.alpha_t       = 0.                               # -
my_constants.gamma_x       = (1+alpha_x**2)/beta_x            # m^-1 
my_constants.gamma_y       = (1+alpha_y**2)/beta_y            # m^-1
my_constants.gamma_t       = (1+alpha_t**2)/beta_t            # m^-1
my_constants.emitt_x       = 1.0e-6                           # m
my_constants.emitt_y       = 1.0e-6                           # m
my_constants.emitt_t       = 1.0e-6                           # m
my_constants.sigma_x       = sqrt(emitt_x * beta_x)           # m
my_constants.sigma_y       = sqrt(emitt_y * beta_y)           # m
my_constants.sigma_z       = sqrt(emitt_t * beta_t)           # m
my_constants.sigma_ux      = beta * sqrt(emitt_x * gamma_x)   # -
my_constants.sigma_uy      = beta * sqrt(emitt_y * gamma_y)   # -
my_constants.sigma_uz      = beta * sqrt(emitt_t * gamma_t)   # -
my_constants.sigma_t       = sigma_z / velocity               # s
my_constants.charge        = current *sigma_t                 # C 
# BOX
my_constants.Lx   = 20*sigma_x  # m
my_constants.Ly   = 20*sigma_y  # m
my_constants.zmin = -20*sigma_z # m
my_constants.zmax = 0
# LATTICE
my_constants.L_drift1      =  7.44e-2 # m 
my_constants.L_drift2      = 14.88e-2 # m
my_constants.L_drift3      =  7.44e-2 # m
my_constants.quad_gradient = 38.64    # T/m 
my_constants.L_quad        = 6.10e-2  # m
# TIME
my_constants.T = (L_drift1+L_drift2+L_drift3+2*L_quad)/velocity # s
my_constants.dt = sigma_t/4                                     # s
my_constants.nt = floor(T/dt)                                   # -

##########################
### GENERAL PARAMETERS ###
##########################
stop_time                = T
geometry.dims            = 3
geometry.prob_lo         = -0.5*Lx -0.5*Ly zmin 
geometry.prob_hi         = +0.5*Lx +0.5*Ly zmax
amr.n_cell               = 64 64 128
amr.max_level            = 0
warpx.limit_verbose_step = 1
warpx.const_dt           = dt
warpx.do_electrostatic   = labframe
warpx.poisson_solver     = fft
warpx.do_moving_window   = 1
warpx.moving_window_dir  = z
warpx.moving_window_v    = beta  # in units of c
algo.particle_shape      = 3
boundary.field_lo        = open open open 
boundary.field_hi        = open open open 

#################
### PARTICLES ###
#################
particles.species_names         = beam
beam.species_type               = proton 
beam.injection_style            = gaussian_beam 
beam.x_rms                      = sigma_x
beam.y_rms                      = sigma_y
beam.z_rms                      = sigma_z 
beam.x_m                        = 0
beam.y_m                        = 0
beam.z_m                        = 0.5*zmin
beam.npart                      = 1e3
beam.q_tot                      = charge
beam.momentum_distribution_type = gaussian
beam.uz_m                       = beta*gamma  
beam.uy_m                       = 0.0
beam.ux_m                       = 0.0
beam.ux_th                      = sigma_ux
beam.uy_th                      = sigma_uy
beam.uz_th                      = sigma_uz

###############
### LATTICE ###
###############
lattice.elements = drift1 quad1 drift2 quad2 drift3
drift1.type = drift
drift1.ds   = L_drift1
quad1.type  = quad
quad1.ds    = L_quad
quad1.dBdx  = -quad_gradient
drift2.type = drift
drift2.ds   = L_drift2
quad2.type  = quad
quad2.ds    = L_quad
quad2.dBdx  = quad_gradient
drift3.type = drift
drift3.ds   = L_drift3

###################
### DIAGNOSTICS ###
###################
warpx.reduced_diags_names = beam_stats
beam_stats.type = BeamRelevant
beam_stats.species = beam
beam_stats.intervals = 1

diagnostics.diags_names = particles_in 
particles_in.intervals = floor(nt/20)
particles_in.diag_type = Full
particles_in.species = beam
particles_in.fields_to_plot = none
particles_in.format = openpmd
particles_in.openpmd_backend = bp
particles_in.dump_last_timestep = 1
```
::::::::::::::::::::::::::::::::::::::::::::::::::


Some notable details:

* **Space charge effects**: 
Space charge is computed self-consistently by solving the Poisson equation at each timestep using the updated charge density from the particle distribution. 
This allows the beam's own fields to affect its dynamics.

* **Turning off space charge**: To turn off space charge effects, set `algo.maxwell_solver = none` and comment out the following inputs:
  ```bash
  # warpx.const_dt           = dt
  # warpx.do_electrostatic   = labframe
  # warpx.poisson_solver     = fft
  # boundary.field_lo        = open open open 
  # boundary.field_hi        = open open open 
  ```

* **External fields**: To initialize an arbitrary external field (such as the quadrupole magnets in a FODO cell), 
check out the [external fields documentation](https://warpx.readthedocs.io/en/latest/usage/parameters.html#external-fields) for details on how to define fields analytically or load them from files.

## Run 

First things first. 
Create a new folder where you copy the [input file](./files/inputs_3d_fodo_cell.txt). 
The simulation should be small enough that you can run it in serial with the Conda installation of WarpX.

::: spoiler

## Let's run in serial

```bash
warpx.3d inputs_3d_fodo_cell.txt
```

Just like that! 💃
Note that with Conda's WarpX you can run this anywhere in your filesystem (provided that you copied there the input of course)
because WarpX's executables are in your `$PATH`.
:::

If you want to make the simulation faster and/or bigger, then you should run with the parallel version of WarpX.
The optimal setup to run the simulation depends on your hardware. 
This is an example that should work on many common laptops, even though it might not be ideal.


::: spoiler

## Let's run in parallel

This is just one way of doing it!

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 <path/to/your/build/bin/warpx.3d> inputs_3d_fodo_cell.txt 
```
:::

::: testimonial

With the default parameters, it may take a while on a laptop.
If you have access to a GPU, you can experience the speed-up yourself.
My experiments: 35 seconds on an NVIDIA A100 GPU, more than 1 hour on 4 cores of my 12th Gen Intel(R) Core(TM) i9-12900H.

:::


## Visualize

### With Python 🐍
Now that we have the results, we can analyze them using Python.  
We will use the [openPMD-viewer][openpmd-viewer] library to grab the data that the simulation produced in `openPMD` format. 
Here you can find [a few tutorials on how to use the viewer](https://openpmd-viewer.readthedocs.io/en/latest/tutorials/tutorials.html).
If you feel nerdy and/or you need to deal with the data in parallel workflows, you can use the [openPMD-api][openpmd-api].

As an example for the FODO cell simulation, we have developed a simple Jupyter notebook where we retrieve 
the beam variables and analyze the beam dynamics through the cell.

Here is a video of the beam travelling through the FODO cell:

<video src="https://gist.github.com/user-attachments/assets/59ad6448-a679-4d2a-b0c3-dd4ccf48662b" controls width="100%">
Your browser does not support the video tag.
</video>

:::::::::::::::::::::::::::::::::::::::::: spoiler

## Let's take a look at the Jupyter notebook

Nbviewer does not load this notebook; you can [view it on GitHub](https://github.com/BLAST-WarpX/warpx-tutorials/blob/main/episodes/files/analysis_3d_fodo_cell.ipynb) (GitHub renders it in the browser) or [download the notebook](./files/analysis_3d_fodo_cell.ipynb) and try it yourself.
Remember to either run the notebook from the simulation directory or change the corresponding path in the notebook. 
If the simulation is too expensive,

::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: keypoints 
 🎯 Particle tracking follows individual particles, while envelope tracking follows the beam envelope - particle tracking is more detailed but computationally expensive.

 🔬 A FODO cell is a periodic focusing structure with alternating focusing and defocusing quadrupole magnets.

 ⚡ WarpX allows you to turn space charge effects on/off and define arbitrary external fields.

 🚀 WarpX is a full PIC code best suited for strong space charge effects and complex electromagnetic interactions. 
 For cases with negligible space charge, **ImpactX** may be a more efficient choice.

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python.

::::::::::::::::::::::::::::::::::::::::::::::::
