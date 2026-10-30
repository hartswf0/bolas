#!/bin/sh
# SCION 20 · Toon Boom Harmony — Production Rig Foundry. Rebuild everything from the score:
#   01 drawing library + palette (vector drawings in code)      -> scene/library.json, scene/palette.json
#   02 exposure sheet from the score (+ track breakdown)          -> scene/xsheet.json, scene/xsheet.tsv, scene/track.json
#   03 node network as data, dependency test                     -> scene/nodegraph.json
#   sheet: model sheets of the library                            -> proof/library_*.jpg
#   render: evaluate the graph per frame in Chromium canvas       -> build/cache/frames/*.jpg, build/cache/measure.json
#   05 sound from the track breakdown                             -> build/cache/sound.wav
#   06 trace from the render's measurements, measured onsets      -> trace.json
#   07 assemble film.mp4, stills from the film, delete frames
#   08 assets.json ; then the PAELEO invariant check
set -e
B=$(cd "$(dirname "$0")" && pwd); D="$B/.."
node "$B/01_library.js"
python3 "$B/02_xsheet.py"
python3 "$B/03_graph.py"
node "$B/sheet.js"
node "$B/render.js"
python3 "$B/05_sound.py"
python3 "$B/06_trace.py"
sh "$B/07_assemble.sh"
python3 "$B/08_assets.py"
python3 "$B/09_regress.py"
cd "$D/../../.." && python3 tools/paeleo/check_handmade.py paeleo/handmade/20-harmony-rig
