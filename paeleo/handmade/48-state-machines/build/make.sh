#!/bin/bash
# SCION-48 · rebuild everything from the score: machine -> board render -> cards/captions -> sound -> trace -> film -> stills -> check
# (python3 tune.py re-tunes the machine against the score and rewrites tuned.json; it is not run by default)
set -e
cd "$(dirname "$0")"
python3 machine.py
./render_all.sh
python3 cards.py
python3 sound.py
python3 trace.py
./encode.sh
./stills.sh
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames cache/seq          # the rendered frames are regenerable; keep the folder lean
