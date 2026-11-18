"""boucle-la U2 (dialogue writer / letterer): hand-lettered balloons, note face, margin furniture.

HANDMADE: every glyph is a pen polyline of the stroke alphabet in proposals/kf_common.py, inked with a
round pen (heavier than kf-2), seeded per balloon so the same balloon is the SAME drawing wherever it is
pasted (palindrome rule: one PNG per panel ID, used by both occurrences).

Outputs RGBA PNGs at page resolution (page = 3200x1800; ink #0D0D0D, page/balloon fill #FBFBFB) to
films/sources/boucle-la/dialogue-writer/lettering/, and lettering.json (positions, seeds, sha256).

Run:  python3 -I letter.py                     (everything, default tail anchors)
      python3 -I letter.py --tail A 600 250    (re-render one balloon with a new tail tip, panel-relative px;
                                               text, seed and letterforms are unchanged, only the tail moves)
"""
import hashlib
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
SWARM = os.path.join(ROOT, "films/swarm/boucle-la")
sys.path.insert(0, os.path.join(SWARM, "proposals"))
import kf_common as kc  # noqa: E402  the work's own stroke alphabet

OUT = os.path.join(ROOT, "films/sources/boucle-la/dialogue-writer/lettering")
os.makedirs(OUT, exist_ok=True)
INK, PAGE = 13, 251
SS = 3  # supersampling
PEN_K = 0.26  # glyph pen = cap * PEN_K (kf-2 used ~0.19; test shot 0.24): heavier, holds at page fit
OUTLINE = 5.0  # balloon outline, page px
TRACK = 0.8  # letter spacing (glyph units); kf_common default 0.55 closes up under the heavier pen


def wrap(s, cap, maxw):
    lines, cur = [], ""
    for wd in s.split(" "):
        t = (cur + " " + wd).strip()
        if cur and kc.text_width(t, cap, TRACK) > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = t
    if cur:
        lines.append(cur)
    # never strand trailing punctuation on its own line
    if len(lines) > 1 and len(lines[-1].replace(" ", "")) <= 2:
        lines[-2] = lines[-2] + " " + lines.pop()
    return lines

# digits for the margin credit (pen strokes, same hand)
kc.G.update({
    "1": (2.2, [[(0.2, 1.2), (1.4, 0), (1.4, 6)], [(0.3, 6), (2.2, 6)]]),
    "3": (3.6, [[(0.2, 0.8), (1.1, 0), (2.6, 0), (3.4, 0.9), (3.3, 2.1), (2.2, 2.9), (1.2, 2.9)],
                [(2.2, 2.9), (3.5, 3.8), (3.5, 5.1), (2.6, 6), (1.0, 6), (0.1, 5.2)]]),
    "8": (3.6, [kc._arc(1.8, 1.5, 1.5, 1.5, 0, 360, 18), kc._arc(1.8, 4.4, 1.8, 1.6, 0, 360, 20)]),
    "9": (3.6, [kc._arc(1.8, 2.0, 1.6, 2.0, 0, 360, 20), [(3.4, 2.0), (3.2, 4.6), (2.2, 6), (0.6, 5.6)]]),
})

# ------------------------------------------------------------------ the lines (exact strings) --
LINES = {
    "A": ("odette", "ET ÇA ?! C'EST TOI QUI L'AS LAISSÉ, CE MOT ?"),
    "B": ("gustave", "MOI ?! TU CROIS QUE J'AI QUE ÇA À FAIRE ?"),
    "C": ("odette", "ALORS DE QUI IL EST ?!"),
    "H": ("gustave", "« À MA CHÈRE ODETTE... » TIENS. C'EST POUR TOI."),
}
# hinge alternates, one lettered balloon per speech-act group (hinge-alternatives.md)
ALTS = {
    "H-G2": ("gustave", "« MON CHER ALFRED... » C'EST BIEN TON ÉCRITURE, NON ?"),
    "H-G3": ("gustave", "C'EST DE MOI, GROSSE BÊTE. BONNE FÊTE, ODETTE."),
    "H-G4": ("gustave", "IL FAIT FROID ICI."),
    "H-G1b": ("gustave", "LIS DONC L'ADRESSE, MA CHÈRE ODETTE."),
}
PANEL = {"A": (850, 580), "B": (850, 580), "C": (850, 580), "H": (2610, 500)}
# balloon layout, panel-relative page px: centre, cap height, max line width, default tail tip.
# Tail tips are PROVISIONAL (from the test-shot rig); U3 recomputes them from U1's mouth anchors and
# re-renders with --tail. Balloon bodies sit in the top 35-40 % and may break the top border (cy - ry < 0).
LAYOUT = {
    "A": dict(c=(515, 112), cap=38, maxw=580, tail=(585, 262)),
    "B": dict(c=(335, 112), cap=38, maxw=580, tail=(265, 258)),
    "C": dict(c=(470, 100), cap=42, maxw=660, tail=(610, 250)),
    "H": dict(c=(960, 128), cap=42, maxw=700, tail=(1390, 175)),
}


