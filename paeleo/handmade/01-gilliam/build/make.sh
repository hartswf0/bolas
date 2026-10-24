#!/bin/sh
# SCION-01 (Gilliam) · PAE-02: rebuild the film from the kit, the found frames and the score.
set -e
cd "$(dirname "$0")"
python3 fetch_sources.py          # archivist: copy the found frames + masks into ../sources
python3 fonts.py                  # woff2 -> ttf
python3 assets.py                 # cutout surgeon: cut, engrave, pivot every card
python3 sound.py                  # sound editor: synthesize the track
python3 render.py cache/video.mp4       # director + mechanics: 72 title + 768 scene + 72 end frames; raw measurements
python3 check.py                  # trace.json + checks.json from the render's own measurements
python3 manifest.py               # assets.json
python3 render.py --stills        # stills/ at 3.6, 9, 19, 28 s
ffmpeg -y -loglevel error -i cache/video.mp4 -i cache/sound.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest ../film.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact ../film.mp4
