#!/bin/bash
cd /home/user/bolas/paeleo/scion/oulipo/films/sources/bang-bang/research
list=(
"magpie_XC537413.mp3|https://upload.wikimedia.org/wikipedia/commons/7/7e/Pica_pica_-_Eurasian_Magpie_XC537413.mp3"
"psm_d648_in_flight.jpg|https://upload.wikimedia.org/wikipedia/commons/d/d0/PSM_V46_D648_Lilienthal_flying_apparatus_in_flight.jpg"
"psm_d648_landing.jpg|https://upload.wikimedia.org/wikipedia/commons/8/8b/PSM_V46_D648_Lilienthal_flying_apparatus_the_landing.jpg"
"brehms1893_raben_full.jpg|https://upload.wikimedia.org/wikipedia/commons/1/10/Brehms_Tierleben%3B_allgemeine_kunde_des_thierreichs._Mit_1910_abbildungen_im_text%2C_11_karten_und_180_tafeln_in_farbendruck_und_holzschnitt._%281893%29_%2814784670385%29.jpg"
)
for it in "${list[@]}"; do
  f=${it%%|*}; u=${it#*|}
  for t in $(seq 1 12); do
    curl -sS -m 120 -A 'oulipo-film-research/1.0' -o "$f" "$u"
    if file -b "$f" | grep -q HTML; then echo "$(date +%T) 429 $f"; rm -f "$f"; sleep 75; else echo "$(date +%T) OK $f $(stat -c%s $f)"; break; fi
  done
  sleep 20
done
