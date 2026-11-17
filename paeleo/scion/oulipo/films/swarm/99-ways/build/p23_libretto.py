"""Page 23 Libretto (genre; medium: stencil-dye).

An opera: a libretto-and-vocal-score page. Four stage pictures printed as HANDMADE stencils in flat dyes
(the page-08 stencil method: one cut stencil per colour with paper ties, fixed misregistration, mottled
dye pooling at the edges) inside a stencilled proscenium (madder curtains, ochre footlights). Beside each
picture: the number, the stage directions (pen hand sheared to an italic, in madder, in parentheses),
and the sung part on a ruled five-line staff: role name, treble clef, stencilled notes, the canon line
underlaid syllable by syllable. Title stencilled with bridges. Lines verbatim (canon c1).
"""
import math
import random
import sys

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
import p08_lipogram as S8  # noqa: E402  (stencil printing: dye, ties, noise, colours)

N, PID, TITLE = 23, "libretto", "Libretto"
SHEET = S8.SHEET
INDIGO, MADDER, OCHRE, VERDI, UMBER, WASH, SKIN = S8.INDIGO, S8.MADDER, S8.OCHRE, S8.VERDI, S8.UMBER, S8.WASH, S8.SKIN
RUBRIC = np.array([138, 40, 30], np.float32)       # stage-direction ink (madder, darker)
STATE = {"staves": 9, "curtain": 0.0, "dirs": True}

LINES = {
    "q": "Pardon me — have you the right time?",
    "a": "Ten past four, by the clock.",
    "t": "Much obliged!",
    "f": "Well, here I am... and what for?",
}

# ------------------------------------------------------------------ stencil helpers
COL = {"wash": WASH, "indigo": INDIGO, "madder": MADDER, "ochre": OCHRE, "verdi": VERDI, "umber": UMBER, "skin": SKIN}


def print_layers(c, layers, seed):
    for i, (name, mask) in enumerate(layers):
        S8.dye(c, mask, COL[name], seed + 17 * i, shift=S8.SHIFT[name], strength=0.55 if name == "wash" else 0.92,
               bridge=name not in ("wash", "skin"))
    return c


def poly_mask(w, h, polys):
    m = np.zeros((h, w), np.uint8)
    for p in polys:
        cv2.fillPoly(m, [np.int32(np.asarray(p) * 4)], 255, cv2.LINE_AA, shift=2)
    return m


# ------------------------------------------------------------------ stage pictures (scene 900 x 570)
SW, SH = 900, 570
FLOOR = 492


def proscenium(closed=0.0):
    """Madder curtains (side drapes, valance), umber apron and boards; ochre footlights. Returns layer dict."""
    w, h = SW, SH
    rnd = random.Random(2301)
    side = 92 + closed * (SW / 2 - 92)
    drapes = []
    for sgn in (1, -1):
        x_edge = side if sgn == 1 else w - side
        x_out = 0 if sgn == 1 else w
        pts = [(x_out, 0), (x_edge, 0)]
        for k in range(9):
            y = 60 + k * (h - 60) / 8
            pts.append((x_edge + sgn * (-14 * math.sin(k * 1.3) - 10 * (k / 8)), y))
        pts.append((x_out, h))
        drapes.append(pts)
    val = [(0, 0), (w, 0), (w, 54)] + [(w - k * w / 12, 54 + 22 * (k % 2)) for k in range(1, 12)] + [(0, 54)]
    curtain = poly_mask(w, h, drapes + [val])
    # fold slits cut into the drapes (stencil cut lines)
    slits = np.zeros((h, w), np.uint8)
    for sgn in (1, -1):
        for f in range(1, 4 + int(closed * 8)):
            x = (side * f / (4 + closed * 8)) if sgn == 1 else w - side * f / (4 + closed * 8)
            cv2.line(slits, (int(x), 70), (int(x + rnd.uniform(-8, 8)), h - 40), 255, 4, cv2.LINE_AA)
    curtain = np.where(slits > 0, 0, curtain).astype(np.uint8)
    apron = np.zeros((h, w), np.uint8)
    apron[h - 46:h] = 255
    boards = np.zeros((h, w), np.uint8)
    for k in range(1, 4):
        y = FLOOR + k * (h - 46 - FLOOR) / 4
        cv2.line(boards, (0, int(y)), (w, int(y)), 255, 3, cv2.LINE_AA)
    lights = np.zeros((h, w), np.uint8)
    for k in range(9):
        cx = 120 + k * (w - 240) / 8
        cv2.ellipse(lights, (int(cx), h - 46), (20, 16), 0, 180, 360, 255, -1, cv2.LINE_AA)
    return {"madder": curtain, "umber": np.maximum(apron, boards), "ochre_fl": lights}


