#!/usr/bin/env python3
"""SCION-MOEBIUS-OTOMO · MESA CHIP, handmade. Ligne claire: one black contour of constant weight, flat fills, no shading but cast
shadow, a vast empty floor and small figures. Speed is drawn as light that stays behind (the sword, the leap, every paint shot).
The knight does not just break: where paint takes it, its outline blooms like coral and then splits. Drawn at 2x and reduced, so
the line holds. Run: python3 render.py"""
import sys, os, json, math, numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools'))
from common import *
sc = score(); rng = np.random.default_rng(1988); K2 = 2; LW = 2 * K2   # constant line weight: 2 px at film size
FLOOR, SILL, HOR = 452.0, 330.0, 318.0
def sx(x): return 505 + 60 * x
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def rot(p, c, a): s, k = math.sin(a), math.cos(a); x, y = p[0] - c[0], p[1] - c[1]; return (c[0] + k * x - s * y, c[1] + s * x + k * y)
WX = sx(6.2); WL, WR = WX - 32, WX + 32
INK = (22, 18, 20)
COL = dict(ceiling=(214, 150, 84), ceiling2=(190, 122, 66), sky=(246, 226, 196), light=(255, 246, 222), far=(226, 176, 136), wall=(200, 112, 70), wall2=(170, 90, 58),
           floor=(236, 222, 206), floor2=(222, 206, 192), shadow=(150, 128, 150), win=(78, 120, 190), step=(206, 172, 132),
           skin=(110, 70, 48), beard=(250, 250, 246), hat=(238, 222, 184), shirt=(252, 252, 248), khaki=(196, 168, 116), boot=(60, 42, 34), gold=(240, 196, 70), gun=(52, 204, 214),
           silver=(214, 220, 230), steel=(176, 186, 204), kgold=(232, 186, 86), red=(212, 44, 44), visor=(40, 40, 60), pleat=(168, 166, 160), badge=(246, 210, 40), eye=(30, 22, 18))

def poly(d, pts, fill, outline=True):
    q = [(x * K2, y * K2) for x, y in pts]; d.polygon(q, fill)
    if outline: d.line(q + [q[0]], INK, LW, joint='curve')
def lab_poly(m, pts, v): ImageDraw.Draw(m).polygon(pts, v)

# ---------- the place: flat bands, the dune overhead with its openings, the columns of light, the canyon wall ----------
def place(d, t, fr):
    poly(d, [(0, 0), (W, 0), (W, HOR), (0, HOR)], COL['sky'], False)
    poly(d, [(0, 0), (W, 0), (W, 70)] + [(x, 70 + 26 * math.sin(x / 110) + 14 * math.sin(x / 37)) for x in range(W, -1, -40)], COL['ceiling'])
    for cx_, r in ((180, 26), (430, 34), (640, 22)):   # openings in the dune
        poly(d, [(cx_ + r * math.cos(a), 60 + r * .35 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24)], COL['light'])
    lx = sx(fr['light_x'])
    for cx_, w, dx in ((180, 22, 40), (430, 30, 50), (640, 18, 30), (lx, 44, 70)):   # columns of light, flat, slanting
        poly(d, [(cx_ - w, 62), (cx_ + w, 62), (cx_ + w + dx, FLOOR + 40), (cx_ - w + dx, FLOOR + 40)], COL['light'], False)
    poly(d, [(0, HOR), (120, HOR - 30), (260, HOR - 18), (420, HOR - 40), (560, HOR - 22), (700, HOR - 34), (760, HOR), (0, HOR)], COL['far'])   # far ridges
    poly(d, [(0, HOR), (W, HOR), (W, H), (0, H)], COL['floor'], False)
    for k in range(5): y = HOR + 12 + k * k * 8; poly(d, [(0, y), (W, y), (W, y + 2 + k), (0, y + 2 + k)], COL['floor2'], False)   # bands of the glass floor
    poly(d, [(lx - 44 + 75, FLOOR + 40), (lx + 44 + 75, FLOOR + 40), (lx + 64 + 86, H), (lx - 64 + 86, H)], COL['light'], False)  # where the light lands
    wall = [(760, 60), (W + 4, 52), (W + 4, FLOOR + 4), (742, FLOOR + 4), (748, 300), (738, 160)]
    poly(d, wall, COL['wall'])
    for y in (120, 190, 260, 360, 420): poly(d, [(748, y), (W, y - 6), (W, y + 3), (748, y + 8)], COL['wall2'], False)
    win = [(WL, SILL), (WL, 96)] + [(WX - 32 * math.cos(a), 96 - 32 * math.sin(a)) for a in np.linspace(0, math.pi, 12)] + [(WR, SILL)]
    poly(d, win, COL['win'])
    poly(d, [(WL - 6, SILL), (WR + 6, SILL), (WR + 6, SILL + 8), (WL - 6, SILL + 8)], COL['wall2'])
    poly(d, [(-4, FLOOR - 60), (sx(-6.9), FLOOR - 60), (sx(-6.9), FLOOR - 30), (sx(-6.55), FLOOR - 30), (sx(-6.55), FLOOR), (-4, FLOOR)], COL['step'])
    return win

