"""Page 14 Double take (genre; medium: brush-plate).

Vaudeville timing on ONE repeated brush plate: the office plate inked for page 07 (dab-chain brush after the
moins-dun-quart-de-seconde plate method, build/brushkit.py) is printed again in every panel, cropped and
scaled like a camera on a stage set. Brushed figures from the b1m2 model are laid on it.
The gag beats: a glance up at the clock, a look away to the window, then the head snaps back to the clock
(the double take) before the answer; the cupboard leaf swings out and stops a whisker from his nose (the near
miss, no fall); a held beat on the key; and the punchline is the forgetting.
Lettering: the shared pen hand (penlib/pen99). Folio by pen99.folio.
"""
import math
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/user/bolas/paeleo/scion/oulipo/films/swarm/99-ways/build")
from b1m2 import *  # noqa
from brushkit import brush, shape
import p07_two_panels as P7P

N, PID, TITLE = 14, "double-take", "Double take"
PW, PH, SS = P7P.PW, P7P.PH, P7P.SS
WIN, SILL, HEADER, DESK, CLOCK, CUP, SDOOR, FLOOR = (P7P.WIN, P7P.SILL, P7P.HEADER, P7P.DESK, P7P.CLOCK, P7P.CUP,
                                                    P7P.SDOOR, P7P.FLOOR)
SHEET = pen99.sheet99()
PAPER = np.array([250, 248, 242], np.float32)
BCAP = 46

# page layout: 4 rows
GAP = 40
ROWS = [(110, 670), (710, 1310), (1350, 1990), (2030, 2730)]
BOXES = {
    "P1": (110, ROWS[0][0], 1010, ROWS[0][1]), "P2": (1050, ROWS[0][0], 2090, ROWS[0][1]),
    "P3": (110, ROWS[1][0], 743, ROWS[1][1]), "P4": (783, ROWS[1][0], 1417, ROWS[1][1]),
    "P5": (1457, ROWS[1][0], 2090, ROWS[1][1]),
    "P6": (110, ROWS[2][0], 950, ROWS[2][1]), "P7": (990, ROWS[2][0], 2090, ROWS[2][1]),
    "P8": (110, ROWS[3][0], 750, ROWS[3][1]), "P9": (790, ROWS[3][0], 2090, ROWS[3][1]),
}


# ------------------------------------------------------------------ plate-space helpers
def stage():
    """A fresh print of the one plate on the 1934 sheet, at plate size."""
    c = SHEET[:PH, :PW].copy()
    P7P.lay_plate(c)
    return c


def relay_desk(c):
    """Re-print the desk part of the plate over a seated figure (the desk stands in front of him)."""
    dx0, dy0, dx1, dy1 = DESK
    x0, y0, x1, y1 = dx0 - 20, dy0 - 2, dx1 + 20, dy1
    c[y0:y1, x0:x1] = SHEET[y0:y1, x0:x1]
    ink = (P7P.plate()[y0:y1, x0:x1] * 255).astype(np.uint8)
    sub = c[y0:y1, x0:x1]
    comp(sub, ink, INK)


def head_ids(shapes):
    return [i for i, s in enumerate(shapes) if (s.role == "skin" and s.z == 0) or s.role in ("hair", "ear", "glass", "glass_in", "glass_arm")]


def turned(body_kw, head_face, head_tilt):
    """Agent whose body faces one way and whose head is turned the other (or the same) way, pinned at the neck."""
    body = agent(**body_kw)
    hk = dict(body_kw)
    hk["face"] = head_face
    hk["tilt"] = head_tilt
    hshapes = agent(**hk)
    bi, hi = head_ids(body), head_ids(hshapes)
    nb = body[bi[0]].pts
    nh = hshapes[hi[0]].pts
    neck_b = (nb[0] + nb[-1]) / 2
    neck_h = (nh[0] + nh[-1]) / 2
    d = neck_b - neck_h
    out = [s for i, s in enumerate(body) if i not in bi]
    for i in hi:
        s = hshapes[i]
        out.append(Shape(s.pts + d, s.role, hole=s.hole, smooth=s.smooth, z=s.z))
    return out


def head_box(shapes):
    pts = np.vstack([s.pts for s in shapes if s.role == "skin" and s.z == 0])
    return pts.min(0), pts.max(0)