def scene(shapes, extra=None, wall_tone=True):
    """Stencil layers for a stage picture: back wall wash, verdigris stage floor, figures/set, proscenium."""
    w, h = SW, SH
    L = S8.fig_layers(shapes, w, h)
    if extra:
        S8.merge(L, extra)
    out = []
    if wall_tone:
        wm = np.zeros((h, w), np.uint8)
        wm[:FLOOR] = 255
        out.append(("wash", wm))
    fl = np.zeros((h, w), np.uint8)
    fl[FLOOR:] = 255
    L["verdi"] = np.maximum(L.get("verdi", np.zeros((h, w), np.uint8)), fl)
    for k in ("ochre", "verdi", "indigo", "madder", "skin", "umber"):
        if k in L:
            out.append((k, L[k]))
    return out


def shirtsleeves(fig, lay):
    """Canon marks: the agent's waistcoat is indigo, but his shirt V and shirtsleeves are bare white paper.
    Cut the sleeve and shirt shapes out of every dye stencil (a 2 px cut line left round them), then print
    an umber garter band and a thin umber cut-edge line round the sleeve so the white reads against the wall."""
    w, h = SW, SH
    sl = S8.M([s for s in fig if s.role in ("sleeve", "shirt")], w, h, roles={"sleeve", "shirt"}, holes=False)
    if sl.max() == 0:
        return lay
    cut = cv2.dilate(sl, np.ones((3, 3), np.uint8))
    out = []
    for name, m in lay:
        if name in ("wash", "indigo", "madder", "ochre"):
            m = np.where(cut > 60, 0, m).astype(np.uint8)
        out.append((name, m))
    edge = cv2.morphologyEx(sl, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    gart = S8.M([s for s in fig if s.role == "garter"], w, h, roles={"garter"}, holes=False)
    out.append(("umber", np.maximum(np.where(edge > 90, 200, 0).astype(np.uint8), gart)))
    return out


def head_box(fig):
    """Mask of the agent's head (skin head, hair, ear, glasses) for the overlap check."""
    m = S8.M([s for s in fig if s.role in ("skin", "hair", "ear", "glass_in")], SW, SH, holes=False,
             roles={"skin", "hair", "ear", "glass_in"})
    return m


CHECK = {}


def stage(n, seed):
    """Render stage picture n (1..4) as float RGB SW x SH on the sheet."""
    w, h = SW, SH
    c = np.ones((h, w, 3), np.float32) * 255
    extra, post = {}, []
    if n == 1:      # E0: memo on the desk, the agent rising and setting off
        fig = desk(430, 330, 250, FLOOR) + lamp(620, 190, 140)
        fig += agent(330, FLOOR + 4, face=1, scale=0.44, legs=(14, -12), sh=22, el=-30, pencil_deg=200, lean=3)
        fig += clock(250, 150, 50, swing=6, pend=False)
        cup, _ = cupboard(735, 210, 120, 282)
        fig += cup
    elif n == 2:    # E1: the stranger at the ticket window; the agent stopped on his way
        ws, sill = window(150, 100, 270, 392, sill=340, header=50)
        for s in ws:
            s.role = "window"
        fig = list(ws) + stranger(285, sill + 2, scale=0.62, glove=True)
        # he faces LEFT, toward the TICKET OFFICE window; the clock hangs high on the wall BEHIND him (right),
        # well clear of his head (checked below: >= 43 scene px = 40 page px)
        ag = agent(560, FLOOR + 4, face=-1, scale=0.44, legs=(10, -8), sh=10, el=-14, tilt=-6, pencil_deg=190)
        ck = clock(715, 132, 40, swing=-6, pend=False)
        fig += ag + ck
        hm = head_box([s for s in ag if s.role in ("skin", "hair", "ear", "glass_in") and s.z >= 0 and min(s.pts[:, 1]) < FLOOR - 230])
        cm = S8.M(ck, w, h, roles={"clock", "dial", "hand"}, holes=False)
        ys, xs = np.nonzero(hm > 20)
        hb = (xs.min(), ys.min(), xs.max(), ys.max())
        ys2, xs2 = np.nonzero(cm > 20)
        cb = (xs2.min(), ys2.min(), xs2.max(), ys2.max())
        gap = max(cb[0] - hb[2], hb[0] - cb[2], cb[1] - hb[3], hb[1] - cb[3])
        CHECK["p2"] = dict(head_box=[int(v) for v in hb], clock_box=[int(v) for v in cb],
                           mask_overlap_px=int(((hm > 20) & (cm > 20)).sum()), bbox_gap_scene_px=int(gap),
                           bbox_gap_page_px=round(gap * PIC_W / SW, 1), agent_faces="left, toward the window")
    elif n == 3:    # E2-E3: he looks up at the clock (4:10); she thanks him and turns away
        ws, sill = window(560, 100, 260, 392, sill=340, header=50)
        for s in ws:
            s.role = "window"
        fig = list(ws) + stranger(725, sill + 2, scale=0.62, face=1, tilt=-3)
        fig += clock(230, 165, 70, swing=10)
        fig += agent(420, FLOOR + 4, face=-1, scale=0.44, legs=(3, -3), tilt=-22, sh=6, el=20, pencil_deg=190)
    else:           # E4-E5: cupboard open, key on its hook; pencil to his chin; SERVICE door shut
        cup, ins = cupboard(330, 190, 190, 290, open_deg=112)
        fig = list(cup) + service_door(600, 170, 150, 322)
        fig += agent(205, FLOOR + 4, face=1, scale=0.44, legs=(3, -3), sh=50, el=120, wr=8, pencil_deg=40, tilt=6)
        ix0, iy0, ix1, iy1 = ins
        kx, ky = (ix0 + ix1) / 2, iy0 + 92
        km = np.zeros((h, w), np.uint8)
        paste_mask(km, key_alpha(), kx, ky, 0.19)
        extra["ochre"] = km
        post.append(("key", kx, ky))
    pros = proscenium(STATE["curtain"] if n == 4 else 0.0)
    lay = scene(fig, extra)
    lay = shirtsleeves(fig, lay)
    lay.append(("ochre", pros["ochre_fl"]))
    lay.append(("madder", pros["madder"]))
    lay.append(("umber", pros["umber"]))
    print_layers(c, lay, seed)
    c *= SHEET[:h, :w].mean(axis=2, keepdims=True) / SHEET.mean()
    paper = np.array([248, 244, 230], np.float32)
    if n == 1:
        slip(c, 470, 262, ["4:15 - open SERVICE door.", "Key in cupboard."], 17, seed + 3, paper=paper, pad=(10, 5), tilt=-3, shadow=0.3)
    if n == 2 or n == 3:
        x0 = 150 if n == 2 else 560
        lm = np.zeros((h, w), np.uint8)
        l = letter(["TICKET OFFICE"], 22, seed + 4, weight=0.17)
        put_mask(lm, l, x0 + (270 if n == 2 else 260) / 2, 100 + 27)
        comp(c, lm, np.array([246, 240, 222], np.float32))
    if n == 4 and STATE["curtain"] < 0.5:
        _, kx, ky = post[0]
        hk = np.zeros((h, w), np.uint8)
        penlib.brush_line(hk, [(kx - 14, ky - 72), (kx + 2, ky - 72), (kx + 2, ky - 62)], 5, seed + 3)
        comp(c, hk, UMBER)
        slip(c, int(kx + 6), int(ky + 22), ["SERVICE"], 15, seed + 4, paper=paper, pad=(8, 3), tilt=8, shadow=0.3)
        slip(c, 622, 205, ["SERVICE"], 20, seed + 5, paper=paper, pad=(10, 4), shadow=0.3)
    return c


# ------------------------------------------------------------------ music
GAP = 17          # staff line spacing


def catmull_open(pts, n=12):
    P = [np.array(p, float) for p in pts]
    P = [P[0]] + P + [P[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


# treble clef, units of staff gaps, origin on the G line, y up
GCLEF = [(0.18, 0.05), (0.55, 0.35), (0.35, 0.8), (-0.25, 0.75), (-0.62, 0.15), (-0.35, -0.6), (0.35, -0.75),
         (0.85, -0.15), (0.65, 0.65), (0.05, 1.45), (-0.25, 2.5), (0.05, 3.55), (0.42, 3.15), (0.32, 2.2),
         (-0.08, 1.4), (-0.02, -0.6), (0.02, -1.9), (-0.3, -2.25), (-0.62, -1.95)]


def staff(ink_m, dye_m, x0, x1, ytop, seed, clef=True, meter=True):
    """Ruled staff (ink), treble clef (ink pen line), 4/4 (pen hand). Returns y of bottom line."""
    for k in range(5):
        y = ytop + k * GAP
        penlib.brush_line(ink_m, [(x0, y), (x1, y + random.Random(seed + k).uniform(-1, 1))], 2.4, seed + k, tremor=0.5)
    penlib.brush_line(ink_m, [(x0, ytop), (x0, ytop + 4 * GAP)], 3, seed + 7, tremor=0.2)
    penlib.brush_line(ink_m, [(x1, ytop), (x1, ytop + 4 * GAP)], 3, seed + 8, tremor=0.2)
    penlib.brush_line(ink_m, [(x1 - 9, ytop), (x1 - 9, ytop + 4 * GAP)], 2, seed + 9, tremor=0.2)
    gy = ytop + 3 * GAP
    if clef:
        pts = [(x0 + 30 + px * GAP, gy - py * GAP) for px, py in GCLEF]
        penlib.brush_line(ink_m, catmull_open(pts), 4.2, seed + 11, tremor=0.3)
    if meter:
        for j, yy in enumerate((ytop + 2 * GAP - 2, ytop + 4 * GAP - 2)):
            l = letter(["4"], int(GAP * 1.9), seed + 12 + j, weight=0.2)
            put_mask(ink_m, l, x0 + 74, yy - GAP)
    return ytop + 4 * GAP


def note(dye_m, x, ytop, step, dur, stem_up=None):
    """Stencilled note. step: 0 = bottom line (E4), +1 per line/space. dur: 1 quarter, 2 half, 0.5 eighth."""
    y = ytop + 4 * GAP - step * GAP / 2
    rx, ry = GAP * 0.66, GAP * 0.48
    head = np.zeros_like(dye_m)
    cv2.ellipse(head, (int(x * 4), int(y * 4)), (int(rx * 4), int(ry * 4)), -22, 0, 360, 255, -1, cv2.LINE_AA, shift=2)
    if dur >= 2:  # open head: cut the counter (stencil island held by a tie at the slant)
        cv2.ellipse(head, (int(x * 4), int(y * 4)), (int(rx * .62 * 4), int(ry * .42 * 4)), -22, 0, 360, 0, -1, cv2.LINE_AA, shift=2)
    np.maximum(dye_m, head, out=dye_m)
    up = step < 4 if stem_up is None else stem_up
    sx = x + (rx * 0.86 if up else -rx * 0.86)
    y1 = y - 3.3 * GAP if up else y + 3.3 * GAP
    cv2.line(dye_m, (int(sx * 4), int(y * 4)), (int(sx * 4), int(y1 * 4)), 255, 9, cv2.LINE_AA, shift=2)
    if dur == 0.5:
        sg = 1 if up else -1
        fl = [(sx, y1), (sx + GAP * 0.45, y1 + sg * GAP * 0.8), (sx + GAP * 1.05, y1 + sg * GAP * 1.6), (sx + GAP * 0.95, y1 + sg * GAP * 2.6)]
        penlib.brush_line(dye_m, fl, 6, int(x), tremor=0.2)
    # ledger lines
    for s in range(-2, step - 1, -2) if step <= -2 else []:
        yy = ytop + 4 * GAP - s * GAP / 2
        cv2.line(dye_m, (int((x - rx * 1.6) * 4), int(yy * 4)), (int((x + rx * 1.6) * 4), int(yy * 4)), 255, 7, cv2.LINE_AA, shift=2)
    for s in range(10, step + 1, 2) if step >= 10 else []:
        yy = ytop + 4 * GAP - s * GAP / 2
        cv2.line(dye_m, (int((x - rx * 1.6) * 4), int(yy * 4)), (int((x + rx * 1.6) * 4), int(yy * 4)), 255, 7, cv2.LINE_AA, shift=2)
    return y


def rest(ink_m, x, ytop, seed):
    """Quarter rest drawn with the pen."""
    pts = [(x - 4, ytop + GAP * 0.6), (x + 6, ytop + GAP * 1.5), (x - 4, ytop + GAP * 2.3), (x + 6, ytop + GAP * 3.1),
           (x - 6, ytop + GAP * 2.9), (x + 2, ytop + GAP * 3.8)]
    penlib.brush_line(ink_m, pts, 5, seed, tremor=0.2)


def setting(ink_m, dye_m, lyr_m, x0, x1, ytop, notes, seed, beats_per_bar=4, lyr_cap=30, name=None, extra_marks=()):
    """Lay a staff with notes [(syllable or None, step, dur)], bar lines every bar, syllables beneath."""
    staff(ink_m, dye_m, x0, x1, ytop, seed)
    if name:
        l = letter_left([name], 30, seed + 90, weight=0.17)
        blit_mask(ink_m, l, int(x0 - l.shape[1] + 2), int(ytop + GAP * 2 - 30 * 1.15))
    xs = x0 + 120
    span = x1 - 30 - xs
    adv = lambda t: sum(penlib.GLYPHS[c][0] * lyr_cap + lyr_cap * .1 for c in pen99.clean(t))
    wid = [max(d * 1.0, (adv(sy) + lyr_cap * 0.9) / 80.0 if sy else 0.6) for sy, _, d in notes]
    tot_w = sum(wid)
    words, t, acc = [], 0.0, 0.0
    total = sum(d for _, _, d in notes)
    for i, (syl, step, dur) in enumerate(notes):
        x = xs + span * (acc + wid[i] * 0.4) / tot_w
        if step is None:
            rest(ink_m, x, ytop, seed + 200 + i)
        else:
            note(dye_m, x, ytop, step, dur)
        if syl:
            words.append((x, syl))
        t += dur
        acc += wid[i]
        if abs(t / beats_per_bar - round(t / beats_per_bar)) < 1e-6 and t < total - 1e-6:
            bx = xs + span * acc / tot_w - 6
            penlib.brush_line(ink_m, [(bx, ytop), (bx, ytop + 4 * GAP)], 2.6, seed + 300 + i, tremor=0.2)
    base = ytop + 4 * GAP + 30 + lyr_cap * 1.0
    for j, (x, syl) in enumerate(words):
        l = letter([syl], lyr_cap, seed + 400 + j)
        put_mask(lyr_m, l, x, base - lyr_cap * 0.42)
    for (mk, mx, my) in extra_marks:
        l = letter([mk], 26, seed + 500 + len(mk), weight=0.16)
        put_mask(lyr_m, l, mx, my)
    return base + 10


def italic(m, shear=0.22):
    h, w = m.shape
    M = np.float32([[1, -shear, shear * h], [0, 1, 0]])
    return cv2.warpAffine(m, M, (w + int(shear * h) + 2, h))


def direction(mask, text, x, y, width, cap, seed):
    """Stage direction: parentheses, wrapped, sheared to an italic. Returns y after."""
    lines = wrap(text, cap, width - 20)
    m = italic(letter_left(lines, cap, seed, weight=0.12))
    blit_mask(mask, m, int(x - cap * 0.5), int(y))
    return int(y + len(lines) * cap * 1.42 + cap * 0.5)


# The settings (our own melodies): (syllable, step, beats). step 0 = E4 bottom line.
MUS = {
    "prelude": [(None, 4, 1), ("tick", 6, 1), (None, 4, 1), ("tock", 3, 1),
                (None, 4, 1), ("tick", 6, 1), (None, 4, 1), ("tock", 3, 1)],
    "q": [("Par-", 6, 0.5), ("don", 8, 1), ("me", 7, 1.5), ("—", None, 1),
          ("have", 5, 0.5), ("you", 6, 0.5), ("the", 7, 1), ("right", 9, 1), ("time?", 10, 2)],
    "a": [("Ten", 4, 1), ("past", 4, 1), ("four,", 2, 2),
          ("by", 1, 1), ("the", 2, 1), ("clock.", 0, 2)],
    "t": [("Much", 8, 1), ("o-", 9, 0.5), ("bliged!", 11, 2.5)],
    "f": [("Well,", 5, 1.5), ("here", 4, 0.5), ("I", 3, 1), ("am...", 1, 1),
          (None, 2, 1), ("and", 2, 1), ("what", 4, 1), ("for?", 6, 1)],
}

NUMS = [
    dict(n=1, head="No. 1   Prelude", tempo="Andante, like a clock",
         d1="Randolph station, Vermont: the office, a September afternoon, 1937. The AGENT sits at his desk; on it a memo: '4:15 - open SERVICE door. Key in cupboard.' He rises and sets off toward the cupboard.",
         parts=[("Orch.", "prelude")], d2=None),
    dict(n=2, head="No. 2   Recitative", tempo="Allegretto",
         d1="On his way. At the ticket window a STRANGER, a lady in a hat, on the platform side, stops him.",
         parts=[("STRANGER", "q")], d2="The AGENT halts and turns to the clock."),
    dict(n=3, head="No. 3   Duettino", tempo="Moderato",
         d1="He looks up at the wall clock: ten past four.",
         parts=[("AGENT", "a"), ("STRANGER", "t")], d2="She leaves the window."),
    dict(n=4, head="No. 4   Aria", tempo="Lento, smarrito",
         d1="He reaches the cupboard and opens it. The brass key hangs on its hook, tagged SERVICE. Pencil to his chin:",
         parts=[("AGENT", "f")], d2="He does not take it. The key stays on its hook; the SERVICE door stays closed. Slow curtain."),
]

# page geometry
X0, X1 = 110, 2090
PIC_W, PIC_H = 840, 532
BLOCK_Y = [470, 1035, 1600, 2165]
BLOCK_H = 555


def title_block(page, ink_m, rub_m):
    # stencilled title with bridges, in madder
    w, h = W, 300
    tm = np.zeros((h, w), np.uint8)
    l = letter(["THE SERVICE KEY"], 104, 2390, weight=0.24)
    put_mask(tm, l, W / 2, 150)
    tm = cv2.dilate(tm, np.ones((5, 5), np.uint8))
    # the stencil bridges: two thin horizontal ties across every letter
    for yy in (150,):
        tm[yy - 3:yy + 3] = 0
    full = np.zeros((H, W), np.uint8)
    full[60:60 + h] = tm
    S8.dye(page, full, MADDER, 2391, shift=(2, -1), bridge=False)
    blit_mask(ink_m, letter(["an opera in one act  -  libretto and vocal score"], 38, 2392), 0, 0) if False else None
    l = letter(["an opera in one act  -  libretto and vocal score"], 38, 2392)
    put_mask(ink_m, l, W / 2, 312)
    l = italic(letter(["Persons:  THE AGENT, station agent at Randolph (baritone)  -  A STRANGER, a lady traveller (soprano)"], 30, 2393, weight=0.12))
    put_mask(ink_m, l, W / 2, 372)
    penlib.brush_line(ink_m, [(X0 + 200, 420), (X1 - 200, 421)], 3, 2394)


def build():
    page = SHEET.copy()
    ink_m = np.zeros((H, W), np.uint8)
    rub_m = np.zeros((H, W), np.uint8)
    dye_m = np.zeros((H, W), np.uint8)
    lyr_m = np.zeros((H, W), np.uint8)
    title_block(page, ink_m, rub_m)
    staves_left = STATE["staves"]
    for i, num in enumerate(NUMS):
        y0 = BLOCK_Y[i]
        left = i % 2 == 0
        px = X0 if left else X1 - PIC_W
        pic = stage(num["n"], 2300 + 31 * i)
        pic = cv2.resize(pic, (PIC_W, PIC_H), interpolation=cv2.INTER_AREA)
        page[y0:y0 + PIC_H, px:px + PIC_W] = pic
        frame = np.zeros((H, W), np.uint8)
        frame = penlib.border_mask((H, W), [(px, y0, px + PIC_W, y0 + PIC_H)], w=7, seed=2350 + i)
        comp(page, frame, INK)
        tx0 = X0 + PIC_W + 70 if left else X0
        tx1 = X1 if left else X1 - PIC_W - 70
        # number and tempo
        l = letter_left([num["head"]], 42, 2360 + i, weight=0.17)
        blit_mask(ink_m, l, int(tx0 - 21), int(y0 - 6))
        l = italic(letter_left([num["tempo"]], 30, 2365 + i))
        blit_mask(ink_m, l, int(tx1 - l.shape[1] + 15), int(y0 + 6))
        y = y0 + 70
        if STATE["dirs"]:
            y = direction(rub_m, "(" + num["d1"] + ")", tx0, y, tx1 - tx0, 31, 2370 + i)
        else:
            y += len(wrap("(" + num["d1"] + ")", 31, tx1 - tx0 - 20)) * 31 * 1.42 + 15
        y += 26
        for j, (role, key) in enumerate(num["parts"]):
            ytop = y + (34 if j == 0 else 14)
            if staves_left > 0:
                notes = MUS[key]
                y = setting(ink_m, dye_m, lyr_m, tx0 + 170, tx1, ytop, notes, 2400 + 50 * i + 7 * j, name=role)
            else:
                staff(ink_m, dye_m, tx0 + 170, tx1, ytop, 2400 + 50 * i + 7 * j)
                l = letter_left([role], 30, 2400 + 50 * i + 7 * j + 90, weight=0.17)
                blit_mask(ink_m, l, int(tx0 + 172 - l.shape[1]), int(ytop + GAP * 2 - 30 * 1.15))
                y = ytop + 4 * GAP + 30 + 30 + 10
            staves_left -= 1
            y += 8
        if num["d2"] and STATE["dirs"] and (staves_left >= 0):
            y = direction(rub_m, "(" + num["d2"] + ")", tx0, y + 6, tx1 - tx0, 31, 2380 + i)
        assert y < y0 + BLOCK_H + 20, (i, y)
    S8.dye(page, dye_m, UMBER * 0.6, 2399, bridge=False, strength=1.0)
    comp(page, ink_m, INK)
    comp(page, lyr_m, INK)
    comp(page, rub_m, RUBRIC)
    return page


if __name__ == "__main__":
    page = build()
    img, size = save_page(page, N, PID, TITLE)
    print("jpeg bytes", size)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        frames = []
        for staves, curtain in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (5, 0.55), (5, 1.0)):
            STATE["staves"], STATE["curtain"] = staves, curtain
            p = np.clip(np.round(build()), 0, 255).astype(np.uint8)
            pen99.folio(p, N, TITLE)
            frames.append(np.asarray(Image.fromarray(p).resize((960, 1242), Image.LANCZOS)))
        save_beats(N, frames)