# ---------- the figures: a pose sheet of strong poses and smooth in-betweens ----------
def limb(a, b, w0, w1):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
    return [(a[0] + nx * w0, a[1] + ny * w0), (b[0] + nx * w1, b[1] + ny * w1), (b[0] - nx * w1, b[1] - ny * w1), (a[0] - nx * w0, a[1] - ny * w0)]
def circle(c, r, n=20): return [(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, n, endpoint=False)]

def mesa(t):
    fr = sc['frames'][min(575, int(round(t * FPS)))]; st = fr['mesa']['state']; x = fr['mesa']['x']
    f = -1 if st == 'walk' else 1; walking = st in ('descend', 'walk') or 14.0 < t < 15.0; ph = t * 2 * math.pi * 1.5
    sw = 0.42 * math.sin(ph) if walking else 0
    aim = ease((t - 6.5) / .16) if t >= 6.5 else 0
    if 12.2 <= t < 14.1 or t >= 20.7: aim = 0 if t < 20.7 else 1 - ease((t - 20.7) / .3)
    sit = ease((t - 21.7) / .5) if t >= 21.7 else 0
    c = ease((t - 12.2) / .12) * (1 - ease((t - 13.95) / .18)) if 12.2 <= t < 14.15 else 0   # the knees give
    gy = FLOOR - 60 + 30 * ease((x + 7.0) / .25) + 30 * ease((x + 6.7) / .25) if sit == 0 else FLOOR
    parts = []; hip = (-12 * f * sit - 6 * f * c, lerp(-84 + 20 * c, -30, sit))
    for s in (sw, -sw):
        if sit: kn = (hip[0] + 30 * f, hip[1] - 6); ft = (hip[0] + 38 * f, 0)
        else: kn = (hip[0] + 44 * math.sin(s) * f + 18 * f * c, hip[1] + 40 * math.cos(s)); ft = (s * 30 * f, 0)
        parts += [(limb(hip, kn, 8, 7), 'khaki', 1), (limb(kn, ft, 7, 6), 'khaki', 1), ([(ft[0] - 6, ft[1] - 8), (ft[0] + 14 * f, ft[1] - 7), (ft[0] + 15 * f, ft[1]), (ft[0] - 7, ft[1])], 'boot', 1)]
    sh = (hip[0] + 3 * f, hip[1] - 60)
    parts.append(([(hip[0] - 15, hip[1] + 4), (hip[0] + 15, hip[1] + 4), (sh[0] + 17, sh[1]), (sh[0] - 17, sh[1])], 'shirt', 1))
    for k in (-7, 7): parts.append(([(hip[0] + k - .8, hip[1] + 2), (hip[0] + k + .8, hip[1] + 2), (sh[0] + k * 1.1 + .8, sh[1] + 6), (sh[0] + k * 1.1 - .8, sh[1] + 6)], 'pleat', 1))   # guayabera pleats
    for k in (-1, 1): parts.append(([(hip[0] + k * 10 - 5, hip[1] - 22), (hip[0] + k * 10 + 5, hip[1] - 22), (hip[0] + k * 10 + 5, hip[1] - 13), (hip[0] + k * 10 - 5, hip[1] - 13)], 'shirt', 1))   # lower pockets
    parts.append(([(sh[0] - 14 * f, sh[1] + 10), (sh[0] - 3 * f, sh[1] + 10), (sh[0] - 3 * f, sh[1] + 20), (sh[0] - 14 * f, sh[1] + 20)], 'badge', 1))   # the badge on the chest pocket, clear of the beard
    parts.insert(0, (limb((sh[0] - 5 * f, sh[1] + 4), (sh[0] - 9 * f - 8 * sw * f, sh[1] + 54), 6, 5), 'shirt', 1))
    hd = (sh[0] + 4 * f, sh[1] - 17)
    parts.append((circle(hd, 12), 'skin', 1))
    parts.append(([(hd[0] + 12 * f, hd[1] - 1), (hd[0] + 15 * f, hd[1] + 2), (hd[0] + 11 * f, hd[1] + 5)], 'skin', 1))   # the nose, in profile
    parts.append(([(hd[0] - 9 * f, hd[1] + 2), (hd[0] + 12 * f, hd[1] + 5), (hd[0] + 9 * f, hd[1] + 22), (hd[0] + 4 * f, hd[1] + 40), (hd[0] + 1 * f, hd[1] + 46), (hd[0] - 3 * f, hd[1] + 30), (hd[0] - 8 * f, hd[1] + 14)], 'beard', 1))   # long, tapering
    parts.append((circle((hd[0] + 7 * f, hd[1] - 2), 5, 14), 'gold', 1)); parts.append((circle((hd[0] + 7 * f, hd[1] - 2), 2.2, 10), 'eye', 1))
    parts.append(([(hd[0] - 28, hd[1] - 9), (hd[0] + 28, hd[1] - 9), (hd[0] + 25, hd[1] - 4), (hd[0] - 25, hd[1] - 4)], 'hat', 1))
    parts.append(([(hd[0] - 12, hd[1] - 9), (hd[0] + 12, hd[1] - 9), (hd[0] + 10, hd[1] - 27), (hd[0] - 10, hd[1] - 27)], 'hat', 1))
    a0 = (sh[0] + 5 * f, sh[1] + 4); lo = (sh[0] + 11 * f, sh[1] + 52); hi = (sh[0] + 48 * f, sh[1] + 2)
    hand = (lerp(lo[0], hi[0], aim), lerp(lo[1], hi[1], aim)); parts.append((limb(a0, hand, 6, 5), 'shirt', 1))
    dv = np.array([hand[0] - a0[0], hand[1] - a0[1]], float); dv /= np.linalg.norm(dv); nv = np.array([-dv[1], dv[0]]) * f; ha = np.array(hand)
    gun = [tuple(ha - dv * 4 - nv * 6), tuple(ha + dv * 26 - nv * 6), tuple(ha + dv * 26 + nv * 1), tuple(ha + dv * 6 + nv * 3), tuple(ha + dv * 2 + nv * 12), tuple(ha - dv * 6 + nv * 11)]
    parts.append((gun, 'gun', 5))
    down = ease((t - 12.27) / .2) * (1 - ease((t - 13.7) / .26)) if 12.2 <= t < 14.15 else 0
    X = sx(x)
    def P(p):
        if down: p = rot(p, (0, -78), -f * down * math.pi / 2 * .97); p = (p[0], p[1] + 66 * down)
        return (X + p[0], gy + p[1])
    muzzle = P(tuple(ha + dv * 28))
    return [([P(p) for p in q], c, l) for q, c, l in parts], muzzle, (X, gy)

