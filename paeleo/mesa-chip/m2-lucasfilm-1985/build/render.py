#!/usr/bin/env python3
"""SCION-LUCASFILM-1985 · MESA CHIP, handmade. A keyed skeleton under a skin of convex glass shards, each with its own normal; a
beauty pass and a separate specular pass composited over it; four jittered sub-frames per frame for motion blur (180 degree shutter);
one rack focus; Uncle Mesa as the painted "live-action" plate actor with grain. Run: python3 render.py"""
import sys, os, json, math, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from common import *
from dopesheet import mesa_keys, knight_keys, sample
sc = score(); rng = np.random.default_rng(1985)
FLOOR, SILL = 470.0, 300.0
def sx(x): return 480 + 58 * x
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
WX = sx(6.2); WL, WR, WT = WX - 28, WX + 28, 120
MK, KK = mesa_keys(sc), knight_keys(sc)
json.dump(dict(mesa=[(t, n) for t, _, n in MK], knight=[(t, n) for t, _, n in KK]), open(os.path.join(OUT, 'dopesheet.json'), 'w'), indent=0)
L = dict(th=64, sh=62, torso=82, neck=26, ua=50, fa=46)

def d(a, f): a = math.radians(a); return (f * math.sin(a), math.cos(a))
def fk(p, f, sc_=1.0):
    J = {'hip': (0.0, 0.0)}; s = p['s']
    up = (f * math.sin(math.radians(s)), -math.cos(math.radians(s)))
    J['chest'] = (up[0] * L['torso'], up[1] * L['torso'])
    hn = (f * math.sin(math.radians(s + p['n'])), -math.cos(math.radians(s + p['n'])))
    J['head'] = (J['chest'][0] + hn[0] * L['neck'], J['chest'][1] + hn[1] * L['neck'])
    J['sh'] = (J['chest'][0] - up[0] * 8, J['chest'][1] - up[1] * 8)
    for side in 'LR':
        a, e = p['a' + side] + s, p['e' + side]
        el = tuple(J['sh'][i] + d(a, f)[i] * L['ua'] for i in (0, 1)); J['el' + side] = el
        J['ha' + side] = tuple(el[i] + d(a + e, f)[i] * L['fa'] for i in (0, 1)); J['fa' + side] = a + e
        t, k = p['t' + side], p['k' + side]
        kn = tuple(d(t, f)[i] * L['th'] for i in (0, 1)); J['kn' + side] = kn
        J['ft' + side] = tuple(kn[i] + d(t - k, f)[i] * L['sh'] for i in (0, 1))
    r = math.radians(f * p['rot']); c, sn = math.cos(r), math.sin(r)
    return {k: ((v[0] * c - v[1] * sn) * sc_, (v[0] * sn + v[1] * c) * sc_) if isinstance(v, tuple) else v for k, v in J.items()}, r

def lowest(J): return max(J[k][1] for k in ('ftL', 'ftR', 'knL', 'knR', 'hip', 'chest', 'head')) + 6
def ground(x): return FLOOR - 112 + 56 * ease((x + 6.95) / .2) + 56 * ease((x + 6.4) / .2)

def place_mesa(t):
    fr = sc['frames'][min(575, int(round(t * FPS)))]; x = fr['mesa']['x']
    f = -1 if (21.0 <= t < 21.9) else 1; p = sample(MK, t)
    J, r = fk(p, f); g = FLOOR if t >= 21.9 else ground(x)
    oy = g - lowest(J); ox = sx(x)
    if p['rot'] < -20: ox -= f * 30 * min(1, -p['rot'] / 88)
    if t >= 21.9: ox -= 22 * ease((t - 21.9) / .2)   # back onto the step   # lying, he is centred on his place, not pivoted on the hip
    return {k: (v[0] + ox, v[1] + oy) if isinstance(v, tuple) else v for k, v in J.items()}, p, f, r

