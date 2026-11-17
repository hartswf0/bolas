"""The A3 page (plan.md section 7): 4961 x 3508 px at 300 dpi, 1 u = 1.1811 px.

Everything on it is ink composited (multiply) onto the foraged paper scan
(Commons 'Vintage Paper Texture (9789792113).jpg', J. Puckett, CC BY 2.0; full
resolution original, luminance kept, its yellow neutralised - grading only).
The strip art is strip/strip-art.png, the same raster as the film, resampled
1.1811x. All other lettering and drawing is pen.py strokes / pen polylines.

Writes assets/pages/les-caids-de-la-gaudriole.png and .pdf.
"""
import os, sys, math, json, random, hashlib
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fold as F
from pen import pen, text_width

ROOT = os.path.normpath(os.path.join(HERE, "../../../.."))          # .../oulipo
ART = os.environ.get("STRIP_ART", os.path.join(HERE, "strip-art.png"))
PAPER = os.path.join(ROOT, "films/sources/les-caids-de-la-gaudriole/paper-engineer/paper-orig.jpg")
OUT = os.environ.get("PAGE_OUT", os.path.join(ROOT, "assets/pages/les-caids-de-la-gaudriole"))
PW, PH = 4961, 3508
K = 300 / 254.0
A, M, B, D, W, H = F.A, F.M, F.B, F.D, F.W, F.H
SJ = F._sheet
INK = 0


def wob(d, pts, w=4, seed=0, dash=None):
    """Pen polyline with a slight hand wobble; dash = (on, off) or (on, off, dot)."""
    rnd = random.Random(seed)
    jit = 0.0
    tot = 0.0
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        n = max(2, int(L / 1.5))
        for k in range(n + 1):
            t = k / n
            s = tot + L * t
            if dash:
                per = sum(dash)
                ph = s % per
                if len(dash) == 2 and ph > dash[0]: continue
                if len(dash) == 3 and not (ph < dash[0] or dash[0] + dash[1] * 0.4 < ph < dash[0] + dash[1] * 0.4 + 2): continue
            jit = 0.96 * jit + rnd.uniform(-0.10, 0.10)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            nx, ny = -(by - ay) / (L or 1), (bx - ax) / (L or 1)
            x += nx * jit; y += ny * jit
            r = w / 2 * (0.85 + 0.3 * math.sin(math.pi * t))
            d.ellipse([x - r, y - r, x + r, y + r], fill=INK)
        tot += L


def circled(d, n, cx, cy, r=30, seed=0):
    pts = [(cx + r * math.cos(2 * math.pi * k / 40), cy + r * math.sin(2 * math.pi * k / 40)) for k in range(41)]
    wob(d, pts, w=4, seed=seed)
    pen(d, str(n), cx, cy - r * 0.55, r * 1.1, ink=INK, seed=seed + 1, anchor="m")


def paper_sheet():
    p = Image.open(PAPER).convert("RGB").rotate(90, expand=True)       # 2794 x 2194 landscape
    s = PW / p.width
    p = p.resize((PW, int(round(p.height * s))), Image.LANCZOS)
    a = np.asarray(p, np.float32)[:PH]
    if a.shape[0] < PH:
        a = np.concatenate([a, a[::-1]], 0)[:PH]
    L = 0.30 * a[..., 0] + 0.59 * a[..., 1] + 0.11 * a[..., 2]
    # keep the scan's wrinkles and fibre (luminance), remove its stain gradient and yellow
    import cv2
    low = cv2.GaussianBlur(L, (0, 0), 120)
    det = L - low
    det = det / (det.std() + 1e-6)
    base = 230 + 5.5 * np.clip(det, -4, 3) + 0.04 * (low - low.mean())
    return np.stack([base + 1, base - 1, base - 6], -1)


