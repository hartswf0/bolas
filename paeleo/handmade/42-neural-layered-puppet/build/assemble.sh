#!/bin/bash
# title (3 s) + scene (768 frames, 32 s) + end card (3 s) + sound -> ../film.mp4 (H.264 + AAC, faststart)
set -e
cd "$(dirname "$0")"
n=$(ls cache/frames/s_*.jpg | wc -l)
[ "$n" -eq 768 ] || { echo "expected 768 scene frames, found $n"; exit 1; }
ffmpeg -y -loglevel error \
  -loop 1 -framerate 24 -t 3 -i cache/title.png \
  -framerate 24 -i cache/frames/s_%04d.jpg \
  -loop 1 -framerate 24 -t 3 -i cache/end.png \
  -i cache/sound.wav \
  -filter_complex "[0:v]format=yuv420p,fade=t=in:st=0:d=0.5,fade=t=out:st=2.6:d=0.4,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];[2:v]format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st=2.5:d=0.5,setsar=1[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset slow -crf 22 -maxrate 2000k -bufsize 4000k -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 128k -t 38 -movflags +faststart ../film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height -show_entries format=duration,size -of compact ../film.mp4
