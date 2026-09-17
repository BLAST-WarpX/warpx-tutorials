#!/usr/bin/env python3
"""Run the HTU-inspired LWFA stage from a raw WarpX input file."""

from pywarpx import warpx

warpx.load_inputs_file("lwfa_warpx_input.txt")
warpx.step()
warpx.finalize()
