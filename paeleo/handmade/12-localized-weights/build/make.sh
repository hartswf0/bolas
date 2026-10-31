#!/bin/bash
# Rebuild PAE-02 / SCION 12 from nothing but this folder, the score and the shared fonts.
# Needs: python3 with numpy, Pillow, scipy, triangle, shapely, fontTools+brotli; ffmpeg.
set -e
# packages: pip install triangle shapely   (scipy, numpy, Pillow, fontTools, brotli were already installed here)
python3 -c "import triangle, shapely" 2>/dev/null || pip install triangle shapely
cd "$(dirname "$0")"
mkdir -p cache/fonts cache/frames cache/meas cache/cards
python3 - <<'PY'
from fontTools.ttLib import TTFont
import glob, os
for f in glob.glob('../../../../tools/paeleo/fonts/*.woff2'):
    out = 'cache/fonts/' + os.path.basename(f).replace('.woff2', '.ttf')
    if not os.path.exists(out):
        t = TTFont(f); t.flavor = None; t.save(out)
PY
python3 proof.py > /dev/null           # solve weights, run the numerical tests, heat maps (proof/)
python3 -c "import rig, person; rig.load(); person.load()"   # cache the weights the renderer uses
python3 sound.py                        # cache/film.wav and cache/levels.json
python3 cards.py                        # title and end card
PIDS=""
for r in "0 192" "192 384" "384 576" "576 768"; do
  set -- $r
  OMP_NUM_THREADS=1 python3 render.py $1 $2 & PIDS="$PIDS $!"
done
wait $PIDS
test "$(ls cache/frames/*.jpg | wc -l)" = 768
python3 trace.py
./assemble.sh
python3 stills.py
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -f cache/frames/*.jpg               # keep the folder lean; frames are regenerable
