"""99 ways, page 17 "Ninety-nine words" (formal / Oulipian rule; medium: photo-cutout).
The incident as six photographic prints mounted album-fashion on the LoC 1934 sheet, each a 99-ways-template rest panel
(Rothstein 1937 agent and office, Rothstein clock, ANRC key; FORAGED, PD) with its canon balloon and a pencilled
caption beneath. Every word on the page outside the folio line, the words standing in the pictures included (the memo's
pencil, TICKET OFFICE on the glass, the SERVICE card and tag), totals exactly 99; the outer margin tallies them in
pencil gates of five, one bundle per print, beside its row. The tally uses no figures, so it adds no words.
A word = a run of characters containing a letter or a digit ('4:15' is one word; a dash alone is not).
The memo's printed head ('MEMO C.V.RY.' and its rules) is left out of this page so every word stays legible.
Run: python3 -I p17_ninety_nine_words.py"""
import json
import random
import re
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
import pen99  # noqa: E402
from pen99 import penlib, ROOT, TPL  # noqa: E402
from cutpaper99 import hexc  # noqa: E402

CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == "ninety-nine-words"][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
SRC = ROOT / "films/sources/99-ways"
OUT_JPG = ROOT / "assets/pages/99-ways/17-ninety-nine-words.jpg"
OUT_PNG = SRC / "masters/17-ninety-nine-words.png"
BEATS = SRC / "beats/17"
REST = TPL / "page" / "rest"
OLD = json.load(open(TPL / "page" / "speech.json"))
W, H = pen99.PAGE_W, pen99.PAGE_H
GRAPH = hexc("#4f4b47")
WHITE = np.array([246, 245, 240], np.float32)

# prints: (rest panel, event, words standing in the picture, balloon lines, balloon cap, caption)
PRINTS = [
    ("P1", "E0", ["4:15", "open", "SERVICE", "door.", "Key", "in", "cupboard."], None, None,
     "Randolph station, one September afternoon. The agent reads his memo, rises, and sets off for the key."),
    ("P4", "E1", ["TICKET", "OFFICE."], ["Pardon me —", "have you the", "right time?"], 40,
     "On his way across, a lady at the window stops him."),
    ("P5", "E2", [], ["Ten past four,", "by the clock."], 58,
     "He looks up at the wall clock and answers."),
    ("P6", "E3", ["TICKET", "OFFICE."], ["Much", "obliged!"], 66,
     "She thanks him and goes."),
    ("P7", "E4", ["SERVICE", "SERVICE"], None, None,
     "He opens the cupboard. There hangs the brass key, tagged."),
    ("P8", "E5", ["SERVICE", "SERVICE"], ["Well, here I am...", "and what for?"], 58,
     "Pencil at his chin, he stands there. The key stays."),
]
for p in PRINTS:
    if p[3]:
        assert " ".join(p[3]) in LN.values(), p


def words(s):
    return [t for t in s.split() if re.search(r"[A-Za-z0-9]", t)]


def count(p):
    return len(p[2]) + (len(words(" ".join(p[3]))) if p[3] else 0) + len(words(p[5]))


TOTAL = sum(count(p) for p in PRINTS)
SKIP = {"P1": {"memo.shadow", "memo", "memo.print", "memo.pencil"}}   # the template memo, re-made larger below


def rest_panel(key):
    d = REST / key
    c = None
    for r in json.load(open(d / "layers.json"))["layers"]:
        if r["name"].startswith("b_") or r["name"] == "border" or r["name"] in SKIP.get(key, ()):
            continue
        im = np.asarray(Image.open(d / r["file"])).astype(np.float32)
        if c is None:
            c = im[..., :3].copy()
        else:
            a = im[..., 3:4] / 255
            c = c * (1 - a) + im[..., :3] * a
    if key == "P1":
        memo_big(c, (282, 806), 340, -6, 1701)
    return c


def memo_big(c, ctr, w, deg, seed):
    """HANDMADE: the memo slip re-made for this page at a size where its pencil can be read and counted"""
    h = w * 0.54
    R = cv2.getRotationMatrix2D((0, 0), deg, 1.0)
    pts = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]], np.float32) @ R[:, :2].T + np.float32(ctr)
    m = np.zeros(c.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(pts * 4)], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(c, m, off=5, blur=4, opacity=0.4)
    c[:] = c * (1 - m[..., None] / 255) + np.float32([246, 244, 236]) * (m[..., None] / 255)
    let = pen99.letter(["4:15 — open", "SERVICE door.", "Key in cupboard."], w * 0.105, seed)
    lh, lw = let.shape
    M = cv2.getRotationMatrix2D((lw / 2, lh / 2), deg, 1.0)
    M[0, 2] += ctr[0] - lw / 2
    M[1, 2] += ctr[1] - lh / 2
    sub = cv2.warpAffine(let, M, (c.shape[1], c.shape[0]))
    penlib.ink_onto(c, sub, np.float32([40, 38, 38]))


