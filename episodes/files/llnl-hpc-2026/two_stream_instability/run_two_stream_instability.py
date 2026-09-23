#!/usr/bin/env python3
"""Run the 1D two-stream instability warm-up from a raw WarpX input file."""

from pywarpx import warpx

warpx.load_inputs_file("two_stream_instability_input.txt")
warpx.step()
warpx.finalize()
