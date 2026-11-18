"""U3 tabletop + light-box cinematographer: shots 1, 2, 3, 5, 7, 8 (plan.md section 6).

Stop-motion on twos: one exposure every 1/12 s, each held two frames in a 24 fps
container. Everything on screen is the printed sheet strip/strip-art.png (Busch 1865
plates cut as puppets + pen.py lettering, U1/U2), printed onto the foraged paper scan
(Commons, J. Puckett, CC BY 2.0), on the foraged wood scan (Commons, CC0).

#40 Physical tabletop capture
    Geometry comes from strip/fold.py (cross_section: exact circular curl bands of 40 u
    at A and M while moving, pressed to 1.6 u when flat; F0/F1 lag bends = the free
    edge trailing the unseen hand). Each planar strip of the cross-section is its own
    perspective-warped piece of the printed sheet (sub-facets inside the curl bands).
    Per-exposure events (alpha, beta, bands, jitter, lamp gain, sound tick, DAG) go to
    shots/fold-events.json. Invariants asserted: F2/F3 stay at z = 0 exactly, crease
    lines on their computed lines, no facet id swap, one tick per moving exposure.
#45 Occlusion compositing
    z-buffer by camera depth per exposure + an occlusion DAG from fold.layer_order;
    visible face per piece chosen by its normal (front ink / back with mirrored
    show-through); contact shadows cast along the lamp with blur and strength from
    height; puppet holdouts in puppet.py; light box = transmission pass T^n with
    blurred deeper ink, ghosts at 2A-x' (mirrored) and x'+D -> x' (unmirrored).
#8  Constraint sketchpad
    B = 2M - A, the composed reflections, contact A == B and the settled view == V(x')
    are asserted in fixture() and written to shots/fixture-shots.json.
"""
import sys, os, math, json, hashlib
import numpy as np
import cv2
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.dirname(HERE)
WS = os.path.dirname(SHOTS)
FILMS = os.path.normpath(os.path.join(WS, "../.."))
sys.path.insert(0, os.path.join(WS, "strip"))
sys.path.insert(0, HERE)
import occlusion_check as OC  # noqa: E402  (repair r1)
import fold as FG                # noqa: E402  (U1's pure geometry, read-only)
import puppet as PUP             # noqa: E402  (rig.json forward kinematics)

SRC = os.path.join(FILMS, "sources/les-caids-de-la-gaudriole")
MEDIA = os.path.join(SRC, "tabletop")
EDITOR = os.path.join(SRC, "tabletop-lightbox-cinematographer-sound")
W, H, SS, FPS = 960, 540, 2, 24
A, M, B, D = FG.A, FG.M, FG.B, FG.D
SW, SH = FG.W, FG.H
assert B == 2 * M - A and D == B - A and 2 * A - M > 0

ART_PATH = os.path.join(WS, "strip/strip-art.png")
ART = np.asarray(Image.open(ART_PATH).convert("L"))
ART_SHA = hashlib.sha256(open(ART_PATH, "rb").read()).hexdigest()

LIGHT = np.array([-0.45, -0.35, 0.82]); LIGHT /= np.linalg.norm(LIGHT)   # key lamp, upper left
LF = LIGHT[2]


# ------------------------------------------------------------------ materials
def _z(a):
    return (a - a.mean()) / (a.std() + 1e-6)


def paper_scan(w, h, y0, flip=False):
    """The real crumpled paper scan: keep its wrinkle relief and fibres (band-pass of
    the scan's own luminance), damp its large stains, neutralise its yellow."""
    p = Image.open(os.path.join(SRC, "paper.jpg")).convert("L")
    p = p.resize((w, int(p.height * w / p.width)), Image.LANCZOS)
    a = np.asarray(p, np.float32)[y0:y0 + h]
    if flip:
        a = a[::-1, ::-1]
    fine = a - cv2.GaussianBlur(a, (0, 0), 2.0)
    wrink = cv2.GaussianBlur(a, (0, 0), 1.0) - cv2.GaussianBlur(a, (0, 0), 18.0)
    stain = cv2.GaussianBlur(a, (0, 0), 18.0)
    base = 238 + 7.5 * np.clip(_z(wrink), -3.5, 3.5) + 2.0 * np.clip(_z(fine), -3, 3) + 2.0 * np.clip(_z(stain), -2, 2)
    return np.stack([base, base - 1.5, base - 5], -1)       # |R-B| ~ 5: near-neutral


def table_texture():
    t = Image.open(os.path.join(SRC, "wood.jpg")).convert("L")
    a = cv2.GaussianBlur(np.asarray(t, np.float32), (0, 0), 1.0)
    a = np.clip(47 + 0.42 * (a - a.mean()), 18, 90)
    return np.stack([a * 1.03, a, a * 0.95], -1)


def folded_V(sheet):
    return FG.folded_view(sheet)


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


