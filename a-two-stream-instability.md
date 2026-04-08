---
title: 'A Two-stream Instability'
teaching: 10
exercises: 20
---

:::::::::::::::::::::::::::::::::::::: questions 

🤼 How do two counter-streaming electron beams become unstable?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Set up, run, and visualize a 1D two-stream instability simulation with WarpX.
Understand how the choice of physical parameters affects the instability growth.

::::::::::::::::::::::::::::::::::::::::::::::::

## Introduction

The **two-stream instability** is one of the most fundamental kinetic instabilities in plasma physics.
When two populations of charged particles (here, electrons) stream through each other 
with a relative drift velocity, small perturbations in the charge density can grow exponentially.
The free energy stored in the relative drift is converted into electrostatic wave energy 
until the beams thermalize and the instability saturates.

This example uses a 1D periodic box with two counter-streaming electron populations 
on a neutralizing ion background. 

## Setup

Make sure to download the [input file](./files/input_1d_two_stream_instability.txt). 

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
my_constants.v_te = sqrt(T0 / m_e) # [m/s]
my_constants.beta0 = ... # [-] 
my_constants.omega_pe = sqrt(n0*q_e**2/(m_e*epsilon0)) # [1/s]
# BOX
my_constants.Lx = ...*clight/omega_pe
my_constants.nx = ...
my_constants.dx = Lx/nx
# TIME
my_constants.cfl = ...
my_constants.T = .../omega_pe
my_constants.dt = cfl * dx / clight
my_constants.nt = floor(T/dt) 

##########################
### GENERAL PARAMETERS ###
##########################
stop_time = T
amr.n_cell = nx nx nx
amr.max_level = 0
geometry.dims = 1
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
ele1.num_particles_per_cell = 200
ele1.profile = constant
ele1.density = n0
ele1.momentum_distribution_type = maxwell_boltzmann
ele1.theta_distribution_type = constant
ele1.theta = T0 / (m_e * clight**2) 
ele1.beta_distribution_type = parser
ele1.beta_function(x,y,z) = beta0
ele1.bulk_vel_dir = +z

ele2.species_type = electron
ele2.injection_style = NRandomPerCell
ele2.num_particles_per_cell = 200
ele2.profile = constant
ele2.density = n0
ele2.momentum_distribution_type = maxwell_boltzmann
ele2.theta_distribution_type = constant
ele2.theta = T0 / (m_e * clight**2) 
ele2.beta_distribution_type = constant
ele2.beta = beta0
ele2.bulk_vel_dir = -z

###################
### DIAGNOSTICS ###
###################
# FULL
diagnostics.diags_names =  particles
particles.intervals = floor(nt/200)
particles.diag_type = Full
particles.species = ele1 ele2 
particles.fields_to_plot = none
particles.format = openpmd
particles.openpmd_backend = bp
particles.dump_last_timestep = 1
particles.ele1.variables = w z uz
particles.ele2.variables = w z uz

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
These are left for you to choose 🗳️! 
Picking sensible physical and numerical parameters is an important part of setting up a simulation.
Here is some guidance.

::::::::::::::::::::::::::::::::::::: challenge

## Choose the physical parameters

The physical parameters you need to set are:

| Parameter | Symbol | Description |
| --        | -----   | ---------   |
| `n0` | $n_0$ | Electron density of each beam $[\mathrm{m^{-3}}]$ |
| `T0` | $T_0$ | Thermal temperature of each beam $[\mathrm{eV}]$ |
| `beta0` | $\beta_0 = v_d/c$ | Drift velocity of each beam normalized to $c$ |

::::::::::::::::::: solution

## Hints

- A typical plasma prototype is an ionized gas. What is the number density of an ionized gas at standard conditions? Think of a fluorescent lamp, a tokamak, or the solar wind.
- The temperature should be low enough that the thermal spread does not wash out the instability: the drift velocity should be larger than the thermal velocity, i.e. $v_d \gg v_{\mathrm{th}}$.
- The drift velocity $\beta_0$ controls how fast the instability grows. Non-relativistic drifts ($\beta_0 \ll 1$) are a good starting point.

::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::: instructor

An ideal gas at standard temperature and pressure ($T = 300\,\mathrm{K}$, $p = 1\,\mathrm{atm}$) has a number density
$n = p/(k_B T) \approx 2.5 \times 10^{25}\,\mathrm{m^{-3}}$.
Typical plasma densities span many orders of magnitude depending on the degree of ionization and the environment:

| Example | Density $[\mathrm{m^{-3}}]$ |
|---------|-----------------------------|
| Solar wind | $\sim 10^{6}$--$10^{7}$ |
| Fluorescent lamp | $\sim 10^{17}$--$10^{18}$ |
| Tokamak core | $\sim 10^{19}$--$10^{20}$ |

Any value in a sensible range will work for this exercise.

:::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: challenge

## Choose the numerical parameters

The numerical parameters you need to set are:

| Parameter | Description |
| ---       | ----------- |
| `Lx` | Box length, expressed in units of $c/\omega_{pe}$ |
| `nx` | Number of grid cells |
| `cfl` | CFL number (must be $< 1$) |
| `T`  | Total simulation time, expressed in units of $\omega_{pe}^{-1}$ |

::::::::::::::::::: solution

## Hints

- The most unstable wavelength is $\lambda \sim 2\pi\,\beta_0\,(c/\omega_{pe})$. The box must be large enough to fit several of these wavelengths.
- The grid must resolve the shortest relevant scale, i.e. $\Delta x \lesssim c/\omega_{pe}$. So `nx` should be at least comparable to `Lx` (in units of $c/\omega_{pe}$).
- The CFL should be $\lesssim 1$ for stability of the Yee solver.
- The simulation must run long enough for the instability to develop and saturate: $\sim 50$--$200\,\omega_{pe}^{-1}$ is a typical range.

