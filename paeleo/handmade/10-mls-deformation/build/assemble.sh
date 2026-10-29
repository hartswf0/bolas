#!/bin/sh
# SCION-10 · title (72) + scene (768) + end card (72) = 912 frames at 24 fps, with the synthesized sound -> ../film.mp4
set -e
H=$(cd "$(dirname "$0")" && pwd); cd "$H/cache/frames"
n=$(ls s_*.jpg | wc -l); [ "$n" -eq 768 ] || { echo "scene frames: $n (want 768)"; exit 1; }
ffmpeg -y -loglevel error -framerate 24 -i t_%04d.jpg -framerate 24 -i s_%04d.jpg -framerate 24 -i e_%04d.jpg -i ../sound.wav \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]" -map "[v]" -map 3:a \
  -c:v libx264 -preset slow -crf 23 -maxrate 2100k -bufsize 4200k -r 24 -c:a aac -b:a 128k -ar 48000 -t 38 \
  -movflags +faststart "$H/../film.mp4"
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,codec_name,width,height -of csv=p=0 "$H/../film.mp4"
ffprobe -v error -show_entries format=duration,size -of csv=p=0 "$H/../film.mp4"
