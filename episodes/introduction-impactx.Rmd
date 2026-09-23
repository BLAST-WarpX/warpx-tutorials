---
title: 'Introduction to ImpactX'
teaching: 10
exercises: 0
---

:::::::::::::::::::::::::::::::::::::: questions

- 🤌 What is ImpactX?
- 🤔 What is a beam dynamics code?
- 🧐 What can I use ImpactX for?
- 🏋️ Does it need HPC?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

- 💡 Understand the basics of beam dynamics codes
- 🧑‍💻 Learn about the features of ImpactX
- 🎯 Recognize applications of ImpactX and its relationship to WarpX.
- 💰 Connect numerics to computational cost.

::::::::::::::::::::::::::::::::::::::::::::::::

## Overview of beam dynamics

[ImpactX][impactx] is an **open-source**, **high-performance** **beam dynamics**
code for particle accelerators. It follows beams through linear accelerators
and rings, including **collective effects** from the particles' own fields.
Think of the input as a bunch of particles and an itinerary through magnets
and accelerating cavities: ImpactX calculates how the bunch changes along
that route. 🧲

A **particle beam** is a group of particles traveling in approximately the
same direction. A short group within a beam is called a **bunch**. Magnetic fields 🧲
steer and focus beams; electric fields 🔋 can give particles energy.
In a **particle accelerator** there are many **elements** that, in sequence,
constitute the accelerator **lattice**.
Each element has a specific function: for instance, radiofrequency cavities accelerate,
dipoles steer the beams, quadrupoles focus the beams, etc.
Each accelerator has its own complex lattice.
**Beam dynamics** describes how the particles' positions and momenta change
as they travel through these components.

### From a lattice to a simulation

In particle tracking, a collection of **macroparticles** samples the bunch's
positions and momenta. Each macroparticle represents part of the physical
beam charge. Increasing their number can improve sampling without changing
the total charge of the beam.

The ordered list of accelerator components is called a **lattice**. Some
basic elements are:

| Element | Role in the beamline |
| --- | --- |
| Drift | A region without an applied focusing or bending field; particles continue along their directions of travel |
| Quadrupole magnet | Focuses in one transverse direction while defocusing in the other; combinations provide overall focusing |
| Dipole magnet | Bends the reference trajectory |
| Chicane (a sequence of magnets) | Sends the beam through a sideways detour and back to its original direction; energy-dependent path lengths can shorten or lengthen a bunch, depending on how energy varies along it |
| Solenoid magnet | Uses a magnetic field along the beam axis to focus the beam and couple horizontal and vertical motion |
| Steering kicker | Gives particles a transverse momentum change to adjust the beam's direction |
| Accelerating cavity | Changes the particles' energies |
| Buncher | Gives particles different energy changes according to their arrival time, allowing subsequent transport to shorten the bunch |
| Aperture / collimator | Defines an opening and removes particles that strike the modeled boundary |
| Beam monitor | Records simulated beam data at a chosen location |

