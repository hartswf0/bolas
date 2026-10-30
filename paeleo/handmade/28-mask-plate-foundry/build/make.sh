#!/bin/sh
# Rebuild SCION 28 from the kit sources and the score. Run from anywhere.
set -e
cd "$(dirname "$0")"
python3 plates.py                 # clean plates, keys, rotos  -> cache/plates
python3 sound.py                  # synthesized sound          -> cache/audio.wav
python3 render.py --film cache/video.mp4   # title + 768 scene frames + end card, piped to x264 (no frames on disk)
ffmpeg -loglevel error -y -i cache/video.mp4 -i cache/audio.wav -c:v copy -c:a aac -b:a 160k -shortest \
       -movflags +faststart ../film.mp4
rm -f cache/video.mp4
python3 trace.py                  # measurements from the encoded film + render mattes -> trace.json, stills, checks
python3 ../../../../tools/paeleo/check_handmade.py ..
