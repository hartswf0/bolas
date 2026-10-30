"""The multiplane camera: render the 768 scene frames and measure the dog in every one.

Per frame: the camera position and focus come from the camera track (common.CAM_KEYS); every plane is projected by its
own transform (cards: an affine scale+shift = parallax f/(Z-cz); quads: a homography); collage pieces are cut and laid
at their depths; all layers are composited far to near.  A dog pass (the alpha of the dog's pieces after every nearer
occluder) and a head pass are kept for measurement.

usage: python3 render.py [start end step]   (frames -> cache/frames/s%04d.jpg, measurements -> cache/meas/%04d.json)
"""
import os, sys, json, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from common import *
import world, dog, person

OUT = os.path.join(CACHE, 'frames'); MEAS = os.path.join(CACHE, 'meas')
os.makedirs(OUT, exist_ok=True); os.makedirs(MEAS, exist_ok=True)

# ---------------------------------------------------------------- textures for the pieces (collage fragments)
TEX_SRC = {
    # name: (file, box, colour, contrast)
    'flank': (KIT + '/archive-dog/frames/f000.jpg', (158, 104, 214, 150), (0.80, 0.58, 0.36), 1.5),
    'saddle': (KIT + '/archive-dog/frames/f000.jpg', (118, 66, 166, 112), (0.30, 0.24, 0.21), 1.3),
    'chest': (KIT + '/archive-dog/frames/f030.jpg', (158, 96, 186, 126), (0.95, 0.86, 0.70), 1.2),
    'leg': (KIT + '/archive-dog/frames/f000.jpg', (168, 150, 204, 190), (0.84, 0.64, 0.42), 1.4),
    'face': (KIT + '/archive-dog/frames/f030.jpg', (186, 98, 226, 140), (0.78, 0.58, 0.40), 1.5),
    'muzzle': (KIT + '/archive-dog/frames/f000.jpg', (118, 66, 150, 98), (0.22, 0.17, 0.15), 1.2),
    'black': (KIT + '/archive-dog/frames/f000.jpg', (120, 70, 140, 90), (0.08, 0.07, 0.07), 1.0),
    'eye': (KIT + '/archive-dog/frames/f000.jpg', (120, 70, 140, 90), (0.05, 0.04, 0.04), 1.0),
    'smock': (SHOTS + '/door-sam/frames/f000.jpg', (215, 105, 305, 245), None, 1.0),
    'hair': (SHOTS + '/door-sam/frames/f000.jpg', (238, 18, 282, 62), (0.16, 0.13, 0.13), 0.6),
    'sleeve': (SHOTS + '/door-sam/frames/f000.jpg', (200, 112, 214, 200), None, 1.0),
    'trousers': (SHOTS + '/door-sam/frames/f000.jpg', (228, 258, 272, 286), (0.22, 0.22, 0.30), 1.0),
    'shoe': (SHOTS + '/door-sam/frames/f000.jpg', (228, 262, 262, 286), (0.10, 0.09, 0.10), 1.0),
    'skin': (SHOTS + '/hand-sam/frames/f000.jpg', (250, 45, 330, 75), (0.80, 0.62, 0.52), 1.0),
    'hand': (SHOTS + '/hand-sam/frames/f000.jpg', (195, 50, 250, 100), (0.88, 0.70, 0.58), 1.0),
}


def make_tex(name):
    f, box, col, con = TEX_SRC[name]
    im = Image.open(f).convert('RGB').crop(box).resize((128, 128), Image.BICUBIC)
    a = np.asarray(im, np.float32) / 255
    if col is not None:
        l = a.mean(-1, keepdims=True)
        l = np.clip((l - l.mean()) * con + 0.55, 0, 1.2)
        a = l * np.array(col, np.float32) * 1.25
    # paper grain: the found fur is soft at this scale, so the cut fragment keeps a printed-paper tooth
    r = np.random.default_rng(len(name) * 31 + 5)
    a = a * (1 + 0.10 * r.standard_normal(a.shape[:2])[..., None].astype(np.float32))
    a = np.concatenate([a, a[:, ::-1]], 1); a = np.concatenate([a, a[::-1]], 0)
    a = np.tile(a, (2, 2, 1))
    return Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8))


TEX = {k: make_tex(k) for k in TEX_SRC}

