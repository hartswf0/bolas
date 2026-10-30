"""SCION 22 · the felt-board stage and the frame renderer.
python3 render.py bg            -> cache/bg_dark.jpg, cache/bg_lit.jpg (the set, drawn once in world metres at 330 px/m)
python3 render.py K M           -> scene frames i with i % M == K into cache/frames/, measurements into cache/measure/
Every puppet piece comes from cache/rig.pkl (the runtime's draw lists); this file only cuts it out of felt and lights it."""
import sys, os, json, math, pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from common import (CACHE, N, FPS, W, H, WALL_IN, WALL_OUT, DOOR_TOP, DOOR_W, STEPS_X, PERSON_BESIDE, ramp, lerp, camera_track)
from felt import Layer, fibre
from shapes import cr, ellipse, strip

R = 330.0
WX0, WX1, WY0, WY1 = -2.4, 5.8, -0.8, 3.4
BW, BH = int((WX1 - WX0) * R), int((WY1 - WY0) * R)


def bgp(x, y):
    return ((x - WX0) * R, (WY1 - y) * R)


def bgpts(P):
    P = np.asarray(P, float)
    return np.stack([(P[:, 0] - WX0) * R, (WY1 - P[:, 1]) * R], 1)


def rect(x0, y0, x1, y1):
    return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], float)


def light_tint(xw, yw, L):
    """world light: dusk ambient outside, the room inside (behind a scrim until the door opens), and the door's light
    spilling out over the porch once it is open.  xw: (W,), yw: (H,) -> (H, W, 3)"""
    X = xw[None, :]
    Y = yw[:, None]
    inside = 1 / (1 + np.exp((X - (WALL_IN + WALL_OUT) / 2) / 0.05))
    dark_in = np.array([0.40, 0.38, 0.50]); lit_in = np.array([1.05, 0.90, 0.68])
    amb = np.array([0.60, 0.64, 0.86])
    warm = np.array([0.62, 0.40, 0.12])
    Lx = max(L, 0.06)
    spill = Lx * np.exp(-np.clip(X - WALL_OUT, 0, None) / 1.5) * np.exp(-np.clip(Y - 0.9, 0, None) / 0.8) * (X > WALL_IN - 0.1)
    out = amb[None, None, :] + spill[..., None] * warm[None, None, :]
    inn = (dark_in + (lit_in - dark_in) * L)[None, None, :] * np.ones_like(X)[..., None] * np.ones_like(Y)[..., None]
    return (out * (1 - inside[..., None]) + inn * inside[..., None]).astype(np.float32)


def sky_image():
    yy = np.linspace(WY1, WY0, BH)[:, None]
    top, mid, hor = np.array([30, 34, 70]), np.array([74, 66, 112]), np.array([170, 112, 110])
    u = np.clip((yy - 0.3) / 3.0, 0, 1)
    col = np.where(u > 0.45, mid + (top - mid) * ((u - 0.45) / 0.55), hor + (mid - hor) * (u / 0.45))
    img = np.broadcast_to(col[:, None, :], (BH, BW, 3)).astype(np.float32) / 255.0
    fib = fibre(1.0)
    n = fib.shape[0]
    ys = np.arange(BH) % n; xs = np.arange(BW) % n
    img = img * (0.92 + 0.08 * fib[np.ix_(ys, xs)])[..., None]
    # moon halo
    mx, my = bgp(3.55, 2.72)
    gy, gx = np.mgrid[0:BH, 0:BW]
    d = np.hypot(gx - mx, gy - my) / R
    img = img + (np.exp(-(d / 0.45) ** 2) * 0.10)[..., None] * np.array([0.9, 0.85, 0.7])
    return img


