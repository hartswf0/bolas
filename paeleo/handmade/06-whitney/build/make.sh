#!/usr/bin/env bash
# SCION 06 · Whitney — rebuild the film from the score. Run from anywhere.
set -euo pipefail
B="$(cd "$(dirname "$0")" && pwd)"; D="$(dirname "$B")"; C="$B/cache"
mkdir -p "$C" "$D/stills" "$D/proof"
cd "$B"
python3 fonts.py
python3 render.py            # build/cache/scene.mp4 + ../trace.json (measured from the drawn points)
python3 audio.py             # build/cache/audio.wav + ../proof/audio.json
python3 cards.py             # build/cache/title.mp4, end.mp4
python3 phase.py             # ../proof/phase.json + phase.png (the 3:2 lock, measured; A/B against drift)
printf "file '%s'\nfile '%s'\nfile '%s'\n" "$C/title.mp4" "$C/scene.mp4" "$C/end.mp4" > "$C/list.txt"
ffmpeg -y -loglevel error -f concat -safe 0 -i "$C/list.txt" -i "$C/audio.wav" -map 0:v -map 1:a \
  -c:v libx264 -preset slow -crf 27 -maxrate 2.3M -bufsize 4.6M -pix_fmt yuv420p -c:a aac -b:a 128k \
  -movflags +faststart -shortest "$D/film.mp4"
for t in 03.6 09.0 19.0 28.0; do
  ffmpeg -y -loglevel error -i "$C/scene.mp4" -ss "$t" -frames:v 1 -q:v 2 "$D/stills/still_${t}s.jpg"
done
python3 ../../../../tools/paeleo/check_handmade.py "$D"
ls -la "$D/film.mp4"
