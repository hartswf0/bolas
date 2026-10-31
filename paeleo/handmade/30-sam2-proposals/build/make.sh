#!/bin/sh
# Rebuild SCION 30 / SAM 2 from the kit and the score. Run from anywhere; needs python3 (numpy, Pillow) and ffmpeg.
set -e
cd "$(dirname "$0")"
python3 proposals.py      # proposals, confidence proxy, object IDs, our person proposals -> cache/proposals.json
python3 sound.py          # synthesized sound -> cache/sound.wav, cache/sound_levels.json
python3 film.py           # 912 frames -> cache/picture.mp4 (frames are piped, never written), trace.json
python3 finish.py         # film.mp4, stills/, proposals/, assets.json
python3 ../../../../tools/paeleo/check_handmade.py ..