def balloon_on(canvas, lines, cap, tip_old, centre_old, seed):
    h, w = canvas.shape[:2]
    let = pen99.letter(lines, cap, seed + 1)
    rx = let.shape[1] * 0.5 * 1.18 + cap * 0.35 + 14
    ry = let.shape[0] * 0.5 * 1.10 + cap * 0.30 + 14
    cx = float(np.clip(centre_old[0], rx + 18, w - rx - 18))
    cy = float(np.clip(centre_old[1], ry + 18, h - ry - 18))
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip_old[0] - cx, tip_old[1] - cy), seed, tail_w=0.24, bend=0.09)
    penlib.lay_balloon(canvas, b, (cx, cy))


def make_print(i, ph):
    key, ev, _, lines, cap, _ = PRINTS[i]
    c = rest_panel(key)
    if lines:
        o = OLD[key][0]
        ctr = list(o["centre_panel_px"])
        if key == "P4":
            ctr = [262, 800]                        # below the lettering on the glass, so TICKET OFFICE. stays legible
        balloon_on(c, lines, cap, o["tail_tip_panel_px"], ctr, 1700 + i * 13)
    hh, ww = c.shape[:2]
    pw = int(round(ww * ph / hh))
    im = cv2.resize(c, (pw, ph), interpolation=cv2.INTER_AREA)
    return im


# ------------------------------------------------------------------ layout
X0, X1 = 110, 1800
ROWS = [(0, 1, 610), (2, 3, 590), (4, 5, 640)]        # (left print, right print, print height)
BORD = 18
CAP_CAP = 38
ROW_Y = [118, 0, 0]
CAPW = 600
TALLY_X0 = 1858


def caption_lines(text, maxw, cap, seed):
    """break a caption into lines that fit maxw px in the pen hand"""
    out, cur = [], ""
    for wd in text.split():
        t = (cur + " " + wd).strip()
        if pen99.letter([t], cap, seed).shape[1] - cap * 1.2 > maxw and cur:
            out.append(cur)
            cur = wd
        else:
            cur = t
    out.append(cur)
    return out


def paste_mask(pg, m, x, y, colour=None):
    sub = np.zeros(pg.shape[:2], np.uint8)
    h, w = m.shape
    sub[y:y + h, x:x + w] = m
    penlib.ink_onto(pg, sub, penlib.INK if colour is None else colour)


def mount(pg, im, x, y, seed):
    """the print with its white border, laid with one shadow, held by four black paper photo corners"""
    h, w = im.shape[:2]
    m = np.zeros(pg.shape[:2], np.uint8)
    rnd = random.Random(seed)
    m[y - BORD:y + h + BORD, x - BORD:x + w + BORD] = 255
    penlib.shadow_onto(pg, m, off=6, blur=5, opacity=0.33)
    pg[y - BORD:y + h + BORD, x - BORD:x + w + BORD] = WHITE
    pg[y:y + h, x:x + w] = im
    L = 62
    for (cx, cy, sx, sy) in ((x - BORD, y - BORD, 1, 1), (x + w + BORD, y - BORD, -1, 1), (x - BORD, y + h + BORD, 1, -1),
                             (x + w + BORD, y + h + BORD, -1, -1)):
        tri = np.array([[cx - sx * 6, cy - sy * 6], [cx + sx * L, cy - sy * 6], [cx - sx * 6, cy + sy * L]], np.float32)
        tm = np.zeros(pg.shape[:2], np.uint8)
        cv2.fillPoly(tm, [np.int32(tri * 4)], 255, cv2.LINE_AA, shift=2)
        penlib.shadow_onto(pg, tm, off=3, blur=2, opacity=0.35)
        pg[:] = pg * (1 - tm[..., None] / 255) + hexc("#1d1b19") * (tm[..., None] / 255)


