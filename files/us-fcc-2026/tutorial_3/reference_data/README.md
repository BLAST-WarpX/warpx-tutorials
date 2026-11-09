# Optional Tutorial 3 reference data

This directory is the expected extraction location for a high-statistics
Tutorial 3 reference dataset. Generated results are intentionally excluded
from Git. The notebook automatically loads compatible results from:

```text
reference_data/outputs_without_warpx/
reference_data/outputs_with_warpx/
reference_data/outputs_with_warpx_beamstrahlung/
```

Each available output directory must contain `moments_b1.csv` and
`moments_b2.csv`. Coupled cases should also contain `handoff_checks.csv`.

## Generate a new reference dataset

Run these commands from the parent `tutorial_3` directory. The arc-only case
is inexpensive relative to the coupled case:

```bash
python exec_tutorial_3.py \
  --no-warpx \
  --macroparticles 1000000 \
  --iterations 1024 \
  --job-dir reference_data \
  --output outputs_without_warpx

python exec_tutorial_3.py \
  --macroparticles 1000000 \
  --iterations 1024 \
  --job-dir reference_data \
  --output outputs_with_warpx
```

The second command launches 1024 WarpX collisions and is intended for an
appropriate GPU or HPC system. Select the supported `--device` and
`--launcher` options for that installation. Do not use `--keep-diags` for the
reference run unless every collision diagnostic is genuinely needed.

An optional beamstrahlung dataset uses the same settings plus
`--beamstrahlung` and `--output outputs_with_warpx_beamstrahlung`.

The Fourier-bin spacing of a 1024-superperiod result is approximately
`1/1024 = 9.77e-4`. The high particle count reduces centroid noise, but it
does not turn the deliberately simplified lattice and collision model into a
production FCC-ee prediction.

## Publish the dataset externally

Archive only the `outputs_*` CSV directories and a provenance file. Do not
include `warpx_read`, `warpx_dump`, or per-collision openPMD diagnostics. The
provenance file should record:

- the warpx-tutorials Git commit;
- the exact commands, random seed, and machine/backend;
- WarpX, ImpactX, Xsuite, Python, and openPMD package versions;
- creation date and author; and
- a SHA-256 checksum for the archive.

A GitHub Release is convenient for workshop material; Zenodo is preferable
when a citable DOI and long-term preservation are desired. After publishing,
add the archive URL and checksum to this file. Older `coords_b*.txt` results
from the retired adapter are not schema-compatible with the current notebook
and should not be presented as results from this implementation.
