#!/bin/sh
# SCION-10 · rebuild everything from the score: the hide, the MLS tests, the handle trajectories, the picture, the
# measurements, the sound, the cards, the film, the stills, the proofs, and the PAELEO invariant check.
set -e
H=$(cd "$(dirname "$0")" && pwd); cd "$H"
python3 paint_dog.py                    # ../assets/dog_hide.png: the one image the dog is made of
python3 mls.py > ../proof/mls_selftest.json   # numerical invariants of the MLS solver (handles hit targets, identity, rigid motion)
python3 pose.py                         # cache/poses.json: per frame, where every handle goes; cache/footfalls.json
python3 render.py                       # cache/frames/s_*.jpg (768) and cache/raw/*.json (measured from each frame)
python3 measure.py                      # ../trace.json, ../proof/onsets.json
python3 sound.py                        # cache/sound.wav, ../proof/sound_levels.json
python3 cards.py                        # title and end card frames, ../proof/endcard.jpg, handles_on_hide.jpg, variants_strip.jpg
python3 strips.py                       # ../proof/*_strip.jpg: weight exponent, the turns, the lie-down, the look-in
./assemble.sh                           # ../film.mp4 (912 frames, 38.0 s)
python3 stills.py                       # ../stills/
rm -f cache/frames/*.jpg                # the shared disk: frames are regenerable
python3 ../../../../tools/paeleo/check_handmade.py ..
