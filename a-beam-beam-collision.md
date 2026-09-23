---
title: 'A Beam-Beam Collision'
teaching: 10
exercises: 20
---

:::::::::::::::::::::::::::::::::::::: questions 

How to use WarpX for beam-beam simulations of colliders 💥?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Learn how to setup, run, and visualize your own beam-beam ☄️☄️ simulation

::::::::::::::::::::::::::::::::::::::::::::::::

![A snapshot of a beam-beam simulation.](https://gist.github.com/user-attachments/assets/217dfcde-8a77-4f73-b4bb-26c83e921255){alt="snapshot of a beam-beam simulation"}


## Setup

In this example we will simulate a bunch of electrons colliding against a bunch of positrons.
We have selected the parameters of the C$^3$ linear collider. 

Whenever you need to prepare an input file, [this is where you want to go](https://warpx.readthedocs.io/en/latest/usage/parameters.html).

:::::::::::::::::::::::::::::::::::::::::: spoiler

### Let's take a look at the input file


``` output
#################################
########## MY CONSTANTS #########
#################################
my_constants.mc2   = m_e*clight*clight
my_constants.nano  = 1.0e-9
my_constants.micro = 1.e-6
my_constants.milli = 1.e-3
my_constants.GeV   = q_e*1.e9

# BEAMS
my_constants.beam_energy = 125*GeV
my_constants.beam_gamma  = beam_energy/mc2 
my_constants.beam_npart  = 6.24e9
my_constants.nmacropart  = 1e5
my_constants.beam_charge = q_e * beam_npart
#my_constants.sigmax     = 210.0*nano 
#my_constants.sigmay     = 3.1*nano
my_constants.sigmaz      = 100.*micro
my_constants.beam_uth    = 0.3/100*beam_gamma
my_constants.mux         = 0.*sigmax
my_constants.muy         = 0.*sigmay
my_constants.muz         = 4*sigmaz
my_constants.emitx       = 900*nano
my_constants.emity       = 20*nano
my_constants.dux         = emitx / sigmax 
my_constants.duy         = emity / sigmay 
my_constants.betax       = 12*milli
my_constants.betay       = 0.12*milli 
my_constants.sigmax      = sqrt( emitx * betax / beam_gamma )
my_constants.sigmay      = sqrt( emity * betay / beam_gamma )

# BOX
my_constants.Lx = 20*sigmax
my_constants.Ly = 20*sigmay
my_constants.Lz = 16*sigmaz
my_constants.nx = 128
my_constants.ny = 128
my_constants.nz = 64
my_constants.dx = Lx/nx
my_constants.dy = Ly/ny
my_constants.dz = Lz/nz

# TIME
my_constants.T = 0.5*Lz/clight
my_constants.dt = T / nz
my_constants.nt = floor(T/dt)

# LUMI DIAG
my_constants.bin_num_1d = 2048
my_constants.bin_center_min_1d = 0.
my_constants.bin_center_max_1d = 2*beam_energy/q_e
my_constants.bin_size_1d = (bin_center_max_1d - bin_center_min_1d) / bin_num_1d
my_constants.bin_edge_min_1d = bin_center_min_1d - 0.5 * bin_size_1d
my_constants.bin_edge_max_1d = bin_center_max_1d + 0.5 * bin_size_1d
my_constants.bin_num_1d_eff = bin_num_1d + 1 

#################################
####### GENERAL PARAMETERS ######
#################################
stop_time = T
amr.n_cell = nx ny nz
amr.max_level = 0
geometry.dims = 3
geometry.prob_lo = -0.5*Lx -0.5*Ly -0.5*Lz
geometry.prob_hi =  0.5*Lx  0.5*Ly  0.5*Lz

#################################
######## BOUNDARY CONDITION #####
#################################
boundary.field_lo = open open open 
boundary.field_hi = open open open 
boundary.particle_lo = Absorbing Absorbing Absorbing
boundary.particle_hi = Absorbing Absorbing Absorbing

#################################
############ NUMERICS ###########
#################################
warpx.do_electrostatic = relativistic
warpx.const_dt = dt 
warpx.grid_type = collocated
algo.particle_shape = 3
algo.particle_pusher = vay 
warpx.poisson_solver = fft
warpx.use_2d_slices_fft_solver = 1

#################################
########### PARTICLES ###########
#################################
particles.species_names = ele1 pos2 pho1 pho2 ele2 pos1
particles.photon_species = pho1 pho2  

ele1.species_type = electron
ele1.injection_style = gaussian_beam
ele1.x_rms = sigmax
ele1.y_rms = sigmay
ele1.z_rms = sigmaz 
ele1.x_m = - mux
ele1.y_m = - muy
ele1.z_m = - muz
ele1.npart = nmacropart
ele1.q_tot = -beam_charge
ele1.z_cut = 4
ele1.focal_distance = muz
ele1.momentum_distribution_type = gaussian
ele1.uz_m = beam_gamma
ele1.uy_m = 0.0
ele1.ux_m = 0.0
ele1.ux_th = dux
ele1.uy_th = duy
ele1.uz_th = beam_uth
ele1.initialize_self_fields = 1
ele1.do_qed_quantum_sync = 1
ele1.qed_quantum_sync_phot_product_species = pho1
ele1.do_classical_radiation_reaction = 0

pos2.species_type = positron
pos2.injection_style = gaussian_beam
pos2.x_rms = sigmax
pos2.y_rms = sigmay
pos2.z_rms = sigmaz
pos2.x_m = mux 
pos2.y_m = muy
pos2.z_m = muz
pos2.npart = nmacropart
pos2.q_tot = beam_charge
pos2.z_cut = 4
pos2.focal_distance = muz
pos2.momentum_distribution_type = gaussian
pos2.uz_m = -beam_gamma
pos2.uy_m = 0.0
pos2.ux_m = 0.0
pos2.ux_th = dux
pos2.uy_th = duy
pos2.uz_th = beam_uth
pos2.initialize_self_fields = 1
pos2.do_qed_quantum_sync = 1
pos2.qed_quantum_sync_phot_product_species = pho2
pos2.do_classical_radiation_reaction = 0

pho1.species_type = photon 
pho1.injection_style = none 
pho1.do_qed_breit_wheeler = 1
pho1.qed_breit_wheeler_ele_product_species = ele1
pho1.qed_breit_wheeler_pos_product_species = pos1

pho2.species_type = photon 
pho2.injection_style = none 
pho2.do_qed_breit_wheeler = 1
pho2.qed_breit_wheeler_ele_product_species = ele2
pho2.qed_breit_wheeler_pos_product_species = pos2

ele2.species_type = electron 
ele2.injection_style = none 
ele2.do_qed_quantum_sync = 1
ele2.qed_quantum_sync_phot_product_species = pho2
ele2.do_classical_radiation_reaction = 0

pos1.species_type = positron
pos1.injection_style = none
pos1.do_qed_quantum_sync = 1
pos1.qed_quantum_sync_phot_product_species = pho1
pos1.do_classical_radiation_reaction = 0

#################################
############# QED ###############
#################################
qed_qs.photon_creation_energy_threshold = 0.

qed_qs.lookup_table_mode = builtin
qed_qs.chi_min = 1.e-7

qed_bw.lookup_table_mode = builtin
qed_bw.chi_min = 1.e-2

warpx.do_qed_schwinger = 0.

#################################
######### DIAGNOSTICS ###########
#################################
# FULL
diagnostics.diags_names = particles_out particles_in

# particles that exit the simulation domain at any given time
particles_out.dump_last_timestep = 1
particles_out.diag_type = BoundaryScraping
particles_out.format = openpmd
particles_out.openpmd_backend = h5
particles_out.intervals = -1

ele1.save_particles_at_xlo = 1
ele1.save_particles_at_ylo = 1
ele1.save_particles_at_zlo = 1
ele1.save_particles_at_xhi = 1
ele1.save_particles_at_yhi = 1
ele1.save_particles_at_zhi = 1

pos2.save_particles_at_xlo = 1
pos2.save_particles_at_ylo = 1
pos2.save_particles_at_zlo = 1
pos2.save_particles_at_xhi = 1
pos2.save_particles_at_yhi = 1
pos2.save_particles_at_zhi = 1

pho1.save_particles_at_xlo = 1
pho1.save_particles_at_ylo = 1
pho1.save_particles_at_zlo = 1
pho1.save_particles_at_xhi = 1
pho1.save_particles_at_yhi = 1
pho1.save_particles_at_zhi = 1

pho2.save_particles_at_xlo = 1
pho2.save_particles_at_ylo = 1
pho2.save_particles_at_zlo = 1
pho2.save_particles_at_xhi = 1
pho2.save_particles_at_yhi = 1
pho2.save_particles_at_zhi = 1

ele2.save_particles_at_xlo = 1
ele2.save_particles_at_ylo = 1
ele2.save_particles_at_zlo = 1
ele2.save_particles_at_xhi = 1
ele2.save_particles_at_yhi = 1
ele2.save_particles_at_zhi = 1

pos1.save_particles_at_xlo = 1
pos1.save_particles_at_ylo = 1
pos1.save_particles_at_zlo = 1
pos1.save_particles_at_xhi = 1
pos1.save_particles_at_yhi = 1
pos1.save_particles_at_zhi = 1

# particles inside the simulation domain 
particles_in.intervals = 1
particles_in.diag_type = Full
particles_in.species = ele1 pos2
particles_in.fields_to_plot = none
particles_in.format = openpmd
particles_in.openpmd_backend = h5
particles_in.dump_last_timestep = 1

# REDUCED
warpx.reduced_diags_names = DiffLumi_ele1_pos2 DiffLumi_ele1_ele2 DiffLumi_pos1_pos2 DiffLumi_pos1_ele2 DiffLumi_pos1_pho2 DiffLumi_ele1_pho2 DiffLumi_pho1_pos2 DiffLumi_pho1_ele2 DiffLumi_pho1_pho2 CollRel_ele1_pos2 

CollRel_ele1_pos2.type = ColliderRelevant
CollRel_ele1_pos2.species = ele1 pos2
CollRel_ele1_pos2.intervals = 1 

DiffLumi_ele1_pos2.type = DifferentialLuminosity
DiffLumi_ele1_pos2.intervals = nt
DiffLumi_ele1_pos2.species = ele1 pos2
DiffLumi_ele1_pos2.bin_number = bin_num_1d_eff
DiffLumi_ele1_pos2.bin_max = bin_edge_max_1d
DiffLumi_ele1_pos2.bin_min = bin_edge_min_1d

DiffLumi_ele1_ele2.type = DifferentialLuminosity
DiffLumi_ele1_ele2.intervals = nt
DiffLumi_ele1_ele2.species = ele1 ele2
DiffLumi_ele1_ele2.bin_number = bin_num_1d_eff
DiffLumi_ele1_ele2.bin_max = bin_edge_max_1d
DiffLumi_ele1_ele2.bin_min = bin_edge_min_1d

DiffLumi_pos1_pos2.type = DifferentialLuminosity
DiffLumi_pos1_pos2.intervals = nt
DiffLumi_pos1_pos2.species = pos1 pos2
DiffLumi_pos1_pos2.bin_number = bin_num_1d_eff
DiffLumi_pos1_pos2.bin_max = bin_edge_max_1d
DiffLumi_pos1_pos2.bin_min = bin_edge_min_1d

DiffLumi_pos1_ele2.type = DifferentialLuminosity
DiffLumi_pos1_ele2.intervals = nt
DiffLumi_pos1_ele2.species = pos1 ele2
DiffLumi_pos1_ele2.bin_number = bin_num_1d_eff
DiffLumi_pos1_ele2.bin_max = bin_edge_max_1d
DiffLumi_pos1_ele2.bin_min = bin_edge_min_1d

DiffLumi_ele1_pho2.type = DifferentialLuminosity
DiffLumi_ele1_pho2.intervals = nt
DiffLumi_ele1_pho2.species = ele1 pho2
DiffLumi_ele1_pho2.bin_number = bin_num_1d_eff
DiffLumi_ele1_pho2.bin_max = bin_edge_max_1d
DiffLumi_ele1_pho2.bin_min = bin_edge_min_1d

DiffLumi_pos1_pho2.type = DifferentialLuminosity
DiffLumi_pos1_pho2.intervals = nt
DiffLumi_pos1_pho2.species = pos1 pho2
DiffLumi_pos1_pho2.bin_number = bin_num_1d_eff
DiffLumi_pos1_pho2.bin_max = bin_edge_max_1d
DiffLumi_pos1_pho2.bin_min = bin_edge_min_1d

DiffLumi_pho1_pos2.type = DifferentialLuminosity
DiffLumi_pho1_pos2.intervals = nt
DiffLumi_pho1_pos2.species = pho1 pos2
DiffLumi_pho1_pos2.bin_number = bin_num_1d_eff
DiffLumi_pho1_pos2.bin_max = bin_edge_max_1d
DiffLumi_pho1_pos2.bin_min = bin_edge_min_1d

DiffLumi_pho1_ele2.type = DifferentialLuminosity
DiffLumi_pho1_ele2.intervals = nt
DiffLumi_pho1_ele2.species = pho1 ele2
DiffLumi_pho1_ele2.bin_number = bin_num_1d_eff
DiffLumi_pho1_ele2.bin_max = bin_edge_max_1d
DiffLumi_pho1_ele2.bin_min = bin_edge_min_1d

DiffLumi_pho1_pho2.type = DifferentialLuminosity
DiffLumi_pho1_pho2.intervals = nt
DiffLumi_pho1_pho2.species = pho1 pho2
DiffLumi_pho1_pho2.bin_number = bin_num_1d_eff
DiffLumi_pho1_pho2.bin_max = bin_edge_max_1d
DiffLumi_pho1_pho2.bin_min = bin_edge_min_1d
```
::::::::::::::::::::::::::::::::::::::::::::::::::


Some notable details:

*  Poisson solver: because the beams are ultra-relativistic (125 GeV electrons and positrons) and flat, 
we use an FFT-based electrostatic solver. 
Specifically, it solves many 2D Poisson equations in the $(x,y)$ plane for each $z$.
The full 3D version of this solver is also available with `warpx.use_2d_slices_fft_solver = 0`. 

*  Resolution: the number of grid cells is reduced to fit in a laptop. For production simulations, make sure you increase the resolution.

*  Timestep: since the beams travel at the speed of light along $z$ and the simulation frame is the center of mass frame, 
it makes sense to choose $dt = dz / ( 2 c )  $. However this is not strictly necessary. Sometimes it can be useful to save resources by choosing a larger timestep.
Just make sure you resolve ''well-enough'' the shortest timescale that you're interested in. 

*  QED lookup tables: here we use the built-in ones for convenience. For production runs, make sure to use tables with enough points and set the 
ranges of the $\chi$ parameter to what you need. 

*  Diagnostics:
    * the trajectories of the beam particles. This diagnostic can easily take up too much memory. 
    For simulations with many macroparticles, consider using a field diagnostic. 
    * all the particles that exit the domain (`BoundaryScraping`)
    * the differential luminosity of every pair of left-ward and right-ward moving species 
    

## Run 

First things first. 
Create a new folder where you copy the [input file](./files/inputs_3d_beambeam_C3.txt). 
The simulation in small enough that you should be able to run it in serial with the Conda installation of WarpX.

::: spoiler

## Let's run in serial

```bash
warpx.3d inputs_3d_beambeam_C3.txt
```

Just like that! 💃
Note that with Conda's WarpX you can run this anywhere in your filesystem (provided that you copied there the input of course)
because WarpX's executable are in your `$PATH`.
:::



If you want to make the simulation faster and/or bigger, then you should run with the parallel version of WarpX.
The optimal setup to run the simulation depends on your hardware. 
This is an example that should work on many common laptops, even though it might not be ideal.


::: spoiler

## Let's run in parallel

This is just one way of doing it!

```bash
export OMP_NUM_THREADS=2
mpirun -np 4 <path/to/your/build/bin/warpx.3d> inputs_3d_beambeam_C3.txt 
```
:::

::: testimonial
On my laptop's CPU (12th Gen Intel® Core™ i9-12900H × 20) the serial simulation took ~195 seconds, while the parallel one ~44 seconds on 4 cores!

:::


## Visualize


### With Python 🐍
Now that we have the results, we can analyze them using Python.  
We will use the [openPMD-viewer][openpmd-viewer] library to grab the data that the simulation produced in `openPMD` format. 
Here you can find [a few great tutorials on how to use the viewer](https://openpmd-viewer.readthedocs.io/en/latest/tutorials/tutorials.html).
If you feel nerdy and/or you need to deal with the data in parallel workflows, you can use the [openPMD-api][openpmd-api].

As an example for the beam-beam simulation, we have developed simple Jupyter notebook where we retrieve 
the beams' particles positions and project them on the $(z,x)$ and $(z,y)$ planes.

:::::::::::::::::::::::::::::::::::::::::: spoiler

## Let's take a look at the Jupyter notebook

<iframe src="https://nbviewer.org/github/BLAST-WarpX/warpx-tutorials/blob/main/episodes/files/analysis_3d_beambeam.ipynb" 
           width="100%" height="800" style="border:none;">
     </iframe>
::::::::::::::::::::::::::::::::::::::::::::::::::

You can [download the notebook](./files/analysis_3d_beambeam.ipynb) and try it yourself.
Remember to either run the notebook from the simulation directory or change the corresponding path in the notebook.


### With Paraview

::: caution

Coming soon!
:::


::::::::::::::::::::::::::::::::::::: keypoints 

 💅 There are several details one needs to take care when setting up a beam-beam simulation

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

 📷 To analyze and visualize the simulation results in [**openPMD**][openpmd] format, 
 you can use the [**openPMD-viewer**][openpmd-viewer] library for Python.

::::::::::::::::::::::::::::::::::::::::::::::::
