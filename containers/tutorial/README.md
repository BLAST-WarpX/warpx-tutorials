# WarpX tutorial container

A Docker image that serves the WarpX tutorials as a browser-based **JupyterLab**
session: notebooks, a terminal, and ready-to-use CPU and CUDA environments with
WarpX and ImpactX.

## Run it locally

```bash
docker build -f containers/tutorial/Dockerfile -t warpx-tutorial:local .
docker run --rm -p 127.0.0.1:3000:3000 warpx-tutorial:local
```

Open <http://localhost:3000/lab>, launch a **Terminal**, and run:

```bash
cd ~/warpx-tutorials/episodes/files
warpx.3d inputs_3d_magnetic_mirror.txt
```

The run takes about 10 seconds and writes approximately 780 MB of diagnostics.
Then open `analysis_3d_magnetic_mirror.ipynb` to visualize the results.

## Select a compute target

JupyterLab provides two kernels:

- **WarpX CPU** uses `/opt/venv-cpu` and is the default for the analysis
  notebooks.
- **WarpX GPU** uses the CUDA-enabled `/opt/venv-gpu`. Select it from
  **Kernel > Change Kernel** before running a simulation notebook.

In a terminal, the CPU environment is active by default. Switch to CUDA with:

```bash
source /opt/venv-gpu/bin/activate
```

That one command swaps both the Python environment and the `warpx.*` binaries
on `PATH`; `deactivate` returns to the CPU environment.

GPU use requires an NVIDIA GPU and the NVIDIA Container Toolkit. Start the
image with GPU access when available:

```bash
docker run --rm --gpus all -p 127.0.0.1:3000:3000 warpx-tutorial:local
```

## What is inside

| Path | Contents |
|---|---|
| `/opt/deps` | ADIOS2 and openPMD-api (C++ **and** Python), shared by both flavors |
| `/opt/warpx-cpu`, `/opt/warpx-gpu` | AMReX, WarpX (`warpx.1d`, `warpx.2d`, `warpx.3d`), ImpactX |
| `/opt/venv-cpu`, `/opt/venv-gpu` | Python: `amrex`, `pywarpx`, `impactx` and the analysis stack (JupyterLab in the CPU venv only) |

The image is built in stages: a CUDA `-devel` builder compiles everything, and
only the installed artifacts are copied into a CUDA `-runtime` final stage.
Nothing compute-agnostic is built twice — ADIOS2 and openPMD-api are built once
in `/opt/deps`, and within each flavor AMReX and pyAMReX are built once and
shared by WarpX and ImpactX. Everything is built as shared libraries, so AMReX
exists once per flavor rather than once per code and per dimensionality.

Both venvs import the single openPMD-api Python module from `/opt/deps` via a
`.pth` file, so the reader is always the same build as the writer. (The PyPI
`openpmd-api` wheel would instead vendor a second, different ADIOS2 and HDF5
into each venv.)

WarpX is built with `WarpX_FFT=ON` (four tutorial inputs use
`warpx.poisson_solver = fft`), QED table generation, and without MPI — no
tutorial runs multi-rank.

### Known limitations

- **RZ is not built.** Every tutorial input is `geometry.dims` 1, 2 or 3, so
  the image ships `warpx.1d`, `warpx.2d` and `warpx.3d` only. Note that
  `episodes/install.Rmd` tells you to check for `warpx.rz` — that section
  describes the Conda-Forge install, not this container. Leaving RZ out also
  removes the BLAS++/LAPACK++ dependency, which WarpX needs only for RZ
  together with FFT.
- `cupy` is installed in the GPU environment only (it is what makes pyAMReX's
  `.to_cupy()` zero-copy GPU-array path work). The CPU environment has no
  `cupy` and does not need one.
- The us-fcc-2026 lesson additionally imports `xsuite` and `cpymad`, which are
  not in the image.
- JupyterLab runs without a token or password. That is fine behind the
  `127.0.0.1` binding above; a publicly reachable host needs its own
  authentication in front.

## Automated builds

A cold build of both flavors exceeds GitHub's 6 h job limit, so
`.github/workflows/tutorial-docker-image.yml` compiles the CPU and GPU flavors
in two parallel jobs. Each publishes its installed trees as a scratch image
(`tutorial-artifacts:<flavor>-<sha>`), and a short assemble job composes the
final image from them using BuildKit build contexts. On `main` the result is
pushed to `ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest` (plus a
`:sha-<commit>` tag).

Pull requests from forks cannot publish the intermediate images, so there the
workflow stops after compiling both flavors — which is the part that can
actually break.
