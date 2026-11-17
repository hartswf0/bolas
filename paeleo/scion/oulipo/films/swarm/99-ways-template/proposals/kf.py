"""Keyframe builder for the 99-ways-template proposals (deterministic: python3 -I kf.py).

Reads only decoded pixels (PIL / OpenCV) from films/sources/99-ways-template/ and the
local Moving Image Archive clip cache (frames pre-extracted with ffmpeg into
sources/99-ways-template/frames/). Writes kf-1.png, kf-2.png, kf-3.png, board.jpg.
"""
import math
import random
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]  # .../oulipo
SRC = ROOT / "films" / "sources" / "99-ways-template"
W, H = 1280, 720
INK = (18, 17, 16)


# ---------------------------------------------------------------- paper (LoC FTP 1934 blank sheet)
def paper(warm=0.35):
    im = Image.open(SRC / "loc" / "blank.jpg").convert("RGB")
    w, h = im.size
    # interior of the sheet, away from the tape and the deckle
    box = (int(w * 0.10), int(h * 0.12), int(w * 0.88), int(h * 0.88))
    im = im.crop(box).resize((W, H), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    g = a.mean(axis=2, keepdims=True)
    # high-key: stretch the sheet toward white, keep the fibre and a trace of its cream
    g = (g - g.mean()) * 2.2 + 236
    a = g * (1 - warm) + (a - a.mean(axis=(0, 1)) + np.array([238, 232, 216])) * warm
    return np.clip(a, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- pen tools
def wobble(pts, amp, seed, step=6):
    """Resample a polyline and add a low-frequency hand tremor."""
    rnd = random.Random(seed)
    out = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / step))
        for i in range(n):
            t = i / n
            out.append([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t])
    out.append(list(pts[-1]))
    out = np.array(out, np.float32)
    ph = [rnd.uniform(0, 6.28) for _ in range(4)]
    k = np.arange(len(out))
    out[:, 0] += amp * (np.sin(k * 0.05 + ph[0]) + 0.4 * np.sin(k * 0.17 + ph[1]))
    out[:, 1] += amp * (np.sin(k * 0.06 + ph[2]) + 0.4 * np.sin(k * 0.21 + ph[3]))
    return out


def brush(mask, pts, w0, w1=None, seed=0):
    """Variable-width brush stroke into a uint8 ink mask (255 = ink). Tapers at both ends."""
    w1 = w0 if w1 is None else w1
    n = len(pts)
    rnd = random.Random(seed)
    for i in range(n - 1):
        t = i / max(1, n - 2)
        taper = min(1.0, 4 * t, 4 * (1 - t)) ** 0.6
        w = max(1, int(round((w0 + (w1 - w0) * t) * (0.55 + 0.45 * taper) * rnd.uniform(0.9, 1.1))))
        cv2.line(mask, tuple(np.int32(pts[i] * 4)), tuple(np.int32(pts[i + 1] * 4)), 255, w,
                 cv2.LINE_AA, shift=2)


def ink_onto(base, mask, color=INK, alpha=1.0):
    m = (mask.astype(np.float32) / 255.0 * alpha)[..., None]
    return (base * (1 - m) + np.array(color, np.float32) * m).astype(np.uint8)


def panel_border(mask, x0, y0, x1, y1, seed, w=5):
    for i, (a, b) in enumerate([((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)),
                                ((x0, y1), (x0, y0))]):
        brush(mask, wobble([a, b], 0.8, seed + i), w, w, seed + i)


