#!/bin/bash
# SCION 15 - rebuild everything from the kit and the score. Needs python3 + numpy + scipy + Pillow, ffmpeg (with libflite).
set -e
B="$(cd "$(dirname "$0")" && pwd)"; cd "$B"; mkdir -p cache
python3 template.py                 # layered template from f006
python3 fit.py                      # render-loss fits of all 50 archive frames (slow: ~10-40 min)
python3 fitsheet.py
python3 learn.py                    # view latent, shape regression, appearance atlases, held-out evaluation
python3 render.py 0 384 & P1=$!     # the scene, two halves in parallel
python3 render.py 384 768 & P2=$!
wait $P1 $P2
python3 assemble.py                 # trace.json with measured onsets
python3 sound.py                    # sound (reads trace.json for the uncertainty tone)
python3 proof_raw.py                # model alone vs film
python3 cards.py
./encode.sh
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames cache/frames_raw cache/cards   # keep the shared disk lean
