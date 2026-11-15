"""Comics helpers for the Oubapo / Madden films: drawn characters, balloons,
panels, pages on a board, and a reading camera.

Everything is drawn with PIL through kit.Ink. Panels are rendered once into
images (fixed seed, no boil) so repeated occurrences can reuse the exact bytes.
"""
from __future__ import annotations

import hashlib
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from kit import *  # noqa: F401,F403
from kit import FONTS, INK, PAGE, PAPER, WASH, ACCENT, BRASS, MUTED, RULE, NIGHT, Ink, W, H, lerp, smooth, clamp, ramp, ease

SKIN = (247, 226, 204)
SKIN_D = (226, 196, 170)
NAVY = (58, 72, 104)
NAVY_D = (40, 48, 72)
OLIVE = (112, 118, 84)
SHIRT = (240, 238, 230)
TROUSER = (62, 58, 62)
HAIR = (70, 50, 40)
WALL = (234, 224, 204)
WALL2 = (220, 206, 182)
FLOOR = (196, 178, 152)
WOOD = (150, 110, 70)
DOORC = (120, 96, 80)
BOARD = (54, 50, 48)
CAPTION = (246, 226, 168)
VCOAT = (150, 40, 50)       # the visitor's coat: rendered as pen hatching
WHITE = (255, 255, 255)
SPOT = (204, 84, 72)        # red spot colour (only quatre-vingt-quinze uses it)
SPOT_L = (232, 158, 146)

# ------------------------------------------------------------ lettering ---

_lf = {}


# Pen-and-ink house rules (after the reference pages): lettering in the mono face,
# thickened with a stroke so it reads as a hand-ruled pen letter; UPPER for the
# Oubapo pages, mixed case for Madden.
STYLE = {"upper": True, "letter": "mono"}


def lfont(size, weight="Bold"):
    key = (int(size), weight, STYLE["letter"])
    if key not in _lf:
        if STYLE["letter"] == "mono":
            f = ImageFont.truetype(str(FONTS / "ibm-plex-mono.woff2"), int(size))
        else:
            f = ImageFont.truetype(str(FONTS / "instrument-sans.woff2"), int(size))
            try:
                f.set_variation_by_name(weight)
            except Exception:
                pass
        _lf[key] = f
    return _lf[key]


def pen_text(d, xy, s, f, fill=INK, anchor="mm"):
    sw = max(1, int(f.size / 26)) if STYLE["letter"] == "mono" else 0
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=fill)


def up(s):
    return s.upper() if STYLE["upper"] else s


def wrap(text, f, maxw):
    out = []
    for para in text.split("\n"):
        words, cur = para.split(" "), ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if f.getlength(trial) <= maxw or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = wd
        out.append(cur)
    return out


def text_block(ink, cx, cy, lines, size, color=INK, weight="Bold", lh=1.16):
    f = lfont(size, weight)
    n = len(lines)
    for k, ln in enumerate(lines):
        y = cy + (k - (n - 1) / 2) * size * lh
        pen_text(ink.d, (cx, y), ln, f, color)


def _superellipse(cx, cy, rx, ry, n=2.6, steps=96):
    pts = []
    for k in range(steps):
        a = 2 * math.pi * k / steps
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + rx * math.copysign(abs(c) ** (2 / n), c), cy + ry * math.copysign(abs(s) ** (2 / n), s)))
    return pts


