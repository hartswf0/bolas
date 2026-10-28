#!/bin/bash
# SCION 42 · rebuild everything from the kit and the score.
#   sweep.sh  : number of layers chosen by held-out IoU (8 fits; slow, ~15 min on 4 cores; results kept in data/sweep)
#   fit.py    : few-shot layer discovery, hinges, held-out test against the controls  -> model/puppet.npz
#   library.py: the source dog's walks re-fitted to the learned layers                -> model/library.npz
#   cards.py, scene.py (768 frames), trace.py, sound.py, assemble.sh                  -> film.mp4, trace.json
set -e
cd "$(dirname "$0")"
mkdir -p cache
[ "$1" = "--sweep" ] && ./sweep.sh
PUPPET_K=8 python3 fit.py      # K fixed at 8: see data/model_selection.json
python3 library.py
python3 cards.py
rm -rf cache/frames
python3 scene.py
python3 trace.py
python3 sound.py cache/perform_sound.json
./assemble.sh
python3 stills.py
rm -rf cache/frames          # keep the folder lean: frames are regenerable
cd ../../../.. && python3 tools/paeleo/check_handmade.py paeleo/handmade/42-neural-layered-puppet
