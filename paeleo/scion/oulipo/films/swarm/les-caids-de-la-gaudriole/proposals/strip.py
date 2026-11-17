"""The shared printable strip for the three proposals.

Ink: Wilhelm Busch, Max und Moritz (1865) plates from Wikimedia Commons (PD), cut
out and re-posed as puppets (the miller's arm is cut at the shoulder and
re-hinged); balloons, lettering, floor line, the porter's sleeve and the key are
drawn here stroke by stroke with pen.py. Nothing is traced from the reference.

Sheet 2400 x 900 px. Panel 1 = x 40..1180, panel 2 = x 1220..2360, y 50..850.
Fold A (mountain) at x=620, fold M (valley) at x=1210 in the gutter, so the
sheet point B = 2M - A = 1800 lands on A. Folded panel = P1[40..A] + P2[B..2360].
"""
import math, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
from pen import pen, text_width

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "../../../sources/les-caids-de-la-gaudriole"))
SW, SH = 2400, 900
PY0, PY1 = 50, 850
P1, P2 = (40, 1180), (1220, 2360)
A, M = 620, 1210
B = 2 * M - A            # 1800
D = B - A                # 1180
INK = 18
LINE_Y = [112, 168, 224]  # cap tops of the three balloon lines
CAP = 36

P1_LINES = [("THE KEY?", "I SWEAR, NOT"), ("IN MY", "ENVELOPE!"), ("ALL", "I CARRY IS PAPER.")]
P2_LINES = [("HERE! SILLY ME -", "I HAD IT"), ("IN THE COAT", "POCKET"), ("ALL", "ALONG.")]


def busch(n):
    im = Image.open(os.path.join(SRC, "busch", f"mm_{n}.png")).convert("L")
    return im


def ink_of(img):
    """Busch scan -> ink darkness 0..255 (255 = full black)."""
    a = 255 - np.asarray(img, dtype=np.float32)
    a = np.clip((a - 25) * 1.25, 0, 255)
    return a.astype(np.uint8)


def wobble_line(d, pts, w=5, seed=0, ink=INK):
    rnd = random.Random(seed)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        n = max(2, int(math.hypot(bx - ax, by - ay) / 1.5))
        jit = 0
        for k in range(n + 1):
            t = k / n
            jit = 0.97 * jit + rnd.uniform(-0.12, 0.12)
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            nx, ny = -(by - ay), (bx - ax)
            L = math.hypot(nx, ny) or 1
            x += nx / L * jit
            y += ny / L * jit
            r = w / 2 * (0.85 + 0.3 * math.sin(math.pi * t))
            d.ellipse([x - r, y - r, x + r, y + r], fill=ink)


