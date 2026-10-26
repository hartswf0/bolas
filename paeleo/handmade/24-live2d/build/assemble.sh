#!/bin/sh
# mux the rendered picture and the synthesized sound into film.mp4 (H.264 + AAC, faststart)
set -e
H=$(cd "$(dirname "$0")" && pwd)
ffmpeg -y -loglevel error -i "$H/cache/picture.mp4" -i "$H/cache/sound.wav" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 128k -ar 48000 -ac 2 -shortest -movflags +faststart "$H/../film.mp4"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$H/../film.mp4"
ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$H/../film.mp4"