KN = []   # the knight's glass panels, in body space
def panel_grid(part, na, nc, cols):
    for i in range(na):
        for j in range(nc): KN.append(dict(part=part, u=(i / na, (i + 1) / na), v=(j / nc - .5, (j + 1) / nc - .5), col=cols[(i * 2 + j) % len(cols)]))
for part, na, nc, cols in (('legL', 3, 2, ['silver', 'steel']), ('legR', 3, 2, ['silver', 'kgold']), ('torso', 4, 3, ['silver', 'kgold', 'red', 'silver']), ('head', 2, 2, ['silver', 'kgold']),
                           ('plume', 3, 1, ['red']), ('arm', 2, 1, ['silver']), ('arm2', 2, 1, ['steel'])): panel_grid(part, na, nc, cols)
WID = dict(legL=17, legR=17, torso=40, head=24, plume=9, arm=12, arm2=12)
def kjoints(t):
    fr = sc['frames'][min(575, int(round(t * FPS)))]; st = fr['knight']['state']
    X, Y = sx(fr['knight']['x']), FLOOR
    if t < 4.5: X, Y = WX, SILL
    elif t < 5.1: u = (t - 4.5) / .6; X = lerp(WX, sx(5.4), 1 - math.exp(-u * 6)); Y = lerp(SILL, FLOOR, ease(u * 1.5)) - 46 * math.sin(math.pi * min(1, u * 1.5))
    walking = st in ('advance', 'advance_broken'); sw = (11 if st == 'advance' else 20) * math.sin(t * 2 * math.pi * (1.3 if st == 'advance' else .9)) if walking else 0
    turn = ease((t - 3.0) / .1) if t >= 3.0 else 0
    J = dict(hip=(X, Y - 86), ftL=(X + sw + 9, Y), ftR=(X - sw - 9, Y), sh=(X - 3, Y - 146), neck=(X - 4, Y - 150), top=(X - 5 - 3 * turn, Y - 180), plume=(X + 16, Y - 204))
    raise_ = ease((t - 11.55) / .45) if 11.55 <= t < 12.0 else (1 - 2 * ease((t - 12.0) / .2) if 12.0 <= t < 12.3 else (-.6 if 12.3 <= t < 14 else 0))
    swd = ease((t - 6.0) / .25) if t >= 6.0 else 0
    J['hand'] = (X - lerp(12, 32, swd) + 8 * raise_, Y - lerp(92, 122, swd) - 52 * max(0, raise_) + 20 * max(0, -raise_)); J['hand2'] = (X + 12, Y - 94)
    ang = math.radians(lerp(100, 30, swd) + 110 * max(0, raise_) - 80 * max(0, -raise_) + (45 * ease((t - 14.0) / .4) if t >= 14.0 else 0))
    J['tip'] = (J['hand'][0] - 76 * swd * math.cos(ang), J['hand'][1] - 76 * swd * math.sin(ang))
    return J, turn, swd
