---
title: 'A Weibel Instability'
teaching: 10
exercises: 20
---

:::::::::::::::::::::::::::::::::::::: questions 

How does a momentum anisotropy in a plasma generate magnetic fields from scratch?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Set up, run, and visualize a 2D Weibel instability simulation with WarpX.
Observe the spontaneous generation of magnetic fields from counter-streaming electron beams.

::::::::::::::::::::::::::::::::::::::::::::::::

## Introduction

The **Weibel instability** (also known as the current filamentation instability) 
is a fundamental electromagnetic instability that arises when there is an anisotropy in the 
momentum distribution of a plasma.
Unlike the two-stream instability, which generates electrostatic waves, 
the Weibel instability generates **magnetic fields**.

The physical mechanism is as follows: when two electron populations stream past each other, 
any small magnetic perturbation will deflect the electrons, 
causing them to bunch into current filaments.
These current filaments in turn amplify the magnetic field that caused the bunching, 
leading to exponential growth until the fields are strong enough to isotropize the distribution.

This instability plays a key role in astrophysical plasmas (e.g. collisionless shocks in gamma-ray bursts)
and in laser-plasma interactions.

In this episode, we simulate it in 2D with two counter-streaming electron populations and periodic boundaries.

## Setup

Make sure to download the [input file](./files/input_2d_weibel_instability.txt).