def place_knight(t):
    fr = sc['frames'][min(575, int(round(t * FPS)))]; p = sample(KK, t); f = -1
    def at(tt, X, g, s_):
        J, r = fk(sample(KK, tt), f, s_); return X, g - lowest(J) - 0
    if t < 4.5: s_ = .6; J, r = fk(p, f, s_); ox, oy = WX, SILL - lowest(J)
    elif t < 4.92:
        u = (t - 4.5) / .42; s_ = lerp(.6, 1.0, ease(u)); J, r = fk(p, f, s_)
        x0, y0 = WX, SILL - lowest(fk(sample(KK, 4.5), f, .6)[0]); x1 = sx(5.4); y1 = FLOOR - lowest(fk(sample(KK, 4.92), f, 1.0)[0])
        ox = lerp(x0, x1, 1 - (1 - u) ** 3); oy = lerp(y0, y1, u * u) - 46 * math.sin(math.pi * u) * (1 - u * .5)
    else: s_ = 1.0; J, r = fk(p, f, s_); ox, oy = sx(fr['knight']['x']), FLOOR - lowest(J)
    return {k: (v[0] + ox, v[1] + oy) if isinstance(v, tuple) else v for k, v in J.items()}, p, f, r, s_

# ---------- the knight's shard skin: fixed in part space, so each shard keeps its identity and its normal ----------
SIL, GLD, RED, STEEL = np.array((196, 204, 216)), np.array((214, 172, 82)), np.array((190, 34, 38)), np.array((150, 160, 178))
PARTS = [  # name, joint a, joint b, width a, width b, along, across, palette
 ('thighR', 'hip', 'knR', 26, 22, 3, 2, [SIL, STEEL]), ('shinR', 'knR', 'ftR', 22, 18, 3, 2, [SIL, GLD]),
 ('uarmL', 'sh', 'elL', 20, 18, 2, 2, [SIL, STEEL]), ('farmL', 'elL', 'haL', 18, 16, 2, 2, [SIL, GLD]),
 ('skirt', 'hip', 'hip+', 50, 58, 2, 4, [GLD, SIL, RED]), ('torso', 'hip', 'chest', 50, 58, 4, 4, [SIL, GLD, SIL, RED, SIL]),
 ('thighL', 'hip', 'knL', 26, 22, 3, 2, [SIL, STEEL]), ('shinL', 'knL', 'ftL', 22, 18, 3, 2, [SIL, GLD]),
 ('helm', 'head+', 'head-', 34, 30, 3, 3, [SIL, SIL, GLD]), ('plume', 'head-', 'plume', 12, 4, 3, 1, [RED]),
 ('uarmR', 'sh', 'elR', 20, 18, 2, 2, [SIL, STEEL]), ('farmR', 'elR', 'haR', 18, 16, 2, 2, [SIL, GLD]),
]
SKIN = []
for name, a, b, w0, w1, na, nc, pal in PARTS:
    grid = np.zeros((na + 1, nc + 1, 2))
    for i in range(na + 1):
        for j in range(nc + 1):
            ju = .3 / na if 0 < i < na else 0; jv = .3 / nc if 0 < j < nc else 0
            grid[i, j] = (i / na + rng.uniform(-ju, ju), j / nc - .5 + rng.uniform(-jv, jv))
    for i in range(na):
        for j in range(nc):
            q = [grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]]
            tris = [(q[0], q[1], q[2]), (q[0], q[2], q[3])] if rng.uniform() < .5 else [(q[0], q[1], q[3]), (q[1], q[2], q[3])]
            for tri in tris:
                SKIN.append(dict(part=name, a=a, b=b, w0=w0, w1=w1, uv=tri, col=pal[(i + j) % len(pal)] * rng.uniform(.9, 1.08), tilt=rng.uniform(-.75, .75, 2), lab=2))
BLADE = [dict(uv=((u0, -.5), (u1, -.5), (u1, .5)), tilt=rng.uniform(-.6, .6, 2)) for u0, u1 in zip(np.linspace(0, 1, 7)[:-1], np.linspace(0, 1, 7)[1:])] + \
        [dict(uv=((u0, -.5), (u1, .5), (u0, .5)), tilt=rng.uniform(-.6, .6, 2)) for u0, u1 in zip(np.linspace(0, 1, 7)[:-1], np.linspace(0, 1, 7)[1:])]
LIGHT = np.array([-.45, -.7, .55]); LIGHT /= np.linalg.norm(LIGHT); HALF = LIGHT + np.array([0, 0, 1.0]); HALF /= np.linalg.norm(HALF)

