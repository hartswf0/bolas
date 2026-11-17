"""Direction 1 - Ombres de la boucle: articulated cut-paper silhouette puppets
(Reiniger, SCION 2) on the loop page. Every figure is an FK rig (SCION 32) whose
parts are cut polygons; a pose is a set of joint angles, and a frame is drawn
fresh from those angles. The keyframe is t = 31 s: the hinge, pose 7 of 12.

Run: python3 -I kf1.py   (writes kf-1.png next to this file)
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kf_common import (INK, PAPER, SEQ, TEXT, W, H, balloon, frame_panel, layout, note_prop,
                       page_furniture, panel_ids)

SS = 3
HERE = os.path.dirname(os.path.abspath(__file__))


def rot(p, a, o=(0, 0)):
    c, s = math.cos(a), math.sin(a)
    x, y = p[0] - o[0], p[1] - o[1]
    return (o[0] + x * c - y * s, o[1] + x * s + y * c)


class Rig:
    """A cut-paper puppet: parts are polygons in parent space, pinned at joints."""

    def __init__(self, d, ox, oy, s, facing):
        self.d, self.ox, self.oy, self.s, self.f = d, ox, oy, s, facing

    def P(self, pts):
        return [(self.ox + self.f * x * self.s, self.oy + y * self.s) for x, y in pts]

    def poly(self, pts, fill=255):
        self.d.polygon(self.P(pts), fill=fill)

    def limb(self, root, segs, widths, hand=None, fill=255):
        """FK chain: segs = [(length, angle_deg_from_down)], cumulative. Returns joint list."""
        joints = [root]
        a = 0.0
        x, y = root
        for (L, ang) in segs:
            a += math.radians(ang)
            x, y = x + L * math.sin(a), y + L * math.cos(a)
            joints.append((x, y))
        for i in range(len(segs)):
            (x0, y0), (x1, y1) = joints[i], joints[i + 1]
            w0, w1 = widths[i], widths[i + 1]
            dx, dy = x1 - x0, y1 - y0
            n = math.hypot(dx, dy) or 1
            nx, ny = -dy / n, dx / n
            self.poly([(x0 + nx * w0, y0 + ny * w0), (x1 + nx * w1, y1 + ny * w1),
                       (x1 - nx * w1, y1 - ny * w1), (x0 - nx * w0, y0 - ny * w0)], fill)
            self.disc(joints[i], w0, fill)
        self.disc(joints[-1], widths[-1], fill)
        if hand:
            hx, hy = joints[-1]
            hp = [rot((hx + px, hy + py), a, (hx, hy)) for px, py in hand]
            self.poly(hp, fill)
        return joints, a

    def disc(self, c, r, fill=255):
        (x, y), = self.P([c])
        r *= self.s
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


MITTEN = [(-2.2, -0.5), (2.2, -0.5), (2.6, 3.2), (1.4, 5.0), (-0.8, 5.2), (-2.4, 3.6)]
POINT = [(-2.0, -0.5), (2.0, -0.5), (2.2, 2.8), (0.8, 9.0), (-0.2, 9.0), (-0.4, 4.0), (-2.4, 3.4)]
OPEN = [(-2.4, -0.5), (2.4, -0.5), (3.6, 5.6), (1.6, 6.4), (0.4, 3.6), (-0.8, 6.6), (-2.6, 5.0)]


def gustave(d, ox, oy, s, pose, cut):
    """Stout man, bald, big nose, facing +x. pose: dict of joint angles (deg)."""
    r = Rig(d, ox, oy, s, 1)
    lean = math.radians(pose.get("lean", 0))
    hip = (0, -44)
    # back arm first (behind body)
    sh_b = rot((-2, -76), lean, hip)
    r.limb(sh_b, [(17, pose["b_sh"]), (15, pose["b_el"])], [4.2, 3.6, 2.8], pose.get("b_hand", MITTEN))
    # legs
    r.poly([(-14, -46), (-3, -46), (-5, 0), (-16, 0), (-15, -20)])
    r.poly([(-1, -46), (12, -46), (14, -20), (13, 0), (2, 0)])
    r.poly([(-18, 0), (-3, 0), (-3, 2.5), (-19, 2.5)])
    r.poly([(1, 0), (19, 0), (20, 2.5), (1, 2.5)])
    # torso: coat with belly, rotated about hip by lean
    torso = [(-17, -46), (-19, -60), (-15, -76), (-6, -82), (6, -82), (16, -74), (25, -60), (24, -48), (14, -40), (-8, -38)]
    r.poly([rot(p, lean, hip) for p in torso])
    # head on neck pivot
    neck = rot((3, -82), lean, hip)
    ht = math.radians(pose.get("head", 0)) + lean
    head = [(-8, 2), (-11, -6), (-12, -14), (-9, -21), (-3, -25), (4, -25), (9, -22), (11, -17), (12, -14),
            (13, -12.5), (16, -12.5), (21, -11.5), (24, -8), (23, -4), (19, -2.6), (15.5, -3.6), (17, -1.2),
            (14, 0.2), (11.5, 0.6), (12.5, 3), (8, 5.5), (2, 5.5)]
    T = lambda pts: [rot((neck[0] + x, neck[1] + y), ht, neck) for x, y in pts]
    r.poly(T(head))
    for tuft in ([(-4, -24), (-6, -29), (-1, -25.5)], [(0, -25), (1, -30.5), (3, -25)], [(3, -24.5), (7, -28), (6.5, -23)]):
        r.poly(T(tuft))
    # cut-outs: spectacles ring, eye slit, ear, coat buttons (Reiniger's internal slits, not texture)
    eye = T([(8.5, -13.5)])[0]
    r.disc(eye, 3.4, 0)
    r.disc(eye, 2.5, 255)
    r.poly([(eye[0] - 1.4, eye[1]), (eye[0], eye[1] - 0.7), (eye[0] + 1.3, eye[1]), (eye[0], eye[1] + 0.6)], 0)
    r.poly(T([(4.9, -13.8), (5.2, -13.0), (-1.5, -12.2), (-1.5, -13.2)]), 0)
    r.poly(T([(-3.5, -12), (-1.6, -10.5), (-2.2, -7), (-4.2, -8.5)]), 0)
    for by in (-72, -64, -56):
        b = rot((17 + (by + 72) * 0.25, by), lean, hip)
        r.disc(b, 0.9, 0)
    # front arm
    sh_f = rot((6, -76), lean, hip)
    j, a = r.limb(sh_f, [(17, pose["f_sh"]), (15, pose["f_el"])], [4.4, 3.8, 3.0], pose.get("f_hand", MITTEN))
    return j


def odette(d, ox, oy, s, pose, cut):
    """Woman with a bun and a bell skirt, facing -x."""
    r = Rig(d, ox, oy, s, -1)
    lean = math.radians(pose.get("lean", 0))
    waist = (0, -52)
    sh_b = rot((-1, -78), lean, waist)
    jb, _ = r.limb(sh_b, [(15, pose["b_sh"]), (14, pose["b_el"])], [3.0, 2.4, 1.9], pose.get("b_hand", MITTEN))
    skirt = [(-6, -52), (6, -52), (10, -30), (17, -6), (19, 0), (-15, 0), (-13, -8), (-9, -30)]
    r.poly(skirt)
    # scalloped hem cut-outs
    for k in range(7):
        r.disc((-12 + k * 4.6, -3.2), 1.0, 0)
    bodice = [(-6, -52), (-7, -64), (-6, -76), (-2, -81), (3, -81), (7, -76), (8, -64), (6, -52)]
    r.poly([rot(p, lean, waist) for p in bodice])
    neck = rot((1, -81), lean, waist)
    ht = math.radians(pose.get("head", 0)) + lean
    head = [(-3, 2), (-6, -4), (-7.5, -11), (-6, -17), (-1, -21.5), (5, -21.5), (8.5, -18), (9.5, -14),
            (10, -12), (12, -10.5), (14.5, -8), (11, -7.6), (11, -5.6), (9.6, -5), (10.2, -3.4), (8.6, -2.6),
            (8, -0.4), (5, 2), (2, 3.5)]
    T = lambda pts: [rot((neck[0] + 1.18 * x, neck[1] + 1.18 * y), ht, neck) for x, y in pts]
    r.poly(T(head))
    bun = T([(-6.5, -21)])[0]
    r.disc(bun, 5.4)
    r.poly(T([(-9, -16), (-13, -9), (-11, -8), (-8, -13)]))  # a loose curl
    eye = T([(6, -12.5)])[0]
    r.poly([(eye[0] - 1.6, eye[1]), (eye[0], eye[1] - 0.9), (eye[0] + 1.6, eye[1]), (eye[0], eye[1] + 0.7)], 0)
    r.poly(T([(3.2, -15.6), (8, -16.6), (8, -15.8), (3.2, -14.9)]), 0)
    # lace collar slits
    for k in range(4):
        c = rot((-3 + k * 2.6, -75), lean, waist)
        r.disc(c, 0.7, 0)
    sh_f = rot((3, -77), lean, waist)
    j, a = r.limb(sh_f, [(15, pose["f_sh"]), (14, pose["f_el"])], [3.4, 2.6, 2.0], pose.get("f_hand", MITTEN))
    return {"f": j, "b": jb}, a


# joint angles: degrees from straight down, positive swings toward the figure's facing
POSES = {
    "A": dict(g=dict(f_sh=12, f_el=48, b_sh=-8, b_el=10, lean=-3, head=-4),
              o=dict(f_sh=108, f_el=46, b_sh=-30, b_el=-80, lean=6, head=6, note="back", hand="f")),
    "B": dict(g=dict(f_sh=66, f_el=64, b_sh=-64, b_el=-64, lean=-7, head=-12, f_hand=OPEN, b_hand=OPEN),
              o=dict(f_sh=22, f_el=56, b_sh=-30, b_el=-80, lean=-2, head=8, note="back", hand="f")),
    "C": dict(g=dict(f_sh=20, f_el=30, b_sh=-14, b_el=12, lean=-10, head=-8),
              o=dict(f_sh=96, f_el=-4, b_sh=-18, b_el=-50, lean=12, head=-2, f_hand=POINT, note="back", hand="b")),
    # hinge, pose 7 of 12: he points at the face of the note she holds out; she recoils
    "H": dict(g=dict(f_sh=88, f_el=4, b_sh=-10, b_el=24, lean=9, head=10, f_hand=POINT),
              o=dict(f_sh=70, f_el=24, b_sh=64, b_el=118, lean=-11, head=-16, note="face", hand="f")),
}


def backlight(w, h, seed):
    """The lit paper behind the puppets: a soft pool, light falling off to the frame."""
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.42
    r = np.sqrt(((xx - cx) / (w * 0.75)) ** 2 + ((yy - cy) / (h * 0.9)) ** 2)
    v = 253 - 44 * np.clip(r, 0, 1) ** 1.6
    rs = np.random.RandomState(seed)
    fib = rs.normal(0, 1.6, (h // 3 + 1, w // 3 + 1)).astype(np.float32)
    fib = np.asarray(Image.fromarray(fib).resize((w, h), Image.BICUBIC))
    return np.clip(v + fib, 0, 255).astype(np.uint8)


def props(d, w, h, s, key):
    """Black cut-paper set: floor strip, table with lamp, window frame."""
    S = s
    d.rectangle([0, h - 10 * S, w, h], fill=255)
    # table at the back between them
    tx = w * 0.5
    d.rectangle([tx - 16 * S, h - 30 * S, tx + 16 * S, h - 27 * S], fill=255)
    d.rectangle([tx - 14 * S, h - 27 * S, tx - 12 * S, h], fill=255)
    d.rectangle([tx + 12 * S, h - 27 * S, tx + 14 * S, h], fill=255)
    d.polygon([(tx - 4 * S, h - 30 * S), (tx - 2.5 * S, h - 40 * S), (tx + 2.5 * S, h - 40 * S), (tx + 4 * S, h - 30 * S)], fill=255)
    # hanging lamp from the top
    d.line([(tx, 0), (tx, 16 * S)], fill=255, width=max(2, int(S // 2)))
    d.polygon([(tx - 8 * S, 24 * S), (tx + 8 * S, 24 * S), (tx + 3 * S, 16 * S), (tx - 3 * S, 16 * S)], fill=255)


def render_panel(key, w, h, seed, wide=False):
    """One panel at SS, returns RGB image (w, h)."""
    Wp, Hp = w * SS, h * SS
    bg = Image.fromarray(backlight(Wp, Hp, seed)).convert("RGB")
    m = Image.new("L", (Wp, Hp), 0)
    d = ImageDraw.Draw(m)
    s = (h / 104.0) * SS  # puppet unit in px: knees-up framing, heads near the top third
    floor = Hp + 30 * s
    props(d, Wp, Hp, s, key)
    pose = POSES[key]
    gx = Wp * (0.40 if wide else 0.27)
    ox = Wp * (0.61 if wide else 0.77)
    gustave(d, gx, floor, s, pose["g"], 0)
    oj, oa = odette(d, ox, floor, s, pose["o"], 0)
    # ink the silhouettes
    bg.paste(Image.new("RGB", bg.size, INK), (0, 0), m)
    # the note in Odette's hand: white paper, the only lit object in black hands
    op = pose["o"]
    hand_j = oj[op.get("hand", "f")][-1]
    hx, hy = ox - hand_j[0] * s, floor + hand_j[1] * s
    if op["note"] == "face":
        nw, nh = int(52 * s / SS), int(35 * s / SS)
        n = note_prop(nw, nh, face=True, seed=7)
        n = n.resize((nw * SS, nh * SS), Image.LANCZOS).rotate(6, expand=True, resample=Image.BICUBIC)
        bg.paste(n, (int(hx - n.width * 0.55), int(hy - n.height * 0.85)), n)
        # her fingers over the card edge (cut paper, in front)
        d2 = ImageDraw.Draw(bg)
        d2.ellipse([hx - 2.6 * s, hy - 3 * s, hx + 2.6 * s, hy + 2 * s], fill=INK)
    else:
        nw, nh = int(13 * s / SS), int(9 * s / SS)
        n = note_prop(nw, nh, face=False)
        n = n.resize((nw * SS, nh * SS), Image.LANCZOS).rotate(-14, expand=True, resample=Image.BICUBIC)
        bg.paste(n, (int(hx - n.width * 0.5), int(hy - n.height * 0.95)), n)
    return bg.resize((w, h), Image.LANCZOS)


def main(out=os.path.join(HERE, "kf-1.png")):
    img = Image.new("RGB", (W, H), PAPER)
    rects = layout()
    cache = {}
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        w, h = x1 - x0, y1 - y0
        key = (k, w, h)
        if key not in cache:  # immutable art: one drawing per letter, reused for its pair
            cache[key] = render_panel(k, w, h, seed=ord(k), wide=(k == "H"))
        p = cache[key]
        if i > 3:  # not yet reached at t = 31 s: the pair waits as a pale ghost
            p = Image.blend(Image.new("RGB", p.size, PAPER), p, 0.2)
        img.paste(p, (x0, y0))
    # balloons (immutable lettering, same seed for each pair)
    tails = {"A": (0.74, 0.62, 0.36), "B": (0.36, 0.40, 0.32), "C": (0.70, 0.66, 0.36), "H": (0.42, 0.30, 0.30)}
    for i, k in enumerate(SEQ):
        x0, y0, x1, y1 = rects[i]
        w, h = x1 - x0, y1 - y0
        bx, by, ty = tails[k]
        cx = x0 + w * {"A": 0.55, "B": 0.42, "C": 0.58, "H": 0.22}[k]
        tail = (x0 + w * bx, y0 + h * ty)
        if i <= 3:
            balloon(img, cx, y0 + 40, k, cap=11 if k != "H" else 12, maxw=220 if k != "H" else 250, tail=tail)
        else:
            balloon(img, cx, y0 + 40, k, cap=11, maxw=220, tail=tail, alpha=70, color=(150, 150, 150))
    for i in range(7):
        frame_panel(img, rects[i], seed=i, width=3 if i != 3 else 4)
    page_furniture(img)
    panel_ids(img, rects)
    img.save(out)
    return out


if __name__ == "__main__":
    print(main())
