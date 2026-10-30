#!/bin/bash
# encode: 3 s title + 32 s scene (768 frames) + 3 s end card = 912 frames; H.264 + AAC, faststart; then delete the frames
set -e
cd "$(dirname "$0")"
C=cache
n=$(ls $C/frames/s_*.jpg | wc -l); [ "$n" = 768 ] || { echo "scene frames: $n (want 768)"; exit 1; }
mkdir -p $C/seq
for k in $(seq 0 71); do ln -sf ../title.jpg $C/seq/f_$(printf %04d $k).jpg; done
for k in $(seq 0 767); do ln -sf ../frames/s_$(printf %04d $k).jpg $C/seq/f_$(printf %04d $((k+72))).jpg; done
for k in $(seq 0 71); do ln -sf ../end.jpg $C/seq/f_$(printf %04d $((k+840))).jpg; done
ffmpeg -y -loglevel error -f lavfi -i anullsrc=r=48000:cl=stereo -t 3 $C/sil.wav
ffmpeg -y -loglevel error -i $C/sil.wav -i $C/scene.wav -i $C/sil.wav -filter_complex "[0][1][2]concat=n=3:v=0:a=1,afade=t=in:d=0.3,afade=t=out:st=37.4:d=0.6[a]" -map "[a]" $C/film.wav
ffmpeg -y -loglevel error -framerate 24 -i $C/seq/f_%04d.jpg -i $C/film.wav -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -tune animation \
  -c:a aac -b:a 128k -movflags +faststart -shortest ../film.mp4
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height,codec_name -show_entries format=duration,size -of compact ../film.mp4
