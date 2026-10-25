"""SCION-GRABCUT · the threshold, cut out of archive film.  Compositor + choreography + measurement.

python3 render.py [--frames a:b] [--out DIR] [--still t1,t2,..]
Writes scene frames (JPEG, 1280x720) to build/cache/frames/s%04d.jpg and build/cache/measure.json (per-frame measurement
of the rendered dog: its own alpha buffer and its head layer's alpha buffer, never the plan).

Coordinates: canvas pixels (x right, y down). World mapping X(x_m) = 325 + 205 x_m (threshold at x = 0, sill 0.56,
porch steps 4.9). Time base: score frame i (24 fps), t = i/24.
Every visible figure is a sprite = an extracted cut (alpha from our graph cut + its source pixels) with a recorded
source (shot, frame, crop origin) and an affine/projective transform to the canvas (the original-coordinate transform).
"""
import os, sys, json, math, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from graphcut import erode, dilate, box_blur

FOLDER = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(FOLDER, '../../..'))
C = os.path.join(HERE, 'cache')
SCORE = json.load(open(os.path.join(ROOT, 'paeleo/handmade/score/threshold-score.json')))
FR = SCORE['frames']
W, H = 1280, 720
FONT_DIR = os.path.join(ROOT, 'tools/paeleo/fonts')


def X(xm):
    return 325.0 + 205.0 * xm


WALL_BASE = 540.0      # where the façade meets the porch boards; the sill line
PORCH_FRONT = 652.0
DOOR_L, DOOR_R, DOOR_T = X(-0.46), X(0.46), WALL_BASE - 410.0
HOUSE_R = 487.0
STEPS_X = min(float(W), X(4.9))

# palette (linear-ish, 0..1)
DUSK = np.array([0.40, 0.47, 0.70], np.float32)      # cold ambient tint for luminance
WARM = np.array([1.00, 0.68, 0.36], np.float32)      # door light
EDGE_COLD = np.array([0.70, 0.78, 0.92], np.float32)  # the visible cut line
EDGE_WARM = np.array([1.00, 0.86, 0.62], np.float32)


# ------------------------------------------------------------------ sprites
class Sprite:
    """lum, alpha, edge (cut line weight) in source-crop pixels; src = provenance."""
    def __init__(self, lum, a, src, edge=None):
        self.lum = lum.astype(np.float32); self.a = a.astype(np.float32); self.src = src
        if edge is None:
            hard = self.a > 0.5
            e = (hard & ~erode(hard, 1)).astype(np.float32)
            edge = box_blur(e, 1) * 1.6
            edge = np.clip(edge, 0, 1) * (self.a > 0.05)
        self.edge = edge.astype(np.float32)
        # round 2: edge-colour decontamination. In the matte band the pixel mixes the dog with the old background (the
        # light rim); replace band luminance by the mean of nearby solid interior pixels.
        solid = self.a > 0.97
        if solid.any():
            num = box_blur(np.where(solid, self.lum, 0), 3); den = box_blur(solid.astype(np.float32), 3)
            inner = num / np.maximum(den, 1e-3)
            band = (self.a <= 0.97) & (self.a > 0) & (den > 0.02)
            self.lum = np.where(band, inner, self.lum).astype(np.float32)
        self.h, self.w = self.a.shape

    def masked(self, m):
        # a piece keeps only the exterior cut line of its parent: joint cuts are not drawn as edges
        return Sprite(self.lum, self.a * m, self.src, edge=self.edge * (m > 0.5))

    def mirrored(self):
        s = Sprite(self.lum[:, ::-1], self.a[:, ::-1], dict(self.src, mirrored=not self.src.get('mirrored', False)), self.edge[:, ::-1])
        return s


def load_cut(shot, name):
    p = os.path.join(C, shot, name + '.npz')
    z = np.load(p)
    rgb = z['rgb'].astype(np.float32) / 255.0
    lum = rgb @ np.array([0.30, 0.59, 0.11], np.float32)
    a = z['alpha'].astype(np.float32)
    return Sprite(lum, a, {'shot': shot, 'piece': name, 'origin': [int(v) for v in z['origin']]}), z


def A_scale_rot(s, ang_deg, sx=None, mirror=False):
    """2x2 linear part: rotate(ang) @ scale. mirror flips x before rotation."""
    a = math.radians(ang_deg)
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    S = np.diag([(sx if sx else s) * (-1 if mirror else 1), s])
    return R @ S


def aff(L, src_pt, dst_pt):
    """3x3 affine mapping sprite px -> canvas px, with linear L and src_pt -> dst_pt."""
    M = np.eye(3)
    M[:2, :2] = L
    M[:2, 2] = np.array(dst_pt) - L @ np.array(src_pt)
    return M


