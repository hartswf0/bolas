"""99 ways, batch 1, page maker 2 (pages 05-08): shared HANDMADE tools.

- One cut-paper figure model (agent in profile: waistcoat, shirt sleeves, sleeve garter, spectacles,
  pencil; stranger bust: cloche hat with a bow, coat collar) authored here as control points, so the
  same people can be cut as shadow puppets (05), printed small round a disc (06), brushed (07) and
  stencilled (08).  Every shape is a closed Catmull-Rom curve reduced to straight scissor facets.
- Lettering is always the shared pen hand (films/swarm/99-ways/kit/pen99.py -> penlib).
Only decoded pixels are read from foraged files (PIL / OpenCV); nothing foraged is executed.
"""
import fcntl
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path("/home/user/bolas/paeleo/scion/oulipo")
sys.path.insert(0, str(ROOT / "films" / "swarm" / "99-ways" / "kit"))
import pen99  # noqa: E402
import penlib  # noqa: E402

SRC = ROOT / "films" / "sources" / "99-ways"
MASTERS = SRC / "masters"
BEATS = SRC / "beats"
PAGES_OUT = ROOT / "assets" / "pages" / "99-ways"
RECORDS = ROOT / "films" / "swarm" / "99-ways" / "pages"
CREDITS = ROOT / "films" / "credits" / "99-ways.json"
TPL_PIECES = ROOT / "films" / "sources" / "99-ways-template" / "cutout-surgeon" / "pieces"
W, H = 2200, 2850
INK = np.array([18, 17, 16], np.float32)


# ------------------------------------------------------------------ geometry
def catmull(pts, n=10):
    P = [np.array(p, float) for p in pts]
    m = len(P)
    out = []
    for i in range(m):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % m], P[(i + 2) % m]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def Mx(tx=0, ty=0, deg=0, s=1.0, flip=False):
    a = math.radians(deg)
    c, si = math.cos(a) * s, math.sin(a) * s
    F = np.diag([-1.0 if flip else 1.0, 1.0, 1.0])
    return np.array([[c, -si, tx], [si, c, ty], [0, 0, 1]]) @ F


def tf(M, pts):
    p = np.asarray(pts, float)
    q = np.c_[p, np.ones(len(p))] @ M.T
    return q[:, :2]


class Shape:
    """A closed cut shape in world coordinates. role: body part / colour role; hole: cut through."""
    def __init__(self, pts, role, hole=False, smooth=True, z=0):
        self.pts, self.role, self.hole, self.smooth, self.z = np.asarray(pts, float), role, hole, smooth, z

    def curve(self):
        return catmull(self.pts) if self.smooth else self.pts


def circle_pts(cx, cy, r, n=14):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def bar_pts(a, b, w):
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-9) * w / 2
    return [a + nrm, b + nrm, b - nrm, a - nrm]


# local part outlines (agent faces +x, y down, units ~ px for a 950-tall figure)
HEAD = [(-26, 4), (-34, -20), (-52, -58), (-57, -98), (-46, -134), (-16, -153), (18, -151), (40, -134),
        (48, -112), (50, -100), (60, -94), (82, -66), (78, -60), (60, -58), (60, -51), (52, -47), (58, -40),
        (56, -28), (44, -16), (24, -8), (20, 4)]
HAIR = [(-54, -78), (-58, -108), (-44, -140), (-14, -158), (20, -156), (44, -132), (47, -118), (18, -130),
        (-12, -125), (-36, -104), (-41, -78)]
EAR = [(-14, -88), (-4, -96), (2, -80), (-4, -66), (-14, -70)]
TORSO = [(-66, 0), (-76, -120), (-72, -230), (-54, -300), (-30, -322), (-8, -332), (20, -332), (42, -318),
         (64, -272), (98, -196), (122, -124), (114, -50), (84, 0)]
