#!/usr/bin/env bash
# SCION-27 · rebuild the film from the kit and the score. bash paeleo/handmade/27-remotion/build/make.sh
set -euo pipefail
B="$(cd "$(dirname "$0")" && pwd)"; F="$(dirname "$B")"; ROOT="$(cd "$F/../../.." && pwd)"
mkdir -p "$B/cache/deps" "$B/cache/public/fonts"
if [ ! -d "$B/cache/deps/node_modules/@remotion/renderer" ]; then
  cp "$B/package.json" "$B/cache/deps/package.json"
  (cd "$B/cache/deps" && npm install --no-audit --no-fund)
fi
cp "$ROOT"/tools/paeleo/fonts/*.woff2 "$B/cache/public/fonts/"
node --experimental-strip-types "$B/solve.ts"          # score → typed manifest + audio event list
python3 "$B/sound.py"                                   # audio events → mix.wav + ../audio.json
node "$B/render.mjs" film matte stills                  # Remotion: Film, DogMatte, four stills
python3 "$B/measure.py"                                 # matte → ../trace.json (measured)
ffmpeg -y -loglevel error -i "$B/cache/film_raw.mp4" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p \
  -c:a aac -b:a 160k -movflags +faststart "$F/film.mp4"
node "$B/repro.mjs"                                     # determinism: re-render frames, compare hashes with the film's
python3 "$ROOT/tools/paeleo/check_handmade.py" "$F"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -show_entries format=duration -of compact "$F/film.mp4"