def shade(col, tilt, ang, boost=1.0, base=.32):
    c, s = math.cos(ang), math.sin(ang); tx, ty = tilt[0] * c - tilt[1] * s, tilt[0] * s + tilt[1] * c
    n = np.array([tx, ty, 1.0]); n /= np.linalg.norm(n)
    dif = max(0, n @ LIGHT); spec = max(0, n @ HALF) ** 36
    c = col * (base + .8 * dif) * boost; m = c.max()
    return (c * 255 / m if m > 255 else c), 255 * 1.4 * spec   # brighter light keeps the glass's hue: scale, never clip

def knight_shards(t):
    J, p, f, r, s_ = place_knight(t)
    hipp, ch, hd = np.array(J['hip']), np.array(J['chest']), np.array(J['head'])
    up = (ch - hipp) / max(1e-6, np.linalg.norm(ch - hipp))
    J['hip+'] = tuple(hipp - up * 30 * s_); J['head+'] = tuple(hd + up * 20 * s_); J['head-'] = tuple(hd - up * 18 * s_)
    J['plume'] = tuple(hd - up * 40 * s_ + np.array([-f * 26 * s_, 0]))
    out = []
    for k, sh in enumerate(SKIN):
        A, B = np.array(J[sh['a']]), np.array(J[sh['b']]); v = B - A; Ln = np.linalg.norm(v) or 1; nrm = np.array([-v[1], v[0]]) / Ln
        pts = [tuple(A + v * u + nrm * (lerp(sh['w0'], sh['w1'], u) * s_) * w) for u, w in sh['uv']]
        out.append((k, pts, sh['col'], sh['tilt'], math.atan2(v[1], v[0]), 2))
    # the visor: label 6, on the face side by p['face']
    cx = hd[0] + f * p['face'] * 15 * s_; cy = hd[1] - 2 * s_; vw = lerp(13, 8, p['face'])
    out.append((len(SKIN), [(cx - vw * s_, cy - 4 * s_), (cx + vw * s_, cy - 4 * s_), (cx + vw * s_, cy + 5 * s_), (cx - vw * s_, cy + 5 * s_)], np.array((24, 24, 36)), np.zeros(2), 0, 6))
    if p['sw'] > .03:
        hand = np.array(J['haR']); ang = math.radians(J['faR'] + p['b']); dvec = np.array([f * math.sin(ang), math.cos(ang)])
        tip = hand + dvec * 96 * s_ * min(1, p['sw']); nrm = np.array([-dvec[1], dvec[0]])
        for k, bl in enumerate(BLADE):
            pts = [tuple(hand + (tip - hand) * u + nrm * 9 * s_ * (1 - .7 * u) * w) for u, w in bl['uv']]
            out.append((1000 + k, pts, RED * 1.15, bl['tilt'], math.atan2(dvec[1], dvec[0]), 4))
    return out, J, p

# the pieces: which shard each shot frees (shoulder first, then from the outside in)
def plan():
    sh, J, p = knight_shards(9.5); shoulder = np.array(J['sh']); hip = np.array(J['hip'])
    ids = [s[0] for s in sh if s[5] == 2]; cen = {s[0]: np.mean(s[1], 0) for s in sh}
    first = sorted(ids, key=lambda i: np.linalg.norm(cen[i] - shoulder)); n = len(ids); k1 = int(round(.12 * n))
    rest = sorted(first[k1:], key=lambda i: -np.linalg.norm(cen[i] - hip) + rng.uniform(0, 30))
    rel = releases(sc, n, first[:k1] + rest); fb = {}
    for shot, tt, paint, pid in rel:
        for i in pid: fb[i] = (shot, tt, paint)
    for k in list(range(1000, 1000 + len(BLADE))) + [len(SKIN)]: fb[k] = (5, sc['pieces'][5]['t'], sc['pieces'][5]['paint'])  # the sword and visor go with the last shot
    return fb
