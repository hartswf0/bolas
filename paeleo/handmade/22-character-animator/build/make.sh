#!/bin/sh
# SCION 22 · rebuild everything from the score (no kit pixels are used; every asset is drawn or synthesized here)
set -e
cd "$(dirname "$0")"
python3 takes.py           # ../takes.json: capture take (score) + trigger, turner, gaze and person takes
python3 voice.py           # formant-synthesized voice -> cache/voice.wav
python3 visemes.py         # visemes computed from the voice audio -> ../puppet/visemes.json
python3 rig.py             # the puppet runtime: behaviours evaluated per frame -> cache/rig.pkl, ../puppet/puppets.json
python3 render.py bg       # the felt set, drawn once in world metres
./render_all.sh            # 768 scene frames (checks the count)
python3 sound.py           # synthesized sound mix + measured levels
python3 cards.py           # title / end card
./assemble.sh              # ../film.mp4 (checks 912 frames)
python3 measure.py         # ../trace.json with measured onsets
python3 stills.py          # ../stills, ../proof (extracted from film.mp4)
python3 ../../../../tools/paeleo/check_handmade.py ..
rm -rf cache/frames cache/seq cache/measure   # keep the folder lean (frames are regenerable)
