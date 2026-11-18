"""Page 53 Tautogram (formal / Oulipian rule; medium: cut-paper).

Every word of every caption begins with K. The six panels are re-cut from page 16's HANDMADE cut-paper kit
(p16_fewest_marks: agent, stranger, clock, ticket window, cupboard on its left jamb, key with SERVICE tag, SERVICE door,
memo, desk; films/swarm/99-ways/kit/cutpaper99.py), with the four lines rewritten as K-words (declared by the canon:
'lines rewritten as K-words'). Each caption is a pasted cut-paper slip opening on a large vermilion cut-paper K; in the
shared pen hand the initial K of every word is inked in vermilion, so the rule shows itself.
Licence of spelling: hard C and QU are respelled with K (klock, kupboard, kwarter, kwhy), the old tautogram trick;
every other word is a dictionary K-word. Object lettering painted on the props (the memo slip, TICKET OFFICE, the
SERVICE card and tag) is the canon's lettering on things, not caption, and is kept.
Run: python3 -I p53_tautogram_k.py
"""
import json
import re
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import Cut, rect, hexc  # noqa: E402
import p16_fewest_marks as p16  # noqa: E402
from b1m2 import save_page, save_beats, write_record, credit_pages  # noqa: E402

N, PID, TITLE = 53, "tautogram-k", "Tautogram"
CANON = json.load(open(ROOT / "films/swarm/99-ways/canon.json"))
C = [c for c in CANON["constraints"] if c["id"] == PID][0]
LN = {k: v["text"] for k, v in CANON["incident"]["lines"].items()}
W, H = pen99.PAGE_W, pen99.PAGE_H
RED = hexc("#b0352a")
SLIP = "#f3ead3"

CAPTIONS = [
    "Keeper knows: key kept kupboard-side. Keeper kommences, keenly.",
    "Kiosk! Kindly kustomer kalls keeper.",
    "Keeper kranes klockward, kalkulates.",
    "Kustomer, kontent, kwits kiosk.",
    "Kupboard kracked: key kept, klearly.",
    "Key kept. Keeper kaput. Kloset kept klosed.",
]
# the four lines, rewritten as K-words (substitutions recorded)
KQ = ["Kindly, keeper:", "know klock-kount?"]
KA = ["Klock kalls:", "kwarter-past,", "kut kwintet."]
KT = ["Kudos, kind", "keeper!"]
KF = ["Keeper's kome...", "kwhy?"]
GLOSS = {"question": ("Pardon me — have you the right time?", " ".join(KQ)),
         "answer": ("Ten past four, by the clock.", " ".join(KA)),
         "thanks": ("Much obliged!", " ".join(KT)),
         "forgetting": ("Well, here I am... and what for?", " ".join(KF))}


def words(s):
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", s)


def all_k(texts):
    return all(w[0] in "Kk" for t in texts for w in words(t))


# ------------------------------------------------------------------ pen lines with vermilion initials
def kline(text, cap, seed, skip_first=False):
    """one pen line (penlib layout reproduced to find each glyph's x) -> (ink mask, vermilion mask)"""
    t = pen99.clean(text)
    m = pen99.letter([t], cap, seed)
    red = np.zeros_like(m)
    x = cap * 0.6 + (m.shape[1] - (sum(penlib.GLYPHS[c][0] * cap + cap * .1 for c in t) - cap * .1) - cap * 1.2) / 2
    prev = " "
    for i, ch in enumerate(t):
        adv = penlib.GLYPHS[ch][0] * cap
        if ch in "Kk" and not prev.isalpha() and prev not in "'-" and not (skip_first and i == 0):
            x0, x1 = int(x - cap * 0.08), int(x + adv * 0.86)
            red[:, max(0, x0):x1] = m[:, max(0, x0):x1]
        prev = ch
        x += adv + cap * .1
    return m, red