# ---------------------------------------------------------------- planes
PLANES = world.build()
BLUR_PX = [0, 1.4, 2.8, 4.5]
for pl in PLANES:
    a = pl['img']
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), 'RGBA')
    pl['pil'] = [im]
    if pl['kind'] == 'card':
        X0, X1, Y0, Y1 = pl['rect']
        p = im.width / (X1 - X0)
        cz0 = -5.0
        s0 = F_PX / (pl['Z'] - cz0)
        for b in BLUR_PX[1:]:
            pl['pil'].append(im.filter(ImageFilter.GaussianBlur(b * p / s0)))
BYNAME = {p['name']: p for p in PLANES}
DOF_K = 14.0


def blur_index(depth, focus_d):
    c = DOF_K * abs(1.0 / depth - 1.0 / focus_d) * 10
    return int(np.argmin([abs(c - b) for b in BLUR_PX]))


def draw_card(canvas, pl, cam, focus_d):
    X0, X1, Y0, Y1 = pl['rect']
    d = pl['Z'] - cam[2]
    if d <= 0.05:
        return None
    s = F_PX / d
    im = pl['pil'][blur_index(d, focus_d) if len(pl['pil']) > 1 else 0]
    p = im.width / (X1 - X0)
    a = p / s
    c = (cam[0] - (W / 2) / s - X0) * p
    f = (Y1 - cam[1] - (H / 2) / s) * p
    # only the screen box the plane covers
    u0 = int(max(0, math.floor(W / 2 + s * (X0 - cam[0])))); u1 = int(min(W, math.ceil(W / 2 + s * (X1 - cam[0]))))
    v0 = int(max(0, math.floor(H / 2 - s * (Y1 - cam[1])))); v1 = int(min(H, math.ceil(H / 2 - s * (Y0 - cam[1]))))
    if u1 <= u0 or v1 <= v0:
        return None
    patch = im.transform((u1 - u0, v1 - v0), Image.AFFINE, (a, 0, c + a * u0, 0, a, f + a * v0), Image.BILINEAR)
    canvas.alpha_composite(patch, (u0, v0))
    return patch, (u0, v0)


def draw_quad(canvas, im, corners, cam, clipz=0.25):
    """a textured planar quad (per-plane projection). corners: 4 world points matching image corners
    (0,0),(w,0),(w,h),(0,h).  Horizontal floors are clipped to stay in front of the camera."""
    corners = [np.array(c, float) for c in corners]
    w, h = im.size
    tex = [(0, 0), (w, 0), (w, h), (0, h)]
    # clip: if the near edge (rows at h) is behind the camera, move it forward
    zmin = cam[2] + clipz
    if corners[3][2] < zmin or corners[2][2] < zmin:
        z0, z1 = corners[0][2], corners[3][2]
        if z0 <= zmin:
            return None
        u = (zmin - z1) / (z0 - z1)
        newh = h * (1 - u)
        corners[3] = corners[3] + (corners[0] - corners[3]) * u
        corners[2] = corners[2] + (corners[1] - corners[2]) * u
        tex = [(0, 0), (w, 0), (w, newh), (0, newh)]
    uu, vv, _ = project(np.array(corners), cam)
    scr = list(zip(uu, vv))
    u0 = int(max(0, math.floor(min(uu)))); u1 = int(min(W, math.ceil(max(uu))))
    v0 = int(max(0, math.floor(min(vv)))); v1 = int(min(H, math.ceil(max(vv))))
    if u1 <= u0 or v1 <= v0:
        return None
    Hm = homography([(x - u0, y - v0) for x, y in scr], tex)
    coeffs = (Hm[0, 0], Hm[0, 1], Hm[0, 2], Hm[1, 0], Hm[1, 1], Hm[1, 2], Hm[2, 0], Hm[2, 1])
    patch = im.transform((u1 - u0, v1 - v0), Image.PERSPECTIVE, coeffs, Image.BILINEAR)
    # mask to the quad polygon (perspective transform repeats edge pixels outside)
    m = Image.new('L', patch.size, 0)
    ImageDraw.Draw(m).polygon([(x - u0, y - v0) for x, y in scr], fill=255)
    patch.putalpha(ImageChops.multiply(patch.getchannel('A'), m))
    canvas.alpha_composite(patch, (u0, v0))
    return patch, (u0, v0)


