"""Writes sound-A/ledger.json from the Commons extmetadata records (info.json, read 2026-11-16) and the build summary."""
import json, os, sys
FILMS = "/home/user/bolas/paeleo/scion/oulipo/films"
OUT = FILMS + "/swarm/la-cite-raymond-queneau/sound-A"
info = {r["title"]: r for r in json.load(open(sys.argv[1]))}
summ = json.load(open(OUT + "/cues-A.summary.json"))
cues = json.load(open(OUT + "/cues-A.json"))
TITLE = {"latch_open": "File:342706 spacejoe lock-3-open-lock-3.wav", "latch_close": "File:342701 spacejoe lock-3-close-lock-1.wav",
         "door_close": "File:Closing an old door.ogg", "handle_creak": "File:Door handle creaking.ogg", "squeaky_door": "File:Squeaky door.ogg",
         "cupboard": "File:Cupboarddoorclose.ogg", "faucet": "File:Faucet water into sink.ogg", "sink": "File:Tapsinkwaternoise.ogg",
         "footstep": "File:Footstep on Gravel (Gravity Sound).mp3", "kids": "File:Douzen kids on playground.ogg", "street": "File:Karlova 0001.ogg",
         "car_pass": "File:Kolem projíždí auto - část, Karlova ulice 001.ogg", "kettle": "File:WWS Whistlingkettle.ogg",
         "musicbox": "File:Music box notes 1.ogg", "radio_song": "File:Victor-73522a-b26758.ogg",
         "bonsoir": ("File:LL-Q150 (fra)-LoquaxFR-bonsoir.wav", "File:LL-Q150 (fra)-Helenou66-bonsoir.wav"),
         "toi": "File:LL-Q150 (fra)-LoquaxFR-toi.wav",
         "bonne_nuit": ("File:LL-Q150 (fra)-Rodrigo5260-bonne nuit.wav", "File:LL-Q150 (fra)-LoquaxFR-bonne nuit.wav")}
SHOWS = {"latch_open": "a lock being opened (close-miked)", "latch_close": "a lock being closed", "door_close": "an old wooden door closing",
         "handle_creak": "a door handle creaking", "squeaky_door": "a squeaky door opening", "cupboard": "a cupboard door closing",
         "faucet": "water from a faucet into a sink", "sink": "a tap running into a sink", "footstep": "a single footstep on gravel",
         "kids": "a dozen children on a playground", "street": "street ambience, Karlova street, Prague (2009-09-01)",
         "car_pass": "a car passing, Karlova street, Prague (2009-09-01)", "kettle": "a whistling kettle coming to the boil",
         "musicbox": "music-box notes", "radio_song": "Victor Schrammel-Orchester, 'O, du himmelblauer See' (Victor 73522-A, matrix B-26758), 78-rpm acoustic recording",
         "bonsoir": "French word 'bonsoir', Lingua Libre", "toi": "French word 'toi', Lingua Libre", "bonne_nuit": "French 'bonne nuit', Lingua Libre"}
use = {}
for c in cues:
    k = c["source_ledger_id"]
    use.setdefault(k, []).append(f"{c['sound_event']} @ {c['t_sound']} s (frame {c['frame']}, {c['picture_event_id']}, {c['stem']})")
L = []
for key, local in summ["foraged_used"].items():
    t = TITLE[key]
    if isinstance(t, tuple):
        t = next(x for x in t if os.path.basename(local).replace("_", "") in x.replace(" ", "").replace("(", "").replace(")", "").replace("File:", "") or True)
        # pick the record whose sanitized name matches the local file
        for cand in TITLE[key]:
            import re
            if re.sub(r"[^A-Za-z0-9._-]+", "_", cand[5:]) == os.path.basename(local): t = cand
    r = info.get(t, {})
    L.append(dict(id=key, title=t[5:], author=r.get("author", ""), license=r.get("license", ""), license_url=r.get("license_url", ""),
                  source_url=r.get("page", ""), file_url=(r.get("url", "").split("?")[0] + ("  (fetched as Commons' .mp3 transcode)" if key == "radio_song" else "")),
                  local_path=local, what_it_shows=SHOWS[key],
                  verified_date_or_place=(r.get("date") or "unverified") + ("; licence read from Commons extmetadata LicenseShortName 2026-11-16"),
                  used_as="; ".join(use.get(key, [])) or "decoded and checked, not placed", kind="FORAGED"))
for c in cues:
    pass
L.append(dict(id="HANDMADE", title="Synthesized elements (kit.Mix primitives, build_A.py)", author="this work", license="n/a (made for this work)",
              license_url="", source_url="", file_url="", local_path="films/swarm/la-cite-raymond-queneau/sound-A/build_A.py",
              what_it_shows="; ".join(summ["handmade"] + sorted({c['sound_event'] for c in cues if c['source_ledger_id'].startswith('HANDMADE')})),
              verified_date_or_place="made 2026-11-16", used_as="see cues-A.json entries whose source_ledger_id starts with HANDMADE", kind="HANDMADE"))
L.append(dict(id="archive-listened-rejected", kind="ABSENCE", title="movingimagearchive.com cache, sound leads",
              what_it_shows="Listened (spectrograms via ffmpeg showspectrumpic, frames viewed): ee12b007 Arteries of New York City 1941 (music 0-2.6 s, 1.7 s of optical-track hiss, then narration to the end); "
                            "b3ef2f32 Command Performance 1942, 1f03935f Party Magic 1938, 93053686 Straight Talk 1992, dab44545 Structure Protection Strategies 2003, 68ae3c9e Legacy for Wings 1991: narration or dialogue throughout; "
                            "7b8a9d52 Wathen amateur film 1944: silent; d2156bef Toute La Bande ep. 9 1970: French TV, rights unclear, also speech: rejected. No narration-free domestic or courtyard stretch long enough for amb/fx; none used.",
              license="", license_url="", source_url="https://www.movingimagearchive.com/", file_url="", local_path="", verified_date_or_place="2026-11-16", used_as="not used"))
json.dump(L, open(OUT + "/ledger.json", "w"), indent=1, ensure_ascii=False)
print(len(L), "rows")
