---
title: 'A Magnetic Mirror'
teaching: 10
exercises: 2
---

:::::::::::::::::::::::::::::::::::::: questions 

🪞 How to simulate the dynamics of charged particles in an external field?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

🏃 Run and 👀 visualize some protons in a magnetic mirror!

::::::::::::::::::::::::::::::::::::::::::::::::

## Setup

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


A few notable details:  

*  The protons are test particles because of the parameter `protons.do_not_deposit=1`. 
This means that the protons do not deposit their current density, therefore they do not contribute to the fields. 

*  The magnetic field is applied directly to the particles with the `particles.B_ext_particle_init_style` flag,
so in principle the grid is not used at all. For technical reasons, we must define a grid nonetheless.

Now that we have an idea of what the input files looks like, let's set up our environment.
Activate the `warpx` environment if you need to.
Create a new directory with your own copy of the input file. 
Also, don't forget to [download the field file](./files/example-femm-3d.h5) and place it in the directory where you will run the input. 


## Run 

::::::::::::::::::::::::::::::::::::: challenge

## Let's run the code

How would you do it? 🤷

:::::::::::::::: solution

```bash
warpx.3d inputs_3d_magnetic_mirror.txt
```
As simple as that! 😉
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


## Visualize

### With Python 🐍

Now that we have the results, we can analyze them using Python.  
We will use the [openPMD-viewer][openpmd-viewer] library to grab the data that the simulation produced in `openPMD` format. 
Here you can find [a few great tutorials on how to use the viewer](https://openpmd-viewer.readthedocs.io/en/latest/tutorials/tutorials.html).
If you feel nerdy and/or you need to deal with the data in parallel workflows, you can use the [openPMD-api][openpmd-api].

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

 💡 The external B field is loaded from an openPMD file, while the protons are defined as test particles.

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python 
 or you can open `.pmd` files directly in [**Paraview**]((https://www.paraview.org/download/)).

::::::::::::::::::::::::::::::::::::::::::::::::
