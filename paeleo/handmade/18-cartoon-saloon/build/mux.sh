#!/bin/sh
# picture + sound -> film.mp4 (H.264 + AAC, faststart)
cd "$(dirname "$0")"
ffmpeg -y -loglevel error -i cache/picture.mp4 -i cache/audio.wav -c:v copy -c:a aac -b:a 128k -ar 48000 -shortest -movflags +faststart ../film.mp4
ls -la ../film.mp4
ffprobe -v error -show_entries format=duration:stream=codec_name,nb_frames -of compact ../film.mp4