def mouth(shapes):
    head = [q for q in shapes if q.role == "skin" and q.z == 0][0].pts
    return head[15]


def whip_lines(c, centre, r, a0, a1, seed, n=3):
    """Brushed speed arcs around a snapping head."""
    rng = np.random.default_rng(seed)
    im = Image.new("L", (PW * SS, PH * SS), 0)
    d = ImageDraw.Draw(im)
    for k in range(n):
        rr = r + k * 26
        pts = [(centre[0] + rr * math.cos(math.radians(a)), centre[1] + rr * math.sin(math.radians(a)))
               for a in np.linspace(a0 + k * 6, a1 - k * 6, 24)]
        brush(d, [(x * SS, y * SS) for x, y in pts], 9 * SS, rng, col=255, taper=(0.5, 0.15), press=0.4)
    m = np.asarray(im.resize((PW, PH), Image.LANCZOS))
    comp(c, m, INK)


def swoosh(c, pivot, r0, r1, a0, a1, seed):
    """Brushed arc lines tracing the path of the swinging cupboard leaf."""
    rng = np.random.default_rng(seed)
    im = Image.new("L", (PW * SS, PH * SS), 0)
    d = ImageDraw.Draw(im)
    for k, rr in enumerate(np.linspace(r0, r1, 3)):
        pts = [(pivot[0] + rr * math.cos(math.radians(a)), pivot[1] + rr * 0.35 * math.sin(math.radians(a)))
               for a in np.linspace(a0, a1, 30)]
        brush(d, [(x * SS, y * SS) for x, y in pts], 7 * SS, rng, col=255, taper=(0.6, 0.1), press=0.4)
    comp(c, np.asarray(im.resize((PW, PH), Image.LANCZOS)), INK)


def open_cupboard(c, leaf_x, key=True, seed=1401):
    """Pasted paper overlay on the plate: the cupboard opened, lit inside, the key on its hook; the leaf swung
    out on the left jamb with its free edge at plate x = CUP[0] - leaf_x."""
    c0, c1, c2, c3 = CUP
    rng = np.random.default_rng(seed)
    im = Image.new("L", (PW * SS, PH * SS), 128)
    d = ImageDraw.Draw(im)
    d.rectangle([(c0 + 20) * SS, (c1 + 20) * SS, (c2 - 20) * SS, (c3 - 20) * SS], fill=255)
    for fy in (0.50, 0.78):
        y = c1 + (c3 - c1) * fy
        shape(d, P7P.S(P7P.rectp(c0 + 20, y, c2 - 20, y + 16, 3)), 5 * SS, rng, fill=0, amp=0.3, press=P7P.PRESS, taper=P7P.TAPER)
    brush(d, P7P.S([(c0 + 20, c1 + 24), (c0 + 30, c3 - 24)]), 7 * SS, rng, col=0, press=P7P.PRESS)
    dy = 44 * leaf_x / 112
    leaf = [(c0, c1 - 6), (c0 - leaf_x, c1 - dy), (c0 - leaf_x, c3 + dy), (c0, c3)]
    dens = []
    for a, b in zip(leaf, leaf[1:] + leaf[:1]):
        for t in np.linspace(0, 1, 8, endpoint=False):
            dens.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    shape(d, P7P.S(dens), P7P.LW * SS, rng, fill=255, amp=0.4, press=P7P.PRESS, taper=P7P.TAPER)
    ins = leaf_x * 0.82
    for (a, b) in ((0.14, 0.46), (0.54, 0.88)):
        y0_, y1_ = c1 + (c3 - c1) * a, c1 + (c3 - c1) * b
        q = [(c0 - leaf_x * 0.16, y0_ - dy * 0.2), (c0 - ins, y0_ - dy * 0.7), (c0 - ins, y1_ + dy * 0.5), (c0 - leaf_x * 0.16, y1_ + dy * 0.14)]
        dq = []
        for a_, b_ in zip(q, q[1:] + q[:1]):
            for t in np.linspace(0, 1, 6, endpoint=False):
                dq.append((a_[0] + (b_[0] - a_[0]) * t, a_[1] + (b_[1] - a_[1]) * t))
        shape(d, P7P.S(dq), 5 * SS, rng, fill=255, amp=0.3, press=P7P.PRESS, taper=P7P.TAPER)
    a = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32)
    comp(c, (np.clip((a - 128) / 127, 0, 1) * 255).astype(np.uint8), PAPER)
    comp(c, (np.clip((128 - a) / 128, 0, 1) * 255).astype(np.uint8), INK)
    if key:
        km = np.zeros((PH, PW), np.uint8)
        kx, ky = c2 - 52, 600
        paste_mask(km, key_alpha(), kx, ky, 0.27)
        hk = np.zeros((PH, PW), np.uint8)
        penlib.brush_line(hk, [(kx - 24, ky - 104), (kx + 4, ky - 104), (kx + 4, ky - 88)], 8, seed + 2)
        comp(c, np.maximum(km, hk), INK)
        slip(c, int(kx + 12), int(ky + 30), ["SERVICE"], 26, seed + 3, paper=np.array([250, 248, 240], np.float32),
             pad=(12, 4), tilt=10, shadow=0.0)
    return leaf