def cam_at(tx, ty, dist, off_vertical_deg, foc):
    t = math.radians(off_vertical_deg)
    return (np.array([tx, ty + dist * math.sin(t), dist * math.cos(t)]), np.array([tx, ty, 0.0]), foc)


# kf-1 family: oblique ~32 deg off vertical, key lamp upper left
CAM_WIDE = cam_at(1200, 470, 3400, 32, 1170)        # whole open strip, ~92 % of frame width
CAM_PACKET = cam_at(1790, 455, 2000, 32, 1150)      # folded packet centred, ~ 80 % of height
CAM_P1 = cam_at(610, 470, 2300, 18, 1300)           # panel 1 at ~ 90 % of frame height
CAM_P2 = cam_at(1790, 470, 2300, 18, 1300)


def lerp(a, b, t):
    return np.asarray(a, float) * (1 - t) + np.asarray(b, float) * t


def cam_mix(c0, c1, t):
    return (lerp(c0[0], c1[0], t), lerp(c0[1], c1[1], t), c0[2] * (1 - t) + c1[2] * t)


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ geometry
def table_contact(cs):
    """Repair r1 (#40 physical constraint): paper cannot pass through the table.
    fold.cross_section integrates the free curve from u = W; when the A band turns the
    tail down before M has lifted F1, the raw curve dips below z = 0 (up to -54 u).
    A real sheet lies on the table from the touchdown point on: from the first point
    with z < 0 the rest of the tail (smaller u) is laid flat on z = 0, face up,
    continuing in the direction of travel, arc length preserved (texture stays u)."""
    u, X, z = cs["u"], cs["X"].copy(), cs["z"].copy()
    neg = np.nonzero(z < -1e-9)[0]
    if len(neg) == 0:
        return cs
    i0 = int(neg[0])
    if i0 == 0:
        return cs
    # touchdown between i0-1 (z>=0) and i0 (z<0)
    t = z[i0 - 1] / (z[i0 - 1] - z[i0]) if z[i0 - 1] != z[i0] else 0.0
    Xt = X[i0 - 1] + t * (X[i0] - X[i0 - 1]); ut = u[i0 - 1] + t * (u[i0] - u[i0 - 1])
    d = 1.0 if X[i0] >= X[i0 - 1] else -1.0
    X[i0:] = Xt + d * (ut - u[i0:]); z[i0:] = 0.0
    out = dict(cs); out["X"], out["z"] = X, z
    ph = cs["phi"].copy(); ph[i0:] = math.pi if d < 0 else 0.0
    out["phi"] = ph; out["nz"] = -np.cos(ph); out["table_contact_from_u"] = float(ut)
    return out


def section(al, be, La, Lm, lag=(0.0, 0.0)):
    cs = table_contact(FG.cross_section(al, be, La, Lm, lag, du=2.0))
    return cs


def strips_from(us, Xs, zs):
    out = [(0, 1)]
    i, n = 1, len(us)
    while i < n - 1:
        j = i + 1
        while j < n - 1:
            a, b = np.array([Xs[i], zs[i]]), np.array([Xs[j + 1], zs[j + 1]])
            seg = b - a; L = np.linalg.norm(seg) + 1e-9
            pts = np.stack([Xs[i:j + 2], zs[i:j + 2]], 1) - a
            dev = np.abs(pts[:, 0] * seg[1] - pts[:, 1] * seg[0]) / L
            if dev.max() > 0.25 or us[i] - us[j + 1] > 120:
                break
            j += 1
        out.append((i, j)); i = j
    return out


