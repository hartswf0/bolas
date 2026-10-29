#!/bin/bash
# SCION 15 - rebuild everything from the kit and the score. Needs python3 + numpy + scipy + Pillow, ffmpeg (with libflite).
set -e
B="$(cd "$(dirname "$0")" && pwd)"; cd "$B"; mkdir -p cache
python3 template.py                 # layered template from f006
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 fit.py 0 25 & J1=$!; python3 fit.py 49 24 & J2=$!; wait $J1 $J2   # render-loss fits, two resumable chunks
python3 fit.py 17 33 & J1=$!; python3 fit.py 49 32 & J2=$!; wait $J1 $J2  # refit 17-49 with multi-start (as built)
python3 fit.py merge
python3 fitsheet.py
python3 learn.py                    # view latent, shape regression, appearance atlases, held-out evaluation
python3 render.py 0 256 & P1=$!; python3 render.py 256 512 & P2=$!; python3 render.py 512 768 & P3=$!
wait $P1 $P2 $P3
python3 assemble.py                 # trace.json with measured onsets
python3 sound.py                    # sound (reads trace.json for the uncertainty tone)
python3 proof_raw.py                # model alone vs film
python3 cards.py
./encode.sh
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames cache/frames_raw cache/cards   # keep the shared disk lean
