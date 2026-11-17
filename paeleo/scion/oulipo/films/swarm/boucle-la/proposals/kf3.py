"""Direction 3 - Rotoscope au lavoir: a real 1915 quarrel (Mabel and Fatty's Wash Day,
Keystone; Library of Congress, no known restrictions / PD) rotoscoped frame by frame into
pen-and-ink (SCION 28 mattes, 30-style figure masks from a median clean plate, 38 pose
selection) on the loop page. Each panel is a held run of real frames, re-inked every
frame (the line boils); the pair panels after the hinge replay the same inked frames.

Rotoscope per frame: clean plate = median of the 16 s segment; figure matte = |frame - plate|;
inside the matte, XDoG pen line + spot blacks + diagonal hatching for mid-tones; outside it,
only the strongest set edges in grey. Keyframe: t = 31 s, the hinge.
Run: python3 -I kf3.py
"""
import glob
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf_common import (INK, PAPER, SEQ, W, H, balloon, frame_panel, layout, note_prop, page_furniture, panel_ids)

HERE = os.path.dirname(os.path.abspath(__file__))
SEG = os.path.join(HERE, "../../../sources/boucle-la/fatty/seg")
# source frame per occurrence (12 fps, segment starts at 156.0 s of the LoC transfer)
FRAME = {"A": 169, "B": 113, "C": 129, "H": 89}
CROP = {"A": (200, 0, 690, 333), "B": (200, 0, 690, 333), "C": (200, 0, 690, 333), "H": (215, 30, 690, 340)}
NOTE_AT = {"A": (468, 118, -20, False), "H": (548, 262, 4, True)}  # source px, rotation, face


def load(i):
    return cv2.imread(os.path.join(SEG, "f%04d.jpg" % i), cv2.IMREAD_GRAYSCALE)


def clean_plate():
    fs = sorted(glob.glob(os.path.join(SEG, "f*.jpg")))[::3]
    st = np.stack([cv2.imread(f, cv2.IMREAD_GRAYSCALE) for f in fs])
    return np.median(st, axis=0).astype(np.uint8)


def xdog(g, sigma=1.1, k=1.6, tau=0.985, eps=-2.0, phi=1.6):
    g = g.astype(np.float32)
    a = cv2.GaussianBlur(g, (0, 0), sigma)
    b = cv2.GaussianBlur(g, (0, 0), sigma * k)
    d = a - tau * b
    e = np.where(d >= eps, 1.0, 1.0 + np.tanh(phi * (d - eps)))
    return e  # 1 = paper, toward 0 = ink


