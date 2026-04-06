---
title: 'A Laser-Driven Ion Accelerator'
teaching: 15
exercises: 25
---

:::::::::::::::::::::::::::::::::::::: questions 

How does an intense laser pulse accelerate ions from a thin solid target?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Set up, run, and visualize a 2D Target Normal Sheath Acceleration (TNSA) simulation with WarpX.
Understand the role of key laser and target parameters in determining the maximum ion energy.

::::::::::::::::::::::::::::::::::::::::::::::::

## Introduction

**Target Normal Sheath Acceleration (TNSA)** is one of the most studied mechanisms for 
laser-driven ion acceleration.
The physics goes roughly as follows:

1. An **intense, short-pulse laser** ($I > 10^{18}$ W/cm$^2$) hits a thin solid-density target.
2. The laser heats electrons at the front surface to relativistic energies.
3. These **hot electrons** traverse the target and escape from the rear surface, 
   setting up a strong electrostatic **sheath field** ($\sim$ TV/m) at the target-vacuum interface.
4. This sheath field ionizes and accelerates ions (typically protons from surface contaminants) 
   to multi-MeV energies in the direction normal to the target surface.

In this episode, we simulate this process in 2D using a laser pulse impinging on a 
composite target: a boron slab (the main target) followed by a thin hydrogen contaminant layer 
from which protons are accelerated.

::: caution

This simulation is significantly more demanding than the instability examples.
Depending on the resolution you choose, you may need a GPU or a parallel run 
to complete it in a reasonable time.

:::

## Setup

Make sure to download the [input file](./files/input_2d_tnsa.txt).