SHIRT_V = [(-6, -334), (22, -334), (46, -312), (30, -248), (12, -290)]
TIE = [(17, -318), (25, -318), (32, -246), (24, -232), (16, -246)]
TROUSER = [(-48, 0), (50, 0), (48, 110), (42, 210), (40, 352), (78, 360), (88, 380), (-42, 380), (-44, 352),
           (-48, 210), (-52, 110)]
UPPER = [(-32, -6), (30, -10), (40, 60), (34, 140), (24, 176), (-24, 176), (-36, 120), (-38, 40)]
FORE = [(-23, -6), (23, -6), (19, 80), (16, 142), (-16, 142), (-21, 80)]
HAND = [(-17, -4), (19, -4), (27, 24), (23, 50), (2, 60), (-16, 46), (-21, 20)]

S_COAT = [(-92, 0), (-88, -80), (-62, -128), (-22, -148), (14, -150), (42, -128), (72, -88), (88, 0)]
S_COLLAR = [(-30, -146), (14, -150), (44, -124), (30, -92), (6, -120), (-24, -118)]
S_HEAD = [(-26, -146), (-36, -188), (-30, -222), (-4, -242), (24, -238), (38, -219), (42, -204), (54, -190),
          (43, -183), (43, -173), (39, -163), (24, -152)]
S_HAT = [(-50, -192), (-52, -236), (-30, -262), (6, -269), (34, -256), (46, -234), (60, -206), (52, -202),
         (40, -212), (0, -214), (-36, -196)]
S_BOW = [(-40, -238), (-58, -252), (-62, -232), (-46, -226)]
S_GLOVE = [(-14, 0), (16, -4), (24, -40), (30, -78), (22, -94), (10, -84), (4, -52), (-12, -30)]


def agent(x, floor, face=1, scale=1.0, legs=(8, -8), lean=0, tilt=0, sh=20, el=-60, wr=0,
          pencil=True, pencil_deg=None, seated=False, far_arm=None, glasses=True):
    """Return Shapes of the agent. face=+1 looks right, -1 left. Angles in degrees, + = clockwise on screen
    for a right-facing figure. sh: upper-arm swing (forward +), el: elbow bend (forward -), wr: wrist."""
    flip = face < 0
    hip_h = 380 * scale
    base = Mx(x, floor - hip_h, 0, scale, flip)
    out = []
    # far arm first (behind torso), then legs, torso, head, near arm
    T = base @ Mx(0, 0, lean)
    if far_arm is not None:
        fa_sh, fa_el = far_arm
        U = T @ Mx(-14, -296) @ Mx(0, 0, -fa_sh)
        out.append(Shape(tf(U, UPPER), "sleeve_far", z=-2))
        Fm = U @ Mx(0, 168) @ Mx(0, 0, -fa_el)
        out.append(Shape(tf(Fm, FORE), "skin_far", z=-2))
        out.append(Shape(tf(Fm @ Mx(0, 140), HAND), "skin_far", z=-2))
    if not seated:
        for k, a in enumerate(legs):
            L = base @ Mx(0, 0, -a)
            out.append(Shape(tf(L, TROUSER), "trousers", z=-1 if k == 1 else 0))
    out.append(Shape(tf(T, TORSO), "waistcoat"))
    out.append(Shape(tf(T, SHIRT_V), "shirt", z=1))
    out.append(Shape(tf(T, TIE), "tie", z=2))
    for k, by in enumerate((-196, -140, -84)):
        bx = 104 + 12 * math.sin((by + 140) / 120)
        out.append(Shape(tf(T, circle_pts(bx - 6, by, 5.5, 8)), "button", hole=True, z=3))
    Hm = T @ Mx(6, -330) @ Mx(0, 0, tilt)
    out.append(Shape(tf(Hm, HEAD), "skin"))
    out.append(Shape(tf(Hm, HAIR), "hair", z=1))
    out.append(Shape(tf(Hm, EAR), "ear", z=1))
    if glasses:
        out.append(Shape(tf(Hm, circle_pts(36, -88, 10, 14)), "glass", hole=True, z=3))
        out.append(Shape(tf(Hm, circle_pts(36, -88, 5.5, 12)), "glass_in", z=4))
        out.append(Shape(tf(Hm, bar_pts((-8, -90), (26, -90), 3.0)), "glass_arm", hole=True, smooth=False, z=3))
    U = T @ Mx(-10, -292) @ Mx(0, 0, -sh)
    out.append(Shape(tf(U, UPPER), "sleeve", z=5))
    out.append(Shape(tf(U, bar_pts((-37, 92), (36, 88), 5)), "garter", hole=True, smooth=False, z=6))
    Fm = U @ Mx(0, 168) @ Mx(0, 0, -el)
    out.append(Shape(tf(Fm, FORE), "skin", z=5))
    Hd = Fm @ Mx(0, 140) @ Mx(0, 0, -wr)
    out.append(Shape(tf(Hd, HAND), "skin", z=5))
    if pencil:
        pd = 200 if pencil_deg is None else pencil_deg
        a = math.radians(pd)
        p0 = np.array([4, 26])
        p1 = p0 + 92 * np.array([math.sin(a), -math.cos(a)])
        out.append(Shape(tf(Hd, bar_pts(p0, p1, 8)), "pencil", smooth=False, z=6))
    # pin joints (light through the rivet holes), shoulder and elbow
    for M0, p in ((U, (0, 4)), (Fm, (0, 2))):
        out.append(Shape(tf(M0, circle_pts(p[0], p[1], 4.5, 8)), "pin", hole=True, z=7))
    return out