def wrap(text, cap, width):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if cur and sum(penlib.GLYPHS[c][0] * cap + cap * .1 for c in pen99.clean(t)) > width:
            out.append(cur)
            cur = w
        else:
            cur = t
    out.append(cur)
    return out


def paste(dst, m, x, y):
    h, w = m.shape
    sub = np.zeros(dst.shape[:2], np.uint8)
    ys, xs, ye, xe = max(0, y), max(0, x), min(dst.shape[0], y + h), min(dst.shape[1], x + w)
    sub[ys:ye, xs:xe] = m[ys - y:ye - y, xs - x:xe - x]
    return sub


def caption(pg, k, box, write=True):
    """a cut-paper slip; the caption's first K cut large in vermilion paper; the rest in the pen hand"""
    x0, y0, x1, y1 = box
    c = Cut(H, W, seed=5300 + k, ground="#ffffff", fibre_off=(k * 97, k * 211))
    c.img = pg              # cut onto the page as it stands (no second fibre pass over the sheet)
    c.piece(np.float32([(x0 + 4, y0 + 6), (x1 - 2, y0), (x1 + 2, y1 - 4), (x0, y1)]), SLIP, opacity=0.32)
    if not write:
        return c.img
    text = CAPTIONS[k]
    capd = 132
    c.cut_letters(["K"], capd, (x0 + 78, (y0 + y1) / 2 + 6), "#b0352a", 5310 + k, margin=1.5)
    cap = 42
    rest = text[1:]
    lines = wrap(rest, cap, (x1 - x0) - 190)
    if len(lines) > 1:   # later lines start flush with the drop cap's right side
        lines = [lines[0]] + wrap(" ".join(lines[1:]), cap, (x1 - x0) - 190)
    lh = cap * 1.42
    top = (y0 + y1) / 2 - lh * len(lines) / 2 - cap * 0.55
    for i, ln in enumerate(lines):
        m, red = kline(ln, cap, 5320 + k * 10 + i, skip_first=False)
        lx = x0 + 150 - int(cap * 0.6)
        ly = int(top + i * lh)
        penlib.ink_onto(c.img, paste(c.img, m, lx, ly))
        penlib.ink_onto(c.img, paste(c.img, red, lx, ly), RED)
    return c.img


# ------------------------------------------------------------------ layout
PW, PH = p16.PW, p16.PH          # 970 x 640 panels
COLX = [110, 1120]
CAPH, CGAP, RGAP = 186, 14, 50
ROWS = [110 + r * (CAPH + CGAP + PH + RGAP) for r in range(3)]


def build(upto=6, slips=True):
    p16.Q, p16.A, p16.T, p16.F = KQ, KA, KT, KF
    pg = pen99.sheet99()
    boxes = []
    for n in range(1, 7):
        col, row = (n - 1) % 2, (n - 1) // 2
        x0, yc = COLX[col], ROWS[row]
        y0 = yc + CAPH + CGAP
        boxes.append((x0, y0, x0 + PW, y0 + PH))
        pg[y0:y0 + PH, x0:x0 + PW] = p16.panel(n, 9)
        if slips:
            pg = caption(pg, n - 1, (x0 - 6, yc, x0 + PW + 6, yc + CAPH), write=(n - 1) < upto)
    bm = penlib.border_mask(pg.shape[:2], boxes, 8, 5390)
    penlib.ink_onto(pg, bm)
    return pg, boxes


