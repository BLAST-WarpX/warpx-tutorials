# WarpX tutorial container

A Docker image that serves the WarpX tutorials as a browser-based **JupyterLab**
session: notebooks, a terminal, and ready-to-use CPU and CUDA WarpX environments.

## Run it locally

```bash
docker build -f containers/tutorial/Dockerfile -t warpx-tutorial:local .
docker run --rm -p 127.0.0.1:3000:3000 warpx-tutorial:local
```

Open <http://localhost:3000/lab>, launch a **Terminal**, and run:

```bash
warpx.3d inputs_3d_magnetic_mirror.txt
```

The run takes about 10 seconds and writes approximately 780 MB of diagnostics.
Then open `analysis_3d_magnetic_mirror.ipynb` to visualize the results.

## Select a compute target

JupyterLab provides two kernels:

- **WarpX CPU** uses the `warpx-cpu` environment and is the default kernel for
  the analysis notebooks.
- **WarpX GPU** uses the CUDA-enabled `warpx-gpu` environment. Select it from
  **Kernel > Change Kernel** before running a simulation notebook or opening a
  terminal with `conda activate warpx-gpu`.

GPU use requires an NVIDIA GPU and the NVIDIA Container Toolkit. Start the
image with GPU access when available:

```bash
docker run --rm --gpus all -p 127.0.0.1:3000:3000 warpx-tutorial:local
```

## Automated builds

`.github/workflows/tutorial-docker-image.yml` builds the image and, on `main`,
pushes it to `ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest` (plus a
`:sha-<commit>` tag).
