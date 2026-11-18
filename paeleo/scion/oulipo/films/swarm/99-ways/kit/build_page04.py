"""99 ways, page 04 "Her version" (voice and language; medium: rol-cutout).
The stranger tells it later to a fellow passenger on the train. Cover-page grammar of the rol-cutout kit (butter page,
warm grey band, jumping red/black cover lettering) with Agence Rol press-photo cutouts: the narrator (Rol 34852, 1913,
a woman in a hat with her handbag), the listener (Rol 49112, 1917, cut by exercices-de-style) and a Rol 1933 railway
carriage interior as the band's picture. Below, six press prints of what she saw (the 99-ways-template Rothstein rest
layers, recomposed without balloons), each with a pasted caption slip in her chatty voice; E4-E5 are printed faint
with a pencilled dashed edge, 'as I picture it', because she did not see them.
Writes assets/pages/99-ways/04-her-version.jpg, films/sources/99-ways/masters/04-her-version.png,
films/sources/99-ways/beats/04/b01..b07.png, films/swarm/99-ways/pages/04.json.  Run: python3 -I build_page04.py"""
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
import build_page01 as b01  # noqa: E402  (panel_rest: the Rothstein rest layers without balloons)
from cutpaper99 import hexc  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = CANON["constraints"][3]
assert C["id"] == "her-version"
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
FOR = SRC / "forage"
OUT_JPG = ROOT / "assets/pages/99-ways/04-her-version.jpg"
OUT_PNG = SRC / "masters/04-her-version.png"
BEATS = SRC / "beats/04"
W, H = pen99.PAGE_W, pen99.PAGE_H
OLD = json.load(open(b01.TPL / "page" / "speech.json"))

BUTTER, BUTTER_TOP, BAND = hexc("#fddb8c"), hexc("#fee498"), hexc("#8e847b")
RED, BLACK, SLIP, PRINT_W = hexc("#d6280a"), hexc("#191304"), hexc("#fff3d2"), hexc("#f6f2e8")


# ------------------------------------------------------------------------------------------- tools
def ground():
    F = pen99.sheet99().mean(axis=2)
    F = F - F.mean()
    t = np.linspace(0, 1, H)[:, None, None] ** 0.6
    g = BUTTER_TOP * (1 - t) + BUTTER * t
    return g + F[..., None] * 0.8, F


def shadow(img, m, off=(7, 9), blur=5, op=0.35):
    sh = np.zeros_like(m)
    dx, dy = off
    sh[dy:, dx:] = m[:-dy, :-dx]
    s = cv2.GaussianBlur(sh, (0, 0), blur).astype(np.float32) / 255 * op
    img *= (1 - s[..., None])


def facet_mask(m, r):
    """scissor margin: dilate, then straight facets"""
    return penlib.scissor(m, r) if r else m


def paste(img, rgb, alpha, M, margin=0, margin_col=PRINT_W, sh=True, op=0.35):
    """rgb float (h,w,3) + alpha uint8, affine M (2x3) into img."""
    a = cv2.warpAffine(alpha, M, (W, H), flags=cv2.INTER_LINEAR)
    c = cv2.warpAffine(rgb.astype(np.float32), M, (W, H), flags=cv2.INTER_CUBIC)
    ab = (a > 127).astype(np.uint8) * 255
    if margin:
        pm = facet_mask(ab, margin)
        if sh:
            shadow(img, pm, op=op)
        pa = pm.astype(np.float32)[..., None] / 255
        img[:] = img * (1 - pa) + margin_col * pa
    elif sh:
        shadow(img, ab, op=op)
    af = a.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - af) + c * af
    return a


def affine(cx, cy, scale, deg, w, h):
    M = cv2.getRotationMatrix2D((w / 2, h / 2), deg, scale)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    return M


def ink_at(img, m, x, y, colour=BLACK, alpha=1.0):
    h, w = m.shape
    x, y = int(x), int(y)
    sub = np.zeros((H, W), np.uint8)
    ys, xs, ye, xe = max(0, y), max(0, x), min(H, y + h), min(W, x + w)
    sub[ys:ye, xs:xe] = m[ys - y:ye - y, xs - x:xe - x]
    penlib.ink_onto(img, sub, colour, alpha)


