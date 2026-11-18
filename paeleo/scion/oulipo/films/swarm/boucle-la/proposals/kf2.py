"""Direction 2 - Daumier à la colle: articulated paper cutouts of a foraged 1839
lithograph (Daumier, Moeurs conjugales no. 3, Rijksmuseum RP-P-OB-41.183, CC0),
animated as Gilliam-style collage puppets (SCION 1, 29, 32, 45) on the loop page.

Each figure is cut (luminance against the crayon vignette, inside a hand-set
scissor envelope) into body / head / forearm pieces, each pinned at a joint.
A pose is a rigid rotation per piece; a frame re-composites the pieces.
Keyframe: t = 31 s, the hinge.  Run: python3 -I kf2.py
"""
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf_common import (INK, PAPER, SEQ, W, H, balloon, frame_panel, layout, note_prop, page_furniture, panel_ids)

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "../../../sources/boucle-la/daumier")
SS = 2

ENV = {
    "man": [(375, 300), (480, 300), (505, 380), (505, 450), (530, 540), (522, 605), (460, 620), (445, 700), (420, 800),
            (470, 900), (480, 925), (380, 945), (330, 965), (270, 940), (285, 840), (265, 780), (225, 760), (225, 560),
            (260, 480), (330, 420)],
    "woman": [(560, 310), (670, 315), (690, 400), (700, 470), (740, 560), (760, 700), (770, 900), (700, 940), (590, 960),
              (560, 930), (560, 870), (540, 820), (525, 700), (522, 600), (540, 540), (580, 470), (560, 420)],
}
# articulated pieces: (polygon in source px, pivot)
PIECES = {
    "man": {"head": ([(330, 290), (520, 290), (520, 448), (455, 452), (420, 470), (330, 470)], (430, 452)),
            "fore": ([(420, 540), (508, 535), (512, 620), (420, 625)], (438, 585))},
    "woman": {"head": ([(540, 300), (700, 300), (700, 452), (640, 452), (600, 462), (540, 462)], (615, 455)),
              "fore": ([(538, 540), (640, 545), (650, 615), (538, 612)], (636, 588))},
}
HAND = {"man": (520, 575), "woman": (540, 572)}


def cutouts():
    img = cv2.imread(os.path.join(SRC, "d0.jpg"))
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = g.shape
    gb = cv2.GaussianBlur(g, (0, 0), 3)
    # print tone -> page tone: the brown paper goes to white, crayon to ink, texture kept
    g = cv2.addWeighted(g, 1.8, cv2.GaussianBlur(g, (0, 0), 2.0), -0.8, 0)  # crisp the crayon grain
    tone = np.clip((g - 60) / (196 - 60), 0, 1) ** 1.8
    tone = (14 + tone * 241).astype(np.uint8)
    figs = {}
    for name, poly in ENV.items():
        E = np.zeros((h, w), np.uint8)
        cv2.fillPoly(E, [np.array(poly, np.int32)], 255)
        m = ((gb > 120) & (E > 0)).astype(np.uint8) * 255
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
        m = np.where(lab == k, 255, 0).astype(np.uint8)
        ff = m.copy()
        cv2.floodFill(ff, None, (0, 0), 255)
        m = m | cv2.bitwise_not(ff)
        if name == "woman":  # drop the hanging towel: the note will take its place
            m[600:, :588] = 0
        # scissors: the contour re-cut as straight snips (polygon simplification), not pixel steps
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        m = np.zeros_like(m)
        for c in cnts:
            cv2.fillPoly(m, [cv2.approxPolyDP(c, 3.2, True)], 255)
        pieces = {}
        rest = m.copy()
        for pn, (pp, piv) in PIECES[name].items():
            P = np.zeros((h, w), np.uint8)
            cv2.fillPoly(P, [np.array(pp, np.int32)], 255)
            pm = m & P
            # the body keeps the paper under each joint (an underlap), so a turned piece never opens a hole
            keep = np.zeros((h, w), np.uint8)
            if pn == "head":
                keep[piv[1] - 14:, :] = 255
            else:
                cv2.circle(keep, piv, 22, 255, -1)
            rest = rest & ~(P & ~keep)
            pieces[pn] = (pm, piv)
        pieces["body"] = (rest, (0, 0))
        out = {}
        for pn, (pm, piv) in pieces.items():
            rim = cv2.dilate(pm, np.ones((7, 7), np.uint8))  # the white scissor margin
            a = np.where(pm > 0, tone, 252).astype(np.uint8)
            rgba = np.dstack([a, a, a, rim])
            ys, xs = np.nonzero(rim)
            x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
            out[pn] = (Image.fromarray(rgba[y0:y1, x0:x1], "RGBA"), (x0, y0), piv)
        figs[name] = out
    return figs