# ------------------------------------------------------------------ renderer
class Renderer:
    def __init__(self):
        self.pf = paper_scan(SW, SH, 40)
        self.pb = paper_scan(SW, SH, 1500, True)
        self.wood = table_texture()
        self.set_art(ART)
        Hp, Wp = H * SS, W * SS
        yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
        self.fall = 1.05 - 0.38 * (((xx - 0.18 * Wp) / (1.25 * Wp)) ** 2 + ((yy + 0.15 * Hp) / (1.3 * Hp)) ** 2)

    def set_art(self, sheet):
        ink = 1 - sheet.astype(np.float32) / 255.0
        self.front = self.pf * (1 - 0.93 * ink[..., None])
        self.back = self.pb * (1 - 0.11 * ink[..., None]) * 0.985   # show-through from the ink side

    def warp(self, cam, tex, c0, c1, r0, r1, corners3d):
        crop = tex[r0:r1, c0:c1]
        h, w = crop.shape[:2]
        src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        dst, zc = cam.proj(corners3d)
        if (zc <= 1).any():
            return None
        x0, y0 = np.floor(dst.min(0)).astype(int) - 2
        x1, y1 = np.ceil(dst.max(0)).astype(int) + 2
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W * SS, x1), min(H * SS, y1)
        if X0 >= X1 or Y0 >= Y1:
            return None
        Hm = cv2.getPerspectiveTransform(src, np.float32(dst - [X0, Y0]))
        sz = (X1 - X0, Y1 - Y0)
        col = cv2.warpPerspective(crop.astype(np.float32), Hm, sz, flags=cv2.INTER_LINEAR)
        m = cv2.warpPerspective(np.ones((h, w), np.float32), Hm, sz, flags=cv2.INTER_LINEAR)
        sx = (np.arange(w, dtype=np.float32) + 0.5) / w
        sy = (np.arange(h, dtype=np.float32) + 0.5) / h
        top_ = zc[0] + (zc[1] - zc[0]) * sx
        bot_ = zc[3] + (zc[2] - zc[3]) * sx
        dpl = (top_[None, :] * (1 - sy[:, None]) + bot_[None, :] * sy[:, None]).astype(np.float32)
        dep = cv2.warpPerspective(dpl, Hm, sz, flags=cv2.INTER_LINEAR)
        mm = np.maximum(m, 1e-3)
        return (X0, Y0, X1, Y1, col / mm[..., None], m, dep / mm)

    def frame(self, cam, cs, gain=1.0, rigid=None, lift=None, ny=1):
        """rigid: (dx, dy, dz, rot_z_deg) whole-sheet transform (shot 1 lay-down).
        lift(u, y) -> extra height (corner lift); pieces are split into ny rows then."""
        us, Xs, zs = cs["u"], cs["X"], cs["z"]
        Wp, Hp = W * SS, H * SS
        img = np.zeros((Hp, Wp, 3), np.float32)
        zbuf = np.full((Hp, Wp), 1e9, np.float32)
        hbuf = np.full((Hp, Wp), -10.0, np.float32)
        th, tw = self.wood.shape[:2]
        tc = np.array([[-2600, -2400, 0], [5000, -2400, 0], [5000, 2900, 0], [-2600, 2900, 0]], float)
        X0, Y0, X1, Y1, col, m, dep = self.warp(cam, self.wood, 0, tw, 0, th, tc)
        img[Y0:Y1, X0:X1] = col
        fall = self.fall

        def place(P):
            if rigid is None:
                return P
            dx, dy, dz, rz = rigid
            c, s = math.cos(math.radians(rz)), math.sin(math.radians(rz))
            cx, cy = SW / 2, SH / 2
            Q = P.copy()
            Q[:, 0] = cx + c * (P[:, 0] - cx) - s * (P[:, 1] - cy) + dx
            Q[:, 1] = cy + s * (P[:, 0] - cx) + c * (P[:, 1] - cy) + dy
            Q[:, 2] = P[:, 2] + dz
            return Q

        rows = np.linspace(0, SH, ny + 1).astype(int)
        pieces = []
        for (i, j) in strips_from(us, Xs, zs):
            ua, ub = us[j], us[i]
            pa = np.array([Xs[j], zs[j]]); pb = np.array([Xs[i], zs[i]])
            if ub - ua < 1e-6:
                continue
            t = (pb - pa) / (ub - ua)
            nf = np.array([-t[1], 0.0, t[0]]); nf /= np.linalg.norm(nf) + 1e-9
            c0, c1 = max(0, int(math.floor(ua)) - 1), min(SW, int(math.ceil(ub)) + 1)
            q0, q1 = pa + t * (c0 - ua), pa + t * (c1 - ua)
            for r0, r1 in zip(rows[:-1], rows[1:]):
                corners = np.array([[q0[0], r0, q0[1]], [q1[0], r0, q1[1]], [q1[0], r1, q1[1]], [q0[0], r1, q0[1]]])
                n_here = nf
                if lift is not None:
                    dz = np.array([lift(c0, r0), lift(c1, r0), lift(c1, r1), lift(c0, r1)])
                    corners[:, 2] += dz
                    e1 = corners[1] - corners[0] + corners[2] - corners[3]
                    e2 = corners[3] - corners[0] + corners[2] - corners[1]
                    n2 = np.cross(e2, e1); n2 /= np.linalg.norm(n2) + 1e-9
                    n_here = n2 if n2 @ nf > 0 else -n2
                corners = place(corners)
                if rigid is not None:
                    rz = math.radians(rigid[3]); c, s = math.cos(rz), math.sin(rz)
                    n_here = np.array([c * n_here[0] - s * n_here[1], s * n_here[0] + c * n_here[1], n_here[2]])
                mid = corners.mean(0)
                front_vis = (cam.pos - mid) @ n_here > 0
                nv = n_here if front_vis else -n_here
                lam = (0.40 + 0.60 * max(0.0, nv @ LIGHT) / LF) * gain       # strong curl shading
                tex = self.front if front_vis else self.back
                pieces.append((corners, float(mid[2]), tex, c0, c1, r0, r1, lam, int(FG.facet_of(0.5 * (ua + ub))[1])))
        # contact shadows: project each piece along the lamp onto the table; soft by height
        bins = [(0, 14, 2.2, 0.42), (14, 120, 9.0, 0.36), (120, 1e9, 22.0, 0.28)]
        smaps = []
        for lo, hi, sig, k in bins:
            sm = np.zeros((Hp, Wp), np.float32); any_ = False
            for corners, zm, *_ in pieces:
                if not (lo <= zm < hi):
                    continue
                c = corners.copy(); ze = c[:, 2] + 3.0
                c[:, 0] += -ze * LIGHT[0] / LIGHT[2]; c[:, 1] += -ze * LIGHT[1] / LIGHT[2]; c[:, 2] = 0
                pts, zc = cam.proj(c)
                s = k * (1 - math.exp(-(zm + 3) / 5.0)) * (1.0 if zm < 120 else max(0.5, 1 - (zm - 120) / 1400))
                tmp = np.zeros_like(sm)
                cv2.fillPoly(tmp, [np.int32(np.round(pts))], float(s), cv2.LINE_AA)
                sm = np.maximum(sm, tmp); any_ = True
            if any_:
                sig_px = sig * cam.foc / 2600
                smaps.append((lo, cv2.GaussianBlur(sm, (0, 0), max(0.8, sig_px * SS))))
        idbuf = np.full((Hp, Wp), -1, np.int16)
        foot = {}
        for corners, zm, tex, c0, c1, r0, r1, lam, fid in pieces:
            r = self.warp(cam, tex, c0, c1, r0, r1, corners)
            if r is None:
                continue
            X0, Y0, X1, Y1, col, m, dep = r
            zb = zbuf[Y0:Y1, X0:X1]
            ok = (m > 0.5) & (dep < zb - 0.02)
            img[Y0:Y1, X0:X1][ok] = col[ok] * lam
            zb[ok] = dep[ok]
            hbuf[Y0:Y1, X0:X1][ok] = zm
            idbuf[Y0:Y1, X0:X1][ok] = fid
            fm = foot.setdefault(fid, np.zeros((Hp, Wp), bool))
            fm[Y0:Y1, X0:X1] |= m > 0.5
        self.last_ids, self.last_foot = idbuf, foot
        isp = hbuf > -5
        f2 = np.where(isp, 0.97 + 0.018 * (fall - fall.mean()) / fall.std(), fall)
        img *= f2[..., None]
        for lo, sm in smaps:
            recv = hbuf < (lo - 2 if lo > 0 else -5)
            img *= (1 - sm * recv)[..., None]
        return cv2.resize(np.clip(img, 0, 255), (W, H), interpolation=cv2.INTER_AREA)


