---
title: 'Instructor Notes'
---

### Discussions at OSSFE 2025

* Who develops WarpX? [A lot of people](https://github.com/BLAST-WarpX/warpx/graphs/contributors) from all around the world that work in different fields! WarpX is an open-source project that belongs to the [High Performance Software Foundation][hpsf], which itself is part of the nonprofit [Linux Foundation](https://www.linuxfoundation.org/).  

* What is the difference between a Monte Carlo code and a Particle-In-Cell code? Typically in MC the particles are independent one another, while in PIC they interact through the self-consistent field (collective effect). That being said, MC can and are included in the core PIC loop to simulate, e.g., binary collisions, ionzation, nuclear reactions, QED processes.

* Why Conda environments over Python environments? Conda is a system package manager, while `pip` is a Python package manager. With `conda` you can install much more than just Python libraries.

* Can WarpX deal with different species? [But of course](https://warpx.readthedocs.io/en/latest/usage/parameters.html#particle-initialization)! One can initialize as many species as desired, with user-define mass and charge. Beware that not all the additional physics modules (ionization, QED, ...) may work for arbitrary species!

* Does WarpX support mixed kinetic and fluid descriptions? Yes, check out the [hybrid solver](https://warpx.readthedocs.io/en/latest/theory/kinetic_fluid_hybrid_model.html)! 

### Two-stream instability: exploratory vs. recipe approach

The two-stream instability can be taught in two complementary ways:

**Recipe approach** (the [Two-Stream Instability](../episodes/a-two-stream-instability.Rmd) episode):
hand students a prepared input file with blanks to fill in.
Good for focusing on parameter selection and physics understanding.

**Exploratory approach** (the [Set Up a Simulation from Scratch](../episodes/set-up-a-simulation-from-scratch.Rmd) episode):
start from the WarpX uniform plasma example, browse the repo together, modify it live.
Good for teaching the *workflow* of setting up a new simulation.

The exploratory approach was used in a live session at UCB (April 2026).
Key observations from that session:

* Students found it very instructive to start from the "wrong" example and iterate.
  The first run (2D, 10 timesteps, warm beams) shows nothing -- and that's the point.
* The most common stumbling blocks: too few timesteps, thermal velocity washing out the instability, 
  and running in 2D/3D when 1D suffices.
* A good sequence of iterations: (1) increase timesteps, (2) set temperature to zero (cold beams), 
  (3) switch to 1D, (4) increase resolution and particles per cell.
* Making a video of the phase-space evolution at the end is very rewarding and helps students 
  connect the physics to the numerical experiment.