# ---------------------------------------------------------------- light
def door_open(t):
    """door angle (deg into the room) and room light."""
    ang = 46 + (102 - 46) * smooth((t - 6.2) / 0.7)
    light = 0.55 + 0.45 * smooth((t - 6.2) / 0.9)
    return ang, light


def light_at(Pt, t):
    """dusk ambient (cool) + warm light from the open door, falling off with distance from the doorway."""
    ang, li = door_open(t)
    amb = np.array([0.62, 0.62, 0.78])
    if Pt[2] > 0.02 and abs(Pt[0]) < 3:
        warm = np.array([1.05, 0.80, 0.55]) * (0.75 + 0.35 * li)
        return warm
    d = math.sqrt(Pt[0] ** 2 + (Pt[1] - 0.6) ** 2 + (Pt[2] * 1.3) ** 2)
    k = li * math.exp(-max(0, d - 0.4) / 0.9) * (0.4 + 0.6 * smooth((t - 6.2) / 0.9))
    return amb * (1 - k * 0.6) + np.array([1.15, 0.84, 0.55]) * k


def spill_layer(t, cam, canvas):
    """the light coming out of the door: a warm trapezoid laid on the porch floor."""
    ang, li = door_open(t)
    k = 0.18 + 0.62 * smooth((t - 6.2) / 0.9)
    w, h = 200, 200
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    zz = yy / h                       # 0 at the sill, 1 at 2 m out
    half = 0.5 + zz * 0.55
    xc = (xx / w - 0.5) * 2.4         # metres across, door centre 0
    a = np.clip((half - np.abs(xc)) * 4, 0, 1) * np.exp(-zz * 1.6) * k
    rgb = np.zeros((h, w, 3), np.float32) + np.array([255, 196, 120], np.float32)
    im = Image.fromarray(np.dstack([rgb, a * 200]).astype(np.uint8), 'RGBA')
    corners = [(-1.2, 0.002, 0.0), (1.2, 0.002, 0.0), (1.2, 0.002, -2.0), (-1.2, 0.002, -2.0)]
    draw_quad(canvas, im, corners, cam)


def shadow(canvas, centre, F, length, width, cam, alpha):
    pts = []
    L = np.array([-F[2], 0, F[0]])
    for k in range(24):
        a = 2 * math.pi * k / 24
        p = centre + F * math.cos(a) * length / 2 + L * math.sin(a) * width / 2
        p = np.array([p[0], 0.003, p[2]])
        pts.append(p)
    uu, vv, _ = project(np.array(pts), cam)
    u0, v0 = int(min(uu)) - 12, int(min(vv)) - 12
    u1, v1 = int(max(uu)) + 12, int(max(vv)) + 12
    if u1 < 0 or v1 < 0 or u0 > W or v0 > H:
        return
    m = Image.new('L', (u1 - u0, v1 - v0), 0)
    ImageDraw.Draw(m).polygon([(x - u0, y - v0) for x, y in zip(uu, vv)], fill=int(255 * alpha))
    m = m.filter(ImageFilter.GaussianBlur(5))
    sh = Image.new('RGBA', m.size, (12, 10, 18, 0)); sh.putalpha(m)
    canvas.alpha_composite(sh, (u0, v0)) if u0 >= 0 and v0 >= 0 else paste_clip(canvas, sh, u0, v0)


def paste_clip(canvas, patch, u0, v0):
    x0, y0 = max(0, u0), max(0, v0)
    x1, y1 = min(W, u0 + patch.width), min(H, v0 + patch.height)
    if x1 <= x0 or y1 <= y0:
        return None
    sub = patch.crop((x0 - u0, y0 - v0, x1 - u0, y1 - v0))
    canvas.alpha_composite(sub, (x0, y0))
    return sub, (x0, y0)


# ---------------------------------------------------------------- collage pieces
JIT = {}
HEAD_RIM = {'skull', 'neck', 'muzzle', 'eara', 'earb'}


def jitter(name, n):
    if name not in JIT:
        r = np.random.default_rng(abs(hash(name)) % (2 ** 31) if False else sum(map(ord, name)) * 7919)
        JIT[name] = 1 + 0.07 * np.convolve(r.standard_normal(n + 4), np.ones(5) / 5, 'valid')[:n]
    return JIT[name]