Whenever you need to prepare an input file, [this is where you want to go](https://warpx.readthedocs.io/en/latest/usage/parameters.html).

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at the input file


``` output
####################
### MY CONSTANTS ###
####################
# PLASMAS
my_constants.n0 = ... # [m^-3]
my_constants.T0 = ...*q_e # [J]
my_constants.beta0 = ... # [-]
my_constants.omega_pe = sqrt(n0*q_e**2/(m_e*epsilon0)) # [1/s]
my_constants.skin_depth = clight / omega_pe # [m]
# BOX
my_constants.Lx = ...*skin_depth
my_constants.nx = ...
my_constants.dx = Lx/nx
# TIME
my_constants.cfl = ...
my_constants.T = .../omega_pe
my_constants.dt = cfl*dx/(sqrt(2)*clight)
my_constants.nt = floor(T/dt) 

##########################
### GENERAL PARAMETERS ###
##########################
stop_time = T
amr.n_cell = nx nx nx
amr.max_level = 0
geometry.dims = 2
geometry.prob_lo = -0.5*Lx -0.5*Lx  -0.5*Lx
geometry.prob_hi =  0.5*Lx  0.5*Lx   0.5*Lx

##########################
### BOUNDARY CONDITION ###
##########################
boundary.field_lo = periodic periodic periodic 
boundary.field_hi = periodic periodic periodic 
boundary.particle_lo = periodic periodic periodic
boundary.particle_hi = periodic periodic periodic

################
### NUMERICS ###
################
warpx.cfl = cfl
algo.maxwell_solver = yee
algo.particle_shape = 3
algo.particle_pusher = boris
warpx.use_filter = 1 

#################
### PARTICLES ###
#################
particles.species_names = ele1 ele2 

ele1.species_type = electron
ele1.injection_style = NRandomPerCell
ele1.num_particles_per_cell = 80
ele1.profile = constant
ele1.density = n0
ele1.momentum_distribution_type = maxwell_boltzmann
ele1.theta_distribution_type = constant
ele1.theta = T0 / (m_e * clight**2) 
ele1.beta_distribution_type = parser
ele1.beta_function(x,y,z) = beta0
ele1.bulk_vel_dir = +y

ele2.species_type = electron
ele2.injection_style = NRandomPerCell
ele2.num_particles_per_cell = 80
ele2.profile = constant
ele2.density = n0
ele2.momentum_distribution_type = maxwell_boltzmann
ele2.theta_distribution_type = constant
ele2.theta = T0 / (m_e * clight**2) 
ele2.beta_distribution_type = constant
ele2.beta = beta0
ele2.bulk_vel_dir = -y

###################
### DIAGNOSTICS ###
###################
# FULL
diagnostics.diags_names =  fields
fields.intervals = floor(nt/200)
fields.diag_type = Full
fields.write_species = 0
fields.fields_to_plot = Bx Bz
fields.format = openpmd
fields.openpmd_backend = bp
fields.dump_last_timestep = 1
# REDUCED
warpx.reduced_diags_names = FieldEnergy FieldMaximum
FieldEnergy.type = FieldEnergy
FieldEnergy.intervals = 1 
FieldMaximum.type = FieldMaximum
FieldMaximum.intervals = 1 
```
::::::::::::::::::::::::::::::::::::::::::::::::::


### Choosing the parameters

You will notice that some parameters in the input file are set to `...` (ellipsis).
These are left for **you** to choose!
Designing a good simulation requires making physical and numerical choices --  
this is part of the exercise.

::::::::::::::::::::::::::::::::::::: challenge

## Choose the physical parameters

The physical parameters you need to set are:

| Parameter | Symbol | Description |
|-----------|--------|-------------|
| `n0` | $n_0$ | Electron density of each beam $[\mathrm{m^{-3}}]$ |
| `T0` | $T_0$ | Thermal temperature of each beam $[\mathrm{eV}]$ |
| `beta0` | $\beta_0 = v_d/c$ | Drift velocity of each beam normalized to $c$ |

Some hints:

- The Weibel instability requires an anisotropy in the momentum space. Here, the anisotropy comes from the relative drift between the two beams. A mildly relativistic drift (e.g. $\beta_0 \sim 0.1$--$0.5$) will produce a clear instability.
- The temperature should be small enough that the thermal spread does not wash out the anisotropy. As a rule of thumb, $v_d \gg v_{\mathrm{th}}$ where $v_{\mathrm{th}} = \sqrt{T_0/m_e}$.
- A density in the range $10^{20}$--$10^{24}$ m$^{-3}$ works well; what matters is that lengths and times are measured in skin depths and inverse plasma frequencies.

:::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: challenge

## Choose the numerical parameters

The numerical parameters you need to set are:

| Parameter | Description |
|-----------|-------------|
| `Lx` | Box length (in each direction), expressed in units of the skin depth $c/\omega_{pe}$ |
| `nx` | Number of grid cells per direction |
| `cfl` | CFL number (must be $< 1/\sqrt{2}$ in 2D for the Yee solver) |
| `T`  | Total simulation time, expressed in units of $\omega_{pe}^{-1}$ |

Some hints:

- The Weibel filaments have a characteristic size of a few skin depths. The box should be large enough to contain several filaments: $\sim 10$--$30$ skin depths per direction is a good starting point.
- You need to resolve the skin depth on the grid: $\Delta x \lesssim c/\omega_{pe}$.
- In 2D, the Yee solver CFL condition is $\mathrm{cfl} < 1/\sqrt{2} \approx 0.7$. Note how the input file already accounts for this in the `dt` formula.
- The Weibel instability grows slower than the two-stream instability. You will need a longer simulation: $\sim 100$--$500\,\omega_{pe}^{-1}$.

:::::::::::::::::::::::::::::::::::::::::::::::::


### Notable details

*  The geometry is **2D** (`geometry.dims = 2`) with **periodic** boundary conditions in all directions.

*  Two electron species (`ele1`, `ele2`) are initialized with equal density and temperature 
but with opposite drift velocities along the $y$-axis.

*  The diagnostics record the magnetic field components `Bx` and `Bz` at regular intervals,  
allowing you to visualize the growth of filamentary magnetic structures.

*  **Reduced diagnostics** (`FieldEnergy`, `FieldMaximum`) track the total field energy and the maximum field amplitude at every timestep.
Since the system starts with essentially zero magnetic field 
(only numerical noise), you can directly observe the exponential growth of the Weibel instability in these quantities.


## Run 

Create a new folder and copy the input file there, after filling in your chosen parameters.

::: spoiler

## Let's run in serial

```bash
warpx.2d input_2d_weibel_instability.txt
```

Easy! 🕺
:::

If you want to speed things up, you can run in parallel:

::: spoiler

## Let's run in parallel

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 <path/to/your/build/bin/warpx.2d> input_2d_weibel_instability.txt
```
:::

::: testimonial

Depending on your choice of resolution and box size, this simulation may take 
from a few minutes to much longer.
If it takes too long, try reducing `nx` or `T`.

:::

You should see a standard output flashing out a lot of info.  
At the end, you should find in your folder:

  * a subfolder called `diags`: here is where the code stored the diagnostics  
  * a file called `warpx_used_inputs`: this is a summary of the inputs that were used to run the simulation  
  * files `FieldEnergy.txt` and `FieldMaximum.txt` with the reduced diagnostics

If that's the case, yey! 💯  

If the run went wrong, you may find a `Backtrace.0.0` file which can be useful for debugging purposes. 
Let me know if the code fails in any way! 


## Visualize

### With Python 🐍

Now that we have the results, we can analyze them using Python.  
We will use the [openPMD-viewer][openpmd-viewer] library to grab the data that the simulation produced in [openPMD][openpmd] format.
Here you can find [a few tutorials on how to use the viewer](https://openpmd-viewer.readthedocs.io/en/latest/tutorials/tutorials.html).
If you feel nerdy and/or you need to deal with the data in parallel workflows, you can use the [openPMD-api][openpmd-api].

Here are some things you can visualize:

1. **Magnetic field maps**: use `get_field('B', 'z')` (or `'x'`) to plot 2D maps of the magnetic field at different times. You should see the formation and growth of filamentary structures.

2. **Field energy vs time**: load `FieldEnergy.txt` and plot the total field energy on a semi-log scale as a function of time. You should see a clear exponential growth phase followed by saturation.

3. **Filament spacing**: from the 2D field maps, estimate the characteristic spacing of the current filaments and compare it to the skin depth $c/\omega_{pe}$.

### With a Jupyter notebook 📓

The notebook includes a magnetic field map ($B_x$) and the evolution of the electric and magnetic field energy on a semi-log scale.

:::::::::::::::::::::::::::::::::::::::::: spoiler

## Let's take a look at the Jupyter notebook

<iframe src="https://nbviewer.org/github/BLAST-WarpX/warpx-tutorials/blob/main/episodes/files/analysis_2d_weibel.ipynb" 
           width="100%" height="800" style="border:none;">
     </iframe>
::::::::::::::::::::::::::::::::::::::::::::::::::

You can [download the notebook](./files/analysis_2d_weibel.ipynb) and try it yourself.
Remember to either run the notebook from the simulation directory or change the corresponding path in the notebook.


::::::::::::::::::::::::::::::::::::: challenge

## Questions for analysis

1. How does the magnetic field energy grow in time? Can you identify a linear (exponential) growth phase on a semi-log plot? Estimate the growth rate $\gamma$ from the slope.

2. What is the characteristic size of the filaments at saturation? How does it compare to the plasma skin depth?

3. How does the growth rate depend on $\beta_0$? Try at least two different drift velocities and compare the field energy time histories.

4. What happens if you increase the temperature $T_0$ while keeping $\beta_0$ fixed? At what point does the instability shut off?

5. Compare this simulation to the [two-stream instability episode](a-two-stream-instability.Rmd). What are the key differences in the fields that are generated (electrostatic vs electromagnetic)?

:::::::::::::::: solution

These are open-ended questions meant to guide your exploration.
The Weibel growth rate in the cold limit scales as $\gamma \sim \omega_{pe}\,\beta_0$, 
and the characteristic filament size is of order the skin depth.
Finite temperature tends to stabilize short-wavelength modes.

:::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::


### Gallery

![Magnetic field structures induced by the Weibel instability.](https://gist.github.com/user-attachments/assets/06318207-831b-4aa3-99bc-e4ca267fc8bc)


![Evolution of the energy stored in the electric and magnetic fields.](https://gist.github.com/user-attachments/assets/216dd776-ab5f-4fa0-a2b0-e5aecdaa0ae4)


<iframe src="https://drive.google.com/file/d/1qWE7rHhq-UadaUbXK9gwWAPEeqd9e__3/preview" width="100%" height="500" allow="autoplay"></iframe>

::::::::::::::::::::::::::::::::::::: keypoints 

 💡 The Weibel instability generates **magnetic fields** from a momentum anisotropy 
 -- unlike the two-stream instability, which generates electrostatic fields.

 🔬 The instability produces current filaments with a characteristic size of order the plasma skin depth $c/\omega_{pe}$.

 📊 Reduced diagnostics (`FieldEnergy`, `FieldMaximum`) are an efficient way to monitor the instability growth without storing large field dumps.

 ⚡ Choosing parameters wisely ($v_d \gg v_{\mathrm{th}}$, sufficient resolution and box size) is essential for observing the instability clearly.

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python.

::::::::::::::::::::::::::::::::::::::::::::::::
