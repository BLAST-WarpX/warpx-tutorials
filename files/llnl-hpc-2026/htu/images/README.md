# Lesson figures: simulation output, not generated artwork

- `wake-density-evolution.png`: y=0 slices at steps 400, 800 and 1200 of the
  completed reduced 3D WarpX run. One common density scale, capped at
  8 × 10^25 m^-3 (higher values saturate). Coordinates z-ct follow the window.
- `htu-beam-density.png`: weighted transverse histograms at the source,
  TCPhosphor (s = 0.418 m), and ChicaneSlit (s = 1.463 m), for the independent
  synthetic 100 MeV and 20 MeV runs. Ranges change between panels; source
  axes are in µm, downstream axes in mm. Color is charge per bin, not a
  physical density normalized by the bin area. Labels give total surviving
  charge. No nonfinite particle coordinates are included or silently removed.
- `htu-transmission.png`: surviving charge and rms beam sizes from those
  ImpactX runs. The low-energy curve stops at the first nonfinite moments;
  the dotted line denotes invalid tracking, not complete physical loss.

Source runs were validated on 2026-09-18. Locally retained diagnostics:
`htu/runs/wake-validated-20260918/` and
`htu/runs/transport-fba4_h7l/comparison/`. Raw diagnostics are not shipped in
this download; each notebook generates fresh results.

To reproduce the figures with new run folders, from `htu/`:

```bash
python lwfa_warpx/plot_wakefield.py YOUR_WARPX_RUN/diags/diag1 \
  --evolution --output images/wake-density-evolution.png
```

For the ImpactX figures, run `htu_transport.ipynb`. Its analysis cells save
`beam_density.png` and `comparison.png` in the run folder. To analyze existing
results, set `run` to that folder and run the analysis cells without rerunning
the simulation.
