"""SCION 35 · render the 32 s scene: a two-colour riso print of the porch at dusk (screen-space dot screen, 6 px),
with the person and the dog pasted on as separately printed cut-outs (print-space dot screens, 7 px) bent per frame by
MLS. Writes build/cache/frames/%04d.jpg and build/cache/meas/%04d.json (measured from the rendered layers).

usage: python3 render.py <start> <end>    (scene frames, end exclusive)
"""
import numpy as np, json, os, sys, time
from PIL import Image, ImageDraw, ImageFont
from common import (W, H, CACHE, PAPER, DOGPAPER, BLUE, ORANGE, inks, screen, mls, jac_svals, splat, smoothstep,
                    GROUND_Y, SILL_X, S_OUT, X_of)
import anim

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
FLOOR_FAR, FLOOR_NEAR = 560.0, 652.0
VP = (700.0, 250.0)
INSIDE_X = SILL_X - 12.0
AP_X0 = 180.0      # the doorway: a lit aperture between this post and the jamb at the sill

# ------------------------------------------------------------------------------------------------ print loading
_prints = {}


def load_print(name):
    if name in _prints:
        return _prints[name]
    meta = anim.meta(name)
    z = np.load(os.path.join(CACHE, 'prints', name + '.npz'))
    layers = {}
    for k in meta['order']:
        a = z[k + '__a'].astype(np.float32); ib = z[k + '__ib'].astype(np.float32); io = z[k + '__io'].astype(np.float32)
        sup = a > 0.002
        # dilate support by 3 px so the cut edge is anti-aliased by the splat
        from PIL import Image as _I, ImageFilter as _F
        sup = np.asarray(_I.fromarray((sup * 255).astype(np.uint8)).filter(_F.MaxFilter(7))) > 0
        ys, xs = np.nonzero(sup)
        layers[k] = dict(xs=xs.astype(np.float32), ys=ys.astype(np.float32), a=a[ys, xs], ib=ib[ys, xs], io=io[ys, xs],
                         bbox=(xs.min(), xs.max(), ys.min(), ys.max()), amask=a)
    _prints[name] = (meta, layers)
    return _prints[name]


G_SP = 8.0   # MLS grid spacing in print px
D_MERGE = 30.0  # print px: handles closer than this in the print act as one (their mean), else a hidden
                # left/right pair that separates in a turn would tear the print between two coincident points


def merge_close(p, q):
    p = [np.array(v) for v in p]; q = [np.array(v) for v in q]
    n = [1] * len(p)
    merged = True
    while merged:
        merged = False
        for a in range(len(p)):
            for b in range(a + 1, len(p)):
                if np.linalg.norm(p[a] - p[b]) < D_MERGE:
                    p[a] = (p[a] * n[a] + p[b] * n[b]) / (n[a] + n[b]); q[a] = (q[a] * n[a] + q[b] * n[b]) / (n[a] + n[b])
                    n[a] += n[b]; del p[b], q[b], n[b]
                    merged = True
                    break
            if merged:
                break
    return np.array(p), np.array(q)