# ------------------------------------------------------------------ light box (#45 transmission)
def lightbox_lum(sheet, lamp, top):
    """Straight down on the light box. Table column X in [D, W): the folded packet.
    Layers: F0 (u = X - D = x', face up, X < B), F1 (u = 2M - X = 2A - x', face down,
    M <= X < B), F2+F3 (u = X = x' + D, face up, X >= M). Light passes up through the
    stack: T per sheet, hidden ink partially transmissive and diffused by the sheets
    above it. The camera's highlight shoulder brings the 1-layer and 3-layer paper to
    one glow (grading only, applied to the real transmission values)."""
    ink = np.clip((1 - sheet.astype(np.float32) / 255.0) / (1 - 18 / 255.0), 0, 1)   # pen/print ink density 1
    Xs = np.arange(D, SW)
    fib = paper_scan(SW, SH, 40)[..., 0] / 238.0
    has0 = Xs < B; has1 = (Xs >= M) & (Xs < B); has2 = Xs >= M
    L0 = np.zeros((SH, len(Xs)), np.float32); L1 = np.zeros_like(L0); L2 = np.zeros_like(L0)
    L0[:, has0] = ink[:, Xs[has0] - D]
    L1[:, has1] = ink[:, 2 * M - Xs[has1]]          # mirrored ghost: u = 2A - x'
    L2[:, has2] = ink[:, Xs[has2]]                  # unmirrored: u = x' + D
    vis = np.where(has0[None, :], L0, L2)
    fv = np.where(has0[None, :], fib[:, np.clip(Xs - D, 0, SW - 1)], fib[:, np.clip(Xs, 0, SW - 1)])
    L1b = cv2.GaussianBlur(L1, (0, 0), 2.4)          # one sheet of diffusion above it
    L2b = np.where(has0[None, :], cv2.GaussianBlur(L2, (0, 0), 4.0), 0)   # two sheets above it
    T = 0.62                                          # one sheet of 80 g paper on the box
    nl = has0.astype(np.float32) + has1 + has2
    nl = np.maximum(nl, 1)
    hidden_T = 0.30                                   # hidden print ink lets some light through
    trans = (T ** nl)[None, :] * (1 - vis * 0.995) * (1 - L1b * (1 - hidden_T)) * (1 - L2b * (1 - hidden_T))
    trans *= (1 + 0.06 * (fv - 1) * 4)                # paper formation (the real scan) in transmission
    expo = lamp * 2.95 / (T ** 3)                     # exposure set on the 3-layer paper
    glow = 252.0 * (1 - np.exp(-expo * trans))        # highlight shoulder (camera)
    refl = 222.0 * (1 - 0.93 * vis) * fv
    lum = np.maximum(top * refl, 0) * (1 - 0.6 * lamp) + glow
    return np.clip(lum, 0, 252), dict(L1=L1, L2=L2, has0=has0, has1=has1, has2=has2)


