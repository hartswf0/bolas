"""Keyframes for le-maki-mococo, proposal round (deterministic).

kf-1  Lecture Profile  foraged PD film (Logic By Machine, Part II): a man in profile, mouth open,
                       cut from his grey board onto the reference's white field; the poem's sound
                       is shown only as a trace (sound-first condition, no text yet).
kf-2  Paper Mouth      handmade articulated cut-paper mouth in extreme profile close-up (jaw on a pivot,
                       swap lips, teeth strip, cast paper shadow); the poem typesets itself letter by
                       letter in the white field (text condition).
kf-3  Gong to Animal   collage metamorphosis: a handmade cut-paper gong on a cord breaks into wedges and
                       the 1895 Brehm/Specht binturong engraving (cut out) is revealed hanging by its tail
                       from the same cord (image condition, the reconsideration).

Run: python3 kf.py
"""
import math
import os
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUL = os.path.abspath(os.path.join(HERE, "../../../.."))
SRC = os.path.join(OUL, "films/sources/le-maki-mococo/r1")
REF = os.path.join(OUL, "assets/references/maki.webp")
CLIP = "/home/user/hartswf0/cineosis-lab/lab/clips/6b7a3bcf-f109-5944-a0c6-43ba31fa5ff6.mp4"
W, H = 1280, 720
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_M = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
SERIF = "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf"
SERIF_I = "/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf"
WHITE = (250, 249, 247)

POEM = ["In the dark it hangs and swings,",
        "binturong, binturong,",
        "smells of popcorn, never rings —",
        "binturong, binturong."]


def font(p, s):
    return ImageFont.truetype(p, s)


def ffmpeg_frame(path, t):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(240, 320, 3).copy()


def ffmpeg_audio(path, t0, dur, sr=8000):
    out = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{dur:.3f}", "-i", path, "-vn",
                          "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768.0


def cue_strip(d, t, sound, text, image, x=48, y=40, ink=(60, 60, 60)):
    f = font(INTER_M, 17)
    d.text((x, y), t, font=f, fill=ink)
    xx = x + 64
    for name, on in (("sound", sound), ("text", text), ("image", image)):
        r = 6
        if on:
            d.ellipse((xx, y + 5, xx + 2 * r, y + 5 + 2 * r), fill=ink)
        else:
            d.ellipse((xx, y + 5, xx + 2 * r, y + 5 + 2 * r), outline=ink, width=2)
        d.text((xx + 18, y), name, font=font(INTER, 17), fill=ink)
        xx += 18 + d.textlength(name, font=font(INTER, 17)) + 26


def caption(d, who, t, words, x, y, maxw, ink=(40, 40, 40)):
    f1 = font(INTER_M, 16)
    f2 = font(INTER, 27)
    d.text((x, y), f"{who}  ·  {t}", font=f1, fill=(120, 120, 120))
    # wrap
    lines, cur = [], ""
    for wd in words.split(" "):
        nxt = (cur + " " + wd).strip()
        if d.textlength(nxt, font=f2) > maxw:
            lines.append(cur)
            cur = wd
        else:
            cur = nxt
    lines.append(cur)
    for i, ln in enumerate(lines):
        d.text((x, y + 26 + i * 36), ln, font=f2, fill=ink)