def warp_print(name, Q, out_h=H, out_w=W):
    """bend one view print to target anchors Q. returns rgba (H,W,4) premult-free colour+coverage, per-layer
    coverage maps, and the distortion measures."""
    meta, layers = load_print(name)
    P = meta['anchors']
    rgb = np.zeros((out_h, out_w, 3), np.float32); cov = np.zeros((out_h, out_w), np.float32)
    lay_cov = {}
    strain = {}
    allpos = []
    for k in meta['order']:
        L = layers[k]
        names = meta['layer_anchors'][k]
        p = np.array([P[n] for n in names]); q = np.array([Q[n] for n in names])
        p, q = merge_close(p, q)
        fam = meta['family'][k]
        if fam == 'affine':
            ev = np.linalg.eigvalsh(np.cov((p - p.mean(0)).T)) if len(p) > 2 else np.array([0, 1])
            if len(p) < 3 or ev[0] / max(ev[1], 1e-9) < 0.03:
                fam = 'similarity'     # handles nearly collinear (e.g. the neck seen from behind): affine is singular
        x0, x1, y0, y1 = L['bbox']
        gxs = np.arange(x0 - G_SP, x1 + 2 * G_SP, G_SP); gys = np.arange(y0 - G_SP, y1 + 2 * G_SP, G_SP)
        gx, gy = np.meshgrid(gxs, gys)
        V = np.stack([gx.ravel(), gy.ravel()], 1)
        # MLS runs in film units: the print is at 2x, so handles and grid are scaled by 1/2 first (rigid admits no scale)
        if len(p) < 2:   # every handle of this layer merged into one (e.g. the head seen from behind): translate it
            F = (V * 0.5 - p[0] * 0.5 + q[0]).reshape(len(gys), len(gxs), 2)
        else:
            F = mls(V * 0.5, p * 0.5, q, fam, meta['falloff'][k]).reshape(len(gys), len(gxs), 2)
        # distortion: singular values of the map, normalised so the rest scale (1/2) reads 1.0
        s1, s2, det = jac_svals(F / (G_SP * 0.5))
        cy = ((gys[:-1] + G_SP / 2).astype(int)).clip(0, L['amask'].shape[0] - 1)
        cx = ((gxs[:-1] + G_SP / 2).astype(int)).clip(0, L['amask'].shape[1] - 1)
        wa = L['amask'][np.ix_(cy, cx)] > 0.5
        guard = False
        if wa.any() and ((det[wa] <= 0).any() or (s1 / np.maximum(s2, 1e-6))[wa].max() > 6) and len(p) > 2:
            # fold guard: the handles crossed (a hidden pair separating mid-swing). Re-solve with the two handles that
            # are farthest apart, as a similarity: it can bend and turn but cannot fold. Logged per frame.
            dd = ((p[:, None] - p[None]) ** 2).sum(-1); a_, b_ = np.unravel_index(dd.argmax(), dd.shape)
            p2, q2 = p[[a_, b_]], q[[a_, b_]]
            F = mls(V * 0.5, p2 * 0.5, q2, 'similarity', meta['falloff'][k]).reshape(len(gys), len(gxs), 2)
            s1, s2, det = jac_svals(F / (G_SP * 0.5)); guard = True
        if wa.any():
            an = (s1 / np.maximum(s2, 1e-6))[wa]
            ar = (s1 * s2)[wa]
            strain[k] = dict(family=fam, fold_guard=guard, aniso_max=float(an.max()), aniso_mean=float(an.mean()),
                             area_min=float(ar.min()), area_max=float(ar.max()), folds=int((det[wa] <= 0).sum()),
                             handle_err=float(np.abs((mls(p * 0.5, p * 0.5, q, fam, meta['falloff'][k]) if len(p) > 1 else q) - q).max()))
        # bilinear lookup of the grid at every print sample
        u = (L['xs'] - gxs[0]) / G_SP; v = (L['ys'] - gys[0]) / G_SP
        i0 = np.clip(np.floor(u).astype(int), 0, len(gxs) - 2); j0 = np.clip(np.floor(v).astype(int), 0, len(gys) - 2)
        fu = (u - i0)[:, None]; fv = (v - j0)[:, None]
        pos = (F[j0, i0] * (1 - fu) * (1 - fv) + F[j0, i0 + 1] * fu * (1 - fv) + F[j0 + 1, i0] * (1 - fu) * fv + F[j0 + 1, i0 + 1] * fu * fv)
        px, py = pos[:, 0] - 0.5, pos[:, 1] - 0.5
        bx0 = int(max(0, np.floor(px.min()) - 2)); bx1 = int(min(out_w, np.ceil(px.max()) + 3))
        by0 = int(max(0, np.floor(py.min()) - 2)); by1 = int(min(out_h, np.ceil(py.max()) + 3))
        if bx1 <= bx0 or by1 <= by0:
            continue
        vals = np.stack([L['a'], L['a'] * L['ib'], L['a'] * L['io']], 1)
        acc, wt = splat(px - bx0, py - by0, vals, by1 - by0, bx1 - bx0)
        # fill pinholes where a strong stretch left no sample (3x3 normalised box)
        holes = wt <= 1e-6
        if holes.any():
            pa = np.pad(acc, ((1, 1), (1, 1), (0, 0))); pw = np.pad(wt, 1)
            sa = sum(pa[1 + dy:pa.shape[0] - 1 + dy, 1 + dx:pa.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            sw = sum(pw[1 + dy:pw.shape[0] - 1 + dy, 1 + dx:pw.shape[1] - 1 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            acc[holes] = sa[holes]; wt[holes] = sw[holes]
        wts = np.maximum(wt, 1e-6)
        c = np.clip(acc[..., 0] / wts, 0, 1) * (wt > 1e-6)
        ib = np.where(acc[..., 0] > 1e-6, acc[..., 1] / np.maximum(acc[..., 0], 1e-6), 0)
        io = np.where(acc[..., 0] > 1e-6, acc[..., 2] / np.maximum(acc[..., 0], 1e-6), 0)
        col = inks(DOGPAPER, ib.astype(np.float32), io.astype(np.float32))
        sl = (slice(by0, by1), slice(bx0, bx1))
        rgb[sl] = rgb[sl] * (1 - c[..., None]) + col * c[..., None]
        cov[sl] = cov[sl] + c * (1 - cov[sl])
        lc = np.zeros((out_h, out_w), np.float32); lc[sl] = c
        lay_cov[k] = lc
    return rgb, cov, lay_cov, strain


# ------------------------------------------------------------------------------------------------ the place
def floor_x_at(x_far, y):
    """a board seam that is at x_far on the far floor edge, followed toward the viewer (perspective from VP)."""
    return VP[0] + (x_far - VP[0]) * (y - VP[1]) / (FLOOR_FAR - VP[1])


def static_place():
    B = np.zeros((H, W), np.float32); O = np.zeros((H, W), np.float32)
    x, y = XX, YY
    out = x >= INSIDE_X + 24
    # sky: deep at the top, lighter and faintly warm at the horizon
    sky = out & (y < 470)
    B[sky] = (0.96 - 0.30 * (y / 470.0))[sky]
    O[sky] = (0.20 * smoothstep(250, 460, y))[sky]
    # moon
    dm = np.sqrt((x - 1040) ** 2 + (y - 112) ** 2)
    moon = np.clip((30 - dm) / 1.5, 0, 1)
    B = B * (1 - moon * 0.92); O = O * (1 - moon) + 0.06 * moon
    halo = np.clip(1 - dm / 110, 0, 1) ** 2 * out
    B = B - 0.12 * halo
    # far hedge / trees: a bumpy dark band
    top = 395 + 18 * np.sin(x / 37.0) + 11 * np.sin(x / 13.0 + 1.3) + 25 * np.sin(x / 151.0 + 0.4) - 40 * np.exp(-((x - 820) / 90.0) ** 2)
    hedge = out & (y > top) & (y < FLOOR_FAR)
    B[hedge] = 0.94; O[hedge] = 0.2
    # porch roof eave and post
    eave = out & (y < 34)
    B[eave] = 0.97; O[eave] = 0.3
    post = (x > 1170) & (x < 1192) & (y < FLOOR_FAR)
    B[post] = 0.88; O[post] = 0.2
    # railing (behind the dog's path)
    rail = out & (x < 1250) & (((y > 452) & (y < 461)) | ((y > 546) & (y < 552)))
    B[rail] = 0.86; O[rail] = 0.22
    bal = out & (x < 1250) & (y >= 461) & (y <= 546) & (((x - 360) % 36) < 7)
    B[bal] = 0.8; O[bal] = 0.2
    # porch floor: boards in perspective
    fl = (y >= FLOOR_FAR) & (y < FLOOR_NEAR) & (x >= INSIDE_X + 6)
    B[fl] = 0.78 - 0.06 * ((y[fl] - FLOOR_FAR) / (FLOOR_NEAR - FLOOR_FAR)); O[fl] = 0.16
    for xf in np.arange(300, 1500, 46):
        xs = floor_x_at(xf, y)
        seam = fl & (np.abs(x - xs) < 1.0)
        B[seam] = 0.92
    # porch fascia and the ground below
    fas = (y >= FLOOR_NEAR) & (y < 676) & (x >= INSIDE_X - 10)
    B[fas] = 0.86; O[fas] = 0.18
    gr = (y >= 676)
    B[gr] = 0.97; O[gr] = 0.24
    # steps at the end of the porch (x = 4.9)
    for n in range(3):
        sx = X_of(4.9) - 2 + n * 14
        st = (x >= sx) & (y >= FLOOR_FAR + n * 26) & (y < FLOOR_NEAR + 24)
        B[st] = 0.7 + 0.08 * n; O[st] = 0.12
    # ------- the house: interior (cut away), wall and jamb
    ins = x < INSIDE_X
    # wall above the door and the cut wall band
    wall = (x >= INSIDE_X) & (x < INSIDE_X + 24) & (y < 162)
    B[wall] = 0.97; O[wall] = 0.55
    lint = (x >= INSIDE_X - 200) & (x < INSIDE_X + 24) & (y >= 150) & (y < 162)
    B[lint] = 0.95; O[lint] = 0.55
    return B, O


PLACE_B, PLACE_O = None, None


def interior(L):
    """the room behind the door: dim before, lamplit after. L = light level 0..1"""
    B = np.zeros((H, W), np.float32); O = np.zeros((H, W), np.float32)
    x, y = XX, YY
    ins = x < INSIDE_X
    wallr = ins & (y < FLOOR_FAR)
    B[ins & (y >= 676)] = 0.97; O[ins & (y >= 676)] = 0.24
    # wallpaper: soft vertical stripes
    stripe = 0.5 + 0.5 * np.cos(2 * np.pi * x / 26.0)
    B[wallr] = (0.88 - 0.36 * L + 0.08 * stripe)[wallr]
    O[wallr] = (0.32 + 0.36 * L + 0.06 * stripe * L)[wallr]
    # glow around the lamp (a ceiling lamp off the top of the frame, at the left)
    g = np.exp(-(((x - 60) / 260.0) ** 2 + ((y - 40) / 330.0) ** 2))
    B[wallr] = np.clip(B[wallr] - 0.25 * L * g[wallr], 0, 1)
    O[wallr] = np.clip(O[wallr] + 0.18 * L * g[wallr], 0, 1)
    # a picture frame on the wall (an empty frame: no image)
    pf = ins & (x > 40) & (x < 106) & (y > 220) & (y < 306)
    pin = ins & (x > 47) & (x < 99) & (y > 227) & (y < 299)
    B[pf & ~pin] = 0.95; O[pf & ~pin] = 0.6
    B[pin] = B[pin] * 0.8
    # floor inside
    fi = ins & (y >= FLOOR_FAR) & (y < FLOOR_NEAR)
    B[fi] = 0.84 - 0.42 * L; O[fi] = 0.42 + 0.3 * L
    # floor seams (perspective, continuing the porch)
    for xf in np.arange(-500, INSIDE_X, 46):
        seam = fi & (np.abs(x - floor_x_at(xf, y)) < 1.0)
        B[seam] = np.clip(B[seam] + 0.3, 0, 1)
    fas = ins & (y >= FLOOR_NEAR) & (y < 676)
    B[fas] = 0.9; O[fas] = 0.3 + 0.2 * L
    # a low bench by the door (where the person sits)
    bench_top = ins & (x > 0) & (x < 92) & (y > 498) & (y < 506)
    B[bench_top] = 0.97; O[bench_top] = 0.55
    legs = ins & (y >= 506) & (y < 572) & (((x > 4) & (x < 10)) | ((x > 80) & (x < 86)))
    B[legs] = 0.97; O[legs] = 0.5
    return B, O, ins


def door_panel(theta_deg, L):
    """the door leaf, hinged at the far jamb, swung theta degrees into the room. Drawn in perspective."""
    th = np.deg2rad(theta_deg)
    hx = AP_X0                                   # hinge on the room-side post of the doorway
    xf = hx + (SILL_X - 4 - AP_X0) * np.cos(th)  # closed: spans the opening; open past 90: lies back into the room
    yb_h, yt_h = FLOOR_FAR + 2, 162
    yb_f = FLOOR_FAR + 2 + (FLOOR_NEAR - FLOOR_FAR - 6) * np.sin(th) * 0.5
    yt_f = 162 + 10 * np.sin(th)
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    d.polygon([(hx, yt_h), (hx, yb_h), (xf, yb_f), (xf, yt_f)], fill=255)
    m = np.asarray(im, np.float32) / 255
    # panel mouldings: two inset rectangles (lines) on the leaf
    im2 = Image.new('L', (W, H), 0); d2 = ImageDraw.Draw(im2)
    for a0, a1 in ((0.1, 0.45), (0.55, 0.9)):
        def P(u, v):
            xa = hx + (xf - hx) * u
            yt = yt_h + (yt_f - yt_h) * u; yb = yb_h + (yb_f - yb_h) * u
            return (xa, yt + (yb - yt) * v)
        d2.line([P(0.18, a0), P(0.82, a0), P(0.82, a1), P(0.18, a1), P(0.18, a0)], fill=255, width=2)
    lines = np.asarray(im2, np.float32) / 255
    B = 0.62 - 0.22 * L + 0.35 * lines
    O = 0.5 + 0.12 * L
    kx = hx + (xf - hx) * 0.86; ky = (yt_h + yb_h) / 2 + 30
    knob = np.clip(5 - np.sqrt((XX - kx) ** 2 + (YY - ky) ** 2), 0, 1)
    B = np.maximum(B, knob); O = np.maximum(O, knob * 0.8)
    return m, B, O


def ellipse(cx, cy, rx, ry, soft=4.0):
    d = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)
    return np.clip((1 - d) * min(rx, ry) / soft + 0.5, 0, 1)


GRAIN = None
FONT = None


def frame(i):
    global PLACE_B, PLACE_O, GRAIN, FONT
    if PLACE_B is None:
        PLACE_B, PLACE_O = static_place()
        rng = np.random.default_rng(35)
        g = rng.normal(0, 1, (H // 4 + 1, W // 4 + 1)).astype(np.float32)
        g = np.asarray(Image.fromarray(((g * 20 + 128).clip(0, 255)).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32)
        GRAIN = 1 + (g - 128) / 128 * 0.035
        FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 11)
    wd = anim.world(i)
    L = wd['light']
    B = PLACE_B.copy(); O = PLACE_O.copy()
    x, y = XX, YY
    Bi, Oi, ins = interior(0.12 + 0.33 * L)            # the room plane stays dim; the light is in the doorway
    ap = (x >= AP_X0) & (x < INSIDE_X) & (y >= 162) & (y < FLOOR_NEAR)
    gl = np.clip(1 - (y - 162) / 700.0, 0.55, 1) * L
    Bi[ap] = (Bi[ap] * (1 - gl[ap]) + 0.02 * gl[ap]); Oi[ap] = (Oi[ap] * (1 - gl[ap]) + 0.24 * gl[ap])
    post = ((x >= AP_X0 - 9) & (x < AP_X0) & (y >= 154) & (y < FLOOR_FAR + 2)) | ((x >= AP_X0 - 9) & (x < INSIDE_X) & (y >= 152) & (y < 162))
    Bi[post] = 0.95; Oi[post] = 0.5
    B[ins] = Bi[ins]; O[ins] = Oi[ins]
    # light out of the door, across the sill and the porch floor (and a little up the railing)
    x, y = XX, YY
    dx = np.clip(x - (INSIDE_X + 12), 0, None)
    spill_floor = ((y >= FLOOR_FAR) & (y < FLOOR_NEAR) & (x > INSIDE_X)) * np.exp(-dx / 560.0)
    # the beam widens toward the viewer: brighter on the near half of the floor
    spill_floor = spill_floor * (0.55 + 0.45 * smoothstep(FLOOR_FAR, FLOOR_NEAR, y))
    spill_up = ((y < FLOOR_FAR) & (y > 300) & (x > INSIDE_X + 24)) * np.exp(-dx / 260.0) * smoothstep(300, 560, y)
    sp = L * spill_floor + 0.5 * L * spill_up
    O = np.clip(O + 0.72 * sp, 0, 1); B = np.clip(B - 0.5 * sp, 0, 1)
    # door leaf
    dm, dB, dO = door_panel(wd['door'], L)
    B = B * (1 - dm) + dB * dm; O = O * (1 - dm) + dO * dm
    # jamb (far reveal) and sill: wood, lit by the room
    jamb = (x >= INSIDE_X + 8) & (x < INSIDE_X + 24) & (y >= 162) & (y < FLOOR_FAR + 2)
    B[jamb] = 0.93; O[jamb] = 0.45 + 0.2 * L
    sx_far = INSIDE_X + 2; sx_near = floor_x_at(sx_far, FLOOR_NEAR)
    sxx = sx_far + (sx_near - sx_far) * (y - FLOOR_FAR) / (FLOOR_NEAR - FLOOR_FAR)
    sill = (y >= FLOOR_FAR - 3) & (y < FLOOR_NEAR + 1) & (x >= sxx - 2) & (x < sxx + 26)
    B[sill] = 0.3 - 0.22 * L; O[sill] = 0.32 + 0.25 * L
    sedge = (y >= FLOOR_NEAR - 2) & (y < FLOOR_NEAR + 8) & (x >= sx_near - 2) & (x < sx_near + 26)
    B[sedge] = 0.85; O[sedge] = 0.5
    # ---- dog pose (measured later) and its shadow on the floor
    shown, Q, root, info = anim.dog_pose(i)
    paws = np.array([Q[k] for k in ('fl_paw', 'fr_paw', 'hl_paw', 'hr_paw')])
    body = np.array([Q[k] for k in ('chest', 'rump', 'withers', 'croup')])
    sx0, sx1 = min(paws[:, 0].min(), body[:, 0].min()), max(paws[:, 0].max(), body[:, 0].max())
    sh = ellipse((sx0 + sx1) / 2, GROUND_Y + 3, (sx1 - sx0) / 2 + 14 + 10 * info['lie'], 9 + 4 * info['lie'], 5)
    # with the door light, a longer cast shadow away from the door
    sh2 = ellipse((sx0 + sx1) / 2 + 34, GROUND_Y + 8, (sx1 - sx0) / 2 + 40, 10, 8) * L
    shade_ = np.clip(0.42 * sh + 0.25 * sh2, 0, 0.5)
    B = np.clip(B + shade_, 0, 1); O = O * (1 - 0.5 * shade_)
    # person shadow
    pshown, PQ, proot = anim.person_pose(i)
    psh = ellipse(proot[0] + 30, proot[1] + 3, 60, 6, 5)
    B = np.clip(B + 0.3 * psh, 0, 1)
    # ---- screen the place (screen space, 6 px, blue 15 deg, orange 75 deg, misregistered)
    ib = screen(B, 5.0, 15.0, xs=XX, ys=YY); io = screen(O, 5.0, 75.0, ox=1.5, oy=-1.0, xs=XX, ys=YY)
    img = inks(PAPER, ib, io)
    # ---- the person, a printed cut-out
    prgb, pcov, _, pstrain = warp_print(pshown, PQ)
    img = img * (1 - pcov[..., None]) + prgb * pcov[..., None] * (0.72 + 0.28 * L)
    # ---- the dog, a printed cut-out bent by MLS
    drgb, dcov, dlay, strain = warp_print(shown, Q)
    # ambient on the dog's stock: dusk blue-grey, warmed in the door light
    warm = L * np.exp(-np.clip(XX - INSIDE_X, 0, None) / 380.0)
    amb = np.stack([0.86 + 0.14 * warm, 0.87 + 0.09 * warm, 0.96 - 0.06 * warm], -1)
    img = img * (1 - dcov[..., None]) + drgb * amb * dcov[..., None]
    img = img * GRAIN[..., None]
    out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
    # ---- measurements from the rendered layers
    ys_, xs_ = np.nonzero(dcov > 0.5)
    hc = dlay.get('head')
    hy, hx = np.nonzero(hc > 0.5) if hc is not None else (np.array([]), np.array([]))
    ty, tx = np.nonzero(dlay['torso'] > 0.5)
    meas = dict(i=i, t=round(i / 24, 4), shown=shown, trans=[info['trans'][0], info['trans'][1], round(info['trans'][2], 3)],
                psi=round(float(info['psi']), 1),
                cx=float(xs_.mean()) if len(xs_) else None, cy=float(ys_.mean()) if len(ys_) else None,
                top=int(ys_.min()) if len(ys_) else None, bottom=int(ys_.max()) if len(ys_) else None,
                left=int(xs_.min()) if len(xs_) else None, right=int(xs_.max()) if len(xs_) else None,
                head_cx=float(hx.mean()) if len(hx) else None, head_cy=float(hy.mean()) if len(hy) else None,
                head_area=int(len(hx)),
                torso_cx=float(tx.mean()) if len(tx) else None, torso_cy=float(ty.mean()) if len(ty) else None,
                torso_top=int(ty.min()) if len(ty) else None,
                nose=[round(float(v), 1) for v in Q['nose']], eye=[round(float(v), 1) for v in Q['eye_r']],
                rump=[round(float(v), 1) for v in Q['rump']], withers=[round(float(v), 1) for v in Q['withers']],
                tail3=[round(float(v), 1) for v in Q['tail3']],
                inside_px=int((dcov[:, :int(SILL_X)] > 0.5).sum()), outside_px=int((dcov[:, int(SILL_X):] > 0.5).sum()),
                tail_inside=bool(Q['tail3'][0] < SILL_X),
                strain=strain, door=wd['door'], light=L)
    return out, meas


if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2])
    os.makedirs(os.path.join(CACHE, 'frames'), exist_ok=True); os.makedirs(os.path.join(CACHE, 'meas'), exist_ok=True)
    t0 = time.time()
    for i in range(a, b):
        im, m = frame(i)
        im.save(os.path.join(CACHE, 'frames', '%04d.jpg' % i), quality=93)
        json.dump(m, open(os.path.join(CACHE, 'meas', '%04d.json' % i), 'w'))
    print('frames', a, b, 'in %.1fs' % (time.time() - t0))
