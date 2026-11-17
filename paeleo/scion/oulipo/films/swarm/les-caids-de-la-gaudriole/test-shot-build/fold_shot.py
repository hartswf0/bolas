"""TEST SHOT - THE FOLD (shot 5 into the shot 6 hold) + the light-box reveal.

Stop-motion of one printed sheet on a table, 12 exposures/s (each held 2 frames
at 24 fps). The sheet is the strip art from proposals/strip.py (Busch 1865
plates cut as puppets + pen.py lettering), printed onto the foraged paper scan.

#40 Physical tabletop capture: the sheet is a strip of paper whose cross-section
    curve is integrated from its creases: valley M and mountain A are curl bands
    of finite length (40 u while moving, pressed down to paper thickness at the
    landing), each facet carries a small inertial lag bend (free edge trails the
    unseen hand); per-exposure events (alpha, beta, bands, jitter, lamp gain,
    sound tick) are written to fold-events.json.
#45 Occlusion compositing: every strip of paper is its own warped RGBA piece with
    a camera-depth plane; a z-buffer decides who is in front in every exposure;
    the visible side (front ink / back with mirrored show-through) is chosen by
    the strip's normal; contact shadows are cast along the lamp direction with
    softness and strength from height; the light box is a transmission pass.
#8  Constraint sketchpad: B = 2M - A, the reflections x -> 2f - x, contact
    A == B and the seam rows are asserted (fixture()); the settled exposure is
    compared with V(x') pixel for pixel in an orthographic top render.
"""
import sys, os, math, json, hashlib, wave, subprocess
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, ".."))
FILMS = os.path.normpath(os.path.join(WORK, "../.."))
sys.path.insert(0, os.path.join(WORK, "proposals"))
sys.path.insert(0, FILMS)
import strip as S          # noqa: E402  (shared strip art, read-only)
from kit import Mix, RATE  # noqa: E402  (kit's sound bed; kit not edited)

MEDIA = os.path.join(FILMS, "sources/les-caids-de-la-gaudriole/test-shot")
SRC = os.path.join(FILMS, "sources/les-caids-de-la-gaudriole")
W, H = 960, 540
SS = 2                                   # supersample
FPS = 24
A, M, B, D = S.A, S.M, S.B, S.D
SW, SH = S.SW, S.SH
assert B == 2 * M - A and D == B - A and 2 * A - M > 0

LIGHT = np.array([-0.45, -0.35, 0.82]); LIGHT /= np.linalg.norm(LIGHT)
LIGHT_FLAT = LIGHT[2]


# ------------------------------------------------------------------ materials
def paper_scan(w, h, y0, seed_flip=False):
    """Real paper scan (Commons, J. Puckett, CC BY 2.0): keep its fibre and
    stain structure, neutralise its yellow to a near-white sheet."""
    p = Image.open(os.path.join(SRC, "paper.jpg")).convert("L")
    p = p.resize((w, int(p.height * w / p.width)), Image.LANCZOS)
    a = np.asarray(p, np.float32)[y0:y0 + h]
    if seed_flip:
        a = a[::-1]
    a = cv2.GaussianBlur(a, (0, 0), 0.6)
    a = (a - a.mean()) / (a.std() + 1e-6)
    base = 241 + 5.0 * np.clip(a, -3, 3)
    return np.stack([base, base - 2, base - 6], -1)       # |R-B| ~ 6


def table_texture():
    """Real wood scan (Commons, Bango Textures, CC0), greyed and darkened."""
    t = Image.open(os.path.join(SRC, "wood.jpg")).convert("L")
    a = np.asarray(t, np.float32)
    a = cv2.GaussianBlur(a, (0, 0), 1.0)
    a = 47 + 0.42 * (a - a.mean())
    a = np.clip(a, 18, 90)
    return np.stack([a * 1.03, a, a * 0.95], -1)


def build_art():
    r = S.build()
    sheet = np.asarray(r["sheet"].convert("L"))
    os.makedirs(MEDIA, exist_ok=True)
    path = os.path.join(MEDIA, "strip-art.png")
    Image.fromarray(sheet).save(path)
    sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
    return sheet, sha


