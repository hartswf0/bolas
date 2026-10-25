#!/bin/sh
# assembles film.mp4: 3 s title + 768 scene frames (score-aligned) + 3 s end card; sound: scene.wav placed at 3 s
set -e
cd "$(dirname "$0")"
OUT=..
N=$(ls cache/frames/s*.jpg | wc -l)
[ "$N" -eq 768 ] || { echo "expected 768 scene frames, found $N"; exit 1; }
ffmpeg -y -loglevel error -loop 1 -t 3 -framerate 24 -i cache/cards/title.png \
  -framerate 24 -i cache/frames/s%04d.jpg \
  -loop 1 -t 3 -framerate 24 -i cache/cards/end.png \
  -i cache/scene.wav \
  -filter_complex "[0:v]fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5,format=yuv420p[a];[1:v]format=yuv420p[b];[2:v]fade=t=in:st=0:d=0.5,format=yuv420p[c];[a][b][c]concat=n=3:v=1:a=0[v];[3:a]adelay=3000|3000,apad,atrim=0:38,afade=t=in:st=2.6:d=0.4,afade=t=out:st=36.5:d=1.5[aud]" \
  -map "[v]" -map "[aud]" -r 24 -c:v libx264 -preset slow -crf 27 -tune animation -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart -t 38 $OUT/film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height,r_frame_rate -of csv=p=0 $OUT/film.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 $OUT/film.mp4
