# Handmade grey-card puppets A, B, C (r3, performance unit).  Reuses the approved test-shot card primitives
# (test-shot-build/shot.py: lay / pencil / brad / capsule, the CC0 cardboard scan as card face, the charcoal-mud
# field) and re-models the figures:
#   - 20+ cut pieces per puppet, split pins at every joint, sleeve breaks and cloth folds pencilled on the card,
#   - pencil faces with expression channels (gaze -> iris + lid, brow -> raised/knit brows, mouth -> open card slot),
#   - B: wet loose hair as 14 separate cut strands, each a 3-link chain with spring-damper follow-through (#41),
#   - C: headband with a two-row pencilled pattern and knot tails; A: hat with crown band and dented brim,
#   - charcoal mud deposit darker in creases (cut edges, elbows, knees), sweat specular pass L200-225 on brow,
#     cheek, nose and knuckles, an overcast top light on the card tones (upper pieces lifted, lower pieces lower).
import sys, math
from pathlib import Path
import numpy as np, cv2
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "test-shot-build"))
sys.path.insert(0, str(HERE))
import shot as S  # noqa: E402  (approved r2 material: card scan, mud, planes, shoe cutout)
from rig import fk, BONES  # noqa: E402

pencil, brad, capsule, gblur, over = S.pencil, S.brad, S.capsule, S.gblur, S.over


def lay(C, polys, tone, mud=0.0, seed=0, shadow=4, **kw):
    """S.lay, guarded for pieces cropped to a sliver by the frame edge (its drop shadow cannot be offset there)."""
    try:
        S.lay(C, polys, tone, mud, seed, shadow, **kw)
    except ValueError:
        S.lay(C, polys, tone, mud, seed, 0, **kw)
bpoly, bframe, tube = S.bpoly, S.bframe, S.tube
HEAD, NECK, BOOT, HAND = S.HEAD, S.NECK, S.BOOT, S.HAND
HEAD_SCALE = 1.22

# card tones lifted toward the reference's bright wet middle (p75 ~ 160, ~6 % above L200)
TONES = {
    "B": dict(shirt=206, collar=220, skin=196, leg=100, boot=56, hair=224, hairline=128),
    "C": dict(shirt=118, collar=134, skin=176, leg=70, boot=46, hair=50, hairline=30, band=206),
    "A": dict(shirt=150, collar=166, skin=164, leg=62, boot=42, hair=52, hairline=30, hat=96),
}
SEED = {"A": 100, "B": 200, "C": 300}


def toplight(y, top, bot):
    """overcast top light: +7 % at the top of the figure, -7 % at its feet (a property of the lighting, not a grade)."""
    q = min(max((y - top) / max(bot - top, 1), 0), 1)
    return 1.07 - 0.14 * q


# ------------------------------------------------------------------ #41 secondary dynamics: wet hair strands
class HairSim:
    """14 strands x 3 links. Each link angle follows a target (rest angle relative to the head, pulled toward
    gravity because the hair is wet and heavy) through a damped spring; the head's angular velocity and the root's
    acceleration are the only impulses, so all motion decays once the head stops. Stepped on twos (12/s)."""
    def __init__(self, n=14, k=60.0, c=11.0):
        self.n, self.k, self.c = n, k, c
        self.a = None; self.w = None; self.prev = None

    def rest(self, head_ang):
        out = []
        for i in range(self.n):
            base = head_ang + 180 + 12 + 4.5 * i          # hang behind the head (facing right): down and back
            out.append([base + 10 * j for j in range(3)])
        return out

    def step(self, head_ang, root, dt=1 / 12):
        R = self.rest(head_ang)
        if self.a is None:
            self.a = [[self._target(r) for r in row] for row in R]; self.w = [[0.0] * 3 for _ in R]
            self.prev = (head_ang, root, (0.0, 0.0)); return self.a
        ph, pr, pv = self.prev
        om = ((head_ang - ph + 180) % 360 - 180) / dt
        v = ((root[0] - pr[0]) / dt, (root[1] - pr[1]) / dt)
        acc = ((v[0] - pv[0]) / dt, (v[1] - pv[1]) / dt)
        for i, row in enumerate(R):
            for j, r in enumerate(row):
                tgt = self._target(r)
                a = self.a[i][j]
                d = (tgt - a + 180) % 360 - 180
                imp = -0.55 * om * (j + 1) / 3 - 0.004 * acc[0] * (j + 1)
                self.w[i][j] += (self.k * d - self.c * self.w[i][j] + imp * 0.6) * dt
                self.a[i][j] = a + self.w[i][j] * dt
        self.prev = (head_ang, root, v)
        return self.a

    @staticmethod
    def _target(r):
        d = (90 - r + 180) % 360 - 180            # pull toward hanging (wet hair is heavy)
        return r + 0.72 * d


