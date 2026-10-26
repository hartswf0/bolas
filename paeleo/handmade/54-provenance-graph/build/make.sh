#!/bin/sh
# Rebuild SCION 54 Provenance Graph from the kit, the found frames, Quick, Draw! and the score.
# Python 3 + numpy + Pillow, ffmpeg. ~10 min on 4 cores.
set -e
cd "$(dirname "$0")"
python3 assets.py          # sources -> derivative DAG (lineage/lineage.json, node cache in build/cache/nodes)
python3 render.py          # score -> layers per frame (lineage/render_deps.jsonl.gz) -> frames + measured trace.json
python3 sound.py           # synthesised sound from the score and the render's foot contacts (lineage/sound.json)
python3 cards.py           # title and end card, frame sequence
cd ..
ffmpeg -y -loglevel error -framerate 24 -i build/cache/seq/%04d.png -i build/cache/sound.wav \
  -c:v libx264 -preset slow -crf 23 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart -shortest film.mp4
cd build
python3 stills.py          # stills/ and proof/ sheets
python3 report.py          # assets.json, lineage/permissions.json, lineage/schema.json
python3 audit.py           # lineage/audit.json: lineage, re-execution from sources, rights, render deps, rebuilt shot
python3 ../../../../tools/paeleo/check_handmade.py ..
