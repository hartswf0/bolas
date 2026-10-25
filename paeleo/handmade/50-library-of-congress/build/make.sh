#!/bin/sh
# Rebuild PAE-02 · SCION 50 from the kit and the score. Run from anywhere.
set -e
B="$(cd "$(dirname "$0")" && pwd)"; F="$(dirname "$B")"
cd "$B"
python3 fonts.py              # woff2 → ttf for PIL (cache)
python3 plates_dog.py         # fig. 1: f006 traced into 11 cut pieces, documented turn frames; engraved
python3 world.py              # pl. I: the section of the house and porch, the door leaf (Straight Talk f030)
python3 person.py             # fig. 2: drawn figure, hand after Door to Heaven f000
python3 render.py --stills    # 912 frames → cache/video.mp4, measure.json, events.json, stills/
python3 trace.py              # trace.json from the measured dog layer
python3 sound.py              # cache/audio.wav and sound.json, from the logged events
ffmpeg -y -loglevel error -i cache/video.mp4 -i cache/audio.wav -c:v copy -c:a aac -b:a 160k -movflags +faststart -shortest "$F/film.mp4"
python3 "$F/../../../tools/paeleo/check_handmade.py" "$F"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height,r_frame_rate -show_entries format=duration,size -of compact "$F/film.mp4"