def tally(pg, n, x0, y0, seed):
    """n pencil ticks in gates of five (four strokes and a bar), three gates a line. Returns bottom y."""
    gw, gh, sp, lh = 50, 50, 22, 74
    k = 0
    line = 0
    while k < n:
        for g in range(3):
            if k >= n:
                break
            take = min(5, n - k)
            gx = x0 + g * (gw + sp)
            gy = y0 + line * lh
            m = np.zeros(pg.shape[:2], np.uint8)
            for t in range(min(4, take)):
                xx = gx + 4 + t * 13
                penlib.brush_line(m, [(xx, gy), (xx + 1, gy + gh)], 3.6, seed + k * 7 + t, tremor=0.5)
            if take == 5:
                penlib.brush_line(m, [(gx - 6, gy + gh - 8), (gx + gw + 2, gy + 8)], 3.4, seed + k * 7 + 5, tremor=0.5)
            penlib.ink_onto(pg, m, GRAPH)
            k += take
        line += 1
    return y0 + line * lh


def build(captions_upto=6):
    pg = pen99.sheet99()
    rec = []
    tally_counts = []
    for r, (a, b, ph) in enumerate(ROWS):
        ims = [make_print(a, ph), make_print(b, ph)]
        ws = [im.shape[1] + 2 * BORD for im in ims]
        gap = (X1 - X0 - sum(ws)) / 3
        x = X0 + gap
        y = ROW_Y[r] + BORD
        if r + 1 < len(ROW_Y):
            ncap = max(len(caption_lines(PRINTS[k][5], CAPW, CAP_CAP, 1720 + k)) for k in (a, b))
            ROW_Y[r + 1] = int(ROW_Y[r] + 2 * BORD + ph + ncap * CAP_CAP * 1.42 + CAP_CAP * 0.8 + 50)
        caps = []
        for j, (i, im) in enumerate(zip((a, b), ims)):
            px = int(x + BORD)
            mount(pg, im, px, y, 1710 + i)
            cw = im.shape[1] + 2 * BORD
            if i < captions_upto:
                lines = caption_lines(PRINTS[i][5], CAPW, CAP_CAP, 1720 + i)
                m = pen99.letter(lines, CAP_CAP, 1720 + i)
                paste_mask(pg, m, int(x + cw / 2 - m.shape[1] / 2), y + ph + BORD + 10)
            n_here = len(PRINTS[i][2]) + (len(words(" ".join(PRINTS[i][3]))) if PRINTS[i][3] else 0) + \
                (len(words(PRINTS[i][5])) if i < captions_upto else 0)
            tally_counts.append(n_here)
            rec.append(dict(print=PRINTS[i][0], event=PRINTS[i][1], words=n_here))
            x += cw + gap
    # the margin tally: one bundle per print, two bundles beside each row, a pencil stroke between rows
    ty = None
    for r in range(3):
        y = ROW_Y[r] + 30
        for j in range(2):
            y = tally(pg, tally_counts[2 * r + j], TALLY_X0, y, 1750 + 2 * r + j) + 44
            if j == 0:
                m = np.zeros(pg.shape[:2], np.uint8)
                cv2.circle(m, (TALLY_X0 + 100, int(y - 32)), 5, 255, -1, cv2.LINE_AA)
                penlib.ink_onto(pg, m, GRAPH)
        if r < 2:
            m = np.zeros(pg.shape[:2], np.uint8)
            penlib.brush_line(m, [(TALLY_X0 - 8, ROW_Y[r + 1] - 40), (2086, ROW_Y[r + 1] - 42)], 2.4, 1790 + r, tremor=0.4)
            penlib.ink_onto(pg, m, GRAPH)
    # the closing double rule under the last bundle
    m = np.zeros(pg.shape[:2], np.uint8)
    yb = y + 4
    for dy in (0, 12):
        penlib.brush_line(m, [(TALLY_X0 - 8, yb + dy), (2086, yb + dy + 1)], 2.6, 1795 + dy, tremor=0.4)
    penlib.ink_onto(pg, m, GRAPH)
    pen99.folio(pg, 17, C["title"])
    return np.clip(np.round(pg), 0, 255).astype(np.uint8), rec, sum(tally_counts)


