#!/bin/sh
# SCION 40 · rebuild everything from the kit and the score. Run from anywhere.
set -e
cd "$(dirname "$0")"
python3 cards.py          # puppet fabricator: plate + skin cards, data/cards.json
python3 set.py            # layout sheet + finished set
python3 hands.py          # archive hands, matted and extended
python3 perform.py        # performers' sheet (ground truth for the synthesized plate only)
python3 plate.py          # synthesized overhead capture plate
python3 track.py          # tracking recovery from the plate's pixels -> data/tracked.json, events.jsonl
python3 track.py --eval   # tracking error against the synthesized truth
python3 render.py         # replay with skins from recovered data, trace.json, onsets
python3 sound.py          # voice + paper foley driven by the recovered events
python3 titles.py         # title and end cards
sh assemble.sh            # encode film.mp4, stills, clean frames
