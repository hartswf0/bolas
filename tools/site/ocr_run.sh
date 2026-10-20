#!/bin/bash
# one frame every STEP seconds of each film with production notes, OCR'd, so notes can be matched to the moment on screen.
# args: id:step ... ; resumes where a previous run stopped
cd "$(dirname "$0")"
for arg in "$@"; do
  id=${arg%%:*}; step=${arg##*:}; [ "$step" = "$id" ] && step=1
  [ -f $id.done ] && continue
  mkdir -p $id
  [ -f $id/.frames ] || { rm -f $id/*.png $id/*.txt; ffmpeg -v error -i /home/claude/bolas/media/films/$id.mp4 -vf "fps=1/$step,scale=640:-2" $id/%04d.png && touch $id/.frames; }
  ls $id/*.png | while read f; do [ -f $f.txt ] || echo $f; done | xargs -r -P 2 -I{} sh -c 'tesseract {} - --psm 11 2>/dev/null | tr "\n" " " > {}.txt'
  python3 -c "
import glob,json,os
d={(int(os.path.basename(f)[:4])-1)*$step:open(f).read() for f in glob.glob('$id/*.png.txt')}
json.dump(d,open('$id.json','w'))"
  rm -f $id/*.png; touch $id.done; echo "done $id"
done
echo ALL DONE