def catmull(pts, n=12, closed=True):
    P = np.array(pts, np.float64)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:
        P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def rough(poly, amp, seed):
    """scissor wobble: low-frequency normal jitter along the outline"""
    rng = np.random.default_rng(seed)
    n = len(poly)
    noise = rng.normal(0, 1, n)
    k = np.exp(-np.linspace(-2, 2, 9) ** 2)
    k /= k.sum()
    noise = np.convolve(np.concatenate([noise[-8:], noise, noise[:8]]), k, "same")[8:-8]
    d = np.roll(poly, -1, 0) - np.roll(poly, 1, 0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    return poly + nrm * noise[:, None] * amp


def paper(w, h, rgb, seed, fib=0.06, mottle=9):
    rng = np.random.default_rng(seed)
    base = np.ones((h, w, 3), np.float32) * np.array(rgb, np.float32)
    low = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 18)
    low /= (np.abs(low).max() + 1e-6)
    base += low[:, :, None] * mottle
    fine = cv2.GaussianBlur(rng.normal(0, 1, (h, w)).astype(np.float32), (0, 0), 0.7) * 3.0
    base += fine[:, :, None]
    # fibres
    fibre = np.zeros((h, w), np.float32)
    for _ in range(int(w * h * fib / 400)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(4, 14)
        cv2.line(fibre, (int(x), int(y)), (int(x + L * math.cos(a)), int(y + L * math.sin(a))),
                 float(rng.choice([-1, 1])), 1, cv2.LINE_AA)
    base += cv2.GaussianBlur(fibre, (0, 0), 0.5)[:, :, None] * 7
    return np.clip(base, 0, 255)


class Card:
    """a stack of cut-paper pieces laid on a white card under one soft light (top-left)"""

    def __init__(self, w=W, h=H, ground=WHITE, seed=0):
        self.img = paper(w, h, ground, seed, fib=0.03, mottle=3)
        self.w, self.h = w, h

    def lay(self, poly, rgb, seed, lift=7, rough_amp=1.3, shade=None):
        poly = rough(np.asarray(poly, np.float64), rough_amp, seed)
        m = np.zeros((self.h, self.w), np.uint8)
        cv2.fillPoly(m, [np.round(poly * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
        mf = m.astype(np.float32) / 255
        # cast shadow on what is below
        if lift:
            sh = shift(mf, int(lift * 0.6), int(lift))
            sh = cv2.GaussianBlur(sh, (0, 0), lift * 0.9)
            self.img *= (1 - 0.28 * sh)[:, :, None]
        tex = paper(self.w, self.h, rgb, seed + 101, fib=0.05, mottle=7)
        if shade is not None:  # shade: function (xx,yy)->multiplier
            yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
            tex *= shade(xx, yy)[:, :, None]
        # bright cut edge (paper thickness catching light)
        edge = cv2.morphologyEx(m, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32) / 255
        edge = np.roll(np.roll(edge, -1, 0), -1, 1) * mf
        tex = tex + edge[:, :, None] * 18
        self.img = self.img * (1 - mf[:, :, None]) + tex * mf[:, :, None]
        return m

    def pil(self):
        return Image.fromarray(np.clip(self.img, 0, 255).astype(np.uint8))


def shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape[:2]
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = a[max(-dy, 0):h - max(dy, 0), max(-dx, 0):w - max(dx, 0)]
    return out


def rot(pts, c, ang):
    c = np.array(c, np.float64)
    a = math.radians(ang)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    return (np.asarray(pts, np.float64) - c) @ R.T + c


# ================================================================ KF-1
def kf1():
    fr = ffmpeg_frame(CLIP, 1.167)
    # scissor cut along the profile (points placed on a 3x view of the frame), refined by GrabCut in a
    # narrow band around the cut (SCION 29); the board behind is discarded for the reference's white field
    prof3 = [(440, 0), (430, 60), (420, 120), (415, 150), (392, 190), (372, 220), (356, 258), (362, 276),
             (392, 284), (425, 292), (430, 330), (443, 362), (462, 384), (470, 398), (463, 412), (472, 436),
             (488, 470), (484, 515), (497, 560), (525, 582), (575, 586), (600, 598), (570, 660), (548, 720),
             (960, 720), (960, 0)]
    poly = np.round(np.array(prof3, np.float64) / 3).astype(np.int32)
    a = fr[:, :, ::-1].copy()
    m0 = np.zeros(a.shape[:2], np.uint8)
    cv2.fillPoly(m0, [poly], 255)
    mask = np.full(m0.shape, cv2.GC_BGD, np.uint8)
    mask[cv2.dilate(m0, np.ones((5, 5), np.uint8)) > 0] = cv2.GC_PR_BGD
    mask[m0 > 0] = cv2.GC_PR_FGD
    mask[cv2.erode(m0, np.ones((7, 7), np.uint8)) > 0] = cv2.GC_FGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(a, mask, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    # chalk tray strip below the chin is board, not person
    S = 3.4
    g = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = cv2.resize(g, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
    mm = cv2.resize(m, None, fx=S, fy=S, interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
    mm = cv2.GaussianBlur(mm, (0, 0), 1.6)
    # high-key tone: lift mids, keep the spectacles black (the reference is a bright, soft close-up)
    g = np.clip((g - 22) * 1.12, 0, 255)
    g = 255 * (g / 255) ** 0.82
    canvas = np.ones((H, W), np.float32) * 249
    ox = W - g.shape[1] + 150
    cut = 95  # lift the frame so the mouth sits at the frame's centre line, as in the reference
    g, mm = g[cut:cut + H], mm[cut:cut + H]
    oy = 0
    hh, ww = g.shape
    sub = canvas[oy:oy + hh, ox:ox + ww]
    cw = min(ww, W - ox)
    sub[:, :cw] = sub[:, :cw] * (1 - mm[:, :cw]) + g[:, :cw] * mm[:, :cw]
    # faint film grain only on the person (it is film)
    rng = np.random.default_rng(3)
    grain = cv2.GaussianBlur(rng.normal(0, 6, canvas.shape).astype(np.float32), (0, 0), 0.9)
    full_m = np.zeros_like(canvas)
    full_m[oy:oy + hh, ox:ox + cw] = mm[:, :cw]
    canvas = np.clip(canvas + grain * full_m, 0, 255)
    img = Image.fromarray(canvas.astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(img)

    # the poem's sound as a trace in front of the mouth (sound-first: no text yet). In the keyframe the
    # trace is the clip's own audio 0.6-2.8 s, standing in for the poem recording.
    au = ffmpeg_audio(CLIP, 0.6, 2.2)
    hop = 40
    env = np.array([np.sqrt(np.mean(au[i:i + hop] ** 2)) for i in range(0, len(au) - hop, hop)])
    env = env / (env.max() + 1e-6)
    x0, x1, yc = 60, 820, 372
    xs = np.linspace(x1, x0, len(env))  # sound leaves the mouth leftward: newest at the mouth
    for i in range(len(env)):
        h = 4 + env[i] * 150
        d.line([(xs[i], yc - h / 2), (xs[i], yc + h / 2)], fill=(70, 70, 70), width=2)
    d.line([(x0, yc), (x1, yc)], fill=(150, 150, 150), width=1)
    # syllable ticks under the trace (heard units, not spelled)
    for sx, lab in ((450, "●"), (330, "●"), (165, "●●")):
        pass
    cue_strip(d, "0:10", True, False, False)
    caption(d, "READER A (fictional)", "0:10, after sound only",
            "“A gong? Something you strike — bin, tu, RONG.”", 52, 560, 560)
    img.save(os.path.join(HERE, "kf-1.png"))
    return img


# ================================================================ KF-2
def mouth_parts(jaw_deg):
    piv = (40, 200)  # the jaw hinge, off-screen left (the ear is out of frame, as in the reference)
    # upper face: nose base at top right, philtrum, ends at the vermilion border (lip laid over it)
    upper = [(0, 0), (585, 0), (590, 22), (560, 48), (515, 58), (488, 70), (480, 100), (490, 135), (505, 158),
             (520, 172), (500, 215), (420, 232), (300, 245), (0, 262)]
    nostril = [(500, 18), (545, 14), (560, 30), (540, 44), (505, 44)]
    upper_lip = [(395, 214), (430, 186), (472, 166), (505, 156), (528, 166), (556, 190), (562, 206), (540, 216),
                 (500, 224), (450, 232), (410, 232)]
    teeth = [(440, 222), (480, 220), (520, 216), (530, 232), (520, 252), (480, 258), (445, 250)]
    cavity = [(405, 236), (470, 226), (540, 214), (548, 238), (530, 285), (470, 300), (420, 296), (398, 270)]
    lower = [(0, 200), (300, 215), (400, 262), (440, 286), (480, 300), (510, 330), (495, 372), (470, 392), (458, 410),
             (470, 450), (498, 500), (506, 552), (488, 600), (440, 640), (380, 676), (350, 720), (0, 720)]
    lower_lip = [(405, 290), (470, 282), (525, 280), (552, 298), (556, 330), (538, 360), (500, 378), (462, 380),
                 (430, 366), (408, 330)]
    lip_hi = [(478, 300), (522, 296), (540, 312), (532, 326), (500, 326), (480, 316)]
    chin_shade = [(470, 450), (498, 500), (506, 552), (488, 600), (440, 640), (420, 640), (460, 590), (474, 540),
                  (468, 490), (455, 455)]
    L = lambda p: rot(catmull(p, 10), piv, jaw_deg)
    return dict(upper=catmull(upper, 10), nostril=catmull(nostril, 8), upper_lip=catmull(upper_lip, 10),
                teeth=catmull(teeth, 8), cavity=L(cavity) * 0.5 + catmull(cavity, 10) * 0.5, lower=L(lower),
                lower_lip=L(lower_lip), lip_hi=L(lip_hi), chin_shade=L(chin_shade))


def kf2():
    c = Card(seed=11)
    P = mouth_parts(jaw_deg=6.0)
    skin = (232, 181, 160)
    lip = (196, 112, 116)
    sh_down = lambda xx, yy: 1.0 - 0.10 * np.clip((yy - 200) / 600, 0, 1) - 0.06 * np.clip((xx - 300) / 300, 0, 1)
    c.lay(P["cavity"], (78, 34, 38), 1, lift=0, rough_amp=0.6)
    c.lay(P["teeth"], (238, 232, 222), 2, lift=3, rough_amp=0.6)
    c.lay(P["lower"], skin, 3, lift=8, shade=sh_down)
    c.lay(P["chin_shade"], (214, 158, 138), 4, lift=2, rough_amp=0.8)
    c.lay(P["lower_lip"], lip, 5, lift=5)
    c.lay(P["lip_hi"], (222, 158, 158), 6, lift=2, rough_amp=0.8)
    c.lay(P["upper"], skin, 7, lift=9, shade=lambda xx, yy: 1.0 - 0.05 * np.clip((xx - 380) / 200, 0, 1))
    c.lay(P["nostril"], (206, 148, 130), 9, lift=2, rough_amp=0.7)
    c.lay(P["upper_lip"], (186, 104, 110), 8, lift=5)
    img = c.pil()
    d = ImageDraw.Draw(img)
    # pins (the puppet's hinges, visible as in a cut-out rig)
    for (px, py) in ((436, 318), (430, 205)):
        d.ellipse((px - 4, py - 4, px + 4, py + 4), fill=(150, 140, 120))
    # the poem typesets letter by letter: line 3 is being read now
    f = font(SERIF, 40)
    x, y = 640, 150
    shown = [POEM[0], POEM[1], "smells of pop"]
    for i, ln in enumerate(shown):
        d.text((x, y + i * 58), ln, font=f, fill=(35, 35, 35))
    # the cursor at the reading point
    cx = x + d.textlength(shown[2], font=f) + 4
    d.rectangle((cx, y + 2 * 58 + 6, cx + 3, y + 2 * 58 + 46), fill=(196, 112, 116))
    cue_strip(d, "0:24", True, True, False, x=640, y=60)
    caption(d, "READER B (fictional)", "0:24, sound + text",
            "“It hangs and swings… a lantern? A bell that’s gone quiet?”", 640, 440, 590)
    img.save(os.path.join(HERE, "kf-2.png"))
    return img


# ================================================================ KF-3
def binturong_cut():
    im = Image.open(os.path.join(SRC, "brehm265.jpg")).convert("RGB")
    ox, oy = 60, 420  # crop-grid origin used to place the scissor points
    pts = [(30, 515), (90, 545), (130, 535), (200, 522), (262, 486), (305, 478), (335, 540), (430, 470), (520, 420),
           (600, 385), (700, 352), (790, 338), (830, 320), (870, 285), (920, 258), (965, 262), (990, 300),
           (985, 360), (968, 430), (950, 500), (920, 565), (880, 625), (855, 700), (815, 790), (790, 870),
           (720, 893), (698, 850), (712, 800), (650, 790), (560, 838), (545, 935), (470, 962), (418, 932),
           (428, 880), (400, 835), (335, 862), (300, 960), (250, 1040), (130, 1040), (140, 1000), (218, 950),
           (228, 860), (195, 800), (150, 760), (128, 722), (100, 680), (95, 600), (78, 560)]
    poly = np.array([(x + ox, y + oy) for x, y in pts], np.int32)
    a = np.asarray(im)[:, :, ::-1].copy()
    m0 = np.zeros(a.shape[:2], np.uint8)
    cv2.fillPoly(m0, [poly], 255)
    gm = np.full(m0.shape, cv2.GC_BGD, np.uint8)
    gm[cv2.dilate(m0, np.ones((15, 15), np.uint8)) > 0] = cv2.GC_PR_BGD
    gm[m0 > 0] = cv2.GC_PR_FGD
    gm[cv2.erode(m0, np.ones((21, 21), np.uint8)) > 0] = cv2.GC_FGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    x0, y0, w0, h0 = cv2.boundingRect(poly)
    pad = 30
    sl = (slice(max(0, y0 - pad), y0 + h0 + pad), slice(max(0, x0 - pad), x0 + w0 + pad))
    sub = gm[sl].copy()
    cv2.grabCut(a[sl].copy(), sub, None, bgd, fgd, 4, cv2.GC_INIT_WITH_MASK)
    gm[sl] = sub
    m = np.where((gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    m = np.where(lab == k, 255, 0).astype(np.uint8)
    # the cut is made by scissors: smooth the matte boundary, keep a thin white paper margin
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    margin = cv2.dilate((m > 128).astype(np.uint8) * 255, np.ones((9, 9), np.uint8))
    rgb = np.asarray(im).astype(np.float32)
    gray = rgb.mean(2, keepdims=True)
    rgb = gray * 0.65 + rgb * 0.35  # cream newsprint toward neutral, keep a little warmth
    rgb = np.where((m > 128)[:, :, None], rgb, np.array([245, 242, 234], np.float32))
    rgba = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), cv2.GaussianBlur(margin, (0, 0), 0.8)])
    ys, xs = np.where(margin > 20)
    piece = Image.fromarray(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")
    tail_tip = (920 + ox - xs.min(), 262 + oy - ys.min())
    return piece, tail_tip


def kf3():
    c = Card(ground=(248, 246, 241), seed=21)
    cx, cy, R = 900, 330, 190
    cord_top = (cx, 0)
    # --- the gong (handmade): bronze card with hammered rings, cut into 12 wedges; 5 have fallen away
    rng = np.random.default_rng(5)
    wedges = []
    for i in range(12):
        a0 = math.radians(-90 + i * 30)
        a1 = math.radians(-90 + (i + 1) * 30)
        arc = [(cx + R * math.cos(a0 + (a1 - a0) * t), cy + R * math.sin(a0 + (a1 - a0) * t)) for t in
               np.linspace(0, 1, 14)]
        wedges.append([(cx, cy)] + arc)
    gone = {2: (240, 150, 38), 3: (300, 300, 64), 4: (190, 420, 101), 5: (40, 380, -48), 6: (-60, 330, 140)}
    # bronze shading by radius (hammered rings)
    def bronze(xx, yy):
        r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        return 0.88 + 0.08 * np.cos(r / 9.0) + 0.06 * np.clip(1 - r / R, 0, 1)

    # the animal goes in first: it is behind the gong, hanging from the cord by its tail
    piece, tip = binturong_cut()
    sc = 0.62
    piece = piece.resize((int(piece.width * sc), int(piece.height * sc)), Image.LANCZOS)
    tip = (tip[0] * sc, tip[1] * sc)
    ang = 52
    pw, ph = piece.size
    rp = piece.rotate(ang, resample=Image.BICUBIC, expand=True)
    # where the tail tip lands after rotation
    ccx, ccy = pw / 2, ph / 2
    a = math.radians(-ang)
    tx = (tip[0] - ccx) * math.cos(a) - (tip[1] - ccy) * math.sin(a) + rp.width / 2
    ty = (tip[0] - ccx) * math.sin(a) + (tip[1] - ccy) * math.cos(a) + rp.height / 2
    knot = (cx + 4, 72)
    px, py = int(knot[0] - tx), int(knot[1] - ty)
    # cord
    base = c.pil()
    dd = ImageDraw.Draw(base)
    dd.line([cord_top, (knot[0], knot[1] + 6)], fill=(92, 72, 52), width=3)
    dd.line([(cx, knot[1]), (cx, cy - R + 4)], fill=(92, 72, 52), width=3)
    # cast shadow of the animal
    al = np.zeros((H, W), np.float32)
    A = np.asarray(rp)[:, :, 3].astype(np.float32) / 255
    x0, y0 = max(px, 0), max(py, 0)
    x1, y1 = min(px + rp.width, W), min(py + rp.height, H)
    al[y0:y1, x0:x1] = A[y0 - py:y1 - py, x0 - px:x1 - px]
    sh = cv2.GaussianBlur(shift(al, 6, 9), (0, 0), 8)
    arr = np.asarray(base).astype(np.float32) * (1 - 0.3 * sh)[:, :, None]
    base = Image.fromarray(arr.astype(np.uint8))
    base.paste(rp, (px, py), rp)
    c.img = np.asarray(base).astype(np.float32)

    # gong wedges still hanging (they cover the animal's upper body: it is coming out from behind)
    for i, wd in enumerate(wedges):
        if i in gone:
            continue
        c.lay(catmull(wd, 2, closed=True) if False else np.array(wd), (176, 136, 82), 40 + i, lift=9, rough_amp=1.0,
              shade=bronze)
    # wedges falling away (rotated, displaced, lower), drawn last: they are in front
    for i, (dx, dy, da) in gone.items():
        wd = np.array(wedges[i])
        ctr = wd.mean(0)
        wd2 = rot(wd, ctr, da) + np.array([dx, dy]) * 0.55
        c.lay(wd2, (176, 136, 82), 60 + i, lift=14, rough_amp=1.0,
              shade=lambda xx, yy: 0.92 + 0.06 * np.cos((xx + yy) / 11.0))
    img = c.pil()
    d = ImageDraw.Draw(img)
    # the boss of the gong and its suspension hole
    d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), outline=(120, 90, 50), width=3)
    # the fixed text: the line does not change, its reading does
    f = font(SERIF, 34)
    tx0, ty0 = 70, 300
    line = POEM[0]
    d.text((tx0, ty0), line, font=f, fill=(35, 35, 35))
    pre = "In the dark it "
    hx = tx0 + d.textlength(pre, font=f)
    hw = d.textlength("hangs", font=f)
    # red-pencil underline under "hangs": the word that changes meaning
    for k in range(3):
        d.line([(hx - 3 + k, ty0 + 46 + k * 0.6), (hx + hw + 4, ty0 + 44 + k * 0.4)], fill=(186, 52, 44), width=2)
    d.text((tx0, ty0 + 60), POEM[2], font=f, fill=(150, 150, 150))
    cue_strip(d, "0:44", True, True, True, x=70, y=40)
    caption(d, "READER A (fictional)", "0:44, image released at 0:38",
            "“Oh — it hangs by its tail. ‘Never rings’: it was never a gong.”", 70, 500, 560)
    img.save(os.path.join(HERE, "kf-3.png"))
    return img


def board(imgs, names):
    ref = Image.open(REF).convert("RGB").resize((640, 360), Image.LANCZOS)
    tiles = [ref] + [i.resize((640, 360), Image.LANCZOS) for i in imgs]
    labels = ["Reference: Le Maki Mococo (Ribot)"] + names
    B = Image.new("RGB", (1300, 2 * 360 + 3 * 20 + 2 * 34), (20, 20, 20))
    d = ImageDraw.Draw(B)
    f = font(INTER_M, 20)
    for k, (t, lb) in enumerate(zip(tiles, labels)):
        x = 10 + (k % 2) * 650
        y = 10 + (k // 2) * (360 + 34 + 20)
        d.text((x, y), lb, font=f, fill=(235, 235, 235))
        B.paste(t, (x, y + 30))
    B.save(os.path.join(HERE, "board.jpg"), quality=90)


if __name__ == "__main__":
    a = kf1()
    b = kf2()
    c = kf3()
    board([a, b, c], ["1 · Lecture Profile (foraged film + cutout)", "2 · Paper Mouth (articulated cut paper)",
                      "3 · Gong to Animal (collage metamorphosis)"])
