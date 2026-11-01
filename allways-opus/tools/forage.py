#!/usr/bin/env python3
"""Ask the Moving Image Archive by hand. One film, one question at a time, one at a time (it rate-limits).
usage: forage.py <film> "query" ["query" ...]
Keeps everything in films/<film>/forage.json, and writes a numbered thumbnail sheet per query to films/<film>/sheets/ so the eye chooses."""
import concurrent.futures as cf, hashlib, json, os, re, sys, time, urllib.request, urllib.error
from PIL import Image, ImageDraw, ImageFont
API = "https://www.movingimagearchive.com/api/search"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"user-agent": "cineosis-44-research", "content-type": "application/json"}
F = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 11)

def search(q, page=None):
    for t in range(8):
        try:
            req = urllib.request.Request(API, data=json.dumps({"query": q}).encode(), headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r: return json.load(r).get("clips", [])
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500: time.sleep(float(e.headers.get("retry-after") or 5 * (t + 1))); continue
            raise
        except Exception: time.sleep(10 * (t + 1))
    return []

def thumb(c):
    p = os.path.join(ROOT, "clips", "thumbs", c["id"] + ".jpg")
    if not os.path.exists(p) or not os.path.getsize(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        try:
            with urllib.request.urlopen(urllib.request.Request(c["thumbnailUrl"], headers={"user-agent": UA["user-agent"]}), timeout=40) as r: open(p, "wb").write(r.read())
        except Exception: return None
    return p

def main():
    film, qs = sys.argv[1], sys.argv[2:]
    d = os.path.join(ROOT, "films", film); os.makedirs(os.path.join(d, "sheets"), exist_ok=True)
    fp = os.path.join(d, "forage.json")
    db = json.load(open(fp)) if os.path.exists(fp) else {"queries": {}, "clips": {}}
    for q in qs:
        if q not in db["queries"]:
            cl = search(q); db["queries"][q] = [c["id"] for c in cl]
            for c in cl:
                db["clips"].setdefault(c["id"], c)
                db["clips"][c["id"]].setdefault("n", len(db["clips"]))
            json.dump(db, open(fp, "w"), indent=0); time.sleep(1.4)
        ids = db["queries"][q]
        with cf.ThreadPoolExecutor(8) as ex: paths = list(ex.map(thumb, [db["clips"][i] for i in ids]))
        W, H, COL = 200, 170, 6; rows = (len(ids) + COL - 1) // COL
        sh = Image.new("RGB", (W * COL, H * rows + 18), "#111"); dr = ImageDraw.Draw(sh); dr.text((4, 3), q[:170], fill="#fc6", font=F)
        for k, (i, p) in enumerate(zip(ids, paths)):
            x, y = W * (k % COL), 18 + H * (k // COL); c = db["clips"][i]
            if p:
                try:
                    im = Image.open(p).convert("RGB"); im.thumbnail((W - 4, H - 30)); sh.paste(im, (x + 2, y + 2))
                except Exception: pass
            dr.text((x + 3, y + H - 28), f"#{c['n']} {round(c.get('durationSeconds') or 0)}s {c.get('sourceYear') or '?'}", fill="#fff", font=F)
            dr.text((x + 3, y + H - 15), (c.get("sourceTitle") or "")[:29], fill="#aaa", font=F)
        name = re.sub(r"[^a-z0-9]+", "-", q.lower())[:60].strip("-") + "-" + hashlib.md5(q.encode()).hexdigest()[:4]
        sh.save(os.path.join(d, "sheets", name + ".jpg"), quality=78); print(os.path.join(d, "sheets", name + ".jpg"), len(ids), flush=True)

main()