def draw_hair_strands(C, H, s, angs, tone, seed, sweat=True):
    """cut strands: each a tapering card sliver hinged at the scalp, laid as separate pieces."""
    for i, row in enumerate(angs):
        q = 2 - 1.5 * i
        p = H(q, 20 - max(0, -q - 6) * 0.9)
        L = (9.5 + 2.5 * ((i * 7) % 3)) * s
        pts_l, pts_r = [], []
        w0 = (2.6 - 0.05 * i) * s
        cur = p
        for j, a in enumerate(row):
            w = w0 * (1 - 0.3 * j)
            nx, ny = -math.sin(math.radians(a)), math.cos(math.radians(a))
            pts_l.append((cur[0] + nx * w, cur[1] + ny * w)); pts_r.append((cur[0] - nx * w, cur[1] - ny * w))
            cur = (cur[0] + L * math.cos(math.radians(a)), cur[1] + L * math.sin(math.radians(a)))
        poly = pts_l + [cur] + pts_r[::-1]
        tn = tone * (0.84 + 0.12 * ((i * 5) % 3) / 2)
        sw = [((pts_l[0][0] + cur[0]) / 2, (pts_l[0][1] + cur[1]) / 2, 0.5 * s, 2.2 * s, row[1] - 90, 224)] if sweat and i % 3 == 0 else []
        lay(C, [poly], tn, 0.25, seed + i, max(1, int(s * .7)), sweat=sw, edge=0.55)