The [ImpactX element reference](https://impactx.readthedocs.io/en/latest/usage/python.html)
describes the available models and their settings. A lattice includes only
the elements you specify; for example, particle losses at a collimator are
modeled only when such an opening is included.

ImpactX advances particles along the reference trajectory, using distance
**s** as the independent variable. At each element, a mathematical map
updates their coordinates to represent passage through that component.
Coordinates describe deviations from a **reference particle**, which follows
the nominal accelerator trajectory. This is useful for measuring beam offsets
and spreads. See the [reference-trajectory explanation](https://impactx.readthedocs.io/en/latest/theory/concepts.html).

Here is the tracking recipe:

1. Specify the reference particle and sample the incoming bunch.
2. Define the lattice and its magnet or cavity settings.
3. Advance the particles through successive elements, including any enabled
   collective effects.
4. Record particle snapshots and quantities such as horizontal and vertical
   beam size along the beamline.

**Space charge** is the interaction of the bunch with its own electric field.
When modeled with a PIC space-charge solver, particle charge is deposited on
a grid, Poisson's equation is solved, and the resulting field acts back on the
particles. This adds grid work to particle tracking. ImpactX therefore is
not limited to tracking independent particles in prescribed fields.
See the [ImpactX model overview](https://impactx.readthedocs.io/en/latest/).

If you want to know more about beam dynamics, here are a few **references**:

* 📚 Two books to explore:
  * [H. Wiedemann, *Particle Accelerator Physics*, 4th edition (2015)](https://doi.org/10.1007/978-3-319-18317-6).
    An open-access introduction to accelerators, beam transport, and focusing.
  * [M. Reiser, *Theory and Design of Charged Particle Beams*, 2nd edition (2008)](https://doi.org/10.1002/9783527622047).
    A reference for beam physics, including space-charge effects.
* 🔬 A look at how the code is checked:
  [C. E. Mitchell et al., *ImpactX Modeling of Benchmark Tests for Space Charge Validation*, HB2023](https://doi.org/10.18429/JACoW-HB2023-THBP44).
* Browse the [ImpactX theory documentation](https://impactx.readthedocs.io/en/latest/theory/concepts.html)
  for the coordinate conventions and models behind the tracking.

## Features and applications of ImpactX

ImpactX helps researchers study beam transport and explore accelerator
settings. The [code overview](https://impactx.readthedocs.io/en/latest/)
describes its scope; the examples below give a taste of what you can investigate.

### What physical questions can ImpactX help answer?

Examples include:

- 🧲 **Focusing and transport:** how do magnet settings affect the beam's size
  and shape along an accelerator?
- 🌈 **Energy spread:** how do particles of different energies respond to the
  same magnets, and how does this affect transport?
- 🎯 **Alignment:** how does a displaced magnet change the beam trajectory?
- 🏎️ **Acceleration and compression:** how do accelerating cavities change
  particle energies, and how can a beamline change a bunch's length?
- 🤝 **Collective effects:** how do a bunch's own electric fields change its
  size and distribution?

The [ImpactX examples](https://impactx.readthedocs.io/en/latest/usage/examples.html)
include focusing cells, alignment errors, accelerating cavities, chicanes,
and beams with space charge. They provide starting points for choosing the
components and effects needed for a particular study.

::::::::::::::::::::::::::::::::::::::::::::::: checklist

Some cool features of ImpactX:

📖 **Open-source!** Explore the [code and development discussions](https://github.com/BLAST-ImpactX/impactx).

🚀 **Runs on CPUs and GPUs**, from small examples to larger beam calculations.

🧲 **Accelerator elements** for focusing, bending, and acceleration, with
models for collective effects such as space charge.

🐍 **Python inputs** to build a lattice, launch a run, and explore different settings.

💾 **Beam diagnostics** to follow particle distributions and beam sizes
along the accelerator.

🔬 **Benchmarks** to check the models against known results:
[try the examples](https://impactx.readthedocs.io/en/latest/usage/examples.html).

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::

## From beam tracking to high-performance computing

🏋️ **The computing workload.** Without collective effects, each particle
can be advanced through a given element independently. This tracking is
**embarrassingly parallel** : particles can be divided among CPU cores or GPUs
with little coordination during their advance.
More particles increase both tracking work and the amount of particle data
that monitors can save.

🤝 **Collective effects change the challenge.** The particles now influence
one another through the electromagnetic field, requiring more computational work and
coordination. For space charge, ImpactX can use **PIC** to deposit particle
charge on a grid, solve for the field, and apply it back to the particles,
avoiding a direct calculation of every particle pair's interaction. Large
calculations need both computing resources and efficient field solvers,
communication, and workload distribution.

## WarpX and ImpactX in the same workflow 🔗

[WarpX](introduction.Rmd) can resolve the evolving particles and fields in a
laser–plasma accelerator. ImpactX can then model transport of a bunch through
downstream accelerator components. These stages use different representations
suited to the physics and scales being studied. Transferring a bunch requires
consistent coordinates and a suitable beam selection.

::::::::::::::::::::::::::::::::::::: keypoints

- 🧲 ImpactX models how particle beams evolve through accelerator components.
- 🎯 The lattice, incoming bunch, and enabled effects define the physical model.
- 💰 Particle count, collective-field calculations, and diagnostics determine
  the workload.

::::::::::::::::::::::::::::::::::::::::::::::::