def behind_glass(c, shapes, seed):
    """The stranger seen THROUGH the ticket window, from the platform side: a pale brushed platform wash fills the
    opening behind her; her figure is clipped to the opening (cut off at the sill); then the plate's own window
    frame and mullions are re-laid over her and brushed glass glints cross her silhouette."""
    x0, y0, x1, y1 = WIN
    ox0, oy0, ox1, oy1 = x0, HEADER, x1, SILL
    rng = np.random.default_rng(seed)
    # 1. the platform outside: paler than the office paper is warm, a cool grey wash with the platform edge,
    #    a canopy post and the far eave brushed in light grey
    im = Image.new("L", (PW * SS, PH * SS), 0)
    d = ImageDraw.Draw(im)
    d.rectangle([ox0 * SS, oy0 * SS, ox1 * SS, oy1 * SS], fill=255)
    wash = np.asarray(im.resize((PW, PH), Image.LANCZOS))
    comp(c, wash, np.array([222, 224, 226], np.float32))
    im = Image.new("L", (PW * SS, PH * SS), 0)
    d = ImageDraw.Draw(im)
    py = oy0 + (oy1 - oy0) * 0.80
    d.rectangle([ox0 * SS, py * SS, ox1 * SS, oy1 * SS], fill=150)
    brush(d, [(ox0 * SS, py * SS), (ox1 * SS, (py - 4) * SS)], 6 * SS, rng, col=255, taper=(0.05, 0.05), press=0.4)
    brush(d, [(ox0 * SS, (oy0 + 26) * SS), (ox1 * SS, (oy0 + 40) * SS)], 10 * SS, rng, col=200, taper=(0.05, 0.05), press=0.4)
    px = ox0 + (ox1 - ox0) * 0.12
    brush(d, [(px * SS, (oy0 + 30) * SS), ((px + 2) * SS, py * SS)], 12 * SS, rng, col=200, taper=(0.05, 0.05), press=0.4)
    out = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32) / 255
    comp(c, (out * 255 * 0.32).astype(np.uint8), INK)
    # 2. her figure, clipped to the opening
    tmp = c.copy()
    P7P.lay_figs(tmp, shapes, seed + 1)
    c[oy0:oy1, ox0:ox1] = tmp[oy0:oy1, ox0:ox1]
    # 3. the plate's window frame and mullions re-laid in front of her
    ink = (P7P.plate() * 255).astype(np.uint8)
    keep = np.zeros_like(ink)
    keep[oy0 - 4:oy1 + 36, ox0 - 30:ox1 + 30] = ink[oy0 - 4:oy1 + 36, ox0 - 30:ox1 + 30]
    comp(c, keep, INK)
    # 4. glass glints: short parallel diagonal white strokes across each pane, bright where they cross her dark
    #    coat or hat, faint on the pale wash
    im = Image.new("L", (PW * SS, PH * SS), 0)
    d = ImageDraw.Draw(im)
    mid_x, mid_y = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    for (gx, gy) in ((ox0 + 34, oy0 + 120), (mid_x + 40, oy0 + 90), (mid_x + 70, mid_y + 100), (ox0 + 60, mid_y + 70)):
        for k, ln in enumerate((70, 46)):
            q = gx + k * 22
            brush(d, [(q * SS, (gy + ln / 2) * SS), ((q + ln * 0.8) * SS, (gy - ln / 2) * SS)], 6 * SS, rng, col=255,
                  taper=(0.35, 0.35), press=0.4)
    g = np.asarray(im.resize((PW, PH), Image.LANCZOS)).astype(np.float32) / 255
    lum = c.mean(2)
    dark = (lum < 120).astype(np.float32)
    comp(c, (g * dark * 255).astype(np.uint8), np.array([238, 240, 242], np.float32), 0.9)
    comp(c, (g * (1 - dark) * 255).astype(np.uint8), np.array([252, 252, 252], np.float32), 0.95)


