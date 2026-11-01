#!/usr/bin/env python3
"""Package the working folders into a publishable case study: allways-opus/ (run.json, films/<slug>/film.json, images, edit lists, critics).
Reads ALLWAYS/films/*; the compact videos and posters come from <stage>/films/<dir>/ (encode.sh). Writes <stage>/allways-opus/.
usage: package_run.py <stage>"""
import hashlib, json, os, re, shutil, subprocess, sys
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = sys.argv[1]; OUT = os.path.join(STAGE, "allways-opus")
WORKS = json.load(open(os.path.join(STAGE, "bolas", "paeleo", "allways", "works.json")))["works"]
BYSLUG = {w["slug"]: w for w in WORKS}
SLUG = {"terra": "terra-incognita", "chase": "cut-to-the-chase", "anybody": "anybody-anywhere", "collective": "collective-inventories"}
REV = json.load(open(os.path.join(STAGE, "src", "reviews_verbatim.json")))
exec(open(os.path.join(HERE, "tools", "case_notes.py")).read())          # NOTES, BUILDER, PACKETS, STATE


def jpg(src, dst, q=68):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert("RGB")
    if im.width > 1280: im = im.resize((1280, round(im.height * 1280 / im.width)), Image.LANCZOS)
    im.save(dst, quality=q, optimize=True, progressive=True)


def qname(q): return re.sub(r"[^a-z0-9]+", "-", q.lower())[:60].strip("-") + "-" + hashlib.md5(q.encode()).hexdigest()[:4] + ".jpg"


def dur(p): return round(float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p])), 2)