FREED = plan(); FLY = {}
for shot_t in sorted(set(v[1] for v in FREED.values())):
    sh, J, p = knight_shards(shot_t)
    for k, pts, col, tilt, ang, lab in sh:
        if k in FREED and FREED[k][1] == shot_t:
            shot = FREED[k][0]; c = np.mean(pts, 0); sp = 1.8 if shot == 5 else 1.0
            FLY[k] = dict(t0=shot_t, shot=shot, pts=np.array(pts) - c, c=c, v=np.array([rng.uniform(-60, 160) * sp, rng.uniform(-220, -60) * sp]), spin=rng.uniform(-9, 9),
                          tilt=tilt, land=FLOOR + 4 + rng.uniform(0, 1) ** 1.4 * (56 if shot == 5 else 34), col=np.array(hexrgb(FREED[k][2]), float))
def piece_at(k, t):
    P_ = FLY[k]; dt = t - P_['t0']; g = 900.0
    # flight until it reaches its landing line, then it lies there flattened
    a = .5 * g; b = P_['v'][1]; c = P_['c'][1] - P_['land']; tl = (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)
    tt = min(dt, tl); pos = P_['c'] + P_['v'] * tt + np.array([0, .5 * g * tt * tt]); ang = P_['spin'] * tt
    flat = 1.0 if dt < tl else .42; cs, sn = math.cos(ang), math.sin(ang)
    pts = [(pos[0] + x * cs - y * sn, pos[1] + (x * sn + y * cs) * flat) for x, y in P_['pts'] * 1.15]
    return pts, ang, dt >= tl

