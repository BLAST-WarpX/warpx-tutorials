# WarpX tutorial container

A Docker image that serves the WarpX tutorials as a browser-based **JupyterLab**
session: notebooks, a terminal, and ready-to-use CPU and CUDA environments with
WarpX and ImpactX.

## Run it

The image is published on GitHub's container registry and needs no login:

```bash
docker pull ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
docker run --rm -p 127.0.0.1:3000:3000 ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
```

To build it yourself instead, from the repository root:

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
docker run --rm --gpus all -p 127.0.0.1:3000:3000 ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest
```

The CUDA build targets compute capability 7.5 (`sm_75`, e.g. the T4 in AWS
g4dn instances) and runs on 7.5 and newer GPUs. On 8.0 and newer (Ampere and
later) the driver first compiles the GPU kernels for that architecture, so the
first GPU run in a new container starts noticeably slower, by one to two
minutes in our tests. The result is cached inside the container: later runs in
the same container start normally, but with `--rm` every new container compiles
again. To avoid this for a specific GPU, build the image yourself with, e.g.,
`--build-arg CUDAARCHS=86`.

## What is inside

| Path | Contents |
|---|---|
| `/opt/deps` | ADIOS2 and openPMD-api (C++ **and** Python), shared by both flavors |
| `/opt/venv` | the shared Python analysis stack (numpy, scipy, matplotlib, pandas, openpmd-viewer, imageio, IPython, ipywidgets, ipympl) |
| `/opt/warpx-cpu`, `/opt/warpx-gpu` | BLAS++, LAPACK++, AMReX, WarpX (`warpx.1d`, `warpx.2d`, `warpx.rz`, `warpx.3d`), ImpactX (`impactx`) |
| `/opt/venv-cpu` | `amrex`, `pywarpx`, `impactx` for CPU, plus JupyterLab and `imageio-ffmpeg` |
| `/opt/venv-gpu` | `amrex`, `pywarpx`, `impactx` for CUDA, plus `cupy` |

The image is built in stages: a CUDA `-devel` builder compiles everything, and
only the installed artifacts are copied into a final stage based on the CUDA
`-base` image plus just the CUDA libraries in use: cuFFT and cuRAND for AMReX,
cuBLAS and cuSOLVER for BLAS++/LAPACK++ (RZ), and cuSPARSE and NVRTC for cupy.

Nothing compute-agnostic is built or shipped twice. ADIOS2 and openPMD-api are
built once in `/opt/deps`; the analysis stack is installed once in `/opt/venv`;
and within each flavor AMReX and pyAMReX are built once and shared by WarpX and
ImpactX. The CPU and GPU venvs reach the shared pieces through a `.pth` file, so
the openPMD-api reader is always the same build as the writer. Everything is
built as shared libraries, so AMReX exists once per flavor rather than once per
code and per dimensionality.

WarpX is built for 1D, 2D, RZ and 3D with `WarpX_FFT=ON` (four tutorial
inputs use `warpx.poisson_solver = fft`; RZ with FFT is what needs BLAS++ and
LAPACK++), QED table generation, and without MPI — no tutorial runs
multi-rank. ImpactX is built with FFT as well, which enables its FFT-based
space charge and CSR solvers. ImpactX compiles its own copy of ABLASTR, but the
image ships only WarpX's `libablastr_3d.so`, which ImpactX uses at runtime.

### Known limitations

- The us-fcc-2026 lesson additionally imports `xsuite` and `cpymad`, which are
  not in the image.
- JupyterLab runs without a token or password. That is fine behind the
  `127.0.0.1` binding above; a publicly reachable host needs its own
  authentication in front.

## Automated builds

`.github/workflows/tutorial-docker-image.yml` compiles the CPU and GPU flavors
in two parallel jobs. Measured cold, the CPU job takes 55–70 min and the CUDA
job 3–4 h, both within GitHub's 6 h job limit. Each publishes its installed
trees as a scratch image
(`tutorial-buildcache:<flavor>-<sha>`), and a short assemble job composes the
final image from them using BuildKit build contexts. On `main` the result is
pushed to `ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest` (plus a
`:sha-<commit>` tag); pull requests from branches of the same repository push
it as `:pr-<number>`.

The workflow uses two GHCR packages:

| Package | Contents |
|---|---|
| `tutorial` | runnable images only: `:latest` and `:sha-<commit>` from `main`, `:pr-<number>` from same-repository pull requests |
| `tutorial-buildcache` | CI internals, not runnable: the BuildKit layer cache (`:cpu`, `:gpu`) and the per-run hand-off to the assemble job (`:<flavor>-<sha>`, scratch images holding the compiled `/opt` trees) |

Pull requests from forks cannot publish the intermediate images, so there the
workflow stops after compiling both flavors — which is the part that can
actually break.
