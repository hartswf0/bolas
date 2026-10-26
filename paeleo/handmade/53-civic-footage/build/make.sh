#!/usr/bin/env bash
# SCION 53 · rebuild the film from the copied archive sources and the score.
set -euo pipefail
cd "$(dirname "$0")"
ROOT=..
TMP=$(mktemp -d)
echo "1/5 picture (render.py -> ffmpeg) ..."
python3 render.py | ffmpeg -y -loglevel error -f rawvideo -pix_fmt rgb24 -s 1280x720 -r 24 -i - \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p "$TMP/picture.mp4"
echo "2/5 sound (sound.py, reads edl.json written by the render) ..."
python3 sound.py
echo "3/5 mux ..."
ffmpeg -y -loglevel error -i "$TMP/picture.mp4" -i audio.wav -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$ROOT/film.mp4"
echo "4/5 stills ..."
for t in 3.6 9 19 28; do
  n=$(python3 -c "print(f'{3.0+$t+0.5/24:.4f}')")
  ffmpeg -y -loglevel error -ss "$n" -i "$ROOT/film.mp4" -frames:v 1 -q:v 2 "$ROOT/stills/scene_$(printf '%05.2f' $t)s.jpg"
done
echo "5/5 check invariants ..."
python3 check.py
rm -rf "$TMP"
