#!/usr/bin/env python3
"""Draws structure-board.png and slots.csv from structure.json (handmade diagram)."""
import json, csv, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "sources" / "la-belle-hortense" / "structure-combinatorial-editor-mystery-designer-verifier-"
d = json.load(open(HERE / "structure.json", encoding="utf-8"))
B = "/usr/share/fonts/X11/Type1/c0583bt_.pfb"; Rg = "/usr/share/fonts/X11/Type1/c0419bt_.pfb"
f = lambda p, s: ImageFont.truetype(p, s)
BLACK, RED, CREAM, TRED, GREEN = (1, 2, 1), (226, 1, 27), (225, 229, 178), (165, 9, 23), (47, 144, 54)
W, H = 1920, 1080
im = Image.new("RGB", (W, H), CREAM); dr = ImageDraw.Draw(im)
dr.text((60, 40), "La belle Hortense", font=f(B, 56), fill=TRED)
dr.text((60, 108), f"structure {d['revision']} · sigma = {d['sigma']} · sigma^6 = id", font=f(B, 28), fill=BLACK)
x0, y0, cw, rh = 140, 210, 150, 92
mods = d["modules"]
for k in range(6):
    dr.text((x0 + k * cw + 40, y0 - 40), f"slot {k+1}", font=f(Rg, 22), fill=BLACK)
centers = {}
for i, m in enumerate(mods):
    y = y0 + i * rh
    dr.text((60, y + 18), m["module"], font=f(B, 40), fill=BLACK)
    for k, a in enumerate(m["appearances"]):
        x = x0 + k * cw
        col = RED if a["motif"] == "A" else BLACK
        dr.rectangle([x + 4, y + 6, x + cw - 4, y + rh - 6], outline=col, width=3 if a["motif"] == "A" else 1)
        dr.text((x + 14, y + 12), f"{a['motif']} {a['motif_fr']}", font=f(B, 24), fill=col)
        dr.text((x + 14, y + 46), a["function"], font=f(Rg, 20), fill=GREEN if a["function"] == "evidence" else BLACK)
        centers[(i, a["motif"])] = (x + cw // 2, y + rh // 2)
# braid strands
for mtf in "BCDEFA":
    pts = [centers[(i, mtf)] for i in range(6)]
    for p, q in zip(pts, pts[1:]):
        dr.line([p[0], p[1] + 40, q[0], q[1] - 40], fill=RED if mtf == "A" else (120, 120, 110), width=4 if mtf == "A" else 1)
# clue timeline
tx0, tx1, ty = 1080, 1860, 260
dr.text((tx0, 180), "clue graph -> S  (time, s)", font=f(B, 28), fill=BLACK)
sx = lambda t: tx0 + (t - 0) / 66 * (tx1 - tx0)
dr.line([sx(0), ty, sx(66), ty], fill=BLACK, width=2)
for t, lab, c in [(21.0, "21.0 fair-play", GREEN), (39.0, "39.0 reader stop", BLACK), (43.2, "43.2 reveal", RED)]:
    dr.line([sx(t), ty - 30, sx(t), ty + 520], fill=c, width=2)
    dr.text((sx(t) + 4, ty - 34 - (24 if t == 43.2 else 0)), lab, font=f(Rg, 18), fill=c)
for j, c in enumerate(sorted(d["clues"], key=lambda c: c["t"])):
    y = ty + 30 + j * 36
    col = RED if c.get("reveal") else (GREEN if c["edge"] == "supports" else BLACK)
    dr.ellipse([sx(c["t"]) - 7, y - 7, sx(c["t"]) + 7, y + 7], fill=col)
    dr.text((sx(c["t"]) + 14, y - 12), f"{c['id']} {c['at']} {c['edge']} {c['claim']}", font=f(Rg, 17), fill=col)
y = 800
dr.text((60, y), "S: " + d["claim"]["text"], font=f(B, 26), fill=TRED)
for n, a in enumerate(d["alternatives"]):
    dr.text((60, y + 44 + n * 34), f"{a['id']} {a['text']}  -- refuted by {', '.join(a['refuted_by'])}", font=f(Rg, 22), fill=BLACK)
dr.text((60, y + 160), "fresh reader stops at 39.0 s: name the leading explanation and the motif that changed it", font=f(Rg, 22), fill=BLACK)
OUT.mkdir(parents=True, exist_ok=True)
im.save(OUT / "structure-board.png")
with open(OUT / "slots.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["id", "start", "end", "sample_t", "motif", "motif_fr", "function", "slot_line", "caption_fr", "caption_en", "sound"])
    for m in mods:
        for a in m["appearances"]:
            w.writerow([a["id"], a["start"], a["end"], a["start"] + 0.75, a["motif"], a["motif_fr"], a["function"], a["slot_line"],
                        a["caption_fr"], a["caption_en"], "; ".join(f"{c['t']} {c['kind']}" for c in a["sound"])])
print(OUT)