def stranger(x, sill, face=1, scale=1.0, tilt=0, glove=False, nod=0):
    flip = face < 0
    B = Mx(x, sill, 0, scale, flip)
    out = [Shape(tf(B, S_COAT), "coat"), Shape(tf(B, S_COLLAR), "collar", z=1)]
    Hm = B @ Mx(0, -148) @ Mx(0, 0, tilt + nod) @ Mx(0, 148)
    out += [Shape(tf(Hm, S_HEAD), "skin_s"), Shape(tf(Hm, S_HAT), "hat", z=1), Shape(tf(Hm, S_BOW), "bow", z=2),
            Shape(tf(Hm, circle_pts(32, -196, 4.5, 10)), "eye", hole=True, z=3)]
    if glove:
        out.append(Shape(tf(B @ Mx(56, -10), S_GLOVE), "glove", z=3))
    return out


def raster(shapes, w, h, ss=2, facet=1.0, roles=None, holes=True, offset=(0, 0)):
    """Union mask (uint8 w x h) of the shapes, cut holes, straight scissor facets."""
    m = np.zeros((h * ss, w * ss), np.uint8)
    for s in sorted(shapes, key=lambda s: s.z):
        if roles is not None and s.role not in roles:
            continue
        if s.hole and not holes:
            continue
        c = (s.curve() + np.array(offset)) * ss
        c = cv2.approxPolyDP(np.int32(c * 4).reshape(-1, 1, 2), facet * ss * 4, True)
        cv2.fillPoly(m, [c], 0 if s.hole else 255, cv2.LINE_AA, shift=2)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)


# ------------------------------------------------------------------ the ANRC key (99-ways-template cutout)
def key_alpha():
    a = np.asarray(Image.open(TPL_PIECES / "key.png"))[..., 3]
    return a


def key_gray():
    return np.asarray(Image.open(TPL_PIECES / "key.png").convert("L")).astype(np.float32)


def paste_mask(dst, src, x, y, scale=1.0, deg=0.0):
    """Max-paste uint8 mask src (centred on x,y) into dst after scale/rotate."""
    h, w = src.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -deg, scale)
    M[0, 2] += x - w / 2
    M[1, 2] += y - h / 2
    warped = cv2.warpAffine(src, M, (dst.shape[1], dst.shape[0]), flags=cv2.INTER_LINEAR)
    np.maximum(dst, warped, out=dst)
    return dst


