#!/usr/bin/env bash
# Populate workshop working copies without replacing any existing path.
set -euo pipefail

workshop_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
materials_dir=$(dirname -- "$workshop_dir")
sources=(
    laser-wakefield/wakefield.ipynb
    laser-wakefield/warpx_helpers.py
    laser-wakefield/lwfa_warpx_input.txt
    laser-wakefield/run_lwfa_warpx.py
    beam-transport/htu_transport.ipynb
    beam-transport/impactx_helpers.py
)
destinations=(
    htu/lwfa_warpx/wakefield.ipynb
    htu/lwfa_warpx/warpx_helpers.py
    htu/lwfa_warpx/lwfa_warpx_input.txt
    htu/lwfa_warpx/run_lwfa_warpx.py
    htu/beamline_impactx/htu_transport.ipynb
    htu/beamline_impactx/impactx_helpers.py
)

# Check all needed sources before creating any working copies.
for i in "${!sources[@]}"; do
    destination="$workshop_dir/${destinations[i]}"
    if [[ -e "$destination" || -L "$destination" ]]; then
        continue
    fi
    if [[ ! -f "$materials_dir/${sources[i]}" ]]; then
        printf 'Missing source: %s\n' "$materials_dir/${sources[i]}" >&2
        printf 'Include episodes/files/laser-wakefield and episodes/files/beam-transport in your checkout.\n' >&2
        exit 1
    fi
done

for i in "${!sources[@]}"; do
    destination="$workshop_dir/${destinations[i]}"
    if [[ -e "$destination" || -L "$destination" ]]; then
        printf 'Keeping %s\n' "${destinations[i]}"
        continue
    fi
    mkdir -p -- "$(dirname -- "$destination")"
    cp -- "$materials_dir/${sources[i]}" "$destination"
    printf 'Prepared %s\n' "${destinations[i]}"
done
printf 'Workshop files are ready. Existing files were left untouched.\n'
