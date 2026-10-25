#!/bin/sh
# Rebuild SCION 05 Norstein from the kit and the score. ~40 min on 4 shared cores.
set -e
cd "$(dirname "$0")"
python3 world.py            # paint the glass planes; key the fog from the cloud footage
OMP_NUM_THREADS=1 python3 render.py   # the multiplane: 768 scene frames + per-frame measurements
python3 sound.py            # synthesize and spatialize the sound; measure levels
python3 scene.py            # export the scene graph and curves
python3 assemble.py         # cards, trace.json, stills, film.mp4
python3 ../../../../tools/paeleo/check_handmade.py ..
