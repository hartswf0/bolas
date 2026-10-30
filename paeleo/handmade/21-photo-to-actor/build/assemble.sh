#!/bin/bash
# title (3 s) + scene (768 frames) + end card (3 s) -> film.mp4 (H.264 + AAC, faststart, 912 frames)
set -e
cd "$(dirname "$0")/.."
C=build/cache
# 38 s soundtrack: room tone fades in under the title, the scene, then a tail under the end card
ffmpeg -hide_banner -loglevel error -y -i $C/scene.wav -af "adelay=3000,apad=whole_dur=38,afade=t=in:st=2.2:d=0.8,afade=t=out:st=35.6:d=2.2" -ar 48000 -ac 1 $C/film.wav
ffmpeg -hide_banner -loglevel error -y \
  -loop 1 -framerate 24 -t 3 -i $C/title.jpg \
  -framerate 24 -start_number 0 -i $C/frames/%04d.jpg \
  -loop 1 -framerate 24 -t 3 -i $C/endcard.jpg \
  -i $C/film.wav \
  -filter_complex "[0:v]fps=24,format=yuv420p,setsar=1[a];[1:v]fps=24,format=yuv420p,setsar=1[b];[2:v]fps=24,format=yuv420p,setsar=1[c];[a][b][c]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map 3:a -c:v libx264 -preset medium -crf ${CRF:-26} -pix_fmt yuv420p -r 24 \
  -c:a aac -b:a 160k -movflags +faststart -shortest film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,codec_name -of csv=p=0 film.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 film.mp4