# a cut-paper profile (a silhouette portrait, facing right), in units of half the head height
PROFILE = [(0, -1.0), (0.4, -0.92), (0.7, -0.65), (0.78, -0.35), (0.74, -0.25), (0.92, -0.02), (0.75, 0.06),
           (0.79, 0.2), (0.72, 0.28), (0.76, 0.38), (0.62, 0.55), (0.3, 0.65), (0.0, 0.6), (-0.3, 0.75), (-0.6, 0.55),
           (-0.8, 0.25), (-0.92, -0.05), (-1.0, -0.2), (-1.25, -0.25), (-1.3, -0.5), (-1.1, -0.68), (-0.85, -0.62),
           (-0.6, -0.88), (-0.3, -1.0)]


def outline(name, shape, cam):
    """screen polygon of a piece and its depth."""
    if shape[0] == 'cap':
        _, a, b, r1, r2 = shape
        (ua, ub), (va, vb), (da, db) = [np.array(v) for v in zip(*[project(a, cam), project(b, cam)])]
        R1, R2 = F_PX * r1 / da, F_PX * r2 / db
        dx, dy = ub - ua, vb - va
        L = math.hypot(dx, dy)
        n = 32
        jt = jitter(name, n)
        if L < 1e-3 or L + min(R1, R2) <= max(R1, R2):
            c = (ua, va) if R1 >= R2 else (ub, vb); R = max(R1, R2)
            pts = [(c[0] + R * jt[k] * math.cos(2 * math.pi * k / n), c[1] + R * jt[k] * math.sin(2 * math.pi * k / n)) for k in range(n)]
            return pts, (da + db) / 2, (ua, va, ub, vb), max(R, 1)
        ang = math.atan2(dy, dx)
        # tangent angle offset for unequal radii
        beta = math.asin(max(-1, min(1, (R1 - R2) / L)))
        pts = []
        half = n // 2
        for k in range(half + 1):          # cap around b, from +90+beta to -90-beta (front)
            th = ang + (math.pi / 2 + beta) - (math.pi + 2 * beta) * k / half
            pts.append((ub + R2 * jt[k] * math.cos(th), vb + R2 * jt[k] * math.sin(th)))
        for k in range(half + 1):          # cap around a (back)
            th = ang - (math.pi / 2 + beta) - (math.pi - 2 * beta) * k / half
            pts.append((ua + R1 * jt[(k + half) % n] * math.cos(th), va + R1 * jt[(k + half) % n] * math.sin(th)))
        return pts, (da + db) / 2, (ua, va, ub, vb), max((R1 + R2) / 2, 1)
    if shape[0] == 'prof':
        _, c, Fv, half = shape
        uc, vc, dc = project(c, cam)
        uf, _, _ = project(c + Fv * 0.2, cam)
        sgn = 1 if uf >= uc else -1
        R = F_PX * half / dc
        pts = [(uc + sgn * x * R, vc + y * R) for x, y in PROFILE]
        return pts, dc, (uc, vc, uc + sgn, vc), R
    if shape[0] == 'tri':
        _, base, tip, wdt = shape
        Ld = np.array([1.0, 0, 0])
        (ub, vb, db), (ut, vt, dt) = project(base, cam), project(tip, cam)
        hw = F_PX * wdt / 2 / db
        dx, dy = ut - ub, vt - vb
        L = max(math.hypot(dx, dy), 1e-3)
        nx, ny = -dy / L, dx / L
        jt = jitter(name, 4)
        pts = [(ub + nx * hw * jt[0], vb + ny * hw * jt[0]), (ut + nx * hw * 0.12, vt + ny * hw * 0.12),
               (ut - nx * hw * 0.12, vt - ny * hw * 0.12), (ub - nx * hw * jt[1], vb - ny * hw * jt[1])]
        return pts, (db + dt) / 2, (ub, vb, ut, vt), max(hw, 1)


