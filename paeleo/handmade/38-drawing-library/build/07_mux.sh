#!/bin/sh
# Mux picture + sound into film.mp4 (H.264 + AAC, 1280x720, 24 fps, 38 s)
set -e
D=$(cd "$(dirname "$0")/.." && pwd)
ffmpeg -y -loglevel error -i "$D/work/picture.mp4" -i "$D/work/sound.wav" -c:v copy -c:a aac -b:a 192k \
  -shortest -movflags +faststart "$D/film.mp4"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate:format=duration -of compact "$D/film.mp4"