def lightbox_frame(sheet, lamp, top):
    lum, _ = lightbox_lum(sheet, lamp, top)
    s = 0.574 * SS
    Wp, Hp = W * SS, H * SS
    cx, cy = (D + SW) / 2, SH / 2
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
    g = 1.0 - 0.06 * (((xx - Wp / 2) / (Wp * 0.6)) ** 2 + ((yy - Hp / 2) / (Hp * 0.7)) ** 2)
    glass = 252.0 * (1 - math.exp(-lamp * 2.95 / 0.62 ** 3 * 1.0)) + top * 120 * (1 - lamp)
    img = np.full((Hp, Wp), min(glass, 253.0), np.float32) * g
    fr = np.zeros((Hp, Wp), np.float32)
    cv2.rectangle(fr, (int(0.035 * Wp), int(0.03 * Hp)), (int(0.965 * Wp), int(0.97 * Hp)), 1.0, -1)
    fr = cv2.GaussianBlur(fr, (0, 0), 1.2 * SS)
    img = img * fr + (24 + 10 * top) * (1 - fr)
    lw, lh = int(lum.shape[1] * s), int(lum.shape[0] * s)
    ls = cv2.resize(lum, (lw, lh), interpolation=cv2.INTER_AREA)
    ox, oy = int(Wp / 2 - (cx - D) * s), int(Hp / 2 - cy * s)
    # soft contact edge of the packet on the glass (paper thickness, top light only)
    img[oy:oy + lh, ox:ox + lw] = ls * (0.95 + 0.05 * g[oy:oy + lh, ox:ox + lw])
    by = int(0.055 * Hp)
    cv2.rectangle(img, (int(Wp / 2 - 210 * SS), by), (int(Wp / 2 + 210 * SS), by + 16 * SS), 28 + 30 * top, -1)
    for px, rw in ((Wp / 2 - 150 * SS, 7), (Wp / 2, 12), (Wp / 2 + 150 * SS, 7)):
        cv2.ellipse(img, (int(px), by + 8 * SS), (rw * SS, 5 * SS), 0, 0, 360, 95 + 60 * top, -1)
    img = np.clip(img, 0, 255)
    rgb = np.stack([img, img * 0.996, img * 0.988], -1)     # neutral glow (R-B <= 3)
    return cv2.resize(rgb, (W, H), interpolation=cv2.INTER_AREA), (ox / SS, oy / SS, s / SS)


# ------------------------------------------------------------------ fold schedule
def fold_state(p):
    """progress p 0..1 -> (alpha_M, beta_A, La, Lm, lag). A leads (fold A first)."""
    be = math.pi * ease(p / 0.82)
    al = math.pi * ease((p - 0.06) / 0.94)
    press = ease((p - 0.84) / 0.16)
    La = 40 - (40 - 6.0) * press
    Lm = 40 - (40 - 6.0) * press
    dp = 1e-3
    dbe = (math.pi * ease((p + dp) / 0.82) - be) / dp
    dal = (math.pi * ease((p + dp - 0.06) / 0.94) - al) / dp
    k0 = -0.10 * dbe * math.sin(be)        # free edge of F0 trails the unseen hand
    k1 = 0.04 * dal * math.sin(al)
    return al, be, La, Lm, (k0, k1)


SETTLE = [  # 3-exposure settle after the landing: pleat presses, free edge springs up and comes down
    # (repair r1: the lag sign was positive, which bent F0's free edge DOWN through F3 and
    #  the table, to z = -5.7 u; it now lifts the free edge 16 u, then 7 u, then flat)
    (math.pi, math.pi, 4.0, 4.0, (-0.035, 0.0)),
    (math.pi, math.pi, 2.6, 2.6, (-0.012, 0.0)),
    (math.pi, math.pi, 1.6, 1.6, (0.0, 0.0)),
]
FLAT = (math.pi, math.pi, 1.6, 1.6, (0.0, 0.0))
OPEN = (0.0, 0.0, 40.0, 40.0, (0.0, 0.0))


# ------------------------------------------------------------------ shot sequences
def seq_shot1(rng):
    out = []
    for e in range(6):
        out.append(dict(kind="empty", state=None, cam=CAM_WIDE))
    fall = [(330, -260, 60, -5.5), (170, -120, 26, -3.0), (70, -40, 9, -1.2), (16, -8, 2, -0.3)]
    for z, dx, dy, rz in fall:
        out.append(dict(kind="fall", state=OPEN, cam=CAM_WIDE, rigid=(dx, dy, z, rz), lift=("corner", 60 + z * 0.2), jit=True))
    for c in (34.0, 12.0, 3.0):
        out.append(dict(kind="settle", state=OPEN, cam=CAM_WIDE, lift=("corner", c), jit=True))
    while len(out) < 48:
        out.append(dict(kind="hold", state=OPEN, cam=CAM_WIDE))
    return out


