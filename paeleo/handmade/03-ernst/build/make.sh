#!/bin/sh
# SCION 03 Ernst · rebuild the film from the kit, the found frames and the score.
set -e
cd "$(dirname "$0")"
mkdir -p cache
python3 fonts.py                 # woff2 -> ttf (cache)
python3 fragments.py             # cut + engrave the found fragments (copies the source frames into ../src)
python3 timeline.py              # score -> poses, step solver
./render_all.sh                  # 768 scene frames (4 processes)
python3 sound.py                 # synthesized soundtrack + measured levels
python3 cards.py                 # title page and colophon
python3 assemble.py              # trace.json, frame sequence, stills
ffmpeg -y -loglevel error -framerate 24 -i cache/seq/f%05d.png -i cache/scene.wav \
  -c:v libx264 -preset slow -crf 23 -tune grain -pix_fmt yuv420p -c:a aac -b:a 128k -shortest \
  -movflags +faststart ../film.mp4
python3 ../../../../tools/paeleo/check_handmade.py ..
