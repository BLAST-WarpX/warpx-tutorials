---
title: 'OSSFE 2025 - Using WarpX, a general purpose particle-in-cell code'  
teaching: 30
exercises: 30
---

:::::::::::::::::::::::::::::::::::::: questions 

- 🤌 What is WarpX? 
- 🔧 How can I install and run WarpX?
- 🕵️ How can I analyze the simulation results?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

- 💻 Install WarpX on your local machine with [Conda](https://docs.conda.io/en/latest/)
- 🏃 Run a fusion-relevant example on your local machine: protons in a magnetic mirror!
- 👀 Visualize the results with `Python` and `Paraview`

::::::::::::::::::::::::::::::::::::::::::::::::

## WarpX, a particle-in-cell code

Welcome to the WarpX tutorial at [OSSFE 2025](https://ossfe.github.io/)! 👋

[WarpX][warpx] is a general purpose **open-source** **high-performance** **Particle-In-Cell** (PIC) code.  
If you are not familiar with the PIC method, here is a picture that condenses the core idea:  

![Some computational particles (a.k.a. macroparticles) traveling in space, across the cells of a grid.](https://gist.github.com/user-attachments/assets/50726d37-2b72-4664-9435-f90d7d2f0043
){alt="macroparticles in the cells of a grid"}

And here is a more informative image that explains the core algorithmic steps.

![The loop at the basis of standard PIC codes.](https://gist.github.com/user-attachments/assets/659c0816-3c13-4375-b17d-03b894e17b93
){alt="pic loop"}

If you want to know more about PIC, here are a few **references**:

*  The two bibles on PIC 📚
     *  [C. K. Birdsall and A. B. Langdon. Plasma Physics Via Computer Simulation.](https://doi.org/10.1201/9781315275048)  
     *  [R. W. Hockney and J. W. Eastwood. Computer simulation using particles.](https://doi.org/10.1201/9780367806934)  
*  An old review written by one of the pioneers: [John M. Dawson, Particle simulation of plasmas, Rev. Mod. Phys. 55, 403](https://doi.org/10.1103/RevModPhys.55.403)  
*  Browse our docs for [many more references about advanced algorithms and methods](https://warpx.readthedocs.io/en/latest/theory/pic.html).

In this tutorial we will go through the **basics of WarpX**: installation, running a simple example and visualizing the results. 
Along the way, we will point to some specific locations in the documentation, for your reference.

::: callout
📣 Everything you need to know to use WarpX is in the [documentation][warpx-readthedocs], check it out!
:::

::::::::::::::::::::::::::::::::::::::::::::::: checklist

Some cool features of WarpX:  

 📖 Open-source - we wouldn't be here otherwise!  

 ✈️ Runs on GPUs: NVIDIA, AMD, and Intel  

 🚀 Runs on multiple GPUs or CPUs, on systems ranging from laptops to supercomputers  

 🤓 **Many many advanced algorithms and methods**: mesh-refinement, embedded boundaries, electrostatic/electromagnetic/pseudospectral solvers, etc.  
 
 💾 Standards: [openPMD][openpmd] for input/output data, [PICMI][picmi] for inputs  

 🤸 Active development and mainteinance: check our [GitHub repo][warpx-github]  

 🗺️ International, cross-disciplinary community: plasma physics, fusion devices, laser-plasma interactions, beam physics, plasma-based acceleration, astrophysics 
 
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

## Installing WarpX using Conda-Forge

First, you need a **Conda** installation and we will assume that you indeed have one.  
If not, follow the [instruction at this link](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html#regular-installation).  
You can install Conda on most operative systems: **Windows, macOS, and Linux**.  
We will also assume you have some familiarity with the **terminal**. 
Once you have Conda on your system, **WarpX is available as a package** via [Conda-Forge](https://conda-forge.org/download/).  
The installation is a **one-liner** 😌!

::: callout
```bash
conda install -c conda-forge warpx 
```
:::

Ok, maybe two lines if you want to keep your system clean by creating a new **environment**. 

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
then you got this 🙌! You can also import `pywarpx` in Python.


## A simple example of a magnetic mirror

In this example we will simulate a bunch of **protons inside a magnetic mirror machine**. 
The protons are initialized with random positions and velocities. 
The magnetic field is loaded from a `.h5` file.
Make sure to download the [input file](./files/inputs_3d_magnetic_mirror.txt). 

Whenever you need to prepare an input file, [this is where you want to go](https://warpx.readthedocs.io/en/latest/usage/parameters.html).
By the way, analytics tell us that this is the most popular page of the documentation 👠! 

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at the input file


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

Now that we have an idea of what the input files looks like, let's set up our environment.
Activate the `warpx` environment if you need to.
Create a new directory with your own copy of the input file. 
Also, don't forget to [download the field file](./files/example-femm-3d.h5) and place it in the directory where you will run the input. 

::::::::::::::::::::::::::::::::::::: challenge

## Let's run the code

How would you do it? 🤷

:::::::::::::::: solution

```bash
warpx.3d inputs_3d_magnetic_mirror.txt
```
:::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::::::


You should see a standard output flashing out a lot of info.  
At the end, you should find in your folder:

  * a subfolder called `diags`: here is where the code stored the diagnostics  
  * a file called `warpx_used_inputs`: this is a summary of the inputs that were used to run the simulation  

If that's the case, yey! 💯  

If the run went wrong, you may find a `Backtrace.0.0` file which can be useful for debugging purposes. 
Let me know if the code fails in any way! 

Here we have loaded the field of hte magnetic bottle from a file.
You can also you can [define an external field analytically](https://warpx.readthedocs.io/en/latest/usage/parameters.html#applied-to-particles).


## Data handling and visualizations 

### With Python 🐍

Now that we have the results, we can analyze them using Python.  
We will use the [openPMD-viewer][openpmd-viewer] library to grab the data that the simulation produced in `openPMD` format. 
Here you can find [a few great tutorials on how to use the viewer](https://openpmd-viewer.readthedocs.io/en/latest/tutorials/tutorials.html).
If you feel nerdy and/or you need to deal with the data in parallel workflows, you can use the [openPMD-api][opepmd-api].

As an example for the magnetic bottle simulation, we have developed simple Jupyter notebook where we retrieve the magnetic field 
and the particle attributes at the end of the simulation.
With a little bit more work, we also plot the trajectories of the particles.

:::::::::::::::::::::::::::::::::::::::::: spoiler

## Let's take a look at the Jupyter notebook

<iframe src="https://nbviewer.org/github/aeriforme/warpx-tutorials/blob/main/episodes/files/analysis_3d_magnetic_mirror.ipynb" 
           width="100%" height="800" style="border:none;">
     </iframe>
::::::::::::::::::::::::::::::::::::::::::::::::::


You can [download the notebook](./files/analysis_3d_magnetic_mirror.ipynb) and try it yourself.
Remember to either run the notebook from the simulation directory or change the corresponding path in the notebook.

### With Paraview

Now it's time to produce some pretty cool images and videos! 😎
If you don't have it, you can [download Paraview here](https://www.paraview.org/download/).
In the `diags/diag1` directory you should find a file named `paraview.pmd`: Paraview can read `.pmd` files.
Just open Paraview and from there open the `.pmd` file.
You should see `Meshes` and `Particles` in your pipeline browser (usually on the left).
We can zhuzh up the pipeline so that we can visualize the trajectories of the protons in time

This is the pipeline that I have used to produce the visualizations below.

![](https://gist.github.com/user-attachments/assets/5847ad00-2f68-4c13-ab42-51485a6551cd){alt="paraview pipeline"}

![Protons trajectories in a magnetic mirror](https://gist.github.com/user-attachments/assets/24b11226-4242-4958-bc12-c09159363065){alt="simulation of proton trajectories inside a magnetic mirror"}

<iframe src="https://drive.google.com/file/d/1HhY2bL4kzkKoNp9eCkdI6S3m49JXUKsx/preview" width="100%" height="500" allow="autoplay"></iframe>


If you make any other 3D visualization with this data, let me know! We can add it here 😉!

And that's all for now! 👋

::::::::::::::::::::::::::::::::::::: keypoints 

 🚀 [**WarpX**][warpx] is a open-source high-performance particle-in-cell code  

 🎯 WarpX is **easy to install via Conda**: `conda -c conda-forge warpx`  

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python 
 or you can open `.pmd` files directly in [**Paraview**]((https://www.paraview.org/download/)).

::::::::::::::::::::::::::::::::::::::::::::::::