def draw_piece(canvas, name, shape, texname, shade, cam, light, masks):
    pts, depth, (ua, va, ub, vb), rad = outline(name, shape, cam)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    u0, v0 = int(math.floor(min(xs))) - 4, int(math.floor(min(ys))) - 4
    u1, v1 = int(math.ceil(max(xs))) + 6, int(math.ceil(max(ys))) + 6
    if u1 < 0 or v1 < 0 or u0 >= W or v0 >= H:
        return None
    w, h = u1 - u0, v1 - v0
    SS = 2
    m = Image.new('L', (w * SS, h * SS), 0)
    ImageDraw.Draw(m).polygon([((x - u0) * SS, (y - v0) * SS) for x, y in pts], fill=255)
    m = m.resize((w, h), Image.BILINEAR)
    # texture: rides with the piece (rotates with the bone, scales with depth)
    ang = math.atan2(vb - va, ub - ua)
    sc = (F_PX / depth) / 260.0 * 1.0
    ca, sa = math.cos(ang), math.sin(ang)
    off = (sum(map(ord, name)) * 37) % 128
    # output (x,y) -> texture: rotate by -ang around (ua,va), divide by scale
    a_ = ca / sc; b_ = sa / sc; d_ = -sa / sc; e_ = ca / sc
    cx, cy = ua - u0, va - v0
    coeffs = (a_, b_, -a_ * cx - b_ * cy + 128 + off, d_, e_, -d_ * cx - e_ * cy + 128 + off // 2)
    tx = TEX[texname].transform((w, h), Image.AFFINE, coeffs, Image.BILINEAR)
    lt = np.array(light) * shade
    tx = Image.fromarray(np.clip(np.asarray(tx, np.float32) * lt, 0, 255).astype(np.uint8))
    # cut paper edge: a thin pale rim where the scissors went
    if rad > 3:
        inner = m.filter(ImageFilter.MinFilter(3))
        if name in HEAD_RIM:
            # the head carries a warm lit rim (light from the door side): it must never read as the tail
            inner = m.filter(ImageFilter.MinFilter(5))
            rim = ImageChops.subtract(m, inner).point(lambda v: v * 0.9)
            tx.paste(Image.new('RGB', tx.size, (246, 222, 184)), (0, 0), rim)
        else:
            rim = ImageChops.subtract(m, inner).point(lambda v: v * 0.45)
            tx.paste(Image.new('RGB', tx.size, tuple(int(min(255, c * 235)) for c in lt / max(lt.max(), 1e-3) * 0.9)), (0, 0), rim)
    # paper relief: a soft shadow of the piece on whatever is behind it
    if rad > 3:
        sh = m.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: v * 0.32)
        shp = Image.new('RGBA', (w, h), (10, 8, 14, 0)); shp.putalpha(sh)
        paste_clip(canvas, shp, u0 + 2, v0 + 2)
    pc = tx.convert('RGBA'); pc.putalpha(m)
    paste_clip(canvas, pc, u0, v0)
    for key in masks:
        mk = masks[key]
        if mk is not None:
            mk.paste(255, (u0, v0), m) if False else paste_mask(mk, m, u0, v0)
    return (ua, va, ub, vb, depth)


def paste_mask(mk, m, u0, v0):
    x0, y0 = max(0, u0), max(0, v0)
    x1, y1 = min(W, u0 + m.width), min(H, v0 + m.height)
    if x1 <= x0 or y1 <= y0:
        return
    sub = m.crop((x0 - u0, y0 - v0, x1 - u0, y1 - v0))
    region = mk.crop((x0, y0, x1, y1))
    mk.paste(ImageChops.lighter(region, sub), (x0, y0))


def occlude(mk, patch_info):
    """a nearer plane hides what is behind it: dog pass *= (1 - plane alpha)."""
    if patch_info is None or mk is None:
        return
    patch, (u0, v0) = patch_info
    a = patch.getchannel('A')
    region = mk.crop((u0, v0, u0 + patch.width, v0 + patch.height))
    mk.paste(ImageChops.multiply(region, ImageChops.invert(a)), (u0, v0))


