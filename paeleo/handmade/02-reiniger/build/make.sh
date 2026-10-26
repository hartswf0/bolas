#!/usr/bin/env bash
# Rebuild SCION-02 (Reiniger) from the kit and the score: stage -> exposure/rig -> picture -> sound -> mux -> measure.
set -euo pipefail
cd "$(dirname "$0")"
python3 stage.py                       # cut the static planes (cached masks)
python3 rig.py                         # read the score, derive acting channels, run the paw-contact solver
python3 render.py out/picture.mp4      # composite 912 frames (72 title + 768 scene + 72 end), measure the dog
python3 sound.py                       # synthesize the pit band from the cue sheet and the paw events
ffmpeg -loglevel error -y -i out/picture.mp4 -i out/sound.wav -c:v copy -c:a aac -b:a 192k \
       -movflags +faststart -shortest ../film.mp4
python3 check.py stills                # trace.json, exposure-sheet.csv, invariants, stills
