#!/usr/bin/env python3
"""Registrar step 2: freeze pool-manifest.json, credits, contact sheet, card prints.

Reads registrar/render-record.json (from registrar_build.py) and the LoC item JSON
saved in registrar/loc-json/. Re-renders frames 0/59/119 of every asset to prove
determinism before writing pool_hash.
"""
import datetime, hashlib, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registrar_build as R
import validate as V

HERE = os.path.dirname(os.path.abspath(__file__))
FILMS = V.FILMS
SRC = R.SRC
REG = os.path.join(SRC, "registrar")
OUT2 = os.path.join(SRC, "registrar-validator")
rel = lambda p: os.path.relpath(p, FILMS)
TODAY = "2026-11-16"

ROLE = {"01": "clock", "02": "hand with a parcel", "03": "second hand", "04": "door", "05": "glance",
        "06": "dropped receipt", "07": "person exiting", "08": "empty threshold"}
USED_AS = {
 "01": "pool asset 01 'l'horloge' (clock): notebook card in slot 1 for cut A, slot 6 after the re-shuffle; cut A event 1 (src 0-59) and cut B event 6 (src 119-84 reversed); rostrum push W0 whole dispatcher's counter -> W1 x1.25 toward the wall clock",
 "02": "pool asset 02 'le colis' (hand with a parcel): notebook card slot 2 -> 3; cut A event 2 (src 0-71), cut B event 3 (src 24-95, full 3 s); push W0 woman with box and co-workers -> W1 x1.25 toward her face and the box",
 "03": "pool asset 03 'la trotteuse' (second hand): notebook card slot 3 -> 5; cut A event 3, cut B event 5 (src 0-59); push W0 upper body with raised watch hand -> W1 x1.2 toward the watch hand",
 "04": "pool asset 04 'la porte' (door): notebook card slot 4 -> 2; cut A event 4 (src 0-59), cut B event 2 (src 0-47); push W0 carriage door and the couple's backs -> W1 x1.2 toward the door opening and the soldier",
 "05": "pool asset 05 'le regard' (glance): notebook card slot 5 -> 1; cut A event 5 (src 0-47), cut B event 1 (src 0-59 at 0.5x, 5 s); push W0 head and shoulders -> W1 x1.3 to the eyes",
 "06": "pool asset 06 'le reçu' (slips on the counter): notebook card slot 6 -> 4; cut A event 6, cut B event 4 (src 30-101); push W0 counter and clerk's hands -> W1 x1.25 toward the slips",
 "07": "pool asset 07 'la sortie' (person exiting): notebook card slot 7 (never moves); cut A event 7, cut B event 7; push W0 file of soldiers -> W1 x1.15 drifting toward the TRACK 2 doorway",
 "08": "pool asset 08 'le seuil' (empty threshold): notebook card slot 8 (never moves); cut A event 8, cut B event 8 (src 0-95); push W0 waiting room with benches -> W1 x1.05 toward the lone red cap",
}
SHOWS = {
 "01": "Two conductors at the dispatcher's office counter; tall wall clock (case clock) behind them, ceiling lamp, papers on the counter.",
 "02": "Woman mail-room worker in a headscarf carrying a large parcel, glancing over her shoulder; co-workers and parcel racks.",
 "03": "Conductor in cap and greatcoat looking up and to the left, holding a pocket watch at chest height; tall clock case at left.",
 "04": "Seen from behind: a soldier's companion (fur coat) and a man in a belted coat at a railway car door; a soldier looks out of the doorway; a red cap at right.",
 "05": "Close portrait of a young red cap in cap and overcoat against black, looking at the camera, head slightly turned (copy negative of a file print, with print border).",
 "06": "Soldiers at a reservation counter under a 'PLEASE ... SLEEPING CAR TICKETS' sign; clerk writes on slips spread on the counter.",
 "07": "A file of soldiers with kit bags walking through a concourse past a 'TRACK 2' gate and an 'ELEVATED TRAINS' sign.",
 "08": "The main waiting room at 1 a.m.: colonnade, rows of empty benches, a few figures; a lone red cap stands among the benches.",
}
LOC_CSV = {"01": "2017844012", "02": "2017844121", "03": "2017844115", "04": "2017843935",
           "05": "2017843923", "06": "2017843913", "07": "2017843870", "08": "2017843779"}
LOCAL = {k: os.path.join(REG, "masters", f"{k}u.tif") for k in LOC_CSV}
LOCAL_REAL = {k: os.path.realpath(v) for k, v in LOCAL.items()}


def sha256(p):
    return R.sha256(p)


def toned_print(aid, long_side=1600):
    """The frozen toned card print: whole clean area, print_op applied, fixed size."""
    im = R.load(aid)
    s, clean, W0, W1 = R.geometry(aid, im.size)
    lo, hi = R.levels(im, clean)
    w, h = clean[2] - clean[0], clean[3] - clean[1]
    k = long_side / max(w, h)
    size = (round(w * k), round(h * k))
    red = 2 if max(im.size) > 8000 else 1
    work = im.reduce(red) if red > 1 else im
    g = work.resize(size, Image.LANCZOS, box=tuple(v / red for v in clean))
    return Image.fromarray(R.print_op(np.asarray(g), lo, hi), "RGB")


