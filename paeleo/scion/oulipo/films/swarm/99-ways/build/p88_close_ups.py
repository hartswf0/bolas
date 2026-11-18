"""Page 88 Close-ups only (reduction and expansion; medium: photo-cutout).

Nine panels, every one an extreme close-up cut from the book's photographs: his hand on the memo, the cupboard
latch, her hands at the window, the clock's hands at 4:10, his mouth, her mouth, the key on its hook, his eyes,
the pencil at his chin. No panel shows a whole figure, or even a whole face.
Photographs: Rothstein 1937 Randolph agent (99-ways-template levelled master, 4360 px), Bubley 1943 visitor
(99-ways-template variant-builders hi cutout), Rothstein 1937 tavern clock with its own hands re-set on the hub
(cutout-surgeon pieces), ANRC 1922 key cutout. HANDMADE: memo slip, SERVICE tag, cut-paper hook, balloons, slips,
borders (shared pen hand). Each crop is cut at its source resolution and only resized; one neutral print grade.
Run: python3 -I p88_close_ups.py [beats]
"""
import json
import math
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/kit")
sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
import pen99  # noqa: E402
from pen99 import penlib, ROOT  # noqa: E402
from cutpaper99 import Cut, rect, ellipse  # noqa: E402
import b1m2 as B  # noqa: E402

N, PID, TITLE = 88, "close-ups", "Close-ups only"
W, H = pen99.PAGE_W, pen99.PAGE_H
TPL = ROOT / "films/sources/99-ways-template"
CS = TPL / "cutout-surgeon/pieces"
MAN = json.load(open(ROOT / "films/swarm/99-ways-template/cutouts/manifest.json"))["pieces"]
CAP, BCAP = 38, 44

ROWS = [(110, 580), (620, 1090), (1130, 1600), (1640, 2110), (2150, 2730)]
X0, X1, G = 110, 2090, 40


def split(widths):
    xs, x = [], X0
    for w in widths:
        xs.append((x, x + w))
        x += w + G
    return xs


R1, R2, R3, R4 = split([1180, 760]), split([1000, 940]), split([1180, 760]), split([600, 1340])
BOX = {
    "P1": (*R1[0], ), "P2": R1[1], "P3": R2[0], "P4": R2[1], "P5": R3[0], "P6": R3[1], "P7": R4[0], "P8": R4[1],
    "P9": (X0, X1),
}
ROW_OF = {"P1": 0, "P2": 0, "P3": 1, "P4": 1, "P5": 2, "P6": 2, "P7": 3, "P8": 3, "P9": 4}


def box(k):
    x0, x1 = BOX[k]
    y0, y1 = ROWS[ROW_OF[k]]
    return x0, y0, x1, y1


# ------------------------------------------------------------------ photographs
_C = {}


def roth():
    if "r" not in _C:
        _C["r"] = np.asarray(Image.open(CS / "rothstein.full_levelled.png").convert("L")).astype(np.float32)
    return _C["r"]


def visitor():
    if "v" not in _C:
        im = np.asarray(Image.open(TPL / "variant-builders/pieces/bubley.visitor.hi.png")).astype(np.float32)
        _C["v"] = im[..., :3].mean(axis=2)
    return _C["v"]


def piece(name):
    im = np.asarray(Image.open(CS / f"{name}.png")).astype(np.float32)
    return im[..., :3].mean(axis=2), im[..., 3]


def clock410():
    """the tavern clock face (hands removed by 99-ways-template) with its own two hands re-set on the hub to 4:10"""
    g, a = piece("clock.face")
    hub = MAN["clock.face"]["pivots_local"]["hub"]
    hh, ww = g.shape
    for n in ("clock.hour", "clock.minute"):
        hg, ha = piece(n)
        p = MAN[n]
        piv = p["pivots_local"]["hub"]
        rot = p["set_to_4_10_rotate_deg"]
        M = cv2.getRotationMatrix2D((float(piv[0]), float(piv[1])), -rot, 1.0)
        M[0, 2] += hub[0] - piv[0]
        M[1, 2] += hub[1] - piv[1]
        wg = cv2.warpAffine(hg, M, (ww, hh), flags=cv2.INTER_CUBIC)
        wa = cv2.warpAffine(ha, M, (ww, hh), flags=cv2.INTER_LINEAR) / 255
        # the hand's own shadow on the dial, a few px down-right
        sh = cv2.GaussianBlur(np.roll(np.roll(wa, 6, 0), 5, 1), (0, 0), 4) * 0.35
        g = g * (1 - sh)
        g = g * (1 - wa) + wg * wa
    return g, hub


