---
title: 'UCB 2026 -- Two-Stream Instability Live Tutorial'
teaching: 0
exercises: 90
---

:::::::::::::::::::::::::::::::::::::: questions 

Where can I find the material from the live WarpX tutorial (April 8, 2026)?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

Review the steps we followed during the live tutorial session.
Access the input files, notebooks, and visualizations produced in class.

::::::::::::::::::::::::::::::::::::::::::::::::

## What we did

In this live session, we set up and ran a **two-stream instability** simulation 
from scratch using [WarpX][warpx], following an exploratory approach:

1. We browsed the [WarpX examples on GitHub](https://github.com/BLAST-WarpX/warpx/tree/development/Examples/Physics_applications)
   and picked the [uniform plasma](https://github.com/BLAST-WarpX/warpx/tree/development/Examples/Physics_applications/uniform_plasma) 
   example as our starting point.
   
2. We **modified the input file**:
   - Duplicated the electron species and added opposite drift velocities (`uz_m`) to create two counter-streaming beams.
   - Defined `my_constants.nt` so we could change the number of timesteps in one place.
   - Introduced a temperature constant `T` and used it to compute the thermal spread:
     `ux_th = sqrt(T/m_e)/clight` (and same for `uy_th`, `uz_th`).
     For an isotropic distribution, the temperature is the same in each direction: 
     $T = T_x = T_y = T_z$, and each component of the thermal spread is set independently.
   - Switched diagnostics to **openPMD** format so we could use [openPMD-viewer][openpmd-viewer] to grab the data.

3. We ran the simulation in **2D** and made a quick **Jupyter notebook** to visualize 
   the phase space $(z, u_z)$.

4. The phase space wasn't changing -- so we **increased the number of timesteps**.

5. We kept iterating: set the **temperature to zero** (cold beams), 
   switched to **1D**, increased the **resolution** and 
   the **number of particles per cell**.

6. Eventually, we saw the **instability develop**: the counter-streaming beams 
   formed vortex structures in phase space.

7. We made a **video** of the phase-space evolution.

## Reference material

For a detailed walkthrough of the exploratory process we followed in class, 
see the [Set Up a Simulation from Scratch](set-up-a-simulation-from-scratch.Rmd) episode.

For a polished version of the two-stream instability simulation, 
with exercises on parameter selection, reduced diagnostics, and analysis notebooks,
see the [Two-Stream Instability](a-two-stream-instability.Rmd) tutorial.

## Files from the session

- [Input file](./files/ucb_lecture/input.txt) used in class
- [Jupyter notebook](./files/ucb_lecture/analysis.ipynb) for phase-space visualization and video generation

### Video from class

Here is the phase-space video we produced at the end of the session:

<iframe src="https://drive.google.com/file/d/1FjqeDtxuj3WbjXiLhzi1K1qIY4v2fDbO/preview" width="100%" height="500" allow="autoplay"></iframe>

As you can see, the dots are too large and it's hard to see the fine structure.
To improve the visualization, use a smaller marker size in the scatter plot, e.g. `s=0.1`.
You may also notice that the instability takes a while to develop -- 
the early frames are not very interesting.

::::::::::::::::::::::::::::::::::::: challenge

## How can you make the instability grow faster?

Try to think of what controls the growth rate. 
What parameters could you change so that the instability develops sooner?

:::::::::::::::: solution

A couple of ideas:

- **Increase the density.** 
  The instability growth rate scales with the plasma frequency $\omega_{pe} \propto \sqrt{n_0}$,
  so a higher density means faster growth.

- **Use random particle positions instead of uniform ones.**
  With `NUniformPerCell`, the particles start on a regular grid, 
  which is very quiet -- the instability has to grow from roundoff-level noise.
  Switching to `NRandomPerCell` introduces more initial noise 
  and can seed the instability earlier.
  Try changing `injection_style` from `NUniformPerCell` to `NRandomPerCell`
  and `num_particles_per_cell_each_dim` to `num_particles_per_cell`.

:::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::: keypoints 

Setting up a simulation is an iterative process: start from an existing example, modify, run, visualize, and refine.

The [WarpX documentation][warpx-readthedocs] and the [examples gallery](https://warpx.readthedocs.io/en/latest/usage/examples.html) are the best starting points.

When things don't look right, check the basics: enough timesteps, adequate resolution, and appropriate temperature.

::::::::::::::::::::::::::::::::::::::::::::::::
