#!/bin/sh
# SCION-24 · rebuild the film from the score: picture (rig + set rendered in Chromium canvas), measurements, sound, mux, stills, checks
set -e
H=$(cd "$(dirname "$0")" && pwd)
cd "$H"
node legcheck.js | head -1                 # planted paws within reach (no sliding through a clamped leg)
node keyform_test.js                       # head keyform table: interpolation error and lip/eye invariants
node sheet.js ../proof body,head,pose      # extreme-view diagnostics
node render.js                             # picture -> cache/picture.mp4, measurements -> cache/raw.json, cues -> cache/events.json
python3 measure.py > /dev/null             # trace.json, proof/onsets.json, proof/measures.json
python3 sound.py > /dev/null               # cache/sound.wav, proof/sound_levels.json
./assemble.sh                              # film.mp4
python3 stills.py                          # stills/
python3 ../../../../tools/paeleo/check_handmade.py ..