def seq_puppet(shot, cam_from, cam_main, drift):
    P = json.load(open(os.path.join(WS, "puppets/poses.json")))["shots"][str(shot)]["exposures"]
    out = []
    n = len(P)
    for i, ex in enumerate(P):
        mv = ease((i + 1) / 12.0)                                  # stepped move onto the panel
        c = cam_mix(cam_from, cam_main, mv)
        if i >= 12:
            d = ease((i - 12) / max(1, n - 30))                    # reading drift, then still
            c = (c[0] + np.array(drift) * d, c[1] + np.array(drift) * d, c[2])
        out.append(dict(kind=f"read{shot}", state=OPEN, cam=c, pose=ex["joints"], jit=i < 12))
    return out


def seq_fold(rng, n_rest=4, n_fold=86):
    out = []
    for e in range(n_rest):
        out.append(dict(kind="rest", state=OPEN, cam=CAM_WIDE, p=0.0, jit=True))
    ps = np.linspace(0, 1, n_fold + 1)[1:]
    ps[:-1] += rng.uniform(-0.003, 0.003, n_fold - 1)              # hand-placed spacing
    ps = np.clip(np.maximum.accumulate(ps), 0, 1)
    for p in ps:
        out.append(dict(kind="fold", state=fold_state(float(p)), cam=cam_mix(CAM_WIDE, CAM_PACKET, ease((p - 0.25) / 0.75)), p=float(p), jit=True))
    for st in SETTLE:
        out.append(dict(kind="settle", state=st, cam=CAM_PACKET, p=1.0, jit=True))
    while len(out) < 96:
        out.append(dict(kind="flat", state=FLAT, cam=CAM_PACKET, p=1.0))
    return out


def seq_replay(rng):
    out = []
    for e in range(6):
        out.append(dict(kind="flat", state=FLAT, cam=CAM_PACKET, p=1.0))
    for i in range(24):                                            # unfold: the fold in reverse
        p = 1 - (i + 1) / 24
        out.append(dict(kind="unfold", state=fold_state(p) if p > 0 else OPEN, cam=cam_mix(CAM_WIDE, CAM_PACKET, ease((p - 0.25) / 0.75)), p=p, jit=True))
    for e in range(12):
        out.append(dict(kind="open-hold", state=OPEN, cam=CAM_WIDE, p=0.0))
    for i in range(24):
        p = (i + 1) / 24
        out.append(dict(kind="refold", state=fold_state(p), cam=cam_mix(CAM_WIDE, CAM_PACKET, ease((p - 0.25) / 0.75)), p=p, jit=True))
    for st in SETTLE:
        out.append(dict(kind="settle", state=st, cam=CAM_PACKET, p=1.0, jit=True))
    while len(out) < 96:
        out.append(dict(kind="flat", state=FLAT, cam=CAM_PACKET, p=1.0))
    return out


def seq_lightbox():
    out = []
    for e in range(12):
        out.append(dict(kind="lb-off", lamp=0.0, top=1.0))
    for e in range(36):                                            # switch, then a 3 s ramp
        t = (e + 1) / 36
        out.append(dict(kind="lb-ramp", lamp=ease(t) ** 0.8, top=1.0 - 0.6 * ease(min(1, t * 1.5))))
    for e in range(36):
        out.append(dict(kind="lb-hold", lamp=1.0, top=0.4))
    for e in range(12):
        t = (e + 1) / 12
        out.append(dict(kind="lb-down", lamp=1 - ease(t), top=0.4 + 0.6 * ease(t)))
    while len(out) < 108:
        out.append(dict(kind="lb-clean", lamp=0.0, top=1.0))
    return out


