#!/usr/bin/env bash
# SCION 32 · rebuild everything from the score: FK tests -> sound -> render (WebGL in headless Chromium) -> trace -> cards -> film
set -euo pipefail
cd "$(dirname "$0")"
node fktest.js          # transform test suite, foot slip, footfalls for the sound, angle curves for the end card
python3 sound.py        # synthesized sound, voice levels
node render.js scene    # 768 scene frames piped as JPEG into cache/scene.mp4, measurements into cache/measure.json
python3 trace.py        # ../trace.json from the render's own measurements
node render.js cards    # title and end cards
bash assemble.sh        # ../film.mp4 and ../stills
python3 ../../../../tools/paeleo/check_handmade.py ..
python3 proof.py        # proof images from the final film
