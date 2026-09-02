# WarpX tutorial container

A Docker image that serves the WarpX tutorials as a browser-based **JupyterLab**
session: notebooks, a terminal, and a ready-to-use `warpx` conda environment.

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

## Automated builds

`.github/workflows/tutorial-docker-image.yml` builds the image and, on `main`,
pushes it to `ghcr.io/blast-warpx/warpx-tutorials/tutorial:latest` (plus a
`:sha-<commit>` tag).
