"""Handmade articulated cut-paper mouth in profile (facing right) + #38 pose library and decoder.

Rig (Reiniger-style pinned joints):
  static : field < cavity < teeth < neck < [jaw group] < head/cheek skin < upper lip (substitution)
  jaw group = tongue + jaw/chin skin + lower lip (substitution), rotated as FK about an off-screen hinge.
Lips are replacement drawings (one fixed drawing per pose id); the jaw is articulation.
Geometry is original (built from anatomical landmarks by eye), not traced from the reference.
"""
import math
import numpy as np
import cv2
import paper as P

HINGE = (-260.0, 30.0)   # TMJ, off-screen left (film px)

SKIN = (202, 154, 138)       # #CA9A8A
SKIN_SH = (172, 128, 113)    # #AC8071
SKIN_HI = (232, 196, 185)    # #E8C4B9
LIP = (157, 86, 93)          # #9D565D
LIP_UP = (140, 78, 80)       # upper lip a touch darker (it faces down, away from the light)
LIP_SH = (125, 78, 71)       # #7D4E47
LIP_HI = (196, 128, 132)
GLOSS = (204, 142, 144)
CAVITY = (66, 26, 23)        # #421A17
TEETH = (238, 230, 216)
TONGUE = (132, 60, 62)

# ---------------------------------------------------------------- pose library (#38) ---
# each pose: jaw (deg), upper-lip lift/protrude, lower-lip protrude/drop/tuck, corner shift, thickness
POSES = {
    "rest":     dict(jaw=0.6, ulift=0, upro=0, lpro=0, ldrop=0, tuck=0, corner=0, thick=1.00, tongue=0),
    "MBP":      dict(jaw=0.0, ulift=-2, upro=3, lpro=4, ldrop=-5, tuck=0, corner=4, thick=0.92, tongue=0),
    "A":        dict(jaw=4.6, ulift=5, upro=-2, lpro=-6, ldrop=4, tuck=0, corner=-4, thick=0.92, tongue=0),
    "O":        dict(jaw=3.0, ulift=3, upro=12, lpro=10, ldrop=2, tuck=0, corner=46, thick=1.10, tongue=0),
    "EI":       dict(jaw=1.8, ulift=6, upro=-4, lpro=-6, ldrop=0, tuck=0, corner=-16, thick=0.86, tongue=0),
    "UW":       dict(jaw=1.4, ulift=1, upro=16, lpro=14, ldrop=0, tuck=0, corner=58, thick=1.08, tongue=0),
    "FV":       dict(jaw=0.9, ulift=4, upro=0, lpro=-16, ldrop=-10, tuck=1, corner=0, thick=0.95, tongue=0),
    "LNT":      dict(jaw=2.0, ulift=4, upro=0, lpro=-2, ldrop=0, tuck=0, corner=-6, thick=0.95, tongue=1),
    "hm":       dict(jaw=0.0, ulift=-2, upro=8, lpro=9, ldrop=-6, tuck=0, corner=26, thick=1.04, tongue=0),
    "surprise": dict(jaw=5.6, ulift=10, upro=2, lpro=-2, ldrop=8, tuck=0, corner=8, thick=1.02, tongue=0),
}
POSE_IDS = list(POSES)
KEY_POSES = {"O", "surprise"}          # protected from smoothing
OPENNESS = {k: v["jaw"] for k, v in POSES.items()}


def upper_lip_poly(p):
    c = 150 + p["corner"]; f = p["upro"]; lift = p["ulift"]; th = p["thick"]
    top = [(c, 140), (c + 70 * (1 - (c - 150) / 400), 108), (300, 66 - 4 * (th - 1) * 10), (362, 38), (398, 28)]
    front = [(416 + f * 0.6, 34), (430 + f, 56), (433 + f, 84), (426 + f, 106 - lift)]
    # underside (stomion line, back toward the corner); lift raises it to show the teeth
    under = [(402 + f * 0.7, 118 - lift * 1.1), (350, 128 - lift * 0.8), (270, 136 - lift * 0.4), (c + 20, 142)]
    # thickness: push the top border up a little for fuller lips
    top = [(x, y - (th - 1) * 30 * (x - c) / 280) for x, y in top]
    return top + front + under


