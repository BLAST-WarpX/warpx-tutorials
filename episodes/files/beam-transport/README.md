# A Beam Transport Line

The [episode](../../a-beam-transport-line.Rmd) explains setup, the HTU beamline,
run instructions, and diagnostic interpretation.

Keep `htu_transport.ipynb` and `impactx_helpers.py` together in this folder.
Open the notebook from `beam-transport/`. It downloads the pinned ImpactX
26.09 `htu_lattice.py` on first use if missing, and saves each simulation
in a fresh folder under `runs/`.

`images/htu-transmission.png` is the beam-size figure used in the episode.

The LLNL workshop's [startup script](../llnl-hpc-2026/startup.sh) creates
working copies from this folder, preserving any existing workshop files.
Figures remain here and are not copied.
