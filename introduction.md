---
title: 'Using WarpX, a general purpose particle-in-cell code'  
teaching: 30
exercises: 30
---

:::::::::::::::::::::::::::::::::::::: questions 

- 🤌 What is WarpX? 
- 🧮 How can I install and run WarpX?
- 🕵️ How can I analyze the simulation results?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

- 💻 Install WarpX on your local machine with [Conda](https://docs.conda.io/en/latest/)
- 🏃 Run a fusion-relevant example on your local machine: protons in a magnetic mirror!
- 👀 Visualize the results with `python` and `Paraview`

::::::::::::::::::::::::::::::::::::::::::::::::

## WarpX: an open-source high-performance particle-in-cell code 

[WarpX](https://github.com/BLAST-WarpX/warpx) is a general purpose Particle-In-Cell (PIC) code.  
If you are not familiar with the PIC method, here is a picture that condenses the core idea:  

If you want to know more, here are a few references:

*  The two bibles on PIC 📚
     *  [C. K. Birdsall and A. B. Langdon. Plasma Physics Via Computer Simulation.](https://doi.org/10.1201/9781315275048)  
     *  [R. W. Hockney and J. W. Eastwood. Computer simulation using particles.](https://doi.org/10.1201/9780367806934)  
*  An old review written by one of the pioneers: [John M. Dawson, Particle simulation of plasmas, Rev. Mod. Phys. 55, 403](https://doi.org/10.1103/RevModPhys.55.403)  


In this tutorial we will go through the basics of WarpX: installation, running a simple example and visualizing the results. 
Along the way, we will point to the documentation for references.


::: callout
Everything you need to know to use WarpX is in the [documentation](https://warpx.readthedocs.io/en/latest/index.html), check it out!
:::

::::::::::::::::::::::::::::::::::::::::::::::: checklist

Some cool features of WarpX:  

*  Open-source - we wouldn't be here otherwise!
*  Runs on GPUs: NVIDIA, AMD, and Intel! 
*  Runs on multiple GPUs or CPUs, from laptops to supercomputers!
*  It has many options: 
    *  electrostatic, electromagnetic, magnetostatic
    *  mesh refinement
    *  embedded boundaries

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

## Installing WarpX using Conda-Forge

First, you need a Conda installation and we will assume that you indeed have one.
If not, follow the instruction at this [link](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html#regular-installation).  
You can install Conda on most operative systems: Windows, macOS, and Linux.  
Once you have Conda on your system, WarpX is available as a package via [Conda-Forge](https://conda-forge.org/download/).  
It's a one-liner, no-brainer, small-potatoes 😌!

::: callout
```bash
conda install -c conda-forge warpx 
```
:::

Ok, maybe two lines if you want to keep your system clean by creating a new environment. 

```bash
conda create -n warpx -c conda-forge warpx 
conda activate warpx 
```

Now you should have 4 different WarpX binaries in your `PATH` called `warpx.1d`, `warpx.2d`, `warpx.3d`, `warpx.rz`.  
Each binary for a different dimensionality.  

To check this, run:
```bash
which warpx.1d warpx.2d warpx.3d warpx.rz
```
If you get 3 different paths that look something like:
```bash
/home/<username>/anaconda3/envs/warpx/bin/warpx.xd
```
then you got this 🙌! You can also import `pywarpx` in `python`



## A simple example of a magnetic mirror

In this example we will simulate a bunch of protons inside a magnetic mirror machine. 
The protons are initialized with random positions and velocities. 
The magnetic field is loaded from a `.h5` file.
You can download the full input file from this [link](../files/inputs_3d_magnetic_mirror.txt)

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at the input file


``` bash
cat ./files/inputs_3d_magnetic_mirror.txt
```

``` output
##########################
# USER-DEFINED CONSTANTS #
##########################
my_constants.Lx = 2 # [m]
my_constants.Ly = 2 # [m] 
my_constants.Lz = 5 # [m]
my_constants.dt = 4.4e-7 # [s]
my_constants.Np = 1000 

############
# NUMERICS #
############
geometry.dims = 3
geometry.prob_hi =  0.5*Lx  0.5*Ly Lz
geometry.prob_lo = -0.5*Lx -0.5*Ly 0
amr.n_cell = 40 40 40
max_step = 500
warpx.const_dt = dt

##############
# ALGORITHMS #
##############
algo.particle_shape = 1
amr.max_level = 0
warpx.do_electrostatic = labframe
warpx.grid_type = collocated
warpx.serialize_initial_conditions = 0
warpx.use_filter = 0

##############
# BOUNDARIES #
##############
boundary.field_hi = pec pec pec
boundary.field_lo = pec pec pec
boundary.particle_hi = absorbing absorbing absorbing
boundary.particle_lo = absorbing absorbing absorbing

#############
# PARTICLES #
#############
particles.species_names = protons
protons.charge = q_e
protons.mass = m_p
protons.do_not_deposit = 1 # test particles
protons.initialize_self_fields = 0
protons.injection_style = gaussian_beam
protons.x_rms = 0.1*Lx
protons.y_rms = 0.1*Ly
protons.z_rms = 0.1*Lz
protons.x_m = 0. 
protons.y_m = 0.
protons.z_m = 0.5*Lz
protons.npart = Np 
protons.q_tot = q_e*Np
protons.momentum_distribution_type = uniform
protons.ux_min = -9.5e-05
protons.uy_min = -9.5e-05
protons.uz_min = -0.000134
protons.ux_max = 9.5e-05
protons.uy_max = 9.5e-05
protons.uz_max = 0.000134

##########
# FIELDS #
##########
# field here is applied on directly the particles! 
particles.B_ext_particle_init_style = read_from_file
particles.read_fields_from_path = example-femm-3d.h5

###############
# DIAGNOSTICS #
###############
diagnostics.diags_names = diag1
diag1.diag_type = Full
diag1.fields_to_plot = Bx By Bz
diag1.format = openpmd
diag1.intervals = 1
diag1.proton.variables = ux uy uz w x y z
diag1.species = protons
diag1.write_species = 1
```
::::::::::::::::::::::::::::::::::::::::::::::::::




## Visualizing with Paraview 


![Protons trajectories in a magnetic mirror](https://gist.github.com/user-attachments/assets/24b11226-4242-4958-bc12-c09159363065){alt="simulation of proton trajectories inside a magnetic mirror"}


## Visualizing with python

::::::::::::::::::::::::::::::::::::: keypoints 

- Use `.md` files for episodes when you want static content
- Use `.Rmd` files for episodes when you need to generate output
- Run `sandpaper::check_lesson()` to identify any issues with your lesson
- Run `sandpaper::build_lesson()` to preview your lesson locally

::::::::::::::::::::::::::::::::::::::::::::::::
