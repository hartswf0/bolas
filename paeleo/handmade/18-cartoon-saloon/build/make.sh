#!/bin/sh
# SCION 18 Cartoon Saloon: rebuild the film from the score (textures -> picture -> trace -> sound -> mux -> stills -> check)
set -e
cd "$(dirname "$0")"
python3 textures.py
node render.mjs
node gaitcheck.mjs
python3 trace.py
python3 sound.py
./mux.sh
python3 stills.py
python3 ../../../../tools/paeleo/check_handmade.py ..
