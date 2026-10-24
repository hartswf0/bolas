#!/bin/sh
# SCION-04 · rebuild the film from the kit and the score. Needs python3 (numpy, Pillow) and ffmpeg. About 10 minutes on 4 CPUs.
set -e
cd "$(dirname "$0")"
python3 01_library.py      # cut the archive shots into tiles (cache/library.*)
python3 02_render.py       # the 32 s scene, the torrent statistics, ../trace.json
python3 03_cards.py        # title and made-of cards
python3 04_sound.py        # synthesized sound from score + torrent statistics
python3 05_assemble.py     # ../film.mp4, ../stills, cache/invariants.json
python3 06_assets.py       # ../assets.json