Whenever you need to prepare an input file, [this is where you want to go](https://warpx.readthedocs.io/en/latest/usage/parameters.html).

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at the input file


``` output
####################
### MY CONSTANTS ###
####################
my_constants.micro = 1e-6
my_constants.femto = 1e-15
my_constants.eV = q_e 
# LASER 
my_constants.FWHM_I = ...*femto # [s]
my_constants.laser_tpeak = 2*FWHM_I # [s]
my_constants.laser_waist = ...*micro # [m] 
my_constants.laser_wavelength = ...*micro # [m]
my_constants.a0 = ... # [-]
# PLASMA 
my_constants.n_c = epsilon0 * m_e * (2*pi*clight)**2 /(laser_wavelength*q_e)**2 # [m^-3] 
my_constants.ne0 = ...*n_c # [m^-3] 
my_constants.Te0 = ...*eV # [J]
my_constants.zmin_targ = 2*FWHM_I*clight # [m]
my_constants.thick_targ = ...*micro # [m]
my_constants.thick_cont = ...*micro # [m]
# BOX
my_constants.Lz = 4*FWHM_I*clight
my_constants.Lx = 10*laser_waist
my_constants.nz = ...
my_constants.nx = ...
my_constants.dx = Lx / nx 
my_constants.dz = Lz / nz
# TIME
my_constants.cfl = ...
my_constants.T = 2*Lz/clight
my_constants.dt = cfl*dx/(sqrt(2)*clight)
my_constants.nt = floor(T/dt) 

##########################
### GENERAL PARAMETERS ###
##########################
stop_time = T
amr.n_cell = nx nz 
amr.max_level = 0
geometry.dims = 2
geometry.prob_lo = -0.5*Lx  0
geometry.prob_hi =  0.5*Lx  Lz

##########################
### BOUNDARY CONDITION ###
##########################
boundary.field_lo = pml pml
boundary.field_hi = pml pml
boundary.particle_lo = absorbing absorbing absorbing
boundary.particle_hi = absorbing absorbing absorbing

###############
### NUMERICS ###
################
algo.particle_shape = 3
algo.maxwell_solver = yee
algo.particle_pusher = boris
algo.current_deposition = esirkepov 
warpx.cfl = cfl
warpx.use_filter = 1

#################
### PARTICLES ###
#################
particles.species_names = ion_targ ele_targ ion_cont ele_cont

ion_targ.species_type = boron
ion_targ.injection_style = NRandomPerCell
ion_targ.num_particles_per_cell = 20
ion_targ.momentum_distribution_type = maxwell_boltzmann
ion_targ.theta = Te0 / (10*m_p*clight**2)
ion_targ.zmin = zmin_targ
ion_targ.zmax = zmin_targ + thick_targ 
ion_targ.profile = constant
ion_targ.density = ne0/5

ele_targ.species_type = electron
ele_targ.injection_style = NRandomPerCell
ele_targ.num_particles_per_cell = 40 
ele_targ.momentum_distribution_type = maxwell_boltzmann
ele_targ.theta = Te0 / (m_e*clight**2)
ele_targ.zmin = zmin_targ
ele_targ.zmax = zmin_targ + thick_targ 
ele_targ.profile = constant
ele_targ.density = ne0

ion_cont.species_type = proton
ion_cont.injection_style = NRandomPerCell
ion_cont.num_particles_per_cell = 100
ion_cont.momentum_distribution_type = maxwell_boltzmann
ion_cont.theta = Te0 / (m_p*clight**2)
ion_cont.zmin = zmin_targ + thick_targ 
ion_cont.zmax =  zmin_targ + thick_targ + thick_cont
ion_cont.profile = constant
ion_cont.density = 5*n_c

ele_cont.species_type = electron
ele_cont.injection_style = NRandomPerCell
ele_cont.num_particles_per_cell = 50
ele_cont.momentum_distribution_type = maxwell_boltzmann
ele_cont.theta = Te0 / (m_e*clight**2)
ele_cont.zmin = zmin_targ + thick_targ 
ele_cont.zmax = zmin_targ + thick_targ + thick_cont
ele_cont.profile = constant
ele_cont.density = 5*n_c

#############
### LASER ###
#############
lasers.names        = laser1
laser1.position     = 0 0 dz
laser1.direction    = 0. 0. 1.         
laser1.polarization = 1. 0. 0.         
laser1.a0           = a0 
laser1.wavelength   = laser_wavelength 
laser1.profile      = Gaussian
laser1.profile_waist = laser_waist 
laser1.profile_duration = FWHM_I/1.17741
laser1.profile_t_peak = laser_tpeak 
laser1.profile_focal_distance = zmin_targ

################
#### DIAGNOSTICS
################
# FULL
diagnostics.diags_names = fields particles
fields.diag_type = Full
fields.fields_to_plot = Ex Ez rho_ele_targ rho_ion_targ rho_ele_cont rho_ion_cont 
fields.format = openpmd
fields.intervals = floor(nt/200) 
fields.openpmd_backend = bp
fields.write_species = 0
particles.diag_type = Full
particles.format = openpmd
particles.openpmd_backend = bp
particles.species = ele_targ ion_cont 
particles.fields_to_plot = none
particles.intervals = floor(nt/200) 

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
This is the most complex input of the tutorial, and the parameter choices will determine 
whether you get meaningful physics out of the simulation.

::::::::::::::::::::::::::::::::::::: challenge

## Choose the laser parameters

| Parameter | Symbol | Description |
|-----------|--------|-------------|
| `FWHM_I` | $\tau_{\mathrm{FWHM}}$ | Pulse duration (FWHM of intensity) $[\mathrm{s}]$ |
| `laser_waist` | $w_0$ | Laser spot size (beam waist) $[\mathrm{m}]$ |
| `laser_wavelength` | $\lambda$ | Laser wavelength $[\mathrm{m}]$ |
| `a0` | $a_0$ | Normalized vector potential (dimensionless laser amplitude) |

Some hints:

- A Ti:Sapphire laser has $\lambda \approx 0.8\,\mu\mathrm{m}$. This is the most common choice.
- Typical ultrashort pulses have durations $\tau_{\mathrm{FWHM}} \sim 20$--$100$ fs.
- The normalized vector potential $a_0$ controls the laser intensity: $I \approx 1.37 \times 10^{18}\, (a_0 / \lambda[\mu\mathrm{m}])^2$ W/cm$^2$. For TNSA, $a_0 \gtrsim 1$ (i.e. relativistic intensity) is required. Values of $a_0 \sim 1$--$10$ are typical.
- The laser waist $w_0$ is typically a few micrometers ($\sim 2$--$10\,\mu\mathrm{m}$).

:::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: challenge

## Choose the target parameters

| Parameter | Symbol | Description |
|-----------|--------|-------------|
| `ne0` | $n_e / n_c$ | Electron density of the main target, in units of the critical density $n_c$ |
| `Te0` | $T_e$ | Initial electron temperature $[\mathrm{eV}]$ |
| `thick_targ` | | Thickness of the main (boron) target $[\mathrm{m}]$ |
| `thick_cont` | | Thickness of the hydrogen contaminant layer $[\mathrm{m}]$ |

Some hints:

- Solid-density targets have $n_e \sim 100$--$500\, n_c$, where $n_c$ is the critical density for the chosen wavelength. However, running at full solid density is very expensive. You may want to start with a reduced density $\sim 10$--$50\, n_c$ to keep the cost manageable.
- The initial temperature is typically a few eV (room temperature ionized material), but the exact value does not matter much since the laser will heat the electrons far beyond this.
- The target thickness is usually a few micrometers ($\sim 1$--$10\,\mu\mathrm{m}$). Thinner targets lead to higher maximum proton energies (up to a point).
- The contaminant layer is very thin ($\sim 0.1$--$1\,\mu\mathrm{m}$).

:::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: challenge

## Choose the numerical parameters

| Parameter | Description |
|-----------|-------------|
| `nz` | Number of grid cells in the laser propagation direction |
| `nx` | Number of grid cells in the transverse direction |
| `cfl` | CFL number (must be $< 1/\sqrt{2}$ in 2D) |

Some hints:

- You need to resolve the laser wavelength: $\Delta z \lesssim \lambda / 20$ is a common rule of thumb, with $\lambda / 30$ or finer being safer.
- The transverse resolution can be somewhat coarser than the longitudinal, but should still resolve the plasma skin depth $c/\omega_{pe}$ for the target density.
- A CFL of $\sim 0.7$ (i.e. $1/\sqrt{2}$) is the maximum allowed.
- For a first test, use a coarser grid to make sure the simulation runs correctly, and then refine.

:::::::::::::::::::::::::::::::::::::::::::::::::


### Notable details

*  The target consists of **four species**: boron ions and electrons for the main target (`ion_targ`, `ele_targ`), 
and protons and electrons for the contaminant layer (`ion_cont`, `ele_cont`).
The boron is initialized with charge state $Z=5$, so the electron density is $5\times$ the ion density.

*  The laser is injected from the $z_{\mathrm{min}}$ boundary using the built-in Gaussian laser profile, 
with the focus placed at the front surface of the target.

*  **PML** (Perfectly Matched Layer) boundary conditions are used for the fields to absorb outgoing electromagnetic waves, 
and **absorbing** boundary conditions are used for particles leaving the box.

*  The `current_deposition = esirkepov` option is used to ensure charge conservation, 
which is essential for a simulation involving dense plasma and strong fields.

*  The diagnostics write out both **field data** (`Ex`, `Ez`, charge densities of each species) 
and **particle data** (target electrons and contaminant protons).


## Run 

Create a new folder and copy the input file there, after filling in your chosen parameters.

::: caution

This simulation is more expensive than the instability examples.
Depending on your resolution, running in serial may take a very long time.
Consider running in parallel or on a GPU.

:::

::: spoiler

## Let's run in serial

```bash
warpx.2d input_2d_tnsa.txt
```
:::

::: spoiler

## Let's run in parallel

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 <path/to/your/build/bin/warpx.2d> input_2d_tnsa.txt
```
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

1. **Electric field maps**: plot `Ex` and `Ez` at several time snapshots to see the laser pulse entering the box, interacting with the target, and the sheath field forming at the rear surface.

2. **Charge density maps**: plot the charge densities (`rho_ele_targ`, `rho_ion_cont`, etc.) to see the electron heating, expansion, and proton acceleration.

3. **Proton energy spectrum**: from the contaminant proton data (`ion_cont`), compute the kinetic energy of each proton and build a histogram. The maximum proton energy is the key figure of merit in TNSA experiments.

4. **Field energy vs time**: use `FieldEnergy.txt` to track how the electromagnetic energy in the box evolves as the laser enters, interacts, and exits.


::::::::::::::::::::::::::::::::::::: challenge

## Questions for analysis

1. What is the maximum proton energy you observe? How does it compare to the theoretical TNSA scaling with laser intensity $a_0$?

2. How does the sheath field $E_z$ at the target rear surface evolve in time? Can you identify the moment when the sheath field is strongest?

3. Try running the simulation with a thinner (or thicker) target. How does the maximum proton energy change? Why?

4. What happens if you increase $a_0$ (i.e., increase the laser intensity)? How does the proton energy spectrum change?

5. Look at the electron density behind the target. Can you see the hot electron population that escapes and creates the sheath?

6. What role does the contaminant layer play? What would happen if you made it thicker, or changed the contaminant species to something heavier (e.g., carbon)?

:::::::::::::::: solution

These are open-ended questions meant to guide your exploration.
A classical TNSA scaling predicts the maximum proton energy $E_{\max} \propto a_0$ (or $\propto \sqrt{I}$),
though the exact scaling depends on target thickness, density, and pulse duration.
Thinner targets generally yield higher maximum energies because the hot electrons recirculate more efficiently.

:::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::::


### Gallery

![Laser interacting with a solid target in a TNSA simulation and accelerating a layer of contaminants.](https://gist.github.com/user-attachments/assets/ecc369e1-58c0-4885-ae29-ac6d51998092){alt="2D map showing the laser electric field interacting with the solid-density target and accelerated protons"}

![Phase space of the accelerated protons at the end of the simulation.](https://gist.github.com/user-attachments/assets/7e3bd05f-e9ab-40c9-b663-78db7576d283){alt="2D map showing the phase space of the accelerated protons at the end of the simulation"}


<iframe src="https://drive.google.com/file/d/19DrJUt7RDr14YqU83sfdWNP7zQk3-bEf/preview" width="100%" height="500" allow="autoplay"></iframe>


::::::::::::::::::::::::::::::::::::: keypoints 

 💡 TNSA accelerates ions via a strong electrostatic sheath field created by hot electrons 
 escaping the rear surface of a laser-irradiated thin target.

 🔬 Key parameters controlling the maximum ion energy are the laser intensity ($a_0$), 
 the target thickness, and the target density.

 ⚙️ Charge-conserving current deposition (`esirkepov`) and proper boundary conditions (PML, absorbing) 
 are essential for this type of simulation.

 ⚡ This is a computationally expensive simulation -- be prepared to iterate on resolution and 
 target density to find a balance between physical fidelity and computational cost.

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python.

::::::::::::::::::::::::::::::::::::::::::::::::
