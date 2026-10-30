#!/usr/bin/env bash
# Builds the contaminant jelly film: frames from the page's render mode, sound from the run's events, then film.mp4 and stills.
set -euo pipefail
cd "$(dirname "$0")"
node render.js
node audio.js
ffmpeg -y -loglevel error -i video.mp4 -i sound.wav -c:v copy -c:a aac -b:a 160k -ar 48000 -shortest ../film.mp4
mkdir -p ../stills
for t in 04.0 09.0 16.0 24.0 31.0; do
  ffmpeg -y -loglevel error -ss "$t" -i ../film.mp4 -frames:v 1 -q:v 3 "../stills/still_${t}s.jpg"
done
echo "film.mp4 and stills written"