# Hershey single-stroke pen lettering, set letter by letter with a hand's jitter
def letter_line(mask, text, cx, cy, size, seed, thick=None):
    rnd = random.Random(seed)
    font = cv2.FONT_HERSHEY_SIMPLEX
    sc = size / 22.0 * 3
    th = thick or max(2, int(size / 8.5 * 3))
    widths = [cv2.getTextSize(c, font, sc, th)[0][0] if c != " " else int(size * 1.1) for c in text]
    total = sum(widths) / 3 + (len(text) - 1) * size * 0.06
    x = cx - total / 2
    for c, cw in zip(text, widths):
        if c != " ":
            tile = np.zeros((int(size * 6), int(cw + size * 3)), np.uint8)
            cv2.putText(tile, c, (int(size * 1.2), int(size * 4.2)), font, sc, 255, th, cv2.LINE_AA)
            ang = rnd.uniform(-3.5, 3.5)
            M = cv2.getRotationMatrix2D((tile.shape[1] / 2, tile.shape[0] / 2), ang, 1.0)
            tile = cv2.warpAffine(tile, M, (tile.shape[1], tile.shape[0]))
            tile = cv2.resize(tile, (tile.shape[1] // 3, tile.shape[0] // 3), interpolation=cv2.INTER_AREA)
            ox = int(x - size * 0.4)
            oy = int(cy - size * 1.4 + rnd.uniform(-1.4, 1.4))
            h, w = tile.shape
            ys, xs = max(0, oy), max(0, ox)
            ye, xe = min(mask.shape[0], oy + h), min(mask.shape[1], ox + w)
            if ye > ys and xe > xs:
                sub = tile[ys - oy:ye - oy, xs - ox:xe - ox]
                mask[ys:ye, xs:xe] = np.maximum(mask[ys:ye, xs:xe], sub)
        x += cw / 3 + size * 0.06


def balloon(base, lines, cx, cy, rx, ry, tail, size, seed, fill=(250, 248, 242), cut=False):
    """Hand-ruled balloon: wobbly ellipse, tail to `tail` point, Hershey lettering inside."""
    rnd = random.Random(seed)
    ang = np.linspace(0, 2 * np.pi, 220)
    r = 1 + 0.025 * np.sin(ang * 3 + rnd.uniform(0, 6)) + 0.015 * np.sin(ang * 7 + rnd.uniform(0, 6))
    pts = np.stack([cx + rx * r * np.cos(ang), cy + ry * r * np.sin(ang)], 1)
    # tail as two lines from the rim to the tip
    tx, ty = tail
    a0 = math.atan2(ty - cy, tx - cx)
    p1 = (cx + rx * 0.82 * math.cos(a0 - 0.22), cy + ry * 0.82 * math.sin(a0 - 0.22))
    p2 = (cx + rx * 0.82 * math.cos(a0 + 0.22), cy + ry * 0.82 * math.sin(a0 + 0.22))
    fillm = np.zeros(base.shape[:2], np.uint8)
    cv2.fillPoly(fillm, [np.int32(pts)], 255, cv2.LINE_AA)
    cv2.fillPoly(fillm, [np.int32([p1, (tx, ty), p2, (cx, cy)])], 255, cv2.LINE_AA)
    if cut:  # cut-paper balloon: a soft cast shadow on the stage behind it
        sh = cv2.GaussianBlur(np.roll(np.roll(fillm, 5, 0), 4, 1), (0, 0), 4)
        base = ink_onto(base, sh, (0, 0, 0), 0.45)
    base = ink_onto(base, fillm, fill, 1.0)
    m = np.zeros(base.shape[:2], np.uint8)
    contour = cv2.findContours(fillm, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    c = max(contour, key=len)[:, 0, :].astype(np.float32)
    brush(m, np.vstack([c, c[:1]]), 3.2 if not cut else 2.0, seed=seed)
    lh = size * 1.45
    y = cy - lh * (len(lines) - 1) / 2
    for i, ln in enumerate(lines):
        letter_line(m, ln, cx, y + i * lh, size, seed + 10 + i)
    return ink_onto(base, m)


# ---------------------------------------------------------------- direction 1: brush-ink rotoscope
def rotoscope(frame_path, box, out_wh, seed, black_lv=52, hatch_lv=105, flip=False):
    """Trace one archive frame into ink: spotted blacks as filled cut contours, contour lines as
    tapered brush strokes, mid-tones as ruled hatching. Returns an ink mask (255 = ink)."""
    g = cv2.cvtColor(cv2.imread(str(frame_path)), cv2.COLOR_BGR2GRAY)
    x0, y0, x1, y1 = box
    g = g[y0:y1, x0:x1]
    if flip:
        g = g[:, ::-1]
    ow, oh = out_wh
    g = cv2.resize(g, (ow, oh), interpolation=cv2.INTER_CUBIC)
    lo, hi = np.percentile(g, 3), np.percentile(g, 99.5)
    g = np.clip((g.astype(np.float32) - lo) / (hi - lo) * 255, 0, 255).astype(np.uint8)
    g = cv2.createCLAHE(2.0, (6, 6)).apply(g)
    g = cv2.bilateralFilter(g, 9, 40, 9)
    g = cv2.GaussianBlur(g, (0, 0), 1.6)
    ink = np.zeros((oh, ow), np.uint8)
    # 1 spotted blacks: threshold, clean, re-cut as simplified polygons (the brush fills)
    blk = (g < black_lv).astype(np.uint8) * 255
    blk = cv2.morphologyEx(blk, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    blk = cv2.morphologyEx(blk, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cs, hier = cv2.findContours(blk, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    for i, c in enumerate(cs):
        if cv2.contourArea(c) < 400:
            continue
        ap = cv2.approxPolyDP(c, 1.8, True)
        col = 255 if hier[0][i][3] < 0 else 0
        cv2.fillPoly(ink, [ap], col, cv2.LINE_AA)
    # 2 contour lines: edges of the smoothed plate, long ones only, re-drawn as tapered strokes
    ed = cv2.Canny(g, 45, 110)
    cs, _ = cv2.findContours(ed, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    k = 0
    for c in cs:
        if len(c) < 70:
            continue
        p = c[:, 0, :].astype(np.float32)
        p = p[: len(p) // 2 + 1]  # Canny contours double back; keep one pass
        p = cv2.approxPolyDP(p.reshape(-1, 1, 2), 1.2, False)[:, 0, :].astype(np.float32)
        if len(p) < 3:
            continue
        brush(ink, wobble(p, 0.6, seed + k, step=3), 3.4, 2.4, seed + k)
        k += 1
    # 2b fine pen lines in the lights (faces, hands, paper): thin strokes, short contours allowed
    lit = cv2.dilate((g >= hatch_lv).astype(np.uint8) * 255, np.ones((3, 3), np.uint8))
    ed2 = cv2.bitwise_and(cv2.Canny(g, 22, 55), lit)
    cs, _ = cv2.findContours(ed2, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
    for c in cs:
        if len(c) < 22:
            continue
        p = c[:, 0, :].astype(np.float32)
        p = p[: len(p) // 2 + 1]
        if len(p) < 3:
            continue
        brush(ink, wobble(p, 0.4, seed + k, step=3), 2.2, 1.6, seed + k)
        k += 1
    # 3 hatching in the mid-greys, ruled at 35 degrees, clipped to the tone band
    mid = ((g >= black_lv) & (g < hatch_lv)).astype(np.uint8) * 255
    mid = cv2.morphologyEx(mid, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    hat = np.zeros_like(ink)
    rnd = random.Random(seed)
    for off in range(-oh, ow, 12):
        a = np.array([[off, oh], [off + oh * 0.7, 0]], np.float32)
        brush(hat, wobble(a, 0.5, seed + off, step=8), 1.3, 1.3, seed + off)
    ink = np.maximum(ink, cv2.bitwise_and(hat, mid))
    return ink


def kf1():
    base = paper(0.2)
    m = np.zeros((H, W), np.uint8)
    F = SRC / "frames"
    # panel A: the clerk lifts his head at the off-panel question (Two Pay Days, 1927, t=0.25 s)
    ax0, ay0, ax1, ay1 = 46, 52, 806, 668
    ink = rotoscope(F / "pay_0.25.png", (8, 0, 308, 240), (ax1 - ax0, ay1 - ay0), 11)
    m[ay0:ay1, ax0:ax1] = np.maximum(m[ay0:ay1, ax0:ax1], ink)
    # panel B: close on the turning head (same reel, t=0.5 s): the next drawing in the substitution
    bx0, by0, bx1, by1 = 836, 52, 1234, 360
    ink = rotoscope(F / "pay_0.5.png", (92, 4, 212, 97), (bx1 - bx0, by1 - by0), 23)
    m[by0:by1, bx0:bx1] = np.maximum(m[by0:by1, bx0:bx1], ink)
    # panel C: the key cupboard, closed, waiting (The Electric House, 1922, t=1.0 s)
    cx0, cy0, cx1, cy1 = 836, 390, 1234, 668
    ink = rotoscope(F / "elec_1.png", (20, 30, 290, 210), (cx1 - cx0, cy1 - cy0), 37, black_lv=40, hatch_lv=90)
    m[cy0:cy1, cx0:cx1] = np.maximum(m[cy0:cy1, cx0:cx1], ink)
    for i, b in enumerate([(ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1), (cx0, cy0, cx1, cy1)]):
        panel_border(m, *b, seed=100 + 7 * i, w=5)
    out = ink_onto(base, m)
    # the question arrives from another room: the tail runs out of the panel, across the gutter
    out = balloon(out, ["What time", "is it?"], 640, 140, 128, 70, (836, 214), 26, 5)
    # KEYS label hand-lettered on the cupboard
    m2 = np.zeros((H, W), np.uint8)
    letter_line(m2, "KEYS", 1035, 420, 17, 77)
    out = ink_onto(out, m2)
    return out


# ---------------------------------------------------------------- direction 2: photo-fumetti cutout
def grabcut_person(img, rect, cut_y):
    mask = np.zeros(img.shape[:2], np.uint8)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, rect, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
    fg[cut_y:] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(fg)
    big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    fg = np.where(lab == big, 255, 0).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # scissor-cut edge: simplify the silhouette into straight facets
    cs, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    out = np.zeros_like(fg)
    cv2.fillPoly(out, [cv2.approxPolyDP(c, 2.5, True)], 255, cv2.LINE_AA)
    return out


def tone(a, lo, hi, gamma=1.0):
    a = np.clip((a.astype(np.float32) - lo) / (hi - lo), 0, 1) ** gamma
    return (a * 255).astype(np.uint8)


def paste(base, rgb, alpha, x, y):
    h, w = alpha.shape
    ys, xs, ye, xe = max(0, y), max(0, x), min(base.shape[0], y + h), min(base.shape[1], x + w)
    a = (alpha[ys - y:ye - y, xs - x:xe - x].astype(np.float32) / 255)[..., None]
    base[ys:ye, xs:xe] = (base[ys:ye, xs:xe] * (1 - a) + rgb[ys - y:ye - y, xs - x:xe - x] * a).astype(np.uint8)
    return base


def kf2():
    base = paper(0.3)
    roth = cv2.imread(str(SRC / "loc" / "8b16710v.jpg"))
    g = cv2.cvtColor(roth, cv2.COLOR_BGR2GRAY)
    gt = tone(g, 28, 215, 0.85)  # high-key print, blacks held
    # panel A (narrow): the ticket window; "Thanks!" comes back from the platform
    ax0, ay0, ax1, ay1 = 46, 52, 400, 668
    crop = gt[170:470, 40:280]
    crop = cv2.resize(crop, (ax1 - ax0, ay1 - ay0), interpolation=cv2.INTER_CUBIC)
    base[ay0:ay1, ax0:ax1] = np.repeat(crop[..., None], 3, 2)
    # panel B (wide): the cupboard, door swung on a paper hinge, the clerk cut from his own desk
    bx0, by0, bx1, by1 = 430, 52, 1234, 668
    bw, bh = bx1 - bx0, by1 - by0
    plate = gt[150:470, 640:1015]  # cupboard wall, boxes above
    sc = max(bw / plate.shape[1], bh / plate.shape[0])
    plate = cv2.resize(plate, (int(plate.shape[1] * sc), int(plate.shape[0] * sc)), interpolation=cv2.INTER_CUBIC)
    ox = (plate.shape[1] - bw) // 2
    stage = np.repeat(plate[:bh, ox:ox + bw, None], 3, 2).copy()
    # cut the left cupboard door (source x 745..860, y 185..440) and swing it open on its hinge
    dx0, dy0, dx1, dy1 = [int(v) for v in ((745 - 640) * sc - ox, (182 - 150) * sc, (862 - 640) * sc - ox, (445 - 150) * sc)]
    door = stage[dy0:dy1, dx0:dx1].copy()
    stage[dy0:dy1, dx0:dx1] = (18, 17, 16)  # dark interior behind the opened door
    # shelves inside, cut from the ticket rack of the same photograph
    rack = gt[115:390, 405:570]
    tgt = stage[dy0 + 15:dy1 - 15, dx0 + 12:dx1 - 12]
    rack = cv2.resize(rack, (tgt.shape[1], tgt.shape[0]))
    rack = (rack.astype(np.float32) * 0.55).astype(np.uint8)
    tgt[:] = np.repeat(rack[..., None], 3, 2)
    open_w = int(door.shape[1] * 0.38)  # foreshortened as it swings toward us
    src = np.float32([[0, 0], [door.shape[1], 0], [door.shape[1], door.shape[0]], [0, door.shape[0]]])
    dst = np.float32([[0, 0], [open_w, -22], [open_w, door.shape[0] + 22], [0, door.shape[0]]])
    Mx = cv2.getPerspectiveTransform(src, dst)
    dw = cv2.warpPerspective(door, Mx, (open_w + 2, door.shape[0] + 46), borderValue=(0, 0, 0))
    da = cv2.warpPerspective(np.full(door.shape[:2], 255, np.uint8), Mx, (open_w + 2, door.shape[0] + 46))
    sh = cv2.GaussianBlur(da, (0, 0), 6)
    paste(stage, np.zeros_like(dw), (sh * 0.5).astype(np.uint8), dx0 - open_w - 4, dy0 - 4)
    paste(stage, dw, da, dx0 - open_w, dy0 - 22)
    # the clerk: GrabCut from the desk plate, cut at the waist, head on its own hinge
    rect = (535, 355, 345, 300)
    fg = grabcut_person(roth, rect, 612)
    ys, xs = np.nonzero(fg)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    fig = np.repeat(gt[y0:y1, x0:x1, None], 3, 2)
    fa = fg[y0:y1, x0:x1]
    s2 = 1.55
    fig = cv2.resize(fig, None, fx=s2, fy=s2, interpolation=cv2.INTER_CUBIC)
    fa = cv2.resize(fa, None, fx=s2, fy=s2, interpolation=cv2.INTER_LINEAR)
    # articulate the head: split at the collar and tilt it back toward the shelves (FK hinge)
    neck = int((450 - y0) * s2)
    head, ha = fig[:neck].copy(), fa[:neck].copy()
    fa_body = fa.copy()
    fa_body[:neck - 6] = 0
    pivot = (int((700 - x0) * s2), neck)
    M = cv2.getRotationMatrix2D(pivot, 9, 1.0)
    head = cv2.warpAffine(head, M, (fig.shape[1], neck), borderValue=(0, 0, 0))
    ha = cv2.warpAffine(ha, M, (fig.shape[1], neck))
    # white scissor margin around each piece, then a cast shadow on the plate
    def margin(a, r=5):
        return cv2.dilate(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    px, py = int(bw * 0.52), bh - fig.shape[0] + 30
    full = np.zeros(fa.shape, np.uint8)
    full = np.maximum(full, margin(fa_body))
    full[:neck] = np.maximum(full[:neck], margin(ha))
    shadow = cv2.GaussianBlur(full, (0, 0), 7)
    paste(stage, np.zeros_like(fig), (shadow * 0.55).astype(np.uint8), px + 12, py + 8)
    paste(stage, np.full_like(fig, 246), full, px, py)
    paste(stage, fig, fa_body, px, py)
    hb = np.zeros_like(fig)
    hb[:neck] = head
    hal = np.zeros(fa.shape, np.uint8)
    hal[:neck] = ha
    paste(stage, hb, hal, px, py)
    base[by0:by1, bx0:bx1] = stage
    m = np.zeros((H, W), np.uint8)
    panel_border(m, ax0, ay0, ax1, ay1, 201, 5)
    panel_border(m, bx0, by0, bx1, by1, 209, 5)
    out = ink_onto(base, m)
    out = balloon(out, ["Thanks!"], 250, 120, 96, 46, (400, 90), 26, 41, cut=True)
    out = balloon(out, ["What the hell", "was I looking", "for, anyway?"], 700, 150, 170, 92, (905, 300), 25, 43, cut=True)
    return out


# ---------------------------------------------------------------- direction 3: cut-paper shadow page
def cutpoly(pts, seed, amp=1.2):
    """Scissor facets: straight cuts between slightly jittered vertices."""
    rnd = random.Random(seed)
    return np.int32([[x + rnd.uniform(-amp, amp), y + rnd.uniform(-amp, amp)] for x, y in pts])


def limb(p, ang, length, w0, w1):
    """A tapered card limb from p at angle ang (deg, 0 = down). Returns polygon and end point."""
    a = math.radians(ang)
    dx, dy = math.sin(a), math.cos(a)
    nx, ny = dy, -dx
    e = (p[0] + dx * length, p[1] + dy * length)
    poly = [(p[0] + nx * w0, p[1] + ny * w0), (e[0] + nx * w1, e[1] + ny * w1),
            (e[0] - nx * w1, e[1] - ny * w1), (p[0] - nx * w0, p[1] - ny * w0)]
    return poly, e


def puppet(mask, hip, s, pose, seed):
    """Reiniger-style hinged card puppet, forward kinematics from the hip.
    pose: thigh/shin/upper-arm/forearm angles for near and far sides, torso lean, head turn."""
    k = seed
    parts = []
    lean = pose["lean"]
    neck = (hip[0] + math.sin(math.radians(lean)) * -110 * s, hip[1] - 110 * s)
    # torso: jacket with a back vent, waistline
    t = [(hip[0] - 24 * s, hip[1] + 6 * s), (hip[0] + 26 * s, hip[1] + 6 * s), (neck[0] + 22 * s, neck[1] + 12 * s),
         (neck[0] + 8 * s, neck[1] - 2 * s), (neck[0] - 12 * s, neck[1] - 2 * s), (neck[0] - 26 * s, neck[1] + 14 * s)]
    parts.append(t)
    # head in profile facing pose['face'] (+1 right, -1 left): skull, nose, chin, collar
    f = pose["face"]
    hx, hy = neck[0] + 2 * s * f, neck[1] - 30 * s
    head = []
    for i in range(18):
        a = math.radians(i * 20)
        head.append((hx + 19 * s * math.cos(a), hy + 22 * s * math.sin(a)))
    parts.append(head)
    parts.append([(hx + 16 * s * f, hy - 6 * s), (hx + 29 * s * f, hy + 6 * s), (hx + 17 * s * f, hy + 9 * s)])  # nose
    parts.append([(hx + 12 * s * f, hy + 14 * s), (hx + 20 * s * f, hy + 18 * s), (hx + 6 * s * f, hy + 26 * s)])  # chin
    # hair tuft at the back and an open mouth notch is cut later
    parts.append([(hx - 18 * s * f, hy - 14 * s), (hx - 4 * s * f, hy - 28 * s), (hx + 12 * s * f, hy - 22 * s),
                  (hx - 22 * s * f, hy + 2 * s)])
    for side in ("far", "near"):
        th, e1 = limb(hip, pose[side + "_thigh"], 62 * s, 13 * s, 9 * s)
        sh, e2 = limb(e1, pose[side + "_shin"], 60 * s, 9 * s, 6 * s)
        a = math.radians(pose[side + "_shin"])
        foot = [(e2[0] - 6 * s, e2[1] - 3 * s), (e2[0] + 24 * s * f * math.cos(a), e2[1] + 3 * s),
                (e2[0] + 22 * s * f, e2[1] + 8 * s), (e2[0] - 8 * s, e2[1] + 8 * s)]
        sho = (neck[0] - 4 * s, neck[1] + 12 * s)
        ua, e3 = limb(sho, pose[side + "_upper"], 50 * s, 9 * s, 7 * s)
        fa, e4 = limb(e3, pose[side + "_fore"], 46 * s, 7 * s, 5 * s)
        hand = [(e4[0] + 7 * s * math.cos(i * 0.9), e4[1] + 7 * s * math.sin(i * 0.9)) for i in range(7)]
        parts += [th, sh, foot, ua, fa, hand]
    for i, p in enumerate(parts):
        cv2.fillPoly(mask, [cutpoly(p, k + i)], 255, cv2.LINE_AA)
    # the mouth, cut open: he is answering
    cv2.fillPoly(mask, [cutpoly([(hx + 21 * s * f, hy + 10 * s), (hx + 11 * s * f, hy + 12 * s),
                                 (hx + 20 * s * f, hy + 14 * s)], k + 99, 0.3)], 0, cv2.LINE_AA)
    # rivets at the joints (visible as tiny light holes, as in hinged card)
    for p in (hip, neck):
        cv2.circle(mask, (int(p[0]), int(p[1])), max(1, int(2 * s)), 0, -1, cv2.LINE_AA)


def kf3():
    # backlit stage: the 1934 sheet lit from behind, light falling off toward the edges
    pap = paper(0.85).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    glow = 1.08 - 0.42 * (((xx - 640) / 820) ** 2 + ((yy - 330) / 560) ** 2)
    stage = np.clip(pap * glow[..., None] * np.array([1.0, 0.94, 0.80]), 0, 255)
    # far layer (tissue further from the glass): doorway to the platform, window, clock, in soft grey
    far = np.zeros((H, W), np.uint8)
    cv2.fillPoly(far, [cutpoly([(40, 120), (150, 120), (150, 610), (40, 610)], 1)], 255)  # door jamb mass
    cv2.fillPoly(far, [cutpoly([(560, 150), (760, 150), (760, 330), (560, 330)], 2)], 255)  # window
    for x in (610, 660, 710):
        cv2.line(far, (x, 150), (x, 330), 0, 6)
    cv2.line(far, (560, 240), (760, 240), 0, 6)
    cv2.circle(far, (470, 170), 34, 255, -1, cv2.LINE_AA)
    cv2.circle(far, (470, 170), 27, 0, -1, cv2.LINE_AA)
    cv2.line(far, (470, 170), (470, 148), 255, 4, cv2.LINE_AA)  # ten past four on the station clock
    cv2.line(far, (470, 170), (488, 176), 255, 4, cv2.LINE_AA)
    cv2.line(far, (470, 170), (482, 151), 255, 3, cv2.LINE_AA)
    farb = cv2.GaussianBlur(far, (0, 0), 3.2)
    stage = stage * (1 - farb[..., None] / 255 * 0.52)
    # near layer (card on the glass): floor, desk and lamp, cupboard with key hooks, the clerk
    near = np.zeros((H, W), np.uint8)
    cv2.fillPoly(near, [cutpoly([(0, 618), (W, 610), (W, H), (0, H)], 3)], 255)
    desk = [(180, 470), (400, 470), (400, 486), (388, 486), (388, 616), (372, 616), (372, 500), (210, 500),
            (210, 616), (194, 616), (194, 486), (180, 486)]
    cv2.fillPoly(near, [cutpoly(desk, 4)], 255, cv2.LINE_AA)
    cv2.fillPoly(near, [cutpoly([(230, 470), (240, 400), (226, 396), (262, 350), (300, 372), (252, 404),
                                 (250, 470)], 5)], 255, cv2.LINE_AA)  # lamp
    # chair pushed back, as he left it
    cv2.fillPoly(near, [cutpoly([(415, 520), (470, 520), (470, 532), (466, 616), (456, 616), (458, 532),
                                 (428, 532), (424, 616), (414, 616), (418, 532), (412, 532), (404, 430),
                                 (414, 428)], 6)], 255, cv2.LINE_AA)
    # cupboard with a cut fretwork panel and a row of key hooks, a key shape on one hook
    cv2.fillPoly(near, [cutpoly([(1010, 200), (1210, 200), (1210, 616), (1010, 616)], 7)], 255, cv2.LINE_AA)
    cv2.fillPoly(near, [cutpoly([(1030, 230), (1100, 230), (1100, 420), (1030, 420)], 8)], 0, cv2.LINE_AA)
    cv2.fillPoly(near, [cutpoly([(1120, 230), (1190, 230), (1190, 420), (1120, 420)], 9)], 0, cv2.LINE_AA)
    for i in range(4):  # the fret: hooks and one key hanging inside the left light panel
        cv2.line(near, (1040 + i * 17, 250), (1040 + i * 17, 262), 255, 3)
    cv2.circle(near, (1057, 285), 9, 255, -1, cv2.LINE_AA)
    cv2.circle(near, (1057, 285), 4, 0, -1, cv2.LINE_AA)
    cv2.fillPoly(near, [np.int32([(1054, 292), (1060, 292), (1060, 330), (1054, 330)])], 255)
    cv2.fillPoly(near, [np.int32([(1060, 318), (1068, 318), (1068, 324), (1060, 324)])], 255)
    cv2.fillPoly(near, [np.int32([(1060, 306), (1066, 306), (1066, 311), (1060, 311)])], 255)
    for x0 in (1030, 1120):  # door lattice in the right light panel
        pass
    for y in range(250, 420, 26):
        cv2.line(near, (1120, y), (1190, y), 255, 3)
    cv2.circle(near, (1108, 470), 7, 0, -1, cv2.LINE_AA)  # keyhole
    # the clerk mid-stride toward the cupboard, head turned back to answer the platform
    pose = dict(lean=-4, face=-1, near_thigh=-26, near_shin=-6, far_thigh=24, far_shin=48,
                near_upper=-24, near_fore=-48, far_upper=22, far_fore=8)
    puppet(near, (790, 470), 1.25, pose, 50)
    # a little blur ghost under the card: it lifts off the glass at the toes (secondary)
    halo = cv2.GaussianBlur(near, (0, 0), 6)
    stage = stage * (1 - halo[..., None] / 255 * 0.25)
    stage = stage * (1 - near[..., None] / 255 * 0.94)
    out = stage.astype(np.uint8)
    # the page: one black card cut with three windows over the continuous stage
    card = np.full((H, W), 255, np.uint8)
    wins = [(46, 52, 452, 668), (480, 52, 878, 668), (906, 52, 1234, 668)]
    for i, (x0, y0, x1, y1) in enumerate(wins):
        cv2.fillPoly(card, [cutpoly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 300 + i, 1.6)], 0, cv2.LINE_AA)
    cardc = np.array([24, 22, 21], np.float32)
    # card has its own front-lit fibre: pull a dark version of the paper
    tex = paper(0.0).astype(np.float32) / 255 * 0.22
    cardimg = cardc + tex * 60
    a = (card.astype(np.float32) / 255)[..., None]
    out = (out * (1 - a) + cardimg * a).astype(np.uint8)
    # cut-paper balloons pinned across the card: the question from the platform, his answer
    out = balloon(out, ["What time", "is it?"], 250, 118, 118, 62, (44, 250), 25, 61, cut=True)
    out = balloon(out, ["Ten past", "four!"], 600, 128, 104, 64, (520, 268), 27, 63, cut=True)
    return out


def board(kfs, names):
    ref = Image.open(ROOT / "assets" / "references" / "madden1.webp").convert("RGB")
    th = 470
    ref = ref.resize((int(ref.width * th / ref.height), th), Image.LANCZOS)
    kw = int(W * th / H) // 1
    tiles = [ref] + [Image.fromarray(k).resize((int(W * (th / 1.0) / H), th), Image.LANCZOS) for k in kfs]
    # two rows: reference + kf1 on top, kf2 + kf3 below
    pad, lab = 16, 34
    row1 = [tiles[0], tiles[1]]
    row2 = [tiles[2], tiles[3]]
    wid = max(sum(t.width for t in row1), sum(t.width for t in row2)) + pad * 3
    hei = 2 * (th + lab) + pad * 3
    b = Image.new("RGB", (wid, hei), (240, 238, 232))
    d = ImageDraw.Draw(b)
    labels = ["Reference: Madden, Template (2005)"] + names
    y = pad
    k = 0
    for row in (row1, row2):
        x = pad
        for t in row:
            b.paste(t, (x, y + lab))
            lm = np.zeros((lab, t.width), np.uint8)
            letter_line(lm, labels[k], t.width // 2, lab // 2 + 4, 16, 900 + k)
            lab_img = Image.fromarray(255 - lm).convert("RGB")
            b.paste(lab_img, (x, y))
            x += t.width + pad
            k += 1
        y += th + lab + pad
    if b.width > 2000:
        b = b.resize((2000, int(b.height * 2000 / b.width)), Image.LANCZOS)
    return b


if __name__ == "__main__":
    names = ["1 Brush-Ink Rotoscope", "2 Photo-Fumetti Cutout", "3 Cut-Paper Shadow Page"]
    ks = [kf1(), kf2(), kf3()]
    for i, k in enumerate(ks, 1):
        Image.fromarray(k).save(HERE / f"kf-{i}.png")
    board(ks, names).save(HERE / "board.jpg", quality=90)
    print("ok")