def seed_of(key, text):
    return sum(map(ord, key + text))


def to_rgba(fill, ink):
    """fill, ink: float [0,1] masks at page scale -> RGBA (gray ink on balloon-white)."""
    g = PAGE * (1 - ink) + INK * ink
    a = np.maximum(fill, ink)
    g8 = np.clip(g + 0.5, 0, 255).astype(np.uint8)
    a8 = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([g8, g8, g8, a8]), "RGBA")


def balloon(key, text, cx, cy, cap, maxw, tail, seed, panel_w=None):
    """Irregular oval balloon with a pointed tail; returns (RGBA image, top-left in the given coords)."""
    lines = wrap(text, cap, maxw)
    lh = cap * 1.5
    tw = max(kc.text_width(l, cap, TRACK) for l in lines)
    th = lh * len(lines) - (lh - cap)
    rx, ry = tw / 2 + cap * 1.6, th / 2 + cap * 1.15
    if panel_w:  # keep the balloon inside its panel horizontally (it may only break the TOP border)
        cx = min(max(cx, rx + 18), panel_w - rx - 18)
    pad = 16
    bx0 = int(math.floor(min(cx - rx, tail[0]) - pad))
    by0 = int(math.floor(min(cy - ry, tail[1]) - pad))
    bx1 = int(math.ceil(max(cx + rx, tail[0]) + pad))
    by1 = int(math.ceil(max(cy + ry, tail[1]) + pad))
    bw, bh = bx1 - bx0, by1 - by0
    fill = Image.new("L", (bw * SS, bh * SS), 0)
    line = Image.new("L", (bw * SS, bh * SS), 0)
    df, dl = ImageDraw.Draw(fill), ImageDraw.Draw(line)
    rs = random.Random(seed)
    lcx, lcy = (cx - bx0) * SS, (cy - by0) * SS
    ph = rs.uniform(0, 6.28)
    pts = []
    for a in np.linspace(0, 2 * math.pi, 120, endpoint=False):
        r = 1 + 0.03 * math.sin(3 * a + ph) + 0.015 * math.sin(5 * a + 2 * ph)
        ca, sa = math.cos(a), math.sin(a)
        e = 2.3
        px = abs(ca) ** (2 / e) * (1 if ca >= 0 else -1)
        py = abs(sa) ** (2 / e) * (1 if sa >= 0 else -1)
        pts.append((lcx + px * rx * SS * r, lcy + py * ry * SS * r))
    tx, ty = (tail[0] - bx0) * SS, (tail[1] - by0) * SS
    ang = math.atan2(ty - lcy, tx - lcx)
    k = min(range(len(pts)), key=lambda i: abs((math.atan2(pts[i][1] - lcy, pts[i][0] - lcx) - ang + math.pi) % (2 * math.pi) - math.pi))
    n = len(pts)
    a0, a1 = pts[(k - 4) % n], pts[(k + 4) % n]
    body = [pts[(k + 4 + j) % n] for j in range(n - 8)]
    shape = body + [a0, (tx, ty), a1]
    df.polygon(shape, fill=255)
    dl.line(shape + [shape[0]], fill=255, width=int(OUTLINE * SS), joint="curve")
    y = lcy - th / 2 * SS
    for i, l in enumerate(lines):
        lw = kc.text_width(l, cap, TRACK) * SS
        kc.ink_text(line, lcx - lw / 2, y, l, cap=cap * SS, seed=seed + i * 13, pen=int(cap * PEN_K * SS), track=TRACK)
        y += lh * SS
    f = np.asarray(fill.resize((bw, bh), Image.LANCZOS), np.float32) / 255
    i_ = np.asarray(line.resize((bw, bh), Image.LANCZOS), np.float32) / 255
    return to_rgba(f, i_), (bx0, by0), lines, (cx, cy)


def text_layer(rows, size, ss=SS):
    """rows: list of (x, y, string, cap, seed, pen, slant). Returns tight RGBA ink layer + its origin."""
    W, H = size
    m = Image.new("L", (W * ss, H * ss), 0)
    for (x, y, s, cap, seed, pen, slant) in rows:
        kc.ink_text(m, x * ss, y * ss, s, cap=cap * ss, seed=seed, pen=int(pen * ss), slant=slant, track=TRACK)
    a = np.asarray(m.resize((W, H), Image.LANCZOS), np.float32) / 255
    return a