# ---------------------------------------------------------------- one frame
def render(i):
    t = i / FPS
    cam, focus_z = camera(t)
    focus_d = focus_z - cam[2]
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    dpieces, dmeta = dog.frame(i)
    ppieces, pmeta = person.frame(i)
    ang, li = door_open(t)
    dmask = Image.new('L', (W, H), 0); hmask = Image.new('L', (W, H), 0); hmask0 = Image.new('L', (W, H), 0)
    items = []   # (sortkey, kind, payload)
    for pl in PLANES:
        key = {'porch_floor': -0.001, 'room_floor': 3.59, 'steps': -0.002, 'porch_front': -2.1, 'railing': -2.11}.get(pl['name'], pl.get('Z', 0))
        if pl['name'] == 'door_leaf':
            key = 0.45
        items.append((key, 'plane', pl))
    items.append((-0.003, 'spill', None))
    items.append((-0.004, 'shadow', None))
    for pc in dpieces + ppieces:
        name, group, shape, tex, shade, bias = pc
        zc = shape[1][2] if shape[0] == 'prof' else (shape[1][2] + shape[2][2]) / 2
        items.append((zc + bias, 'piece', pc))
    items.sort(key=lambda it: -it[0])
    rec = {}
    for key, kind, pl in items:
        if kind == 'plane':
            if pl['kind'] == 'card':
                info = draw_card(canvas, pl, cam, focus_d)
            elif pl['kind'] == 'quad':
                im = pl['pil'][0]
                if pl.get('interior'):
                    im = lit(pl, li)
                info = draw_quad(canvas, im, pl['corners'], cam)
            elif pl['kind'] == 'leaf':
                a = math.radians(ang)
                hx = -0.46
                c = [(hx, 2.04, 0.0), (hx + 0.92 * math.cos(a), 2.04, 0.92 * math.sin(a)),
                     (hx + 0.92 * math.cos(a), 0.0, 0.92 * math.sin(a)), (hx, 0.0, 0.0)]
                info = draw_quad(canvas, pl['pil'][0], c, cam)
            if pl.get('interior') and pl['kind'] == 'card':
                pass
            if key < 0.45:
                occlude(dmask, info); occlude(hmask, info)
            # room dims before the door opens: darken interior planes in the canvas after drawing the wall
            if pl['name'] == 'house_wall':
                pass
        elif kind == 'spill':
            spill_layer(t, cam, canvas)
        elif kind == 'shadow':
            m = dmeta
            ctr = (m['S'] + m['H']) / 2
            Fv = np.array([math.cos(math.radians(m['hb'])), 0, math.sin(math.radians(m['hb']))])
            shadow(canvas, ctr, Fv, 0.85, 0.36 + 0.06 * m['lie'], cam, 0.55)
            pm = pmeta
            shadow(canvas, pm['R'] + np.array([0.15 * pm['sit'], 0, 0]), np.array([1.0, 0, 0]), 0.5 + 0.6 * pm['sit'], 0.4, cam, 0.5)
        else:
            name, group, shape, tex, shade, bias = pl
            P3 = shape[1] if shape[0] in ('tri', 'prof') else (shape[1] + shape[2]) / 2
            light = light_at(P3, t)
            if group == 'person':
                light = light * (0.55 if t < 6.2 else 0.75)    # backlit: a silhouette against the room
            masks = {}
            if group in ('body', 'head'):
                masks['d'] = dmask
                if group == 'head':
                    masks['h'] = hmask
            if group == 'head':
                masks['h0'] = hmask0
            r = draw_piece(canvas, name, shape, tex, shade, cam, light, masks)
            if r is not None:
                rec[name] = r
    # interior light level (the door "opens and light comes out")
    frame_rgb = canvas.convert('RGB')
    # measurements
    D = np.asarray(dmask, np.float32) / 255
    Hm_ = np.asarray(hmask, np.float32) / 255
    area = D.sum()
    yy, xx = np.mgrid[0:H, 0:W]
    meas = dict(i=i, t=round(t, 4), cam=[round(float(c), 4) for c in cam], focus_z=round(focus_z, 3), area_px=float(area))
    if area > 0:
        cu, cv = float((D * xx).sum() / area), float((D * yy).sum() / area)
        rows = np.where(D.max(1) > 0.5)[0]; cols = np.where(D.max(0) > 0.5)[0]
        zr = float(dmeta['R'][2])
        meas.update(x_screen=round(cu, 2), y_screen=round(cv, 2), bbox=[int(cols.min()), int(rows.min()), int(cols.max()), int(rows.max())],
                    x_world_measured=round(float(unproject_x(cu, zr, cam)), 4), z_root=round(zr, 4),
                    height_m=round(float((rows.max() - rows.min()) * (zr - cam[2] + 0.0) / F_PX), 4))
    ha = Hm_.sum()
    hv0 = [np.asarray(hmask0, np.float32).sum() / 255]
    if ha > 0:
        meas['head_screen'] = [round(float((Hm_ * xx).sum() / ha), 2), round(float((Hm_ * yy).sum() / ha), 2)]
    # pieces as laid: skull, muzzle tip, withers (screen) and their depths
    # laid pieces unprojected at the depth they were laid at: world position of the back (saddle) and the head
    def world_of(r):
        u = (r[0] + r[2]) / 2; v = (r[1] + r[3]) / 2; dd = r[4]
        return [cam[0] + (u - W / 2) * dd / F_PX, cam[1] - (v - H / 2) * dd / F_PX, cam[2] + dd]
    for nm in ('saddle', 'skull', 'nose', 'flank'):
        if nm in rec:
            meas['w_' + nm] = [round(float(c), 4) for c in world_of(rec[nm])]
    hv = np.asarray(hmask, np.float32).sum()
    meas['head_visible_share'] = round(float(ha / hv0[0]), 3) if hv0[0] > 0 else None
    if 'skull' in rec and 'nose' in rec:
        sk, no = rec['skull'], rec['nose']
        meas['skull'] = [round(sk[0], 2), round(sk[1], 2), round(sk[4], 3)]
        meas['nose'] = [round(no[0], 2), round(no[1], 2), round(no[4], 3)]
    wu, wv, wd = project(dmeta['withers'], cam)
    meas['withers'] = [round(float(wu), 2), round(float(wv), 2), round(float(wd), 3)]
    meas['px_per_m'] = round(F_PX / float(wd), 3)
    meas['hb'] = round(dmeta['hb'], 2); meas['hh'] = round(dmeta['hh'], 2)
    meas['lie_drive'] = round(dmeta['lie'], 3); meas['look_drive'] = round(dmeta['look'], 3)
    meas['feet'] = [[round(float(f[0]), 4), round(float(f[1]), 4), round(float(f[2]), 4)] for f in dmeta['feet']]
    meas['swinging'] = dmeta['swinging']
    meas['person_x'] = round(float(pmeta['x']), 3)
    meas['door_angle'] = round(ang, 2); meas['room_light'] = round(li, 3)
    # what share of the dog's pixels are inside the door frame region (x in the opening and deeper than the wall)
    return frame_rgb, meas, dmask, hmask