def rr_pts(x0, y0, x1, y1, r, steps=10):
    pts = []
    for cx, cy, a0 in [(x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]:
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


def balloon(d, x0, x1, y0, y1, tail, seed):
    """Balloon frame whose top and bottom run level through the fold lines."""
    d.rounded_rectangle([x0, y0, x1, y1], radius=60, fill=255)
    wobble_line(d, rr_pts(x0, y0, x1, y1, 60), w=5, seed=seed)
    (bx, tx, ty) = tail
    d.polygon([(bx - 22, y1 - 3), (bx + 22, y1 - 3), (tx, ty)], fill=255)
    wobble_line(d, [(bx - 22, y1), (tx, ty), (bx + 22, y1)], w=5, seed=seed + 1)


def small_balloon(d, cx, cy, lines, tail, seed, size=26):
    w = max(text_width(s, size) for s in lines) + 50
    h = len(lines) * size * 1.6 + 30
    x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
    d.ellipse([x0, y0, x1, y1], fill=255)
    pts = [(cx + w / 2 * math.cos(2 * math.pi * k / 60), cy + h / 2 * math.sin(2 * math.pi * k / 60)) for k in range(61)]
    tx, ty = tail
    d.polygon([(cx - 14, y1 - 8), (cx + 14, y1 - 8), (tx, ty)], fill=255)
    wobble_line(d, pts, w=4, seed=seed)
    wobble_line(d, [(cx - 14, y1 - 4), (tx, ty), (cx + 14, y1 - 4)], w=4, seed=seed + 2)
    for i, s in enumerate(lines):
        pen(d, s, cx, y0 + 18 + i * size * 1.6, size, ink=INK, seed=seed + 10 + i, anchor="m")


def paste_ink(canvas, ink, x, y):
    """Darken-composite an ink array (0..255) at (x,y) on an L canvas array (255=white)."""
    h, w = ink.shape
    H, W = canvas.shape
    xa, ya = max(0, x), max(0, y)
    xb, yb = min(W, x + w), min(H, y + h)
    if xa >= xb or ya >= yb:
        return
    sub = ink[ya - y:yb - y, xa - x:xb - x]
    canvas[ya:yb, xa:xb] = np.minimum(canvas[ya:yb, xa:xb], 255 - sub)


def white_out(canvas, poly):
    m = Image.new("L", (canvas.shape[1], canvas.shape[0]), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    canvas[np.asarray(m) > 0] = 255


# ---------------------------------------------------------------- puppets
MS = 1.3                       # miller scale
MILLER_BOX = (680, 60, 1114, 625)
ARM_POLY = [(1004, 322), (1064, 316), (1071, 396), (1097, 414), (1110, 452), (1106, 482), (1058, 488),
            (1016, 472), (1012, 436), (1019, 410), (1010, 370)]
SHOULDER = (1036, 326)
ARM_ROT = 52                   # degrees CCW: the hanging arm swings forward to reach the fold


def miller_parts():
    """Return (body_ink, arm_ink, arm_origin, cuff_xy_in_body_coords) all at scale MS, body box origin."""
    src = busch("082")
    x0, y0, x1, y1 = MILLER_BOX
    full = np.pad(ink_of(src.crop(MILLER_BOX)), ((0, 120), (0, 260)))
    # arm piece with occluding white inside its polygon
    poly = [((px - x0), (py - y0)) for px, py in ARM_POLY]
    m = Image.new("L", (full.shape[1], full.shape[0]), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    m = np.asarray(m.filter(ImageFilter.MaxFilter(3)))
    arm = np.where(m > 0, full, 0).astype(np.uint8)
    body = np.where(m > 0, 0, full).astype(np.uint8)
    # restore the coat edge where the arm was lifted away: a pen contour along the coat
    sx, sy = SHOULDER[0] - x0, SHOULDER[1] - y0
    # rotate arm about shoulder (with an occlusion matte)
    arm_im = Image.fromarray(arm)
    matte = Image.fromarray(m)
    arm_r = arm_im.rotate(ARM_ROT, resample=Image.BICUBIC, center=(sx, sy))
    matte_r = matte.rotate(ARM_ROT, resample=Image.BICUBIC, center=(sx, sy))
    # cuff centre after rotation (src cuff ~ (1044,402))
    cx, cy = 1044 - x0, 402 - y0
    a = math.radians(-ARM_ROT)
    rx = sx + (cx - sx) * math.cos(a) - (cy - sy) * math.sin(a)
    ry = sy + (cx - sx) * math.sin(a) + (cy - sy) * math.cos(a)
    sc = lambda im: im.resize((int(im.width * MS), int(im.height * MS)), Image.LANCZOS)
    return (np.asarray(sc(Image.fromarray(body))), np.asarray(sc(arm_r)), np.asarray(sc(matte_r)),
            (rx * MS, ry * MS))


def farmer(flip=False, s=1.2):
    src = busch("031").crop((160, 40, 560, 600))
    k = ink_of(src)
    # drop the stick: keep his figure only (stick runs up-right from the hands)
    im = Image.fromarray(k)
    d = ImageDraw.Draw(im)
    d.polygon([(286, 200), (440, 60), (470, 95), (345, 262), (315, 310), (275, 345), (250, 318), (283, 275)], fill=0)
    if flip:
        im = ImageOps.mirror(im)
    return np.asarray(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS))


def boys(s=0.62):
    src = busch("001")
    w, h = src.size
    k = ink_of(src.crop((int(w * 0.05), int(h * 0.12), int(w * 0.97), int(h * 0.88))))
    im = Image.fromarray(k)
    return np.asarray(im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS))


def draw_key(d, x, y, s=1.0, seed=5, sil=False):
    """A bit-key drawn with the pen, bow at (x,y), shaft hanging down."""
    r = 17 * s
    pts = [(x + r * math.cos(2 * math.pi * k / 40), y + r * math.sin(2 * math.pi * k / 40)) for k in range(41)]
    d.ellipse([x - r, y - r, x + r, y + r], fill=INK if sil else 255)
    wobble_line(d, pts, w=6 * s, seed=seed)
    if sil:
        d.ellipse([x - 7 * s, y - 7 * s, x + 7 * s, y + 7 * s], fill=255)
    r2 = 7 * s
    wobble_line(d, [(x + r2 * math.cos(2 * math.pi * k / 20), y + r2 * math.sin(2 * math.pi * k / 20)) for k in range(21)], w=4 * s, seed=seed + 1)
    L = 92 * s
    d.rectangle([x - 4 * s, y + r, x + 4 * s, y + r + L], fill=INK if sil else 255)
    if sil:
        d.rectangle([x + 4 * s, y + r + L - 30 * s, x + 24 * s, y + r + L - 16 * s], fill=INK)
        d.rectangle([x + 4 * s, y + r + L - 16 * s, x + 14 * s, y + r + L], fill=INK)
    wobble_line(d, [(x - 4 * s, y + r), (x - 4 * s, y + r + L)], w=4 * s, seed=seed + 2)
    wobble_line(d, [(x + 4 * s, y + r), (x + 4 * s, y + r + L - 30 * s)], w=4 * s, seed=seed + 3)
    wobble_line(d, [(x + 4 * s, y + r + L - 30 * s), (x + 24 * s, y + r + L - 30 * s), (x + 24 * s, y + r + L - 16 * s),
                    (x + 14 * s, y + r + L - 16 * s), (x + 14 * s, y + r + L), (x - 4 * s, y + r + L)], w=4 * s, seed=seed + 4)
    for k in range(4):
        yy = y + r + 8 * s + k * 12 * s
        wobble_line(d, [(x - 1 * s, yy), (x + 2 * s, yy + 4 * s)], w=2, seed=seed + 9 + k)


def silhouette(ink, close=9, clip=None, open_bottom=False):
    """Cut a solid card silhouette from a line drawing: close the outline, fill its holes.
    clip: list of (x0,y0,x1,y1) fractions of the piece to cut away with the scissors."""
    import cv2
    b = (ink > 90).astype(np.uint8)
    h, w = b.shape
    for (x0, y0, x1, y1) in (clip or []):
        b[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close))
    b = cv2.morphologyEx(b, cv2.MORPH_CLOSE, k)
    ff = np.pad(b, 1).copy() * 255
    mask = np.zeros((h + 4, w + 4), np.uint8)
    seeds = [(0, 0), (w + 1, 0)] if open_bottom else [(0, 0), (w + 1, 0), (0, h + 1), (w + 1, h + 1)]
    for sx, sy in seeds:
        if ff[sy, sx] == 0:
            cv2.floodFill(ff, mask, (sx, sy), 128)
    if not open_bottom:
        cv2.floodFill(ff, mask, (0, 0), 128)
    filled = (ff[1:-1, 1:-1] != 128).astype(np.uint8)
    # keep only large connected pieces (one card)
    n, lab, st, _ = cv2.connectedComponentsWithStats(filled)
    keep = np.zeros_like(filled)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > 0.02 * h * w or st[i, cv2.CC_STAT_AREA] > 4000:
            keep[lab == i] = 1
    keep = cv2.GaussianBlur(keep.astype(np.float32), (3, 3), 0)
    return (np.clip(keep, 0, 1) * 255).astype(np.uint8)


