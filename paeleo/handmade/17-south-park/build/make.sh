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
python3 render.py                  # frames -> build/cache/video.mp4, trace.json, stills
ffmpeg -y -loglevel error -i "$B/cache/video.mp4" -i "$B/cache/sound.wav" -c:v copy -c:a aac -b:a 160k -shortest -movflags +faststart "$F/film.mp4"
python3 ../../../../tools/paeleo/check_handmade.py "$F"
