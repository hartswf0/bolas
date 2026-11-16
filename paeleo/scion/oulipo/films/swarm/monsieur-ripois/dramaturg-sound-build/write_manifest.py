"""Writes sound-manifest.json and merges sound credits into films/credits/monsieur-ripois.json.
Licences are read from the saved Commons extmetadata responses (sound/commons-extmetadata-*.json)."""
import json, re, glob, html
from pathlib import Path
ROOT = Path("/home/user/bolas/paeleo/scion/oulipo/films")
SND = ROOT / "sources/monsieur-ripois/sound"
SW = ROOT / "swarm/monsieur-ripois"
ev = json.load(open(SW / "dramaturg-sound-build/sound-events.json"))
meta = {}
for f in sorted(glob.glob(str(SND / "commons-extmetadata-*.json"))) + [str(ROOT / "sources/monsieur-ripois/test-shot/clock-meta.json")]:
    for pg in json.load(open(f))["query"]["pages"].values():
        if "imageinfo" in pg: meta[pg["title"]] = pg["imageinfo"][0]
def strip(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()
fname = lambda t: re.sub(r"[^A-Za-z0-9._-]", "_", t[5:])
USE = {
 "File:Clock (tic tac).ogg": ("clock-tictac.ogg", "mechanical clock ticking (CC0, 2026)", "the clock of the present room, ticks cut individually (hiss gated out) and re-laid at 1 Hz from 1.75 s; muffled + reverberant in S2"),
 "File:Closing an old door.ogg": ("Closing_an_old_door.ogg", "an old wooden door being closed, with the quiet room around it", "ROOM TONE: the quiet stretches between its events, looped with crossfades at -50 dBFS (present dry, S2 muffled); its strongest event as the shadow-play door"),
 "File:Door handle creaking.ogg": ("Door_handle_creaking.ogg", "a door handle being turned, creaking", "S2a door latch (muffled) at 9.17 s"),
 "File:Squeaky door hinge.ogg": ("Squeaky_door_hinge.ogg", "a squeaky storage-locker door hinge", "S2a door swinging open; pitched up 1.7x as the box-lid hinge when the aunt opens it (S2c, muffled)"),
 "File:Cupboarddoorclose.ogg": ("Cupboarddoorclose.ogg", "a wooden cupboard door closing", "box lid: muffled lid shut inside the swallow (17.0 s), dry lid click when she closes it (39.5 s), clasp tick (7.75 s)"),
 "File:Knocking on wood or door.ogg": ("Knocking_on_wood_or_door.ogg", "knuckles knocking on wood", "single knocks low-passed to 900 Hz as heel steps on parquet (S2a), and to 1.4 kHz as the box set down on a lap / into hands"),
 "File:Book paper pages assorted.ogg": ("Book_paper_pages_assorted.ogg", "book pages and paper handled", "receipt slip landing and settling, three unfolds, receipt laid in the velvet slot; one slow movement low-passed as cloth rustle (his hand to his knee)"),
 "File:Assorted creaking noises of office chair.ogg": ("Assorted_creaking_noises_of_office_chair.ogg", "an office chair creaking", "sofa cushion/spring creak on his lean (3.42 s), low-passed 2.5 kHz"),
}
used_sources = {e["source"] for e in ev["events"]} | {"clock-tictac.ogg", "Closing_an_old_door.ogg"}
items, credits = [], []
for title, (local, shows, used) in USE.items():
    if local not in used_sources or title not in meta: continue
    ii = meta[title]; em = ii["extmetadata"]; g = lambda k: (em.get(k) or {}).get("value", "")
    lic = g("LicenseShortName")
    assert re.match(r"(?i)^(public domain|pd|cc0|cc by(-sa)? [0-9.]+)$", lic.strip()), (title, lic)
    lp = ROOT / "sources/monsieur-ripois" / ("test-shot" if local == "clock-tictac.ogg" else "sound/raw") / local
    rec = dict(id="SND-" + re.sub(r"[^a-z0-9]+", "-", title[5:].lower()).strip("-")[:40], title=title, author=strip(g("Artist")) or "unknown (Commons uploader)",
               license=lic, license_url=g("LicenseUrl"), source_url=ii["descriptionurl"], file_url=ii["url"].split("?")[0], local_path=str(lp),
               what_it_shows=shows + ("; " + strip(g("ImageDescription"))[:160] if g("ImageDescription") else ""),
               verified_date_or_place=strip(g("DateTimeOriginal")) or "unverified", used_as=used,
               licence_read_from="Commons extmetadata.LicenseShortName (API, 2026-11-16)")
    rec["cue_times_s"] = [e["t"] for e in ev["events"] if e["source"] == local]
    items.append(rec)
    credits.append({k: rec[k] for k in ("title", "author", "license", "license_url", "source_url", "file_url")} | {"used_as": "sound: " + used})
files = []
for f, what in [("mix-master.wav", "full 44.0 s master mix (stereo): dry present bed + muffled reverberant flashback bed (9.0-19.5 s) + all cue sounds"),
                ("mix-late.wav", "--late mix (identical to master: --late changes picture only)"),
                ("mix-baseline.wav", "--baseline mix: clasp tick and all receipt / slot / lid-click sounds (718-948) removed"),
                ("bed-present-dry.wav", "present bed alone: room tone + clock + present cue sounds, silent 9.0-19.5"),
                ("bed-flashback-muffled.wav", "flashback bed alone: same room and clock + S2 cue sounds, low-passed 650 Hz, 1.6 s reverb, 4 dB under the present; only 9.0-19.5 (hard in, hard out on frame 468)"),
                ("sfx-present-dry.wav", "present cue sounds only, dry"), ("sfx-flashback-raw.wav", "S2 cue sounds before muffling (for re-timing)"),
                ("room-tone-dry.wav", "room tone stem, 44 s"), ("clock-dry.wav", "clock stem, 44 s")]:
    files.append(dict(file=str(SND / f), what=what))
manifest = dict(slug="monsieur-ripois", owner="U1 dramaturg-sound", rate=44100, fps=24, duration_s=44.0,
  build="python3 -I films/swarm/monsieur-ripois/dramaturg-sound-build/build_sound.py; then write_manifest.py",
  perspective=dict(present="dry, close: room tone at -50 dBFS RMS + clock; cue sounds unfiltered",
                   flashback="« selon lui »: same room+clock+cues low-passed 650 Hz, 1.6 s decaying-noise reverb (wet 0.95 / dry 0.35), 4 dB under the present; hard cut back to dry on frame 468 (19.5 s)"),
  files=files, oneshots_dir=str(ROOT / "sources/monsieur-ripois/dramaturg-sound"), oneshots=ev["oneshots"], events=ev["events"],
  tick_times_s=ev["tick_times"], declared_silences=["no ring sound in the swallow (406-413)", "no voice anywhere (captions are the voice)", "no music", "43.0-44.0 silence"],
  stats=ev["stats"], sources=items,
  handmade=[dict(what="convolution reverb impulse response (decaying filtered noise, numpy) and the 650 Hz muffling filter", where="build_sound.py"),
            dict(what="the mix/cue timeline itself", where="build_sound.py PRESENT / FLASH lists")],
  synthesis_fallbacks=[] if not ev["missing"] else [dict(missing=m, note="no licensed source downloaded; cue silent in this build") for m in ev["missing"]],
  absences=json.load(open(SW / "dramaturg-sound-build/absences.json")) if (SW / "dramaturg-sound-build/absences.json").exists() else [])
json.dump(manifest, open(SW / "sound-manifest.json", "w"), ensure_ascii=False, indent=1)
cp = ROOT / "credits/monsieur-ripois.json"
cur = json.load(open(cp)) if cp.exists() else []
have = {c["source_url"] for c in cur}
cur += [c for c in credits if c["source_url"] not in have]
json.dump(cur, open(cp, "w"), ensure_ascii=False, indent=1)
print(len(items), "sound sources;", len(cur), "credits total")
