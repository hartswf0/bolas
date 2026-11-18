"""Write page.json and route.json from build-report.json.  python3 -I records.py"""
import hashlib, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SWARM = os.path.dirname(HERE); ROOT = os.path.abspath(os.path.join(SWARM, "../../.."))
MEDIA = os.path.join(ROOT, "films/sources/boucle-la/page-animator")
R = json.load(open(os.path.join(MEDIA, "build-report.json")))
CJ = json.load(open(os.path.join(SWARM, "cutouts.json")))
sh = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
rel = lambda p: os.path.relpath(p, ROOT)
import sys; sys.path.insert(0, HERE)
import panels as P
SEQ, SLOTS = P.SEQ, P.SLOTS
piece_sha = {k: v["sha256"] for k, v in CJ["pieces"].items()}
code_sha = {f: sh(os.path.join(HERE, f)) for f in ("panels.py", "build.py")}
code_sha["rig.py"] = sh(os.path.join(SWARM, "panel-artist/rig.py"))
code_sha["letter.py"] = sh(os.path.join(SWARM, "dialogue-writer-build/letter.py"))
panels = {}
for pid in "ABCH":
    rep = R["report"][pid]
    bal = R["balloons"][pid]
    bal["sha256"] = sh(os.path.join(ROOT, bal["file"]))
    key_src = json.dumps(dict(pieces=piece_sha, code=code_sha, poses=[d["pose"] for d in rep["drawings"]], jitter=[d["jitter_px"] for d in rep["drawings"]],
                              balloon=bal["sha256"], frame=P.FRAME[pid], size=P.SIZE[pid], pad=P.PAD), sort_keys=True)
    slots = [s for s, k in zip(SLOTS, SEQ) if k == pid]
    n = rep["n"]
    sheet = R["sheets"][pid]
    panels[pid] = dict(
        speaker=bal["speaker"], text=bal["text"], slots=slots,
        occurrences=[i + 1 for i, k in enumerate(SEQ) if k == pid],
        panel_rects={s: list(P.RECT[s]) for s in slots}, crop_rects={s: list(R["crop"][s]) for s in slots},
        raster_size=list(P.raster_size(pid)), frame_s_ox_oy=[round(v, 3) for v in P.FRAME[pid]],
        cache_key=hashlib.sha256(key_src.encode()).hexdigest(),
        held_drawing=dict(file=rep["drawings"][-1]["file"], sha256=rep["drawings"][-1]["sha256"]),
        page_crop_pixels_sha256={s: R["crop_sha"][s] for s in slots},
        held_equals_page_crop=True,
        frames_dir=rel(os.path.join(MEDIA, "frames", pid)),
        drawings=n, frames=n * 2, on="2s (every drawing exposed exactly 2 frames at 24 fps; f####.png are hard links to d###.png)",
        act_s=round(n * 2 / 24, 3), hold_after_last_frame_min_s=3.0,
        balloon_drawing=sheet["balloon_drawing"], balloon_frame=sheet["balloon_drawing"] * 2,
        face_out_drawing=sheet["face_out"], face_out_frame=None if sheet["face_out"] is None else sheet["face_out"] * 2,
        balloon=bal,
        fk_selfcheck=dict(joint_coincidence_err_px=rep["fk_joint_err_px"], bone_length_dev_px=rep["fk_bone_dev_px"], note_anchor_err_px=rep["note_anchor_err_px"]),
        tone=R["tone"][slots[0]],
        exposure_sheet=[dict(drawing=d["drawing"], frames=[d["drawing"] * 2, d["drawing"] * 2 + 1], sha256=d["sha256"], pose=d["pose"],
                             paper_jerk_px=d["jitter_px"], balloon=d["balloon"], ground=d["ground"]) for d in rep["drawings"]],
    )