def main():
    rec = json.load(open(os.path.join(REG, "render-record.json")))
    assert sorted(rec) == sorted(R.POOL), sorted(rec)
    # determinism: re-render three frames per asset and compare
    det = {}
    for aid in sorted(R.POOL):
        im = R.load(aid)
        s, clean, W0, W1 = R.geometry(aid, im.size)
        lo, hi = R.levels(im, clean)
        red = rec[aid]["reduce"]
        work = im.reduce(red) if red > 1 else im
        wins = R.windows(W0, W1)
        ok = True
        for i in (0, 59, 119):
            fr = work.resize((R.OW, R.OH), Image.LANCZOS, box=tuple(v / red for v in wins[i]))
            m = hashlib.md5(R.print_op(np.asarray(fr), lo, hi).tobytes()).hexdigest()
            png = V.rgb_md5_png(os.path.join(R.ASSETS, aid, f"{i:04d}.png"))
            ok &= (m == rec[aid]["frame_md5"][i] == png)
        det[aid] = ok
        print("determinism", aid, ok, flush=True)
    assert all(det.values()), det

    print_op = {"name": "print-stage-1943",
                "order": ["LoC master TIFF (8-bit L)", "integer box reduce r (r=2 when a side > 8000 px, else 1)",
                          "per-frame eased 16:9 window crop, LANCZOS resample to 1280x720 (float box, PIL)",
                          "levels: v = clip((x - lo)/(hi - lo), 0, 1) with lo/hi = the asset's p0.5/p99.5 inside clean_bounds (fixed, recorded per asset)",
                          "paper curve: v' = v ** gamma (one gamma for all 8)",
                          "warm silver-gelatin map: rgb = black + v' * (white - black), rounded to uint8"],
                "black_rgb": list(R.BLACK), "white_rgb": list(R.WHITE), "gamma": R.GAMMA,
                "levels_percentiles": [R.LO_PCT, R.HI_PCT],
                "no": ["grain", "vignette", "blur", "sharpen", "tint per shot", "dither"],
                "applies_to": "every appearance of a print: rostrum assets and notebook card prints (registrar-validator/prints/<id>.png)"}
    assets = []
    items = {}
    for aid in sorted(R.POOL):
        loc = json.load(open(os.path.join(REG, "loc-json", f"{LOC_CSV[aid]}.json")))
        it = loc["item"]
        items[aid] = it
        r = rec[aid]
        assets.append({
            "asset_id": aid, "proof_role": ROLE[aid], "title": it["title"],
            "loc_item": LOC_CSV[aid], "source_anchor": f"https://www.loc.gov/item/{LOC_CSV[aid]}/",
            "file_url": R.POOL[aid]["tif"], "local_path": rel(LOCAL_REAL[aid]),
            "source_sha256": sha256(LOCAL_REAL[aid]),
            "source_note": ("copy negative made from the 1943 file print (LC-USZ62-130642); the print's own white border and easel surround are outside clean_bounds"
                            if aid == "05" else "digital file from the original negative (LoC master TIFF)"),
            "native_bounds": r["native_bounds"], "clean_bounds": r["clean_bounds"],
            "clean_bounds_note": "image area inside the film rebate, excluding OWI-NNNNN edge codes, notches and KODAK SAFETY edge print (05: inside the print border); chosen by eye on registrar/preview/grid_*.jpg",
            "print_op": {"reduce": r["reduce"], "levels": r["levels"]},
            "window_path": {"coords": "master pixels (x0,y0,x1,y1), 16:9", "W0": r["W0"], "W1": r["W1"],
                            "ease": "cubic in-out, t = i/119", "zoom": round((r["W0"][2] - r["W0"][0]) / (r["W1"][2] - r["W1"][0]), 3)},
            "N": R.N, "frame_dir": rel(os.path.join(R.ASSETS, aid)),
            "frame_md5": r["frame_md5"],
        })
    man = {"schema": "scion.pool-manifest/1", "slug": "la-machine-a-tuer-le-temps", "N": R.N,
           "size": [R.OW, R.OH], "fps": 24, "print_op": print_op, "assets": assets}
    man["pool_hash"] = V.pool_hash(man)
    man["pool_hash_def"] = "sha256 of validate.canonical(manifest): JSON (sort_keys, separators=(',',':')) of {slug, N, size, print_op, assets sorted by id: {asset_id, source_sha256, print_op, window_path, frame_md5}}"
    man["frame_md5_def"] = "md5 of the frame's raw RGB24 bytes (1280x720x3, row-major); identical to `ffmpeg -i NNNN.png -pix_fmt rgb24 -f framemd5`"
    man["frozen"] = {"date": TODAY, "by": "U1 registrar-validator", "determinism": det,
                     "builder": rel(os.path.join(HERE, "registrar_build.py")), "freezer": rel(os.path.abspath(__file__)),
                     "validator": rel(os.path.join(HERE, "validate.py"))}

    # card prints for the notebook animator (frozen toned print at one size)
    pd = os.path.join(OUT2, "prints")
    os.makedirs(pd, exist_ok=True)
    cards = {}
    for aid in sorted(R.POOL):
        im = toned_print(aid)
        fp = os.path.join(pd, f"{aid}.png")
        im.save(fp)
        cards[aid] = {"path": rel(fp), "size": list(im.size), "rgb_md5": hashlib.md5(im.tobytes()).hexdigest(),
                      "parent": {"source_sha256": next(a["source_sha256"] for a in assets if a["asset_id"] == aid),
                                 "op": "print_op over clean_bounds, LANCZOS to 1600 px long side"}}
    man["card_prints"] = {"note": "Notebook pages must paste these frozen toned prints, scaled uniformly (one scale per card across the film) and moved by translation only; record print_md5 = md5 of the scaled card print in the ledger.",
                          "items": cards}

    # contact sheet: frames 0, 60, 119 of each asset
    cw, ch = 384, 216
    sheet = Image.new("RGB", (60 + 3 * (cw + 8), 8 * (ch + 26) + 40), (236, 229, 213))
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
    except Exception:
        fnt = ImageFont.load_default()
    d.text((10, 10), f"pool {man['pool_hash'][:16]}…  frames 0 / 60 / 119  (1280x720, print_op, no grain)", fill=(66, 58, 47), font=fnt)
    for k, aid in enumerate(sorted(R.POOL)):
        y = 36 + k * (ch + 26)
        d.text((10, y + ch // 2), aid, fill=(183, 97, 88), font=fnt)
        for j, i in enumerate((0, 60, 119)):
            t = Image.open(os.path.join(R.ASSETS, aid, f"{i:04d}.png")).resize((cw, ch), Image.LANCZOS)
            sheet.paste(t, (50 + j * (cw + 8), y))
        d.text((50, y + ch + 3), f"{ROLE[aid]} · {items[aid]['title'][:80]}", fill=(66, 58, 47), font=fnt)
    cs = os.path.join(REG, "contact-sheet.jpg")
    sheet.save(cs, quality=88)
    man["contact_sheet"] = rel(cs)

    # evidence records
    ev = []
    for a in assets:
        it = items[a["asset_id"]]
        ev.append({"id": a["asset_id"], "title": it["title"] + " (1943)",
                   "author": "Jack Delano (1914-1997), photographer; U.S. Office of War Information (FSA/OWI)",
                   "license": "No known restrictions on publication (US government work, FSA/OWI; public domain)",
                   "rights_advisory_verbatim": it.get("rights_advisory"),
                   "license_url": "https://www.loc.gov/rr/print/res/071_fsab.html",
                   "source_url": a["source_anchor"], "file_url": a["file_url"], "local_path": a["local_path"],
                   "source_sha256": a["source_sha256"], "what_it_shows": SHOWS[a["asset_id"]],
                   "verified_date_or_place": f"Chicago, Union Station; {', '.join(it.get('created_published') or [])} (LoC caption card); rights re-read {TODAY} from {a['source_anchor']}?fo=json",
                   "call_number": it.get("call_number"), "used_as": USED_AS[a["asset_id"]], "kind": "FORAGED"})
    man["evidence"] = ev
    man["evidence_other"] = json.load(open(os.path.join(OUT2, "evidence-other.json")))
    out = os.path.join(HERE, "pool-manifest.json")
    json.dump(man, open(out, "w"), indent=1, ensure_ascii=False)
    print("pool_hash", man["pool_hash"])

    # credits
    cp = os.path.join(FILMS, "credits", "la-machine-a-tuer-le-temps.json")
    cred = json.load(open(cp))
    used = {f"https://www.loc.gov/item/{v}/": k for k, v in LOC_CSV.items()}
    newc = []
    for c in cred:
        if c.get("source_url") in used:
            continue
        if "loc.gov/item/" in c.get("source_url", ""):
            c = dict(c, used_as="not used (candidate evaluated for the pool; not in the frozen 8)")
        newc.append(c)
    for e in ev:
        newc.insert(int(e["id"]) - 1, {"title": e["title"], "author": e["author"], "license": e["license"] + "; LoC rights advisory: " + e["rights_advisory_verbatim"],
                                       "license_url": e["license_url"], "source_url": e["source_url"], "file_url": e["file_url"],
                                       "used_as": e["used_as"]})
    json.dump(newc, open(cp, "w"), indent=1, ensure_ascii=False)
    print("credits", len(newc), "entries")


if __name__ == "__main__":
    main()
