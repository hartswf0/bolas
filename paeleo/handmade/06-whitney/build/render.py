"""SCION 06 · Whitney — the renderer (light points on a dusk field) and the measurer.

python3 render.py               renders the 32 s scene to build/cache/scene.mp4 and writes ../trace.json
python3 render.py --test 3.6 9  renders single frames to ../proof/test_<t>.png (with 8 frames of persistence before)

Every mark is a point of light: a dot splatted (bilinear) into a float light buffer that decays frame to frame
(the persistence of Whitney's slit-scan and oscilloscope light), blurred slightly for the dot and once more for the glow.
The camera is fixed. The trace is measured from the projected points of the dog that were actually drawn.
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import harmonic as H
import figures as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, 'cache')
W, Hh = 1280, 720

# ---------------------------------------------------------------- camera
# wide and fixed until the approach (0-14.8 s); during the approach it dollies with the dog toward the sill (eased),
# and is fixed again, close, from 23.6 s. x_world_measured in the trace back-projects through each frame's camera.
WIDE = dict(cam=np.array([3.0, 0.85, 5.2]), tgt=np.array([1.50, 0.80, 0.0]), focal=1000.0, cx=640.0, cy=388.0)
CLOSE = dict(cam=np.array([2.0, 1.45, 3.4]), tgt=np.array([-0.35, 0.40, 0.0]), focal=1050.0, cx=640.0, cy=400.0)
CAM = TGT = FOCAL = CX = CY = _f = _r = _u = None


def cam_mix(t):
    return float(H.smooth(14.9, 23.7, t))


def set_cam(t):
    global CAM, TGT, FOCAL, CX, CY, _f, _r, _u
    s = cam_mix(t)
    CAM = WIDE['cam'] * (1 - s) + CLOSE['cam'] * s
    TGT = WIDE['tgt'] * (1 - s) + CLOSE['tgt'] * s
    FOCAL = WIDE['focal'] * (1 - s) + CLOSE['focal'] * s
    CX = WIDE['cx'] * (1 - s) + CLOSE['cx'] * s; CY = WIDE['cy'] * (1 - s) + CLOSE['cy'] * s
    _f = TGT - CAM; _f = _f / np.linalg.norm(_f)
    _r = np.cross(_f, [0, 1, 0]); _r = _r / np.linalg.norm(_r)
    _u = np.cross(_r, _f)


set_cam(0.0)


def project(P):
    d = P - CAM
    x = d @ _r; y = d @ _u; z = d @ _f
    z = np.maximum(z, 0.1)
    return CX + FOCAL * x / z, CY - FOCAL * y / z, z


def unproject_u(sx, sy, plane_z=0.0):
    """ray through a screen point meets the plane z = plane_z: returns world u (metres along the porch)."""
    d = _f + (sx - CX) / FOCAL * _r - (sy - CY) / FOCAL * _u
    s = (plane_z - CAM[2]) / d[2]
    p = CAM + s * d
    return float(p[0]), float(p[1])


# ---------------------------------------------------------------- the compositional field (static points)
def lattice():
    pts, col, w = [], [], []
    def add(P, c, ww):
        P = np.asarray(P, float).reshape(-1, 3); pts.append(P)
        col.append(np.broadcast_to(np.asarray(c, float), P.shape)); w.append(np.full(len(P), ww))
    # porch floor: plank lines of dots, u 0 .. 4.45, z -1.7 .. 1.7
    zs = np.arange(-1.7, 2.75, 0.2); us = np.arange(0.02, 4.46, 0.1)
    U, Z = np.meshgrid(us, zs)
    add(np.stack([U.ravel(), np.zeros(U.size), Z.ravel()], 1), [0.55, 0.52, 0.78], 0.11)
    # porch edge and steps (porch end at u = 4.45, the score's 4.9)
    for k, (du, dy) in enumerate([(0, 0), (0.28, -0.18), (0.56, -0.36)]):
        z = np.arange(-1.7, 0.81, 0.04)
        add(np.stack([np.full(z.size, 4.47 + du), np.full(z.size, dy), z], 1), [0.7, 0.66, 0.92], 0.30 - 0.08 * k)
    # facade (plane u = 0): wall lattice with the door opening (z in [-0.45, 0.45], y < 2.05) left open
    zs = np.arange(-4.4, 2.0, 0.2); ys = np.arange(0.0, 2.95, 0.2)
    Z, Y = np.meshgrid(zs, ys)
    m = ~((np.abs(Z) < 0.5) & (Y < 2.1))
    add(np.stack([np.zeros(m.sum()), Y[m], Z[m]], 1), [0.50, 0.46, 0.75], 0.08)
    # door frame: jambs, lintel (outer face u = 0 and inner face u = -0.30) and the sill
    for uu, ww in ((0.0, 0.55), (-0.30, 0.22)):
        y = np.arange(0, 2.06, 0.025)
        for zz in (-0.46, 0.46):
            add(np.stack([np.full(y.size, uu), y, np.full(y.size, zz)], 1), [0.85, 0.80, 1.0], ww)
        z = np.arange(-0.46, 0.47, 0.025)
        add(np.stack([np.full(z.size, uu), np.full(z.size, 2.06), z], 1), [0.85, 0.80, 1.0], ww)
    z = np.arange(-0.46, 0.47, 0.02)
    for uu, yy in ((0.06, 0.05), (-0.30, 0.05), (0.06, 0.0)):
        add(np.stack([np.full(z.size, uu), np.full(z.size, yy), z], 1), [1.0, 0.95, 0.85], 0.75)
    u = np.arange(-0.30, 0.07, 0.025)
    for zz in (-0.46, 0.46):
        add(np.stack([u, np.full(u.size, 0.05), np.full(u.size, zz)], 1), [1.0, 0.95, 0.85], 0.6)
    # porch post (near the steps, far side)
    y = np.arange(0, 2.95, 0.035)
    add(np.stack([np.full(y.size, 4.3), y, np.full(y.size, -1.55)], 1), [0.6, 0.56, 0.85], 0.35)
    P = np.concatenate(pts); C = np.concatenate(col); Wt = np.concatenate(w)
    return P, C, Wt


def interior():
    """the room behind the door, in point-lines: floorboards running into the room, a back wall of horizontal lines,
    lit only when the door opens."""
    zs = np.arange(-4.4, 1.61, 0.05); ys = np.arange(0.06, 2.9, 0.16)
    Z, Y = np.meshgrid(zs, ys)
    back = np.stack([np.full(Z.size, -2.6), Y.ravel(), Z.ravel()], 1)
    us = np.arange(-2.58, -0.31, 0.04); zs2 = np.arange(-4.4, 1.61, 0.15)
    U, Z2 = np.meshgrid(us, zs2)
    floor = np.stack([U.ravel(), np.zeros(U.size), Z2.ravel()], 1)
    return np.concatenate([back, floor])


def through_opening(P):
    """True where the camera sees the point through the door opening (both faces of the frame): the wall hides the rest."""
    ok = np.ones(len(P), bool)
    for uu in (0.0, -0.30):
        s = (uu - CAM[0]) / (P[:, 0] - CAM[0] + 1e-9)
        Q = CAM[None] + s[:, None] * (P - CAM[None])
        ok &= (np.abs(Q[:, 2]) < 0.46) & (Q[:, 1] >= -0.01) & (Q[:, 1] <= 2.06)
    return ok | (P[:, 0] >= -0.02)


def hills():
    """the horizon beyond the porch: a sum of three periodic functions, as dots."""
    x = np.linspace(0, W, 420)
    y = 455 - 18 * np.sin(x / 140 + 0.4) - 9 * np.sin(x / 61 + 1.3) - 5 * np.sin(x / 23)
    return x, y


def sky():
    y = np.linspace(0, 1, Hh)[:, None]
    top = np.array([0.025, 0.03, 0.085]); mid = np.array([0.10, 0.06, 0.16]); low = np.array([0.24, 0.10, 0.17])
    a = np.clip(y / 0.62, 0, 1)
    c = top * (1 - a) + mid * a
    b = np.clip((y - 0.45) / 0.2, 0, 1)
    c = c * (1 - b) + low * b
    g = np.clip((y - 0.64) / 0.1, 0, 1)
    c = c * (1 - g) + np.array([0.03, 0.025, 0.06]) * g
    return np.broadcast_to(c[:, None, :], (Hh, W, 3)).astype(np.float32).copy()


rng = np.random.default_rng(6)
STARS = np.stack([rng.uniform(0, W, 140), rng.uniform(0, 330, 140)], 1)
STAR_K = rng.integers(1, 7, 140)
STAR_PH = rng.uniform(0, 2 * math.pi, 140)


# ---------------------------------------------------------------- splatting
def splat(buf, sx, sy, col, w):
    m = (sx >= 0) & (sx < W - 1) & (sy >= 0) & (sy < Hh - 1) & (w > 0)
    sx, sy, col, w = sx[m], sy[m], col[m], w[m]
    x0 = np.floor(sx).astype(int); y0 = np.floor(sy).astype(int)
    fx = sx - x0; fy = sy - y0
    flat = buf.reshape(-1, 3)
    for dx, dy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
        idx = (y0 + dy) * W + (x0 + dx)
        for ch in range(3):
            flat[:, ch] += np.bincount(idx, weights=ww * w * col[:, ch], minlength=W * Hh)


def blur(img, k):
    """separable binomial blur, k passes of [1 2 1]/4 along each axis."""
    a = img
    for _ in range(k):
        a = a.copy(); a[1:-1] = 0.25 * a[:-2] + 0.5 * a[1:-1] + 0.25 * a[2:]
        a[:, 1:-1] = 0.25 * a[:, :-2] + 0.5 * a[:, 1:-1] + 0.25 * a[:, 2:]
    return a


def up4(small):
    """float upsample x4 (repeat, then a light blur): no 8-bit banding."""
    return blur(np.repeat(np.repeat(small, 4, 0), 4, 1), 2)


def glow(buf):
    small = buf.reshape(Hh // 4, 4, W // 4, 4, 3).mean((1, 3))
    return up4(blur(small, 6))


# ---------------------------------------------------------------- the voice as wavefronts
VOICE = [  # (onset, duration, kind, text, syllable onsets)
    (1.05, 0.95, 'call', 'Come here!', [1.05, 1.40]),
    (3.45, 0.95, 'call', 'Come here!', [3.45, 3.80]),
    (7.50, 1.35, 'soft', "It's all right.", [7.50, 7.74, 8.10]),
    (10.50, 1.10, 'soft', "It's all right.", [10.50, 10.74, 11.05]),
    (26.45, 0.85, 'soft', 'Come in.', [26.45, 26.80]),
]
SPEED = {'call': 3.6, 'soft': 1.1}


def wavefronts():
    out = []
    for on, dur, kind, text, syl in VOICE:
        for s in syl:
            n = 3 if kind == 'call' else 1
            for k in range(n):
                out.append((s + 0.07 * k, kind))
    return out


WAVES = wavefronts()


class Scene:
    def __init__(self):
        self.S = H.load_score()
        self.B = H.bank(self.S)
        self.Q = H.choreography(self.S, self.B)
        self.Pq = H.person(self.S, self.B)
        self.Dq = H.door(self.S, self.B)
        self.static = lattice()
        self.inner = interior()
        self.sky = sky()
        self.hx, self.hy = hills()
        self.agit = self.agitation()
        self.light = np.zeros((Hh, W, 3), np.float32)     # the field: long persistence (accumulation)
        self.body = np.zeros((Hh, W, 3), np.float32)      # bodies and voices: short persistence (no smear)
        F = os.path.join(CACHE, 'Literata400i.ttf')
        self.font_call = ImageFont.truetype(F, 34)
        self.font_soft = ImageFont.truetype(F, 22)

    def agitation(self):
        """a call's wavefront striking the dog: impulses at arrival (event envelopes), plus the reaching hand."""
        t = H.T; a = np.zeros(H.N)
        for te, kind in WAVES:
            if kind != 'call':
                continue
            i0 = int(te * H.FPS)
            mouth_u = self.Pq['u'][i0] + 0.1
            dist = abs(self.Q['u'][i0] - mouth_u)
            th = te + dist / SPEED['call']
            a += np.where(t >= th, 0.55 * np.exp(-(t - th) / 0.45), 0)
        a += 0.35 * self.Pq['reach']
        return np.clip(a, 0, 1)

    def qd(self, i):
        Q = self.Q
        return {k: (Q[k][i] if hasattr(Q[k], '__len__') and not isinstance(Q[k], str) else Q[k]) for k in Q}

    def frame(self, i):
        t = i / H.FPS; B = self.B
        set_cam(t)
        G.PSI = float(B['psi'][i])
        lock = float(B['lock'][i])
        self.isx, self.isy, self.isz = project(self.inner)
        th_h, th_d = B['th_house'][i], B['th_dog'][i]
        light = self.Dq['light'][i]; dens = B['density'][i]
        L = self.light
        L *= 0.42 + 0.3 * dens      # persistence grows with density (accumulation), shrinks in the release
        Bd = self.body
        Bd *= 0.22
        # ---- static field: brightness breathes at the house rate (the 2 of the 3:2), harmonic per row
        P, C, Wt = self.static
        pulse = 0.85 + 0.15 * np.cos(th_h - 0.9 * P[:, 0])
        wt = Wt * pulse
        # the porch planks carry the 3:2 relation: their dots ripple with psi (drifting under the calls, still when locked)
        P = P.copy()
        plank = (P[:, 1] == 0) & (P[:, 0] > 0)
        P[plank, 0] += 0.045 * np.sin(5.0 * P[plank, 2] + 2.0 * P[plank, 0] - B['psi'][i])
        self.sx0, self.sy0, self.sz0 = project(P)
        # door light on the porch floor: a fan from the doorway, carrying a wave outward at the house rate
        fl = (P[:, 1] == 0) & (P[:, 0] > 0) & (P[:, 0] < 4.46)
        fan = (np.abs(P[:, 2]) < 0.48 + 0.30 * P[:, 0]) & fl
        # the light's wave runs out along the porch at 3/2 of the house phase; it reaches further as the lock grows,
        # and when locked its crest arrives at the dog exactly as the dog's breath peaks (2 theta_dog = 3 theta_house)
        du = P[:, 0] - self.Q['u'][i]
        wave = 0.5 + 0.5 * np.cos(2.4 * du - 1.5 * th_h)
        reach = 1.2 + 3.0 * lock * float(H.smooth(6.5, 9.0, t))
        boost = np.where(fan, light * 3.4 * np.exp(-P[:, 0] / reach) * wave ** 2, 0)
        cols = C * (1 - np.clip(boost, 0, 1)[:, None] * 0.6) + np.array([1.0, 0.78, 0.45]) * np.clip(boost, 0, 1)[:, None] * 0.6
        splat(L, self.sx0, self.sy0, cols, (wt + boost * 0.5) * 0.9)
        # interior
        IP = self.inner
        # cutaway: the room's floor is seen whole (the facade is a dot lattice); its back wall only through the door
        vis = np.where(IP[:, 1] == 0, 1.0, np.where(through_opening(IP), 1.0, 0.25))
        onfloor = IP[:, 1] == 0
        lamp = np.exp(-((IP[:, 1] - 1.5) ** 2 + (IP[:, 2] + 0.5) ** 2) / 0.35)
        dh = np.sqrt((IP[:, 0] + 2.4) ** 2 + (IP[:, 2] + 3.6) ** 2)          # distance from the hearth
        fall = np.where(onfloor, 0.10 + 1.4 * np.exp(-dh / 1.2) + 0.5 * np.exp(-(IP[:, 0] + 0.3) ** 2 / 0.5 - IP[:, 2] ** 2 / 0.6),
                        0.25 + 1.0 * np.exp(-dh / 1.0))
        ib = light * (0.75 + 0.25 * np.cos(th_h - 1.2 * IP[:, 0])) * fall * vis
        splat(L, self.isx, self.isy, np.tile([1.0, 0.76, 0.42], (len(IP), 1)), ib * 1.1)
        # the hearth at the back of the room, low: a small fire of points on a Lissajous knot, flickering at the house rate
        if light > 0.05:
            s_ = np.linspace(0, 2 * math.pi, 140, endpoint=False)
            hp_ = np.stack([np.full(140, -2.45), 0.05 + 0.30 * np.abs(np.sin(2 * s_ + 0.7 * th_h)) * (0.8 + 0.2 * np.sin(3 * s_)),
                            -3.6 + 0.30 * np.sin(3 * s_ + th_h)], 1)
            sx, sy, _ = project(hp_)
            splat(L, sx, sy, np.tile([1.0, 0.62, 0.28], (140, 1)), np.full(140, light * 1.1))
            self.hearth = hp_
        # light leaving the door: points on straight trajectories, one per (lane, phase), periodic in the house rate
        if light > 0.05:
            lanes = np.linspace(-0.42, 0.42, 9); ph = np.arange(14) / 14
            Lz, Ph = np.meshgrid(lanes, ph)
            s = (Ph + th_h / (2 * math.pi) * 0.5) % 1.0
            pu = -0.3 + 3.6 * s; py = 1.6 * (1 - s) ** 1.6 + 0.02; pz = Lz * (1 + 0.6 * s)
            pp = np.stack([pu.ravel(), py.ravel(), pz.ravel()], 1)
            sx, sy, _ = project(pp)
            splat(L, sx, sy, np.tile([1.0, 0.82, 0.5], (len(pp), 1)), (light * 0.55 * (1 - s.ravel()) ** 1.2))
        # the lit opening: a field of warm points filling the door, breathing at the house rate
        if light > 0.02:
            gz2 = np.arange(-0.43, 0.44, 0.045); gy2 = np.arange(0.03, 2.04, 0.045)
            Gz2, Gy2 = np.meshgrid(gz2, gy2)
            op = np.stack([np.full(Gz2.size, -0.34), Gy2.ravel(), Gz2.ravel()], 1)
            sx, sy, _ = project(op)
            pw = light * (0.55 + 0.15 * np.cos(th_h - 1.5 * op[:, 1])) * np.exp(-op[:, 1] / 0.35) * 0.8   # only a low glow at the sill: the room itself is the light
            haze = np.zeros_like(L)
            splat(haze, sx, sy, np.tile([1.0, 0.72, 0.40], (len(op), 1)), pw)
            # the light falling out across the sill onto the porch
            fu = np.arange(-0.3, 2.6, 0.05); fz = np.arange(-0.6, 0.61, 0.05)
            FU, FZ = np.meshgrid(fu, fz)
            m = np.abs(FZ) < 0.46 + 0.28 * np.maximum(FU, 0)
            fp = np.stack([FU[m], np.zeros(m.sum()), FZ[m]], 1)
            sx, sy, _ = project(fp)
            splat(haze, sx, sy, np.tile([1.0, 0.70, 0.38], (len(fp), 1)), light * 0.35 * np.exp(-np.maximum(fp[:, 0], 0) / 1.0))
            sx, sy, _ = project(np.array([[-2.45, 0.2, -3.6]]))
            splat(haze, np.array([sx[0] + dx for dx in (-6, 0, 6) for _ in (0,)]), np.full(3, sy[0]), np.tile([1.0, 0.6, 0.3], (3, 1)), np.full(3, light * 25.0))
            self.haze = haze
        else:
            self.haze = None
        # the door leaf: a panel of dots hinged at (u -0.30, z -0.46), swinging inward
        a = self.Dq['angle'][i]
        gz = np.linspace(0, 0.9, 10); gy = np.linspace(0.02, 2.02, 24)
        Gz, Gy = np.meshgrid(gz, gy)
        leaf = np.stack([-0.30 - Gz.ravel() * math.sin(a), Gy.ravel(), -0.46 + Gz.ravel() * math.cos(a)], 1)
        sx, sy, _ = project(leaf)
        splat(L, sx, sy, np.tile([0.85, 0.75, 0.95], (len(leaf), 1)), np.full(len(leaf), 0.35))
        # ---- the person
        pq = {k: self.Pq[k][i] for k in ('u', 'z', 'sit', 'reach', 'low', 'lean')}
        PD = G.person(pq, t, th_h)
        PD['w'] = PD['w'] * np.where(through_opening(PD['p']), 1.0, 0.8)
        self.draw_body(Bd, PD, 3.0 + 1.2 * light)
        # ---- the voice: wavefronts from the mouth (calls hot and fast, the soft voice slow, warm, faint)
        dog_u = self.Q['u'][i]
        for te, kind in WAVES:
            age = t - te
            if age < 0 or age > (1.6 if kind == 'call' else 3.2):
                continue
            r = 0.12 + SPEED[kind] * age
            mouth = PD['mouth']
            span = math.radians(28 if kind == 'call' else 62)
            n = int(10 + r * (30 if kind == 'call' else 40))
            ang = np.linspace(-span, span, n)
            # the plane of the arc: toward the dog (down slope) and up
            target = np.array([dog_u, 0.45, 0.0])
            dv = target - mouth; dv /= np.linalg.norm(dv)
            upv = np.array([0, 1.0, 0]) - dv[1] * dv; upv /= np.linalg.norm(upv)
            arc = mouth[None] + r * (np.cos(ang)[:, None] * dv[None] + np.sin(ang)[:, None] * upv[None])
            sx, sy, _ = project(arc)
            if kind == 'call':
                col = np.array([1.0, 0.35, 0.40]); wv = 1.7 * max(0, 1 - age / 1.6) ** 0.8
            else:
                col = np.array([1.0, 0.85, 0.55]); wv = 0.45 * max(0, 1 - age / 3.2)
            splat(Bd, sx, sy, np.tile(col, (n, 1)), np.full(n, wv))
        # ---- the dog
        q = self.qd(i)
        warm = 0.3 * light * float(np.exp(-max(q['u'], 0) / 2.0))
        D = G.dog(q, t, th_d, self.agit[i], warm, 0.55 + 0.45 * dens)
        dogb = np.zeros_like(Bd)
        meas = self.draw_body(dogb, D, 2.5 * (0.85 + 0.25 * (0.5 + 0.5 * math.cos(th_d))))
        Bd += dogb
        # the body stands against the light: a soft occlusion mask from the dog's own dots dims what is behind it
        sm = dogb.reshape(Hh // 4, 4, W // 4, 4, 3).sum((1, 3)).mean(2)
        sm = blur(sm[..., None], 3)[..., 0]
        occ = np.clip(up4(sm[..., None])[..., 0] * 1.6, 0, 0.85)[..., None]
        # ---- composite
        img = self.sky.copy()
        # stars pulse at integer multiples of the house rate (an oscillator bank on the sky)
        sb = 0.06 + 0.05 * np.cos(STAR_K * th_h + STAR_PH)
        st = np.zeros_like(img)
        splat(st, STARS[:, 0], STARS[:, 1], np.tile([0.8, 0.85, 1.0], (140, 1)), sb * 3)
        # the moon is the phase visualizer: the trail of (sin theta_dog, sin theta_house) over the last 6 s.
        # Locked at 3:2 it retraces one closed figure; drifting, it smears and turns.
        j0 = max(0, i - 144)
        jj = np.arange(j0, i + 1)
        mx = 1085 + 44 * np.sin(B['th_dog'][jj]); my = 118 - 44 * np.sin(B['th_house'][jj] + 0.6)
        age = (i - jj) / 144.0
        splat(st, mx, my, np.tile([0.95, 0.92, 0.80], (len(jj), 1)), 0.9 * (1 - age) ** 1.5 + 0.05)
        Lt = (L + st) * (1 - occ) + Bd
        dot = blur(Lt, 1)
        g = glow(Lt)
        lum = dot * 1.85 + g * 0.6
        if self.haze is not None:
            small = self.haze.reshape(Hh // 4, 4, W // 4, 4, 3).sum((1, 3))
            small = blur(small, 10)
            lum = lum + up4(small) * 2.0 * (1 - occ)
        out = 1 - (1 - img) * np.exp(-lum)
        im = Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8))
        self.subtitle(im, t, PD)
        return im, meas, D

    def draw_body(self, L, D, gain):
        sx, sy, sz = project(D['p'])
        v = CAM[None] - D['p']; v /= np.linalg.norm(v, axis=1, keepdims=True)
        ndv = (D['n'] * v).sum(1)
        # light-pen shading: rims (the silhouette) bright, the near face moderate, the far face dim
        # a tube seen end-on: its rings are not a silhouette, so the rim term fades with |tangent . view|
        endon = np.abs((D['tg'] * v).sum(1))
        b = 0.20 + 0.42 * np.clip(ndv, 0, 1) + 0.70 * np.exp(-(ndv / 0.32) ** 2) * (ndv > -0.55) * (1 - endon) ** 2
        b = np.where(D['part'] == 6, 1.0, b)
        splat(L, sx, sy, D['c'], D['w'] * b * gain * 0.62)
        return dict(sx=sx, sy=sy, part=D['part'])

    def subtitle(self, im, t, PD):
        d = ImageDraw.Draw(im)
        for on, dur, kind, text, syl in VOICE:
            if on - 0.05 <= t <= on + dur + 0.6:
                a = min(1, (t - on + 0.05) / 0.12) * (1 - max(0, (t - on - dur)) / 0.6)
                f = self.font_call if kind == 'call' else self.font_soft
                sx, sy, _ = project(PD['head'][None])
                col = (255, 120, 125) if kind == 'call' else (255, 224, 170)
                k = (0.95 if kind == 'call' else 0.6) * a
                c = tuple(int(v * k) for v in col)
                x, y = float(sx[0]) - 40, float(sy[0]) - 95
                d.text((x, y), text, font=f, fill=c)


