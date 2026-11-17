#!/bin/bash
cd /home/user/bolas/paeleo/scion/oulipo/films/sources/boucle-la/test-shot
UA="oulipo-film-research/1.0"
get(){ for i in 1 2 3 4 5; do sleep $((60*i)); curl -sS -A "$UA" -o "$1" "$2"; if ! file "$1" | grep -q HTML; then echo ok $1; return; fi; echo retry $1; done; }
get audio/ghanta.wav "https://upload.wikimedia.org/wikipedia/commons/c/cf/274316_the-very-real-horst_ghanta-leather-mallet-2015-05-16.wav"
get audio/paper-pages.ogg "https://upload.wikimedia.org/wikipedia/commons/7/79/Book_paper_pages_assorted.ogg"
get daumier-orig.jpg "https://upload.wikimedia.org/wikipedia/commons/7/79/Echtpaar_bespreekt_huishoudelijke_financi%C3%ABn_in_de_slaapkamer_Et_les_cinq_francs_de_ce_matin_%28..%29_%28titel_op_object%29_Gezinssituaties_%28serietitel%29_Moeurs_conjugales_%28serietitel_op_object%29%2C_RP-P-OB-41.183.jpg"
for i in 1 2 3; do sleep 90; t="File:Echtpaar bespreekt huishoudelijke financiën in de slaapkamer Et les cinq francs de ce matin (..) (titel op object) Gezinssituaties (serietitel) Moeurs conjugales (serietitel op object), RP-P-OB-41.183.jpg"; curl -sS -A "$UA" --get "https://commons.wikimedia.org/w/api.php" --data-urlencode "action=query" --data-urlencode "format=json" --data-urlencode "titles=$t" --data-urlencode "prop=imageinfo" --data-urlencode "iiprop=url|size|extmetadata" --data-urlencode "iiextmetadatafilter=LicenseShortName|LicenseUrl|Artist|Credit|ObjectName|DateTimeOriginal|UsageTerms" > daumier-meta.json; if head -c 1 daumier-meta.json | grep -q '{'; then echo meta ok; break; fi; done
echo done
