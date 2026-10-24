#!/bin/sh
# Rebuild everything from the Quick, Draw! files and the score.
#   01: stroke features + review contact sheets (the eye-picking was done on these sheets;
#       the picks are written down as LABELS in 02_library.py)
#   09, 10 (round 2), 11 (round 3): head-low pool sheets, stride-twin search, head-shape partner search
#   02: the pose-state library (copies the used drawings, key_id kept)
#   03: the dynamic-programming decoder (the decoded pose schedule)
#   04: the picture (title card, 768 scene frames, end card) + the render's own measurements
#   05: the sound
#   06: trace.json, checks.json, error histogram, schedule picture
#   07: mux to film.mp4
set -e
B=$(cd "$(dirname "$0")" && pwd)
python3 "$B/01_features.py"
python3 "$B/09_headlow_sheets.py"
python3 "$B/10_twin_search.py"
python3 "$B/11_head_partner.py"
python3 "$B/02_library.py"
python3 "$B/03_decode.py"
python3 "$B/04_render.py"
python3 "$B/05_sound.py"
python3 "$B/06_check.py" > /dev/null
python3 "$B/08_assets.py"
sh "$B/07_mux.sh"
# keep the folder lean: the picture-only and sound-only intermediates are not needed after the mux
rm -f "$B/../work/picture.mp4" "$B/../work/sound.wav"