def folded_V(sheet):
    """V(x') = Sheet(x') for x' < A, Sheet(x' + D) for x' >= A (x' in 0..SW-D)."""
    wf = SW - D
    out = np.empty((SH, wf), sheet.dtype)
    out[:, :A] = sheet[:, :A]
    out[:, A:] = sheet[:, A + D:A + D + (wf - A)]
    return out


# ------------------------------------------------------------------ geometry
def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def schedule(p):
    """Fold state at progress p (0..1): crease angles, band lengths, lag bends."""
    al = math.pi * ease(p / 0.80)
    be = math.pi * ease((p - 0.05) / 0.95)
    press = ease((p - 0.80) / 0.17)
    Lm = 40 - (40 - 1.6) * press
    La = 40 - (40 - 1.6) * press
    dp = 1e-3
    dal = (math.pi * ease((p + dp) / 0.80) - al) / dp
    dbe = (math.pi * ease((p + dp - 0.05) / 0.95) - be) / dp
    k0 = -0.42 * dbe / 4.0          # free edge trails the hand (rad of bend over F0)
    k1 = 0.16 * dal / 6.0 * math.sin(al)
    return al, be, Lm, La, k0, k1


def curve(al, be, Lm, La, k0, k1):
    """Cross-section of the sheet: returns u samples (descending) and X, z, phi.
    The part u >= M + Lm/2 lies flat on the table at X = u."""
    u = M + Lm / 2
    X, z, ph = u, 0.0, math.pi            # travel toward decreasing u
    us, Xs, zs, ps = [SW, u], [SW, X], [0.0, 0.0], [math.pi, math.pi]
    f1a, f1b = A + La / 2, M - Lm / 2
    f0b = A - La / 2
    while u > 0:
        inb = (M - Lm / 2) < u <= (M + Lm / 2) + 1e-9 or (A - La / 2) < u <= (A + La / 2) + 1e-9
        du = 0.25 if inb else 4.0
        nxt = max([b for b in (M - Lm / 2, A + La / 2, A - La / 2, 0.0) if b < u - 1e-9] or [0.0])
        du = min(du, u - nxt)
        um = u - du / 2
        if M - Lm / 2 <= um <= M + Lm / 2:
            kap = -al / Lm
        elif A - La / 2 <= um <= A + La / 2:
            kap = be / La
        elif f1a < um < f1b:
            kap = k1 / (f1b - f1a)
        elif um < f0b:
            w = (f0b - um) / f0b           # bend grows toward the free edge
            kap = k0 * 2 * w / f0b
        else:
            kap = 0.0
        pm = ph + kap * du / 2
        X += math.cos(pm) * du
        z += math.sin(pm) * du
        ph += kap * du
        u -= du
        us.append(u); Xs.append(X); zs.append(z); ps.append(ph)
    return np.array(us), np.array(Xs), np.array(zs), np.array(ps)


def strips_from(us, Xs, zs):
    """Group the samples into planar strips: fine in the bands, coarse on flats."""
    out = []
    i = 0
    n = len(us)
    out.append((0, 1))                       # the flat F2/F3 piece on the table
    i = 1
    while i < n - 1:
        j = i + 1
        while j < n - 1:
            # chord deviation test keeps each strip planar within 0.25 u
            a, b = np.array([Xs[i], zs[i]]), np.array([Xs[j + 1], zs[j + 1]])
            seg = b - a
            L = np.linalg.norm(seg) + 1e-9
            pts = np.stack([Xs[i:j + 2], zs[i:j + 2]], 1) - a
            dev = np.abs(pts[:, 0] * seg[1] - pts[:, 1] * seg[0]) / L
            if dev.max() > 0.25 or us[i] - us[j + 1] > 120:
                break
            j += 1
        out.append((i, j))
        i = j
    return out


# ------------------------------------------------------------------ camera
class Cam:
    def __init__(self, pos, tgt, foc):
        self.pos = np.asarray(pos, float)
        f = np.asarray(tgt, float) - self.pos
        self.f = f / np.linalg.norm(f)
        r = np.cross([0, 0, 1.0], self.f); self.r = r / np.linalg.norm(r)
        self.u = np.cross(self.f, self.r)
        self.foc = foc * SS

    def proj(self, P):
        P = np.atleast_2d(P) - self.pos
        zc = P @ self.f
        return np.stack([W * SS / 2 + self.foc * (P @ self.r) / zc,
                         H * SS / 2 - self.foc * (P @ self.u) / zc], 1), zc


