#!/usr/bin/env bash
# Builds the contaminant jelly film: frames from the page's render mode, sound from the run's events, then film.mp4 and stills.
# make.sh        the annotated cut  -> ../film.mp4, ../stills/
# make.sh mood   the textless cut   -> ../mood/film.mp4, ../mood/stills/ (archive frames instead of words)
set -euo pipefail
cd "$(dirname "$0")"
if [ "${1:-}" = mood ]; then export MOOD=1; tag=-mood; dir=../mood; else tag=; dir=..; fi
node render.js
node audio.js
ffmpeg -y -loglevel error -i "video$tag.mp4" -i "sound$tag.wav" -c:v copy -c:a aac -b:a 160k -ar 48000 -shortest "$dir/film.mp4"
mkdir -p "$dir/stills"
for t in 04.0 09.0 16.0 24.0 31.0 39.5; do
  ffmpeg -y -loglevel error -ss "$t" -i "$dir/film.mp4" -frames:v 1 -q:v 3 "$dir/stills/still_${t}s.jpg"
done
echo "$dir/film.mp4 and stills written"
