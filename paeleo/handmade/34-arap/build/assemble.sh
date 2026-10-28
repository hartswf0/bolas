#!/bin/bash
# Title (72 frames) + scene (768 frames) + end card (72 frames) = 912 frames, 38.0 s; H.264 + AAC, faststart.
set -e
B=$(cd "$(dirname "$0")" && pwd); C=$B/cache; OUT=$B/../film.mp4
n=$(ls $C/frames/f*.jpg | wc -l); [ "$n" = 768 ] || { echo "scene frames: $n (want 768)"; exit 1; }
ffmpeg -y -loglevel error \
  -loop 1 -framerate 24 -t 3 -i $C/cards/title.png \
  -framerate 24 -i $C/frames/f%04d.jpg \
  -loop 1 -framerate 24 -t 3 -i $C/cards/end.png \
  -i $C/sound.wav \
  -filter_complex "[0:v]fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5,format=yuv420p[a];[1:v]format=yuv420p[b];[2:v]fade=t=in:st=0:d=0.5,format=yuv420p[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset slow -crf 23 -tune animation -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 128k -movflags +faststart -t 38 $OUT
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -of csv=p=0 $OUT
ls -la $OUT
