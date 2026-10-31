#!/bin/bash
# title (3 s) + scene (768 frames) + end card (3 s) + sound -> film.mp4 (H.264 + AAC, faststart)
set -e
cd "$(dirname "$0")"
C=cache
ffmpeg -y -loglevel error \
  -loop 1 -framerate 24 -t 3 -i $C/cards/title.jpg \
  -framerate 24 -start_number 0 -i $C/frames/%04d.jpg \
  -loop 1 -framerate 24 -t 3 -i $C/cards/end.jpg \
  -i $C/film.wav \
  -filter_complex "[0:v]fade=t=out:st=2.6:d=0.4,format=yuv420p[a];[1:v]format=yuv420p[b];[2:v]fade=t=in:st=0:d=0.3,format=yuv420p[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -r 24 -c:a aac -b:a 128k -ar 48000 \
  -movflags +faststart -shortest ../film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 ../film.mp4
ls -la ../film.mp4