class Canvas:
    def __init__(self, bg):
        self.rgb = bg.copy()
        self.light = None
        self.masks = {}

    def draw(self, sp, M, exposure=1.0, lit=0.0, edge_k=0.0, tag=None, tint=None, warmth=None, z_mask=None, opacity=1.0):
        """composite sprite with projective/affine M (sprite->canvas). Bilinear inverse sampling inside the bbox."""
        corners = np.array([[0, 0, 1], [sp.w, 0, 1], [0, sp.h, 1], [sp.w, sp.h, 1]], float).T
        pc = M @ corners; pc = pc[:2] / pc[2]
        x0 = int(max(0, math.floor(pc[0].min()) - 1)); x1 = int(min(W, math.ceil(pc[0].max()) + 1))
        y0 = int(max(0, math.floor(pc[1].min()) - 1)); y1 = int(min(H, math.ceil(pc[1].max()) + 1))
        if x1 <= x0 or y1 <= y0:
            return
        Mi = np.linalg.inv(M)
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        P = Mi @ np.stack([xx.ravel() + .5, yy.ravel() + .5, np.ones(xx.size)])
        u = (P[0] / P[2] - .5).reshape(xx.shape); v = (P[1] / P[2] - .5).reshape(xx.shape)
        ok = (u > -1) & (u < sp.w) & (v > -1) & (v < sp.h)
        if not ok.any():
            return
        u0 = np.floor(u).astype(int); v0 = np.floor(v).astype(int); fu = (u - u0).astype(np.float32); fv = (v - v0).astype(np.float32)

        def samp(img):
            pad = np.pad(img, 1)
            a = pad[np.clip(v0 + 1, 0, sp.h + 1), np.clip(u0 + 1, 0, sp.w + 1)]
            b = pad[np.clip(v0 + 1, 0, sp.h + 1), np.clip(u0 + 2, 0, sp.w + 1)]
            c = pad[np.clip(v0 + 2, 0, sp.h + 1), np.clip(u0 + 1, 0, sp.w + 1)]
            d = pad[np.clip(v0 + 2, 0, sp.h + 1), np.clip(u0 + 2, 0, sp.w + 1)]
            return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv
        al = samp(sp.a) * ok * opacity
        if z_mask is not None:
            al = al * z_mask[y0:y1, x0:x1]
        pl = samp(sp.lum * sp.a) / np.maximum(samp(sp.a), 1e-4)
        ed = samp(sp.edge) * ok
        Lw = self.light[y0:y1, x0:x1] if self.light is not None else 0
        Lw = Lw * lit
        base = (DUSK if tint is None else tint) * exposure
        col = pl[..., None] * (base[None, None, :] + (WARM[None, None, :] * Lw[..., None] if lit else 0))
        ek = ed[..., None] * edge_k * (0.35 + 0.65 * np.clip(exposure, 0, 1.2))
        ecol = EDGE_COLD * (0.55 * exposure + 0.25) + (EDGE_WARM * np.clip(Lw, 0, 1)[..., None] if lit else 0)
        col = col * (1 - ek) + ecol * ek
        dst = self.rgb[y0:y1, x0:x1]
        self.rgb[y0:y1, x0:x1] = dst * (1 - al[..., None]) + col * al[..., None]
        cov = self.masks.setdefault('_cov', np.zeros((H, W), np.float32))
        cov[y0:y1, x0:x1] = cov[y0:y1, x0:x1] * (1 - al) + al
        for k in list(self.masks):
            if k not in ('_cov', tag):
                self.masks[k][y0:y1, x0:x1] *= (1 - al)    # occluded by this piece
        if tag:
            m = self.masks.setdefault(tag, np.zeros((H, W), np.float32))
            m[y0:y1, x0:x1] = m[y0:y1, x0:x1] * (1 - al) + al


# ------------------------------------------------------------------ assets
def joint_split(sp, lines):
    """manual contour markup: split a sprite by straight joint lines (crop coords). lines: name -> (p, q, side_pt)
    returns name -> mask (float), remainder 'torso'. Each child piece gets a 3 px tab past its joint so rotation leaves no
    gap (the overlap is the joint)."""
    hh, ww = sp.a.shape
    yy, xx = np.mgrid[:hh, :ww]
    rem = np.ones((hh, ww), bool)
    out = {}
    for name, (p, q, side, extra) in lines.items():
        p = np.array(p, float); q = np.array(q, float); n = np.array([-(q - p)[1], (q - p)[0]]); n /= np.linalg.norm(n)
        sgn = np.sign((np.array(side) - p) @ n)
        d = ((xx - p[0]) * n[0] + (yy - p[1]) * n[1]) * sgn
        m = d > 0
        if extra is not None:
            m &= extra(xx, yy)
        m &= rem
        out[name] = m.astype(np.float32)
        rem &= ~m
    out['torso'] = rem.astype(np.float32)
    return out


