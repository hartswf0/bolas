#!/bin/bash
# Rebuild SCION 37 from the kit and the score:
# mesh + weights -> coat -> performance -> render (DQS) -> proof (LBS vs DQS, weights) -> sound -> cards -> film -> trace -> stills
set -e
cd "$(dirname "$0")"
python3 mesh.py dog person
python3 texture.py
python3 perform.py
rm -rf cache/frames cache/measure
./run_lanes.sh
python3 proof.py
python3 sound.py
python3 cards.py
./assemble.sh
python3 trace.py
python3 stills.py
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames          # rendered frames are regenerable; keep the folder lean
