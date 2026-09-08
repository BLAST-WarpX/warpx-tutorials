"""Run one WarpX collision from a rendered parameter file."""

from __future__ import annotations

import argparse

from pywarpx import warpx


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="Rendered WarpX parameter file")
    args = parser.parse_args()

    warpx.load_inputs_file(args.input_file)
    try:
        warpx.step()
    finally:
        warpx.finalize()


if __name__ == "__main__":
    main()