::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::

### Notable details

*  Two electron species (`ele1`, `ele2`) are initialized with equal density `n0` and temperature `T0`, 
but with opposite drift velocities $\pm \beta_0 c$ along the $z$-axis.

*  There is **no ion background** in this input. 
Because we do not ask WarpX to solve Poisson's equation at initialization, 
the fields start at zero and the uniform charge density of the electrons never sources a DC field, 
effectively acting as if a neutralizing background were present.

*  The diagnostics write out particle data (`z`, `uz`) for both species, 
which lets you construct the phase space $(z, u_z)$ at each snapshot.

*  **Reduced diagnostics** (`FieldEnergy`, `FieldMaximum`) record the total field energy and the maximum field value at every timestep,
so you can track the exponential growth of the instability without post-processing the full data.


## Run 

Create a new folder and copy the input file there. Then fill it with your chosen parameters.
This is a 1D simulation, so it should run very quickly even in serial.

::: spoiler

## Let's run

```bash
warpx.1d input_1d_two_stream_instability.txt
```

Just like that! 💃
:::

You should see a standard output flashing out a lot of info.  
At the end, you should find in your folder:

  * a subfolder `diags/particles/` with the full particle diagnostics  
  * files `FieldEnergy.txt` and `FieldMaximum.txt` with the reduced diagnostics, inside `diags/reducedfiles/`  
  * a file called `warpx_used_inputs`: a summary of the inputs that were used to run the simulation

If that's the case, yey! 💯  

If the run went wrong, you may find a `Backtrace.0.0` file which can be useful for debugging purposes. 


## Visualize

### With Python 🐍

Now that we have the results, we can analyze them using Python.  
We will use the [openPMD-viewer][openpmd-viewer] library to grab the data that the simulation produced in [openPMD][openpmd] format.
Here you can find [a few tutorials on how to use the viewer](https://openpmd-viewer.readthedocs.io/en/latest/tutorials/tutorials.html).
If you feel nerdy and/or you need to deal with the data in parallel workflows, you can use the [openPMD-api][openpmd-api].

Here are some things you can visualize:

1. **Phase space** $(z, u_z)$: plot the particle positions and momenta at several time snapshots to see how the beams evolve from smooth streams into characteristic "cat-eye" vortices.

2. **Field energy vs time**: load `FieldEnergy.txt` and plot the total electrostatic energy as a function of time on a semi-log scale. You should see an exponential growth phase followed by saturation.

3. **Growth rate**: from the slope of $\ln(E_{\mathrm{field}})$ during the linear phase, extract the growth rate and compare it to the theoretical prediction $\gamma \sim \omega_{pe}$.

### With a Jupyter notebook 📓

The notebook includes a phase-space plot $(z, u_z)$ and the evolution of the electric and magnetic field energy on a semi-log scale.

:::::::::::::::::::::::::::::::::::::::::: spoiler

## Let's take a look at the Jupyter notebook

<iframe src="https://nbviewer.org/github/BLAST-WarpX/warpx-tutorials/blob/main/episodes/files/analysis_1d_twostream.ipynb" 
           width="100%" height="800" style="border:none;">
     </iframe>
::::::::::::::::::::::::::::::::::::::::::::::::::

You can [download the notebook](./files/analysis_1d_twostream.ipynb) and try it yourself.
Remember to either run the notebook from the simulation directory or change the corresponding path in the notebook.


::::::::::::::::::::::::::::::::::::: challenge

## Questions for analysis

1. Describe what you observe in the phase space $(z, u_z)$ at different times and in the field energy evolution. Can you identify distinct stages?

2. How does the growth rate of the field energy depend on the drift velocity $\beta_0$? Try running with two different values and compare.

3. What happens to the phase space after saturation? Can you identify particle trapping in the electrostatic potential wells?

4. If you increase the temperature (decrease the ratio $v_d / v_{\mathrm{th}}$), does the instability still develop? At what point is it suppressed?

5. How does the number of particles per cell affect the noise level and the onset of the instability?

:::::::::::::::: solution

These are open-ended questions meant to guide your exploration.
The key insight is that the instability requires $v_d > v_{\mathrm{th}}$; 
when thermal effects dominate, Landau damping stabilizes the modes.

:::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::: spoiler

### Gallery

![Phase space of the two-stream instability at saturation.](https://gist.github.com/user-attachments/assets/0160a10a-9a08-443c-84a3-610a9a5eeb73){alt="Phase space plot showing the two counter-streaming electron beams forming vortex structures at saturation"}

![Evolution of the field energy.](https://gist.github.com/user-attachments/assets/907e36d9-a91e-4939-899a-22b78519b81a){alt="Evolution of the field energy."}

<iframe src="https://drive.google.com/file/d/17_CKWVxKYjx0XPaUb2o1Z4cfkPAkPecB/preview" width="100%" height="500" allow="autoplay"></iframe>

::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::: keypoints 

 💡 The two-stream instability converts the kinetic energy of counter-streaming beams into electrostatic wave energy.

 🔬 The instability growth rate depends on the ratio of drift velocity to thermal velocity: $v_d / v_{\mathrm{th}} \gg 1$ is needed for the instability to develop.

 📊 Reduced diagnostics (`FieldEnergy`, `FieldMaximum`) let you track the instability growth in real time without post-processing full datasets.

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python.

::::::::::::::::::::::::::::::::::::::::::::::::