# ------------------------------------------------------------------ pen lettering helpers
def letter(lines, cap, seed, weight=0.13):
    return pen99.letter(lines, cap, seed, weight)


def put_mask(canvas_mask, m, cx, cy):
    """Paste lettering mask m centred at (cx, cy) into a page-size mask (max)."""
    h, w = m.shape
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    H0, W0 = canvas_mask.shape
    xs, ys, xe, ye = max(0, x0), max(0, y0), min(W0, x0 + w), min(H0, y0 + h)
    if xe > xs and ye > ys:
        sub = canvas_mask[ys:ye, xs:xe]
        np.maximum(sub, m[ys - y0:ye - y0, xs - x0:xe - x0], out=sub)
    return canvas_mask


def wrap(text, cap, width):
    """Greedy wrap by the pen hand's advances."""
    words, lines, cur = text.split(), [], ""
    adv = lambda s: sum(penlib.GLYPHS[c][0] * cap + cap * .1 for c in pen99.clean(s))
    for wd in words:
        t = (cur + " " + wd).strip()
        if adv(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def letter_left(lines, cap, seed, weight=0.13):
    """Left-aligned lettering: one mask per line, stacked."""
    ms = [pen99.letter([l], cap, seed + i, weight) for i, l in enumerate(lines)]
    lh = int(cap * 1.42)
    Wm = max(m.shape[1] for m in ms)
    Hm = lh * (len(ms) - 1) + ms[-1].shape[0]
    out = np.zeros((Hm, Wm), np.uint8)
    for i, m in enumerate(ms):
        y = i * lh
        out[y:y + m.shape[0], :m.shape[1]] = np.maximum(out[y:y + m.shape[0], :m.shape[1]], m)
    return out


def blit_mask(dst, m, x0, y0):
    h, w = m.shape
    H0, W0 = dst.shape
    xs, ys, xe, ye = max(0, x0), max(0, y0), min(W0, x0 + w), min(H0, y0 + h)
    if xe > xs and ye > ys:
        sub = dst[ys:ye, xs:xe]
        np.maximum(sub, m[ys - y0:ye - y0, xs - x0:xe - x0], out=sub)
    return dst


def comp(base, mask, color, alpha=1.0):
    a = (mask.astype(np.float32) / 255.0 * alpha)[..., None]
    base *= (1 - a)
    base += np.asarray(color, np.float32) * a
    return base


# ------------------------------------------------------------------ output
def save_page(img, n, pid, title):
    img = np.clip(np.round(img), 0, 255).astype(np.uint8)
    assert img.shape == (H, W, 3)
    pen99.folio(img, n, title)
    MASTERS.mkdir(parents=True, exist_ok=True)
    PAGES_OUT.mkdir(parents=True, exist_ok=True)
    im = Image.fromarray(img)
    im.save(MASTERS / f"{n:02d}-{pid}.png", optimize=True)
    jp = PAGES_OUT / f"{n:02d}-{pid}.jpg"
    im.save(jp, quality=90)
    return img, jp.stat().st_size


def save_beats(n, frames):
    d = BEATS / f"{n:02d}"
    d.mkdir(parents=True, exist_ok=True)
    for f in d.glob("b*.png"):
        f.unlink()
    for i, fr in enumerate(frames, 1):
        im = Image.fromarray(np.clip(np.round(fr), 0, 255).astype(np.uint8))
        if im.size != (960, 1242):
            im = im.resize((960, 1242), Image.LANCZOS)
        im.save(d / f"b{i:02d}.png", optimize=True)
    return len(frames)


def write_record(rec):
    RECORDS.mkdir(parents=True, exist_ok=True)
    with open(RECORDS / f"{rec['n']:02d}.json", "w") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False)


