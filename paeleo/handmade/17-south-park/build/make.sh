#!/bin/sh
# SCION 17 // rebuild the film from the kit and the score. Run from anywhere.
set -e
B="$(cd "$(dirname "$0")" && pwd)"; F="$B/.."
mkdir -p "$B/cache" "$F/stills" "$F/proof"
cd "$B"
python3 qd_pick.py                 # copy the Quick, Draw! drawings used (key_ids) into assets/
python3 sheet_dog.py               # cast bible: Biscuit's direction states and expressions
python3 sheet_person.py            # cast bible: Maren's postures and mouth atlas
python3 sound.py                   # synthesized voice + foley, cut to the director's events
rm -f "$B"/cache/seg_*.mp4 "$B"/cache/trace_*.json
python3 render.py --cards-seg       # title and end cards
a=0; while [ $a -lt 768 ]; do python3 render.py --range $a $((a+96)); a=$((a+96)); done   # scene in chunks (one process each)
python3 render.py --assemble        # -> build/cache/video.mp4, trace.json
ffmpeg -y -loglevel error -i "$B/cache/video.mp4" -i "$B/cache/sound.wav" -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "$F/film.mp4"
python3 ../../../../tools/paeleo/check_handmade.py "$F"