def balloon(ink, cx, cy, text, size=34, tail=None, maxw=420, kind="speech", width=4, weight="Bold",
            fill=PAGE, color=INK, tail_w=None, lines=None, pad=None):
    """Speech / thought / whisper balloon centred at (cx, cy); tail points at `tail`.

    Returns the balloon's bounding box."""
    f = lfont(size, weight)
    lines = lines or wrap(up(text) if kind != "keep" else text, f, maxw)
    tw = max(f.getlength(ln) for ln in lines)
    th = size * 1.16 * len(lines)
    px, py = pad or (size * 0.75, size * 0.55)
    rx, ry = (tw / 2 + px) * 1.08, (th / 2 + py) * 1.1
    pts = _superellipse(cx, cy, rx, ry)
    n = len(pts)
    c = tuple(fill)
    if kind == "thought":
        ink.d.ellipse([cx - rx - 6, cy - ry - 6, cx + rx + 6, cy + ry + 6], fill=c)
        bumps = 16
        for k in range(bumps):
            a = 2 * math.pi * k / bumps
            bx, by = cx + rx * math.cos(a), cy + ry * math.sin(a)
            r = size * 0.62
            ink.circle(bx, by, r, fill=c, color=color, width=width * 0.8)
        ink.d.ellipse([cx - rx + 2, cy - ry + 2, cx + rx - 2, cy + ry - 2], fill=c)
        if tail:
            tx, ty = tail
            for k, fr in enumerate((0.45, 0.68, 0.86)):
                bx, by = lerp(cx, tx, fr + 0.0), lerp(cy + ry * 0.6, ty, fr)
                r = size * (0.32 - 0.08 * k)
                ink.circle(bx, by, r, fill=c, color=color, width=width * 0.7)
        text_block(ink, cx, cy, lines, size, color, weight)
        return (cx - rx, cy - ry, cx + rx, cy + ry)
    # tail geometry
    gap = None
    if tail:
        tx, ty = tail
        ang = math.atan2(ty - cy, tx - cx)
        def adiff(i):
            d = (math.atan2(pts[i][1] - cy, pts[i][0] - cx) - ang) % (2 * math.pi)
            return min(d, 2 * math.pi - d)
        best = min(range(n), key=adiff)
        k = max(2, int((tail_w or size * 0.55) / (2 * math.pi * max(rx, ry) / n)))
        i1, i2 = (best - k) % n, (best + k) % n
        b1, b2 = pts[i1], pts[i2]
        # slight curve: tip offset
        ink.d.polygon([b1, b2, (tx, ty)], fill=c)
        gap = (i1, i2)
    ink.d.polygon(pts, fill=c)
    if gap:
        ink.d.polygon([b1, b2, (tx, ty)], fill=c)
    # outline
    if gap:
        i1, i2 = gap
        seq = [pts[(i2 + j) % n] for j in range(((i1 - i2) % n) + 1)]
    else:
        seq = pts + [pts[0]]
    if kind == "whisper":
        for j in range(0, len(seq) - 1, 2):
            ink.line([seq[j], seq[j + 1]], color, width * 0.8)
    else:
        ink.line(seq, color, width)
    if gap:
        ink.line([b1, (tx, ty), b2], color, width)
    text_block(ink, cx, cy, lines, size, color, weight)
    return (cx - rx, cy - ry, cx + rx, cy + ry)


def caption_box(ink, x, y, text, size=28, maxw=380, fill=CAPTION, color=INK, width=3, anchor="lt", weight="SemiBold"):
    f = lfont(size, weight)
    lines = wrap(up(text), f, maxw)
    tw = max(f.getlength(ln) for ln in lines)
    th = size * 1.16 * len(lines)
    bw, bh = tw + size * 0.9, th + size * 0.6
    if anchor[0] == "r":
        x -= bw
    elif anchor[0] == "m":
        x -= bw / 2
    if anchor[1] == "b":
        y -= bh
    ink.rect(x, y, x + bw, y + bh, fill=fill, color=color, width=width)
    text_block(ink, x + bw / 2, y + bh / 2, lines, size, color, weight)
    return (x, y, x + bw, y + bh)


