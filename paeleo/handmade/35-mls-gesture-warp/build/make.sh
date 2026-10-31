#!/bin/bash
# SCION 35 · rebuild everything from code and the score
set -e
cd "$(dirname "$0")"
python3 dogprint.py          # the 13 view prints of the dog (print-space dot screens) + proof/view_prints.jpg
python3 personprint.py       # the person's two prints
python3 sound.py             # audio.wav + measured levels
python3 cards.py             # title and end card
rm -rf cache/frames cache/meas
./render_all.sh              # 768 scene frames (MLS warps, screen-space porch) + per-frame measurements
python3 measure.py           # ../trace.json, onsets measured from the render
./assemble.sh                # ../film.mp4
python3 stills.py            # ../stills/*.jpg and proof sheets, extracted from the encoded film
rm -rf cache/frames          # rendered frames are not kept (disk is shared)
python3 ../../../../tools/paeleo/check_handmade.py ..
