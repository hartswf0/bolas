#!/usr/bin/env python3
"""SCION-MAMBETY · MESA CHIP, handmade. Told by a griot, not shot by a camera: torn paper cut from the game's own footage, puppets of
stiff cards, the clock kept and the angle broken. Holds and jump cuts on a plucked rhythm, the fall and the first hit each told three
times, and returning images (horns, the sea, the kanaga, the game's own shards) that interrupt at decisions. Run: python3 render.py"""
import sys, os, json, math, numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, '..'); sys.path.insert(0, os.path.join(HERE, '..', '..', 'tools')); sys.path.insert(0, HERE)
from common import *
import footage as FT
sc = score(); rng = np.random.default_rng(1973)
F = FT.frames(); MAT, MATLOG = FT.hunt(F, np.random.default_rng(73)); PL, PLLOG = FT.cut(F, FT.PLATES); INS, INSLOG = FT.cut(F, FT.INSERTS)
json.dump(dict(materials=MATLOG, plates=PLLOG, inserts=INSLOG, note='every source is a picture made by this project (make-photo/mesa); no outside footage'), open(os.path.join(OUT, 'assets.json'), 'w'), indent=1)
FLOOR, SILL = 470.0, 322.0
def sx(x): return 470 + 60 * x
def ease(u): u = min(1, max(0, u)); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def rot(p, c, a): s, k = math.sin(a), math.cos(a); x, y = p[0] - c[0], p[1] - c[1]; return (c[0] + k * x - s * y, c[1] + s * x + k * y)
WX = sx(6.2); WL, WR = WX - 32, WX + 32

# ---------- the backdrop: strips torn from the footage ----------
def torn_mask(w, h, r, edges='tb'):
    m = Image.new('L', (w, h), 255); d = ImageDraw.Draw(m); walk = lambda n: np.cumsum(r.normal(0, 1.6, n)).clip(-7, 7) + 8
    if 't' in edges: top = walk(w); d.polygon([(0, 0)] + [(x, top[x]) for x in range(w)] + [(w, 0)], 0)
    if 'b' in edges: bot = walk(w); d.polygon([(0, h)] + [(x, h - bot[x]) for x in range(w)] + [(w, h)], 0)
    if 'l' in edges: le = walk(h); d.polygon([(0, 0)] + [(le[y], y) for y in range(h)] + [(0, h)], 0)
    if 'r' in edges: ri = walk(h); d.polygon([(w, 0)] + [(w - ri[y], y) for y in range(h)] + [(w, h)], 0)
    return m
def backdrop():
    r = np.random.default_rng(5); B = Image.new('RGB', (W, H), tuple(MAT['night'].reshape(-1, 3).mean(0).astype(int)))
    sky = PL['sky'].resize((W + 40, 230)); B.paste(sky, (-20, -24), torn_mask(W + 40, 230, r, 'b'))
    gw = ImageEnhance.Brightness(PL['glasswall'].resize((W + 40, 280))).enhance(.85); B.paste(gw, (-20, 170), torn_mask(W + 40, 280, r, 'tb'))
    fl = PL['floor'].resize((W + 40, 150)); B.paste(fl, (-20, int(FLOOR) - 34), torn_mask(W + 40, 150, r, 't'))
    can = PL['canyon'].resize((240, 380)); B.paste(can, (int(WL) - 70, 60), torn_mask(240, 380, r, 'lt'))
    win = PL['window'].resize((int(WR - WL), int(SILL - 70))); B.paste(win, (int(WL), 70), torn_mask(win.size[0], win.size[1], r, 'lr'))
    steps = Image.fromarray(np.tile(MAT['sand'], (3, 2, 1))).resize((int(sx(-6.55)) + 20, 70)); steps = Image.fromarray(np.tile(MAT['sand'], (3, 3, 1))).resize((int(sx(-6.2)) + 20, 66)); B.paste(ImageEnhance.Brightness(steps).enhance(.95), (-20, int(FLOOR) - 30), torn_mask(steps.size[0], 66, r, 'r'))
    ImageDraw.Draw(B).line([(0, int(FLOOR) - 29), (int(sx(-6.2)), int(FLOOR) - 29)], (250, 226, 170), 3)
    wm = np.zeros((H, W), bool); wm[72:int(SILL) - 2, int(WL) + 8:int(WR) - 8] = True
    return np.asarray(B), wm