def jumpy(img, text, x, y, cap, seed, colours=(RED, BLACK)):
    """cover lettering: the shared pen hand, letter by letter, each with its own size and baseline; colour by word."""
    rnd = random.Random(seed)
    wi = 0
    for ch in text:
        if ch == " ":
            x += cap * 0.45
            wi += 1
            continue
        c = cap * rnd.uniform(0.82, 1.22)
        m = pen99.letter([ch], c, rnd.randint(0, 99999), weight=0.20)
        m = cv2.dilate(m, np.ones((3, 3), np.uint8))
        yb = y + rnd.uniform(-0.09, 0.09) * cap
        ink_at(img, m, x - c * 0.6, yb - c * 1.15, colours[wi % len(colours)])
        x += m.shape[1] - c * 1.1
    return x


def slip(img, lines, cap, x, y, w, seed, deg=0.0, num=None, num_right=True):
    """a cut caption slip pasted at (x, y) top-left, width w, pen lettering in her voice."""
    let = pen99.letter(lines, cap, seed)
    lh, lw = let.shape
    hh = lh + int(cap * 0.5)
    ww = max(w, lw + int(cap * 0.6))
    rgb = np.zeros((hh, ww, 3), np.float32) + SLIP
    a = np.zeros((hh, ww), np.uint8)
    pts = np.array([(4, 6), (ww - 3, 2), (ww - 5, hh - 4), (3, hh - 2)], np.int32)
    cv2.fillPoly(a, [pts], 255)
    ox = (ww - lw) // 2
    oy = (hh - lh) // 2
    L = np.zeros((hh, ww), np.uint8)
    L[oy:oy + lh, ox:ox + lw] = let
    rgb = rgb * (1 - L[..., None] / 255.0) + BLACK * (L[..., None] / 255.0)
    M = affine(x + ww / 2, y + hh / 2, 1.0, deg, ww, hh)
    paste(img, rgb, a, M, sh=True, op=0.3)
    if num is not None:
        jumpy(img, str(num), (x + ww - 22) if num_right else (x - 22), y + 34, 64, seed + 5, (RED,))
    return ww, hh


def balloon(img, lines, cap, centre, tip, seed):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=0.22, bend=0.10)
    penlib.lay_balloon(img, b, centre)


# ------------------------------------------------------------------------------------------- material
def woman():
    im = np.asarray(Image.open(FOR / "rol34852_woman_rgba.png")).astype(np.float32)
    x0, x1, y0, y1 = 290, 740, 225, 1495
    return im[y0:y1, x0:x1, :3], im[y0:y1, x0:x1, 3].astype(np.uint8)


def man():
    im = np.asarray(Image.open(ROOT / "films/sources/exercices-de-style/forage/man_rgba.png")).astype(np.float32)
    x0, x1, y0, y1 = 180, 1230, 150, 1737
    g = im[y0:y1, x0:x1, :3]
    return g, im[y0:y1, x0:x1, 3].astype(np.uint8)


def sepia(g, k=0.07):
    """one grade for every print: slight warm tone toward the page (<= 8 %)"""
    L = g.mean(axis=2, keepdims=True) if g.ndim == 3 else g[..., None]
    return L * (1 - k) + (L / 255.0 * BUTTER) * k


def wagon():
    g = np.asarray(Image.open(FOR / "rol_wagon_etage_1933_1280.jpg").convert("L")).astype(np.float32)
    g = g[60:900, 60:1230]                       # inside the plate edge (no number, no black rebate)
    g = np.clip((g - 18) / (235 - 18), 0, 1) ** 0.95 * 255
    return g


CROPS = {"P1": (0, 160, 740, 930), "P4": (0, 300, 560, 883), "P5": (40, 0, 940, 937),
         "P3": (0, 140, 730, 900), "P7": (0, 0, 1000, 980), "P8": (150, 0, 1150, 980)}


def rest_print(key):
    c, used = b01.panel_rest(key)
    x0, y0, x1, y1 = CROPS[key]
    return c[y0:y1, x0:x1].mean(axis=2), (x0, y0), used


# ------------------------------------------------------------------------------------------- page
Q = ["Pardon me —", "have you the", "right time?"]
A = ["Ten past four,", "by the clock."]
T = ["Much", "obliged!"]
F = ["Well, here I am...", "and what for?"]
assert " ".join(Q) == LN["question"] and " ".join(A) == LN["answer"] and " ".join(T) == LN["thanks"] and " ".join(F) == LN["forgetting"]