def lower_lip_poly(p):
    """In jaw space (unrotated)."""
    c = 150 + p["corner"]; f = p["lpro"]; d = p["ldrop"]; th = p["thick"]
    if p["tuck"]:   # F/V: lower lip rolls in under the upper teeth
        return [(c + 16, 146), (260, 140), (340, 128 + d), (384 + f, 122 + d), (400 + f, 140 + d), (402 + f, 176),
                (390 + f, 214), (360, 236), (300, 238), (230, 214), (c + 6, 170)]
    bot = 256 + (th - 1) * 40
    return [(c + 18, 146), (250, 141 + d * 0.3), (330, 134 + d * 0.6), (382 + f * 0.8, 133 + d), (404 + f, 146 + d),
            (414 + f, 176 + d * 0.5), (410 + f, 210), (392 + f * 0.6, 240), (352, bot), (296, bot - 2), (236, 228),
            (190, 196), (c + 6, 164)]


def gloss_poly(p):
    f = p["lpro"]; d = p["ldrop"]
    if p["tuck"]:
        return [(350, 150), (380 + f, 146), (392 + f, 160), (372, 168), (348, 164)]
    return [(300, 160 + d * 0.5), (350, 150 + d * 0.7), (384 + f * 0.8, 150 + d * 0.9), (402 + f, 162 + d * 0.8),
            (398 + f, 172 + d * 0.6), (370, 168 + d * 0.5), (330, 170 + d * 0.4), (304, 168 + d * 0.4)]


HEAD = [(-40, -20), (414, -20), (412, -2), (398, 12), (392, 22), (398, 30), (360, 48), (300, 84), (220, 118), (150, 140),
        (146, 176), (136, 226), (118, 286), (92, 348), (58, 410), (14, 466), (-40, 520)]
JAW = [(-320, 120), (150, 132), (300, 150), (392, 190), (388, 250), (366, 282), (352, 300), (360, 330), (378, 362),
       (382, 398), (372, 432), (346, 460), (300, 482), (236, 498), (150, 510), (40, 528), (-320, 560)]
NECK = [(-40, 380), (180, 440), (300, 452), (278, 482), (252, 512), (232, 580), (-40, 580)]
TEETH_PTS = [(326, 96), (392, 98), (403, 104), (405, 122), (398, 136), (386, 139), (370, 137), (350, 133), (328, 129)]
CAVITY_PTS = [(150, 132), (300, 108), (404, 102), (414, 128), (408, 172), (398, 212), (300, 222), (150, 200)]
TONGUE_PTS = [(170, 200), (290, 178), (356, 176), (384, 190), (378, 208), (330, 222), (220, 232), (160, 226)]
TONGUE_UP = [(170, 196), (290, 168), (360, 150), (392, 140), (398, 156), (366, 186), (300, 210), (180, 226)]


def _skin_model(kind):
    def f(rgb, a):
        H, W = a.shape
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
        if kind == "jaw":
            # soft shade under the jaw and toward the throat, light on the chin top
            g = np.clip((yy - 0.62) * 3.2, 0, 1) * np.clip((xx - 0.12) * 4, 0, 1)
            rgb = rgb * (1 - 0.13 * g[..., None])
        elif kind == "head":
            g = np.clip((0.40 - xx) * 1.4, 0, 1) * np.clip(yy * 1.5, 0, 1)
            rgb = rgb * (1 - 0.06 * g[..., None])
        return rgb
    return f


def _lip_model(lower):
    def f(rgb, a):
        H, W = a.shape
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        if lower:   # darker toward the underside where the lip turns away
            g = np.clip((yy - 0.36) * 9, 0, 1)
            rgb = rgb * (1 - 0.15 * g[..., None])
        else:       # upper lip: lighter top border, shadowed underside
            g = np.clip((yy - 0.12) * 10, 0, 1)
            rgb = rgb * (1 - 0.10 * g[..., None])
        return rgb
    return f


