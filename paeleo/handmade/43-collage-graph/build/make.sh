#!/bin/sh
# SCION 43 · Collage Graph Rewriting · rebuild the film from the kit and the score
set -e
cd "$(dirname "$0")"
python3 fonts.py            # house fonts -> ttf (cache)
python3 fragments.py        # archive forager + matte: cut every typed fragment (cache/frags, cache/frags.json, ../proof/fragments.jpg)
python3 render_all.py       # rule engine + compositor: 768 scene frames + per-frame measurements (cache/frames, cache/meas)
python3 trace.py            # ../trace.json (measured), ../graph_trace.json
python3 sound.py            # synthesized sound (cache/sound.wav) + measured levels
python3 cards.py            # title / end cards
python3 assemble.py         # ../film.mp4 (38.0 s), ../stills
python3 assets.py           # ../assets.json (source ledger)
python3 rulebook.py         # ../rulebook.json
python3 ../../../../tools/paeleo/check_handmade.py ..
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -of csv=p=0 ../film.mp4