LIT_CACHE = {}


def lit(pl, li):
    k = (pl['name'], round(li, 2))
    if k not in LIT_CACHE:
        im = pl['pil'][0]
        a = np.asarray(im, np.float32).copy()
        a[..., :3] *= li
        LIT_CACHE.clear() if len(LIT_CACHE) > 8 else None
        LIT_CACHE[k] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
    return LIT_CACHE[k]


def apply_room_light():
    """interior cards are dimmed by the room light level at draw time."""
    pass


# interior cards need the light level too: wrap draw_card for interior planes
_orig_draw_card = draw_card


def draw_card(canvas, pl, cam, focus_d):
    if pl.get('interior'):
        t = CUR_T[0]
        ang, li = door_open(t)
        key = (pl['name'], round(li, 2))
        if key not in LIT_CACHE:
            src = pl['pil'][0]
            a = np.asarray(src, np.float32).copy(); a[..., :3] *= li
            LIT_CACHE[key] = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'RGBA')
        pl2 = dict(pl); pl2['pil'] = [LIT_CACHE[key]]
        return _orig_draw_card(canvas, pl2, cam, focus_d)
    return _orig_draw_card(canvas, pl, cam, focus_d)


CUR_T = [0.0]


def main(a, b, step=1):
    for i in range(a, b, step):
        CUR_T[0] = i / FPS
        im, meas, dm, hm = render(i)
        im.save(os.path.join(OUT, f's{i:04d}.jpg'), quality=90)
        json.dump(meas, open(os.path.join(MEAS, f'{i:04d}.json'), 'w'))


if __name__ == '__main__':
    args = [int(v) for v in sys.argv[1:]] or [0, N]
    main(*args)
