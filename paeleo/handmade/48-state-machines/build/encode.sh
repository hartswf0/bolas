#!/bin/bash
# assemble 72 title + 768 scene + 72 end frames (912) with the sound into ../film.mp4 (H.264 + AAC, faststart, <= 12 MB)
set -e
cd "$(dirname "$0")"
rm -rf cache/seq && mkdir -p cache/seq
k=0
for f in $(ls cache/frames/t*.jpg | sort) $(ls cache/frames/s*.jpg | sort) $(ls cache/frames/e*.jpg | sort); do
  ln -s "../frames/$(basename $f)" "cache/seq/$(printf %04d $k).jpg"; k=$((k+1))
done
echo "frames: $k"
[ "$k" -eq 912 ] || { echo "frame count wrong ($k)"; exit 1; }
for crf in 23 25 27 29 31; do
  ffmpeg -y -loglevel error -framerate 24 -i cache/seq/%04d.jpg -i cache/sound.wav -map 0:v -map 1:a \
    -c:v libx264 -preset slow -crf $crf -pix_fmt yuv420p -r 24 -c:a aac -b:a 160k -movflags +faststart -shortest ../film.mp4
  sz=$(stat -c %s ../film.mp4)
  echo "crf $crf -> $sz bytes"
  [ "$sz" -le 11800000 ] && break
done
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,codec_name,width,height,r_frame_rate -show_entries format=duration -of compact ../film.mp4