# ------------------------------------------------------------------ fixture (#8)
def fixture():
    rep = dict(strip_art_sha256=ART_SHA, B_eq_2M_minus_A=B == 2 * M - A, two_A_minus_M=2 * A - M,
               compose_A_then_M=all(2 * (2 * A - M) - (2 * A - x) == x - D for x in range(M, B + 1)))
    al, be, La, Lm, lag = FLAT
    cs = FG.cross_section(al, be, La, Lm, lag, du=0.25)
    u, X, z = cs["u"], cs["X"], cs["z"]
    f0 = u < A - La / 2; f1 = (u > A + La / 2) & (u < M - Lm / 2); f23 = u > M + Lm / 2
    rep["F0_map_err_u (X = u + D)"] = float(np.abs(X[f0] - (u[f0] + D)).max())
    rep["F1_map_err_u (X = 2M - u)"] = float(np.abs(X[f1] - (2 * M - u[f1])).max())
    rep["F2F3_z_max_u"] = float(np.abs(z[f23]).max())
    rep["layer_heights_u (F1, F0)"] = [round(float(z[f1].mean()), 3), round(float(z[f0].mean()), 3)]
    tv = FG.top_view_index(cs, np.arange(D, SW), exclude_bands=True, tol=0.13)
    V = folded_V(ART)
    worst, cols, crease_cols = 0, 0, []
    for k, Xc in enumerate(np.arange(D, SW)):
        uu = tv["u"][k]
        if np.isnan(uu):
            continue
        if abs(Xc + 0.5 - B) <= La / 2 + 0.5:      # the pressed crease edge itself (curl band A)
            crease_cols.append(int(Xc - D)); continue
        uc = int(np.floor(uu))
        worst = max(worst, int(np.abs(ART[:, uc].astype(int) - V[:, Xc - D].astype(int)).max())); cols += 1
    rep["settled_top_view_vs_V_max_abs_diff"] = worst
    rep["settled_top_view_cols_checked"] = cols
    rep["settled_crease_cols_excluded_xprime"] = crease_cols
    rep["settled_DAG"] = FG.layer_order(cs)
    # ghost positions in the light-box pass
    _, st = lightbox_lum(ART, 1.0, 0.4)
    xs = np.arange(D, SW) - D
    rep["ghost_map_mirrored_A..M"] = "layer2 column x' reads sheet u = 2A - x' (= 2M - X)"
    rep["ghost_map_unmirrored_M..B"] = "layer3 column x' reads sheet u = x' + D"
    rep["ghost_check_samples"] = [dict(sheet_u=int(uu), xprime_mirrored=int(2 * A - uu)) for uu in (700, 900, 1100)] + \
                                 [dict(sheet_u=int(uu), xprime_unmirrored=int(uu - D)) for uu in (1300, 1500, 1700)]
    L1 = st["L1"]; ok = True
    for uu in (700, 900, 1100):
        ok &= np.allclose(L1[:, 2 * A - uu], np.clip((1 - ART[:, uu].astype(np.float32) / 255.0) / (1 - 18 / 255.0), 0, 1))
    L2 = st["L2"]
    for uu in (1300, 1500, 1700):
        ok &= np.allclose(L2[:, uu - D], np.clip((1 - ART[:, uu].astype(np.float32) / 255.0) / (1 - 18 / 255.0), 0, 1))
    rep["ghost_positions_exact"] = bool(ok)
    return rep


# ------------------------------------------------------------------ main
def corner_lift(c):
    # bottom-left corner of the sheet lifted by c u (paper still springing as it lands)
    def f(u, y):
        a = max(0.0, 1 - u / 520.0); b = max(0.0, (y - SH * 0.35) / (SH * 0.65))
        return c * (a ** 1.6) * (b ** 1.4)
    return f


