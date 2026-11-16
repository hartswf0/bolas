# edit-r2/r3: add the newly used foraged items to films/credits/la-mort-en-ce-jardin.json (licences read live from Commons
# extmetadata on 2026-11-16; raw API answers saved under sources/la-mort-en-ce-jardin/edit/meta/).
import json, os, sys
SW = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILMS = os.path.abspath(os.path.join(SW, "..", ".."))
CR = os.path.join(FILMS, "credits", "la-mort-en-ce-jardin.json")
SOUND = json.load(open(os.path.join(SW, "sound.json")))
rows = json.load(open(CR))
# edit-r3: Buttress Roots 1 is no longer in the film (the close's P1 plane is now the fluted Mekong trunk, already credited)
keep = [r for r in rows if r.get("added_in") not in ("edit-r2", "edit-r3")]
for r in keep:
    if "LACMA 51.47.2" in r["title"] or "LACMA_51.47.2" in r.get("source_url", ""):
        r["title"] = "Pair of Woman's Bar Shoes (Wedding) LACMA 51.47.2a-b.jpg"          # the exact Commons filename
        if "1892" not in r["used_as"]:
            r["used_as"] = "the wedding shoe (LACMA 51.47.2a-b, United States, 1892): " + r["used_as"]
    if r["title"].startswith("Lavers Hill") or r["title"].startswith("Dietmar Rabich /"):
        r["commons_file"] = "Lavers Hill (AU), Melba Gully State Park -- 2019 -- 1133 (bw).jpg"
        # the author's requested credit form, leading the rendered row (the site renders title first)
        r["title"] = 'Dietmar Rabich / Wikimedia Commons / "Lavers Hill (AU), Melba Gully State Park -- 2019 -- 1133 (bw)" / CC BY-SA 4.0'
        r["attribution_requested_by_author"] = r["title"]
new = []
have = SOUND["have"]
if have.get("jungle"):
    new.append(dict(title="Jungle Sound Thailand Phuket.flac", author="Amada44", license="CC BY-SA 3.0", license_url="https://creativecommons.org/licenses/by-sa/3.0",
                    source_url="https://commons.wikimedia.org/wiki/File:Jungle_Sound_Thailand_Phuket.flac",
                    file_url="https://upload.wikimedia.org/wikipedia/commons/transcoded/3/3a/Jungle_Sound_Thailand_Phuket.flac/Jungle_Sound_Thailand_Phuket.flac.mp3",
                    used_as="jungle ambience bed (looped), with the declared silences", license_checked_2026_11_16="CC BY-SA 3.0 (live extmetadata, edit-r3)", decoded_from="the Commons mp3 transcode of the same file (upload.wikimedia.org/.../transcoded/...); the original FLAC URL returned HTTP 429", added_in="edit-r3"))
if have.get("splash"):
    new.append(dict(title="Bathtub water splashes.ogg", author="gradha", license="Public domain", license_url="",
                    source_url="https://commons.wikimedia.org/wiki/File:Bathtub_water_splashes.ogg",
                    file_url="https://upload.wikimedia.org/wikipedia/commons/transcoded/8/83/Bathtub_water_splashes.ogg/Bathtub_water_splashes.ogg.mp3",
                    used_as="the splash on the last crosser's shins (3.42-4.52 s)", license_checked_2026_11_16="Public domain (live extmetadata, edit-r3)", decoded_from="the Commons mp3 transcode of the same file", added_in="edit-r3"))
if have.get("tide"):
    new.append(dict(title="Water over rocks as tide recedes.ogg", author="earthcalling", license="Public domain", license_url="",
                    source_url="https://commons.wikimedia.org/wiki/File:Water_over_rocks_as_tide_recedes.ogg",
                    file_url="https://upload.wikimedia.org/wikipedia/commons/transcoded/6/60/Water_over_rocks_as_tide_recedes.ogg/Water_over_rocks_as_tide_recedes.ogg.mp3",
                    used_as="close water lap at the plank foot in the two retrieval closes", license_checked_2026_11_16="Public domain (live extmetadata, edit-r3)", decoded_from="the Commons mp3 transcode of the same file", added_in="edit-r3"))
json.dump(keep + new, open(CR, "w"), ensure_ascii=False, indent=1)
print(len(keep + new), "rows;", [r["title"] for r in new])