def lerp(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


CAM_WIDE = ((1180.0, 2850.0, 2650.0), (1230.0, 180.0, 0.0), 1000.0)
CAM_CLOSE = ((1790.0, 1080.0, 2420.0), (1790.0, 462.0, 0.0), 1370.0)


# ------------------------------------------------------------------ renderer
class Renderer:
    def __init__(self, sheet):
        ink = 1 - sheet.astype(np.float32) / 255.0
        pf = paper_scan(SW, SH, 40)
        pb = paper_scan(SW, SH, 1500, True)
        self.front = pf * (1 - 0.93 * ink[..., None])
        self.back = pb * (1 - 0.10 * ink[..., None]) * 0.985   # show-through
        self.wood = table_texture()

    def warp_piece(self, cam, tex, c0, c1, corners3d, acc):
        crop = tex[:, c0:c1]
        h, w = crop.shape[:2]
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst, zc = cam.proj(corners3d)
        if (zc <= 1).any():
            return
        x0, y0 = np.floor(dst.min(0)).astype(int) - 2
        x1, y1 = np.ceil(dst.max(0)).astype(int) + 2
        X0, Y0 = max(0, x0), max(0, y0)
        X1, Y1 = min(W * SS, x1), min(H * SS, y1)
        if X0 >= X1 or Y0 >= Y1:
            return
        Hm = cv2.getPerspectiveTransform(src, np.float32(dst - [X0, Y0]))
        sz = (X1 - X0, Y1 - Y0)
        col = cv2.warpPerspective(crop.astype(np.float32), Hm, sz, flags=cv2.INTER_LINEAR)
        m = cv2.warpPerspective(np.ones((h, w), np.float32), Hm, sz, flags=cv2.INTER_LINEAR)
        # camera depth is linear across a planar piece: warp a 2x2 depth plane
        sx = (np.arange(w, dtype=np.float32) + 0.5) / w
        sy = (np.arange(h, dtype=np.float32) + 0.5) / h
        top_ = zc[0] + (zc[1] - zc[0]) * sx
        bot_ = zc[3] + (zc[2] - zc[3]) * sx
        dpl = (top_[None, :] * (1 - sy[:, None]) + bot_[None, :] * sy[:, None]).astype(np.float32)
        dep = cv2.warpPerspective(dpl, Hm, sz, flags=cv2.INTER_LINEAR)
        mm = np.maximum(m, 1e-3)
        col = col / mm[..., None]               # un-premultiply: no dark seams at piece edges
        dep = dep / mm
        return (X0, Y0, X1, Y1, col, m, dep)

    def frame(self, cam, us, Xs, zs, gain=1.0, shadow=True, info=None):
        Wp, Hp = W * SS, H * SS
        img = np.zeros((Hp, Wp, 3), np.float32)
        zbuf = np.full((Hp, Wp), 1e9, np.float32)
        hbuf = np.full((Hp, Wp), -10.0, np.float32)
        # table: the wood scan as a plane at z=0, 6 x 4 m of sheet units
        th, tw = self.wood.shape[:2]
        tc = np.array([[-2600, -2400, 0], [5000, -2400, 0], [5000, 2700, 0], [-2600, 2700, 0]], float)
        r = self.warp_piece(cam, self.wood, 0, tw, tc, None)
        X0, Y0, X1, Y1, col, m, dep = r
        img[Y0:Y1, X0:X1] = col
        # lamp falloff on the table (upper left key)
        yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
        fall = 1.05 - 0.38 * (((xx - 0.18 * Wp) / (1.25 * Wp)) ** 2 + ((yy + 0.15 * Hp) / (1.3 * Hp)) ** 2)
        pieces = []
        for (i, j) in strips_from(us, Xs, zs):
            ua, ub = us[j], us[i]           # ua < ub
            pa = np.array([Xs[j], zs[j]]); pb = np.array([Xs[i], zs[i]])
            if ub - ua < 1e-6:
                continue
            t = (pb - pa) / (ub - ua)       # d(X,z)/du
            nf = np.array([-t[1], 0.0, t[0]]); nf /= np.linalg.norm(nf) + 1e-9
            mid = np.array([(pa[0] + pb[0]) / 2, SH / 2, (pa[1] + pb[1]) / 2])
            front_vis = (cam.pos - mid) @ nf > 0
            nv = nf if front_vis else -nf
            lam = (0.58 + 0.42 * max(0.0, nv @ LIGHT) / LIGHT_FLAT) * gain
            tex = self.front if front_vis else self.back
            c0, c1 = max(0, int(math.floor(ua)) - 1), min(SW, int(math.ceil(ub)) + 1)
            P = lambda uu: (pa + t * (uu - ua))
            q0, q1 = P(c0), P(c1)
            corners = np.array([[q0[0], 0, q0[1]], [q1[0], 0, q1[1]], [q1[0], SH, q1[1]], [q0[0], SH, q0[1]]])
            pieces.append((corners, (pa[1] + pb[1]) / 2, tex, c0, c1, lam))
        # contact shadows, cast along the lamp from each piece's height
        if shadow:
            bins = [(0, 14, 2.2, 0.42), (14, 120, 9.0, 0.36), (120, 1e9, 22.0, 0.28)]
            smaps = []
            for lo, hi, sig, k in bins:
                sm = np.zeros((Hp, Wp), np.float32)
                for corners, zm, *_ in pieces:
                    if not (lo <= zm < hi):
                        continue
                    c = corners.copy()
                    ze = c[:, 2] + 3.0
                    c[:, 0] += -ze * LIGHT[0] / LIGHT[2]
                    c[:, 1] += -ze * LIGHT[1] / LIGHT[2]
                    c[:, 2] = 0
                    pts, zc = cam.proj(c)
                    s = k * (1 - math.exp(-(zm + 3) / 5.0)) * (1.0 if zm < 120 else max(0.5, 1 - (zm - 120) / 1400))
                    tmp = np.zeros_like(sm)
                    cv2.fillPoly(tmp, [np.int32(np.round(pts))], float(s), cv2.LINE_AA)
                    sm = np.maximum(sm, tmp)
                sig_px = sig * SS * cam.foc / SS / 2600
                sm = cv2.GaussianBlur(sm, (0, 0), max(0.8, sig_px * SS))
                smaps.append((lo, sm))
        # z-buffered composite of the paper pieces
        for corners, zm, tex, c0, c1, lam in pieces:
            r = self.warp_piece(cam, tex, c0, c1, corners, None)
            if r is None:
                continue
            X0, Y0, X1, Y1, col, m, dep = r
            zb = zbuf[Y0:Y1, X0:X1]
            ok = (m > 0.5) & (dep < zb - 0.02)
            img[Y0:Y1, X0:X1][ok] = col[ok] * lam
            zb[ok] = dep[ok]
            hbuf[Y0:Y1, X0:X1][ok] = zm
        # table falloff applies to the wood only; paper gets a gentler version
        isp = hbuf > -5
        f2 = np.where(isp, 0.97 + 0.03 * (fall - fall.mean()) / fall.std() * 0.6, fall)
        img *= f2[..., None]
        if shadow:
            for lo, sm in smaps:
                recv = hbuf < (lo - 2 if lo > 0 else -5)
                img *= (1 - sm * recv)[..., None]
        out = cv2.resize(np.clip(img, 0, 255), (W, H), interpolation=cv2.INTER_AREA)
        return out


# ------------------------------------------------------------------ light box
def lightbox(sheet, lamp, top=0.40):
    """Straight down on an animator's light box: transmission through the real
    stacked layers. lamp 0..1. Layers for folded column X (table frame):
    F0 (u = X - D, up), F1 (u = 2M - X, face down -> mirrored), F2/F3 (u = X)."""
    ink = 1 - sheet.astype(np.float32) / 255.0
    x0w, x1w = D, SW                         # folded object spans X 1180..2400
    Xs = np.arange(x0w, x1w)
    fib = paper_scan(SW, SH, 40)[..., 0] / 241.0
    fibb = paper_scan(SW, SH, 1500, True)[..., 0] / 241.0
    n = len(Xs)
    L0 = np.zeros((SH, n), np.float32); L1 = np.zeros_like(L0); L2 = np.zeros_like(L0)
    has0 = Xs < B; has1 = (Xs >= M) & (Xs < B); has2 = Xs >= M
    L0[:, has0] = ink[:, Xs[has0] - D]
    L1[:, has1] = ink[:, 2 * M - Xs[has1]]            # mirrored: u = 2M - X  (= 2A - x')
    L2[:, has2] = ink[:, Xs[has2]]
    vis = np.where(has0[None, :], L0, L2)            # what the top light sees
    fvis = np.where(has0[None, :], fib[:, np.clip(Xs - D, 0, SW - 1)], fib[:, np.clip(Xs, 0, SW - 1)])
    # paper above a hidden layer diffuses its ink
    L1b = cv2.GaussianBlur(L1, (0, 0), 2.2)
    L2b = np.where(has0[None, :], cv2.GaussianBlur(L2, (0, 0), 3.6), 0)
    T = 0.84
    nl = has0.astype(np.float32) + has1 + has2
    hidden_ink_T = 0.45                                  # print ink is not opaque to a light box
    trans = (T ** nl)[None, :] * (1 - vis * 0.97) * (1 - L1b * (1 - hidden_ink_T)) * (1 - L2b * (1 - hidden_ink_T))
    trans = trans * (0.985 + 0.015 * (fvis - 1) * 8)
    refl = 225.0 * (1 - 0.93 * vis) * fvis
    lum = top * refl + lamp * 158.0 * trans / T     # exposure: one layer + top light ~ 248
    # soft shoulder: the camera's exposure on the bright box (grading only)
    glass = lamp * 238.0 + top * 40
    return lum, glass, (x0w, x1w)


def lightbox_frame(sheet, lamp, top):
    lum, glass, (x0w, x1w) = lightbox(sheet, lamp, top)
    s = 0.574 * SS                       # px per u: panel 800 u -> 85% of frame height
    Wp, Hp = W * SS, H * SS
    cx, cy = (x0w + x1w) / 2, SH / 2
    # glass with a slight falloff, frame and peg bar (handmade object, lit by its lamp)
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
    g = 1.0 - 0.10 * (((xx - Wp / 2) / (Wp * 0.6)) ** 2 + ((yy - Hp / 2) / (Hp * 0.7)) ** 2)
    img = np.full((Hp, Wp), glass, np.float32) * g
    fr = np.zeros((Hp, Wp), np.float32)
    cv2.rectangle(fr, (int(0.035 * Wp), int(0.03 * Hp)), (int(0.965 * Wp), int(0.97 * Hp)), 1.0, -1)
    fr = cv2.GaussianBlur(fr, (0, 0), 1.2 * SS)
    img = img * fr + (24 + 8 * top) * (1 - fr)
    lw, lh = int(lum.shape[1] * s), int(lum.shape[0] * s)
    ls = cv2.resize(lum, (lw, lh), interpolation=cv2.INTER_AREA)
    ox, oy = int(Wp / 2 - (cx - x0w) * s), int(Hp / 2 - cy * s)
    gsub = g[oy:oy + lh, ox:ox + lw]
    img[oy:oy + lh, ox:ox + lw] = ls * (0.9 + 0.1 * gsub)
    # peg bar: a steel bar with three pegs along the top of the glass
    by = int(0.055 * Hp)
    cv2.rectangle(img, (int(Wp / 2 - 210 * SS), by), (int(Wp / 2 + 210 * SS), by + 16 * SS), 30 + 30 * top, -1)
    for px, rw in ((Wp / 2 - 150 * SS, 7), (Wp / 2, 12), (Wp / 2 + 150 * SS, 7)):
        cv2.ellipse(img, (int(px), by + 8 * SS), (rw * SS, 5 * SS), 0, 0, 360, 95 + 60 * top, -1)
    img = np.clip(img, 0, 255)
    rgb = np.stack([img, img * 0.995, img * 0.985], -1)       # neutral box (R-B <= 4)
    return cv2.resize(rgb, (W, H), interpolation=cv2.INTER_AREA), (ox / SS, oy / SS, s / SS)


# ------------------------------------------------------------------ fixture (#8)
def fixture(sheet, rend):
    rep = {}
    rep["B_eq_2M_minus_A"] = B == 2 * M - A
    rep["2A_minus_M"] = 2 * A - M
    # reflections compose: x -> 2A - x then the image of M -> x - D for M..B
    rep["compose_A_then_M_ok"] = all(2 * (2 * A - M) - (2 * A - x) == x - D for x in range(M, B + 1))
    # settled geometry maps u -> X exactly (table frame)
    al, be, Lm, La, k0, k1 = schedule(1.0)
    us, Xs, zs, _ = curve(al, be, Lm, La, k0, k1)
    f0 = us < A - La / 2
    f1 = (us > A + La / 2) & (us < M - Lm / 2)
    rep["F0_map_err_u"] = float(np.abs(Xs[f0] - (us[f0] + D)).max())
    rep["F1_map_err_u"] = float(np.abs(Xs[f1] - (2 * M - us[f1])).max())
    rep["layer_heights_u"] = [float(zs[f1].mean()), float(zs[f0].mean())]
    # orthographic top view of the settled sheet: for each table column X take the
    # highest paper surface over it (dense resampling of the curve) and compare
    # its ink column with V(x'), x' = X - D
    Vx = folded_V(sheet)
    uu = np.linspace(0, SW, SW * 8 + 1)
    Xi = np.interp(uu, us[::-1], Xs[::-1]); zi = np.interp(uu, us[::-1], zs[::-1])
    worst, cols = 0, 0
    for X in range(D, SW):
        sel = np.abs(Xi - X) < 0.07
        if not sel.any():
            continue
        u = int(round(uu[np.argmax(np.where(sel, zi, -1e9))]))
        worst = max(worst, int(np.abs(sheet[:, min(u, SW - 1)].astype(int) - Vx[:, X - D].astype(int)).max()))
        cols += 1
    rep["settled_vs_V_max_abs_diff"] = worst
    rep["settled_vs_V_cols_checked"] = cols
    # seam rows: ink rows crossing x=A-1 in P1 vs x=B+1 in P2 (balloon borders, frame, floor)
    colA = sheet[:, A - 2] < 128; colB = sheet[:, B + 2] < 128
    def runs(c):
        r, on = [], None
        for y, v in enumerate(c):
            if v and on is None: on = y
            if not v and on is not None: r.append((on + y - 1) / 2); on = None
        return r
    ra, rb = runs(colA), runs(colB)
    pairs = []
    for y in ra:
        if rb:
            yb = min(rb, key=lambda q: abs(q - y))
            pairs.append((y, yb, abs(y - yb)))
    rep["seam_crossings"] = [(round(a, 1), round(b, 1), round(c, 1)) for a, b, c in pairs]
    return rep


# ------------------------------------------------------------------ main
def main():
    sheet, sha = build_art()
    rend = Renderer(sheet)
    rng = np.random.RandomState(7)
    N_REST, N_FOLD, N_SET, N_PUSH, N_HOLD = 5, 55, 5, 12, 15
    N_LB_OFF, N_LB_RAMP, N_LB_HOLD = 4, 11, 13
    seq = []   # one dict per exposure
    for e in range(N_REST):
        seq.append(dict(kind="rest", p=0.0, cam=0.0, jit=True))
    ps = np.linspace(0, 1, N_FOLD)
    ps[1:-1] += rng.uniform(-0.004, 0.004, N_FOLD - 2)      # hand-placed spacing
    ps = np.maximum.accumulate(ps)
    for p in ps:
        seq.append(dict(kind="fold", p=float(p), cam=0.0, jit=True))
    for e in range(N_SET):
        seq.append(dict(kind="settled", p=1.0, cam=0.0, jit=False))
    for e in range(N_PUSH):
        seq.append(dict(kind="push", p=1.0, cam=ease((e + 1) / N_PUSH), jit=False))
    for e in range(N_HOLD):
        seq.append(dict(kind="hold", p=1.0, cam=1.0, jit=False))
    for e in range(N_LB_OFF):
        seq.append(dict(kind="lightbox", lamp=0.0))
    for e in range(N_LB_RAMP):
        seq.append(dict(kind="lightbox", lamp=ease((e + 1) / N_LB_RAMP) ** 0.8))
    for e in range(N_LB_HOLD):
        seq.append(dict(kind="lightbox", lamp=1.0))

    frames_dir = os.path.join(MEDIA, "exposures")
    os.makedirs(frames_dir, exist_ok=True)
    events = []
    cache = {}
    prev = None
    for k, ex in enumerate(seq):
        t = k / 12.0
        if ex["kind"] == "lightbox":
            key = ("lb", round(ex["lamp"], 4))
            if key not in cache:
                cache[key] = lightbox_frame(sheet, ex["lamp"], 0.40)[0]
            img = cache[key]
            events.append(dict(exposure=k, t=round(t, 4), kind="lightbox", lamp=round(ex["lamp"], 3), top_light=0.40))
        else:
            al, be, Lm, La, k0, k1 = schedule(ex["p"])
            us, Xs, zs, phs = curve(al, be, Lm, La, k0, k1)
            c = ex["cam"]
            pos = lerp(CAM_WIDE[0], CAM_CLOSE[0], c); tgt = lerp(CAM_WIDE[1], CAM_CLOSE[1], c)
            foc = CAM_WIDE[2] * (1 - c) + CAM_CLOSE[2] * c
            jit = rng.normal(0, 1.0, 3) if ex["jit"] else np.zeros(3)
            gain = 1 + (rng.uniform(-0.02, 0.02) if ex["jit"] else 0.0)
            cam = Cam(pos + jit, tgt + jit * 0.5, foc)
            key = (round(ex["p"], 6), round(c, 6), tuple(np.round(jit, 4)), round(gain, 5))
            if key not in cache:
                cache[key] = rend.frame(cam, us, Xs, zs, gain)
            img = cache[key]
            # layer order probe at three table columns (#45 DAG trace)
            def top_at(Xq):
                best, lab = -1e9, None
                for i in range(len(us) - 1):
                    lo, hi = sorted((Xs[i], Xs[i + 1]))
                    if lo <= Xq <= hi and max(zs[i], zs[i + 1]) > best:
                        best = max(zs[i], zs[i + 1]); uu = us[i]
                        lab = "F0" if uu < A else ("F1" if uu < M else "F2/F3")
                return lab
            events.append(dict(exposure=k, t=round(t, 4), kind=ex["kind"], p=round(ex["p"], 4),
                               alpha_M_deg=round(math.degrees(al), 2), beta_A_deg=round(math.degrees(be), 2),
                               band_M_u=round(Lm, 2), band_A_u=round(La, 2), lag_F0_rad=round(k0, 4), lag_F1_rad=round(k1, 4),
                               min_z_u=round(float(zs.min()), 3), max_z_u=round(float(zs.max()), 1),
                               cam_jitter_u=[round(float(v), 3) for v in jit], lamp_gain=round(gain, 4),
                               top_layer_at_X={str(x): top_at(x) for x in (1300, 1700, 2100)}))
        out = np.clip(img, 0, 255).astype(np.uint8)
        Image.fromarray(out).save(os.path.join(frames_dir, f"e{k:03d}.png"))
        if k % 10 == 0:
            print("exposure", k, ex["kind"], flush=True)
    # sound tick per exposure (fold kinds)
    for ev in events:
        ev["tick"] = ev["kind"] == "fold" and ev["exposure"] > N_REST
    json.dump(dict(fps_exposures=12, fps_container=FPS, strip_art_sha256=sha, n=len(seq), events=events),
              open(os.path.join(WORK, "test-shot-build", "fold-events.json"), "w"), indent=1)
    rep = fixture(sheet, rend)
    rep["strip_art_sha256"] = sha
    json.dump(rep, open(os.path.join(WORK, "test-shot-build", "fixture.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1)[:1500])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--probe":
        sheet, _ = build_art()
        rend = Renderer(sheet)
        for i, p in enumerate([0.0, 0.25, 0.4, 0.6, 0.85, 1.0]):
            al, be, Lm, La, k0, k1 = schedule(p)
            us, Xs, zs, _ = curve(al, be, Lm, La, k0, k1)
            print(p, round(math.degrees(al)), round(math.degrees(be)), 'minz', round(zs.min(), 2), 'maxz', round(zs.max()))
            cam = Cam(*CAM_WIDE) if p < 1 else Cam(*CAM_CLOSE)
            Image.fromarray(np.clip(rend.frame(cam, us, Xs, zs), 0, 255).astype(np.uint8)).save(f"/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/probe{i}.png")
        Image.fromarray(np.clip(lightbox_frame(sheet, 1.0, 0.4)[0], 0, 255).astype(np.uint8)).save("/tmp/claude-0/-home-user/a99ec93a-6f31-57b0-a2ec-fb930dfe1aad/scratchpad/probe_lb.png")
    else:
        main()