def run(only=None):
    os.makedirs(MEDIA, exist_ok=True); os.makedirs(EDITOR, exist_ok=True)
    rend = Renderer()
    rng = np.random.RandomState(40)
    shots = {"1": seq_shot1(rng),
             "2": seq_puppet(2, CAM_WIDE, CAM_P1, (90, -20, 0)),
             "3": seq_puppet(3, CAM_P1, CAM_P2, (160, 10, 0)),
             "5": seq_fold(rng), "7": seq_replay(rng), "8": seq_lightbox()}
    events = dict(slug="les-caids-de-la-gaudriole", unit="tabletop-lightbox-cinematographer-sound",
                  fps_exposures=12, fps_container=FPS, on="twos", strip_art_sha256=ART_SHA,
                  geometry=dict(A=A, M=M, B=B, D=D, W=SW, H=SH), shots={})
    rest_render = PUP.render({}).astype(np.int16)
    for sk, seq in shots.items():
        if only and sk not in only:
            continue
        d_out = os.path.join(MEDIA, f"shot-{sk}")
        os.makedirs(d_out, exist_ok=True)
        for f in os.listdir(d_out):
            os.remove(os.path.join(d_out, f))
        evs, cache, occ = [], {}, {}
        for k, ex in enumerate(seq):
            t = round(k / 12.0, 4)
            if sk == "8":
                key = (round(ex["lamp"], 4), round(ex["top"], 4))
                if key not in cache:
                    cache[key] = lightbox_frame(ART, ex["lamp"], ex["top"])[0]
                img = cache[key]
                evs.append(dict(exposure=k, t=t, kind=ex["kind"], lamp=round(ex["lamp"], 4), top_light=round(ex["top"], 3),
                                alpha_M_deg=180.0, beta_A_deg=180.0, cam_jitter_u=[0, 0, 0], lamp_gain=1.0,
                                tick=None if ex["kind"] != "lb-ramp" or k != 12 else "switch"))
            else:
                jit = rng.normal(0, 1.0, 3) if ex.get("jit") else np.zeros(3)
                gain = 1 + (rng.uniform(-0.02, 0.02) if ex.get("jit") else 0.0)
                pos, tgt, foc = ex["cam"]
                cam = Cam(pos + jit, tgt + jit * 0.5, foc)
                pose = ex.get("pose")
                art_key = None
                if pose:
                    r = PUP.render(pose).astype(np.int16)
                    changed = np.abs(r - rest_render) > 2
                    sheet = np.where(changed, r, ART).astype(np.uint8)
                    art_key = hashlib.md5(sheet.tobytes()).hexdigest()
                    rend.set_art(sheet)
                else:
                    rend.set_art(ART) if getattr(rend, "_cur", None) else None
                rend._cur = art_key
                if ex["state"] is None:
                    st = OPEN; cs = None
                else:
                    st = ex["state"]; cs = section(*st)
                lift = corner_lift(ex["lift"][1]) if ex.get("lift") else None
                key = (sk if pose else "", art_key, tuple(np.round(np.r_[pos, tgt, foc, jit], 3)), round(gain, 5),
                       tuple(np.round([st[0], st[1], st[2], st[3], st[4][0], st[4][1]], 6)), str(ex.get("rigid")), str(ex.get("lift")), ex["state"] is None)
                if key not in cache:
                    if cs is None:      # empty table
                        cs_e = dict(u=np.array([0.0, 1.0]), X=np.array([-9000.0, -9001.0]), z=np.array([-50.0, -50.0]))
                        img = rend.frame(cam, cs_e, gain)
                    else:
                        img = rend.frame(cam, cs, gain, rigid=ex.get("rigid"), lift=lift, ny=4 if lift else 1)
                        if sk in ("5", "7"):
                            g = OC.geometry_ok(cs)
                            top = OC.f0_on_top(cs, A) and ex["kind"] != "rest" and ex["kind"] != "open-hold"
                            pc = OC.pixel_check(rend, SS) if top else dict(checked=False)
                            occ[key] = dict(geometry=g, f0_top=bool(top), pixels=pc)
                    cache[key] = img
                img = cache[key]
                if pose:
                    rend.set_art(ART); rend._cur = None
                ev = dict(exposure=k, t=t, kind=ex["kind"], alpha_M_deg=round(math.degrees(st[0]), 3),
                          beta_A_deg=round(math.degrees(st[1]), 3), band_A_u=round(st[2], 2), band_M_u=round(st[3], 2),
                          lag_F0_rad=round(st[4][0], 4), lag_F1_rad=round(st[4][1], 4),
                          cam_jitter_u=[round(float(v), 3) for v in jit], lamp_gain=round(gain, 4),
                          cam_target=[round(float(v), 1) for v in tgt])
                if cs is not None:
                    zf = cs["z"][cs["u"] >= M + st[3] / 2]
                    assert np.abs(zf).max() < 1e-9, "F2/F3 left the table"
                    ev["min_z_u"] = round(float(cs["z"].min()), 3); ev["max_z_u"] = round(float(cs["z"].max()), 1)
                    if sk in ("5", "7"):
                        ev["occlusion_dag"] = FG.layer_order(cs)
                        ev["occlusion_check"] = occ.get(key)
                if ex.get("rigid"):
                    ev["sheet_rigid_dx_dy_dz_rotz"] = list(ex["rigid"])
                if ex.get("lift"):
                    ev["corner_lift_u"] = ex["lift"][1]
                if pose:
                    ev["joints"] = pose
                # sound tick: one per moving exposure
                moving = ex["kind"] in ("fall", "settle", "fold", "unfold", "refold") or (pose and k > 0 and pose != seq[k - 1].get("pose"))
                ev["tick"] = ("land" if ex["kind"] == "settle" and (k == 0 or seq[k - 1]["kind"] not in ("settle",)) else
                              "paper" if moving else None)
                evs.append(ev)
            Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(d_out, f"e{k:03d}.png"))
        events["shots"][sk] = dict(n=len(seq), seconds=len(seq) / 12.0, events=evs)
        if sk in ("5", "7"):
            oc = [e["occlusion_check"] for e in evs if e.get("occlusion_check")]
            events["shots"][sk]["occlusion_summary"] = dict(
                exposures=len(evs), geometry_ok_all=all(o["geometry"]["ok"] for o in oc),
                f0_top_exposures_pixel_checked=sum(1 for o in oc if o["pixels"].get("checked")),
                pixel_ok_all=all(o["pixels"].get("ok", True) for o in oc),
                max_wrong_px=max([o["pixels"].get("wrong_px", 0) for o in oc] + [0]))
            print("occlusion", sk, events["shots"][sk]["occlusion_summary"], flush=True)
        print("shot", sk, len(seq), "exposures, distinct renders", len(cache), flush=True)
    return events


if __name__ == "__main__":
    only = sys.argv[1:] or None
    ev = run(only)
    path = os.path.join(SHOTS, "fold-events.json")
    if only and os.path.exists(path):
        old = json.load(open(path)); old["shots"].update(ev["shots"]); ev = old
    json.dump(ev, open(path, "w"), indent=0)
    rep = fixture()
    json.dump(rep, open(os.path.join(SHOTS, "fixture-shots.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1)[:1600])
