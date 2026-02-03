---
title: 'Install'
teaching: 10
exercises: 0
---

:::::::::::::::::::::::::::::::::::::: questions 

- 🔧 How can I install and run WarpX?
- 🕵️ How can I analyze the simulation results?

::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::: objectives

- 💻 Install WarpX on your local machine either with [Conda](https://docs.conda.io/en/latest/) or from source
- 👀 Install the visualizations tools in `Python` and `Paraview`

::::::::::::::::::::::::::::::::::::::::::::::::


## Basic dependencies 


Just a heads-up before we dive deeper.

::: callout
📣 Everything you need to know to use WarpX is in the [documentation][warpx-readthedocs], check it out!
:::


## Via Conda-Forge

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

::: note
The first `warpx` (after `-n`) is the name of the conda environment; 
the second `warpx` is the name of the package to be installed from the conda-forge channel.
:::

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


::: caution

Conda's WarpX is serial! To get a parallel WarpX version, install it from source.

:::



## From source


::: caution

Coming soon. For now, [refer to the main documentation](https://warpx.readthedocs.io/en/latest/install/users.html#from-source-with-cmake).
:::


::::::::::::::::::::::::::::::::::::: keypoints 

 🎯 WarpX is **easy to install via Conda**: `conda -c conda-forge warpx`

 🔍 The [**documentation**][warpx-readthedocs] is the first place to look for answers, 
 otherwise check out our [**issues**][warpx-issues] and [**discussions**][warpx-discussions] and ask there.  

::::::::::::::::::::::::::::::::::::::::::::::::
