"""Page 79 Stutter (reduction and expansion; medium: brush-plate).

Every beat is drawn twice in a row, the second slightly altered, the errand already fading.
Six beats (E0-E5), each printed twice side by side from page 29's HANDMADE brush plate of the office: the first pull
fully inked, the second a ghost pull (the plate printed again without re-inking: paler, a few px off register) with
the figure redrawn a little moved. The captions stutter (the second repeats itself) and the errand's own words
(key, SERVICE door, 4:15, cupboard) lose ink panel by panel until they are gone; the four canon lines are kept.
Reuses build/p29_one_fixed_lens.py (plate, clock hands, cupboard door, brushed figures, brushed balloons; plate
geometry of p07, the dab-chain brush of moins-dun-quart-de-seconde-pour-vivre via brushkit), b1m2 figures,
the ANRC 1922 key cutout.  Run: python3 -I p79_stutter.py [beats]
"""
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p29_one_fixed_lens as P
import p07_two_panels as p7

N, PID, TITLE = 79, "stutter", "Stutter"
SHEET = cv2.GaussianBlur(P.SHEET, (0, 0), 0.6)
AY = P.AGENT_Y
WX = P.WX

# ------------------------------------------------------------------ layout: 3 rows x (pair, pair)
PWD, PIC_H, CAP_H = 469, 672, 156
GIN, GOUT, GROW = 14, 74, 40
XS = [110, 110 + PWD + GIN, 110 + 2 * PWD + GIN + GOUT, 110 + 3 * PWD + 2 * GIN + GOUT]
ROWS = [110 + r * (PIC_H + CAP_H + GROW) for r in range(3)]
CROP_W, CROP_Y0 = 740, 110
CROP_H = int(round(CROP_W * PIC_H / PWD))       # 1061


def boxes():
    out = []
    for r in range(3):
        for c in range(4):
            out.append((XS[c], ROWS[r], XS[c] + PWD, ROWS[r] + PIC_H))
    return out


BOXES = boxes()

Q = ["Pardon me —", "have you the", "right time?"]
A_ = ["Ten past four,", "by the clock."]
TH = ["Much", "obliged!"]
F = ["Well, here I", "am... and", "what for?"]


# ------------------------------------------------------------------ the six beats, each in two drawings (alt=0/1)
def b_e0(c, alt):
    P.clock_hands(c, 4, 9, 7901); P.door_closed(c, 7902)
    x = 930 + 34 * alt
    P.figs(c, agent(x, AY, face=1, scale=0.86, legs=(10 + 8 * alt, -10 - 6 * alt), sh=-10 - 6 * alt, el=18, lean=2 + alt,
                    pencil_deg=200), 7903 + alt)


def b_e1(c, alt):
    P.clock_hands(c, 4, 10, 7911); P.door_closed(c, 7902)
    P.figs(c, stranger(WX - 10, P.SILL + 6, face=1, scale=1.25, glove=True, nod=4 * alt), 7912 + alt)
    P.figs(c, agent(630 + 22 * alt, AY, face=-1, scale=0.86, legs=(8, -8), sh=6, el=10 + 8 * alt, tilt=-2 - 3 * alt,
                    pencil_deg=200), 7914 + alt)
    P.bal(c, Q, 62, (390, 305 + 10 * alt), (230, 450), 7916 + alt)


def b_e2(c, alt):
    P.clock_hands(c, 4, 10, 7911); P.door_closed(c, 7902)
    P.figs(c, stranger(WX - 10, P.SILL + 6, face=1, scale=1.25, glove=True), 7912)
    a = agent(750 + 16 * alt, AY, face=-1, scale=0.86, legs=(8, -8), sh=10, el=-20 - 8 * alt, tilt=-26 + 6 * alt,
              pencil_deg=200)
    P.figs(c, a, 7921 + alt)
    P.bal(c, A_, 60, (390 + 8 * alt, 262), P.agent_mouth(a), 7923 + alt)


def b_e3(c, alt):
    P.clock_hands(c, 4, 10, 7911); P.door_closed(c, 7902)
    P.figs(c, stranger(WX - 60 - 26 * alt, P.SILL + 6, face=-1, scale=1.2, tilt=-6 - 4 * alt), 7931 + alt)
    P.figs(c, agent(700 + 40 * alt, AY, face=1, scale=0.86, legs=(14 + 6 * alt, -12 - 6 * alt), sh=-8, el=16,
                    pencil_deg=200), 7933 + alt)
    P.bal(c, TH, 70, (440, 300), (300, 450), 7935 + alt)


def b_e4(c, alt):
    P.clock_hands(c, 4, 11, 7941); P.door_open(c, 7942)
    P.figs(c, agent(1262 + 12 * alt, AY, face=1, scale=0.86, legs=(4, -4), sh=-4 + 6 * alt, el=12 + 10 * alt,
                    pencil_deg=200 - 6 * alt, tilt=2 * alt), 7943 + alt)