def measure(i, meas, D, scene):
    """what the dog did in this frame, from its drawn points (screen) and the drawing's anchors."""
    sx, sy, part = meas['sx'], meas['sy'], meas['part']
    torso = part == 0
    xs, ys = float(sx[torso].mean()), float(sy[torso].mean())
    # facing: where the head is drawn relative to the rump, on screen (door is to the left)
    a = D['anchor']
    hx, _, _ = project(a['chest'][None]); rx, _, _ = project(a['rump'][None])
    head_pts = part == 2
    hsx = float(sx[head_pts].mean()) if head_pts.any() else float('nan')
    facing = 1 if float(hx[0]) < float(rx[0]) else -1
    nx, _, _ = project(a['nose'][None]); kx, _, _ = project(a['skull'][None])
    gaze = 1 if float(nx[0]) < float(kx[0]) else -1      # the drawn nose left of the drawn skull: looking toward the door
    loc = D['local']
    back_y = loc['withers_y']
    lying = loc['sh_y'] < 0.40
    posture = 'lying' if lying else ('crouched' if loc['sh_y'] < 0.53 else 'standing')
    u_meas, _ = unproject_u(xs, ys + 0.0) if False else (None, None)
    # x_world_measured: the drawn torso centre's screen point, back-projected onto the dog's walking plane (z = 0)
    # at the height of the torso anchor (the camera is fixed, so this equals reading the screen position in metres)
    ty = float(a['torso'][1])
    d = _f + (xs - CX) / FOCAL * _r - (ys - CY) / FOCAL * _u
    # solve CAM + s d with z = 0
    s = -CAM[2] / d[2]
    pw = CAM + s * d
    return dict(i=i, t=round(i / 24, 4), state=scene.Q['state'][i], x_score=round(float(scene.Q['x'][i]), 4),
                x_screen=round(xs, 2), y_screen=round(ys, 2), x_world_measured=round(float(pw[0]) + H.U_OFFSET, 4),
                facing=facing, gaze=gaze, posture=posture, head_screen_x=round(hsx, 2),
                head_below_back_m=round(back_y - loc['skull_y'], 3), shoulder_h_m=round(loc['sh_y'], 3),
                feet_planted=[k for k, v in D['contacts'].items() if v])