def credit_pages(ids, n, new_entries=()):
    """Additively record page n on existing credit ids; append new entries. Locked read-modify-write."""
    with open(CREDITS, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        d = json.load(f)
        have = {e["id"]: e for e in d}
        for e in new_entries:
            if e["id"] not in have:
                d.append(e)
                have[e["id"]] = e
        for i in ids:
            e = have[i]
            pg = e.setdefault("pages", [])
            if n not in pg:
                pg.append(n)
                pg.sort()
        f.seek(0)
        f.truncate()
        json.dump(d, f, indent=1, ensure_ascii=False)
        fcntl.flock(f, fcntl.LOCK_UN)


# ------------------------------------------------------------------ scenery cut pieces (absolute coords)
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def R_(x0, y0, x1, y1, role, hole=False, z=0):
    return Shape(rect(x0, y0, x1, y1), role, hole=hole, smooth=False, z=z)


def desk(x0, top, w, floor, drawers=2):
    s = [R_(x0 - 14, top, x0 + w + 14, top + 24, "desk"),
         R_(x0, top + 24, x0 + w * 0.38, floor - 30, "desk"),
         R_(x0 + w * 0.38, top + 24, x0 + w, top + 120, "desk"),
         R_(x0 + w - 28, top + 120, x0 + w, floor, "desk"), R_(x0, floor - 30, x0 + 26, floor, "desk"),
         R_(x0 + w * 0.38 - 26, floor - 30, x0 + w * 0.38, floor, "desk")]
    for k in range(drawers):
        y = top + 60 + k * (floor - top - 110) / drawers
        s.append(R_(x0 + 22, y, x0 + w * 0.38 - 22, y + 5, "slit", hole=True, z=1))
        s.append(Shape(circle_pts(x0 + w * 0.19, y + 30, 6, 8), "slit", hole=True, z=1))
    s.append(R_(x0 + w * 0.45, top + 70, x0 + w * 0.93, top + 75, "slit", hole=True, z=1))
    return s


def lamp(x, top, h):
    shade = [(x - 70, top + 70), (x - 40, top), (x + 40, top), (x + 70, top + 70)]
    return [Shape(shade, "lamp", smooth=False), R_(x - 6, top + 70, x + 6, top + h - 14, "lamp"),
            Shape([(x - 44, top + h), (x - 30, top + h - 18), (x + 30, top + h - 18), (x + 44, top + h)], "lamp", smooth=False)]


def window(x0, y0, w, h, sill=None, header=90):
    """Ticket window frame: header board (lettering cut later), posts, sill counter, glazing bars."""
    sill = y0 + h * 0.66 if sill is None else sill
    t = 26
    s = [R_(x0 - 30, y0, x0 + w + 30, y0 + header, "window"),
         R_(x0 - 30, y0, x0, y0 + h, "window"), R_(x0 + w, y0, x0 + w + 30, y0 + h, "window"),
         R_(x0 - 60, sill, x0 + w + 60, sill + 34, "window"), R_(x0 - 30, sill + 34, x0 + w + 30, y0 + h, "window"),
         R_(x0 + w / 2 - t / 4, y0 + header, x0 + w / 2 + t / 4, sill, "window"),
         R_(x0, y0 + header + (sill - y0 - header) * 0.42, x0 + w, y0 + header + (sill - y0 - header) * 0.42 + t / 2, "window")]
    return s, sill


def clock(cx, cy, r, hh=4, mm=10, pend=True, swing=0.0):
    s = [Shape(circle_pts(cx, cy, r, 40), "clock"), Shape(circle_pts(cx, cy, r * 0.80, 40), "dial", hole=True, z=1)]
    for k in range(12):
        a = math.radians(k * 30)
        p0 = (cx + r * 0.66 * math.sin(a), cy - r * 0.66 * math.cos(a))
        p1 = (cx + r * 0.78 * math.sin(a), cy - r * 0.78 * math.cos(a))
        s.append(Shape(bar_pts(p0, p1, r * (0.07 if k % 3 == 0 else 0.04)), "clock", smooth=False, z=2))
    am = math.radians(mm * 6)
    ah = math.radians((hh % 12) * 30 + mm * 0.5)
    s.append(Shape(bar_pts((cx - 0.12 * r * math.sin(ah), cy + 0.12 * r * math.cos(ah)),
                           (cx + r * 0.42 * math.sin(ah), cy - r * 0.42 * math.cos(ah)), r * 0.075), "hand", smooth=False, z=3))
    s.append(Shape(bar_pts((cx - 0.14 * r * math.sin(am), cy + 0.14 * r * math.cos(am)),
                           (cx + r * 0.66 * math.sin(am), cy - r * 0.66 * math.cos(am)), r * 0.045), "hand", smooth=False, z=3))
    s.append(Shape(circle_pts(cx, cy, r * 0.07, 10), "hand", z=4))
    if pend:
        bx0, by0, bx1, by1 = cx - r * 0.55, cy + r * 0.85, cx + r * 0.55, cy + r * 2.25
        s.append(Shape([(bx0, by0), (bx1, by0), (bx1, by1 - r * .2), (cx, by1 + r * .1), (bx0, by1 - r * .2)], "clock", smooth=False))
        s.append(R_(cx - r * 0.34, by0 + r * 0.25, cx + r * 0.34, by1 - r * 0.35, "pendwin", hole=True, z=1))
        a = math.radians(swing)
        bob = (cx + r * 1.0 * math.sin(a), by0 + r * 0.1 + r * 1.0 * math.cos(a))
        s.append(Shape(bar_pts((cx, by0 + r * 0.1), bob, r * 0.05), "clock", smooth=False, z=2))
        s.append(Shape(circle_pts(bob[0], bob[1], r * 0.17, 16), "clock", z=2))
    return s


def cupboard(x0, y0, w, h, open_deg=0.0):
    """Cupboard on its own; door hinged on the LEFT jamb, swinging toward the viewer. Returns shapes and
    the interior box (lit opening) for the page to hang the key in."""
    s = [R_(x0 - 16, y0 - 30, x0 + w + 16, y0, "cupboard"), R_(x0, y0, x0 + w, y0 + h, "cupboard")]
    ix0, iy0, ix1, iy1 = x0 + 22, y0 + 22, x0 + w - 22, y0 + h - 22
    th = math.radians(open_deg)
    if open_deg <= 0.5:
        for (a, b, c, d) in ((0.16, 0.08, 0.84, 0.46), (0.16, 0.54, 0.84, 0.92)):
            px0, py0, px1, py1 = x0 + w * a, y0 + h * b, x0 + w * c, y0 + h * d
            for e in (rect(px0, py0, px1, py0 + 5), rect(px0, py1 - 5, px1, py1),
                      rect(px0, py0, px0 + 5, py1), rect(px1 - 5, py0, px1, py1)):
                s.append(Shape(e, "slit", hole=True, smooth=False, z=1))
        s.append(Shape(circle_pts(x0 + w * 0.9, y0 + h * 0.5, 8, 10), "slit", hole=True, z=1))
        return s, None
    s.append(R_(ix0, iy0, ix1, iy1, "inside", hole=True, z=1))
    for fy in (0.30, 0.66):
        s.append(R_(ix0, y0 + h * fy, ix1, y0 + h * fy + 14, "shelf", z=2))
    # the door leaf, projected: free edge at x0 + w cos(th), nearer edge taller
    ex = x0 + w * math.cos(th)
    dy = h * 0.07 * math.sin(th)
    leaf = [(x0, y0), (ex, y0 - dy), (ex, y0 + h + dy), (x0, y0 + h)]
    s.append(Shape(leaf, "door", smooth=False, z=3))
    return s, (ix0, iy0, ix1, iy1)


def service_door(x0, y0, w, h):
    s = [R_(x0 - 18, y0 - 20, x0 + w + 18, y0 + h, "sdoor")]
    for (a, b, c, d) in ((0.18, 0.30, 0.82, 0.55), (0.18, 0.62, 0.82, 0.92)):
        px0, py0, px1, py1 = x0 + w * a, y0 + h * b, x0 + w * c, y0 + h * d
        for e in (rect(px0, py0, px1, py0 + 5), rect(px0, py1 - 5, px1, py1),
                  rect(px0, py0, px0 + 5, py1), rect(px1 - 5, py0, px1, py1)):
            s.append(Shape(e, "slit", hole=True, smooth=False, z=1))
    s.append(Shape(circle_pts(x0 + w * 0.86, y0 + h * 0.56, 9, 10), "slit", hole=True, z=1))
    return s


# ------------------------------------------------------------------ panel furniture shared by 05-08
CAPTION_PAPER = np.array([238, 231, 212], np.float32)


def slip(canvas, x0, y0, lines, cap, seed, paper=CAPTION_PAPER, pad=(22, 16), align="left", min_w=0,
         tilt=0.0, shadow=0.38, ink=INK, weight=0.13):
    """A pasted paper slip with pen lettering; returns its box. Lettering left-aligned (or centred)."""
    m = letter_left(lines, cap, seed, weight) if align == "left" else letter(lines, cap, seed, weight)
    h, w = m.shape
    bw, bh = max(min_w, w + 2 * pad[0] - int(cap * 1.0)), h + 2 * pad[1] - int(cap * 0.3)
    rnd = random.Random(seed)
    poly = np.array([(x0 + rnd.uniform(-3, 3), y0 + rnd.uniform(-3, 3)), (x0 + bw + rnd.uniform(-3, 3), y0 + rnd.uniform(-3, 3)),
                     (x0 + bw + rnd.uniform(-3, 3), y0 + bh + rnd.uniform(-3, 3)), (x0 + rnd.uniform(-3, 3), y0 + bh + rnd.uniform(-3, 3))])
    if tilt:
        c = poly.mean(0)
        a = math.radians(tilt)
        poly = (poly - c) @ np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]]) + c
    pm = np.zeros(canvas.shape[:2], np.uint8)
    cv2.fillPoly(pm, [np.int32(poly * 4)], 255, cv2.LINE_AA, shift=2)
    penlib.shadow_onto(canvas, pm, off=5, blur=4, opacity=shadow)
    comp(canvas, pm, paper)
    lm = np.zeros(canvas.shape[:2], np.uint8)
    ox = x0 + pad[0] - int(cap * 0.5) if align == "left" else int(x0 + bw / 2 - w / 2)
    lm = blit_mask(lm, m, int(ox), int(y0 + pad[1] - cap * 0.15))
    if tilt:
        c = poly.mean(0)
        M = cv2.getRotationMatrix2D((float(c[0]), float(c[1])), -tilt, 1.0)
        lm = cv2.warpAffine(lm, M, (lm.shape[1], lm.shape[0]))
    comp(canvas, lm, ink)
    return (x0, y0, x0 + bw, y0 + bh)


def balloon(canvas, lines, cap, at, tail_tip_abs, seed, tail_w=0.30, bend=0.10):
    """Pen-hand cut-paper balloon (penlib.balloon_piece) centred at `at`, tail to an absolute point."""
    tip = (tail_tip_abs[0] - at[0], tail_tip_abs[1] - at[1])
    b = penlib.balloon_piece([pen99.clean(l) for l in lines], cap, tip, seed, tail_w=tail_w, bend=bend)
    penlib.lay_balloon(canvas, b, at)
    return b


def frame_border(canvas, boxes, w=10, seed=905):
    m = penlib.border_mask(canvas.shape[:2], [tuple(int(v) for v in b) for b in boxes], w=w, seed=seed)
    comp(canvas, m, INK)
    return canvas
