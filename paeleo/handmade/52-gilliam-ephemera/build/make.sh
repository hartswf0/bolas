#!/bin/sh
# Rebuild the film from the kit and the score. Intermediates go to build/cache/ (regenerable).
set -e
B=$(cd "$(dirname "$0")" && pwd)
cd "$B"
python3 cut_pieces.py          # cut every piece from its source print -> cache/pieces, proof/cutting_sheet.jpg
python3 voice.py               # the voice takes and the mouth chart read from them
python3 xsheet.py              # the exposure sheet -> ../xsheet.json
rm -f cache/frames/*.jpg
python3 render.py              # shoot the exposures -> cache/frames/s*.jpg, ../trace.json
python3 cards.py               # title and end cards
python3 sound.py               # the track -> cache/sound.wav, proof/sound_levels.json
python3 measure.py > /dev/null # measured onsets etc. -> proof/measured.json
python3 stills.py              # ../stills/
./assemble.sh                  # ../film.mp4
n=$(ls cache/frames | grep -c '^s'); echo "scene frames: $n (expect 768)"
python3 ../../../../tools/paeleo/check_handmade.py ..
