"""Merge pieces_out.json with the evidence records and absences into cutouts/manifest.json. python3 -I finalize.py"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
CUT = HERE.parent
m = json.load(open(HERE / "pieces_out.json"))
cred = json.load(open(CUT / "credits-draft.json"))
S = "films/sources/99-ways-template/"
local = {"2017776093": S + "test-shot/rothstein_master_s3.png", "2017776111": S + "cutout-surgeon/raw/clock_master_s4.png",
         "2017679951": S + "test-shot/14940v.jpg", "2017861739": S + "loc/8d33109v.jpg",
         "2017861713": S + "cutout-surgeon/raw/bubley82_head_master.png", "musftpsets.200218222": S + "loc/blank.jpg",
         "2017776087": S + "cutout-surgeon/loc/8b16704v.jpg"}
shows = {"2017776093": "the Randolph agent at his desk under the TICKET OFFICE glass, ticket-rack case, two-leaf cupboard, pendant lamps",
         "2017776111": "an octagon-drop schoolhouse wall clock (Roman dial, hands at about 12:10) over a framed tavern rules card",
         "2017679951": "a large ornamental key on a dark ground",
         "2017861739": "a woman in a white apron standing before a bus-station window",
         "2017861713": "a ticket agent in glasses, white coat and dark tie at a counter, looking off to his right",
         "musftpsets.200218222": "a blank cream sheet with tape at its corners",
         "2017776087": "the station's waiting-room wall: EXPRESS & TELEGRAPH window, posters, an old man in a straw hat"}
ev = []
for c in cred:
    lid = c["source_url"].rstrip("/").split("/")[-1]
    ev.append({"id": "loc:" + lid, **{k: c[k] for k in ("title", "author", "license", "license_url", "source_url", "file_url")},
               "local_path": local.get(lid, ""), "what_it_shows": shows.get(lid, ""),
               "verified_date_or_place": "rights_advisory re-read from https://www.loc.gov/item/%s/?fo=json on 2026-11-17 (copy in %scutout-surgeon/loc/%s.json)" % (lid, S, lid),
               "used_as": c["used_as"]})
ev.append({"id": "loc:2017802673/2017802742/2017861708", "title": "Wolcott 1940 Mount Whittier ticket agent / baggage agent; Bubley 1943 bus-station agent",
           "author": "Marion Post Wolcott; Esther Bubley (FSA/OWI)", "license": "No known restrictions on publication (FSA/OWI)",
           "license_url": "https://www.loc.gov/rr/print/res/071_fsab.html", "source_url": "https://www.loc.gov/item/2017802673/ ; /2017802742/ ; /2017861708/",
           "file_url": "service JPEGs 8c11760v, 8c11830v, 8d33077v", "local_path": S + "loc/", "what_it_shows": "agents at their desks / a woman seated before a bus station",
           "verified_date_or_place": "rights re-read 2026-11-17", "used_as": "re-verified spares for the variant-builders (platform view); not cut by this unit"})
m["evidence"] = ev
m["handmade"] = [
    "Seeds and contour markup (box + scribble polygons, hair ellipse, pencil line, FK split polygons) authored in cutouts/build/pieces.py",
    "Repairs: Telea low band + native grain transplanted from the same photograph (no synthetic noise): shirt under the arm, pencil strip on the temple, fist edge over the ear, dial under the clock hands, glass behind the lamp",
    "Empty-desk plate: same-row texture transplant (counter rows from the right; beadboard rows shifted by whole plank periods) + Telea/grain on the desk top",
    "Scissor margins baked by bake_margin() at ~8 px page scale (*.margin.png); the white is paper (247,246,242), not a glow"]
m["absences"] = [
    "No second photograph of the Randolph agent exists online: LoC FSA negatives 8b16701-8b16715 (the Randolph/Vermont run) were looked at; none shows the agent again. So no real 'looking up' head of the same man. Offered: bubley82.agent.head (a matched FSA agent, level sideways gaze) as a declared Gilliam substitution, or keep the Rothstein head with the collar hinge.",
    "Searched LoC FSA for a matched agent looking UP (queries: clerk, looking up, puzzled, thinking, station agent, head scratching). Closest: Delano 1943 Parmelee passenger agent (2017843893) looks up but wears a uniform cap and dark coat: rejected (does not match the bare-headed clerk).",
    "No room door in the Randolph frame: the SERVICE door is the cupboard's right leaf (declared).",
    "Moving Image Archive stills for clock/key: only 320x240 colour or mixed frames, too small for a 3300-px page; none used. LoC (same photographer, same trip, 1937) supplied the clock instead.",
    "Rothstein master: not re-fetched. The test shot's multi-range reassembly (every 3rd row/col, 4360x3100 of rows 300-9600, cols 480-13560) was reused after an orientation/registration check against 8b16710v.jpg (see sources.rothstein.orientation_check). The trimmed margins are film rebate and the KODAK edge print, not picture.",
    "Sound was not foraged by this unit (assigned to rig-animator)."]
m["downloads_this_unit_MB"] = round((11761048 + 2237677 + 131072 + 65536 + 1.4e6) / 1e6, 1)
json.dump(m, open(CUT / "manifest.json", "w"), indent=1)
print("pieces", len(m["pieces"]), "plates", len(m["plates"]), "evidence", len(ev))