panels["A"]["reads_as"] = "accuse: her forearm raises the note at his face; her head nods on the stress (drawing 7); his head lags back; settle; hold"
panels["B"]["reads_as"] = "'MOI ?!': anticipation dip, forearm flips up palm-out (overshoot drawing 4), head jerks back nose-up one drawing later (5 = balloon), her note drops; settle; hold"
panels["C"]["reads_as"] = "press: she rocks back, then the lean leads from the feet (overshoot 5), head arrives a drawing later (6 = balloon), note pushed out; settle; hold"
panels["H"]["reads_as"] = ("reveal: heads swing in (drawings 0-5, overshoot 4); he points with the open hand, she lifts the note (6-11); he nods at it (12-18); "
                           "card flip over 6 drawings 19-24 (turn 30,60,90 edge-on substitution back->face,120,150,180); drawing 24 face-out: ground cuts to spot black, "
                           "the bell; recoil (lean leads 25-27, head lags, overshoot 28), his nod accent 30 = balloon, settle to the held drawing 32")
timing = {  # plan section 6 film slots; the sequence starts at seq_start_s, the drawing 0 is shown from slot start during the camera slide
    "o1": dict(id="A", slot="r1c1", slot_s=[5.0, 11.5], seq_start_s=5.5), "o2": dict(id="B", slot="r1c2", slot_s=[11.5, 18.0], seq_start_s=12.0),
    "o3": dict(id="C", slot="r1c3", slot_s=[18.0, 24.5], seq_start_s=18.5), "o4": dict(id="H", slot="r2", slot_s=[24.5, 37.0], seq_start_s=26.0),
    "o5": dict(id="C", slot="r3c1", slot_s=[39.0, 45.5], seq_start_s=39.5), "o6": dict(id="B", slot="r3c2", slot_s=[45.5, 52.0], seq_start_s=46.0),
    "o7": dict(id="A", slot="r3c3", slot_s=[52.0, 58.5], seq_start_s=52.5)}
for o in timing.values():
    p = panels[o["id"]]
    o["act_end_s"] = round(o["seq_start_s"] + p["act_s"], 3)
    o["hold_s"] = round(o["slot_s"][1] - o["act_end_s"], 3)
    o["balloon_s"] = round(o["seq_start_s"] + p["balloon_frame"] / 24, 3)
    if p["face_out_frame"] is not None:
        o["face_out_s"] = round(o["seq_start_s"] + p["face_out_frame"] / 24, 3); o["bell_onset_s"] = o["face_out_s"]
        o["rustle_s"] = round(o["seq_start_s"] + 24 / 24, 3)
    assert o["hold_s"] >= 3.0, o
