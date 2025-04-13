---
title: 'Introduction to WarpX'
teaching: 10
exercises: 0
---


:::::::::::::::::::::::::::::::::::::: questions 

- 🤌 What is WarpX? 
- 🤔 What is a PIC code?
- 🧐 What can I use WarpX for?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

- 💡 Understand the basics of PIC codes
- 🧑‍💻 Learn about the features of WarpX 
- 🎯 Figure out if WarpX can be useful for you!

::::::::::::::::::::::::::::::::::::::::::::::::

## Overview of PIC  

[WarpX][warpx] is a general purpose **open-source** **high-performance** **Particle-In-Cell** (PIC) code.   
The PIC method is a very popular approach to **simulate the dynamics of physical systems governed by relativistic electrodynamics**.
**Plasmas ⭐ and beams ☄️**, which are often made of charged particles that may travel almost at the speed of light, fall into this category.
Additionally, other physical effects can be integrated into the PIC algorithm, such as different **quantum** 🎲 processes.

Here is a picture that condenses the core idea: there are _particles_ and _fields_.
The particles are approximated as _macroparticles_ (usually each representative of many real particles), while the fields are approximated on a _grid_ in space.
The particles and the fields are updated, self-consistently, in a temporal loop.  

![Some macroparticles traveling in space, across the cells of a grid.](https://gist.github.com/user-attachments/assets/50726d37-2b72-4664-9435-f90d7d2f0043
){alt="macroparticles in the cells of a grid"}

Here is a more informative image that explains the core algorithmic steps.
As the particles travel in space, they generate currents, which in turn generate an electromagnetic field. 
The electromagnetic field then push the particles via the Lorentz force. 
Therefore, the current density $\textbf{J}$ and the force $\textbf{F}_L$ are the quantitieis that connect the particles and the fields, or in PIC lingo, the macroparticles and the grid.
Hence, the idea is the following.
First, define a well-posed initial condition, and then iterate the following:
* Interpolate the fields from the grid to the particles' positions and compute the Lorentz force that acts on each macroparticle,
* Advance the position and momenta of the macroparticles using Newton equations,
* Project while cumulating the contribution to the current density of each macroparticles,
* Solve Maxwell's equations.

In some cases, one can choose to solve Poisson's equation instead of Maxwell's. 
In that case, the current $\textbf{J}$ calculation is replaced with the charge density $\rho$ calculation.
Once $\rho$ is known, the electrostic potential is computed to then find the electric field.

![The loop at the basis of standard PIC codes.](https://gist.github.com/user-attachments/assets/659c0816-3c13-4375-b17d-03b894e17b93
){alt="pic loop"}


If you want to know more about PIC, here are a few **references**:

*  The two bibles on PIC 📚
     *  [C. K. Birdsall and A. B. Langdon. Plasma Physics Via Computer Simulation.](https://doi.org/10.1201/9781315275048)  
     *  [R. W. Hockney and J. W. Eastwood. Computer simulation using particles.](https://doi.org/10.1201/9780367806934)  
*  An old review written by one of the pioneers: [John M. Dawson, Particle simulation of plasmas, Rev. Mod. Phys. 55, 403](https://doi.org/10.1103/RevModPhys.55.403)  
*  Browse our docs for [many, many more references about advanced algorithms and methods](https://warpx.readthedocs.io/en/latest/theory/pic.html).


## Features and applications of WarpX

WarpX is developed and used by a wide range of researchers working in different fields, from beam physics to nuclear fusion and a lot more.
To learn about what WarpX can be used for, [check out our examples](https://warpx.readthedocs.io/en/latest/usage/examples.html)
and the [scientific publications that acknowledged WarpX](https://warpx.readthedocs.io/en/latest/highlights.html).



::::::::::::::::::::::::::::::::::::::::::::::: checklist

Some cool features of WarpX: 

 📖 Open-source!  

 ✈️ Runs on GPUs: NVIDIA, AMD, and Intel  

 🚀 Runs on multiple GPUs or CPUs, on systems ranging from laptops to supercomputers  

 🤓 **Many many advanced algorithms and methods**: mesh-refinement, embedded boundaries, electrostatic/electromagnetic/pseudospectral solvers, etc.  
 
 💾 Standards: [openPMD][openpmd] for input/output data, [PICMI][picmi] for inputs  

 🤸 Active development and mainteinance: check out our [GitHub repo][warpx-github]  

 🗺️ International, cross-disciplinary community: plasma physics, fusion devices, laser-plasma interactions, beam physics, plasma-based acceleration, astrophysics, others? 
 
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

We will add here more details soon!


::::::::::::::::::::::::::::::::::::: keypoints 

 🔮 **The particle-in-cell** method is used to simulate the self-consistent dynamics of relativistic charged particles

 🚀 [**WarpX**][warpx] is a open-source high-performance particle-in-cell code  

 ✨ [**WarpX**][warpx] is used in a variety of scientif domains   


::::::::::::::::::::::::::::::::::::::::::::::::