def build_background():
    sky = sky_image()
    lay = Layer(BW, BH)
    unlit = Layer(BW, BH)        # moon and stars: they make their own light
    P = lambda pts: bgpts(pts)
    rng = np.random.default_rng(5)
    # stars: little cross stitches
    for _ in range(70):
        x, y = rng.uniform(WALL_OUT + 0.3, WX1), rng.uniform(1.7, WY1)
        if math.hypot(x - 3.55, y - 2.72) < 0.3:
            continue
        r = rng.uniform(0.012, 0.022)
        for a in (0.3, 0.3 + math.pi / 2):
            unlit.piece(P(strip(np.array([(x - r * math.cos(a), y - r * math.sin(a)), (x + r * math.cos(a), y + r * math.sin(a))]), [0.004, 0.004], cap=False)), (236, 226, 190), shadow=False, fuzz=0.3)
    unlit.piece(P(ellipse(3.55, 2.72, 0.15, 0.15, n=48)), (240, 228, 186), stitch=True, shadow=False)
    unlit.piece(P(ellipse(3.50, 2.75, 0.03, 0.025)), (214, 200, 160), shadow=False)
    unlit.piece(P(ellipse(3.61, 2.68, 0.022, 0.02)), (214, 200, 160), shadow=False)
    # far hills and trees (garden beyond the porch)
    hills = [(WALL_OUT, -0.5), (WALL_OUT, 0.55), (1.4, 0.75), (2.6, 0.62), (3.7, 0.85), (4.8, 0.66), (5.8, 0.78), (5.8, -0.5)]
    lay.piece(P(cr(hills, n=8)), (52, 62, 92), shadow=False)
    hills2 = [(WALL_OUT, -0.5), (WALL_OUT, 0.32), (1.0, 0.42), (2.2, 0.36), (3.3, 0.5), (4.4, 0.40), (5.8, 0.46), (5.8, -0.5)]
    lay.piece(P(cr(hills2, n=8)), (44, 58, 72), shadow=True)
    for tx, th, tw in ((2.15, 2.05, 0.75), (5.15, 1.8, 0.6)):
        lay.piece(P(rect(tx - 0.05, 0.0, tx + 0.05, th * 0.5)), (48, 40, 44))
        for k, (dx, dy, r) in enumerate([(0, th, tw * 0.55), (-tw * 0.45, th * 0.8, tw * 0.42), (tw * 0.45, th * 0.82, tw * 0.45), (0, th * 0.66, tw * 0.5)]):
            lay.piece(P(ellipse(tx + dx, dy, r, r * 0.8, n=36)), (40 + 4 * k, 58 + 3 * k, 66 + 2 * k), stitch=k == 0)
    # garden ground beyond the steps
    lay.piece(P(rect(4.85, -0.8, WX1, -0.5)), (46, 62, 50))
    # porch: back rail (far side of the porch, low), posts, roof
    for px in (1.05, 2.95, 4.72):
        lay.piece(P(rect(px - 0.04, 0.0, px + 0.04, 0.92)), (96, 76, 66), stitch=False)
    lay.piece(P(rect(WALL_OUT, 0.86, 4.76, 0.93)), (104, 82, 70))
    lay.piece(P(rect(WALL_OUT, 0.46, 4.76, 0.50)), (92, 72, 62), shadow=True)
    lay.piece(P(rect(4.74, 0.0, 4.86, 2.42)), (122, 92, 70), stitch=True)
    lay.piece(P([(WALL_OUT, 2.62), (5.05, 2.40), (5.05, 2.30), (WALL_OUT, 2.42)]), (84, 64, 70), stitch=True)
    for k in range(9):
        x = WALL_OUT + 0.08 + k * 0.5
        lay.piece(P(rect(x, 2.31 + (2.62 - 2.42) * (1 - (x - WALL_OUT) / 4.5) * 0.0, x + 0.03, 2.40 + 0.2 * (1 - (x - WALL_OUT) / 4.5))), (66, 50, 56), shadow=False)
    # porch deck: fascia, boards, the dark crawl space beneath, the steps
    lay.piece(P(rect(WALL_OUT, -0.8, 4.92, -0.16)), (36, 32, 40), shadow=False)
    for k in range(18):
        x = WALL_OUT + 0.1 + k * 0.25
        lay.piece(P(strip(np.array([(x, -0.17), (x + 0.22, -0.78)]), [0.008, 0.008], cap=False)), (58, 50, 58), shadow=False)
    lay.piece(P(rect(WALL_OUT - 0.02, -0.17, 4.94, 0.0)), (128, 90, 62), stitch=True)
    for k in range(10):
        x = WALL_OUT + 0.45 * k + 0.2
        lay.piece(P(rect(x, -0.165, x + 0.012, -0.005)), (96, 66, 46), shadow=False)
    for k, (sx, sy) in enumerate([(4.92, -0.17), (5.14, -0.34), (5.36, -0.50)]):
        lay.piece(P(rect(sx, sy - 0.17 + (0.0 if k < 2 else 0.0), sx + 0.26, sy)), (120, 84, 58), stitch=True)
    # the house: interior back wall (wallpaper), skirting, ceiling, floor section, the wall section with the doorway
    lay.piece(P(rect(WX0, 0.0, WALL_IN, 2.78)), (186, 136, 104), shadow=False)
    for k in range(260):
        x, y = rng.uniform(WX0 + 0.05, WALL_IN - 0.05), rng.uniform(0.2, 2.7)
        lay.piece(P(ellipse(x, y, 0.012, 0.012, n=8)), (160, 104, 92) if k % 2 else (204, 168, 120), shadow=False, fuzz=0.2)
    lay.piece(P(rect(WX0, 0.0, WALL_IN, 0.13)), (122, 84, 62), stitch=True)
    lay.piece(P(rect(WX0, 1.52, WALL_IN, 1.56)), (150, 104, 80), shadow=True)
    lay.piece(P(rect(WX0, 2.78, WALL_IN + 0.01, WY1)), (62, 48, 58), shadow=True)
    lay.piece(P(rect(WX0, WY0, WALL_OUT, 0.0)), (64, 46, 44), shadow=True)
    for k in range(14):
        x = WX0 + 0.1 + k * 0.2
        lay.piece(P(strip(np.array([(x, -0.03), (x + 0.4, -0.75)]), [0.006, 0.006], cap=False)), (84, 62, 58), shadow=False)
    lay.piece(P(rect(WX0, -0.04, WALL_IN, 0.0)), (140, 98, 66), shadow=False)
    # the inner hall doorway: the lit depth of the house (the look-in target)
    lay.piece(P(rect(-0.98, 0.0, -0.58, 1.86)), (150, 106, 70), stitch=True)
    lay.piece(P(rect(-0.94, 0.0, -0.62, 1.82)), (236, 196, 128), shadow=False)
    lay.piece(P(rect(-0.94, 0.0, -0.62, 0.05)), (170, 120, 80), shadow=False)
    lay.piece(P(rect(-0.86, 0.85, -0.70, 1.25)), (214, 170, 100), shadow=False)
    # picture on the wall, lamp table, bench
    lay.piece(P(rect(-1.62, 1.22, -1.12, 1.62)), (118, 78, 50), stitch=True)
    lay.piece(P(rect(-1.57, 1.27, -1.17, 1.57)), (90, 104, 128))
    lay.piece(P(cr([(-1.57, 1.27), (-1.57, 1.36), (-1.42, 1.43), (-1.28, 1.37), (-1.17, 1.40), (-1.17, 1.27)], n=5)), (70, 92, 74))
    lay.piece(P(ellipse(-1.25, 1.50, 0.03, 0.03)), (236, 222, 170), shadow=False)
    lay.piece(P(rect(-2.25, 0.66, -1.75, 0.71)), (120, 80, 54), stitch=True)
    for lx in (-2.20, -1.82):
        lay.piece(P(rect(lx, 0.0, lx + 0.035, 0.66)), (104, 70, 48))
    lay.piece(P(rect(-2.02, 0.71, -1.98, 1.02)), (170, 150, 120))
    lay.piece(P([(-2.16, 1.0), (-1.84, 1.0), (-1.90, 1.24), (-2.10, 1.24)]), (232, 196, 124), stitch=True)
    lay.piece(P(rect(PERSON_BESIDE - 0.24, 0.38, PERSON_BESIDE + 0.16, 0.44)), (128, 86, 56), stitch=True)
    for lx in (PERSON_BESIDE - 0.21, PERSON_BESIDE + 0.10):
        lay.piece(P(rect(lx, 0.0, lx + 0.04, 0.38)), (110, 74, 48))
    # wall section above the door (lintel and wall cut), the far door casing, the sill
    lay.piece(P(rect(WALL_IN, 0.0, WALL_OUT, DOOR_TOP)), (170, 124, 82), stitch=True)
    lay.piece(P(rect(WALL_IN + 0.03, 0.0, WALL_OUT - 0.03, DOOR_TOP - 0.03)), (150, 106, 70), shadow=False)
    lay.piece(P(rect(WALL_IN - 0.02, DOOR_TOP, WALL_OUT + 0.03, WY1)), (82, 60, 66), stitch=True)
    for k in range(10):
        y = DOOR_TOP + 0.12 + k * 0.14
        lay.piece(P(strip(np.array([(WALL_IN + 0.01, y), (WALL_OUT - 0.01, y + 0.12)]), [0.006, 0.006], cap=False)), (104, 80, 84), shadow=False)
    lay.piece(P(rect(WALL_IN - 0.05, DOOR_TOP - 0.05, WALL_OUT + 0.05, DOOR_TOP + 0.02)), (150, 108, 72), stitch=True)
    lay.piece(P(rect(0.30, 0.0, 0.62, 0.035)), (196, 156, 104), stitch=False)
    # bake: dark (door ajar, scrim) and lit
    xw = WX0 + (np.arange(BW) + 0.5) / R
    yw = WY1 - (np.arange(BH) + 0.5) / R
    for L, name in ((0.0, 'bg_dark'), (1.0, 'bg_lit')):
        tint = light_tint(xw, yw, L)
        base = sky * (1 - unlit.a)[..., None] * (1 - unlit.under_shadow)[..., None] + unlit.rgb
        out = base * (1 - lay.under_shadow)[..., None] * (1 - lay.a)[..., None] + lay.rgb * tint
        if L > 0:
            # the door's light: a sheer organza shaft from the doorway down onto the porch, and the lamp's glow
            gl = Image.new('L', (BW, BH), 0)
            ImageDraw.Draw(gl).polygon([tuple(p) for p in bgpts([(WALL_OUT, DOOR_TOP - 0.05), (WALL_OUT, 0.0), (3.2, 0.0), (1.6, 0.9)])], fill=255)
            g = np.asarray(gl.filter(ImageFilter.GaussianBlur(30)), np.float32) / 255.0
            out = out + g[..., None] * np.array([0.20, 0.14, 0.05]) * 0.9
            gy, gx = np.mgrid[0:BH, 0:BW]
            for (gx0, gy0, rr, kk) in ((-2.0, 1.12, 0.5, 0.22), (-0.78, 1.0, 0.55, 0.20)):
                lx, ly = bgp(gx0, gy0)
                d = np.hypot(gx - lx, gy - ly) / R
                out = out + (np.exp(-(d / rr) ** 2) * kk)[..., None] * np.array([1.0, 0.8, 0.45])
        img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
        img.save(os.path.join(CACHE, name + '.jpg'), quality=95)
    print('background', BW, BH)