lett = os.path.join(ROOT, "films/sources/boucle-la/dialogue-writer/lettering")
page_png = os.path.join(ROOT, "assets/pages/boucle-la.png"); ann_png = os.path.join(ROOT, "assets/pages/boucle-la-annotated.png")
out = dict(
    slug="boucle-la", unit="U3 page-animator", owner="page-animator", date="2026-11-17", mode="handmake",
    acceptance="Page 3200x1800 with A B C / H / C B A; each pair's page crops pixel-identical and equal to the held drawing of ONE frame directory; "
               "every ID >= 8 distinct drawings on 2s with paper jerk, settle and a held final drawing; H face-out frame indexed; annotations in gutters only.",
    base_revision=dict(cutouts_json=sh(os.path.join(SWARM, "cutouts.json")), script_json=sh(os.path.join(SWARM, "script.json")),
                       plan_json=sh(os.path.join(SWARM, "plan.json")), lettering_json=sh(os.path.join(lett, "lettering.json")), code=code_sha, pieces=piece_sha),
    read_set=["films/swarm/boucle-la/plan.md", "plan.json", "cutouts.json", "panel-artist/rig.py", "script.json", "dialogue-writer-build/letter.py",
              "films/sources/boucle-la/panel-artist/cut/*.png", "films/sources/boucle-la/dialogue-writer/lettering/*.png", "test-shot-ledger.json"],
    write_set=["assets/pages/boucle-la.png", "assets/pages/boucle-la-annotated.png", "films/swarm/boucle-la/page.json", "films/swarm/boucle-la/route.json",
               "films/swarm/boucle-la/page-animator-build/*", "films/sources/boucle-la/page-animator/**"],
    page=dict(file=rel(page_png), sha256=sh(page_png), size=[3200, 1800], ground="#FBFBFB", ink="#0D0D0D",
              layout="margin column 0-540 (U2 margin-column.png); rows A B C / H (full width, spot black) / C B A; hand-inked borders ~6 px (H 7 px), one border drawing per ID",
              panel_rects=P.RECT, crop_pad=P.PAD, panel_id_rects=R["id_rects"],
              panel_ids_note="U2's id letters, tight-cropped and scaled to 16 px wide, in the right-hand gutter beside each panel's bottom-right corner (outside every crop)",
              tone=R["tone"], v1_check=dict(min_black_ABC=min(R["tone"][s]["black_lt60"] for s in SLOTS if s != "r2"), chroma_p99=R["tone"]["page"]["chroma_p99"]),
              framing="s = 1.20 page px per thumb px; heads top ~188 px (A B C, panel 580 high: heads in the middle third, figures 67 % of height, waist-up); "
                      "H heads top ~112 px of 500 (figures 78 %); balloons in the top 35-40 %"),
    annotated=dict(file=rel(ann_png), sha256=sh(ann_png), route_polyline=R["route_pts"], tags=R["tags"],
                   rule="route line and speech-act tags drawn only in the gutters/margins; asserted: no annotation pixel inside any panel crop",
                   film_layer=dict(file=rel(R["outputs"]["layer"]), sha256=sh(R["outputs"]["layer"]), what="RGBA ink layer of the same annotations for the film's section 4")),
    editor_media=dict(page=rel(os.path.join(MEDIA, "page.png")), ghost_page=dict(file=rel(R["outputs"]["ghost"]), what="every story panel at 22 % ink over page; furniture inked (film only)"),
                      frames_root=rel(os.path.join(MEDIA, "frames")), annotation_layer=rel(R["outputs"]["layer"]),
                      paste_rule="paste frames/<ID>/f####.png at the occurrence's crop_rect top-left on the page raster; after the last frame hold the last frame (== page crop)"),
    panels=panels, occurrences=timing,
    face_out=dict(id="H", drawing=panels["H"]["face_out_drawing"], frame_in_sequence=panels["H"]["face_out_frame"], film_s=timing["o4"]["face_out_s"],
                  note="frame 48 of frames/H/ (sequence starting at film 26.0 s) is the first face-out frame: ground cut to spot black + the single bell onset"),
    techniques=dict(
        scion32="U1's rig (feet->body->neck->head, body->elbow->forearm->hand->note), matrices root->leaf in fixed order; poses = U1 canonical + U1 entry; "
                "in-betweens keyed by hand per ID; joint coincidence and bone-length self-check measured on every drawing (see fk_selfcheck)",
        scion1="on 2s; anticipation, snap with few in-betweens, overshoot, head lags the body by one drawing, 3-6 settle drawings; paper jerk = seeded "
               "+/-0.9 px frame jitter and +/-0.3 deg root jitter per drawing (zero on the final drawing); note = substitution object (back drawing -> face drawing at edge-on); "
               "the cut to black on the face-out drawing",
        scion29="pieces cut by U1 (cutouts.json); not re-cut here"),
    evidence=[dict(id="daumier-moeurs-conjugales-3",
                   title="Honoré Daumier, Mœurs conjugales no. 3, « Et les cinq francs de ce matin ?… » (1839), Rijksmuseum RP-P-OB-41.183",
                   author="Honoré Daumier (print, 1839); Aubert & Cie (printer/publisher); scan Rijksmuseum", license="CC0",
                   license_url="http://creativecommons.org/publicdomain/zero/1.0/deed.en",
                   source_url="https://commons.wikimedia.org/wiki/File:Echtpaar_bespreekt_huishoudelijke_financi%C3%ABn_in_de_slaapkamer_Et_les_cinq_francs_de_ce_matin_(..)_(titel_op_object)_Gezinssituaties_(serietitel)_Moeurs_conjugales_(serietitel_op_object),_RP-P-OB-41.183.jpg",
                   file_url="https://upload.wikimedia.org/wikipedia/commons/7/79/Echtpaar_bespreekt_huishoudelijke_financi%C3%ABn_in_de_slaapkamer_Et_les_cinq_francs_de_ce_matin_%28..%29_%28titel_op_object%29_Gezinssituaties_%28serietitel%29_Moeurs_conjugales_%28serietitel_op_object%29%2C_RP-P-OB-41.183.jpg",
                   local_path="films/sources/boucle-la/panel-artist/daumier-1920.jpg (via U1's cut pieces films/sources/boucle-la/panel-artist/cut/*.png)",
                   what_it_shows="a married couple in nightcaps and nightshirts quarrelling at the bedside, the man left, the woman right, hands meeting; crayon lithograph",
                   verified_date_or_place="Commons extmetadata in films/sources/boucle-la/panel-artist/meta-raw.json (fetched 2026-11-17 by U1): LicenseShortName=CC0, "
                                          "UsageTerms 'Creative Commons Zero, Public Domain Dedication', DateTimeOriginal 1839, Paris (Rijksmuseum record); read by U3 from that file, not re-fetched",
                   used_as="all figure pieces (heads, bodies, forearms) and the backdrop crayon of every panel, via U1's rig; levels by U1 only")],
    handmade=[
        dict(item="panel borders (one wobbly pen rectangle per panel ID, seeded 101-104)", how="supersampled round-pen polyline, ~6 px (H 7 px)", where="page-animator-build/panels.py"),
        dict(item="balloons A B C H with tails re-aimed from the rig's mouth anchors", how="U2's letter.balloon() with U2's exact text, seed, cap and max width (letterforms unchanged); only the tail tip moves",
             where="films/sources/boucle-la/page-animator/lettering/balloon-*.png"),
        dict(item="the note card (back with crease; face À MA CHÈRE / ODETTE) at panel scale 110x72 px", how="U2's letter.note_card(); card flip by perspective foreshortening, edge-on drawn as one pen stroke, substitution at 90 deg",
             where="panels.py draw_note"),
        dict(item="route line with arrowheads, gutter layout of panel IDs and speech-act tags", how="pen polyline through gutters; U2's tag lettering scaled to 15 px", where="assets/pages/boucle-la-annotated.png, page-animator/annotation-layer.png"),
        dict(item="exposure sheets, in-betweens, paper jerk", how="hand-keyed per ID", where="page-animator-build/build.py")],
    absences=[
        "No new downloads by U3 (all material from U1 and U2).",
        "U1's original-resolution file is not in films/sources/boucle-la/panel-artist/orig/ (empty); pieces come from the 1920 px Commons thumbnail. At s=1.2 the page uses ~0.6 page px per source px, so resolution is sufficient.",
        "Plan allows balloons to break the top border; at this framing none needs to, so the crop pad is 6 px and the gutters stay free for the annotation route.",
        "B: where Gustave's forearm flips up, the vacated lower sleeve on his body piece reads as a near-blank white patch (U1's reclothed area); not U3's piece to change.",
        "Panel blacks: A/B/C ~23 % below L60 (reference rows 25-31 %); chroma p99 0. U3 did not re-level U1's pieces.",
        "Voice clips are not in U3's scope (U2 prepared them; default mix: bell + rustle only)."],
    builds=["films/swarm/boucle-la/page-animator-build/panels.py", "build.py", "records.py"],
)
json.dump(out, open(os.path.join(SWARM, "page.json"), "w"), indent=1, ensure_ascii=False)
route = dict(slug="boucle-la", owner="U3 page-animator",
             reading_route=[dict(occurrence=i + 1, id=k, slot=s, rect=list(P.RECT[s])) for i, (k, s) in enumerate(zip(SEQ, SLOTS))],
             panel_id_path=SEQ, path_string="A B C H C B A",
             pairs=[dict(id="A", slots=["r1c1", "r3c3"], occurrences=[1, 7]), dict(id="B", slots=["r1c2", "r3c2"], occurrences=[2, 6]),
                    dict(id="C", slots=["r1c3", "r3c1"], occurrences=[3, 5])],
             hinge=dict(id="H", slot="r2", occurrence=4, unpaired=True, ground="spot black"),
             page_direction_note="row 3 is read left to right (C B A) as page grammar requires, so the story runs backward through the mirror",
             annotated_route_polyline=R["route_pts"])
json.dump(route, open(os.path.join(SWARM, "route.json"), "w"), indent=1, ensure_ascii=False)
print("written")
