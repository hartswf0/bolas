#!/bin/bash
# SCION 45 · Occlusion Compositing: rebuild the film from the kit and the score.
# Needs python3 (numpy, Pillow), ffmpeg (with flite). PROCS sets parallel render workers (default 3).
set -euo pipefail
cd "$(dirname "$0")"
python3 cels.py          # the dog: RGBA cels from the archive frames (SAM x garbage mattes)
python3 plates.py        # hallway, door leaf, bulb, sky, hand
python3 sound.py         # voice (flite), foley, dusk, the room held out by the door -> cache/scene_audio.wav
PROCS=${PROCS:-3} python3 render.py   # 768 scene frames + per-frame records (DAG, passes, measurements)
python3 measure.py       # trace.json, measured.json (onsets, occlusion assertions, overlap events)
python3 assets.py        # assets.json, cache/cels_used.json
python3 cards.py         # title and end cards
python3 assemble.py film stills proof   # film.mp4 (38 s), stills/, proof/
python3 ../../../../tools/paeleo/check_handmade.py ..
python3 assemble.py operator   # operator page with the measured state