# ---------- the plate: a painted backdrop of the sunken cathedral ----------
def plate():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); img = np.zeros((H, W, 3), np.float32)
    img[:] = np.array([38, 26, 34]) + (yy / H)[..., None] * np.array([20, 14, 10])
    for k, cx in enumerate((120, 300, 480, 660)):   # far windows, soft
        m = (np.abs(xx - cx) < 34) & (yy > 70) & (yy < 300) & ((yy > 104) | ((xx - cx) ** 2 + (yy - 104) ** 2 < 34 ** 2))
        pal = np.array([(40, 60, 150), (150, 30, 40), (200, 150, 60), (30, 90, 70), (60, 40, 110)], np.float32)
        cell = ((xx // 11).astype(int) * 7 + (yy // 13).astype(int) * 3 + k) % 5
        lead_ = ((xx % 11) < 1.5) | ((yy % 13) < 1.5)
        img[m] = pal[cell[m]] * np.where(lead_[m], .25, 1.0)[:, None]
    for cx in (210, 390, 570):   # columns
        m = np.abs(xx - cx) < 22; sh_ = np.clip(1 - np.abs(xx - cx + 8) / 22, 0, 1); img[m & (yy < FLOOR)] = (np.array([70, 52, 44]) * (.5 + .7 * sh_[..., None]))[m & (yy < FLOOR)]
    img[yy < 44] = np.array([210, 140, 70]) * (.8 + .2 * np.sin(xx[yy < 44] / 40))[..., None]      # the dune overhead
    wall = (xx > 740 + (yy - 40) * .06) & (yy < FLOOR)
    strat = .82 + .1 * np.sin(yy / 6 + np.sin(xx / 50) * .8) + .06 * np.sin(yy / 23); img[wall] = (np.array([176, 98, 58]) * strat[..., None])[wall]
    win = (xx > WL) & (xx < WR) & (yy < SILL) & ((yy > WT + 28) | ((xx - WX) ** 2 + (yy - WT - 28) ** 2 < 28 ** 2))
    img[win] = np.array([30, 50, 120]) + 30 * np.sin(yy[win] / 7)[..., None]
    fl = yy >= FLOOR   # the mirror floor in perspective
    depth = (yy - FLOOR + 1) / (H - FLOOR); img[fl] = (np.array([22, 22, 34]) + depth[fl][:, None] * np.array([30, 30, 44]))
    vx = 480; gl = np.zeros((H, W), bool)
    for k in range(-14, 15): gl |= fl & (np.abs((xx - vx) - k * 70 * (yy - FLOOR + 40) / 110) < .8 + depth * .8)
    for k in range(1, 6): gl |= fl & (np.abs(yy - (FLOOR + k * k * 2.8)) < .7)
    img[gl] = img[gl] * .5 + np.array([70, 70, 90]) * .5
    steps = (xx < sx(-6.95)) & (yy > FLOOR - 112) | (xx < sx(-6.4)) & (yy > FLOOR - 56)
    sm = steps & (yy < FLOOR); nose = (np.abs(yy - (FLOOR - 112)) < 3) | (np.abs(yy - (FLOOR - 56)) < 3)
    img[sm] = np.array([150, 124, 98]) * np.where(nose[sm], 1.5, .9 + .08 * np.sin(yy[sm] / 3))[:, None]
    img = ndimage.gaussian_filter(img, (1.6, 1.6, 0)) * (1 + .05 * ndimage.gaussian_filter(rng.normal(0, 1, (H, W)), 1.2))[..., None]
    return np.clip(img, 0, 255), win
PLATE, WINMASK = plate()
def plate_blur(r):
    key = round(r * 2) / 2
    if key not in plate_blur.c: plate_blur.c[key] = ndimage.gaussian_filter(PLATE, (key, key, 0)) if key > 0 else PLATE
    return plate_blur.c[key]
plate_blur.c = {}

# ---------- Uncle Mesa, painted: a Black man in his sixties, long white beard, round glasses with gold lenses, cream wide-brimmed
# hat, white guayabera-style shirt with the MESA CHIP badge, khaki trousers, dark boots, the six-shooter of paint ----------
CS = dict(skin=(128, 84, 58), beard=(252, 252, 250), hat=(232, 216, 178), shirt=(232, 226, 210), khaki=(176, 148, 102), boot=(46, 32, 26), gun=(40, 190, 200), gold=(232, 186, 70))
def mesa_draw(dr, dm, t, lab=True):
    J, p, f, r = place_mesa(t)
    def cap(a, b, w, c, l=1):
        dr.line([a, b], CS[c], int(w)); [dr.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], CS[c]) for q in (a, b)]
        if lab: dm.line([a, b], l, int(w)); [dm.ellipse([q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2], l) for q in (a, b)]
    cap(J['sh'], J['elL'], 15, 'shirt'); cap(J['elL'], J['haL'], 13, 'shirt'); cap(J['haL'], J['haL'], 11, 'skin')
    for s in 'LR':
        cap(J['hip'], J['kn' + s], 23, 'khaki'); cap(J['kn' + s], J['ft' + s], 19, 'khaki')
        ft = J['ft' + s]; cs, sn = math.cos(r), math.sin(r); toe = (ft[0] + f * 18 * cs, ft[1] + f * 18 * sn); cap(ft, toe, 14, 'boot')
    hip, ch = J['hip'], J['chest']; v = np.array(ch) - np.array(hip); n_ = np.array([-v[1], v[0]]) / (np.linalg.norm(v) or 1)
    torso = [tuple(np.array(hip) + n_ * 19), tuple(np.array(hip) - n_ * 19), tuple(np.array(ch) - n_ * 22), tuple(np.array(ch) + n_ * 22)]
    dr.polygon(torso, CS['shirt']); dm.polygon(torso, 1) if lab else None
    for k in (-.45, .45): a_ = np.array(hip) + n_ * 19 * k; b_ = np.array(ch) + n_ * 22 * k; dr.line([tuple(a_), tuple(b_)], (196, 194, 186), 2)   # guayabera pleats
    for k in (-.55, .45): pk = np.array(hip) + v * .22 + n_ * 19 * k; dr.rectangle([pk[0] - 6, pk[1] - 5, pk[0] + 6, pk[1] + 5], outline=(196, 194, 186), width=2)
    badge = np.array(ch) - v * .22 + n_ * f * -10; dr.rectangle([badge[0] - 5, badge[1] - 4, badge[0] + 5, badge[1] + 4], (236, 196, 40))
    hd = J['head']; cap(ch, hd, 14, 'skin'); dr.ellipse([hd[0] - 17, hd[1] - 19, hd[0] + 17, hd[1] + 17], CS['skin']); dm.ellipse([hd[0] - 17, hd[1] - 19, hd[0] + 17, hd[1] + 17], 1) if lab else None
    cs, sn = math.cos(r), math.sin(r); R = lambda x, y: (hd[0] + x * cs - y * sn, hd[1] + x * sn + y * cs)
    beard = [R(-9 * f, 7), R(16 * f, 7), R(13 * f, 44), R(3 * f, 58), R(-8 * f, 28)]; dr.polygon(beard, CS['beard'], outline=(120, 116, 110)); dr.line(beard[1:4], (150, 146, 140), 2); dm.polygon(beard, 1) if lab else None
    for gx in (1, 11): gl_ = R(gx * f, -4); dr.ellipse([gl_[0] - 5, gl_[1] - 5, gl_[0] + 5, gl_[1] + 5], CS['gold'], outline=(90, 70, 30), width=2)
    brim = [R(-36, -17), R(36, -17), R(32, -12), R(-32, -12)]; crown = [R(-14, -17), R(14, -17), R(12, -36), R(-12, -36)]
    if 12.25 <= t < 14.45:   # knocked off at the fall; it lies on the floor; his hand takes it up as he rises
        fl_x = sx(-4.3) - 110; u = 0; u0 = ease((t - 12.25) / .2)
        hx = lerp(lerp(hd[0], fl_x, u0), hd[0], u); hy = lerp(lerp(hd[1] - 13, FLOOR - 1, u0), hd[1] - 17, u)
        if t >= 13.85:   # he takes it from the floor on the way up and puts it on
            v_ = ease((t - 13.85) / .55); hx = lerp(fl_x, hd[0], v_); hy = lerp(FLOOR - 1, hd[1] - 17, v_) - 30 * math.sin(math.pi * v_)
        brim = [(hx - 36, hy), (hx + 36, hy), (hx + 32, hy - 6), (hx - 32, hy - 6)]; crown = [(hx - 14, hy - 6), (hx + 14, hy - 6), (hx + 12, hy - 21), (hx - 12, hy - 21)]
    for q in (brim, crown): dr.polygon(q, CS['hat']); dm.polygon(q, 1) if lab else None
    cap(J['sh'], J['elR'], 15, 'shirt'); cap(J['elR'], J['haR'], 13, 'shirt'); cap(J['haR'], J['haR'], 11, 'skin')
    ha = np.array(J['haR']); a = math.radians(J['faR']) + r; dv = np.array([f * math.sin(a), math.cos(a)]) if r == 0 else np.array([f * math.sin(math.radians(J['faR'])), math.cos(math.radians(J['faR']))])
    if r != 0: dv = np.array([dv[0] * cs - dv[1] * sn, dv[0] * sn + dv[1] * cs])
    nv = np.array([-dv[1], dv[0]])
    gun = [tuple(ha - dv * 6 + nv * 7), tuple(ha + dv * 30 + nv * 7), tuple(ha + dv * 30 - nv * 2), tuple(ha + dv * 6 - nv * 4), tuple(ha + dv * 2 - nv * 14), tuple(ha - dv * 6 - nv * 12)]
    dr.polygon(gun, CS['gun']); dm.polygon(gun, 5) if lab else None
    return J