CELLS = [  # key, event, caption (her voice), balloon (lines, cap, centre in print px, tip in print px or 'her'), imagined
    ("P1", "E0", ["There he sat at his", "desk, frowning at some", "slip of paper.", "Up he gets."], None, False),
    ("P4", "E1", ["Well, my watch had", "stopped, so I tapped", "on his glass, polite", "as you please:"], (Q, 44, (0.50, 0.17), "her"), False),
    ("P5", "E2", ["He squints round", "at that big clock", "of his and says:"], (A, 46, (0.50, 0.16), "P5"), False),
    ("P3", "E3", ["So I thanked him,", "and off he went", "the other way."], (T, 52, (0.30, 0.20), "her"), False),
    ("P7", "E4", ["Now I couldn't see,", "mind you, but I'll", "wager he went and", "opened his cupboard..."], None, True),
    ("P8", "E5", ["...and stood there", "like a post, pencil", "on his chin! That", "SERVICE door never", "did open."], (F, 42, (0.45, 0.15), "P8"), True),
]
ROWS = [(1010, 1560), (1585, 2135), (2155, 2690)]
COLS = [(110, 1080), (1120, 2090)]


def build(reveal=7):
    img, F_ = ground()
    rec = {}
    # ---- the band: later, on the train
    by0, by1 = 110, 790
    band = np.zeros((by1 - by0, 1980, 3), np.float32) + BAND + F_[by0:by1, 110:2090, None] * 1.4
    img[by0:by1, 110:2090] = band
    wg = wagon()
    hh, ww = wg.shape
    s = 600 / hh
    pr = np.dstack([sepia(np.dstack([wg] * 3))])
    paste(img, pr, np.full((hh, ww), 255, np.uint8), affine(760, 450, s, 1.2, ww, hh), margin=14)
    wt = pen99.letter(["Later, on the train"], 38, 4410)
    ink_at(img, wt, 2075 - wt.shape[1], 118, hexc("#fbf7ee"))
    # listener (Rol 49112), then the narrator (Rol 34852), who stands in the aisle and overflows the band
    g, a = man()
    s = 560 / g.shape[0]
    paste(img, sepia(np.dstack([g.mean(2)] * 3)), a, affine(1730, by1 - 560 * 0.5 + 6, s, 0, g.shape[1], g.shape[0]), margin=8)
    g, a = woman()
    s = 960 / g.shape[0]
    paste(img, sepia(np.dstack([g.mean(2)] * 3)), a, affine(330, 130 + 480, s, -1.0, g.shape[1], g.shape[0]), margin=8)
    if reveal >= 0:
        balloon(img, ["You'll never guess", "what I saw at", "Randolph today!"], 50, (990, 285), (395, 225), 4420)
        balloon(img, ["Do tell!"], 46, (1500, 330), (1655, 470), 4421)
    # cover line
    jumpy(img, "The agent who forgot!", 760, 935, 92, 4430)
    # ---- six prints of what she saw
    for i, (key, ev, cap_lines, bal, imagined) in enumerate(CELLS):
        if i >= reveal - 1:
            continue
        r, col = divmod(i, 2)
        y0, y1 = ROWS[r]
        x0, x1 = COLS[col]
        g, off, used = rest_print(key)
        ph, pw = g.shape
        sc = 520 / ph
        dw = pw * sc
        photo_left = (r % 2 == 0)
        px = x0 + 20 + dw / 2 if photo_left else x1 - 20 - dw / 2
        py = (y0 + y1) / 2 + 5
        deg = [-1.2, 0.9, 1.1, -0.8, -1.4, 1.0][i]
        rgb = sepia(np.dstack([g] * 3))
        if imagined:   # as she pictures it: a faint print, pale and soft-edged, no white border
            rgb = rgb * 0.45 + BUTTER * 0.55
        rgb = rgb.astype(np.float32)
        alpha = np.full((ph, pw), 255, np.uint8)
        M = affine(px, py, sc, deg, pw, ph)
        if imagined:
            am = paste(img, rgb, alpha, M, margin=0, sh=False)
            # pencilled dashed edge
            cs, _ = cv2.findContours((am > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cnt = max(cs, key=len)[:, 0, :].astype(np.float32)
            dm = np.zeros((H, W), np.uint8)
            for k in range(0, len(cnt) - 30, 52):
                cv2.polylines(dm, [np.int32(cnt[k:k + 30] * 4)], False, 255, 5, cv2.LINE_AA, shift=2)
            penlib.ink_onto(img, dm, hexc("#4a4238"), 0.85)
            tagm = pen99.letter(["as I picture it"], 32, 4450 + i)
            ink_at(img, tagm, px - tagm.shape[1] / 2, py + 520 / 2 + 2, hexc("#4a4238"))
        else:
            paste(img, rgb, alpha, M, margin=16, op=0.4)
        # her caption slip, pasted over the print's inner edge
        sw = 430
        sx = (px + dw / 2 - 60) if photo_left else (px - dw / 2 - sw + 60)
        sx = float(np.clip(sx, x0, x1 - sw))
        sy = y0 + 40 + (i % 2) * 30
        slip(img, cap_lines, 40, sx, sy, sw, 4460 + i, deg=[0.8, -0.6, -1.0, 0.7, 0.9, -0.8][i], num=i + 1, num_right=photo_left)
        # the balloon is pasted on over the print (centre and tail target mapped from print px to page px)
        if bal:
            lines, cap, ctr, tgt = bal
            P = lambda q: M @ np.array([q[0], q[1], 1.0])
            cx, cy = P((ctr[0] * pw, ctr[1] * ph))
            if tgt == "her":
                side = -1 if photo_left else 1           # out of the picture's outer side, toward her at the glass
                tip = P((pw * (0.5 + 0.5 * side), ph * 0.55)) + np.array([45.0 * side, 0.0])            # out of the picture, toward the one who saw it
            else:
                o = OLD[tgt][0]["tail_tip_panel_px"]
                tip = P((o[0] - off[0], o[1] - off[1]))
            bw = pen99.letter(lines, cap, 1).shape[1] * 0.62 + cap
            lo, hi = px - dw / 2 + bw, px + dw / 2 - bw
            cx = float(np.clip(cx, lo, hi)) if lo < hi else float(px)
            cy = max(cy, y0 + cap * 2.4)
            balloon(img, lines, cap, (cx, cy), tip, 4440 + i)
        rec[key] = dict(event=ev, caption=" ".join(cap_lines), imagined=imagined, print_layers=used,
                        balloon=(" ".join(bal[0]) if bal else None))
    pen99.folio(img, 4, C["title"])
    return np.clip(np.round(img), 0, 255).astype(np.uint8), rec


def main():
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS, ROOT / "films/swarm/99-ways/pages"):
        p.mkdir(parents=True, exist_ok=True)
    page, rec = build(7)
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    if "--page-only" in sys.argv:
        print(size)
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    bd = []
    for j in range(1, 8):
        im = page if j == 7 else build(j)[0]
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: " + ("the train band: she begins, 'You'll never guess...'" if j == 1 else
                                     f"print {j - 1} ({CELLS[j - 2][1]}) pasted with her caption slip" +
                                     (" (faint, as she pictures it)" if CELLS[j - 2][4] else "")))
    record = {
        "n": 4, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "sources": ["99-ways:rol-34852-sainte-catherine-1913", "exercices-de-style:rol-49112-homme-pardessus-1917",
                    "99-ways:rol-wagon-a-etage-1933", "99-ways-template:rothstein-randolph-agent-1937",
                    "99-ways-template:rothstein-tavern-clock-1937", "99-ways-template:anrc-gold-key-1922",
                    "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": ["the narrator cut from Rol 34852 (GrabCut with hand-drawn scissor paths, the hat forced in by a drawn path), white scissor margin",
                 "the listener: Rol 49112 cutout reused from exercices-de-style (forage/man_rgba.png)",
                 "band picture: Rol 1933 carriage interior, cropped inside the plate edge, printed with a white border",
                 "six prints of what she saw recomposed from the 99-ways-template rest layers (P1, P4, P5, P3, P7, P8) without the old balloons; one sepia grade (7 %) for every photograph on the page",
                 "E4 and E5 printed faint with a pencilled dashed edge and 'as I picture it' (declared: told as she imagines them)",
                 "caption slips in her voice, the four canonical lines in the shared cut-paper balloons inside the prints (her own two tailed out of the print toward her), her opening line and the listener's 'Do tell!' in the band",
                 "cover grammar: butter ground, warm grey band, jumping red/black cover line lettered letter by letter in the shared pen hand (no font)",
                 "folio '04 / Her version' (pen99.folio)"],
        "events": {k: v for k, v in ((r["event"], f"{k}: {r['caption']}" + (f" | balloon: {r['balloon']}" if r['balloon'] else "")) for k, r in rec.items())},
        "lines": LN,
        "added_lines": {"STRANGER (later, on the train)": "You'll never guess what I saw at Randolph today!", "FELLOW PASSENGER": "Do tell!"},
        "beat": "her telling performed: the band with her opening line, then the six prints pasted one by one with her caption slips; the last two arrive faint, as she pictures them",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "narrator": "every caption is first person ('I', 'my', 'mind you'); the band shows her speaking to a listener on a train",
                       "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/04.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    main()