# ------------------------------------------------------------------ the figure
def draw_figure(C, J, s, who, facing=1, mud=1.0, gaze=0.0, brow=0.0, mouth=0.0, hair=None,
                between_cb=None, front_hand_cb=None, after_head_cb=None, contact=None, light=(None, None)):
    T = dict(TONES[who]); sd = SEED[who]
    shd = max(2, int(1.2 * s + 1))
    top, bot = light
    if top is None:
        ys = [p[1] for b in J.values() for p in (b[0], b[1])]; top, bot = min(ys), max(ys)
    Lt = lambda b: toplight((J[b][0][1] + J[b][1][1]) / 2, top, bot)
    if contact: S.soft_shadow(C, *contact)
    sl = .62 if who == "B" else 1.0
    # ---- far side (a second card a tone down)
    lay(C, [bpoly(J, "thigh_f", tube(-.08, 1.02, 15, 12), s, facing)], T["leg"] * .8 * Lt("thigh_f"), mud * 1.2, sd + 1, shd)
    lay(C, [bpoly(J, "shin_f", tube(0, 1.0, 11.5, 8.5), s, facing)], T["leg"] * .8 * Lt("shin_f"), mud * 1.6, sd + 2, shd)
    lay(C, [bpoly(J, "foot_f", BOOT, s, facing)], T["boot"] * .85, mud, sd + 3, shd)
    lay(C, [bpoly(J, "upper_f", tube(-.15, sl, 11, 9.5), s, facing)], T["shirt"] * .82 * Lt("upper_f"), mud, sd + 4, shd)
    lay(C, [bpoly(J, "fore_f", tube(-.1, 1.02, 7.5, 5.8) if who == "B" else tube(-.1, .95, 9, 7.5), s, facing)],
        (T["skin"] if who == "B" else T["shirt"]) * .82 * Lt("fore_f"), mud * 1.2, sd + 5, shd)
    p0, Lh, (ux, uy), _ = bframe(J, "hand_f")
    lay(C, [bpoly(J, "hand_f", HAND, s, facing)], T["skin"] * .86, mud * 1.7, sd + 6, shd,
        sweat=[(p0[0] + ux * Lh * .9, p0[1] + uy * Lh * .9, 2.2 * s, 0.7 * s, math.degrees(math.atan2(uy, ux)), 208)])
    if between_cb: between_cb(C)
    # ---- torso
    if who == "B":
        tor = [(0.02, -19), (0.0, 16), (0.25, 17), (0.5, 21.5), (0.66, 23), (0.8, 20), (0.93, 14), (1.02, 7),
               (1.05, -2), (1.03, -12), (0.95, -19.5), (0.6, -20.5), (0.3, -20)]
    else:
        tor = [(0.02, -21), (0.0, 19), (0.3, 20), (0.6, 21), (0.85, 20), (1.0, 14), (1.06, 4), (1.05, -8),
               (1.0, -19), (0.85, -24), (0.5, -23), (0.2, -22)]
    lay(C, [bpoly(J, "spine", tor, s, facing)], T["shirt"] * Lt("spine"), mud * 1.1, sd + 7, shd + 1,
        smudges=[(*bpoly(J, "spine", [(0.42, 8)], s, facing)[0], 9 * s, 5 * s, 30, 0.38),
                 (*bpoly(J, "spine", [(0.78, -10)], s, facing)[0], 7 * s, 4 * s, -20, 0.32),
                 (*bpoly(J, "spine", [(0.2, -14)], s, facing)[0], 6 * s, 9 * s, 10, 0.30)],
        sweat=[(*bpoly(J, "spine", [(0.72, 12)], s, facing)[0], 4 * s, 1.0 * s, 70, 212)])
    pencil(C, bpoly(J, "spine", [(0.1, 15), (0.5, 17.5 if who == "B" else 17), (0.94, 10)], s, facing), max(1.5, s * .6), 70, .6, sd)
    if who != "B":
        pencil(C, bpoly(J, "spine", [(0.66, 1), (0.66, 10), (0.52, 10), (0.52, 1), (0.66, 1)], s, facing), max(1, s * .4), 95, .45, sd + 1)
    for k in range(4):   # cloth folds: drag lines from the belt up toward the far shoulder, plus a sweat-dark patch crease
        u = 0.16 + 0.16 * k
        pencil(C, bpoly(J, "spine", [(u, -16), (u + 0.05, -9), (u + 0.1, -4)], s, facing), max(1, s * .45), 92, .5, sd + 2 + k)
    pencil(C, bpoly(J, "spine", [(0.55, 4), (0.62, 9), (0.74, 11)], s, facing), max(1, s * .4), 100, .4, sd + 9)
    lay(C, [bpoly(J, "spine", [(0.86, 4), (1.06, 13), (1.02, -1)], s, facing),
            bpoly(J, "spine", [(0.9, -6), (1.07, -13), (1.04, 1)], s, facing)], T["collar"], mud * .6, sd + 8, 2)
    for k in range(3):
        bx, by = bpoly(J, "spine", [(0.36 + 0.17 * k, 16.5 if who == "B" else 17.5)], s, facing)[0]
        brad(C, bx, by, max(1.5, s * 1.0))
    lay(C, [bpoly(J, "spine", [(-0.16, -21), (-0.16, 19), (0.1, 19.5), (0.1, -21)], s, facing)], T["leg"], mud * 1.3, sd + 9, 2)
    pencil(C, bpoly(J, "spine", [(0.07, -20), (0.07, 18)], s, facing), max(1.5, s * .8), 40, .8, sd + 3)
    lay(C, [bpoly(J, "neck", NECK, s, facing)], T["skin"] * .92, mud, sd + 10, 2)
    # ---- head (cut a size large, as in shadow-play rigs)
    s0 = s; s = s * HEAD_SCALE
    H = S.hframe(J, s, facing)
    if who == "B":
        back = [(9, 17), (2, 23.5), (-8, 23), (-17, 15), (-21, 3), (-20, -9), (-16, -14), (-11, -8), (-8, 7), (0, 14), (8, 13)]
        lay(C, [[H(*p) for p in back]], T["hair"] * .78, 0.25, sd + 11, 2)
        if hair is not None: draw_hair_strands(C, H, s, hair, T["hair"], sd + 70)
    hsw = [(*H(9, 13), 2.6 * s, 0.6 * s, -8, 222), (*H(18.6, -2.4), 0.9 * s, 0.6 * s, 0, 218),
           (*H(7.5, -2.5), 1.8 * s, 0.5 * s, 35, 210), (*H(15.6, 3.5), 0.5 * s, 1.4 * s, 10, 214)]
    lay(C, [[H(*p) for p in HEAD]], T["skin"] * 1.03, mud * 0.55, sd + 12, shd, sweat=hsw, edge=0.6,
        smudges=[(*H(4, -11), 5 * s, 3 * s, 20, 0.26), (*H(-4, 12), 5 * s, 2.4 * s, -10, 0.18), (*H(12, -14), 3 * s, 1.6 * s, 0, 0.2)])
    lay(C, [[H(-7.5 + 2.8 * math.cos(q), -1.5 + 4.2 * math.sin(q)) for q in np.linspace(0, 6.28, 16, endpoint=False)]],
        T["skin"] * .9, 0, sd + 13, 0, edge=0)
    pencil(C, [H(-6, 2), H(-9, 0.5), H(-9, -3.5), H(-6.5, -5)], max(1, s * .3), 110, .5, sd + 4)
    # eye: thin white card almond; pencilled iris dot drops with the gaze; upper lid line; light lower lid
    lay(C, [[H(*p) for p in ((7.0, 6.4), (9.4, 8.6), (12.2, 8.6), (14.0, 6.6), (12.6, 4.4), (9.4, 4.4))]], 216, 0, sd + 14, 0, edge=0.25, tex=False)
    gy = 6.5 - 1.3 * gaze
    ir = [H(11.6 + 1.15 * math.cos(q), gy + 1.15 * math.sin(q)) for q in np.linspace(0, 6.28, 12, endpoint=False)]
    lay(C, [ir], 34, 0, sd + 7, 0, edge=0, tex=False)
    lidy = 8.6 - 1.6 * gaze
    pencil(C, [H(6.8, 6.4), H(9.4, lidy), H(12.2, lidy), H(14.2, 6.6)], max(1.4, s * .42), 34, 1, sd + 5)
    pencil(C, [H(9.2, 4.2), H(12.6, 4.2)], max(1, s * .25), 96, .55, sd + 6)
    # brow: raised (fear / concern) lifts and tilts the inner end; negative knits it down
    by_o, by_i = 11.4 + 1.2 * brow, 12.0 + 2.4 * brow
    pencil(C, [H(6, by_o), H(10, by_o + 1.0 + 0.4 * brow), H(14, by_i)], max(1.4, s * .5), 40 if who != "B" else 84, .95, sd + 8)
    if brow > 0.3:   # forehead lines when the brow lifts
        for k in range(2):
            pencil(C, [H(5, 14.5 + 1.6 * k), H(10, 15.2 + 1.6 * k), H(13, 14.6 + 1.6 * k)], max(1, s * .28), 120, .4 * brow, sd + 90 + k)
    pencil(C, [H(16.2, -4.0), H(17.2, -4.3)], max(1, s * .45), 50, .8, sd + 9)
    pencil(C, [H(13.4, -1.2), H(15.6, -6.6)], max(1, s * .3), 112, .45, sd + 15)        # nasolabial crease
    # mouth: a closed pencil line, or an open dark slot cut in the card
    if mouth > 0.12:
        mh = 0.6 + 2.6 * mouth
        lay(C, [[H(*p) for p in ((12.8, -9.6), (15.6, -9.8), (16.0, -10.4 - mh * .6), (14.8, -10.2 - mh), (13.0, -10.0 - mh * .7))]],
            40, 0, sd + 16, 0, edge=0, tex=False)
    else:
        pencil(C, [H(13.2, -10.0), H(14.4, -10.4), H(15.4, -10.2)], max(1.2, s * .5), 42, .9, sd + 10)
    pencil(C, [H(12.8, -12.8 - 0.8 * mouth), H(14.6, -12.6 - 0.8 * mouth)], max(1, s * .3), 110, .5, sd + 11)
    for k in range(4):
        pencil(C, [H(2 + 2.2 * k, -3 - 0.5 * k), H(0 + 2.2 * k, -9 - 0.5 * k)], max(1, s * .28), 108, .45, sd + 60 + k)
    if who == "B":
        fr = [(13.5, 15), (9, 21), (1, 23), (-6, 21), (-2, 17.5), (2, 16.5), (4, 12.5), (6.5, 15.5), (8.5, 11.5), (10.2, 14.6), (12.4, 11.8)]
        lay(C, [[H(*p) for p in fr]], T["hair"], 0.18, sd + 15, 2,
            sweat=[(*H(2, 21.5), 3 * s, .6 * s, -15, 228), (*H(9, 17), 1.6 * s, .5 * s, -35, 222)])
        for k in range(7):
            q = -6 + 2.8 * k
            pencil(C, [H(q, 22 - abs(q) * .15), H(q - 2.5, 15 - k * .6)], max(1, s * .33), T["hairline"], .55, sd + 20 + k)
        for k in range(3):   # wet forelock strands stuck to the forehead
            q = 1 + 2.4 * k
            lay(C, [[H(q, 14.0), H(q + 1.4, 13.8), H(q + 2.2 - k, 9.6 - k), H(q + 1.0 - k, 9.4 - k)]], T["hair"] * .9, 0.2, sd + 40 + k, 1, edge=0.6)
    if who == "C":
        cap = [(12, 15), (4, 21.5), (-8, 21), (-16, 13), (-17, 1), (-13.5, -6), (-11, 3), (-5, 11), (8, 12)]
        lay(C, [[H(*p) for p in cap]], T["hair"], 0.2, sd + 15, 2)
        band = [(15, 14.5), (5, 16.6), (-8, 16), (-17.5, 12.5), (-17, 6), (-8, 9.5), (5, 10), (14.6, 8.6)]
        tails = [[H(-16, 11), H(-25, 1), H(-23, -1.5), H(-15.5, 7)], [H(-16, 9.5), H(-21, -6), H(-18.5, -7), H(-15, 7)]]
        lay(C, [[H(*p) for p in band]] + tails, T["band"], 0.6, sd + 16, 2, sweat=[(*H(8, 14), 3 * s, .7 * s, 0, 222)])
        for k in range(9):            # pencilled pattern: zigzag row, dots between, a ruled edge on each side
            q = 13 - 3.4 * k
            pencil(C, [H(q, 10.6), H(q - 1.7, 14.6), H(q - 3.4, 10.6)], max(1, s * .45), 46, .85, sd + 30 + k)
            pencil(C, [H(q - 1.7, 11.6), H(q - 1.5, 11.7)], max(1.5, s * .7), 36, .9, sd + 40 + k)
            pencil(C, [H(q, 15.6), H(q - 0.9, 15.9)], max(1, s * .45), 60, .7, sd + 50 + k)
        pencil(C, [H(15, 9.4), H(5, 10.6), H(-8, 10.0), H(-17, 6.8)], max(1, s * .35), 70, .6, sd + 61)
        pencil(C, [H(15, 14.0), H(5, 16.0), H(-8, 15.4), H(-17.5, 12.0)], max(1, s * .35), 70, .6, sd + 62)
    if who == "A":
        brim = [(22, 13), (8, 12), (-21, 12.5), (-22, 9), (-6, 10.4), (21, 10)]
        crown = [(13, 11), (12, 20), (6, 23.5), (-4, 22.5), (-10, 24), (-13, 11)]
        lay(C, [[H(*p) for p in crown], [H(*p) for p in brim]], T["hat"], 0.6, sd + 17, 2, sweat=[(*H(4, 21), 3 * s, .5 * s, 0, 160)])
        lay(C, [[H(*p) for p in ((13.2, 11), (12.6, 14.2), (-12.8, 14.2), (-13, 11))]], T["hat"] * .55, 0.3, sd + 18, 1)
        pencil(C, [H(2, 22.6), H(0, 17)], max(1, s * .35), 50, .6, sd + 19)       # crown dent
    if after_head_cb: after_head_cb(C, H)
    s = s0
    # ---- near side
    lay(C, [bpoly(J, "thigh_n", tube(-.1, 1.03, 16, 12.5), s, facing)], T["leg"] * Lt("thigh_n"), mud * 1.3, sd + 18, shd,
        smudges=[(*bpoly(J, "thigh_n", [(0.75, 2)], s, facing)[0], 10 * s, 6 * s, 0, 0.4),
                 (*bpoly(J, "thigh_n", [(0.98, 0)], s, facing)[0], 9 * s, 9 * s, 0, 0.45)])       # wet knee
    lay(C, [bpoly(J, "shin_n", tube(0, 1.0, 12, 9), s, facing)], T["leg"] * Lt("shin_n"), mud * 1.8, sd + 19, shd)
    pencil(C, bpoly(J, "thigh_n", [(0.82, -10), (0.92, -4), (0.86, 3)], s, facing), max(1, s * .4), 40, .5, sd + 21)   # knee crease
    lay(C, [bpoly(J, "foot_n", BOOT, s, facing)], T["boot"], mud, sd + 20, shd)
    lay(C, [bpoly(J, "upper_n", tube(-.15, sl, 11.5, 10), s, facing)], T["shirt"] * Lt("upper_n"), mud, sd + 21, shd)
    if who == "B":
        lay(C, [bpoly(J, "upper_n", [(.5, -11), (.72, -10.5), (.72, 10.5), (.5, 11)], s, facing)], T["collar"], mud * .5, sd + 22, 2)
        lay(C, [bpoly(J, "upper_f", [(.5, -10.5), (.72, -10), (.72, 10), (.5, 10.5)], s, facing)], T["collar"] * .85, mud * .5, sd + 23, 1)
        lay(C, [bpoly(J, "upper_n", tube(.66, 1.02, 8.2, 7.6), s, facing)], T["skin"], mud, sd + 24, 2)
        pencil(C, bpoly(J, "upper_n", [(.54, -9), (.6, -3), (.55, 3), (.61, 9)], s, facing), max(1, s * .35), 110, .5, sd + 25)  # roll folds
    else:   # sleeve break at the elbow: a pencilled chevron of folds
        for k in range(3):
            u = 0.74 + 0.07 * k
            pencil(C, bpoly(J, "upper_n", [(u, -9), (u + 0.06, -2), (u - 0.02, 6)], s, facing), max(1, s * .4), 50 if who == "C" else 80, .55, sd + 26 + k)
    lay(C, [bpoly(J, "fore_n", tube(-.1, 1.02, 8, 6) if who == "B" else tube(-.1, .95, 9.5, 8), s, facing)],
        (T["skin"] if who == "B" else T["shirt"]) * Lt("fore_n"), mud * 1.3, sd + 27, shd,
        smudges=[(*bpoly(J, "fore_n", [(0.7, 2)], s, facing)[0], 6 * s, 3 * s, 0, 0.35)])
    if who != "B":   # cuff
        lay(C, [bpoly(J, "fore_n", [(.82, -9.5), (.96, -8.2), (.96, 8.2), (.82, 9.5)], s, facing)], T["shirt"] * 1.08, mud * .8, sd + 28, 1)
    if front_hand_cb: front_hand_cb(C)
    p0, Lh, (ux, uy), _ = bframe(J, "hand_n")
    lay(C, [bpoly(J, "hand_n", HAND, s, facing)], T["skin"], mud * 1.9, sd + 29, shd,
        sweat=[(p0[0] + ux * Lh * .9, p0[1] + uy * Lh * .9, 2.6 * s, 0.8 * s, math.degrees(math.atan2(uy, ux)), 216),
               (p0[0] + ux * Lh * 1.3, p0[1] + uy * Lh * 1.3, 1.2 * s, 0.6 * s, 0, 212)])
    for k in range(3):   # pencilled knuckle creases
        pencil(C, bpoly(J, "hand_n", [(1.05 + 0.16 * k, -5.5), (1.15 + 0.16 * k, -2)], s, facing), max(1, s * .3), 90, .5, sd + 80 + k)
    for b in ("thigh_f", "shin_f", "upper_f", "fore_f", "hand_f", "thigh_n", "shin_n", "foot_n", "upper_n", "fore_n", "hand_n", "neck"):
        brad(C, *J[b][0], max(2, 1.6 * s))