def draw_frame_layers(t, lab=False):
    M = Image.new('RGBA', (W, H), (0, 0, 0, 0)); K = Image.new('RGBA', (W, H), (0, 0, 0, 0)); Sp = Image.new('L', (W, H), 0); LB = Image.new('L', (W, H), 0)
    dM, dK, dS, dL = ImageDraw.Draw(M), ImageDraw.Draw(K), ImageDraw.Draw(Sp), ImageDraw.Draw(LB)
    if lab: dL.bitmap((0, 0), Image.fromarray((WINMASK * 255).astype(np.uint8)), fill=3)
    fr = sc['frames'][min(575, int(round(t * FPS)))]; lx = sx(fr['light_x'])
    # fallen and flying pieces (behind the figures when on the floor)
    for k in sorted(FLY, key=lambda k: -FLY[k]['shot']):   # the last shot's pieces lie under the earlier ones
        if t < FLY[k]['t0']: continue
        pts, ang, landed = piece_at(k, t); cx = np.mean([q[0] for q in pts])
        boost = 1.15 + 1.2 * math.exp(-((cx - lx - (pts[0][1] - 50) * .18) / 50) ** 2) + (1.3 * math.exp(-((cx - coda_x(t)) / 70) ** 2) * ease((t - 20.5) / .8) if t > 20.5 else 0)
        col, sp = shade(FLY[k]['col'], FLY[k]['tilt'], ang * 1.7, boost, base=.6)   # paint is matte: it holds its colour in shadow
        dK.polygon(pts, tuple(int(c) for c in col) + (255,)); dS.polygon(pts, int(min(255, sp * boost * (.35 if landed else 1))))
        if lab: dL.polygon(pts, 10 + FLY[k]['shot'])
    mesa_draw(dM, dL if lab else ImageDraw.Draw(Image.new('L', (8, 8))), t, lab)
    if t < 19.5 + 1e-6:
        sh, J, p = knight_shards(t)
        for k, pts, col, tilt, ang, lb in sh:
            if k in FREED and t >= FREED[k][1]: continue
            c, sp = shade(col, tilt, ang)
            dK.polygon(pts, tuple(int(v) for v in c) + (255,), outline=(26, 26, 34, 255)); dS.polygon(pts, int(min(255, sp)))
            if lab: dL.polygon(pts, lb)
    return M, K, Sp, LB