def rotoscope(i, plate, up=2):
    g = load(i)
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    ge = clahe.apply(g)
    gb = cv2.GaussianBlur(g, (0, 0), 2.5)
    m = (gb > 92).astype(np.uint8) * 255
    m[:, :205] = 0
    m[:, 640:] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    keep = np.zeros_like(m)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] > 1200:
            keep[lab == k] = 255
    m = keep
    # work at 2x for a smoother pen
    G = cv2.resize(ge, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    G0 = cv2.resize(g, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
    M = cv2.resize(m, None, fx=up, fy=up, interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
    M = cv2.GaussianBlur(M, (0, 0), 2)
    line_fig = xdog(G, sigma=1.05, eps=-0.6, phi=2.2)
    # the rotoscope contour: the matte's edge re-drawn as a pen line, the rotoscoper's first stroke
    mb = (M > 0.5).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(mb, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = np.ones_like(G, np.float32)
    for c in cnts:
        c = cv2.approxPolyDP(c, 1.5, True)
        cv2.polylines(contour, [c], True, 0.0, thickness=5, lineType=cv2.LINE_AA)
    line_bg = xdog(cv2.GaussianBlur(G, (0, 0), 2.2), sigma=1.6, eps=-4.5, phi=1.0)
    h, w = G.shape
    yy, xx = np.mgrid[0:h, 0:w]
    hatch = (((xx + yy) % 9) < 2).astype(np.float32)          # 45-degree pen hatching
    hatch2 = (((xx - yy) % 9) < 2).astype(np.float32)
    lum = cv2.GaussianBlur(G0, (0, 0), 2.0).astype(np.float32)
    ink = np.ones_like(lum)
    ink = np.minimum(ink, line_fig)
    ink = np.where(lum < 62, 0.0, ink)                         # spot blacks (hair, shadow)
    ink = np.where((lum >= 62) & (lum < 118), np.minimum(ink, 1 - hatch * 0.95), ink)
    ink = np.where((lum >= 62) & (lum < 92), np.minimum(ink, 1 - hatch2 * 0.9), ink)
    ink = np.minimum(ink, contour)
    # fine pen: eyes, mouths, folds - small-scale edges inside the figures only
    fine = cv2.Canny(cv2.GaussianBlur(G, (0, 0), 1.3), 40, 95)
    fine = cv2.dilate(fine, np.ones((2, 2), np.uint8))
    ink = np.where(fine > 0, 0.0, ink)
    bg = np.where(lum < 70, 0.06, 1.0).astype(np.float32)   # spot black ground, as on Lécroart's night panels
    bg = np.where((lum >= 70), np.minimum(bg, 1 - hatch * 0.9), bg)
    edges = cv2.Canny(cv2.GaussianBlur(G0, (0, 0), 2.5), 30, 70)
    bg = np.where(edges > 0, np.where(bg < 0.5, 0.55, 0.0), bg)
    out = M * ink + (1 - M) * bg
    out = cv2.GaussianBlur(out, (0, 0), 0.6)
    return (np.clip(out, 0, 1) * 255).astype(np.uint8), up


def iris_insert(size):
    """A period iris insert: the note's face, inked, in a black circular matte."""
    S = 3
    im = Image.new("RGB", (size * S, size * S), (246, 244, 238))
    n = note_prop(int(size * 0.62), int(size * 0.42), face=True, seed=7).resize((int(size * 0.62) * S, int(size * 0.42) * S), Image.LANCZOS)
    n = n.rotate(4, expand=True, resample=Image.BICUBIC)
    im.paste(n, ((im.width - n.width) // 2, (im.height - n.height) // 2), n)
    d = ImageDraw.Draw(im)
    # two inked fingers over the card edge (drawn, matching the rotoscope pen)
    cx, cy = im.width // 2 + int(size * 0.26 * S), im.height // 2 + int(size * 0.12 * S)
    for k in range(2):
        d.rounded_rectangle([cx - 9 * S + k * 13 * S, cy - 6 * S, cx + 3 * S + k * 13 * S, cy + 26 * S], radius=6 * S,
                            fill=(250, 249, 245), outline=INK, width=2 * S)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).ellipse([4 * S, 4 * S, im.width - 4 * S, im.height - 4 * S], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2 * S))
    out = Image.new("RGB", im.size, (14, 14, 14))
    out.paste(im, (0, 0), mask)
    return out.resize((size, size), Image.LANCZOS)


def render_panel(key, w, h, plate):
    art, up = rotoscope(FRAME[key], plate)
    x0, y0, x1, y1 = [v * up for v in CROP[key]]
    pil = Image.fromarray(art).convert("RGB")
    if key in NOTE_AT:
        nx, ny, rot, face = NOTE_AT[key]
        nw = 46 if face else 30
        n = note_prop(nw, int(nw * 0.68), face=face, seed=7).resize((nw * up, int(nw * 0.68) * up), Image.LANCZOS)
        n = n.rotate(rot, expand=True, resample=Image.BICUBIC)
        pil.paste(n, (nx * up - n.width // 2, ny * up - n.height // 2), n)
    crop = pil.crop((x0, y0, x1, y1))
    if key != "H":
        return crop.resize((w, h), Image.LANCZOS)
    # the hinge: the two-shot between spot blacks, with an iris insert of the note
    panel = Image.new("RGB", (w, h), (14, 14, 14))
    ch = h
    cw = int(crop.width * ch / crop.height)
    shot = crop.resize((cw, ch), Image.LANCZOS)
    sx = int(w * 0.52 - cw / 2)
    panel.paste(shot, (sx, 0))
    d = ImageDraw.Draw(panel)
    d.line([(sx, 0), (sx, h)], fill=INK, width=3)
    d.line([(sx + cw, 0), (sx + cw, h)], fill=INK, width=3)
    ins = iris_insert(int(h * 0.9))
    panel.paste(ins, (sx + cw + int((w - sx - cw - ins.width) / 2), int(h * 0.05)))
    return panel


def main(out=os.path.join(HERE, "kf-3.png")):
    plate = clean_plate()
    img = Image.new("RGB", (W, H), PAPER)
    rects = layout()
    cache = {}
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        w, h = x1 - x0, y1 - y0
        if (k, w, h) not in cache:
            cache[(k, w, h)] = render_panel(k, w, h, plate)
        p = cache[(k, w, h)]
        if i > 3:
            p = Image.blend(Image.new("RGB", p.size, PAPER), p, 0.2)
        img.paste(p, (x0, y0))
    spots = {"A": (0.70, 0.13, 0.70, 0.38), "B": (0.68, 0.13, 0.30, 0.27), "C": (0.72, 0.12, 0.72, 0.40),
             "H": (0.17, 0.30, 0.42, 0.36)}
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        w, h = x1 - x0, y1 - y0
        bx, by, tx, ty = spots[k]
        kw = dict(cap=10, maxw=170) if k != "H" else dict(cap=12, maxw=230)
        if i > 3:
            kw.update(alpha=70, color=(150, 150, 150))
        balloon(img, x0 + w * bx, y0 + h * by, k, tail=(x0 + w * tx, y0 + h * ty), **kw)
    for i in range(7):
        frame_panel(img, rects[i], seed=i, width=3 if i != 3 else 4)
    page_furniture(img)
    panel_ids(img, rects)
    img.save(out)
    return out


if __name__ == "__main__":
    print(main())