def save_tight(a, name, origin, extra=None, fill=None):
    ys, xs = np.nonzero(a > 0.004)
    y0, y1, x0, x1 = max(0, ys.min() - 4), ys.max() + 5, max(0, xs.min() - 4), xs.max() + 5
    crop = a[y0:y1, x0:x1]
    fc = np.zeros_like(crop) if fill is None else fill[y0:y1, x0:x1]
    im = to_rgba(fc, crop)
    p = os.path.join(OUT, name)
    im.save(p)
    rec = dict(file=os.path.relpath(p, ROOT), page_xy=[int(origin[0] + x0), int(origin[1] + y0)], size=list(im.size),
               sha256=hashlib.sha256(open(p, "rb").read()).hexdigest())
    rec.update(extra or {})
    return rec


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def do_balloon(key, speaker, text, lay, name):
    seed = seed_of(key if key in LINES else "H", text)
    pw = PANEL["H" if key.startswith("H") else key][0]
    im, (bx, by), lines, c = balloon(key, text, lay["c"][0], lay["c"][1], lay["cap"], lay["maxw"], lay["tail"], seed, pw)
    lay = dict(lay, c=c)
    p = os.path.join(OUT, name)
    im.save(p)
    return dict(file=os.path.relpath(p, ROOT), offset_in_panel=[bx, by], size=list(im.size), seed=seed,
                cap=lay["cap"], pen=round(lay["cap"] * PEN_K, 2), outline=OUTLINE, maxw=lay["maxw"],
                centre_in_panel=list(lay["c"]), tail_tip_in_panel=list(lay["tail"]), wrapped_lines=lines,
                speaker=speaker, text=text, sha256=sha(p))


# ------------------------------------------------------------------ the note (handmade card) --
NOTE_FACE = ["À MA CHÈRE", "ODETTE"]


def note_card(face, w, h, seed=21, lines=NOTE_FACE, ss=4):
    """Cut card, pen outline, lettered face (or creased back). RGBA at w x h page px."""
    W_, H_ = w * ss, h * ss
    paper = Image.new("L", (W_, H_), 0)
    ink = Image.new("L", (W_, H_), 0)
    rs = random.Random(11 if face else 12)
    m = 2 * ss
    quad = [(m + rs.uniform(0, 2) * ss, m), (W_ - m, m + rs.uniform(0, 2) * ss), (W_ - m - rs.uniform(0, 2) * ss, H_ - m),
            (m, H_ - m - rs.uniform(0, 2) * ss)]
    ImageDraw.Draw(paper).polygon(quad, fill=255)
    di = ImageDraw.Draw(ink)
    di.line(quad + [quad[0]], fill=255, width=max(2, int(w / 52 * ss)), joint="curve")
    if face:
        cap = min(h * 0.215, 0.84 * w / max(kc.text_width(l, 1.0, TRACK) for l in lines))
        y = (h - cap * (1.75 * (len(lines) - 1) + 1)) / 2
        for i, l in enumerate(lines):
            lw = kc.text_width(l, cap, TRACK)
            kc.ink_text(ink, (w - lw) / 2 * ss, y * ss, l, cap=cap * ss, seed=seed + i, pen=max(2, int(cap * 0.24 * ss)), slant=0.16, track=TRACK)
            y += cap * 1.75
    else:
        di.line([(W_ * 0.52, m * 2), (W_ * 0.5, H_ - m * 2)], fill=150, width=max(1, int(w / 90 * ss)))
    p = np.asarray(paper.resize((w, h), Image.LANCZOS), np.float32) / 255
    i_ = np.asarray(ink.resize((w, h), Image.LANCZOS), np.float32) / 255
    return to_rgba(p, i_)


def loop_arrow():
    W, H = 540, 1800
    m = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(m)
    pts = kc._arc(270 * SS, 960 * SS, 150 * SS, 400 * SS, -80, 262, 90)
    rs = random.Random(9)
    pts = [(x + rs.uniform(-1.5, 1.5) * SS, y + rs.uniform(-1.5, 1.5) * SS) for x, y in pts]
    d.line(pts, fill=255, width=int(8 * SS), joint="curve")
    ex, ey = pts[-1]
    d.polygon([(ex - 28 * SS, ey + 18 * SS), (ex + 26 * SS, ey + 10 * SS), (ex + 4 * SS, ey - 38 * SS)], fill=255)
    return np.asarray(m.resize((W, H), Image.LANCZOS), np.float32) / 255