def grade(g, lo=14, hi=244):
    """one neutral print grade for every crop: the photograph's grey scale mapped into the print's paper/black"""
    t = np.clip(g / 255.0, 0, 1)
    v = lo + (hi - lo) * t
    return np.dstack([v * 1.0, v * 0.985, v * 0.955])


def crop(g, bx, size):
    """crop box (x0, y0, x1, y1) in source px, resized to size (w, h); returns float gray"""
    x0, y0, x1, y1 = [int(round(v)) for v in bx]
    c = g[y0:y1, x0:x1]
    w, h = size
    s = w / c.shape[1]
    return cv2.resize(c, (w, h), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC), s


def fit_box(cx, cy, src_w, aspect):
    """a crop box of width src_w around (cx, cy) with the panel's aspect (w / h)"""
    h = src_w / aspect
    return (cx - src_w / 2, cy - h / 2, cx + src_w / 2, cy + h / 2)


def cutout_onto(img, g, a, x, y, s, deg=0.0, margin=9, shadow=0.42):
    """lay a photo cutout (gray g, alpha a) with its white scissor margin and paper shadow; top-left at (x, y)"""
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((g.shape[1] / 2, g.shape[0] / 2), -deg, s)
    M[0, 2] += x - g.shape[1] / 2 + g.shape[1] * s / 2
    M[1, 2] += y - g.shape[0] / 2 + g.shape[0] * s / 2
    wg = cv2.warpAffine(g, M, (w, h), flags=cv2.INTER_CUBIC)
    wa = cv2.warpAffine(a, M, (w, h), flags=cv2.INTER_LINEAR)
    m = (wa > 127).astype(np.uint8) * 255
    pm = penlib.scissor(m, margin) if margin else m
    penlib.shadow_onto(img, pm, off=6, blur=5, opacity=shadow)
    pa = pm.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - pa) + np.array([246, 242, 232], np.float32) * pa
    af = wa.astype(np.float32)[..., None] / 255
    img[:] = img * (1 - af) + grade(wg) * af
    return M


def cap_slip(img, text, wmax, seed, x=20, y=18, bottom=False, right=False):
    lines = B.wrap(text, CAP, wmax)
    if bottom:
        y = img.shape[0] - 20 - (int(CAP * 1.42) * (len(lines) - 1) + int(CAP * 1.75))
    if right:
        x = img.shape[1] - 20 - int(wmax)
    return B.slip(img, x, y, lines, CAP, seed)


def bal(img, lines, centre, tip, seed, cap=BCAP):
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, (tip[0] - centre[0], tip[1] - centre[1]), seed,
                             tail_w=0.24, bend=0.10)
    penlib.lay_balloon(img, b, centre)


# ------------------------------------------------------------------ the nine close-ups
def size(k):
    x0, y0, x1, y1 = box(k)
    return x1 - x0, y1 - y0


def p1():      # E0 his hand on the desk, the memo slip by it
    w, h = size("P1")
    g, s = crop(roth(), fit_box(2330, 2700, 900, w / h), (w, h))
    img = grade(g)
    # the memo slip (HANDMADE), laid on the desk just right of his fist, under the edge of his ledger
    B.slip(img, 640, 215, ["MEMO  C.V.RY.", "4:15 - open SERVICE door.", "Key in cupboard."], 33, 8801,
           paper=np.array([246, 241, 226], np.float32), tilt=-4, shadow=0.45)
    cap_slip(img, "4:09. The memo under his hand.", 600, 8802)
    return img


def p2():      # E0 the latch of the closed cupboard: where he is going
    w, h = size("P2")
    g, s = crop(roth(), fit_box(3700, 1235, 640, w / h), (w, h))
    img = grade(g)
    cap_slip(img, "Up he gets, for the cupboard.", 560, 8811, bottom=True)
    return img