def bg_frame(bgimg, cam):
    s = cam['s']
    k = s / R
    sw, sh = int(round(BW * k)), int(round(BH * k))
    scaled = bgimg.resize((sw, sh), Image.LANCZOS) if abs(k - 1) > 1e-3 else bgimg
    x0 = (cam['camx'] - 640.0 / s - WX0) * s
    y0 = (WY1 - cam['floor'] / s) * s
    return scaled.transform((W, H), Image.AFFINE, (1, 0, x0, 0, 1, y0), resample=Image.BILINEAR)


def render_frame(i, rig, bgs, cams):
    cam = cams[i]
    t = i / FPS
    s = cam['s']
    s = float(s)
    zoom = s / 230.0
    L = ramp(t, 6.15, 6.75)
    bd = np.asarray(bg_frame(bgs[0], cam), np.float32) / 255.0
    if L > 0:
        bl = np.asarray(bg_frame(bgs[1], cam), np.float32) / 255.0
        bg = bd * (1 - L) + bl * L
    else:
        bg = bd
    xw = cam['camx'] + (np.arange(W) + 0.5 - 640.0) / s
    yw = (cam['floor'] - (np.arange(H) + 0.5)) / s
    tint = light_tint(xw, yw, L)
    lay = Layer(W, H)
    S = lambda P: np.stack([640.0 + (np.asarray(P)[:, 0] - cam['camx']) * s, cam['floor'] - np.asarray(P)[:, 1] * s], 1)
    st = rig['states'][i]
    # door leaf (behind everything that moves): its visible width is the leaf's swing, a sheer light crack while ajar
    ang = math.radians(st['door_angle'])
    ex = WALL_IN - DOOR_W * math.sin(ang)
    lift = 0.05 * math.sin(ang)
    leaf = [(ex, -0.01 - lift * 0.3), (WALL_IN, 0.0), (WALL_IN, 1.99), (ex, 1.99 + lift)]
    lay.piece(S(leaf), (146, 96, 60), zoom=zoom, stitch=True, tint=tint)
    if math.sin(ang) > 0.15:
        for (a0, a1) in ((0.12, 0.88), (1.08, 1.86)):
            ux0, ux1 = 0.18, 0.82
            pp = [(lerp(ex, WALL_IN, ux0), a0), (lerp(ex, WALL_IN, ux1), a0), (lerp(ex, WALL_IN, ux1), a1), (lerp(ex, WALL_IN, ux0), a1)]
            lay.piece(S(pp), (128, 82, 52), zoom=zoom, shadow=True, tint=tint)
        lay.piece(S(ellipse(ex + 0.06 * math.sin(ang), 0.96, 0.028, 0.028)), (214, 182, 74), zoom=zoom, tint=tint)
    if L < 1:
        crack = [(WALL_IN - 0.02, 0.0), (WALL_IN + 0.02, 0.0), (WALL_IN + 0.02, 1.99), (WALL_IN - 0.02, 1.99)]
        lay.piece(S(crack), (250, 214, 140), zoom=zoom, shadow=False, alpha=0.75 * (1 - L), fuzz=0.0, tex=False)
    items = sorted(rig['frames'][i], key=lambda it: it['z'])
    for it in items:
        P = S(it['pts'])
        if it['tex'] == 'shadow':
            lay.piece(P, (10, 8, 14), zoom=zoom, shadow=False, alpha=0.38, fuzz=0.0, tex=False)
            continue
        rec = None
        if it['g'] == 'dog':
            rec = 'dog'
        lay.piece(P, it['col'], zoom=zoom, stitch=it['st'], shadow=it['sh'], tint=tint, record=rec, tile_off=(int(P[0, 0] * 0.0), 0))
        if it['n'].startswith('Dog/Head') and '/Ear' not in it['n']:
            g = lay.masks.setdefault('head', np.zeros((H, W), np.float32))
            m = Image.new('L', (W, H), 0)
            ImageDraw.Draw(m).polygon([tuple(p) for p in P], fill=255)
            g[:] = np.maximum(g, np.asarray(m, np.float32) / 255.0)
    out = lay.over(bg)
    # vignette: a felt board under a warm stage lamp
    gy, gx = np.ogrid[0:H, 0:W]
    v = 1 - 0.22 * (((gx - 640) / 760.0) ** 2 + ((gy - 380) / 520.0) ** 2)
    out = out * v[..., None]
    img = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    img.save(os.path.join(CACHE, 'frames', '%04d.jpg' % i), quality=93)
    # measurement from this render
    m = lay.masks.get('dog')
    hm = lay.masks.get('head')
    meas = {'i': i}
    if m is not None and m.sum() > 10:
        ys, xs_ = np.nonzero(m > 0.5)
        w = m[ys, xs_]
        cx, cy = float((xs_ * w).sum() / w.sum()), float((ys * w).sum() / w.sum())
        meas.update({'cx': cx, 'cy': cy, 'x0': int(xs_.min()), 'x1': int(xs_.max()), 'y0': int(ys.min()), 'y1': int(ys.max()), 'area': float(w.sum())})
        wxp = cam['camx'] + (xs_ - 640.0) / s
        meas['inside_share'] = float(w[wxp < WALL_IN].sum() / w.sum())
        meas['outside_share'] = float(w[wxp > WALL_OUT].sum() / w.sum())
        meas['x_world'] = cam['camx'] + (cx - 640.0) / s
        meas['frac_in_frame'] = 1.0
    if hm is not None and hm.sum() > 5:
        ys, xs_ = np.nonzero(hm > 0.5)
        meas['hx'], meas['hy'] = float(xs_.mean()), float(ys.mean())
        meas['head_top'] = int(ys.min())
    json.dump(meas, open(os.path.join(CACHE, 'measure', '%04d.json' % i), 'w'))


def main():
    if sys.argv[1] == 'bg':
        build_background()
        return
    k, M = int(sys.argv[1]), int(sys.argv[2])
    only = [int(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
    os.makedirs(os.path.join(CACHE, 'frames'), exist_ok=True)
    os.makedirs(os.path.join(CACHE, 'measure'), exist_ok=True)
    rig = pickle.load(open(os.path.join(CACHE, 'rig.pkl'), 'rb'))
    cams = [st['cam'] for st in rig['states']]
    bgs = [Image.open(os.path.join(CACHE, 'bg_dark.jpg')).convert('RGB'), Image.open(os.path.join(CACHE, 'bg_lit.jpg')).convert('RGB')]
    idx = only if only else range(k, N, M)
    for i in idx:
        render_frame(i, rig, bgs, cams)


if __name__ == '__main__':
    main()