def place(canvas, piece, s, off, ang=0.0, piv=None, body_rot=0.0, body_piv=(0, 0), shadow=True):
    """Paste a cut piece: scale s, rotate ang (deg) about its joint, then the whole figure
    by body_rot about the feet. off = canvas position of source (0,0)."""
    im, (x0, y0), jp = piece
    piv = piv or (jp if jp != (0, 0) else body_piv)
    a = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    px, py = (piv[0] - x0) * s, (piv[1] - y0) * s
    tot = ang + body_rot
    # rotate around the joint: expand on a canvas centred on the joint
    R = int(max(math.hypot(cx - px, cy - py) for cx in (0, a.width) for cy in (0, a.height))) + 4
    big = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
    big.paste(a, (int(R - px), int(R - py)))
    big = big.rotate(-tot, resample=Image.BICUBIC, center=(R, R))
    # joint position after the body rotation about the feet
    jx, jy = piv[0], piv[1]
    bx, by = body_piv
    c, sn = math.cos(math.radians(body_rot)), math.sin(math.radians(body_rot))
    jx2, jy2 = bx + (jx - bx) * c - (jy - by) * sn, by + (jx - bx) * sn + (jy - by) * c
    X, Y = off[0] + jx2 * s - R, off[1] + jy2 * s - R
    if shadow:  # contact shadow: paper lying on paper
        sh = big.split()[3].filter(ImageFilter.GaussianBlur(3 * SS)).point(lambda v: v * 90 // 255)
        canvas.paste(Image.new("RGB", big.size, (0, 0, 0)), (int(X + 3 * SS), int(Y + 4 * SS)), sh)
    canvas.paste(big, (int(X), int(Y)), big)
    return lambda p: (off[0] + (bx + (p[0] - bx) * c - (p[1] - by) * sn) * s,
                      off[1] + (by + (p[0] - bx) * sn + (p[1] - by) * c) * s)


# pose: body lean (deg, about the feet), head and forearm rotations (deg, about neck/elbow)
POSES = {
    "A": {"man": dict(lean=-2, head=-6, fore=22), "woman": dict(lean=3, head=-4, fore=62, note="back")},
    "B": {"man": dict(lean=-5, head=-16, fore=-40), "woman": dict(lean=0, head=6, fore=-6, note="back")},
    "C": {"man": dict(lean=-7, head=-10, fore=26), "woman": dict(lean=6, head=4, fore=20, note="back")},
    "H": {"man": dict(lean=5, head=10, fore=30), "woman": dict(lean=-6, head=-14, fore=-14, note="face")},
}


def render_panel(figs, key, w, h, wide=False):
    Wp, Hp = w * SS, h * SS
    dark = key == "H"
    canvas = Image.new("RGB", (Wp, Hp), (22, 22, 22) if dark else (250, 249, 245))
    d = ImageDraw.Draw(canvas)
    s = Hp / (560.0 if not wide else 430.0)  # knees-up; the hinge comes in closer
    if not dark:  # a hand-inked floor line and wall rail: Lécroart keeps the set to a few strokes
        d.line([(0, Hp * 0.80), (Wp, Hp * 0.80 + 3 * SS)], fill=INK, width=2 * SS)
        d.line([(0, Hp * 0.47), (Wp, Hp * 0.47 - 2 * SS)], fill=(120, 120, 120), width=SS)
    pose = POSES[key]
    gap = 0.0 if not wide else 0.0
    cx = Wp * 0.5
    top = -190 * s if not wide else -262 * s
    offs = {"man": (cx - 470 * s - (40 if wide else 14) * SS, top),
            "woman": (cx - 560 * s + (40 if wide else 14) * SS, top)}
    feet = {"man": (380, 930), "woman": (660, 930)}
    hand_xy = None
    for name in ("man", "woman"):
        P = pose[name]
        f = figs[name]
        tr = place(canvas, f["body"], s, offs[name], 0, None, P["lean"], feet[name])
        place(canvas, f["head"], s, offs[name], P["head"], None, P["lean"], feet[name])
        if name == "woman":
            # forearm rotates about the elbow; the hand point follows the same transform
            fp = f["fore"][2]
            place(canvas, f["fore"], s, offs[name], P["fore"], None, P["lean"], feet[name])
            hx, hy = HAND["woman"]
            a = math.radians(P["fore"])
            hx2 = fp[0] + (hx - fp[0]) * math.cos(a) - (hy - fp[1]) * math.sin(a)
            hy2 = fp[1] + (hx - fp[0]) * math.sin(a) + (hy - fp[1]) * math.cos(a)
            hand_xy = tr((hx2, hy2))
        else:
            place(canvas, f["fore"], s, offs[name], P["fore"], None, P["lean"], feet[name])
    # the handmade note in Odette's hand
    face = pose["woman"]["note"] == "face"
    nw, nh = (int(96 * SS), int(64 * SS)) if face else (int(30 * SS), int(21 * SS))
    n = note_prop(nw // SS, nh // SS, face=face, seed=7).resize((nw, nh), Image.LANCZOS)
    n = n.rotate(5 if face else -18, expand=True, resample=Image.BICUBIC)
    sh = n.split()[3].filter(ImageFilter.GaussianBlur(3 * SS)).point(lambda v: v * 110 // 255)
    nx, ny = int(hand_xy[0] - n.width * 0.5), int(hand_xy[1] - n.height * (0.35 if face else 0.8))
    canvas.paste(Image.new("RGB", n.size, (0, 0, 0)), (nx + 3 * SS, ny + 4 * SS), sh)
    canvas.paste(n, (nx, ny), n)
    return canvas.resize((w, h), Image.LANCZOS)


def main(out=os.path.join(HERE, "kf-2.png")):
    figs = cutouts()
    img = Image.new("RGB", (W, H), PAPER)
    rects = layout()
    cache = {}
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        w, h = x1 - x0, y1 - y0
        if (k, w, h) not in cache:
            cache[(k, w, h)] = render_panel(figs, k, w, h, wide=(k == "H"))
        p = cache[(k, w, h)]
        if i > 3:
            p = Image.blend(Image.new("RGB", p.size, PAPER), p, 0.2)
        img.paste(p, (x0, y0))
    spots = {"A": (0.62, 0.40, 0.62, 0.30), "B": (0.36, 0.16, 0.44, 0.30), "C": (0.62, 0.30, 0.62, 0.30),
             "H": (0.24, 0.20, 0.44, 0.34)}
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        w, h = x1 - x0, y1 - y0
        bx, by, tx, ty = spots[k]
        kw = dict(cap=11, maxw=200) if k != "H" else dict(cap=12, maxw=260)
        if i > 3:
            kw.update(alpha=70, color=(150, 150, 150))
        balloon(img, x0 + w * bx, y0 + 38, k, tail=(x0 + w * tx, y0 + h * ty), **kw)
    for i in range(7):
        frame_panel(img, rects[i], seed=i, width=3 if i != 3 else 4)
    page_furniture(img)
    panel_ids(img, rects)
    img.save(out)
    return out


if __name__ == "__main__":
    print(main())