SEG = dict(legL=('hip', 'ftL'), legR=('hip', 'ftR'), torso=('hip', 'sh'), head=('neck', 'top'), plume=('top', 'plume'), arm=('sh', 'hand'), arm2=('sh', 'hand2'))
def knight(t):
    J, turn, swd = kjoints(t); out = []
    for i, p in enumerate(KN):
        a, b = J[SEG[p['part']][0]], J[SEG[p['part']][1]]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L; w = WID[p['part']] * 1.25
        q = [(a[0] + dx * u + nx * w * v, a[1] + dy * u + ny * w * v) for u, v in ((p['u'][0], p['v'][0]), (p['u'][1], p['v'][0]), (p['u'][1], p['v'][1]), (p['u'][0], p['v'][1]))]
        out.append((i, q, p['col'], 2))
    vc = (J['top'][0] - 7 * turn + 1, J['top'][1] + 16); out.append((len(KN), [(vc[0] - 8, vc[1] - 3), (vc[0] + 6, vc[1] - 3), (vc[0] + 6, vc[1] + 3), (vc[0] - 8, vc[1] + 3)], 'visor', 6))
    if swd > .05: out.append((len(KN) + 1, limb(J['hand'], J['tip'], 5, 1.5), 'red', 4))
    return out, J

def plan():
    pcs = [p for p in knight(9.5)[0] if p[3] == 2]; J = kjoints(9.5)[0]
    cen = {i: np.mean(q, 0) for i, q, _, _ in pcs}; ids = sorted(cen, key=lambda i: np.hypot(*(cen[i] - np.array(J['sh']))))
    n = len(ids); k1 = int(round(.12 * n)); rest = ids[k1:]; rng.shuffle(rest); fb = {}
    for shot, tt, paint, lst in releases(sc, n, ids[:k1] + rest):
        for i in lst: fb[i] = (shot, tt, paint)
    fb[len(KN)] = fb[len(KN) + 1] = (5, sc['pieces'][5]['t'], sc['pieces'][5]['paint'])
    return fb
