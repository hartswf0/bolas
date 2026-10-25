#!/usr/bin/env bash
# Rebuild SCION 39 · Turn Lab from the score: plan → frames + measurements → trace → sound → film → stills → checks.
set -euo pipefail
cd "$(dirname "$0")/.."
B=build; C=build/cache
node $B/controller.js                       # orientation controller: score → plan.json
node $B/render.js                           # drawing atlas → frames, id-mask measurements
python3 $B/trace.py                         # trace.json from the measurements
python3 $B/sound.py                         # synthesized sound + measured levels
python3 $B/assemble.py                      # film.mp4, stills
python3 $B/identity_loop.py                 # identity-continuity loop + reviewer frame index
python3 ../../../tools/paeleo/check_handmade.py .