films_meta = []
for d in sorted(os.listdir(os.path.join(HERE, "films"))):
    W = os.path.join(HERE, "films", d)
    if not os.path.exists(os.path.join(W, "ledger.json")): continue
    slug = SLUG.get(d, d); w = BYSLUG[slug]; O = os.path.join(OUT, "films", slug); os.makedirs(O, exist_ok=True)
    db = json.load(open(os.path.join(W, "forage.json"))); byn = {c["n"]: c for c in db["clips"].values()}; byid = db["clips"]
    led = json.load(open(os.path.join(W, "ledger.json")))
    # video + poster (compact encode)
    enc = os.path.join(STAGE, "films", d); shutil.copy(os.path.join(enc, d + ".mp4"), os.path.join(O, slug + ".mp4")); shutil.copy(os.path.join(enc, "poster.jpg"), os.path.join(O, "poster.jpg"))
    # shots (with the route back to the source clip)
    shots = []
    for s in led["shots"]:
        c = byid.get(s.get("clip")); x = dict(s)
        if c: x["url"] = c.get("videoUrl"); x["clip_start"] = c.get("startSeconds"); x["source_slug"] = c.get("sourceSlug")
        shots.append(x)
    used = {}
    for s in shots:
        if s.get("clip") in byid: used.setdefault(byid[s["clip"]]["n"], []).append(s.get("position") or s.get("pair"))
    edl = json.load(open(os.path.join(W, "edl.json"))) if os.path.exists(os.path.join(W, "edl.json")) else None
    if edl:                                    # clips used only for their sound count as used too
        for i, e in enumerate(edl["shots"], 1):
            if isinstance(e.get("sound"), list):
                for x in e["sound"]:
                    if "clip" in x: used.setdefault(x["clip"], [])
    # searches and their contact sheets
    searches = []
    for q, ids in db["queries"].items():
        f = qname(q); p = os.path.join(W, "sheets", f)
        if os.path.exists(p): jpg(p, os.path.join(O, "img", "sheet-" + f)); searches.append({"q": q, "results": len(ids), "sheet": "img/sheet-" + f})
    # filmstrips
    looks = []
    sd = os.path.join(W, "strips")
    for f in sorted(os.listdir(sd) if os.path.isdir(sd) else [], key=lambda x: (int(re.match(r"(\d+)", x).group(1)), x)):
        if not f.endswith(".jpg"): continue
        n = int(re.match(r"(\d+)", f).group(1)); c = byn.get(n)
        if not c: continue
        jpg(os.path.join(sd, f), os.path.join(O, "img", "strip-" + f))
        pos = used.get(n)
        looks.append({"img": "img/strip-" + f, "clip": n, "label": f"#{n} {c.get('sourceTitle')} ({c.get('sourceYear') or 'undated'})", "used": pos or [], "in_cut": n in used})
    # reel of the final cut
    reel = os.path.join(W, "reel.jpg")
    if os.path.exists(reel): jpg(reel, os.path.join(O, "img", "reel.jpg"))
    # critic packets and verbatim reports
    reviews = []
    for i, r in enumerate(REV.get(d, []), 1):
        pk = PACKETS.get((d, i)); rv = {"round": i, "who": "independent critic (fresh Claude Sonnet 5.5 agent)", "verdict": re.match(r"VERDICT:\s*(.*?)[\.\(]", r["text"]).group(1).strip() if re.match(r"VERDICT:\s*(.*?)[\.\(]", r["text"]) else "", "text": r["text"], "builder_note": BUILDER.get((d, i), "")}
        if pk:
            cs = os.path.join(W, "critic", "sheet.jpg"); ct = os.path.join(W, "critic", "transcript.txt")
            jpg(cs, os.path.join(O, "img", f"critic-r{i}-sheet.jpg"), 62); os.makedirs(os.path.join(O, "critic"), exist_ok=True); shutil.copy(ct, os.path.join(O, "critic", f"transcript-r{i}.txt"))
            rv["packet"] = {"sheet": f"img/critic-r{i}-sheet.jpg", "transcript": f"critic/transcript-r{i}.txt", "note": pk}
        else: rv["packet"] = {"note": "This round's packet images were overwritten when the next round's packet was built, so they are not kept."}
        reviews.append(rv)
    if os.path.exists(os.path.join(W, "critic", "brief.md")): shutil.copy(os.path.join(W, "critic", "brief.md"), os.path.join(O, "brief.md"))
    # raw files
    files = []
    for name, label in (("edl.json", "edit list: every in, out, gain and reason, as written"), ("ledger.json", "ledger: each shot traced to its source seconds"), ("pairs.json", "pairs: the side-by-side list")):
        if os.path.exists(os.path.join(W, name)):
            if name == "ledger.json": json.dump({"film": slug, "duration": led["duration"], "shots": shots}, open(os.path.join(O, name), "w"), indent=1)
            else: shutil.copy(os.path.join(W, name), os.path.join(O, name))
            files.append({"path": name, "label": label})
    if os.path.exists(os.path.join(O, "brief.md")): files.append({"path": "brief.md", "label": "the brief the critic received"})
    extras = EXTRAS(d, W, O, jpg)
    film = {"slug": slug, "title": w["title"], "state": STATE[d], "summary": NOTES[d]["summary"],
            "video": {"src": slug + ".mp4", "poster": "poster.jpg", "duration": dur(os.path.join(O, slug + ".mp4")), "width": 800, "height": 600, "card": "ends with a 5 s card naming every source"},
            "searches": searches, "looks": looks, "shots": shots, "reel": "img/reel.jpg" if os.path.exists(reel) else None, "reviews": reviews,
            "repairs": NOTES[d].get("repairs", []), "notes": {k: NOTES[d].get(k, []) for k in ("worked", "failed", "open")}, "extras": extras, "files": files}
    if d in SEEN_LATE: film["notes"]["failed"].insert(0, SEEN_LATE[d])
    json.dump(film, open(os.path.join(O, "film.json"), "w"), indent=1)
    films_meta.append({"slug": slug, "title": w["title"], "state": STATE[d], "verdict": reviews[-1]["verdict"] if reviews else "", "duration": film["video"]["duration"], "poster": f"films/{slug}/poster.jpg", "rounds": len(reviews), "searches": len(searches), "shots": len(shots)})
    print(slug, len(searches), "searches", len(looks), "strips", len(shots), "shots", len(reviews), "reviews")
json.dump({"films": films_meta}, open(os.path.join(OUT, "films.json"), "w"), indent=1)

# tools, with machine-specific paths turned into environment variables
os.makedirs(os.path.join(OUT, "tools"), exist_ok=True)
for n in ("forage.py", "look.py", "hear.py", "beats.py", "cut.py", "pairs.py", "reel.py", "packet.py", "erase.py", "erase_plate.py", "speak.py", "adopt.py", "package_run.py", "case_notes.py"):
    s = open(os.path.join(HERE, "tools", n)).read()
    s = s.replace('os.environ.get("SAM2_ROOT", os.path.expanduser("~/sam2-root"))', 'os.environ.get("SAM2_ROOT", os.path.expanduser("~/sam2-root"))')
    s = s.replace('LAB = os.environ.get("CINEOSIS_LAB", os.path.expanduser("~/cineosis-lab/lab"))', 'LAB = os.environ.get("CINEOSIS_LAB", os.path.expanduser("~/cineosis-lab/lab"))')
    open(os.path.join(OUT, "tools", n), "w").write(s)
