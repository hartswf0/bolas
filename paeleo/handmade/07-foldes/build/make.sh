#!/bin/sh
# SCION 07 · Foldès · rebuild the film from the score: keys -> registered sequence -> frames -> sound -> film, stills, proofs
set -e
cd "$(dirname "$0")"
python3 keys.py          # the key contour drawing set -> ../keys/
python3 solve.py         # registered morph sequence, foot solver, trace.json, topology
python3 render.py --clean
for i in 1 2 3 4 5 6 7 8; do python3 render.py --chunk 160; done   # frames in resumable chunks + cards -> cache/frames
test "$(ls cache/frames | wc -l)" -eq 912
python3 sound.py         # synthesized sound -> cache/film.wav, cache/levels.json
ffmpeg -y -loglevel error -framerate 24 -i cache/frames/%04d.png -i cache/film.wav \
  -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -tune animation -c:a aac -b:a 128k -ar 48000 \
  -movflags +faststart -shortest ../film.mp4
python3 proofs.py        # stills, key sheet, morph strips, before/after, extracted-frame checks
python3 ../../../../tools/paeleo/check_handmade.py ..