def build(sil=False):
    SI = silhouette if sil else (lambda a, **k: a)
    """Return dict: 'sheet' L image (open strip ink on white), geometry and fragment inventory."""
    cv = np.full((SH, SW), 255, np.uint8)
    _f = Image.fromarray(cv); _d = ImageDraw.Draw(_f)
    for (x0, x1), sd in [(P1, 3), (P2, 4)]:   # floor lines first, figures stand over them
        wobble_line(_d, [(x0 + 10, PY1 - 60), (x1 - 10, PY1 - 56)], w=3, seed=sd)
    cv = np.array(_f)
    body, arm, matte, cuff = miller_parts()
    # place miller so the rotated cuff sits exactly on fold A
    MX = int(round(A - cuff[0])) + 6
    MY = PY1 - 8 - int((MILLER_BOX[3] - MILLER_BOX[1]) * MS) + 30
    paste_ink(cv, SI(body, close=17, clip=[(0, 0, 0.07, 1)]) if sil else body, MX, MY)
    white_out_mask = np.zeros_like(cv, bool)
    hh, ww = matte.shape
    sub = cv[MY:MY + hh, MX:MX + ww]
    mm = matte[:sub.shape[0], :sub.shape[1]] > 128
    sub[mm] = 255
    paste_ink(cv, SI(arm), MX, MY)
    cuff_y = MY + cuff[1]
    # the hand that lies beyond A (in panel 1's hidden band) -> reuse as a cutout for panel 2
    hand_cut = cv[int(cuff_y - 70):int(cuff_y + 110), A:A + 150].copy()
    hand_ink = 255 - hand_cut
    hand_ink[:30] = 0

    # panel 1 band: the porter (flipped farmer) listening
    fl = farmer(flip=True, s=0.95)
    paste_ink(cv, SI(fl, clip=[(0.62, 0.5, 1, 1), (0.9, 0, 1, 1)]) if sil else fl, P1[1] - fl.shape[1] - 12, PY1 - fl.shape[0] - 6)
    # panel 2: the porter facing right, his sleeve reaching to B
    fr = farmer(flip=False, s=1.15)
    FX, FY = 1300, PY1 - fr.shape[0] - 6
    paste_ink(cv, SI(fr, clip=[(0, 0.5, 0.38, 1), (0, 0, 0.1, 1)]) if sil else fr, FX, FY)
    # the hand + key beyond B (same cut of the miller's hand, now with a key)
    paste_ink(cv, hand_ink, B, int(cuff_y - 70))

    cv[int(cuff_y - 95):int(cuff_y - 30), B - 90:B - 2] = 255
    img = Image.fromarray(cv)
    d = ImageDraw.Draw(img)
    # porter's forearm, pen-drawn from the end of his striped Busch sleeve to the cuff at B
    ex, ey = FX + (440 - 160) * 1.15, FY + (300 - 40) * 1.15
    cy0, cy1 = cuff_y - 24, cuff_y + 24
    top = [(ex - 4, ey - 30), (ex + (B - ex) * 0.55, cy0 + 8), (B - 2, cy0)]
    bot = [(B - 2, cy1), (ex + (B - ex) * 0.5, cy1 + 10), (ex + 6, ey + 30)]
    d.polygon(top + bot, fill=INK if sil else 255)
    wobble_line(d, top, w=6, seed=41)
    wobble_line(d, bot, w=6, seed=42)
    for k in range(0 if sil else 5):  # stripes across the sleeve, as on the farmer's own arm
        t = 0.12 + k * 0.16
        pa = (top[0][0] + (top[2][0] - top[0][0]) * t, top[0][1] + (top[2][1] - top[0][1]) * t + 5)
        pb = (bot[2][0] + (bot[0][0] - bot[2][0]) * t, bot[2][1] + (bot[0][1] - bot[2][1]) * t - 5)
        wobble_line(d, [pa, pb], w=4, seed=50 + k)
    wobble_line(d, [(B - 24, cy0 + 1), (B - 26, cy1 - 1)], w=4, seed=60)
    # the key, in the panel-2 hand (beyond B), drawn with the pen
    draw_key(d, B + 70, cuff_y + 58, 1.0, sil=sil)

    # boys in panel 2's right corner
    by = boys(0.4)
    paste_ink(np.asarray(img).copy(), by, 0, 0)  # (no-op guard)
    arr = np.array(img)
    paste_ink(arr, SI(by, close=7, open_bottom=True) if sil else by, P2[1] - by.shape[1] - 10, PY1 - by.shape[0] - 2)
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)


    # balloons + split lettering
    head1 = (MX + (1040 - MILLER_BOX[0]) * MS, MY + (200 - MILLER_BOX[1]) * MS)
    balloon(d, P1[0] + 40, P1[1] - 40, 80, 276, tail=(450, 505, 318), seed=11)
    balloon(d, P2[0] + 40, P2[1] - 40, 80, 276, tail=(1460, FX + 300, FY + 70), seed=12)
    frags = []
    for i, (l, r) in enumerate(P1_LINES):
        y = LINE_Y[i]
        frags.append(("P1", "miller", i, "L", pen(d, l, A - 10, y, CAP, seed=100 + i, anchor="r"), l))
        frags.append(("P1", "miller", i, "R", pen(d, r, A + 12, y, CAP, seed=110 + i, anchor="l"), r))
    for i, (l, r) in enumerate(P2_LINES):
        y = LINE_Y[i]
        frags.append(("P2", "porter", i, "L", pen(d, l, B - 10, y, CAP, seed=200 + i, anchor="r"), l))
        frags.append(("P2", "porter", i, "R", pen(d, r, B + 12, y, CAP, seed=210 + i, anchor="l"), r))
    small_balloon(d, 1040, 380, ["WHO TOOK", "IT, THEN?"], (990, 470), seed=300)
    small_balloon(d, 2215, 430, ["OH?", "REALLY?"], (2250, 575), seed=310)

    # panel borders (pen) + gutter
    for (x0, x1), s in [(P1, 21), (P2, 22)]:
        wobble_line(d, rr_pts(x0, PY0, x1, PY1, 4, 2), w=6, seed=s)
    arr = np.array(img)
    arr[:, :P1[0] - 3] = 255; arr[:, P2[1] + 4:] = 255
    arr[:PY0 - 3] = 255; arr[PY1 + 4:] = 255
    arr[:, P1[1] + 4:P2[0] - 3] = 255
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img)
    # fold marks in the margins (triangles + letters), as on a printed Oubapo strip
    for x, lab in [(A, "A"), (M, "M"), (B, "B")]:
        for yy, sgn in [(18, 1), (SH - 18, -1)]:
            d.polygon([(x - 10, yy - 10 * sgn), (x + 10, yy - 10 * sgn), (x, yy + 4 * sgn)], fill=INK)
        pen(d, lab, x + 16, 8, 18, seed=400 + x)
    return dict(sheet=img, frags=frags, cuff_y=cuff_y, A=A, M=M, B=B)


def folded(sheet):
    """Folded panel: P1[40..A] beside P2[B..2360] (only existing ink)."""
    w = (A - P1[0]) + (P2[1] - B)
    out = Image.new("L", (w + 80, SH), 255)
    out.paste(sheet.crop((0, 0, A, SH)), (0, 0))
    out.paste(sheet.crop((B, 0, P2[1] + 40, SH)), (A, 0))
    return out


if __name__ == "__main__":
    r = build()
    r["sheet"].save(os.path.join(HERE, "strip-open.png"))
    folded(r["sheet"]).save(os.path.join(HERE, "strip-folded.png"))
    for f in r["frags"]:
        print(f)
