#!/usr/bin/env bash
# SCION 09 · Igarashi — rebuild the film from the drawings, the score and the kit's Quick, Draw! picks.
# Run from anywhere: bash paeleo/handmade/09-igarashi/build/make.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(dirname "$HERE")"; CACHE="$HERE/cache"
mkdir -p "$CACHE" "$ROOT/stills" "$ROOT/proof"
cd "$ROOT"
node build/draw_assets.js            # source drawings -> assets/drawings/*.png
python3 build/mesh.py                # triangulated meshes + handles + feature-protect weights -> assets/mesh/*.json
node build/events.js                 # paw landings, sit, lie, tail thumps from the rig -> build/cache/events.json
python3 build/sound.py               # synthesized sound + flite voice -> build/cache/sound.wav
node build/render.js --film          # ARAP solve + render every frame -> build/cache/picture.mp4, build/cache/measure.json
python3 build/trace.py               # trace.json, diagnostics.json, measured onsets
ffmpeg -y -loglevel error -i "$CACHE/picture.mp4" -i "$CACHE/sound.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart film.mp4
for t in 03.6 09.0 19.0 28.0; do
  n=$(python3 -c "print(72 + round(float('$t') * 24))")
  ffmpeg -y -loglevel error -i "$CACHE/picture.mp4" -vf "select=eq(n\,$n)" -frames:v 1 -q:v 2 "stills/still_${t}s.jpg"
done
node build/proof.js                  # ARAP vs weighted skinning, meshes, handles -> proof/
python3 /home/user/bolas/tools/paeleo/check_handmade.py "$ROOT" || true
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -show_entries format=duration,size -of compact film.mp4
