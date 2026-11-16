# edit-r2: add the newly used foraged items to films/credits/la-mort-en-ce-jardin.json (licences read live from Commons
# extmetadata on 2026-11-16; raw API answers saved under sources/la-mort-en-ce-jardin/edit/meta/).
import json, os, sys
SW = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
CR = os.path.join(FILMS, "credits", "la-mort-en-ce-jardin.json")
SOUND = json.load(open(os.path.join(SW, "sound.json")))
rows = json.load(open(CR))
keep = [r for r in rows if not r.get("added_in") == "edit-r2"]
new = [dict(title="Buttress Roots 1.jpg", author="Mokkie", license="CC BY-SA 4.0", license_url="https://creativecommons.org/licenses/by-sa/4.0",
            source_url="https://commons.wikimedia.org/wiki/File:Buttress_Roots_1.jpg",
            file_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Buttress_Roots_1.jpg/1280px-Buttress_Roots_1.jpg",
            used_as="GrabCut cutout (U1 cut P1b_flange), one monotone curve: P1 buttress-flange plane behind the hand-off in the L-S5 / E-S4 closes",
            license_checked_2026_11_16="CC BY-SA 4.0", added_in="edit-r2")]
have = SOUND["have"]
if have.get("jungle"):
    new.append(dict(title="Jungle Sound Thailand Phuket.flac", author="Amada44", license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
                    source_url="https://commons.wikimedia.org/wiki/File:Jungle_Sound_Thailand_Phuket.flac",
                    file_url="https://upload.wikimedia.org/wikipedia/commons/3/3a/Jungle_Sound_Thailand_Phuket.flac",
                    used_as="jungle ambience bed (looped), with the declared silences", license_checked_2026_11_16="CC BY-SA 3.0", added_in="edit-r2"))
if have.get("splash"):
    new.append(dict(title="Bathtub water splashes.ogg", author="gradha", license="Public domain", license_url="",
                    source_url="https://commons.wikimedia.org/wiki/File:Bathtub_water_splashes.ogg",
                    file_url="https://upload.wikimedia.org/wikipedia/commons/8/83/Bathtub_water_splashes.ogg",
                    used_as="the splash on the last crosser's shins (3.2-4.3 s)", license_checked_2026_11_16="Public domain", added_in="edit-r2"))
if have.get("tide"):
    new.append(dict(title="Water over rocks as tide recedes.ogg", author="earthcalling", license="Public domain", license_url="",
                    source_url="https://commons.wikimedia.org/wiki/File:Water_over_rocks_as_tide_recedes.ogg",
                    file_url="https://upload.wikimedia.org/wikipedia/commons/6/60/Water_over_rocks_as_tide_recedes.ogg",
                    used_as="close water lap at the plank foot in the two retrieval closes", license_checked_2026_11_16="Public domain", added_in="edit-r2"))
json.dump(keep + new, open(CR, "w"), ensure_ascii=False, indent=1)
print(len(keep + new), "rows;", [r["title"] for r in new])
