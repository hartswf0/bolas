#!/bin/bash
# title (72 frames) + scene (768 frames) + end card (72 frames) -> ../film.mp4 (1280x720, 24 fps, H.264 + AAC, faststart)
set -e
cd "$(dirname "$0")"
n=$(ls cache/frames/*.jpg | wc -l); [ "$n" = 768 ] || { echo "scene frames: $n (need 768)"; exit 1; }
rm -rf cache/seq; mkdir -p cache/seq
python3 - <<'PY'
from PIL import Image
for name, a in (('title', 0), ('endcard', 840)):
    im = Image.open('cache/%s.png' % name).convert('RGB')
    for k in range(72): im.save('cache/seq/%04d.jpg' % (a + k), quality=95) if k == 0 else None
PY
for k in $(seq 1 71); do ln -sf 0000.jpg cache/seq/$(printf %04d $k).jpg; ln -sf 0840.jpg cache/seq/$(printf %04d $((840+k))).jpg; done
for k in $(seq 0 767); do ln -sf ../frames/$(printf %04d $k).jpg cache/seq/$(printf %04d $((72+k))).jpg; done
ffmpeg -y -loglevel error -framerate 24 -i cache/seq/%04d.jpg -i cache/scene.wav \
  -filter_complex "[1:a]adelay=3000|3000,apad=whole_dur=38,afade=t=in:st=0:d=2.5,afade=t=out:st=35.4:d=2.6[a]" \
  -map 0:v -map "[a]" -c:v libx264 -preset slow -crf ${CRF:-23} -pix_fmt yuv420p -r 24 -t 38 \
  -c:a aac -b:a 128k -movflags +faststart ../film.mp4
rm -rf cache/seq
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames,width,height,codec_name -of csv=p=0 ../film.mp4
ffprobe -v error -show_entries format=duration,size -of csv=p=0 ../film.mp4