class Assets:
    def __init__(self):
        self.dog = {}
        for i in range(50):
            p = os.path.join(C, 'dog', 'f%03d.npz' % i)
            if os.path.exists(p):
                sp, z = load_cut('dog', 'f%03d' % i)
                hard = sp.a > .5
                ys, xs = np.nonzero(hard)
                sp.anchor = (float(xs.mean()), float(ys.max()))
                sp.bbox = (xs.min(), ys.min(), xs.max(), ys.max())
                self.dog[i] = sp
        self.cam = np.array(json.load(open(os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog/camera.json'))))
        # ---- the puppet: frame 13 split at its joints (crop coords of f013, origin 54,54)
        p13 = self.dog[13]
        L = {
            'head': ((33, 62), (66, 47), (35, 30), None),
            'tail': ((147, 80), (147, 115), (160, 100), lambda x, y: y > 82),
            'fore': ((38, 103), (104, 103), (70, 130), lambda x, y: x < 106),
            'hind': ((106, 99), (152, 96), (130, 130), lambda x, y: x >= 106),
        }
        parts = joint_split(p13, L)
        hh, ww = p13.a.shape; yy, xx = np.mgrid[:hh, :ww]
        parts['fore_a'] = parts['fore'] * (xx < 72)     # the leg reaching forward (slanted ~22 deg in f13)
        parts['fore_b'] = parts['fore'] * (xx >= 72) * (xx < 92)    # the upright leg (x>=92 below the joint is belly: torso)
        parts['torso'] = np.maximum(parts['torso'], parts['fore'] * (xx >= 92))
        self.pup = {k: p13.masked(m) for k, m in parts.items()}
        # round 2: the lying body, one piece. torso + hind (+ tail root) above a floor line, each column filled from its
        # top contour down to that line with the nearest fur above (a recorded repair: the occluded belly), then the
        # contour rounded. No hind legs hang below it; nothing is left as a notch.
        self.lie_floor = 116.0
        bm = (parts['torso'] + parts['hind'] + parts['fore'] * (xx >= 72) + parts['tail'] * (xx < 153)) * (p13.a > .5)   # round 3: the tail root belongs to the body
        bm = (bm > 0.5) & (yy < self.lie_floor)
        filled = bm.copy(); lum = p13.lum.copy()
        cols = np.nonzero(bm.any(0))[0]
        xc0, xc1 = cols.min(), cols.max()
        solid13 = bm & (p13.a > .9) & (yy > 80)
        bsum = (np.where(solid13, p13.lum, 0)).sum(0); bcnt = solid13.sum(0)
        k = np.ones(21) / 21
        band_mean = np.convolve(bsum, k, 'same') / np.maximum(np.convolve(bcnt, k, 'same'), 1e-3)
        for x in cols:
            ys = np.nonzero(bm[:, x])[0]
            # the fill line curves up into the chest and the rump so neither end is a vertical wall
            # round 3: a drawn belly contour (recorded repair), not a straight floor line: the chest rounds down to the
            # elbow, the belly lifts between elbow and haunch, the haunch rounds onto the boards, with a little fur
            xa, xb = xc0 + 22, xc1 - 34
            lift = 6.0 * math.sin(math.pi * min(1, max(0, (x - xa) / max(1, xb - xa)))) if xa < x < xb else 0.0
            xh = xc1 - 24                                   # the haunch: a round mound touching the boards at one place
            lift += min(10.0, 0.012 * (x - xh) ** 2) if x > xb - 6 else 0.0
            fur = 1.4 * math.sin(x * 0.7) + 0.9 * math.sin(x * 1.9 + 1.0)
            yb = int(round(self.lie_floor - lift + fur - 1.6 * max(0, xc0 + 24 - x) - 1.3 * max(0, x - (xc1 - 16))))
            y0 = ys.min()
            filled[max(yb, y0):, x] = False        # the drawn belly contour also trims original pixels below it
            if yb <= y0:
                continue
            filled[y0:yb, x] = True
            for y in range(y0, yb):
                if bm[y, x] and p13.a[y, x] > .9:
                    continue
                # clone-stamp repair: fur from 30 px above in the same column (inside the body), else the band mean
                ys2 = y - 30
                if ys2 >= 0 and bm[ys2, x] and p13.a[ys2, x] > .9:
                    lum[y, x] = p13.lum[ys2, x] * 0.86
                else:
                    lum[y, x] = band_mean[x] * 0.86
        # round the two lower corners and the contour
        f = filled.astype(np.float32)
        for _ in range(2):
            f = box_blur(f, 1)
        filled = f > 0.5
        lum = np.where(filled & (p13.a < .9), box_blur(lum, 1), lum)
        self.lie_tail = p13.masked(parts['tail'] * (xx >= 150))
        self.lie_body = Sprite(lum, filled.astype(np.float32) * np.clip(box_blur(filled.astype(np.float32), 1) * 1.6 - 0.3, 0, 1),
                               {'shot': 'dog', 'piece': 'f013 lying body', 'repair': 'column fill to floor line, corners rounded'}, edge=np.zeros_like(lum))
        # head with a 7 px neck tab past its joint line (hidden under the body when drawn behind it)
        p = np.array([33.0, 62.0]); q = np.array([66.0, 47.0]); n = np.array([-(q - p)[1], (q - p)[0]]); n /= np.linalg.norm(n)
        sgn = np.sign((np.array([35.0, 30.0]) - p) @ n)
        d = ((xx - p[0]) * n[0] + (yy - p[1]) * n[1]) * sgn
        near = (xx - 48) ** 2 + (yy - 58) ** 2 < 11 ** 2
        self.head_tab = p13.masked((((d > 0) | ((d > -7) & near)) & (p13.a > .5)).astype(np.float32))
        self.piv = {'neck': (48, 58), 'shoulder': (66, 101), 'hip': (128, 96), 'tail': (147, 92), 'body': (95, 80)}
        self.pup_anchor = p13.anchor
        # back-of-head piece (frame 0: head raised, seen from behind): look in
        p0 = self.dog[0]
        hh, ww = p0.a.shape; yy, xx = np.mgrid[:hh, :ww]
        self.backhead = p0.masked(((yy < 68) & (xx < 62)).astype(np.float32))
        self.backhead_piv = (40, 64)
        # round 2: the frame-0 head's top was a SAM-straight run; round its contour (3 box passes, re-thresholded)
        f = self.backhead.a.copy()
        for _ in range(3):
            f = box_blur(f, 2)
        ab = np.clip((f - 0.5) * 4 + 0.5, 0, 1) * (self.backhead.a > 0.01 + 0 * f)
        ab = np.clip((f - 0.5) * 4 + 0.5, 0, 1)
        ell = ((xx - 38) / 27.0) ** 2 + ((yy - 40) / 34.0) ** 2 < 1.0     # round 3: an elliptical crop, not a box
        self.backhead = Sprite(p0.lum, ab * ell, dict(self.backhead.src, repair='contour rounded, elliptical crop'))
        # ---- world pieces
        self.w = {}
        for n in ('woman_stand', 'door_panel', 'hand', 'pillar', 'shrub', 'bowl'):
            sp, z = load_cut('world', n)
            self.w[n] = sp
        ws = self.w['woman_stand']
        hh, ww = ws.a.shape; yy, xx = np.mgrid[:hh, :ww]
        arm = ((xx > 127) & (yy > 90) & (yy < 205)).astype(np.float32)
        self.woman_body = ws.masked(1 - arm)
        self.woman_arm = ws.masked(arm)
        self.woman_upper = ws.masked(((yy < 206).astype(np.float32)) * (1 - arm))
        self.woman_lower = ws.masked((yy >= 200).astype(np.float32))
        # repair: the archive frame cuts her off below the knee; extend the trousers by stretching the last 24 rows
        low = ws.lum[-24:]; la = ws.a[-24:]
        self.woman_shins = Sprite(low, la * (la > .5), {'shot': 'world', 'piece': 'woman_stand', 'repair': 'last 24 rows stretched'})
        self.plate = np.array(Image.open(os.path.join(C, 'plate', 'plate.png'))).astype(np.float32) / 255.0


def smooth(u):
    u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)


def lerp(a, b, u):
    return a + (b - a) * u


# ------------------------------------------------------------------ static world
def build_background(A):
    bg = np.zeros((H, W, 3), np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None]
    # dusk sky: deep blue overhead to a dim violet-grey horizon
    top = np.array([0.035, 0.045, 0.11]); hor = np.array([0.22, 0.21, 0.30])
    u = np.clip(yy / 470.0, 0, 1) ** 1.4
    sky = top[None, None, :] * (1 - u[..., None]) + hor[None, None, :] * u[..., None]
    bg[:] = sky
    cv = Canvas(bg)
    # the dog's own place beyond the porch: the clean plate (path, shrub, lawn) far off in the dusk, dark and soft
    pl = A.plate
    far = Image.fromarray((pl[0:150, 100:491] * 255).astype(np.uint8)).resize((900, 150), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.2))
    f = np.array(far).astype(np.float32) / 255.0
    fade = np.clip(np.linspace(-0.2, 1.4, 150), 0, 1)[:, None]
    blend = cv.rgb[390:540, 380:1280]
    cv.rgb[390:540, 380:1280] = blend * (1 - fade[..., None] * .85) + (f[:, :900][..., None] * np.array([0.07, 0.08, 0.14]) + 0.008) * fade[..., None] * .85
    bg = cv.rgb
    # house façade: stone, tiled from the pillar cut (mirrored tiles), dark
    pi = A.w['pillar']
    tile_l = pi.lum * pi.a + (1 - pi.a) * np.median(pi.lum[pi.a > .5])
    th, tw = tile_l.shape
    S = 1.55
    tile = np.array(Image.fromarray((tile_l * 255).astype(np.uint8)).resize((int(tw * S), int(th * S)), Image.BICUBIC)).astype(np.float32) / 255
    tile = tile[6:-6, 6:-6]
    TH, TW = tile.shape
    wall = np.zeros((int(WALL_BASE), int(HOUSE_R)), np.float32)
    for j, y in enumerate(range(0, wall.shape[0], TH)):
        for k, x in enumerate(range(-(j % 2) * TW // 2, wall.shape[1], TW)):
            t = tile[:, ::-1] if (j + k) % 2 else tile
            t = t[::-1] if j % 2 else t
            ys, xs = slice(y, min(y + TH, wall.shape[0])), slice(max(x, 0), min(x + TW, wall.shape[1]))
            wall[ys, xs] = t[: ys.stop - ys.start, (xs.start - x): (xs.start - x) + (xs.stop - xs.start)]
    wall = wall * 0.55 + 0.12
    bg[:int(WALL_BASE), :int(HOUSE_R)] = wall[..., None] * DUSK[None, None, :] * 0.42
    # the house corner: a lit edge line
    bg[:int(WALL_BASE), int(HOUSE_R) - 3:int(HOUSE_R)] *= 1.6
    # porch boards: the dog's own path (clean plate), stretched along the porch, very dark
    pb = Image.fromarray((pl[150:300, 60:470] * 255).astype(np.uint8)).resize((int(STEPS_X), int(PORCH_FRONT - WALL_BASE)))
    pb = np.array(pb).astype(np.float32) / 255
    rows = np.linspace(0.75, 1.1, pb.shape[0])[:, None]
    bg[int(WALL_BASE):int(PORCH_FRONT), :int(STEPS_X)] = (pb * rows)[..., None] * DUSK * 0.34
    bg[int(PORCH_FRONT) - 2:int(PORCH_FRONT), :int(STEPS_X)] = DUSK * 0.30   # board edge catches the sky
    # below the porch: dark
    bg[int(PORCH_FRONT):, :] = np.array([0.02, 0.022, 0.04])
    # steps at the porch end
    for k in range(3):
        x0 = int(STEPS_X + k * 26); y0 = int(WALL_BASE + 18 + k * 34)
        bg[y0:y0 + 34, x0:W] = DUSK * (0.20 - k * 0.04)
        bg[y0:y0 + 2, x0:W] = DUSK * 0.33
    bg[int(PORCH_FRONT):, int(STEPS_X) - 4:int(STEPS_X)] = 0.01
    return bg


# ------------------------------------------------------------------ door, light
def door_open(t):
    """0 ajar .. 1 open; the score opens the door at 6.2 s (swing over 0.9 s)."""
    return smooth((t - 6.2) / 0.9)


def light_field(t, o):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx = (DOOR_L + DOOR_R) / 2
    amb = 0.06 + 0.94 * o
    # on figures: falls off with distance from the doorway (centre at sill height)
    d = np.hypot((xx - cx) / 1.0, (yy - 430) / 1.6)
    Lf = amb * 1.05 * np.exp(-d / 300.0)
    # ajar: a thin warm slit only near the door gap
    return Lf.astype(np.float32)


def draw_doorway(cv, A, t, o):
    rgb = cv.rgb
    x0, x1, y0, y1 = int(DOOR_L), int(DOOR_R), int(DOOR_T), int(WALL_BASE)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    # the interior: warm light, brighter low and toward the back of the hall; a floor line inside
    glow = (0.55 + 0.45 * ((yy - y0) / (y1 - y0))) * (1 - 0.35 * np.abs((xx - (x0 + x1) / 2) / ((x1 - x0) / 2)))
    lvl = 0.22 + 0.78 * o
    interior = WARM[None, None, :] * (glow * lvl)[..., None] * 0.95
    floor_y = y1 - 46
    interior[int(floor_y - y0):] *= 0.78
    interior[int(floor_y - y0):int(floor_y - y0) + 2] *= 0.6
    rgb[y0:y1, x0:x1] = np.maximum(rgb[y0:y1, x0:x1] * 0.2, interior + np.array([0.015, 0.015, 0.03]))
    # the door panel (Straight Talk, frame 28), hinged on the left jamb, swinging inward
    dp = A.w['door_panel']
    ys, xs = np.nonzero(dp.a > .5)
    # source corners of the panel (from its own cut): TL, TR, BR, BL
    pts = np.stack([xs, ys], 1).astype(float)
    TL = pts[np.argmin(pts[:, 0] + pts[:, 1])]; TR = pts[np.argmax(pts[:, 0] - pts[:, 1])]
    BR = pts[np.argmax(pts[:, 0] + pts[:, 1])]; BL = pts[np.argmax(pts[:, 1] - pts[:, 0])]
    theta = math.radians(22 + (80 - 22) * o)
    wdoor = (x1 - x0) * math.cos(theta)
    recede = 18 * math.sin(theta)        # the free edge recedes into the house: shorter, by perspective
    dst = np.array([[x0, y0 - 30], [x0 + wdoor, y0 - 30 + recede], [x0 + wdoor, y1 - recede * .6], [x0, y1]], float)
    Hm = homography(np.array([TL, TR, BR, BL]), dst)
    # the panel faces the dusk; its inner side gets the hall light as it opens
    cv.draw(dp, Hm, exposure=0.30 - 0.12 * o, lit=0.25 * o, edge_k=0.35)
    # the gap of light when ajar (a strip between the free edge and the right jamb, already in interior)
    return Hm


def homography(src, dst):
    Am = []
    for (x, y), (u, v) in zip(src, dst):
        Am.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        Am.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, Vt = np.linalg.svd(np.array(Am))
    Hm = Vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]


def draw_frame_stone(cv, A, o):
    """jambs + lintel from the pillar cut, in front of the door panel; the sill."""
    pi = A.w['pillar']
    lt = 0.9
    for xl, mirror in ((DOOR_L - 20, False), (DOOR_R - 4, True)):
        M = aff(A_scale_rot(1.0, 0, sx=24 / pi.w, mirror=mirror), (0 if not mirror else pi.w, 0), (xl, DOOR_T - 22))
        M[:2, :2] = np.array([[24.0 / pi.w * (-1 if mirror else 1), 0], [0, (WALL_BASE - DOOR_T + 24) / pi.h]])
        M[:2, 2] = [xl + (24 if mirror else 0), DOOR_T - 22]
        cv.draw(pi, M, exposure=0.36, lit=0.5, edge_k=0.4)
    # lintel: the pillar on its side
    L = np.array([[0, (DOOR_R - DOOR_L + 48) / pi.h], [-26.0 / pi.w, 0]])
    M = np.eye(3); M[:2, :2] = L
    M[:2, 2] = [DOOR_L - 24, DOOR_T + 4 - 0] - L @ np.array([pi.w, 0])
    cv.draw(pi, M, exposure=0.40, lit=0.4, edge_k=0.4)
    # sill: a pale stone threshold strip, catching the light
    y = int(WALL_BASE)
    sl = 0.16 + 0.55 * o
    cv.rgb[y - 3:y + 9, int(DOOR_L - 14):int(DOOR_R + 14)] = DUSK * 0.33 + WARM * sl * 0.55
    cv.rgb[y - 3:y - 1, int(DOOR_L - 14):int(DOOR_R + 14)] *= 1.35


def floor_spill(cv, o):
    """the light that comes out lies on the porch boards as a widening trapezoid."""
    if o <= 0.001:
        return
    y0, y1 = int(WALL_BASE + 8), int(PORCH_FRONT)
    yy, xx = np.mgrid[y0:y1, 0:int(STEPS_X)].astype(np.float32)
    v = (yy - y0) / (y1 - y0)
    l = DOOR_L - 10 - 40 * v; r = DOOR_R + 10 + 330 * v
    inside = np.clip((xx - l) / 30, 0, 1) * np.clip((r - xx) / 60, 0, 1)
    fall = np.exp(-np.abs(xx - (DOOR_L + DOOR_R) / 2) / 420.0) * (1 - 0.3 * v)
    s = (o * inside * fall * 0.55).astype(np.float32)
    seg = cv.rgb[y0:y1, :int(STEPS_X)]
    lum = seg.mean(2, keepdims=True)
    cv.rgb[y0:y1, :int(STEPS_X)] = seg + (lum * 2.2 + 0.05) * WARM * s[..., None]


# ------------------------------------------------------------------ the dog
DOG_S = 1.36
WALK = [42, 43, 44, 45]          # the archive dog's own walk, head low (mirrored to face the door)
WATCH = [9]   # round 3: f10/f11 dropped (hindquarter slab); f9 holds, breathing                      # standing, head up, looking at the person (boils between real frames)
TURN_AWAY = [13, 30, 34, 44]       # round 2: f15, f26, f36, f38, f40, f42 dropped (boxy or muddled cuts)   # the real dog turning from side-left through frontal to right
TURN_BACK = [('m', 30), ('m', 30), ('m', 44), 13]   # round 2: real cuts only, mirrored, head leading to the door


def feet_y(xm):
    """the dog walks in front of the façade; as it comes to the door it comes into the depth of the doorway."""
    u = smooth((2.3 - xm) / (2.3 - 0.59))
    return lerp(620.0, WALL_BASE + 6, u)


def depth_scale(fy):
    return 1.0 - 0.0009 * (620.0 - fy)


def walk_stride_px():
    return None


class DogRig:
    def __init__(self, A):
        self.A = A
        # registered source positions (plate coords) of the walk drawings: feet account for the travel
        cam = A.cam
        self.walk_u = {i: A.dog[i].anchor[0] + A.dog[i].src['origin'][0] - cam[i, 0] for i in WALK}
        us = [self.walk_u[i] for i in WALK]
        self.cycle_len = (us[-1] - us[0]) + (us[-1] - us[-2])  # travel of one pass through the drawings (source px)
        self.pose = json.load(open(os.path.join(ROOT, 'paeleo/handmade/kit/archive-dog/pose_agent_v8.json')))

    def frame_sprite(self, i, mirror):
        sp = self.A.dog[i]
        return (sp.mirrored() if mirror else sp), sp

    def place_frame(self, cv, i, mirror, x_anchor, fy, exposure, lit, s=None, tag='dog', ang=0.0, head_tag=None):
        sp, orig = self.frame_sprite(i, mirror)
        s = (s or DOG_S) * depth_scale(fy)
        ax, ay = orig.anchor
        if mirror:
            ax = orig.w - ax
        M = aff(A_scale_rot(s, ang), (ax, ay), (x_anchor, fy))
        if i in WATCH:   # breathing: a 0.7 % rise of the body about its feet, ~0.4 Hz (score time from cv)
            br = 1.0 + 0.007 * math.sin(getattr(cv, 't', 0.0) * 2.5)
            M = M @ aff(np.diag([1.0, br]), (ax, ay), (ax, ay))
        cv.draw(sp, M, exposure=exposure, lit=lit, tag=tag)
        # where this drawing's nose and tail are on the canvas (the kit's rig keys for that source frame, carried by M)
        from extract import interp_pose
        k = self.pose.get(str(i)) or interp_pose(self.pose, i)
        ox, oy = orig.src['origin']
        def tc(p):
            px, py = p[0] - ox, p[1] - oy
            if mirror:
                px = orig.w - px
            v = M @ np.array([px, py, 1.0]); return [float(v[0]), float(v[1])]
        cv.marks = {'nose': tc(k['nose']), 'tail': tc(k['tail']), 'neck': tc(k['neck'])}
        # head layer for measurement: the part of the drawing ahead of the shoulders (where the head is) is measured from
        # the drawing itself: the leading 30 % of the dog's width in its facing direction, upper half
        return M

    # ---------------- puppet
    def puppet(self, cv, x_anchor, fy, mirror, lie, rest, head, look, tail, wag, t, exposure, lit, head_back=0.0, breathe=0.0):
        """the lying dog: f13's own pieces re-posed (round 2). The body is ONE piece: torso + haunch cut at the floor line
        and column-filled down to it (no notches, no hanging hind legs); the forelegs are laid forward along the boards;
        the head (with a hidden neck tab) is drawn behind the body so the neck covers its cut; the tail lies behind.
        lie 0.4 (going down) .. 1 (down); rest lays the chin on the paws; look swaps in the back-of-head piece."""
        A = self.A; P = A.piv; pp = A.pup
        s = DOG_S * depth_scale(fy)
        ax, ay = A.pup_anchor
        sg = -1.0 if mirror else 1.0
        R = np.array([[s * sg, 0], [0, s]])
        def to_canvas(p):
            return np.array([x_anchor, fy]) + R @ (np.array(p) - np.array([ax, ay]))
        def rot(deg):
            a = math.radians(deg); return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        u = min(1.0, max(0.0, (lie - 0.4) / 0.6))
        floor_src = A.lie_floor                      # source row of the body's cut floor line
        drop = (ay - floor_src) * (0.55 + 0.45 * u)  # at u = 1 the floor line sits on the boards
        body = np.array(P['body'])
        Tt = np.diag([1.0, 1.0 + 0.012 * breathe])
        def torso_pt(p):
            return body + Tt @ (np.array(p) - body) + np.array([0, drop])
        # tail: behind, lowered onto the boards, wagging with the score
        tail_ang = 12.0 * u + wag * 8.0 * math.sin(t * 2 * math.pi * 2.2)
        M = aff(R @ rot(tail_ang), (151, 96), to_canvas(torso_pt((151, 96))))
        cv.draw(A.lie_tail, M, exposure=exposure * 0.9, lit=lit, tag='dog')
        # head transform
        neck = np.array(P['neck'])
        if look > 0.5:
            head_sp = A.backhead
            Mh = aff(R @ (rot(0) * 0.98), A.backhead_piv, to_canvas(torso_pt(neck) + np.array([6, 2])))
            cv.head_piece = 'back_of_head_f000'; cv.marks = None
        else:
            hang = -(lerp(-6.0, 12.0, 1 - min(1.2, head)) + 36.0 + 26.0 * rest)
            hdrop = 6.0 + 12.0 * rest
            head_sp = A.head_tab
            Mh = aff(R @ rot(hang), neck, to_canvas(torso_pt(neck) + np.array([0, hdrop])))
            cv.head_piece = 'head_f013'
            from extract import interp_pose
            k13 = interp_pose(self.pose, 13)
            def th(p):
                v = Mh @ np.array([p[0] - 54, p[1] - 54, 1.0]); return [float(v[0]), float(v[1])]
            cv.marks = {'nose': th(k13['nose']), 'neck': th(k13['neck']), 'tail': None}
        cv.draw(head_sp, Mh, exposure=exposure * (1.05 if look > 0.5 else 1.0), lit=lit, tag='head')
        # forelegs laid forward along the boards, drawn BEHIND the body (round 3: the leg tops' joint cut is hidden under
        # the chest); both at one angle, the far leg a little behind and above the near one so they overlap (no gap)
        fore_ang = 88.0 * (0.9 + 0.1 * u)
        for leg, a0, off, ek in (('fore_b', 0.0, (-2.0, -15.0), 0.8), ('fore_a', -22.0, (-12.0, -6.0), 1.0)):
            M = aff(R @ (rot(fore_ang + a0) @ np.diag([1, 0.9])), P['shoulder'],
                    to_canvas(torso_pt(P['shoulder']) + np.array(off)))
            cv.draw(pp[leg], M, exposure=exposure * ek, lit=lit, tag='dog')
        # the body, one piece, over the leg tops and the neck
        M = aff(R @ Tt, body, to_canvas(torso_pt(body)))
        cv.draw(A.lie_body, M, exposure=exposure, lit=lit, tag='dog')


def mask_add(cv, tag, M, sp):
    pass


# ------------------------------------------------------------------ the person
def draw_person(cv, A, t, sc, o):
    """the woman cut from Straight Talk (back view, read as a dusk silhouette), re-posed from her own pieces:
    body, sleeve (pivot at the shoulder), lower cut (hips/thighs) and the repaired shins; her offered hand is the
    Door to Heaven hand cut from its card."""
    p = sc['person']
    sit = p['sit']; reach = p['reach']; low = p['low']; mouth = p['mouth']
    px = X(p['x'])
    s = 0.94
    ws = A.w['woman_stand']
    exp = 0.24 + 0.08 * (1 - o)
    lit = 0.85
    calling = 1.0 if p['voice'] == 'call' else 0.0
    lean = -3.5 * calling * smooth(mouth * 2) - 4.0 * reach
    sho = np.array([135.0, 100.0]); end = np.array([138.0, 200.0])
    if sit < 0.02:
        feet = WALL_BASE + 2
        knee_y = feet - 82
        M = aff(A_scale_rot(s, lean), (ws.w * .45, ws.h), (px, knee_y))
        sh = A.woman_shins
        Ms = aff(np.array([[s, 0], [0, (feet - knee_y + 6) / sh.h]]), (ws.w * .45, 0), (px, knee_y - 4))
        cv.draw(sh, Ms, exposure=exp * .8, lit=lit, edge_k=0.2)
        cv.draw(A.woman_body, M, exposure=exp, lit=lit)
        arm_dir = 90.0 - 80.0 * smooth(reach)          # 90 = hanging, 10 = pointing at the porch
        Ma = aff(A_scale_rot(s, arm_dir - 90.0), sho, M[:2, :2] @ sho + M[:2, 2])
        cv.draw(A.woman_arm, Ma, exposure=exp, lit=lit)
        if reach > 0.05:
            hand_at_end(cv, A, Ma[:2, :2] @ end + Ma[:2, 2], arm_dir + 6, exp, lit, reach)
        return
    # stepping aside and sitting down beside the door, knees up, back to the wall
    u = smooth(sit)
    feet = lerp(WALL_BASE + 2, 600.0, smooth(sit * 1.6))
    stand_hip = feet - 82 - s * (ws.h - 206)
    hip = np.array([px, lerp(stand_hip, feet - 6, u)])
    # thigh: the lower cut, swung from hanging (90 deg) to forward and a little up (-25 deg)
    th_dir = lerp(90.0, -28.0, u)
    lo = A.woman_lower
    Ml = aff(A_scale_rot(s, th_dir - 90.0), (75, 203), hip)
    thigh_len = s * (ws.h - 203)
    knee = hip + thigh_len * np.array([math.cos(math.radians(th_dir)), math.sin(math.radians(th_dir))])
    # shins: from the knee down to the boards
    sh = A.woman_shins
    foot = np.array([knee[0] + 18 * u, feet])
    v = foot - knee; ln = max(8.0, np.linalg.norm(v)); ang = math.degrees(math.atan2(v[1], v[0])) - 90.0
    Lsh = A_scale_rot(1.0, ang) @ np.diag([s, ln / sh.h])
    cv.draw(sh, aff(Lsh, (sh.w * .45, 0), knee), exposure=exp * .8, lit=lit, edge_k=0.2)
    cv.draw(lo, Ml, exposure=exp, lit=lit)
    up = A.woman_upper
    Mu = aff(A_scale_rot(s, -5 * u), (75, 203), hip + np.array([-2, 2]))
    cv.draw(up, Mu, exposure=exp, lit=lit)
    # the arm, and the hand offered low toward the porch (score: hand 'low' from 6.8 s)
    arm_dir = lerp(90.0, 48.0, smooth(low)) - 4 * u
    Ma = aff(A_scale_rot(s, arm_dir - 90.0), sho, Mu[:2, :2] @ sho + Mu[:2, 2])
    cv.draw(A.woman_arm, Ma, exposure=exp, lit=lit)
    if low > 0.02:
        hand_at_end(cv, A, Ma[:2, :2] @ end + Ma[:2, 2], lerp(arm_dir, 22.0, smooth(low)), exp, lit, low)


def hand_at_end(cv, A, wrist_dst, direction, exp, lit, amt):
    """the Door to Heaven hand (cut from its card), mirrored so the fingers point along `direction` (deg, 0 = right,
    positive = down), its forearm's cut end at the sleeve's end."""
    hd = A.w['hand'].mirrored()
    wrist = (hd.w - 228.0, 52.0)
    M = aff(A_scale_rot(0.40, direction - 7.0), wrist, wrist_dst)
    cv.draw(hd, M, exposure=exp * 1.3, lit=lit * 1.15, opacity=min(1, amt * 3), tag='hand')


# ------------------------------------------------------------------ choreography
def dog_plan(i):
    """which drawing the dog is at frame i (a pure function of the score's state and act values + our timing)."""
    f = FR[i]; t = f['t']; d = f['dog']; a = d['act']; st = d['state']
    return t, d, a, st


class Choreo:
    def __init__(self, A):
        self.A = A; self.rig = DogRig(A)
        # walk drawing index driven by distance travelled (score x); registered positions so feet hold
        self.walk_state = None

    def walk_pose(self, dist_px, mirror_dir):
        """distance travelled in canvas px since the walk started -> (drawing index, x offset of its registered anchor)"""
        rig = self.rig
        s = DOG_S
        steps = [rig.walk_u[WALK[k + 1]] - rig.walk_u[WALK[k]] for k in range(len(WALK) - 1)]
        steps.append(steps[-1])
        stride_src = sum(steps)
        cyc = dist_px / s / stride_src
        n = int(math.floor(cyc)); rem = (cyc - n) * stride_src
        acc = 0.0; k = 0
        while k < len(WALK) - 1 and acc + steps[k] <= rem:
            acc += steps[k]; k += 1
        # the drawing's registered position: cycle start + accumulated source travel (no sliding within a drawing)
        pos = (n * stride_src + acc) * s
        return WALK[k], pos

    def frame(self, cv, i, o):
        A = self.A; rig = self.rig
        t, d, a, st = dog_plan(i)
        x = d['x']
        fy = feet_y(x)
        L = cv.light
        lit = 1.0
        exp = 0.72 + 0.43 * smooth((x - 1.0) / 1.6)   # round 2: the dog out on the dusk porch is lifted; near the lit door the light carries it
        info = {'drawing': None}
        # timeline (s): measured choice onsets are taken from the render, these are the plan's switch points
        if t < 1.0:
            k = WATCH[int(t * 2.2) % len(WATCH)]
            rig.place_frame(cv, k, False, X(x), fy, exp, lit)
            info['drawing'] = ('frame', k, False)
        elif t < 2.333:
            # backing away: the archive dog's walk, mirrored to face the door and played backwards, head low
            dist = (X(x) - X(3.0))
            # backwards: drawing order reversed as distance grows
            k, pos = self.walk_pose(dist, -1)
            k = WALK[len(WALK) - 1 - WALK.index(k)]
            rig.place_frame(cv, k, True, X(3.0) + pos + 0.0, fy, exp, lit)
            info['drawing'] = ('frame', k, True)
        elif t < 3.417:
            k = WATCH[int((t - 2.333) * 2.2) % len(WATCH)]
            rig.place_frame(cv, k, False, X(x), fy, exp, lit)
            info['drawing'] = ('frame', k, False)
        elif t < 3.86:
            # the refusal: the real dog turning away, drawing by drawing
            n = len(TURN_AWAY)
            u = (t - 3.417) / (3.86 - 3.417)
            k = TURN_AWAY[min(n - 1, int(u * n))]
            sf = 1.0 if k < 20 else 1.1
            rig.place_frame(cv, k, False, X(x), fy, exp, lit, s=DOG_S * sf)
            info['drawing'] = ('frame', k, False)
        elif t < 4.45:
            k = 44
            rig.place_frame(cv, k, False, X(x), fy, exp, lit, s=DOG_S * 1.1)
            info['drawing'] = ('frame', k, False)
        elif t < 7.458:
            # lies down with its back to the door (puppet, mirrored): straight into the descent, chin onto its paws
            u = min(1.0, max(0.0, (t - 4.45) / 0.5)); lie = 0.4 + 0.6 * (1 - (1 - u) ** 2)
            rig.puppet(cv, X(x), fy, True, lie, a['rest'], a['head'], 0, a['tail'], 0, t, exp, lit, breathe=math.sin(t * 2.4))
            info['drawing'] = ('puppet', True, lie)
        elif t < 8.45:
            # turns back to look: it is up and its head comes round, real cuts mirrored (head toward the door), then side
            n = len(TURN_BACK)
            u = (t - 7.458) / (8.2 - 7.458)
            k = TURN_BACK[min(n - 1, int(u * n))]
            if isinstance(k, tuple):
                rig.place_frame(cv, k[1], True, X(x), fy, exp, lit, s=DOG_S * 1.1)
            else:
                rig.place_frame(cv, k, False, X(x), fy, exp, lit)
            info['drawing'] = ('turnback', str(k))
        elif t < 14.708:
            k = WATCH[int((t - 8.45) * 1.6) % len(WATCH)]
            rig.place_frame(cv, k, False, X(x), fy, exp, lit)
            info['drawing'] = ('frame', k, False)
        elif t < 23.792:
            # coming, head low: the archive dog's own walk mirrored toward the door, drawing chosen by distance
            dist = X(4.0) - X(x)
            k, pos = self.walk_pose(dist, 1)
            ax = X(4.0) - pos
            rig.place_frame(cv, k, True, ax, fy, exp, lit)
            info['drawing'] = ('frame', k, True)
        else:
            # at the sill: lies down across it, half in the doorway (puppet, facing in)
            u = min(1.0, max(0.0, (t - 23.792) / 0.5)); lie = 0.4 + 0.6 * (1 - (1 - u) ** 2)   # straight into the descent
            head = a['head']; rest = a['rest']; look = a['look']
            rig.puppet(cv, X(x), fy, False, lie, rest, head, look, a['tail'], a['wag'], t, exp, lit, breathe=math.sin(t * 2.0) * (1 if t > 24.6 else 0))
            info['drawing'] = ('puppet', False, lie, look > .5)
        return info


# ------------------------------------------------------------------ captions (the typed prompts, our way: a cut slip)
def caption(img, text, alpha):
    if not text or alpha <= 0.01:
        return img
    d = ImageDraw.Draw(img, 'RGBA')
    f = ImageFont.truetype(os.path.join(FONT_DIR, 'f14.woff2'), 19)
    tw = d.textlength(text, font=f)
    x, y = 64, 662
    a = int(200 * alpha)
    d.rectangle([x - 12, y - 8, x + tw + 12, y + 26], fill=(196, 200, 212, int(a * .16)), outline=(200, 210, 230, int(a * .5)))
    d.text((x, y), text, font=f, fill=(214, 220, 232, a))
    return img


def prompt_at(t):
    cur = ''; t0 = -9
    for pt, txt in SCORE.get('prompts_list', []):
        pass
    for f in SCORE['frames']:
        pass
    return cur


PROMPTS = [(0.4, 'the person calls: Come here.'), (2.8, 'call again, and reach for it.'), (4.8, 'sit down beside the door.'),
           (5.8, 'open the door.'), (6.4, 'offer a hand, low.'), (7.0, "say it softly: it's all right."), (25.8, 'come in.')]


def prompt_for(t):
    cur = None
    for k, (pt, txt) in enumerate(PROMPTS):
        if t >= pt:
            nxt = PROMPTS[k + 1][0] if k + 1 < len(PROMPTS) else 99
            dur = min(nxt - pt, 2.6)
            if t < pt + dur:
                u = min(1, (t - pt) / .25, (pt + dur - t) / .35)
                cur = (txt, max(0, u))
    return cur


# ------------------------------------------------------------------ main
def grain(rng, k=0.010):
    g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)
    return g * k


def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot((xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2))
    return (1 - 0.32 * np.clip(r - 0.45, 0, 1) ** 1.5).astype(np.float32)


def render(frames, outdir, measure_path):
    A = Assets()
    bg = build_background(A)
    ch = Choreo(A)
    vig = vignette()
    os.makedirs(outdir, exist_ok=True)
    meas = {}
    if os.path.exists(measure_path):
        meas = {int(k): v for k, v in json.load(open(measure_path)).items()}
    for i in frames:
        f = FR[i]; t = f['t']
        o = door_open(t)
        cv = Canvas(bg)
        cv.light = light_field(t, o)
        draw_doorway(cv, A, t, o)
        draw_frame_stone(cv, A, o)
        floor_spill(cv, o)
        # the person (in the doorway, or beside the door)
        draw_person(cv, A, t, f, o)
        # the dog: shadow first (from its own rendered alpha on a scratch canvas), then the cut
        scratch = Canvas(np.zeros((H, W, 3), np.float32)); scratch.light = cv.light; scratch.t = t
        info = ch.frame(scratch, i, o)
        dm = scratch.masks.get('_cov', np.zeros((H, W), np.float32))
        hm = scratch.masks.get('head', np.zeros((H, W), np.float32))
        # contact + cast shadow on the boards: the dog's own alpha flattened onto the floor, away from the light
        ys, xs = np.nonzero(dm > .5)
        if len(ys):
            foot = ys.max()
            sh = np.zeros((H, W), np.float32)
            img = Image.fromarray((dm * 255).astype(np.uint8))
            flat = img.resize((W, max(1, int(H * 0.16))))
            fl = np.array(flat).astype(np.float32) / 255
            yoff = int(foot - fl.shape[0] * (foot / H)) + 2
            push = int(18 + 60 * o)
            y0 = max(0, yoff); y1 = min(H, yoff + fl.shape[0])
            sh[y0:y1, :] = fl[: y1 - y0]
            sh = np.roll(sh, push, 1)
            sh = np.array(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
            fm = np.zeros((H, W), np.float32); fm[int(WALL_BASE):int(PORCH_FRONT), :int(STEPS_X)] = 1
            cv.rgb *= (1 - 0.55 * sh * fm)[..., None]
        # composite the dog: scratch holds premultiplied colour over black; masks give coverage
        cov = np.clip(dm, 0, 1)
        # scratch.rgb was composited over black, so rgb = col * cov  -> over: dst*(1-cov) + scratch
        cv.rgb = cv.rgb * (1 - cov[..., None]) + scratch.rgb
        out = np.clip(cv.rgb * vig[..., None], 0, 1)
        rng = np.random.default_rng(1000 + i)
        out = np.clip(out + grain(rng)[..., None] * (0.4 + out), 0, 1)
        img = Image.fromarray((out ** (1 / 1.15) * 255).astype(np.uint8))
        pr = prompt_for(t)
        if pr:
            img = caption(img, pr[0], pr[1])
        img.save(os.path.join(outdir, 's%04d.jpg' % i), quality=90)
        # ---- measurement (from the rendered dog layers)
        m = {'i': i, 't': round(t, 4)}
        if len(ys):
            m['cx'] = float(xs.mean()); m['cy'] = float(ys.mean()); m['top'] = int(ys.min()); m['bottom'] = int(ys.max())
            m['left'] = int(xs.min()); m['right'] = int(xs.max()); m['area'] = int((dm > .5).sum())
            hy, hx = np.nonzero(hm > .5)
            m['head_cx'] = float(hx.mean()) if len(hx) else None
            m['head_cy'] = float(hy.mean()) if len(hy) else None
            inside = (xs < DOOR_R).mean()
            m['frac_inside_frame'] = float(inside)
            from straight import longest_runs
            y0b, y1b, x0b, x1b = max(0, ys.min() - 2), ys.max() + 3, max(0, xs.min() - 2), xs.max() + 3
            m['straight_run_px'] = longest_runs(dm[y0b:y1b, x0b:x1b] > .5)   # longest h/v boundary run (canvas px)
        m['drawing'] = [str(v) for v in info['drawing']] if info['drawing'] else None
        mk = getattr(scratch, 'marks', None)
        if mk:
            m['nose'] = mk['nose']; m['neck'] = mk['neck']; m['tail'] = mk['tail']
        m['head_piece'] = getattr(scratch, 'head_piece', None)
        m['door_open'] = round(o, 3)
        meas[i] = m
        if i % 48 == 0:
            print('frame', i, t, info['drawing'], flush=True)
    json.dump({str(k): meas[k] for k in sorted(meas)}, open(measure_path, 'w'))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', default='0:768')
    ap.add_argument('--out', default=os.path.join(C, 'frames'))
    ap.add_argument('--measure', default=os.path.join(C, 'measure.json'))
    ap.add_argument('--times', default=None)
    a = ap.parse_args()
    if a.times:
        fr = [int(round(float(x) * 24)) for x in a.times.split(',')]
    else:
        lo, hi = [int(v) for v in a.frames.split(':')]
        fr = list(range(lo, hi))
    render(fr, a.out, a.measure)