def main():
    art = Image.open(ART).convert("L")
    assert art.size == (W, H)
    sha = hashlib.sha256(open(ART, "rb").read()).hexdigest()
    sheet = np.asarray(art)
    V = F.folded_view(sheet)
    ink = Image.new("L", (PW, PH), 255)
    d = ImageDraw.Draw(ink)

    # ---------------- band 1: title
    pen(d, "FOLDED DIALOGUE - THE BORROWED KEY", 160, 70, 100, ink=INK, seed=1, width=14)
    pen(d, "AFTER É. LÉCROART, LES CAÏDS DE LA GAUDRIOLE / OUBAPO   -   FIGURES: WILHELM BUSCH, MAX UND MORITZ, 1865 (PUBLIC DOMAIN)",
        160, 212, 32, ink=INK, seed=2)
    pen(d, "ONE SHEET, ONE MARKED PLEAT. READ IT OPEN, THEN FOLD B ONTO A AND READ IT AGAIN. NOTHING IS ADDED.", 160, 262, 32, ink=INK, seed=3)

    # ---------------- band 2: the print strip at 100 %
    sw, sh = int(round(W * K)), int(round(H * K))          # 2835 x 1063
    SX, SY = (PW - sw) // 2, 500
    ink.paste(art.resize((sw, sh), Image.LANCZOS), (SX, SY))
    d = ImageDraw.Draw(ink)
    U = lambda u: SX + u * K
    Y = lambda v: SY + v * K
    # crop marks at the four corners (outside the sheet)
    for cx, cy, sx_, sy_ in [(SX, SY, -1, -1), (SX + sw, SY, 1, -1), (SX, SY + sh, -1, 1), (SX + sw, SY + sh, 1, 1)]:
        wob(d, [(cx + sx_ * 20, cy), (cx + sx_ * 110, cy)], w=3, seed=cx + cy)
        wob(d, [(cx, cy + sy_ * 20), (cx, cy + sy_ * 110)], w=3, seed=cx + cy + 1)
    pen(d, "PRINT STRIP - CUT ON THE CROP MARKS", 160, SY + 60, 30, ink=INK, seed=5)
    # fold lines continued into the page margin above and below the strip
    for x, kind, glyph, dash, sd in [(A, "MOUNTAIN", "Λ", (26, 14, 1), 10), (M, "VALLEY", "V", (22, 14), 20), (B, "LAY ON A", "", (4, 10), 30)]:
        X = U(x)
        wob(d, [(X, SY - 120), (X, SY - 22)], w=3, seed=sd, dash=dash)
        wob(d, [(X, SY + sh + 22), (X, SY + sh + 120)], w=3, seed=sd + 1, dash=dash)
        lab = {A: "A", M: "M", B: "B"}[x]
        pen(d, lab, X + 14, SY - 118, 40, ink=INK, seed=sd + 2)
        if glyph == "Λ":
            wob(d, [(X + 60, SY - 80), (X + 76, SY - 112), (X + 92, SY - 80)], w=4, seed=sd + 3)
        elif glyph == "V":
            wob(d, [(X + 60, SY - 112), (X + 76, SY - 80), (X + 92, SY - 112)], w=4, seed=sd + 3)
        pen(d, kind, X + 110, SY - 112, 26, ink=INK, seed=sd + 4)
    # open reading route numbers, in the right margin beside each balloon
    routes_open = [(1, SJ["balloons"]["P1"][0] - 20, 178), (2, 1010, 372), (3, SJ["balloons"]["P2"][0] - 20, 178), (4, 2215, 430)]
    for n, ux, uy in routes_open:
        pass
    # numbers drawn in the margin above the strip, with a pen leader to the balloon edge
    for n, ux, ly in [(1, 120, None), (2, 1010, None), (3, 1300, None), (4, 2215, None)]:
        cx = U(ux); cy = SY - 175
        circled(d, n, cx, cy, 26, seed=900 + n)
    pen(d, "OPEN READING ORDER", 160, SY + 110, 26, ink=INK, seed=920)
    # ruler 0-240 mm under the strip
    RY = SY + sh + 130
    wob(d, [(U(0), RY), (U(2400), RY)], w=3, seed=40)
    for mm in range(0, 241):
        X = U(mm * 10)
        L = 36 if mm % 10 == 0 else (24 if mm % 5 == 0 else 14)
        d.line([(X, RY), (X, RY + L)], fill=INK, width=2 if mm % 10 else 3)
        if mm % 10 == 0:
            pen(d, str(mm), X, RY + 46, 26, ink=INK, seed=1000 + mm, anchor="m")
    pen(d, "MM", U(2400) + 40, RY + 46, 26, ink=INK, seed=41)
    pen(d, "PRINT AT 100 % - THE RULER MUST MEASURE 240 MM.  STRIP 240 X 90 MM.", U(0), RY + 100, 30, ink=INK, seed=42)

    # ---------------- band 3: the reference's row  [open P1|P2] -> folded, + pleat section + seam insets
    B3 = 1937
    half = art.resize((sw // 2, sh // 2), Image.LANCZOS)
    hx = 160
    ink.paste(half, (hx, B3 + 230))
    d = ImageDraw.Draw(ink)
    pen(d, "OPEN (0.5 X)", hx, B3 + 170, 32, ink=INK, seed=50)
    fw = int(round(V.shape[1] * K))
    fold_im = Image.fromarray(V).resize((fw, sh), Image.LANCZOS)
    fx = hx + sw // 2 + 330
    ink.paste(fold_im, (fx, B3 - 20))
    d = ImageDraw.Draw(ink)
    pen(d, "FOLDED (100 %)", fx - 330, B3 + 60, 32, ink=INK, seed=51)
    # folded route numbers beside the folded panel
    circled(d, 1, fx - 50, B3 - 20 + 178 * K, 30, seed=960)
    circled(d, 2, fx + fw + 50, B3 - 20 + 430 * K, 30, seed=962)
    # arrow (pen)
    ay = B3 + 230 + sh // 4
    a0, a1 = hx + sw // 2 + 50, fx - 110
    wob(d, [(a0, ay), (a1, ay)], w=7, seed=52)
    wob(d, [(a1 - 50, ay - 40), (a1 + 6, ay), (a1 - 50, ay + 40)], w=7, seed=53)
    pen(d, "FOLD", (a0 + a1) / 2, ay - 70, 30, ink=INK, seed=54, anchor="m")
    # pleat cross-section (side view), from fold.cross_section at the pressed state, exaggerated in z
    cx0, cw = fx + fw + 150, PW - (fx + fw + 150) - 140
    sx = cw / 1300.0
    X_ = lambda X: cx0 + (X - 1120) * sx
    base_y = B3 + 330; g = 46
    pen(d, "PLEAT, SIDE VIEW (TABLE X TO SCALE, THICKNESS EXAGGERATED)", cx0, B3 + 50, 24, ink=INK, seed=56)
    wob(d, [(X_(1120), base_y + 30), (X_(2420), base_y + 30)], w=2, seed=64, dash=(10, 8))
    wob(d, [(X_(M), base_y), (X_(2400), base_y)], w=5, seed=55)                       # layer 3: F2+F3 on the table
    wob(d, [(X_(M), base_y - g), (X_(B), base_y - g)], w=5, seed=58)                  # layer 2: F1 face down
    wob(d, [(X_(D), base_y - 2 * g), (X_(B), base_y - 2 * g)], w=5, seed=59)          # layer 1: F0 face up
    for (xc, y0_, sgn, sd) in [(M, base_y, -1, 65), (B, base_y - g, 1, 66)]:
        pts = [(X_(xc) + sgn * (g / 2) * math.sin(math.pi * k / 20), y0_ - g / 2 + (g / 2) * math.cos(math.pi * k / 20)) for k in range(21)]
        wob(d, pts, w=5, seed=sd)
    pen(d, "M", X_(M) - 70, base_y - 40, 28, ink=INK, seed=62)
    pen(d, "A ON B", X_(B) + 40, base_y - 2 * g - 20, 28, ink=INK, seed=61)
    pen(d, "1", X_(D) - 40, base_y - 2 * g - 12, 24, ink=INK, seed=67)
    pen(d, "2", X_(1500), base_y - g - 40, 24, ink=INK, seed=68)
    pen(d, "3", X_(2100), base_y - 40, 24, ink=INK, seed=69)
    pen(d, "TABLE", X_(2150), base_y + 44, 22, ink=INK, seed=63)
    lbl = [("LAYER 1  F0  0-620 U  FACE UP  (X = U + D)", 0), ("LAYER 2  F1  620-1210 U  FACE DOWN  (X = 2M - U)", 1), ("LAYER 3  F2 + F3  1210-2400 U  FACE UP  (X = U)", 2)]
    for i, (t, k) in enumerate(lbl):
        pen(d, t, cx0, B3 + 410 + i * 42, 22, ink=INK, seed=57 + i)
    # 100x seam insets: 40 x 40 u of the folded view, at 8.5 px/u
    fxj = json.load(open(os.path.join(HERE, "fixture.json"))) if os.path.exists(os.path.join(HERE, "fixture.json")) else {}
    crops = [(c["name"], c["center_folded"][1]) for c in fxj.get("5_seam_crops", {}).get("crops", [])] or \
            [("BALLOON TOP", 80), ("BALLOON BOTTOM", 276), ("FLOOR LINE", 792), ("SLEEVE / HAND", 520)]
    t = 330
    iy = B3 + 580
    pen(d, "SEAM A = B, 4 X 4 MM CROPS ENLARGED (100 X TEST)", cx0, iy, 26, ink=INK, seed=70)
    for i, (name, y) in enumerate(crops):
        y = int(round(y))
        c = Image.fromarray(V[y - 20:y + 20, A - 20:A + 20]).resize((t, t), Image.NEAREST)
        ox = cx0 + i * (t + 36)
        ink.paste(c, (ox, iy + 50))
        d = ImageDraw.Draw(ink)
        d.rectangle([ox - 2, iy + 48, ox + t + 1, iy + 51 + t], outline=INK, width=2)
        sxx = ox + t // 2
        d.polygon([(sxx - 9, iy + 30), (sxx + 9, iy + 30), (sxx, iy + 46)], fill=INK)
        pen(d, name, ox, iy + t + 66, 20, ink=INK, seed=71 + i)

    # ---------------- band 4: inventory | coordinates | assembly + routes
    B4 = 3080
    c1, c2, c3 = 160, 2330, 3480
    pen(d, "FRAGMENT INVENTORY (SHEET U, 1 U = 0.1 MM)", c1, B4 - 80, 30, ink=INK, seed=80)
    rows = [f for f in SJ["fragments"] if f["layer"] == "balloon"] + [f for f in SJ["fragments"] if f["layer"] != "balloon"]
    lh = 22
    ncol = 2
    per = (len(rows) + 1) // ncol
    for i, f in enumerate(rows):
        col, r = divmod(i, per)
        x0, y0, x1, y1 = f["bbox"]
        st = "VISIBLE" if f["state"] == "visible" else ("GHOST, MIRRORED" if f["mirrored"] else "GHOST")
        name = f["text"] if f["layer"] == "balloon" else f["id"].split(".", 1)[1].upper()
        if len(name) > 22: name = name[:21] + "."
        line = f"{f['id'].split('.')[0]} {name}  {int(x0)}-{int(x1)} > {int(f['folded'][0])}-{int(f['folded'][1])} L{f['depth']} {st}"
        pen(d, line, c1 + col * 1090, B4 - 20 + r * (lh + 10), lh, ink=INK, seed=1200 + i)
    pen(d, "FOLD COORDINATES AND TOLERANCES", c2, B4 - 80, 30, ink=INK, seed=81)
    coords = ["A = 620 U (62.0 MM)  MOUNTAIN, FIRST", "M = 1210 U (121.0 MM)  VALLEY, GUTTER",
              "B = 2M - A = 1800 U (180.0 MM)", "D = B - A = 1180 U   2A - M = 30 U",
              "MAP: X > 2F - X  (A, THEN THE IMAGE OF M)", "0-A: X  /  A-M: 2A - X (DOWN)", "M-2400: X - D (UP)",
              "SEAM TOLERANCE 0.5 MM (5 U); DIGITAL 0", "FOLDED PANEL 1140 U = PANEL WIDTH"]
    for i, t_ in enumerate(coords):
        pen(d, t_, c2, B4 - 20 + i * 42, 24, ink=INK, seed=1300 + i)
    pen(d, "ASSEMBLY", c3, B4 - 80, 30, ink=INK, seed=82)
    steps = ["1 PRINT THIS PAGE AT 100 %.", "2 CUT THE STRIP ON THE CROP MARKS.", "3 MOUNTAIN-FOLD ON A (DASH-DOT).",
             "4 VALLEY-FOLD ON M (DASHED).", "5 SLIDE UNTIL MARK B COVERS MARK A, TOP AND BOTTOM.", "6 READ."]
    for i, t_ in enumerate(steps):
        pen(d, t_, c3, B4 - 20 + i * 42, 24, ink=INK, seed=1400 + i)
    pen(d, "OPEN: 1 MILLER  2 PORTER  3 PORTER  4 BOYS", c3, B4 + 250, 24, ink=INK, seed=1410)
    pen(d, "FOLDED: 1 MILLER (ONE BALLOON)  2 BOYS", c3, B4 + 292, 24, ink=INK, seed=1411)
    pen(d, "PAPER SCAN: J. PUCKETT, CC BY 2.0, VIA WIKIMEDIA COMMONS. LETTERING: HAND-STROKED PEN ALPHABET.",
        c1, PH - 48, 20, ink=INK, seed=1500)

    # ---------------- composite onto the paper
    paper = paper_sheet()
    inkf = 1 - np.asarray(ink, np.float32) / 255.0
    out = paper * (1 - 0.92 * inkf[..., None])
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT + ".png", dpi=(300, 300))
    img.save(OUT + ".pdf", "PDF", resolution=300.0)
    meta = dict(page=OUT + ".png", size=[PW, PH], dpi=300, px_per_u=K, strip_origin_px=[SX, SY], strip_size_px=[sw, sh],
                folded_origin_px=[fx, B3 - 20], half_origin_px=[hx, B3 + 230], strip_art_sha256=sha)
    json.dump(meta, open(os.path.join(HERE, "page-layout.json"), "w"), indent=1)
    return meta


if __name__ == "__main__":
    print(main())
