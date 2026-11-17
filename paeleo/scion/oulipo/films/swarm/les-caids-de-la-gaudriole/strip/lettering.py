"""strip/lettering.py - the writer's layer: balloons, lettering, panel frames, floor
lines and fold marks for sheet rev 1, drawn with the pen alphabet (strip/pen.py) and
the proposals' pen-line helpers, at the frozen positions in sheet.json.

Writes strip/lettering-layer.png (L, 2400 x 900, ink dark on white 255) and
strip/lettering-alpha.png (balloon interiors white-out matte: 255 where the balloon
paper must cover figure ink). The panel artist composes figures under it.
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(HERE, "..", "proposals"))
import pen as P                                   # strip/pen.py (with digits)
sys.modules["pen"] = P
import strip as ST                                # proposals/strip.py helpers (pen lines)
SJ = json.load(open(os.path.join(HERE, "sheet.json")))
W, H = SJ["W"], SJ["H"]
A, M, B = SJ["A"], SJ["M"], SJ["B"]
INK = 18


def main():
    img = Image.new("L", (W, H), 255)
    matte = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img); dm = ImageDraw.Draw(matte)
    for k, ((x0, y0), (x1, y1)) in SJ["floor_lines"].items():
        ST.wobble_line(d, [(x0, y0), (x1, y1)], w=3, seed=3 if k == "P1" else 4)
    tails = {"P1": (450, 505, 318), "P2": (1460, 1600, 330)}
    for k, (x0, x1, y0, y1) in SJ["balloons"].items():
        ST.balloon(d, x0, x1, y0, y1, tail=tails[k], seed=11 if k == "P1" else 12)
        dm.rounded_rectangle([x0, y0, x1, y1], radius=60, fill=255)
        bx, tx, ty = tails[k]
        dm.polygon([(bx - 22, y1 - 3), (bx + 22, y1 - 3), (tx, ty)], fill=255)
    for f in SJ["fragments"]:
        if f["layer"] != "balloon" or f["line"] is None: continue
        x0, y0, x1, y1 = f["bbox"]
        seed = (100 if f["panel"] == "P1" else 200) + (0 if f["side"] == "L" else 10) + f["line"] - 1
        if f["side"] == "L":
            P.pen(d, f["text"], x1, y0, SJ["cap_u"], ink=INK, seed=seed, anchor="r")
        else:
            P.pen(d, f["text"], x0, y0, SJ["cap_u"], ink=INK, seed=seed, anchor="l")
    smalls = {"P1.porter.ask": ((1010, 372), ["WHO BORROWED", "IT, THEN?"], (985, 470), 300),
              "P2.boys.say": ((2215, 430), ["OH?", "REALLY?"], (2250, 575), 310)}
    for fid, ((cx, cy), lines, tail, seed) in smalls.items():
        size = 26
        w = max(P.text_width(s, size) for s in lines) + (50 if len(lines) < 3 else 96); h = len(lines) * size * 1.6 + 30
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        d.ellipse([x0, y0, x1, y1], fill=255)
        pts = [(cx + w / 2 * ST.math.cos(2 * ST.math.pi * k / 60), cy + h / 2 * ST.math.sin(2 * ST.math.pi * k / 60)) for k in range(61)]
        d.polygon([(cx - 14, y1 - 8), (cx + 14, y1 - 8), tail], fill=255)
        ST.wobble_line(d, pts, w=4, seed=seed)
        ST.wobble_line(d, [(cx - 14, y1 - 4), tail, (cx + 14, y1 - 4)], w=4, seed=seed + 2)
        for i, s in enumerate(lines):
            P.pen(d, s, cx, y0 + 18 + i * size * 1.6, size, ink=INK, seed=seed + 10 + i, anchor="m")
        dm.ellipse([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], fill=255)
        dm.polygon([(cx - 14, cy + h / 2 - 8), (cx + 14, cy + h / 2 - 8), tail], fill=255)
    for k, s in [("P1", 21), ("P2", 22)]:
        x0, x1 = SJ["panels"][k]["x"]; y0, y1 = SJ["panels"][k]["y"]
        ST.wobble_line(d, ST.rr_pts(x0, y0, x1, y1, 4, 2), w=6, seed=s)
    for x, lab in [(A, "A"), (M, "M"), (B, "B")]:
        for yy, sgn in [(18, 1), (H - 18, -1)]:
            d.polygon([(x - 10, yy - 10 * sgn), (x + 10, yy - 10 * sgn), (x, yy + 4 * sgn)], fill=INK)
        P.pen(d, lab, x + 16, 8, 18, ink=INK, seed=400 + x)
    img.save(os.path.join(HERE, "lettering-layer.png"))
    matte.save(os.path.join(HERE, "lettering-alpha.png"))


if __name__ == "__main__":
    main()