def p3():      # E1 her hands at the window
    w, h = size("P3")
    g, s = crop(visitor(), fit_box(560, 880, 640, w / h), (w, h))
    img = grade(g)
    cap_slip(img, "At the ticket window:", 480, 8821)
    bal(img, ["Pardon me —", "have you the", "right time?"], (770, 150), (640, 470), 8822)
    return img


def p4():      # E2 the clock's hands at 4:10
    w, h = size("P4")
    g, hub = clock410()
    bx = fit_box(hub[0] + 245, hub[1] - 10, 690, w / h)
    c, s = crop(g, bx, (w, h))
    img = grade(c)
    cap_slip(img, "4:10.", 200, 8831, bottom=True)
    return img


def p5():      # E2 his mouth: the answer
    w, h = size("P5")
    g, s = crop(roth(), fit_box(3060, 1975, 560, w / h), (w, h))
    img = grade(g)
    bal(img, ["Ten past four,", "by the clock."], (300, 150), (560, 300), 8841)
    return img


def p6():      # E3 her mouth: the thanks
    w, h = size("P6")
    g, s = crop(visitor(), fit_box(440, 235, 330, w / h), (w, h))
    img = grade(g)
    bal(img, ["Much", "obliged!"], (560, 120), (390, 330), 8851)
    return img


def p7():      # E4 the key on its hook inside the open cupboard
    w, h = size("P7")
    # the cupboard's inside: a crop of the Rothstein cupboard's dark panelling
    g, s = crop(roth(), fit_box(3330, 1250, 300, w / h), (w, h))
    img = grade(g * 0.55)
    c = Cut(h, w, 8861, ground=img)
    kx = w * 0.42
    c.piece(rect(kx - 14, 40, kx + 14, 110), "#8a8478")                       # hook (cut paper)
    c.strip((kx, 96), (kx + 26, 128), 12, "#8a8478")
    img = c.img
    kg, ka = piece("key")
    sk = 0.66
    cutout_onto(img, kg, ka, kx - kg.shape[1] * sk / 2 + 20, 108, sk, deg=0, margin=8)
    B.slip(img, int(kx + 34), 210, ["SERVICE"], 34, 8862, paper=np.array([238, 228, 196], np.float32), tilt=9, shadow=0.45)
    cap_slip(img, "The cupboard opens.", 440, 8863, bottom=True)
    return img


def p8():      # E5 his eyes, behind the glasses: the errand gone
    w, h = size("P8")
    g, s = crop(roth(), fit_box(3010, 1870, 520, w / h), (w, h))
    img = grade(g)
    cap_slip(img, "There hangs the key. And he...", 640, 8871, bottom=True)
    return img


def p9():      # E5 the pencil at his chin: the forgetting line; the outcome
    w, h = size("P9")
    g, s = crop(roth(), fit_box(3240, 2040, 760, w / h), (w, h))
    img = grade(g)
    bal(img, ["Well, here I am...", "and what for?"], (470, 175), (900, 330), 8881)
    cap_slip(img, "The key stays on its hook. The SERVICE door stays shut.", 1100, 8882, bottom=True)
    return img


PANELS = [("P1", p1), ("P2", p2), ("P3", p3), ("P4", p4), ("P5", p5), ("P6", p6), ("P7", p7), ("P8", p8), ("P9", p9)]


def build(n=9):
    pg = pen99.sheet99().astype(np.float32)
    boxes = []
    for k, fn in PANELS[:n]:
        x0, y0, x1, y1 = box(k)
        m = np.zeros((H, W), np.uint8)
        m[y0:y1, x0:x1] = 255
        penlib.shadow_onto(pg, m, off=7, blur=7, opacity=0.40)
        pg[y0:y1, x0:x1] = fn()
        boxes.append((x0, y0, x1, y1))
    B.frame_border(pg, boxes, w=10, seed=8890)
    return pg