def seen_states(trace):
    """classify what a viewer can see from the drawn geometry alone (not from the score's labels), per frame:
    lie_down = lying posture at the sill; refuse = the drawn head points away from the door; retreat = crouched and
    moving away; approach = moving toward the door; else watch. Writes state_seen into each frame and returns the
    first frame of each of the six choices as seen."""
    xs = np.array([f['x_world_measured'] for f in trace])
    v = np.gradient(np.convolve(np.pad(xs, 3, mode='edge'), np.ones(7) / 7, 'valid')) * 24
    for f, vv in zip(trace, v):
        if f['posture'] == 'lying' and f['x_world_measured'] < 0.8:
            s = 'lie_down'
        elif f['gaze'] == -1:
            s = 'refuse'
        elif f['posture'] == 'crouched' and vv > 0.08:
            s = 'retreat'
        elif vv < -0.08:
            s = 'approach'
        else:
            s = 'watch'
        f['state_seen'] = s
    S = H.load_score(); out = []
    for c in S['choices']:
        hit = next((f for f in trace if f['t'] >= c['t'] - .5 and f['state_seen'] == c['to']), None)
        out.append(dict(t=c['t'], to=c['to'], seen_at=None if hit is None else hit['t'], dt=None if hit is None else round(hit['t'] - c['t'], 3)))
    json.dump(dict(about='the six choices as classified from the drawn geometry (render.py seen_states), not from the score labels',
                   choices=out), open(os.path.join(OUT, 'proof', 'seen_states.json'), 'w'), indent=1)
    print('seen', out)
    return out


