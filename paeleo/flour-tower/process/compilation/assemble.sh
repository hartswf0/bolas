set -e
cd /home/claude/yt; mkdir -p seg
ENC="-c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r 30 -an"
card(){ # name file dur
  ffmpeg -y -v error -framerate 30 -i cards/$2.png -vf "format=yuv420p,loop=-1:1,trim=duration=$3,fade=t=in:st=0:d=0.5,fade=t=out:st=$(python3 -c "print($3-0.5)"):d=0.5,setpts=PTS-STARTPTS" $ENC seg/tmp_$1.mp4 && mv seg/tmp_$1.mp4 seg/$1.mp4; }
card a00 00-open 6
card a01 01-story 9
i=2
for f in 02-reiniger 06-whitney 07-foldes 08-sutherland 14-pose2pose 41-soft-body; do
  n=${f%%-*}; name=$(python3 -c "print({'02':'SCION 02 · REINIGER','06':'SCION 06 · WHITNEY','07':'SCION 07 · FOLDÈS','08':'SCION 08 · SUTHERLAND','14':'SCION 14 · POSE2POSE','41':'SCION 41 · SOFT BODY'}['$n'])")
  col=$(python3 -c "
from PIL import Image;im=Image.open('frames/$f/0000.jpg').convert('RGB');print('0x%02x%02x%02x'%im.getpixel((2,2)))")
  card b${i}a sw$n 4
  ffmpeg -y -v error -framerate 30 -i frames/$f/%04d.jpg -vf "scale=1920:1080:force_original_aspect_ratio=decrease:flags=lanczos,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=$col,drawtext=fontfile=/home/claude/yt/fonts/JetBrainsMono.ttf:text='$name':x=40:y=h-64:fontsize=24:fontcolor=white@0.85:box=1:boxcolor=0x0b0d10@0.55:boxborderw=10,fade=t=in:st=0:d=0.3,fade=t=out:st=31.7:d=0.3" $ENC -t 32 seg/tmp_b${i}b.mp4 && mv seg/tmp_b${i}b.mp4 seg/b${i}b.mp4
  i=$((i+1))
done
card z99 99-end 10
ls seg/*.mp4 | sort | sed "s#^seg/#file '#;s#\$#'#" > seg/list.txt
ffmpeg -y -v error -f concat -safe 0 -i seg/list.txt -c copy tmp_video.mp4
ffmpeg -y -v error -i tmp_video.mp4 -i score.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart tmp_final.mp4 && mv tmp_final.mp4 pae03-flour-tower.mp4
ffprobe -v error -show_entries format=duration,size -of default=nw=1 pae03-flour-tower.mp4
