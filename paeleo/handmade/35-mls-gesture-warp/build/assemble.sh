#!/bin/bash
# title (3 s) + 768 scene frames (32 s) + end card (3 s) = 912 frames, 38.0 s; H.264 + AAC, faststart
set -e
cd "$(dirname "$0")"
CRF=${CRF:-27}
ffmpeg -y -loglevel error \
  -loop 1 -framerate 24 -t 3 -i cache/title.jpg \
  -framerate 24 -start_number 0 -i cache/frames/%04d.jpg \
  -loop 1 -framerate 24 -t 3 -i cache/end.jpg \
  -i cache/audio.wav \
  -filter_complex "[0:v]format=yuv420p,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];[2:v]format=yuv420p,setsar=1[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset slow -crf $CRF -tune grain -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 128k -t 38 -movflags +faststart ../film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -of csv=p=0 ../film.mp4
ls -l ../film.mp4