def b_e5(c, alt):
    P.clock_hands(c, 4, 11, 7941); P.door_open(c, 7942)
    g = dict(p7.AG2)
    x = g.pop("x")
    g["tilt"] = 6 + 4 * alt
    g["el"] = 140 - 6 * alt
    a = agent(x + 8 * alt, AY, face=1, **g)
    P.figs(c, a, 7951 + alt)
    fp = p7.face_points(a)
    P.bal(c, F, 56, (1640, 330 + 8 * alt), (fp["nose"][0] + 4, fp["lip_lo"][1] + 11), 7953 + alt, ctrl=(1500, 420))


BEATS = [("E0", b_e0, 330), ("E1", b_e1, 0), ("E2", b_e2, 100), ("E3", b_e3, 0), ("E4", b_e4, 1140),
         ("E5", b_e5, 1140)]

# captions: (A, B); words in *stars* are the errand's own and lose ink panel by panel
CAPS = [
    ("The memo: open the *SERVICE* *door* at *4:15.* Up he gets for the *key.*",
     "The memo, the memo... up he gets for the... the *key.*"),
    ("On his way, a lady at the ticket window.",
     "On his way, on his way: a lady."),
    ("He looks up at the clock and tells her.",
     "He looks, looks up at the clock."),
    ("She goes. On he goes to the *cupboard,* for the *key.*",
     "She goes, she goes. On to the... the *cupboard.*"),
    ("He opens it. There hangs the *key,* tagged *SERVICE.*",
     "He opens it, opens it. There hangs the... the..."),
    ("He stands there.",
     "He stands, stands there. The key stays on its hook; the SERVICE door stays shut."),
]


def errand_ink(i):
    return float(max(0.0, 1.0 - 0.09 * i - 0.14 * (i % 2)))


def caption(page, text, x0, y0, width, cap, seed, fade):
    """word-by-word pen lettering; starred words printed at the errand's ink (fade)."""
    words = text.split()
    sp = cap * 0.42
    masks = []
    for k, w in enumerate(words):
        err = w.startswith("*")
        w = w.strip("*")
        if w.endswith("*"):
            w = w[:-1]
        w = w.replace("*", "")
        m = pen99.letter([w], cap, seed + k)
        masks.append((m, err))
    x, y = x0, y0
    lh = int(cap * 1.42)
    faded = []
    for m, err in masks:
        adv = m.shape[1] - cap * 1.2
        if x + adv > x0 + width and x > x0:
            x, y = x0, y + lh
        mm = np.zeros(page.shape[:2], np.uint8)
        blit_mask(mm, m, int(x - cap * 0.6), int(y - cap * 0.15))
        a = fade if err else 1.0
        if a > 0.02:
            comp(page, mm, INK, alpha=a)
        if err:
            faded.append(round(a, 3))
        x += adv + sp
    return y + lh - y0, faded


def panel_pic(k):
    """k = 0..11: beat k//2, drawing k%2 (1 = the ghost pull, figure redrawn a little moved)."""
    ev, fn, cx0 = BEATS[k // 2]
    alt = k % 2
    c = P.background()
    fn(c, alt)
    crop = c[CROP_Y0:CROP_Y0 + CROP_H, cx0:cx0 + CROP_W]
    p = cv2.resize(crop, (PWD, PIC_H), interpolation=cv2.INTER_AREA)
    if alt:                                     # second pull: less ink, a few px off register
        p = 255 - (255 - p) * 0.74
        p = np.roll(p, (3, 4), axis=(0, 1))
        p[:3, :] = 255
        p[:, :4] = 255
    return p


def build(upto=12):
    page = SHEET.copy()
    rec = []
    for k, (x0, y0, x1, y1) in enumerate(BOXES):
        if k >= upto:
            continue
        p = panel_pic(k)
        page[y0:y1, x0:x1] = page[y0:y1, x0:x1] * (p / 255.0)
        t = CAPS[k // 2][k % 2]
        hgt, faded = caption(page, t, x0 + 6, y1 + 26, PWD - 10, 32, 7960 + 17 * k, errand_ink(k))
        rec.append(dict(panel=k + 1, event=BEATS[k // 2][0], drawing="first" if k % 2 == 0 else "second (ghost pull)",
                        caption=t.replace("*", ""), errand_ink=faded))
    frame_border(page, BOXES[:upto], w=9, seed=7990)
    return page, rec


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    page, rec = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    import json
    json.dump(rec, open("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/p79_rec.json", "w"),
              indent=1)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = [build(u)[0] for u in (1, 2, 4, 6, 8, 10, 11, 12)]
        save_beats(N, [np.asarray(Image.fromarray(finish(f)).resize((960, 1242), Image.LANCZOS)) for f in frames])