PIECES = {  # the cut pieces each puppet is made of (for the record and the sheet)
    "common": ["far thigh", "far shin", "far boot", "far upper sleeve", "far forearm", "far hand", "torso (shirt/blouse)",
               "collar flap x2", "trouser top + belt", "neck", "head (profile)", "ear", "eye white", "near thigh", "near shin",
               "near boot", "near upper sleeve", "near forearm", "near hand", "split pins x12 + 3 buttons"],
    "A": ["hat crown", "hat brim", "hat band", "cuff"],
    "B": ["back hair mass", "14 wet hair strands (3-link chains)", "front hair", "3 forelock strands", "rolled cuffs x2", "bare forearm"],
    "C": ["cropped hair", "headband with two pencilled rows", "two knot tails", "cuff"],
}


def bag_piece(C, hx, hy, s, ang=0, seed=500, high=False):
    """dry bag: dark oilcloth roll-top (handmade card) with strap, tie and buckle pin; a soft sheen L~112."""
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    R = lambda x, y: (hx + (x * c - y * sn) * s, hy + (x * sn + y * c) * s)
    strap = [R(-3, 0), R(3, 0), R(11, 16), R(7, 17), R(0, 4), R(-7, 17), R(-11, 16)]
    body = [R(-21, 18), R(21, 18), R(24, 30), R(25, 60), R(22, 70), R(-22, 70), R(-25, 60), R(-24, 30)]
    roll = [R(-23, 14), R(23, 14), R(24, 24), R(-24, 24)]
    tie = [R(18, 16), R(30, 12), R(31, 15), R(20, 21)]
    lay(C, [strap], 132, 0.3, seed, 2)
    lay(C, [body], 58, 0.6, seed + 1, max(2, int(s * 2)), sweat=[(*R(-14, 32), 6 * s, 1.0 * s, -8, 112), (*R(10, 50), 3 * s, 0.6 * s, 80, 96)])
    for k in range(3):  # oilcloth creases
        pencil(C, [R(-16 + 12 * k, 28), R(-12 + 12 * k, 46), R(-15 + 12 * k, 64)], max(1, s * .5), 36, .7, seed + 3 + k)
    lay(C, [roll], 80, 0.4, seed + 2, 2)
    lay(C, [tie], 120, 0.3, seed + 6, 1)
    pencil(C, [R(-22, 19), R(22, 19)], max(1, s * .6), 40, .8, seed)
    brad(C, *R(0, 19), max(2, 1.6 * s))