def main():
    assert TOTAL == 99, TOTAL
    for p in (OUT_JPG.parent, OUT_PNG.parent, BEATS):
        p.mkdir(parents=True, exist_ok=True)
    page, rec, ticks = build(6)
    assert ticks == 99
    Image.fromarray(page).save(OUT_PNG, compress_level=6)
    Image.fromarray(page).save(OUT_JPG, quality=90, dpi=(300, 300))
    size = OUT_JPG.stat().st_size
    print("jpeg", size, "ticks", ticks)
    if "--page-only" in sys.argv:
        return
    for f in BEATS.glob("b*.png"):
        f.unlink()
    bd = []
    running = 0
    for j, up in enumerate(range(0, 7), 1):
        im, _, t = build(up) if up < 6 else (page, None, ticks)
        Image.fromarray(im).resize((960, 1242), Image.LANCZOS).save(BEATS / f"b{j:02d}.png")
        bd.append(f"b{j:02d}: " + ("the six prints with only their own words (signs, memo, balloons), tallied: " if up == 0 else
                                   f"+ caption {up} ({PRINTS[up - 1][1]}) pencilled and its words ticked off: ") + f"{t} ticks")
    record = {
        "n": 17, "id": C["id"], "title": C["title"], "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": str(OUT_JPG.relative_to(ROOT)), "master": str(OUT_PNG.relative_to(ROOT)), "beats_dir": str(BEATS.relative_to(ROOT)),
        "build": "films/swarm/99-ways/build/p17_ninety_nine_words.py",
        "sources": ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:rothstein-tavern-clock-1937",
                    "99-ways-template:anrc-gold-key-1922", "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "six photographic prints recomposed from the 99-ways-template rest layers P1, P4, P5, P6, P7, P8 (Rothstein 1937 office and agent cutouts, Rothstein clock at 4:10, ANRC key on its hook; the template's handmade memo, SERVICE card, hook and tag), the old b1 balloons and the memo's printed head left out",
            "each print mounted album-fashion: white print border, one shadow, four black paper photo corners (handmade)",
            "the four canon lines as fresh cut-paper balloons in the shared pen hand (penlib.balloon_piece), tails at the template's own targets",
            "six pencilled captions in the shared pen hand, written to make the page's words come to exactly 99",
            "the margin tally: 99 graphite ticks in gates of five, one bundle per print, two bundles beside each row, a rule between rows and a closing double rule; the tally uses no figures, so it adds no words",
            "folio '17 / Ninety-nine words' (pen99.folio)"],
        "word_count": {p[0] + " " + p[1]: {"in_picture": p[2], "balloon": words(" ".join(p[3])) if p[3] else [],
                                           "caption": words(p[5]), "total": count(p)} for p in PRINTS},
        "counting_convention": "a word is any space-separated run containing a letter or digit ('4:15' counts once; the dashes in the memo and in the question are not words); every lettered word on the page outside the folio line is counted, including those standing in the photographs (TICKET OFFICE. on the glass, the SERVICE card and tag, the memo's pencil). The clock dial's numerals are part of the photographed clock and not counted.",
        "events": {p[1]: f"print {p[0]}: {p[5]}" + (f" | balloon: {' '.join(p[3])}" if p[3] else "") for p in PRINTS},
        "lines": LN,
        "beat": "the captions are pencilled one by one under the prints and each caption's words are ticked off in the margin tally, which grows from the pictures' own 37 words to 99",
        "beat_frames": bd,
        "self_check": {"size_px": [page.shape[1], page.shape[0]], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "words_total": TOTAL, "tally_ticks": ticks, "per_print": rec, "lines_verbatim": True,
                       "pending": "independent blind reading not run by the maker"},
    }
    json.dump(record, open(ROOT / "films/swarm/99-ways/pages/17.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(record["self_check"], indent=1))


if __name__ == "__main__":
    print("TOTAL words", TOTAL, [count(p) for p in PRINTS])
    if "--count" not in sys.argv:
        main()