BACK, WINM = backdrop()

def tex_poly(img, lab, pts, mat, lv, jitter=0.0, r=None, shade=1.0):
    """paste a torn piece of a material, cut to this polygon"""
    if r is not None and jitter: pts = [(x + r.normal(0, jitter), y + r.normal(0, jitter)) for x, y in pts]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]; x0, y0, x1, y1 = int(min(xs)) - 1, int(min(ys)) - 1, int(max(xs)) + 2, int(max(ys)) + 2
    if x1 <= x0 or y1 <= y0: return
    m = Image.new('L', (x1 - x0, y1 - y0), 0); ImageDraw.Draw(m).polygon([(x - x0, y - y0) for x, y in pts], 255)
    t = MAT[mat] if isinstance(mat, str) else mat
    th, tw = t.shape[:2]; reps = ((y1 - y0) // th + 2, (x1 - x0) // tw + 2); tile = np.tile(t, (reps[0], reps[1], 1))
    oy, ox = (abs(hash((mat if isinstance(mat, str) else 'm', x0 // 40))) % th), (abs(hash((y0 // 40, 'x'))) % tw)
    patch = tile[oy:oy + y1 - y0, ox:ox + x1 - x0].astype(np.float32) * shade
    img.paste(Image.fromarray(np.clip(patch, 0, 255).astype(np.uint8)), (x0, y0), m)
    if lab is not None: ImageDraw.Draw(lab).polygon(pts, lv)

def quad(a, b, w0, w1):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
    return [(a[0] + nx * w0 / 2, a[1] + ny * w0 / 2), (b[0] + nx * w1 / 2, b[1] + ny * w1 / 2), (b[0] - nx * w1 / 2, b[1] - ny * w1 / 2), (a[0] - nx * w0 / 2, a[1] - ny * w0 / 2)]

# ---------- Uncle Mesa, a puppet of seven cards: a Black man in his sixties, long white beard, round glasses with gold lenses,
# cream wide-brimmed hat, white guayabera-style shirt, khaki trousers, dark boots, the six-shooter of paint ----------
def mesa_cards(t, hold_i):
    fr = sc['frames'][min(575, int(round(t * FPS)))]; st = fr['mesa']['state']; x = fr['mesa']['x']
    f = -1 if st == 'walk' else 1; walking = st in ('descend', 'walk') or 14.0 < t < 15.0
    sw = (14 if hold_i % 2 else -14) if walking else 0               # the walk is two cards, swapped on each hold: staccato, as told
    aim = ease((t - 6.5) / .1) if t >= 6.5 else 0.0
    if 12.2 <= t < 14.05 or t >= 20.8: aim = 0.0
    sit = ease((t - 21.9) / .15) if t >= 21.9 else 0.0
    gy = FLOOR - 60 + 30 * ease((x + 7.0) / .25) + 30 * ease((x + 6.7) / .25) if sit == 0 else FLOOR
    cards = []; hip = (0, -120 + 80 * sit)
    for k, s in enumerate((sw, -sw)):
        if sit:
            knee = (36 * f, hip[1] - 4); foot = (44 * f, 0); cards += [(quad(hip, knee, 30, 26), 'khaki', 1), (quad(knee, foot, 26, 22), 'khaki', 1)]
        else:
            a = math.radians(s); foot = (math.sin(a) * 120 * f, math.cos(a) * 120 + hip[1]); cards.append((quad(hip, foot, 30, 24), 'khaki', 1))
        cards.append(([(foot[0] - 10, foot[1] - 12), (foot[0] + 24 * f, foot[1] - 12), (foot[0] + 26 * f, foot[1] + 1), (foot[0] - 10, foot[1] + 1)], 'boot', 1))
    sh = (hip[0] + 4 * f, hip[1] - 88)
    cards.append(([(hip[0] - 22, hip[1] + 6), (hip[0] + 22, hip[1] + 6), (sh[0] + 26, sh[1]), (sh[0] - 26, sh[1])], 'shirt', 1))
    cards.append((quad((sh[0] - 8 * f, sh[1] + 6), (sh[0] - 12 * f, sh[1] + 78), 18, 16), 'shirt', 1))
    hd = (sh[0] + 6 * f, sh[1] - 26)
    cards.append(([(hd[0] - 21 + 21 * math.cos(a), hd[1] + 23 * math.sin(a)) if False else (hd[0] + 21 * math.cos(a), hd[1] + 23 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 18)], 'skin', 1))
    cards.append(([(hd[0] - 12 * f, hd[1] + 6), (hd[0] + 20 * f, hd[1] + 6), (hd[0] + 16 * f, hd[1] + 50), (hd[0] + 2 * f, hd[1] + 60), (hd[0] - 10 * f, hd[1] + 30)], 'beard', 1))
    for gx in (2, 14): cards.append(([(hd[0] + gx * f + 6 * math.cos(a), hd[1] - 4 + 6 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 12)], 'gold', 1))
    cards.insert(-3, ([(sh[0] + 2 * f, sh[1] + 16), (sh[0] + 16 * f, sh[1] + 16), (sh[0] + 16 * f, sh[1] + 27), (sh[0] + 2 * f, sh[1] + 27)], np.full((12, 12, 3), (240, 204, 40), np.uint8), 1))
    cards.append(([(hd[0] - 44, hd[1] - 16), (hd[0] + 44, hd[1] - 16), (hd[0] + 40, hd[1] - 8), (hd[0] - 40, hd[1] - 8)], 'hat', 1))
    cards.append(([(hd[0] - 18, hd[1] - 16), (hd[0] + 18, hd[1] - 16), (hd[0] + 15, hd[1] - 42), (hd[0] - 15, hd[1] - 42)], 'hat', 1))
    a0 = (sh[0] + 6 * f, sh[1] + 6); lo = (sh[0] + 14 * f, sh[1] + 76); hi = (sh[0] + 68 * f, sh[1] + 2)
    hand = (lerp(lo[0], hi[0], aim), lerp(lo[1], hi[1], aim)); cards.append((quad(a0, hand, 18, 16), 'shirt', 1))
    dv = np.array([hand[0] - a0[0], hand[1] - a0[1]]); dv /= np.linalg.norm(dv); nv = np.array([-dv[1], dv[0]]) * f; ha = np.array(hand)
    gun = [tuple(ha - dv * 6 - nv * 9), tuple(ha + dv * 38 - nv * 9), tuple(ha + dv * 38 + nv * 2), tuple(ha + dv * 8 + nv * 4), tuple(ha + dv * 2 + nv * 18), tuple(ha - dv * 8 + nv * 16)]
    cards.append((gun, np.full((24, 24, 3), (40, 196, 206), np.uint8) + rng.integers(0, 20, (24, 24, 1)).astype(np.uint8), 5))
    down = 0.0
    if 12.2 <= t < 14.05: down = ease((t - 12.2) / .1) * (1 - ease((t - 13.85) / .2))
    X = sx(x)
    def place(p):
        if down: p = rot(p, (0, -110), -f * down * math.pi / 2 * .96); p = (p[0], p[1] + 96 * down)
        if sit: p = (p[0] - 20 * f * sit, p[1])
        return (X + p[0], gy + p[1])
    return [([place(p) for p in q], m, l) for q, m, l in cards]

# ---------- the knight, a card of torn glass pieces ----------
KPIECES = []
def kgrid(name, a, b, w, na, nc, mats):
    for i in range(na):
        for j in range(nc): KPIECES.append(dict(part=name, a=a, b=b, w=w, u=(i / na, (i + 1) / na), v=(j / nc - .5, (j + 1) / nc - .5), mat=mats[(i + j) % len(mats)], jit=rng.normal(0, 1.8, (4, 2))))
kgrid('legL', 'hip', 'ftL', 26, 3, 2, ['silver', 'gold']); kgrid('legR', 'hip', 'ftR', 26, 3, 2, ['silver', 'gold'])
kgrid('torso', 'hip', 'sh', 58, 4, 4, ['silver', 'gold', 'silver', 'redglass']); kgrid('head', 'neck', 'top', 34, 2, 3, ['silver', 'gold'])
kgrid('plume', 'top', 'plume', 12, 3, 1, ['redglass']); kgrid('arm', 'sh', 'hand', 18, 3, 1, ['silver', 'gold']); kgrid('arm2', 'sh', 'hand2', 18, 3, 1, ['silver'])
def kjoints(t):
    fr = sc['frames'][min(575, int(round(t * FPS)))]; st = fr['knight']['state']; f = -1
    X, Y = sx(fr['knight']['x']), FLOOR
    if t < 4.5: X, Y = WX, SILL
    elif t < 5.1: u = (t - 4.5) / .6; X = lerp(WX, sx(5.4), 1 - math.exp(-u * 6)); Y = lerp(SILL, FLOOR, ease(u * 1.5)) - 40 * math.sin(math.pi * min(1, u * 1.5))
    walking = st in ('advance', 'advance_broken'); sw = (12 if st == 'advance' else 22) * math.sin(t * 2 * math.pi * (1.3 if st == 'advance' else .9)) if walking else 0
    J = {'hip': (X, Y - 124)}
    J['ftL'] = (X + 1.4 * sw, Y); J['ftR'] = (X - 1.4 * sw, Y); J['sh'] = (X - 4, Y - 205); J['neck'] = (X - 6, Y - 212)
    turn = ease((t - 3.0) / .1) if t >= 3.0 else 0
    J['top'] = (X - 6 - 4 * turn, Y - 252); J['plume'] = (X + 22, Y - 284)
    raise_ = ease((t - 11.55) / .45) if 11.55 <= t < 12.0 else (1 - 2 * ease((t - 12.0) / .2) if 12.0 <= t < 12.3 else (-.6 if 12.3 <= t < 14 else 0))
    swd = ease((t - 6.0) / .15) if t >= 6.0 else 0
    J['hand'] = (X - lerp(16, 46, swd) + 10 * raise_, Y - lerp(130, 170, swd) - 70 * max(0, raise_) + 30 * max(0, -raise_)); J['hand2'] = (X + 16, Y - 132)
    ang = math.radians(lerp(100, 30, swd) + 110 * max(0, raise_) - 80 * max(0, -raise_) + (50 * ease((t - 14.0) / .4) if t >= 14.0 else 0))
    J['tip'] = (J['hand'][0] - 104 * swd * math.cos(ang), J['hand'][1] - 104 * swd * math.sin(ang))
    return J, turn, swd
def kpieces(t):
    J, turn, swd = kjoints(t); out = []
    for i, p in enumerate(KPIECES):
        a, b = J[p['a']], J[p['b']]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
        q = [(a[0] + dx * u + nx * p['w'] * v + p['jit'][k][0], a[1] + dy * u + ny * p['w'] * v + p['jit'][k][1]) for k, (u, v) in enumerate(((p['u'][0], p['v'][0]), (p['u'][1], p['v'][0]), (p['u'][1], p['v'][1]), (p['u'][0], p['v'][1])))]
        out.append((i, q, p['mat'], 2))
    vc = (J['top'][0] - 15 * turn + 4, J['top'][1] + 22); out.append((len(KPIECES), [(vc[0] - 12, vc[1] - 5), (vc[0] + 9, vc[1] - 5), (vc[0] + 9, vc[1] + 5), (vc[0] - 12, vc[1] + 5)], 'night', 6))
    if swd > .05: out.append((len(KPIECES) + 1, quad(J['hand'], J['tip'], 14, 5), 'redglass', 4))
    return out
def plan():
    pcs = [p for p in kpieces(9.5) if p[3] == 2]; J, _, _ = kjoints(9.5)
    cen = {i: np.mean(q, 0) for i, q, _, _ in pcs}; ids = sorted(cen, key=lambda i: np.hypot(*(cen[i] - np.array(J['sh']))))
    n = len(ids); k1 = int(round(.12 * n)); rest = ids[k1:]; rng.shuffle(rest); fb = {}
    for shot, tt, paint, lst in releases(sc, n, ids[:k1] + rest):
        for i in lst: fb[i] = (shot, tt, paint)
    fb[len(KPIECES)] = fb[len(KPIECES) + 1] = (5, sc['pieces'][5]['t'], sc['pieces'][5]['paint'])
    return fb
FREED = plan(); FLY = {}
for tt in sorted(set(v[1] for v in FREED.values())):
    for i, q, m, l in kpieces(tt):
        if i in FREED and FREED[i][1] == tt:
            shot = FREED[i][0]; c = np.mean(q, 0); spread = 150 if shot == 5 else 50
            FLY[i] = dict(t0=tt, shot=shot, q=np.array(q) - c, c=c, land=(c[0] + rng.uniform(-spread, spread * .6), FLOOR + 6 + rng.uniform(0, 1) ** 1.5 * (52 if shot == 5 else 30)), ang=rng.uniform(-2, 2),
                          paint=np.clip(MAT[m].astype(np.float32) * .18 + np.array(hexrgb(FREED[i][2])) * .86, 0, 255).astype(np.uint8))   # the paint takes the glass: its own grain under the colour

# ---------- the scene at master time t ----------
def scene(t, hold_i):
    img = Image.fromarray(BACK.copy()); lab = Image.new('L', (W, H), 0); ImageDraw.Draw(lab).bitmap((0, 0), Image.fromarray((WINM * 255).astype(np.uint8)), fill=3)
    r = np.random.default_rng(hold_i)   # the paper edges boil once per hold, not per frame
    fig = Image.fromarray(BACK.copy()); fl = Image.new('L', (W, H), 0)
    for q, m, l in mesa_cards(t, hold_i): tex_poly(fig, fl, q, m, 255)
    if t < 19.5:
        for i, q, m, l in kpieces(t):
            if not (i in FREED and t >= FREED[i][1]): tex_poly(fig, fl, q, m, 255)
    F_ = int(FLOOR); a = np.asarray(fig).astype(np.float32); al = np.asarray(fl).astype(np.float32)[..., None] / 255
    n_ = H - F_; src = a[F_ - n_:F_][::-1]; sal = al[F_ - n_:F_][::-1] * .42
    base = np.asarray(img).astype(np.float32); base[F_:] = base[F_:] * (1 - sal) + src * .7 * sal; img = Image.fromarray(base.astype(np.uint8))
    for i, P in FLY.items():
        if t < P['t0']: continue
        u = min(1, (t - P['t0']) / .45); X = lerp(P['c'][0], P['land'][0], u); Y = lerp(P['c'][1], P['land'][1], u * u); fl = lerp(1, .5, u)
        q = [rot((X + x * 1.2, Y + y * fl * 1.2), (X, Y), P['ang'] * u) for x, y in P['q']]; tex_poly(img, lab, q, P['paint'], 10 + P['shot'])
    for q, m, l in mesa_cards(t, hold_i): tex_poly(img, lab, q, m, l, .8, r)
    if t < 19.5:
        for i, q, m, l in kpieces(t):
            if i in FREED and t >= FREED[i][1]: continue
            tex_poly(img, lab, q, m, l, .8, r, shade=1.08)
    return img, lab

# ---------- the edit: a griot's rhythm ----------
EVENTS = [e['t'] for e in sc['events']]
HOLDS = [2, 1, 1, 3, 1, 2, 1, 1, 2, 3]           # the kora's pattern, in frames
INSERTS = [(1.30, 1.62, 'sea'), (3.55, 3.88, 'kanaga'), (7.00, 7.25, 'horns'), (10.40, 10.62, 'mural'), (14.45, 14.70, 'horns'), (20.10, 20.35, 'shards'), (21.25, 21.50, 'horns'), ]
RETELL = [  # (start, end, source time at start, zoom, mirror): the same moment again, cut differently, the clock going on underneath
    (9.62, 9.75, 9.44, 1.8, False), (9.75, 9.88, 9.47, 2.5, True),
    (12.36, 12.50, 12.16, 1.7, False), (12.50, 12.64, 12.19, 2.3, True),
    (19.62, 19.76, 19.46, 1.9, False), (23.0, 24.1, 23.0, 1.9, False)]
def edl():
    out, hi, f, k = [], 0, 0, 0
    while f < 576:
        t = f / FPS; ins = next((c for c in INSERTS if c[0] <= t < c[1]), None); ret = next((c for c in RETELL if c[0] <= t < c[1]), None)
        if ins: out.append(('insert', ins[2], (t - ins[0]) / (ins[1] - ins[0]), hi)); f += 1; continue
        if ret: out.append(('retell', ret[2] + (t - ret[0]), ret[3], ret[4], hi)); f += 1; continue
        near = any(abs(t - e) < 4 / FPS for e in EVENTS)
        n = 1 if near else HOLDS[k % len(HOLDS)]; k += 1; hi += 1
        for j in range(n):
            if f + j < 576: out.append(('master', t, hi))
        f += n
    return out[:576]
EDL = edl()

def grade(im, f, r):
    a = np.asarray(im).astype(np.float32)
    g = a.mean(2, keepdims=True); a = g + (a - g) * 1.22                     # hot
    a = a * np.array([1.06, .99, .9]) + np.array([8, 2, -6])                  # worn, warm
    a *= 1 + .035 * math.sin(f * 2.1) + r.normal(0, .015)                      # flicker
    a += r.normal(0, 7, (H, W, 1))                                            # grain
    for _ in range(r.integers(0, 3)): x = r.integers(0, W); a[:, x:x + 1] = a[:, x:x + 1] * .55 + 80       # scratches
    for _ in range(r.integers(2, 9)): x, y = r.integers(0, W), r.integers(0, H); a[y:y + 3, x:x + 2] = 20 # dust
    yy, xx = np.mgrid[0:H, 0:W]; a *= (1 - .38 * (((xx - 480) / 560) ** 2 + ((yy - 270) / 380) ** 2))[..., None]
    return np.clip(a, 0, 255).astype(np.uint8)

def frame(f):
    r = np.random.default_rng(1000 + f); e = EDL[f]
    if e[0] == 'master':
        img, lab = scene(e[1], e[2]); dx, dy = int(r.integers(-1, 2)), int(r.integers(-1, 2))   # gate weave
        rgb = grade(img, f, r); rgb = np.roll(rgb, (dy, dx), (0, 1)); lab = np.roll(np.asarray(lab), (dy, dx), (0, 1)); return rgb, lab, False, e
    if e[0] == 'retell':
        img, _ = scene(e[1], e[4]); t = e[1]; fr = sc['frames'][min(575, int(round(t * FPS)))]
        cx = (sx(fr['mesa']['x']) + sx(fr['knight']['x'])) / 2 if t < 19.5 else sx(fr['knight']['x']); z = e[2]; w, h = W / z, H / z
        x0 = min(max(0, cx - w / 2), W - w); y0 = min(max(0, FLOOR - 120 - h / 2), H - h)
        if t >= 23.0:   # the coda: down on the pieces, and a light crossing them
            x0, y0 = sx(-4.6), H - h
            a_ = np.asarray(img).astype(np.float32); xx = np.arange(W)[None, :, None]; lx = lerp(sx(-5.2), sx(-1.0), (t - 23.0) / 1.0)
            a_[int(FLOOR) - 20:] *= 1 + .55 * np.exp(-((xx - lx) / 45) ** 2); img = Image.fromarray(np.clip(a_, 0, 255).astype(np.uint8))
        img = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)
        if e[3]: img = ImageOps.mirror(img)
        return grade(img, f, r), np.zeros((H, W), np.uint8), True, e
    src = INS[e[1]]; u = e[2]; z = 1.0 + .12 * u      # the insert drifts in
    if e[1] == 'horns':
        src = src.copy(); dd = ImageDraw.Draw(src); rr = np.random.default_rng(42); fired = [p for p in sc['pieces'] if p['t'] <= f / FPS]
        for k, p in enumerate(fired):
            for j in range(10):
                cx, cy = rr.uniform(40, src.size[0] - 40), rr.uniform(20, src.size[1] - 20); rad = rr.uniform(8, 22)
                dd.ellipse([cx - rad, cy - rad * .8, cx + rad, cy + rad * .8], hexrgb(p['paint']))
    w, h = src.size[0] / z, src.size[1] / z; im = src.crop((int((src.size[0] - w) / 2), int((src.size[1] - h) / 2), int((src.size[0] + w) / 2), int((src.size[1] + h) / 2)))
    im = ImageOps.fit(im, (W, H)); return grade(im, f, r), np.zeros((H, W), np.uint8), True, e

def kora(f0, d, r):
    """Karplus-Strong: a plucked string"""
    n = int(d * SR); p = int(SR / f0); buf = r.uniform(-1, 1, p).astype(np.float32); out = np.zeros(n, np.float32)
    for i in range(n): out[i] = buf[i % p]; buf[i % p] = .5 * (buf[i % p] + buf[(i + 1) % p]) * .996
    return out * env(n, .002, d / 2.5)
def sound():
    buf = tl(24.0); r = np.random.default_rng(11); scale = [196, 220, 247, 294, 330, 392, 440]
    hum = noise(24.0, r, 1e9, lp=300) * .04; buf += hum[:len(buf)] * np.clip((23.0 - np.arange(len(buf)) / SR) * 4, 0, 1)   # the street, until the silence
    t, k = 0.0, 0
    while t < 23.0:                                                         # the teller's string keeps time
        add(buf, t, kora(scale[(k * 3 + (k // 5)) % len(scale)], .7, r), .22); t += [.25, .25, .5, .25, .75][k % 5]; k += 1
    for e in sc['events']:
        if e['what'].startswith('hit') or e['what'] == 'shatter':
            add(buf, e['t'] - .12, noise(.06, r, .03, lp=2500), .8)          # the shot arrives a little before the picture
            for j in range(5 if e['what'] != 'shatter' else 18): add(buf, e['t'] + r.uniform(0, .6), kora(800 + r.uniform(0, 900), .4, r), .1)
    add(buf, 12.2, noise(.3, r, .15, lp=500), .9); add(buf, 12.45, noise(.3, r, .15, lp=500), .6); add(buf, 12.6, noise(.3, r, .15, lp=500), .4)   # the fall, told three times
    for a, b, nm in INSERTS:
        if nm == 'horns': add(buf, a, tone(98, b - a + .3, .05, .4, harm=(1., .6, .4, .3)), .5)   # a horn for the horns
    write_wav(os.path.join(HERE, 'sound.wav'), buf)

if __name__ == '__main__':
    os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
    sound(); meter = Meter(sc); film = Film(os.path.join(OUT, 'film.mp4')); still = set(int(round(s * FPS)) for s in STILL_T)
    for f in range(576):
        rgb, lab, skip, e = frame(f); film.put(rgb); meter.frame(f, lab[::2, ::2], rgb, skip=skip)
        if f in still: Image.fromarray(rgb).save(os.path.join(OUT, 'stills', f'still_{f / FPS:04.1f}s.jpg'), quality=90)
        if f % 48 == 0: print('frame', f, flush=True)
    for nm, tt in (('retell_fall', 12.42), ('retell_hit', 9.8), ('insert_horns', 7.1), ('insert_sea', 23.5)):
        Image.fromarray(frame(int(round(tt * FPS)))[0]).save(os.path.join(OUT, 'stills', f'{nm}_{tt:04.1f}s.jpg'), quality=90)
    film.close(os.path.join(HERE, 'sound.wav'))
    rep = meter.report(); json.dump(rep, open(os.path.join(OUT, 'invariants.json'), 'w'), indent=1)
    json.dump(dict(swarm='SCION-MAMBETY', edl=[list(map(lambda v: round(v, 3) if isinstance(v, float) else v, e)) for e in EDL], frames=meter.rows), open(os.path.join(OUT, 'trace.json'), 'w'))
    contact(os.path.join(OUT, 'stills'), os.path.join(OUT, 'stills', 'contact.jpg'))
    print({k: (v['ok'] if isinstance(v, dict) else v) for k, v in rep.items()})