def main():
    tails = {}
    if "--tail" in sys.argv:
        i = sys.argv.index("--tail")
        k, x, y = sys.argv[i + 1], float(sys.argv[i + 2]), float(sys.argv[i + 3])
        tails[k] = (x, y)
    rec = dict(owner="U2 dialogue-writer", page_size=[3200, 1800], ink=INK, page=PAGE, pen_k=PEN_K,
               method="single-stroke capital alphabet of proposals/kf_common.py (pen polylines), round pen, "
                      "supersampled x3, seeded per balloon; no fonts", balloons={}, alternates={}, furniture={}, note={})
    for key, (spk, text) in LINES.items():
        lay = dict(LAYOUT[key])
        if key in tails:
            lay["tail"] = tails[key]
        rec["balloons"][key] = do_balloon(key, spk, text, lay, f"balloon-{key}.png")
    for key, (spk, text) in ALTS.items():
        lay = dict(LAYOUT["H"])
        rec["alternates"][key] = do_balloon(key, spk, text, lay, f"balloon-{key}.png")
    # margin column furniture (page coords; column 0..540)
    F = rec["furniture"]
    col = (540, 1800)
    items = {
        "title-le-mot": [(40, 74, "LE MOT", 112, 3, 19, 0.1)],
        "title-subtitle": [(52, 262, "OU QUI L'A", 52, 4, 10, 0.06), (52, 342, "LAISSÉ ?", 52, 5, 10, 0.06)],
        "route": [(60, 1520, "A B C H C B A", 46, 40, 8.5, 0.06)],
        "etude-oubapo": [(54, 1636, "ÉTUDE · OUBAPO", 32, 60, 6, 0.06)],
        "credit-daumier": [(54, 1702, "D'APRÈS DAUMIER, 1839", 24, 61, 4.5, 0.06)],
    }
    whole = np.zeros((col[1], col[0]), np.float32)
    for name, rows in items.items():
        a = text_layer(rows, col)
        whole = np.maximum(whole, a)
        F[name] = save_tight(a, f"{name}.png", (0, 0), dict(strings=[r[2] for r in rows], seeds=[r[4] for r in rows],
                                                          caps=[r[3] for r in rows], pens=[r[5] for r in rows]))
    la = loop_arrow()
    whole = np.maximum(whole, la)
    F["loop-arrow"] = save_tight(la, "loop-arrow.png", (0, 0), dict(what="hand-drawn pen loop (ellipse + arrowhead)"))
    p = os.path.join(OUT, "margin-column.png")
    to_rgba(np.zeros_like(whole), whole).save(p)
    F["margin-column"] = dict(file=os.path.relpath(p, ROOT), page_xy=[0, 0], size=[540, 1800], sha256=sha(p),
                              what="all margin furniture in one layer, page coords 0..540 x 0..1800")
    # panel IDs (gutter letters) and film-only speech-act tags
    for k in "ABCH":
        a = text_layer([(6, 6, k, 18, 90 + "ABCH".index(k), 3.2, 0.06)], (40, 40))
        F[f"id-{k}"] = save_tight(a, f"id-{k}.png", (0, 0), dict(string=k, note="paste at panel (x1-26, y1+6); page_xy is relative"))
    tags = ["ACCUSE", "DENY", "PRESS", "REVEAL", "DEFLECT", "JAB", "COUNTER-ACCUSE"]
    for i, t in enumerate(tags):
        cap = 24
        w = int(kc.text_width(t, cap, TRACK)) + 20
        a = text_layer([(8, 8, t, cap, 200 + i, 4.2, 0.06)], (w, 50))
        F[f"tag-o{i + 1}"] = save_tight(a, f"tag-o{i + 1}-{t.lower()}.png", (0, 0),
                                       dict(string=t, occurrence=i + 1, note="film-only annotation layer / annotated page, gutters only"))
    # the note: face (À MA CHÈRE / ODETTE) and back, at page size and a 4x master
    N = rec["note"]
    for tag, (w, h) in {"page": (140, 92), "x4": (560, 368)}.items():
        for face in (True, False):
            im = note_card(face, w, h)
            p = os.path.join(OUT, f"note-{'face' if face else 'back'}-{tag}.png")
            im.save(p)
            N[f"{'face' if face else 'back'}-{tag}"] = dict(file=os.path.relpath(p, ROOT), size=[w, h], sha256=sha(p))
    N["face_text"] = NOTE_FACE
    N["note"] = ("page size 140x92 px is ~12 % smaller than the test shot's card (per the user's note: slightly smaller "
                 "relative to the hands, still legible: cap ~20 px at page scale, ~12 px at 1920 px page fit)")
    # alternate note face for hinge group G2
    im = note_card(True, 140, 92, seed=31, lines=["MON CHER", "ALFRED"])
    p = os.path.join(OUT, "note-face-G2-alfred-page.png")
    im.save(p)
    N["face-G2-alternate"] = dict(file=os.path.relpath(p, ROOT), size=[140, 92], sha256=sha(p), face_text=["MON CHER", "ALFRED"])
    json.dump(rec, open(os.path.join(OUT, "lettering.json"), "w"), ensure_ascii=False, indent=1)
    print("lettering written:", OUT)


if __name__ == "__main__":
    main()