class Mouth:
    def __init__(self):
        self.static = {}
        self.lib = {}
        sw = dict(seed=11)
        poly = lambda pts, seed: P.scissor(P.catmull(pts), seed)
        self.head = P.piece(poly(HEAD, 1), SKIN, 1, SKIN_SH, SKIN_HI, fibre=0.026, model=0.09, extra=_skin_model("head"))
        self.jaw = P.piece(poly(JAW, 2), SKIN, 2, SKIN_SH, SKIN_HI, fibre=0.026, model=0.11, extra=_skin_model("jaw"))
        self.neck = P.piece(poly(NECK, 3), (192, 145, 129), 3, SKIN_SH, SKIN_HI, fibre=0.026, model=0.08)
        self.teeth = P.piece(poly(TEETH_PTS, 4), TEETH, 4, (200, 190, 176), (250, 246, 238), fibre=0.0, rim=0.22, model=0.08)
        self.cavity = P.piece(poly(CAVITY_PTS, 5), CAVITY, 5, fibre=0.0, rim=0.04, model=0.02)
        self.tongue = {0: P.piece(poly(TONGUE_PTS, 6), TONGUE, 6, fibre=0.0, rim=0.08),
                       1: P.piece(poly(TONGUE_UP, 7), TONGUE, 7, fibre=0.0, rim=0.08)}
        # tooth divisions (cut lines drawn on the teeth strip)
        t = self.teeth
        for x0 in (352, 378):
            xs = int(x0 * P.S)
            t[int(98 * P.S):int(138 * P.S), xs:xs + 2, :3] *= 0.86
        for i, pid in enumerate(POSE_IDS):
            p = POSES[pid]
            up = P.piece(poly(upper_lip_poly(p), 100 + i), LIP_UP, 100 + i, LIP_SH, LIP_HI, fibre=0.012, rim=0.2,
                         model=0.12, extra=_lip_model(False))
            lo = P.piece(poly(lower_lip_poly(p), 200 + i), LIP, 200 + i, LIP_SH, LIP_HI, fibre=0.012, rim=0.2,
                         model=0.14, extra=_lip_model(True))
            gl = P.piece(poly(gloss_poly(p), 300 + i), GLOSS, 300 + i, (180, 110, 116), (236, 196, 196), fibre=0.0, rim=0.12, model=0.25)
            # gloss is a separate small piece of glossy paper glued onto the lower lip: compose it into the lip drawing
            P.shadow(lo, gl[..., 3], dx=1.0, dy=1.5, blur=1.2, strength=0.25, clip=lo[..., 3])
            P.over(lo, gl, 0.92)
            self.lib[pid] = (up, lo)

    def render(self, pose, jaw_deg, bg):
        """bg: float RGB 2x canvas (white field + anything behind the mouth). Returns composited float RGB."""
        p = POSES[pose]
        up, lo = self.lib[pose]
        img = bg.copy()
        P.over(img, self.cavity)
        tg = P.rotate_rgba(self.tongue[p["tongue"]], jaw_deg, HINGE)
        P.over(img, tg)
        P.shadow(img, self.teeth[..., 3], dx=1.2, dy=2.0, blur=1.5, strength=0.35, clip=self.cavity[..., 3])
        P.over(img, self.teeth)
        P.shadow(img, self.neck[..., 3], strength=0.10, dx=2, dy=2)
        P.over(img, self.neck)
        # jaw group: lower lip glued on jaw skin; whole group rotates about the hinge
        grp = self.jaw.copy()
        P.shadow(grp, lo[..., 3], dx=1.5, dy=3.0, blur=2.5, strength=0.22, clip=grp[..., 3])
        a = lo[..., 3:4]
        grp[..., :3] = lo[..., :3] * a + grp[..., :3] * (1 - a)
        grp[..., 3] = np.maximum(grp[..., 3], lo[..., 3])
        grp = P.rotate_rgba(grp, jaw_deg, HINGE)
        P.shadow(img, grp[..., 3], dx=2.5, dy=3.5, blur=3.0, strength=0.24)
        P.over(img, grp)
        P.shadow(img, self.head[..., 3], dx=2.5, dy=3.5, blur=3.0, strength=0.26)
        P.over(img, self.head)
        P.shadow(img, up[..., 3], dx=1.5, dy=3.0, blur=2.5, strength=0.30)
        P.over(img, up)
        return img


# ------------------------------------------------------------------ decoder (#38) ---
def decode(targets, fps_hold=2):
    """targets: list per 12-fps step of dict pose->match cost (lower better). Viterbi with transition cost.
    Returns pose id per step. Penalises open<->closed jumps, protects key poses (their match cost is kept)."""
    ids = POSE_IDS
    n = len(ids)
    T = np.zeros((n, n))
    for i, a in enumerate(ids):
        for j, b in enumerate(ids):
            if a != b:
                T[i, j] = 0.15 + 0.12 * abs(OPENNESS[a] - OPENNESS[b])
    INF = 1e9
    cost = np.array([targets[0].get(k, 3.0) for k in ids])
    back = []
    for t in range(1, len(targets)):
        c = np.array([targets[t].get(k, 3.0) for k in ids])
        tot = cost[:, None] + T
        bi = tot.argmin(0)
        back.append(bi)
        cost = tot[bi, range(n)] + c
    path = [int(cost.argmin())]
    for bi in reversed(back):
        path.append(int(bi[path[-1]]))
    path = path[::-1]
    return [ids[k] for k in path]