def coda_x(t): return sx(lerp(-6.0, 0.5, ease((t - 20.5) / 3.5)))
def focus(t):
    """the rack focus: on Uncle Mesa coming down; at the head turn it racks to the knight in the far window; when it leaps, back"""
    f = 3.0
    if t >= 2.2: f = lerp(3.0, 8.0, ease((t - 2.2) / .55))   # sharp on the knight before it turns
    if t >= 4.5: f = lerp(8.0, 3.0, ease((t - 4.5) / .45))
    return f
def blur_rgba(im, r):
    a = np.asarray(im).astype(np.float32)
    if r < .35: return a
    pm = a[..., :3] * (a[..., 3:] / 255); pm = ndimage.gaussian_filter(pm, (r, r, 0)); al = ndimage.gaussian_filter(a[..., 3], r)
    return np.concatenate([pm / np.maximum(1e-3, al[..., None] / 255), al[..., None]], -1)

def frame(f):
    t = f / FPS; acc = np.zeros((H, W, 3), np.float32); fd = focus(t)
    kd = 8.0 if t < 4.5 else lerp(8.0, 3.0, ease((t - 4.5) / .42)) if t < 4.92 else 3.0
    for j in range(6):   # six jittered sub-frames across a 180 degree shutter
        ts = t + ((j + rng.uniform(0, 1)) / 6 - .5) * (.5 / FPS)
        M, K, Sp, _ = draw_frame_layers(max(0, ts))
        m = blur_rgba(M, max(.7, .9 * abs(3.0 - fd)))
        al = m[..., 3] > 8
        if al.any():
            ys_, xs_ = np.nonzero(al); x0_, x1_, y0_, y1_ = xs_.min(), xs_.max() + 1, ys_.min(), ys_.max() + 1
            gx = np.linspace(1.12, .72, x1_ - x0_)[None, :] * np.linspace(1.05, .85, y1_ - y0_)[:, None]
            m[y0_:y1_, x0_:x1_, :3] *= gx[..., None]; m[..., :3] += rng.normal(0, 5, (H, W, 1)) * al[..., None]
        k = blur_rgba(K, .9 * abs(kd - fd)); base = plate_blur(min(4, .5 + .55 * abs(10 - fd))).copy()
        # reflections in the mirror floor: the figures flipped about the floor line, dim, a little soft
        rows = np.arange(int(FLOOR), H); src = (2 * int(FLOOR) - rows).clip(0, H - 1)
        for lay in (m, k):
            rf = lay[src]; al = rf[..., 3:] / 255 * .3; base[int(FLOOR):] = base[int(FLOOR):] * (1 - al) + rf[..., :3] * al
        for lay in (m, k): al = lay[..., 3:] / 255; base = base * (1 - al) + lay[..., :3] * al
        sp = ndimage.gaussian_filter(np.asarray(Sp).astype(np.float32), .8 + .9 * abs(kd - fd)); base += (sp + .6 * ndimage.gaussian_filter(sp, 5))[..., None] * np.array([1, .97, .9])
        acc += base
    img = acc / 6
    fr = sc['frames'][f]; lx = sx(fr['light_x']); yy, xx = np.mgrid[0:H, 0:W]
    shaft = np.exp(-((xx - lx - (yy - 50) * .18) / 46) ** 2) * (yy > 44) * (.25 + .3 * (yy / H))
    img = img * (1 + shaft[..., None] * np.array([1.0, .9, .65]) * (.6 + .4 * ease(t / 4))) + shaft[..., None] * 18   # light multiplies what it falls on, so paint keeps its hue
    if t > 20.5: img = img * (1 + (np.exp(-((xx - coda_x(t)) / 70) ** 2) * (yy > FLOOR - 10) * ease((t - 20.5) / .8))[..., None] * .7)
    img = img * (.62 + .38 * ease(t / 3.5)) * (1 - .35 * (((xx - 480) / 540) ** 2 + ((yy - 270) / 400) ** 2))[..., None]
    img += rng.normal(0, 3.5, (H, W, 1))
    _, _, _, LB = draw_frame_layers(t, lab=True)
    return np.clip(img, 0, 255).astype(np.uint8), np.asarray(LB)

