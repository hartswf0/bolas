#!/bin/sh
# Render PAELEO-00 into OUTDIR: picture (render.js), sound (sound.py), then the film with loudness set to -18 LUFS.
# tools/paeleo/fonts must hold the site's three faces as woff2 with a local.css (see README.md).
set -e
OUT=$1; D=$(dirname "$0")
node "$D/render.js" "$OUT"
python3 "$D/sound.py" "$OUT"
ffmpeg -y -loglevel error -i "$OUT/picture.mp4" -i "$OUT/sound.wav" -c:v copy -af loudnorm=I=-18:TP=-1.5:LRA=11 -ar 44100 -c:a aac -b:a 160k -shortest -movflags +faststart "$OUT/paeleo-00.mp4"
