---
title: 'Instructor Notes'
---

### Discussions at OSSFE 2025

* Who develops WarpX? [A lot of people][https://github.com/BLAST-WarpX/warpx/graphs/contributors] from all around the world that work in different fields! WarpX is an open-source project that belongs to the [High Performance Software Foundation][hpsf], which itself is part of the nonprofit [Linux Foundation][https://www.linuxfoundation.org/].  

* What is the difference between a Monte Carlo code and a Particle-In-Cell code? Typically in MC the particles are independent one another, while in PIC they interact through the self-consistent field (collective effect). That being said, MC can and are included in the core PIC loop to simulate, e.g., binary collisions, ionzation, nuclear reactions, QED processes.

* Why Conda environments over Python environments? Conda is a system package manager, while `pip` is a Python package manager. With `conda` you can install much more than just Python libraries.

* Can WarpX deal with different species? [But of course][https://warpx.readthedocs.io/en/latest/usage/parameters.html#particle-initialization]! One can initialize as many species as desired, with user-define mass and charge. Beware that not all the additional physics modules (ionization, QED, ...) may work for arbitrary species!

* Does WarpX support mixed kinetic and fluid descriptions? Yes, check out the [hybrid solver][https://warpx.readthedocs.io/en/latest/theory/kinetic_fluid_hybrid_model.html]! 