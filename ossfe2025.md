---
title: 'OSSFE 2025 - Using WarpX, a general purpose particle-in-cell code'  
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

## WarpX, a particle-in-cell code

Welcome to the WarpX tutorial at [OSSFE 2025](https://ossfe.github.io/)!

[WarpX](https://github.com/BLAST-WarpX/warpx) is a general purpose **open-source** **high-performance** Particle-In-Cell (PIC) code.  
If you are not familiar with the PIC method, here is a picture that condenses the core idea:  

If you want to know more, here are a few references:

*  The two bibles on PIC 📚
     *  [C. K. Birdsall and A. B. Langdon. Plasma Physics Via Computer Simulation.](https://doi.org/10.1201/9781315275048)  
     *  [R. W. Hockney and J. W. Eastwood. Computer simulation using particles.](https://doi.org/10.1201/9780367806934)  
*  An old review written by one of the pioneers: [John M. Dawson, Particle simulation of plasmas, Rev. Mod. Phys. 55, 403](https://doi.org/10.1103/RevModPhys.55.403)  
*  Browse our docs for [many more references about advanced algorithms and methods](https://warpx.readthedocs.io/en/latest/theory/pic.html).


In this tutorial we will go through the basics of WarpX: installation, running a simple example and visualizing the results. 
Along the way, we will point to some specific locations in the documentation, for your reference.


::: callout
Everything you need to know to use WarpX is in the [documentation](https://warpx.readthedocs.io/en/latest/index.html), check it out!
:::

::::::::::::::::::::::::::::::::::::::::::::::: checklist

Some cool features of WarpX:  

- [x] Open-source - we wouldn't be here otherwise  
- [x] Runs on GPUs: NVIDIA, AMD, and Intel  
- [x] Runs on multiple GPUs or CPUs, on systems ranging from laptops to supercomputers
- [x] Advanced algorithms and methods: mesh-refinement, embedded boundaries, electrostatic/electromagnetic/pseudospectral solvers, etc.
- [x] Standards: [openPMD](https://www.openpmd.org/#/start) for output data, [PICMI](https://github.com/picmi-standard/picmi) for inputs 
- [x] Active development and mainteinance: check our [GitHub repo](https://github.com/BLAST-WarpX/warpx)
- [x] International, cross-disciplinary community: plasma physics, fusion devices, laser-plasma interactions, beam physics, plasma-based acceleration, astrophysics 
 
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

## Installing WarpX using Conda-Forge

First, you need a Conda installation and we will assume that you indeed have one.  
We will also assume you have some familiarity with the terminal. 
If not, follow the [instruction at this link](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html#regular-installation).  
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
Make sure to download the [input file](./files/inputs_3d_magnetic_mirror.txt). 

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
Also, don't forget to [download the field file](../files/example-femm-3d.h5) and place it in the directory where you will run the input. 

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



## Visualizing with python

Now that we have the results, we can analyze them using `python`.  
We will use the [openPMD-viewer](https://openpmd-viewer.readthedocs.io/en/latest/) library to grab the data that the simulation produced in `openPMD` format. 

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at a simple Jupyter notebook

<iframe src="https://nbviewer.org/github/aeriforme/warpx-tutorials/blob/main/episodes/files/analysis_3d_magnetic_mirror.ipynb" 
           width="100%" height="800" style="border:none;">
     </iframe>
::::::::::::::::::::::::::::::::::::::::::::::::::


## Visualizing with Paraview 

Add stuff...

You can get images and videos 😎

![Protons trajectories in a magnetic mirror](https://gist.github.com/user-attachments/assets/24b11226-4242-4958-bc12-c09159363065){alt="simulation of proton trajectories inside a magnetic mirror"}


<iframe src="https://drive.google.com/file/d/1HhY2bL4kzkKoNp9eCkdI6S3m49JXUKsx/preview" width="100%" height="500" allow="autoplay"></iframe>

::::::::::::::::::::::::::::::::::::: keypoints 

- WarpX is a open-source high-performance particle-in-cell code
- WarpX is easy to install using `Conda`: `conda -c conda-forge warpx`
- The documentation is the first place to look for answers, otherwise check out our Issues and Discussions 
- Visualizing 3D results with Paraview and `openpmd` data using `.pmd` files. 

::::::::::::::::::::::::::::::::::::::::::::::::