def record(size_):
    rec = {
        "n": N, "id": PID, "title": TITLE, "family": "reduction and expansion", "medium": "photo-cutout", "canon_revision": "c1",
        "rule": "Only extreme close-ups: hand, mouth, clock hand, latch, key, eye, pencil at the chin.",
        "declares": "keeps E0-E5, the four lines and the outcome",
        "file": f"assets/pages/99-ways/{N}-{PID}.jpg",
        "master": f"films/sources/99-ways/masters/{N}-{PID}.png",
        "beats_dir": f"films/sources/99-ways/beats/{N}",
        "build": "films/swarm/99-ways/build/p88_close_ups.py",
        "sources": ["99-ways-template:rothstein-randolph-agent-1937", "99-ways-template:bubley-stranger-1943",
                    "99-ways-template:rothstein-tavern-clock-1937", "99-ways-template:anrc-gold-key-1922",
                    "99-ways-template:loc-blank-sheet-1934", "99-ways:handmade"],
        "made": [
            "nine extreme close-ups cut from the 99-ways-template photographs at their source resolution and only resized, one neutral print grade on all: Rothstein's 1937 Randolph agent (levelled 4360 px master: his fist on the desk, the cupboard latch, his mouth, his eyes behind the glasses, the pencil at his chin, the cupboard panelling), Bubley's 1943 visitor (hi cutout: her clasped hands, her mouth), the Rothstein tavern clock (face with its hands removed, its own hour and minute hands re-set on the hub to 4:10 with a small cast shadow), the ANRC 1922 key cutout laid with a white scissor margin",
            "HANDMADE: the memo slip ('MEMO C.V.RY. / 4:15 - open SERVICE door. / Key in cupboard.') laid on the desk by his fist, the SERVICE tag, a cut-paper hook, caption slips and the four canon lines in the shared cut-paper balloons, hand-ruled borders",
            "folio '88 / Close-ups only' (pen99.folio)",
        ],
        "panels": {
            "P1": "hand: his fist on the desk beside the memo slip (E0)",
            "P2": "latch: the closed cupboard's latch (E0, where he is going)",
            "P3": "hand: her clasped hands at the window; the question (E1)",
            "P4": "clock hand: the hands at 4:10 (E2)",
            "P5": "mouth: his mouth and chin; the answer (E2)",
            "P6": "mouth: her mouth; the thanks (E3)",
            "P7": "key: the brass key on its hook, tagged SERVICE, inside the open cupboard (E4)",
            "P8": "eye: his eyes behind the glasses, cast down (E5)",
            "P9": "pencil at the chin: the forgetting line; caption: key stays, SERVICE door shut (E5, outcome)",
        },
        "events": {"E0": "P1-P2", "E1": "P3", "E2": "P4-P5", "E3": "P6", "E4": "P7", "E5": "P8-P9"},
        "lines": {"question": "Pardon me — have you the right time?", "answer": "Ten past four, by the clock.",
                  "thanks": "Much obliged!", "forgetting": "Well, here I am... and what for?"},
        "substitutions": "none",
        "beat": "the cutting-in performed: the close-ups are laid one after another, hand, latch, her hands and question, the clock at 4:10, the two mouths, the key, the eyes, and last the pencil at the chin with the forgetting line",
        "beat_frames": ["b01: P1-P2 (hand on the memo, latch)", "b02: + P3 her hands, the question", "b03: + P4 the clock at 4:10",
                        "b04: + P5 his mouth, the answer", "b05: + P6 her mouth, the thanks", "b06: + P7 the key on its hook",
                        "b07: + P8 his eyes", "b08: + P9 pencil at the chin, the forgetting line (the page)"],
        "self_check": {
            "size_px": [W, H], "jpeg_bytes": size_, "jpeg_quality": 90, "in_target_0.4_1.2MB": 400000 <= size_ <= 1200000,
            "panels": 9, "whole_figures": 0, "whole_faces": 0,
            "check": "No panel shows a whole figure: each crop is a part of a body or object (largest crop: the pencil-at-chin band, chin to hand); checked by the maker on the full page",
            "evidence": "perceptually judged (from the full page) by the maker; blind reading pending",
        },
    }
    B.write_record(rec)
    B.credit_pages(rec["sources"], N)


if __name__ == "__main__":
    page = build()
    img, size_ = B.save_page(page, N, PID, TITLE)
    print("jpeg bytes", size_)
    record(size_)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        fr = []
        for n in range(2, 9):
            p = np.clip(np.round(build(n)), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            fr.append(cv2.resize(p, (960, 1242), interpolation=cv2.INTER_AREA))
        fr.append(cv2.resize(img, (960, 1242), interpolation=cv2.INTER_AREA))
        print("beats", B.save_beats(N, fr))