def render_all():
    sc = Scene()
    path = os.path.join(CACHE, 'scene.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{Hh}',
                           '-r', '24', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-pix_fmt', 'yuv420p', path],
                          stdin=subprocess.PIPE)
    trace = []
    for i in range(H.N):
        im, meas, D = sc.frame(i)
        ff.stdin.write(im.tobytes())
        trace.append(measure(i, meas, D, sc))
        if i % 96 == 0:
            print('frame', i, flush=True)
    ff.stdin.close(); ff.wait()
    seen = seen_states(trace)
    B = sc.B
    json.dump(dict(about='SCION 06 Whitney: what the dog did, measured from the drawn points of each scene frame. '
                         'x_screen/y_screen: mean screen position of the drawn torso dots; x_world_measured: that screen point '
                         'back-projected through the fixed camera onto the walking plane, in score metres; facing: 1 when the '
                         'drawn chest is left of the drawn rump (toward the door), -1 when turned away; posture from the drawn '
                         'shoulder height; head_below_back_m: withers height minus skull height (positive = head below the back).',
                   fps=24, frames=trace,
                   oscillators=dict(psi=[round(float(v), 4) for v in B['psi']], dpsi=[round(float(v), 4) for v in B['dpsi']])),
              open(os.path.join(OUT, 'trace.json'), 'w'))
    print('wrote', path)


def render_test(times, prefix='test'):
    sc = Scene()
    os.makedirs(os.path.join(OUT, 'proof'), exist_ok=True)
    for tt in times:
        i = int(round(tt * 24))
        sc.light[:] = 0; sc.body[:] = 0
        for j in range(max(0, i - 8), i + 1):
            im, meas, D = sc.frame(j)
        im.save(os.path.join(OUT, 'proof', f'{prefix}_{tt:05.2f}.png'))
        print(tt, measure(i, meas, D, sc))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        render_test([float(v) for v in sys.argv[2:]])
    else:
        render_all()