FREED = plan(); FLY = {}
BLOOM = .22   # the outline grows for this long before the piece lets go
for tt in sorted(set(v[1] for v in FREED.values())):
    for i, q, c, l in knight(tt)[0]:
        if i in FREED and FREED[i][1] == tt:
            shot = FREED[i][0]; cc = np.mean(q, 0); spread = 140 if shot == 5 else 46
            FLY[i] = dict(t0=tt, shot=shot, q=np.array(q) - cc, c=cc, land=(cc[0] + rng.uniform(-spread, spread * .7) + 12, FLOOR + 6 + rng.uniform(0, 1) ** 1.5 * (60 if shot == 5 else 34)),
                          ang=rng.uniform(-2.5, 2.5) if i != len(KN) + 1 else 1.4, col=hexrgb(FREED[i][2]), own=c, sc=.55 if i == len(KN) + 1 else 1.6, lobes=rng.integers(3, 6), ph=rng.uniform(0, 6.28))
def bloom_shape(q, u, lobes, ph):
    """the piece's outline grows organic lobes, like coral or a crystal flowering, before it breaks off"""
    c = np.mean(q, 0); out = []; n = len(q)
    for k in range(n * 6):
        a = q[k // 6]; b = q[((k // 6) + 1) % n]; s = (k % 6) / 6; p = np.array(a) * (1 - s) + np.array(b) * s
        ang = math.atan2(p[1] - c[1], p[0] - c[0]); g = 1 + u * (.5 + .55 * max(0, math.sin(lobes * ang + ph)))
        out.append(tuple(c + (p - c) * g))
    return out

def trails(t):
    """light that stays behind: the sword's tip, the leap, every shot from the muzzle to where it lands"""
    tr = []
    if t >= 6.0 and t < 19.5:
        pts = [knight(t - k / 60)[1]['tip'] for k in range(0, 14) if t - k / 60 >= 6.0]
        if len(pts) > 2: tr.append((pts, (255, 90, 80), 6))
    if 4.5 <= t < 5.6:
        pts = [kjoints(t - k / 40)[0]['sh'] for k in range(0, 16) if t - k / 40 >= 4.5]
        if len(pts) > 2: tr.append((pts, (150, 200, 255), 9))
    for p in sc['pieces']:
        t0, t1 = p['t'] - .14, p['t'] + .35
        if t0 <= t < t1:
            _, mz, _ = mesa(p['t'] - .14); tgt = np.mean([q for i, q, c, l in knight(p['t'])[0] if FREED.get(i, (0, -1))[1] == p['t']][0], 0) if any(FREED.get(i, (0, -1))[1] == p['t'] for i in range(len(KN))) else np.array(kjoints(p['t'])[0]['sh'])
            head = min(1, (t - t0) / .14); tail = max(0, (t - t0 - .26) / .3)
            pts = [tuple(np.array(mz) * (1 - s) + tgt * s) for s in np.linspace(tail, head, 12)]
            if head > tail: tr.append((pts, hexrgb(p['paint']), 11))
    return tr

def coda(t, x):
    if t <= 20.5: return 1.0
    cx = sx(lerp(-6.0, 0.5, ease((t - 20.5) / 3.5))); return 1 + .45 * math.exp(-((x - cx - 40) / 80) ** 2) * ease((t - 20.5) / .8)
def draw(t):
    fr = sc['frames'][min(575, int(round(t * FPS)))]
    im = Image.new('RGB', (W * K2, H * K2)); d = ImageDraw.Draw(im); lab = Image.new('L', (W, H), 0)
    win = place(d, t, fr); lab_poly(lab, win, 3)
    ms, muzzle, mfoot = mesa(t); kn = []
    if t < 19.5: kn, J = knight(t)
    # cast shadows only: every figure throws a flat sheared shadow away from the light
    def shadow(q, y0): return [(x + (y0 - y) * .9, y0 + (y0 - y) * .16) for x, y in q]
    for q, c, l in ms: poly(d, shadow(q, mfoot[1]), COL['shadow'], False)
    ky = FLOOR if t >= 5.1 else None
    if ky:
        for i, q, c, l in kn:
            if not (i in FREED and t >= FREED[i][1]): poly(d, shadow(q, ky), COL['shadow'], False)
    def refl(q, y0, c): poly(d, [(x, 2 * y0 - y) for x, y in q], tuple(int(lerp(v, f_, .5) * .82) for v, f_ in zip(c, COL['floor2'])))
    for q, c, l in ms: refl(q, mfoot[1] if mfoot[1] >= FLOOR - 1 else FLOOR, COL[c])
    if ky:
        for i, q, c, l in kn:
            if not (i in FREED and t >= FREED[i][1]): refl(q, FLOOR, COL[c])
    # the coda light: after the last break a low light crosses the floor and the pieces, left to right
    if t > 20.5:
        cx = sx(lerp(-6.0, 0.5, ease((t - 20.5) / 3.5))); a_ = ease((t - 20.5) / .8)
        poly(d, [(cx - 60, FLOOR - 4), (cx + 60, FLOOR - 4), (cx + 110, H), (cx - 10, H)], tuple(int(lerp(v, 255, .55 * a_)) for v in COL['floor']), False)
    # pieces: blooming in place, then falling, then lying where they fell
    for i, P in sorted(FLY.items(), key=lambda kv: -kv[1]['shot']):   # the last shot's pieces lie under the earlier ones
        if t < P['t0']: continue
        dt = t - P['t0']
        if dt < BLOOM:
            src = knight(P['t0'])[0]; q = next(qq for ii, qq, cc, ll in src if ii == i); qq = bloom_shape(q, dt / BLOOM, P['lobes'], P['ph'])
        else:
            u = min(1, (dt - BLOOM) / .45); X = lerp(P['c'][0], P['land'][0], u); Y = lerp(P['c'][1], P['land'][1], u * u); fl = lerp(1, .5, u)
            qq = [rot((X + x * P['sc'], Y + y * fl * P['sc']), (X, Y), P['ang'] * u) for x, y in P['q']]
        cx_, cy_ = np.mean([q_[0] for q_ in qq]), np.mean([q_[1] for q_ in qq]); g = coda(t, cx_)
        c_ = np.array(P['col'], float) * g; c_ = c_ * 255 / c_.max() if c_.max() > 255 else c_; lit = tuple(int(lerp(v, 255, (g - 1) * .12)) for v in c_); poly(d, qq, lit); lab_poly(lab, qq, 10 + P['shot'])
        core = [(cx_ + (x_ - cx_) * .32, cy_ + (y_ - cy_) * .32) for x_, y_ in qq]; poly(d, core, tuple(int(min(255, v * g)) for v in COL[P['own']]), False)   # the knight's own glass, under the paint
    for q, c, l in ms: poly(d, q, COL[c]); lab_poly(lab, q, l)
    for i, q, c, l in kn:
        if i in FREED and t >= FREED[i][1]: continue
        poly(d, q, COL[c]); lab_poly(lab, q, l)
    for pts, col, w in trails(t):   # trails: tapered, bright, no outline (they are light, not things)
        for k in range(len(pts) - 1):
            a = k / (len(pts) - 1); ww = max(1, int(w * K2 * (1 - a)))
            d.line([(pts[k][0] * K2, pts[k][1] * K2), (pts[k + 1][0] * K2, pts[k + 1][1] * K2)], tuple(int(lerp(255, v, .4 + .6 * a)) for v in col), ww)
    rgb = np.asarray(im.resize((W, H), Image.LANCZOS))
    return rgb, np.asarray(lab)

def frame(f): return draw(f / FPS)

def drum(r, f0=70, d=.6):
    n = int(d * SR); tt = np.arange(n) / SR; ph = 2 * np.pi * np.cumsum(f0 * (1 + 1.5 * np.exp(-tt * 18))) / SR
    return (np.sin(ph) * np.exp(-tt * 6) + .3 * r.standard_normal(n) * np.exp(-tt * 40)).astype(np.float32)
def sound():
    buf = tl(24.0); r = np.random.default_rng(88); n = len(buf); tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * f * tt + .3 * np.sin(2 * np.pi * .2 * tt)) for f in (110, 138.6, 164.8, 220)) * .025; buf += pad * np.clip(tt / 3, 0, 1)
    beats = list(np.arange(6.5, 12.2, .5)) + list(np.arange(14.0, 19.5, .375))   # the drums come in with the gun and drive toward each break
    for b in beats: add(buf, b, drum(r, 62 if int(b * 4) % 4 == 0 else 90, .5), .5)
    add(buf, 4.5, noise(.5, r, .3, lp=4000) * np.linspace(1, 0, int(.5 * SR)), .3)
    add(buf, 6.0, tone(1200, 1.4, .01, .6, harm=(1., .4, .2)), .25)
    for p in sc['pieces']:
        zap = tone(880, .2, .002, .08) * np.linspace(1, .2, int(.2 * SR)); add(buf, p['t'] - .14, zap, .5)
        sh = sum(tone(f, .5, .01, .3) for f in r.uniform(1500, 4000, 6)) * np.linspace(.2, 1, int(.5 * SR)); add(buf, p['t'], sh, .12)   # the bloom, rising
        add(buf, p['t'] + BLOOM, noise(.15, r, .05, lp=5000), .35)
        for k in range(5): add(buf, p['t'] + BLOOM + .02 * k, chime(1200 + r.uniform(0, 1800), 1.2), .45)
    add(buf, 12.2, drum(r, 40, 1.4), 1.3); [add(buf, 19.5 + BLOOM + r.uniform(0, .8), chime(900 + r.uniform(0, 2600), 1.6), .3) for _ in range(30)]; add(buf, 19.5 + BLOOM, drum(r, 36, 2.0), 1.2)
    write_wav(os.path.join(HERE, 'sound.wav'), buf)

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    sound(); meter = Meter(sc); film = Film(os.path.join(OUT, 'film.mp4')); still = set(int(round(s * FPS)) for s in STILL_T)
    for f in range(576):
        rgb, lab = frame(f); t = f / FPS; skip = 19.54 <= t < 20.1
        if skip:
            z = 1.8 - .5 * ease((t - 19.54) / .56); cx, cy = sx(-3.6), FLOOR - 90; w, h = W / z, H / z
            x0 = min(max(0, cx - w / 2), W - w); y0 = min(max(0, cy - h / 2), H - h)   # the push-in stays inside the drawing
            rgb = np.asarray(Image.fromarray(rgb).crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.LANCZOS))
        film.put(rgb); meter.frame(f, lab[::2, ::2], rgb, skip=skip)
        if f in still: Image.fromarray(rgb).save(os.path.join(OUT, 'stills', f'still_{f / FPS:04.1f}s.jpg'), quality=90)
        if f % 48 == 0: print('frame', f, flush=True)
    for nm, tt in (('bloom', 9.6), ('last-bloom', 19.62), ('trail', 4.75)): Image.fromarray(frame(int(round(tt * FPS)))[0]).save(os.path.join(OUT, 'stills', f'{nm}_{tt:05.2f}s.jpg'), quality=90)
    film.close(os.path.join(HERE, 'sound.wav'))
    rep = meter.report(); json.dump(rep, open(os.path.join(OUT, 'invariants.json'), 'w'), indent=1)
    json.dump(dict(swarm='SCION-MOEBIUS-OTOMO', panels=len(KN), line_px=LW / K2, bloom_s=BLOOM, frames=meter.rows), open(os.path.join(OUT, 'trace.json'), 'w'))
    contact(os.path.join(OUT, 'stills'), os.path.join(OUT, 'stills', 'contact.jpg'))
    print({k: (v['ok'] if isinstance(v, dict) else v) for k, v in rep.items()})
