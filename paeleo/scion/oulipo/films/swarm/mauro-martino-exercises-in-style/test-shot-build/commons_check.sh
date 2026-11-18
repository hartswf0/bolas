#!/bin/bash
# Re-verify licences via Commons extmetadata, with backoff on 429.
OUT=/home/user/bolas/paeleo/scion/oulipo/films/sources/mauro-martino-exercises-in-style/test-shot
q() { # $1 outfile, rest: curl args
  local o=$1; shift
  for i in 1 2 3 4 5 6 7 8; do
    c=$(curl -sS -A "oulipo-film-research/1.0" -G "https://commons.wikimedia.org/w/api.php" "$@" -d format=json -o "$o" -w "%{http_code}")
    [ "$c" = 200 ] && return 0
    sleep $((20*i))
  done; return 1
}
q $OUT/rol-meta.json --data-urlencode "titles=File:1-6-16, nouvel autobus Madeleine-Bastille - btv1b6946541g.jpg" -d action=query -d prop=imageinfo -d "iiprop=url|extmetadata|sha1"
sleep 5
q $OUT/audio-search.json -d action=query -d list=search -d srnamespace=6 --data-urlencode "srsearch=street traffic ambience filetype:audio" -d srlimit=40
sleep 5
q $OUT/audio-search2.json -d action=query -d list=search -d srnamespace=6 --data-urlencode "srsearch=bus engine idling filetype:audio" -d srlimit=30
sleep 5
q $OUT/audio-search3.json -d action=query -d list=search -d srnamespace=6 --data-urlencode "srsearch=tram bell filetype:audio" -d srlimit=30
echo done
