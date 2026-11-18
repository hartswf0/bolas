#!/bin/bash
# Re-read Brehm p.265 licence from Commons extmetadata, backing off on 429.
OUT=/home/user/bolas/paeleo/scion/oulipo/films/sources/le-maki-mococo/imagecue
URL="https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|size|sha1|mime|extmetadata&titles=File:Brehm%27s_Life_of_animals_(Page_265)_(6220164475).jpg"
d=20
for i in 1 2 3 4 5 6 7; do
  sleep $d
  c=$(curl -sS -A "oulipo-film-research/1.0" "$URL" -o $OUT/brehm265_extmetadata.json -w "%{http_code}")
  echo "$(date -u +%FT%TZ) try $i http $c" >> $OUT/fetch_licence.log
  [ "$c" = "200" ] && exit 0
  d=$((d*2))
done