if __name__ == "__main__":
    assert all_k(CAPTIONS), [w for t in CAPTIONS for w in words(t) if w[0] not in "Kk"]
    assert all_k(KQ + KA + KT + KF)
    page, boxes = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size, "bottom", boxes[-1][3])
    frames = []
    for u in range(0, 7):
        p = img if u == 6 else np.clip(np.round(build(u)[0]), 0, 255).astype(np.uint8)
        if u < 6:
            pen99.folio(p, N, TITLE)
        frames.append(p)
    save_beats(N, frames)
    src = ["99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"]
    credit_pages(src, N)
    nwords = sum(len(words(t)) for t in CAPTIONS + KQ + KA + KT + KF)
    rec = {
        "n": N, "id": PID, "title": TITLE, "rule": C["rule"], "medium": C["medium"], "family": C["family"],
        "canon_revision": CANON["revision"], "declares": C["declares"],
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg", "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p53_tautogram_k.py (panels: p16_fewest_marks.py; cut paper: kit/cutpaper99.py)",
        "sources": src,
        "made": [
            "six panels E0-E5 re-cut from page 16's HANDMADE cut-paper kit (p16_fewest_marks.panel: scissor-faceted flat papers with the LoC 1934 sheet's fibre as relative tone, one down-right paper shadow): memo on the desk, the stranger behind the TICKET OFFICE glass, the clock at 4:10, the cupboard open on its left jamb with the key on its hook tagged SERVICE, the SERVICE door shut",
            "six caption slips cut from cream paper, each opening on a large vermilion cut-paper K (cutpaper99.cut_letters: the shared pen hand's K cut out of paper); the caption written on in the shared pen hand with the initial K of every word inked in vermilion",
            "the four lines rewritten as K-words in the shared cut-paper balloons (penlib.balloon_piece)",
            "hand-ruled borders (penlib.border_mask); folio '53 / Tautogram' (pen99.folio)"],
        "captions": CAPTIONS,
        "events": {"E0": "panel 1: memo on the desk, he rises; 'Keeper knows: key kept kupboard-side. Keeper kommences, keenly.'",
                   "E1": "panel 2: the stranger at the glass; 'Kiosk! Kindly kustomer kalls keeper.'; balloon 'Kindly, keeper: know klock-kount?'",
                   "E2": "panel 3: head back to the clock at 4:10; 'Keeper kranes klockward, kalkulates.'; balloon 'Klock kalls: kwarter-past, kut kwintet.'",
                   "E3": "panel 4: she turns away; 'Kustomer, kontent, kwits kiosk.'; balloon 'Kudos, kind keeper!'",
                   "E4": "panel 5: the cupboard open, key on its hook; 'Kupboard kracked: key kept, klearly.'",
                   "E5": "panel 6: pencil to chin; 'Key kept. Keeper kaput. Kloset kept klosed.'; balloon 'Keeper's kome... kwhy?'"},
        "lines": LN,
        "substitutions": {k: {"canon": a, "page": b} for k, (a, b) in GLOSS.items()},
        "substitution_notes": "answer: 'quarter past, cut [a] quintet' = quarter past less five = ten past (the clock in the panel reads 4:10); 'Kloset' is the SERVICE door; hard c and qu respelled with K (klock, kupboard, kustomer, kwarter, kwintet, kwits, kwhy, kalkulates, kracked, kranes, kut, kome, kontent, kommences, kalls, klosed, kloset, klearly), every other word a dictionary K-word (keeper, key, kept, knows, keenly, kiosk, kindly, kind, know, kudos, kaput)",
        "beat": "the caption slips are written on one by one: each slip gets its cut vermilion K, then its K-words",
        "beat_frames": ["b01: the six panels with six blank cut slips"] + [f"b{u + 1:02d}: slips 1-{u} written" for u in range(1, 7)],
        "self_check": {"size_px": [2200, 2850], "jpeg_bytes": size, "jpeg_quality": 90,
                       "in_target_0.4_1.2MB": 400000 <= size <= 1200000,
                       "every_caption_word_begins_with_k": all_k(CAPTIONS),
                       "every_balloon_word_begins_with_k": all_k(KQ + KA + KT + KF),
                       "words_checked": nwords,
                       "outside_rule": "object lettering on the props (memo slip, TICKET OFFICE, SERVICE card and tag) and the folio line",
                       "check": "Every caption word begins with K (machine-checked on the text; vermilion initials let a reader check by eye)",
                       "pending": "independent blind reading not run by the maker"},
    }
    write_record(rec)
    print(json.dumps(rec["self_check"], indent=1))