def sound():
    buf = tl(24.0); r = np.random.default_rng(3); n = len(buf); tt = np.arange(n) / SR
    for f0, g in ((55, .5), (82.4, .3), (110, .25)):   # low strings, a slow swell
        saw = sum(np.sin(2 * np.pi * f0 * k * tt) / k for k in range(1, 9)); buf += g * .05 * saw * (.4 + .6 * np.clip(tt / 10, 0, 1)) * np.clip((23.5 - tt) / 1.5, 0, 1)
    for t0, _, nm in MK:
        if nm.startswith('walk c1'): add(buf, t0, noise(.08, r, .04, lp=900), .35)          # boot heels
    for t0, _, nm in KK:
        if nm.startswith('walk kc1') or nm.startswith('lands'): add(buf, t0, noise(.12, r, .05, lp=3000), .5); add(buf, t0, chime(260 + r.uniform(0, 80), .5), .15)  # glass and steel feet
    add(buf, 3.05, chime(880, 1.2), .2); add(buf, 4.5, noise(.3, r, .15), .3); add(buf, 6.0, chime(1760, 2.0), .35); add(buf, 6.05, chime(2637, 1.4), .2)   # the draw rings
    for i, p in enumerate(sc['pieces']):
        add(buf, p['t'], noise(.05, r, .02, lp=1500), 1.0)
        for k in range(6 if i < 5 else 26): add(buf, p['t'] + .05 + r.uniform(0, .5 if i < 5 else 1.4), chime(900 + r.uniform(0, 2400), .9), .12)
    add(buf, 11.95, noise(.25, r, .2, lp=2000) * np.linspace(0, 1, int(.25 * SR)), .5); add(buf, 12.2, tone(48, 1.2, .002, .5, harm=(1., .5, .3)), 1.2); add(buf, 12.2, noise(.2, r, .1, lp=400), .9)
    write_wav(os.path.join(HERE, 'sound.wav'), buf)

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    sound(); meter = Meter(sc); film = Film(os.path.join(OUT, 'film.mp4')); still = set(int(round(s * FPS)) for s in STILL_T)
    for f in range(len(sc['frames'])):
        rgb, lab = frame(f); film.put(rgb); meter.frame(f, lab[::2, ::2], rgb)
        if f in still: Image.fromarray(rgb).save(os.path.join(OUT, 'stills', f'still_{f / FPS:04.1f}s.jpg'), quality=90)
        if f % 48 == 0: print('frame', f, flush=True)
    film.close(os.path.join(HERE, 'sound.wav'))
    rep = meter.report(); json.dump(rep, open(os.path.join(OUT, 'invariants.json'), 'w'), indent=1)
    json.dump(dict(swarm='SCION-LUCASFILM-1985', shards=len(SKIN), blade_shards=len(BLADE), subframes=4, shutter_deg=180, frames=meter.rows), open(os.path.join(OUT, 'trace.json'), 'w'))
    contact(os.path.join(OUT, 'stills'), os.path.join(OUT, 'stills', 'contact.jpg'))
    print({k: (v['ok'] if isinstance(v, dict) else v) for k, v in rep.items()})