def crop(c, x0, x1, top, out_wh):
    """Camera: the plate-space strip x0..x1 from `top` down, scaled to the panel (height from the panel aspect)."""
    W, H = out_wh
    h = (x1 - x0) * H / W
    y0 = max(0, min(top, PH - h))
    sub = c[int(round(y0)):int(round(y0 + h)), int(round(x0)):int(round(x1))]
    s = W / sub.shape[1]
    out = cv2.resize(sub, (W, H), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    to = lambda p: ((p[0] - x0) * s, (p[1] - y0) * s)
    return out.astype(np.float32), to


def bballoon(canvas, lines, cap, at, tip, seed, ctrl=None):
    """White balloon with a brushed contour (as page 07), at page scale on the panel canvas."""
    Hc, Wc = canvas.shape[:2]
    rng = np.random.default_rng(seed)
    lm = letter(lines, cap, seed + 1)
    h, w = lm.shape
    rx, ry = w * 0.5 * 1.16 + cap * 0.35, h * 0.5 * 1.08 + cap * 0.3
    cx, cy = at
    aim = tip if ctrl is None else ctrl
    a0 = math.atan2((aim[1] - cy) / ry, (aim[0] - cx) / rx)
    b1 = np.array((cx + rx * .85 * math.cos(a0 - 0.2), cy + ry * .85 * math.sin(a0 - 0.2)))
    b2 = np.array((cx + rx * .85 * math.cos(a0 + 0.2), cy + ry * .85 * math.sin(a0 + 0.2)))
    mid = (b1 + b2) / 2
    tp = np.array(tip, float)
    if ctrl is None:
        bend = np.array([-(tp[1] - mid[1]), tp[0] - mid[0]]) * 0.08
        c1_, c2_ = mid + bend, mid + bend * .5
    else:
        cp = np.array(ctrl, float)
        nrm = np.array([-(tp[1] - cp[1]), tp[0] - cp[0]])
        nrm = nrm / (np.linalg.norm(nrm) + 1e-9) * cap * 0.22
        c1_, c2_ = cp + nrm, cp - nrm
    tail = [b1 * (1 - t) ** 2 + 2 * (1 - t) * t * c1_ + tp * t * t for t in np.linspace(0, 1, 40)]
    tail += [tp * (1 - t) ** 2 + 2 * (1 - t) * t * c2_ + b2 * t * t for t in np.linspace(0, 1, 40)]
    m = np.zeros((Hc * SS, Wc * SS), np.uint8)
    cv2.ellipse(m, (int(cx * SS), int(cy * SS)), (int(rx * SS), int(ry * SS)), 0, 0, 360, 255, -1)
    cv2.fillPoly(m, [np.int32(np.array(tail + [mid]) * SS)], 255)
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cpts = max(cs, key=len)[:, 0, :].astype(float)[::3]
    im = Image.new("L", (Wc * SS, Hc * SS), 128)
    d = ImageDraw.Draw(im)
    shape(d, [tuple(p) for p in cpts], 7 * SS, rng, fill=255, amp=0.3 * SS, press=0.45, taper=P7P.TAPER)
    a = np.asarray(im.resize((Wc, Hc), Image.LANCZOS)).astype(np.float32)
    comp(canvas, (np.clip((a - 128) / 127, 0, 1) * 255).astype(np.uint8), np.array([252, 250, 244], np.float32))
    comp(canvas, (np.clip((128 - a) / 128, 0, 1) * 255).astype(np.uint8), INK)
    mm = np.zeros((Hc, Wc), np.uint8)
    put_mask(mm, lm, cx, cy + cap * 0.02)
    comp(canvas, mm, INK)


def tag(canvas, text, x, y, seed, cap=34):
    """A small pasted caption slip (timing marks of the act)."""
    return slip(canvas, int(x), int(y), [text], cap, seed, paper=np.array([246, 240, 222], np.float32), pad=(16, 8), shadow=0.25)


def size(k):
    x0, y0, x1, y1 = BOXES[k]
    return x1 - x0, y1 - y0


# ------------------------------------------------------------------ panels
def P1(st):
    c = stage()
    a = agent(640, FLOOR + 60, face=1, scale=0.74, seated=True, lean=8, tilt=18, sh=34, el=74, wr=-10, pencil_deg=60, far_arm=(30, 60))
    P7P.lay_figs(c, a, 1411)
    relay_desk(c)
    P7P.memo(c)
    out, to = crop(c, 330, 1010, 480, size("P1"))
    return out


def P2(st):
    c = stage()
    x0, y0, x1, y1 = WIN
    behind_glass(c, stranger((x0 + x1) / 2 + 40, SILL + 40, face=1, scale=1.25, glove=True), 1421)
    a = agent(900, FLOOR + 12, face=1, scale=0.80, legs=(20, -18), sh=-20, el=22, lean=3, pencil_deg=200, far_arm=(20, 20))
    a = turned(dict(x=900, floor=FLOOR + 12, face=1, scale=0.80, legs=(20, -18), sh=-20, el=22, lean=3, pencil_deg=200,
                    far_arm=(20, 20)), -1, 0)
    P7P.lay_figs(c, a, 1422)
    out, to = crop(c, 0, 1240, 230, size("P2"))
    bballoon(out, ["Pardon me —", "have you the", "right time?"], BCAP, (520, 120), to((250, 470)), 1423)
    return out


CLOCK_CAM = (150, 820, 300)
BODY = dict(x=420, floor=FLOOR + 20, face=-1, scale=0.80, legs=(4, -4), sh=6, el=14, pencil_deg=190)


def P3(st):
    """The glance: body to the window, head turned up to the clock, unhurried."""
    c = stage()
    a = turned(BODY, 1, -20)
    P7P.lay_figs(c, a, 1431)
    out, to = crop(c, *CLOCK_CAM, size("P3"))
    tag(out, "a glance...", 24, 22, 1432)
    return out


def P4(st):
    """Away: back to the window, as if nothing."""
    c = stage()
    a = agent(**dict(BODY, tilt=2))
    P7P.lay_figs(c, a, 1441)
    out, to = crop(c, *CLOCK_CAM, size("P4"))
    tag(out, "away...", 24, 22, 1442)
    return out


def P5(st):
    """The take: the head snaps back to the clock, brushed whip lines; then the answer."""
    c = stage()
    a = turned(BODY, 1, -30) if st.get("snap", True) else agent(**dict(BODY, tilt=2))
    P7P.lay_figs(c, a, 1451)
    (hx0, hy0), (hx1, hy1) = head_box(a)
    if st.get("whip", True) and st.get("snap", True):
        whip_lines(c, ((hx0 + hx1) / 2 - 10, (hy0 + hy1) / 2), 92, 150, 250, 1452)
    out, to = crop(c, *CLOCK_CAM, size("P5"))
    tag(out, "and back!", 24, 22, 1453)
    if st.get("line", True):
        bballoon(out, ["Ten past four,", "by the clock."], BCAP, (400, 470), to(mouth(a) + np.array([10, 6])), 1454)
    return out


def P6(st):
    c = stage()
    x0, y0, x1, y1 = WIN
    behind_glass(c, stranger((x0 + x1) / 2 - 50, SILL + 40, face=-1, scale=1.25, tilt=-6), 1461)
    a = agent(760, FLOOR + 12, face=1, scale=0.80, legs=(18, -16), sh=-18, el=20, lean=3, pencil_deg=200, far_arm=(18, 18))
    P7P.lay_figs(c, a, 1462)
    out, to = crop(c, 0, 1020, 230, size("P6"))
    bballoon(out, ["Much", "obliged!"], BCAP, (560, 110), to((338, 452)), 1463)
    return out


def P7(st):
    """The near miss: he pulls, the leaf swings out on its left jamb and stops a whisker short of his nose."""
    c = stage()
    lx = st.get("leaf", 250)
    if lx > 0:
        open_cupboard(c, lx, key=True, seed=1471)
    c0 = CUP[0]
    edge_x = c0 - lx
    lean = st.get("lean", -20)
    kw = dict(face=1, scale=0.80, legs=(14, -10), lean=lean, tilt=-10, sh=60, el=-30, wr=0, pencil_deg=230)
    a = agent(0, FLOOR + 12, **kw)
    (hx0, hy0), (hx1, hy1) = head_box(a)
    nose = [q for q in a if q.role == "skin" and q.z == 0][0].pts[11]
    gap = st.get("gap", 34)
    dx = (edge_x - gap) - nose[0]
    a = [Shape(s.pts + np.array([dx, 0]), s.role, hole=s.hole, smooth=s.smooth, z=s.z) for s in a]
    P7P.lay_figs(c, a, 1472)
    if lx >= 200 and st.get("swoosh", True):
        swoosh(c, (c0, 420), lx * 0.55, lx * 0.95, 200, 130, 1473)
    out, to = crop(c, CUP[0] - 250 - 520, CUP[2] + 240, 300, size("P7"))
    if lx >= 200:
        tag(out, "whoosh... missed!", 24, 22, 1474)
    return out


def P8(st):
    """A held beat: the key, in plain view."""
    c = stage()
    open_cupboard(c, 112, key=True, seed=1481)
    out, to = crop(c, CUP[2] - 190, CUP[2] + 110, 380, size("P8"))
    tag(out, "beat.", 24, 22, 1482)
    return out


def P9(st):
    c = stage()
    leaf = open_cupboard(c, 112, key=True, seed=1491)
    a = agent(1262, FLOOR + 12, face=1, scale=0.86, legs=(4, -4), sh=5, el=140, wr=40, pencil_deg=175, tilt=6)
    P7P.lay_figs(c, a, 1492)
    out, to = crop(c, 420, 1980, 270, size("P9"))
    if st.get("line", True):
        m = mouth(a)
        bballoon(out, ["Well,", "here I am...", "and what for?"], 50, (300, 170), to((m[0] + 14, m[1] + 8)), 1493,
                 ctrl=to((1100, 300)))
    return out


PANELS = [("P1", P1), ("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5), ("P6", P6), ("P7", P7), ("P8", P8), ("P9", P9)]


def build(state=None):
    state = state or {}
    page = SHEET.copy()
    for k, fn in PANELS:
        x0, y0, x1, y1 = BOXES[k]
        page[y0:y1, x0:x1] = fn(state.get(k, {}))
    frame_border(page, list(BOXES.values()), w=12, seed=1499)
    return page


def finish(p):
    p = np.clip(np.round(p), 0, 255).astype(np.uint8)
    pen99.folio(p, N, TITLE)
    return p


if __name__ == "__main__":
    P7P.PLATE_LAID.clear()
    page = build()
    print("plate prints", len(P7P.PLATE_LAID), "distinct", len(set(P7P.PLATE_LAID)), P7P.PLATE_LAID[0][:16])
    img, sz = save_page(page, N, PID, TITLE)
    print("jpeg bytes", sz)
    if len(sys.argv) > 1 and sys.argv[1] == "beats":
        # the double take, then the near miss: row 2 and 3 states
        states = [
            {"P4": {}, "P5": {"snap": False, "line": False}, "P7": {"leaf": 0}, "P9": {"line": False}},
            {"P5": {"whip": True, "line": False}, "P7": {"leaf": 0}, "P9": {"line": False}},
            {"P7": {"leaf": 0}, "P9": {"line": False}},
            {"P7": {"leaf": 120, "lean": -4, "gap": 140}, "P9": {"line": False}},
            {"P7": {"leaf": 250}, "P9": {"line": False}},
            {},
        ]
        save_beats(N, [np.asarray(Image.fromarray(finish(build(s))).resize((960, 1242), Image.LANCZOS)) for s in states])