def sfx(ink, x, y, text, size=70, angle=-8, color=ACCENT, stroke=INK, sw=5):
    f = lfont(size, "Bold")
    tw = int(f.getlength(text)) + 40
    layer = Image.new("RGBA", (tw, int(size * 1.6)), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((tw / 2, size * 0.8), text, font=f, fill=tuple(color) + (255,), anchor="mm",
                               stroke_width=sw, stroke_fill=tuple(stroke) + (255,))
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    ink.img.paste(layer, (int(x - layer.width / 2), int(y - layer.height / 2)), layer)
    ink.d = ImageDraw.Draw(ink.img, "RGBA")


# ------------------------------------------------------------ figures ---

CAST = {
    "visitor": dict(coat=VCOAT, trousers=TROUSER, hair=HAIR, hat="cloche", long=True),
    "porter": dict(coat=NAVY, trousers=NAVY_D, hair=(60, 52, 48), hat="cap", tash=True),
    "clerk": dict(coat=OLIVE, trousers=(80, 74, 70), hair=(120, 110, 100), hat=None, glasses=True, shirt=True),
    "other": dict(coat=(96, 112, 88), trousers=TROUSER, hair=(150, 104, 60), hat=None),
}


def _limb(ink, pts, col, w):
    ink.line(pts, INK, w + 5)
    ink.line(pts, col, w, amount=0.4)


def person(ink, x, y, s=1.0, who="visitor", facing=1, pose="stand", arms=None, phase=0.0, mouth="flat",
           brows="flat", eyes="open", look=(1, 0), back=False, lean=0.0, holding=None, sweat=False):
    """A cartoon person, feet at (x, y); about 255*s px tall standing.

    arms: {"front": (upper_deg, fore_deg), "back": (...)} measured from straight down,
    positive swings toward `facing`. Returns anchor points (head, hands, ...)."""
    u = s
    c = CAST[who]
    coat = c["coat"]
    out = {}
    if pose == "sit":
        hip = (x, y - 78 * u)
        sh = (x + lean * u, y - 168 * u)
    else:
        hip = (x, y - 108 * u)
        sh = (x + lean * u, y - 200 * u)
    head = (sh[0] + 3 * u * facing, sh[1] - 40 * u)
    out["head"] = head
    lw = 15 * u
    # ---- legs
    if pose == "sit":
        knee = (hip[0] + 58 * u * facing, hip[1] + 4 * u)
        legs = [[(hip[0] - 6 * u * facing, hip[1]), knee, (knee[0] + 4 * u * facing, y - 6 * u)],
                [hip, (knee[0] - 10 * u * facing, knee[1] - 2 * u), (knee[0] - 10 * u * facing, y - 6 * u)]]
    elif pose in ("walk", "run"):
        amp = 0.42 if pose == "walk" else 0.7
        a = math.sin(2 * math.pi * phase) * amp
        legs = []
        for sg in (1, -1):
            th = a * sg
            knee = (hip[0] + math.sin(th) * 52 * u * facing, hip[1] + math.cos(th) * 52 * u)
            bend = max(0, -math.sin(2 * math.pi * phase) * sg) * 0.6
            foot = (knee[0] + math.sin(th - bend) * 50 * u * facing, knee[1] + math.cos(th - bend) * 50 * u)
            legs.append([hip, knee, foot])
    else:
        legs = [[(hip[0] - 9 * u, hip[1]), (x - 11 * u, y - 52 * u), (x - 13 * u, y - 6 * u)],
                [(hip[0] + 9 * u, hip[1]), (x + 11 * u, y - 52 * u), (x + 13 * u, y - 6 * u)]]
    for leg in legs:
        _limb(ink, leg, c["trousers"], lw)
        fx, fy = leg[-1]
        ink.ellipse(fx + 6 * u * (facing or 1), fy + 2 * u, 14 * u, 7 * u, fill=INK, color=INK, width=2)
    # ---- arms setup
    arms = arms or {}
    fa = arms.get("front", (8, 4))
    ba = arms.get("back", (-8, -4))
    f_ = facing or 1

    def arm(shoulder, ang):
        a1, a2 = math.radians(ang[0]), math.radians(ang[1])
        el = (shoulder[0] + math.sin(a1) * 50 * u * f_, shoulder[1] + math.cos(a1) * 50 * u)
        hd = (el[0] + math.sin(a2) * 46 * u * f_, el[1] + math.cos(a2) * 46 * u)
        return el, hd

    shb = (sh[0] - 15 * u * f_, sh[1] + 8 * u)
    shf = (sh[0] + 15 * u * f_, sh[1] + 8 * u)
    if back:
        shb, shf = shf, shb
    elb, hb = arm(shb, ba)
    if not back:
        _limb(ink, [shb, elb, hb], coat, 14 * u)
        ink.circle(hb[0], hb[1], 8 * u, fill=SKIN, color=INK, width=2.5)
    # ---- torso
    hem = y - (62 if c.get("long") else 92) * u
    if pose == "sit":
        hem = hip[1] + 6 * u
    hx = hip[0]
    tor = [(sh[0] - 25 * u, sh[1] - 2 * u), (sh[0] + 25 * u, sh[1] - 2 * u),
           (hx + 31 * u, hem), (hx - 31 * u, hem)]
    if pose == "sit":
        tor = [(sh[0] - 25 * u, sh[1] - 2 * u), (sh[0] + 25 * u, sh[1] - 2 * u),
               (hx + 30 * u + 30 * u * f_ * (f_ > 0), hem), (hx - 30 * u + 30 * u * f_ * (f_ < 0), hem)]
    ink.poly(tor, fill=coat, color=INK, width=3.5)
    if c.get("shirt") and not back:
        mx = sh[0] + 5 * u * f_
        ink.poly([(mx - 10 * u, sh[1] - 2 * u), (mx + 10 * u, sh[1] - 2 * u), (mx, sh[1] + 40 * u)], fill=SHIRT, color=INK, width=2)
    if not back:
        bx = sh[0] + 6 * u * f_
        for k in range(3):
            by = lerp(sh[1] + 20 * u, hem - 14 * u, k / 2.5)
            if pose != "sit" or by < hip[1]:
                ink.circle(bx, by, 2.6 * u, fill=BRASS if who == "porter" else INK, color=INK, width=1, rough=False)
        ink.line([(sh[0] - 9 * u, sh[1] - 2 * u), (sh[0] + 4 * u * f_, sh[1] + 16 * u), (sh[0] + 12 * u, sh[1] - 2 * u)], INK, 2.5)
    # neck
    ink.rect(head[0] - 7 * u, head[1] + 22 * u, head[0] + 7 * u, sh[1] + 2 * u, fill=SKIN, color=INK, width=2)
    # ---- head
    hr, hry = 25 * u, 29 * u
    hx_, hy_ = head
    hair = c["hair"]
    if who == "visitor":
        ink.poly([(hx_ - 31 * u, hy_ - 6 * u), (hx_ + 31 * u, hy_ - 6 * u), (hx_ + 30 * u, hy_ + 22 * u), (hx_ - 30 * u, hy_ + 22 * u)],
                 fill=hair, color=INK, width=2.5)
    ink.ellipse(hx_, hy_, hr, hry, fill=SKIN, color=INK, width=3)
    fx = 8 * u * f_ if not back else 0
    if back:
        if who == "visitor":
            ink.ellipse(hx_, hy_ - 2 * u, hr + 4 * u, hry, fill=hair, color=INK, width=3)
        else:
            ink.ellipse(hx_, hy_ - 6 * u, hr, hry - 6 * u, fill=hair, color=INK, width=2.5)
    else:
        # hair / ears
        if who == "visitor":
            ink.poly([(hx_ - 27 * u, hy_ - 4 * u), (hx_ - 20 * u, hy_ - 26 * u), (hx_ + 22 * u, hy_ - 26 * u),
                      (hx_ + 28 * u, hy_ - 2 * u), (hx_ + 10 * u * f_, hy_ - 14 * u)], fill=hair, color=INK, width=2.5)
        elif who == "clerk":
            for sg in (-1, 1):
                ink.ellipse(hx_ + sg * 23 * u, hy_ - 4 * u, 6 * u, 12 * u, fill=hair, color=INK, width=2)
        elif who == "other":
            ink.poly([(hx_ - 26 * u, hy_ - 6 * u), (hx_ - 10 * u, hy_ - 32 * u), (hx_ + 18 * u, hy_ - 30 * u), (hx_ + 27 * u, hy_ - 8 * u)],
                     fill=hair, color=INK, width=2.5)
        ex, ey = hx_ + fx, hy_ + 1 * u
        lx, ly = look
        for sg in (-1, 1):
            px = ex + sg * 10 * u
            if eyes == "closed":
                ink.arc(px, ey, 4.5 * u, math.pi * 0.1, math.pi * 0.9, INK, 2.5)
            elif eyes == "wide":
                ink.ellipse(px, ey, 5.5 * u, 6.5 * u, fill=PAGE, color=INK, width=2)
                ink.circle(px + lx * 2 * u, ey + ly * 2 * u, 2.4 * u, fill=INK, color=INK, width=1, rough=False)
            elif eyes == "side":
                ink.ellipse(px + lx * 2.5 * u, ey + ly * 1.5 * u, 2.6 * u, 4.2 * u, fill=INK, color=INK, width=1, rough=False)
                ink.line([(px - 5 * u, ey - 1 * u), (px + 5 * u, ey - 1 * u)], INK, 2)
            else:
                ink.ellipse(px + lx * 1.5 * u, ey + ly * 1.5 * u, 3 * u, 4.4 * u, fill=INK, color=INK, width=1, rough=False)
            # brows
            by = ey - 11 * u
            inner, outer = (px - sg * 5 * u * 0 + (-sg) * 5 * u, px + sg * 6 * u)
            dy_in = {"flat": 0, "angry": 4, "worried": -4, "raised": -5, "sly": 2 * sg}.get(brows, 0) * u
            dy_out = {"raised": -5, "sly": -2 * sg}.get(brows, 0) * u
            ink.line([(inner, by + dy_in), (outer, by + dy_out)], INK, 3)
        if c.get("glasses"):
            for sg in (-1, 1):
                ink.circle(ex + sg * 10 * u, ey, 7.5 * u, color=INK, width=2)
            ink.line([(ex - 3 * u, ey), (ex + 3 * u, ey)], INK, 2)
        # nose
        nx = ex + 2 * u * f_
        ink.line([(nx, ey + 2 * u), (nx + 6 * u * f_, ey + 10 * u), (nx, ey + 12 * u)], INK, 2.5)
        my = ey + 20 * u
        mx = ex + 1 * u * f_
        if c.get("tash"):
            ink.poly([(mx - 11 * u, my - 4 * u), (mx + 11 * u, my - 4 * u), (mx + 13 * u, my + 1 * u), (mx, my - 1 * u), (mx - 13 * u, my + 1 * u)],
                     fill=c["hair"], color=INK, width=1.5)
            my += 3 * u
        if mouth == "flat":
            ink.line([(mx - 6 * u, my), (mx + 6 * u, my)], INK, 2.5)
        elif mouth == "smile":
            ink.arc(mx, my - 4 * u, 8 * u, math.pi * 0.15, math.pi * 0.85, INK, 2.5)
        elif mouth == "smirk":
            ink.line([(mx - 6 * u, my + 1 * u), (mx + 3 * u, my), (mx + 8 * u * f_, my - 4 * u)], INK, 2.5)
        elif mouth == "frown":
            ink.arc(mx, my + 6 * u, 7 * u, math.pi * 1.15, math.pi * 1.85, INK, 2.5)
        elif mouth == "open":
            ink.ellipse(mx, my + 1 * u, 7 * u, 5.5 * u, fill=(90, 30, 36), color=INK, width=2)
        elif mouth == "shout":
            ink.ellipse(mx, my + 2 * u, 9 * u, 8 * u, fill=(90, 30, 36), color=INK, width=2)
        elif mouth == "o":
            ink.circle(mx, my + 1 * u, 3.5 * u, fill=(90, 30, 36), color=INK, width=2)
        elif mouth == "wavy":
            ink.line([(mx - 7 * u, my), (mx - 3 * u, my - 2 * u), (mx + 1 * u, my + 1 * u), (mx + 5 * u, my - 2 * u), (mx + 8 * u, my)], INK, 2.2)
        if sweat:
            ink.poly([(hx_ - f_ * 30 * u, hy_ - 14 * u), (hx_ - f_ * 34 * u, hy_ - 4 * u), (hx_ - f_ * 26 * u, hy_ - 4 * u)],
                     fill=(170, 200, 230), color=INK, width=1.5)
    # hats
    if c.get("hat") == "cap":
        ink.poly([(hx_ - 27 * u, hy_ - 14 * u), (hx_ + 27 * u, hy_ - 14 * u), (hx_ + 29 * u, hy_ - 36 * u), (hx_ - 29 * u, hy_ - 36 * u)],
                 fill=NAVY_D, color=INK, width=2.5)
        if not back:
            ink.poly([(hx_ + f_ * 4 * u, hy_ - 15 * u), (hx_ + f_ * 38 * u, hy_ - 9 * u), (hx_ + f_ * 30 * u, hy_ - 16 * u)], fill=INK, color=INK, width=2)
            ink.circle(hx_ + f_ * 6 * u, hy_ - 25 * u, 4.5 * u, fill=BRASS, color=INK, width=1.5)
    elif c.get("hat") == "cloche":
        ink.poly([(hx_ - 33 * u, hy_ - 12 * u), (hx_ + 33 * u, hy_ - 12 * u), (hx_ + 24 * u, hy_ - 34 * u), (hx_, hy_ - 38 * u), (hx_ - 24 * u, hy_ - 34 * u)],
                 fill=(70, 62, 72), color=INK, width=2.5)
        ink.line([(hx_ - 28 * u, hy_ - 17 * u), (hx_ + 28 * u, hy_ - 17 * u)], BRASS, 4 * u)
    # ---- front arm + holding
    elf, hf = arm(shf, fa)
    out["hands"] = {"front": hf, "back": hb}
    if holding:
        holding(ink, hf, hb)
    if back:
        _limb(ink, [shb, elb, hb], coat, 14 * u)
        ink.circle(hb[0], hb[1], 8 * u, fill=SKIN, color=INK, width=2.5)
    _limb(ink, [shf, elf, hf], coat, 14 * u)
    ink.circle(hf[0], hf[1], 8.5 * u, fill=SKIN, color=INK, width=2.5)
    return out


def point_hand(ink, hand, toward, u=1.0):
    """A pointing index finger from hand toward a direction (dx sign)."""
    hx, hy = hand
    ink.line([(hx, hy), (hx + toward * 16 * u, hy - 1 * u)], INK, 6 * u)
    ink.line([(hx, hy), (hx + toward * 16 * u, hy - 1 * u)], SKIN, 3.2 * u, amount=0.2)


# ------------------------------------------------------------- props ---

def bench_s(ink, x, y, w=300, u=1.0, fill=WOOD):
    ink.rect(x - w / 2, y - 64 * u, x + w / 2, y - 52 * u, fill=fill, color=INK, width=3)
    ink.rect(x - w / 2, y - 120 * u, x + w / 2, y - 104 * u, fill=fill, color=INK, width=3)
    ink.rect(x - w / 2, y - 98 * u, x + w / 2, y - 84 * u, fill=fill, color=INK, width=3)
    for px in (x - w / 2 + 16 * u, x + w / 2 - 16 * u):
        ink.line([(px, y - 52 * u), (px, y)], INK, 5 * u)
        ink.line([(px, y - 120 * u), (px, y - 64 * u)], INK, 4 * u)


def door_s(ink, x, y, w=120, h=230, fill=DOORC, sign="SERVICE", u=1.0, keyhole=True):
    ink.rect(x - w / 2 - 10 * u, y - h - 10 * u, x + w / 2 + 10 * u, y, fill=(90, 74, 62), color=INK, width=3)
    ink.rect(x - w / 2, y - h, x + w / 2, y, fill=fill, color=INK, width=3)
    for k in range(2):
        yy0 = y - h + 18 * u + k * (h / 2)
        ink.rect(x - w / 2 + 14 * u, yy0, x + w / 2 - 14 * u, yy0 + h / 2 - 34 * u, color=(80, 62, 52), width=2)
    ink.circle(x + w / 2 - 18 * u, y - h / 2, 6 * u, fill=BRASS, color=INK, width=2)
    if keyhole:
        ink.circle(x + w / 2 - 18 * u, y - h / 2 + 18 * u, 3 * u, fill=INK, color=INK, width=1, rough=False)
    if sign:
        f = lfont(int(15 * u), "Bold")
        tw = f.getlength(sign) + 16 * u
        ink.rect(x - tw / 2, y - h - 46 * u, x + tw / 2, y - h - 18 * u, fill=PAGE, color=INK, width=2)
        ink.d.text((x, y - h - 32 * u), sign, font=f, fill=INK, anchor="mm")


def bell_s(ink, x, y, u=1.0, ringing=False):
    """Station bell on a wall bracket; (x, y) is the bracket's wall point."""
    ink.line([(x, y), (x + 34 * u, y)], INK, 5 * u)
    ink.line([(x + 34 * u, y), (x + 34 * u, y + 10 * u)], INK, 3 * u)
    bx, by = x + 34 * u, y + 10 * u
    tilt = 0.25 if ringing else 0.0
    ca, sa = math.cos(tilt), math.sin(tilt)

    def P(px, py):
        return (bx + px * ca - py * sa, by + px * sa + py * ca)

    ink.poly([P(-6, 0), P(6, 0), P(16, 14), P(22, 34), P(28, 40), P(-28, 40), P(-22, 34), P(-16, 14)],
             fill=BRASS, color=INK, width=3)
    ink.circle(*P(0, 44), 5 * u, fill=INK, color=INK, width=1)
    if ringing:
        for k in (1, 2):
            ink.arc(bx, by + 24 * u, (30 + 14 * k) * u, -math.pi * 0.95, -math.pi * 0.62, INK, 3)
            ink.arc(bx, by + 24 * u, (30 + 14 * k) * u, -math.pi * 0.38, -math.pi * 0.05, INK, 3)


def wall_clock(ink, x, y, r, hours=4 + 10 / 60):
    clock(ink, x, y, r, hours)


def station_bg(ink, w, h, floor_y, dado=None, tiles=True, wall=WALL):
    ink.d.rectangle([0, 0, w, floor_y], fill=wall)
    dado = dado if dado is not None else floor_y - (floor_y * 0.38)
    ink.d.rectangle([0, dado, w, floor_y], fill=WALL2)
    if tiles:
        for xx in range(0, int(w) + 40, 40):
            ink.line([(xx, dado), (xx, floor_y)], RULE, 1.4, alpha=200)
        for yy in range(int(dado), int(floor_y), 22):
            ink.line([(0, yy), (w, yy)], RULE, 1.2, alpha=170)
    ink.line([(0, dado), (w, dado)], INK, 3)
    ink.d.rectangle([0, floor_y, w, h], fill=FLOOR)
    ink.line([(0, floor_y), (w, floor_y)], INK, 3)
    for k in range(1, 5):
        yy = floor_y + (h - floor_y) * (k / 5) ** 1.3
        ink.line([(0, yy), (w, yy)], (170, 152, 128), 1.6, alpha=200)


def envelope_s(ink, x, y, w=70, h=46, open_=0.0, seal=True, angle=0.0):
    envelope(ink, x, y, w, h, open_)
    if seal and open_ < 0.3:
        ink.circle(x, y + 2, max(4, w * 0.08), fill=ACCENT, color=INK, width=1.5)


# ------------------------------------------------------------- panels ---

# exact fill colour -> treatment. Anything not listed is thresholded by luminance,
# so every drawing comes out as black-and-white pen and ink with solid blacks.
INK_MAP = {VCOAT: "hatch", BRASS: "white", (170, 136, 100): "white", ACCENT: "white", CAPTION: "white",
           (40, 50, 110): "black", (176, 176, 168): "white", (120, 140, 90): "black"}


def ink_treat(img, extra=None, threshold=140):
    a = np.asarray(img.convert("RGB")).astype(np.int32)
    lum = (a[..., 0] * 299 + a[..., 1] * 587 + a[..., 2] * 114) / 1000.0
    out = np.clip((lum - (threshold - 24)) / 48.0, 0, 1)[..., None] * 255.0
    out = np.repeat(out, 3, axis=2)
    hh, ww = lum.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    hatch = ((xx + yy) % 8) < 2
    table = dict(INK_MAP)
    table.update(extra or {})
    for col, tr in table.items():
        m = (a[..., 0] == col[0]) & (a[..., 1] == col[1]) & (a[..., 2] == col[2])
        if not m.any():
            continue
        if tr == "white":
            out[m] = 255
        elif tr == "black":
            out[m] = 0
        elif tr == "hatch":
            out[m] = 255
            out[m & hatch] = 0
        elif tr == "dots":
            dots = ((xx % 7) < 2) & ((yy % 7) < 2)
            out[m] = 255
            out[m & dots] = 0
        else:  # an explicit colour (spot)
            out[m] = tr
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def make_panel(w, h, draw, seed=0, bg=PAGE, border=6, wobble=0.9, treat=None, raw=False):
    """Render a panel once. `draw(ink, w, h)` paints it; a border is ruled last,
    then the colour sketch is inked (see ink_treat) unless raw=True."""
    ink = Ink(0, 0, (int(w), int(h)), boil=0, wobble=wobble, seed=seed)
    ink.d.rectangle([0, 0, w, h], fill=bg)
    draw(ink, w, h)
    ink.rect(border / 2, border / 2, w - border / 2, h - border / 2, color=INK, width=border, rough=False)
    img = ink.img.convert("RGB")
    return img if raw else ink_treat(img, treat)


def grayscale_frames(film):
    """Wrap a Film so every finished frame is black and white (the pages are ink only)."""
    base = film.frame

    def frame(k):
        return base(k).convert("L").convert("RGB")

    film.frame = frame
    return film


def art_id(img):
    return hashlib.sha1(img.tobytes()).hexdigest()[:10]


class Board:
    """A page lying on a dark table, with margin so the camera can roam."""

    def __init__(self, pw, ph, margin=200, ground=BOARD, paper=WHITE):
        self.pw, self.ph, self.m = pw, ph, margin
        self.img = Image.new("RGB", (pw + 2 * margin, ph + 2 * margin), ground)
        sh = Image.new("L", self.img.size, 0)
        ImageDraw.Draw(sh).rectangle([margin + 14, margin + 18, margin + pw + 14, margin + ph + 18], fill=150)
        sh = sh.filter(ImageFilter.GaussianBlur(18))
        self.img.paste(Image.new("RGB", self.img.size, (20, 18, 18)), (0, 0), sh)
        ImageDraw.Draw(self.img).rectangle([margin, margin, margin + pw, margin + ph], fill=paper)

    def place(self, img, x, y):
        self.img.paste(img, (int(self.m + x), int(self.m + y)))
        return (self.m + x, self.m + y, self.m + x + img.width, self.m + y + img.height)

    def r(self, x0, y0, x1, y1):
        return (self.m + x0, self.m + y0, self.m + x1, self.m + y1)

    def page(self):
        return (self.m, self.m, self.m + self.pw, self.m + self.ph)

    def ink(self):
        k = Ink(0, 0, self.img.size, boil=0, wobble=0.8, seed=99)
        k.img = self.img
        k.d = ImageDraw.Draw(self.img, "RGBA")
        return k


# ------------------------------------------------------------- camera ---

def fit_box(rect, pad=0.05, aspect=W / H):
    x0, y0, x1, y1 = rect
    w, h = (x1 - x0), (y1 - y0)
    w += 2 * pad * max(w, h * aspect)
    h += 2 * pad * max(h, w / aspect)
    if w / h > aspect:
        h = w / aspect
    else:
        w = h * aspect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def clamp_box(box, size):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w > size[0] or h > size[1]:
        k = min(size[0] / w, size[1] / h)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        w, h = w * k, h * k
        x0, y0 = cx - w / 2, cy - h / 2
    x0 = min(max(0, x0), size[0] - w)
    y0 = min(max(0, y0), size[1] - h)
    return (x0, y0, x0 + w, y0 + h)


def view(img, box, size=(W, H)):
    box = clamp_box(box, img.size)
    return img.resize(size, Image.BILINEAR, box=box)


def lerp_box(a, b, x):
    # interpolate centre linearly, size geometrically (smoother zoom)
    ca = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
    cb = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
    wa, wb = a[2] - a[0], b[2] - b[0]
    w = wa * (wb / wa) ** x
    h = w * (a[3] - a[1]) / wa
    cx, cy = lerp(ca[0], cb[0], x), lerp(ca[1], cb[1], x)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


class Shots:
    """Camera script: a list of (duration, box) holds joined by eased moves.

    add(box, hold, move): move `move` seconds from the previous box, then hold."""

    def __init__(self, start=0.0):
        self.keys = []  # (t0, t1, box_from, box_to)
        self.t = start
        self.last = None
        self.marks = []

    def add(self, box, hold=2.0, move=0.7, tag=None):
        if self.last is not None and move > 0:
            self.keys.append((self.t, self.t + move, self.last, box))
            self.t += move
        self.marks.append((self.t, tag))
        self.keys.append((self.t, self.t + hold, box, box))
        self.t += hold
        self.last = box
        return self.t

    def at(self, t):
        for a, b, p, q in self.keys:
            if a <= t < b:
                return p if p is q else lerp_box(p, q, smooth((t - a) / (b - a)))
        return self.keys[-1][3] if t >= self.keys[-1][1] else self.keys[0][2]

    def tag_at(self, t):
        cur = None
        for a, tag in self.marks:
            if t >= a:
                cur = tag
        return cur


def page_turn(a, b, x):
    """Leaf turns about the left edge: front of `a`, then its blank back, revealing `b`."""
    x = clamp(x)
    out = b.copy()
    cw = abs(math.cos(math.pi * x))
    lw = max(1, int(W * cw))
    d = ImageDraw.Draw(out, "RGBA")
    # shadow cast on b
    for k in range(40):
        d.line([(lw + k, 0), (lw + k, H)], fill=(0, 0, 0, int(90 * (1 - k / 40) * (1 - cw * 0.5))))
    if x < 0.5:
        leaf = a.resize((lw, H), Image.BILINEAR)
        shade = Image.new("RGB", (lw, H), (0, 0, 0))
        leaf = Image.blend(leaf, shade, 0.35 * (1 - cw))
    else:
        leaf = Image.new("RGB", (lw, H), mix_color(PAGE, (180, 170, 150), 1 - cw))
    out.paste(leaf, (0, 0))
    return out


def voice(mix, at, text, pitch=140, pan=0.0, gain=0.07, seed=None):
    """Murmur under a balloon, length from the text. Same seed = identical clip."""
    dur = clamp(0.055 * len(text) + 0.3, 0.5, 2.6)
    if seed is None:
        seed = int(hashlib.md5(text.encode()).hexdigest()[:6], 16)
    mix.murmur(at, dur, gain=gain, pitch=pitch, pan=pan, seed=seed)
    return dur


def path_overlay(ink, pts, color=ACCENT, width=6, dots=True, numbers=True, alpha=230, size=22, upto=None):
    pts = pts if upto is None else pts[:upto]
    if len(pts) >= 2:
        ink.line(pts, color, width, rough=False, alpha=alpha)
    if dots:
        for k, (x, y) in enumerate(pts):
            ink.circle(x, y, size * 0.8, fill=color, color=PAGE, width=3, rough=False, alpha=alpha)
            if numbers:
                ink.d.text((x, y), str(k + 1), font=lfont(size, "Bold"), fill=PAGE, anchor="mm")
